"""Generative validator - Check if surebet is artificially generated.

Implementation Requirements:
- Reject surebets with generatives value of 2 (clearly generative)
- Value 0 = normal, 1 = probably generative, 2 = clearly generative
- CPU-only operation (no I/O)

Reference:
- docs/03-ADRs.md: ADR-015 (Origin Filtering)
- docs/01-SRS.md: RF-003 (validation requirements)

TODO: Implement GenerativeValidator
"""

from typing import Tuple, Optional

from .base import BaseValidator


class GenerativeValidator(BaseValidator):
    """
    Validator for generative bets detection.
    
    Rejects surebets where any leg is "clearly generative" (value 2).
    Generative bets are artificially created opportunities that are
    less reliable.
    
    Generatives field format: "0,2" (comma-separated values per leg)
    - 0 = normal bet
    - 1 = probably generative
    - 2 = clearly generative (reject)
    
    TODO: Implement based on:
    - ADR-015 in docs/03-ADRs.md
    - RF-003 in docs/01-SRS.md
    """
    
    def __init__(self, reject_threshold: int = 2):
        """
        Initialize with rejection threshold.
        
        Args:
            reject_threshold: Minimum generative value to reject (default 2)
        """
        self._reject_threshold = reject_threshold
    
    @property
    def name(self) -> str:
        return "GenerativeValidator"
    
    async def validate(self, pick_data: dict) -> Tuple[bool, Optional[str]]:
        """
        Check if surebet contains generative bets.
        
        Args:
            pick_data: Surebet data from API
            
        Returns:
            (True, None) if no clearly generative legs
            (False, "message") if any leg has generatives >= threshold
            
        Note: Default generatives is "0,0" if field not present.
        """
        raise NotImplementedError("GenerativeValidator.validate not implemented")
