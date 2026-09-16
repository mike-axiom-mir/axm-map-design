# Runtime Weather temporal-exposure budget 001

This Runtime / Optimization lane stacks exactly on VFX PR #25 head `92cfe5d0dc7e254c1c3e19c5fc168298dea3493a`, where the VFX owner has already proven the optional receiving-only policy `TWO_TAP_HALF_OPACITY_RECEIVING_ONLY_TEMPORAL_EXPOSURE` at deterministic review phases.

## Bounded question

The VFX candidate keeps 36 source Weather streaks but renders 72 receiving ribbons: a current continuous-phase tap plus a 15.625 ms lagged tap at half interpolated source opacity. VFX explicitly leaves target/runtime cost unclaimed.

Runtime asks only:

> What proof-host submission, observed memory and Weather-preparation cost is added by carrying 72 receiving ribbons instead of the same 36-ribbon continuous-phase control when both use the same mutable Weather mesh/material/node and the same exact source phases?

## Measurement contract

The exact parent VFX retained artifact is consumed by identity rather than regenerated or relabelled. Its visual candidate result remains VFX-owned.

Two fresh Godot 4.7.2 GL Compatibility processes then run the same nine deterministic review phases and both fixed cameras:

- `single_tap_control`: 36 source-width ribbons from the exact current continuous-phase sample;
- `two_tap_temporal_exposure`: the same current phase plus the exact VFX-owned lagged phase, 72 receiving ribbons total.

The measurement loop performs no image readback or PNG encoding. That preserves Runtime PR #31's proven observer-separation rule instead of reintroducing screenshot cost into timing evidence.

For each phase/context the receipt retains:

- exact current and lagged source brackets/digests;
- 36 source streaks and exact 36/72 receiving streak counts;
- projected source-width residuals;
- stable Weather and sapling resource identities;
- Weather preparation/build/fill microseconds;
- post-draw wait microseconds;
- RenderingServer draw, object, primitive, buffer-memory and texture-memory observations.

A deliberate candidate presentation-count mutation must fail closed.

## Ownership / visual tradeoff

Runtime changes no Weather source row, interpolation rule, opacity budget, lag, VFX look or Art Direction preference. The exact VFX parent retains direct A/B visual evidence and reports lower deterministic inter-frame mean-absolute-RGB medians with a small Weather-local visual delta, while explicitly holding possible short ghosting / broader atmospheric footprint for Visual QA and Art Direction.

Runtime will not collapse the two taps or change their opacity to save cost. If this representation is visually preferred later, any lower-cost representation must be a separate bounded experiment with independent visual equivalence evidence.

## Expected scoped outcome

The workflow is evidence-gated. A green result may claim only:

`PASS_TWO_TAP_TEMPORAL_EXPOSURE_RUNTIME_COST_CHARACTERIZED`

with decision:

`HOLD_PERFORMANCE_NEUTRALITY__TWO_TAP_RECEIVING_COST_IS_NONZERO`

Exact measured values belong to the retained target-host report and must not be guessed into this document before the real run completes.

## Non-claims

This lane does not establish authored 32 Hz delivery, target-device CPU/GPU frame time, FPS, VRAM/heap residency, arbitrary cameras/resolutions, physical Weather, gameplay, final VFX preference, VFX adoption, CANON, production readiness, or Runtime mastery.

`axm-create-me` remains coordination-only. The four AXM roots — Truth, Agency / non-domination, Continuity, Wisdom before speed — remain the merge gate.
