# Compact-east current-world wall-clock rendered sequence 001

Status: Animation evidence lane only. No Runtime controller, gameplay or final visual acceptance is claimed here.

## Purpose

Retain a directly reviewable rendered sequence from the exact frozen compact-east current-world `AnimationPlayer` receiver after the exact-key and real-loop characterization at predecessor head `48dc93848aa336f9b6079ccfe738acbe539253ac`.

The source motion is unchanged:

- `0.50 s` duration;
- `16` unique loop states from `17` endpoint-inclusive VFX states;
- exact source step `31.25 ms`;
- `NEAREST` interpolation;
- `DISCRETE` value updates;
- `LOOP_LINEAR` loop mode;
- Weather and west-sapling remain frozen at phase `00` in this proof receiver.

## Bounded improvement

Contract: `axm.animation-compact-east-current-world-wallclock-sequence/v0.1`.

The observer performs one full warmup loop, then retains every proof-host `frame_post_draw` raster it observes across two consecutive complete loops plus the closing seam frame. Each retained frame carries:

- monotonic wall-clock timestamp from the start of retained capture;
- `AnimationPlayer.current_animation_position`;
- exact observed compact-east mesh phase identity;
- wrap/cycle marker;
- retained PNG identity in the evidence artifact.

PNG encoding happens after playback stops so disk compression does not alter the captured loop timing. The per-frame viewport image readback itself is still instrumentation and may alter proof-host cadence. Therefore timing from this lane is evidence about this instrumented capture path, not uninstrumented display scanout or target-device delivery.

## Required predecessor

Exact predecessor playback proof:

- head `48dc93848aa336f9b6079ccfe738acbe539253ac`;
- workflow `35253584821`;
- result `PASS_COMPACT_EAST_CURRENT_WORLD_EXACT_KEY_BINDING_AND_REAL_LOOP_DELIVERY_CHARACTERIZED`;
- `full_source_state_delivery_accepted = false` remains preserved.

Exact current-world VFX receiving parent remains:

`29ef2d4cc4398b3f26290e4e1f1f10398ca9898c`.

Exact Nature VFX source remains:

`cef2ad78d8e36a55ada5dad07329f1a7125d48de`.

## Truth boundary

A green result from this lane means only that two consecutive post-warmup loops plus the closing seam were retained as actual frame-post-draw rasters from the frozen receiver with timestamp and exact phase identity. It gives Art Direction and Visual QA a reviewable temporal sequence that the predecessor lacked.

It does **not** establish every 31.25 ms source slot was presented, uninstrumented frame cadence, display scanout, smooth interpolation, physical wind, final motion naturalness, target-device performance, Runtime controller/state-machine correctness, collision/gameplay, Art/QA acceptance, CANON or production readiness.
