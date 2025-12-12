"""Tests for validators."""

import pytest
from unittest.mock import AsyncMock

from src.domain.rules.validators.odds_validator import OddsValidator
from src.domain.rules.validators.profit_validator import ProfitValidator
from src.domain.rules.validators.time_validator import TimeValidator
from src.domain.rules.validation_chain import ValidationChain


class TestOddsValidator:
    """Tests for OddsValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = OddsValidator(min_odds=1.10, max_odds=9.99)
    
    @pytest.mark.asyncio
    async def test_valid_odds(self):
        """Test with valid odds."""
        pick_data = {
            "prongs": [
                {"odd": 2.50},
                {"odd": 1.80},
            ]
        }
        
        is_valid, error = await self.validator.validate(pick_data)
        
        assert is_valid is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_odds_too_low(self):
        """Test with odds below minimum."""
        pick_data = {
            "prongs": [
                {"odd": 1.05},  # Below 1.10
                {"odd": 1.80},
            ]
        }
        
        is_valid, error = await self.validator.validate(pick_data)
        
        assert is_valid is False
        assert "1.05" in error
    
    @pytest.mark.asyncio
    async def test_odds_too_high(self):
        """Test with odds above maximum."""
        pick_data = {
            "prongs": [
                {"odd": 15.00},  # Above 9.99
                {"odd": 1.80},
            ]
        }
        
        is_valid, error = await self.validator.validate(pick_data)
        
        assert is_valid is False
        assert "15" in error


class TestProfitValidator:
    """Tests for ProfitValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ProfitValidator(min_profit=-1.0, max_profit=25.0)
    
    @pytest.mark.asyncio
    async def test_valid_profit(self):
        """Test with valid profit."""
        pick_data = {"profit": 3.5}
        
        is_valid, error = await self.validator.validate(pick_data)
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_profit_too_low(self):
        """Test with profit below minimum."""
        pick_data = {"profit": -2.5}
        
        is_valid, error = await self.validator.validate(pick_data)
        
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_profit_too_high(self):
        """Test with profit above maximum."""
        pick_data = {"profit": 30.0}
        
        is_valid, error = await self.validator.validate(pick_data)
        
        assert is_valid is False


class TestValidationChain:
    """Tests for ValidationChain."""
    
    @pytest.mark.asyncio
    async def test_all_validators_pass(self):
        """Test when all validators pass."""
        chain = ValidationChain([
            OddsValidator(),
            ProfitValidator(),
        ])
        
        pick_data = {
            "prongs": [{"odd": 2.00}],
            "profit": 2.0,
        }
        
        result = await chain.validate(pick_data)
        
        assert result.is_valid is True
    
    @pytest.mark.asyncio
    async def test_fail_fast(self):
        """Test that chain fails fast on first failure."""
        chain = ValidationChain([
            OddsValidator(min_odds=1.10, max_odds=9.99),
            ProfitValidator(),
        ])
        
        pick_data = {
            "prongs": [{"odd": 0.5}],  # Invalid odds
            "profit": 2.0,
        }
        
        result = await chain.validate(pick_data)
        
        assert result.is_valid is False
        assert result.failed_validator == "odds_validator"
