# Conservative SVG SMIL for WeChat articles

Use this reference when implementing or validating inline SVG animation for 微信公众号. These are conservative design rules, not a guarantee of behavior in every client version.

## Contents

- Minimal syntax
- Timing rules
- Transform rules
- Static fallback and accessibility
- Layout and text
- Several figures in one article
- Compatibility and performance
- Inserting into WeChat
- Verification

## Minimal syntax

Use XML-compatible SVG and inline attributes:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 750 480"
     width="750" height="480" style="display:block;max-width:100%;height:auto"
     role="img" aria-labelledby="f1-title f1-desc">
  <title id="f1-title">Short figure title</title>
  <desc id="f1-desc">The single takeaway conveyed by the animation.</desc>
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
- A repeated keyTime (`keyTimes="0;0.7;0.7;1"`) makes an instant jump at that moment, which is useful for wrapping a playhead back to the start.
- Narrative loops that must stay in step should divide the main loop exactly (6s with 3s, 2s or 1.5s). A 5s loop beside a 6s loop drifts by a second every cycle. Short ambient loops such as a 0.9s loader may drift without harm.

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

Make the first entry of every `values` list match that static state. Paused previews, reduced-motion settings, screenshots, share thumbnails and clients without SMIL all show t=0, so a loop that starts from an empty canvas looks broken there. The usual shape is `values="1;0;0;1;1"`: complete, quick reset, wait, entrance, hold. An element that is absent in the complete state (a loader that has finished) can start at 0 as long as its static attribute is also 0.

When a figure must break this on purpose, mark the animation with `data-validate-allow="blank-first-frame"` and explain why in the delivery note. The same attribute with `transform-override` covers a figure that deliberately demonstrates the transform-replacement bug.

Include:

- A concise `<title>`.
- A `<desc>` that communicates the takeaway, not merely “animation”.
- Readable contrast and text sizes.
- No essential information encoded by motion alone; the final state, labels, or caption should also convey it.

Avoid flashing and rapid full-scene alternation. If the surrounding publishing workflow supports reduced-motion handling, use it; do not assume inline SMIL automatically honors the reader's system preference.

## Layout and text

- Use a `viewBox` and responsive surrounding container such as `max-width:100%;height:auto` where the editor permits it.
- A 750-wide figure is displayed at roughly 340–360 CSS px on a phone, about 0.46×. Minimum sizes in 750-wide units:

  | Role | Size | ≈ on phone |
  |---|---|---|
  | Figure title | 36–40 | 17–18 px |
  | Caption / takeaway line | 26–28 | 12–13 px |
  | Body labels, card text | 22–24 | 10–11 px |
  | Secondary notes, axis ticks | 20 | 9 px |

  The validator warns below 20. If a label does not fit at these sizes, shorten it or give it more room; do not shrink it.
- Choose height from actual content. Do not force every figure into the same aspect ratio.
- SVG `<text>` does not wrap automatically. Use separate `<text>` or `<tspan>` lines with explicit positions.
- Test long Chinese and Latin strings, mixed-case text, punctuation, and enlarged text.
- Keep essential labels outside moving masks and clipping regions.
- Preserve visual stability: avoid moving the whole canvas or changing layout between frames.

## Several figures in one article

All figures of an article end up in one HTML document, so:

- Prefix every `id` with the figure's name (`f2-title`, `f2-desc`, `f2-clip`). Generic ids such as `title`, `desc` or `svgTitle` collide.
- Validate the figures together: `python scripts/validate_svg.py f1.svg f2.svg f3.svg` reports ids shared between files.
- Reuse one frame for the series: canvas width, background, kicker/title/divider/caption positions, palette, type sizes and the easing set. Keep the content inside the frame specific to each passage.

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

## Inserting into WeChat

The SVG must reach the article as markup. Uploading an `.svg` file as an image drops the animation.

The [WeChat MP HTML Source Helper](https://github.com/shyboy/wechat-mp-html-source-helper) Chrome extension adds an `HTML 源码` button to the WeChat editor:

1. Load the extension unpacked from `chrome://extensions/` (developer mode).
2. In the article editor, click where the figure should go (press Enter first to leave an empty paragraph), then click `HTML 源码`.
3. Paste the SVG markup and click `插入到光标位置`. Use `替换全文` only to replace the whole article with a prepared HTML body.
4. Read the cleanup and compatibility notes shown in the dialog, save the draft, reopen it, and preview on a phone in light and dark mode.

Before pasting, the extension removes scripts, iframes, `<style>`/`<link>`, `foreignObject`, form controls, `on*` handlers, unsafe URLs, and SVG animations whose `attributeName` is outside: `opacity`, `fill`, `fill-opacity`, `stroke`, `stroke-opacity`, `stroke-width`, `transform`, `x`, `y`, `x1`, `y1`, `x2`, `y2`, `cx`, `cy`, `r`, `rx`, `ry`, `width`, `height`, `viewBox`, `d`, `points`, `visibility`. The validator warns about any other `attributeName`. It also warns about `display:flex`, `grid`, `position` and CSS variables in inline styles; prefer tables or plain blocks for article layout around the figures.

WeChat cleans the content again when the draft is saved. Neither the extension nor this skill can guarantee what WeChat keeps, so the phone preview of the saved draft is the final check.

Bitmaps (for example a paper texture) must be uploaded to the account's 素材库 first and referenced by their WeChat image URL (`mmbiz.qpic.cn`); the extension does not upload images.

## Verification

Run the bundled deterministic checks:

```bash
python scripts/validate_svg.py path/to/output.svg
```

The validator checks XML structure, dependencies, timing arrays, splines, the syntax of animated values, transforms replaced by `animateTransform`, a hidden first frame, small text, ids (also across files), loop drift, event-driven behavior and attributes stripped by WeChat import tools. It cannot prove visual quality or WeChat-client compatibility.

Render the key moments into a contact sheet:

```bash
python scripts/render_frames.py path/to/output.svg --out frames
python scripts/render_frames.py path/to/output.svg --times 0,1.8,5.4   # specific moments
python scripts/render_frames.py path/to/output.svg --width 360         # phone width
```

It needs Python Playwright and a Chrome/Chromium (set `CHROME_PATH` if it is not found). To inspect by hand in a browser that supports SVG SMIL, use:

```js
const svg = document.querySelector('svg');
svg.pauseAnimations();
svg.setCurrentTime(3.3); // seconds
```

Inspect at least the initial state, each meaningful transition, the completed state, and the reset. Confirm object visibility and text layout at each keyframe. Resume animations and remove any temporary preview overlays after testing.
