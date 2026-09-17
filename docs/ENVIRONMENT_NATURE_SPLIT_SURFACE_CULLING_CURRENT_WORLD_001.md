# Environment Nature split surface-culling — current-world receiving review 001

## Scope

This Environment / World Art follow-on stays on existing Map PR #24. It does not author or adopt new Nature geometry. It receives one bounded material-role culling policy inside the exact current multi-asset world:

- existing `woody` surface -> `CULL_BACK`;
- existing `foliage` surface -> `CULL_DISABLED`;
- exact current Nature geometry remains `390 vertices / 570 triangles` for sapling, compact east tree and east-rear tree;
- Geometry PR #10's `490 / 620` explicit leaf-backface candidate is **not** adopted.

The motivation is cross-owner evidence already present in the constellation: the source winding migration makes woody backface culling meaningful; the bounded Materials sidedness review preferred material-side two-sided foliage for its exact sapling proof; current VFX evidence shows the explicit-backface alternative can follow the dynamic response but deliberately leaves Map receiving and final shaded preference open.

## Exact parent

Environment parent head:

`b0fa28733d77cad79d78f29e7ef76ccb9ab0b399`

Parent composition digest:

`6a7c4fa18d24d739b879d0fa8ecf76eb9ec8103ada0e771b65d401afe375adfb`

Retained parent artifact:

- ID `10474474259`;
- archive SHA-256 `08347ca601af63cdbfd6d421ac86ffbaad110ef1e556c4e961de1b96d7772bf3`.

## Donor context

- current Nature material-family head: `8b2e0523d7a2b210c6404f15bafb08fbedcad4dd`;
- bounded material-side sidedness review: `0b7fdfac3be4d9c25236fa8733108e7d32533657`, artifact `10443379564`, SHA-256 `2d45af990804bfb03e1d6950bb5440a57948ff6bc8b413d0b92e8462e107a514`;
- current Nature VFX dynamic leaf review: `4e5211d14286f9c292e769a78971f24d59194141`;
- explicit leaf geometry candidate owner: `da3adbef4de8cddb8f3ebe841d39bb31a8936f5f`.

These are context/owner evidence. Environment does not transfer their authority or promote the explicit geometry candidate.

## Evidence contract

The builder must preserve all 17 exact current-world states and every source payload. The only scene mutation allowed is a receiving-policy annotation plus its derived scene/composition digest.

The Godot 4.7.2 GL Compatibility observer reuses the exact established current-world renderer, Object footprint visibility and Weather-width proof. It changes only the two existing Nature material surfaces at commit time: woody receives backface culling; foliage remains two-sided.

The target-host verifier requires:

1. 68 exact parent/candidate current-world frames to exist and be compared;
2. a nonzero renderer-visible delta, so the review is not mislabeled as a no-op;
3. all 1,224 inherited Weather-width measurements to stay inside the existing `0.05 px` gate;
4. draw calls, objects, primitives, observed buffer memory and observed texture memory to remain unchanged versus the exact parent proof;
5. the target-host receipt to carry the exact split-culling identity;
6. explicit leaf-backface geometry to remain unadopted.

A target-host PASS is **receiving evidence only**. Pixel deltas are retained for Art Direction / Visual QA rather than automatically labeled visually better.

## Ownership / handoff

- Nature Geometry retains topology and leaf-backface candidate ownership.
- Nature Materials retains woody/foliage values and sidedness/lookdev evidence.
- Nature VFX retains dynamic response evidence.
- Environment owns only this current-world composition/receiving review.
- Runtime owns any performance/value decision.
- Art Direction / Visual QA own final visual preference.
- `axm-create-me` remains coordination-only.

## Non-claims

This pass does not claim final Nature look, source-level sidedness adoption, explicit-backface rejection outside this exact review, normals/tangents/UVs/textures/translucency/subsurface, physical wind or botanical correctness, target-device performance, collision/navigation/gameplay, CANON, production readiness, or Environment mastery.

The four AXM roots remain the merge gate: Truth; Agency / non-domination; Continuity; Wisdom before speed.
