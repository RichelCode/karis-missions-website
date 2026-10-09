#!/usr/bin/env python3
"""
Draw the illustrations for "Ama Shines Her Light", the Karis picture book.

Uses the same figures and palette as the Little Lights devotions
(tools/make_kids_art.py) so the two read as one family. Writes SVGs into
`assets/img/storybook/`. Edit a scene, then run:

    python3 tools/make_storybook_art.py
    python3 tools/build.py
"""
from __future__ import annotations

from pathlib import Path

from make_kids_art import (BARK, GRASS, GRASS_2, H, INK, LEAF, LEAF_3, NAVY, RED, ROOT, SAND,
                           SEA, SEA_2, SKIN, SUN, W, bubble, cloud, heart, person, sky, sparkle,
                           sun, svg, tree)

OUT = ROOT / "assets" / "img" / "storybook"

DUSK = ("#203a6b", "#f2a96b")
NIGHT = ("#101f3d", "#2b356b")
STORM = ("#1d2433", "#3b4458")

# Kente-style stripes for Nana's cloth: gold, green, red and black.
KENTE = ('<defs><pattern id="kente" width="24" height="24" patternUnits="userSpaceOnUse">'
         '<rect width="24" height="24" fill="#f2b632"/><rect y="6" width="24" height="5" fill="#1f7a3a"/>'
         '<rect y="15" width="24" height="3" fill="#c1272d"/><rect x="10" width="4" height="24" fill="#1f1a17" opacity=".75"/>'
         '</pattern></defs>')


# ---------------------------------------------------------------- the cast

def ama(x, y, s=.85, arms="down", back=False, extra="", flip=False):
    return person(x, y, s, "brown", "#ffcd4a", "#e2a85a", "puffs", "black", arms=arms,
                  robe=True, back=back, extra=extra, flip=flip)


def nana(x, y, s=1.0, arms="down", back=False, extra="", flip=False):
    return person(x, y, s, "deep", "url(#kente)", "#c1272d", "wrap", "#c1272d", arms=arms,
                  robe=True, back=back, extra=extra, flip=flip)


def kwame(x, y, s=.88, arms="down", back=False, extra="", flip=False):
    return person(x, y, s, "deep", "#36a3d9", NAVY, "short", "black", arms=arms,
                  back=back, extra=extra, flip=flip)


def esi(x, y, s=.62, arms="down", extra="", flip=False):
    return person(x, y, s, "deep", "#ff9fb6", "#8e6cc9", "puffs", "black", arms=arms,
                  robe=True, extra=extra, flip=flip)


def papa(x, y, s=1.08, arms="down", extra="", flip=False):
    return person(x, y, s, "deep", "#3aa76d", "#5a3e8c", "short", "black", arms=arms,
                  beard=True, extra=extra, flip=flip)


# ---------------------------------------------------------------- places

def canoe(x, y, s=1.0, colours=("#c1272d", "#ffcd4a", "#1f7a3a"), flip=False):
    m = " scale(-1 1)" if flip else ""
    a, b, c = colours
    return (f'<g transform="translate({x} {y}) scale({s}){m}">'
            f'<path d="M-130 -30 Q-110 0 -60 6 L70 6 Q120 0 140 -34 Q60 -18 0 -18 Q-60 -18 -130 -30Z" fill="{a}"/>'
            f'<path d="M-118 -24 Q-60 -12 0 -12 Q60 -12 130 -26 L126 -18 Q60 -4 0 -4 Q-60 -4 -114 -16Z" fill="{b}"/>'
            f'<path d="M-104 -8 Q-50 2 0 2 Q50 2 110 -10" stroke="{c}" stroke-width="5" fill="none"/>'
            f'<rect x="96" y="-90" width="4" height="60" fill="{INK}"/>'
            f'<path d="M100 -90 L132 -80 L100 -70Z" fill="{c}"/></g>')


