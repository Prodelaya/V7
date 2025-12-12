"""Main entry point for Retador application."""

import asyncio
import logging
import signal
from typing import Optional

from src.config.settings import Settings
from src.config.bookmakers import BookmakerConfig
from src.config.logging_config import setup_logging
from src.domain.rules.validation_chain import ValidationChain
from src.domain.rules.validators import (
    OddsValidator,
    ProfitValidator,
    TimeValidator,
)
from src.domain.services.calculation_service import CalculationService
from src.infrastructure.api.surebet_client import SurebetClient
from src.infrastructure.api.rate_limiter import AdaptiveRateLimiter
from src.infrastructure.repositories.redis_repository import RedisRepository
from src.infrastructure.messaging.telegram_gateway import TelegramGateway
from src.infrastructure.messaging.message_formatter import MessageFormatter
from src.application.handlers.pick_handler import PickHandler


logger = logging.getLogger(__name__)


class Retador:
    """Main application class."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.bookmaker_config = BookmakerConfig()
        self._is_running = False
        self._components: dict = {}
    
    async def setup(self) -> None:
        """Initialize all components."""
        logger.info("Initializing Retador v2.0...")
        
        # Rate limiter
        rate_limiter = AdaptiveRateLimiter(
            requests_per_second=self.settings.polling.requests_per_second,
            base_interval=self.settings.polling.base_interval,
            max_interval=self.settings.polling.max_interval,
        )
        
        # API client
        api_client = SurebetClient(
            api_url=self.settings.api.url,
            api_token=self.settings.api.token,
            rate_limiter=rate_limiter,
            timeout=self.settings.api.timeout,
        )
        
        # Redis repository
        redis_repo = RedisRepository(
            host=self.settings.redis.host,
            port=self.settings.redis.port,
            password=self.settings.redis.password,
            username=self.settings.redis.username,
            db=self.settings.redis.db,
        )
        
        # Recover cursor from Redis
        saved_cursor = await redis_repo.get_cursor()
        if saved_cursor:
            api_client.set_cursor(saved_cursor)
            logger.info(f"Recovered cursor: {saved_cursor}")
        
        # Message formatter and Telegram gateway
        formatter = MessageFormatter(cache_ttl=self.settings.cache_ttl)
        telegram = TelegramGateway(
            bot_tokens=self.settings.telegram.tokens,
            formatter=formatter,
        )
        
        # Validation chain
        validation_chain = ValidationChain([
            OddsValidator(
                min_odds=self.settings.validation.min_odds,
                max_odds=self.settings.validation.max_odds,
            ),
            ProfitValidator(
                min_profit=self.settings.validation.min_profit,
                max_profit=self.settings.validation.max_profit,
            ),
            TimeValidator(
                min_seconds=self.settings.validation.min_event_time,
            ),
        ])
        
        # Calculation service
        calc_service = CalculationService()
        
        # Pick handler
        pick_handler = PickHandler(
            validation_chain=validation_chain,
            calculation_service=calc_service,
            message_gateway=telegram,
            pick_repository=redis_repo,
            channel_mapping=self.bookmaker_config.channel_mapping,
            max_concurrent=self.settings.concurrent_picks,
        )
        
        # Store components
        self._components = {
            "rate_limiter": rate_limiter,
            "api_client": api_client,
            "redis_repo": redis_repo,
            "telegram": telegram,
            "pick_handler": pick_handler,
        }
        
        logger.info("Retador initialized successfully")
    
    async def run(self) -> None:
        """Main processing loop."""
        self._is_running = True
        
        api_client = self._components["api_client"]
        redis_repo = self._components["redis_repo"]
        pick_handler = self._components["pick_handler"]
        telegram = self._components["telegram"]
        
        # Start Telegram processing
        await telegram.start_processing()
        
        logger.info("Starting main processing loop...")
        
        while self._is_running:
            try:
                # Fetch surebets
                surebets = await api_client.fetch_surebets(
                    bookmakers=self.bookmaker_config.bookmaker_ids,
                    sports=self.settings.sports,
                    limit=self.settings.limit,
                    min_profit=self.settings.validation.min_profit,
                )
                
                if surebets:
                    # Process picks
                    stats = await pick_handler.process_surebets(surebets)
                    logger.info(
                        f"Processed: {stats['validated']}/{stats['total']} validated, "
                        f"{stats['sent']} sent, {stats['failed']} failed"
                    )
                    
                    # Persist cursor
                    cursor = api_client.get_cursor()
                    if cursor:
                        await redis_repo.set_cursor(cursor)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(1)
    
    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down Retador...")
        self._is_running = False
        
        # Close components
        if "telegram" in self._components:
            await self._components["telegram"].close()
        if "api_client" in self._components:
            await self._components["api_client"].close()
        if "redis_repo" in self._components:
            await self._components["redis_repo"].close()
        
        logger.info("Shutdown complete")


async def main():
    """Main entry point."""
    # Load settings
    settings = Settings.from_env()
    
    # Setup logging
    setup_logging(
        level=logging.INFO,
        telegram_bot_token=settings.telegram.tokens[0] if settings.telegram.tokens else None,
        telegram_chat_id=settings.telegram.log_channel_id,
    )
    
    # Create and run application
    app = Retador(settings)
    
    # Handle signals
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        asyncio.create_task(app.shutdown())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await app.setup()
        await app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
