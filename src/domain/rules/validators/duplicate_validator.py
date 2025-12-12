"""Duplicate validator for pick validation."""

from typing import Tuple, Protocol


class DuplicateChecker(Protocol):
    """Protocol for duplicate checking backends."""
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...
    
    async def exists_any(self, keys: list[str]) -> bool:
        """Check if any key exists."""
        ...


class DuplicateValidator:
    """
    Validates that a pick has not been sent before.
    
    Checks both the exact pick and opposite market keys.
    Uses external duplicate checker (Redis repository).
    """
    
    def __init__(self, duplicate_checker: DuplicateChecker):
        self._checker = duplicate_checker
    
    @property
    def name(self) -> str:
        return "duplicate_validator"
    
    async def validate(self, pick_data: dict) -> Tuple[bool, str | None]:
        """Validate pick is not a duplicate."""
        try:
            # Generate primary key
            key = self._generate_key(pick_data)
            
            # Check if already sent
            if await self._checker.exists(key):
                return (False, f"Duplicate pick: {key}")
            
            # Generate and check opposite market keys
            opposite_keys = self._generate_opposite_keys(pick_data)
            if opposite_keys and await self._checker.exists_any(opposite_keys):
                return (False, f"Opposite market already sent")
            
            return (True, None)
            
        except Exception as e:
            return (False, f"Duplicate check error: {e}")
    
    def _generate_key(self, pick_data: dict) -> str:
        """Generate unique key for pick."""
        teams = pick_data.get("teams", ["", ""])
        event_time = str(pick_data.get("time", ""))
        type_dict = pick_data.get("type", {})
        market_type = type_dict.get("type", "").lower()
        variety = type_dict.get("variety", "").lower()
        bookmaker = pick_data.get("target_bookmaker", "")
        
        return f"{teams[0]}:{teams[1]}:{event_time}:{market_type}:{variety}:{bookmaker}"
    
    def _generate_opposite_keys(self, pick_data: dict) -> list[str]:
        """Generate keys for opposite markets."""
        from ...value_objects.market_type import OPPOSITE_MARKETS
        
        teams = pick_data.get("teams", ["", ""])
        event_time = str(pick_data.get("time", ""))
        type_dict = pick_data.get("type", {})
        market_type = type_dict.get("type", "").lower()
        variety = type_dict.get("variety", "").lower()
        bookmaker = pick_data.get("target_bookmaker", "")
        
        base = f"{teams[0]}:{teams[1]}:{event_time}"
        
        opposite_types = OPPOSITE_MARKETS.get(market_type, [])
        return [f"{base}:{opp}:{variety}:{bookmaker}" for opp in opposite_types]
