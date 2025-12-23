"""Surebet entity representing an arbitrage opportunity.

A Surebet represents an arbitrage opportunity between two bookmakers:
- prong_sharp: The side at a sharp bookmaker (e.g., Pinnacle) used as reference
- prong_soft: The side at a soft bookmaker (e.g., Retabet) where we place bets

The sharp bookmaker provides the reference odds, and the soft bookmaker
is our target where picks are sent to users.

Implementation Requirements:
- Contains two prongs: sharp (Pinnacle) and soft (target bookmaker)
- Calculates profit from the two prongs
- Determines which prong is sharp vs soft based on bookmaker hierarchy
- Immutable dataclass (frozen=True)
- Factory method: Surebet.from_api_response(data)
- Conversion to Pick: surebet.to_pick()

Reference:
- docs/04-Structure.md: "domain/entities/"
- docs/05-Implementation.md: Task 1.8
- docs/01-SRS.md: Section 2.2 (Business Model)
- docs/02-PDR.md: Section 3.1.2 (Entities)
- legacy/RetadorV6.py: determine_bet_roles()
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, FrozenSet, Optional, Tuple

from ..value_objects.odds import Odds
from ..value_objects.profit import Profit
from .pick import Pick


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DOMAIN CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Bookmakers classified as "sharp" (reference bookmakers)
# Sharp bookmakers have the most accurate odds and are used as counterparty
# Reference: legacy/RetadorV6.py BOOKIE_HIERARCHY
#
# TODO(Fase 4): Esta constante será reemplazada por configuración desde .env
# En Fase 4, Settings.SHARP_BOOKMAKERS se inyectará en from_api_response()
# Ver: docs/09-Bookmakers-Configuration.md para el diseño detallado
#
SHARP_BOOKMAKERS: FrozenSet[str] = frozenset({
    "pinnaclesports",
    # bet365 can act as sharp in some contexts but is commented out
    # to match current production behavior
})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUREBET ENTITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass(frozen=True)
class Surebet:
    """Immutable entity representing a surebet (arbitrage opportunity).

    A surebet consists of two prongs (betting sides):
    - prong_sharp: The side at the sharp bookmaker (reference, e.g., Pinnacle)
    - prong_soft: The side at the soft bookmaker (target, e.g., Retabet)

    The profit comes from the odds difference between the two bookmakers,
    allowing guaranteed profit regardless of the match outcome.

    Attributes:
        prong_sharp: Pick at the sharp bookmaker (reference odds).
        prong_soft: Pick at the soft bookmaker (where we place bets).
        profit: Profit percentage as a Profit value object.
        surebet_id: Optional unique identifier from the API.
        created: Optional timestamp when the surebet was created in the API.

    Examples:
        >>> from datetime import datetime, timezone
        >>> from src.domain.value_objects import Odds, MarketType
        >>> sharp_pick = Pick(
        ...     teams=("Team A", "Team B"),
        ...     odds=Odds(2.10),
        ...     market_type=MarketType.OVER,
        ...     variety="2.5",
        ...     event_time=datetime.now(timezone.utc),
        ...     bookmaker="pinnaclesports",
        ... )
        >>> soft_pick = Pick(
        ...     teams=("Team A", "Team B"),
        ...     odds=Odds(2.05),
        ...     market_type=MarketType.UNDER,
        ...     variety="2.5",
        ...     event_time=datetime.now(timezone.utc),
        ...     bookmaker="retabet_apuestas",
        ... )
        >>> surebet = Surebet(
        ...     prong_sharp=sharp_pick,
        ...     prong_soft=soft_pick,
        ...     profit=Profit(2.5),
        ... )
        >>> surebet.is_profitable
        True
    """

    prong_sharp: Pick
    prong_soft: Pick
    profit: Profit
    surebet_id: Optional[int] = None
    created: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate Surebet data consistency.

        Note:
            Sharp bookmaker validation is performed in from_api_response()
            using the configured sharp_bookmakers set. For direct construction,
            the caller is responsible for providing correct sharp/soft prongs.

        Raises:
            ValueError: If prong_sharp and prong_soft are from the same bookmaker,
                       or if created is not timezone-aware.
        """
        # Validate that prong_sharp and prong_soft are from different bookmakers
        if self.prong_sharp.bookmaker == self.prong_soft.bookmaker:
            raise ValueError(
                f"prong_sharp and prong_soft cannot be from the same bookmaker: "
                f"'{self.prong_sharp.bookmaker}'"
            )

        # Validate created has timezone if provided
        if self.created is not None and self.created.tzinfo is None:
            raise ValueError("created must be timezone-aware (has tzinfo)")

    @classmethod
    def from_api_response(
        cls,
        data: Dict[str, Any],
        sharp_bookmakers: Optional[FrozenSet[str]] = None,
    ) -> Surebet:
        """Create Surebet from API response.

        Parses the raw API response and determines which prong is sharp
        and which is soft based on the bookmaker hierarchy.

        Args:
            data: Raw API response dict with 'prongs' array and 'profit'.
                  Expected structure from docs/08-API-Documentation.md.
            sharp_bookmakers: Optional set of sharp bookmaker names.
                            Defaults to SHARP_BOOKMAKERS module constant.

        Returns:
            Surebet entity with properly assigned prongs.

        Raises:
            ValueError: If required fields are missing, if prongs count
                       is not 2, or if no sharp bookmaker is found.

        Examples:
            >>> data = {
            ...     "id": 785141488,
            ...     "profit": 2.5,
            ...     "prongs": [
            ...         {"bk": "pinnaclesports", "value": 2.10, ...},
            ...         {"bk": "retabet_apuestas", "value": 2.05, ...},
            ...     ]
            ... }
            >>> surebet = Surebet.from_api_response(data)
            >>> surebet.sharp_bookmaker
            'pinnaclesports'
        """
        if sharp_bookmakers is None:
            sharp_bookmakers = SHARP_BOOKMAKERS

        # Validate prongs structure
        prongs = data.get("prongs", [])
        if not prongs or len(prongs) != 2:
            raise ValueError(
                f"Expected exactly 2 prongs in API response, "
                f"got {len(prongs) if prongs else 0}"
            )

        # Validate profit exists
        profit_value = data.get("profit")
        if profit_value is None:
            raise ValueError("Missing 'profit' in API response")

        # Create Pick entities from prongs
        pick1 = Pick.from_api_response(prongs[0])
        pick2 = Pick.from_api_response(prongs[1])

        # Determine roles: which is sharp, which is soft
        if pick1.bookmaker in sharp_bookmakers:
            prong_sharp, prong_soft = pick1, pick2
        elif pick2.bookmaker in sharp_bookmakers:
            prong_sharp, prong_soft = pick2, pick1
        else:
            raise ValueError(
                f"No sharp bookmaker found in prongs. "
                f"Bookmakers: {pick1.bookmaker}, {pick2.bookmaker}. "
                f"Expected one of: {sorted(sharp_bookmakers)}"
            )

        # Validate soft prong is not a sharp
        if prong_soft.bookmaker in sharp_bookmakers:
            raise ValueError(
                f"Both prongs are from sharp bookmakers: "
                f"{pick1.bookmaker}, {pick2.bookmaker}"
            )

        # Create Profit value object
        profit = Profit(float(profit_value))

        # Extract optional metadata
        surebet_id = data.get("id")

        created = None
        created_ms = data.get("created")
        if created_ms is not None:
            created = datetime.fromtimestamp(
                int(created_ms) / 1000,
                tz=timezone.utc,
            )

        return cls(
            prong_sharp=prong_sharp,
            prong_soft=prong_soft,
            profit=profit,
            surebet_id=surebet_id,
            created=created,
        )

    def to_pick(self) -> Pick:
        """Convert to Pick entity (the soft prong becomes the pick).

        The soft prong is the side where we actually place bets and send
        recommendations to users.

        Returns:
            Pick entity for the soft side.

        Examples:
            >>> pick = surebet.to_pick()
            >>> pick.bookmaker
            'retabet_apuestas'
        """
        return self.prong_soft

    # -------------------------------------------------------------------------
    # Convenience Properties
    # -------------------------------------------------------------------------

    @property
    def sharp_odds(self) -> Odds:
        """Get odds from the sharp bookmaker.

        Returns:
            Odds value object from prong_sharp.
        """
        return self.prong_sharp.odds

    @property
    def soft_odds(self) -> Odds:
        """Get odds from the soft bookmaker.

        Returns:
            Odds value object from prong_soft.
        """
        return self.prong_soft.odds

    @property
    def sharp_bookmaker(self) -> str:
        """Get the sharp bookmaker name.

        Returns:
            Bookmaker identifier (e.g., "pinnaclesports").
        """
        return self.prong_sharp.bookmaker

    @property
    def soft_bookmaker(self) -> str:
        """Get the soft bookmaker name.

        Returns:
            Bookmaker identifier (e.g., "retabet_apuestas").
        """
        return self.prong_soft.bookmaker

    @property
    def teams(self) -> Tuple[str, str]:
        """Get the team names from the soft prong.

        Returns:
            Tuple of (team1, team2) names.
        """
        return self.prong_soft.teams

    @property
    def event_time(self) -> datetime:
        """Get the event start time from the soft prong.

        Returns:
            Timezone-aware datetime of the event.
        """
        return self.prong_soft.event_time

    @property
    def tournament(self) -> str:
        """Get the tournament name from the soft prong.

        Returns:
            Tournament/league name.
        """
        return self.prong_soft.tournament

    @property
    def sport_id(self) -> str:
        """Get the sport identifier from the soft prong.

        Returns:
            Sport ID (e.g., "Football", "CounterStrike").
        """
        return self.prong_soft.sport_id

    @property
    def is_profitable(self) -> bool:
        """Check if the surebet has positive profit.

        Returns:
            True if profit > 0.
        """
        return self.profit.value > 0

    @property
    def is_acceptable(self) -> bool:
        """Check if the surebet profit is within acceptable trading range.

        This delegates to Profit.is_acceptable() which checks against
        business rules (typically -1% to 25%).

        Returns:
            True if profit is within acceptable range.
        """
        return self.profit.is_acceptable()

    @property
    def redis_key(self) -> str:
        """Get Redis key for deduplication (delegated to soft prong).

        The soft prong's redis_key is used because that's the pick
        we're actually sending to users.

        Returns:
            Redis key string for deduplication.
        """
        return self.prong_soft.redis_key

    def get_opposite_keys(self) -> list:
        """Get Redis keys for opposite market picks (delegated to soft prong).

        Returns:
            List of Redis keys for opposite markets.
        """
        return self.prong_soft.get_opposite_keys()

    # -------------------------------------------------------------------------
    # String Representations
    # -------------------------------------------------------------------------

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"Surebet({self.teams[0]} vs {self.teams[1]}, "
            f"{self.sharp_bookmaker} vs {self.soft_bookmaker}, "
            f"profit={self.profit})"
        )

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"Surebet("
            f"prong_sharp={self.prong_sharp!r}, "
            f"prong_soft={self.prong_soft!r}, "
            f"profit={self.profit!r}, "
            f"surebet_id={self.surebet_id!r}, "
            f"created={self.created!r})"
        )
