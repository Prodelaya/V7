"""Main entry point for Retador v2.0.

Implementation Requirements:
- Load configuration from environment
- Initialize all components in dependency order
- Start main polling loop
- Graceful shutdown on SIGINT/SIGTERM

Reference:
- docs/05-Implementation.md: Task 7.1
- docs/02-PDR.md: Section 2.3 (Flujo de Datos Principal)
- docs/03-ADRs.md: ADR-014 (asyncio.gather, no workers)
"""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import Any, Dict, Optional

# Application
from src.application.handlers.pick_handler import PickHandler

# Configuration
from src.config.bookmakers import BookmakerConfig
from src.config.logging_config import setup_logging
from src.config.settings import Settings

# Domain
from src.domain.services.calculation_service import CalculationService

# Infrastructure
from src.infrastructure.api.rate_limiter import AdaptiveRateLimiter
from src.infrastructure.api.surebet_client import SurebetClient
from src.infrastructure.messaging.message_formatter import MessageFormatter
from src.infrastructure.messaging.telegram_gateway import TelegramGateway
from src.infrastructure.repositories.redis_repository import RedisRepository

logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL STATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_running: bool = True
_shutdown_event: Optional[asyncio.Event] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIGNAL HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _request_shutdown(signum: int, frame: Any) -> None:
    """Signal handler - request graceful shutdown."""
    global _running
    logger.info(f"Received signal {signum}, requesting graceful shutdown...")
    _running = False
    if _shutdown_event:
        _shutdown_event.set()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMPONENT INITIALIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def init_components(settings: Settings) -> Dict[str, Any]:
    """
    Initialize all components in dependency order.

    Order:
    1. Redis Repository (no dependencies)
    2. Rate Limiter (no dependencies)
    3. API Client (depends on: redis_repo, rate_limiter)
    4. Calculation Service (no dependencies)
    5. Message Formatter (depends on: calculation_service)
    6. Telegram Gateway (no dependencies)
    7. Pick Handler (depends on: all above)

    Args:
        settings: Application settings

    Returns:
        Dict of initialized components
    """
    bookmaker_config = BookmakerConfig()

    # 1. Redis Repository
    logger.info("Initializing Redis repository...")
    redis_repo = await RedisRepository.from_settings(settings.redis)

    # 2. Rate Limiter
    logger.info("Initializing rate limiter...")
    rate_limiter = AdaptiveRateLimiter(
        base_interval=settings.polling.base_interval,
        max_interval=settings.polling.max_interval,
    )

    # 3. API Client
    logger.info("Initializing API client...")
    api_client = SurebetClient(
        api_url=settings.api.url,
        api_token=settings.api.token,
        rate_limiter=rate_limiter,
        cursor_repository=redis_repo,
        api_query=settings.api_query,
        bookmakers=bookmaker_config._api_bookmakers_list,
    )
    await api_client.initialize()

    # 4. Calculation Service
    logger.info("Initializing calculation service...")
    calculation_service = CalculationService()

    # 5. Message Formatter
    logger.info("Initializing message formatter...")
    message_formatter = MessageFormatter(calculation_service)

    # 6. Telegram Gateway
    logger.info("Initializing Telegram gateway...")
    telegram_gateway = TelegramGateway(
        bot_tokens=settings.telegram.bot_tokens,
        formatter=message_formatter,
        max_queue_size=settings.telegram.max_queue_size,
    )

    # 7. Pick Handler
    logger.info("Initializing pick handler...")
    handler = PickHandler.create_with_duplicate_validation(
        repository=redis_repo,
        message_formatter=message_formatter,
        message_gateway=telegram_gateway,
        bookmaker_config=bookmaker_config,
        calculation_service=calculation_service,
        max_concurrent=settings.concurrent_picks,
    )

    logger.info("All components initialized successfully")

    return {
        "redis": redis_repo,
        "rate_limiter": rate_limiter,
        "api_client": api_client,
        "telegram": telegram_gateway,
        "handler": handler,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN LOOP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def run_main_loop(
    api_client: SurebetClient,
    handler: PickHandler,
    rate_limiter: AdaptiveRateLimiter,
    telegram: TelegramGateway,
) -> None:
    """
    Main polling loop - fetch, process, repeat.

    Flow:
    1. Start Telegram background processing
    2. Fetch picks from API
    3. Process batch with handler
    4. Wait for adaptive interval
    5. Repeat until shutdown requested

    Args:
        api_client: Initialized SurebetClient
        handler: Initialized PickHandler
        rate_limiter: AdaptiveRateLimiter for polling intervals
        telegram: TelegramGateway for message sending
    """
    global _running, _shutdown_event
    _shutdown_event = asyncio.Event()

    # Start Telegram processing task
    await telegram.start_processing()

    logger.info("Starting main polling loop...")
    poll_count = 0

    while _running:
        try:
            poll_count += 1

            # Fetch picks from API
            picks = await api_client.fetch_picks()

            if picks:
                # Process batch
                stats = await handler.process_surebets(picks)
                logger.info(
                    f"Poll #{poll_count}: {stats['sent']}/{stats['total']} sent, "
                    f"{stats['validated']} validated, {stats['failed']} failed"
                )
            else:
                logger.debug(f"Poll #{poll_count}: No new picks")

            # Wait before next poll (adaptive interval)
            await asyncio.sleep(rate_limiter.current_interval)

        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            # Brief pause to prevent tight error loop
            await asyncio.sleep(1.0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLEANUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def cleanup(components: Dict[str, Any]) -> None:
    """
    Graceful shutdown of all components.

    Order (reverse of initialization):
    1. Stop Telegram (drains queue first)
    2. Close API client
    3. Close Redis last (may still be needed)

    Args:
        components: Dict of initialized components
    """
    logger.info("Starting graceful shutdown...")

    # Stop Telegram processing (drains remaining queue)
    if "telegram" in components:
        try:
            logger.info("Stopping Telegram gateway...")
            await components["telegram"].stop_processing()
            await components["telegram"].close()
        except Exception as e:
            logger.warning(f"Error closing Telegram: {e}")

    # Close API client
    if "api_client" in components:
        try:
            logger.info("Closing API client...")
            await components["api_client"].close()
        except Exception as e:
            logger.warning(f"Error closing API client: {e}")

    # Close Redis last
    if "redis" in components:
        try:
            logger.info("Closing Redis connection...")
            await components["redis"].close()
        except Exception as e:
            logger.warning(f"Error closing Redis: {e}")

    logger.info("Graceful shutdown complete")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def main() -> None:
    """
    Main application entry point.

    Flow:
    1. Load configuration from environment
    2. Setup logging
    3. Initialize all components
    4. Run main polling loop
    5. Cleanup on exit
    """
    # Load configuration
    settings = Settings()

    # Setup logging (includes Telegram error handler if configured)
    log_channel = settings.telegram.log_channel_id if hasattr(settings.telegram, 'log_channel_id') else None
    bot_tokens = settings.telegram.bot_tokens
    setup_logging(
        telegram_token=bot_tokens[0] if bot_tokens and log_channel else None,
        telegram_chat_id=log_channel,
    )

    logger.info("=" * 60)
    logger.info("Retador v2.0 starting...")
    logger.info(f"API URL: {settings.api.url}")
    logger.info(f"Polling interval: {settings.polling.base_interval}s - {settings.polling.max_interval}s")
    logger.info(f"Max concurrent picks: {settings.concurrent_picks}")
    logger.info("=" * 60)

    components: Dict[str, Any] = {}

    try:
        # Initialize components
        components = await init_components(settings)

        # Run main loop
        await run_main_loop(
            api_client=components["api_client"],
            handler=components["handler"],
            rate_limiter=components["rate_limiter"],
            telegram=components["telegram"],
        )

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        await cleanup(components)


if __name__ == "__main__":
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _request_shutdown)
    signal.signal(signal.SIGTERM, _request_shutdown)

    # Run application
    asyncio.run(main())
