# Technical Art — Building named receiver boundary 001

## Scope

This is a bounded follow-on inside existing Technical Art PR #27. It does not replace the historical source-rebind proof and does not opt Map into a new Building geometry revision.

Building Hard Surface now owns a versioned producer interface, `axm.building-build-result/v0.1`, at PR #2. Procedural has already migrated one consumer to that named interface. Map Technical Art still needed an explicit consumer-side projection that declares which Building fields it requires instead of treating tuple length/index as the cross-repo contract.

The adapter in `tools/technical_art_building_named_receiver.py` consumes the producer-owned named result and emits only the exact Map receiving projection required by this lane:

- `pavilion`
- `panel`
- `receiver_fits`
- `obj_lines`
- `bounds_min`
- `bounds_max`
- `readable_path_gap_m`
- `negative_controls`
- `topology_summary`

The Building producer remains authority for the meaning of those fields.

## Current pressure test

Pinned Building head: `34124101e616c423c5a3ed5e122ddf09b98a1650`.

That head contains two materially different producer surfaces at once:

1. the unchanged base closed/outward pavilion build result: 19 emitted boxes including panels, 152 vertices, 228 triangles;
2. the separate source-owned `axm.building-header-segmentation/v0.1` opt-in overlay: 23 emitted boxes, 184 vertices, 276 triangles.

The Technical Art adapter must bind the first by the source-owned named contract while proving the second cannot silently become the Map base receiver merely because it exists in the same producer repository.

The evidence also appends an opaque tenth value to the historical producer tuple and routes it through Building's own `from_legacy_output()` adapter. The Map named projection must remain byte-semantically identical.

## Fail-closed behavior

The projection rejects:

- build-result schema drift;
- a missing declared dependency such as `topology_summary`;
- any attempt to relabel the 23-box / 184-vertex / 276-triangle header overlay as the 19-box Map base receiver.

No nearest-match, tuple-width guess, source rewrite, topology coercion, or automatic successor adoption is allowed.

## UC boundary

Universal Creation is inspected but is not a dependency of this repair. Building producer naming and Map receiver dependency declaration are domain-bound integration plumbing. Moving these field names or Building topology policy into UC would centralize domain semantics for convenience rather than expose a proven generic primitive.

## Truth boundary

A PASS proves only that Map Technical Art can produce the exact existing base receiving projection from Building's versioned named result at the pinned producer head, remains insensitive to an opaque later legacy-tuple extension through the producer-owned adapter, and keeps the newer header-segmentation successor explicitly opt-in.

It does **not** prove or imply Environment adoption of the header overlay, current-world target-host rendering for that overlay, material remapping for segmented headers, Runtime acceptance, final visual acceptance, gameplay, CANON, production readiness, UC extraction, or Technical Art mastery.

`axm-create-me` remains coordination-only. The four AXM roots remain the merge gate.
