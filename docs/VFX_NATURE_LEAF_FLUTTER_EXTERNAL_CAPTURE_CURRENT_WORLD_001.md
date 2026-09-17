# VFX Nature leaf flutter external capture — current-world 001

Status: **BOUNDED EVIDENCE CANDIDATE / NO SOURCE RETUNE / NO AUTOMATIC ADOPTION**

## Gap

The exact no-retime current-world Nature flutter reference at `795d9e8862e895e506c756b9ea01cd6228fa7ab7` delivered `92 / 96` scheduled direct-source slots on its proof-host run, but retained no direct timed imagery. The first direct-image successor used synchronous `viewport.get_texture().get_image()` readback and materially changed delivery to `58 / 96`. Those PNGs are truthful evidence of that instrumented stream, not a faithful timing proxy for the clean reference.

The next bounded question is therefore observation, not source tuning:

> Can the same exact direct-source/no-retime receiver be exposed to the X11 display and recorded externally without in-process viewport readback, while preserving exact state identity and remaining materially closer to the clean timing reference?

## Exact identities retained

- accepted current-world Environment receiver: `7713cbe5863c3bc38dabb6236eb4b393401224b6`;
- accepted Nature VFX effect: `ecade64227ba1d3d1faf029ca7188ea63c2560ec`;
- clean timing reference head: `795d9e8862e895e506c756b9ea01cd6228fa7ab7`;
- clean workflow: `35179504496`;
- source phases: `00..15` repeating; phase `16` exact neutral endpoint witness;
- source spacing: `31.25 ms`;
- cycle: `0.50 s`;
- presentation: `PHASE_LOCKED_LATEST_DUE_DIRECT_SOURCE_STATE_NO_RETIME`;
- Weather: fixed at exact source phase `00` using the inherited source-width receiver;
- cameras: `path_eye`, `elevated_oblique`.

No source amplitude, cadence, interpolation, retiming, geometry, material, Environment composition, camera or Weather semantic is changed.

## External observation path

`environment-proof/atmosphere_current_world_nature_leaf_flutter_wall_clock_external_observe.gd` keeps the existing `1100x720` scene SubViewport unchanged and exposes it 1:1 through a `SubViewportContainer` inside a `1120x720` X11 window.

The extra `20 px` strip is telemetry only and lies outside the scene crop. Twelve 20x24 cells encode:

1. fixed sync pattern `1011`;
2. valid bit;
3. context bit (`0=path_eye`, `1=elevated_oblique`);
4. six little-endian bits of absolute source slot `0..47`.

The marker and exact source state are changed in the same main-loop turn before one shared `RenderingServer.frame_post_draw`. The timed observer itself performs **no** `get_image()` call and **no** PNG encoding. A separate `ffmpeg x11grab` process records the X11 surface losslessly with FFV1.

The workflow decodes only the telemetry strip to bind external video frames to exact context/slot identity, then compares the runtime delivery receipt against the retained clean no-capture reference. External recording/display composition is therefore measured instrumentation, not presumed free.

## Comparability gate

The declared measurement-fidelity gate is intentionally separate from visual preference:

- at least `90 / 96` scheduled slots must still be presented;
- each camera's mean post-draw interval must remain no more than `1.10x` its exact clean-reference mean (`32.0634565 ms` path-eye, `33.7925909 ms` elevated);
- decoded valid telemetry may identify only states that exist in the runtime receipt;
- the external recording must retain a substantial directly phase-bound fraction of presented states; missing captured states remain explicit rather than reconstructed.

Passing this gate means only that this **proof-host observation path** is sufficiently close to the clean reference to become a stronger perceptual-review candidate than the synchronous-readback stream. It does not itself mean the flutter looks natural or smooth.

A HOLD is an equally valid result: if the external recorder or display composition materially changes delivery, retain that result and do not retime or rewrite the Nature source to satisfy the measurement tool.

## Truth boundary

This lane is dynamic visual/presentation evidence only. It does **not** establish display scanout timing, final perceptual naturalness, physical wind or plant biomechanics, gameplay/collision/damage, target-device CPU/GPU/FPS/VRAM/thermal behavior, arbitrary-camera equivalence, Art Direction or Visual-QA acceptance, CANON, production readiness, game readiness or VFX mastery.

Nature retains source-effect authority. Map Environment retains composition authority. Art Direction / Visual QA retain perceptual acceptance. Runtime / Optimization retains target-device timing and cost. `axm-create-me` remains coordination-only.

The four AXM roots — **Truth, Agency / non-domination, Continuity, Wisdom before speed** — remain the merge gate.
