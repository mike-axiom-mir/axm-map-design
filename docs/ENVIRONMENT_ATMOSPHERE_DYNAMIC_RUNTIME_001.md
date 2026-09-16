# Environment Atmosphere Dynamic Runtime 001

Status: **EXPERIMENTAL / NO PRODUCT PROMOTION**

## Bounded question

Can the already-retained synchronized Weather + accepted Nature sapling sequence reuse one sapling `MeshInstance3D`, one `ArrayMesh`, and one material across live proof-host updates, instead of reconstructing those resources for every sample, without changing the exact retained frames or per-frame draw/object/primitive counters?

This Runtime lane stacks on VFX PR #12 exact head `d476cf7c11de74c53397cb21e6f40f90a51c0356`. It does not redesign the Weather field, Nature deformation, Map composition, or cameras.

## Why this lane

The earlier Runtime Weather lane already proved stable reuse for the dynamic Weather `ImmediateMesh`. Re-running that question would duplicate accepted evidence. VFX PR #12 is the first current Map proof that combines the accepted Weather sequence with a genuinely moving source-owned Nature sapling in the same bounded scene, so the new highest-risk lifecycle boundary is the deforming sapling mesh.

## Before / control

`rebuild_sapling_control` is an intentionally synthetic measurement control. In one live Godot process it keeps Weather on a stable reused node/mesh/material but frees and reconstructs only the sapling node, `ArrayMesh`, and material for every evidence and stress update.

It is **not** a claim that AXM currently ships or previously shipped such a reconstruction path.

## Candidate

`reuse_sapling_mesh` creates one sapling node, one `ArrayMesh`, and one material, then clears/recommits only the single triangle surface for each exact authored deformation sample. Weather follows the same stable-reuse path as the control.

The test uses the exact nine VFX states, 390 source vertices, 570 source triangles, 36 Weather streaks, two fixed cameras, nine retained updates, and 48 × 9 stress updates.

## Acceptance gate

A Runtime PASS requires all of the following simultaneously:

- exact VFX prerequisite/source identity and nine-state schedule retained;
- Weather resource identity stable and identical in lifecycle semantics in both modes;
- candidate sapling node/mesh/material identity stable across retained evidence states;
- candidate constructs one sapling node/mesh/material versus 441 of each in the synthetic control across 9 retained + 432 stress updates;
- one sapling surface, 390 source vertices, and 570 source triangles at every retained state;
- identical draw-call, visible-object, and primitive counters for every control/candidate retained frame;
- byte-identical control/candidate PNGs for all 18 fixed-camera frame pairs.

CPU-side submission timings and `RenderingServer` memory counters are retained as hosted-run observations only. They are not acceptance gates or target-device budgets.

## Art Director tradeoff handoff

If all retained control/candidate PNG pairs are byte-identical, Runtime reports `NONE_OBSERVED_IN_EXACT_RETAINED_PROOF_FRAMES`. That does not replace Art Director ownership of motion quality, deformation quality, scene hierarchy, or final visual acceptance.

If any pair differs, the Runtime gate fails and the difference must be retained for Art Director review rather than silently accepted.

## Truth boundary / non-claims

This proof does **not** establish target-device FPS, GPU frame time, mobile/console behavior, production VRAM or streaming budgets, physical wind, physics, collision, gameplay, animation-controller semantics, continuous interpolation, final Art Direction, Visual QA, CANON, product promotion, or Runtime mastery.

The four AXM roots remain the merge gate: Truth, Agency / non-domination, Continuity, and Wisdom before speed.
