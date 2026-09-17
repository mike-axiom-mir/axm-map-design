# VFX Nature leaf flutter clean-vs-ideal timing review 001

Status: EXPERIMENTAL VFX / ATMOSPHERE REVIEW EVIDENCE

This follow-on stays inside the existing Map VFX PR #35 lane. It does not retune the accepted Nature leaf-flutter source, create another live recorder, change Environment composition, change Weather, or move product implementation into `axm-create-me`.

## Why this is the next bounded proof

The accepted clean no-live-capture wall-clock run is still the timing authority and presented 92/96 scheduled direct-source states. Every attempted live visual observer materially perturbed that timing: synchronous image capture delivered 58/96, visible X11 with no recorder delivered 57/96, and visible X11 plus FFV1 delivered 39/96.

The telemetry-bound reconstruction is now independently revalidated from the exact clean timing receipt plus separately rendered real-Godot source-state images. The remaining useful VFX question is therefore perceptual review support: give Art Direction / Visual QA a bounded way to compare the clean measured presentation rhythm against the exact authored 31.25 ms direct-source schedule without modifying the source effect or pretending an observer-disturbed recording is the clean stream.

## Exact inputs

- accepted current-world receiver: `7713cbe5863c3bc38dabb6236eb4b393401224b6`;
- accepted Nature leaf-flutter effect: `ecade64227ba1d3d1faf029ca7188ea63c2560ec`;
- clean no-capture timing authority: `795d9e8862e895e506c756b9ea01cd6228fa7ab7` / workflow `35179504496`;
- retained telemetry-bound reconstruction artifact: workflow `35195889303`, artifact `10485154774`, SHA-256 `b6c07a67c82c8499d0475e7c73c2d6f1a9a74890d715f8a90a46ff2354519374`;
- independent reconstruction validator repair: head `79fb8260c898171ce7c6357d1cbd4a5f69bc231a`, workflow `35200830432`.

## Review surface

The review builder verifies the exact reconstruction state, all 34 real-Godot static source-phase PNG hashes, exact phase/digest bindings, exact 92/96 clean presentation event set, exact skipped slots, phase-00/16 neutral identity, and the existing no-interpolation / no-retime truth flags.

It then emits one self-contained HTML review plus lossless FFV1 convenience streams for both fixed cameras. The right-hand reference is an **unobserved authored schedule**: 48 direct-source slots per context at 31.25 ms spacing plus the exact neutral endpoint at 1500 ms, using the same verified real-Godot source-state image bank. It is a counterfactual review reference, not measured runtime.

The HTML has two explicit clock views:

- **Raw telemetry clock**: preserves the exact clean `frame_post_draw` offsets against authored due-time. This includes the proof-host's initial presentation latency.
- **Cadence-aligned review**: subtracts only the first clean `frame_post_draw` offset so the first presented frame starts at t=0. Every later measured interval and every skipped source slot stays unchanged. This is inspection alignment only; it is not timing authority and does not retime the Nature source.

The convenience media use a 1000 Hz still-image demuxer time base so the retained 31.25 ms / measured event durations are not silently quantized to the default 25 fps image time base. The encoded media remain review surfaces only; JSON telemetry is timing authority.

## Expected exact timing facts

The review must retain:

- `path_eye`: 47/48 presented slots, skip `[19]`, clean post-draw interval range about `28.924..58.852 ms` and mean about `32.063 ms`;
- `elevated_oblique`: 45/48 presented slots, skips `[11, 23, 38]`, interval range about `32.541..34.945 ms` and mean about `33.793 ms`;
- no interpolation;
- no source retiming;
- no source amplitude/phase-count change;
- Weather fixed at the exact phase-00 source-width presentation inherited by the clean reference.

These are proof-host presentation facts, not aesthetic thresholds.

## Ownership and truth boundary

Nature VFX remains source-effect owner. Map/VFX owns only this receiving/review evidence. Environment keeps composition authority. Art Direction / Visual QA own naturalness and smoothness judgment. Runtime owns target-device timing/performance. Weather owns Weather semantics.

A PASS for this review surface does **not** establish direct framebuffer capture of the clean timed stream, display scanout timing, human-perceived naturalness, final VFX quality, target-device CPU/GPU/FPS behavior, physical wind or biomechanics, gameplay/collision behavior, CANON, production readiness, or VFX mastery.

The four AXM roots remain the merge gate: **Truth, Agency / non-domination, Continuity, Wisdom before speed**.
