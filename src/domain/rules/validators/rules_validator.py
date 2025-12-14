"""Rules validator - Check if surebet has conflicting sporting rules.

Implementation Requirements:
- Reject surebets with 'rd' field (different rules between bookmakers)
- Safety check since hide-different-rules=true filters most at API level
- CPU-only operation (no I/O)

Reference:
- docs/03-ADRs.md: ADR-015 (Origin Filtering)
- docs/01-SRS.md: RF-003 (validation requirements)

TODO: Implement RulesValidator
"""

from typing import Tuple, Optional

from .base import BaseValidator


class RulesValidator(BaseValidator):
    """
    Validator for sporting rules consistency.
    
    Rejects surebets where the 'rd' field is present, indicating
    that bookmakers may have different sporting rules (e.g., one
    counts overtime, the other doesn't).
    
    This is a safety check since hide-different-rules=true should
    filter most of these at the API level.
    
    TODO: Implement based on:
    - ADR-015 in docs/03-ADRs.md
    - RF-003 in docs/01-SRS.md
    """
    
    @property
    def name(self) -> str:
        return "RulesValidator"
    
    async def validate(self, pick_data: dict) -> Tuple[bool, Optional[str]]:
        """
        Check if surebet has conflicting rules.
        
        Args:
            pick_data: Surebet data from API
            
        Returns:
            (True, None) if no 'rd' field present
            (False, "message") if 'rd' field exists
            
        Note: The 'rd' field format is [[0], [1], [1]] indicating
        which legs have different rules.
        """
        raise NotImplementedError("RulesValidator.validate not implemented")
