# Environment Object selected UV0 current-world receiver 001

## Bounded question

Can the exact UV0 / TEXCOORD_0 identity already proven by Object Technical Art be received on the two source-owned service faces that Environment just made independently addressable, **without** changing any material, texture, geometry, weather, nature or other world pixels?

This is intentionally a UV-receiving pass, not a selected-roughness appearance pass.

## Pinned authority

- parent Environment segmentation head: `8856745aa0f3de626599afa35fe16a92ae68fa50`;
- Technical Art PR #28 head: `1bcdbae786e02f3ca46a89e4e0ff608d74f364b4`;
- Technical Art selected-roughness semantic workflow: `35207908611`;
- retained TA artifact: `10490650986`, SHA-256 `0e24efcbfefb129ef24c153b50020ac321a9789dbf8c148794dfc45f5c9f5f90`;
- exact two-surface TA spec SHA-256: `1f87a7b287c7caa138deee64b687d0aba67a3485ddeae6f80a38ebd906a86aec`;
- Materials authority head: `0515a2d5ad2c7a1eb545f2b7b327b7367530dfca`;
- Materials selected scalar identity: `b8d13c07f9b71278042b0d42d44b84579a3f327c6adf6723cae4c8c8f06dd38e`.

The TA donor provides exact source-surface position/UV pairs. Environment consumes those pairs only on:

- `lid_inner_service_surface` — source triangles `[12,13]` — receiver surface 1;
- `front_service_panel_outer_service_surface` — source triangles `[28,29]` — receiver surface 3.

## Receiving method

The observer starts from the accepted seven-surface Environment segmentation receiver. It does not reconstruct either selected face from a new primitive. Instead it:

1. keeps the parent segmented vertex, normal and index arrays;
2. finds the four referenced receiver vertices on each selected two-triangle face;
3. matches those positions against the exact four Technical-Art source-surface positions with a maximum allowed positional residual of `1e-6 m`;
4. attaches the exact matching Technical-Art TEXCOORD_0 value to each receiver vertex;
5. leaves all unused UV slots at deterministic zero;
6. leaves UV0 absent on all five non-selected receiver surfaces;
7. reuses the exact existing material objects unchanged.

No selected roughness texture is bound in this pass.

## Required evidence

A valid PASS requires:

- both selected surfaces match all four TA corners exactly once;
- the Object remains 7 surfaces / 812 triangles;
- UV0 exists only on the two selected faces;
- selected roughness and Environment adoption remain false;
- the retained 17-state Building + Nature + Object + footprint + Weather scene rerenders to 68/68 byte-identical frames versus the segmentation parent;
- all 1,224 Weather projected-width observations remain within the existing `0.05 px` gate;
- a mutated TA UV donor is rejected fail-closed.

## Reusable Environment rule

`EXACT_RECEIVER_UV_BINDING_MUST_MATCH_PINNED_SOURCE_SURFACE_POSITION_TO_TEXCOORD_IDENTITY_BEFORE_SPATIAL_MATERIAL_FIELD_REVIEW`

A renderer can attach a spatial material field only after the receiving geometry has an exact, provenance-bound coordinate identity. A matching material name or equal texture digest is not enough.

## Non-claims

This pass does not approve the selected roughness appearance, production UV authoring, a final atlas/storage representation, tangent-space production quality, Runtime/device cost, Art Direction / Visual QA acceptance, CANON or production readiness. Object source authority remains in Object; Map owns only receiving composition evidence. `axm-create-me` remains coordination-only.
