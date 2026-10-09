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
from datetime import date, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PAGES = SRC / "pages"
PARTIALS = SRC / "partials"
DATA = SRC / "data"

# ---------------------------------------------------------------- settings
# Everything the ministry needs to switch on lives here. Fill a value in,
# run this script, and push. Leave one empty and that feature stays off,
# with the site saying honestly what to do instead.

# Your own domain, e.g. "karismissions.org". When set, the build writes the
# CNAME file GitHub Pages needs and every canonical URL follows it.
CUSTOM_DOMAIN = ""

# Where form messages are delivered, e.g. "https://formspree.io/f/abcdwxyz".
# Until it is set, each form offers a pre-filled email instead.
FORM_ENDPOINT = ""

# The ministry's online giving page (Tithe.ly, Givebutter, PayPal, ...).
# Until it is set, the Give page directs people to phone or email.
GIVING_URL = ""
GIVING_PROVIDER = ""          # shown to donors, e.g. "Tithe.ly"

# Privacy-friendly visitor counts from GoatCounter (no cookies, no personal
# data). Enter the site code, e.g. "karis" for karis.goatcounter.com. The
# Privacy Policy updates itself to match.
GOATCOUNTER_CODE = ""

SITE_URL = (f"https://{CUSTOM_DOMAIN}" if CUSTOM_DOMAIN
            else "https://richelcode.github.io/karis-missions-website")
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
        {"label": "Plan Your Visit", "href": "visit.html"},
        {"label": "Events", "href": "events.html"},
        {"label": "Contact", "href": "contact.html"},
    ]},
    {"label": "Know & Grow", "href": "know-grow.html", "children": [
        {"label": "Know & Grow", "href": "know-grow.html"},
        {"label": "Devotions", "href": "devotions.html"},
        {"label": "Little Lights (Kids)", "href": "kids-devotions.html"},
        {"label": "Children's Storybook", "href": "storybook.html"},
        {"label": "Articles", "href": "articles.html"},
        {"label": "Watch", "href": "videos.html"},
        {"label": "Books & Publications", "href": "books.html"},
    ]},
    {"label": "Missions", "href": "missions.html", "children": [
        {"label": "Our Missions Work", "href": "missions.html"},
        {"label": "Serve in Ghana", "href": "serve-ghana.html"},
        {"label": "Missions for Children", "href": "missions-children.html"},
        {"label": "Field Notes", "href": "field-notes.html"},
        {"label": "Volunteer Application", "href": "volunteer-application.html"},
        {"label": "Partner With Karis", "href": "partner.html"},
    ]},
    {"label": "Academy", "href": "academy.html"},
    {"label": "Resources", "href": "resources.html", "children": [
        {"label": "Resource Center", "href": "resources.html"},
        {"label": "Gospel Tracts", "href": "resources.html#tracts"},
        {"label": "Outreach Materials", "href": "resources.html#outreach"},
        {"label": "For Children", "href": "resources.html#children"},
    ]},
    {"label": "Prayer", "href": "prayer.html"},
]

