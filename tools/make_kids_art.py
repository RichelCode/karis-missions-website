#!/usr/bin/env python3
"""
Draw the illustrations for Little Lights, the children's devotions.

Writes plain SVG scenes into `assets/img/kids/`. Drawn rather than
photographed on purpose: the ministry does not publish photographs of
children without written consent (see safeguarding.html), and simple
illustration reads better at a child's eye level anyway.

Every figure is built from the same few shapes so the set looks like one
book. Edit a scene below, then run:

    python3 tools/make_kids_art.py
    python3 tools/build.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "kids"

W, H = 800, 520

# A warm picture-book palette that sits beside the site's navy and red.
SKY, SKY_2 = "#cdeefc", "#9fd8f2"
SUN = "#ffcd4a"
GRASS, GRASS_2 = "#93d16f", "#63ad55"
LEAF, LEAF_2, LEAF_3 = "#4fae57", "#6cc06a", "#3d9446"
BARK = "#8a5a3b"
SAND = "#f4dfae"
SEA, SEA_2 = "#4fb3d9", "#2f8fbf"
INK = "#2a2a35"
CHEEK = "#ff8f8f"
RED = "#c1272d"
NAVY = "#10243c"

SKIN = {"deep": "#5c3a1e", "brown": "#8d5524", "tan": "#c68642",
        "light": "#e0ac69", "fair": "#f1c27d"}
HAIR = {"black": "#1f1a17", "brown": "#4a2f1d", "dark": "#2e2018"}


# ---------------------------------------------------------------- shapes

def svg(body: str, title: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>\n')


def sky(top: str = SKY, bottom: str = SKY_2, gid: str = "sky") -> str:
    return (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/>'
            f'</linearGradient></defs><rect width="{W}" height="{H}" fill="url(#{gid})"/>')


def sun(x: float, y: float, r: float = 46) -> str:
    rays = "".join(
        f'<rect x="{x - 4}" y="{y - r - 30}" width="8" height="20" rx="4" fill="{SUN}" '
        f'transform="rotate({a} {x} {y})"/>' for a in range(0, 360, 45))
    return f'{rays}<circle cx="{x}" cy="{y}" r="{r}" fill="{SUN}"/>'


def cloud(x: float, y: float, s: float = 1) -> str:
    return (f'<g transform="translate({x} {y}) scale({s})" fill="#fff" opacity=".92">'
            f'<ellipse cx="0" cy="0" rx="46" ry="22"/><circle cx="-20" cy="-12" r="22"/>'
            f'<circle cx="16" cy="-18" r="27"/></g>')


def hills(y: float = 400) -> str:
    return (f'<path d="M0 {y - 30} Q200 {y - 90} 420 {y - 40} T800 {y - 50} V{H} H0Z" fill="{GRASS_2}"/>'
            f'<path d="M0 {y} Q260 {y - 50} 520 {y - 10} T800 {y - 20} V{H} H0Z" fill="{GRASS}"/>')


def face(cy: float, smile: bool = True) -> str:
    mouth = (f'<path d="M-8 {cy + 8} Q0 {cy + 16} 8 {cy + 8}" fill="none" stroke="{INK}" '
             f'stroke-width="3" stroke-linecap="round"/>' if smile else "")
    return (f'<circle cx="-9" cy="{cy - 2}" r="3.4" fill="{INK}"/>'
            f'<circle cx="9" cy="{cy - 2}" r="3.4" fill="{INK}"/>'
            f'<circle cx="-15" cy="{cy + 7}" r="5" fill="{CHEEK}" opacity=".45"/>'
            f'<circle cx="15" cy="{cy + 7}" r="5" fill="{CHEEK}" opacity=".45"/>{mouth}')


def hair(style: str, cy: float, colour: str) -> str:
    if style == "short":
        return (f'<path d="M-27 {cy} Q-28 {cy - 30} 0 {cy - 30} Q28 {cy - 30} 27 {cy} '
                f'Q20 {cy - 14} 0 {cy - 16} Q-20 {cy - 14} -27 {cy}Z" fill="{colour}"/>')
    if style == "puffs":
        return (f'<circle cx="-24" cy="{cy - 22}" r="13" fill="{colour}"/>'
                f'<circle cx="24" cy="{cy - 22}" r="13" fill="{colour}"/>'
                f'<path d="M-26 {cy - 2} Q-26 {cy - 28} 0 {cy - 28} Q26 {cy - 28} 26 {cy - 2} '
                f'Q14 {cy - 16} 0 {cy - 16} Q-14 {cy - 16} -26 {cy - 2}Z" fill="{colour}"/>')
    if style == "long":
        return (f'<path d="M-30 {cy + 30} Q-34 {cy - 30} 0 {cy - 30} Q34 {cy - 30} 30 {cy + 30} '
                f'L22 {cy + 30} Q24 {cy - 8} 0 {cy - 14} Q-24 {cy - 8} -22 {cy + 30}Z" fill="{colour}"/>')
    if style == "wrap":   # head covering
        return (f'<path d="M-31 {cy + 34} Q-36 {cy - 34} 0 {cy - 34} Q36 {cy - 34} 31 {cy + 34} '
                f'L22 {cy + 30} Q24 {cy - 10} 0 {cy - 16} Q-24 {cy - 10} -22 {cy + 30}Z" fill="{colour}"/>')
    return ""


ARMS = {
    "down":   ((-34, -50), (34, -50)),
    "up":     ((-42, -150), (42, -150)),
    "wave":   ((-34, -50), (46, -146)),
    "point":  ((-34, -50), (70, -112)),
    "out":    ((-62, -84), (62, -84)),
    "hold":   ((-30, -96), (30, -96)),
    "reach":  ((-66, -100), (34, -50)),
}


def person(x: float, y: float, s: float = 1, skin: str = "brown", top: str = RED,
           legs: str = NAVY, hair_style: str = "short", hair_colour: str = "black",
           arms: str = "down", robe: bool = False, back: bool = False, beard: bool = False,
           flip: bool = False, extra: str = "") -> str:
    """A figure standing with its feet at (x, y). Scale 1 is about 150px tall."""
    sk = SKIN.get(skin, skin)
    hc = HAIR.get(hair_colour, hair_colour)
    head_cy = -124
    (lx, ly), (rx, ry) = ARMS[arms]

    if robe:
        body = (f'<path d="M-24 -98 Q0 -106 24 -98 L36 -4 Q0 4 -36 -4Z" fill="{top}"/>'
                f'<rect x="-27" y="-60" width="54" height="9" rx="4" fill="{legs}" opacity=".85"/>'
                f'<ellipse cx="-12" cy="-2" rx="11" ry="6" fill="{BARK}"/>'
                f'<ellipse cx="12" cy="-2" rx="11" ry="6" fill="{BARK}"/>')
    else:
        body = (f'<rect x="-16" y="-48" width="13" height="46" rx="6" fill="{legs}"/>'
                f'<rect x="3" y="-48" width="13" height="46" rx="6" fill="{legs}"/>'
                f'<ellipse cx="-11" cy="-2" rx="11" ry="6" fill="{INK}"/>'
                f'<ellipse cx="11" cy="-2" rx="11" ry="6" fill="{INK}"/>'
                f'<rect x="-25" y="-100" width="50" height="58" rx="16" fill="{top}"/>')

    arm = lambda ex, ey: (
        f'<path d="M{-22 if ex < 0 else 22} -90 L{ex} {ey}" stroke="{top}" stroke-width="13" '
        f'stroke-linecap="round"/><circle cx="{ex}" cy="{ey}" r="7.5" fill="{sk}"/>')

    head = f'<circle cx="0" cy="{head_cy}" r="27" fill="{sk}"/>'
    if back:
        # Seen from behind: the hair covers the head and there is no face.
        head += (f'<circle cx="0" cy="{head_cy - 2}" r="27" fill="{hc}"/>'
                 f'<rect x="-8" y="{head_cy + 20}" width="16" height="12" fill="{sk}"/>')
        if hair_style == "puffs":
            head += (f'<circle cx="-24" cy="{head_cy - 22}" r="13" fill="{hc}"/>'
                     f'<circle cx="24" cy="{head_cy - 22}" r="13" fill="{hc}"/>')
    else:
        head += hair(hair_style, head_cy, hc) + face(head_cy)
        if beard:
            head += (f'<path d="M-24 {head_cy + 2} Q-22 {head_cy + 34} 0 {head_cy + 34} '
                     f'Q22 {head_cy + 34} 24 {head_cy + 2} Q14 {head_cy + 20} 0 {head_cy + 20} '
                     f'Q-14 {head_cy + 20} -24 {head_cy + 2}Z" fill="{hc}"/>'
                     f'<path d="M-7 {head_cy + 12} Q0 {head_cy + 17} 7 {head_cy + 12}" fill="none" '
                     f'stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')

    mirror = " scale(-1 1)" if flip else ""
    return (f'<g transform="translate({x} {y}) scale({s}){mirror}">'
            f'{body}{arm(lx, ly)}{arm(rx, ry)}{head}{extra}</g>')


def bubble(x: float, y: float, w: float, text: str, tail_x: float, tail_y: float,
           size: int = 26) -> str:
    h = size * 2
    return (f'<path d="M{x + 30} {y + h - 2} L{tail_x} {tail_y} L{x + 64} {y + h - 2}Z" fill="#fff"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="#fff"/>'
            f'<text x="{x + w / 2}" y="{y + h / 2 + size * .36}" text-anchor="middle" '
            f'font-family="Trebuchet MS, Verdana, sans-serif" font-weight="700" '
            f'font-size="{size}" fill="{NAVY}">{text}</text>')


def sparkle(x: float, y: float, s: float = 1, colour: str = SUN) -> str:
    return (f'<path transform="translate({x} {y}) scale({s})" '
            f'd="M0 -14 Q2 -2 14 0 Q2 2 0 14 Q-2 2 -14 0 Q-2 -2 0 -14Z" fill="{colour}"/>')


def heart(x: float, y: float, s: float = 1, colour: str = RED) -> str:
    return (f'<path transform="translate({x} {y}) scale({s})" '
            f'd="M0 12 C-22 -2 -14 -22 0 -10 C14 -22 22 -2 0 12Z" fill="{colour}"/>')


def tree(x: float, y: float, s: float = 1) -> str:
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<path d="M-24 0 Q-14 -120 -18 -210 L18 -210 Q14 -120 24 0Z" fill="{BARK}"/>'
            f'<path d="M-6 -150 Q-60 -170 -110 -200" stroke="{BARK}" stroke-width="16" fill="none" stroke-linecap="round"/>'
            f'<path d="M6 -170 Q60 -190 100 -230" stroke="{BARK}" stroke-width="14" fill="none" stroke-linecap="round"/>'
            f'<circle cx="-110" cy="-250" r="78" fill="{LEAF_3}"/>'
            f'<circle cx="100" cy="-270" r="84" fill="{LEAF_3}"/>'
            f'<circle cx="0" cy="-320" r="96" fill="{LEAF}"/>'
            f'<circle cx="-60" cy="-300" r="66" fill="{LEAF_2}"/>'
            f'<circle cx="60" cy="-330" r="58" fill="{LEAF_2}"/></g>')


# ---------------------------------------------------------------- scenes

def cover() -> str:
    stars = "".join(sparkle(x, y, s, "#fff3c4") for x, y, s in
                    [(90, 70, .8), (210, 130, .5), (330, 60, .6), (520, 100, .5),
                     (690, 60, .9), (740, 170, .5), (150, 210, .4), (610, 200, .45)])
    beam = ('<defs><linearGradient id="beamR" x1="0" x2="1"><stop offset="0" stop-color="#fff3b0" '
            'stop-opacity=".85"/><stop offset="1" stop-color="#fff3b0" stop-opacity="0"/></linearGradient>'
            '<linearGradient id="beamL" x1="1" x2="0"><stop offset="0" stop-color="#fff3b0" '
            'stop-opacity=".6"/><stop offset="1" stop-color="#fff3b0" stop-opacity="0"/></linearGradient></defs>'
            '<path d="M560 170 L800 96 L800 250Z" fill="url(#beamR)"/>'
            '<path d="M560 170 L330 86 L330 236Z" fill="url(#beamL)"/>')
    lighthouse = (
        f'<path d="M520 420 L534 200 L586 200 L600 420Z" fill="#fff"/>'
        f'<path d="M524 362 L596 362 L593 316 L527 316Z" fill="{RED}"/>'
        f'<path d="M530 268 L590 268 L588 236 L532 236Z" fill="{RED}"/>'
        f'<rect x="530" y="140" width="60" height="62" rx="6" fill="#ffe27a"/>'
        f'<rect x="522" y="196" width="76" height="12" rx="4" fill="{NAVY}"/>'
        f'<path d="M524 142 L560 104 L596 142Z" fill="{RED}"/>'
        f'<circle cx="560" cy="170" r="16" fill="#fff8d6"/>')
    sea = (f'<rect y="390" width="{W}" height="130" fill="{SEA_2}"/>'
           f'<path d="M0 400 Q50 386 100 400 T200 400 T300 400 T400 400 T500 400 T600 400 T700 400 T800 400 V420 H0Z" fill="{SEA}"/>')
    rocks = (f'<path d="M440 430 Q480 380 560 392 Q650 380 700 430 Q690 470 570 470 Q450 470 440 430Z" fill="#6b6f80"/>'
             f'<path d="M0 470 Q120 410 300 430 Q360 440 380 520 H0Z" fill="{SAND}"/>')
    kids = (person(150, 488, .78, "deep", "#ffb02e", "#3a7bd5", "puffs", arms="up")
            + person(240, 492, .82, "light", "#36a3d9", NAVY, "short", "brown", arms="wave")
            + person(318, 486, .7, "tan", "#ef6f6c", "#5a3e8c", "long", arms="up"))
    return svg(sky("#16335a", "#5d5a9e", "dusk") + stars + beam + sea + rocks + lighthouse + kids,
               "Three children on the shore at dusk, arms raised, beside a lighthouse shining over the sea")


def know() -> str:
    crowd = (person(110, 470, .74, "fair", "#7fb2e5", NAVY, "long", "brown", flip=True)
             + person(390, 478, .78, "deep", "#f0a13a", "#6d4c41", "wrap", "#8e44ad"))
    jesus = person(250, 488, 1.05, "brown", "#fbf6ea", RED, arms="wave", robe=True, back=True,
                   hair_colour="dark")
    zac = person(612, 214, .62, "tan", "#2f9e8f", NAVY, "short", "black", arms="out", beard=True)
    # A branch to sit on, and leaves in front so he is up in the tree, not in front of it.
    leaves_front = (f'<path d="M520 222 Q612 200 700 214" stroke="{BARK}" stroke-width="14" '
                    f'fill="none" stroke-linecap="round"/>'
                    f'<circle cx="548" cy="226" r="34" fill="{LEAF_2}"/>'
                    f'<circle cx="612" cy="232" r="30" fill="{LEAF}"/>'
                    f'<circle cx="680" cy="230" r="34" fill="{LEAF_2}"/>')
    return svg(sky() + sun(110, 90) + cloud(330, 80) + hills(430) + tree(615, 470, 1.0)
               + zac + leaves_front + crowd + jesus
               + bubble(80, 196, 230, "Zacchaeus!", 240, 330),
               "A short man waving from the branches of a big tree while Jesus, seen from behind, calls up to him")


def grow() -> str:
    pot = lambda x: (f'<path d="M{x - 38} 400 L{x + 38} 400 L{x + 30} 462 L{x - 30} 462Z" fill="#d9774a"/>'
                     f'<rect x="{x - 44}" y="392" width="88" height="16" rx="5" fill="#c4663c"/>')
    sprout = (f'<path d="M400 394 Q400 370 402 356" stroke="{LEAF_3}" stroke-width="6" fill="none"/>'
              f'<ellipse cx="390" cy="356" rx="14" ry="8" fill="{LEAF_2}" transform="rotate(-30 390 356)"/>'
              f'<ellipse cx="414" cy="352" rx="14" ry="8" fill="{LEAF_2}" transform="rotate(30 414 352)"/>')
    plant = (f'<path d="M540 394 Q536 330 544 290" stroke="{LEAF_3}" stroke-width="7" fill="none"/>'
             + "".join(f'<ellipse cx="{540 + dx}" cy="{y}" rx="24" ry="11" fill="{LEAF_2}" '
                       f'transform="rotate({r} {540 + dx} {y})"/>'
                       for dx, y, r in [(-22, 360, -25), (24, 340, 25), (-20, 310, -30), (22, 292, 30)]))
    flower = (f'<path d="M690 394 Q684 290 694 196" stroke="{LEAF_3}" stroke-width="8" fill="none"/>'
              + "".join(f'<ellipse cx="{690 + dx}" cy="{y}" rx="28" ry="12" fill="{LEAF}" '
                        f'transform="rotate({r} {690 + dx} {y})"/>'
                        for dx, y, r in [(-26, 350, -25), (28, 320, 25), (-24, 280, -30), (26, 250, 28)])
              + "".join(f'<circle cx="{694 + dx}" cy="{180 + dy}" r="22" fill="#ff9fb6"/>'
                        for dx, dy in [(0, -30), (28, -10), (18, 24), (-18, 24), (-28, -10)])
              + f'<circle cx="694" cy="180" r="18" fill="{SUN}"/>')
    can = (f'<g transform="translate(232 300)"><rect x="0" y="0" width="64" height="50" rx="10" fill="#3a8fd6"/>'
           f'<path d="M62 12 L122 -18 L126 -10 L64 26Z" fill="#3a8fd6"/>'
           f'<path d="M10 0 Q32 -30 54 0" stroke="#2c6fa8" stroke-width="7" fill="none"/></g>')
    drops = "".join(f'<path d="M{x} {y} q6 10 0 16 q-6 -6 0 -16Z" fill="#5bc0eb"/>'
                    for x, y in [(370, 300), (388, 322), (360, 334), (382, 346)])
    child = person(190, 470, 1.0, "brown", "#ffb02e", "#3a7bd5", "puffs", arms="out")
    return svg(sky() + sun(690, 80, 40) + cloud(170, 90, .9) + cloud(470, 70, .7)
               + f'<rect y="440" width="{W}" height="80" fill="{GRASS}"/>'
               + pot(400) + pot(540) + pot(690) + sprout + plant + flower
               + child + can + drops + sparkle(470, 220, 1.1) + sparkle(620, 140, .8),
               "A girl with a watering can beside three pots: a tiny sprout, a bigger plant and a tall flower")


def serve() -> str:
    tones = list(SKIN.values())
    crowd = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{tones[(i * 3) % len(tones)]}"/>'
        f'<path d="M{x - r * 1.2} {y + r * 2.4} Q{x} {y + r * .6} {x + r * 1.2} {y + r * 2.4}Z" '
        f'fill="{["#ef6f6c", "#36a3d9", "#ffb02e", "#8e6cc9", "#4fae57"][i % 5]}"/>'
        for i, (x, y, r) in enumerate(
            [(60 + 62 * k + (n % 2) * 30, 260 + n * 40, 14 + n * 2)
             for n in range(3) for k in range(13)]))
    loaves = "".join(f'<ellipse cx="{x}" cy="{y}" rx="22" ry="13" fill="#e2a85a"/>'
                     f'<path d="M{x - 10} {y - 4} l6 6 M{x} {y - 6} l6 6 M{x + 10} {y - 4} l5 5" '
                     f'stroke="#b97a33" stroke-width="2.5"/>'
                     for x, y in [(-50, -18), (-14, -24), (22, -20), (-34, -40), (6, -44)])
    fish = "".join(f'<g transform="translate({x} {y}) rotate({r})"><ellipse rx="24" ry="11" fill="#f2884b"/>'
                   f'<path d="M20 0 L38 -12 L38 12Z" fill="#f2884b"/><circle cx="-12" cy="-2" r="2.6" fill="{INK}"/></g>'
                   for x, y, r in [(46, -40, -15), (40, -16, 10)])
    basket = (f'<g transform="translate(400 238)">{loaves}{fish}'
              f'<path d="M-76 -10 L76 -10 L60 40 L-60 40Z" fill="#c8924f"/>'
              f'<path d="M-70 4 H70 M-64 22 H64" stroke="#a87337" stroke-width="4"/></g>')
    boy = person(400, 492, 1.12, "deep", "#3aa76d", "#5a3e8c", "short", arms="up")
    return svg(sky() + sun(700, 80, 40) + cloud(150, 70) + hills(330) + crowd
               + f'<path d="M0 420 Q400 380 800 420 V{H} H0Z" fill="{GRASS}"/>'
               + boy + basket + sparkle(280, 170, 1.2) + sparkle(530, 150, 1) + sparkle(560, 260, .7),
               "A boy holding up a basket with five loaves and two fish in front of a big crowd on a hillside")


def go() -> str:
    house = (f'<rect x="440" y="170" width="330" height="280" fill="#f3e2c4"/>'
             f'<rect x="420" y="150" width="370" height="30" rx="4" fill="#e3c99a"/>'
             f'<path d="M500 450 V320 Q540 270 580 320 V450Z" fill="#8a5a3b"/>'
             f'<path d="M640 300 V250 Q670 220 700 250 V300Z" fill="{SEA_2}"/>'
             f'<path d="M640 300 V250 Q670 220 700 250 V300Z" fill="none" stroke="#e3c99a" stroke-width="6"/>')
    palm = (f'<path d="M120 450 Q130 330 110 220" stroke="{BARK}" stroke-width="18" fill="none" stroke-linecap="round"/>'
            + "".join(f'<path d="M110 220 Q{110 + dx * .5} {220 + dy - 30} {110 + dx} {220 + dy}" '
                      f'stroke="{LEAF}" stroke-width="16" fill="none" stroke-linecap="round"/>'
                      for dx, dy in [(-90, 30), (90, 30), (-70, -40), (70, -40), (0, -70)]))
    girl = person(300, 470, .9, "tan", "#ffb02e", "#ef6f6c", "puffs", arms="point")
    lady = person(560, 476, 1.05, "light", "#8e6cc9", "#f0a13a", "wrap", "#3aa76d", robe=True, flip=True)
    return svg(sky() + sun(80, 80, 40) + cloud(330, 80, .8)
               + f'<rect y="440" width="{W}" height="80" fill="{SAND}"/>'
               + palm + house + girl + lady
               + bubble(200, 196, 220, "God can help!", 300, 300, 24)
               + heart(450, 230, 1.2) + sparkle(470, 190, .7),
               "A young girl pointing and telling a lady in a big house that God can help")


def multiply() -> str:
    sea = (f'<rect y="300" width="{W}" height="140" fill="{SEA}"/>'
           + "".join(f'<path d="M{x} {y} q15 -10 30 0" stroke="#fff" stroke-width="4" fill="none" opacity=".7"/>'
                     for x, y in [(60, 340), (180, 370), (300, 330), (420, 380), (560, 345), (680, 372)]))
    boat = (f'<path d="M520 330 L720 330 L690 370 L550 370Z" fill="#a0522d"/>'
            f'<rect x="616" y="200" width="7" height="130" fill="#6d3d1f"/>'
            f'<path d="M626 206 L626 320 L700 320Z" fill="#fff"/>')
    shore = f'<path d="M0 420 Q400 380 800 420 V{H} H0Z" fill="{SAND}"/>'
    # Andrew leads the way and holds his brother's hand.
    andrew = person(280, 486, 1.0, "brown", "#36a3d9", "#e2a85a", "short", arms="reach", robe=True)
    simon = person(360, 490, 1.1, "brown", RED, "#e2a85a", "short", "dark", robe=True, beard=True)
    return svg(sky() + sun(110, 90, 42) + cloud(380, 70, .8) + sea + boat + shore
               + simon + andrew + heart(320, 300, 1.1) + sparkle(200, 220, .9) + sparkle(470, 210, .8),
               "Andrew taking his brother Simon by the hand to bring him to Jesus, by a lake with a fishing boat")


# ---------------------------------------------------------------- Christmas and Easter

NIGHT, NIGHT_2 = "#14284a", "#3b3f7a"


def stars(points) -> str:
    return "".join(sparkle(x, y, sc, "#fff3c4") for x, y, sc in points)


STAR_FIELD = [(70, 60, .6), (180, 120, .4), (300, 50, .5), (420, 140, .35), (690, 70, .6),
              (760, 180, .4), (120, 220, .35), (640, 210, .3), (380, 230, .3)]


def big_star(x: float, y: float, s: float = 1) -> str:
    return (f'<circle cx="{x}" cy="{y}" r="{70 * s}" fill="#fff3c4" opacity=".18"/>'
            f'<circle cx="{x}" cy="{y}" r="{40 * s}" fill="#fff3c4" opacity=".25"/>'
            f'<path transform="translate({x} {y}) scale({s * 2.4})" '
            f'd="M0 -14 Q2 -2 14 0 Q2 2 0 14 Q-2 2 -14 0 Q-2 -2 0 -14Z" fill="#ffe27a"/>')


def donkey(x: float, y: float, s: float = 1, flip: bool = False) -> str:
    m = " scale(-1 1)" if flip else ""
    g = "#9a8f88"
    return (f'<g transform="translate({x} {y}) scale({s}){m}">'
            + "".join(f'<rect x="{lx}" y="-46" width="11" height="46" rx="5" fill="{g}"/>'
                      for lx in (-52, -32, 22, 40))
            + f'<ellipse cx="-4" cy="-62" rx="66" ry="30" fill="{g}"/>'
            f'<path d="M-68 -66 Q-86 -60 -84 -40" stroke="{g}" stroke-width="6" fill="none" stroke-linecap="round"/>'
            f'<path d="M44 -74 L66 -116 L88 -104 L70 -66Z" fill="{g}"/>'
            f'<ellipse cx="88" cy="-110" rx="22" ry="15" fill="{g}" transform="rotate(-25 88 -110)"/>'
            f'<ellipse cx="102" cy="-102" rx="9" ry="7" fill="#7d726c"/>'
            f'<ellipse cx="72" cy="-138" rx="5" ry="16" fill="{g}" transform="rotate(-15 72 -138)"/>'
            f'<ellipse cx="82" cy="-140" rx="5" ry="16" fill="{g}" transform="rotate(10 82 -140)"/>'
            f'<circle cx="88" cy="-114" r="3" fill="{INK}"/></g>')


def sheep(x: float, y: float, s: float = 1, flip: bool = False) -> str:
    m = " scale(-1 1)" if flip else ""
    wool = "".join(f'<circle cx="{cx}" cy="{cy}" r="16" fill="#fff"/>'
                   for cx, cy in [(-24, -40), (-6, -48), (12, -46), (26, -38), (-14, -28), (8, -28)])
    return (f'<g transform="translate({x} {y}) scale({s}){m}">'
            f'<rect x="-20" y="-24" width="7" height="24" rx="3" fill="{INK}"/>'
            f'<rect x="12" y="-24" width="7" height="24" rx="3" fill="{INK}"/>'
            f'{wool}<ellipse cx="38" cy="-46" rx="12" ry="15" fill="{INK}"/>'
            f'<circle cx="42" cy="-50" r="2.4" fill="#fff"/></g>')


def palm_frond(x: float, y: float, s: float = 1) -> str:
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<path d="M0 0 Q6 -40 4 -80" stroke="{LEAF_3}" stroke-width="4" fill="none"/>'
            + "".join(f'<ellipse cx="{(-1) ** i * 12 + 4}" cy="{-20 - i * 9}" rx="13" ry="5" fill="{LEAF}" '
                      f'transform="rotate({(-1) ** i * 35} {(-1) ** i * 12 + 4} {-20 - i * 9})"/>'
                      for i in range(7))
            + "</g>")


def promise() -> str:
    village = "".join(
        f'<rect x="{x}" y="{430 - h}" width="{w}" height="{h}" fill="#6b5a80"/>'
        f'<path d="M{x - 6} {430 - h} L{x + w / 2} {400 - h} L{x + w + 6} {430 - h}Z" fill="#54466a"/>'
        f'<rect x="{x + w / 2 - 8}" y="{440 - h}" width="16" height="16" fill="#ffe27a" opacity=".85"/>'
        for x, w, h in [(470, 70, 60), (560, 90, 80), (670, 70, 56), (740, 60, 70)])
    hill = (f'<path d="M0 360 Q160 300 340 340 Q420 360 460 430 V{H} H0Z" fill="#2f6b4f"/>'
            f'<rect y="430" width="{W}" height="90" fill="#24523d"/>')
    scroll = ('<rect x="-48" y="-112" width="30" height="40" rx="4" fill="#f4dfae"/>'
              '<rect x="-52" y="-116" width="38" height="8" rx="4" fill="#d9b77a"/>'
              '<rect x="-52" y="-76" width="38" height="8" rx="4" fill="#d9b77a"/>')
    isaiah = person(220, 352, 1.0, "tan", "#7a5bb5", "#d9b77a", "short", "#e8e4dc", arms="wave",
                    robe=True, beard=True, extra=scroll)
    return svg(sky(NIGHT, NIGHT_2, "night") + stars(STAR_FIELD) + big_star(580, 120)
               + village + hill + isaiah,
               "A man with a scroll on a hill at night, pointing up at one big bright star above a sleeping village")


def born() -> str:
    stable = (f'<rect x="170" y="230" width="460" height="230" fill="#8a5a3b"/>'
              f'<rect x="196" y="256" width="408" height="204" fill="#5e3d27"/>'
              f'<path d="M140 240 L400 140 L660 240 L630 252 L400 166 L170 252Z" fill="#a8713f"/>'
              f'<rect y="440" width="{W}" height="80" fill="#3c5a3a"/>'
              f'<path d="M196 460 L604 460 L604 430 Q400 412 196 430Z" fill="#e7c766"/>')
    manger = ('<path d="M340 440 L460 440 L448 400 L352 400Z" fill="#a8713f"/>'
              '<path d="M346 404 Q400 384 454 404Z" fill="#e7c766"/>'
              '<ellipse cx="404" cy="392" rx="34" ry="13" fill="#fdf6e3"/>'
              f'<circle cx="374" cy="388" r="13" fill="{SKIN["brown"]}"/>'
              f'<circle cx="370" cy="386" r="2" fill="{INK}"/><circle cx="378" cy="386" r="2" fill="{INK}"/>')
    glow = '<ellipse cx="400" cy="396" rx="120" ry="60" fill="#fff3c4" opacity=".25"/>'
    mary = person(290, 454, .92, "brown", "#3f7fcf", "#f4dfae", "wrap", "#2f62a8", robe=True)
    joseph = person(520, 456, 1.02, "brown", "#9b6a3f", "#e2a85a", "short", "dark", robe=True, beard=True)
    return svg(sky(NIGHT, NIGHT_2, "night") + stars(STAR_FIELD) + big_star(400, 70, .8)
               + f'<path d="M400 96 L380 150 L420 150Z" fill="#fff3c4" opacity=".25"/>'
               + stable + glow + donkey(200, 452, .62, flip=True) + sheep(600, 456, .8)
               + manger + mary + joseph,
               "Mary and Joseph beside baby Jesus lying in a manger, with a donkey and a sheep, under a bright star")


def shepherds() -> str:
    wings = ('<g transform="translate(400 240)">'
             '<ellipse cx="-58" cy="-90" rx="52" ry="24" fill="#fff8dc" transform="rotate(-30 -58 -90)"/>'
             '<ellipse cx="58" cy="-90" rx="52" ry="24" fill="#fff8dc" transform="rotate(30 58 -90)"/></g>')
    angel = person(400, 240, .9, "tan", "#fffaf0", "#ffe27a", "short", "#e0b84a", arms="out", robe=True)
    glow = ('<circle cx="400" cy="160" r="150" fill="#fff3c4" opacity=".16"/>'
            '<circle cx="400" cy="160" r="95" fill="#fff3c4" opacity=".2"/>')
    hill = (f'<path d="M0 360 Q200 320 420 350 T800 340 V{H} H0Z" fill="#2f6b4f"/>'
            f'<path d="M0 430 Q300 400 800 430 V{H} H0Z" fill="#24523d"/>')
    staff = '<path d="M50 -84 L50 4 M50 -84 Q50 -104 34 -100" stroke="#8a5a3b" stroke-width="6" fill="none" stroke-linecap="round"/>'
    s1 = person(170, 470, 1.0, "brown", "#c98a4b", "#6d4c41", "wrap", "#e8d5b0", arms="up", robe=True)
    s2 = person(630, 474, 1.05, "deep", "#7b8f4a", "#6d4c41", "short", arms="out", robe=True, beard=True,
                flip=True, extra=staff)
    return svg(sky(NIGHT, NIGHT_2, "night") + stars(STAR_FIELD) + glow + wings + angel + hill
               + sheep(300, 440, .8) + sheep(470, 452, .9, flip=True) + sheep(390, 470, .7)
               + s1 + s2 + sparkle(260, 120, 1, "#fff3c4") + sparkle(560, 110, 1.2, "#fff3c4"),
               "Shepherds and their sheep on a hillside at night, looking up in wonder at a shining angel")


def hosanna() -> str:
    road = (f'<rect y="400" width="{W}" height="120" fill="{GRASS}"/>'
            f'<path d="M0 430 Q400 400 800 430 L800 490 Q400 460 0 490Z" fill="{SAND}"/>'
            + "".join(f'<rect x="{x}" y="{y}" width="56" height="22" rx="5" fill="{c}" transform="rotate({r} {x} {y})"/>'
                      for x, y, r, c in [(150, 448, -6, RED), (300, 438, 4, "#3a7bd5"), (560, 440, -3, "#8e6cc9")]))
    palms = "".join(
        f'<path d="M{x} 420 Q{x + 10} 300 {x - 6} 200" stroke="{BARK}" stroke-width="16" fill="none" stroke-linecap="round"/>'
        + "".join(f'<path d="M{x - 6} 200 Q{x - 6 + dx * .5} {170 + dy} {x - 6 + dx} {200 + dy}" '
                  f'stroke="{LEAF}" stroke-width="15" fill="none" stroke-linecap="round"/>'
                  for dx, dy in [(-80, 30), (80, 30), (-60, -36), (60, -36), (0, -64)])
        for x in (70, 740))
    rider = person(430, 380, .78, "brown", "#fbf6ea", RED, arms="down", robe=True, hair_colour="dark", back=True)
    kid1 = person(220, 478, .8, "deep", "#ffb02e", "#3a7bd5", "puffs", arms="up",
                  extra=palm_frond(-42, -150, 1) + palm_frond(42, -150, 1))
    kid2 = person(640, 482, .86, "light", "#36a3d9", NAVY, "short", "brown", arms="wave",
                  extra=palm_frond(46, -146, 1.1))
    kid3 = person(310, 488, .66, "tan", "#ef6f6c", "#5a3e8c", "long", arms="up",
                  extra=palm_frond(42, -150, .9))
    return svg(sky() + sun(400, 80, 40) + cloud(200, 90, .8) + cloud(600, 70, .7) + road + palms
               + donkey(420, 452, .95) + rider + kid1 + kid3 + kid2
               + bubble(470, 150, 220, "Hosanna!", 600, 300),
               "Jesus riding a donkey along a road while children wave palm branches and cheer")


def cross() -> str:
    hill = (f'<path d="M0 420 Q400 250 800 420 V{H} H0Z" fill="{GRASS_2}"/>'
            f'<path d="M0 470 Q400 380 800 470 V{H} H0Z" fill="{GRASS}"/>')
    wood = "#7a4a2b"
    the_cross = (f'<rect x="388" y="150" width="24" height="200" rx="3" fill="{wood}"/>'
                 f'<rect x="336" y="196" width="128" height="22" rx="3" fill="{wood}"/>')
    flowers = "".join(f'<circle cx="{x}" cy="{y}" r="7" fill="{c}"/><circle cx="{x}" cy="{y}" r="3" fill="{SUN}"/>'
                      for x, y, c in [(120, 470, "#ff9fb6"), (200, 450, "#fff"), (600, 452, "#ff9fb6"),
                                      (680, 470, "#fff"), (300, 480, "#ffcd4a"), (520, 486, "#ff9fb6")])
    return svg(sky("#f6b47e", "#a77bc4", "dusk") + sun(400, 300, 70) + hill + the_cross + flowers
               + heart(400, 90, 2.2) + sparkle(250, 130, .9, "#fff3c4") + sparkle(560, 120, 1.1, "#fff3c4"),
               "A wooden cross on a quiet green hill under a soft evening sky, with a red heart in the sky above")


def alive() -> str:
    rock = (f'<path d="M420 440 Q440 220 600 200 Q760 210 800 300 V440Z" fill="#a39a8f"/>'
            f'<path d="M560 440 L560 340 Q600 290 640 340 L640 440Z" fill="#3b3631"/>'
            f'<circle cx="480" cy="390" r="56" fill="#8a8178"/>'
            f'<circle cx="480" cy="390" r="56" fill="none" stroke="#776e66" stroke-width="6"/>')
    ground = f'<rect y="430" width="{W}" height="90" fill="{GRASS}"/>'
    flowers = "".join(f'<path d="M{x} 470 L{x} 444" stroke="{LEAF_3}" stroke-width="4"/>'
                      f'<circle cx="{x}" cy="440" r="9" fill="{c}"/><circle cx="{x}" cy="440" r="4" fill="{SUN}"/>'
                      for x, c in [(330, "#ff9fb6"), (380, "#fff"), (700, "#ff9fb6"), (740, "#8e6cc9"), (60, "#fff")])
    w1 = person(150, 484, .95, "brown", "#ef6f6c", "#f4dfae", "wrap", "#8e44ad", arms="out", robe=True)
    w2 = person(260, 488, .9, "tan", "#3aa76d", "#f4dfae", "wrap", "#f0a13a", arms="up", robe=True)
    return svg(sky("#ffe6a8", "#ffb98a", "dawn") + sun(240, 150, 60) + cloud(560, 90, .8) + rock + ground
               + flowers + w1 + w2 + sparkle(600, 300, 1.4) + sparkle(680, 250, .9) + sparkle(530, 270, .8)
               + bubble(520, 120, 240, "He is risen!", 600, 290),
               "An empty tomb with its big round stone rolled away at sunrise, flowers blooming, and two women full of joy")


SCENES = {"cover": cover, "know": know, "grow": grow, "serve": serve,
          "go": go, "multiply": multiply,
          "promise": promise, "born": born, "shepherds": shepherds,
          "hosanna": hosanna, "cross": cross, "alive": alive}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in SCENES.items():
        path = OUT / f"{name}.svg"
        path.write_text(draw(), encoding="utf-8")
        print(f"  {path.relative_to(ROOT)}  {path.stat().st_size / 1024:.1f}KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
