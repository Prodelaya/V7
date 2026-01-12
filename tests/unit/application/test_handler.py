
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.handlers.pick_handler import PickHandler, MessageGateway, PickRepository
from src.application.dto.pick_dto import PickDTO
from src.domain.entities.pick import Pick
from src.domain.entities.surebet import Surebet
from src.domain.rules.validation_chain import ValidationChain, ValidationResult
from src.domain.services.calculators.base import StakeResult, MinOddsResult
from src.config.bookmakers import BookmakerConfig

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.fixture
def mock_validation_chain():
    chain = MagicMock(spec=ValidationChain)
    chain.validate = AsyncMock()
    return chain

@pytest.fixture
def mock_calculation_service():
    service = MagicMock()
    service.calculate_stake.return_value = StakeResult(emoji="🟢")
    service.calculate_min_odds.return_value = MinOddsResult(min_odds=1.85, profit_threshold=-0.01)
    return service

@pytest.fixture
def mock_message_formatter():
    formatter = MagicMock()
    formatter.format = AsyncMock(return_value="<b>Surebet!</b>")
    return formatter

@pytest.fixture
def mock_message_gateway():
    gateway = MagicMock(spec=MessageGateway)
    gateway.send = AsyncMock(return_value=True)
    return gateway

@pytest.fixture
def mock_pick_repository():
    repo = MagicMock(spec=PickRepository)
    repo.save_with_opposites = AsyncMock(return_value=True)
    return repo

@pytest.fixture
def mock_bookmaker_config():
    config = MagicMock(spec=BookmakerConfig)
    # Attributes
    config.target_bookmakers = ["retabet_apuestas"]
    # Methods
    config.get_sharp_bookmakers.return_value = frozenset({"pinnaclesports"})
    config.is_target.return_value = True
    config.is_valid_contrapartida.return_value = True
    config.get_channel.return_value = 12345
    return config

@pytest.fixture
def pick_handler(
    mock_validation_chain,
    mock_calculation_service,
    mock_message_formatter,
    mock_message_gateway,
    mock_pick_repository,
    mock_bookmaker_config,
):
    return PickHandler(
        validation_chain=mock_validation_chain,
        calculation_service=mock_calculation_service,
        message_formatter=mock_message_formatter,
        message_gateway=mock_message_gateway,
        pick_repository=mock_pick_repository,
        bookmaker_config=mock_bookmaker_config,
        max_concurrent=5,  # Low concurrency for easier testing
    )

