"""Pick handler - Main application service for processing picks.

Implementation Requirements:
- Orchestrate full flow: fetch → validate → dedup → calculate → send
- Use asyncio.gather for parallel processing (NOT workers/queues)
- Coordinate with validation chain, calculation service, telegram gateway

Reference:
- docs/05-Implementation.md: Task 6.4
- docs/02-PDR.md: Section 3.2 (Application Layer)
- docs/03-ADRs.md: ADR-014 (asyncio.gather, no workers)
- docs/03-ADRs.md: ADR-013 (await Redis, no fire-and-forget)
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Protocol

if TYPE_CHECKING:
    from src.config.bookmakers import BookmakerConfig
    from src.domain.entities.pick import Pick
    from src.domain.rules.validation_chain import ValidationChain
    from src.domain.services.calculation_service import CalculationService
    from src.infrastructure.messaging.message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROTOCOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class MessageGateway(Protocol):
    """Protocol for message sending (matches TelegramGateway)."""

    async def send(
        self,
        pick: "Pick",
        channel_id: int,
        profit: float,
        formatted_message: Optional[str] = None,
    ) -> bool:
        """Queue pick for sending via Telegram."""
        ...


class PickRepository(Protocol):
    """Protocol for pick persistence (matches RedisRepository)."""

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...

    async def exists_any(self, keys: List[str]) -> bool:
        """Check if any key exists."""
        ...

    async def save_with_opposites(self, pick: "Pick", ttl: int) -> bool:
        """Save pick and its opposite market keys."""
        ...


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PICK HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class PickHandler:
    """
    Application service for processing picks.

    Orchestrates the complete pick processing flow:
    1. Convert raw picks to DTOs/entities
    2. Validate with ValidationChain (fail-fast)
    3. Check duplicates/rebotes in Redis (via DuplicateValidator)
    4. Calculate stake and min_odds
    5. Format message
    6. Send via Telegram (with priority queue)
    7. Mark as sent in Redis (with await, NOT fire-and-forget)

    Uses asyncio.gather for parallel processing.
    ⚠️ NO workers/queues (from ADR-014 - adds latency)
    ⚠️ Always await Redis operations (from ADR-013 - no fire-and-forget)

    Example:
        >>> handler = PickHandler.create_with_duplicate_validation(
        ...     repository=redis_repo,
        ...     message_formatter=formatter,
        ...     message_gateway=telegram_gateway,
        ...     bookmaker_config=config,
        ... )
        >>> stats = await handler.process_surebets(raw_surebets)
        >>> print(f"Sent: {stats['sent']}/{stats['total']}")
    """

    # TTL bounds for Redis keys
    MIN_TTL = 60  # 1 minute minimum
    MAX_TTL = 86400  # 24 hours maximum

    def __init__(
        self,
        validation_chain: "ValidationChain",
        calculation_service: "CalculationService",
        message_formatter: "MessageFormatter",
        message_gateway: MessageGateway,
        pick_repository: PickRepository,
        bookmaker_config: "BookmakerConfig",
        max_concurrent: int = 250,
    ):
        """
        Initialize PickHandler.

        Args:
            validation_chain: ValidationChain for pick validation
                             (should include DuplicateValidator)
            calculation_service: CalculationService for stake/min_odds
            message_formatter: MessageFormatter for HTML message generation
            message_gateway: Gateway for sending Telegram messages
            pick_repository: Repository for marking picks as sent
            bookmaker_config: Configuration for bookmaker validation and channels
            max_concurrent: Maximum concurrent pick processing (default: 250)
        """
        self._validation_chain = validation_chain
        self._calculation_service = calculation_service
        self._message_formatter = message_formatter
        self._message_gateway = message_gateway
        self._pick_repository = pick_repository
        self._bookmaker_config = bookmaker_config
        self._semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(
            f"PickHandler initialized with max_concurrent={max_concurrent}"
        )

    async def process_surebets(self, surebets: List[dict]) -> Dict[str, int]:
        """
        Process a batch of surebets using asyncio.gather (ADR-014).

        Args:
            surebets: Raw surebet data from API (list of dicts with 'prongs')

        Returns:
            Statistics dict with keys:
            - total: Number of surebets received
            - converted: Successfully converted to DTOs
            - validated: Passed validation chain
            - sent: Successfully queued for sending
            - failed: Failed at any stage

        Example:
            >>> stats = await handler.process_surebets(api_response['records'])
            >>> print(f"Processed {stats['total']}, sent {stats['sent']}")
        """
        stats: Dict[str, int] = {
            "total": len(surebets),
            "converted": 0,
            "validated": 0,
            "sent": 0,
            "failed": 0,
        }

        if not surebets:
            logger.debug("No surebets to process")
            return stats

        # Create tasks for parallel processing (ADR-014)
        tasks = [
            self._process_single(surebet_data, stats)
            for surebet_data in surebets
        ]

        # Execute all tasks in parallel with exception handling
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(
            f"Batch processed: {stats['sent']}/{stats['total']} sent, "
            f"{stats['validated']} validated, {stats['failed']} failed"
        )

        return stats

    async def _process_single(
        self,
        surebet_data: dict,
        stats: Dict[str, int],
    ) -> None:
        """
        Process a single surebet with semaphore control.

        Flow:
        1. Convert raw dict → PickDTO
        2. Extract Surebet and Pick entities
        3. Validate with ValidationChain
        4. Calculate stake and min_odds
        5. Format message
        6. Queue via TelegramGateway
        7. Save to Redis (await per ADR-013)

        Args:
            surebet_data: Raw API surebet dict
            stats: Shared stats dict (mutated in-place)
        """
        # Import here to avoid circular imports
        from ..dto.pick_dto import PickDTO

        async with self._semaphore:
            try:
                # Step 1: Convert to DTO
                try:
                    dto = PickDTO.from_api_response(
                        surebet_data,
                        self._bookmaker_config,
                    )
                    stats["converted"] += 1
                except (ValueError, KeyError, TypeError) as e:
                    logger.debug(f"DTO conversion failed: {e}")
                    stats["failed"] += 1
                    return

                # Step 2: Get domain entities
                surebet = dto.to_surebet()
                pick = dto.to_pick()

                # Step 3: Validate (chain includes DuplicateValidator)
                result = await self._validation_chain.validate(surebet)
                if not result.is_valid:
                    logger.debug(
                        f"Validation failed ({result.failed_validator}): "
                        f"{result.error_message}"
                    )
                    stats["failed"] += 1
                    return

                stats["validated"] += 1

                # Step 4: Calculate stake and min_odds
                stake_result = self._calculation_service.calculate_stake(
                    dto.profit,
                    dto.sharp_bookmaker,
                )
                if stake_result is None:
                    # Rejected by calculator (profit out of range)
                    logger.debug(
                        f"Stake calculation rejected profit={dto.profit}"
                    )
                    stats["failed"] += 1
                    return

                # Step 5: Format message
                formatted = await self._message_formatter.format(
                    pick,
                    sharp_odds=surebet.sharp_odds.value,
                    profit=dto.profit,
                    sharp_bookmaker=dto.sharp_bookmaker,
                )
                if not formatted:
                    # Formatter rejected (e.g., stake calculation failed inside)
                    logger.debug("Message formatting returned empty")
                    stats["failed"] += 1
                    return

                # Step 6: Queue message for sending
                queued = await self._message_gateway.send(
                    pick,
                    dto.channel_id,
                    dto.profit,
                    formatted_message=formatted,
                )

                if not queued:
                    logger.debug("Message rejected by gateway (queue full?)")
                    stats["failed"] += 1
                    return

                # Step 7: Mark as sent in Redis (MUST await per ADR-013)
                ttl = self._calculate_ttl(pick)
                saved = await self._pick_repository.save_with_opposites(
                    pick, ttl
                )
                if not saved:
                    # Log warning but don't fail - message already queued
                    logger.warning(
                        f"Failed to save pick to Redis: "
                        f"{pick.redis_key[:50]}..."
                    )

                stats["sent"] += 1

            except Exception as e:
                logger.error(f"Unexpected error processing surebet: {e}")
                stats["failed"] += 1

    def _calculate_ttl(self, pick: "Pick") -> int:
        """
        Calculate Redis TTL based on event time.

        TTL = seconds until event, bounded to [MIN_TTL, MAX_TTL].
        For events that have already started, returns MIN_TTL.

        Args:
            pick: Pick entity with event_time

        Returns:
            TTL in seconds (between 60 and 86400)
        """
        seconds_until = int(pick.seconds_until_event())

        # Add buffer for events that just started
        if seconds_until <= 0:
            return self.MIN_TTL

        return max(self.MIN_TTL, min(self.MAX_TTL, seconds_until))

    @classmethod
    def create_with_duplicate_validation(
        cls,
        repository: PickRepository,
        message_formatter: "MessageFormatter",
        message_gateway: MessageGateway,
        bookmaker_config: "BookmakerConfig",
        calculation_service: Optional["CalculationService"] = None,
        max_concurrent: int = 250,
    ) -> "PickHandler":
        """
        Factory method that creates handler with DuplicateValidator in chain.

        Convenience method for standard setup where DuplicateValidator
        needs to be wired with the repository.

        Args:
            repository: PickRepository for deduplication and persistence
            message_formatter: MessageFormatter for HTML generation
            message_gateway: TelegramGateway for sending
            bookmaker_config: BookmakerConfig for validation
            calculation_service: Optional CalculationService
                                (creates default if None)
            max_concurrent: Maximum concurrent processing (default: 250)

        Returns:
            Configured PickHandler with ValidationChain including
            DuplicateValidator.

        Example:
            >>> handler = PickHandler.create_with_duplicate_validation(
            ...     repository=redis_repo,
            ...     message_formatter=formatter,
            ...     message_gateway=gateway,
            ...     bookmaker_config=config,
            ... )
        """
        from ...domain.rules.validation_chain import ValidationChain
        from ...domain.rules.validators.duplicate_validator import (
            DuplicateValidator,
        )
        from ...domain.services.calculation_service import CalculationService

        # Create default validation chain + add DuplicateValidator
        chain = ValidationChain.create_default()
        chain.add_validator(DuplicateValidator(repository))

        return cls(
            validation_chain=chain,
            calculation_service=calculation_service or CalculationService(),
            message_formatter=message_formatter,
            message_gateway=message_gateway,
            pick_repository=repository,
            bookmaker_config=bookmaker_config,
            max_concurrent=max_concurrent,
        )
