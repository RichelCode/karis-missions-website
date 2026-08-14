#!/usr/bin/env python3
"""
Remove em dashes from all site copy, rewriting the punctuation rather than
just swapping the character.

Runs in two passes:

  1. OVERRIDES — phrases where the dash was doing real work (introducing a
     list, holding an aside) and a mechanical swap would read badly. These
     are rewritten by hand.
  2. General rules for the remainder:
       <strong>Label</strong> — text  ->  <strong>Label</strong>: text
       ... — We are ...               ->  ... . We are ...
       ... — we would like ...        ->  ... . We would like ...
       ... — and so on                ->  ... , and so on

En dashes in numeric ranges (9:00 – 10:15am, 3–4 weeks) are deliberately left
alone: they are correct typography and are not what reads as machine-written.

Usage:  python3 tools/dedash.py [--apply]
"""
from __future__ import annotations

import argparse
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGETS = sorted((ROOT / "src").rglob("*.html")) + [ROOT / "src" / "data" / "downloads.json"]

# Phrases the general rules would mangle. Applied first, in order.
OVERRIDES: list[tuple[str, str]] = [
    # Titles and meta descriptions
    ("Karis Missions International — Taking the Gospel, Making Disciples",
     "Karis Missions International: Taking the Gospel, Making Disciples"),
    ("The Statement of Faith of Karis Missions International — our convictions",
     "The Statement of Faith of Karis Missions International: our convictions"),
    ("Contact Karis Missions International — questions, ministry invitations, partnerships, resources, and mission enquiries — all welcome.",
     "Contact Karis Missions International about questions, ministry invitations, partnerships, resources, and mission enquiries."),
    ("Support Gospel-centered mission through Karis Missions International — missionary preparation",
     "Support Gospel-centered mission through Karis Missions International: missionary preparation"),
    ("ministry partners — Learn, Live, Lead, Multiply.",
     "ministry partners: Learn, Live, Lead, Multiply."),

    # Lists introduced by a dash
    ("<p>Our teaching and discipleship ministry — devotions,",
     "<p>Our teaching and discipleship ministry: devotions,"),
    ("around the Karis Framework — Know, Grow, Serve, Go, Multiply.",
     "around the Karis Framework: Know, Grow, Serve, Go, Multiply."),
    ("participate in the Great Commission — making disciples of all nations",
     "participate in the Great Commission: making disciples of all nations"),
    ("where our assemblies are already planted — street outreach,",
     "where our assemblies are already planted: street outreach,"),
    ("formation, not information alone: <strong>Learn",
     "formation, not information alone: <strong>Learn"),

    # Asides that need brackets rather than a comma
    ("existing in three Persons — Father, Son, and Holy Spirit — equal in power and glory",
     "existing in three Persons (Father, Son, and Holy Spirit), equal in power and glory"),
    ("<p>Whatever you are carrying — a decision, a diagnosis, a family, a fear, a person you have prayed for over years — you can bring it here.",
     "<p>Whatever you are carrying (a decision, a diagnosis, a family, a fear, a person you have prayed for over years), you can bring it here."),
    ("We affirm the Holy Bible — the sixty-six books of the Old and New Testaments — as the inspired",
     "We affirm the Holy Bible, the sixty-six books of the Old and New Testaments, as the inspired"),
    ("comes from the Greek <em>charis</em> — grace.",
     "comes from the Greek <em>charis</em>, meaning grace."),

    # Select options and field hints
    ("<option>100 — Foundations</option>", "<option>100: Foundations</option>"),
    ("<option>200 — Discipleship</option>", "<option>200: Discipleship</option>"),
    ("<option>300 — Ministry</option>", "<option>300: Ministry</option>"),
    ("<option>400 — Missions</option>", "<option>400: Missions</option>"),
    ("<option>500 — Leadership</option>", "<option>500: Leadership</option>"),
    ("<option>Praise report — answered prayer</option>",
     "<option>Praise report: answered prayer</option>"),
    ("<li>Join us in person — midweek prayer meets every week.</li>",
     "<li>Join us in person: midweek prayer meets every week.</li>"),

    # Hero fact strip: each should end cleanly, then invite the click
    ("5905 Flintridge Drive, Colorado Springs — <a href=\"assemblies.html\">and three more assemblies</a>",
     "5905 Flintridge Drive, Colorado Springs. <a href=\"assemblies.html\">See all four assemblies</a>"),
    ("Print-ready and free to reproduce — <a href=\"resources.html#tracts\">download them now</a>",
     "Print-ready and free to reproduce. <a href=\"resources.html#tracts\">Download them now</a>"),
    ("One week to three months, with a local church — <a href=\"volunteer-application.html\">apply to serve</a>",
     "One week to three months, with a local church. <a href=\"volunteer-application.html\">Apply to serve</a>"),

    # FAQ question that must stay a question
    ("<summary>I cannot give financially — can I still help?</summary>",
     "<summary>I cannot give financially. Can I still help?</summary>"),

    # Sentences that read better rebuilt than repunctuated
    ("move a person to the next one — a decision is a beginning, not a result.",
     "move a person to the next one. A decision is a beginning, not a result."),
    ("churches, and mission teams — no sign-up, no cost, no permission process.",
     "churches, and mission teams, with no sign-up, no cost, and no permission process."),
    ("tri-fold tracts in PDF and editable Word — swap in your own assembly's details and print.",
     "tri-fold tracts in PDF and editable Word. Swap in your own assembly's details and print."),
    ("<a href=\"contact.html\">tell us</a> — it moves up the list.",
     "<a href=\"contact.html\">tell us</a> and it moves up the list."),
    ("<a href=\"partner.html\">Partner page</a> — they reach the right people faster.",
     "<a href=\"partner.html\">Partner page</a>. Those reach the right people faster."),
]

