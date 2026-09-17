# Environment Building utility-panel clearance current-world receiver 001

## Scope

Environment receives one fresh Building source correction into the existing real multi-asset current-world review surface. Building Hard Surface PR #17 corrected the utility-panel body-center standoff from `0.08 m` to `0.10 m` so the full `0.08 m` body clears the `0.04 m` receiver plate by the declared `0.02 m`. Building Procedural PR #4 derives the corresponding two receiver-normal translations. This lane does not rewrite either owner.

The exact retained Environment parent remains the already-green selected-roughness + compact-east composition at `4bd7eaf6970716dde4159448c92556785f47e954`. Object selected roughness, Nature compact-east motion, Weather source widths, footprint cue, route, cameras, lights, Building material values and non-panel Building topology remain fixed.

## Preserved failed first attempt

Hosted run `35260357907` at Environment head `ce40c64bbfa07cd944bae6fac322986aea5307c5` failed at the bounded verifier after Godot rendered all 68 frames. Its retained artifact is `10514557596`, SHA-256 `756719002b6658690b7e68713921a92687a3fd902e640455194e179d440352ce`.

That failure exposed a real receiving-path defect rather than a threshold problem. The first observer overrode the historical `add_building_material` compatibility path and expected the old `152 vertex / 228 triangle` receiver. The actual retained current world renders the source-policy-selected `header-segmented-23` representation through `add_segmented_building`: `184 vertices / 276 triangles / 5 material surfaces`, segmentation revision `service-pavilion-001/interpenetration-free-header-segmentation-003`. The failed candidate therefore left the active Building receiver untouched. Direct comparison of its 68 rendered frames to the exact retained parent found `0` changed pixels.

The verifier was correct to reject that run because the actual static Building rows contained no clearance-rebind observation. This repair does not weaken the gate or relabel the failed run green.

## Repaired bounded receiving change

The receiver now binds explicitly to the active current-world Building identity:

- current source-policy head: `a976af429b0ea90e0f0cc72d4a8bd4eb8fef22d3`;
- current variant: `header-segmented-23`;
- segmentation source head: `34124101e616c423c5a3ed5e122ddf09b98a1650`;
- segmentation revision: `service-pavilion-001/interpenetration-free-header-segmentation-003`;
- placement translation carried by that receiver: `[0, 7.2, 0] m`;
- exact current representation: `184 vertices / 276 triangles / 5 material surfaces`.

Only sixteen current-receiver vertices move: eight vertices of each existing utility-panel proof box.

Source-authority centers remain:

- `front-utility-bay`: `[-2.45,-1.08,1.65] -> [-2.45,-1.10,1.65]`, translation `[0,-0.02,0]`;
- `east-utility-bay`: `[3.88,0.10,1.65] -> [3.90,0.10,1.65]`, translation `[+0.02,0,0]`.

In the active header-segmented receiver, after its explicit `[0,7.2,0]` placement translation, those same boxes are:

- front current-receiver center: `[-2.45,6.12,1.65] -> [-2.45,6.10,1.65]`, vertices `168..175`;
- east current-receiver center: `[3.88,7.30,1.65] -> [3.90,7.30,1.65]`, vertices `176..183`.

No topology, surface partition or material value change is authorized. The current Building identity remains `184 / 276 / 5`.

## Reusable rule

`SOURCE_OWNED_RECEIVER_PLACEMENT_SUCCESSOR_MUST_BE_REBOUND_EXPLICITLY_IN_THE_REAL_WORLD_WHILE_UNRELATED_ASSET_CANDIDATES_REMAIN_EXACT_AND_ADOPTION_STAYS_HELD`

A source-owner placement correction is not inherited merely because local service-surface geometry is unchanged. Environment must bind the correction to the **actual active receiver**, not a historical compatibility path, prove unrelated current-world candidates remain exact, and keep adoption separate from observation.

## Evidence target

The dedicated gate renders the exact retained 17-state world in both Weather modes and both review cameras, producing 68 Godot 4.7.2 frames. It checks:

- all 17 static Building rows are the active `header-segmented-23` receiver and carry the exact new nested clearance observation;
- exact `184 / 276 / 5` structural identity and all current Building material/segmentation metadata remain fixed;
- all 17 Object selected-roughness observations remain exact;
- compact-east remains the exact `0..16` phase sequence;
- all `1,224` Weather projected-width observations remain within the existing `0.05 px` boundary;
- draw-call, object and primitive submission counts remain unchanged versus the exact retained parent;
- the raster effect of the 20 mm receiver translation is characterized across all 68 matched frames, with **no minimum visual-delta threshold invented** merely to force observability;
- a negative control changing the front successor current-receiver center by `1 cm` is rejected fail-closed.

## Authority boundary

Hard Surface owns the source clearance correction. Procedural owns the bounded receiver-normal derivation. Building’s existing current-source policy / segmentation chain owns the active receiver identity. Environment owns only the current-world receiving candidate, lineage binding, composition continuity and visual observability characterization. Runtime owns representation/device acceptance. Art Direction and independent Visual QA own appearance/readability acceptance. Object, Nature and Weather owners retain their existing source authorities. All Environment adoption flags remain false.

This does not establish manufacturing validity, production UV/material state, runtime attachment, collision, gameplay, CANON, production readiness or Environment mastery. `axm-create-me` remains coordination-only; Truth, Agency / non-domination, Continuity and Wisdom before speed remain the merge gate.
