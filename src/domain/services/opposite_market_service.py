"""Opposite market service for rebote detection.

Implementation Requirements:
- Map each market to its opposite(s)
- Used to prevent sending both sides of same bet
- Generate opposite Redis keys for deduplication

Reference:
- docs/04-Structure.md: "domain/services/"
- docs/05-Implementation.md: Task 6.3
- docs/01-SRS.md: RF-004, Appendix 6.1
- legacy/RetadorV6.py: opposite_markets (line 880), get_market_opposites (line 1029)

TODO: Implement OppositeMarketService
"""

from typing import List


class OppositeMarketService:
    """
    Service for resolving opposite betting markets.

    Used to detect "rebotes" (bounces) where the opposite market
    was already sent, indicating odds movement we should avoid.

    Opposite markets (from docs/01-SRS.md Appendix 6.1):
        | Market   | Opposite(s)     |
        |----------|-----------------|
        | win1     | win2            |
        | over     | under           |
        | ah1      | ah2             |
        | odd      | even            |
        | yes      | no              |
        | _1x      | _x2, _12        |

    TODO: Implement based on:
    - Task 6.3 in docs/05-Implementation.md
    - Appendix 6.1 in docs/01-SRS.md
    - get_market_opposites() in legacy/RetadorV6.py (line 1029)
    """

    # Mapping from market type to its opposites
    # Reference: legacy/RetadorV6.py line 880
    OPPOSITE_MARKETS = {
        "ah1": "ah2",
        "ah2": "ah1",
        "win1": "win2",
        "win2": "win1",
        "winonly1": "winonly2",
        "winonly2": "winonly1",
        "win1retx": "win2retx",
        "win2retx": "win1retx",
        "over": "under",
        "under": "over",
        "eover": "e_under",
        "e_under": "eover",
        "even": "odd",
        "odd": "even",
        "win1tonil": "win2tonil",
        "win2tonil": "win1tonil",
        "clean_sheet_1": "clean_sheet_2",
        "clean_sheet_2": "clean_sheet_1",
        "_1x": ["_x2", "_12"],
        "_x2": ["_1x", "_12"],
        "_12": ["_1x", "_x2"],
        "win1 qualify": "win2 qualify",
        "BETWEENMARGINH1": "BETWEENMARGINH2",
    }

    def get_opposites(self, market_type: str) -> List[str]:
        """
        Get opposite market types for a given market.

        Args:
            market_type: Market type string (e.g., "over", "win1")

        Returns:
            List of opposite market type strings

        Example:
            >>> service = OppositeMarketService()
            >>> service.get_opposites("over")
            ["under"]
            >>> service.get_opposites("_1x")
            ["_x2", "_12"]
        """
        raise NotImplementedError("OppositeMarketService.get_opposites not implemented")

    def get_opposite_keys(
        self, base_key: str, market_type: str, bookmaker: str
    ) -> List[str]:
        """
        Generate Redis keys for opposite markets.

        Used to check if opposite market was already sent.

        Args:
            base_key: Base key without market (team1:team2:timestamp)
            market_type: Current market type
            bookmaker: Target bookmaker

        Returns:
            List of Redis keys for opposite markets

        Reference: _get_opposite_keys() in legacy/RetadorV6.py (line 1053)
        """
        raise NotImplementedError(
            "OppositeMarketService.get_opposite_keys not implemented"
        )
