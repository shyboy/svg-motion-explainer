---
name: svg-motion-explainer
description: Generate explanatory inline SVG and SMIL motion graphics from articles, reports, tutorials, and product explanations, especially for WeChat Official Account articles (微信公众号 SVG 动效). Use when asked to identify content that would benefit from animation, design a motion narrative, create or validate an explanatory SVG, visualize processes/comparisons/causality/state changes, or produce 公众号动效/SVG SMIL 动画. Do not use for generic illustrations, video/GIF editing, or merely replacing text in a fixed animation template.
---

# SVG Motion Explainer

Create animation that improves the reader's understanding of a specific passage. Treat motion as an explanatory variable, not decoration. Generate the narrative from the article each time; do not default to a previously used layout or template.

## Load the bundled knowledge

1. Read [references/narrative-patterns.md](references/narrative-patterns.md) before choosing a visual narrative or making a storyboard.
2. Read [references/smil-wechat.md](references/smil-wechat.md) before writing SVG for WeChat or validating SMIL timing.
3. Run `python scripts/validate_svg.py <file.svg>` for every generated SVG.
4. Use [assets/parallel-tasks-example.svg](assets/parallel-tasks-example.svg) only as one worked example of timing and structure, never as the default output template.

## Workflow

### 1. Establish the explanation goal

Read the source passage and identify:

- The claim or instruction the author is making.
- The entities, actions, order, direction, states, and constraints that are explicit in the source.
- The reader's likely question or misconception.
- What the reader should understand after viewing that is harder to grasp from text alone.

Do not invent product behavior, causal claims, numbers, or steps to make an animation more interesting. Label a visual analogy as an analogy when it is not a literal depiction.

### 2. Decide whether motion is justified

Use animation only when at least one of these changes carries meaning:

- Order or sequence.
- Direction of movement or information flow.
- State or status.
- Timing, concurrency, delay, or progress.
- Cause and effect.
- Attention across a complex diagram.

Prefer a static SVG when only hierarchy, styling, or spatial layout matters. If removing the motion would lose no explanatory information, redesign or omit the animation. Do not animate every illustration or every paragraph.

### 3. Write an explanation contract

Before coding, write a compact internal contract:

```text
Source passage:
Reader question:
Single takeaway:
Motion-worthy relationship:
Literal depiction or analogy:
Static fallback state:
```

Keep one primary takeaway per SVG. If there are several unrelated takeaways, split them into separate figures or simplify the passage first.

### 4. Choose the narrative from the content

Select a pattern because it matches the source relationship, not because it looks familiar:

- Steps → staged reveal or progressive construction.
- Routing → object movement between persistent nodes.
- Parallel work → simultaneous starts and independent completion times.
- Comparison → corresponding objects undergoing equivalent visual operations.
- State change → before/after transition with stable object identity.
- Causality → trigger, action, observable result.
- Hierarchy → structural reveal without gratuitous movement.
- Spatial navigation → cursor, viewport, or focus movement.

Consult `references/narrative-patterns.md` for variations and failure modes. Combine patterns only when the article explicitly combines the relationships.

### 5. Storyboard before writing SVG

Define 3–7 beats and a short loop, normally 4–8 seconds for a small WeChat figure:

1. Establish the initial state.
2. Introduce the meaningful trigger.
3. Show the relationship changing.
4. Hold long enough to read the result.
5. Reset or return to the initial state.

Specify what moves, what remains stable, when text appears, and which state remains visible if SMIL is unsupported. Prefer short loops because WeChat inline SMIL commonly starts with page load rather than when the reader reaches the figure.

Do not make essential text visible for only a brief instant. Do not rely on click, hover, scroll, or user-controlled playback unless the target environment is explicitly known to support it.

### 6. Implement a self-contained SVG

For conservative WeChat output:

- Use inline SVG with a `viewBox`; start with width `750` and choose height from the content rather than forcing a template ratio.
- Use `<title>` and `<desc>` to state the takeaway.
- Prefer `<animate>` for opacity and `<animateTransform>` for translation and scale.
- Keep objects visually stable across states so readers can track identity.
- Wrap animated transforms in nested groups when a static transform must also be preserved.
- Set initial attributes to a meaningful static fallback.
- Use manual line breaks for text and check the narrowest intended viewport.
- Avoid JavaScript, external assets, event-driven playback, and fragile effects listed in `references/smil-wechat.md`.

Write new geometry and timing appropriate to the article. Do not merely replace labels in `parallel-tasks-example.svg`.

### 7. Verify logic, syntax, and rendering

Run the validator and fix every error:

```bash
python scripts/validate_svg.py path/to/output.svg
```

Then verify:

- The animation expresses the explanation contract.
- Initial, middle, completion, and reset states are correct.
- Parallel items actually start and finish at the intended times.
- No text overlaps, clips, or becomes unreadable during motion.
- The static fallback is understandable.
- The loop does not flash or jump unintentionally.

When a browser is available, inspect actual rendering and use `pauseAnimations()` plus `setCurrentTime(t)` to check keyframes. When no renderer is available, explicitly report that visual rendering was not verified; never claim a screenshot or browser test that did not occur.

WeChat client behavior can vary. Treat browser validation as necessary but not sufficient; recommend a draft preview in the intended WeChat client for final publishing.

### 8. Deliver the result and its rationale

Provide:

- The `.svg` file.
- One or two sentences explaining why this motion pattern fits the passage.
- The loop duration and important completion timings when useful.
- Instructions to insert the SVG inline rather than upload it as a static image.
- Any remaining compatibility or visual-verification limitations.

Do not create a web application, video, GIF, or editor unless the user separately requests one.

## Quality bar

A successful result lets the reader answer the original question more quickly and accurately. It uses the minimum motion needed, preserves textual meaning, and remains comprehensible as a static figure.
