# Environment Nature leaf flutter — current-world receiving 001

## Scope

This Environment / World Art follow-on stays on existing Map PR #24. It receives one already-proven Nature VFX source candidate into the exact current multi-asset world rather than opening another VFX or Geometry lane.

Exact parent: Environment Nature split surface-culling head `10c6e29790b0b53b20abd603738cb54671af013c`.

Exact VFX owner: Nature PR #11 head `ecade64227ba1d3d1faf029ca7188ea63c2560ec`, result `PASS_BOUNDED_DETERMINISTIC_LEAF_FLUTTER_SOURCE_CANDIDATE`.

Geometry context only: Nature Geometry PR #10 head `da3adbef4de8cddb8f3ebe841d39bb31a8936f5f`. Its explicit 490v/620t backface candidate is rebuilt only to recover the VFX owner's exact 390v/570t front-source phases. Environment does **not** adopt that explicit-backface representation.

## Receiving rule

For each of the existing 17 current-world states:

1. rebuild the exact VFX leaf-flutter donor;
2. verify the current-world sapling is the donor's no-flutter front mesh plus the already-authored stable Map translation;
3. take only the donor candidate's first 390 front-source vertices and first 570 source triangles;
4. require every changed front vertex to belong to the existing foliage surface domain;
5. preserve the accepted `woody=CULL_BACK / foliage=CULL_DISABLED` receiver policy;
6. preserve Building, indexed Object, visible footprint cue, static Nature, Weather, route, cameras and lighting;
7. require exact source and rendered identity at phase 0 and phase 16;
8. compare all 68 retained current-world frames and retain the observed pixel deltas for Art Direction / Visual QA rather than auto-accepting motion quality.

## Evidence gate

A PASS must establish:

- exact VFX source head and Geometry context head bound;
- exact 17 source phases aligned with current-world state time;
- no non-foliage vertex receives the flutter delta;
- maximum current-world added vertex displacement stays inside the VFX owner's `0.0085 m` cap;
- exact rendered neutral endpoints across both cameras and both Weather presentations;
- renderer-visible interior motion in both fixed current-world cameras;
- all 1,224 inherited Weather width measurements remain valid;
- no proof-host draw/object/primitive/buffer/texture counter change.

## Ownership / truth boundary

Map / Environment owns only receiving composition. Nature VFX retains motion-source authority. Nature Geometry retains topology authority. Materials and Art Direction retain shaded appearance and preference. Visual QA retains independent perceptual review. Runtime retains timing/cost and target-device acceptance.

A PASS does not prove natural flutter, physical wind, continuous wall-clock playback, final shaded backface response, arbitrary-view equivalence, target-device performance, gameplay, CANON, production readiness or Environment mastery.
