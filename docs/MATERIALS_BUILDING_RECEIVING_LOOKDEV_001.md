# Materials — Building Receiving LookDev 001

This bounded Materials / LookDev lane transfers the exact Building Materials PR #3 candidate into the exact Map PR #11 seed-29 receiving scene. It intentionally changes only Building surface response.

## Exact prerequisites

- Map receiving scene: `mike-axiom-mir/axm-map-design#11` at `c72838eb4b40ee7903a3c3e326a1bf77fa08bee5`.
- Building structural source: `mike-axiom-mir/axm-building-design#2` at `4faa769b406bf3ad0ba9489a77141c27f122ce51`.
- Building Materials candidate: `mike-axiom-mir/axm-building-design#3` at `484ced313ba0337ea27eebd01c5677e72e8456af`.
- Material profile SHA-256: `85650897cde5bceaf1eb2d389c2a61d47c3d50a2000e429cac8a7846c8c153c4`.
- Renderer: pinned Godot 4.7.2 GL Compatibility.
- Cameras: exact PR #11 `path_eye` and `elevated_oblique`.

## Controlled A/B

Both states rebuild Map PR #11 through its own source-integration contract first. The exact 152-vertex / 228-triangle Building world mesh is then partitioned into the five source-owned material roles without moving a vertex or changing a triangle.

The neutral control and candidate use the same five-surface partition, so the renderer sees identical Building geometry/surface grouping. Only material fields differ:

- `frame_galvanized`
- `infill_coating`
- `roof_membrane`
- `slab_mineral`
- `utility_panel_ochre`

The receiving host is derived fail-closed from the exact inherited Environment observer rather than recreating scene lighting/cameras independently. Nature, Weather, path, seed, Object proxies, remaining Nature proxies and cameras remain unchanged.

## Art-direction question

This is specifically the handoff requested by current Art Direction and Visual QA: does the standalone Building surface hierarchy survive the real Environment lighting/context without turning the ochre service panels into the path-end focal point, collapsing the roof/infill into one black mass, or worsening the known triangular front-panel light/shadow read?

The workflow produces two exact fixed-camera neutral/candidate pairs plus machine pixel-delta evidence. Pixel change proves attribution only; Materials can inspect the retained images, while final Art Direction / Visual QA own aesthetic acceptance.

## Truth boundary

A structural/render PASS proves exact provenance, exact scene preservation, exact Building geometry preservation, successful target-host rendering, and a visible surface-only delta in both fixed cameras.

It does **not** prove final lookdev, final lighting, UVs, textures, decals, weathering, physically measured steel/concrete/coating behavior, renderer equivalence, target-device runtime cost, architecture/engineering, collision/navigation, gameplay, CANON, production readiness, or Materials mastery.

`axm-create-me` remains coordination-only. The four AXM roots remain the merge gate: Truth, Agency/non-domination, Continuity, and Wisdom before speed.
