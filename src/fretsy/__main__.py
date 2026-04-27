"""CLI entry point: dump all chord diagrams to a directory.

Usage:
    python -m fretsy [output_dir] [--fmt svg|png] [--scale N] [--style NAME]

Examples:
    python -m fretsy                          # SVGs to ./fretsy_output/
    python -m fretsy out --fmt png            # PNGs to ./out/
    python -m fretsy out --style dark         # dark theme
    python -m fretsy out --scale 3            # high-res PNGs
"""

from __future__ import annotations

import argparse
import time

from fretsy._diagram import (
    STYLE_DARK,
    STYLE_DEFAULT,
    STYLE_MINIMAL,
    STYLE_PASTEL,
    save_batch,
)
from fretsy._library import CHORDS

STYLES = {
    "default": STYLE_DEFAULT,
    "dark": STYLE_DARK,
    "minimal": STYLE_MINIMAL,
    "pastel": STYLE_PASTEL,
}


def main() -> None:
    """CLI entry point: export all built-in chord diagrams to a directory."""
    parser = argparse.ArgumentParser(
        prog="fretsy",
        description="Export all built-in chord diagrams to a directory.",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="fretsy_output",
        help="Output directory (default: fretsy_output)",
    )
    parser.add_argument(
        "--fmt",
        choices=["svg", "png"],
        default="svg",
        help="Output format (default: svg)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=2.0,
        help="PNG scale factor (default: 2.0)",
    )
    parser.add_argument(
        "--style",
        choices=list(STYLES.keys()),
        default="default",
        help="Visual theme (default: default)",
    )

    args = parser.parse_args()
    style = STYLES[args.style]

    print(f"Exporting {len(CHORDS)} chords as {args.fmt.upper()} to {args.output}/")
    print(f"Style: {args.style}, scale: {args.scale}")

    start = time.time()
    paths = save_batch(
        CHORDS,
        directory=args.output,
        fmt=args.fmt,
        scale=args.scale,
        style=style,
        name_fn=lambda chord, i: f"{i:04d}_{chord.name}",
    )
    elapsed = time.time() - start

    print(f"Done — {len(paths)} files in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
