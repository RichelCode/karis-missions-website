#!/usr/bin/env python3
"""
Karis Missions International — asset preparation.

Takes the raw ministry material in `Richeal/` and produces two web-ready trees:

  assets/downloads/  public documents, cleanly named, size-optimised
  assets/img/        photography, logos and document preview images

Run from the project root:  python3 tools/prepare_assets.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "Richeal"
DOWNLOADS = ROOT / "assets" / "downloads"
IMG = ROOT / "assets" / "img"

# Ghostscript keeps the print tracts readable while cutting them down enough to
# be reasonable to download over a phone connection.
GS_SETTINGS = "/ebook"


def log(msg: str) -> None:
    print(f"  {msg}")


def ensure_dirs() -> None:
    for d in (
        DOWNLOADS / "tracts",
        DOWNLOADS / "brand",
        DOWNLOADS / "outreach",
        IMG / "previews",
        IMG / "brand",
        IMG / "photos",
    ):
        d.mkdir(parents=True, exist_ok=True)


def compress_pdf(src: Path, dest: Path) -> None:
    """Shrink a print-resolution PDF for web download, falling back to a copy."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                "gs",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.5",
                f"-dPDFSETTINGS={GS_SETTINGS}",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                "-dDetectDuplicateImages=true",
                f"-sOutputFile={dest}",
                str(src),
            ],
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        shutil.copy2(src, dest)
        log(f"! ghostscript unavailable, copied {dest.name} unchanged")
        return

    # A compressed file that grew is not worth keeping.
    if dest.stat().st_size >= src.stat().st_size:
        shutil.copy2(src, dest)

    before = src.stat().st_size / 1_048_576
    after = dest.stat().st_size / 1_048_576
    log(f"{dest.relative_to(ROOT)}  {before:.1f}MB -> {after:.1f}MB")


