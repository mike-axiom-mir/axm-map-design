# Runtime Weather Width Cadence Cache 001

Status: EXPERIMENTAL / BOUNDED RUNTIME EVIDENCE ONLY

This Runtime lane is stacked exactly on Map VFX PR #25 head `bbc8721a8af60b11e660773786426965c421e4ff` after its real Godot 4.7.2 wall-clock observer reached the target host and retained a 32 Hz cadence failure. The authored source interval remains exactly `31.25 ms`; this lane does not relax that contract.

## Question

Does moving the already-finite 17-state Weather-width + sapling mesh construction outside the timed playback window, then swapping exact prebuilt mesh resources on schedule, reduce timed update pressure enough to improve the exact proof-host cadence without changing the retained rendered appearance?

## Before / after

The control is the inherited VFX receiving path: one mutable Weather `ImmediateMesh` and one mutable sapling `ArrayMesh` are rebuilt from exact source state during every scheduled sample.

The candidate prebuilds the same exact 17 Weather and sapling states before the wall clock starts for each fixed camera context, then swaps the already-built mesh resources during timed playback. The exact inherited Weather source-width projection and sapling builders are used to create the cache; Runtime does not duplicate source semantics or invent a second Weather generator.

This deliberately trades more mesh resources / memory and stable mutable mesh-resource identity for less timed rebuild work. RenderingServer buffer/texture counters are retained before and after cache construction so the memory side of that trade is visible.

## Evidence

The dedicated Runtime observer runs both modes in the same Godot 4.7.2 GL Compatibility process for both exact `1100x720` cameras and all 17 exact source states. It records per-sample submit lateness, update-end lateness, post-draw lateness, update duration, post-draw wait, exact source digests and Runtime counters.

For visual tradeoff review it also retains matched rebuild/cached PNG pairs at states `0 / 8 / 16` in both cameras. The verifier requires all six pairs to be byte-identical before the Runtime evidence is structurally acceptable.

The verifier distinguishes three possible bounded outcomes rather than forcing a success story:

- full proof-host cadence candidate if cached submit and post-draw deadlines both clear the unchanged `31.25 ms` interval and timed update work is reduced;
- submit-cadence improvement with post-draw held if only scheduling clears;
- update-cost reduction with cadence held if the cache reduces timed work but the renderer/presentation path remains late.

A deliberate source-identity drift control must fail closed.

## Ownership / non-claims

VFX / Weather retain source and visual-effect semantics. Environment retains world composition. Runtime owns this representation/cost experiment only. The cached representation is not VFX adoption and its changing mesh-resource identity is explicit rather than hidden.

No target-device CPU/GPU/FPS/VRAM, arbitrary camera/resolution/stream, physical Weather, gameplay, final Art Direction, CANON, production readiness or Runtime mastery is claimed from this proof-host experiment. `axm-create-me` remains coordination-only. The four AXM roots remain the merge gate.
