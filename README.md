# fretsy 🎸

A pure-Python library for generating guitar chord diagram images in SVG and PNG.
Ships with 3,000+ built-in chord definitions across all 12 keys.

## Install

```bash
uv add fretsy
```

SVG rendering uses only the standard library. For PNG export you also need `cairosvg` (which requires system `libcairo`):

```bash
# macOS
brew install cairo
uv add fretsy --extra png

# Ubuntu / Debian
sudo apt install libcairo2-dev
uv add fretsy --extra png
```

---

## Quick start

```python
from fretsy import ChordDiagram, save

# Define a chord by hand
chord = ChordDiagram(
    name="Am",
    frets=[-1, 0, 2, 2, 1, 0],   # one per string, low-E first
    fingers=[0, 0, 2, 3, 1, 0],  # finger numbers shown inside dots
)

save(chord, "Am.svg")   # SVG — no extra deps
save(chord, "Am.png")   # PNG — requires fretsy[png]
```

Or grab one from the built-in library:

```python
from fretsy import find_chord, save

am = find_chord("Am")[0]
save(am, "Am.svg")
```

---

## Defining chords

Every chord is a `ChordDiagram` dataclass. The only required fields are `name` and `frets`:

```python
from fretsy import ChordDiagram

# Simple open chord
e_major = ChordDiagram("E", frets=[0, 2, 2, 1, 0, 0])

# With finger numbers
a_minor = ChordDiagram("Am", frets=[-1, 0, 2, 2, 1, 0], fingers=[0, 0, 2, 3, 1, 0])

# Barre chord — barre=(fret, from_string, to_string), 1-indexed
f_major = ChordDiagram(
    "F",
    frets=[1, 1, 2, 3, 3, 1],
    fingers=[1, 1, 2, 4, 3, 1],
    barre=(1, 1, 6),
)

# High-position chord — base_fret auto-detects, or set it explicitly
bb = ChordDiagram("Bb", frets=[6, 6, 7, 8, 8, 6], barre=(6, 1, 6))
# base_fret auto-set to 6

# Optional label (subtitle shown below the chord name)
bb_a_form = ChordDiagram(
    "Bb", frets=[-1, 1, 3, 3, 3, 1], barre=(1, 2, 6), label="A-form"
)
```

### Fret notation

| Value | Meaning |
|-------|---------|
| `-1` | Muted string (drawn as ✕) |
| `0` | Open string (drawn as ○) |
| `1`+ | Fret number (filled dot on the grid) |

The `frets` list always has 6 elements, ordered low-E → high-E.

---

## Rendering

### Save to file

```python
from fretsy import save

save(chord, "chord.svg")              # SVG (format inferred from extension)
save(chord, "chord.png")              # PNG
save(chord, "chord.png", scale=3.0)   # high-res PNG (default scale=2.0)
save(chord, "out.xml", fmt="svg")     # explicit format override
```

`save()` creates parent directories automatically and returns the output `Path`.

### Get raw bytes / string

```python
from fretsy import render_svg, render_png

svg_string = render_svg(chord)              # str
png_bytes  = render_png(chord, scale=2.0)   # bytes
```

### Batch export

```python
from fretsy import save_batch, BEGINNER_CHORDS, STYLE_DARK

# Save all beginner chords as PNGs
paths = save_batch(BEGINNER_CHORDS, "output/beginners", fmt="png", scale=2.0)

# Custom filenames
paths = save_batch(
    BEGINNER_CHORDS,
    "output/numbered",
    fmt="svg",
    name_fn=lambda chord, i: f"{i:02d}_{chord.name}",
)
```

`save_batch()` auto-deduplicates filenames when multiple chords share the same name, and sanitizes slashes/spaces.

---

## Styles and themes

Pass a `DiagramStyle` (or a built-in preset) to any render/save function:

```python
from fretsy import save, STYLE_DARK

save(chord, "dark.png", style=STYLE_DARK)
```

### Built-in themes

| Preset | Look |
|--------|------|
| `STYLE_DEFAULT` | White background, navy dots |
| `STYLE_DARK` | Dark background, red/pink accents |
| `STYLE_MINIMAL` | Black and white |
| `STYLE_PASTEL` | Soft blue dots, light feel |

### Custom themes

Every visual property is configurable via `DiagramStyle`:

```python
from fretsy import DiagramStyle, save

solarized = DiagramStyle(
    background_color="#fdf6e3",
    dot_color="#268bd2",
    barre_color="#268bd2",
    chord_name_color="#073642",
    chord_name_font="'Comic Sans MS', cursive",
    width=220,
    height=260,
    num_frets=5,
)
save(chord, "solarized.svg", style=solarized)
```

For transparent backgrounds (useful for embedding in web pages):

```python
transparent = DiagramStyle(background_opacity=0.0)
svg = render_svg(chord, style=transparent)
```

---

## Built-in chord library

fretsy ships with 3,000+ chord definitions covering all 12 keys, multiple voicings, and a wide range of qualities. All chords live in a single `CHORDS` list, and convenience sublists filter by technique or quality:

```python
from fretsy import (
    CHORDS,            # master list — all 3,000+ chords
    find_chord,        # lookup by name

    # By technique
    OPEN_CHORDS,       # no barre, open strings, first position
    BARRE_CHORDS,      # uses a barre
    POWER_CHORDS,      # root + fifth (E5, A5, etc.)

    # By quality
    MAJOR_CHORDS,
    MINOR_CHORDS,      # m, m7, m9, mmaj7, etc.
    DOMINANT_CHORDS,   # 7, 9, 11, 13, 6
    DIMINISHED_CHORDS, # dim, dim7
    AUGMENTED_CHORDS,  # aug, aug7, aug9
    SUSPENDED_CHORDS,  # sus2, sus4, 7sus4

    # Special
    JAZZ_CHORDS,       # maj7, 9, 11, 13, altered
    SLASH_CHORDS,      # inversions (Am/G, C/E, etc.)
    PRIMARY_CHORDS,    # first voicing only (no "var." variants)
    BEGINNER_CHORDS,   # E, A, D, G, C, Em, Am, Dm
)
```

### Searching

```python
from fretsy import find_chord, BEGINNER_CHORDS

# All voicings of Bb (returns list[ChordDiagram])
all_bb = find_chord("Bb")

# Search within a subset
find_chord("C", chords=BEGINNER_CHORDS)  # just the open C
```

Every sublist references the same objects in `CHORDS` — no data is duplicated.

---

## Development

```bash
# Clone and set up
git clone https://github.com/OWNER/fretsy.git
cd fretsy
uv sync

# Run tests
uv run pytest

# Dump all 3,000+ chords to a directory (great for visual QA)
uv run fretsy output/              # SVGs with default theme
uv run fretsy output/ --fmt png    # PNGs
uv run fretsy output/ --style dark # dark theme
uv run fretsy output/ --scale 3    # high-res

# Also works as a module
uv run python -m fretsy output/

# Lint
uv run ruff check src/ tests/

# Auto-fix lint issues
uv run ruff check --fix src/ tests/

# Format
uv run ruff format src/ tests/

# Type check
uv run pyrefly check
```

---

## License

MIT
