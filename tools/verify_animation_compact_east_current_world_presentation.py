#!/usr/bin/env python3
"""Verify bounded compact-east current-world presentation evidence.

This verifier deliberately separates the timed real-playback observation from the
post-playback review rasters.  It does not promote proof-host observation into
scanout, target-device, Runtime-controller, gameplay, Art, QA, CANON, or
production acceptance.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.animation-compact-east-current-world-presentation-observation/v0.1"
WALLCLOCK_PREDECESSOR_HEAD = "84a186f087d8d7353cbfb98750f765d21bcc52be"
PARENT_VFX_HEAD = "29ef2d4cc4398b3f26290e4e1f1f10398ca9898c"
NATURE_VFX_HEAD = "cef2ad78d8e36a55ada5dad07329f1a7125d48de"
PASS_STATE = "PASS_COMPACT_EAST_CURRENT_WORLD_LOW_INTRUSION_PRESENTATION_CREST_RETAINED"
HOLD_STATE = "HOLD_COMPACT_EAST_CURRENT_WORLD_LOW_INTRUSION_PRESENTATION_CREST_NOT_RETAINED_EVERY_LOOP"
WALLCLOCK_STATE = "PASS_COMPACT_EAST_CURRENT_WORLD_REVIEWABLE_WALL_CLOCK_FRAME_SEQUENCE_RETAINED"
CREST_PHASE = 8


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"expected object in {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wallclock-report", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--raster-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    predecessor = load_json(args.wallclock_report)
    runtime = load_json(args.runtime)

    checks: dict[str, bool] = {}

    checks["predecessor_state"] = predecessor.get("state") == WALLCLOCK_STATE
    checks["schema"] = runtime.get("schema") == SCHEMA
    checks["wallclock_predecessor_head"] = runtime.get("exact_wallclock_predecessor_head") == WALLCLOCK_PREDECESSOR_HEAD
    checks["parent_vfx_head"] = runtime.get("parent_vfx_receiving_head") == PARENT_VFX_HEAD
    checks["nature_vfx_head"] = runtime.get("nature_vfx_head") == NATURE_VFX_HEAD
    checks["source_duration"] = abs(float(runtime.get("duration_s", -1.0)) - 0.5) <= 1e-12
    checks["source_interval_count"] = int(runtime.get("intervals", -1)) == 16
    checks["source_state_count"] = int(runtime.get("authored_endpoint_inclusive_states", -1)) == 17
    checks["loop_state_count"] = int(runtime.get("loop_track_unique_states", -1)) == 16
    checks["source_step"] = abs(float(runtime.get("source_step_s", -1.0)) - 0.03125) <= 1e-12
    checks["interpolation"] = runtime.get("animation_track_interpolation") == "NEAREST"
    checks["update_mode"] = runtime.get("animation_update_mode") == "DISCRETE"
    checks["loop_mode"] = runtime.get("animation_loop_mode") == "LOOP_LINEAR"
    checks["timed_loop_no_image_readback"] = int(runtime.get("timed_loop_viewport_image_readbacks", -1)) == 0
    checks["timed_loop_no_disk_write"] = int(runtime.get("timed_loop_disk_writes", -1)) == 0
    checks["warmup"] = int(runtime.get("warmup_wraps", -1)) >= 1
    checks["three_observed_loops"] = int(runtime.get("observed_complete_loops", -1)) == 3
    checks["endpoint_seam"] = float(runtime.get("source_endpoint_geometry_delta_m", 1.0)) <= 1e-12
    checks["loop_step_residual"] = float(runtime.get("loop_step_residual_m", 1.0)) <= 1e-12
    checks["frozen_weather"] = int(runtime.get("frozen_weather_phase", -1)) == 0
    checks["frozen_sapling"] = int(runtime.get("frozen_west_sapling_phase", -1)) == 0
    checks["authority_flags"] = all(
        runtime.get(key) is False
        for key in (
            "full_source_state_delivery_accepted",
            "display_scanout_accepted",
            "target_device_delivery_accepted",
            "visual_motion_naturalness_accepted",
            "runtime_controller_accepted",
            "gameplay_accepted",
        )
    )

    cycles = runtime.get("observed_cycles_phases", [])
    require(isinstance(cycles, list) and len(cycles) == 3, "expected three observed cycles")
    normalized_cycles: list[list[int]] = []
    for index, cycle in enumerate(cycles):
        require(isinstance(cycle, list) and len(cycle) >= 2, f"cycle {index} has insufficient progression")
        normalized = [int(value) for value in cycle]
        require(all(0 <= phase < 16 for phase in normalized), f"cycle {index} contains invalid phase")
        normalized_cycles.append(normalized)
    checks["cycle_phase_domain"] = True

    crest_by_cycle = [CREST_PHASE in cycle for cycle in normalized_cycles]
    reported_crest_by_cycle = runtime.get("crest_observed_by_cycle", [])
    checks["crest_vector_consistent"] = reported_crest_by_cycle == crest_by_cycle
    crest_all = all(crest_by_cycle)
    checks["crest_all_flag_consistent"] = bool(runtime.get("crest_observed_all_cycles")) == crest_all
    checks["state_matches_crest_result"] = runtime.get("state") == (PASS_STATE if crest_all else HOLD_STATE)

    # Fail-closed verifier-only negative control: remove the crest from one otherwise
    # retained cycle and require the salience predicate to reject it.
    mutated_cycles = copy.deepcopy(normalized_cycles)
    mutated_cycles[0] = [phase for phase in mutated_cycles[0] if phase != CREST_PHASE]
    negative_control_rejected = not all(CREST_PHASE in cycle for cycle in mutated_cycles)
    checks["negative_control_crest_omission_rejected"] = negative_control_rejected

    transitions = runtime.get("phase_transitions", [])
    require(isinstance(transitions, list) and len(transitions) >= 8, "too few phase transitions")
    prior_timestamp = -1.0
    for index, row in enumerate(transitions):
        require(isinstance(row, dict), f"transition {index} is not an object")
        timestamp = float(row.get("timestamp_s", -1.0))
        phase = int(row.get("observed_phase", -1))
        require(timestamp >= prior_timestamp, f"transition timestamps regress at {index}")
        require(0 <= phase < 16, f"transition {index} phase out of range")
        prior_timestamp = timestamp
    checks["transition_timestamps_monotonic"] = True
    checks["transition_count_consistent"] = int(runtime.get("phase_transition_count", -1)) == len(transitions)
    checks["frame_observations_present"] = int(runtime.get("frame_post_draw_observation_count", 0)) > len(transitions)

    cycle_durations = runtime.get("cycle_durations_s", [])
    checks["cycle_duration_count"] = isinstance(cycle_durations, list) and len(cycle_durations) == 3
    if checks["cycle_duration_count"]:
        checks["cycle_durations_finite_positive"] = all(0.0 < float(value) < 2.0 for value in cycle_durations)
    else:
        checks["cycle_durations_finite_positive"] = False

    rasters = runtime.get("reconstructed_phase_rasters", [])
    require(isinstance(rasters, list) and len(rasters) == 16, "expected 16 post-playback phase rasters")
    raster_hashes: dict[int, str] = {}
    raster_sizes: dict[int, int] = {}
    for row in rasters:
        require(isinstance(row, dict), "raster row is not an object")
        phase = int(row.get("phase", -1))
        require(0 <= phase < 16, f"invalid raster phase {phase}")
        require(phase not in raster_hashes, f"duplicate raster phase {phase}")
        path = args.raster_dir / f"animation-presentation-phase-{phase:02d}.png"
        require(path.is_file(), f"missing reconstructed raster for phase {phase}: {path}")
        require(path.stat().st_size > 0, f"empty raster for phase {phase}")
        require(int(row.get("width", -1)) == 1100 and int(row.get("height", -1)) == 720, f"unexpected raster size at phase {phase}")
        raster_hashes[phase] = sha256(path)
        raster_sizes[phase] = path.stat().st_size

    checks["all_16_review_rasters"] = set(raster_hashes) == set(range(16))
    checks["crest_raster_distinct_from_precrest"] = raster_hashes[8] != raster_hashes[7]
    checks["crest_raster_distinct_from_postcrest"] = raster_hashes[8] != raster_hashes[9]
    checks["symmetric_pre_post_crest_raster_identity"] = raster_hashes[7] == raster_hashes[9]

    require(all(checks.values()), f"verification checks failed: {[name for name, ok in checks.items() if not ok]}")

    report = dict(runtime)
    report["checks"] = checks
    report["crest_observed_by_cycle_recomputed"] = crest_by_cycle
    report["negative_control_crest_omission_rejected"] = negative_control_rejected
    report["reconstructed_phase_raster_sha256"] = {str(key): value for key, value in sorted(raster_hashes.items())}
    report["reconstructed_phase_raster_bytes"] = {str(key): value for key, value in sorted(raster_sizes.items())}
    report["verification_truth_boundary"] = (
        "Timed playback was observed through frame_post_draw metadata only with zero viewport image readbacks and zero disk writes recorded in the timed loop. "
        "The 16 PNGs are exact post-playback phase reconstructions from the frozen receiver and camera, used to make the actually observed phase sequence reviewable. "
        "This verifier does not claim display scanout, target-device delivery, complete source-slot presentation, physical wind, final naturalness, Runtime controller/state-machine behavior, gameplay, Art/QA acceptance, CANON, or production readiness."
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(report["state"])
    print("crest_observed_by_cycle=", crest_by_cycle)
    print("cycle_durations_s=", cycle_durations)
    print("frame_post_draw_interval_ms=", runtime.get("frame_post_draw_interval_min_ms"), runtime.get("frame_post_draw_interval_mean_ms"), runtime.get("frame_post_draw_interval_max_ms"))
    print("phase7_sha256=", raster_hashes[7])
    print("phase8_sha256=", raster_hashes[8])
    print("phase9_sha256=", raster_hashes[9])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
