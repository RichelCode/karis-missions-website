# Karis Missions International, Website

A static website for Karis Missions International, built around the Karis Framework:
**Know · Grow · Serve · Go · Multiply**.

No frameworks, no build server, no runtime dependencies. The published site is plain
HTML, CSS, and one small JavaScript file, so it can be hosted anywhere, including free
static hosts.

---

## Preview locally

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

(Opening `index.html` directly also works, but a local server is closer to the real thing.)

---

## How the site is put together

Pages are **generated** from shared parts, so the header, navigation, and footer exist in
one place rather than being copy-pasted into every page.

```
src/
  partials/
    base.html          document shell: <head>, topbar, header, footer
    schema.html        structured data for search engines (home page only)
  pages/               one file per page, page content only
  data/
    downloads.json     the master list behind the Resource Center
tools/
  build.py             generates the site
  prepare_assets.py    turns Richeal/ into web-ready downloads and images
  fetch_videos.py      pulls the YouTube channel feed and thumbnails
  fetch_articles.py    pulls the Medium feed for the Articles page
  make_icons.py        favicon, app icon, and social share image
  check_site.py        checks links, images, and form labels
  dedash.py            strips em dashes out of the copy
assets/
  css/styles.css       design system (edit directly, not generated)
                       Type: Fraunces for headings, Karla for text.
                       Deliberately not Inter, and labels are sentence case
                       rather than uppercase-and-letterspaced.
  js/site.js           navigation, forms, resource search
  img/                 photography, logos, document previews
  downloads/           the public documents people can download
Richeal/               original source material (not published as-is)
*.html                 GENERATED, do not edit these directly
```

### Rebuilding after a change

```bash
python3 tools/build.py       # regenerate every page
python3 tools/check_site.py  # verify links, images, form labels
```

### Testing the navigation for real

`tools/test_clicks.py` drives headless Chrome and actually clicks things:
every top-level nav item, every dropdown item, the mobile drawer, and every
internal link on every page. It also checks that no dropdown has an unbridged
hover gap, the bug that made the menus unusable with a mouse.

```bash
pip3 install --user websocket-client   # one-time
python3 -m http.server 8000 &          # the test needs the site served
python3 tools/test_clicks.py --port 8000
```

> **Important:** the `.html` files in the project root are generated output.
> Edit `src/pages/…` instead. Anything you change in the root is overwritten
> the next time `build.py` runs.

### Adding a page

1. Create `src/pages/your-page.html`.
2. Start it with a meta block:

   ```html
   <!--meta
   title: Your Page
   crumb: Your Page
   description: One sentence for search engines and link previews.
   hero_eyebrow: Section label
   hero_title: Your Page
   hero_text: A short introductory line.
   -->
   ```
3. Write the page body below it.
4. To put it in the menu, add it to `NAV` (and/or `FOOTER_COLUMNS`) in `tools/build.py`.
5. Run `python3 tools/build.py`.

### After publishing a new YouTube video

```bash
python3 tools/fetch_videos.py   # reads the channel feed, saves thumbnails
python3 tools/build.py
```

`fetch_videos.py` reads the public RSS feed for the channel
(`@isharethatyoumayknow`), writes `src/data/videos.json`, and downloads each
thumbnail into `assets/img/videos/`. Titles and blurbs in that JSON can be
edited by hand, but re-running the script overwrites them.

The Watch page shows a still image with a play button rather than an embedded
player. Nothing is requested from YouTube, and no YouTube cookie is set, until
a visitor actually presses play; at that point the `youtube-nocookie.com`
player is inserted. This keeps the page fast and matches what `privacy.html`
tells visitors.

### After publishing a new Medium article

```bash
python3 tools/fetch_articles.py
python3 tools/build.py
```

Reads the public feed for `medium.com/@andrewsasiedu` and writes
`src/data/articles.json`. The newest piece is featured; the rest fall into a
grid below it.

The article's own lead artwork is downloaded into `assets/img/articles/` and
served from this site, so cards do not call Medium's CDN on every page view.
Only the post's own image is taken; Medium's tracking pixel is skipped.

