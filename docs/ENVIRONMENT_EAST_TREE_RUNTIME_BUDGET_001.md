# Environment East-Tree Runtime Budget 001

Status: bounded Runtime / Optimization evidence stacked on the exact Environment east-foreground source-replacement head.

## Question

What is the proof-host runtime cost of replacing the exact seed-29 `proxy:nature-tree-east-b` box with the exact source-owned `compact-east-tree-neutral-001`, while preserving the accepted Environment scene, fixed cameras, west source sapling and Weather field?

## Compared states

1. `baseline` — the exact current Environment state before the east-tree source replacement, including the east Nature proxy.
2. `candidate` — the exact Environment replacement candidate from PR #4, where only that proxy is removed and the exact compact source mesh is inserted with no hidden source scaling or extra rotation.

Both states are rebuilt from the Environment replacement contract and measured in fresh pinned Godot 4.7.2 GL Compatibility processes.

## Budget contract

This lane does not invent a target FPS or production memory budget. It asks a narrower reusable question: can one source mesh replace one proxy without consuming an additional visible-object slot, draw-call slot or texture-memory slot in either fixed camera?

The candidate is allowed to increase renderer primitive count and buffer residency because it replaces a box with real 390-vertex / 570-triangle source geometry. Those deltas are measured and retained rather than guessed. Renderer counters remain proof-host observations and are not relabelled as authored topology.

## Visual tradeoff boundary

The Runtime lane changes no source geometry, placement, camera, lighting, Weather semantics or materials. It reproduces the exact Environment A/B relationship: `path_eye` should remain byte-identical because the replaced target is outside that fixed view, while `elevated_oblique` should retain a visible byte-level delta because that is where the hierarchy-motivated replacement appears.

That is evidence that the Runtime measurement stayed on the intended visual candidate. It is not Art Director or Visual Observer acceptance of the compact tree.

## Non-claims

A PASS proves only the comparative proof-host cost and one-slot draw/object/texture contract for this exact proxy-to-source replacement. It does not establish target-device FPS or GPU time, a production memory cap, streaming/LOD policy, final Environment Art Direction, botanical correctness, deformation cost, collision/navigation/gameplay, CANON, production readiness, or Runtime mastery.
