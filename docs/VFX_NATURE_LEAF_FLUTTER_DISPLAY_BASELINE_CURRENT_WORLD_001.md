# VFX Nature leaf flutter visible-display baseline — current world 001

Status: BOUNDED OBSERVATION / NO EFFECT RETUNE / NO RECORDER

## Gap

The exact accepted Nature leaf micro-flutter already has:

- a clean no-capture wall-clock reference on the proof host;
- synchronous in-process visual capture, which materially perturbs delivery;
- external X11 + FFV1 phase-bound capture, which also materially perturbs delivery.

The external run cannot distinguish how much of that slowdown comes from presenting the Godot scene through the visible X11 composition path versus the external grabber/encoder process. Retuning the accepted effect to satisfy instrumentation would be the wrong repair.

## Bounded successor

This evidence lane runs the same visible X11 current-world surface and the same telemetry marker used by the external capture observer, but starts **no recorder process**.

It keeps fixed:

- accepted current-world Nature receiver evidence: `7713cbe5863c3bc38dabb6236eb4b393401224b6`;
- accepted Nature leaf-flutter source effect: `ecade64227ba1d3d1faf029ca7188ea63c2560ec`;
- clean timing reference: `795d9e8862e895e506c756b9ea01cd6228fa7ab7`, workflow `35179504496`;
- 16 unique repeating direct source phases (`00..15`) plus exact endpoint witness `16`;
- source spacing `31.25 ms` / cycle `0.50 s`;
- phase-locked latest-due direct-source scheduler;
- no interpolation and no retiming;
- Weather fixed at exact source phase `00`;
- the same `path_eye` and `elevated_oblique` current-world cameras;
- the same `1120x720` X11 window containing the `1100x720` scene plus a narrow telemetry strip.

The workflow deliberately does not start `ffmpeg`, `x11grab`, a video encoder, viewport readback or PNG encoding during the timed windows.

## Evidence question

Does the visible X11 display/composition + telemetry surface by itself remain comparable to the clean offscreen/no-capture reference?

Declared comparability gate:

- at least `90/96` source slots presented;
- mean post-draw cadence in each fixed camera no worse than `1.10x` the clean reference.

A HOLD is valid evidence. The workflow must not modify the visual source, retime the effect or loosen the gate to obtain a PASS.

## Result semantics

Possible scoped results:

- `PASS_VISIBLE_X11_DISPLAY_TELEMETRY_BASELINE_COMPARABLE_TO_CLEAN_REFERENCE`
- `HOLD_VISIBLE_X11_DISPLAY_TELEMETRY_BASELINE_PERTURBS_CLEAN_REFERENCE`

If PASS, the external grabber/encoder becomes the stronger suspected source of the previous slowdown and a lower-load recorder can be evaluated separately.

If HOLD, the visible X11/display-composition path itself is already materially different from the clean reference, so another recorder experiment would not be timing-faithful on this proof host.

## Truth boundary

This is instrumentation-isolation evidence only. It does **not** prove display scanout timing, perceptual smoothness or naturalness, target-device performance, physical wind/biomechanics, gameplay/collision, final Art/QA acceptance, CANON, production readiness or VFX mastery.

Map Environment keeps composition ownership; Nature VFX keeps source-effect ownership; Art Direction / Visual QA keep perceptual acceptance; Runtime keeps target-device performance. `axm-create-me` remains coordination-only. The four AXM roots — Truth, Agency / non-domination, Continuity, Wisdom before speed — remain the merge gate.
