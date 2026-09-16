# Runtime live Object current-world import budget 001

Status: bounded Runtime / Optimization evidence lane.

## Why this lane exists

Environment PR #21 is the first exact current-world scene that combines the existing 17-state Weather + west-sapling sequence with the exact source-owned west Object replacement. Its retained Godot evidence already shows a real cost change, but Environment correctly leaves Runtime acceptance and target-device budgets unclaimed.

This lane does not change the scene. It turns that observed source-import cost into an exact, fail-closed proof-host budget contract.

## Exact before / after identities

Baseline:

- Map PR #20 head: `3e641a5ea7b2507a53e5ff1a8fba0f0f9c94abaf`;
- retained artifact: `10440445348`;
- exact 17-state current-world Weather + west-sapling sequence;
- pinned Godot `4.7.2 GL Compatibility`.

Candidate donor:

- Environment PR #21 head: `5ad4ef48a33eaaf76f6fefef315896da10b17eb4`;
- retained artifact: `10442202692`;
- exact Object source donor: `d3fa10a270faae7925811f44f03381fe5c5d0215`;
- Object target-host signature: `468 vertices / 812 triangles / CULL_DISABLED`;
- the PR #20 dynamic Weather/sapling identities remain exact.

## Measure-before observation

Across all 17 retained states, the exact PR #20 → PR #21 proof-host delta is stable in both fixed camera contexts:

- draw calls: `+0`;
- visible objects: `+0`;
- `RenderingServer` primitives: `+1600`;
- observed buffer memory: `+47,976 B`;
- observed texture memory: `+0 B`.

Absolute retained counter sets are:

- `path_eye`: `20 / 20 / 4392` → `20 / 20 / 5992` draw calls / objects / primitives;
- `elevated_oblique`: `27 / 27 / 6150` → `27 / 27 / 7750`;
- observed buffer memory: `6,532,344 B` → `6,580,320 B`;
- observed texture memory remains `12,875,715 B`.

These are pinned proof-host observations, not generic renderer semantics and not target-device budgets.

## Bounded Runtime contract

`axm.environment-live-object-current-world-runtime-budget/v0.1` requires the exact source replacement to preserve the existing runtime slot relationship across all 17 states:

1. no additional draw-call slot;
2. no additional visible-object slot;
3. no texture-residency delta in the retained proof-host counter;
4. exact `+47,976 B` observed buffer delta;
5. exact `+1600` `RenderingServer` primitive delta;
6. exact Weather/sapling state identities;
7. candidate static-source set equals the baseline set plus exactly the source-owned Object;
8. exact Object runtime signature remains `468 / 812 / CULL_DISABLED`.

The budget verifier fails closed if any of those relationships drift.

## Visual tradeoff retained for Art Direction

The Runtime lane changes no geometry, material, transform, camera, lighting, Weather state or sapling motion. The expected baseline/candidate visual difference is therefore the already-intentional static proxy → exact Object source replacement.

Across all 17 matched frame pairs, the retained source-import delta is stable:

- `path_eye`: `7,779 / 792,000` changed pixels (`0.9821969697%`) in every state;
- `elevated_oblique`: `3,205 / 792,000` (`0.4046717172%`) in every state.

Runtime records this as an intentional source-replacement delta, not an optimization-induced visual tradeoff and not an Art Direction acceptance claim.

## Reuse boundary

The reusable pattern being tested is narrow: a proxy → exact source upgrade may keep one receiving draw/object slot while its mesh residency and submitted primitive cost change measurably. Exact before/after source identity, target-host counters and retained visual attribution should be bound together instead of inferring cost from triangle counts alone.

One current-world case does not justify a universal budget registry, UC subsystem, LOD framework or cross-renderer constant.

## Truth boundary

A PASS proves only this exact proof-host import budget in pinned Godot 4.7.2 GL Compatibility for the exact current Environment/Object identities. It does not prove target-device FPS, GPU frame time, VRAM, production allocator behavior, renderer-independent primitive semantics, browser/mobile/console budgets, LOD/streaming policy, collision/gameplay, final art, CANON, production readiness, game readiness, or Runtime / Optimization mastery.
