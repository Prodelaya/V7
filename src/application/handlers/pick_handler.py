"""Pick handler - Main application service for processing picks.

Implementation Requirements:
- Orchestrate full flow: fetch → validate → dedup → calculate → send
- Use asyncio.gather for parallel processing (NOT workers/queues)
- Coordinate with validation chain, calculation service, telegram gateway

Reference:
- docs/05-Implementation.md: Task 6.4
- docs/02-PDR.md: Section 3.2 (Application Layer)
- docs/03-ADRs.md: ADR-014 (asyncio.gather, no workers)

TODO: Implement PickHandler
"""

import asyncio
from typing import Dict, List, Protocol


class MessageGateway(Protocol):
    """Protocol for message sending."""
    async def send(self, pick, channel_id: int) -> bool: ...


class PickRepository(Protocol):
    """Protocol for pick persistence."""
    async def mark_sent(self, pick) -> bool: ...


class PickHandler:
    """
    Application service for processing picks.

    Orchestrates the complete pick processing flow:
    1. Convert raw picks to DTOs/entities
    2. Validate with ValidationChain (fail-fast)
    3. Check duplicates/rebotes in Redis
    4. Calculate stake and min_odds
    5. Format message
    6. Send via Telegram (with priority queue)
    7. Mark as sent in Redis (with await, NOT fire-and-forget)

    Uses asyncio.gather for parallel processing.
    ⚠️ NO workers/queues (from ADR-014 - adds latency)

    TODO: Implement based on:
    - Task 6.4 in docs/05-Implementation.md
    - Section 3.2 in docs/02-PDR.md
    - ADR-014 in docs/03-ADRs.md
    """

    def __init__(
        self,
        validation_chain,
        calculation_service,
        message_gateway: MessageGateway,
        pick_repository: PickRepository,
        channel_mapping: Dict[str, int],
        max_concurrent: int = 250,
    ):
        """
        Initialize PickHandler.

        Args:
            validation_chain: ValidationChain for pick validation
            calculation_service: CalculationService for stake/min_odds
            message_gateway: Gateway for sending Telegram messages
            pick_repository: Repository for marking picks as sent
            channel_mapping: Map of bookmaker -> channel_id
            max_concurrent: Maximum concurrent pick processing
        """
        self._validation_chain = validation_chain
        self._calculation_service = calculation_service
        self._message_gateway = message_gateway
        self._pick_repository = pick_repository
        self._channel_mapping = channel_mapping
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def process_surebets(self, surebets: List[dict]) -> Dict[str, int]:
        """
        Process a batch of surebets.

        Uses asyncio.gather for parallel processing.

        Args:
            surebets: Raw surebet data from API

        Returns:
            Statistics dict with total, validated, sent, failed counts

        Example flow (from docs/05-Implementation.md 6.4):
            1. Convertir raw_picks a DTOs/Entidades
            2. Para cada pick (con asyncio.gather):
               a. Validar con ValidationChain
               b. Si válido: check duplicado en Redis
               c. Si no duplicado: calcular stake + min_odds
               d. Formatear mensaje
               e. Encolar en TelegramGateway
               f. Guardar en Redis (con await, no fire-and-forget)
            3. Retornar cantidad de picks enviados
        """
        raise NotImplementedError("PickHandler.process_surebets not implemented")

    async def _process_single(self, surebet_data: dict, stats: Dict[str, int]) -> None:
        """
        Process a single surebet.

        Uses semaphore for concurrency control.
        """
        raise NotImplementedError("PickHandler._process_single not implemented")
