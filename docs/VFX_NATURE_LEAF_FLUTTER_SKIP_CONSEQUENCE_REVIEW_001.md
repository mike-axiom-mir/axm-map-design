# VFX Nature leaf flutter skipped-state consequence review 001

Status: bounded evidence/review surface only.

## Purpose

The clean no-capture current-world Nature flutter timing proof delivered 92 of 96 authored source slots. The existing clean-vs-ideal reviewer shows when the clean proof-host stream and the authored schedule diverge, but it does not isolate the exact visual content of the four source states that were skipped.

This review adds that missing evidence without changing the accepted Nature effect, timing policy, Environment receiver, Weather state, cameras, geometry, materials, source spacing, or scheduler.

## Exact lineage

- accepted current-world receiver evidence: `7713cbe5863c3bc38dabb6236eb4b393401224b6`;
- accepted Nature leaf-flutter source effect: `ecade64227ba1d3d1faf029ca7188ea63c2560ec`;
- clean timing authority: `795d9e8862e895e506c756b9ea01cd6228fa7ab7`;
- exact reconstruction artifact source run: `35195889303`;
- clean scheduling mode: `PHASE_LOCKED_LATEST_DUE_DIRECT_SOURCE_STATE_NO_RETIME`;
- clean scheduled/presented count: `96 / 92`;
- exact skipped slots: `path_eye=[19]`, `elevated_oblique=[11,23,38]`.

## Bounded review

For each skipped slot the builder identifies:

1. the exact previous clean-presented direct source state;
2. the exact authored source state that was due but not presented in that slot;
3. the exact next clean-presented direct source state;
4. pixel-exact absolute-difference metrics and raw diagnostic images for previous→skipped, skipped→next, and the actually presented previous→next jump.

All three state images come from the retained real-Godot static source-state bank already bound to the accepted receiver/effect lineage. The skipped image is therefore an exact authored source state, but **not** a claim that this framebuffer was directly captured during the clean timed stream.

A deliberate wrong skipped-phase binding must fail before the review may pass.

## Difference-image semantics

Raw absolute-difference images preserve channel deltas exactly. Separate `x8` diagnostic images exist only to make small changes easier to see. Their amplification factor is explicit and they must not be interpreted as faithful effect amplitude.

The JSON manifest is the metric authority; the HTML is a convenience review surface.

## Truth boundary

A PASS establishes only that the exact four clean proof-host source drops can be mapped fail-closed to their exact previous / skipped / next real-Godot source-state images and compared with deterministic pixel metrics.

It does **not** establish:

- human-perceived naturalness or smoothness;
- whether any skipped state is perceptually important enough to justify retiming or interpolation;
- direct framebuffer capture of the clean timed stream;
- display scanout timing;
- physical wind or biomechanics;
- gameplay, collision, damage or simulation behavior;
- target-device CPU/GPU/FPS/VRAM/thermal behavior;
- final Art Direction / Visual QA acceptance;
- CANON or production readiness.

Art Direction / Visual QA retain perceptual acceptance. Runtime retains target-device timing/performance. Nature VFX retains source-effect ownership. Environment retains composition ownership.

`axm-create-me` remains coordination-only. The four AXM roots remain the merge gate: Truth, Agency / non-domination, Continuity, Wisdom before speed.
