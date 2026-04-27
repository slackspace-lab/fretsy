"""Tests for save and save_batch."""

from __future__ import annotations

from pathlib import Path

import pytest

from fretsy import ChordDiagram, save, save_batch


@pytest.fixture
def am_chord():
    return ChordDiagram("Am", frets=[-1, 0, 2, 2, 1, 0])


class TestSave:
    def test_save_svg(self, am_chord, tmp_path):
        out = save(am_chord, tmp_path / "Am.svg")
        assert out.exists()
        assert out.suffix == ".svg"
        content = out.read_text()
        assert "<svg" in content
        assert "Am" in content

    def test_save_auto_format_svg(self, am_chord, tmp_path):
        out = save(am_chord, tmp_path / "chord.svg")
        assert out.read_text().startswith("<svg")

    def test_save_explicit_format(self, am_chord, tmp_path):
        out = save(am_chord, tmp_path / "chord.xml", fmt="svg")
        assert out.exists()
        assert "<svg" in out.read_text()

    def test_save_unsupported_format(self, am_chord, tmp_path):
        with pytest.raises(ValueError, match="Unsupported format"):
            save(am_chord, tmp_path / "chord.bmp", fmt="bmp")

    def test_save_creates_directories(self, am_chord, tmp_path):
        out = save(am_chord, tmp_path / "deep" / "nested" / "Am.svg")
        assert out.exists()

    def test_save_returns_path(self, am_chord, tmp_path):
        out = save(am_chord, tmp_path / "Am.svg")
        assert isinstance(out, Path)
        assert out == tmp_path / "Am.svg"


class TestSaveBatch:
    def test_batch_svg(self, tmp_path):
        chords = [
            ChordDiagram("E", frets=[0, 2, 2, 1, 0, 0]),
            ChordDiagram("Am", frets=[-1, 0, 2, 2, 1, 0]),
        ]
        paths = save_batch(chords, tmp_path / "batch", fmt="svg")
        assert len(paths) == 2
        assert all(p.exists() for p in paths)
        assert all(p.suffix == ".svg" for p in paths)

    def test_batch_custom_names(self, tmp_path):
        chords = [
            ChordDiagram("E", frets=[0, 2, 2, 1, 0, 0]),
            ChordDiagram("Am", frets=[-1, 0, 2, 2, 1, 0]),
        ]
        paths = save_batch(
            chords,
            tmp_path / "named",
            fmt="svg",
            name_fn=lambda c, i: f"{i:02d}_{c.name}",
        )
        assert paths[0].stem == "00_E"
        assert paths[1].stem == "01_Am"

    def test_batch_deduplicates_names(self, tmp_path):
        chords = [
            ChordDiagram("C", frets=[-1, 3, 2, 0, 1, 0]),
            ChordDiagram("C", frets=[-1, 3, 5, 5, 5, 3]),
        ]
        paths = save_batch(chords, tmp_path / "dupes", fmt="svg")
        assert len(paths) == 2
        stems = {p.stem for p in paths}
        assert len(stems) == 2  # names should be deduplicated

    def test_batch_creates_directory(self, tmp_path):
        chords = [ChordDiagram("G", frets=[3, 2, 0, 0, 0, 3])]
        out_dir = tmp_path / "new_dir"
        paths = save_batch(chords, out_dir, fmt="svg")
        assert out_dir.is_dir()
        assert len(paths) == 1

    def test_batch_sanitizes_filenames(self, tmp_path):
        chords = [ChordDiagram("C/E", frets=[-1, 3, 2, 0, 1, 0])]
        paths = save_batch(chords, tmp_path / "slash", fmt="svg")
        assert "/" not in paths[0].name