def palm(x, y, s=1.0):
    fronds = "".join(f'<path d="M0 -200 Q{dx * .5} {-230 + dy} {dx} {-200 + dy}" stroke="{LEAF}" '
                     f'stroke-width="15" fill="none" stroke-linecap="round"/>'
                     for dx, dy in [(-90, 34), (90, 34), (-70, -36), (70, -36), (0, -66), (-40, 60)])
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<path d="M10 0 Q22 -110 0 -200" stroke="{BARK}" stroke-width="16" fill="none" stroke-linecap="round"/>'
            f'{fronds}<circle cx="-8" cy="-190" r="8" fill="#6b4a2b"/><circle cx="8" cy="-186" r="8" fill="#6b4a2b"/></g>')


def lighthouse(x, y, s=1.0, beams=True, dark_sky=False):
    beam = ""
    if beams:
        # Light that fades as it travels, so it glows rather than greys on a dusk sky.
        strength = ".85" if dark_sky else ".55"
        beam = (f'<defs><linearGradient id="beamR" x1="0" x2="1"><stop offset="0" stop-color="#fff3b0" '
                f'stop-opacity="{strength}"/><stop offset="1" stop-color="#fff3b0" stop-opacity="0"/></linearGradient>'
                f'<linearGradient id="beamL" x1="1" x2="0"><stop offset="0" stop-color="#fff3b0" '
                f'stop-opacity="{strength}"/><stop offset="1" stop-color="#fff3b0" stop-opacity="0"/></linearGradient></defs>'
                f'<path d="M0 -172 L300 -250 L300 -94Z" fill="url(#beamR)"/>'
                f'<path d="M0 -172 L-300 -250 L-300 -94Z" fill="url(#beamL)" opacity=".7"/>')
    return (f'<g transform="translate({x} {y}) scale({s})">{beam}'
            f'<path d="M-40 0 L-26 -150 L26 -150 L40 0Z" fill="#fff"/>'
            f'<path d="M-36 -40 L36 -40 L33 -76 L-33 -76Z" fill="{RED}"/>'
            f'<path d="M-30 -104 L30 -104 L28 -128 L-28 -128Z" fill="{RED}"/>'
            f'<rect x="-24" y="-196" width="48" height="48" rx="5" fill="#ffe27a"/>'
            f'<rect x="-32" y="-152" width="64" height="10" rx="3" fill="{NAVY}"/>'
            f'<path d="M-30 -194 L0 -226 L30 -194Z" fill="{RED}"/>'
            f'<circle cx="0" cy="-172" r="13" fill="#fff8d6"/></g>')


def sea(y=330, colour=SEA, deep=SEA_2):
    waves = "".join(f'<path d="M{x} {y + dy} q15 -9 30 0" stroke="#fff" stroke-width="4" fill="none" opacity=".6"/>'
                    for x, dy in [(40, 30), (190, 55), (330, 25), (470, 60), (620, 35), (720, 70)])
    return f'<rect y="{y}" width="{W}" height="{H - y}" fill="{deep}"/><rect y="{y}" width="{W}" height="40" fill="{colour}"/>{waves}'


def rocks(y=440):
    return (f'<path d="M0 {y} Q120 {y - 60} 260 {y - 30} Q400 {y - 70} 520 {y - 20} Q660 {y - 50} 800 {y - 10} V{H} H0Z" fill="#7a7468"/>'
            f'<path d="M0 {y + 30} Q200 {y} 400 {y + 20} T800 {y + 20} V{H} H0Z" fill="#625d53"/>')


def hill(x, y, w, colour="#3d7a52"):
    return f'<path d="M{x - w / 2} {y} Q{x} {y - 120} {x + w / 2} {y}Z" fill="{colour}"/>'


def star_field(n=14, seed=3):
    pts, v = [], seed
    for _ in range(n):
        v = (v * 9301 + 49297) % 233280
        x = 30 + (v % 740)
        v = (v * 9301 + 49297) % 233280
        y = 20 + (v % 170)
        pts.append(sparkle(x, y, .3 + (v % 5) / 10, "#fff3c4"))
    return "".join(pts)


def basket(x, y, s=1.0):
    toms = "".join(f'<circle cx="{cx}" cy="{cy}" r="11" fill="#e2412f"/>'
                   for cx, cy in [(-26, -16), (-6, -22), (14, -20), (30, -12), (-14, -6), (8, -8)])
    return (f'<g transform="translate({x} {y}) scale({s})">{toms}'
            f'<path d="M-46 -6 L46 -6 L36 18 L-36 18Z" fill="#c8924f"/>'
            f'<path d="M-40 4 H40" stroke="#a87337" stroke-width="4"/></g>')


