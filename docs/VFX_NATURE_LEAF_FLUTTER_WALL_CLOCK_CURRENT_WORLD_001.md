# VFX Nature Leaf Flutter Wall-Clock Current-World 001

## Scope

This VFX / Atmosphere lane stacks on the current Map Environment PR #24 branch while pinning its exact already-accepted leaf-flutter receiver evidence at `7713cbe5863c3bc38dabb6236eb4b393401224b6`. It consumes the exact Art-preferred Nature leaf micro-flutter effect head `ecade64227ba1d3d1faf029ca7188ea63c2560ec` without reauthoring it.

The bounded question is only:

> Can the exact accepted 16-state repeating leaf-flutter source cycle be presented against monotonic wall clock inside the exact accepted current-world Godot receiver at its authored `31.25 ms` source spacing, and if not, which source slots are actually skipped?

## Preserved inputs

The proof preserves:

- the exact accepted current-world Environment composition and two fixed cameras;
- the accepted `390v / 570t` Nature receiver with woody `CULL_BACK` and foliage `CULL_DISABLED`;
- the exact leaf-local flutter spatial response: `5°` cap, per-leaf phase offsets, no added non-leaf motion, exact neutral endpoints;
- the exact inherited source sample spacing of `0.03125 s` and `0.50 s` response window;
- source-width Weather semantics.

Weather is held literally at source phase `00` during each timing run so Weather animation cannot masquerade as leaf-flutter timing cost or cadence. No geometry, material, camera, environment, Weather semantic, amplitude, phase offset, interpolation or retiming change is introduced.

## Scheduler

The proof uses a phase-locked monotonic-wall-clock scheduler:

- `16` unique repeating source phases (`00..15`);
- phase `16` is retained only as the exact neutral endpoint witness and is not inserted as a duplicate-neutral dwell;
- nominal slot spacing: `31.25 ms`;
- cycle duration: `0.50 s`;
- `3` cycles per fixed camera;
- if the host falls behind, the receiver selects the latest due direct source state and records skipped source slots rather than slowing the effect.

For every actually presented slot the observer records source identity plus selection, mesh-submit and `RenderingServer.frame_post_draw` timestamps relative to the ideal due time. This makes source drops and proof-host lateness explicit.

## Result semantics

A successful workflow may return either:

- `PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_WALL_CLOCK_REFERENCE_FULL_SOURCE_COVERAGE`, or
- `PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_WALL_CLOCK_REFERENCE_SOURCE_DROPS_OBSERVED`.

Both mean the bounded characterization executed truthfully. The second state is not a timing acceptance; it preserves missed source slots as evidence for the next VFX / Runtime / Art decision.

## Truth boundary

This proof is a real Godot 4.7.2 GL Compatibility proof-host wall-clock presentation characterization. It is not display scanout timing, perceptual naturalness, physical wind or plant biomechanics, gameplay/collision, target-device CPU/GPU/FPS/VRAM/thermal/battery acceptance, arbitrary-view equivalence, final Art Direction / Visual QA acceptance, CANON, production readiness, or VFX mastery.

`axm-create-me` remains coordination-only. The four AXM roots — Truth, Agency / non-domination, Continuity, Wisdom before speed — remain the merge gate.
