"""Tests for the chord library and groupings."""

from __future__ import annotations

from fretsy import (
    ALL_CHORDS,
    AUGMENTED_CHORDS,
    BARRE_CHORDS,
    BEGINNER_CHORDS,
    CHORDS,
    DIMINISHED_CHORDS,
    DOMINANT_CHORDS,
    JAZZ_CHORDS,
    MAJOR_CHORDS,
    MINOR_CHORDS,
    OPEN_CHORDS,
    POWER_CHORDS,
    PRIMARY_CHORDS,
    SLASH_CHORDS,
    SUSPENDED_CHORDS,
    ChordDiagram,
    find_chord,
)


class TestChordsIntegrity:
    def test_chords_not_empty(self):
        assert len(CHORDS) > 3000

    def test_all_chords_is_chords(self):
        assert ALL_CHORDS is CHORDS

    def test_all_entries_are_chord_diagrams(self):
        for c in CHORDS:
            assert isinstance(c, ChordDiagram)

    def test_all_frets_have_six_elements(self):
        for c in CHORDS:
            assert len(c.frets) == 6, f"{c.name}: frets has {len(c.frets)} elements"

    def test_all_fingers_have_six_elements(self):
        for c in CHORDS:
            assert len(c.fingers) == 6, f"{c.name}: fingers has {len(c.fingers)} elements"


class TestGroupings:
    """Verify each grouping list references objects from CHORDS (not copies)."""

    def test_groups_are_nonempty(self):
        for name, group in [
            ("OPEN_CHORDS", OPEN_CHORDS),
            ("BARRE_CHORDS", BARRE_CHORDS),
            ("POWER_CHORDS", POWER_CHORDS),
            ("MAJOR_CHORDS", MAJOR_CHORDS),
            ("MINOR_CHORDS", MINOR_CHORDS),
            ("DOMINANT_CHORDS", DOMINANT_CHORDS),
            ("DIMINISHED_CHORDS", DIMINISHED_CHORDS),
            ("AUGMENTED_CHORDS", AUGMENTED_CHORDS),
            ("SUSPENDED_CHORDS", SUSPENDED_CHORDS),
            ("JAZZ_CHORDS", JAZZ_CHORDS),
            ("SLASH_CHORDS", SLASH_CHORDS),
            ("PRIMARY_CHORDS", PRIMARY_CHORDS),
            ("BEGINNER_CHORDS", BEGINNER_CHORDS),
        ]:
            assert len(group) > 0, f"{name} is empty"

    def test_groups_reference_chords(self):
        """All grouped items should be the same objects as in CHORDS."""
        chords_set = set(id(c) for c in CHORDS)
        for name, group in [
            ("OPEN_CHORDS", OPEN_CHORDS),
            ("BARRE_CHORDS", BARRE_CHORDS),
            ("BEGINNER_CHORDS", BEGINNER_CHORDS),
            ("POWER_CHORDS", POWER_CHORDS),
        ]:
            for c in group:
                assert id(c) in chords_set, f"{name}: {c.name} not in CHORDS"

    def test_barre_chords_all_have_barre(self):
        for c in BARRE_CHORDS:
            assert c.barre is not None, f"{c.name} has no barre"

    def test_open_chords_have_open_strings(self):
        for c in OPEN_CHORDS:
            assert 0 in c.frets, f"{c.name} has no open string"
            assert c.barre is None, f"{c.name} has a barre"
            assert c.base_fret == 1, f"{c.name} base_fret={c.base_fret}"

    def test_power_chords_names_end_with_5(self):
        for c in POWER_CHORDS:
            assert "5" in c.name, f"{c.name} doesn't contain '5'"

    def test_slash_chords_contain_slash(self):
        for c in SLASH_CHORDS:
            assert "/" in c.name, f"{c.name} has no slash"

    def test_beginner_chords(self):
        names = {c.name for c in BEGINNER_CHORDS}
        expected = {"E", "A", "D", "G", "C", "Em", "Am", "Dm"}
        assert names == expected

    def test_primary_chords_no_variants(self):
        for c in PRIMARY_CHORDS:
            if c.label:
                assert "var" not in c.label, f"{c.name} label={c.label}"

    def test_diminished_chords_quality(self):
        for c in DIMINISHED_CHORDS:
            assert "dim" in c.name, f"{c.name} not diminished"

    def test_augmented_chords_quality(self):
        for c in AUGMENTED_CHORDS:
            assert "aug" in c.name, f"{c.name} not augmented"

    def test_suspended_chords_quality(self):
        for c in SUSPENDED_CHORDS:
            assert "sus" in c.name, f"{c.name} not suspended"


class TestFindChord:
    def test_find_existing(self):
        results = find_chord("Am")
        assert len(results) >= 1
        assert all(c.name == "Am" for c in results)

    def test_find_nonexistent(self):
        assert find_chord("Zzzz") == []

    def test_find_in_subset(self):
        results = find_chord("C", chords=BEGINNER_CHORDS)
        assert len(results) == 1
        assert results[0].name == "C"

    def test_find_returns_multiple_voicings(self):
        results = find_chord("C")
        assert len(results) > 1  # should have multiple voicings

    def test_case_sensitive(self):
        assert find_chord("am") == []
        assert len(find_chord("Am")) >= 1
