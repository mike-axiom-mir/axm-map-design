# Animation compact-east current-world presentation observation 001

Status: bounded 3D Animation / Motion evidence lane. `axm-create-me` remains coordination-only.

## Contract

`axm.animation-compact-east-current-world-presentation-observation/v0.1`

This successor answers the concrete Art Direction / Visual QA handoff from the retained wall-clock packet at exact predecessor `84a186f087d8d7353cbfb98750f765d21bcc52be`: does the current proof host still retain the compact-east motion crest when viewport image readback and PNG encoding are removed from the timed real-playback loop?

The source is frozen:

- current-world VFX parent `29ef2d4cc4398b3f26290e4e1f1f10398ca9898c`;
- Nature VFX owner `cef2ad78d8e36a55ada5dad07329f1a7125d48de`;
- duration `0.50 s`;
- 16 intervals / 17 endpoint-inclusive source states;
- exact source step `31.25 ms`;
- 16 unique loop phases `00..15`, with phase `16` retained as the duplicate-neutral seam witness;
- `NEAREST` interpolation, `DISCRETE` update, `LOOP_LINEAR` loop mode;
- Weather and west-sapling frozen at phase `00`;
- camera, lighting, geometry and source amplitude unchanged.

## Bounded method

After one warmup wrap, Godot 4.7.2 runs three complete real `AnimationPlayer.play()` loops. During that timed section the observer waits for `RenderingServer.frame_post_draw` and records only in-memory metadata: monotonic timestamp, current AnimationPlayer position, exact active source-mesh phase, wrap/cycle marker and persistent receiver/player identity.

The timed section performs **zero viewport image readbacks and zero disk writes**. This removes the expensive image-readback/PNG path that produced the prior 42–56 ms retained-frame intervals. It is still an observer on a proof host, so it is not relabelled as display scanout or target-device delivery.

For this exact discrete receiver, phase `08` is the unique visible crest between symmetric phases `07` and `09`. The scoped result is PASS only if phase `08` is observed in every one of the three post-warmup loops. Missing it produces a truthful HOLD, not a source retime.

After timed playback has stopped, the observer reconstructs one exact raster for each phase `00..15` from the same frozen receiver/camera. These 16 PNGs are review aids keyed to the observed phase sequence; they are not claimed to be captured display frames. The verifier additionally requires the retained phase-08 raster to differ from phases 07 and 09 while the symmetric 07/09 rasters remain identical, and a verifier-only crest-omission mutation must fail the salience predicate.

## Truth boundary

A green result may prove only that the exact frozen current-world receiver retains its discrete crest during three low-intrusion proof-host presentation observations and that the observed phase sequence can be reviewed against exact post-playback phase rasters.

It does **not** establish full 31.25 ms source-slot delivery, uninstrumented display scanout, target-device behavior, physical wind, smooth interpolation, final timing/weight/naturalness, Runtime controller/state-machine behavior, collision/input/gameplay, Art Direction or Visual QA acceptance, CANON, or production readiness.

The four AXM roots — Truth, Agency / non-domination, Continuity, Wisdom before speed — remain the merge gate.
