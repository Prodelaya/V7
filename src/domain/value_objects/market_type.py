"""MarketType enum representing betting market types.

Implementation Requirements (Task 1.4):
- Enum with predefined market types
- Method: get_opposites() -> List[MarketType]
- Method: from_string(value) -> MarketType
- Mapping of opposite markets for rebote detection

Reference:
- docs/04-Structure.md: "value_objects/"
- docs/05-Implementation.md: Task 1.4
- docs/01-SRS.md: Appendix 6.1 (Opposite Markets)
- legacy/RetadorV6.py: opposite_markets dict (line 880)
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, List, Tuple

from src.shared.exceptions import InvalidMarketError

logger = logging.getLogger(__name__)


class MarketType(Enum):
    """
    Enum of valid betting market types.

    Markets with opposites (from docs/01-SRS.md and legacy):
        - win1 ↔ win2
        - over ↔ under
        - ah1 ↔ ah2
        - odd ↔ even
        - yes ↔ no
        - _1x ↔ _x2, _12 (double chance - multiple opposites)
        - And many more...

    Examples:
        >>> market = MarketType.WIN1
        >>> opposites = market.get_opposites()
        >>> MarketType.WIN2 in opposites
        True

        >>> MarketType.from_string("OVER")
        <MarketType.OVER: 'over'>
    """

    # -------------------------------------------------------------------------
    # Money line / Match winner
    # -------------------------------------------------------------------------
    WIN1 = "win1"
    WIN2 = "win2"
    DRAW = "draw"

    # -------------------------------------------------------------------------
    # Double chance
    # -------------------------------------------------------------------------
    _1X = "_1x"
    _X2 = "_x2"
    _12 = "_12"

    # -------------------------------------------------------------------------
    # Totals
    # -------------------------------------------------------------------------
    OVER = "over"
    UNDER = "under"

    # -------------------------------------------------------------------------
    # E-sports totals
    # -------------------------------------------------------------------------
    EOVER = "eover"
    EUNDER = "e_under"

    # -------------------------------------------------------------------------
    # Asian handicap
    # -------------------------------------------------------------------------
    AH1 = "ah1"
    AH2 = "ah2"

    # -------------------------------------------------------------------------
    # Odd/Even
    # -------------------------------------------------------------------------
    ODD = "odd"
    EVEN = "even"

    # -------------------------------------------------------------------------
    # Yes/No (BTTS, etc.)
    # -------------------------------------------------------------------------
    YES = "yes"
    NO = "no"

    # -------------------------------------------------------------------------
    # Draw no bet
    # -------------------------------------------------------------------------
    WIN1RETX = "win1retx"
    WIN2RETX = "win2retx"

    # -------------------------------------------------------------------------
    # Win only
    # -------------------------------------------------------------------------
    WINONLY1 = "winonly1"
    WINONLY2 = "winonly2"

    # -------------------------------------------------------------------------
    # Win to nil
    # -------------------------------------------------------------------------
    WIN1TONIL = "win1tonil"
    WIN2TONIL = "win2tonil"

    # -------------------------------------------------------------------------
    # Clean sheet
    # -------------------------------------------------------------------------
    CLEAN_SHEET_1 = "clean_sheet_1"
    CLEAN_SHEET_2 = "clean_sheet_2"

    # -------------------------------------------------------------------------
    # Qualification
    # -------------------------------------------------------------------------
    WIN1_QUALIFY = "win1 qualify"
    WIN2_QUALIFY = "win2 qualify"

    # -------------------------------------------------------------------------
    # Between margin (handicap variant)
    # -------------------------------------------------------------------------
    BETWEENMARGINH1 = "betweenmarginh1"
    BETWEENMARGINH2 = "betweenmarginh2"

    # -------------------------------------------------------------------------
    # Unknown market (fallback for unrecognized markets from API)
    # -------------------------------------------------------------------------
    UNKNOWN = "__unknown__"

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------

    def get_opposites(self) -> List[MarketType]:
        """
        Get opposite market types for this market.

        Used for rebote detection - we don't send both sides
        of the same bet.

        Returns:
            List of opposite MarketType values. Empty list if no opposites.

        Reference: Appendix 6.1 in docs/01-SRS.md, legacy/RetadorV6.py line 880

        Examples:
            >>> MarketType.WIN1.get_opposites()
            [<MarketType.WIN2: 'win2'>]
            >>> MarketType._1X.get_opposites()
            [<MarketType._X2: '_x2'>, <MarketType._12: '_12'>]
            >>> MarketType.DRAW.get_opposites()
            []
        """
        return list(_OPPOSITE_MAP.get(self, ()))

    @classmethod
    def from_string(cls, value: str, *, strict: bool = False) -> MarketType:
        """
        Create MarketType from string (case-insensitive).

        Args:
            value: Market type string from API (e.g., "win1", "OVER", "ah1")
            strict: If True, raise InvalidMarketError for unknown markets.
                    If False (default), return UNKNOWN and log a warning.

        Returns:
            Matching MarketType enum value, or UNKNOWN if not found and not strict.

        Raises:
            InvalidMarketError: If value is empty, or if strict=True and no match.

        Examples:
            >>> MarketType.from_string("OVER")
            <MarketType.OVER: 'over'>
            >>> MarketType.from_string("Win1")
            <MarketType.WIN1: 'win1'>
            >>> MarketType.from_string("unknown_xyz")
            <MarketType.UNKNOWN: '__unknown__'>
            >>> MarketType.from_string("unknown_xyz", strict=True)
            InvalidMarketError: Unknown market type: 'unknown_xyz'
        """
        if not value or not value.strip():
            raise InvalidMarketError("Market type cannot be empty")

        normalized = value.lower().strip()

        for member in cls:
            # Skip UNKNOWN when searching - it's a fallback, not a valid match
            if member == cls.UNKNOWN:
                continue
            if member.value == normalized:
                return member

        # Market not found
        if strict:
            raise InvalidMarketError(f"Unknown market type: '{value}'")

        # Log warning so we can detect new markets to add
        logger.warning(
            f"Unknown market type: '{value}' - treating as UNKNOWN. "
            "Consider adding this market to MarketType enum."
        )
        return cls.UNKNOWN

    def has_opposites(self) -> bool:
        """
        Check if this market type has opposing markets.

        Returns:
            True if this market has at least one opposite.

        Examples:
            >>> MarketType.WIN1.has_opposites()
            True
            >>> MarketType.DRAW.has_opposites()
            False
        """
        return bool(_OPPOSITE_MAP.get(self, ()))

    def is_opposite_of(self, other: MarketType) -> bool:
        """
        Check if this market is opposite to another.

        Args:
            other: Another MarketType to check against.

        Returns:
            True if other is in this market's opposites.

        Examples:
            >>> MarketType.WIN1.is_opposite_of(MarketType.WIN2)
            True
            >>> MarketType.WIN1.is_opposite_of(MarketType.OVER)
            False
        """
        return other in self.get_opposites()


# =============================================================================
# OPPOSITE MARKETS MAPPING
# =============================================================================
# This mapping MUST be defined after the MarketType class.
# Using Tuple for immutability; get_opposites() returns a new list.
# Reference: legacy/RetadorV6.py lines 880-893

_OPPOSITE_MAP: Dict[MarketType, Tuple[MarketType, ...]] = {
    # Money line / Match winner (symmetric 1:1)
    MarketType.WIN1: (MarketType.WIN2,),
    MarketType.WIN2: (MarketType.WIN1,),
    # DRAW has no opposite
    # Double chance (multiple opposites)
    MarketType._1X: (MarketType._X2, MarketType._12),
    MarketType._X2: (MarketType._1X, MarketType._12),
    MarketType._12: (MarketType._1X, MarketType._X2),
    # Totals (symmetric 1:1)
    MarketType.OVER: (MarketType.UNDER,),
    MarketType.UNDER: (MarketType.OVER,),
    # E-sports totals (symmetric 1:1)
    MarketType.EOVER: (MarketType.EUNDER,),
    MarketType.EUNDER: (MarketType.EOVER,),
    # Asian handicap (symmetric 1:1)
    MarketType.AH1: (MarketType.AH2,),
    MarketType.AH2: (MarketType.AH1,),
    # Odd/Even (symmetric 1:1)
    MarketType.ODD: (MarketType.EVEN,),
    MarketType.EVEN: (MarketType.ODD,),
    # Yes/No (symmetric 1:1)
    MarketType.YES: (MarketType.NO,),
    MarketType.NO: (MarketType.YES,),
    # Draw no bet (symmetric 1:1)
    MarketType.WIN1RETX: (MarketType.WIN2RETX,),
    MarketType.WIN2RETX: (MarketType.WIN1RETX,),
    # Win only (symmetric 1:1)
    MarketType.WINONLY1: (MarketType.WINONLY2,),
    MarketType.WINONLY2: (MarketType.WINONLY1,),
    # Win to nil (symmetric 1:1)
    MarketType.WIN1TONIL: (MarketType.WIN2TONIL,),
    MarketType.WIN2TONIL: (MarketType.WIN1TONIL,),
    # Clean sheet (symmetric 1:1)
    MarketType.CLEAN_SHEET_1: (MarketType.CLEAN_SHEET_2,),
    MarketType.CLEAN_SHEET_2: (MarketType.CLEAN_SHEET_1,),
    # Qualification (symmetric 1:1)
    MarketType.WIN1_QUALIFY: (MarketType.WIN2_QUALIFY,),
    MarketType.WIN2_QUALIFY: (MarketType.WIN1_QUALIFY,),
    # Between margin (symmetric 1:1)
    MarketType.BETWEENMARGINH1: (MarketType.BETWEENMARGINH2,),
    MarketType.BETWEENMARGINH2: (MarketType.BETWEENMARGINH1,),
}


# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================
# This dictionary is kept for backward compatibility with code that expects
# string-based market type lookups. Prefer MarketType.get_opposites() instead.
#
# DEPRECATED: Use MarketType.get_opposites() method instead.


def _generate_legacy_opposite_markets() -> Dict[str, List[str]]:
    """Generate OPPOSITE_MARKETS dict from enum for consistency."""
    result: Dict[str, List[str]] = {}
    for market, opposites in _OPPOSITE_MAP.items():
        result[market.value] = [opp.value for opp in opposites]
    return result


OPPOSITE_MARKETS: Dict[str, List[str]] = _generate_legacy_opposite_markets()
