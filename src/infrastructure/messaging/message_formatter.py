"""Message formatter with HTML cache."""

import html
import logging
from datetime import datetime
from typing import Optional

from pytz import timezone as pytz_timezone

from ...domain.entities.pick import Pick
from ..cache.local_cache import LocalCache


logger = logging.getLogger(__name__)


class MessageFormatter:
    """
    Formats picks for Telegram messages.
    
    Features:
    - HTML formatting
    - Cache for static parts (teams, tournament, date)
    - Timezone conversion to Spain
    """
    
    TIMEZONE = pytz_timezone("Europe/Madrid")
    
    def __init__(self, cache_ttl: int = 60):
        self._cache = LocalCache(max_size=1000)
        self._cache_ttl = cache_ttl
    
    async def format(self, pick: Pick) -> str:
        """
        Format pick as HTML message for Telegram.
        
        Args:
            pick: Pick entity to format
            
        Returns:
            HTML formatted message string
        """
        # Get cached static parts
        cache_key = self._get_cache_key(pick)
        cached_static = self._cache.get(cache_key)
        
        if cached_static:
            static_part = cached_static
        else:
            static_part = self._format_static(pick)
            await self._cache.set(cache_key, static_part)
        
        # Dynamic parts (odds, profit, stake)
        dynamic_part = self._format_dynamic(pick)
        
        return f"{dynamic_part}\n{static_part}"
    
    def _get_cache_key(self, pick: Pick) -> str:
        """Generate cache key for static parts."""
        return f"{pick.teams[0]}:{pick.teams[1]}:{int(pick.event_time.timestamp())}:{pick.bookmaker}"
    
    def _format_static(self, pick: Pick) -> str:
        """Format static parts (cached)."""
        # Convert to Spain timezone
        spain_time = pick.event_time.astimezone(self.TIMEZONE)
        date_str = spain_time.strftime("%d/%m/%Y %H:%M")
        
        teams = f"{html.escape(pick.teams[0])} vs {html.escape(pick.teams[1])}"
        tournament = html.escape(pick.tournament)
        
        lines = [
            f"🏟️ <b>{teams}</b>",
            f"🏆 {tournament}",
            f"📅 {date_str}",
        ]
        
        if pick.link:
            lines.append(f"🔗 <a href=\"{pick.link}\">Ir a la apuesta</a>")
        
        return "\n".join(lines)
    
    def _format_dynamic(self, pick: Pick) -> str:
        """Format dynamic parts (always fresh)."""
        stake_emoji = pick.stake_level
        
        # Market type formatting
        market_display = self._format_market(pick)
        
        lines = [
            f"{stake_emoji} <b>{html.escape(pick.bookmaker.upper())}</b>",
            f"📊 {market_display}",
            f"💰 Cuota: <b>{pick.odds.value:.2f}</b> (mín: {pick.min_odds.value:.2f})",
            f"📈 Profit: <b>{pick.profit.value:.2f}%</b>",
        ]
        
        return "\n".join(lines)
    
    def _format_market(self, pick: Pick) -> str:
        """Format market type for display."""
        market = pick.market_type.value.upper()
        
        # Add variety if present
        if pick.variety:
            return f"{market} {pick.variety}"
        
        return market
