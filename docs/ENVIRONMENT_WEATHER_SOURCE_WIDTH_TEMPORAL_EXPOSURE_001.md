# Current-world Weather source-width temporal exposure candidate 001

## Scope

This is a receiving-only VFX presentation experiment stacked on the exact source-width + continuous-phase Weather path already proven in Map VFX PR #25.

It does not rewrite `axm-weather-design`, the source-owned seed `44021` layout, the 17 exact Weather states, source-authored streak width, current-world composition, sapling source motion, Runtime scheduling, gameplay, physics, Universal Creation, or `axm-create-me` product code.

## Why this candidate exists

Visual QA found that the existing continuous-phase interpolation math is source-bound and spatially clean, but the exact proof-host presentation still arrived in coarse enough intervals that frame-to-frame changes were materially larger than the authored 32 Hz sequence. Runtime then isolated inline evidence capture as a large proof-harness perturbation and still observed renderer/post-draw cadence above the authored 31.25 ms interval.

VFX should not take Runtime's scheduling or renderer-optimization lane. This experiment instead asks one narrower presentation question:

> Can one source streak be shown as a bounded two-tap temporal exposure, using the current continuous-phase position plus a 15.625 ms lagged continuous-phase position, without changing source width or exceeding the source opacity budget?

## Exact presentation rule

For every one of the 36 source streaks:

- current tap: exact continuous-phase interpolated Weather geometry at review phase `t`, at `0.5 ×` its interpolated source opacity;
- lagged tap: exact continuous-phase interpolated Weather geometry at `max(0, t - 15.625 ms)`, at `0.5 ×` its interpolated source opacity;
- both taps retain the exact source-authored `width_px` and use the already-proven camera-projected ribbon path;
- streak identity must match across the two taps;
- sapling geometry remains one current-phase interpolation only; no vegetation ghosting is introduced;
- combined weight is exactly `1.0`.

For equal source alpha `a`, two half-alpha layers have theoretical combined alpha `1 - (1 - a/2)^2 = a - a²/4`, which does not exceed `a`. When the two source opacities differ across the 15.625 ms lag, the observer compares the theoretical combined contribution against the larger of the two source values and fails closed on an over-budget result.

The source still contains 36 streaks. The receiver uses 72 presentation ribbons because each source streak has two explicitly paired exposure taps. That is presentation geometry, not a claim that Weather density doubled.

## Review sequence

The Godot 4.7.2 GL Compatibility observer evaluates deterministic, non-wall-clock review phases:

`0 / 62.5 / 125 / 187.5 / 250 / 312.5 / 375 / 437.5 / 500 ms`

in both fixed `1100×720` cameras:

- `path_eye`
- `elevated_oblique`

At every phase it retains:

1. single-tap continuous-phase control PNG + raw RGBA8 frame;
2. two-tap temporal-exposure candidate PNG + raw RGBA8 frame;
3. exact current and lagged source brackets/digests;
4. source-width projection residuals;
5. Weather/sapling resource identities;
6. explicit opacity-budget evidence.

The raw RGBA8 evidence lets the independent Python verifier measure exact candidate/control pixel deltas and inter-frame mean-absolute-RGB deltas without adding screenshot readback to a wall-clock timing claim. Those metrics are diagnostics for QA and Art Direction, not an automatic aesthetic gate.

## Expected bounded PASS

`PASS_BOUNDED_TEMPORAL_EXPOSURE_VISUAL_CANDIDATE` means only that:

- the exact source-width structure remains green;
- both cameras cover the exact review phases;
- current and lagged presentation taps bind adjacent exact source rows by digest;
- the two-tap opacity budget stays bounded;
- control has 36 and candidate has 72 exact source-width measurements per phase;
- all projected widths stay within the existing `0.05 px` tolerance;
- Weather/sapling receiving resources stay stable;
- PNG and RGBA8 evidence is retained and hash-bound;
- the candidate creates a direct visible delta after the initial clamped phase;
- rear-tree culling remains unchanged.

A deliberate opacity-weight drift is required to fail closed.

## Visual tradeoff / handoff

The candidate may soften visible temporal stepping by carrying a short history of the streak field, but it can also read as short ghosting or slightly broaden the apparent atmospheric footprint. The current Art Direction decision explicitly says not to increase atmosphere prominence, so the opacity split is deliberately conservative and source-bounded.

Visual Observer / QA and Art Direction still own whether the retained motion-exposure look is preferable or temporally equivalent enough. Runtime still owns cadence, draw/submission cost, renderer scheduling and target-device performance.

## Non-claims

Even with a green workflow this does **not** prove:

- authored 32 Hz wall-clock delivery;
- target-device FPS or GPU/CPU cost;
- final motion smoothness or aesthetic acceptance;
- physical wind, precipitation, turbulence or volumetric Weather;
- gameplay visibility, collision, damage or physics response;
- arbitrary cameras, resolutions, FOVs or renderers;
- CANON, production readiness or VFX mastery.

`axm-create-me` remains coordination-only. The four AXM roots remain the merge gate.
