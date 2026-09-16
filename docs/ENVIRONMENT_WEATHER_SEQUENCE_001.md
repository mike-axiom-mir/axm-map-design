# Environment Weather Sequence 001

Status: **VFX / Atmosphere sampled receiving-scene evidence only**.

## Why this exists

The exact source-owned Weather candidate is already deterministic and the Environment proof host already renders its `0.50 s` state as one bounded line surface. Runtime has separately shown that this static 36-streak field remains one additional draw call in the pinned host.

What remained unproven was whether the same source-owned visual field could be sampled through its existing `0.0–0.5 s` evidence window inside the real seed-29 Environment scene while keeping every non-Weather scene input fixed.

This lane does **not** change Weather source semantics. It adds an evidence-only intermediate sampling schedule:

`0.0000 / 0.0625 / 0.1250 / 0.1875 / 0.2500 / 0.3125 / 0.3750 / 0.4375 / 0.5000 s`.

Those intermediate times are observation samples inside the already-authored no-wrap source window. They are not new physical weather, gameplay timing or a new source animation contract.

## Exact ownership / provenance

- receiving Environment base: `axm-map-design#4` exact head `8f81c57d9169dc9faba0cb01b85f17dff92bad6f`;
- Nature source remains the exact receiving-scene sapling source and stays neutral in every state;
- Weather source: `axm-weather-design#2` exact head `ca2eaba519e8449835b0ea6ef944b7080c3caa6a`;
- Weather semantics remain `VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED`;
- existing `path_eye` and `elevated_oblique` cameras are unchanged;
- existing Weather render presentation remains proof-only and not physical altitude.

## Bounded gates

The sequence fails closed unless:

- existing Environment source integration re-passes;
- existing Weather source evaluation re-passes;
- all nine samples remain inside the authored source time window;
- all 36 streak IDs/order are preserved;
- all line endpoints remain inside the source scene extent;
- every sampled field is materially distinct by exact field digest;
- adjacent source-head displacement matches the exact authored visual speed projected onto the source visual direction;
- adjacent crosswind drift stays at floating-point-zero tolerance;
- the complete non-Weather receiving scene remains byte-semantically identical across all nine states.

The workflow then renders every state through the **existing** Environment Godot 4.7.2 GL Compatibility observation host rather than creating another scene renderer.

## Truth boundary

A PASS means the exact source-owned Weather field survives a denser deterministic sampled sequence in the existing receiving scene and every retained state is target-host renderable.

It does **not** prove continuous live playback, frame interpolation, runtime update cost, target FPS, physical wind, precipitation, volumetrics, forces, gameplay, collision, final Environment hierarchy, final material/lighting quality, Art Director acceptance, CANON, production readiness or VFX mastery.

Runtime owns cost if a live changing-geometry path is later implemented. Art Direction / Visual Observer own perceptual acceptance. The four AXM roots remain the merge gate.
