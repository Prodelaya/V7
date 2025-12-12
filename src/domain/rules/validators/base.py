"""Base validator abstract class.

Implementation Requirements:
- Abstract base class with validate() method
- Return tuple of (is_valid, error_message)
- Name property for identification

Reference:
- docs/05-Implementation.md: Task 3.1

TODO: Implement BaseValidator
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional


class BaseValidator(ABC):
    """
    Abstract base class for pick validators.
    
    Each validator checks one specific rule and returns
    a validation result.
    
    TODO: Implement based on:
    - Task 3.1 in docs/05-Implementation.md
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Identifier for this validator.
        
        Returns:
            Validator name (e.g., "OddsValidator")
        """
        pass
    
    @abstractmethod
    async def validate(self, pick_data: dict) -> Tuple[bool, Optional[str]]:
        """
        Validate pick data.
        
        Args:
            pick_data: Raw pick data from API
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if validation passed
            - error_message: Description of failure, or None
        """
        pass
