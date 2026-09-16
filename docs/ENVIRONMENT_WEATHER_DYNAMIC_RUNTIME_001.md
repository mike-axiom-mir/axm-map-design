# Environment Weather Dynamic Runtime 001

Status: **EXPERIMENTAL RUNTIME EVIDENCE / NO PRODUCT PROMOTION**

## Question

The VFX receiving lane proves nine exact source-derived Weather states in the same seed-29 Environment scene, while explicitly leaving same-process changing-mesh behavior and runtime update cost unproven.

This Runtime lane asks one bounded question:

> Can the exact 36-streak visual-only Weather field advance through those same nine states in one pinned Godot process while retaining one visible line surface and one persistent Weather node/mesh/material, instead of rebuilding those resources for every state, without changing the retained rendered result or proof-host runtime counters?

## Exact base

This lane stacks on:

- `mike-axiom-mir/axm-map-design#7`;
- exact base head `10f1152b73240d0755bb14fa1c7744da3c544355`;
- exact Environment base head `8f81c57d9169dc9faba0cb01b85f17dff92bad6f`;
- exact Weather source head `ca2eaba519e8449835b0ea6ef944b7080c3caa6a`;
- Weather semantics `VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED`.

The exact nine-state sampling schedule remains:

`0 / .0625 / .125 / .1875 / .25 / .3125 / .375 / .4375 / .5 s`.

No source Weather semantics, streak identity/order, Environment placement, sapling, proxies, path, cameras, proof material, lighting, or Universal Creation code is changed.

## Measure-before control

The comparison uses two same-process proof-host strategies over the exact same sequence.

### `rebuild_control`

A deliberately simple synthetic control frees and reconstructs the Weather `MeshInstance3D`, `ImmediateMesh`, and `StandardMaterial3D` for every sampled update.

This is **not claimed to be an existing product implementation**. It is a controlled reconstruction baseline for measuring resource churn in the same host/process shape as the candidate.

### `reuse_single_mesh`

The bounded candidate creates exactly one Weather `MeshInstance3D`, one `ImmediateMesh`, and one material. Every sampled state clears/rebuilds only that mesh's single line surface while retaining the same node, mesh-resource, and material identities.

The candidate does not alter the source field. It changes only proof-host resource lifecycle.

## Evidence contract

The dedicated Runtime workflow rebuilds the exact VFX sequence from pinned Nature/Weather dependencies, then runs both strategies in fresh pinned **Godot 4.7.2 GL Compatibility** processes.

For both strategies it retains:

- exact input/source/sequence identity;
- all nine same-process updates;
- Weather node / mesh / material instance identities;
- surface count and streak count;
- `RenderingServer` objects / primitives / draw calls / texture-memory / buffer-memory counters from both fixed cameras;
- exact PNGs for both fixed cameras at every sample;
- CPU-side GDScript submission timings;
- bounded repeated-update memory/counter observations.

The final comparison fails closed unless the candidate:

1. preserves exact source/sequence identity;
2. keeps one node, one mesh resource, and one material across all retained samples;
3. keeps one line surface containing the exact 36 streaks;
4. matches the reconstruction control's retained proof-host counters sample-for-sample;
5. produces byte-identical retained PNGs sample-for-sample in both cameras;
6. still produces nine distinct Weather frames per camera;
7. creates only one Weather node/mesh/material while the synthetic control recreates them per update.

CPU timings and memory observations are retained but are **not** used as universal performance gates. GitHub-runner timing noise, driver behavior and `RenderingServer` counters are not target-device budgets.

## Visual tradeoff rule

A resource-lifecycle optimization is not allowed to earn a Runtime PASS by silently changing the VFX result. The candidate must retain byte-identical proof frames against the same-process reconstruction control for every sample and both fixed cameras.

If render bytes differ, the Runtime comparison HOLDs for Art Director / Visual Observer review instead of declaring the changed output "optimized."

## Truth boundary

A future PASS from this lane proves only a bounded same-process proof-host resource-reuse contract for this exact visual-only 36-streak Weather sequence. It may establish reduced node/mesh/material creation churn while preserving retained visual and counter evidence.

It does **not** prove:

- target-device FPS or GPU frame time;
- target memory/draw-call budgets;
- asynchronous production VFX architecture;
- physical wind, forces, precipitation or volumetrics;
- final Environment or Art Director acceptance;
- gameplay, collision or simulation behavior;
- generic Godot particle/line policy;
- a Universal Creation runtime organ;
- CANON, production readiness, or Runtime / Optimization mastery.

The four AXM roots remain the merge gate. `axm-create-me` remains coordination-only.
