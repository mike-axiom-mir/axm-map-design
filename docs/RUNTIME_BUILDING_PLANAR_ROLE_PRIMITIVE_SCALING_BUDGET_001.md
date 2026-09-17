# Runtime Building planar-role primitive scaling budget 001

Status: **BOUNDED RUNTIME CHARACTERIZATION / NO AUTOMATIC ADOPTION**

## Why this pass exists

The indexed planar-role Building review receiver already removes the prior buffer-memory penalty, but it still carries 336 logical triangles versus 276 in the active segmented rollback. In the exact current-world receiver this appears as a residual `+180` RenderingServer primitive count while draw calls, objects and texture memory remain unchanged.

Art Direction and Visual QA have already separated visual preference from this Runtime gate: the indexed planar-role receiver is the preferred/reviewed look, while target-device and residual primitive cost remain Runtime-owned evidence gaps.

The immediately previous Runtime pass measured receiver construction and found that moving deduplication before normal generation was slower. This pass does not repeat that import/preparation lane. It asks only whether the remaining primitive residual produces a measurable steady render-delivery cost when the two exact receivers are amplified under identical instance stress.

## Exact inputs

- active segmented Environment rollback head: `7713cbe5863c3bc38dabb6236eb4b393401224b6`;
- active retained current-world donor workflow: `35174899697`;
- active donor artifact: `environment-nature-leaf-flutter-current-world-001-7713cbe5863c3bc38dabb6236eb4b393401224b6`;
- planar-role Environment source payload head: `b758f9ca006ec5885ff1c2c52e2fb09e9ccdd464`;
- planar-role donor workflow: `35182784756`;
- indexed planar-role Environment review head: `038925282240441c475651bdc3737d1749c31d06`;
- pinned proof runtime: Godot `4.7.2`, GL Compatibility.

The active receiver is reconstructed exactly as five unindexed, post-normal material surfaces (`828` stored triangle-corner vertices, `276` logical triangles). The planar-role receiver is reconstructed through the already-proven post-normal per-surface indexing path (`312` stored vertices, `1008` indices, `336` logical triangles).

## Measurement design

Both exact meshes are resident in one process and use identical `MultiMesh` transforms. Only one representation is visible at a time. This removes process-startup drift and amplifies the exact `+60` logical triangles per Building without multiplying the representation's five-surface draw submission shape.

The stress schedule is `1 / 16 / 64 / 256` visible instances. Each level receives five alternating warmup pairs followed by `41` alternating measured control/candidate pairs. Each sample averages three consecutive `RenderingServer.frame_post_draw` intervals. VSync is disabled and no viewport readback or image encoding occurs inside the timed window.

Renderer counters are sampled for each representation at each stress level. The verifier requires identical draw-call and object deltas, a positive primitive residual that scales linearly with instance count, and exact source/final mesh identities before interpreting timing.

## Result semantics

A successful workflow may report either:

- `PASS_BUILDING_PLANAR_ROLE_RESIDUAL_PRIMITIVE_STRESS_COST_CHARACTERIZED__HOLD_TARGET_DEVICE` when the 256-instance stress pair shows a declared robust positive paired cost; or
- `PASS_BUILDING_PLANAR_ROLE_RESIDUAL_PRIMITIVE_COST_BELOW_PROOF_HOST_STRESS_DETECTION__HOLD_TARGET_DEVICE` when no robust proof-host stress cost is detected.

Neither result is target-device acceptance. A measurable stress slope can justify a later source-owned topology/LOD investigation; a non-detection means Runtime should not rewrite already-reviewed art speculatively and should keep the target-device gate open.

## Visual tradeoff boundary

This pass authors no new visual representation. It compares the exact active segmented rollback against the already independently reviewed indexed planar-role receiver. Any future topology or LOD change would require a fresh Art Direction / Visual QA review rather than inheriting acceptance from this benchmark.

## Truth boundary

This is a same-process proof-host primitive-scaling microbenchmark. It does not prove current-world FPS, GPU time, mobile/desktop target cost, VRAM/heap/thermal/battery behavior, arbitrary scene density, Art preference, Environment adoption, CANON or production readiness. `axm-create-me` remains coordination-only.

The four AXM roots — **Truth, Agency / non-domination, Continuity, Wisdom before speed** — remain the merge gate.