def copy_doc(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    log(f"{dest.relative_to(ROOT)}  {dest.stat().st_size / 1024:.0f}KB")


def save_web_image(im: Image.Image, dest: Path, width: int, quality: int = 82) -> None:
    """Resize to `width`, then write JPEG (opaque) or PNG (has transparency)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if im.width > width:
        height = round(im.height * width / im.width)
        im = im.resize((width, height), Image.LANCZOS)

    if dest.suffix == ".png":
        im.save(dest, "PNG", optimize=True)
    else:
        im.convert("RGB").save(dest, "JPEG", quality=quality, optimize=True, progressive=True)
    log(f"{dest.relative_to(ROOT)}  {im.width}x{im.height}  {dest.stat().st_size / 1024:.0f}KB")


def render_pdf_page(pdf: Path, page: int, dpi: int = 150) -> Image.Image | None:
    """Rasterise one page of a PDF via pdftoppm."""
    out = ROOT / "tools" / "_tmp_render"
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["pdftoppm", "-png", "-r", str(dpi), "-f", str(page), "-l", str(page),
             str(pdf), str(out)],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    produced = sorted(out.parent.glob("_tmp_render*.png"))
    if not produced:
        return None
    im = Image.open(produced[0]).convert("RGB")
    im.load()
    for p in produced:
        p.unlink()
    return im


def tract_cover(pdf: Path, dest: Path) -> None:
    """
    The tracts are three-panel landscape spreads; on page 1 the right-hand
    panel is the front cover. Crop it out to use as the download card image.
    """
    im = render_pdf_page(pdf, 1)
    if im is None:
        log(f"! could not render {pdf.name}")
        return
    left = round(im.width * 2 / 3)
    save_web_image(im.crop((left, 0, im.width, im.height)), dest, 640)


def main() -> int:
    if not RAW.exists():
        print(f"error: source folder not found: {RAW}", file=sys.stderr)
        return 1

    ensure_dirs()

    print("\nGospel tracts")
    tracts = [
        ("You May Not Feel Lost.pdf", "You May Not Feel Lost.docx",
         "you-may-not-feel-lost"),
        ("Are You Ready to Meet Your Maker.pdf", "Are You Ready to Meet Your Maker.docx",
         "are-you-ready-to-meet-your-maker"),
        ("The Call to Truely Believe BROCHURE.pdf", "The Call to Truly Believe.docx",
         "the-call-to-truly-believe"),
    ]
    for pdf_name, docx_name, slug in tracts:
        pdf = RAW / "Tracts" / pdf_name
        docx = RAW / "Tracts" / docx_name
        if pdf.exists():
            compress_pdf(pdf, DOWNLOADS / "tracts" / f"{slug}.pdf")
            tract_cover(pdf, IMG / "previews" / f"{slug}.jpg")
        if docx.exists():
            copy_doc(docx, DOWNLOADS / "tracts" / f"{slug}.docx")

    print("\nBrand files")
    for src_name, dest_name in [
        ("Missions-Logo-png.png", "karis-missions-logo-full-colour.png"),
        ("Missions-Logo-2-PNG.png", "karis-missions-logo-alternate.png"),
    ]:
        src = RAW / src_name
        if src.exists():
            copy_doc(src, DOWNLOADS / "brand" / dest_name)
    for src_name, dest_name in [
        ("Missions Logo 5.pdf", "karis-missions-logo-print-a.pdf"),
        ("Missions Logo 6.pdf", "karis-missions-logo-print-b.pdf"),
    ]:
        src = RAW / src_name
        if src.exists():
            compress_pdf(src, DOWNLOADS / "brand" / dest_name)

    print("\nOutreach material")
    hangers = [
        ("Door Hangers/thumbnail-1.png", "door-hanger-sunday-service-navy.png"),
        ("Door Hangers/thumbnail-2.png", "door-hanger-sunday-service-green.png"),
    ]
    for src_name, dest_name in hangers:
        src = RAW / src_name
        if src.exists():
            copy_doc(src, DOWNLOADS / "outreach" / dest_name)
            save_web_image(Image.open(src), IMG / "previews" / dest_name.replace(".png", ".jpg"), 560)

    placard = RAW / "Placard" / "ANDY.pdf"
    if placard.exists():
        compress_pdf(placard, DOWNLOADS / "outreach" / "yard-sign-jesus-is-coming-soon.pdf")
        im = render_pdf_page(placard, 1, dpi=72)
        if im is not None:
            save_web_image(im, IMG / "previews" / "yard-sign-jesus-is-coming-soon.jpg", 640)

    signage = [
        ("Sign post/Signage 3ft by 5ft.png", "banner-3ft-by-5ft.png"),
        ("Sign post/Angled Flags.png", "feather-flag-a.png"),
        ("Sign post/Angled Flags 2.png", "feather-flag-b.png"),
        ("Sign post/Angled Flags 3.png", "feather-flag-c.png"),
    ]
    for src_name, dest_name in signage:
        src = RAW / src_name
        if src.exists():
            copy_doc(src, DOWNLOADS / "outreach" / dest_name)
            save_web_image(Image.open(src), IMG / "previews" / dest_name.replace(".png", ".jpg"), 640)

    print("\nPhotography and logos")
    lighthouse = RAW / "World ligh.png"
    if lighthouse.exists():
        save_web_image(Image.open(lighthouse), IMG / "photos" / "lighthouse-sunset.jpg", 1600, quality=80)

    # The Sunday-service poster carries the only genuine congregation photograph
    # in the source material. Crop the photo out of the poster artwork.
    poster = RAW / "Sign post" / "thumbnail-3.png"
    if poster.exists():
        im = Image.open(poster).convert("RGB")
        w, h = im.size
        crop = im.crop((0, round(h * 0.525), w, round(h * 0.757)))
        save_web_image(crop, IMG / "photos" / "congregation.jpg", 1200, quality=84)

    # A tighter crop of the same photograph, centred on the child and the adult
    # kneeling beside her, for the children's missions page.
    if poster.exists():
        pw, ph = crop.size
        kids = crop.crop((round(pw * 0.30), 0, round(pw * 0.72), ph))
        save_web_image(kids, IMG / "photos" / "children.jpg", 560, quality=86)

    # A transparent logo mark so the brand reads correctly on dark backgrounds.
    mark = RAW / "Missions-Logo-png.png"
    if mark.exists():
        save_web_image(Image.open(mark).convert("RGBA"), IMG / "brand" / "logo-mark.png", 400)

    # Tract preview images double as outreach photography on the resources page.
    for src_name, dest_name in [
        ("Tracts/Tracts 3/PHOTO-2025-05-21-20-10-23.jpg", "tract-spread-rescue.jpg"),
        ("Tracts/Tracts 4/PHOTO-2025-05-21-12-46-11.jpg", "tract-spread-believe.jpg"),
    ]:
        src = RAW / src_name
        if src.exists():
            save_web_image(Image.open(src), IMG / "previews" / dest_name, 1200, quality=80)

    print("\nDone.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
