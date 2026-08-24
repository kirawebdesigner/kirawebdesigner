#!/usr/bin/env python3
"""Turn a photo into a lightweight SVG dot-matrix portrait.

Optional local tool: install Pillow with `python -m pip install pillow`, then run:
python scripts/dotify.py me.png -o assets/portrait --cols 88 --equalize --detail 0.5 --color
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from xml.sax.saxutils import escape

try:
    from PIL import Image, ImageEnhance, ImageOps
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required for portrait generation. Install it with: python -m pip install pillow") from exc


def luminance(rgb: tuple[int, int, int]) -> float:
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("assets/portrait"))
    parser.add_argument("--cols", type=int, default=88)
    parser.add_argument("--detail", type=float, default=0.5)
    parser.add_argument("--equalize", action="store_true")
    parser.add_argument("--color", action="store_true")
    parser.add_argument("--circle", action="store_true")
    args = parser.parse_args()

    image = Image.open(args.image).convert("RGBA")
    if args.circle:
        side = min(image.size)
        left = (image.width - side) // 2
        top = (image.height - side) // 2
        image = image.crop((left, top, left + side, top + side))
    aspect = image.height / image.width
    rows = max(1, round(args.cols * aspect * 0.52))
    image = image.resize((args.cols, rows), Image.Resampling.LANCZOS)
    rgb_image = image.convert("RGB")
    if args.equalize:
        gray = ImageOps.equalize(ImageOps.grayscale(rgb_image))
        gray = ImageEnhance.Contrast(gray).enhance(1 + args.detail)
    else:
        gray = ImageEnhance.Contrast(ImageOps.grayscale(rgb_image)).enhance(1 + args.detail)

    cell = 10
    width, height = args.cols * cell, rows * cell
    dots: list[str] = []
    for y in range(rows):
        for x in range(args.cols):
            alpha = image.getpixel((x, y))[3] / 255
            if alpha < 0.05:
                continue
            brightness = gray.getpixel((x, y)) / 255
            radius = 1.0 + (1 - brightness) * 3.3
            color = rgb_image.getpixel((x, y)) if args.color else (63, 185, 80)
            fill = "#%02x%02x%02x" % color
            dots.append(f'<circle cx="{x*cell+cell/2:.1f}" cy="{y*cell+cell/2:.1f}" r="{radius:.2f}" fill="{fill}" fill-opacity="{alpha:.3f}"/>')

    clip = ""
    if args.circle:
        clip = f'<defs><clipPath id="portrait-circle"><circle cx="{width/2}" cy="{height/2}" r="{min(width,height)/2}"/></clipPath></defs>'
        dots = [f'<g clip-path="url(#portrait-circle)">', *dots, "</g>"]
    body = f'<rect width="{width}" height="{height}" fill="none"/>\n{clip}\n' + "\n".join(dots)
    output = args.output.with_suffix(".svg")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Dot matrix portrait">\n{body}\n</svg>\n', encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
