# Environment Runtime Budget 001

Status: bounded Runtime / Optimization evidence lane stacked on Environment PR #4.

## Question

What does the first real source-owned Nature + Weather environment slice cost in the same pinned Godot proof host relative to the exact seed-29 proxy composition, and does the current 36-streak Weather representation stay batched rather than expanding into per-streak draws?

## Compared states

1. `proxy_baseline` — exact seed-29 proxy composition before the source replacement; no source sapling and no Weather overlay.
2. `source_sapling_only` — measurement ablation with the exact source-owned sapling but no Weather. This is not a proposed product state.
3. `source_sapling_weather` — exact current Environment source slice.

All states preserve the same map/building/remaining nature/object bodies, proof path overlay, lighting, fixed cameras, renderer and source integration identity. Each state runs in a fresh Godot process to avoid treating prior scene residency as the current state's memory.

## Runtime contract

The lane records Godot `RenderingServer` objects, submitted/render-reported primitives, draw calls, texture memory and buffer memory from both existing Environment cameras. Absolute target budgets are intentionally not invented.

The first exact measurement exposed an important counter-semantics correction. The source owns **36 Weather streaks** and the observation host submits them as **one `ImmediateMesh` surface**. Relative to the exact `source_sapling_only` ablation, pinned Godot 4.7.2 GL Compatibility measured **+1 draw call, +1 object, +144 `RenderingServer` primitives and +864 bytes of buffer memory** in both fixed cameras. The initial test incorrectly assumed the renderer counter would report 36 primitives because the source authored 36 lines; that assumption failed and is retained as historical evidence rather than rewritten away.

The corrected bounded performance gate therefore preserves the actually observed host behavior: the 36 source-owned streaks must remain one additional draw call and the pinned proof host must continue to report the same +144 renderer-primitive delta. The value `144` is **not** relabelled as 144 authored streaks or 144 authored line primitives.

The same comparison also records, without yet accepting a target budget, that replacing the reserved tree proxy with the exact source-owned sapling changes neither draw-call nor visible-object count in either camera while increasing the proof-host buffer counter by **33,456 bytes** and the renderer primitive counter by **1,674**. Those primitive-counter values are renderer observations, not replacements for the source truth of **390 vertices / 570 authored triangles**.

## Visual boundary

This Runtime lane changes no current Environment geometry, materials, placement, cameras or visual-direction semantics. The proxy baseline is before-evidence, not a proposed rollback, and the no-Weather scene is measurement-only. Directly retained captures show the expected visual tradeoff: the proxy baseline has a large green block where the real sapling later carries a much thinner branching silhouette, while the full source slice additionally carries the visible blue Weather streak field. Runtime savings cannot authorize silently reverting either source-owned visual contribution.

Art Direction remains independent: any later LOD, batching, mesh-normal/indexing, culling or streaming change must retain its own before/after visual review rather than inheriting acceptance from these counters.

## Non-claims

This does not establish target-device FPS/frame-time, production memory/draw-call budgets, a final LOD or streaming strategy, final environment composition, physical Weather, gameplay/traversal/collision, production readiness, CANON or Runtime mastery. Renderer memory and primitive counters remain observational because backend expansion, caching and shared resources are not decomposed by this proof.
