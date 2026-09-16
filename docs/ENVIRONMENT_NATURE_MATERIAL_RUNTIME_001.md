# Environment Nature material sharing runtime evidence 001

Status: **RUNTIME EXPERIMENT / EXACT RECEIVING-SCENE EVIDENCE**

## Question

Environment PR #15 is the first current Map scene with three simultaneous source-owned Nature meshes: the west sapling, compact east tree, and east-rear tree. The existing Godot observation host gives every Nature source mesh a visually identical immutable `StandardMaterial3D`, but constructs a separate material for every mesh in every fixed-camera viewport.

This Runtime lane asks one bounded scaling question:

> Can the exact current three-source Nature scene share one immutable proof-host Nature material resource across all three source meshes and both fixed observation contexts without changing exact retained pixels or renderer submission counters?

## Exact prerequisite

- receiving base: `mike-axiom-mir/axm-map-design` Environment PR #15 exact head `03e956475158a59d70cca08b73be23c141e4cb1f`;
- rear Nature source: `mike-axiom-mir/axm-nature-design@a4e5ee011e1d87f47866a7e6c6f4e66f57b6af12`;
- compact Nature source: `mike-axiom-mir/axm-nature-design@64116d63fc76daa1623b5fd5046a4e6074100bda`;
- west sapling source: `mike-axiom-mir/axm-nature-design@fbc202449981f2bac153951c561ed0ed6120c936`;
- Building source: `mike-axiom-mir/axm-building-design@4faa769b406bf3ad0ba9489a77141c27f122ce51`;
- Weather source: `mike-axiom-mir/axm-weather-design@ca2eaba519e8449835b0ea6ef944b7080c3caa6a`;
- proof renderer: pinned Godot 4.7.2 GL Compatibility.

The Environment PR #15 candidate payload is rebuilt through its existing source-owned builder before Runtime observation. Runtime does not author or move Nature, Building, Weather, Map, camera, path, lighting, or Object state.

## Compared modes

`per_mesh_material_control` intentionally reproduces the current observation-host behavior for Nature source meshes: one visually identical `StandardMaterial3D` is constructed per Nature mesh each time a fixed-camera viewport is built.

`shared_nature_material` creates the same material values once and reuses that immutable resource for every Nature source mesh and both sequential fixed-camera viewport builds.

The control is a bounded measurement reference. It is not a claim about a shipped product path.

## Acceptance gate

For this exact scene, a PASS requires:

- exactly three Nature source meshes in each context;
- control: three distinct Nature material identities per context and six Nature material constructions across the two contexts;
- candidate: one Nature material identity per context, the same identity across both contexts, and one Nature material construction total;
- exact source rows equal except for the deliberately changed material resource identity;
- exact draw-call, visible-object and renderer-primitive counters equal per context;
- control/candidate PNG bytes identical for `path_eye` and `elevated_oblique`.

Buffer/texture memory counters are retained as observations but are not an acceptance gate because Godot's exposed counters do not provide a complete material-resource residency measurement.

## Visual tradeoff handoff

If both fixed-camera image pairs are byte-identical, Runtime records:

`NONE_OBSERVED_IN_EXACT_RETAINED_PROOF_FRAMES`

That means only that material-resource sharing itself did not alter these exact proof frames. It is not final Art Direction approval of the underlying Nature forms, proof material, lighting, or scene.

## Reuse boundary

This is the first current multi-source static Nature sharing case. Together with the existing stable Weather resource and moving-sapling resource-reuse evidence, it strengthens a receiving-host rule: identical immutable renderer resources should be shared when source semantics do not require per-instance mutation.

It does **not** justify a Universal Creation runtime organ or a global material registry yet. The exact material here is a Map proof-host representation, not a source-owned final Nature material system.

## Non-claims

A PASS does not establish target-device FPS, GPU timing, VRAM, mobile/browser/console budgets, production allocator behavior, LOD or streaming policy, final materials/textures/shaders, dynamic batching/instancing, deformation cost for the compact/rear trees, collision/navigation/gameplay, final Art Direction, CANON, production readiness, or Runtime / Optimization mastery.

The four AXM roots remain the merge gate. `axm-create-me` remains coordination-only.
