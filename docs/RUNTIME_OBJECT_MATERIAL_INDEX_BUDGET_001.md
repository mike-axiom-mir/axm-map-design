# Runtime — Object material indexed-surface budget 001

## Bounded question

Can the exact current-world Object receiver preferred by 3D Art Direction keep its five source-owned scalar material roles and exact rendered appearance while replacing repeated unindexed triangle-corner vertices with an indexed ArrayMesh representation?

This is a Runtime / Optimization representation experiment only. It does not collapse material roles, alter source geometry, change the Object scale/transform, or decide visual preference.

## Exact parent

The experiment stacks exactly on Environment current-world Object material-family head:

`6575cc38db9f0f62b14a82b352d8582edf89856d`

Retained parent evidence:

- workflow `35141819693` — SUCCESS;
- artifact `10466065113`;
- artifact SHA-256 `87dd366302e94b5a6f8241e110e9629c2d81a0d7321197b14a52b860642fd519`;
- exact 468-source-vertex / 812-triangle Object geometry;
- five material roles: `shell_coating`, `service_dark`, `hardware_steel`, `rubber_guard`, `interface_orange`;
- source head `d3fa10a270faae7925811f44f03381fe5c5d0215`;
- Object Materials head `c85517446a769e0d5f880fc0e9e32f47124f7b5e`.

The existing receiver emits each triangle corner through `SurfaceTool`, generates normals, and commits five material surfaces without calling `SurfaceTool.index()`. Therefore the live proof-host mesh is intentionally measured again as the control before any representation change.

## Candidate

The candidate starts from the already-validated exact five-surface receiver mesh and, per material surface:

1. imports that surface into a fresh `SurfaceTool`;
2. calls `SurfaceTool.index()` so only vertices identical across all generated attributes are reused;
3. commits the indexed surface into a new `ArrayMesh`;
4. restores the exact original material resource for that surface.

Because indexing occurs after normals are generated, a hard edge whose generated normals differ is not silently welded. The five surface/material boundaries remain intact.

## Evidence contract

Pinned host: Godot 4.7.2 GL Compatibility.

Two independent real-host processes run the exact same 17-state current-world observer:

- `UNINDEXED_CONTROL`;
- `INDEXED_CANDIDATE`.

The Runtime gate requires:

- exact parent/source/material authority;
- exact five surfaces in both modes;
- exact 812 rendered Object triangles in both modes;
- zero indices in the measured control;
- candidate index stream covering every original triangle corner;
- strictly fewer candidate stored vertices;
- lower logical position+normal+32-bit-index payload under the explicitly declared model;
- all 68 retained current-world PNGs byte-identical across the two processes;
- draw-call, object-in-frame and primitive-in-frame counters unchanged for every corresponding observation;
- a deliberate no-vertex-reduction mutation must fail closed.

The verifier also records RenderingServer buffer and texture memory deltas, but does not force a memory-win claim from those coarse process-level counters.

## Visual tradeoff boundary

The intended visual tradeoff is **none**. Any retained-frame difference fails this experiment rather than being accepted by Runtime. Art Direction and Visual Observer / QA retain authority over the underlying Object look; Runtime is only testing storage/submission representation.

## Truth boundary

A PASS proves only a bounded receiver-side representation improvement for this exact static Object, exact five material surfaces, exact current-world proof host and fixed retained views. The logical byte model counts position + normal payload plus 32-bit indices; it is not a claim about driver packing, VRAM allocation, heap residency, CPU/GPU frame time, FPS, import-time performance, arbitrary assets, gameplay, final Art Direction, CANON, production readiness or Runtime mastery.

No capability is moved to Universal Creation or Profession Fabric from one Object proof. If the pattern repeats across independent assets and source domains, capability placement can be reconsidered with separate evidence.
