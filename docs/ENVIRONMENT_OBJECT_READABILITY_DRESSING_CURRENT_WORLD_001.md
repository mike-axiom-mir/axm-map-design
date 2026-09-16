# Environment current-world Object readability dressing 001

## Question

Can the current accepted Environment world improve the west equipment-case's scale/readability **without changing the Object source scale or source geometry**?

The exact current world at Map Environment PR #24 already proves the source-owned `modular-equipment-case-001` in the west receiver slot, but the source is materially smaller than the historical proxy that defined the slot. Art Direction explicitly held Object scale/readability and asked that any follow-on use an exact source/receiver comparison rather than arbitrary rescaling.

## Bounded Environment candidate

This lane keeps the exact Object source unchanged and adds one Map-owned world-dressing cue derived only from the already-accepted historical receiver footprint:

- dressing: `environment:dressing:west-object-service-footprint-frame-001`;
- exact reserved footprint: `x=-4.025387..-2.890757 m`, `y=3.736077..4.870707 m`;
- four low bars combined into **one static mesh / one material surface / 48 triangles**;
- strip width: `0.045 m`;
- height: `0.02 m`;
- material: dark rough neutral `RGBA(0.16, 0.19, 0.21, 1)`, metallic `0`, roughness `0.9`;
- no textures, no collision, no navigation or gameplay authority;
- no Object scale, position, rotation, source geometry or source material mutation.

The frame visually exposes the receiver footprint as world dressing instead of pretending the source object itself is larger.

## Structural bounds

Against the exact current source and receiver:

- Object source world AABB: `[-3.914641..., 3.984236..., 0] -> [-3.001502..., 4.622547..., 0.422] m`;
- minimum Object-to-frame inner clearance: **>= 0.06 m**;
- minimum separation from the readable path: **>= 1.0 m**;
- the frame remains inside the already-accepted west receiver footprint;
- Building, Weather source-width state, Nature, east proxy, route, cameras and lighting are copied exactly from the accepted Environment parent.

## Evidence plan

The dedicated workflow binds exact parent Environment head `5b9b55ec67e31655f51d1acc67284816067e5be6` and retained artifact `10454469590` before building the candidate. It then:

1. exercises fail-closed controls for parent drift, receiver-footprint drift, missing Object source and path intrusion;
2. renders the exact 17-state world in Godot 4.7.2 GL Compatibility;
3. retains both fixed `1100x720` cameras and both inherited Weather presentation modes, producing 68 candidate frames;
4. compares every candidate frame to the exact retained accepted parent frame;
5. requires every visual delta to remain inside the projected dressing footprint (plus a small antialiasing margin);
6. rechecks exact Object, Building, rear-tree culling and all 1,224 source-width observations;
7. records proof-host Runtime counters only as diagnostics for Runtime handoff.

## Ownership and handoffs

- **Environment / Map owns:** receiver-footprint dressing, spatial readability and exact composition evidence.
- **Object owns:** source geometry, scale semantics, materials, articulation and all Object-internal design.
- **Art Direction + Visual QA own:** whether this exact dressing actually improves current-world hierarchy enough to adopt visually.
- **Runtime owns:** any performance/budget acceptance if the dressing is visually preferred.
- **Gameplay / Systems own:** collision, interaction, service-zone rules or navigation if any are ever desired. None are created here.
- **Universal Creation / Profession Fabric:** unchanged; this single Environment receiving candidate does not justify extraction.
- **axm-create-me:** coordination/status only.

## Truth boundary

A PASS can prove only that this exact Environment-owned receiver-footprint frame is structurally bounded, visible and localized in the exact current world while source identities remain fixed. It does not prove final visual preference, physical mounting, gameplay meaning, collision/navigation, target-device performance, CANON, production readiness or Environment mastery.
