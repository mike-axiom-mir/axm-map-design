# Environment Eye-Level Proof 001

Status: **EXPERIMENTAL / OBSERVATION EVIDENCE ONLY**

This proof extends the existing source-owned Environment slice without changing its composition rules. It consumes the exact seed-29 map variant, exact Nature sapling source and exact Weather visual field already proven by the Environment integration lane, then renders the mixed scene from two fixed cameras in Godot 4.7.2 GL Compatibility.

## Why this exists

The prior retained evidence is top-down. That is enough to prove the central path remains open in plan view, but it does not show whether the same composition remains readable at human eye height or whether building/nature/object masses create unexpected depth/occlusion conflicts.

The smallest useful next step is therefore observation, not another asset system:

- `path_eye`: fixed camera inside the declared central readable path, looking down its length;
- `elevated_oblique`: fixed three-quarter context spanning map, building proxy, remaining nature proxies, object proxies, the exact source-owned sapling and the Weather visual field.

## Source ownership

No source asset is moved or rewritten by this proof. It re-runs the existing `axm.environment-source-integration/v0.1` evaluator against the exact pinned donor heads before emitting the runtime payload.

The Godot proof host converts source coordinates `[x_right, y_forward, z_up]` into Godot `[x_right, y_up, z_back]` as `[x, z, -y]`. The sapling is rendered with culling disabled only so the original planar leaf blades remain visible in this observation host; that is not material acceptance and does not replace the Technical Art leaf-backface evidence.

The Weather source is two-dimensional. For the observation host only, its exact sampled XY streak endpoints are displayed on a fixed 3.0 m presentation plane. This is explicitly **not** a physical altitude, weather volume or wind-force claim.

## Evidence gate

A bounded PASS requires:

- the existing Environment source integration still PASSes;
- map surface, building proxy, remaining nature proxy and object proxy classes are all present;
- the exact 390-vertex / 570-triangle sapling is present;
- all 36 source-owned Weather streaks are present;
- both fixed cameras are retained;
- the proof-only culling and weather-presentation truth boundaries remain explicit;
- Godot 4.7.2 GL Compatibility captures both contexts successfully and records exact payload identity.

## Non-claims

A successful capture does **not** establish final environment art, traversal, collision, gameplay, physical weather, final lighting/materials, vegetation deformation, runtime cost, Art Director acceptance, Visual Observer acceptance, CANON, production readiness or Environment / World Art mastery.
