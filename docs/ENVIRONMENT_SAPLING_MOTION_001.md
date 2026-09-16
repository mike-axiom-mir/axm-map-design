# Environment Sapling Motion 001

Status: EXPERIMENTAL VFX / RECEIVING-SCENE EVIDENCE ONLY.

## Purpose

Prove whether the exact locally accepted Nature sapling response survives the existing seed-29 Environment composition without changing placement, cameras, source-owned Weather, proxy state, proof material, or the 0.180 m response ceiling.

This lane stacks on `axm-map-design` PR #4 exact head `d52cb54a2aeb3eb4f5668e3d6ba4b05ddcc02899` and consumes:

- Nature source head `fbc202449981f2bac153951c561ed0ed6120c936`;
- Nature VFX head `cee14f5b3feea78b0adcd044bad2ea3c97657fc6`;
- retained Nature VFX artifact `10429159566`;
- Weather source head `ca2eaba519e8449835b0ea6ef944b7080c3caa6a`;
- Art Direction decision `PASS_ART_DIRECTION_LOCAL_SWAY_HIERARCHY_001 / RELEASE_TO_SCENE_INTEGRATION`.

## Bounded comparison

Only the sapling vertex state changes:

- neutral: `0.000 s`;
- peak: `0.250 s`.

The response remains `HIERARCHICAL_TRUNK_BRANCH_LEAF_HALF_SINE_VISUAL_SWAY`, visual-only, with the exact 0.180 m maximum displacement ceiling. The source-local neutral mesh is translated into the exact receiving placement; the same translation is applied to the peak mesh. No scale, rotation, placement retune, material candidate, gust, turbulence, inertia, physics, or gameplay semantics are introduced.

Both states retain the exact fixed Environment cameras:

- `path_eye`;
- `elevated_oblique`.

The exact 36-streak Weather field remains a 3.0 m render-presentation plane and is not physical altitude.

## Gates

The receiving proof fails closed unless:

- the Environment source integration still passes;
- exact Nature source, Nature VFX, and Weather checkout heads match;
- VFX neutral topology matches the already placed Environment sapling topology;
- Environment placement is a pure translation of the source-owned sapling;
- the peak keeps that exact placement transform and topology;
- the maximum neutral->peak vertex displacement is exactly the declared 0.180 m ceiling within tolerance;
- neither neutral nor peak sapling AABB intrudes into the declared readable path;
- cameras, Weather field, proxies, and proof-material truth boundary remain unchanged.

Pinned Godot 4.7.2 GL Compatibility then captures neutral and peak from both fixed cameras.

## Truth boundary

A PASS proves only that these exact neutral and peak states can be reconstructed from exact source/VFX provenance, remain inside the receiving path constraint, and render in the pinned proof host from the existing cameras. Direct visual review is still required to decide whether the moving sapling steals focus, worsens the oblique hierarchy issue, or introduces scene-level silhouette/overlap defects.

It does not prove physical wind, continuous runtime playback quality, lag/inertia/overshoot, shaded production deformation, self-intersection freedom, final materials, final world art, runtime budgets, gameplay, collision, CANON, production readiness, or VFX mastery.

The four AXM roots remain the merge gate.
