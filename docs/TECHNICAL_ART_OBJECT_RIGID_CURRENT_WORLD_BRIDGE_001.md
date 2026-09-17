# Technical Art — Object rigid current-world bridge 001

## Question

The active Environment receiver is truthful but static: it preserves the exact Object source, seven receiving surfaces, selected UV0 and selected roughness, yet exposes no source-owned moving-component boundary for the already-authored lid/latch sequence. Object Technical Art PR #16 already proves a 31-component rigid scene through generic UC, including the source-owned lid subtree and hinge pivot. The bounded integration question is whether those exact component boundaries can replace the current Map Object `MeshInstance3D` **without changing the neutral current-world result**.

## Bounded repair

This lane stacks on Map Environment PR #24 and adds a receiving adapter only. It does not rewrite Object geometry or ownership and does not add Object semantics to UC.

The workflow:

1. binds the exact retained 17-state / 68-frame current-world parent at Map head `d0461a787525d19004d83334c282adacaa06afed`;
2. binds Object Technical Art PR #16 at `965fb2f24dbd0b0cbb748d9f8b8712d62966315f` and its retained rigid-scene evidence;
3. rebuilds the exact Object source-group partition and checks that it matches the exact 31 transported Technical Art primitives;
4. checks the generic UC `axm.rigid-scene-graph/v0.1` executable blob is unchanged between the tested donor `6dc465987e01362264f88b7cef4213609ae50763` and inspected-current UC `e9eed3d9eb66392992cc18c8884bfade0d3b8efd`;
5. generates a receiver-only component map outside UC;
6. lets Godot first construct the existing seven-surface Map receiver, including generated normals, exact selected UV0 and selected roughness;
7. partitions only the existing index streams into exact source-owned component nodes while reusing the existing position/normal/UV/material resources;
8. localizes the exact lid-owned subtree around the already-proven source hinge pivot and reconstructs the neutral world positions through the lid node translation;
9. rerenders the same 68 real current-world frames and requires pixel-exact neutral equivalence to the retained parent;
10. retains Animation, VFX, Runtime/device, Art/QA, Environment adoption, CANON and production as separate gates.

## Reusable contract

`SOURCE_OWNED_RIGID_COMPONENT_BOUNDARIES_MAY_REPLACE_A_STATIC_RECEIVER_ONLY_WHEN_THE_EXISTING_MATERIAL_NORMAL_UV_AND_NEUTRAL_WORLD_IMAGE_IDENTITIES_REMAIN_EXACT`

This is deliberately a receiver contract, not a new UC feature. Domain knowledge remains in Object and its specialist lanes. UC remains the generic transport it already proved.

## Expected scoped result

`PASS_CURRENT_WORLD_OBJECT_RIGID_COMPONENT_BOUNDARY_NEUTRAL_EQUIVALENCE__ANIMATION_VFX_ADOPTION_HELD`

A PASS means only that the exact current-world Object can be represented by the exact Object-owned rigid component boundaries with the existing Map material/normal/UV/roughness appearance unchanged in the neutral 68-frame world. It does **not** mean the 101-sample Animation choreography or phase-bound VFX has been applied, nor that the higher component draw/submission cost is Runtime-acceptable.

## Fail-closed checks

The evidence rejects source-byte drift, Object Technical Art donor drift, UC rigid-scene executable drift, missing/overlapping/gapped source component ranges, lid ownership drift, fixed-lever reparenting, missing required moving boundaries, current-world source/material/UV/roughness drift, component-map byte drift, and any changed pixel in the retained 68-frame neutral set. A deliberate one-pixel mutation is retained as the visual negative control.

## Ownership / roots

- Object owns component geometry, group identity, hinge pivot and keeper/lever ownership.
- Animation owns authored time/motion semantics and is not adopted here.
- VFX owns phase-bound effect semantics and is not adopted here.
- Map/Environment owns receiving composition but does not self-approve this candidate.
- Runtime owns target-device cost and acceptance.
- Art Direction / independent Visual QA own final look acceptance.
- UC remains generic and unchanged.
- `axm-create-me` remains coordination/status only.

Truth, Agency / non-domination, Continuity and Wisdom before speed remain the merge gate.
