# Current-world dense atmosphere rebind 001

## Scope

This VFX lane stacks exactly on Environment PR #18 head `f548f98959bf6769716a6d7c87bac69f9f548389` and consumes, by exact donor identity, the already-proven dense live VFX sequence from Map PR #16 head `6e386d513c0b2e821a89fb066b2e3ab58a0d6868`.

The gap is evidence lineage, not a request for a new effect. PR #16 proves the exact 17-state Weather + accepted sapling sequence with source-owned per-streak opacity and stable proof-host resources, but it lives on the older Environment ancestry. PR #18 now owns the current receiving scene with source-owned Building/vegetation and the migrated rear/right tree under isolated `CULL_BACK`, and explicitly did not consume PR #16.

## Bounded rebind

The rebind keeps the current PR #18 world static and changes only the two already-proven visual-effect surfaces over the exact 17-state schedule:

- Weather lines are copied from the exact PR #16 source sequence, including all 36 source-owned opacity values;
- west sapling vertices follow the exact accepted Nature visual response sequence while triangle identity remains fixed;
- source-owned Building, compact east tree, migrated rear/right tree, remaining proxies, path, cameras and culling review remain exact PR #18 state;
- rear/right tree remains the only static source under `CULL_BACK`; other static source meshes remain `CULL_DISABLED` for the inherited isolated review contract;
- the Godot proof host keeps one Weather node/mesh/material and one sapling node/mesh/material across all 17 state updates;
- all 34 retained frames are evidence outputs, not final art authority.

## Exact donors

- current Environment receiving donor: `f548f98959bf6769716a6d7c87bac69f9f548389`;
- dense VFX donor: `6e386d513c0b2e821a89fb066b2e3ab58a0d6868`;
- dense VFX sequence digest: `f7f2cad01184e8651bcc722b755a2f3c2292ca13e81c7399579d7f42e0c19b30`;
- accepted Nature visual response: `cee14f5b3feea78b0adcd044bad2ea3c97657fc6`;
- Weather source: `ca2eaba519e8449835b0ea6ef944b7080c3caa6a`;
- migrated rear-tree source: `4ddbe66e5c02d22407ef773d5346a2fe6f349a2d` / mesh `aa9d450a78fef722672ea9af0f9aca98b4c1a0ca3705661784f5f61f3e9b6a31`.

## Truth boundary

A PASS proves only that the existing exact visual-only atmosphere sequence can be rebound into the exact current Map receiving state without source drift, static-world drift or loss of the inherited rear-tree culling isolation, and can be consumed through stable proof-host resources in pinned Godot 4.7.2 GL Compatibility.

It does not prove physical wind/forces, turbulence, precipitation, volumetrics, deformation for the compact/rear trees, source `width_px` fidelity, wall-clock playback, renderer interpolation, target-device performance, gameplay/collision, final atmosphere quality, Art Direction / Visual QA acceptance, CANON, production readiness or VFX mastery.

`axm-create-me` remains coordination-only. The four AXM roots remain the merge gate.
