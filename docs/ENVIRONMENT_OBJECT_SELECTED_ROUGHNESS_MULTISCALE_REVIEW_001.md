# Environment Object Selected Roughness Multiscale Review 001

## Purpose

The exact selected-roughness current-world candidate is already structurally and visually observable in the retained Godot scene, but its change is intentionally small in the two fixed composition cameras. This review pass adds a reusable **derived inspection surface** without changing the scene, cameras, lights, source assets, UVs, materials, Weather, or adoption state.

The goal is not to make the roughness look stronger. The goal is to let Art Direction and independent Visual QA inspect the exact same full-scene evidence at three scales:

1. original full current-world frame;
2. Object-neighborhood crop;
3. selected-surface-local crop plus an explicitly amplified absolute-difference diagnostic.

## Exact evidence identity

Source Environment head:

`d8a1d950ed5f21e6ad356404f46407c99c160017`

Source state:

`PASS_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_APPEARANCE_CANDIDATE_REVIEW_READY__ENVIRONMENT_ADOPTION_HELD`

Exact UV0-only parent evidence:

- artifact `10501901585`;
- SHA-256 `a3e3c3adc794877d84f3735f4f4ff69e3120843588da5c8aaa259d7ab7b965e3`;
- parent Environment head `4eed6da68f746ca2849c89fa88533f82bc836b26`.

Exact selected-roughness candidate evidence:

- workflow `35235994153`;
- artifact `10502588586`;
- SHA-256 `60c1e589e3e1c3a7dab5430b55ef59542dd7ca35dad8b13653d165c79eee3a1e`.

The retained real scene contains Building + Nature + indexed Object + visible footprint cue + Weather across 17 states and two fixed cameras / two retained presentation modes for 68 matched frames.

## Frozen raster facts

The review must reproduce, not reinterpret:

- `6,426` raw changed pixels across all 68 frames;
- `1,666` pixels above 1 LSB;
- maximum channel delta `7 LSB`;
- `path_eye` raw change envelope `x=314..342, y=440..448`;
- `elevated_oblique` raw change envelope `x=549..559, y=307..313`;
- all `1,224` inherited Weather projected-width measurements retained, with source evidence maximum residual `0.00974698571769128 px` under the existing `0.05 px` gate.

A review run fails closed if the exact A/B raster change escapes those already-observed localized envelopes. This is a provenance/localization gate, not a universal aesthetic threshold.

## Derived review output

Representative states are `00`, `08`, and `16` for both retained modes and both fixed contexts. Twelve review sheets are generated. Each sheet contains:

- parent full scene;
- candidate full scene;
- candidate neighborhood crop;
- parent local crop;
- candidate local crop;
- absolute RGB difference multiplied by `32` for diagnostic visibility.

The amplified panel is explicitly diagnostic. It is never treated as the desired look and does not replace the original frame.

## Reusable rule

`SUBTLE_WORLD_SURFACE_CHANGE_REVIEW_SHOULD_PRESERVE_FULL_SCENE_AUTHORITY_AND_ADD_DERIVED_MULTI_SCALE_INSPECTION_WITHOUT_REAUTHORING_CAMERA_LIGHT_OR_ASSET_STATE`

This is useful for small material, decal, wear, wetness, or surface-response changes that are real in a world scene but difficult to inspect at gameplay composition scale. The full frame remains authority; local crops and amplified differences are derived review aids only.

## Ownership and holds

Environment owns the review composition/evidence surface only.

- Object / Materials retain source and material meaning.
- Technical Art retains exact transport/UV identity.
- Runtime retains representation and target-device acceptance.
- Art Direction and independent Visual QA retain appearance preference/acceptance.
- `environment_adoption=false` remains unchanged.
- The exact UV0-only receiver remains rollback/default until the separate owner gates permit otherwise.

No new camera, light, Object scale, roughness value, texture, UV, geometry, Weather state, Nature state, Building state, footprint state, route state, gameplay behavior, CANON, or production-readiness claim is created by this review pass.

The four AXM roots remain the merge gate: Truth; Agency / non-domination; Continuity; Wisdom before speed.
