#!/usr/bin/env python3
"""
Make the printable children's downloads:

  assets/downloads/kids/little-lights-colouring-book.pdf
      Every Little Lights picture turned into black-and-white line art.
  assets/downloads/kids/ama-shines-her-light.pdf
      The picture book, one landscape sheet per page.
  assets/img/kids/colouring/*.png
      The line art on its own, for the website.

Needs Google Chrome (to draw the SVG pictures and print the book) and
Pillow (`pip install pillow`, which the feed scripts use as well). Run it
after changing the pictures or the story, then rebuild:

    python3 tools/build.py          # the book is printed from the built page
    python3 tools/make_pdfs.py
    python3 tools/build.py          # picks up the new file sizes
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"
KIDS_IMG = ROOT / "assets" / "img" / "kids"
LINE_ART = KIDS_IMG / "colouring"
DOWNLOADS = ROOT / "assets" / "downloads" / "kids"

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FONT_DIRS = ["/System/Library/Fonts/Supplemental", "/usr/share/fonts/truetype/dejavu",
             "C:/Windows/Fonts"]

# A4 landscape at 150 dpi.
PAGE_W, PAGE_H, DPI = 1754, 1240, 150


def chrome(*args: str) -> None:
    if not Path(CHROME).exists() and not shutil.which(CHROME):
        sys.exit(f"Google Chrome not found at {CHROME}. Set CHROME=/path/to/chrome.")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--no-first-run", "--virtual-time-budget=4000", *args],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def font(names: list[str], size: int) -> ImageFont.ImageFont:
    for folder in FONT_DIRS:
        for name in names:
            path = Path(folder) / name
            if path.exists():
                return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size)


def render_svg(svg: Path, out: Path, width: int = 1600, height: int = 1040) -> Image.Image:
    chrome(f"--window-size={width},{height}", "--force-device-scale-factor=1",
           f"--screenshot={out}", svg.as_uri())
    return Image.open(out).convert("RGB")


def line_art(img: Image.Image) -> Image.Image:
    """
    Flat-colour illustrations have an edge exactly where one colour meets
    another, so an edge filter on each colour channel gives clean outlines.
    """
    edges = [ch.filter(ImageFilter.FIND_EDGES) for ch in img.split()]
    combined = ImageChops.lighter(ImageChops.lighter(edges[0], edges[1]), edges[2])
    lines = combined.point(lambda v: 255 if v > 28 else 0)
    lines = lines.filter(ImageFilter.MaxFilter(5))           # crayon-friendly thickness
    lines = lines.crop((3, 3, lines.width - 3, lines.height - 3))  # drop the frame edge
    return ImageOps.invert(lines).convert("RGB")


def colouring_book() -> None:
    kids = json.loads((DATA / "kids-devotions.json").read_text(encoding="utf-8"))
    LINE_ART.mkdir(parents=True, exist_ok=True)
    title_font = font(["Trebuchet MS Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"], 64)
    small_font = font(["Trebuchet MS.ttf", "DejaVuSans.ttf", "arial.ttf"], 34)

    def sheet(art: Image.Image, heading: str, sub: str) -> Image.Image:
        page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        draw = ImageDraw.Draw(page)
        draw.text((PAGE_W // 2, 70), heading, fill="black", font=title_font, anchor="mm")
        draw.text((PAGE_W // 2, 135), sub, fill="#444444", font=small_font, anchor="mm")
        art = art.resize((1560, int(1560 * art.height / art.width)))
        page.paste(art, ((PAGE_W - art.width) // 2, 185))
        draw.text((PAGE_W // 2, PAGE_H - 30), "Little Lights  ·  Karis Missions International",
                  fill="#888888", font=small_font, anchor="mm")
        return page

    sheets = []
    with tempfile.TemporaryDirectory() as tmp:
        cover = line_art(render_svg(KIDS_IMG / "cover.svg", Path(tmp) / "cover.png"))
        sheets.append(sheet(cover, "My Little Lights Colouring Book", "This book belongs to: ______________________"))
        for series in kids["series"]:
            for n, d in enumerate(series["devotions"], 1):
                name = Path(d["image"]).stem
                art = line_art(render_svg(ROOT / d["image"], Path(tmp) / f"{name}.png"))
                art.resize((800, 520)).save(LINE_ART / f"{name}.png", optimize=True)
                sheets.append(sheet(art, d["title"], f'{d["verse"]["ref"]}  ·  {series["title"]}, day {n}'))
                print(f"  colouring page: {d['title']}")

    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    out = DOWNLOADS / "little-lights-colouring-book.pdf"
    sheets[0].save(out, save_all=True, append_images=sheets[1:], resolution=DPI)
    print(f"  {out.relative_to(ROOT)}  {out.stat().st_size / 1024:.0f}KB, {len(sheets)} pages")


def storybook() -> None:
    built = ROOT / "storybook.html"
    if not built.exists():
        sys.exit("Run tools/build.py first: the book is printed from the built page.")
    match = re.search(r"<!--book-->(.*?)<!--/book-->", built.read_text(encoding="utf-8"), re.S)
    if not match:
        sys.exit("No <!--book--> markers in storybook.html.")

    # A bare page holding only the book, served from the project root so its
    # relative image paths and the stylesheet resolve.
    page = ROOT / "_storybook-print.html"
    page.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Young+Serif&family=Figtree:wght@400;600&display=swap">'
        '<link rel="stylesheet" href="assets/css/styles.css">'
        '<style>body{background:#fff}.book{max-width:none}</style></head>'
        f'<body class="kids-page"><div class="kids">{match.group(1)}</div></body></html>',
        encoding="utf-8")
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    out = DOWNLOADS / "ama-shines-her-light.pdf"
    try:
        chrome("--no-pdf-header-footer", f"--print-to-pdf={out}", page.as_uri())
    finally:
        page.unlink()
    print(f"  {out.relative_to(ROOT)}  {out.stat().st_size / 1024:.0f}KB")


def main() -> int:
    colouring_book()
    storybook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
