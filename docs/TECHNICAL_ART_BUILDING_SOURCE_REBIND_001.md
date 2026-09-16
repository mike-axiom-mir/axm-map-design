# Technical Art — Building source rebind 001

Status: DRAFT / EVIDENCE-GATED

## Gap

Building Hard Surface has source-owned the closed/outward box-shell successor at PR #2 head `57f66b1245812f0c3d402232a046b86c0b5c72d8`, and Building Materials PR #3 has independently rebound its unchanged five-surface family at head `ca92ef79d65a2ba287b7a76464bedceb6a31a1b6`.

The established Map Materials receiver at PR #14 remains pinned to the historical Building source head `4faa769b406bf3ad0ba9489a77141c27f122ce51`. Numeric vertex/placement equality is not successor provenance. The successor Building evaluator also now returns one additive topology-evidence value after the eight outputs that the older Map receivers consumed. Both Map receiving layers were destructuring exactly eight outputs, so the new producer could not pass through the existing source/material receiving path even though its first eight fields remained compatible.

## Bounded repair

This lane stacks on exact Map PR #14 head `0e2d571af4fd5772e9d48da013dc245914654660` and keeps its Godot observer, comparison host and material values unchanged.

The smallest compatibility repair is receiver-side and domain-neutral: `environment_building_source_replacement.py` and `environment_building_material_receiving.py` now require a stable eight-field producer prefix and accept additive trailing producer evidence outputs. They do **not** inspect or reinterpret the Building-owned `topology_summary`; exact source identity and the explicit triangle/surface partition remain the evidence for the topology successor. This prevents Map or UC from absorbing Building domain semantics merely to accommodate an additive producer contract.

The lane additionally:

- pins successor Building Hard Surface head `57f66b1245812f0c3d402232a046b86c0b5c72d8`;
- pins successor-bound Building Materials head `ca92ef79d65a2ba287b7a76464bedceb6a31a1b6`;
- preserves the exact material profile SHA-256 `e8dd0c33b9b2aea108194af57a8fe8de39c7e67bb86109af6dbf3895f22c010b`;
- preserves 152 world vertices, 228 triangles, five surface roles, seed 29, placement, Nature, Weather, Object proxies, cameras, path and lighting;
- requires the topology/surface partition to change from the historical face table rather than silently relabelling old evidence;
- compares the historical and successor structural receipts explicitly;
- runs the exact successor neutral/candidate scene through the established Godot 4.7.2 GL Compatibility target host.

No Building topology rule is authored in Map or UC. No Building material values are authored here. No current-world PR #24 state is changed here. No Runtime policy is changed here.

## Evidence contract

Structural PASS:

`PASS_MAP_BUILDING_SOURCE_OWNED_TOPOLOGY_REBIND_STRUCTURE`

requires:

1. exact historical and successor source/material identities;
2. unchanged panel source and material-profile identities;
3. unchanged five material values and role order;
4. exact unchanged world vertices and 152v/228t budget;
5. explicit changed topology/surface partition;
6. unchanged placement translation;
7. unchanged non-Building seed-29 receiving state;
8. both receiver layers accepting the producer's stable eight-field prefix without claiming the additive evidence field.

The workflow also deliberately rejects successor source-head drift, material-profile drift, stale historical topology and unrelated receiving-scene drift.

Target-host PASS:

`PASS_MAP_BUILDING_SOURCE_OWNED_TOPOLOGY_REBIND_TARGET_HOST`

requires the successor neutral and five-surface scene digests to reach the pinned Godot host, retain 152 vertices / 228 triangles / five roles in both fixed cameras, and retain a visible material-only A/B delta.

## Ownership and handoff

- Building Hard Surface owns the successor source/topology semantics and any meaning of its additive topology evidence.
- Building Materials owns material values and the separate current-world infill repair.
- Technical Art owns the stable receiving-prefix compatibility repair and this exact cross-repo receiving/provenance handoff.
- Environment PR #24 remains truthful for its historical Building chain and must explicitly rebind before claiming the successor in the dynamic current world.
- Runtime PR #26 remains truthful for its historical chain and must remeasure after a successor Environment receiving identity exists.
- Universal Creation is unchanged. This task exposes no missing reusable UC mechanism; adding Building topology policy to UC would be incorrect placement.
- `axm-create-me` remains coordination-only.

## Non-claims

This lane does not establish final Art Direction or Visual QA acceptance, UV/texture/decal/weathering quality, final normals/tangents, target-device performance, collision/navigation/gameplay, current-world PR #24 adoption, Runtime PR #26 successor acceptance, CANON, production readiness or Technical Art mastery.

The four AXM roots — Truth, Agency / non-domination, Continuity, Wisdom before speed — remain the merge gate.
