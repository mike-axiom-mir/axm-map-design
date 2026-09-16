# Environment rear-tree normal-culling receiving review 001

## Scope

This Environment / World Art lane stacks exactly on Map PR #15 head `03e956475158a59d70cca08b73be23c141e4cb1f` after Visual QA accepted the rear/right tree's culling-disabled hierarchy but blocked normal-culling adoption of the historical mesh.

The review does not redesign the tree, move the placement, consume Building Materials PR #14, consume Runtime PR #17, consume VFX PR #16, change Weather, alter Object proxies, or add Nature policy to Universal Creation.

It compares one exact receiving-scene variable:

- historical Nature PR #8 rear mesh `d7fc5deaa1c12d1d8c7d7b6dc95bf1e8544ce26140ee2e4a7d2c67a2c4133e48`;
- migrated Nature PR #9 source-generated rear mesh `aa9d450a78fef722672ea9af0f9aca98b4c1a0ca3705661784f5f61f3e9b6a31`.

Both retain source digest `0adf2cde8cfc355ec21b6fb06c6759b753300164b5f72ba029dc1b8c6d2ef307`, the exact PR #15 placement and the same 390 vertices / 570 triangles. The migration is accepted into this review only when world vertices and per-triangle vertex membership remain exact and exactly 260 triangle rows change winding.

## Culling isolation

The existing Godot 4.7.2 GL Compatibility Environment observer now accepts an optional target-source culling review. Historical behavior remains the default when no review is declared.

For this review only:

- `source:nature:east-rear-tree-neutral-001` receives `CULL_BACK`;
- west sapling and compact east source remain `CULL_DISABLED`;
- Building, Weather, Object proxies, remaining Nature proxies, path, cameras, lighting and neutral proof materials are unchanged.

This prevents still-historical topology in other Nature bodies from contaminating the rear-tree comparison.

## Evidence gate

The dedicated workflow must:

1. rebuild exact PR #15 composition from its pinned Building, Nature and Weather dependencies;
2. rebuild exact Nature PR #9 source output rather than copying Geometry's old derived candidate;
3. prove unchanged source digest, world vertices, triangle membership, placement, path, cameras, Weather and unrelated source meshes;
4. prove the expected historical -> migrated rear mesh lineage and exactly 260 changed triangle rows;
5. render historical and migrated scenes through the same target-only `CULL_BACK` observer state from `path_eye` and `elevated_oblique`;
6. retain runtime receipts, exact scene payloads, pixel/hash comparison and all four PNGs.

A visible A/B delta is expected from prior isolated Technical Art evidence, but the Environment workflow records the actual receiving result rather than assuming it.

## Truth boundary

A structural PASS means only that the exact source migration reaches the exact receiving scene without hidden form/composition changes and is ready for the declared target-host culling comparison. A target-host PASS means only that both exact scenes rendered under the declared isolation and the resulting image relationship was retained.

Neither result establishes global outward-normal correctness, final leaf/backface representation, final vegetation materials, deformation/wind quality, target-device FPS/GPU/memory budgets, collision/navigation/gameplay, CANON, production readiness or Environment/Nature mastery.

Art Direction / Visual QA own the perceptual/adoption verdict. Geometry owns source topology. Technical Art owns UC/transport contracts. Runtime owns performance. The four AXM roots remain the merge gate.
