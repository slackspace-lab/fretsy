"""
fretsy — Guitar chord diagram image generator.
Renders clean SVG/PNG chord diagrams from fingering data.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ChordDiagram:
    """A guitar chord fingering definition.

    Attributes:
        name: Display name for the chord (e.g. ``"Am"``, ``"F#m7"``).
        frets: 6-element list of fret positions, one per string from low-E to
            high-E. Use ``-1`` for muted, ``0`` for open, and ``1``-N for fret
            numbers (relative to the diagram grid).
        fingers: 6-element list of finger numbers (``1``-``4``) displayed inside
            the fretted dots. Use ``0`` for no label. Defaults to all zeros.
        barre: Optional barre indicator as ``(fret, from_string, to_string)``
            where *fret* is the grid-relative fret position and strings are
            1-indexed (low-E = 1). Draws a rounded bar across the specified
            string range.
        base_fret: The real fret number at the top of the diagram. When ``1``
            (default), a thick nut is drawn. When > 1, the nut is replaced by a
            fret number label. Auto-detected when the lowest fret exceeds 4.
        label: Optional subtitle shown below the chord name (e.g. ``"A-form"``,
            ``"var. 2"``).

    Raises:
        ValueError: If *frets* or *fingers* does not have exactly 6 elements.

    Example::

        ChordDiagram(
            "F",
            frets=[1, 1, 2, 3, 3, 1],
            fingers=[1, 1, 2, 4, 3, 1],
            barre=(1, 1, 6),
        )
    """

    name: str
    frets: list[int]
    fingers: list[int] = field(default_factory=lambda: [0] * 6)
    barre: tuple[int, int, int] | None = None  # (fret, lo_str, hi_str)
    base_fret: int = 1
    label: str | None = None

    def __post_init__(self) -> None:
        """Validate fields and auto-detect ``base_fret`` for high-position chords.

        Raises:
            ValueError: If *frets* or *fingers* does not have exactly 6 elements.
        """
        if len(self.frets) != 6:
            raise ValueError("frets must have exactly 6 elements")
        if self.fingers and len(self.fingers) != 6:
            raise ValueError("fingers must have exactly 6 elements")
        if not self.fingers:
            self.fingers = [0] * 6

        # Auto-detect base_fret when not explicitly set:
        # if the lowest fret > 4, assume it's a high-position chord
        if self.base_fret == 1:
            playable = [f for f in self.frets if f > 0]
            if self.barre:
                playable.append(self.barre[0])
            if playable and min(playable) > 4:
                self.base_fret = min(playable)


# ---------------------------------------------------------------------------
# Style / theme
# ---------------------------------------------------------------------------


@dataclass
class DiagramStyle:
    """Visual configuration for rendering chord diagrams.

    Controls every aspect of the diagram appearance including canvas size,
    grid colors, dot styling, text fonts/sizes, and background. Pass an
    instance to any render or save function to override the default theme.

    Attributes:
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        padding_top: Space above the grid for chord name, label, and markers.
        padding_side: Left/right margin around the grid.
        padding_bottom: Space below the grid.
        num_frets: Number of fret rows shown on the grid.
        string_color: CSS color for vertical string lines.
        fret_color: CSS color for horizontal fret lines.
        nut_color: CSS color for the thick nut bar (when ``base_fret == 1``).
        nut_thickness: Height of the nut bar in pixels.
        string_thickness: Stroke width of string lines.
        fret_thickness: Stroke width of fret lines.
        dot_color: Fill color for fretted-note dots.
        dot_radius_frac: Dot radius as a fraction of string spacing.
        open_dot_color: Stroke color for open-string circles.
        open_dot_thickness: Stroke width for open-string circles.
        open_dot_radius_frac: Open-circle radius as a fraction of string spacing.
        barre_color: Fill color for the barre bar.
        barre_opacity: Opacity of the barre bar (``0.0``-``1.0``).
        chord_name_size: Font size for the chord name.
        chord_name_color: CSS color for the chord name.
        chord_name_font: CSS font-family for the chord name.
        label_size: Font size for the optional label/subtitle.
        label_color: CSS color for the label.
        label_font: CSS font-family for the label.
        finger_num_color: Text color for finger numbers inside dots.
        finger_num_size: Font size for finger numbers.
        finger_num_font: CSS font-family for finger numbers.
        mute_color: CSS color for the muted-string X marker.
        mute_size: Size of the muted-string X marker.
        fret_label_color: CSS color for the base-fret number label.
        fret_label_size: Font size for the base-fret number label.
        fret_label_font: CSS font-family for the base-fret number label.
        background_color: CSS color for the diagram background.
        background_opacity: Background opacity (``0.0`` for transparent).

    Example::

        style = DiagramStyle(
            background_color="#1a1a2e",
            dot_color="#e94560",
            chord_name_color="#ffffff",
        )
    """

    # Canvas
    width: int = 200
    height: int = 280
    padding_top: int = 82  # space for chord name + label + open/mute markers
    padding_side: int = 30
    padding_bottom: int = 30

    # Grid
    num_frets: int = 5
    string_color: str = "#333333"
    fret_color: str = "#333333"
    nut_color: str = "#222222"
    nut_thickness: int = 5
    string_thickness: float = 1.5
    fret_thickness: float = 1.2

    # Dots
    dot_color: str = "#1a1a2e"
    dot_radius_frac: float = 0.36
    open_dot_color: str = "#1a1a2e"
    open_dot_thickness: float = 2.0
    open_dot_radius_frac: float = 0.28

    # Barre
    barre_color: str = "#1a1a2e"
    barre_opacity: float = 1.0

    # Text
    chord_name_size: int = 22
    chord_name_color: str = "#1a1a2e"
    chord_name_font: str = "Georgia, 'Times New Roman', serif"
    label_size: int = 11
    label_color: str = "#666666"
    label_font: str = "Arial, Helvetica, sans-serif"
    finger_num_color: str = "#ffffff"
    finger_num_size: int = 11
    finger_num_font: str = "Arial, Helvetica, sans-serif"
    mute_color: str = "#cc3333"
    mute_size: int = 12
    fret_label_color: str = "#555555"
    fret_label_size: int = 11
    fret_label_font: str = "Arial, Helvetica, sans-serif"

    # Background
    background_color: str = "#ffffff"
    background_opacity: float = 1.0  # 0.0 = transparent

    @property
    def grid_width(self) -> int:
        """Usable width of the fretboard grid in pixels (``width - 2 * padding_side``)."""
        return self.width - 2 * self.padding_side

    @property
    def grid_height(self) -> int:
        """Usable height of the fretboard grid in pixels.

        Computed as ``height - padding_top - padding_bottom``.
        """
        return self.height - self.padding_top - self.padding_bottom

    @property
    def string_spacing(self) -> float:
        """Horizontal distance between adjacent strings in pixels."""
        return self.grid_width / 5  # 6 strings -> 5 gaps

    @property
    def fret_spacing(self) -> float:
        """Vertical distance between adjacent frets in pixels."""
        return self.grid_height / self.num_frets


STYLE_DEFAULT = DiagramStyle()
STYLE_DARK = DiagramStyle(
    background_color="#1a1a2e",
    string_color="#aaaacc",
    fret_color="#aaaacc",
    nut_color="#ccccdd",
    dot_color="#e94560",
    open_dot_color="#e94560",
    barre_color="#e94560",
    chord_name_color="#ffffff",
    label_color="#aaaacc",
    fret_label_color="#aaaacc",
    mute_color="#e94560",
)
STYLE_MINIMAL = DiagramStyle(
    chord_name_size=18,
    dot_color="#000000",
    open_dot_color="#000000",
    barre_color="#000000",
    nut_color="#000000",
    string_color="#000000",
    fret_color="#000000",
)
STYLE_PASTEL = DiagramStyle(
    dot_color="#5b7fa6",
    open_dot_color="#5b7fa6",
    barre_color="#5b7fa6",
    nut_color="#444444",
    chord_name_color="#333366",
    mute_color="#d9534f",
)


# ---------------------------------------------------------------------------
# SVG renderer
# ---------------------------------------------------------------------------


def _svg_el(tag: str, **attrs: str | int | float) -> ET.Element:
    """Create an SVG element with the given tag and attributes.

    Attribute names have underscores converted to hyphens so Python keyword
    arguments can mirror SVG attribute names (e.g. ``stroke_width`` becomes
    ``stroke-width``). All values are stringified.

    Args:
        tag: SVG element name (e.g. ``"rect"``, ``"circle"``, ``"text"``).
        **attrs: Attribute key-value pairs. Underscores in keys are replaced
            with hyphens.

    Returns:
        A new ``xml.etree.ElementTree.Element``.
    """
    clean = {k.replace("_", "-"): str(v) for k, v in attrs.items()}
    return ET.Element(tag, clean)


def _sub(parent: ET.Element, tag: str, **attrs: str | int | float) -> ET.Element:
    """Create an SVG child element and append it to *parent*.

    Convenience wrapper around :func:`_svg_el` that also appends the new
    element to the parent.

    Args:
        parent: The parent SVG element to append to.
        tag: SVG element name.
        **attrs: Attribute key-value pairs (same rules as :func:`_svg_el`).

    Returns:
        The newly created and appended ``Element``.
    """
    el = _svg_el(tag, **attrs)
    parent.append(el)
    return el


def render_svg(chord: ChordDiagram, style: DiagramStyle = STYLE_DEFAULT) -> str:
    """Render a chord diagram as an SVG string.

    Args:
        chord: The chord fingering to render.
        style: Visual theme. Defaults to ``STYLE_DEFAULT``.

    Returns:
        A complete SVG document as a string (no XML declaration).

    Example::

        svg = render_svg(ChordDiagram("Am", frets=[-1, 0, 2, 2, 1, 0]))
        with open("Am.svg", "w") as f:
            f.write(svg)
    """
    s = style
    W, H = s.width, s.height
    ss = s.string_spacing
    fs = s.fret_spacing
    left = s.padding_side
    top = s.padding_top

    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(W),
            "height": str(H),
            "viewBox": f"0 0 {W} {H}",
        },
    )

    # Background
    if s.background_opacity > 0:
        _sub(
            svg,
            "rect",
            x="0",
            y="0",
            width=str(W),
            height=str(H),
            fill=s.background_color,
            opacity=str(s.background_opacity),
        )

    # Chord name
    _sub(
        svg,
        "text",
        x=str(W // 2),
        y=str(top - 52 + s.chord_name_size * 0.37),
        text_anchor="middle",
        font_family=s.chord_name_font,
        font_size=str(s.chord_name_size),
        font_weight="bold",
        fill=s.chord_name_color,
    ).text = chord.name

    # Optional label
    if chord.label:
        _sub(
            svg,
            "text",
            x=str(W // 2),
            y=str(top - 34 + s.label_size * 0.37),
            text_anchor="middle",
            font_family=s.label_font,
            font_size=str(s.label_size),
            fill=s.label_color,
        ).text = chord.label

    # Nut or base-fret marker
    if chord.base_fret == 1:
        _sub(
            svg,
            "rect",
            x=str(left),
            y=str(top),
            width=str(s.grid_width),
            height=str(s.nut_thickness),
            fill=s.nut_color,
        )
        grid_top = top + s.nut_thickness
    else:
        # Show fret number to the left, centered in the first fret space
        # Offset enough to clear any barre overhang (dot_r past the first string)
        grid_top = top
        _barre_overhang = ss * s.dot_radius_frac
        _sub(
            svg,
            "text",
            x=str(left - _barre_overhang - 4),
            y=str(grid_top + fs * 0.5 + s.fret_label_size * 0.37),
            text_anchor="end",
            font_family=s.fret_label_font,
            font_size=str(s.fret_label_size),
            fill=s.fret_label_color,
        ).text = str(chord.base_fret)

    # Fret lines
    for fi in range(s.num_frets + 1):
        y = grid_top + fi * fs
        _sub(
            svg,
            "line",
            x1=str(left),
            y1=str(y),
            x2=str(left + s.grid_width),
            y2=str(y),
            stroke=s.fret_color,
            stroke_width=str(s.fret_thickness),
        )

    # String lines
    for si in range(6):
        x = left + si * ss
        _sub(
            svg,
            "line",
            x1=str(x),
            y1=str(grid_top),
            x2=str(x),
            y2=str(grid_top + s.num_frets * fs),
            stroke=s.string_color,
            stroke_width=str(s.string_thickness),
        )

    dot_r = ss * s.dot_radius_frac
    open_r = ss * s.open_dot_radius_frac

    # Barre arc
    if chord.barre:
        b_fret, b_lo, b_hi = chord.barre  # 1-indexed strings
        b_fret_rel = b_fret
        by = grid_top + (b_fret_rel - 0.5) * fs
        bx1 = left + (b_lo - 1) * ss - dot_r  # extend past left string
        bx2 = left + (b_hi - 1) * ss + dot_r  # extend past right string
        bw = bx2 - bx1
        bh = dot_r * 2
        rx = dot_r
        _sub(
            svg,
            "rect",
            x=str(bx1),
            y=str(by - dot_r),
            width=str(bw),
            height=str(bh),
            rx=str(rx),
            ry=str(rx),
            fill=s.barre_color,
            opacity=str(s.barre_opacity),
        )
        # Finger labels on each barre-covered string that isn't fretted elsewhere
        barre_finger = None
        for si2 in range(6):
            if (
                chord.barre[1] <= si2 + 1 <= chord.barre[2]
                and chord.frets[si2] == chord.barre[0]
                and chord.fingers[si2] > 0
            ):
                barre_finger = chord.fingers[si2]
                break
        if barre_finger:
            for si2 in range(6):
                str_num = si2 + 1
                if not (b_lo <= str_num <= b_hi):
                    continue
                # Show finger number on strings where the barre is the active fret
                # (i.e. the string's fret matches the barre fret)
                if chord.frets[si2] != b_fret:
                    continue
                bx = left + si2 * ss
                _sub(
                    svg,
                    "text",
                    x=str(bx - s.finger_num_size * 0.3),
                    y=str(by + s.finger_num_size * 0.37),
                    font_family=s.finger_num_font,
                    font_size=str(s.finger_num_size),
                    font_weight="bold",
                    fill=s.finger_num_color,
                ).text = str(barre_finger)

    # Per-string markers
    for si in range(6):
        fret_val = chord.frets[si]
        finger = chord.fingers[si] if chord.fingers else 0
        x = left + si * ss

        if fret_val == -1:
            # Muted — draw X above the grid
            r = open_r
            yx = grid_top - r - 10
            d = r * 0.7
            _sub(
                svg,
                "line",
                x1=str(x - d),
                y1=str(yx - d),
                x2=str(x + d),
                y2=str(yx + d),
                stroke=s.mute_color,
                stroke_width=str(s.open_dot_thickness + 0.5),
                stroke_linecap="round",
            )
            _sub(
                svg,
                "line",
                x1=str(x + d),
                y1=str(yx - d),
                x2=str(x - d),
                y2=str(yx + d),
                stroke=s.mute_color,
                stroke_width=str(s.open_dot_thickness + 0.5),
                stroke_linecap="round",
            )

        elif fret_val == 0:
            # Open string; circle above grid
            yx = grid_top - open_r - 10
            _sub(
                svg,
                "circle",
                cx=str(x),
                cy=str(yx),
                r=str(open_r),
                fill="none",
                stroke=s.open_dot_color,
                stroke_width=str(s.open_dot_thickness),
            )

        else:
            # Fretted note
            fret_rel = fret_val
            # Skip if barre already covers this string/fret
            is_barre_covered = (
                chord.barre
                and chord.barre[0] == fret_val
                and chord.barre[1] <= si + 1 <= chord.barre[2]
            )
            dy = grid_top + (fret_rel - 0.5) * fs
            if not is_barre_covered:
                _sub(svg, "circle", cx=str(x), cy=str(dy), r=str(dot_r), fill=s.dot_color)
            # Finger number label inside dot (skip if barre-covered)
            if finger and finger > 0 and not is_barre_covered:
                _sub(
                    svg,
                    "text",
                    x=str(x - s.finger_num_size * 0.3),
                    y=str(dy + s.finger_num_size * 0.37),
                    font_family=s.finger_num_font,
                    font_size=str(s.finger_num_size),
                    font_weight="bold",
                    fill=s.finger_num_color,
                ).text = str(finger)

    return ET.tostring(svg, encoding="unicode", xml_declaration=False)


# ---------------------------------------------------------------------------
# PNG export
# ---------------------------------------------------------------------------


def render_png(
    chord: ChordDiagram,
    style: DiagramStyle = STYLE_DEFAULT,
    scale: float = 2.0,
) -> bytes:
    """Render a chord diagram as PNG bytes.

    Requires the ``cairosvg`` package and system ``libcairo``. Install with
    ``uv add fretsy --extra png`` (macOS also needs ``brew install cairo``).

    On macOS with Homebrew, the function automatically sets
    ``DYLD_FALLBACK_LIBRARY_PATH`` so ``cairocffi`` can find ``libcairo``.

    Args:
        chord: The chord fingering to render.
        style: Visual theme. Defaults to ``STYLE_DEFAULT``.
        scale: Resolution multiplier. ``2.0`` (default) produces a 2x image.

    Returns:
        Raw PNG image data as bytes.

    Raises:
        ImportError: If ``cairosvg`` is not installed.
    """
    import os
    import sys

    # macOS + Homebrew: cairocffi needs help finding libcairo
    if sys.platform == "darwin" and "DYLD_FALLBACK_LIBRARY_PATH" not in os.environ:
        brew_lib = "/opt/homebrew/lib"
        if Path(brew_lib, "libcairo.dylib").exists():
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = brew_lib

    try:
        import cairosvg  # pyrefly: ignore[missing-import]
    except ImportError as err:
        raise ImportError("cairosvg is required for PNG export: uv add fretsy --extra png") from err
    svg_str = render_svg(chord, style)
    result = cairosvg.svg2png(
        bytestring=svg_str.encode(),
        scale=scale,
    )
    assert isinstance(result, bytes)  # always bytes when no write_to is given
    return result


def save(
    chord: ChordDiagram,
    path: str | Path,
    style: DiagramStyle = STYLE_DEFAULT,
    fmt: str = "auto",
    scale: float = 2.0,
) -> Path:
    """Save a chord diagram to a file.

    Creates parent directories automatically.

    Args:
        chord: The chord fingering to render.
        path: Output file path. Can be a string or ``Path``.
        style: Visual theme. Defaults to ``STYLE_DEFAULT``.
        fmt: Output format — ``"svg"``, ``"png"``, or ``"auto"`` (default).
            When ``"auto"``, the format is inferred from the file extension.
        scale: PNG resolution multiplier (ignored for SVG).

    Returns:
        The resolved output ``Path``.

    Raises:
        ValueError: If *fmt* is not ``"svg"``, ``"png"``, or ``"auto"``.

    Example::

        save(chord, "output/Am.svg")
        save(chord, "output/Am.png", scale=3.0, style=STYLE_DARK)
    """
    path = Path(path)
    resolved_fmt = fmt
    if fmt == "auto":
        resolved_fmt = path.suffix.lstrip(".").lower() or "png"

    path.parent.mkdir(parents=True, exist_ok=True)
    if resolved_fmt == "svg":
        path.write_text(render_svg(chord, style), encoding="utf-8")
    elif resolved_fmt == "png":
        path.write_bytes(render_png(chord, style, scale=scale))
    else:
        raise ValueError(f"Unsupported format: {resolved_fmt!r}. Use 'svg' or 'png'.")
    return path


def save_batch(
    chords: list[ChordDiagram],
    directory: str | Path,
    style: DiagramStyle = STYLE_DEFAULT,
    fmt: str = "png",
    scale: float = 2.0,
    name_fn: Callable[[ChordDiagram, int], str] | None = None,
) -> list[Path]:
    """Save multiple chord diagrams to a directory.

    Filenames default to the chord name (e.g. ``Am.png``). Duplicate names are
    auto-suffixed (``Am.png``, ``Am_2.png``). Slashes and spaces in names are
    replaced with underscores.

    Args:
        chords: List of chord fingerings to render.
        directory: Output directory. Created if it doesn't exist.
        style: Visual theme applied to all diagrams.
        fmt: Output format — ``"svg"`` or ``"png"`` (default).
        scale: PNG resolution multiplier (ignored for SVG).
        name_fn: Optional callable ``(chord, index) -> str`` that returns the
            filename stem for each chord. When ``None``, uses ``chord.name``.

    Returns:
        List of output ``Path`` objects, one per chord.

    Example::

        from fretsy import save_batch, BEGINNER_CHORDS, STYLE_DARK

        save_batch(BEGINNER_CHORDS, "output/", fmt="svg")
        save_batch(
            BEGINNER_CHORDS, "output/",
            name_fn=lambda c, i: f"{i:02d}_{c.name}",
        )
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    saved = []
    counts: dict[str, int] = {}
    for i, chord in enumerate(chords):
        stem = name_fn(chord, i) if name_fn else chord.name
        # Sanitize for filesystem
        stem = stem.replace("/", "_").replace("\\", "_").replace(" ", "_")
        counts[stem] = counts.get(stem, 0) + 1
        if counts[stem] > 1:
            stem = f"{stem}_{counts[stem]}"
        out = save(chord, directory / f"{stem}.{fmt}", style=style, fmt=fmt, scale=scale)
        saved.append(out)
    return saved
