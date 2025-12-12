"""Tests for odds calculators."""

import pytest

from src.domain.value_objects.odds import Odds
from src.domain.value_objects.profit import Profit
from src.domain.services.calculators.pinnacle import PinnacleCalculator
from src.domain.services.calculators.factory import CalculatorFactory


class TestPinnacleCalculator:
    """Tests for PinnacleCalculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = PinnacleCalculator()
    
    def test_calculate_min_odds_standard(self):
        """Test minimum odds calculation with standard input."""
        sharp_odds = Odds(2.00)
        min_odds = self.calculator.calculate_min_odds(sharp_odds, target_profit=-1.0)
        
        # Formula: 1 / (1 + (-0.01) - 1/2.00) = 1 / (0.99 - 0.5) = 1 / 0.49 ≈ 2.04
        assert 2.00 <= min_odds.value <= 2.10
    
    def test_calculate_min_odds_low_odds(self):
        """Test minimum odds with low sharp odds."""
        sharp_odds = Odds(1.50)
        min_odds = self.calculator.calculate_min_odds(sharp_odds, target_profit=-1.0)
        
        # Should be higher than sharp odds for low values
        assert min_odds.value > 2.5
    
    def test_calculate_min_odds_high_odds(self):
        """Test minimum odds with high sharp odds."""
        sharp_odds = Odds(5.00)
        min_odds = self.calculator.calculate_min_odds(sharp_odds, target_profit=-1.0)
        
        # Should be lower for high sharp odds
        assert min_odds.value < 1.30
    
    def test_calculate_value_positive_profit(self):
        """Test profit calculation with profitable surebet."""
        soft_odds = Odds(2.10)
        sharp_odds = Odds(2.00)
        
        profit = self.calculator.calculate_value(soft_odds, sharp_odds)
        
        # Combined probability > 1 means positive profit
        assert isinstance(profit, Profit)
        assert profit.value > 0
    
    def test_calculate_value_negative_profit(self):
        """Test profit calculation with negative surebet."""
        soft_odds = Odds(1.90)
        sharp_odds = Odds(2.00)
        
        profit = self.calculator.calculate_value(soft_odds, sharp_odds)
        
        # Combined probability < 1 means negative profit
        assert profit.value < 0


class TestCalculatorFactory:
    """Tests for CalculatorFactory."""
    
    def test_get_pinnacle_calculator(self):
        """Test getting Pinnacle calculator."""
        factory = CalculatorFactory()
        
        calculator = factory.get_calculator("pinnaclesports")
        
        assert isinstance(calculator, PinnacleCalculator)
    
    def test_get_calculator_case_insensitive(self):
        """Test that bookmaker lookup is case insensitive."""
        factory = CalculatorFactory()
        
        calc1 = factory.get_calculator("PINNACLESPORTS")
        calc2 = factory.get_calculator("pinnaclesports")
        
        assert calc1 is calc2
    
    def test_default_calculator(self):
        """Test that unknown bookmaker returns default calculator."""
        factory = CalculatorFactory()
        
        calculator = factory.get_calculator("unknown_bookmaker")
        
        assert isinstance(calculator, PinnacleCalculator)
