from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PARENT_HEAD = "29ef2d4cc4398b3f26290e4e1f1f10398ca9898c"
PARENT_RESULT = "PASS_CURRENT_WORLD_COMPACT_EAST_VISUAL_RESPONSE_TARGET_HOST"
RUNTIME_RESULT = "PASS_COMPACT_EAST_CURRENT_WORLD_EXACT_KEY_BINDING_AND_REAL_LOOP_DELIVERY_CHARACTERIZED"
SCHEMA = "axm.animation-compact-east-current-world-discrete-playback/v0.2"
DELIVERY_SEMANTICS = "PROCESS_FRAME_OBSERVATION_CHARACTERIZED_NOT_FULL_SOURCE_SLOT_DELIVERY_ACCEPTANCE"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(parent_report: dict[str, Any], runtime: dict[str, Any], captures: list[Path]) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    checks["parent_target_host_pass"] = parent_report.get("state") == PARENT_RESULT
    checks["schema"] = runtime.get("schema") == SCHEMA
    checks["parent_head"] = runtime.get("parent_vfx_receiving_head") == PARENT_HEAD
    checks["runtime_pass"] = runtime.get("state") == RUNTIME_RESULT
    checks["exact_source_timing"] = (
        float(runtime.get("duration_s", -1.0)) == 0.5
        and int(runtime.get("intervals", -1)) == 16
        and int(runtime.get("authored_endpoint_inclusive_states", -1)) == 17
        and int(runtime.get("loop_track_unique_states", -1)) == 16
        and abs(float(runtime.get("source_step_s", -1.0)) - 0.03125) <= 1e-12
    )
    checks["discrete_exact_state_policy"] = (
        runtime.get("source_motion_truth") == "DISCRETE_EXACT_VFX_STATES_NOT_SMOOTH_INTERPOLATION"
        and runtime.get("animation_track_interpolation") == "NEAREST"
        and runtime.get("animation_update_mode") == "DISCRETE"
    )
    exact = runtime.get("deterministic_exact_key_checks", [])
    checks["all_16_exact_keys_seekable"] = (
        len(exact) == 16
        and int(runtime.get("deterministic_exact_key_count", -1)) == 16
        and [int(row.get("phase", -1)) for row in exact] == list(range(16))
    )
    checks["exact_endpoint_seam"] = float(runtime.get("source_endpoint_geometry_delta_m", 1.0)) <= 1e-12
    checks["loop_matches_authored_final_step"] = float(runtime.get("loop_step_residual_m", 1.0)) <= 1e-12
    checks["negative_control_rejected"] = (
        runtime.get("negative_control_result") == "REJECTED_AS_REQUIRED"
        and float(runtime.get("negative_control_endpoint_mutation_m", 0.0)) >= 0.000999
    )

    cycles = runtime.get("real_playback_cycles_observed_phases", [])
    checks["three_real_wraps"] = int(runtime.get("real_playback_wraps", -1)) == 3 and len(cycles) == 3
    checks["real_playback_progress_observed"] = (
        len(cycles) == 3
        and all(len({int(v) for v in cycle}) >= 2 for cycle in cycles)
        and int(runtime.get("real_playback_process_frames", 0)) > 0
        and int(runtime.get("real_playback_observed_phase_changes", 0)) >= 3
    )

    expected_missing = [
        [phase for phase in range(16) if phase not in {int(v) for v in cycle}]
        for cycle in cycles
    ]
    actual_missing = runtime.get("real_playback_missing_phases_by_cycle", [])
    all_states_seen_each_cycle = len(expected_missing) == 3 and all(not row for row in expected_missing)
    checks["delivery_characterization_consistent"] = (
        actual_missing == expected_missing
        and bool(runtime.get("full_source_state_delivery_observed", False)) == all_states_seen_each_cycle
        and runtime.get("real_playback_delivery_semantics") == DELIVERY_SEMANTICS
        and runtime.get("full_source_state_delivery_accepted") is False
    )
    checks["process_frame_intervals_recorded"] = (
        float(runtime.get("process_frame_interval_min_ms", -1.0)) >= 0.0
        and float(runtime.get("process_frame_interval_mean_ms", -1.0)) >= 0.0
        and float(runtime.get("process_frame_interval_max_ms", -1.0)) >= float(runtime.get("process_frame_interval_min_ms", -1.0))
    )
    checks["persistent_receiver"] = (
        int(runtime.get("persistent_receiver_instance_id", 0)) > 0
        and int(runtime.get("persistent_animation_player_instance_id", 0)) > 0
    )
    checks["unrelated_motion_frozen"] = (
        int(runtime.get("frozen_weather_phase", -1)) == 0
        and int(runtime.get("frozen_west_sapling_phase", -1)) == 0
    )
    checks["three_retained_captures"] = len(captures) == 3 and all(path.is_file() and path.stat().st_size > 0 for path in captures)
    if not all(checks.values()):
        failed = [key for key, value in checks.items() if not value]
        raise ValueError(f"compact-east current-world Animation evidence failed: {failed}")
    return {
        "schema": "axm.animation-compact-east-current-world-playback-evidence/v0.2",
        "state": RUNTIME_RESULT,
        "parent_vfx_receiving_head": PARENT_HEAD,
        "checks": checks,
        "source_endpoint_geometry_delta_m": runtime["source_endpoint_geometry_delta_m"],
        "authored_final_step_m": runtime["authored_final_step_m"],
        "loop_step_m": runtime["loop_step_m"],
        "loop_step_residual_m": runtime["loop_step_residual_m"],
        "negative_control_endpoint_mutation_m": runtime["negative_control_endpoint_mutation_m"],
        "real_playback_wraps": runtime["real_playback_wraps"],
        "real_playback_process_frames": runtime["real_playback_process_frames"],
        "real_playback_observed_phase_changes": runtime["real_playback_observed_phase_changes"],
        "real_playback_cycles_observed_phases": cycles,
        "real_playback_missing_phases_by_cycle": actual_missing,
        "full_source_state_delivery_observed": runtime["full_source_state_delivery_observed"],
        "full_source_state_delivery_accepted": runtime["full_source_state_delivery_accepted"],
        "real_playback_wrap_times_s": runtime["real_playback_wrap_times_s"],
        "real_playback_cycle_durations_s": runtime["real_playback_cycle_durations_s"],
        "process_frame_interval_min_ms": runtime["process_frame_interval_min_ms"],
        "process_frame_interval_mean_ms": runtime["process_frame_interval_mean_ms"],
        "process_frame_interval_max_ms": runtime["process_frame_interval_max_ms"],
        "retained_capture_names": [path.name for path in captures],
        "truth_boundary": runtime.get("truth_boundary"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-report", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    captures = sorted(args.capture_dir.glob("*.png"))
    report = verify(load(args.parent_report), load(args.runtime), captures)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
