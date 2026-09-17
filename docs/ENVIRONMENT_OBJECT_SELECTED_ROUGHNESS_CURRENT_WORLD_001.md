# Environment Object Selected Roughness — Current World 001

Status: bounded Environment appearance candidate; no automatic adoption.

## Purpose

Take the exact Materials-selected `service_dark` roughness field only after the current Map receiver has already proven exact source-surface segmentation and exact source-vertex -> TEXCOORD_0 identity. Bind that field to the two protected selected faces in the real Building + Nature + Object + footprint + Weather scene, then measure the resulting raster and proof-host runtime deltas without taking Art/QA or Runtime authority.

## Exact lineage

- parent Environment head: `4eed6da68f746ca2849c89fa88533f82bc836b26`;
- Object source head: `d3fa10a270faae7925811f44f03381fe5c5d0215`;
- Materials authority head: `0515a2d5ad2c7a1eb545f2b7b327b7367530dfca`;
- Technical Art authority head: `1bcdbae786e02f3ca46a89e4e0ff608d74f364b4`;
- exact selected R8 scalar SHA-256: `b8d13c07f9b71278042b0d42d44b84579a3f327c6adf6723cae4c8c8f06dd38e`;
- exact serialized PNG SHA-256: `57cf746a9a7e0615884fe3c45c6c4df677c2bd0631def61b3ccb1684daa26949`;
- exact Technical Art selected-surface spec SHA-256: `1f87a7b287c7caa138deee64b687d0aba67a3485ddeae6f80a38ebd906a86aec`.

Selected surfaces remain exactly:

- `lid_inner_service_surface`;
- `front_service_panel_outer_service_surface`.

## Receiver rule

`SPATIAL_MATERIAL_FIELD_MAY_ENTER_CURRENT_WORLD_REVIEW_ONLY_AFTER_EXACT_SURFACE_AND_UV_IDENTITY__APPEARANCE_AND_RUNTIME_ACCEPTANCE_REMAIN_SEPARATE`

The candidate reuses the exact seven-surface parent mesh arrays. Only the two selected faces receive the selected roughness texture through their already-proven UV0. Their current receiver albedo and metallic values remain unchanged. Non-selected surfaces receive no roughness texture.

This deliberately tests the spatial roughness field only. It does not reinterpret Object source ownership or turn the selected field into production texture art.

## Evidence gate

The dedicated workflow must:

1. bind and hash the exact parent Environment evidence, Object/Materials/Technical-Art donors and selected field;
2. rerender the retained 17-state / 68-frame Godot 4.7.2 current world;
3. compare every candidate frame against the exact UV0-only parent;
4. recheck all 1,224 inherited Weather projected-width measurements;
5. require draw calls, objects and primitives to remain unchanged versus the exact UV0-only parent;
6. report buffer/texture-memory deltas as proof-host measurements without calling them target-device acceptance;
7. reject a mutated selected-field PNG fail-closed;
8. keep `environment_adoption=false` regardless of whether the field is visibly resolved.

A visible >1-LSB raster delta yields a review-ready appearance candidate. A no->1-LSB result remains a truthful visibility HOLD rather than being promoted by intent.

## Ownership boundary

- Object owns source geometry and surface semantics.
- Materials owns the selected roughness field identity/meaning.
- Technical Art owns UV/channel/transport evidence.
- Environment owns assembled-world receiving and composition evidence.
- Runtime owns cost/device acceptance.
- Art Direction and independent Visual QA own appearance acceptance.
- `axm-create-me` remains coordination-only.

No CANON, production-readiness or mastery claim follows from this proof.
