# Technical Art — Building planar-role UC index bridge 001

Status: BOUNDED CROSS-REPO TECHNICAL-ART EVIDENCE LANE

This lane answers one narrow question:

> Can Universal Creation observe the same post-normal per-surface index grouping as the real Godot `SurfaceTool.index()` receiver for the exact Building planar-role current-world path, without absorbing Building semantics or pretending that receiver-side attribute repacking is exact?

## Exact owners

- Building Hard Surface owns the planar-role representation `boundary-only-planar-role-rectangle-render-001` at exact head `93f22e4eeb9bb32516d4b11f8d8bcf47d9792910`.
- Building Materials owns the pinned five-role material partition at exact head `4179aa1401f5a9114399e2f998c96809d4b8ed2e`.
- Runtime owns the measured post-normal per-surface indexing evidence at exact head `8d5860c308c244d314ede5b79021e46f35c4040d`.
- Universal Creation owns only the generic indexed-surface eligibility observer. This lane pins the exact UC head under test in CI.
- Technical Art owns this cross-repo identity/equivalence proof only.

## Exact receiver path

The current-world planar-role receiver emits five separate material surfaces and generates final normals before indexing. Runtime then calls `SurfaceTool.index()` independently inside each final material surface.

The retained Runtime result is:

- 5 material surfaces;
- 336 triangles;
- 1,008 stored unindexed triangle-corner vertices;
- 312 stored indexed vertices;
- 1,008 indices.

The Technical Art observer subclasses that exact Runtime receiver and records the real Godot arrays immediately before and after `SurfaceTool.index()`:

- POSITION;
- NORMAL;
- storage index stream;
- triangle-corner index stream;
- caller-owned material-partition identity.

No replacement mesh is authored by Technical Art.

## UC contract being tested

The merged UC observer's conservative default keeps source-vertex identity in the candidate key. That is intentionally safe for source-lineage preservation but cannot describe receiver-local triangle-corner deduplication when equal render tuples come from distinct corner/source identities.

The bounded UC successor under test adds one explicit opt-in diagnostic policy:

`ATTRIBUTES_AND_PROTECTED_SPLITS`

Under that policy:

1. full supported render attributes remain exact;
2. `protected_split_ids` is mandatory;
3. distinct source vertices may share one structural candidate only when every declared render attribute and protected split identity is exactly equal;
4. cross-source candidate groups remain separately reported;
5. the existing source-lineage-preserving policy remains the default;
6. UC still emits no replacement mesh and authorizes no adoption.

For this Building proof, the five material partitions remain separate calls and every render vertex carries the caller-owned partition split identity. UC therefore cannot merge across Building material roles.

## Exact structural result

Across all five surfaces, UC and the real Godot receiver agree on the same partition of the 1,008 triangle corners into 312 indexed vertex groups. Their raw index numbers and stored vertex order need not match: those are representation-local labels. Technical Art instead requires a bijection between the candidate groups and exact preservation of the decoded POSITION corner stream.

The observed structural identity is:

- 1,008 input triangle corners;
- 312 indexed groups;
- 1,008 output indices;
- 336 triangles;
- 5 material partitions;
- exact corner-grouping isomorphism between UC and Godot on every surface;
- exact decoded POSITION corner stream on every surface;
- UC exactly reproduces the pre-index NORMAL corner stream used for its candidate grouping.

The conservative UC policy is rerun on the same exact input and must retain all 1,008 source/corner identities. Cross-source mode without the explicit split declaration must return `HOLD_CROSS_SOURCE_SPLIT_DECLARATION_REQUIRED` with no candidate.

## Receiver-side normal observation

The exact Godot `create_from -> index -> commit` receiver does not return the pre-index normal rows bit-for-bit unchanged on this pinned path. The retained observation is deliberately separate from the structural grouping PASS:

- 120 of 1,008 decoded triangle-corner normal rows change;
- every changed corner is in `frame_galvanized`;
- maximum absolute component delta: `0.00011304020881702792`;
- maximum angular delta: `0.006869404718583788` degrees;
- the other four material surfaces retain exact normal rows.

This is a **transport exactness HOLD**, not a visual rejection and not a visual acceptance. The numeric drift is small, but Art Direction / Visual QA own whether it is visually acceptable. Technical Art does not erase it by loosening the observer, and UC does not learn a Building-specific tolerance.

## Retained failed proofs

The failed runs are part of the evidence chain rather than discarded noise.

The first proof required identical raw index IDs / vertex storage order between independent indexers. That was over-constrained: index labels are local implementation details, so the Technical Art contract was repaired to compare group identity rather than byte-layout identity.

The second proof then required exact decoded POSITION+NORMAL equality after Godot indexing. That correctly exposed the receiver-side normal repack above. The final contract therefore separates the exact structural indexing proof from the independently held normal-transport observation instead of silently weakening either boundary.

## Negative controls

The final workflow also swaps two indices in the real Godot receiver output. That changes the corner grouping / decoded position assignment and must be rejected. A count-only match is not enough.

## Truth boundary

This lane does **not** claim:

- automatic Building, Environment or Runtime adoption;
- that UC owns Building material, topology or representation semantics;
- raw index-ID or stored vertex-order identity between independent indexers;
- exact post-index NORMAL transport;
- visual equality or independent Visual QA acceptance;
- removal or acceptance of the residual Runtime primitive cost;
- target-device CPU/GPU/FPS/VRAM/heap behavior;
- arbitrary-mesh indexing safety;
- UV/tangent/normal-map/custom-channel/deformation equivalence beyond the exact declared channels;
- collision, navigation, manufacturing, gameplay or structural transport validity;
- CANON, Profession Fabric promotion or production readiness.

The four AXM roots remain the gate: **Truth, Agency / non-domination, Continuity, Wisdom before speed**.
