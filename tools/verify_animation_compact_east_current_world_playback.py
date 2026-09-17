from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PARENT_HEAD = "29ef2d4cc4398b3f26290e4e1f1f10398ca9898c"
PARENT_RESULT = "PASS_CURRENT_WORLD_COMPACT_EAST_VISUAL_RESPONSE_TARGET_HOST"
RUNTIME_RESULT = "PASS_COMPACT_EAST_CURRENT_WORLD_EXACT_STATE_ANIMATIONPLAYER_PLAYBACK_AND_LOOP"
SCHEMA = "axm.animation-compact-east-current-world-discrete-playback/v0.1"


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
    checks["all_16_exact_keys"] = (
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
    checks["all_states_seen_each_cycle"] = len(cycles) == 3 and all(
        sorted({int(v) for v in cycle}) == list(range(16)) for cycle in cycles
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
        "schema": "axm.animation-compact-east-current-world-playback-evidence/v0.1",
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
        "real_playback_wrap_times_s": runtime["real_playback_wrap_times_s"],
        "real_playback_cycle_durations_s": runtime["real_playback_cycle_durations_s"],
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
