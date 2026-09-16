# Environment current-world Nature material-family integration 001

## Question
Can the exact Materials-owned three-source woody/foliage family be received by the current full Map world without changing Nature form, motion, placement or current proof culling, while keeping the accepted Building header segmentation, Object+dressing, Weather source-width presentation, path, cameras and lighting fixed?

## Exact donors
- Environment parent implementation evidence: `dfd4e1d662ab7d6d9f1a5c8dd35b571418154f6e` / composition `073aaba4066f223be2f298d631550acb724c30f6b17ee1d51a285e4d2bbeb8b2`.
- Parent review/ancestry surface: `bd065c8ee23ddee922c4aa9b4aa6e3d9504ffb06`.
- Nature Materials: `8b2e0523d7a2b210c6404f15bafb08fbedcad4dd` / `nature-woody-foliage-family-001`.
- Nature geometry reference: `da3adbef4de8cddb8f3ebe841d39bb31a8936f5f`.

The geometry reference is used only to recover exact source-owned triangle-region membership. Receiver geometry is not replaced. Winding may remain the current receiver lineage, which is important because the live world currently carries different accepted culling/topology histories for sapling, compact east tree and migrated rear tree.

## Bounded change
The family attaches exactly two material roles to all three current Nature identities:
- `woody`: `#5C3B27FF`, metallic `0.0`, roughness `0.84`;
- `foliage`: `#5A823EFF`, metallic `0.0`, roughness `0.58`.

Each 390-vertex / 570-triangle source is partitioned from source-owned region metadata into 520 woody triangles and 50 foliage triangles. The dynamic sapling keeps its exact 17-state deformation sequence. Static compact/rear trees keep their current placement and triangle membership. Existing proof culling is preserved rather than using this Environment pass to choose a new leaf-sidedness strategy.

## Evidence gate
CI must retain:
- exact structural composition packet and fail-closed controls;
- Godot 4.7.2 GL Compatibility runtime receipt;
- all 68 candidate frames (17 states × 2 cameras × 2 inherited Weather modes);
- direct exact-frame comparison against the retained segmented-Building parent;
- inherited 1,224 Weather source-width measurements;
- runtime counter deltas as diagnostics for Runtime review.

## Truth boundary
A PASS establishes only this exact receiving composition and its direct fixed-camera consequence. It does not establish final Nature material preference, final leaf sidedness, UV/texture/subsurface/transmission quality, physical botanical correctness, arbitrary-camera equivalence, target-device performance, gameplay, CANON, production readiness or Environment mastery.