FOOTER_COLUMNS = [
    ("Explore", [
        ("About Karis", "about.html"),
        ("What We Believe", "beliefs.html"),
        ("Know & Grow", "know-grow.html"),
        ("Little Lights for Kids", "kids-devotions.html"),
        ("Karis Academy", "academy.html"),
        ("Resource Center", "resources.html"),
    ]),
    ("Get Involved", [
        ("Our Missions Work", "missions.html"),
        ("Serve in Ghana", "serve-ghana.html"),
        ("Field Notes", "field-notes.html"),
        ("Volunteer Application", "volunteer-application.html"),
        ("Partner With Karis", "partner.html"),
        ("Give", "give.html"),
    ]),
    ("Connect", [
        ("Prayer Center", "prayer.html"),
        ("Places of Worship", "assemblies.html"),
        ("Plan Your Visit", "visit.html"),
        ("Events", "events.html"),
        ("Contact Us", "contact.html"),
        ("Privacy Policy", "privacy.html"),
        ("Photo Credits", "credits.html"),
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
    # A single kids devotion lights up its section, like the index it belongs to.
    section = KIDS_INDEX if current.startswith("kids-") else current
    out = []
    for i, item in enumerate(NAV):
        hrefs = {item["href"]} | {c["href"].split("#")[0] for c in item.get("children", [])}
        is_active = section in hrefs
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


# ---------------------------------------------------------------- kids devotions

KIDS_INDEX = "kids-devotions.html"


def load_kids() -> dict:
    """Read Little Lights, the children's devotions, from src/data."""
    path = DATA / "kids-devotions.json"
    if not path.exists():
        return {"series": []}
    data = json.loads(read(path))
    for series in data["series"]:
        for d in series["devotions"]:
            if not (ROOT / d["image"]).exists():
                print(f"  ! missing kids illustration: {d['image']}  (run tools/make_kids_art.py)")
    return data


def render_kids_cards(data: dict) -> str:
    """Every series as its own section of picture cards."""
    out = []
    for series in data["series"]:
        cards = []
        for n, d in enumerate(series["devotions"], 1):
            cards.append(
                f'<li class="kids-card kids-{d["colour"]}" data-kids-card="{d["slug"]}">'
                f'<a href="{d["slug"]}.html">'
                f'<span class="kids-card-art"><img src="{d["image"]}" alt="" loading="lazy" '
                f'width="800" height="520"></span>'
                f'<span class="kids-card-body">'
                f'<span class="kids-step">Day {n} &middot; {escape(d["step"])}</span>'
                f'<span class="kids-card-title">{escape(d["title"])}</span>'
                f'<span class="kids-card-idea">{escape(d["big_idea"])}</span>'
                f'<span class="kids-done-badge" aria-hidden="true">&#9733; Done</span>'
                f'</span></a></li>'
            )
        count = len(series["devotions"])
        out.append(
            f'<section class="kids-series" id="{series["id"]}">'
            f'<div class="kids-series-head"><span class="kids-season">{escape(series["season"])}</span>'
            f'<h2>{escape(series["title"])}</h2><p>{escape(series["intro"])}</p></div>'
            f'<ol class="kids-cards kids-cards-{count}">{"".join(cards)}</ol></section>'
        )
    return "".join(out)


def render_kids_day(series: dict, n: int) -> tuple[dict[str, str], str]:
    """One devotion as a page: its meta block and its body."""
    days = series["devotions"]
    d = days[n]
    total = len(days)

    story = "".join(f"<p>{escape(p)}</p>" for p in d["story"])
    talk = "".join(f"<li>{escape(q)}</li>" for q in d["talk"])

    prev_link = (f'<a class="kids-pager-prev" href="{days[n - 1]["slug"]}.html">'
                 f'<span>Day {n}</span>{escape(days[n - 1]["title"])}</a>' if n > 0 else
                 f'<a class="kids-pager-prev" href="{KIDS_INDEX}"><span>Back to</span>All the stories</a>')
    next_link = (f'<a class="kids-pager-next" href="{days[n + 1]["slug"]}.html">'
                 f'<span>Day {n + 2}</span>{escape(days[n + 1]["title"])}</a>' if n + 1 < total else
                 f'<a class="kids-pager-next" href="{KIDS_INDEX}"><span>You finished!</span>See all your stars</a>')

    body = f"""
<section class="content kids kids-{d["colour"]}">
  <div class="container kids-day">
    <figure class="kids-art">
      <img src="{d["image"]}" alt="{escape(d["image_alt"])}" width="800" height="520">
      <span class="kids-art-badge">{escape(d["step"])}</span>
    </figure>

    <div class="kids-tools">
      <button type="button" class="kids-btn kids-read" data-read-aloud aria-pressed="false">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9z" fill="currentColor"/><path d="M16 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        <span>Read it to me</span>
      </button>
      <p class="kids-passage">From the Bible: <strong>{escape(d["passage"])}</strong></p>
    </div>

    <div class="kids-block kids-story" data-read>
      <h2>The story</h2>
      {story}
    </div>

    <div class="kids-block kids-idea" data-read>
      <h2>The big idea</h2>
      <p>{escape(d["big_idea"])}</p>
    </div>

    <div class="kids-block kids-verse" data-read>
      <h2>Memory verse</h2>
      <blockquote><p>&ldquo;{escape(d["verse"]["text"])}&rdquo;</p>
      <footer>{escape(d["verse"]["ref"])}</footer></blockquote>
      <p class="kids-tip">Say it three times: first in a whisper, then in your normal voice, then nice and loud!</p>
    </div>

    <div class="kids-trio">
      <div class="kids-block kids-talk" data-read>
        <h2>Talk about it</h2>
        <ul>{talk}</ul>
      </div>
      <div class="kids-block kids-try" data-read>
        <h2>Try this</h2>
        <p>{escape(d["try"])}</p>
      </div>
      <div class="kids-block kids-pray" data-read>
        <h2>Let's pray</h2>
        <p>{escape(d["prayer"])}</p>
      </div>
    </div>

    <div class="kids-finish">
      <button type="button" class="kids-btn kids-done" data-kids-done="{d["slug"]}" aria-pressed="false">
        <span class="kids-star" aria-hidden="true">&#9733;</span>
        <span class="kids-done-label">I did it!</span>
      </button>
      <p class="kids-done-note" aria-live="polite"></p>
    </div>

    <aside class="callout info kids-grownups">
      <p><strong>For grown-ups.</strong> {escape(d["grown_ups"])}</p>
    </aside>

    <nav class="kids-pager" aria-label="Devotion days">{prev_link}{next_link}</nav>
  </div>
</section>
"""
    meta = {
        "title": f'{d["title"]}: Little Lights, Day {n + 1}',
        "crumb": f"Day {n + 1}",
        "crumb_parent": f"Little Lights|{KIDS_INDEX}",
        "description": f'A devotion for children from {d["passage"]}: {d["big_idea"]} '
                       f'A Bible story, memory verse, activity and prayer from Karis Missions International.',
        "hero_eyebrow": (f'Little Lights &middot; {escape(series["title"])} &middot; '
                         f'Day {n + 1} of {total}'),
        "hero_title": escape(d["title"]),
        "hero_text": escape(d["big_idea"]),
        "body_class": "kids-page",
    }
    return meta, body


# ---------------------------------------------------------------- events

CALENDAR = ROOT / "assets" / "calendar"
DAY_NAMES = {"MO": "Monday", "TU": "Tuesday", "WE": "Wednesday", "TH": "Thursday",
             "FR": "Friday", "SA": "Saturday", "SU": "Sunday"}
DAY_ORDER = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"]
# Fixed, so the generated calendar files only change when an event does.
ICS_ANCHOR = date(2026, 1, 1)


def load_events() -> dict:
    path = DATA / "events.json"
    return json.loads(read(path)) if path.exists() else {"weekly": [], "upcoming": []}


def clock(hhmm: str) -> str:
    """'18:30' -> '6:30pm', '10:00' -> '10:00am'."""
    h, m = (int(x) for x in hhmm.split(":"))
    return f"{(h - 1) % 12 + 1}:{m:02d}{'am' if h < 12 else 'pm'}"


def ics_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def write_ics(uid: str, title: str, start: str, end: str, tz: str, location: str,
              description: str, rrule: str = "") -> str:
    """Write one calendar file and return its site path."""
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Karis Missions International//Events//EN",
        "BEGIN:VEVENT", f"UID:{uid}@karismissions", "DTSTAMP:20260101T000000Z",
        f"DTSTART;TZID={tz}:{start}", f"DTEND;TZID={tz}:{end}",
        f"SUMMARY:{ics_text(title)}", f"LOCATION:{ics_text(location)}",
        f"DESCRIPTION:{ics_text(description)}",
    ]
    if rrule:
        lines.append(f"RRULE:{rrule}")
    lines += ["END:VEVENT", "END:VCALENDAR"]
    CALENDAR.mkdir(parents=True, exist_ok=True)
    (CALENDAR / f"{uid}.ics").write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return f"assets/calendar/{uid}.ics"


def first_weekday(code: str) -> date:
    target = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"].index(code)
    return ICS_ANCHOR + timedelta(days=(target - ICS_ANCHOR.weekday()) % 7)


CAL_ICON = ('<svg class=ico viewBox="0 0 16 16" aria-hidden=true><rect x="2" y="3" width="12" '
            'height="11" rx="1.5" fill=none stroke=currentColor stroke-width=1.5/><path d="M2 6.5h12M5.5 '
            '1.5v3M10.5 1.5v3" fill=none stroke=currentColor stroke-width=1.5 stroke-linecap=round/></svg>')


def render_events(data: dict) -> str:
    """Upcoming one-off events first, then the weekly rhythm, each with a calendar file."""
    if CALENDAR.exists():
        shutil.rmtree(CALENDAR)

    today = date.today()
    upcoming = sorted((e for e in data.get("upcoming", [])
                       if date.fromisoformat(e.get("end_date", e["date"])) >= today),
                      key=lambda e: (e["date"], e.get("start", "")))
    if upcoming:
        cards = []
        for e in upcoming:
            d = date.fromisoformat(e["date"])
            uid = f'{e["date"]}-{re.sub(r"[^a-z0-9]+", "-", e["title"].lower()).strip("-")}'
            day = d.strftime("%Y%m%d")
            ics = write_ics(uid, e["title"], f'{day}T{e.get("start", "00:00").replace(":", "")}00',
                            f'{day}T{e.get("end", "23:59").replace(":", "")}00',
                            e.get("tz", "America/Denver"), e.get("address", e.get("place", "")),
                            e.get("description", ""))
            when = (f'{clock(e["start"])} to {clock(e["end"])}' if e.get("start") and e.get("end") else "")
            more = (f'<a class="link-more" href="{escape(e["link"])}">Find out more</a>' if e.get("link") else "")
            cards.append(
                f'<article class="event-card"><p class="event-date"><span>{d.strftime("%b")}</span>'
                f'<strong>{d.day}</strong></p><div><h3>{escape(e["title"])}</h3>'
                f'<p class="event-meta">{d.strftime("%A")}{" &middot; " + when if when else ""}'
                f'{" &middot; " + escape(e["place"]) if e.get("place") else ""}</p>'
                f'<p>{escape(e.get("description", ""))}</p>'
                f'<div class="event-actions"><a class="btn btn-sm btn-quiet" href="{ics}" download>'
                f'{CAL_ICON}Add to calendar</a>{more}</div></div></article>')
        up_html = f'<div class="event-list">{"".join(cards)}</div>'
    else:
        up_html = ('<p class="dl-empty">No special events are scheduled just now. Outreaches, '
                   'conferences, and Ghana trip dates will appear here as they are confirmed. '
                   '<a href="https://whatsapp.com/channel/0029Vb7Ffb34o7qVjXOzrD3j" rel="noopener">'
                   'Follow the WhatsApp channel</a> to hear first.</p>')

    rows = []
    for e in sorted(data.get("weekly", []),
                    key=lambda e: (DAY_ORDER.index(e["day"]), e["start"])):
        first = first_weekday(e["day"]).strftime("%Y%m%d")
        ics = write_ics(e["id"], f'{e["title"]}: {e["assembly"]}',
                        f'{first}T{e["start"].replace(":", "")}00', f'{first}T{e["end"].replace(":", "")}00',
                        e["tz"], e["address"], e.get("note", ""), f'FREQ=WEEKLY;BYDAY={e["day"]}')
        zone = "MT" if e["tz"] == "America/Denver" else "ET"
        note = f'<span class="small">{escape(e["note"])}</span>' if e.get("note") else ""
        rows.append(
            f'<li><span class="wk-day">{DAY_NAMES[e["day"]]}</span>'
            f'<span class="wk-time">{clock(e["start"])} to {clock(e["end"])} {zone}</span>'
            f'<span class="wk-what"><strong>{escape(e["title"])}</strong>'
            f'{escape(e["assembly"])}{note}</span>'
            f'<a class="wk-ics" href="{ics}" download aria-label="Add {escape(e["title"])}, '
            f'{escape(e["assembly"])}, to your calendar">{CAL_ICON}<span>Add</span></a></li>')

    return (f'<h2 id="upcoming" style="margin-top:0">Coming Up</h2>{up_html}'
            f'<h2 id="weekly">Every Week</h2><ul class="weekly">{"".join(rows)}</ul>')


# ---------------------------------------------------------------- field notes

def load_field_notes() -> dict:
    path = DATA / "field-notes.json"
    return json.loads(read(path)) if path.exists() else {"notes": []}


def render_field_notes(data: dict) -> str:
    notes = sorted(data.get("notes", []), key=lambda n: n["date"], reverse=True)
    if not notes:
        return ('<p class="dl-empty">The first reports from the field will be posted here after our '
                'next team serves. Until then, short updates go out first on our '
                '<a href="https://whatsapp.com/channel/0029Vb7Ffb34o7qVjXOzrD3j" rel="noopener">WhatsApp channel</a> '
                'and in the <a href="https://www.facebook.com/share/g/1BQzYh2Wvi/" rel="noopener">Facebook group</a>.</p>')
    out = []
    for n in notes:
        d = date.fromisoformat(n["date"])
        img = (f'<figure class="note-figure"><img src="{n["image"]}" alt="{escape(n.get("image_alt", ""))}" '
               f'loading="lazy"></figure>' if n.get("image") else "")
        body = "".join(f"<p>{escape(p)}</p>" for p in n.get("body", []))
        pray = ("<div class=note-pray><h4>Please pray</h4><ul>"
                + "".join(f"<li>{escape(x)}</li>" for x in n["prayer"]) + "</ul></div>"
                if n.get("prayer") else "")
        out.append(
            f'<article class="field-note" id="{n.get("slug", n["date"])}">{img}<div class="prose">'
            f'<p class="article-meta">{d.strftime("%-d %B %Y")}'
            f'{" &middot; " + escape(n["place"]) if n.get("place") else ""}</p>'
            f'<h2>{escape(n["title"])}</h2>{body}{pray}</div></article>')
    return "".join(out)


# ---------------------------------------------------------------- storybook

def load_storybook() -> dict | None:
    path = DATA / "storybook.json"
    return json.loads(read(path)) if path.exists() else None


def render_storybook(book: dict | None) -> str:
    """
    The picture book as a stack of pages. With JavaScript it becomes a
    one-page-at-a-time reader; without it, and in print, every page shows in
    order, one per sheet, which is also how the PDF is made.
    """
    if not book:
        return ""
    pages = [
        f'<article class="book-page book-cover" data-page>'
        f'<figure class="book-art"><img src="{book["cover"]}" alt="{escape(book["cover_alt"])}" '
        f'width="800" height="520"></figure>'
        f'<div class="book-title"><h2>{escape(book["title"])}</h2>'
        f'<p>{escape(book["subtitle"])}</p><p class="book-byline">{escape(book["byline"])}</p></div></article>'
    ]
    for n, pg in enumerate(book["pages"], 1):
        img = f'assets/img/storybook/{pg["image"]}.svg'
        if not (ROOT / img).exists():
            print(f"  ! missing storybook illustration: {img}  (run tools/make_storybook_art.py)")
        step = (f'<span class="book-step" title="Karis Framework">{escape(pg["step"])}</span>'
                if pg.get("step") else "")
        text = "".join(f"<p>{escape(t)}</p>" for t in pg["text"])
        pages.append(
            f'<article class="book-page" data-page>'
            f'<figure class="book-art"><img src="{img}" alt="{escape(pg["alt"])}" width="800" height="520" '
            f'loading="{"eager" if n == 1 else "lazy"}">{step}</figure>'
            f'<div class="book-text" data-book-text>{text}</div>'
            f'<span class="book-num" aria-hidden="true">{n}</span></article>'
        )
    verses = "".join(f'<blockquote><p>&ldquo;{escape(v["text"])}&rdquo;</p><footer>{escape(v["ref"])}</footer>'
                     f'</blockquote>' for v in book["verses"])
    talk = "".join(f"<li>{escape(t)}</li>" for t in book["talk"])
    words = "".join(f'<div><dt>{escape(w["word"])}</dt><dd>{escape(w["meaning"])}</dd></div>'
                    for w in book["words"])
    pages.append(
        f'<article class="book-page book-back" data-page><div class="book-back-grid">'
        f'<div><h3>From the Bible</h3>{verses}</div>'
        f'<div><h3>Talk about it together</h3><ol>{talk}</ol></div>'
        f'<div><h3>Words from Ghana</h3><dl>{words}</dl></div>'
        f'</div></article>'
    )
    controls = (
        '<div class="book-controls" hidden>'
        '<button type="button" class="kids-btn book-prev" data-book-prev aria-label="Previous page">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" '
        'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
        '<p class="book-count" aria-live="polite" data-book-count></p>'
        '<button type="button" class="kids-btn kids-read book-read" data-book-read aria-pressed="false">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9z" fill="currentColor"/>'
        '<path d="M16 8.5a5 5 0 0 1 0 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
        '</svg><span>Read this page</span></button>'
        '<button type="button" class="kids-btn book-next" data-book-next aria-label="Next page">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" '
        'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button></div>'
    )
    # The markers let tools/make_pdfs.py lift the book out to print it on its own.
    return (f'<!--book--><div class="book" data-book aria-label="{escape(book["title"])}, picture book">'
            f'<div class="book-pages">{"".join(pages)}</div>{controls}</div><!--/book-->')


# ---------------------------------------------------------------- photo credits

LICENCE_URLS = {
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
}


def render_photo_credits() -> str:
    """Title, author, source and licence for every freely licensed photo."""
    path = DATA / "photo-credits.json"
    if not path.exists():
        return ""
    rows = []
    for slug, c in json.loads(read(path)).items():
        lic = escape(c["license"])
        lic_html = (f'<a href="{LICENCE_URLS[c["license"]]}" rel="noopener license">{lic}</a>'
                    if c["license"] in LICENCE_URLS else lic)
        rows.append(
            f'<li><img src="assets/img/photos/{slug}.jpg" alt="" loading="lazy">'
            f'<div><strong>{escape(c["title"])}</strong>'
            f'<span>by {escape(c["author"])} &middot; {lic_html} &middot; '
            f'<a href="{escape(c["source"])}" rel="noopener">source</a></span></div></li>')
    return f'<ul class="credits">{"".join(rows)}</ul>'


# ---------------------------------------------------------------- settings-driven blocks

def render_analytics() -> str:
    if not GOATCOUNTER_CODE:
        return ""
    return (f'<script data-goatcounter="https://{GOATCOUNTER_CODE}.goatcounter.com/count" '
            f'async src="https://gc.zgo.at/count.js"></script>')


def render_analytics_policy() -> str:
    if not GOATCOUNTER_CODE:
        return ("<p>This website does not set advertising or tracking cookies of its own, and it "
                "does not use analytics or profile visitors. If we add website analytics in future, "
                "this policy will be updated before it goes live.</p>")
    return ("<p>This website does not set advertising or tracking cookies, and it does not profile "
            "visitors. To understand which pages are useful, we count visits with "
            '<a href="https://www.goatcounter.com" rel="noopener">GoatCounter</a>, a privacy-friendly '
            "service that sets no cookies and stores no personal information: only the page viewed, "
            "the referring site, and broad details such as screen size and country. We cannot use it "
            "to identify you.</p>")


def render_giving() -> str:
    if not GIVING_URL:
        return ('<div class="callout gold"><p><strong>Online giving is being set up.</strong> We are '
                "completing the ministry's donation processing and financial-accountability "
                "arrangements, and we will not take card details through this website until that is "
                "properly in place. In the meantime, please use one of the routes below and we will "
                "make sure your gift is directed and receipted correctly.</p></div>")
    via = f" through {escape(GIVING_PROVIDER)}" if GIVING_PROVIDER else ""
    return (f'<div class="give-online"><div><h3>Give online</h3>'
            f"<p>Give once or set up a regular gift{via}, our secure giving partner. Card details "
            f"go directly to them and never pass through this website. You will receive a receipt "
            f"by email.</p></div>"
            f'<a class="btn btn-red" href="{escape(GIVING_URL)}" rel="noopener">Give online now</a></div>'
            f'<p class="small">Prefer to give another way? Use one of the routes below.</p>')


# ---------------------------------------------------------------- page build

def render_document(slug: str, meta: dict[str, str], body: str,
                    partials: dict[str, str]) -> str:
    """Wrap a page body in the shared shell: head, navigation, hero, footer."""
    title = meta.get("title", SITE_NAME)
    full_title = title if slug == "index.html" else f"{title} | {SITE_NAME}"
    description = meta.get("description", "")
    canonical = f"{SITE_URL}/{'' if slug == 'index.html' else slug}"

    # Page hero (every page except the home page, which builds its own).
    hero = ""
    if meta.get("hero_title"):
        parent = ""
        if meta.get("crumb_parent"):
            label, href = meta["crumb_parent"].split("|", 1)
            parent = f'<li><a href="{href}">{label}</a></li>'
        crumb = (
            f'<nav class=crumbs aria-label=Breadcrumb><ol>'
            f'<li><a href="index.html">Home</a></li>{parent}'
            f'<li aria-current=page>{meta.get("crumb", title)}</li></ol></nav>'
        )
        hero_text = f'<p>{meta["hero_text"]}</p>' if meta.get("hero_text") else ""
        hero = (
            f'<section class=page-hero><div class=container>{crumb}'
            f'<p class=eyebrow>{meta.get("hero_eyebrow", SITE_NAME)}</p>'
            f'<h1>{meta["hero_title"]}</h1>{hero_text}</div></section>'
        )

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
        "FORM_ENDPOINT": escape(FORM_ENDPOINT),
        "ANALYTICS": render_analytics(),
    })


