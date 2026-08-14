#!/usr/bin/env python3
"""
Karis Missions International — static site builder.

Every page in `src/pages/` holds only its own content. The shared chrome
(document head, navigation, footer) lives once in `src/partials/` and is
injected here, so a nav change is one edit rather than twenty.

Output is plain static HTML in the project root — no server, no runtime
dependency. Open index.html directly or host it anywhere.

Usage:  python3 tools/build.py
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PAGES = SRC / "pages"
PARTIALS = SRC / "partials"
DATA = SRC / "data"

# The live address. Change this if a custom domain is added later, then
# rebuild: it drives canonical URLs, share cards, sitemap.xml and schema.
SITE_URL = "https://richelcode.github.io/karis-missions-website"
SITE_NAME = "Karis Missions International"

META_BLOCK = re.compile(r"^\s*<!--meta(.*?)-->", re.DOTALL)


# ---------------------------------------------------------------- helpers

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_meta(raw: str) -> tuple[dict[str, str], str]:
    """Split a page file into its `<!--meta ... -->` header and its body."""
    match = META_BLOCK.match(raw)
    if not match:
        return {}, raw

    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, raw[match.end():].lstrip("\n")


def human_size(num_bytes: int) -> str:
    if num_bytes >= 1_048_576:
        return f"{num_bytes / 1_048_576:.1f} MB"
    return f"{max(1, round(num_bytes / 1024))} KB"


def substitute(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


# ---------------------------------------------------------------- navigation

# Grouped so the header carries six predictable choices instead of twelve.
NAV: list[dict] = [
    {"label": "About", "href": "about.html", "children": [
        {"label": "Who We Are", "href": "about.html"},
        {"label": "What We Believe", "href": "beliefs.html"},
        {"label": "Places of Worship", "href": "assemblies.html"},
        {"label": "Contact", "href": "contact.html"},
    ]},
    {"label": "Know & Grow", "href": "know-grow.html", "children": [
        {"label": "Know & Grow", "href": "know-grow.html"},
        {"label": "Devotions", "href": "devotions.html"},
        {"label": "Articles", "href": "articles.html"},
        {"label": "Watch", "href": "videos.html"},
        {"label": "Books & Publications", "href": "books.html"},
    ]},
    {"label": "Missions", "href": "missions.html", "children": [
        {"label": "Our Missions Work", "href": "missions.html"},
        {"label": "Serve in Ghana", "href": "serve-ghana.html"},
        {"label": "Missions for Children", "href": "missions-children.html"},
        {"label": "Volunteer Application", "href": "volunteer-application.html"},
        {"label": "Partner With Karis", "href": "partner.html"},
    ]},
    {"label": "Academy", "href": "academy.html"},
    {"label": "Resources", "href": "resources.html", "children": [
        {"label": "Resource Center", "href": "resources.html"},
        {"label": "Gospel Tracts", "href": "resources.html#tracts"},
        {"label": "Outreach Materials", "href": "resources.html#outreach"},
    ]},
    {"label": "Prayer", "href": "prayer.html"},
]

FOOTER_COLUMNS = [
    ("Explore", [
        ("About Karis", "about.html"),
        ("What We Believe", "beliefs.html"),
        ("Know & Grow", "know-grow.html"),
        ("Karis Academy", "academy.html"),
        ("Resource Center", "resources.html"),
    ]),
    ("Get Involved", [
        ("Our Missions Work", "missions.html"),
        ("Serve in Ghana", "serve-ghana.html"),
        ("Volunteer Application", "volunteer-application.html"),
        ("Partner With Karis", "partner.html"),
        ("Give", "give.html"),
    ]),
    ("Connect", [
        ("Prayer Center", "prayer.html"),
        ("Places of Worship", "assemblies.html"),
        ("Contact Us", "contact.html"),
        ("Privacy Policy", "privacy.html"),
        ("Safeguarding", "safeguarding.html"),
    ]),
]


CHEVRON = ('<svg class="chev" viewBox="0 0 12 8" aria-hidden="true">'
           '<path d="M1 1.5 6 6.5l5-5" fill="none" stroke="currentColor" stroke-width="2" '
           'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def render_nav(current: str) -> str:
    """
    Primary navigation.

    Every top-level item is a real link to its own page. Groups additionally get
    a separate chevron button that opens the submenu, so the label stays
    clickable and the disclosure stays operable by keyboard and on touch.
    """
    out = []
    for i, item in enumerate(NAV):
        hrefs = {item["href"]} | {c["href"].split("#")[0] for c in item.get("children", [])}
        is_active = current in hrefs
        current_attr = ' aria-current="page"' if current == item["href"] else ""
        label = escape(item["label"])

        if "children" not in item:
            out.append(
                f'<li class="nav-item{" active" if is_active else ""}">'
                f'<a class="nav-link" href="{item["href"]}"{current_attr}>{label}</a></li>'
            )
            continue

        menu_id = f"menu-{i}"
        links = "".join(
            f'<li><a href="{c["href"]}"'
            f'{" aria-current=\"page\"" if current == c["href"] else ""}>'
            f'{escape(c["label"])}</a></li>'
            for c in item["children"]
        )
        out.append(
            f'<li class="nav-item has-menu{" active" if is_active else ""}">'
            f'<a class="nav-link" href="{item["href"]}"{current_attr}>{label}</a>'
            f'<button type="button" class="nav-toggle" aria-expanded="false" '
            f'aria-controls="{menu_id}" aria-label="Show {label} menu">{CHEVRON}</button>'
            f'<ul class="submenu" id="{menu_id}">{links}</ul></li>'
        )
    return "".join(out)


def render_footer_columns() -> str:
    out = []
    for heading, links in FOOTER_COLUMNS:
        items = "".join(f'<li><a href="{href}">{label}</a></li>' for label, href in links)
        out.append(f"<div><h2 class=footer-head>{heading}</h2><ul class=footer-list>{items}</ul></div>")
    return "".join(out)


# ---------------------------------------------------------------- downloads

def load_downloads() -> dict:
    """
    Read the download manifest and stamp each entry with the real file size
    from disk, so the site can never advertise a size it does not have.
    """
    manifest = json.loads(read(DATA / "downloads.json"))
    for group in manifest["groups"]:
        kept = []
        for item in group["items"]:
            files = []
            for f in item["files"]:
                path = ROOT / f["path"]
                if not path.exists():
                    print(f"  ! missing download: {f['path']}")
                    continue
                f["size"] = human_size(path.stat().st_size)
                files.append(f)
            if not files:
                continue
            item["files"] = files
            kept.append(item)
        group["items"] = kept
    return manifest


def render_downloads(manifest: dict) -> str:
    """Build the Resource Center sections from the manifest."""
    blocks = []
    for group in manifest["groups"]:
        cards = []
        for item in group["items"]:
            thumb = (
                f'<div class=dl-thumb><img src="{item["preview"]}" alt="" loading=lazy '
                f'width=560 height=740></div>'
                if item.get("preview") else ""
            )
            tags = "".join(f'<span class=tag>{t}</span>' for t in item.get("tags", []))
            buttons = "".join(
                f'<a class="btn btn-sm {"btn-navy" if n == 0 else "btn-quiet"}" '
                f'href="{f["path"]}" download>'
                f'<svg class=ico viewBox="0 0 16 16" aria-hidden=true>'
                f'<path d="M8 1v9m0 0L4.5 6.5M8 10l3.5-3.5M2 13h12" fill=none '
                f'stroke=currentColor stroke-width=1.6 stroke-linecap=round '
                f'stroke-linejoin=round/></svg>'
                f'{f["label"]} <span class=dl-meta>{f["size"]}</span></a>'
                for n, f in enumerate(item["files"])
            )
            cards.append(
                f'<article class="card dl-card" data-search="{item["title"].lower()} '
                f'{" ".join(item.get("tags", [])).lower()} {item["description"].lower()}">'
                f'{thumb}<div class=dl-body><div class=tags>{tags}</div>'
                f'<h3>{item["title"]}</h3><p>{item["description"]}</p>'
                f'<div class=dl-actions>{buttons}</div></div></article>'
            )
        blocks.append(
            f'<section class=dl-group id="{group["id"]}">'
            f'<div class=section-header><h2>{group["title"]}</h2>'
            f'<p class=lead>{group["intro"]}</p></div>'
            f'<div class="grid grid-3 dl-grid">{"".join(cards)}</div></section>'
        )
    return "".join(blocks)


# ---------------------------------------------------------------- videos

PLAY_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
             '<path d="M8 5.5v13l11-6.5z" fill="currentColor"/></svg>')


def load_videos() -> dict:
    """Read the video manifest produced by tools/fetch_videos.py."""
    path = DATA / "videos.json"
    if not path.exists():
        return {"videos": [], "channel_url": "https://youtube.com/@isharethatyoumayknow"}
    data = json.loads(read(path))
    kept = []
    for v in data.get("videos", []):
        if v.get("thumbnail") and not (ROOT / v["thumbnail"]).exists():
            print(f"  ! missing video thumbnail: {v['thumbnail']}")
            v["thumbnail"] = None
        kept.append(v)
    data["videos"] = kept
    return data


def render_video(v: dict, featured: bool = False) -> str:
    """
    A click-to-play facade. The thumbnail is served from our own domain, so
    nothing is requested from YouTube until the visitor presses play.
    """
    title = escape(v["title"])
    thumb = (f'<img src="{v["thumbnail"]}" alt="" loading="{"eager" if featured else "lazy"}" '
             f'width="960" height="540">' if v.get("thumbnail") else "")
    desc = f'<p>{escape(v["description"])}</p>' if v.get("description") else ""
    heading = "h2" if featured else "h3"

    player = (
        f'<div class="video-frame">'
        f'<button type="button" class="video-play" data-video="{v["id"]}" '
        f'data-title="{title}" aria-label="Play video: {title}">'
        f'{thumb}<span class="video-play-btn" aria-hidden="true">{PLAY_ICON}</span>'
        f'</button></div>'
    )
    body = (
        f'<div class="video-body">'
        f'<p class="video-date">{escape(v.get("published_label", ""))}</p>'
        f'<{heading}>{title}</{heading}>{desc}'
        f'<a class="link-more" href="https://www.youtube.com/watch?v={v["id"]}" '
        f'rel="noopener">Open on YouTube</a></div>'
    )
    cls = "video-card featured" if featured else "video-card"
    return f'<article class="{cls}">{player}{body}</article>'


def render_videos(data: dict) -> str:
    videos = data.get("videos", [])
    if not videos:
        return ('<p class="dl-empty">The video library is being loaded. '
                f'<a href="{data["channel_url"]}" rel="noopener">Watch on YouTube</a>.</p>')

    latest, rest = videos[0], videos[1:]
    out = [render_video(latest, featured=True)]
    if rest:
        out.append('<h2 class="video-more-head">More from the channel</h2>')
        out.append('<div class="video-grid">'
                   + "".join(render_video(v) for v in rest) + "</div>")
    return "".join(out)


# ---------------------------------------------------------------- articles

def load_articles() -> dict:
    """Read the article manifest produced by tools/fetch_articles.py."""
    path = DATA / "articles.json"
    if not path.exists():
        return {"articles": [], "profile_url": "https://medium.com/@andrewsasiedu",
                "author": "Karis Missions International"}
    return json.loads(read(path))


def render_article(a: dict, featured: bool = False) -> str:
    """
    A card that links out. The piece itself lives on Medium; we carry the
    title, the date, how long it takes to read, and a single preview line.
    """
    heading = "h2" if featured else "h3"
    meta = " &middot; ".join(filter(None, [
        escape(a.get("published_label", "")), escape(a.get("reading_time", ""))]))
    tags = "".join(f'<span class="tag">{escape(t)}</span>' for t in a.get("tags", []))
    teaser = f'<p class="article-teaser">{escape(a["teaser"])}</p>' if a.get("teaser") else ""

    image = (
        f'<span class="article-thumb">'
        f'<img src="{a["image"]}" alt="" loading="{"eager" if featured else "lazy"}" '
        f'width="1280" height="1024"></span>'
        if a.get("image") else ""
    )

    return (
        f'<article class="article-card{" featured" if featured else ""}">'
        f'<a class="article-link" href="{a["url"]}" rel="noopener">'
        f'{image}'
        f'<span class="article-text">'
        f'<p class="article-meta">{meta}</p>'
        f'<{heading}>{escape(a["title"])}</{heading}>'
        f'{teaser}'
        f'<div class="tags">{tags}</div>'
        f'<span class="link-more">Read on Medium</span>'
        f'</span></a></article>'
    )


def render_articles(data: dict) -> str:
    items = data.get("articles", [])
    if not items:
        return ('<p class="dl-empty">The first articles are being written. '
                f'<a href="{data["profile_url"]}" rel="noopener">Follow on Medium</a> '
                'to see them as they are published.</p>')

    latest, rest = items[0], items[1:]
    out = [render_article(latest, featured=True)]
    if rest:
        out.append('<h2 class="video-more-head">More writing</h2>')
        out.append('<div class="article-grid">'
                   + "".join(render_article(a) for a in rest) + "</div>")
    return "".join(out)


# ---------------------------------------------------------------- page build

def build_page(path: Path, partials: dict[str, str], downloads_html: str,
               manifest: dict, videos: dict, articles: dict) -> str:
    meta, body = parse_meta(read(path))
    slug = path.name

    title = meta.get("title", SITE_NAME)
    full_title = title if slug == "index.html" else f"{title} | {SITE_NAME}"
    description = meta.get("description", "")
    canonical = f"{SITE_URL}/{'' if slug == 'index.html' else slug}"

    # Page hero (every page except the home page, which builds its own).
    hero = ""
    if meta.get("hero_title"):
        crumb = (
            f'<nav class=crumbs aria-label=Breadcrumb><ol>'
            f'<li><a href="index.html">Home</a></li>'
            f'<li aria-current=page>{meta.get("crumb", title)}</li></ol></nav>'
        )
        hero_text = f'<p>{meta["hero_text"]}</p>' if meta.get("hero_text") else ""
        hero = (
            f'<section class=page-hero><div class=container>{crumb}'
            f'<p class=eyebrow>{meta.get("hero_eyebrow", SITE_NAME)}</p>'
            f'<h1>{meta["hero_title"]}</h1>{hero_text}</div></section>'
        )

    body = body.replace("{{DOWNLOADS}}", downloads_html)
    body = body.replace("{{VIDEOS}}", render_videos(videos))
    body = body.replace("{{ARTICLES}}", render_articles(articles))
    body = body.replace("{{ARTICLE_COUNT}}", str(len(articles.get("articles", []))))
    body = body.replace("{{VIDEO_COUNT}}", str(len(videos.get("videos", []))))
    # DOWNLOAD_COUNT counts resources as the visitor sees them (one card each),
    # matching the live counter on the Resource Center. DOWNLOAD_FILES counts
    # every individual file, since one resource may ship several formats.
    body = body.replace("{{DOWNLOAD_COUNT}}", str(
        sum(len(g["items"]) for g in manifest["groups"])
    ))
    body = body.replace("{{DOWNLOAD_FILES}}", str(
        sum(len(i["files"]) for g in manifest["groups"] for i in g["items"])
    ))

    schema = partials["schema"] if slug == "index.html" else ""

    return substitute(partials["base"], {
        "TITLE": full_title,
        "DESCRIPTION": description,
        "CANONICAL": canonical,
        "OG_IMAGE": f"{SITE_URL}/{meta.get('og_image', 'assets/img/og-default.jpg')}",
        "OG_TYPE": "website",
        "BODY_CLASS": meta.get("body_class", ""),
        "SCHEMA": schema,
        "NAV": render_nav(slug),
        "HERO": hero,
        "CONTENT": body,
        "FOOTER_COLUMNS": render_footer_columns(),
        "YEAR": str(date.today().year),
    })


def write_sitemap(slugs: list[str]) -> None:
    urls = "".join(
        f"<url><loc>{SITE_URL}/{'' if s == 'index.html' else s}</loc>"
        f"<changefreq>monthly</changefreq>"
        f"<priority>{'1.0' if s == 'index.html' else '0.7'}</priority></url>"
        for s in sorted(slugs) if s != "404.html"
    )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>\n",
        encoding="utf-8",
    )
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )


def main() -> int:
    partials = {p.stem: read(p) for p in PARTIALS.glob("*.html")}
    manifest = load_downloads()
    downloads_html = render_downloads(manifest)
    videos = load_videos()
    articles = load_articles()

    print("\nBuilding pages")
    slugs = []
    for page in sorted(PAGES.glob("*.html")):
        html = build_page(page, partials, downloads_html, manifest, videos, articles)
        (ROOT / page.name).write_text(html, encoding="utf-8")
        slugs.append(page.name)
        print(f"  {page.name}  {len(html) / 1024:.1f}KB")

    write_sitemap(slugs)
    print("  sitemap.xml\n  robots.txt")

    # Remove pages that used to exist but are no longer part of the site.
    for stale in ROOT.glob("*.html"):
        if stale.name not in slugs:
            stale.unlink()
            print(f"  removed stale page: {stale.name}")

    print(f"\nDone — {len(slugs)} pages.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
