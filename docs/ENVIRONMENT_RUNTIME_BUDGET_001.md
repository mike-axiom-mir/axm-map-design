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

The lane records Godot `RenderingServer` objects, submitted primitives, draw calls, texture memory and buffer memory from both existing Environment cameras. Absolute target budgets are intentionally not invented.

The only bounded performance gate introduced here is grounded in the current implementation: the 36 retained source-owned Weather streaks are authored into one `ImmediateMesh` surface. Relative to the exact `source_sapling_only` ablation, the full scene must therefore add exactly one draw call and 36 submitted line primitives in both fixed cameras. If that changes, the evidence holds rather than silently accepting a per-streak draw expansion.

## Visual boundary

This Runtime lane changes no current Environment geometry, materials, placement, cameras or visual-direction semantics. The proxy baseline is before-evidence, not a proposed rollback, and the no-Weather scene is measurement-only. Art Direction remains independent: runtime savings cannot authorize removal of the real sapling, atmosphere, or any later accepted visual treatment.

## Non-claims

This does not establish target-device FPS/frame-time, production memory/draw-call budgets, a final LOD or streaming strategy, final environment composition, physical Weather, gameplay/traversal/collision, production readiness, CANON or Runtime mastery. Renderer memory counters remain observational because caching/shared resources are not decomposed by this proof.
