# Environment Object selected-surface segmentation receiver 001

## Scope

This is a bounded receiving-only change on existing Environment PR #24. The current five-material Object receiver is split only enough to make the two source-owned selected service faces independently addressable in the assembled Map world.

Source-owner correspondence is already proven at Environment head `be4e0dbf245c4658c48b902024cf397cc6557b5f`:

- `lid_inner_service_surface` = source triangles `[12,13]`;
- `front_service_panel_outer_service_surface` = source triangles `[28,29]`.

The receiver keeps the exact current material family and preserves parent emitted vertex positions and generated normals. It reuses the exact same parent material objects. No UV0/TEXCOORD_0 stream and no selected roughness texture are added.

## Receiver partition

The five material surfaces become seven independently addressable receiver segments while retaining five unique materials:

- `shell_coating_remainder` — 22 triangles — `shell_coating`;
- `lid_inner_service_surface` — 2 triangles — `shell_coating`;
- `service_dark_remainder` — 10 triangles — `service_dark`;
- `front_service_panel_outer_service_surface` — 2 triangles — `service_dark`;
- `hardware_steel` — 656 triangles;
- `rubber_guard` — 96 triangles;
- `interface_orange` — 24 triangles.

Total host coverage remains exactly 812 triangles.

## Evidence requirement

The dedicated workflow rerenders the same 17-state Building + Nature + indexed Object + footprint + Weather world in pinned Godot 4.7.2 and compares all 68 frames against the preceding five-surface receiver-readiness artifact. All 1,224 Weather projected-width observations must remain inside the existing `0.05 px` gate.

The intended narrow success state is:

`PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACES_INDEPENDENTLY_ADDRESSABLE__UV0_AND_SELECTED_ROUGHNESS_ADOPTION_HELD`

A PASS means only that exact selected-face segmentation survives the real receiving composition without changing the retained pixels. It does not mean the selected roughness is ready to adopt.

## Next owner boundary

The next legitimate receiving step is exact UV0/TEXCOORD_0 binding for those two source-owned selected surfaces under Materials / Technical-Art authority. Only after that should Environment render the selected roughness in the full world.

Runtime owns cost/device acceptance for the additional receiver surfaces. Art Direction and independent Visual QA own appearance acceptance once a textured current-world receiver exists.

## Non-claims

No Object source geometry, source-surface semantics, source frames, source metric domains, material values, UVs, texture values, Building, Nature, Weather, route, camera, lighting, gameplay, Runtime policy, CANON or production-ready claim is authored here. `axm-create-me` remains coordination-only and the four AXM roots remain the merge gate.
