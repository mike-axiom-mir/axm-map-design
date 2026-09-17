# VFX Nature leaf flutter — direct timed current-world capture 001

Status: BOUNDED EVIDENCE CANDIDATE / NO SOURCE RETUNE

## Gap

The existing current-world wall-clock reference proves phase-locked latest-due direct-source scheduling and truthfully records dropped source slots, but its retained artifact contains timing logs only. Visual QA and Art Direction therefore cannot judge the actually delivered no-retime stream from direct rendered frames.

This successor closes only that evidence gap. It does not change the accepted Nature flutter source, spatial amplitude, source cadence, Weather semantics, geometry, materials, Environment composition, cameras, gameplay or physics.

## Exact inherited identities

- accepted current-world Nature receiver: `7713cbe5863c3bc38dabb6236eb4b393401224b6`;
- accepted Nature leaf-flutter source effect: `ecade64227ba1d3d1faf029ca7188ea63c2560ec`;
- presentation mode: `PHASE_LOCKED_LATEST_DUE_DIRECT_SOURCE_STATE_NO_RETIME`;
- source phases: `00..15` repeating, with phase `16` retained only as the exact neutral endpoint witness;
- nominal source spacing: `31.25 ms`;
- nominal cycle duration: `0.50 s`;
- Weather remains fixed at exact source phase `00` using the existing source-width presentation;
- cameras remain `path_eye` and `elevated_oblique`.

## Bounded improvement

For every direct source state that is actually presented by the inherited wall-clock scheduler:

1. apply the exact source sapling state;
2. wait for `RenderingServer.frame_post_draw`;
3. read back that exact current viewport into an `Image`;
4. retain the source slot, cycle, phase identity and viewport-readback duration;
5. defer PNG encoding until the timed scheduling window has ended;
6. save one PNG per actually presented state plus the exact neutral endpoint witness.

This makes the retained visual evidence correspond to the states the real proof-host scheduler actually presented rather than reconstructing them later from sampled source frames.

PNG encoding is deliberately moved outside the timed window. Viewport readback itself can still influence later scheduling, so its duration is measured and retained. The pre-existing no-capture timing reference remains the clean timing baseline; this capture run is a visual-observation instrument, not a replacement performance benchmark.

## Acceptance boundary

A green workflow may establish only that:

- direct post-draw frames were retained for every state actually presented during this capture run;
- each retained frame remains bound to its exact direct source slot/phase identity;
- source drops remain explicit rather than being hidden by retiming;
- Weather, source cadence and accepted spatial response were not silently rewritten;
- the exact endpoint witness remains separately retained.

It does **not** establish:

- display scanout timing;
- perceptual smoothness or naturalness;
- final Art Direction or Visual QA acceptance;
- target-device CPU/GPU/FPS/VRAM/thermal/battery performance;
- physical wind, plant biomechanics or aerodynamics;
- gameplay, collision, damage or interaction behavior;
- CANON, production readiness or VFX mastery.

`axm-create-me` remains coordination-only. The four AXM roots — Truth, Agency / non-domination, Continuity, Wisdom before speed — remain the merge gate.
