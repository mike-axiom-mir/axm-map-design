# Runtime Building compact-v2 current-world budget 001

Status: **BOUNDED RUNTIME / CONSUMER-CHOICE HOLD**

This Runtime pass does not change Building source geometry or Environment composition. It compares the exact same-head current-world parent artifact with the exact compact-v2 review artifact already rendered by Environment on Godot 4.7.2 GL Compatibility.

## Why this exists

The isolated Building Runtime pass proved that compact-v2 is cheaper than the large `1420v / 2884t` boundary reference. The actual Map world does not render that reference. It currently renders a much smaller five-surface segmented Building at `184v / 276t`.

Therefore `compact-v2` must be judged against the receiver it would actually replace, not against the larger source-relative reference that gave it its name.

## Exact evidence inputs

Environment head:

`ef2cb9cc84edc10ab66c2230daca625623e0b00d`

Current-world parent:

- workflow run `35179857526`;
- artifact `10478624997`;
- Building receiver `184 vertices / 276 triangles / 5 surfaces`.

Compact-v2 current-world review:

- workflow run `35179857530`;
- artifact `10480305129`;
- Building receiver `1004 vertices / 2052 triangles / 5 surfaces`;
- Godot observation completed successfully before Environment's inherited visual-continuity verifier rejected the candidate.

## Runtime decision

`HOLD_CURRENT_WORLD_BUILDING_COMPACT_V2__RUNTIME_AND_VISUAL_REGRESSION`

Across all 68 matched state × camera × Weather-mode observations, the compact-v2 review receiver changes the proof-host counters by a stable:

- `+106,560 B` RenderingServer buffer memory;
- `+5,328` RenderingServer primitives;
- `+0` draw calls;
- `+0` objects;
- `+0 B` observed texture memory.

Runtime therefore keeps the current `184v / 276t` segmented receiver as the performance baseline. Compact-v2 is not a Runtime optimization in the current world, even though it remains smaller than the separate `1420v / 2884t` boundary reference.

## Visual tradeoff

The exact Environment compact-v2 workflow correctly failed its inherited `0.1%` full-frame `>1 LSB` continuity guard after successful Godot observation.

Runtime independently compares the same 68 retained images:

- elevated oblique: about `2.413%` of pixels exceed 1 LSB, max channel delta `180` LSB;
- path eye: about `3.204%` exceed 1 LSB, max channel delta `198` LSB.

That visual difference is far larger than the bounded seven-pixel isolated Building comparison from the prior Runtime pass. Art Direction and Visual QA retain authority over whether the different shell has visual value; Runtime does not treat that value as a performance justification.

## Reusable rule

> A representation name such as `compact`, `optimized`, or `LOD` is only relative to its declared comparison target. Before adopting it downstream, compare it against the **actual active consumer representation** on the exact receiver. A source-relative win can still be a current-world regression.

## Truth boundary

This is proof-host current-world evidence only. It does not establish target-device CPU/GPU frame time, FPS, VRAM/heap, thermal/battery behavior, arbitrary-camera equivalence, Technical-Art transport acceptance, gameplay behavior, CANON or production readiness.