def bible(dx=0, dy=-96, s=1.0):
    return (f'<g transform="translate({dx} {dy}) scale({s})">'
            f'<path d="M-30 -14 L0 -8 L30 -14 L30 14 L0 20 L-30 14Z" fill="#fff"/>'
            f'<path d="M0 -8 V20" stroke="#bbb" stroke-width="2"/>'
            f'<path d="M-30 14 L0 20 L30 14 L30 18 L0 24 L-30 18Z" fill="{RED}"/></g>')


def rain(n=60):
    out, v = [], 7
    for _ in range(n):
        v = (v * 9301 + 49297) % 233280
        x = v % W
        v = (v * 9301 + 49297) % 233280
        y = v % H
        out.append(f'<path d="M{x} {y} l-8 22" stroke="#a9c4e8" stroke-width="2.5" opacity=".6" stroke-linecap="round"/>')
    return "".join(out)


# ---------------------------------------------------------------- pages

def cover():
    return svg(KENTE + sky(*DUSK, "dusk") + star_field(8) + sea(320) + lighthouse(600, 330, 1.1, dark_sky=True)
               + rocks(450) + ama(260, 470, 1.05, arms="up") + sparkle(170, 300, 1.2, "#fff3c4")
               + sparkle(360, 290, .9, "#fff3c4"),
               "Ama raising her arms on the rocks by the sea as a lighthouse shines at dusk")


def beach():
    return svg(sky() + sun(110, 90, 44) + cloud(380, 70, .8) + sea(300)
               + hill(700, 300, 220) + lighthouse(700, 230, .45, beams=False)
               + f'<path d="M0 380 Q400 340 800 380 V{H} H0Z" fill="{SAND}"/>'
               + palm(70, 420, 1.0) + palm(760, 400, .9)
               + canoe(250, 420, .85) + canoe(560, 440, .9, ("#1f7a3a", "#ffcd4a", "#c1272d"), flip=True)
               + canoe(420, 395, .6, ("#3a7bd5", "#fff", "#c1272d"))
               + ama(400, 490, 1.0, arms="wave"),
               "Ama waving on a sandy beach with palm trees and brightly painted canoes")


def lighthouse_scene():
    return svg(KENTE + sky(*DUSK, "dusk") + star_field(6) + sea(300) + hill(640, 300, 300, "#2f5e46")
               + lighthouse(640, 220, .8, dark_sky=True) + rocks(430)
               + nana(210, 470, 1.0) + ama(320, 474, .82, arms="point")
               + bubble(90, 200, 300, "Why does it shine?", 300, 340, 24),
               "Ama and her grandmother on the rocks at sunset, watching the lighthouse shine")


def church():
    wall = (f'<rect width="{W}" height="{H}" fill="#f6ead2"/>'
            + "".join(f'<path d="M{x} 250 V120 Q{x + 40} 70 {x + 80} 120 V250Z" fill="#bfe3f5"/>'
                      f'<path d="M{x + 40} 90 V250 M{x} 170 H{x + 80}" stroke="#f6ead2" stroke-width="6"/>'
                      for x in (60, 660))
            + f'<rect y="380" width="{W}" height="140" fill="#c9a77a"/>')
    cross = '<rect x="392" y="40" width="16" height="80" fill="#8a5a3b"/><rect x="368" y="62" width="64" height="14" fill="#8a5a3b"/>'
    pulpit = '<path d="M338 412 L462 412 L448 300 L352 300Z" fill="#8a5a3b"/><rect x="336" y="292" width="128" height="14" rx="4" fill="#6d3d1f"/>'
    pastor = person(400, 400, 1.15, "deep", NAVY, NAVY, "short", "black", arms="hold",
                    extra=bible(0, -98, .8))
    bench = '<rect x="80" y="470" width="640" height="22" rx="6" fill="#6d3d1f"/>'
    congregation = (person(190, 520, .9, "brown", "#3aa76d", NAVY, back=True)
                    + nana(330, 524, .95, back=True) + ama(430, 524, .78, back=True)
                    + person(560, 522, .92, "tan", "#8e6cc9", NAVY, "wrap", "#3a7bd5", robe=True, back=True))
    return svg(KENTE + wall + cross + pastor + pulpit + bench + congregation
               + bubble(450, 120, 330, "You are the light of the world.", 440, 210, 20),
               "A pastor reading from the Bible at the front of a church while Ama and Nana listen")


