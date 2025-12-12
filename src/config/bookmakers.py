"""Bookmaker configuration and channel mappings.

Implementation Requirements:
- List of sharp bookmakers (Pinnacle)
- List of soft bookmakers (targets)
- Allowed contrapartidas mapping
- Telegram channel IDs per bookmaker

Reference:
- docs/05-Implementation.md: Task 4.2
- docs/01-SRS.md: Section 2.4 (Users and Characteristics)
- legacy/RetadorV6.py: BotConfig (line 291-356)

TODO: Implement BookmakerConfig
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class BookmakerConfig:
    """
    Bookmaker configuration.
    
    Contains:
    - Sharp bookmakers (reference for odds)
    - Soft bookmakers (targets for betting)
    - Allowed contrapartidas per soft
    - Telegram channel mappings
    
    TODO: Implement based on:
    - Task 4.2 in docs/05-Implementation.md
    - BotConfig in legacy/RetadorV6.py
    """
    
    # Sharp bookmakers in priority order
    # First found in surebet is the sharp reference
    sharp_hierarchy: List[str] = field(default_factory=lambda: [
        "pinnaclesports",
        "bet365",
    ])
    
    # Soft bookmakers we send picks for
    target_bookmakers: List[str] = field(default_factory=lambda: [
        "retabet_apuestas",
        "yaasscasino",
        # Add more as needed
    ])
    
    # Which sharps are allowed for each soft
    allowed_contrapartidas: Dict[str, List[str]] = field(default_factory=lambda: {
        "retabet_apuestas": ["pinnaclesports"],
        "yaasscasino": ["pinnaclesports"],
        # Add more as needed
    })
    
    # Telegram channel ID per bookmaker
    channel_mapping: Dict[str, int] = field(default_factory=lambda: {
        "retabet_apuestas": 0,  # TODO: Add real channel IDs
        "yaasscasino": 0,
        # Add more as needed
    })
    
    def is_sharp(self, bookmaker: str) -> bool:
        """Check if bookmaker is in sharp hierarchy."""
        raise NotImplementedError("BookmakerConfig.is_sharp not implemented")
    
    def is_target(self, bookmaker: str) -> bool:
        """Check if bookmaker is a target soft."""
        raise NotImplementedError("BookmakerConfig.is_target not implemented")
    
    def get_channel(self, bookmaker: str) -> int:
        """Get Telegram channel ID for bookmaker."""
        raise NotImplementedError("BookmakerConfig.get_channel not implemented")
    
    def is_valid_contrapartida(self, soft: str, sharp: str) -> bool:
        """Check if sharp is allowed for this soft."""
        raise NotImplementedError("BookmakerConfig.is_valid_contrapartida not implemented")
