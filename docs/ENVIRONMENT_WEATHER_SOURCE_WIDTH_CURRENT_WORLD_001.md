# Current-world Weather source-width proof

Status: **SOURCE-WIDTH STRUCTURE + FIXED-CAMERA TARGET HOST PROVED / WALL-CLOCK PRESENTATION EVIDENCE-GATED**

This VFX lane stacks exactly on Map VFX PR #22 head `e482d003853e52fc835f1797ddfb6506a50083ef` and consumes Weather PR #3 exact seed `44021` without changing Weather source semantics.

## Proven source-width boundary

The Weather source owns one deterministic screen-pixel `width_px` per streak. The current receiving path binds all 36 exact source widths by streak identity/order and presents them as camera-projected ribbons in the two fixed `1100x720` proof cameras while preserving source opacity, the 17-state Weather sequence, the west-sapling response and rear-tree culling.

Exact predecessor head `15a03b7c3ba3aaa7c0475ca1a3091c15581f559b` established:

- `PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE`;
- `PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_TARGET_HOST`;
- 17 states × 2 cameras × 36 streaks = 1,224 projected-width measurements;
- maximum projected-width residual `0.00974698571769128 px` against the `0.05 px` gate;
- 68 retained control/candidate frames;
- five explicit path-eye near-plane endpoint clips and no silently dropped source streaks.

Independent Visual QA subsequently cleared the retained fixed-camera source-width presentation for clipping-artifact/readability risk. That does not choose the final atmosphere style.

## Current bounded gap — real elapsed-time presentation

The prior VFX evidence deliberately held wall-clock playback. Earlier dense-state work already proved that the exact source-owned Weather + sapling fields can be directly evaluated at the 17 source times `0.0 .. 0.5 s` in `0.03125 s` steps. The missing question is whether the exact source-width presentation can be **scheduled and actually drawn in Godot on that source timeline** rather than only inspected as independently settled states.

This follow-on adds no interpolation and invents no new Weather state. It reuses the exact 17 direct source evaluations and the already-proven source-width ribbon representation.

For each fixed camera independently, the playback observer:

1. warms the exact existing scene/resources outside the clock window;
2. starts a monotonic Godot wall clock;
3. schedules each exact state at its authored `0.03125 s` source-evaluation time;
4. updates the same Weather and sapling resources;
5. waits for `RenderingServer.frame_post_draw` before recording the presentation timestamp;
6. records source identities, projected-width residual and near-plane clipping evidence for every state.

The verifier requires all 17 states in exact order in both cameras, exact source digests, stable resource identities, the existing `0.05 px` width gate, the exact five/zero near-plane clip totals, and both submission and post-draw observation within one source interval of each scheduled source time. A `0.5 ms` numerical/scheduler epsilon is allowed only around that one-interval deadline.

Dedicated workflow:

`VFX Weather source-width wall-clock presentation evidence`

Expected scoped state, only if exact-head CI proves it:

`PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_BOUNDED_WALL_CLOCK_PRESENTATION`

A deliberate timing-drift negative control must fail closed. The gate is not weakened if CI cannot meet the authored source cadence.

## Ownership boundary

Weather keeps stochastic layout, direct source evaluation, visual direction/speed, opacity and width ownership. Map owns only this target-host receiving/presentation evidence. No Weather policy is copied into Universal Creation, no Environment composition or Materials choice changes, and `axm-create-me` remains coordination-only.

The camera-projected ribbon remains a proof-host representation. The wall-clock verifier is a VFX temporal-presentation check, not a Runtime performance budget or gameplay/controller system.

## Non-claims

Even after a scoped wall-clock PASS, this lane does not establish interpolated continuity between direct source samples, arbitrary camera/FOV/resolution fidelity, renderer-independent line/ribbon semantics, target-device FPS/GPU/CPU/VRAM/overdraw budgets, physical wind/precipitation/turbulence/forces, gameplay visibility/collision/damage, final Art Direction preference, CANON, production readiness, or VFX / Atmosphere mastery.

The four AXM roots remain the merge gate: Truth, Agency / non-domination, Continuity, and Wisdom before speed.