Article **text** is not copied. Each card carries the title, date, reading
time, tags, and the standfirst line, then links out to Medium to read the
piece. That keeps the writing where it is published and where its stats and
followers accrue.

To change the account, edit `HANDLE` and `AUTHOR_NAME` at the top of
`tools/fetch_articles.py`.

### Adding a download

1. Put the file in `assets/downloads/tracts/`, `…/outreach/`, or `…/brand/`.
2. Add an entry to `src/data/downloads.json`.
3. Run `python3 tools/build.py`.

File sizes shown on the site are read from the real files at build time, so they are
always accurate. If a listed file is missing, the build prints a warning and skips it
rather than publishing a broken link.

---

## Before going live

### 1. Connect the forms, required

Every form (contact, prayer, volunteer application, partnership, giving, notifications)
is built and validated but not yet wired to a destination.

1. Create a free account at <https://formspree.io> and add a form.
2. Open `assets/js/site.js`.
3. Set `FORM_ENDPOINT` to the endpoint Formspree gives you:

   ```js
   var FORM_ENDPOINT = 'https://formspree.io/f/yourid';
   ```

Until this is done nothing is silently lost: each form tells the visitor to email us
instead and offers a pre-filled mail link.

### 2. Set the real domain

`SITE_URL` in `tools/build.py` is currently `https://www.karismissions.org`. Change it to
the real domain, then rebuild, it drives the canonical URLs, social share tags,
`sitemap.xml`, and structured data.

### 3. Confirm the details we published

These were taken from the ministry's own printed material. Please confirm each one:

| | |
|---|---|
| General phone / email | +1 (719) 678-7888 · tackiausa@gmail.com |
| Social | WhatsApp channel · YouTube @isharethatyoumayknow · Facebook page and group · Instagram |
| Karis International Assembly | 5905 Flintridge Dr, Colorado Springs CO 80918, Sun 10am–12pm |
| Midweek (Colorado Springs) | 5926 Del Paz Dr, Colorado Springs CO 80918, Thu 6:30–8pm |
| Denver Assembly | 380 S Potomac St, Suite 125, Aurora CO 80012, (303) 731-9067 |
| The Radiant Assembly | 3530 W 29th St, Greeley CO 80634, (423) 946-4030 |
| Delaware Central Assembly | 2042 Sunset Lake Rd, Newark DE 19702, (302) 456-9293 |

**Still needed: service times for Denver and Greeley.** Both pages currently say "call ahead
to confirm service times" because those were not on any of the printed material. Send the
times and they go straight in.

No em dashes anywhere in the copy, by request. `tools/dedash.py` can be re-run if any creep
back in.

### 4. Still to come

- **Online giving.** The Give page explains that giving is being arranged and directs
  people to phone or email. Connect an approved donation processor when ready.
- **Devotions, articles, videos, books.** These pages honestly say the content is in
  preparation and collect email addresses, rather than showing placeholder writing.
- **Full safeguarding policy.** `safeguarding.html` publishes the ministry's commitments
  and notes that the complete Board-adopted policy will follow.
- **Analytics.** None installed. If you add any, update `privacy.html` first, because it
  currently states that no tracking is used.

---

## What is already done

- 22 pages, all sharing one header, navigation, and footer.
- Grouped navigation with keyboard-accessible dropdowns and a mobile drawer.
- Resource Center serving **8 resources / 13 files**: three complete gospel tracts
  (PDF + editable Word) plus outreach and signage artwork. The logo-download section
  was removed at the ministry's request; the files remain in `assets/downloads/brand/`
  if they are ever wanted back (add them to `src/data/downloads.json` to restore).
- Every form has proper labels, validation, required-field handling, a spam honeypot,
  and an accessible success/error state.
- Search-engine and social basics: canonical URLs, Open Graph and Twitter cards, a
  generated `sitemap.xml` and `robots.txt`, favicon and app icons, and `Organization`
  plus `Church` structured data carrying real service times and addresses.
- Privacy Policy, Terms of Use, Safeguarding statement, and a 404 page.
- Responsive from 320px up, with reduced-motion and print stylesheets.
- `tools/check_site.py` reports zero broken links, zero images missing `alt`, and zero
  unlabelled form controls.
