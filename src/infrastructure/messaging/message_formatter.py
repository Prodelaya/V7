"""Message formatter with HTML cache.

Implementation Requirements:
- Format pick to HTML for Telegram
- Cache static parts (teams, tournament, date)
- Dynamic parts: stake emoji, odds, min_odds
- Escape HTML special characters

Reference:
- docs/05-Implementation.md: Task 5C.1
- docs/02-PDR.md: Section 3.3.3 (Message Formatter)
- docs/03-ADRs.md: ADR-011 (Cache HTML)
- docs/01-SRS.md: RF-007, RF-010
"""

import html
import re
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

import pytz

if TYPE_CHECKING:
    from src.domain.entities.pick import Pick
    from src.domain.services.calculation_service import CalculationService


class MessageFormatter:
    """
    Formatter for Telegram messages with HTML cache.

    Caches static parts that don't change per event:
    - teams
    - tournament
    - date

    Computes dynamic parts per pick:
    - stake emoji (based on profit)
    - odds
    - min_odds

    Cache key: {team1}:{team2}:{timestamp_ms}:{bookie}
    Cache TTL: 60 seconds

    Reference:
    - ADR-011 in docs/03-ADRs.md
    - RF-007, RF-010 in docs/01-SRS.md
    - MessageFormatter in legacy/RetadorV6.py (line 1138)
    """

    CACHE_TTL = 60  # seconds

    # Message template (from legacy V6)
    MESSAGE_TEMPLATE = (
        "<b>{stake} {type_info} @{odds} (🔻{min_odds})</b>\n\n"
        "{teams}\n"
        "{tournament}\n"
        "{date}\n\n"
        "{link}"
    )

    # Sport emojis
    SPORT_EMOJIS = {
        'football': '⚽️',
        'basketball': '🏀',
        'americanfootball': '🏈',
        'rugby': '🏉',
        'hockey': '🏑',
        'tennis': '🎾',
        'tabletennis': '🏓',
        'handball': '🤾🏼‍♂️',
        'baseball': '⚾️',
        'volleyball': '🏐',
        'e_football': '🎮',
        'darts': '🎯',
        'counterstrike': '🎮',
        'esports': '🎮',
    }

    # Days in Spanish
    DAYS_ES = {
        0: 'Lunes',
        1: 'Martes',
        2: 'Miércoles',
        3: 'Jueves',
        4: 'Viernes',
        5: 'Sábado',
        6: 'Domingo',
    }

    # Market type replacements
    MARKET_REPLACEMENTS = {
        'win1retx': 'DNB1',
        'win2retx': 'DNB2',
        'winonly1': 'WIN1',
        'winonly2': 'WIN2',
        'win1': 'WIN1',
        'win2': 'WIN2',
        '_1x': '1X',
        '_x2': 'X2',
        '_12': '12',
        'e_over': 'E OVER',
        'e_under': 'E UNDER',
    }

    # Words to remove from type info
    WORDS_TO_REMOVE = {
        'point', 'points', 'overall', 'regular', 'overtime',
        'goal', 'goals', 'regulartime', 'set', 'time', 'total',
        'game', 'games', 'match', 'matches',
        '(second_yellow_is_yellow_and_red_card)',
    }

    def __init__(
        self,
        calculation_service: Optional["CalculationService"] = None
    ) -> None:
        """
        Initialize formatter.

        Args:
            calculation_service: Service for stake/min_odds calculations.
                               If None, stake/min_odds must be passed to format().
        """
        self._calculation_service = calculation_service
        self._cache: dict[str, tuple[float, dict]] = {}
        self._spain_tz = pytz.timezone("Europe/Madrid")

    async def format(
        self,
        pick: "Pick",
        sharp_odds: Optional[float] = None,
        profit: Optional[float] = None,
        sharp_bookmaker: str = "pinnaclesports",
    ) -> str:
        """
        Format pick to HTML message.

        Uses cache for static parts (teams, tournament, date).
        Dynamic parts (stake, odds, min_odds) are computed fresh.

        Args:
            pick: Pick entity to format
            sharp_odds: Odds from sharp bookmaker (for min_odds calculation)
            profit: Surebet profit percentage (for stake calculation)
            sharp_bookmaker: Name of sharp bookmaker

        Returns:
            Formatted HTML string ready for Telegram

        Raises:
            ValueError: If calculation_service is None and stake/min_odds
                       cannot be computed
        """
        # 1. Generate cache key
        cache_key = self._get_cache_key(pick)

        # 2. Try to get cached static parts
        cached = self._get_cached_parts(cache_key)

        if cached:
            teams = cached['teams']
            tournament = cached['tournament']
            date = cached['date']
        else:
            # 3. Format static parts
            teams = self._format_teams(pick)
            tournament = self._format_tournament(pick)
            date = self._format_date(pick.event_timestamp_ms)

            # 4. Cache for next time
            self._cache_parts(cache_key, {
                'teams': teams,
                'tournament': tournament,
                'date': date,
            })

        # 5. Format dynamic parts (NOT cached)
        type_info = self._format_type_info(pick)

        # 6. Calculate stake and min_odds
        stake_emoji = ""
        min_odds_value = 0.0

        if self._calculation_service and profit is not None:
            stake_result = self._calculation_service.calculate_stake(
                profit, sharp_bookmaker
            )
            if stake_result:
                stake_emoji = stake_result.emoji
            else:
                # Rejected by calculator - return empty to skip this pick
                return ""

        if self._calculation_service and sharp_odds is not None:
            min_odds_result = self._calculation_service.calculate_min_odds(
                sharp_odds, sharp_bookmaker
            )
            min_odds_value = min_odds_result.min_odds

        # 7. Adjust URL domain (RF-010)
        link_url = self._adjust_domain(pick.link or "")
        link_html = ""
        if link_url:
            escaped_url = html.escape(link_url, quote=True)
            display_url = html.escape(link_url, quote=False)
            link_html = f'🔗 <a href="{escaped_url}">{display_url}</a>'

        # 8. Build final message using MESSAGE_TEMPLATE
        return self.MESSAGE_TEMPLATE.format(
            stake=self._safe_escape(stake_emoji),
            type_info=self._safe_escape(type_info),
            odds=self._safe_escape(str(pick.odds.value)),
            min_odds=self._safe_escape(str(min_odds_value)),
            teams=teams,
            tournament=tournament,
            date=date,
            link=link_html,
        )

    def _get_cache_key(self, pick: "Pick") -> str:
        """
        Generate cache key from pick data.

        Format: {team1}:{team2}:{timestamp_ms}:{bookie}

        Args:
            pick: Pick entity

        Returns:
            Cache key string
        """
        return ":".join([
            pick.teams[0],
            pick.teams[1],
            str(pick.event_timestamp_ms),
            pick.bookmaker,
        ])

    def _get_cached_parts(self, key: str) -> Optional[dict]:
        """
        Get cached static parts if not expired.

        Args:
            key: Cache key

        Returns:
            Dict with teams, tournament, date if valid cache hit,
            None if expired or not found
        """
        if key not in self._cache:
            return None

        cached_time, parts = self._cache[key]
        current_time = time.time()

        if current_time - cached_time > self.CACHE_TTL:
            # Expired - remove from cache
            del self._cache[key]
            return None

        return parts

    def _cache_parts(self, key: str, parts: dict) -> None:
        """
        Cache static parts with timestamp.

        Args:
            key: Cache key
            parts: Dict with teams, tournament, date
        """
        current_time = time.time()
        self._cache[key] = (current_time, parts)

        # Cleanup: remove expired entries (limit to avoid memory leak)
        self._cleanup_expired_cache()

    def _cleanup_expired_cache(self) -> None:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            k for k, (cached_time, _) in self._cache.items()
            if current_time - cached_time > self.CACHE_TTL
        ]
        for k in expired_keys:
            del self._cache[k]

    def _format_teams(self, pick: "Pick") -> str:
        """
        Format team names with sport emoji.

        Format: "{sport_emoji} <code>{team1}</code> vs <code>{team2}</code>"

        Args:
            pick: Pick entity

        Returns:
            Formatted teams HTML string
        """
        sport_key = pick.sport_id.lower() if pick.sport_id else ""
        emoji = self.SPORT_EMOJIS.get(sport_key, "")

        team1 = self._safe_escape(pick.teams[0]).title()
        team2 = self._safe_escape(pick.teams[1]).title()

        return f"{emoji} <code>{team1}</code> vs <code>{team2}</code>"

    def _format_tournament(self, pick: "Pick") -> str:
        """
        Format tournament and sport.

        Format: "🏆 {tournament} ({sport_id})"

        Args:
            pick: Pick entity

        Returns:
            Formatted tournament HTML string
        """
        tournament = self._clean_text(pick.tournament).title()
        sport = self._clean_text(pick.sport_id).title()

        return f"🏆 {tournament} ({sport})"

    def _format_date(self, timestamp_ms: int) -> str:
        """
        Format event date/time in Spain timezone.

        Format: "📅 {dd/mm/yyyy} ({día} {HH:MM})"

        Args:
            timestamp_ms: Event timestamp in milliseconds

        Returns:
            Formatted date HTML string
        """
        if not timestamp_ms:
            return ""

        try:
            # Convert milliseconds to seconds
            timestamp_s = timestamp_ms / 1000

            # Create UTC datetime
            event_time_utc = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)

            # Convert to Spain timezone
            event_time_spain = event_time_utc.astimezone(self._spain_tz)

            # Format components
            fecha = event_time_spain.strftime('%d/%m/%Y')
            hora = event_time_spain.strftime('%H:%M')
            dia = self.DAYS_ES.get(event_time_spain.weekday(), "")

            return f"📅 {fecha} ({dia} {hora})"

        except (ValueError, OSError, OverflowError):
            return ""

    def _format_type_info(self, pick: "Pick") -> str:
        """
        Format market type, variety.

        Applies replacements and removes filler words.
        Returns UPPERCASE.

        Args:
            pick: Pick entity

        Returns:
            Formatted type info string in uppercase
        """
        parts = []

        # Add market type
        market_type = pick.market_type.value if pick.market_type else ""
        if market_type:
            cleaned = self._clean_text(market_type)
            if cleaned:
                parts.append(cleaned)

        # Add variety
        if pick.variety:
            cleaned_variety = self._clean_text(pick.variety)
            if cleaned_variety:
                parts.append(cleaned_variety)

        # Combine and uppercase
        result = ' '.join(parts).upper()

        # Apply market replacements after joining
        for old, new in self.MARKET_REPLACEMENTS.items():
            result = result.replace(old.upper(), new)

        return result

    def _clean_text(self, text: str) -> str:
        """
        Clean and escape text for HTML.

        - Removes words from WORDS_TO_REMOVE
        - Applies replacements
        - Escapes HTML special characters
        - Normalizes whitespace

        Args:
            text: Raw text to clean

        Returns:
            Cleaned and escaped text
        """
        if not text:
            return ""

        # Convert to lowercase and strip
        result = str(text).strip().lower()

        # Remove unwanted words
        words_pattern = '|'.join(re.escape(w) for w in self.WORDS_TO_REMOVE)
        pattern = rf'\b({words_pattern})\b'
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        # Apply replacements
        for old, new in self.MARKET_REPLACEMENTS.items():
            result = result.replace(old.lower(), new.lower())

        # Normalize whitespace
        result = ' '.join(result.split())

        # Escape HTML
        return html.escape(result, quote=False)

    def _safe_escape(self, text: Optional[str]) -> str:
        """
        Safely escape HTML special characters.

        Args:
            text: Text to escape (can be None)

        Returns:
            Escaped text, or empty string if None
        """
        if text is None:
            return ""
        return html.escape(str(text).strip(), quote=False)

    def _adjust_domain(self, url: str) -> str:
        """
        Adjust bookmaker URL domains for Spanish market (RF-010).

        Transformations:
        - bet365.com -> bet365.es (path in UPPERCASE)
        - betway.com/en -> betway.es/es
        - bwin.com/en -> bwin.es/es
        - pokerstars.uk -> pokerstars.es
        - sportswidget.versus.es -> www.versus.es/apuestas

        Args:
            url: Original bookmaker URL

        Returns:
            Adjusted URL for Spanish market

        Reference:
            ajustar_dominio() in legacy/RetadorV6.py (line 1319)
        """
        if not url:
            return ""

        # Bet365: .com -> .es and path to UPPERCASE
        if "bet365" in url:
            url = url.replace("bet365.com", "bet365.es")
            # Split by .es to separate domain from path
            parts = url.split(".es", 1)
            if len(parts) > 1:
                domain = parts[0]
                path = parts[1]
                return f"{domain}.es{path.upper()}"
            return url

        # Betway: .com/en -> .es/es
        if "betway" in url:
            url = url.replace(
                "sports.betway.com/en/sports",
                "sports.betway.es/es/sports"
            )
            return url

        # Bwin: .com/en -> .es/es
        if "bwin" in url:
            url = url.replace(
                "sports.bwin.com/en/",
                "sports.bwin.es/es/"
            )
            return url

        # Versus with sportswidget
        if "sportswidget.versus.es" in url:
            url = url.replace(
                "sportswidget.versus.es/sports",
                "www.versus.es/apuestas/sports"
            )
            return url

        # Versus without sportswidget
        if "versus.es/sports" in url and "www." not in url:
            url = url.replace(
                "versus.es/sports",
                "www.versus.es/apuestas/sports"
            )
            return url

        # PokerStars: .uk -> .es
        if "pokerstars" in url:
            url = url.replace("pokerstars.uk/", "pokerstars.es/")
            return url

        return url

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        """Return current cache size."""
        return len(self._cache)
