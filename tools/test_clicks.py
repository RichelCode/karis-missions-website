#!/usr/bin/env python3
"""
Drive a real browser and click things, rather than trusting the markup.

Checks, on every page of the site:
  * every top-level nav item navigates to the page it names
  * every dropdown opens on click and its items navigate
  * the dropdown survives the pointer travelling from the label to the menu
    (the classic hover-gap bug)
  * every in-page link resolves to a real page, with no JS errors on the way
  * the mobile drawer opens, closes, and its links navigate

Usage:  python3 tools/test_clicks.py [--port 8000]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import websocket  # websocket-client

ROOT = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


class Browser:
    """A very small Chrome DevTools Protocol client."""

    def __init__(self, debug_port: int = 9222, width: int = 1440, height: int = 900):
        self.proc = subprocess.Popen(
            [CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
             f"--remote-debugging-port={debug_port}",
             "--remote-allow-origins=*",
             f"--window-size={width},{height}",
             "--user-data-dir=/tmp/karis-cdp-profile",
             "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        ws_url = self._wait_for_target(debug_port)
        self.ws = websocket.create_connection(ws_url, timeout=20, suppress_origin=True)
        self.msg_id = 0
        self.send("Runtime.enable")
        self.send("Page.enable")
        # The profile directory persists between runs, so without this the
        # browser happily tests a stale copy of the CSS and JS.
        self.send("Network.enable")
        self.send("Network.setCacheDisabled", cacheDisabled=True)
        # Collect uncaught errors on every page, before any page script runs.
        self.send(
            "Page.addScriptToEvaluateOnNewDocument",
            source="window.__errs=[];"
                   "addEventListener('error',e=>window.__errs.push(String(e.message)));"
                   "addEventListener('unhandledrejection',"
                   "e=>window.__errs.push('unhandled rejection: '+e.reason));",
        )

    @staticmethod
    def _wait_for_target(port: int, timeout: float = 20) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as r:
                    for t in json.load(r):
                        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                            return t["webSocketDebuggerUrl"]
            except (urllib.error.URLError, ConnectionError, json.JSONDecodeError):
                pass
            time.sleep(0.25)
        raise RuntimeError("Chrome did not expose a debugging target")

    def send(self, method: str, **params) -> dict:
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                return msg.get("result", {})

    def eval(self, expression: str, awaitp: bool = False):
        res = self.send("Runtime.evaluate", expression=expression,
                        returnByValue=True, awaitPromise=awaitp)
        if "exceptionDetails" in res:
            detail = res["exceptionDetails"]
            text = detail.get("exception", {}).get("description") or detail.get("text")
            raise RuntimeError(f"JS error: {text}")
        return res.get("result", {}).get("value")

    def goto(self, url: str) -> None:
        self.send("Page.navigate", url=url)
        self._settle()

    def _settle(self, timeout: float = 12) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if self.eval("document.readyState") == "complete" and \
                   self.eval("!!document.querySelector('.site-header')"):
                    time.sleep(0.12)
                    return
            except RuntimeError:
                pass
            time.sleep(0.12)

    def close(self) -> None:
        try:
            self.ws.close()
        finally:
            self.proc.terminate()


def here(b: Browser) -> str:
    return b.eval("location.pathname.split('/').pop() || 'index.html'")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    base = f"http://localhost:{args.port}"

    pages = sorted(p.name for p in ROOT.glob("*.html"))
    failures: list[str] = []
    checked = {"nav": 0, "submenu": 0, "links": 0}

    b = Browser()
    try:
        # ---------- 1. every top-level nav item navigates -------------------
        print("\nTop-level navigation")
        b.goto(f"{base}/index.html")
        items = b.eval("""
            Array.from(document.querySelectorAll('.nav-list > li > .nav-link'))
                 .map(a => ({text: a.textContent.trim(),
                             href: a.getAttribute('href')}))
        """)
        for item in items:
            b.goto(f"{base}/index.html")
            b.eval(
                "document.querySelector('.nav-list > li > .nav-link[href=\"%s\"]').click()"
                % item["href"]
            )
            b._settle()
            landed = here(b)
            checked["nav"] += 1
            ok = landed == item["href"]
            print(f"  {'ok ' if ok else 'FAIL'} {item['text']:<16} -> {landed}")
            if not ok:
                failures.append(
                    f"nav '{item['text']}' went to {landed}, expected {item['href']}")

        # ---------- 2. dropdowns open, survive the gap, and navigate --------
        print("\nDropdown menus")
        b.goto(f"{base}/index.html")
        groups = b.eval("""
            Array.from(document.querySelectorAll('.has-menu')).map((li, i) => ({
              i: i,
              label: li.querySelector('.nav-link').textContent.trim(),
              items: Array.from(li.querySelectorAll('.submenu a'))
                          .map(a => a.getAttribute('href'))
            }))
        """)
        for g in groups:
            # Open by clicking the chevron.
            b.goto(f"{base}/index.html")
            opened = b.eval(f"""
                (() => {{
                  const li = document.querySelectorAll('.has-menu')[{g['i']}];
                  li.querySelector('.nav-toggle').click();
                  const menu = li.querySelector('.submenu');
                  return getComputedStyle(menu).display !== 'none';
                }})()
            """)
            if not opened:
                failures.append(f"dropdown '{g['label']}' did not open on click")
                print(f"  FAIL {g['label']:<16} did not open")
                continue

            # The submenu must sit within the invisible bridge, so a pointer
            # moving straight down from the label never leaves the <li>.
            gap = b.eval(f"""
                (() => {{
                  const li = document.querySelectorAll('.has-menu')[{g['i']}];
                  const link = li.querySelector('.nav-link').getBoundingClientRect();
                  const menu = li.querySelector('.submenu').getBoundingClientRect();
                  const bridge = getComputedStyle(li, '::after');
                  const h = parseFloat(bridge.height) || 0;
                  return Math.round(menu.top - link.bottom - h);
                }})()
            """)
            bridged = gap <= 0
            if not bridged:
                failures.append(
                    f"dropdown '{g['label']}' has a {gap}px unbridged hover gap")

            # Every item in the menu must navigate.
            bad = []
            for href in g["items"]:
                b.goto(f"{base}/index.html")
                b.eval(f"""
                    (() => {{
                      const li = document.querySelectorAll('.has-menu')[{g['i']}];
                      li.querySelector('.nav-toggle').click();
                      li.querySelector('.submenu a[href="{href}"]').click();
                    }})()
                """)
                b._settle()
                landed = here(b)
                checked["submenu"] += 1
                if landed != href.split("#")[0]:
                    bad.append(f"{href} -> {landed}")
            if bad:
                failures.append(f"dropdown '{g['label']}' items failed: {', '.join(bad)}")
            state = "ok " if bridged and not bad else "FAIL"
            print(f"  {state} {g['label']:<16} opens, {len(g['items'])} items, "
                  f"gap {gap}px")

        # ---------- 3. mobile drawer ---------------------------------------
        print("\nMobile drawer")
        b.send("Emulation.setDeviceMetricsOverride", width=390, height=780,
               deviceScaleFactor=2, mobile=True)
        b.goto(f"{base}/index.html")
        drawer = b.eval("""
            (() => {
              const btn = document.querySelector('.menu-btn');
              const nav = document.getElementById('primaryNav');
              const vis = () => getComputedStyle(nav).visibility;
              const before = vis();
              btn.click();
              const open = vis();
              const w = nav.getBoundingClientRect().width;
              const h = nav.getBoundingClientRect().height;
              btn.click();
              return {before, open, closed: vis(), w: Math.round(w), h: Math.round(h),
                      vh: window.innerHeight};
            })()
        """)
        full_height = drawer["h"] >= drawer["vh"] - 2
        drawer_ok = (drawer["before"] == "hidden" and drawer["open"] == "visible"
                     and drawer["closed"] == "hidden" and full_height)
        print(f"  {'ok ' if drawer_ok else 'FAIL'} opens/closes, "
              f"{drawer['w']}x{drawer['h']}px (viewport {drawer['vh']}px tall)")
        if not drawer_ok:
            failures.append(
                f"mobile drawer: {drawer} — expected hidden/visible/hidden and full height")

        # A drawer link must navigate.
        b.goto(f"{base}/index.html")
        b.eval("""
            document.querySelector('.menu-btn').click();
            document.querySelector('#primaryNav .nav-link[href="prayer.html"]').click();
        """)
        b._settle()
        if here(b) != "prayer.html":
            failures.append(f"drawer link went to {here(b)}, expected prayer.html")
        else:
            print("  ok  drawer link navigates")
        b.send("Emulation.clearDeviceMetricsOverride")

        # ---------- 4. every link on every page ----------------------------
        print("\nEvery link on every page")
        for page in pages:
            b.goto(f"{base}/{page}")
            errors = b.eval("""
                Array.from(document.querySelectorAll('a[href]'))
                  .map(a => ({href: a.getAttribute('href'),
                              text: (a.textContent || a.getAttribute('aria-label') || '').trim()}))
                  .filter(l => l.href && !/^(https?:|mailto:|tel:|#)/.test(l.href))
            """)
            broken = []
            for link in errors:
                target = link["href"].split("#")[0]
                checked["links"] += 1
                if not (ROOT / target).exists():
                    broken.append(f"{link['text'] or '(no text)'} -> {link['href']}")
            status = "ok " if not broken else "FAIL"
            print(f"  {status} {page:<28} {len(errors)} internal links")
            for bad in broken:
                failures.append(f"{page}: broken link {bad}")

        # ---------- 5. no JavaScript errors anywhere ------------------------
        print("\nJavaScript errors")
        for page in pages:
            b.goto(f"{base}/{page}")
            errs = b.eval("window.__errs || []")
            if errs:
                failures.append(f"{page}: JS errors {errs}")
        print(f"  ok  {len(pages)} pages loaded without throwing")

    finally:
        b.close()

    print(f"\nChecked {checked['nav']} top-level items, {checked['submenu']} submenu "
          f"items, {checked['links']} internal links across {len(pages)} pages.")

    if failures:
        print(f"\n{len(failures)} FAILURE(S):\n")
        for f in failures:
            print(f"  {f}")
        return 1

    print("\nAll navigation and links work.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