def bedtime():
    room = (f'<rect width="{W}" height="{H}" fill="#2d3a63"/>'
            f'<rect x="520" y="70" width="200" height="170" rx="8" fill="#14284a"/>'
            f'<circle cx="640" cy="130" r="30" fill="#fff3c4"/><circle cx="652" cy="122" r="26" fill="#14284a"/>'
            + "".join(sparkle(x, y, .4, "#fff3c4") for x, y in [(560, 110), (590, 200), (690, 200)])
            + f'<path d="M620 70 V240 M520 155 H720" stroke="#5a6a98" stroke-width="8"/>'
            f'<rect y="430" width="{W}" height="90" fill="#4a3a5e"/>')
    bed = ('<rect x="120" y="360" width="420" height="80" rx="12" fill="#8a5a3b"/>'
           '<rect x="100" y="300" width="30" height="150" rx="8" fill="#6d3d1f"/>'
           '<ellipse cx="190" cy="350" rx="56" ry="24" fill="#fff"/>'
           '<path d="M200 330 Q380 300 530 340 L530 380 L200 380Z" fill="#ffcd4a"/>'
           + "".join(f'<circle cx="{x}" cy="{y}" r="7" fill="#f2884b"/>' for x, y in [(280, 345), (360, 335), (440, 345)]))
    head = ('<g transform="translate(190 326)">'
            f'<circle r="25" fill="{SKIN["brown"]}"/>'
            '<circle cx="-22" cy="-20" r="12" fill="#1f1a17"/><circle cx="22" cy="-20" r="12" fill="#1f1a17"/>'
            '<path d="M-24 -2 Q-24 -26 0 -26 Q24 -26 24 -2 Q12 -14 0 -14 Q-12 -14 -24 -2Z" fill="#1f1a17"/>'
            f'<path d="M-12 0 q4 3 8 0 M4 0 q4 3 8 0" stroke="{INK}" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
            f'<path d="M-6 10 Q0 15 6 10" stroke="{INK}" stroke-width="2.5" fill="none" stroke-linecap="round"/></g>')
    glow = '<circle cx="190" cy="326" r="60" fill="#fff3c4" opacity=".22"/>'
    return svg(KENTE + room + glow + bed + head + nana(380, 470, 1.0, arms="hold")
               + heart(260, 240, 1.4, "#ffcd4a") + sparkle(300, 200, .8, "#fff3c4"),
               "Nana sitting beside Ama's bed at night while Ama prays, with the moon in the window")


def morning():
    wall = (f'<rect y="300" width="{W}" height="140" fill="#e8c9a0"/>'
            f'<rect y="290" width="{W}" height="14" fill="#d1ad80"/>'
            f'<rect y="430" width="{W}" height="90" fill="#d9b88f"/>')
    return svg(KENTE + sky("#ffd9a0", "#ffeccd", "dawn") + sun(400, 270, 80) + wall
               + palm(720, 440, .9) + nana(300, 480, 1.0, arms="hold")
               + ama(440, 482, .84, arms="hold", extra=bible(0, -96, 1))
               + sparkle(380, 170, 1.1) + sparkle(560, 200, .8) + sparkle(220, 210, .7),
               "Ama and Nana reading a Bible together in their courtyard as the sun rises")


