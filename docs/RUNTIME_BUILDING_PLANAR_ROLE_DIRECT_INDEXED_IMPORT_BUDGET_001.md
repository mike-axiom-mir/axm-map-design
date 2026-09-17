# Runtime Building planar-role direct indexed import budget 001

This bounded Runtime lane stacks on the exact Environment indexed-planar review head `038925282240441c475651bdc3737d1749c31d06` and runs on branch `studio/runtime-building-planar-role-direct-indexed-import-budget-001`.

It does not change Building semantic source authority, the five material roles/scalars, the 336-triangle planar-role representation, current-world composition, or `axm-create-me` product code.

## Question

The current review receiver already proves the renderer-memory benefit of post-normal per-surface indexing: it builds 1,008 unindexed triangle-corner vertices, generates normals, then `create_from + SurfaceTool.index()` compacts the exact five surfaces to 312 stored vertices / 1,008 indices.

This pass asks a different import/preparation question: is it cheaper to deduplicate the exact per-material position domain to 312 vertices first, attach the same 1,008 triangle indices, and then run the same pinned Godot `generate_normals()` step?

## Truth-boundary repairs

The first v0.1 experiment attempted to emit direct position + hand-derived cardinal-normal + index arrays. It correctly failed the exact final-storage identity gate: that normal domain was not equivalent to the current Godot-generated domain. The failed run is preserved.

The repaired v0.2 candidate performs only the already-proven position-domain deduplication before the same Godot normal-generation step. It finishes at the exact same 5 surfaces / 312 stored vertices / 1,008 indices / 336 triangles.

A second measurement repair was also necessary: the current-world scene constructs the Building once and copies the static-source receipt into all 17 state rows. Those repeated receipt values are one construction observation, not 17 timing samples. Final preparation evidence therefore comes from a separate benchmark with 5 warmup pairs and 41 independently timed, alternating control/candidate pairs.

## Measured result

On the pinned Godot 4.7.2 proof host, the repeated benchmark holds the candidate rather than adopting it:

- post-normal-index control median: 619 us; p90: 628 us;
- index-before-normal candidate median: 728 us; p90: 737 us;
- median difference: +109 us / +17.609047% for the candidate;
- paired-delta median: +108 us;
- candidate faster pairs: 0 / 41.

The separate current-world A/B still ends in the same final renderer representation. Across 68 observations the candidate-minus-control deltas are exactly 0 for draw calls, objects, primitives, observed buffer memory and observed texture memory. All 68 retained frame pairs have a measurable but bounded raster delta: at most 55 changed pixels per frame, maximum 1 LSB per channel, and zero pixels above 1 LSB. Art Direction / Visual QA retain that visual decision.

Scoped result: `HOLD_BUILDING_INDEX_BEFORE_NORMAL_RECEIVER_PREPARATION_WIN_NOT_REPRODUCED`.

Decision: keep the existing post-normal indexed receiver as the control. Do not move the deduplication earlier merely because it sounds cheaper; in this exact GDScript receiver the repeated proof-host measurement is slower.

## Boundaries

This is proof-host CPU-side geometry-construction evidence only. It is not target-device CPU/GPU frame time, FPS, VRAM/heap, import/export transport equivalence, arbitrary UV/tangent/color/skin/morph/custom-channel safety, Art/QA acceptance, Environment adoption, CANON, or production readiness.

Environment owns receiver adoption. Art Direction / Visual QA own the nonzero raster tradeoff. Technical Art owns transport/import equivalence outside this procedural receiver path. The four AXM roots remain the merge gate.
