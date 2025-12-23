"""Bookmaker entity representing a betting house.

A Bookmaker is classified as either SHARP (reference bookmakers like Pinnacle)
or SOFT (target bookmakers where we place bets like Retabet, Yaass, etc.).

Reference:
- docs/04-Structure.md: "domain/entities/"
- docs/05-Implementation.md: Task 1.6
- docs/02-PDR.md: Section 3.1.2 (Entities)
- legacy/RetadorV6.py: BotConfig.BOOKIE_HIERARCHY, TARGET_BOOKIES
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BookmakerType(Enum):
    """Classification of bookmaker type.

    SHARP bookmakers (e.g., Pinnacle) are used as reference for odds calculation.
    SOFT bookmakers (e.g., Retabet) are target houses where we place bets.

    Examples:
        >>> BookmakerType.SHARP.value
        'sharp'
        >>> BookmakerType.SOFT.value
        'soft'
    """

    SHARP = "sharp"
    SOFT = "soft"


@dataclass(frozen=True)
class Bookmaker:
    """Immutable entity representing a bookmaker/betting house.

    Attributes:
        name: Internal identifier used in API (e.g., "pinnaclesports", "retabet_apuestas").
              Must be non-empty and lowercase.
        bookmaker_type: Classification as SHARP or SOFT.
        display_name: Human-readable name (e.g., "Pinnacle Sports").
                      Auto-generated from name if not provided.
        channel_id: Optional Telegram channel ID for sending picks to this bookmaker.
                    Typically only SOFT bookmakers have channels.

    Examples:
        >>> pinnacle = Bookmaker.sharp("pinnaclesports")
        >>> pinnacle.is_sharp
        True
        >>> pinnacle.display_name
        'Pinnaclesports'

        >>> retabet = Bookmaker.soft("retabet_apuestas", channel_id=-123456789)
        >>> retabet.is_soft
        True
        >>> retabet.has_channel
        True
        >>> retabet.display_name
        'Retabet Apuestas'
    """

    name: str
    bookmaker_type: BookmakerType
    display_name: Optional[str] = None
    channel_id: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate bookmaker data and auto-generate display_name if needed."""
        # Validate name is not empty
        if not self.name or not self.name.strip():
            raise ValueError("Bookmaker name cannot be empty")

        # Auto-generate display_name if not provided
        if self.display_name is None:
            # Use object.__setattr__ because dataclass is frozen
            object.__setattr__(
                self, "display_name", self._generate_display_name(self.name)
            )

    @staticmethod
    def _generate_display_name(name: str) -> str:
        """Generate human-readable display name from internal name.

        Converts underscores to spaces and applies title case.

        Args:
            name: Internal bookmaker name (e.g., "retabet_apuestas").

        Returns:
            Human-readable name (e.g., "Retabet Apuestas").
        """
        return name.replace("_", " ").title()

    @property
    def is_sharp(self) -> bool:
        """Check if bookmaker is a SHARP (reference bookmaker).

        Sharp bookmakers like Pinnacle have the sharpest odds and are used
        as reference for calculating minimum acceptable odds.

        Returns:
            True if bookmaker_type is SHARP.
        """
        return self.bookmaker_type == BookmakerType.SHARP

    @property
    def is_soft(self) -> bool:
        """Check if bookmaker is a SOFT (target bookmaker).

        Soft bookmakers are where we actually place our bets.

        Returns:
            True if bookmaker_type is SOFT.
        """
        return self.bookmaker_type == BookmakerType.SOFT

    @property
    def has_channel(self) -> bool:
        """Check if bookmaker has a Telegram channel configured.

        Returns:
            True if channel_id is set.
        """
        return self.channel_id is not None

    @classmethod
    def sharp(
        cls,
        name: str,
        display_name: Optional[str] = None,
    ) -> Bookmaker:
        """Factory method to create a SHARP bookmaker.

        Sharp bookmakers are reference houses (e.g., Pinnacle) used for
        odds calculation. They typically don't have Telegram channels.

        Args:
            name: Internal identifier (e.g., "pinnaclesports").
            display_name: Optional human-readable name.

        Returns:
            Bookmaker instance with type SHARP.

        Examples:
            >>> pinnacle = Bookmaker.sharp("pinnaclesports")
            >>> pinnacle.is_sharp
            True
        """
        return cls(
            name=name,
            bookmaker_type=BookmakerType.SHARP,
            display_name=display_name,
        )

    @classmethod
    def soft(
        cls,
        name: str,
        channel_id: Optional[int] = None,
        display_name: Optional[str] = None,
    ) -> Bookmaker:
        """Factory method to create a SOFT bookmaker.

        Soft bookmakers are target houses where we place bets.
        They typically have Telegram channels for sending picks.

        Args:
            name: Internal identifier (e.g., "retabet_apuestas").
            channel_id: Optional Telegram channel ID for this bookmaker.
            display_name: Optional human-readable name.

        Returns:
            Bookmaker instance with type SOFT.

        Examples:
            >>> retabet = Bookmaker.soft("retabet_apuestas", channel_id=-123)
            >>> retabet.is_soft
            True
            >>> retabet.has_channel
            True
        """
        return cls(
            name=name,
            bookmaker_type=BookmakerType.SOFT,
            display_name=display_name,
            channel_id=channel_id,
        )
