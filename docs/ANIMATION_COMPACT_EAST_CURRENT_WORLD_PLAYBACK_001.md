# Animation — compact-east current-world exact-state playback 001

## Scope

This Animation lane stacks exactly on Map VFX PR #43 head `29ef2d4cc4398b3f26290e4e1f1f10398ca9898c`, which already proves that Nature VFX PR #11's exact compact-east 17-state response is visibly received in the current world.

Animation changes no Nature source state, VFX timing/amplitude, Weather semantics, west-sapling motion, Building/Object/rear-Nature identity, camera, light, material, Runtime controller, collision or gameplay logic.

## Bounded question

Can the already-authored compact-east response be driven by a real Godot `AnimationPlayer` inside the exact current-world proof receiver as a repeated discrete exact-state loop, while preserving the authored neutral endpoint/seam and freezing unrelated motion?

## Contract

`axm.animation-compact-east-current-world-discrete-playback/v0.1`

- source duration: `0.50 s`;
- source intervals: `16`;
- source endpoint-inclusive states: `17`;
- source spacing: `31.25 ms`;
- loop track: phases `00..15` only;
- phase `16` is not discarded: it remains the exact source neutral endpoint/seam witness and must equal phase `00` geometrically;
- track interpolation: `NEAREST`;
- update mode: `DISCRETE`;
- loop mode: `LOOP_LINEAR`;
- current-world review context: existing fixed `elevated_oblique` camera;
- Weather and west-sapling are frozen at their exact phase-00 state so this proof isolates compact-east motion.

The observer deterministically seeks every one of the 16 unique loop keys, captures source phases `00 / 08 / 15`, then performs real capture-free `AnimationPlayer.play()` until three loop seams are crossed. Each completed cycle must have observed all 16 exact mesh resources.

A verifier-only `+1 mm` neutral-endpoint corruption must be detected before playback. No source or tolerance is changed to make the proof pass.

## Truth boundary

A PASS proves only exact-state target-host playback and repeated loop continuity for this exact current-world receiver. It is not smooth interpolation, physical wind/biomechanics, final timing/naturalness, a production Runtime controller/state machine, target-device performance, collision/gameplay, Art Direction/Visual QA acceptance, CANON or production readiness.

This lane is intentionally distinct from Map PR #35, which characterizes wall-clock delivery of the separate west-sapling leaf-flutter effect. The west sapling is frozen here and is not retimed or re-evaluated.

`axm-create-me` remains coordination-only. Truth, Agency / non-domination, Continuity, and Wisdom before speed remain the merge gate.
