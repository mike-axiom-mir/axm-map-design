# Environment Weather Source-Width Temporal Exposure — Opacity-Normalized Candidate 001

Status: EXPERIMENTAL VFX RECEIVING PROOF

This follow-on stays inside Map PR #25 and preserves the previous half-opacity temporal-exposure result as historical evidence. It addresses one bounded Visual-QA defect only: at zero lag, two half-opacity coincident taps did not reproduce the single-tap source opacity, so lower inter-frame RGB change was confounded by static dimming.

## Candidate

Policy: `TWO_TAP_TRANSMITTANCE_NORMALIZED_RECEIVING_ONLY_TEMPORAL_EXPOSURE`

For each authored Weather streak, the receiver still presents two source-bound taps: current continuous-phase state and a source-bound sample lagged by at most `15.625 ms`. Source `width_px`, streak identity, source brackets and Weather authority remain unchanged. Sapling deformation stays single-phase.

Instead of multiplying source alpha directly by `0.5`, each tap maps source alpha `a` to a half-weight transmittance contribution:

`tap_alpha = 1 - (1 - a)^0.5`

For coincident equal-source taps this gives:

`1 - (1 - tap_alpha)^2 = a`

so zero-lag presentation reconstructs the original source alpha rather than introducing static attenuation. For unequal adjacent source alphas, the combined alpha remains bounded by the larger source alpha.

## Exact bounded proof

The proof reuses the same 17 exact Weather source states, two fixed `1100×720` cameras and deterministic review phases used by the earlier temporal-exposure candidate. It retains control/candidate PNG and raw RGBA8 frames, source/provenance brackets, per-streak opacity rows, projected-width measurements and resource identity.

The independent verifier requires:

- the previous source-width / source-bracket / retained-frame contract to remain green;
- 36 retained per-streak opacity rows for every review sample;
- each current/lagged tap alpha to match the transmittance-exponent formula;
- combined alpha never to exceed the larger of the two source alphas;
- equal-source taps to reconstruct source alpha within `1e-9`;
- exact zero-lag source identity at phase `0 ms`;
- direct phase-0 candidate/control brightness equivalence inside narrow pixel bounds, including signed-luma balance;
- a deliberate normalization mutation to fail closed.

## Ownership and non-claims

Weather remains source authority. Map/VFX owns only this receiving/presentation experiment. Runtime retains cadence, renderer cost and target-device performance. Visual Observer / QA and Art Direction retain perceptual smoothness, ghosting and atmosphere-prominence acceptance.

A PASS does not establish authored `32 Hz` delivery, human-perceived smoothness, final VFX aesthetics, target-device performance, arbitrary-camera/resolution equivalence, physical wind/precipitation, gameplay/physics behavior, CANON, production readiness or VFX mastery.

The four AXM roots remain the merge gate: Truth, Agency / non-domination, Continuity, Wisdom before speed.