INDEPENDENT = {
    "we", "it", "they", "you", "i", "he", "she", "this", "that", "there",
    "our", "your", "their", "his", "her", "its", "nothing", "none",
    "please", "come", "start", "ask", "tell", "send", "give", "take", "use",
    "read", "write", "call", "those", "these", "midweek",
}
CONJUNCTION = {"and", "but", "so", "or", "yet", "nor", "then", "with", "without",
               "including", "even", "not", "no", "shared", "worth", "written",
               "each", "in", "of", "for", "to", "a", "an", "the", "as", "all"}

DASH = re.compile(r"\s*—\s*(\w+)?")


def general_pass(text: str) -> tuple[str, int]:
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        count += 1
        word = m.group(1) or ""
        lower = word.lower()
        before = text[:m.start()].rstrip()

        if before.endswith("</strong>"):
            return f": {word}"
        if word and word[0].isupper():
            return f". {word}"
        if lower in CONJUNCTION:
            return f", {word}"
        if lower in INDEPENDENT:
            return f". {word.capitalize()}"
        return f", {word}"

    return DASH.sub(repl, text), count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the changes")
    args = ap.parse_args()

    total_over = total_gen = 0
    for path in TARGETS:
        original = path.read_text(encoding="utf-8")
        if "—" not in original:
            continue

        updated = original
        applied = []
        for old, new in OVERRIDES:
            if old in updated:
                updated = updated.replace(old, new)
                applied.append(new)
        total_over += len(applied)

        updated, n = general_pass(updated)
        total_gen += n

        print(f"\n{path.relative_to(ROOT)}  ({len(applied)} rewritten by hand, {n} by rule)")
        for new in applied:
            print(f"    * {new[:104]}")

        if args.apply:
            path.write_text(updated, encoding="utf-8")

    print(f"\n{total_over} hand-rewritten, {total_gen} by rule. "
          f"{'Written.' if args.apply else 'Dry run — re-run with --apply.'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
