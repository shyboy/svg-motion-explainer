#!/usr/bin/env python3
"""Validate conservative, self-contained SVG SMIL output.

Usage:
  python scripts/validate_svg.py figure.svg
  python scripts/validate_svg.py fig1.svg fig2.svg fig3.svg   # figures for one article
  python scripts/validate_svg.py --strict figure.svg          # warnings also fail

Pass every figure that will be inlined into the same article in one call so that
id collisions between figures are caught.

A figure that breaks a rule on purpose (for example, to demonstrate a bug) can mark
the animation element with data-validate-allow="transform-override" or
data-validate-allow="blank-first-frame"; the finding is then reported as ALLOWED.

Exit code 0 = no errors; 1 = validation errors or unreadable file.
Warnings do not change the exit code unless --strict is given.
"""

from pathlib import Path
import math
import re
import sys
import xml.etree.ElementTree as ET

SVG = "{http://www.w3.org/2000/svg}"
XLINK = "{http://www.w3.org/1999/xlink}href"
ANIMATION_TAGS = {f"{SVG}animate", f"{SVG}animateTransform", f"{SVG}animateMotion", f"{SVG}set"}
EVENT_BEGIN = re.compile(r"(?:^|[;\s])(?:[A-Za-z0-9_-]+\.)?(?:click|mouse|touch|pointer|scroll|focus|blur|load|begin|end)(?:$|[;\s])", re.I)
NUMBER = re.compile(r"^-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
NUM_IN_TEXT = re.compile(r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")

# Phone rendering: a 750-unit-wide figure is shown at roughly 340–360 CSS px, i.e. ~0.46x.
REFERENCE_WIDTH = 750.0
MIN_FONT_SIZE = 20.0          # in 750-wide units ≈ 9 px on a phone; below this is hard to read
DEFAULT_FONT_SIZE = 16.0
AMBIENT_LOOP_SECONDS = 1.5    # loaders/pulses shorter than this may drift without harm
GENERIC_IDS = {"title", "desc", "svgtitle", "svgdesc", "figure", "chart", "diagram", "g1", "path1"}

# How many numbers each entry of `values` (or from/to/by) must have.
TRANSFORM_ARITY = {"translate": (1, 2), "scale": (1, 2), "rotate": (1, 3), "skewX": (1, 1), "skewY": (1, 1)}
NUMERIC_ATTRS = {
    "opacity", "fill-opacity", "stroke-opacity", "stroke-width", "stroke-dashoffset",
    "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "width", "height",
    "font-size", "offset",
}
UNIT_OPACITY = {"opacity", "fill-opacity", "stroke-opacity"}
# attributeName values kept by the wechat-mp-html-source-helper extension when pasting into the WeChat editor.
HELPER_KEEPS = re.compile(
    r"^(opacity|fill|fill-opacity|stroke|stroke-opacity|stroke-width|transform|x|y|x1|y1|x2|y2|cx|cy|r|rx|ry"
    r"|width|height|viewBox|d|points|visibility)$", re.I)


def numbers(value):
    if value is None:
        return None
    parts = [part.strip() for part in value.split(";")]
    if not parts or any(not NUMBER.match(part) for part in parts):
        return None
    return [float(part) for part in parts]


def local_name(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def split_numbers(entry):
    """Split an SVG number list such as '0 12' or '1,0.5'. Return None if any token is not a number."""
    tokens = [t for t in re.split(r"[\s,]+", entry.strip()) if t]
    if not tokens or any(not NUMBER.match(t) for t in tokens):
        return None
    return [float(t) for t in tokens]


def parse_length(value):
    if value is None:
        return None
    match = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*(px)?\s*$", value)
    return float(match.group(1)) if match else None


def style_value(el, prop):
    style = el.get("style") or ""
    match = re.search(rf"(?:^|;)\s*{re.escape(prop)}\s*:\s*([^;]+)", style, re.I)
    return match.group(1).strip() if match else None


def font_size_of(el, inherited):
    raw = style_value(el, "font-size") or el.get("font-size")
    size = parse_length(raw)
    return size if size is not None else inherited


def check_entry_syntax(label, el, entries, field, errors, warnings):
    """Check that every animated value is well formed for the attribute being animated."""
    tag = local_name(el.tag)
    attr = el.get("attributeName") or ""
    if tag == "animateTransform":
        typ = el.get("type", "translate")
        lo, hi = TRANSFORM_ARITY.get(typ, (1, 6))
        for i, entry in enumerate(entries, 1):
            nums = split_numbers(entry)
            if nums is None:
                errors.append(f"{label}: {field} entry {i} '{entry.strip()}' is not a number list for type=\"{typ}\".")
            elif not lo <= len(nums) <= hi:
                errors.append(f"{label}: {field} entry {i} '{entry.strip()}' has {len(nums)} numbers; type=\"{typ}\" takes {lo}–{hi}.")
            elif typ == "scale" and any(n == 0 for n in nums):
                warnings.append(f"{label}: scale value 0 collapses the shape; use a small value such as 0.01 if that is intended.")
    elif attr in NUMERIC_ATTRS:
        for i, entry in enumerate(entries, 1):
            nums = split_numbers(entry)
            if nums is None or len(nums) != 1:
                errors.append(f"{label}: {field} entry {i} '{entry.strip()}' is not a single number for {attr}.")
            elif attr in UNIT_OPACITY and not 0 <= nums[0] <= 1:
                errors.append(f"{label}: {attr} value {nums[0]:g} is outside 0–1.")
    elif tag != "animateMotion":
        for i, entry in enumerate(entries, 1):
            if not entry.strip():
                errors.append(f"{label}: {field} entry {i} is empty.")
            elif "{" in entry or "}" in entry or "$" in entry:
                errors.append(f"{label}: {field} entry {i} '{entry.strip()}' looks like an unfilled template placeholder.")


def allowed(el, rule):
    """Opt-out for figures that break a rule on purpose, e.g. to demonstrate a bug."""
    return rule in (el.get("data-validate-allow") or "").split()


def static_opacity(el):
    raw = style_value(el, "opacity") or el.get("opacity")
    nums = split_numbers(raw) if raw else None
    return nums[0] if nums and len(nums) == 1 else 1.0


def first_value(el):
    values = el.get("values")
    if values is not None:
        return values.split(";")[0].strip()
    return el.get("from")


def validate(path):
    errors = []
    warnings = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError, UnicodeError) as exc:
        return [f"Cannot parse SVG: {exc}"], warnings, {}, set(), []
    root = tree.getroot()
    if root.tag != f"{SVG}svg" and local_name(root.tag) != "svg":
        errors.append("Root element is not SVG.")
        return errors, warnings, {}, set(), []

    view_box = root.get("viewBox")
    scale_to_reference = 1.0
    if not view_box:
        warnings.append("Missing viewBox; responsive scaling may be unreliable.")
    else:
        parts = split_numbers(view_box)
        if not parts or len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
            errors.append(f"Invalid viewBox '{view_box}'.")
        else:
            scale_to_reference = REFERENCE_WIDTH / parts[2]
    if root.find(f"{SVG}title") is None:
        warnings.append("Missing <title> for accessible fallback.")
    if root.find(f"{SVG}desc") is None:
        warnings.append("Missing <desc>; add the figure's takeaway.")

    parent_of = {child: parent for parent in root.iter() for child in parent}

    ids = set()
    animations = []
    external_refs = []
    event_attrs = []
    small_text = []
    min_font = None

    def walk(el, inherited_font):
        nonlocal min_font
        size = font_size_of(el, inherited_font)
        name = local_name(el.tag)
        if name in {"text", "tspan", "textPath"}:
            own_text = (el.text or "").strip()
            if own_text:
                effective = size * scale_to_reference
                min_font = effective if min_font is None else min(min_font, effective)
                if effective < MIN_FONT_SIZE:
                    small_text.append((effective, own_text[:16]))
        for child in el:
            walk(child, size)

    walk(root, DEFAULT_FONT_SIZE)

    for el in root.iter():
        element_id = el.get("id")
        if element_id:
            if element_id in ids:
                errors.append(f"Duplicate id: {element_id}")
            ids.add(element_id)
            if element_id.lower() in GENERIC_IDS:
                warnings.append(f"Generic id '{element_id}' will collide when several figures are inlined in one article; prefix it with the figure name.")
        name = local_name(el.tag)
        if name in {"script", "foreignObject"}:
            errors.append(f"Disallowed conservative element: <{name}>")
        if name == "set":
            warnings.append("<set> changes state without a transition; verify its fallback carefully.")
        if name == "animateMotion":
            warnings.append("<animateMotion> requires explicit target-client testing.")
        for attr, value in el.attrib.items():
            attr_name = local_name(attr)
            if attr_name.lower().startswith("on"):
                event_attrs.append((name, attr_name))
            if attr_name == "style" and re.search(r"animation\s*:|transition\s*:|@keyframes", value, re.I):
                warnings.append(f"CSS motion found on <{name}>; conservative output should use SMIL.")
            if attr in {"href", XLINK, "src"} and value and not value.startswith("#"):
                external_refs.append((name, value))
        if el.tag in ANIMATION_TAGS:
            animations.append(el)

    for name, attr in event_attrs:
        errors.append(f"Event handler found on <{name}>: {attr}")
    for name, value in external_refs:
        if re.match(r"https?://[^/]*(qpic\.cn|qlogo\.cn)/", value):
            warnings.append(f"External image on <{name}> is on the WeChat image host; confirm it was uploaded from this account's 素材库.")
        else:
            warnings.append(f"External resource on <{name}>: {value}")

    if small_text:
        sample = ", ".join(f"'{t}' ({s:g})" for s, t in sorted(small_text)[:4])
        warnings.append(
            f"{len(small_text)} text element(s) below {MIN_FONT_SIZE:g} units at 750 width "
            f"(about {MIN_FONT_SIZE * 0.46:.0f} px on a phone): {sample}.")

    duration_values = set()
    blank_first_frame = []
    allowances = []
    for index, el in enumerate(animations, 1):
        tag = local_name(el.tag)
        attr = el.get("attributeName") or ""
        label = f"Animation {index} (<{tag}> {attr}{' ' + el.get('type') if el.get('type') else ''})"
        dur = el.get("dur")
        if dur:
            match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)s\s*", dur)
            if not match or float(match.group(1)) <= 0:
                errors.append(f"{label}: invalid dur '{dur}'.")
            else:
                duration_values.add(float(match.group(1)))
        else:
            warnings.append(f"{label}: missing dur; verify target behavior.")

        begin = el.get("begin", "")
        if EVENT_BEGIN.search(begin):
            errors.append(f"{label}: event-driven begin '{begin}' is not conservative inline output.")

        values = el.get("values")
        entries = values.split(";") if values is not None else None
        value_count = len(entries) if entries is not None else None
        if entries is not None:
            check_entry_syntax(label, el, entries, "values", errors, warnings)
        for field in ("from", "to", "by"):
            if el.get(field) is not None:
                check_entry_syntax(label, el, [el.get(field)], field, errors, warnings)

        key_times_raw = el.get("keyTimes")
        key_times = numbers(key_times_raw)
        if key_times_raw is not None:
            if key_times is None:
                errors.append(f"{label}: keyTimes contains a non-numeric entry.")
            else:
                if key_times[0] != 0 or (el.get("calcMode") != "discrete" and key_times[-1] != 1):
                    errors.append(f"{label}: keyTimes must start at 0 and end at 1.")
                if any(not math.isfinite(x) or x < 0 or x > 1 for x in key_times):
                    errors.append(f"{label}: keyTimes entries must be between 0 and 1.")
                if any(b < a for a, b in zip(key_times, key_times[1:])):
                    errors.append(f"{label}: keyTimes must be monotonic.")
                if value_count is not None and len(key_times) != value_count:
                    errors.append(f"{label}: values has {value_count} entries but keyTimes has {len(key_times)}.")
        elif el.get("calcMode") == "spline":
            errors.append(f"{label}: spline mode requires keyTimes.")

        splines_raw = el.get("keySplines")
        if el.get("calcMode") == "spline":
            if not splines_raw:
                errors.append(f"{label}: spline mode requires keySplines.")
            elif key_times is not None and len(key_times) > 0:
                segments = [segment.strip() for segment in splines_raw.split(";")]
                if len(segments) != len(key_times) - 1:
                    errors.append(f"{label}: expected {len(key_times) - 1} keySplines segments, found {len(segments)}.")
                for segment in segments:
                    coords = segment.split()
                    if len(coords) != 4 or any(not NUMBER.match(x) for x in coords):
                        errors.append(f"{label}: invalid keySplines segment '{segment}'.")
                        continue
                    if any(not 0 <= float(x) <= 1 for x in coords):
                        errors.append(f"{label}: keySplines coordinates must be between 0 and 1.")
        if el.get("attributeName") is None and tag != "animateMotion":
            warnings.append(f"{label}: missing attributeName.")
        elif attr and not HELPER_KEEPS.match(attr):
            warnings.append(f"{label}: attributeName=\"{attr}\" is removed by the WeChat HTML source helper; "
                            "prefer opacity, transform, fill, stroke or geometry attributes.")

        # animateTransform replaces the target's own transform unless additive="sum".
        target = parent_of.get(el)
        if (tag == "animateTransform" and el.get("href") is None and el.get(XLINK) is None
                and target is not None and target.get("transform")
                and el.get("additive", "replace") != "sum"):
            (allowances if allowed(el, "transform-override") else errors).append(
                f"{label}: its target <{local_name(target.tag)}> already has transform=\"{target.get('transform')}\", "
                "which the animation replaces. Move the static transform to an outer <g> and animate an inner <g>.")

        # First frame: what a paused, reduced-motion, screenshot or thumbnail view shows.
        # Only a mismatch matters: the element is visible at rest (static fallback) but hidden at t=0.
        first = first_value(el)
        hidden_at_start = False
        if attr in UNIT_OPACITY and first is not None:
            nums = split_numbers(first)
            hidden_at_start = bool(nums) and len(nums) == 1 and nums[0] == 0
        elif attr == "visibility" and first is not None:
            hidden_at_start = first.strip() == "hidden"
        elif tag == "animateTransform" and el.get("type") == "scale" and first is not None:
            nums = split_numbers(first)
            hidden_at_start = bool(nums) and all(abs(n) < 0.05 for n in nums)
        if hidden_at_start and target is not None and static_opacity(target) > 0:
            if allowed(el, "blank-first-frame"):
                allowances.append(f"{label}: starts invisible at t=0 (allowed by data-validate-allow).")
            else:
                blank_first_frame.append(label)

    if blank_first_frame:
        warnings.append(
            f"{len(blank_first_frame)} animation(s) start invisible at t=0 ({'; '.join(blank_first_frame[:3])}"
            f"{'; …' if len(blank_first_frame) > 3 else ''}) although visible in the static fallback. Paused, "
            "reduced-motion and screenshot views show the first frame; prefer values whose first entry is the "
            "complete state, then reset and replay.")

    narrative = sorted(d for d in duration_values if d >= AMBIENT_LOOP_SECONDS)
    if len(narrative) > 1:
        longest = narrative[-1]
        drifting = [d for d in narrative[:-1] if abs(longest / d - round(longest / d)) > 1e-3]
        if drifting:
            warnings.append(
                f"Loop durations {', '.join(f'{d:g}s' for d in drifting)} do not divide {longest:g}s; "
                "their phase drifts each cycle, so beats that should line up will not.")

    if not animations:
        warnings.append("No SMIL animation found; confirm that a static SVG was intended.")
    stats = {
        "animations": len(animations),
        "durations_seconds": sorted(duration_values),
        "elements": sum(1 for _ in root.iter()),
        "external_references": len(external_refs),
        "min_font_size_at_750": round(min_font, 1) if min_font is not None else None,
    }
    stats["allowed"] = len(allowances)
    return errors, warnings, stats, ids, allowances


def main(argv):
    strict = "--strict" in argv
    paths = [Path(a) for a in argv if a != "--strict"]
    if not paths:
        print(__doc__.strip(), file=sys.stderr)
        return 1
    failed = False
    seen_ids = {}
    for path in paths:
        errors, warnings, stats, ids, allowances = validate(path)
        for element_id in sorted(ids):
            if element_id in seen_ids and seen_ids[element_id] != path:
                errors.append(f"id '{element_id}' is also used in {seen_ids[element_id]}; ids must be unique across one article.")
            seen_ids.setdefault(element_id, path)
        if len(paths) > 1:
            print(f"== {path}")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for note in allowances:
            print(f"ALLOWED: {note}")
        if stats:
            print("STATS: " + ", ".join(f"{key}={value}" for key, value in stats.items()))
        bad = bool(errors) or (strict and bool(warnings))
        failed = failed or bad
        print(f"RESULT: {'FAIL' if bad else 'PASS'} ({len(errors)} errors, {len(warnings)} warnings)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
