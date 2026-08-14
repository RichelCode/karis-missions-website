#!/usr/bin/env python3
"""
Generate the raster icons and the social share image.

  assets/img/apple-touch-icon.png   180x180 home-screen icon
  assets/img/favicon-32.png          32x32  fallback favicon
  assets/img/og-default.jpg         1200x630 link preview card

Run from the project root:  python3 tools/make_icons.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"

NAVY = (15, 46, 79)
DEEP = (8, 28, 49)
RED = (198, 40, 40)
GOLD = (226, 185, 95)
CREAM = (248, 246, 241)

# macOS system faces, in preference order.
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]
FONT_SANS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def load_font(paths: list[str], size: int) -> ImageFont.FreeTypeFont:
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def rounded_icon(size: int) -> Image.Image:
    """Navy tile carrying the Karis lighthouse — legible at small sizes."""
    s = size * 4  # supersample, then downscale for clean edges
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = s / 64  # the favicon.svg is drawn on a 64-unit grid

    d.rounded_rectangle([0, 0, s, s], radius=14 * u, fill=NAVY)

    # Light rays from the lantern
    beam = GOLD + (178,)
    d.polygon([(23.5 * u, 15.5 * u), (11 * u, 11.5 * u), (9.6 * u, 15.8 * u), (22.2 * u, 19.8 * u)],
              fill=beam)
    d.polygon([(40.5 * u, 15.5 * u), (53 * u, 11.5 * u), (54.4 * u, 15.8 * u), (41.8 * u, 19.8 * u)],
              fill=beam)

    # Lantern room
    d.polygon([(32 * u, 5.5 * u), (35.6 * u, 12 * u), (28.4 * u, 12 * u)], fill=RED)
    d.rounded_rectangle([26.6 * u, 12 * u, 37.4 * u, 19 * u], radius=1.4 * u, fill=RED)
    d.rounded_rectangle([24.6 * u, 19 * u, 39.4 * u, 22.2 * u], radius=1.6 * u, fill=RED)

    # Tower, tapering outward toward the base
    d.polygon([(27.4 * u, 22.2 * u), (36.6 * u, 22.2 * u), (39.2 * u, 42.8 * u), (24.8 * u, 42.8 * u)],
              fill=RED)
    d.rounded_rectangle([30.4 * u, 30 * u, 33.6 * u, 42.8 * u], radius=1.2 * u, fill=NAVY)

    # Cupped hands — bottom half of an ellipse, so it reads as a bowl not a pill
    d.chord([13 * u, 21.5 * u, 51 * u, 58 * u], 0, 180, fill=CREAM)

    return im.resize((size, size), Image.LANCZOS)


def og_card() -> Image.Image:
    w, h = 1200, 630
    im = Image.new("RGB", (w, h), DEEP)
    d = ImageDraw.Draw(im)

    # Soft brand wash in the upper right.
    glow = Image.new("RGB", (w, h), DEEP)
    gd = ImageDraw.Draw(glow)
    for i in range(28, 0, -1):
        r = i * 26
        gd.ellipse([w - 250 - r, -180 - r, w - 250 + r, -180 + r],
                   fill=(DEEP[0] + i, DEEP[1] + int(i * 1.6), DEEP[2] + int(i * 2.4)))
    im = Image.blend(im, glow, 0.85)
    d = ImageDraw.Draw(im)

    # Gold rule
    d.rectangle([80, 148, 188, 154], fill=GOLD)

    f_eyebrow = load_font(FONT_SANS, 24)
    f_title = load_font(FONT_CANDIDATES, 74)
    f_sub = load_font(FONT_SANS, 29)

    d.text((80, 100), "KARIS MISSIONS INTERNATIONAL", font=f_eyebrow, fill=GOLD)
    d.text((80, 196), "Know Christ. Grow in Him.", font=f_title, fill=(255, 255, 255))
    d.text((80, 286), "Go make disciples.", font=f_title, fill=(255, 255, 255))
    d.text((80, 404), "Taking the Gospel · Making Disciples", font=f_sub, fill=(190, 208, 224))
    d.text((80, 444), "Transforming Communities", font=f_sub, fill=(190, 208, 224))
    d.text((80, 528), "I SHARE THAT YOU MAY KNOW", font=f_eyebrow, fill=(150, 175, 200))

    # Logo mark, bottom right
    mark_path = IMG / "brand" / "logo-mark.png"
    if mark_path.exists():
        mark = Image.open(mark_path).convert("RGBA").resize((190, 190), Image.LANCZOS)
        plate = Image.new("RGBA", (230, 230), (255, 255, 255, 235))
        plate_mask = Image.new("L", (230, 230), 0)
        ImageDraw.Draw(plate_mask).rounded_rectangle([0, 0, 230, 230], radius=32, fill=255)
        im.paste(plate, (w - 300, h - 300), plate_mask)
        im.paste(mark, (w - 280, h - 280), mark)

    return im


def main() -> int:
    IMG.mkdir(parents=True, exist_ok=True)

    rounded_icon(180).save(IMG / "apple-touch-icon.png", "PNG", optimize=True)
    rounded_icon(32).save(IMG / "favicon-32.png", "PNG", optimize=True)
    og_card().save(IMG / "og-default.jpg", "JPEG", quality=88, optimize=True, progressive=True)

    for name in ("apple-touch-icon.png", "favicon-32.png", "og-default.jpg"):
        p = IMG / name
        print(f"  assets/img/{name}  {p.stat().st_size / 1024:.0f}KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
