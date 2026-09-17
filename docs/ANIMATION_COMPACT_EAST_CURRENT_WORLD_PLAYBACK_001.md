# Animation — compact-east current-world exact-state playback 001

## Scope

This Animation lane stacks exactly on Map VFX PR #43 head `29ef2d4cc4398b3f26290e4e1f1f10398ca9898c`, which already proves that Nature VFX PR #11's exact compact-east 17-state response is visibly received in the current world.

Animation changes no Nature source state, VFX timing/amplitude, Weather semantics, west-sapling motion, Building/Object/rear-Nature identity, camera, light, material, Runtime controller, collision or gameplay logic.

Art Direction has since explicitly frozen the sampled compact-east spatial response for playback review. This lane therefore repairs/characterizes the receiver only; it does not retime or reshape the source to satisfy proof-host delivery.

## Bounded question

Can the already-authored compact-east response be bound to a real Godot `AnimationPlayer` inside the exact current-world proof receiver as a repeated discrete exact-state loop, while preserving the authored neutral endpoint/seam, freezing unrelated motion, and truthfully separating exact-key applicability from what a proof-host process-frame observer actually sees in wall-clock playback?

## Contract

`axm.animation-compact-east-current-world-discrete-playback/v0.2`

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

The observer first deterministically seeks every one of the 16 unique loop keys and requires the exact mesh resource for each key. It retains source phases `00 / 08 / 15` as current-world captures. It then performs real capture-free `AnimationPlayer.play()` through three loop seams with persistent receiver/player identity.

The two observations are deliberately not conflated:

1. **Exact-key binding:** all 16 discrete source states must be individually seekable and applied exactly through `AnimationPlayer`.
2. **Real-loop delivery characterization:** process-frame observation records which exact source resources were actually seen in each wall-clock cycle, which source slots were not observed, wrap durations, process-frame interval statistics and phase transitions. Missing proof-host observation slots are retained as evidence. They are not converted into a source-motion failure and are not permission to retime the source.

A verifier-only `+1 mm` neutral-endpoint corruption must still be detected before playback. Unknown playback mesh resources, receiver identity drift, lack of repeated progression, or failure to cross three loop seams still fail closed.

## Preserved failed predecessor

Exact head `abad9beeb57dc99ba60aad60d3fb38046395972e`, workflow `35248112953`, failed because the observer required every one of the 16 states to be sampled by the proof-host `process_frame` loop in every 0.50 s cycle. The first observed cycle contained phases:

`[0, 2, 3, 5, 6, 7, 9, 10, 11, 12, 14, 15]`

so phases `1 / 4 / 8 / 13` were not observed at process-frame sampling points. The exact VFX prerequisite, real Godot setup and retained evidence upload all succeeded. That result is retained as a delivery-observer finding, not relabelled as a source-motion defect.

The v0.2 repair changes only evidence semantics and instrumentation. Source geometry, source timing, 31.25 ms cadence, phase resources, interpolation/update policy, cameras and acceptance ownership are unchanged.

## Result semantics

A scoped PASS under v0.2 may prove:

- the exact 16 unique source states are correctly bound and seekable through the real current-world `AnimationPlayer` receiver;
- the neutral seam is exact and adds no motion beyond the authored final step;
- a verifier-only endpoint corruption fails closed;
- the player progresses through repeated real loops while receiver/player identity remains stable;
- proof-host process-frame delivery is measured and any unobserved source slots are explicitly retained.

A scoped PASS does **not** require or imply that every 31.25 ms source slot was observed in every wall-clock cycle. `full_source_state_delivery_accepted` remains false in this lane.

## Truth boundary

This evidence is exact-key target-host binding plus proof-host repeated-loop delivery characterization for this exact current-world receiver. It is not smooth interpolation, full source-slot delivery acceptance, display scanout evidence, physical wind/biomechanics, final timing/naturalness, a production Runtime controller/state machine, target-device performance, collision/gameplay, Art Direction/Visual QA acceptance, CANON or production readiness.

This lane is intentionally distinct from Map PR #35, which characterizes wall-clock delivery of the separate west-sapling leaf-flutter effect. That adjacent lane also preserves direct source timing and records missed source slots rather than silently retiming; the west sapling itself remains frozen here and is not re-evaluated.

`axm-create-me` remains coordination-only. Truth, Agency / non-domination, Continuity, and Wisdom before speed remain the merge gate.
