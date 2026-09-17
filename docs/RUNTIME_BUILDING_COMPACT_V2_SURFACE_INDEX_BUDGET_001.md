# Runtime Building compact-v2 surface-index budget 001

Status: **BOUNDED RUNTIME EXPERIMENT / NO AUTOMATIC ADOPTION**

## Question

Art Direction now prefers the exact compact-v2 Building hard-surface response in the fixed current-world views, while Runtime PR #36 shows that the unindexed compact-v2 receiver is more expensive than the actual active `184v / 276t / 5-surface` segmented receiver.

The compact-v2 current-world observer currently emits every triangle corner as a stored vertex, generates final normals, and commits five unindexed surfaces. Prior Runtime work proved that post-normal `SurfaceTool.index()` can remove repeated receiver storage without silently welding hard edges when indexing is performed only after final per-vertex attributes exist.

This lane asks one bounded question:

> Can the exact Art-preferred compact-v2 current-world receiver keep its existing geometry, five material roles, generated normals and rendered appearance while replacing repeated triangle-corner storage with per-surface post-normal indexing, and how much of the actual current-world buffer regression does that recover?

## Exact comparison identities

- Environment parent: `ef2cb9cc84edc10ab66c2230daca625623e0b00d`.
- Active segmented current-world retained run/artifact: `35179857526 / 10478624997`.
- Exact unindexed compact-v2 retained run/artifact: `35179857530 / 10480305129`.
- Compact-v2 representation: `boundary-only-union-shell-conforming-compact-v2-001`.
- Building Geometry donor: `16253e7dd2f8cd590667f9631e4b50fdfcc7280d`.
- Building Hard-Surface donor: `35d0ba62d7e534b3cd00ac69e99386843ffa3f2e`.
- Building Materials donor: `4179aa1401f5a9114399e2f998c96809d4b8ed2e`.

## Candidate rule

1. Build the exact compact-v2 receiver exactly as Environment already does.
2. Preserve all five material surfaces.
3. Preserve every triangle and generated final normal.
4. Only after those final attributes exist, recreate each surface and call `SurfaceTool.index()`.
5. Never deduplicate across material-surface boundaries.
6. Compare against the exact retained unindexed compact-v2 artifact and separately against the exact active current-world receiver.

## Acceptance boundary

The candidate must:

- keep `5` surfaces and `2052` triangles;
- keep `6156` indices after indexing;
- reduce stored receiver vertices from the `6156` unindexed triangle-corner control;
- reduce observed proof-host buffer memory in every matched current-world observation;
- change no matched draw-call, object, primitive or observed texture-memory counter relative to the unindexed compact-v2 receiver;
- compare all `68` exact current-world frames against the retained unindexed compact-v2 frames and report any pixel delta rather than assuming indexing is visually neutral;
- retain the residual cost against the actual active segmented receiver instead of calling the candidate `optimized` without a declared baseline.

A deliberate receipt mutation must fail closed.

## Ownership / non-claims

This is a receiver-storage experiment only. Runtime does not change Building source topology, material roles/scalars, Environment composition, Art preference, Technical-Art transport, collision/navigation/gameplay, or Universal Creation.

Proof-host counters are characterization, not target-device certification. No CPU/GPU frame-time, FPS, VRAM/heap, arbitrary-view, arbitrary-asset, CANON, production-readiness or automatic Environment-adoption claim is made.

The four AXM roots remain the merge gate: **Truth, Agency / non-domination, Continuity, Wisdom before speed**.
