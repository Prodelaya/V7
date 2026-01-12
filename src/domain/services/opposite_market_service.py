"""Opposite market service for rebote detection.

Service for resolving opposite betting markets and generating Redis keys
for deduplication. Provides a string-based interface that delegates to
the MarketType enum for the actual opposite market lookup.

Implementation Notes:
- Wraps MarketType.get_opposites() with a string-based interface
- Used by code that doesn't work directly with MarketType enum
- Consistent with legacy get_market_opposites() interface

Reference:
- docs/04-Structure.md: "domain/services/"
- docs/05-Implementation.md: Task 6.3
- docs/01-SRS.md: RF-004, Appendix 6.1
- legacy/RetadorV6.py: opposite_markets (line 880), get_market_opposites (line 1029)
"""

from typing import List

from ..value_objects.market_type import MarketType


class OppositeMarketService:
    """
    Service for resolving opposite betting markets.

    Used to detect "rebotes" (bounces) where the opposite market
    was already sent, indicating odds movement we should avoid.

    This service provides a string-based interface for opposite market
    resolution, delegating to MarketType.get_opposites() internally.

    Opposite markets (from docs/01-SRS.md Appendix 6.1):
        | Market   | Opposite(s)     |
        |----------|-----------------|
        | win1     | win2            |
        | over     | under           |
        | ah1      | ah2             |
        | odd      | even            |
        | yes      | no              |
        | _1x      | _x2, _12        |

    Example:
        >>> service = OppositeMarketService()
        >>> service.get_opposites("over")
        ['under']
        >>> service.get_opposites("_1x")
        ['_x2', '_12']
        >>> service.get_opposite_keys("TeamA:TeamB:1234567890:2.5", "over", "bookie")
        ['TeamA:TeamB:1234567890:2.5:under:bookie']
    """

    def get_opposites(self, market_type: str) -> List[str]:
        """
        Get opposite market types for a given market.

        Converts the string to MarketType enum and delegates to
        MarketType.get_opposites(). Case-insensitive.

        Args:
            market_type: Market type string (e.g., "over", "win1", "OVER")

        Returns:
            List of opposite market type strings.
            Empty list if market has no opposites or is unknown.

        Examples:
            >>> service = OppositeMarketService()
            >>> service.get_opposites("over")
            ['under']
            >>> service.get_opposites("win1")
            ['win2']
            >>> service.get_opposites("_1x")
            ['_x2', '_12']
            >>> service.get_opposites("draw")  # No opposite
            []
            >>> service.get_opposites("unknown_xyz")  # Unknown market
            []

        Reference:
            - MarketType.get_opposites() in domain/value_objects/market_type.py
            - get_market_opposites() in legacy/RetadorV6.py (line 1029)
        """
        # Convert string to MarketType enum (non-strict: unknown → UNKNOWN)
        market_enum = MarketType.from_string(market_type, strict=False)

        # Get opposites as enum list
        opposite_enums = market_enum.get_opposites()

        # Convert back to strings
        return [opp.value for opp in opposite_enums]

    def get_opposite_keys(
        self, base_key: str, market_type: str, bookmaker: str
    ) -> List[str]:
        """
        Generate Redis keys for opposite markets.

        Used to check if opposite market was already sent (rebote detection).
        The base_key should contain everything except market and bookmaker.

        Args:
            base_key: Base key (team1:team2:timestamp:variety) - without market/bookie
            market_type: Current market type (e.g., "over", "win1")
            bookmaker: Target bookmaker identifier

        Returns:
            List of Redis keys for opposite markets.
            Empty list if market has no opposites.

        Key format: {base_key}:{opposite_market}:{bookmaker}

        Examples:
            >>> service = OppositeMarketService()
            >>> service.get_opposite_keys("TeamA:TeamB:1234567890:2.5", "over", "bookie")
            ['TeamA:TeamB:1234567890:2.5:under:bookie']
            >>> service.get_opposite_keys("TeamA:TeamB:1234567890:", "_1x", "pinnacle")
            ['TeamA:TeamB:1234567890::_x2:pinnacle', 'TeamA:TeamB:1234567890::_12:pinnacle']

        Reference:
            - _get_opposite_keys() in legacy/RetadorV6.py (line 1053)
            - Pick.get_opposite_keys() in domain/entities/pick.py
        """
        opposite_types = self.get_opposites(market_type)

        if not opposite_types:
            return []

        # Generate keys: base_key + opposite_market + bookmaker
        return [f"{base_key}:{opp}:{bookmaker}" for opp in opposite_types]
