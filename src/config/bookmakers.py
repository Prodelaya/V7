"""Bookmaker configuration and channel mappings.

Centralizes all bookmaker-related configuration:
- Sharp bookmakers (reference for odds)
- Target bookmakers (where we send picks)
- Telegram channel mappings
- Allowed contrapartidas (sharp-soft pairs)

Reference:
- docs/05-Implementation.md: Task 4.2
- docs/09-Bookmakers-Configuration.md: Full design
- docs/01-SRS.md: Section 2.4 (Users and Characteristics)
- legacy/RetadorV6.py: BotConfig (line 291-356)
"""

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional

from src.domain.entities.bookmaker import Bookmaker


@dataclass(frozen=True)
class BookmakerConfig:
    """Immutable configuration for bookmakers.

    Attributes:
        sharp_hierarchy: Ordered list of sharp bookmakers (first = highest priority)
        target_bookmakers: List of target bookmakers (soft) to send picks for
        channel_mapping: Telegram channel IDs per target bookmaker
        allowed_contrapartidas: Valid sharp counterparts per target (optional filter)
        api_bookmakers: All bookmakers to query from API (derived if not provided)

    Examples:
        >>> config = BookmakerConfig(
        ...     sharp_hierarchy=["pinnaclesports"],
        ...     target_bookmakers=["retabet_apuestas", "yaasscasino"],
        ...     channel_mapping={
        ...         "retabet_apuestas": -1002294438792,
        ...         "yaasscasino": -1002360901387,
        ...     },
        ... )
        >>> config.is_sharp("pinnaclesports")
        True
        >>> config.get_channel("retabet_apuestas")
        -1002294438792
    """

    # Sharp bookmakers in priority order (first found in surebet is sharp reference)
    sharp_hierarchy: List[str] = field(default_factory=lambda: ["pinnaclesports"])

    # Target (soft) bookmakers we send picks for
    target_bookmakers: List[str] = field(default_factory=list)

    # Telegram channel ID per target bookmaker
    channel_mapping: Dict[str, int] = field(default_factory=dict)

    # Which sharps are allowed for each target (optional, if empty = all allowed)
    allowed_contrapartidas: Dict[str, List[str]] = field(default_factory=dict)

    # All bookmakers to include in API query (auto-derived if None)
    api_bookmakers: Optional[List[str]] = None

    # Internal: cached set for O(1) sharp lookup
    _sharp_set: FrozenSet[str] = field(default=frozenset(), repr=False)
    _target_set: FrozenSet[str] = field(default=frozenset(), repr=False)
    _api_bookmakers_list: List[str] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Validate configuration and build internal caches."""
        # Build internal sets for O(1) lookups
        object.__setattr__(self, "_sharp_set", frozenset(self.sharp_hierarchy))
        object.__setattr__(self, "_target_set", frozenset(self.target_bookmakers))

        # Derive API bookmakers if not provided
        if self.api_bookmakers is None:
            derived = list(self.sharp_hierarchy) + [
                t for t in self.target_bookmakers if t not in self._sharp_set
            ]
            object.__setattr__(self, "_api_bookmakers_list", derived)
        else:
            object.__setattr__(self, "_api_bookmakers_list", list(self.api_bookmakers))

        # Validation
        self._validate()

    def _validate(self) -> None:
        """Perform validation checks on configuration."""
        # 1. Must have at least one sharp bookmaker
        if not self.sharp_hierarchy:
            raise ValueError("sharp_hierarchy must have at least one bookmaker")

        # 2. Each target must have a channel mapping
        missing_channels = [
            t for t in self.target_bookmakers if t not in self.channel_mapping
        ]
        if missing_channels:
            raise ValueError(
                f"Missing channel mapping for target bookmakers: {missing_channels}"
            )

        # 3. All targets and sharps must be in api_bookmakers
        all_required = set(self.sharp_hierarchy) | set(self.target_bookmakers)
        api_set = set(self._api_bookmakers_list)
        missing_from_api = all_required - api_set
        if missing_from_api:
            raise ValueError(f"Bookmakers missing from API list: {missing_from_api}")

        # 4. No overlap between sharps and targets
        overlap = self._sharp_set & self._target_set
        if overlap:
            raise ValueError(f"Bookmakers cannot be both sharp and target: {overlap}")

    def is_sharp(self, bookmaker: str) -> bool:
        """Check if bookmaker is in sharp hierarchy.

        Args:
            bookmaker: Bookmaker identifier (e.g., "pinnaclesports")

        Returns:
            True if bookmaker is a sharp reference.
        """
        return bookmaker in self._sharp_set

    def is_target(self, bookmaker: str) -> bool:
        """Check if bookmaker is a target (soft).

        Args:
            bookmaker: Bookmaker identifier (e.g., "retabet_apuestas")

        Returns:
            True if bookmaker is a target soft.
        """
        return bookmaker in self._target_set

    def get_channel(self, bookmaker: str) -> Optional[int]:
        """Get Telegram channel ID for a bookmaker.

        Args:
            bookmaker: Bookmaker identifier

        Returns:
            Channel ID if configured, None otherwise.
        """
        return self.channel_mapping.get(bookmaker)

    def is_valid_contrapartida(self, soft: str, sharp: str) -> bool:
        """Check if sharp is a valid counterpart for soft.

        If allowed_contrapartidas is not configured for the soft,
        all sharps are considered valid.

        Args:
            soft: Target bookmaker identifier
            sharp: Sharp bookmaker identifier

        Returns:
            True if the sharp-soft pair is valid.
        """
        # Must be a valid sharp
        if not self.is_sharp(sharp):
            return False

        # If no restrictions defined, all sharps are valid
        if soft not in self.allowed_contrapartidas:
            return True

        # Check if sharp is in allowed list
        return sharp in self.allowed_contrapartidas[soft]

    def get_api_source_param(self) -> str:
        """Get the formatted source parameter for API requests.

        Returns:
            Pipe-separated string of bookmaker identifiers.
        """
        return "|".join(self._api_bookmakers_list)

    def get_first_sharp(self, bookmaker_names: List[str]) -> Optional[str]:
        """Get the first sharp bookmaker from a list (by hierarchy priority).

        Useful for determining which prong is the sharp in a surebet.

        Args:
            bookmaker_names: List of bookmaker identifiers

        Returns:
            First matching sharp bookmaker, or None if none found.
        """
        for sharp in self.sharp_hierarchy:
            if sharp in bookmaker_names:
                return sharp
        return None

    def to_bookmaker_entities(self) -> Dict[str, Bookmaker]:
        """Create Bookmaker entities from configuration.

        Returns:
            Dictionary mapping bookmaker name to Bookmaker entity.
        """
        entities: Dict[str, Bookmaker] = {}

        # Create sharp entities
        for name in self.sharp_hierarchy:
            entities[name] = Bookmaker.sharp(name)

        # Create soft entities with channels
        for name in self.target_bookmakers:
            channel_id = self.channel_mapping.get(name)
            entities[name] = Bookmaker.soft(name, channel_id=channel_id)

        return entities

    @classmethod
    def create_default(cls) -> "BookmakerConfig":
        """Create a default configuration for testing.

        Returns:
            BookmakerConfig with minimal valid defaults.
        """
        return cls(
            sharp_hierarchy=["pinnaclesports"],
            target_bookmakers=[],
            channel_mapping={},
            allowed_contrapartidas={},
        )

    @classmethod
    def from_legacy(cls) -> "BookmakerConfig":
        """Create configuration matching legacy RetadorV6.

        This is a reference for migration, using the exact values
        from the legacy codebase (with placeholder channel IDs).

        Returns:
            BookmakerConfig matching V6 configuration.
        """
        return cls(
            sharp_hierarchy=["pinnaclesports", "bet365"],
            target_bookmakers=["retabet_apuestas", "yaasscasino"],
            channel_mapping={
                "retabet_apuestas": 0,  # Placeholder - set real IDs in .env
                "yaasscasino": 0,
            },
            allowed_contrapartidas={
                "retabet_apuestas": ["pinnaclesports"],
                "yaasscasino": ["pinnaclesports"],
            },
        )
