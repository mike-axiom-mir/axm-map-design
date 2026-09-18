# Environment Weather Source-Width Temporal Exposure — Source-Cadence Review 001

Status: EXPERIMENTAL VFX REVIEW SURFACE

This review-only follow-on stays inside Map PR #25. It does **not** create another Weather presentation variant. The exact single-tap source-width control remains the current visual reference, and the exact opacity-normalized two-tap candidate at `dd4a85223ba70f7086db2fdc292e4cb57ac38e47` remains unchanged.

## Gap

The normalized candidate has deterministic still-frame A/B evidence, but Art Direction 041 correctly held it as a preferred presentation because the current evidence does not demonstrate meaningful perceptual temporal gain. The previous review surface samples nine deterministic phases at 62.5 ms spacing; that is useful for spatial readability but is not a viewer-facing review of the complete authored 31.25 ms source cadence.

The bounded question here is therefore only:

> Can the unchanged single-tap reference and unchanged normalized two-tap candidate be captured through the same real Godot receiver at all 17 authored source-evaluation phases and retained as an exact, one-shot A/B sequence for human temporal review without retuning the effect?

## Review surface

The proof captures both existing fixed `1100×720` cameras at every authored source phase:

`0, 31.25, 62.5, …, 500 ms`.

For each phase it retains:

- the exact single-tap source-width control;
- the exact opacity-normalized two-tap candidate;
- the current source bracket and the candidate's `15.625 ms` lagged bracket;
- normalized opacity rows for all 36 source streaks;
- source-width projection receipts;
- direct PNG and RGBA8 frame identities.

The candidate still uses `TWO_TAP_TRANSMITTANCE_NORMALIZED_RECEIVING_ONLY_TEMPORAL_EXPOSURE`. Weather source seed/state/width/opacity semantics, density, lighting, cameras, world composition, sapling motion, Runtime scheduling, gameplay and physics are unchanged.

The retained artifact also includes an offline HTML page that advances the exact frame pairs against a **nominal** 32 Hz clock for one-shot human review. It deliberately does not auto-loop, because the end-to-start seam is not part of the authored source sequence.

## Evidence boundary

A green proof may establish only that the real Godot proof receiver captured both unchanged presentations at every authored 31.25 ms source-evaluation phase with exact source-width/provenance and opacity-normalization contracts, and that those retained frames are available as a one-shot nominal-32-Hz review surface.

It does **not** establish:

- browser or display 32 Hz delivery;
- target-device frame pacing or performance;
- human-perceived smoothness;
- aesthetic superiority or Art Direction / independent Visual QA preference;
- physical wind, precipitation, airflow, pressure or fluid behavior;
- collision, damage, interaction or gameplay-event semantics;
- arbitrary camera / resolution / FOV equivalence;
- Runtime adoption;
- CANON;
- production or game readiness;
- VFX mastery.

Weather retains source semantics. Runtime retains scheduling/device authority. Art Direction and independent Visual QA retain perceptual acceptance. VFX owns only the bounded receiving presentation and truthful review evidence.

The four AXM roots remain the gate: Truth, Agency / non-domination, Continuity, Wisdom before speed.
