"""Pick Data Transfer Object for API/domain conversion.

Bridges raw API responses with domain entities (Pick, Surebet).
Uses Hybrid Approach: delegates parsing to Surebet.from_api_response()
while adding application-layer validations.

Implementation Requirements:
- Parse raw API response via Surebet.from_api_response()
- Validate target bookmaker is configured
- Validate contrapartida is allowed
- Extract channel_id for Telegram sending

Reference:
- docs/05-Implementation.md: Task 6.1
- docs/04-Structure.md: "application/dto/"
"""

from dataclasses import dataclass
from typing import List

from ...config.bookmakers import BookmakerConfig
from ...domain.entities.pick import Pick
from ...domain.entities.surebet import Surebet


@dataclass
class PickDTO:
    """
    Data Transfer Object for converting API data to domain entities.

    Uses Surebet internally for parsing (avoiding code duplication)
    while adding application-layer validation for target bookmaker
    configuration and channel mapping.

    Attributes:
        channel_id: Telegram channel ID for the soft bookmaker.
        _surebet: Internal Surebet entity (parsed from API).
        _bookmaker_config: BookmakerConfig for validation reference.

    Examples:
        >>> config = BookmakerConfig(...)
        >>> dto = PickDTO.from_api_response(api_data, config)
        >>> pick = dto.to_pick()
        >>> surebet = dto.to_surebet()
        >>> dto.channel_id
        -1002294438792
    """

    channel_id: int
    _surebet: Surebet
    _bookmaker_config: BookmakerConfig

    @classmethod
    def from_api_response(
        cls,
        data: dict,
        bookmaker_config: BookmakerConfig,
    ) -> "PickDTO":
        """
        Create DTO from raw API response.

        Determines which prong is sharp and which is soft based
        on bookmaker hierarchy, then validates against configuration.

        Args:
            data: Raw API response with 'prongs' array.
            bookmaker_config: Configuration for bookmaker validation.

        Returns:
            PickDTO instance.

        Raises:
            ValueError: If prongs are missing/invalid, no sharp found,
                       soft not in targets, contrapartida not allowed,
                       or no channel configured.

        Reference:
            - Surebet.from_api_response() for parsing logic
            - BookmakerConfig for validation methods
        """
        # Delegate parsing to Surebet (uses sharp_hierarchy for role detection)
        surebet = Surebet.from_api_response(
            data,
            sharp_bookmakers=bookmaker_config._sharp_set,
        )

        # Application-layer validation: soft must be a target bookmaker
        soft_bk = surebet.soft_bookmaker
        if not bookmaker_config.is_target(soft_bk):
            raise ValueError(
                f"Bookmaker '{soft_bk}' is not a target bookmaker. "
                f"Expected one of: {list(bookmaker_config.target_bookmakers)}"
            )

        # Validate contrapartida is allowed (if restrictions configured)
        sharp_bk = surebet.sharp_bookmaker
        if not bookmaker_config.is_valid_contrapartida(soft_bk, sharp_bk):
            raise ValueError(
                f"Sharp '{sharp_bk}' is not an allowed contrapartida "
                f"for '{soft_bk}'"
            )

        # Get channel ID (required for sending)
        channel_id = bookmaker_config.get_channel(soft_bk)
        if channel_id is None:
            raise ValueError(
                f"No channel configured for bookmaker '{soft_bk}'"
            )

        return cls(
            channel_id=channel_id,
            _surebet=surebet,
            _bookmaker_config=bookmaker_config,
        )

    def to_pick(self) -> Pick:
        """
        Convert DTO to domain Pick entity.

        Returns the soft prong as the Pick to send to users.

        Returns:
            Pick domain entity (soft bookmaker side).
        """
        return self._surebet.to_pick()

    def to_surebet(self) -> Surebet:
        """
        Convert DTO to domain Surebet entity.

        Returns:
            Surebet domain entity with both prongs.
        """
        return self._surebet

    # ─────────────────────────────────────────────────────────────────────────
    # Convenience Properties (for PickHandler)
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def profit(self) -> float:
        """Get profit percentage value."""
        return self._surebet.profit.value

    @property
    def soft_bookmaker(self) -> str:
        """Get soft bookmaker name."""
        return self._surebet.soft_bookmaker

    @property
    def sharp_bookmaker(self) -> str:
        """Get sharp bookmaker name."""
        return self._surebet.sharp_bookmaker

    @property
    def redis_key(self) -> str:
        """Get Redis key for deduplication."""
        return self._surebet.redis_key

    def get_opposite_keys(self) -> List[str]:
        """Get Redis keys for opposite markets (rebote detection)."""
        return self._surebet.get_opposite_keys()