def build_page(path: Path, partials: dict[str, str], downloads_html: str,
               manifest: dict, videos: dict, articles: dict, kids: dict) -> str:
    meta, body = parse_meta(read(path))

    body = body.replace("{{KIDS_DEVOTIONS}}", render_kids_cards(kids))
    body = body.replace("{{GIVING}}", render_giving())
    body = body.replace("{{PHOTO_CREDITS}}", render_photo_credits())
    if "{{EVENTS}}" in body:
        body = body.replace("{{EVENTS}}", render_events(load_events()))
    body = body.replace("{{FIELD_NOTES}}", render_field_notes(load_field_notes()))
    if "{{STORYBOOK}}" in body:
        body = body.replace("{{STORYBOOK}}", render_storybook(load_storybook()))
    body = body.replace("{{ANALYTICS_POLICY}}", render_analytics_policy())
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

    return render_document(path.name, meta, body, partials)


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
    kids = load_kids()

    print("\nBuilding pages")
    slugs = []
    for page in sorted(PAGES.glob("*.html")):
        html = build_page(page, partials, downloads_html, manifest, videos, articles, kids)
        (ROOT / page.name).write_text(html, encoding="utf-8")
        slugs.append(page.name)
        print(f"  {page.name}  {len(html) / 1024:.1f}KB")

    # Little Lights: one generated page per children's devotion.
    for series in kids["series"]:
        for n, d in enumerate(series["devotions"]):
            slug = f'{d["slug"]}.html'
            meta, body = render_kids_day(series, n)
            html = render_document(slug, meta, body, partials)
            (ROOT / slug).write_text(html, encoding="utf-8")
            slugs.append(slug)
            print(f"  {slug}  {len(html) / 1024:.1f}KB")

    write_sitemap(slugs)
    print("  sitemap.xml\n  robots.txt")

    cname = ROOT / "CNAME"
    if CUSTOM_DOMAIN:
        cname.write_text(CUSTOM_DOMAIN + "\n", encoding="utf-8")
        print(f"  CNAME  {CUSTOM_DOMAIN}")
    elif cname.exists():
        cname.unlink()
        print("  removed CNAME (no custom domain set)")

    # Remove pages that used to exist but are no longer part of the site.
    for stale in ROOT.glob("*.html"):
        if stale.name not in slugs:
            stale.unlink()
            print(f"  removed stale page: {stale.name}")

    print(f"\nDone — {len(slugs)} pages.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
