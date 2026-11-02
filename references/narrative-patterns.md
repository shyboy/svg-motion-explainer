# Narrative patterns for explanatory motion

Use this reference to translate an article's meaning into a visual narrative. Choose a pattern from the relationship in the source, not from a preferred visual style.

## Contents

- Selection table
- Pattern guidance
- Storyboard construction
- Worked analysis
- Figures as a series
- Final narrative checks

## Selection table

| Source signal | Reader's question | Visual encoding | Motion that adds meaning |
|---|---|---|---|
| Ordered steps, instructions | What happens first and next? | Persistent stages or stacked items | Staged reveal, progressive construction |
| Inputs, router, outputs, messages | Where does information go? | Nodes connected by visible paths | Move a message/object along the relationship |
| Concurrent jobs, independent delays | What runs together and what finishes when? | Parallel tracks or task cards | Simultaneous entry, independent loaders and completion |
| Before/after, enabled/disabled | What changed? | Same object in two states | Crossfade or transition while preserving identity |
| Trigger and consequence | Why does this result happen? | Trigger → action → result | Temporally linked cause and response |
| Two approaches or systems | How are they different? | Corresponding regions with matched visual grammar | Equivalent operations with different paths, timing, or outcomes |
| Parent/child, layers, ownership | What belongs to what? | Nested or grouped persistent structure | Reveal levels or move focus; avoid unnecessary motion |
| Navigation, menus, shortcuts | Where does the user act? | Simplified interface and cursor/focus | Move focus, press, open the resulting surface |
| Accumulation, progress, queue | How far has it advanced? | Bar, queue, counter, or stack | Grow, drain, advance, or complete |
| Feedback, retry, loop | What happens next after the result? | Circular or returning relationship | Return a signal to its origin and show the response |
| Dense diagram with one important region | Where should I look? | Stable diagram with a focus layer | Pulse, spotlight, or temporary annotation |

## Pattern guidance

### Sequence

Keep every stage visible as a faint scaffold when order matters more than surprise. Reveal the active stage and retain completed stages so the reader does not need to memorize them. Avoid typewriter effects for long text; reveal meaningful blocks instead.

### Flow and routing

Keep source, router, and destination nodes stationary. Move a small persistent token to show direction. Use the same token shape for the same kind of information. Do not animate every connecting line when one moving token explains the path more clearly.

### Parallel work

Start tracks together and complete them independently. A loop that completes tasks in visual order from top to bottom may accidentally imply dependence; use deliberate completion times that match the article. If the source only says tasks are parallel but gives no durations, use illustrative timing without presenting it as measured data.

### Comparison

Use the same scale, object sizes, and operation timing on both sides unless a difference is itself the point. Motion should expose the distinction, such as local versus remote execution, rather than make one side visually louder.

### State change

Preserve object identity through the transition. Change only the meaningful property: status, color, position, membership, or completion. A static before/after pair is often better when timing is irrelevant.

### Causality

Order the beats as trigger, mechanism, result. Keep the trigger visible while the result appears if the reader must connect them. Do not use a decorative pulse that suggests causality absent from the article.

### Hierarchy and structure

Prefer static layout for pure taxonomy. Add motion only to reveal layers, ownership changes, or a walkthrough order. Scaling an entire diagram rarely explains hierarchy.

### Spatial navigation

Use the minimum recognizable interface. A simulated cursor is a visual narrator, not a real control. Make the target and the resulting state change explicit; never imply that readers can interact with the SVG itself.

### Progress and accumulation

Use scale or position to encode actual progress direction. Distinguish determinate progress from an indeterminate loader. Do not fabricate precise percentages or completion times from qualitative text.

### Attention and annotation

Keep the diagram stable and animate only a focus ring, mask, pointer, or annotation. Avoid repeated full-screen flashing. A single gentle pulse is usually enough.

## Storyboard construction

Write beats in source terms before converting them to SVG attributes:

```text
Takeaway: One sentence the figure must communicate.
Persistent objects: Things the reader must track across time.
Initial state: What is already true? (This is also the t=0 frame and the static fallback, so it must read on its own.)
Trigger: What starts the meaningful change?
Change: Which relationship, state, or direction changes?
Result: What should the reader notice?
Hold: Which text and final state need reading time?
Reset: How does the loop return without confusing the reader?
Fallback: Which complete or representative state remains without SMIL?
```

Use 3–7 beats and one primary idea. Prefer stable objects with 1–3 moving properties over animating the entire scene. Motion should normally last only as long as needed, followed by a readable hold.

## Worked analysis

Source idea: “A router receives requests from several channels, assigns work to workers, and returns their results.”

```text
Reader question: Why is the router useful if workers perform the tasks?
Takeaway: The reader talks to one router while execution is distributed.
Pattern: Flow and routing.
Persistent objects: Input channels, router, workers, message token.
Initial state: Channels and workers are visible; no message is moving.
Beats:
1. A request moves from channel A to the router.
2. The router sends it to worker 1.
3. Another request travels from channel B to worker 2.
4. A result returns from a worker to the router.
5. The router sends the result to the originating channel.
Fallback: All nodes and the final returned result remain understandable.
```

Why this works: movement explains direction and responsibility. A looping cursor or fading cards would not explain the architecture as precisely.

## Figures as a series

When one article gets several figures, the reader should recognise them as one set and spend attention on what differs.

- Decide the shared frame once: canvas width, background, kicker, title, divider and caption positions, type sizes, palette, and the easing set (for example entrance `0.16 1 0.3 1`, in-out `0.42 0 0.58 1`, hold `0 0 1 1`).
- Use the caption line to state each figure's takeaway in words, so a reader who scrolls past the motion still gets it.
- Choose each figure's pattern independently. A series of six parallel-task figures is a sign that the template, not the article, chose the narrative.
- Give each figure its own loop length from its own storyboard; sharing the frame does not mean sharing the timing.
- Prefix ids per figure (`f1-`, `f2-`, …).

## Final narrative checks

- Can the takeaway be stated without mentioning the animation technique?
- Does every moving object have a source-grounded role?
- Is the direction of motion semantically correct?
- Does the animation accidentally imply sequence, dependency, scale, or timing absent from the article?
- Can the reader track object identity throughout?
- Is the result visible long enough to read?
- If motion is removed, is a meaningful explanation lost? If not, use a static SVG or simplify the design.
- Does the t=0 frame, on its own, still state the takeaway?