@pytest.fixture
def sample_surebet_data():
    return {
        "profit": 2.5,
        "prongs": [
            {
                "bk": "pinnaclesports",
                "value": 2.10,
                "teams": ["Team A", "Team B"],
                "time": 1735686000000,  # Fixed time
                "type": {"type": "over", "variety": "2.5"},
                "sport_id": "football"
            },
            {
                "bk": "retabet_apuestas",
                "value": 2.05,
                "teams": ["Team A", "Team B"],
                "time": 1735686000000,
                "type": {"type": "under", "variety": "2.5"},
                "sport_id": "football"
            }
        ]
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INITIALIZATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_init_with_all_dependencies(pick_handler):
    """Verify handler initializes with all dependencies."""
    assert pick_handler._validation_chain is not None
    assert pick_handler._calculation_service is not None
    assert pick_handler._message_gateway is not None
    assert pick_handler._semaphore._value == 5

def test_create_with_duplicate_validation_factory(
    mock_pick_repository,
    mock_message_formatter,
    mock_message_gateway,
    mock_bookmaker_config,
    mock_calculation_service
):
    """Verify factory method creates handler with DuplicateValidator."""
    with patch("src.domain.rules.validation_chain.ValidationChain.create_default") as mock_chain_create:
        mock_chain_instance = MagicMock()
        mock_chain_create.return_value = mock_chain_instance

        handler = PickHandler.create_with_duplicate_validation(
            repository=mock_pick_repository,
            message_formatter=mock_message_formatter,
            message_gateway=mock_message_gateway,
            bookmaker_config=mock_bookmaker_config,
            calculation_service=mock_calculation_service
        )

        assert mock_chain_create.called
        assert mock_chain_instance.add_validator.called
        assert handler._pick_repository == mock_pick_repository

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DTO CONVERSION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_process_single_converts_dto_successfully(pick_handler, sample_surebet_data):
    """Verify successful DTO conversion flow."""
    stats = {"converted": 0, "failed": 0, "validated": 0, "sent": 0}
    pick_handler._validation_chain.validate.return_value = ValidationResult(is_valid=True)
    
    await pick_handler._process_single(sample_surebet_data, stats)
    
    assert stats["converted"] == 1
    assert stats["failed"] == 0

@pytest.mark.asyncio
async def test_process_single_handles_dto_conversion_error(pick_handler):
    """Verify handling of invalid data during DTO conversion."""
    stats = {"converted": 0, "failed": 0, "validated": 0, "sent": 0}
    invalid_data = {"missing": "fields"}
    
    await pick_handler._process_single(invalid_data, stats)
    
    assert stats["converted"] == 0
    assert stats["failed"] == 1
    assert stats["sent"] == 0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VALIDATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_process_single_passes_validation(pick_handler, sample_surebet_data):
    """Verify successful validation allows processing to continue."""
    stats = {"converted": 0, "failed": 0, "validated": 0, "sent": 0}
    pick_handler._validation_chain.validate.return_value = ValidationResult(is_valid=True)
    
    with patch("src.application.dto.pick_dto.PickDTO.from_api_response") as mock_dto_factory:
        mock_dto = MagicMock(spec=PickDTO)
        mock_dto.to_surebet.return_value = MagicMock(spec=Surebet)
        mock_dto.to_pick.return_value = MagicMock(spec=Pick)
        mock_dto.channel_id = 12345
        mock_dto_factory.return_value = mock_dto
        
        await pick_handler._process_single(sample_surebet_data, stats)
        
        assert stats["validated"] == 1
        assert stats["failed"] == 0

@pytest.mark.asyncio
async def test_process_single_fails_validation_increments_failed(pick_handler, sample_surebet_data):
    """Verify failed validation stops processing and updates stats."""
    stats = {"converted": 0, "failed": 0, "validated": 0, "sent": 0}
    pick_handler._validation_chain.validate.return_value = ValidationResult(
        is_valid=False, error_message="Duplicate"
    )
    
    with patch("src.application.dto.pick_dto.PickDTO.from_api_response") as mock_dto_factory:
        mock_dto = MagicMock(spec=PickDTO)
        # Add necessary properties that handle_single might access before validation
        mock_dto.profit = 2.5
        mock_dto_factory.return_value = mock_dto
        
        await pick_handler._process_single(sample_surebet_data, stats)
        
        assert stats["validated"] == 0
        assert stats["failed"] == 1
        # Should NOT reach sending stage
        assert not pick_handler._message_gateway.send.called

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CALCULATION & FORMATTING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_process_single_rejects_out_of_range_profit(pick_handler, sample_surebet_data):
    """Verify pick is dropped if calculation service returns None (invalid profit)."""
    stats = {"converted": 0, "failed": 0, "validated": 0, "sent": 0}
    pick_handler._validation_chain.validate.return_value = ValidationResult(is_valid=True)
    pick_handler._calculation_service.calculate_stake.return_value = None  # Reject
    
    with patch("src.application.dto.pick_dto.PickDTO.from_api_response") as mock_dto_factory:
        mock_dto = MagicMock(spec=PickDTO)
        mock_dto.profit = 25.0
        mock_dto.sharp_bookmaker = "pinnaclesports"
        mock_dto.to_surebet.return_value = MagicMock(spec=Surebet)
        mock_dto_factory.return_value = mock_dto
        
        await pick_handler._process_single(sample_surebet_data, stats)
        
        assert stats["failed"] == 1
        assert not pick_handler._message_gateway.send.called

@pytest.mark.asyncio
async def test_process_single_handles_empty_formatted_message(pick_handler, sample_surebet_data):
    """Verify pick is dropped if message formatter returns empty string."""
    stats = {"converted": 0, "failed": 0, "validated": 0, "sent": 0}
    pick_handler._validation_chain.validate.return_value = ValidationResult(is_valid=True)
    pick_handler._message_formatter.format.return_value = ""  # Empty message
    
    with patch("src.application.dto.pick_dto.PickDTO.from_api_response") as mock_dto_factory:
        mock_dto = MagicMock(spec=PickDTO)
        mock_dto.channel_id = 12345
        mock_dto_factory.return_value = mock_dto
        
        await pick_handler._process_single(sample_surebet_data, stats)
        
        assert stats["failed"] == 1
        assert not pick_handler._message_gateway.send.called

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GATEWAY & PERSISTENCE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_process_single_queues_message_and_saves(pick_handler, sample_surebet_data):
    """Verify successful flow queues message and saves to Redis."""
    stats = {"converted": 0, "failed": 0, "validated": 0, "sent": 0}
    pick_handler._validation_chain.validate.return_value = ValidationResult(is_valid=True)
    
    with patch("src.application.dto.pick_dto.PickDTO.from_api_response") as mock_dto_factory:
        mock_dto = MagicMock(spec=PickDTO)
        mock_pick = MagicMock(spec=Pick)
        # Mock seconds_until_event for TTL calculation
        mock_pick.seconds_until_event.return_value = 3600
        mock_dto.to_pick.return_value = mock_pick
        mock_dto.channel_id = 12345
        mock_dto_factory.return_value = mock_dto
        
        await pick_handler._process_single(sample_surebet_data, stats)
        
        assert pick_handler._message_gateway.send.called
        assert pick_handler._pick_repository.save_with_opposites.called
        assert stats["sent"] == 1

@pytest.mark.asyncio
async def test_process_single_handles_queue_full(pick_handler, sample_surebet_data):
    """Verify failure when gateway rejects message (queue full)."""
    stats = {"converted": 0, "failed": 0, "validated": 0, "sent": 0}
    pick_handler._validation_chain.validate.return_value = ValidationResult(is_valid=True)
    pick_handler._message_gateway.send.return_value = False  # Qeue full
    
    with patch("src.application.dto.pick_dto.PickDTO.from_api_response") as mock_dto_factory:
        mock_dto = MagicMock(spec=PickDTO)
        mock_dto.channel_id = 12345
        mock_dto_factory.return_value = mock_dto
        
        await pick_handler._process_single(sample_surebet_data, stats)
        
        assert stats["failed"] == 1
        assert stats["sent"] == 0
        # Should NOT save to redis if not queued
        assert not pick_handler._pick_repository.save_with_opposites.called

@pytest.mark.asyncio
async def test_process_single_logs_warning_on_redis_failure(pick_handler, sample_surebet_data, caplog):
    """Verify that Redis failure doesn't fail the pick (it's already queued)."""
    stats = {"converted": 0, "failed": 0, "validated": 0, "sent": 0}
    pick_handler._validation_chain.validate.return_value = ValidationResult(is_valid=True)
    # Gateway accepts, but Redis fails
    pick_handler._message_gateway.send.return_value = True
    pick_handler._pick_repository.save_with_opposites.return_value = False
    
    with patch("src.application.dto.pick_dto.PickDTO.from_api_response") as mock_dto_factory:
        mock_dto = MagicMock(spec=PickDTO)
        mock_pick = MagicMock(spec=Pick)
        mock_pick.seconds_until_event.return_value = 3600
        mock_pick.redis_key = "test_key"
        mock_dto.to_pick.return_value = mock_pick
        mock_dto.channel_id = 12345
        mock_dto_factory.return_value = mock_dto
        
        await pick_handler._process_single(sample_surebet_data, stats)
        
        assert stats["sent"] == 1  # Still counts as sent
        assert "Failed to save pick to Redis" in caplog.text

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BATCH & CONCURRENCY TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.asyncio
async def test_process_surebets_handles_mixed_results(pick_handler):
    """Verify batch processing correctly aggregates stats."""
    batch = [{"id": 1}, {"id": 2}, {"id": 3}]
    
    # Mock process_single to simulate mixed outcomes
    async def side_effect(data, stats):
        if data["id"] == 1:
            stats["sent"] += 1
        elif data["id"] == 2:
            stats["failed"] += 1
        else:
            stats["validated"] += 1 # Validated but maybe not sent
            
    with patch.object(pick_handler, '_process_single', side_effect=side_effect):
        stats = await pick_handler.process_surebets(batch)
        
        assert stats["total"] == 3
        assert stats["sent"] == 1
        assert stats["failed"] == 1
        assert stats["validated"] == 1

@pytest.mark.asyncio
async def test_semaphore_limits_concurrency(pick_handler):
    """Verify semaphore limits concurrent tasks."""
    # pick_handler fixture has max_concurrent=5
    assert pick_handler._semaphore._value == 5
    
    # Simulate a task that holds the semaphore
    async with pick_handler._semaphore:
        assert pick_handler._semaphore._value == 4


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TTL CALCULATION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_calculate_ttl_logic(pick_handler):
    """Verify TTL calculation bounds."""
    mock_pick = MagicMock(spec=Pick)
    
    # Case 1: Standard future event (1 hour)
    mock_pick.seconds_until_event.return_value = 3600
    assert pick_handler._calculate_ttl(mock_pick) == 3600
    
    # Case 2: Event already started (negative time)
    mock_pick.seconds_until_event.return_value = -100
    assert pick_handler._calculate_ttl(mock_pick) == 60  # Min TTL
    
    # Case 3: Event very far in future (> 24h)
    mock_pick.seconds_until_event.return_value = 100000
    assert pick_handler._calculate_ttl(mock_pick) == 86400  # Max TTL
