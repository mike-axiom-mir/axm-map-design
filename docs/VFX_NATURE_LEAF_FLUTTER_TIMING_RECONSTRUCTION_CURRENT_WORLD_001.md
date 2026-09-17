# VFX Nature leaf flutter telemetry-bound timing reconstruction — current world 001

Status: EXPERIMENTAL / NON-CANON / VFX EVIDENCE

## Why this successor exists

The clean no-capture current-world wall-clock reference at exact VFX head `795d9e8862e895e506c756b9ea01cd6228fa7ab7` delivered 92 / 96 scheduled direct source states. Every live visual-capture path tested afterward materially changed that delivery:

- synchronous post-draw framebuffer capture: 58 / 96;
- visible X11 + telemetry without a recorder: 57 / 96;
- visible X11 + external FFV1 recorder: 39 / 96.

The next useful VFX question is therefore not another recorder and not a source retime. It is whether Art / Visual QA can receive a reviewable visual reconstruction whose **timing identity comes from the already-measured clean stream** while its visual states come from separately rendered exact source phases.

## Bounded method

This lane keeps the accepted source and receiver unchanged:

- accepted current-world leaf-flutter receiver: `7713cbe5863c3bc38dabb6236eb4b393401224b6`;
- accepted Nature leaf micro-flutter source: `ecade64227ba1d3d1faf029ca7188ea63c2560ec`;
- clean timing head: `795d9e8862e895e506c756b9ea01cd6228fa7ab7`;
- clean timing workflow: `35179504496`;
- 16 unique repeating direct source phases `00..15`;
- phase `16` remains only the exact neutral endpoint witness;
- source spacing remains `31.25 ms`; no interpolation or source retiming is introduced;
- Weather remains fixed at exact source phase `00`, matching the clean timing isolation policy;
- cameras remain `path_eye` and `elevated_oblique`.

A new untimed real-Godot observer renders a fixed-Weather image bank for all 17 exact sapling source states in both cameras. Framebuffer readback and PNG encoding happen only in that static observer, where they cannot contaminate the already-retained clean timing measurement.

The workflow then binds every clean wall-clock record to the matching static source-state image by exact `source_phase_index` and `sapling_mesh_digest`. It constructs a machine-readable reconstruction timeline from the clean `frame_post_draw` timestamps. The pre-run neutral state at time zero is included because the clean observer establishes phase `00` before starting its monotonic timer; the endpoint witness is retained separately after the timed window.

The retained review video is a convenience rendering of that manifest. The manifest and clean runtime receipt, not video encoder timing, remain the evidence authority.

## Required gates

A scoped PASS requires:

1. exact accepted receiver, source-effect and clean-timing identities;
2. exact clean result `92 / 96`, including `47 / 48` path-eye and `45 / 48` elevated-oblique delivery;
3. exact clean skipped-slot sets: path-eye `[19]`, elevated-oblique `[11, 23, 38]`;
4. 34 real-Godot fixed-Weather PNGs: 17 phases × 2 cameras;
5. exact phase `00 == 16` neutral image identity in each camera;
6. every clean presented record's sapling digest equals the static image-bank phase digest selected for reconstruction;
7. direct phase IDs only, no interpolated image synthesis;
8. a deliberate wrong-phase mutation must fail the reconstruction identity gate;
9. retained reconstruction manifest plus review media and exact provenance receipts.

## Truth boundary

A green result would prove only that the exact clean timing receipt can be combined fail-closed with separately rendered exact current-world source-state images to produce a **telemetry-bound presentation-state reconstruction**.

It would not be a direct framebuffer capture of the clean timed run. It would not prove that unrelated renderer noise, sub-frame visual effects, display composition or monitor scanout are reproduced. It would not establish perceptual naturalness or final Art / Visual QA acceptance. It would not prove physical wind, biomechanics, gameplay, collision, damage, target-device performance, CANON, production readiness or VFX mastery.

This method is intentionally preferable to retiming the source or weakening the observation gate merely to make an intrusive recorder look smooth.

`axm-create-me` remains coordination-only. The four AXM roots — Truth, Agency / non-domination, Continuity, Wisdom before speed — remain the merge gate.
