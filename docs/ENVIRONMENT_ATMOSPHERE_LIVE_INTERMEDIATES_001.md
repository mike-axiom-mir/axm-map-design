# Environment atmosphere live intermediates 001

Status: **EXPERIMENTAL VFX / ATMOSPHERE EVIDENCE / NO PRODUCT PROMOTION**

## Bounded question

The existing VFX lane already proves 17 exact source-evaluated synchronized Weather + accepted sapling states in one Godot 4.7.2 GL Compatibility process with stable Weather and sapling node/mesh/material identities.

A later sibling VFX lane (`axm-map-design#9`, exact head `1d24506e1d5f37cad32c878a15ac6908bf096329`) independently proved that the Weather source's already-carried per-streak opacity can reach the Godot image through one `ImmediateMesh` line surface using vertex-color alpha. The dense live observer still used the older uniform proof alpha `0.62`, so the studio's most advanced temporal proof had weaker Weather representation fidelity than the dedicated opacity proof.

This extension asks one narrow composition question:

> Can all 17 exact dense Weather + sapling states retain the exact existing geometry/motion sequence and stable-resource lifecycle while the Weather path consumes the exact source-owned per-streak opacity already present in every state?

## Ownership and provenance

- Weather source authority remains `mike-axiom-mir/axm-weather-design#2` at exact head `ca2eaba519e8449835b0ea6ef944b7080c3caa6a`.
- Nature visual-response authority remains `mike-axiom-mir/axm-nature-design#2` at exact head `cee14f5b3feea78b0adcd044bad2ea3c97657fc6`.
- The dense synchronization source sequence remains stacked on Map VFX PR #12 and Runtime PR #13.
- Map VFX PR #9 head `1d24506e1d5f37cad32c878a15ac6908bf096329` is mechanism provenance for the receiving-side vertex-alpha representation only; it does not become Weather source authority and is not silently treated as ancestry.
- `axm-create-me` remains coordination-only.

## Preserved source sequence

The extension must retain the existing dense sequence digest exactly:

`f7f2cad01184e8651bcc722b755a2f3c2292ca13e81c7399579d7f42e0c19b30`

That sequence still contains 17 states from `0.0` through `0.5 s` in exact `0.03125 s` increments, including the nine prior exact samples plus eight source-evaluated half-steps. No Weather tail/head geometry, sapling geometry, sampling schedule, source motion semantic, camera, path or scene placement is changed by the opacity composition.

## Receiving representation

The live Weather resource remains one stable `MeshInstance3D`, one stable `ImmediateMesh`, one stable `StandardMaterial3D`, and one line surface across all 17 updates.

The only intended renderer-side representation change is:

- material base alpha becomes `1.0`;
- `vertex_color_use_as_albedo` is enabled;
- before each line endpoint is submitted, the exact carried source opacity is written through `surface_set_color(Color(1,1,1,opacity))`;
- source `width_px` remains explicitly **not mapped** to 3D line width.

Every source opacity must stay in `[0,1]`, the source streak ID/opacity profile must be identical across all 17 motion states, and every target-host update must report the exact source min/max/mean while preserving 36 streaks and one line surface.

## Evidence gates

`tools/environment_atmosphere_live_opacity.py` fails closed unless:

- the dense source sequence itself still passes;
- exact Weather source head and exact historical dense sequence digest are preserved;
- all 17 states contain the same 36 unique streak identities and exact opacity profile;
- the profile contains authored variation rather than one uniform value;
- the Godot receipt reports source-opacity consumption on all 17 updates;
- min/max/mean opacity readback matches the source rows at retained precision;
- the receiving mechanism is bound to exact VFX PR #9 provenance;
- source `width_px` remains outside the claimed 3D fidelity boundary.

The existing dense target-host verifier remains responsible for stable resource identities, exact counts, all 34 retained frames, frame non-identity across time, and stable per-camera draw/object/primitive counters. This opacity verifier adds fidelity evidence; it does not replace Runtime ownership.

## Truth boundary

A PASS proves only that the exact source-owned per-streak Weather opacity already present in the 17 dense source states survives the same-process Godot proof-host path while the exact dense Weather/Nature geometry sequence and stable-resource lifecycle remain intact.

It does **not** prove:

- better or final atmosphere art;
- source `width_px` fidelity in 3D;
- wall-clock cadence, renderer interpolation or arbitrary continuous playback;
- physical wind, forces, turbulence, precipitation, fog, smoke or volumetrics;
- gameplay visibility, damage, collision or simulation authority;
- target-device FPS, GPU time, memory, overdraw or battery cost;
- final Art Direction / Visual Observer acceptance;
- transfer of sapling deformation semantics to other Nature bodies;
- UC extraction, generic VFX architecture, CANON, production readiness or VFX mastery.

The four AXM roots remain the merge gate.