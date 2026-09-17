# Environment — Object phase-bound VFX receiver readiness 001

## Scope

This is an Environment / World Art receiving-boundary check on the existing Map PR #24 lane. It does **not** author or retime the Object animation, redesign the lid-release motes, change Rigging, replace the current Object material/UV/roughness receiver, or promote any candidate.

The exact real-world parent is Environment head `d0461a787525d19004d83334c282adacaa06afed`, retained as artifact `10516853353` with archive SHA-256 `f879277d1e4b3c37b9a7fc491d992e520345a8642f56d0ae17abfcd9957444c0`. That parent already proves the current Building + Nature + Object + footprint + Weather composition across 17 states / 68 real Godot 4.7.2 frames while holding Environment adoption.

The new donor is Object VFX PR #31 at exact head `5f8b7bef1a8a0d1babeba7945962c83cd938529b`. Its retained owner-seed effect is phase-bound to the exact Object Animation sequence at `0.25 s` and uses the same Object source SHA-256 as the current Map receiver.

## Why this is the current Environment gap

The source identity is already aligned:

- current Map Object source SHA-256: `49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a`;
- Object VFX effect source SHA-256: same exact value;
- Object Animation sequence host source SHA-256: same exact value.

The current Map receiver is nevertheless explicitly an `EXACT_STATIC_HOST_ONLY__NO_UTILITY_MODULE__NO_INNER_LID_REVIEW_SLOT` receiver. It preserves the exact 812-triangle source, selected-face segmentation, exact UV0 identity and selected roughness, but it does not expose the Animation/Rigging-owned moving component boundaries needed by the authoritative lid/latch sequence.

Rendering the motes into this static receiver would therefore create a visually plausible but structurally false proof: the effect would appear without the source-owned motion to which its trigger is bound.

## Bounded improvement

The new contract and verifier bind the exact retained multi-asset world to the exact Object source, VFX and Animation identities and resolve the minimum source groups that any truthful world receiver must be able to move:

- `lid_shell`: source faces `12..23`;
- `latch_0_lever`: source faces `48..59`;
- `latch_1_lever`: source faces `72..83`.

Those ranges are not guessed. The verifier re-executes the exact deterministic Object builder pinned by Git blob identity and checks the resulting group ranges against the contract.

This does **not** claim that those three groups alone are the complete production articulation partition. Rigging / Technical Art remain authoritative for the exact moving hierarchy, pivots, lid-owned hinge pieces and transport. The three groups are the minimum undeniable motion boundary exposed by the current sequence.

## Decision

Expected scoped state:

`HOLD_CURRENT_WORLD_OBJECT_PHASE_BOUND_VFX_RECEIVER__STATIC_HOST_LACKS_ANIMATION_OWNED_COMPONENT_BOUNDARY`

Reusable rule:

`PHASE_BOUND_OBJECT_VFX_MUST_NOT_ENTER_WORLD_COMPOSITION_UNTIL_THE_WORLD_RECEIVER_PRESERVES_THE_ANIMATION_OWNED_MOVING_COMPONENT_BOUNDARIES`

No Environment, VFX or Animation adoption follows from this check.

## Next legitimate receiving step

Environment has two acceptable routes, both requiring new proof rather than assumption:

1. preserve the current Map material / UV0 / selected-roughness receiver while splitting the exact Animation/Rigging-owned moving source components into transformable receiver nodes, then prove the neutral 68-frame real-world raster remains unchanged before applying motion; or
2. receive the exact Technical-Art / Animation rigid scene directly, but only after proving exact geometry, material, selected-roughness and world-transform equivalence to the current Map receiver.

Only after one of those routes is green should the owner-seed lid-release motes be rendered in the full world. Art Direction / Visual QA keep perceptual acceptance; Animation keeps timing/easing; Rigging keeps articulation; Technical Art keeps transport; Runtime keeps production/runtime acceptance.

## Evidence boundary

This pass intentionally reuses the exact retained real-world parent instead of producing new screenshots: no scene content is changed. The new evidence is the cross-repo receiver-readiness relation itself. A negative control mutates the VFX source identity and must fail closed.
