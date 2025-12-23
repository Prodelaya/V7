"""Tests for domain entities.

Test Requirements:
- Bookmaker creation and validation
- BookmakerType enum values
- Immutability of entities

Reference:
- docs/05-Implementation.md: Task 1.9
"""

from dataclasses import FrozenInstanceError

import pytest

from src.domain.entities.bookmaker import Bookmaker, BookmakerType


class TestBookmakerType:
    """Tests for BookmakerType enum."""

    # -------------------------------------------------------------------------
    # Enum Values
    # -------------------------------------------------------------------------

    def test_sharp_value(self) -> None:
        """SHARP should have value 'sharp'."""
        assert BookmakerType.SHARP.value == "sharp"

    def test_soft_value(self) -> None:
        """SOFT should have value 'soft'."""
        assert BookmakerType.SOFT.value == "soft"

    def test_enum_has_two_members(self) -> None:
        """BookmakerType should have exactly 2 members."""
        assert len(BookmakerType) == 2

    def test_enum_members_are_sharp_and_soft(self) -> None:
        """BookmakerType should only contain SHARP and SOFT."""
        members = {member.name for member in BookmakerType}
        assert members == {"SHARP", "SOFT"}


class TestBookmaker:
    """Tests for Bookmaker entity."""

    # -------------------------------------------------------------------------
    # Valid Creation
    # -------------------------------------------------------------------------

    def test_create_sharp_bookmaker(self) -> None:
        """Should create a SHARP bookmaker successfully."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.name == "pinnaclesports"
        assert bookmaker.bookmaker_type == BookmakerType.SHARP

    def test_create_soft_bookmaker(self) -> None:
        """Should create a SOFT bookmaker successfully."""
        bookmaker = Bookmaker(name="retabet_apuestas", bookmaker_type=BookmakerType.SOFT)
        assert bookmaker.name == "retabet_apuestas"
        assert bookmaker.bookmaker_type == BookmakerType.SOFT

    def test_create_bookmaker_with_channel(self) -> None:
        """Should create bookmaker with channel_id."""
        bookmaker = Bookmaker(
            name="retabet_apuestas",
            bookmaker_type=BookmakerType.SOFT,
            channel_id=-123456789,
        )
        assert bookmaker.channel_id == -123456789

    def test_create_bookmaker_without_channel(self) -> None:
        """Should create bookmaker without channel_id (None by default)."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.channel_id is None

    def test_create_bookmaker_with_explicit_display_name(self) -> None:
        """Should use explicit display_name when provided."""
        bookmaker = Bookmaker(
            name="pinnaclesports",
            bookmaker_type=BookmakerType.SHARP,
            display_name="Pinnacle Sports",
        )
        assert bookmaker.display_name == "Pinnacle Sports"

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def test_empty_name_raises_error(self) -> None:
        """Empty name should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Bookmaker(name="", bookmaker_type=BookmakerType.SHARP)

    def test_whitespace_only_name_raises_error(self) -> None:
        """Whitespace-only name should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Bookmaker(name="   ", bookmaker_type=BookmakerType.SHARP)

    # -------------------------------------------------------------------------
    # is_sharp Property
    # -------------------------------------------------------------------------

    def test_is_sharp_true_for_sharp_bookmaker(self) -> None:
        """is_sharp should return True for SHARP bookmaker."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.is_sharp is True

    def test_is_sharp_false_for_soft_bookmaker(self) -> None:
        """is_sharp should return False for SOFT bookmaker."""
        bookmaker = Bookmaker(name="retabet_apuestas", bookmaker_type=BookmakerType.SOFT)
        assert bookmaker.is_sharp is False

    # -------------------------------------------------------------------------
    # is_soft Property
    # -------------------------------------------------------------------------

    def test_is_soft_true_for_soft_bookmaker(self) -> None:
        """is_soft should return True for SOFT bookmaker."""
        bookmaker = Bookmaker(name="retabet_apuestas", bookmaker_type=BookmakerType.SOFT)
        assert bookmaker.is_soft is True

    def test_is_soft_false_for_sharp_bookmaker(self) -> None:
        """is_soft should return False for SHARP bookmaker."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.is_soft is False

    # -------------------------------------------------------------------------
    # has_channel Property
    # -------------------------------------------------------------------------

    def test_has_channel_true_when_set(self) -> None:
        """has_channel should return True when channel_id is set."""
        bookmaker = Bookmaker(
            name="retabet_apuestas",
            bookmaker_type=BookmakerType.SOFT,
            channel_id=-123456789,
        )
        assert bookmaker.has_channel is True

    def test_has_channel_false_when_none(self) -> None:
        """has_channel should return False when channel_id is None."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.has_channel is False

    # -------------------------------------------------------------------------
    # display_name Auto-generation
    # -------------------------------------------------------------------------

    def test_display_name_auto_generated_simple(self) -> None:
        """display_name should be auto-generated from simple name."""
        bookmaker = Bookmaker(name="pinnaclesports", bookmaker_type=BookmakerType.SHARP)
        assert bookmaker.display_name == "Pinnaclesports"

    def test_display_name_auto_generated_with_underscores(self) -> None:
        """display_name should convert underscores to spaces and title case."""
        bookmaker = Bookmaker(name="retabet_apuestas", bookmaker_type=BookmakerType.SOFT)
        assert bookmaker.display_name == "Retabet Apuestas"

    def test_display_name_auto_generated_with_multiple_underscores(self) -> None:
        """display_name should handle multiple underscores."""
        bookmaker = Bookmaker(name="admiral_at", bookmaker_type=BookmakerType.SOFT)
        assert bookmaker.display_name == "Admiral At"

    # -------------------------------------------------------------------------
    # Factory Method: sharp()
    # -------------------------------------------------------------------------

    def test_sharp_factory_creates_sharp_bookmaker(self) -> None:
        """Bookmaker.sharp() should create a SHARP bookmaker."""
        bookmaker = Bookmaker.sharp("pinnaclesports")
        assert bookmaker.is_sharp is True
        assert bookmaker.bookmaker_type == BookmakerType.SHARP

    def test_sharp_factory_with_display_name(self) -> None:
        """Bookmaker.sharp() should accept display_name."""
        bookmaker = Bookmaker.sharp("pinnaclesports", display_name="Pinnacle")
        assert bookmaker.display_name == "Pinnacle"

    def test_sharp_factory_no_channel(self) -> None:
        """Bookmaker.sharp() should not set channel_id."""
        bookmaker = Bookmaker.sharp("pinnaclesports")
        assert bookmaker.channel_id is None
        assert bookmaker.has_channel is False

    # -------------------------------------------------------------------------
    # Factory Method: soft()
    # -------------------------------------------------------------------------

    def test_soft_factory_creates_soft_bookmaker(self) -> None:
        """Bookmaker.soft() should create a SOFT bookmaker."""
        bookmaker = Bookmaker.soft("retabet_apuestas")
        assert bookmaker.is_soft is True
        assert bookmaker.bookmaker_type == BookmakerType.SOFT

    def test_soft_factory_with_channel(self) -> None:
        """Bookmaker.soft() should accept channel_id."""
        bookmaker = Bookmaker.soft("retabet_apuestas", channel_id=-123456789)
        assert bookmaker.channel_id == -123456789
        assert bookmaker.has_channel is True

    def test_soft_factory_with_display_name(self) -> None:
        """Bookmaker.soft() should accept display_name."""
        bookmaker = Bookmaker.soft("retabet_apuestas", display_name="Retabet")
        assert bookmaker.display_name == "Retabet"

    def test_soft_factory_without_channel(self) -> None:
        """Bookmaker.soft() without channel_id should have None."""
        bookmaker = Bookmaker.soft("yaasscasino")
        assert bookmaker.channel_id is None
        assert bookmaker.has_channel is False

    # -------------------------------------------------------------------------
    # Immutability
    # -------------------------------------------------------------------------

    def test_bookmaker_is_immutable_name(self) -> None:
        """Bookmaker should be immutable (cannot change name)."""
        bookmaker = Bookmaker.sharp("pinnaclesports")
        with pytest.raises(FrozenInstanceError):
            bookmaker.name = "bet365"  # type: ignore[misc]

    def test_bookmaker_is_immutable_type(self) -> None:
        """Bookmaker should be immutable (cannot change bookmaker_type)."""
        bookmaker = Bookmaker.sharp("pinnaclesports")
        with pytest.raises(FrozenInstanceError):
            bookmaker.bookmaker_type = BookmakerType.SOFT  # type: ignore[misc]

    def test_bookmaker_is_immutable_channel(self) -> None:
        """Bookmaker should be immutable (cannot change channel_id)."""
        bookmaker = Bookmaker.soft("retabet_apuestas", channel_id=-123)
        with pytest.raises(FrozenInstanceError):
            bookmaker.channel_id = -456  # type: ignore[misc]

    # -------------------------------------------------------------------------
    # Equality (dataclass default)
    # -------------------------------------------------------------------------

    def test_bookmakers_with_same_values_are_equal(self) -> None:
        """Two bookmakers with same values should be equal."""
        bm1 = Bookmaker.sharp("pinnaclesports")
        bm2 = Bookmaker.sharp("pinnaclesports")
        assert bm1 == bm2

    def test_bookmakers_with_different_names_are_not_equal(self) -> None:
        """Two bookmakers with different names should not be equal."""
        bm1 = Bookmaker.sharp("pinnaclesports")
        bm2 = Bookmaker.sharp("bet365")
        assert bm1 != bm2

    def test_bookmakers_with_different_types_are_not_equal(self) -> None:
        """Two bookmakers with different types should not be equal."""
        bm1 = Bookmaker(name="test", bookmaker_type=BookmakerType.SHARP)
        bm2 = Bookmaker(name="test", bookmaker_type=BookmakerType.SOFT)
        assert bm1 != bm2

    # -------------------------------------------------------------------------
    # Real-world Examples
    # -------------------------------------------------------------------------

    def test_pinnacle_is_sharp(self) -> None:
        """Pinnacle should be creatable as SHARP."""
        pinnacle = Bookmaker.sharp("pinnaclesports")
        assert pinnacle.name == "pinnaclesports"
        assert pinnacle.is_sharp is True
        assert pinnacle.is_soft is False
        assert pinnacle.has_channel is False

    def test_retabet_is_soft_with_channel(self) -> None:
        """Retabet should be creatable as SOFT with channel."""
        retabet = Bookmaker.soft("retabet_apuestas", channel_id=-1001234567890)
        assert retabet.name == "retabet_apuestas"
        assert retabet.is_soft is True
        assert retabet.is_sharp is False
        assert retabet.has_channel is True
        assert retabet.display_name == "Retabet Apuestas"
