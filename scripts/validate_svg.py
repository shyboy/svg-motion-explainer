#!/usr/bin/env python3
"""Validate conservative, self-contained SVG SMIL output.

Usage: python scripts/validate_svg.py path/to/file.svg
Exit code 0 = no errors; 1 = validation errors or unreadable file.
Warnings do not change the exit code.
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


def numbers(value):
    if value is None:
        return None
    parts = [part.strip() for part in value.split(";")]
    if not parts or any(not NUMBER.match(part) for part in parts):
        return None
    return [float(part) for part in parts]


def local_name(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def validate(path):
    errors = []
    warnings = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError, UnicodeError) as exc:
        return [f"Cannot parse SVG: {exc}"], warnings, {}
    root = tree.getroot()
    if root.tag != f"{SVG}svg" and local_name(root.tag) != "svg":
        errors.append("Root element is not SVG.")
        return errors, warnings, {}
    if not root.get("viewBox"):
        warnings.append("Missing viewBox; responsive scaling may be unreliable.")
    if root.find(f"{SVG}title") is None:
        warnings.append("Missing <title> for accessible fallback.")
    if root.find(f"{SVG}desc") is None:
        warnings.append("Missing <desc>; add the figure's takeaway.")

    ids = set()
    animations = []
    external_refs = []
    event_attrs = []
    for el in root.iter():
        element_id = el.get("id")
        if element_id:
            if element_id in ids:
                errors.append(f"Duplicate id: {element_id}")
            ids.add(element_id)
        name = local_name(el.tag)
        if name in {"script", "foreignObject"}:
            errors.append(f"Disallowed conservative element: <{name}>")
        if name in {"set"}:
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
        warnings.append(f"External resource on <{name}>: {value}")

    duration_values = set()
    for index, el in enumerate(animations, 1):
        label = f"Animation {index} (<{local_name(el.tag)}>)"
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
        value_count = len(values.split(";")) if values is not None else None
        key_times_raw = el.get("keyTimes")
        key_times = numbers(key_times_raw)
        if key_times_raw is not None:
            if key_times is None:
                errors.append(f"{label}: keyTimes contains a non-numeric entry.")
            else:
                if key_times[0] != 0 or key_times[-1] != 1:
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
        calc_mode = el.get("calcMode")
        if calc_mode == "spline":
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
        if el.get("attributeName") is None and local_name(el.tag) != "animateMotion":
            warnings.append(f"{label}: missing attributeName.")

    if not animations:
        warnings.append("No SMIL animation found; confirm that a static SVG was intended.")
    stats = {
        "animations": len(animations),
        "durations_seconds": sorted(duration_values),
        "elements": sum(1 for _ in root.iter()),
        "external_references": len(external_refs),
    }
    return errors, warnings, stats


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_svg.py path/to/file.svg", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    errors, warnings, stats = validate(path)
    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    if stats:
        print("STATS: " + ", ".join(f"{key}={value}" for key, value in stats.items()))
    print(f"RESULT: {'FAIL' if errors else 'PASS'} ({len(errors)} errors, {len(warnings)} warnings)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
