# Environment selected-roughness + compact-east visual attribution 001

## Scope

This is an Environment / World Art receiving-evidence improvement on the existing Map Environment lane. It changes no scene source, Object material value, Nature/VFX response, Weather source, camera, light, Runtime representation, gameplay state, Universal Creation product code or `axm-create-me` product code.

It consumes three exact retained **real Godot current-world** artifacts that already passed their owner gates:

1. UV0-only Object parent: Map head `4eed6da68f746ca2849c89fa88533f82bc836b26`, artifact `10501901585`, SHA-256 `a3e3c3adc794877d84f3735f4f4ff69e3120843588da5c8aaa259d7ab7b965e3`.
2. selected-roughness-only successor: Map head `d8a1d950ed5f21e6ad356404f46407c99c160017`, artifact `10502588586`, SHA-256 `60c1e589e3e1c3a7dab5430b55ef59542dd7ca35dad8b13653d165c79eee3a1e`.
3. selected-roughness + compact-east composition: Map head `4bd7eaf6970716dde4159448c92556785f47e954`, artifact `10509037278`, SHA-256 `8f2f8aa4bb11e2f868a6ce36dd381933ba1ea6c59be7b82ed00d1dfe5402ee97`.

All three retain the same 17-state, two-camera, two-Weather-review-mode world family with Building, Nature, Object, the Map footprint cue and source-width Weather present.

## Gap

The combined Environment receiver is green, and Art Direction has frozen compact-east sampled spatial response for playback review. What remained unproven was a narrower Environment question:

> In the exact retained current-world raster, can the Object roughness contribution and the subsequently stacked compact-east contribution still be attributed independently, or does stacking create overlapping/suppressed raster evidence that should be surfaced before combined adoption?

Separate owner PASSes do not answer that automatically.

## Reusable rule

`SEQUENTIAL_WORLD_CANDIDATES_REQUIRE_PIXEL_ATTRIBUTION_AGAINST_EXACT_RETAINED_PARENTS_BEFORE_COMBINED_ADOPTION`

For a sequential world stack `A -> B -> D`:

- measure contribution 1 as `A -> B`;
- measure contribution 2 as `B -> D`;
- retain the full `A -> D` raster as combined authority;
- fail closed if the two contribution masks overlap when the candidate is claimed independent;
- fail closed if the combined changed-pixel mask is not the exact union of the two retained contributions;
- keep visual preference and Runtime/device acceptance with their owners.

This is deliberately a retained-raster attribution rule, not a universal renderer-composition law.

## Exact observed attribution

Across all 68 matched retained frames:

- selected roughness versus UV0 parent: `6,426` raw changed pixels total, `1,666` above 1 LSB, maximum `7 LSB`;
- compact-east added after selected roughness: `197,697` raw changed pixels total, `185,888` above 1 LSB, maximum `191 LSB`;
- combined versus UV0 parent: `204,123` raw changed pixels total, maximum `191 LSB`;
- roughness/compact changed-pixel overlap: `0`;
- combined pixels outside the exact sequential union: `0`;
- sequential-union pixels missing from the combined raster: `0`.

Therefore the final changed-pixel mask is the **exact disjoint union** of the two retained contributions in this evidence set.

Context detail is retained rather than averaged away:

- `path_eye`: compact-east remains non-observing; all combined delta there is the already-reviewed Object roughness contribution;
- `elevated_oblique`: Object roughness occupies the small retained receiver region while compact-east occupies its separate tree region; the exact masks do not overlap in either Weather review mode.

Two phase-08 review boards are derived from the exact full retained frames. The original PNGs remain visual authority; the boards and masks are diagnostic only.

## Ownership / handoff

- Environment owns this cross-asset attribution receipt and keeps both adoption flags false.
- Object Materials owns selected roughness meaning/value.
- Object Technical Art owns UV/texture transport.
- Nature/VFX owns compact-east source response and Weather visual-direction semantics remain Weather-owned.
- Animation owns current-world playback repair/characterization.
- Runtime owns representation/device cost.
- Art Direction and independent Visual QA own visual preference/final appearance acceptance.

No source retune, camera move, material amplification, motion retiming or Runtime optimization is requested by this result.

## Truth boundary

A PASS establishes only exact attribution across the three pinned retained current-world artifacts and their 68 fixed frames. It does not establish continuous playback, arbitrary cameras/lights/renderers, physical wind, target-device CPU/GPU/FPS/VRAM/thermal behavior, final aesthetic preference, CANON, production/game readiness, or Environment / World Art mastery.

The four AXM roots remain the merge gate: Truth, Agency / non-domination, Continuity, Wisdom before speed.
