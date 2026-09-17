# Technical Art — Building planar-role UC index bridge 001

Status: BOUNDED CROSS-REPO TECHNICAL-ART EVIDENCE LANE

This lane answers one narrow question:

> Does the generic Universal Creation indexed-surface observer, when explicitly asked to evaluate exact render tuples rather than source-vertex identity, produce the same per-surface post-normal index representation that the real Godot `SurfaceTool.index()` receiver produces for the exact Building planar-role current-world path?

## Exact owners

- Building Hard Surface owns the planar-role representation: `boundary-only-planar-role-rectangle-render-001` at exact head `93f22e4eeb9bb32516d4b11f8d8bcf47d9792910`.
- Building Materials owns the pinned five-role material partition at exact head `4179aa1401f5a9114399e2f998c96809d4b8ed2e`.
- Runtime owns the measured post-normal per-surface indexing evidence at exact head `8d5860c308c244d314ede5b79021e46f35c4040d`.
- Universal Creation owns only the generic indexed-surface eligibility observer. This lane pins the exact UC head under test in CI.
- Technical Art owns this cross-repo identity/equivalence proof only.

## Exact receiver path

The current-world planar-role receiver emits five separate material surfaces and generates final normals before indexing. The Runtime successor then calls `SurfaceTool.index()` independently inside each final surface.

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

The bounded UC successor under test adds an explicit opt-in candidate identity policy:

`ATTRIBUTES_AND_PROTECTED_SPLITS`

Under that policy:

1. full supported render attributes remain exact;
2. `protected_split_ids` is mandatory;
3. distinct source vertices may share one structural candidate only when every declared render attribute and protected split identity is exactly equal;
4. cross-source candidate groups remain separately reported;
5. UC still emits no replacement mesh and authorizes no adoption.

For this Building proof, the five material partitions remain separate calls and each vertex carries the caller-owned partition split identity. UC therefore cannot merge across Building material roles.

## Required proof

For every one of the five exact Godot surfaces, the proof requires:

- UC result `POST_ATTRIBUTE_TUPLE_DEDUP_CANDIDATE`;
- UC render state `RENDER_DOMAIN_CROSS_SOURCE_DEDUP_CANDIDATE`;
- UC candidate vertex count exactly equals the real Godot indexed surface vertex count;
- UC candidate index stream exactly equals the real Godot `SurfaceTool.index()` stream;
- UC candidate POSITION first-occurrence order exactly equals the real indexed vertex order;
- UC candidate NORMAL first-occurrence order exactly equals the real indexed normal order.

Aggregate expected identity is therefore exactly 312 vertices / 1,008 indices / 336 triangles across five surfaces.

## Negative controls

The same exact input is also evaluated with UC's conservative default. It must preserve all 1,008 triangle-corner identities rather than silently crossing source identity.

The explicit cross-source policy is then rerun with the protected-split declaration removed. It must return `HOLD_CROSS_SOURCE_SPLIT_DECLARATION_REQUIRED` with no candidate.

Finally, the workflow mutates the real Godot indexed output by swapping two indices. The Technical Art verifier must reject the mutated receiver instead of accepting a count-only match.

## Truth boundary

This lane does **not** claim:

- automatic Building, Environment or Runtime adoption;
- that UC should own Building material, topology or representation semantics;
- visual equality or independent Visual QA acceptance;
- removal or acceptance of the residual Runtime primitive cost;
- target-device CPU/GPU/FPS/VRAM/heap behavior;
- arbitrary-mesh indexing safety;
- UV/tangent/normal-map/custom-channel/deformation equivalence beyond the exact declared channels;
- collision, navigation, manufacturing, gameplay or structural transport validity;
- CANON, Profession Fabric promotion or production readiness.

The four AXM roots remain the gate: **Truth, Agency / non-domination, Continuity, Wisdom before speed**.
