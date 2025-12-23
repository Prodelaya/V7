"""Pick entity representing a validated betting pick.

A Pick represents one side of a surebet - the betting recommendation
that will be sent to users. It contains all information needed for:
- Display (teams, odds, market, tournament)
- Deduplication (redis_key, opposite_keys)
- Validation (event_time, bookmaker)

Implementation Requirements:
- Immutable dataclass (frozen=True)
- Contains: teams, odds, market_type, event_time, bookmaker, tournament
- Factory method: Pick.from_api_response(data)
- Redis key generation: pick.redis_key
- Reference to value objects: Odds, MarketType

Reference:
- docs/04-Structure.md: "domain/entities/"
- docs/05-Implementation.md: Task 1.7
- docs/01-SRS.md: RF-004 for Redis key format
- docs/08-API-Documentation.md: API response structure
- legacy/RetadorV6.py: _get_complete_key(), _get_opposite_keys()
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..value_objects.market_type import MarketType
from ..value_objects.odds import Odds


@dataclass(frozen=True)
class Pick:
    """Immutable entity representing a validated betting pick.

    A Pick is one prong (side) of a surebet, containing all the information
    needed to send a betting recommendation to users.

    Attributes:
        teams: Tuple of exactly 2 team names (team1, team2).
        odds: Betting odds as an Odds value object.
        market_type: Type of bet market (over, under, win1, etc.).
        variety: Market variety/condition (e.g., "map", "goals").
        event_time: When the event starts (timezone-aware datetime).
        bookmaker: Bookmaker identifier from API (e.g., "pinnaclesports").
        tournament: Tournament/league name.
        sport_id: Sport identifier from API.
        link: Optional URL to the bet on the bookmaker's website.

    Examples:
        >>> from datetime import datetime, timezone
        >>> from src.domain.value_objects import Odds, MarketType
        >>> pick = Pick(
        ...     teams=("Team A", "Team B"),
        ...     odds=Odds(2.05),
        ...     market_type=MarketType.OVER,
        ...     variety="2.5",
        ...     event_time=datetime.now(timezone.utc),
        ...     bookmaker="pinnaclesports",
        ...     tournament="Premier League",
        ...     sport_id="Football",
        ... )
        >>> pick.redis_key
        'Team A:Team B:...:over:2.5:pinnaclesports'
    """

    teams: Tuple[str, str]
    odds: Odds
    market_type: MarketType
    variety: str
    event_time: datetime
    bookmaker: str
    tournament: str = ""
    sport_id: str = ""
    link: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate Pick data consistency.

        Raises:
            ValueError: If teams is not exactly 2 elements, team names are empty,
                       bookmaker is empty, or event_time is not timezone-aware.
        """
        # Validate teams tuple has exactly 2 elements
        if len(self.teams) != 2:
            raise ValueError(
                f"Pick must have exactly 2 teams, got {len(self.teams)}"
            )

        # Validate team names are not empty
        if not self.teams[0] or not self.teams[0].strip():
            raise ValueError("First team name cannot be empty")
        if not self.teams[1] or not self.teams[1].strip():
            raise ValueError("Second team name cannot be empty")

        # Validate bookmaker is not empty
        if not self.bookmaker or not self.bookmaker.strip():
            raise ValueError("Bookmaker cannot be empty")

        # Validate event_time is timezone-aware
        if self.event_time.tzinfo is None:
            raise ValueError(
                "event_time must be timezone-aware (has tzinfo)"
            )

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> Pick:
        """Create Pick from API response data (a prong).

        Parses the raw API response format and creates a validated Pick entity.
        The API returns timestamps in milliseconds and nested type information.

        Args:
            data: Raw API response dict representing a prong (one side of surebet).
                  Expected fields: teams, value, bk, time, type, tournament, sport_id.
                  See docs/08-API-Documentation.md for full structure.

        Returns:
            Validated Pick entity.

        Raises:
            ValueError: If required fields are missing or invalid.
            InvalidOddsError: If odds value is outside valid range.
            InvalidMarketError: If market type is empty (strict mode only).

        Examples:
            >>> data = {
            ...     "teams": ["Fnatic", "G2"],
            ...     "value": 2.05,
            ...     "bk": "pinnaclesports",
            ...     "time": 1684157400000,
            ...     "type": {"type": "over", "variety": "2.5"},
            ...     "tournament": "BLAST Paris Major",
            ...     "sport_id": "CounterStrike",
            ... }
            >>> pick = Pick.from_api_response(data)
            >>> pick.odds.value
            2.05
        """
        # Extract and validate teams
        teams = data.get("teams", [])
        if not teams or len(teams) != 2:
            raise ValueError(
                f"Expected 2 teams in API response, got {len(teams) if teams else 0}"
            )

        # Create Odds value object (validates internally)
        odds_value = data.get("value")
        if odds_value is None:
            raise ValueError("Missing 'value' (odds) in API response")
        odds = Odds(float(odds_value))

        # Extract market type from nested 'type' object
        type_info = data.get("type", {})
        market_type_str = type_info.get("type", "")
        if not market_type_str:
            raise ValueError("Missing 'type.type' (market type) in API response")
        # Use non-strict mode: unknown markets become UNKNOWN (with warning log)
        market_type = MarketType.from_string(market_type_str, strict=False)

        # Extract variety (can be empty string)
        variety = str(type_info.get("variety", ""))

        # Convert timestamp from milliseconds to datetime
        timestamp_ms = data.get("time")
        if timestamp_ms is None:
            raise ValueError("Missing 'time' (event timestamp) in API response")
        event_time = datetime.fromtimestamp(
            int(timestamp_ms) / 1000,  # Convert ms to seconds
            tz=timezone.utc
        )

        # Extract bookmaker
        bookmaker = data.get("bk", "")
        if not bookmaker:
            raise ValueError("Missing 'bk' (bookmaker) in API response")

        # Extract optional fields
        tournament = data.get("tournament", "")
        sport_id = data.get("sport_id", "")

        # Extract link with priority: stake_nav > view_nav > event_nav
        link = cls._extract_link(data)

        return cls(
            teams=tuple(teams),  # type: ignore[arg-type]
            odds=odds,
            market_type=market_type,
            variety=variety,
            event_time=event_time,
            bookmaker=bookmaker,
            tournament=tournament,
            sport_id=sport_id,
            link=link,
        )

    @staticmethod
    def _extract_link(data: Dict[str, Any]) -> Optional[str]:
        """Extract the most specific link available from API response.

        Priority order: stake_nav > view_nav > event_nav
        Each nav object contains a 'links' array with HTTP request info.

        Args:
            data: Raw API response dict.

        Returns:
            URL string if found, None otherwise.
        """
        for nav_key in ("stake_nav", "view_nav", "event_nav"):
            nav = data.get(nav_key)
            if nav and isinstance(nav, dict):
                links = nav.get("links")
                if links and isinstance(links, list) and len(links) > 0:
                    first_link = links[0]
                    if isinstance(first_link, dict) and "link" in first_link:
                        link_info = first_link["link"]
                        if isinstance(link_info, dict):
                            url = link_info.get("url")
                            if url:
                                return str(url)
        return None

    @property
    def redis_key(self) -> str:
        """Generate unique Redis key for deduplication.

        Format: {team1}:{team2}:{timestamp_ms}:{market}:{variety}:{bookie}

        This key uniquely identifies a pick to prevent sending duplicates.
        The timestamp is in milliseconds to match API format.

        Returns:
            Redis key string.

        Reference:
            - RF-004 in docs/01-SRS.md
            - _get_complete_key() in legacy/RetadorV6.py (line 1012)

        Examples:
            >>> pick.redis_key
            'Fnatic:G2:1684157400000:over:map:pinnaclesports'
        """
        timestamp_ms = self.event_timestamp_ms
        return ":".join([
            self.teams[0],
            self.teams[1],
            str(timestamp_ms),
            self.market_type.value,
            self.variety,
            self.bookmaker,
        ])

    def get_opposite_keys(self) -> List[str]:
        """Generate Redis keys for opposite market picks.

        Used to prevent sending both sides of the same bet ("rebote").
        For example, if we send OVER, we shouldn't also send UNDER
        for the same event.

        Returns:
            List of Redis keys for opposite markets.
            Empty list if market has no opposites.

        Reference:
            - _get_opposite_keys() in legacy/RetadorV6.py (line 1053)
            - Appendix 6.1 in docs/01-SRS.md

        Examples:
            >>> pick = Pick(..., market_type=MarketType.OVER, ...)
            >>> pick.get_opposite_keys()
            ['Team A:Team B:1234567890:under:2.5:bookie']
        """
        opposite_types = self.market_type.get_opposites()

        if not opposite_types:
            return []

        timestamp_ms = self.event_timestamp_ms
        base = f"{self.teams[0]}:{self.teams[1]}:{timestamp_ms}"

        return [
            f"{base}:{opp.value}:{self.variety}:{self.bookmaker}"
            for opp in opposite_types
        ]

    @property
    def event_timestamp_ms(self) -> int:
        """Get event timestamp in milliseconds (API format).

        Returns:
            Event time as Unix timestamp in milliseconds.
        """
        return int(self.event_time.timestamp() * 1000)

    @property
    def is_future_event(self) -> bool:
        """Check if the event has not started yet.

        Returns:
            True if event_time is in the future.
        """
        return self.event_time > datetime.now(timezone.utc)

    def seconds_until_event(self) -> float:
        """Calculate seconds until the event starts.

        Returns:
            Seconds until event. Negative if event has already started.
        """
        return (self.event_time - datetime.now(timezone.utc)).total_seconds()

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"Pick({self.teams[0]} vs {self.teams[1]}, "
            f"{self.market_type.value} @ {self.odds}, "
            f"{self.bookmaker})"
        )

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"Pick(teams={self.teams!r}, odds={self.odds!r}, "
            f"market_type={self.market_type!r}, variety={self.variety!r}, "
            f"event_time={self.event_time!r}, bookmaker={self.bookmaker!r}, "
            f"tournament={self.tournament!r}, sport_id={self.sport_id!r}, "
            f"link={self.link!r})"
        )
