"""Message formatter with HTML cache.

Implementation Requirements:
- Format pick to HTML for Telegram
- Cache static parts (teams, tournament, date)
- Dynamic parts: stake emoji, odds, min_odds
- Escape HTML special characters

Reference:
- docs/05-Implementation.md: Task 5.7
- docs/02-PDR.md: Section 3.3.3 (Message Formatter)
- docs/03-ADRs.md: ADR-011 (Cache HTML)
- docs/01-SRS.md: RF-007

TODO: Implement MessageFormatter
"""

import html
from typing import Optional


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

    Cache key: {team1}:{team2}:{timestamp}:{bookie}
    Cache TTL: 60 seconds

    TODO: Implement based on:
    - Task 5.7 in docs/05-Implementation.md
    - ADR-011 in docs/03-ADRs.md
    - RF-007 in docs/01-SRS.md
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
    }

    def __init__(self, calculation_service=None):
        """
        Initialize formatter.

        Args:
            calculation_service: Service for stake/min_odds calculations
        """
        self._calculation_service = calculation_service
        self._cache = {}  # {cache_key: (timestamp, parts_dict)}

    async def format(self, pick) -> str:
        """
        Format pick to HTML message.

        Uses cache for static parts.

        Args:
            pick: Pick entity

        Returns:
            Formatted HTML string
        """
        raise NotImplementedError("MessageFormatter.format not implemented")

    def _get_cache_key(self, pick) -> str:
        """Generate cache key from pick data."""
        raise NotImplementedError("MessageFormatter._get_cache_key not implemented")

    def _get_cached_parts(self, key: str) -> Optional[dict]:
        """Get cached static parts if not expired."""
        raise NotImplementedError("MessageFormatter._get_cached_parts not implemented")

    def _cache_parts(self, key: str, parts: dict) -> None:
        """Cache static parts with timestamp."""
        raise NotImplementedError("MessageFormatter._cache_parts not implemented")

    def _format_teams(self, pick) -> str:
        """Format team names with sport emoji."""
        raise NotImplementedError("MessageFormatter._format_teams not implemented")

    def _format_tournament(self, pick) -> str:
        """Format tournament and sport."""
        raise NotImplementedError("MessageFormatter._format_tournament not implemented")

    def _format_date(self, timestamp: int) -> str:
        """Format event date/time in Spain timezone."""
        raise NotImplementedError("MessageFormatter._format_date not implemented")

    def _format_type_info(self, pick) -> str:
        """Format market type, condition, variety."""
        raise NotImplementedError("MessageFormatter._format_type_info not implemented")

    def _clean_text(self, text: str) -> str:
        """Clean and escape text for HTML."""
        raise NotImplementedError("MessageFormatter._clean_text not implemented")

    def _safe_escape(self, text) -> str:
        """Safely escape HTML special characters."""
        if text is None:
            return ""
        return html.escape(str(text).strip(), quote=False)

    def _adjust_domain(self, url: str) -> str:
        """
        Adjust bookmaker URL domains.

        - bet365.com -> bet365.es
        - betway.com/en -> betway.es/es
        - Etc.

        Reference: ajustar_dominio() in legacy V6 (line 1319)
        """
        raise NotImplementedError("MessageFormatter._adjust_domain not implemented")
