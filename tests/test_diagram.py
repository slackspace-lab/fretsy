"""Tests for ChordDiagram, DiagramStyle, and rendering."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from fretsy import (
    STYLE_DARK,
    STYLE_DEFAULT,
    STYLE_MINIMAL,
    STYLE_PASTEL,
    ChordDiagram,
    DiagramStyle,
    render_svg,
)

# ---------------------------------------------------------------------------
# ChordDiagram construction
# ---------------------------------------------------------------------------


class TestChordDiagram:
    def test_basic_construction(self):
        c = ChordDiagram("Am", frets=[-1, 0, 2, 2, 1, 0])
        assert c.name == "Am"
        assert c.frets == [-1, 0, 2, 2, 1, 0]
        assert c.fingers == [0, 0, 0, 0, 0, 0]
        assert c.barre is None
        assert c.base_fret == 1
        assert c.label is None

    def test_fingers_and_barre(self):
        c = ChordDiagram(
            "F",
            frets=[1, 1, 2, 3, 3, 1],
            fingers=[1, 1, 2, 4, 3, 1],
            barre=(1, 1, 6),
        )
        assert c.fingers == [1, 1, 2, 4, 3, 1]
        assert c.barre == (1, 1, 6)

    def test_auto_base_fret(self):
        c = ChordDiagram("Bb", frets=[6, 6, 7, 8, 8, 6])
        assert c.base_fret == 6

    def test_base_fret_not_overridden_when_explicit(self):
        c = ChordDiagram("X", frets=[5, 5, 6, 7, 7, 5], base_fret=5)
        assert c.base_fret == 5

    def test_base_fret_clamped_when_too_high(self):
        # base_fret=3 with relative frets — should be preserved as-is
        c = ChordDiagram("X", frets=[-1, 1, 3, 3, 3, 1], base_fret=3)
        assert c.base_fret == 3

    def test_base_fret_clamped_with_barre(self):
        # barre at fret 1 with base_fret=3 — should be preserved
        c = ChordDiagram("X", frets=[-1, 1, 3, 3, 3, 1], barre=(1, 2, 6), base_fret=3)
        assert c.base_fret == 3

    def test_low_frets_keep_base_fret_1(self):
        c = ChordDiagram("E", frets=[0, 2, 2, 1, 0, 0])
        assert c.base_fret == 1

    def test_invalid_frets_length(self):
        with pytest.raises(ValueError, match="frets must have exactly 6"):
            ChordDiagram("X", frets=[0, 1, 2])

    def test_invalid_fingers_length(self):
        with pytest.raises(ValueError, match="fingers must have exactly 6"):
            ChordDiagram("X", frets=[0, 0, 0, 0, 0, 0], fingers=[1, 2])

    def test_label(self):
        c = ChordDiagram("Bb", frets=[-1, 1, 3, 3, 3, 1], label="A-form")
        assert c.label == "A-form"


# ---------------------------------------------------------------------------
# DiagramStyle
# ---------------------------------------------------------------------------


class TestDiagramStyle:
    def test_default_dimensions(self):
        s = DiagramStyle()
        assert s.width == 200
        assert s.height == 280  # base height; actual SVG height is dynamic

    def test_computed_properties(self):
        s = DiagramStyle(width=200, padding_side=30, height=280, padding_top=82, padding_bottom=30)
        assert s.grid_width == 140  # 200 - 2*30
        assert s.grid_height == 168  # 280 - 82 - 30
        assert s.string_spacing == 140 / 5
        assert s.fret_spacing == 168 / 5

    def test_custom_style(self):
        s = DiagramStyle(background_color="#000", dot_color="#fff", width=300)
        assert s.background_color == "#000"
        assert s.dot_color == "#fff"
        assert s.width == 300

    def test_preset_styles_exist(self):
        for style in (STYLE_DEFAULT, STYLE_DARK, STYLE_MINIMAL, STYLE_PASTEL):
            assert isinstance(style, DiagramStyle)


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------


class TestRenderSvg:
    def _parse(self, svg_str: str) -> ET.Element:
        return ET.fromstring(svg_str)

    def test_returns_valid_svg(self):
        chord = ChordDiagram("Am", frets=[-1, 0, 2, 2, 1, 0])
        svg = render_svg(chord)
        root = self._parse(svg)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"

    def test_contains_chord_name(self):
        chord = ChordDiagram("G7", frets=[3, 2, 0, 0, 0, 1])
        svg = render_svg(chord)
        assert "G7" in svg

    def test_contains_label(self):
        chord = ChordDiagram("Bb", frets=[-1, 1, 3, 3, 3, 1], label="A-form")
        svg = render_svg(chord)
        assert "A-form" in svg

    def test_muted_string_draws_x(self):
        chord = ChordDiagram("Am", frets=[-1, 0, 2, 2, 1, 0])
        svg = render_svg(chord)
        # Muted strings are drawn as two crossing lines (X shape)
        # The SVG should have stroke-linecap="round" for the X marks
        assert 'stroke-linecap="round"' in svg

    def test_open_string_draws_circle(self):
        chord = ChordDiagram("Em", frets=[0, 2, 2, 0, 0, 0])
        svg = render_svg(chord)
        root = self._parse(svg)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        circles = root.findall(".//svg:circle", ns)
        assert len(circles) > 0

    def test_barre_draws_rect(self):
        chord = ChordDiagram("F", frets=[1, 1, 2, 3, 3, 1], barre=(1, 1, 6))
        svg = render_svg(chord)
        root = self._parse(svg)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        rects = root.findall(".//svg:rect", ns)
        # At least background + nut + barre rect
        assert len(rects) >= 3

    def test_finger_numbers_in_svg(self):
        chord = ChordDiagram("Am", frets=[-1, 0, 2, 2, 1, 0], fingers=[0, 0, 2, 3, 1, 0])
        svg = render_svg(chord)
        root = self._parse(svg)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        texts = [t.text for t in root.findall(".//svg:text", ns) if t.text]
        # Should contain finger numbers 1, 2, 3
        assert "1" in texts
        assert "2" in texts
        assert "3" in texts

    def test_high_base_fret_shows_fret_number(self):
        chord = ChordDiagram("Bb", frets=[6, 6, 7, 8, 8, 6])
        svg = render_svg(chord)
        assert "6" in svg  # base_fret label

    def test_all_styles_render(self):
        chord = ChordDiagram("C", frets=[-1, 3, 2, 0, 1, 0])
        for style in (STYLE_DEFAULT, STYLE_DARK, STYLE_MINIMAL, STYLE_PASTEL):
            svg = render_svg(chord, style=style)
            root = self._parse(svg)
            assert root.tag == "{http://www.w3.org/2000/svg}svg"

    def test_transparent_background(self):
        style = DiagramStyle(background_opacity=0.0)
        chord = ChordDiagram("E", frets=[0, 2, 2, 1, 0, 0])
        svg = render_svg(chord, style=style)
        root = self._parse(svg)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        # No background rect when opacity is 0
        rects = root.findall(".//svg:rect", ns)
        bg_rects = [r for r in rects if r.get("x") == "0" and r.get("y") == "0"]
        assert len(bg_rects) == 0

    def test_dimensions_match_style(self):
        style = DiagramStyle(width=300, height=400)
        chord = ChordDiagram("D", frets=[-1, -1, 0, 2, 3, 2])
        svg = render_svg(chord, style=style)
        root = self._parse(svg)
        assert root.get("width") == "300"
        # Height is dynamic based on content, but should be close to style.height
        h = int(root.get("height"))
        assert h >= 350  # at least reasonable
        assert h <= 450  # not wildly off
