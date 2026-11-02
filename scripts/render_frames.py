#!/usr/bin/env python3
"""Render the key moments of SMIL SVG figures into a contact sheet.

Usage:
  python scripts/render_frames.py figure.svg [more.svg ...] [--out frames] [--times 0,1.5,3]
                                  [--max-frames 8] [--width 750]

For each SVG the script:
  1. collects every turning point (keyTimes x dur) of the main loop, plus the
     midpoint of each transition, and keeps at most --max-frames of them;
  2. opens the SVG in headless Chrome/Chromium, pauses it with pauseAnimations()
     and jumps to each time with setCurrentTime(t);
  3. saves one PNG per frame and a labelled contact sheet <name>-sheet.png;
  4. reports text that leaves the canvas at any rendered frame.

Look at the contact sheet: the script proves that frames render, not that they
explain the passage well.

Requirements: Python Playwright (pip install playwright). It uses the browser in
CHROME_PATH if set, otherwise a system Chrome/Chromium, otherwise Playwright's own
(python -m playwright install chromium). Pillow is optional; without it no sheet is
made and only the individual frames are saved.
"""

import argparse
import asyncio
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = "{http://www.w3.org/2000/svg}"
ANIMATION_TAGS = {f"{SVG}animate", f"{SVG}animateTransform", f"{SVG}animateMotion", f"{SVG}set"}
AMBIENT_LOOP_SECONDS = 1.5


def seconds(value):
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)s\s*", value or "")
    return float(match.group(1)) if match else None


def key_moments(svg_path, max_frames):
    """Turning points of the longest loop, midpoints of transitions, deduplicated."""
    root = ET.parse(svg_path).getroot()
    anims = [el for el in root.iter() if el.tag in ANIMATION_TAGS]
    durs = [d for d in (seconds(a.get("dur")) for a in anims) if d]
    if not durs:
        return [0.0], 0.0
    main = max(durs)
    points = {0.0}
    for a in anims:
        dur = seconds(a.get("dur"))
        if not dur or dur < min(AMBIENT_LOOP_SECONDS, main):
            continue  # loaders and pulses would flood the sheet
        try:
            kts = [float(k) for k in (a.get("keyTimes") or "0;1").split(";")]
        except ValueError:
            continue
        reps = max(1, round(main / dur))
        for r in range(reps):
            for i, k in enumerate(kts):
                points.add(round((r + k) * dur, 3))
                if i + 1 < len(kts) and kts[i + 1] - k > 1e-6:
                    points.add(round((r + (k + kts[i + 1]) / 2) * dur, 3))
    times = sorted(t for t in points if 0 <= t < main - 1e-3)
    merged = []
    for t in times:
        if not merged or t - merged[-1] >= 0.12:
            merged.append(t)
    if len(merged) > max_frames:
        step = (len(merged) - 1) / (max_frames - 1)
        merged = [merged[round(i * step)] for i in range(max_frames)]
    return merged, main


def find_browser():
    for candidate in (os.environ.get("CHROME_PATH"), shutil.which("google-chrome"),
                      shutil.which("chromium"), shutil.which("chromium-browser"),
                      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if candidate and Path(candidate).exists():
            return candidate
    return None


OVERFLOW_JS = """
() => {
  const svg = document.querySelector('svg');
  const box = svg.getBoundingClientRect();
  const out = [];
  svg.querySelectorAll('text').forEach((t) => {
    const r = t.getBoundingClientRect();
    if (!r.width || getComputedStyle(t).opacity === '0') return;
    if (r.left < box.left - 1 || r.right > box.right + 1 || r.top < box.top - 1 || r.bottom > box.bottom + 1)
      out.push(t.textContent.trim().slice(0, 20));
  });
  return out;
}
"""


async def render(paths, out_dir, explicit_times, max_frames, width):
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: Playwright is not installed. Run: pip install playwright", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    browser_path = find_browser()
    problems = 0
    async with async_playwright() as p:
        launch = {"executable_path": browser_path} if browser_path else {}
        try:
            browser = await p.chromium.launch(**launch)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: cannot start Chromium ({exc}). Set CHROME_PATH or run "
                  "`python -m playwright install chromium`.", file=sys.stderr)
            return 1
        page = await browser.new_page(viewport={"width": width, "height": 1200}, device_scale_factor=1)
        for path in paths:
            times, main = (explicit_times, None) if explicit_times else key_moments(path, max_frames)
            svg = path.read_text(encoding="utf-8")
            svg = re.sub(r"^\s*<\?xml[^>]*>", "", svg)
            await page.set_content(
                f'<html><body style="margin:0;background:#fff">'
                f'<div style="width:{width}px">{svg}</div></body></html>')
            await page.wait_for_timeout(200)
            frames = []
            overflow = set()
            for t in times:
                await page.evaluate(
                    f"() => {{ const s = document.querySelector('svg'); s.pauseAnimations(); s.setCurrentTime({t}); }}")
                await page.wait_for_timeout(60)
                for text in await page.evaluate(OVERFLOW_JS):
                    overflow.add(text)
                frame = out_dir / f"{path.stem}@{t:g}s.png"
                await (await page.query_selector("svg")).screenshot(path=str(frame))
                frames.append((t, frame))
            sheet = make_sheet(frames, out_dir / f"{path.stem}-sheet.png")
            loop = f", loop {main:g}s" if main else ""
            print(f"{path}: {len(frames)} frames at {', '.join(f'{t:g}s' for t in times)}{loop}")
            if sheet:
                print(f"  sheet: {sheet}")
            if overflow:
                problems += 1
                print(f"  WARNING: text leaves the canvas in at least one frame: {', '.join(sorted(overflow))}")
        await browser.close()
    return 1 if problems else 0


def make_sheet(frames, target):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    images = [(t, Image.open(f).convert("RGB")) for t, f in frames]
    if not images:
        return None
    thumb_w = 360
    scaled = [(t, im.resize((thumb_w, round(im.height * thumb_w / im.width)))) for t, im in images]
    cols = min(4, len(scaled))
    rows = (len(scaled) + cols - 1) // cols
    cell_h = max(im.height for _, im in scaled) + 34
    sheet = Image.new("RGB", (cols * (thumb_w + 16) + 16, rows * cell_h + 16), "#FFFFFF")
    draw = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate(scaled):
        x = 16 + (i % cols) * (thumb_w + 16)
        y = 16 + (i // cols) * cell_h
        draw.text((x, y), f"t = {t:g}s", fill="#333333")
        sheet.paste(im, (x, y + 18))
    sheet.save(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("svgs", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=Path("frames"))
    parser.add_argument("--times", help="comma-separated seconds, e.g. 0,1.2,3")
    parser.add_argument("--max-frames", type=int, default=8)
    parser.add_argument("--width", type=int, default=750, help="render width in CSS px (use 360 to mimic a phone)")
    args = parser.parse_args()
    times = [float(t) for t in args.times.split(",")] if args.times else None
    return asyncio.run(render(args.svgs, args.out, times, max(2, args.max_frames), args.width))


if __name__ == "__main__":
    raise SystemExit(main())
