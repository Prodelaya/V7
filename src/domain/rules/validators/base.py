"""Base validator interface."""

from abc import ABC, abstractmethod
from typing import Tuple


class BaseValidator(ABC):
    """
    Abstract base class for pick validators.
    
    Each validator checks one specific aspect of a pick.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique validator name."""
        pass
    
    @abstractmethod
    async def validate(self, pick_data: dict) -> Tuple[bool, str | None]:
        """
        Validate a pick.
        
        Args:
            pick_data: Raw pick data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
            error_message is None if valid
        """
        pass
