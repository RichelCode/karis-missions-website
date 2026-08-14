#!/usr/bin/env python3
"""
Sanity checks over the built site: broken internal links, missing assets,
unlabelled form controls, and images without alt text.

Run from the project root:  python3 tools/check_site.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent

HREF = re.compile(r'(?:href|src)="([^"]+)"')
ID = re.compile(r'\bid="([^"]+)"')
IMG = re.compile(r"<img\b[^>]*>", re.I)
LABEL_FOR = re.compile(r'<label[^>]*\bfor="([^"]+)"')
CONTROL = re.compile(r'<(?:input|select|textarea)\b[^>]*>', re.I)
ATTR = re.compile(r'(\w[\w-]*)="([^"]*)"')

SKIP_SCHEMES = {"http", "https", "mailto", "tel", "data"}


def attrs(tag: str) -> dict[str, str]:
    return {k.lower(): v for k, v in ATTR.findall(tag)}


def main() -> int:
    pages = sorted(ROOT.glob("*.html"))
    if not pages:
        print("No built pages found — run tools/build.py first.", file=sys.stderr)
        return 1

    ids: dict[str, set[str]] = {p.name: set(ID.findall(p.read_text(encoding="utf-8"))) for p in pages}
    problems: list[str] = []
    stats = {"links": 0, "images": 0, "controls": 0}

    for page in pages:
        html = page.read_text(encoding="utf-8")
        here = page.name

        # ---- links and asset references
        for raw in HREF.findall(html):
            target = raw.strip()
            if not target or target.startswith("#"):
                # Same-page anchor
                if len(target) > 1 and target[1:] not in ids[here]:
                    problems.append(f"{here}: anchor '{target}' has no matching id")
                continue
            if urlparse(target).scheme in SKIP_SCHEMES:
                continue

            stats["links"] += 1
            path_part, _, frag = target.partition("#")
            path_part = unquote(path_part)
            resolved = (ROOT / path_part).resolve()

            if not resolved.exists():
                problems.append(f"{here}: missing target -> {path_part}")
                continue
            if frag and path_part.endswith(".html"):
                if frag not in ids.get(Path(path_part).name, set()):
                    problems.append(f"{here}: '{path_part}#{frag}' — no such id on that page")

        # ---- images need alt (empty alt is fine: decorative)
        for tag in IMG.findall(html):
            stats["images"] += 1
            if "alt=" not in tag.lower():
                problems.append(f"{here}: <img> without alt attribute -> {tag[:80]}")

        # ---- every form control needs a label, aria-label, or wrapping label
        labelled = set(LABEL_FOR.findall(html))
        for tag in CONTROL.findall(html):
            a = attrs(tag)
            if a.get("type") in {"hidden", "submit", "button"}:
                continue
            stats["controls"] += 1
            has_label = (
                a.get("id", "") in labelled
                or "aria-label" in a
                or "aria-labelledby" in a
            )
            if not has_label:
                problems.append(f"{here}: form control without a label -> {tag[:90]}")

    print(f"\nChecked {len(pages)} pages — "
          f"{stats['links']} links, {stats['images']} images, {stats['controls']} form controls")

    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nNo problems found.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
