# Current-world Weather source-width proof

Status: **EVIDENCE-GATED / DO NOT PRE-CLAIM PASS**

This VFX lane stacks exactly on Map VFX PR #22 head `e482d003853e52fc835f1797ddfb6506a50083ef`.

## Gap

The Weather source already owns one screen-pixel presentation width per streak (`width_px`, authored deterministically in the exact Weather PR #3 seeded family), and the source-local SVG evidence uses that value directly as stroke width. The strongest current Map target-host path retains opacity, streak identity, layout, motion, the west-sapling response and rear-tree culling, but explicitly reports `SOURCE_WIDTH_PX_NOT_MAPPED_TO_3D_LINE_WIDTH_IN_THIS_PROOF`.

This lane closes only that presentation-fidelity gap for the exact source-owned seed `44021` and the two already-fixed `1100x720` Map proof cameras.

## Bounded approach

- rebuild exact Map PR #22 from its pinned donors at its exact head;
- rebuild exact Weather PR #3 seed `44021` and bind all 36 source-authored `width_px` values by exact streak ID/order;
- preserve every parent Weather line field, all 17 Weather-field identities, all 17 west-sapling mesh identities, static world state, source opacity and rear-tree culling;
- compare the inherited renderer-default `PRIMITIVE_LINES` control with a candidate camera-projected ribbon representation;
- for each endpoint, construct the ribbon edge from the fixed camera's screen projection and `Camera3D.project_position`, so the candidate's measured projected cross-section targets the exact source width in pixels;
- retain all 17 states in both fixed cameras for both control and candidate (68 PNGs total);
- report proof-host draw/object/primitive counters as observations, not as Runtime acceptance.

## Ownership boundary

Weather keeps ownership of its stochastic layout, visual direction/speed semantics, opacity and source width. Map owns only this receiving proof. No Weather rule is copied into Universal Creation, no Environment composition is changed, and `axm-create-me` remains coordination-only.

The ribbon is a proof-host presentation representation. It is not a physical precipitation diameter, volumetric primitive, gameplay visibility contract, renderer-independent solution, or target-device performance policy.

## Exact evidence gate

The dedicated workflow must establish both:

- `PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE`; and
- `PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_TARGET_HOST`.

The live gate requires all 17 states, both fixed cameras, all 36 streak widths per state/camera, one stable Weather resource identity, one stable sapling resource identity, preserved rear-tree `CULL_BACK`, retained A/B frames, stable per-camera control/candidate counter sets, and maximum projected width residual no greater than `0.05 px`.

Until that exact-head workflow is green, this lane remains implemented/queued rather than PASS.

## Non-claims

Even after a scoped PASS, this lane does not establish arbitrary camera or resolution fidelity, renderer-independent line/ribbon semantics, wall-clock playback, target-device FPS/GPU/VRAM/overdraw budgets, physical wind or precipitation, gameplay visibility/collision/damage, final Art Direction / Visual QA acceptance, CANON, production readiness, or VFX / Atmosphere mastery.

The four AXM roots remain the merge gate: Truth, Agency / non-domination, Continuity, and Wisdom before speed.
