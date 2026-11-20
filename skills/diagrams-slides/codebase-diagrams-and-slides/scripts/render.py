#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
render.py - render SVG and HTML to PNG with a headless Chromium browser for visual QA.

Finds Chrome / Edge / Chromium automatically on Windows, macOS and Linux.

Examples
--------
# render every .svg in a folder to PNGs (for inspection)
python render.py svgs --dir docs/diagrams --out docs/diagrams/preview

# render specific slides of an HTML deck (uses #N deep links)
python render.py html --file docs/presentation.html --slides 11 \
       --out docs/diagrams/preview --size 1600x900

# render only some slides
python render.py html --file docs/presentation.html --pages 1 4 6 11 --out docs/diagrams/preview
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


def find_browser():
    env = os.environ.get("CHROME_PATH") or os.environ.get("CHROME")
    if env and os.path.exists(env):
        return env
    for name in ("google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def file_uri(path):
    return Path(path).resolve().as_uri()


def shot(browser, url, png, size, scale):
    w, h = size
    tmp = os.path.join(tempfile.gettempdir(), "cr_" + uuid.uuid4().hex)
    cmd = [
        browser, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
        f"--user-data-dir={tmp}", f"--force-device-scale-factor={scale}",
        f"--window-size={w},{h}", "--virtual-time-budget=3500",
        f"--screenshot={png}", url,
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=90)
    except Exception as e:                                  # noqa: BLE001
        print("  error:", e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return os.path.exists(png)


def parse_size(s):
    w, h = s.lower().split("x")
    return int(w), int(h)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    a = sub.add_parser("svgs", help="render all .svg in a directory")
    a.add_argument("--dir", required=True)
    a.add_argument("--out", default="preview")
    a.add_argument("--size", default="1280x720")
    a.add_argument("--scale", type=float, default=2.0)

    b = sub.add_parser("html", help="render slides of an HTML deck")
    b.add_argument("--file", required=True)
    b.add_argument("--slides", type=int, default=0, help="render 1..N")
    b.add_argument("--pages", type=int, nargs="*", help="explicit slide numbers")
    b.add_argument("--out", default="preview")
    b.add_argument("--size", default="1600x900")
    b.add_argument("--scale", type=float, default=1.5)

    args = ap.parse_args()
    browser = find_browser()
    if not browser:
        print("No Chrome/Edge/Chromium found. Set CHROME_PATH to the browser binary.")
        sys.exit(2)
    print("browser:", browser)
    os.makedirs(args.out, exist_ok=True)
    size = parse_size(args.size)
    ok = 0

    if args.mode == "svgs":
        files = sorted(glob.glob(os.path.join(args.dir, "*.svg")))
        if not files:
            print("no .svg files in", args.dir)
            sys.exit(1)
        for svgf in files:
            png = os.path.join(args.out, Path(svgf).stem + ".png")
            good = shot(browser, file_uri(svgf), png, size, args.scale)
            print(("OK  " if good else "FAIL ") + Path(svgf).name)
            ok += bool(good)
        print(f"done: {ok}/{len(files)} rendered -> {args.out}")
    else:
        base = file_uri(args.file)
        pages = args.pages or (list(range(1, args.slides + 1)) if args.slides else [1])
        for n in pages:
            png = os.path.join(args.out, f"slide_{n:02d}.png")
            good = shot(browser, f"{base}#{n}", png, size, args.scale)
            print(("OK  slide " if good else "FAIL slide ") + str(n))
            ok += bool(good)
        print(f"done: {ok}/{len(pages)} slides rendered -> {args.out}")


if __name__ == "__main__":
    main()
