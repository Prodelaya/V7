"""Pick handler for processing surebets."""

import asyncio
import logging
from typing import List, Protocol

from ...domain.entities.surebet import Surebet
from ...domain.entities.pick import Pick
from ...domain.rules.validation_chain import ValidationChain
from ...domain.services.calculation_service import CalculationService
from ..dto.pick_dto import PickDTO


logger = logging.getLogger(__name__)


class MessageGateway(Protocol):
    """Protocol for message sending."""
    async def send(self, pick: Pick, channel_id: int) -> bool:
        ...


class PickRepository(Protocol):
    """Protocol for pick persistence."""
    async def mark_sent(self, pick: Pick) -> bool:
        ...


class PickHandler:
    """
    Application service for processing picks.
    
    Orchestrates validation, calculation, and distribution of picks
    using asyncio.gather for parallel processing.
    """
    
    def __init__(
        self,
        validation_chain: ValidationChain,
        calculation_service: CalculationService,
        message_gateway: MessageGateway,
        pick_repository: PickRepository,
        channel_mapping: dict[str, int],
        max_concurrent: int = 250,
    ):
        self._validation_chain = validation_chain
        self._calculation_service = calculation_service
        self._message_gateway = message_gateway
        self._pick_repository = pick_repository
        self._channel_mapping = channel_mapping
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_surebets(self, surebets: List[dict]) -> dict:
        """
        Process a batch of surebets.
        
        Args:
            surebets: Raw surebet data from API
            
        Returns:
            Processing statistics
        """
        stats = {
            "total": len(surebets),
            "validated": 0,
            "sent": 0,
            "failed": 0,
        }
        
        # Process in parallel with semaphore
        tasks = [
            self._process_single(surebet, stats)
            for surebet in surebets
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return stats
    
    async def _process_single(self, surebet_data: dict, stats: dict) -> None:
        """Process a single surebet."""
        async with self._semaphore:
            try:
                # Validate
                result = await self._validation_chain.validate(surebet_data)
                if not result.is_valid:
                    logger.debug(f"Validation failed: {result.error_message}")
                    return
                
                stats["validated"] += 1
                
                # Convert to Pick
                pick = self._create_pick(surebet_data)
                if not pick:
                    return
                
                # Get channel
                channel_id = self._channel_mapping.get(pick.bookmaker)
                if not channel_id:
                    logger.warning(f"No channel for bookmaker: {pick.bookmaker}")
                    return
                
                # Send message
                success = await self._message_gateway.send(pick, channel_id)
                if success:
                    await self._pick_repository.mark_sent(pick)
                    stats["sent"] += 1
                else:
                    stats["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing surebet: {e}")
                stats["failed"] += 1
    
    def _create_pick(self, surebet_data: dict) -> Pick | None:
        """Create Pick entity from surebet data."""
        try:
            dto = PickDTO.from_api_response(surebet_data)
            return dto.to_entity(self._calculation_service)
        except Exception as e:
            logger.error(f"Error creating pick: {e}")
            return None
