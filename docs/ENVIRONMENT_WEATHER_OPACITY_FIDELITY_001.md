# Environment Weather opacity fidelity 001

Status: **EXPERIMENTAL VFX / ATMOSPHERE EVIDENCE / NO PRODUCT PROMOTION**

## Question

The exact source-owned Weather study already authors one opacity value per streak, and the Environment receiving payload already carries those values into every `weather_lines` row. The pinned Godot observation host, however, historically rendered all 36 streaks with one uniform alpha (`0.62`).

That means the existing Environment and VFX target-host renders prove source-derived streak geometry and motion/readability, but they do **not** prove source opacity fidelity.

This lane asks one bounded question:

> Can the current real seed-29 Environment proof host consume the exact already-carried per-streak Weather opacity without changing streak geometry, Weather semantics, cameras, scene composition, source identities, or unrelated rendering state?

## Exact base and ownership

This lane starts from the current Environment PR #4 head on publication and changes only VFX receiving representation.

Source authority remains:

- Weather source: `mike-axiom-mir/axm-weather-design#2`;
- exact Weather head: `ca2eaba519e8449835b0ea6ef944b7080c3caa6a`;
- semantics: `VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED`;
- exact receiving payload: the existing `environment_eye_level.build_scene_payload()` result;
- target host: Godot 4.7.2 GL Compatibility `environment-proof/observe.gd`.

No Weather source field is re-authored here. `axm-create-me` remains coordination-only.

## Before / control

Historical target-host mode:

`UNIFORM_PROOF_ALPHA_0P62`

All 36 line streaks use the existing single unshaded blue material at alpha `0.62`. The source opacity values remain present in the payload but are not consumed by the renderer.

## Candidate

Candidate mode:

`SOURCE_STREAK_OPACITY_VERTEX_ALPHA`

The candidate keeps one `ImmediateMesh` line surface and the same material family, but enables `vertex_color_use_as_albedo` and writes each exact source streak opacity to both vertices of that streak via `ImmediateMesh.surface_set_color()` before the vertices are submitted.

The candidate does **not**:

- change tail/head geometry or presentation height;
- change source streak order/identity;
- change the Weather motion contract;
- create additional per-streak draw surfaces or materials;
- infer physical density, humidity, precipitation or wind force;
- map source `width_px` into 3D line width.

`width_px` remains an SVG/source presentation attribute with no proven portable 3D mapping in this lane.

## Evidence contract

`tools/environment_weather_opacity_fidelity.py` rebuilds the exact current receiving payload from pinned Nature/Weather dependencies and emits two scenes that are machine-equal after removing only `weather_render_profile` and their resulting `scene_digest`.

The exact same `observe.gd` host then renders both profiles from both fixed cameras. The dedicated Godot image comparator requires a nonzero retained pixel delta in each camera and records changed-pixel count, fraction, bounding box, brighter/darker changed pixels and mean absolute RGB delta.

A visible pixel delta is **not** automatically called aesthetically better. It proves only that the source opacity signal reached the target-host image.

The historical default remains backward compatible: payloads without `weather_render_profile` continue to use uniform alpha `0.62`, so inherited Environment evidence is not silently rewritten by this VFX lane.

## Truth boundary

A PASS proves only that:

- the exact current Environment payload contains 36 source-owned streak opacity values;
- control and candidate scene state are identical except the explicit render profile;
- the pinned Godot host can consume the carried source opacity on one line surface using vertex alpha;
- the resulting fixed-camera PNGs visibly differ from the historical uniform-alpha control.

It does **not** prove:

- better Art Direction or final atmosphere quality;
- source `width_px` fidelity in 3D;
- continuous live playback, interpolation quality or frame pacing;
- target FPS, GPU cost, memory budgets or generic renderer policy;
- physical wind, precipitation, fog, volumetrics, force or simulation;
- gameplay, visibility balance, damage or collision;
- CANON, production readiness, or VFX / Atmosphere mastery.

Art Director / Visual Observer own perceptual acceptance. Runtime owns cost. Weather keeps source semantics. The four AXM roots remain the merge gate.
