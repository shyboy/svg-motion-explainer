# Conservative SVG SMIL for WeChat articles

Use this reference when implementing or validating inline SVG animation for 微信公众号. These are conservative design rules, not a guarantee of behavior in every client version.

## Contents

- Minimal syntax
- Timing rules
- Transform rules
- Static fallback and accessibility
- Layout and text
- Compatibility and performance
- Verification

## Minimal syntax

Use XML-compatible SVG and inline attributes:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 750 480"
     width="750" height="480" role="img" aria-labelledby="title desc">
  <title id="title">Short figure title</title>
  <desc id="desc">The single takeaway conveyed by the animation.</desc>
  <g>
    <animate attributeName="opacity"
             values="0;0;1;1;0" keyTimes="0;0.1;0.2;0.8;1"
             calcMode="spline"
             keySplines="0 0 1 1;0.16 1 0.3 1;0 0 1 1;0.42 0 0.58 1"
             dur="6s" begin="0s" repeatCount="indefinite"/>
    <!-- Visible geometry and text -->
  </g>
</svg>
```

When inserting into an article, insert the SVG markup inline. Do not upload it as an ordinary raster image and expect SMIL to survive.

## Timing rules

- `dur` sets the loop duration. `keyTimes` are fractions of that duration, not seconds.
- Convert seconds with `fraction = seconds / durationSeconds`.
- `values` and `keyTimes` must contain the same number of entries.
- `keyTimes` must start at `0`, end at `1`, and increase monotonically.
- For `calcMode="spline"`, `keySplines` needs one fewer segment than `values`.
- Each spline segment contains four numbers between 0 and 1.
- `begin="0s"` and `repeatCount="indefinite"` create autonomous looping; they do not wait for viewport entry.
- Avoid event begins such as `click`, `mouseover`, or `scroll` in conservative WeChat output.
- Use `calcMode="discrete"` for stepped changes such as an 8-dot loader. Do not use discrete mode for text that must remain continuously readable.

Common easings:

```text
0.16 1 0.3 1    Fast start, soft arrival; useful for entrances
0.42 0 0.58 1   Smooth acceleration and deceleration
0 0 1 1         Linear segment or a timing hold
```

For a small completion bounce, scale around the object's local origin:

```xml
<animateTransform attributeName="transform" type="scale"
  values="1;1;1.4;0.94;1;1"
  keyTimes="0;0.5;0.5233;0.5567;0.5917;1"
  dur="6s" repeatCount="indefinite"/>
```

## Transform rules

SMIL transform animation can replace the target's static transform. Preserve positioning with nested groups:

```xml
<g transform="translate(120 240)">       <!-- static position -->
  <g>
    <animateTransform attributeName="transform" type="translate"
      values="0 8;0 0;0 0" keyTimes="0;0.2;1" dur="6s"
      repeatCount="indefinite"/>
    <!-- local geometry -->
  </g>
</g>
```

Use an additional nested group for scale so the object scales around its intended local center. Prefer simple translation and scale over path morphing, rotation-heavy scenes, or custom motion paths when client consistency matters.

## Static fallback and accessibility

Set ordinary SVG attributes to a meaningful state even when an `<animate>` later changes them. If SMIL is ignored, the reader should see a complete or representative figure rather than an empty canvas.

Include:

- A concise `<title>`.
- A `<desc>` that communicates the takeaway, not merely “animation”.
- Readable contrast and text sizes.
- No essential information encoded by motion alone; the final state, labels, or caption should also convey it.

Avoid flashing and rapid full-scene alternation. If the surrounding publishing workflow supports reduced-motion handling, use it; do not assume inline SMIL automatically honors the reader's system preference.

## Layout and text

- Use a `viewBox` and responsive surrounding container such as `max-width:100%;height:auto` where the editor permits it.
- Choose height from actual content. Do not force every figure into the same aspect ratio.
- SVG `<text>` does not wrap automatically. Use separate `<text>` or `<tspan>` lines with explicit positions.
- Test long Chinese and Latin strings, mixed-case text, punctuation, and enlarged text.
- Keep essential labels outside moving masks and clipping regions.
- Preserve visual stability: avoid moving the whole canvas or changing layout between frames.

## Compatibility and performance

For the broadest conservative output, avoid:

- JavaScript and event handlers.
- External images, fonts, stylesheets, or network dependencies.
- `foreignObject` and HTML-dependent rendering.
- CSS-only animation as the sole motion mechanism.
- Complex filters, large blurs, heavy masks, and many simultaneous moving objects.
- Path morphing and `animateMotion` unless the target client has been explicitly tested.
- Tiny text and essential details that only appear during a short frame.

Keep loops short because all inline figures may begin at page load. Consider that offscreen animations may continue running. More animation nodes means more opportunities for timing errors and potentially more rendering cost.

Do not claim universal WeChat support based only on desktop browser success. Final behavior should be checked in a draft on the intended mobile client.

## Verification

Run the bundled deterministic checks:

```bash
python scripts/validate_svg.py path/to/output.svg
```

The validator checks XML structure, dependencies, timing arrays, splines, duplicate IDs, and common event-driven behavior. It cannot prove visual quality or WeChat-client compatibility.

In a browser that supports SVG SMIL, use:

```js
const svg = document.querySelector('svg');
svg.pauseAnimations();
svg.setCurrentTime(3.3); // seconds
```

Inspect at least the initial state, each meaningful transition, the completed state, and the reset. Confirm object visibility and text layout at each keyframe. Resume animations and remove any temporary preview overlays after testing.
