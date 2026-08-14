#!/usr/bin/env python3
"""
Pull the Karis Medium feed and prepare it for the Articles page.

Writes `src/data/articles.json` with each post's title, link, date, tags and
reading time.

Deliberately does NOT copy article bodies or download Medium's images:
the writing and the artwork belong where they are published. Cards carry a
short preview line only, of the kind a link preview shows, and every card
sends the reader to Medium to read the piece.

Run whenever a new article is published:

    python3 tools/fetch_articles.py
    python3 tools/build.py
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"
IMAGES = ROOT / "assets" / "img" / "articles"

HANDLE = "andrewsasiedu"
# Medium titles the feed "Stories by <handle> on Medium"; show a real name.
AUTHOR_NAME = "Andrews Asiedu"
FEED = f"https://medium.com/feed/@{HANDLE}"
PROFILE = f"https://medium.com/@{HANDLE}"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

WORDS_PER_MINUTE = 220
TEASER_LIMIT = 130          # a link-preview line, not an excerpt of the piece

MONTHS = {m: i for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
MONTH_NAMES = ("January February March April May June July "
               "August September October November December").split()


def get_bytes(url: str) -> bytes:
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30).read()


def get(url: str) -> str:
    return get_bytes(url).decode("utf-8", errors="replace")


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60].rstrip("-")


def save_lead_image(markup: str, slug: str) -> str | None:
    """
    Save the article's own lead artwork so the card can show it without
    calling out to Medium's CDN on every page view. Only the post's own
    image is taken; Medium's tracking pixel is ignored.
    """
    for src in re.findall(r'<img[^>]+src="([^"]+)"', markup):
        if "/_/stat" in src or "medium.com/_" in src:
            continue
        # Ask the CDN for a larger rendition than the feed's default.
        full = re.sub(r"/max/\d+/", "/max/2400/", src)
        try:
            data = get_bytes(full)
        except Exception:
            continue
        if len(data) < 8000:
            continue

        IMAGES.mkdir(parents=True, exist_ok=True)
        tmp = IMAGES / f"{slug}.tmp"
        tmp.write_bytes(data)
        try:
            im = Image.open(tmp).convert("RGB")
            if im.width > 1280:
                im = im.resize((1280, round(im.height * 1280 / im.width)), Image.LANCZOS)
            dest = IMAGES / f"{slug}.jpg"
            im.save(dest, "JPEG", quality=84, optimize=True, progressive=True)
            tmp.unlink(missing_ok=True)
            print(f"  image  {dest.relative_to(ROOT)}  {im.width}x{im.height}  "
                  f"{dest.stat().st_size / 1024:.0f}KB")
            return f"assets/img/articles/{slug}.jpg"
        except Exception:
            tmp.unlink(missing_ok=True)
    return None


def cdata(field: str, item: str) -> str:
    m = re.search(rf"<{field}>\s*(?:<!\[CDATA\[(.*?)\]\]>|(.*?))\s*</{field}>",
                  item, re.S)
    if not m:
        return ""
    return html.unescape((m.group(1) or m.group(2) or "").strip())


def parse_date(raw: str) -> tuple[str, str]:
    """'Sun, 09 Aug 2026 05:59:46 GMT' -> ('2026-08-09', '9 August 2026')."""
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})", raw)
    if not m:
        return "", raw
    day, mon, year = int(m.group(1)), MONTHS.get(m.group(2), 1), m.group(3)
    return f"{year}-{mon:02d}-{day:02d}", f"{day} {MONTH_NAMES[mon - 1]} {year}"


def plain_text(markup: str) -> str:
    text = re.sub(r"<figure.*?</figure>", " ", markup, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def reading_time(markup: str) -> str:
    words = len(plain_text(markup).split())
    if not words:
        return ""
    return f"{max(1, round(words / WORDS_PER_MINUTE))} min read"


def teaser(markup: str) -> str:
    """
    One short line for the card. Medium posts open with a subtitle heading,
    which is the author's own summary and exactly the right thing to show.
    Fall back to the opening sentence only when there is no subtitle.
    """
    # Medium renders the standfirst as the first short paragraph (or an h3/h4).
    lead = re.search(r"<(?:h[34]|p)[^>]*>(.*?)</(?:h[34]|p)>", markup, re.S)
    if lead:
        line = plain_text(lead.group(1))
        if 15 <= len(line) <= 150:
            return line if line[-1] in ".?!" else line + "."

    text = plain_text(markup)
    if not text:
        return ""
    text = re.sub(r"[—–]", ",", text)
    if len(text) <= TEASER_LIMIT:
        return text
    cut = text[:TEASER_LIMIT]
    stop = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    if stop > 50:
        return cut[:stop + 1].strip()
    return cut.rsplit(" ", 1)[0].strip() + "…"


def main() -> int:
    print(f"\nFetching {FEED}")
    try:
        xml = get(FEED)
    except Exception as exc:
        print(f"error: could not read the Medium feed: {exc}", file=sys.stderr)
        return 1

    author = AUTHOR_NAME

    articles = []
    for item in re.findall(r"<item>(.*?)</item>", xml, re.S):
        body = cdata("content:encoded", item)
        published, label = parse_date(cdata("pubDate", item))
        title = cdata("title", item)
        slug = slugify(title)
        articles.append({
            "title": title,
            "slug": slug,
            "image": save_lead_image(body, slug),
            "url": cdata("link", item).split("?")[0],
            "published": published,
            "published_label": label,
            "reading_time": reading_time(body),
            "teaser": teaser(body),
            "tags": [html.unescape(t) for t in
                     re.findall(r"<category>\s*<!\[CDATA\[(.*?)\]\]>\s*</category>", item)][:3],
        })

    if not articles:
        print("warning: the feed contained no articles", file=sys.stderr)

    articles.sort(key=lambda a: a["published"], reverse=True)

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "articles.json").write_text(json.dumps({
        "_comment": ("Generated by tools/fetch_articles.py from the public Medium "
                     "feed. Re-run it after publishing, then run tools/build.py. "
                     "Article text and images are not copied: every card links "
                     "out to Medium to read the piece."),
        "author": author,
        "profile_url": PROFILE,
        "articles": articles,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n{len(articles)} article(s) written to src/data/articles.json")
    for a in articles:
        print(f"  {a['published_label']:<18} {a['reading_time']:<12} {a['title']}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
