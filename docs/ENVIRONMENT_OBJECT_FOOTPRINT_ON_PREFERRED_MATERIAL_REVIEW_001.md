# Environment — Object footprint cue on preferred material review 001

## Bounded question

The current Environment world already carries two independently useful Object changes:

1. the Map-owned west receiver-footprint cue from Environment head `a29aa1e3d2260e8eb5ab2ac78a95d35ce131214c`; and
2. the exact five-surface Object material family now preferred by 3D Art Direction at current-world head `6575cc38db9f0f62b14a82b352d8582edf89856d`.

Art Direction explicitly preferred the Object material family **without independently accepting the footprint cue** and kept the historical small-source scale/readability question open. The older footprint A/B was made against the pre-Object-material world, so it is not sufficient by itself to decide the cue in the current preferred visual context.

This review closes only that evidence gap.

## Review contract

No new product/world composition is authored. The exact current-world payload and exact retained current-world frames from Environment artifact `10466065113` are the parent.

A proof-only observer runs the same world twice:

- `CONTROL_HIDDEN`: the existing footprint mesh is still created with the exact same geometry/material/resource residency, but its `visible` flag is false;
- `CANDIDATE_VISIBLE`: the exact existing footprint mesh remains visible, reproducing the current world.

Everything else is held fixed: Object geometry/transform/scale/material family, Building, Nature, Weather, route, cameras and lighting.

The candidate-visible run must reproduce all 68 retained current-world frames exactly. The hidden-vs-visible delta must remain inside the already-projected footprint bounds. This makes the review attributable to cue visibility rather than a source/material/composition rebuild.

## Evidence gate

The dedicated workflow must establish:

`PASS_CURRENT_WORLD_OBJECT_FOOTPRINT_ON_PREFERRED_MATERIAL_REVIEW_READY`

with:

- exact current-world head `6575cc38db9f0f62b14a82b352d8582edf89856d`;
- exact composition digest `677dfe17afe49bf3f6edc28359c40a8add3dc357cb918529f0015a99f71baf70`;
- exact Object source + five-surface material authority;
- 68/68 candidate-visible frames pixel-identical to retained current-world evidence;
- 68/68 cue visibility deltas localized to projected dressing bounds;
- the historical cue extent preserved at 161 changed pixels in `path_eye` and 106 in `elevated_oblique`;
- all 1,224 source-width Weather observations still within the inherited `0.05 px` gate.

## Ownership / handoffs

- **Environment / Map:** owns the footprint cue and this receiving comparison.
- **Object:** retains source geometry, scale, material semantics and all mechanical authority.
- **3D Art Direction + Visual Observer / QA:** decide whether the cue should remain preferred now that it can be judged against the preferred Object material family.
- **Runtime / Optimization:** prior cue creation-cost evidence remains historical; this visibility A/B intentionally keeps cue resource residency present in both modes and is not a replacement target-device budget.
- **Building / Nature / Weather:** unchanged.
- **Universal Creation / Profession Fabric:** unchanged; one scene-specific receiver cue does not justify extraction.
- **axm-create-me:** coordination/status only.

## Truth boundary

A PASS makes the exact current-world footprint cue review-ready and attributable. It does not grant final visual preference, alter Object scale, create gameplay/service-zone semantics, prove target-device performance, establish arbitrary-camera equivalence, authorize CANON, or imply production readiness.