def market():
    stalls = "".join(
        f'<rect x="{x}" y="300" width="8" height="120" fill="#6d3d1f"/>'
        f'<path d="M{x - 70} 300 Q{x + 4} 240 {x + 78} 300Z" fill="{c}"/>'
        f'<rect x="{x - 60}" y="380" width="130" height="40" fill="#a8713f"/>'
        + "".join(f'<circle cx="{x - 44 + k * 22}" cy="374" r="10" fill="{f}"/>' for k in range(5))
        for x, c, f in [(110, "#3a7bd5", "#e2412f"), (680, "#c1272d", "#ffcd4a")])
    ground = f'<rect y="420" width="{W}" height="100" fill="#d9b88f"/>'
    load = basket(0, -168, .95)
    efua = person(560, 486, 1.02, "brown", "#8e6cc9", "#f2b632", "wrap", "#3aa76d", robe=True,
                  arms="wave", flip=True)
    return svg(KENTE + sky() + sun(400, 70, 36) + cloud(240, 80, .7) + stalls + ground
               + ama(330, 484, .9, arms="up", extra=load) + efua
               + bubble(480, 170, 250, "Medaase, Ama!", 560, 300, 24),
               "Ama carrying a basket of tomatoes on her head through a market as Auntie Efua thanks her")


def school():
    building = ('<rect x="40" y="220" width="320" height="200" fill="#5fa8d3"/>'
                '<path d="M20 230 L200 160 L380 230Z" fill="#a8713f"/>'
                '<rect x="170" y="320" width="60" height="100" fill="#2d3a63"/>'
                + "".join(f'<rect x="{x}" y="260" width="50" height="40" fill="#fff" opacity=".85"/>' for x in (70, 280))
                + '<rect x="120" y="190" width="160" height="26" rx="4" fill="#fff"/>'
                f'<text x="200" y="209" text-anchor="middle" font-family="Trebuchet MS, Verdana, sans-serif" '
                f'font-weight="700" font-size="16" fill="{NAVY}">SCHOOL</text>')
    ground = f'<rect y="420" width="{W}" height="100" fill="{GRASS}"/>'
    mango = tree(640, 470, .8) + "".join(f'<ellipse cx="{x}" cy="{y}" rx="8" ry="11" fill="#f2a53a"/>'
                                         for x, y in [(590, 260), (680, 230), (720, 270), (620, 210)])
    kenkey = '<ellipse cx="74" cy="-118" rx="18" ry="11" fill="#7fb35a"/><path d="M58 -118 H90" stroke="#5e8f3f" stroke-width="3"/>'
    return svg(sky() + sun(110, 80, 38) + cloud(440, 70, .8) + building + ground + mango
               + kwame(650, 474, .82) + ama(450, 478, .88, arms="point", extra=kenkey)
               + bubble(330, 160, 200, "Akwaaba!", 440, 320, 26),
               "Ama walking over to a new boy, Kwame, who is alone under a mango tree, to share her lunch")


def friends():
    ground = f'<rect y="420" width="{W}" height="100" fill="{GRASS}"/>'
    mango = tree(400, 470, 1.05) + "".join(f'<ellipse cx="{x}" cy="{y}" rx="9" ry="12" fill="#f2a53a"/>'
                                           for x, y in [(320, 200), (470, 170), (520, 230), (300, 130), (420, 110)])
    return svg(sky() + sun(700, 80, 38) + cloud(160, 80, .8) + ground + mango
               + ama(300, 482, .9, arms="out") + kwame(510, 482, .9, arms="down", flip=True)
               + heart(405, 370, 1.6) + sparkle(380, 340, .6) + sparkle(430, 330, .5)
               + bubble(520, 250, 270, "Why are you kind?", 520, 340, 22),
               "Ama and Kwame talking together under the mango tree, with a heart between them")


def storm():
    waves = "".join(f'<path d="M{x} 380 q40 -50 80 0 q-20 -10 -30 10Z" fill="#3a6f94"/>'
                    for x in range(-20, 820, 90))
    bolt = '<path d="M520 40 L480 140 L510 140 L470 240 L560 120 L528 120 L560 40Z" fill="#ffe27a"/>'
    town = "".join(f'<rect x="{x}" y="{420 - h}" width="60" height="{h}" fill="#2a2f3d"/>'
                   f'<rect x="{x + 22}" y="{434 - h}" width="16" height="16" fill="#1a1e28"/>'
                   for x, h in [(20, 60), (100, 80), (180, 50)])
    boat = canoe(600, 350, .45, ("#c1272d", "#ffcd4a", "#1f7a3a"))
    return svg(sky(*STORM, "storm") + bolt + sea(340, "#2c5878", "#1e3e57") + waves + boat
               + f'<path d="M0 420 Q150 400 300 430 V{H} H0Z" fill="#4a4538"/>' + town + rain(80),
               "A wild storm over the sea at night, with rain, lightning, big waves and a small canoe far away")


