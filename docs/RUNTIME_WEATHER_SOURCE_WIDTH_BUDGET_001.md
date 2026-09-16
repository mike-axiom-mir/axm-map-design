# Runtime Weather source-width budget 001

## Scope

This Runtime / Optimization evidence lane consumes the exact retained Environment PR #24 source-correct + Weather-source-width artifact and characterizes only the cost of its thin-line control versus the already-proven camera-projected source-width ribbon representation.

Exact producer identity:

- Map Environment head: `0d8b2279ecbba47b9696a951db9513883fbef6c5`;
- composition digest: `132e877c8016d833f43d7a4cfe303ad2595913c757b85dd212192eafafed1973`;
- retained artifact: `10452505109`;
- retained ZIP SHA-256: `4ffc52fc421d38a92829d3bf663ab5a48dfc144d16f31028f742ce19855512f4`;
- proof runtime: Godot 4.7.2 GL Compatibility;
- 17 states, two fixed 1100×720 cameras, 36 Weather streaks.

Runtime changes no Environment, VFX, Building, Nature, Object, camera, lighting or material producer code. It derives a fail-closed budget receipt from exact retained target-host evidence and independently recomputes all 34 control/candidate image differences.

## Measure-before / after

Thin-line control:

- `path_eye`: 32 draw calls / 32 objects / 5,992 primitives / 6,580,320 B observed buffer / 12,875,715 B observed texture;
- `elevated_oblique`: 39 / 39 / 7,750 / 6,580,320 B / 12,875,715 B.

Source-width ribbon candidate:

- `path_eye`: 32 / 32 / 6,136 / 6,582,624 B / 12,875,715 B;
- `elevated_oblique`: 39 / 39 / 7,894 / 6,582,624 B / 12,875,715 B.

Stable exact delta across all 17 states in both cameras:

- draw calls: `+0`;
- objects in frame: `+0`;
- RenderingServer primitives: `+144`;
- observed buffer memory: `+2,304 B`;
- observed texture memory: `+0 B`.

Relative to each exact control counter set, the primitive increase is about `+2.4032%` in `path_eye` and `+1.8581%` in `elevated_oblique`. The observed buffer counter increases by about `+0.0350%`.

This yields the bounded decision:

`PASS_BOUNDED_SOURCE_WIDTH_PRESENTATION_COST__PLUS_144_PRIMITIVES_PLUS_2304_BUFFER_BYTES_NO_DRAW_OBJECT_TEXTURE_DELTA`

The `+144` and `+2,304 B` values are exact proof-host observations, not a generic per-streak or renderer-independent cost law.

## Visual tradeoff retained for Art Direction

Runtime does not alter pixels. The exact retained source-width candidate remains a sparse visual delta against the control while preserving the broader source-correct Building/Nature/Object/path world. Existing Art Direction / Visual QA preference for the authored-width presentation stays separate from Runtime acceptance.

The Runtime evidence recomputes all 34 A/B frame differences and requires every pair to remain visibly different but sparse (`<0.5%` changed pixels per frame). It also retains the existing five explicit near-plane endpoint clips instead of hiding that representation boundary.

## Truth boundary

A PASS characterizes only this exact fixed-camera Godot 4.7.2 GL Compatibility representation and exact retained producer artifact. It does not establish CPU/GPU frame time, FPS, overdraw, VRAM, heap/allocator residency, arbitrary-camera/resolution cost, mobile/browser/console budgets, physical Weather dimensions, gameplay visibility/collision/damage, final Art Direction, CANON, production readiness, game readiness or Runtime / Optimization mastery.

`axm-create-me` remains coordination-only. Map/VFX/Weather/Building/Nature/Object retain their existing ownership boundaries. The four AXM roots remain the merge gate.
