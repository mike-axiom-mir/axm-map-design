# Technical Art — Building utility-panel material GLB bridge 001

## Bounded gap

Building Geometry PR #18 and Materials PR #3 both stop at the same explicit handoff: Geometry owns the exact 1.10 m × 1.50 m service-surface chart, Materials owns the 512 × 512 serialized review checker plus its 352 × 480 active region and 320 px/m review target, while Technical Art owns the material-bearing GLB package and exact UV/material/image transport. The shared UC `inspect_material_uv_density` observer was intentionally not consumed until such an artifact existed.

This lane closes only that transport gap. It does not author a new UV chart, choose density, choose an atlas, redesign the checker, change source geometry, select production material policy, change Universal Creation, or authorize receiver/runtime/visual adoption.

## Exact owner chain

- Hard Surface PR #17 current head `fbfa3b47048755b45dac91451171d5511c8d4f47`: exact local +X service surface, 4 corners, 1.10 m × 1.50 m, source-domain blob `8b4484d4ccbd500e58910a2835d8780112489919`.
- Geometry PR #18 head `02944a9f10528a051603df3a6fd7b3183730773f`: exact 4-corner/2-triangle normalized chart blob `08431f75edff5ae7d8b8c32468190e7a1b81d526` and review-sampling handoff blob `498fdc5251a7393bc38aa14910678c3650ad5ddb`.
- Materials PR #3 head `5f096369eee2ef44275ea8f1c7dc1b6e564e71c8`: serialized-review contract blob `620bc298256d21ee008b6fe870135f09212f8db9`; retained artifact `10518114336` from workflow `35270493702`; exact review PNG 2531 B, SHA-256 `e932cdd94d370184c7361862d5064149cc193e3a8fd80b269cab6543c0919198`; reloaded RGBA8 SHA-256 `02f8f464eabc734a3be687a7706edf8b8f62ece834fa981c8c993fbb8227bb4b`.
- Current UC head selected for this proof: `13a823349a568db266099564d6f5d8d7bac48b2b`; generic material UV observer blob remains `bc7aa2ffc2c598d75a78739c70fd349138f511e2`.

The base64 fixture in this Technical Art lane is an exact byte copy of the retained Materials PNG, pinned by the artifact/run/digest record. It is a transport fixture, not a transfer of Materials authority.

## Smallest reusable contract

`tools/technical_art_building_utility_panel_material_glb_bridge.py` consumes owner contracts and the exact retained review PNG and emits one bounded proof carrier:

- Hard-Surface-owned local corner positions;
- Geometry-owned triangle connectivity and normalized chart;
- Materials-owned active-region placement mapped into `TEXCOORD_0`;
- the exact Materials PNG embedded in GLB `bufferView` storage and bound to `baseColorTexture`;
- Materials-owned scalar metallic/roughness copied into the proof carrier without promoting it to production policy.

The bridge also retains the existing full-square/aspect-blind negative using the same source geometry and image. No Building rule is added to UC.

## Required evidence

The workflow must prove all of the following on the exact Technical Art head:

1. all owner heads and Git blobs match the pinned contracts;
2. the copied PNG exactly matches Materials retained bytes;
3. the positive GLB is material-bearing and embeds that exact image;
4. current generic UC reads the positive GLB as 320 texels/m in both principal directions and reads the aspect-blind negative as approximately 341.33/465.45 texels/m;
5. a real Godot 4.7.2 import exposes the same four UV corners, the expected material scalars, a readable 512 × 512 image, and the exact Materials RGBA8 base-level digest;
6. one-byte image drift and active-region drift fail closed.

## Truth boundary

A PASS proves an exact, bounded owner → Technical Art GLB → generic UC observer → real Godot import path for this review carrier. It does not make the GLB source truth, adopt production UVs or texture policy, approve visual quality, select runtime storage/cost, authorize Environment adoption, establish CANON, or claim production/game readiness. The four AXM roots remain the gate.