def praying():
    return svg(sky(*STORM, "storm") + sea(330, "#2c5878", "#1e3e57")
               + hill(640, 330, 320, "#253a30") + lighthouse(640, 250, .8, dark_sky=True)
               + f'<path d="M0 410 Q400 380 800 410 V{H} H0Z" fill="#4a4538"/>'
               + ama(250, 484, .9, arms="down") + kwame(330, 486, .9, arms="down")
               + heart(290, 300, 1.2, "#ffcd4a") + rain(70),
               "Ama and Kwame holding hands and praying in the rain while the lighthouse shines on the hill")


def home():
    return svg(KENTE + sky(*NIGHT, "night") + star_field(16) + sea(300, "#2f5f8a", "#22476b")
               + hill(700, 300, 240, "#253a30") + lighthouse(700, 230, .55, dark_sky=True)
               + f'<path d="M0 380 Q400 350 800 380 V{H} H0Z" fill="#c9b48a"/>'
               + canoe(160, 410, .8) + canoe(620, 420, .75, ("#1f7a3a", "#ffcd4a", "#c1272d"), flip=True)
               + papa(420, 486, 1.05, arms="out") + kwame(470, 488, .8, arms="out", flip=True)
               + nana(140, 488, .9) + ama(230, 490, .76, arms="up")
               + heart(445, 300, 1.3),
               "Canoes safe on the beach under the stars as Kwame hugs his father, with Ama and Nana watching")


def together():
    chapel = ('<rect x="470" y="220" width="280" height="210" fill="#fbf2e2"/>'
              '<path d="M450 230 L610 130 L770 230Z" fill="#c1272d"/>'
              '<rect x="602" y="70" width="16" height="70" fill="#8a5a3b"/><rect x="586" y="88" width="48" height="12" fill="#8a5a3b"/>'
              '<path d="M580 430 V350 Q610 320 640 350 V430Z" fill="#8a5a3b"/>'
              + "".join(f'<path d="M{x} 310 V270 Q{x + 18} 250 {x + 36} 270 V310Z" fill="#bfe3f5"/>' for x in (500, 690)))
    ground = f'<rect y="430" width="{W}" height="90" fill="{GRASS}"/><path d="M560 430 L660 430 L520 520 L380 520Z" fill="{SAND}"/>'
    return svg(sky() + sun(110, 80, 40) + cloud(330, 70, .8) + chapel + ground + palm(420, 430, .8)
               + ama(160, 492, .86, arms="down") + kwame(240, 494, .86, arms="down")
               + esi(310, 496, .6, arms="up")
               + sparkle(370, 260, 1) + sparkle(200, 250, .8),
               "Ama, Kwame and his little sister Esi walking together towards a church on a sunny morning")


def ending():
    return svg(KENTE + sky(*DUSK, "dusk") + star_field(12) + sea(300) + hill(660, 300, 280, "#2f5e46")
               + lighthouse(660, 220, .78, dark_sky=True) + rocks(430)
               + nana(120, 470, .95) + ama(220, 472, .8, arms="up") + kwame(300, 474, .82, arms="wave")
               + esi(370, 476, .6, arms="up")
               + heart(250, 250, 1.1, "#ffcd4a") + heart(330, 230, .9, "#ffcd4a"),
               "Ama, Kwame, Esi and Nana together on the rocks at dusk, watching the lighthouse under the first stars")


SCENES = {"cover": cover, "beach": beach, "lighthouse": lighthouse_scene, "church": church,
          "bedtime": bedtime, "morning": morning, "market": market, "school": school,
          "friends": friends, "storm": storm, "praying": praying, "home": home,
          "together": together, "ending": ending}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in SCENES.items():
        path = OUT / f"{name}.svg"
        path.write_text(draw(), encoding="utf-8")
        print(f"  {path.relative_to(ROOT)}  {path.stat().st_size / 1024:.1f}KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
