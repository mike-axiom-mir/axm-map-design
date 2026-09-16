# Environment Object Source Replacement 001

Status: **EVIDENCE CANDIDATE / ENVIRONMENT RECEIVING ONLY**

This lane replaces exactly one remaining Map proxy, `proxy:object-crate-west`, with the exact source-owned `modular-equipment-case-001` structural mesh from `mike-axiom-mir/axm-object-design` head `d3fa10a270faae7925811f44f03381fe5c5d0215`.

## Why this lane exists

The accepted Environment scene now carries real Building, multiple real Nature sources and real Weather while both Object slots remain proxy boxes. Object has since gained deterministic source geometry, structural interface evidence and an independent target-host import proof. Environment can therefore test one source body in the real world scene without taking ownership of Object materials, articulation, attachments or runtime behavior.

## Exact receiving rule

The west Object proxy keeps its exact **current varied receiving identity** from the PR #18 scene:

- position `[-3.458072, 4.303392, 0.567315] m`;
- reserved size `[1.13463, 1.13463, 1.13463] m`;
- retained dressing rotation `-4.626112 degrees` around source Z / world vertical;
- source is grounded by its exact minimum Z;
- no receiving scale is allowed.

The first exact cross-repo run intentionally failed because the initial draft had copied the older unvaried baseline slot (`[-3.4, 4.6, 0.55]`, `[1.1, 1.1, 1.1]`, `18 degrees`) instead of the already-varied PR #18 receiving state. That failure was retained as a provenance check: this lane was corrected to the exact current slot rather than silently moving the world back to stale coordinates.

The exact Object builder is rerun from source in CI. The candidate requires source SHA-256 `49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a`, OBJ SHA-256 `3e01ef3bf4935ee6aee7c56c03dc0b7f54c308e5ac2eb6a7583252a366901106`, `468` vertices, `812` triangles, zero degenerate triangles and `PASS_STRUCTURAL_INTERFACE_PROOF` before Map placement is evaluated.

## Context held exact

The baseline is the migrated rear-tree normal-culling Environment scene from Map PR #18. The candidate preserves:

- seed 29 and the exact already-varied west Object slot;
- exact Building pavilion source;
- west sapling, compact east tree and migrated rear/right tree;
- rear/right tree target-only `CULL_BACK` review state;
- exact Weather field;
- east Object proxy as a control/remaining proxy;
- central readable path and minimum spacing gate;
- fixed `path_eye` and `elevated_oblique` cameras;
- Environment lighting and proof-material rules.

Map Materials PR #14, VFX PR #16 and Runtime PR #17 are not consumed. Object Materials PR #6, Rigging PR #15, Animation PR #10, Runtime PR #13 and Technical Art PR #7 are not consumed either. Those lanes remain separate evidence about the same source family.

## Evidence rule

A structural PASS requires the exact source mesh to remain inside the current reserved west Object footprint/height after the retained `-4.626112-degree` dressing rotation, remain grounded, keep the readable path open, preserve minimum spacing, leave unrelated scene state exact and add exactly one `object-source` mesh.

The dedicated target-host workflow renders baseline and candidate through the existing pinned Godot 4.7.2 GL Compatibility Environment observer. It requires the exact Object source to appear as `468 / 812` in the target-host receipt while the migrated rear tree remains the isolated `CULL_BACK` source. At least one fixed camera must produce a byte-different retained image so the replacement is not an invisible bookkeeping change.

## Truth boundary

A PASS proves only exact receiving fit, preserved multi-asset scene state and target-host visibility for this one source-owned Object structural mesh in this exact current Map slot. It does **not** prove final Object materials, lid/latch motion, service-module attachment, UC GLB equivalence, collision, gameplay, target-device runtime budgets, final environment dressing, final Art Direction, CANON, production readiness or Environment/Object mastery.

`axm-create-me` remains coordination-only. Source ownership stays in Object, receiving composition stays in Map, and the four AXM roots remain the merge gate.
