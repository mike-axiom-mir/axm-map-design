# Environment Atmosphere Sync 001

## Purpose

This VFX receiving proof tests one bounded cross-asset reactive relationship that was still unproven after the separate Nature-sway and Weather-sequence lanes: can the exact accepted sapling visual response and the exact source-owned Weather streak field be sampled on the same evidence clock and exact visual direction inside the same Environment scene without changing either source contract?

It deliberately does **not** create a physical wind system, force coupling, a generic VFX graph, new Weather semantics, a new Nature response, or a runtime performance policy.

## Exact prerequisites

- receiving VFX Weather sequence: `mike-axiom-mir/axm-map-design` PR #7 head `10f1152b73240d0755bb14fa1c7744da3c544355`;
- Nature visual response: `mike-axiom-mir/axm-nature-design` PR #2 head `cee14f5b3feea78b0adcd044bad2ea3c97657fc6`;
- Weather source: `mike-axiom-mir/axm-weather-design` PR #2 head `ca2eaba519e8449835b0ea6ef944b7080c3caa6a`;
- Weather semantics remain `VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED`;
- source Weather sequence schedule remains `0 / .0625 / .125 / .1875 / .25 / .3125 / .375 / .4375 / .5 s`;
- Nature response duration remains exactly `0.5 s` with the existing `0.18 m` maximum displacement ceiling;
- the existing fixed `path_eye` and `elevated_oblique` cameras remain unchanged.

## Contract

`axm.environment-atmosphere-sync-proof-evidence/v0.1` builds the already-proven nine Weather receiving states first, then revalidates the already-accepted Nature response and samples that response at the exact same nine times.

For every state it requires:

- exact Weather field rows are preserved from the Weather-only control;
- exact visual-only semantics are preserved;
- Nature and Weather use the exact same source-owned visual direction;
- the sapling remains 390 vertices / 570 triangles;
- the existing receiving translation is preserved;
- path clearance and minimum spacing remain valid;
- sampled sapling displacement remains at or below `0.18 m`;
- static scene items, cameras, readable path, source integration and Weather presentation remain unchanged.

The first and last synchronized sapling states must return exactly to the neutral control geometry. The midpoint must differ from the neutral control.

## Target-host proof

The dedicated workflow renders all nine synchronized candidates through the existing pinned Godot 4.7.2 GL Compatibility Environment host. It also renders matched Weather-only controls at `0.0`, `0.25` and `0.5 s`.

The target-host gate requires:

- nine distinct synchronized images in each fixed camera;
- exact control/candidate image equality at `0.0 s`;
- visible control/candidate inequality at `0.25 s`;
- exact control/candidate image equality again at `0.5 s`.

This makes the bounded visual return falsifiable without inventing interpolation or using successful rendering as a claim of final atmosphere quality.

## Ownership and non-overlap

- Weather PR #2 continues to own streak semantics and source field behavior.
- Nature PR #2 continues to own the sapling visual response.
- Map VFX PR #7 continues to own the Weather-only sampled receiving sequence.
- Map Runtime PR #8 continues to own same-process resource reuse/update-cost evidence.
- Map VFX PR #9 continues to own source-opacity target-host fidelity.
- Environment owns composition; this proof does not retune placement or cameras.
- Art Direction / Visual Observer own perceptual acceptance.

The relationship introduced here is therefore only:

`SHARED_EVIDENCE_CLOCK_AND_EXACT_VISUAL_DIRECTION_NOT_PHYSICAL_COUPLING`.

## Truth boundary

A PASS establishes that these two already-authored visual effects can coexist on one exact sampled clock and direction in the bounded receiving scene with deterministic neutral return and preserved structural gates.

It does **not** establish physical wind or forces, turbulence, precipitation, volumetrics, continuous interpolation, live frame pacing, target FPS/GPU cost, collision, gameplay, final Art Direction, generic VFX architecture, UC extraction, CANON, production readiness, or VFX mastery.
