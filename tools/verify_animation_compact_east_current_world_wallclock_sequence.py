from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PREDECESSOR_HEAD = "48dc93848aa336f9b6079ccfe738acbe539253ac"
PARENT_HEAD = "29ef2d4cc4398b3f26290e4e1f1f10398ca9898c"
SCHEMA = "axm.animation-compact-east-current-world-wallclock-sequence/v0.1"
RUNTIME_RESULT = "PASS_COMPACT_EAST_CURRENT_WORLD_REVIEWABLE_WALL_CLOCK_FRAME_SEQUENCE_RETAINED"
CAPTURE_SEMANTICS = "FRAME_POST_DRAW_RENDERED_SEQUENCE_WITH_IMAGE_READBACK_INSTRUMENTATION_NOT_UNINSTRUMENTED_DISPLAY_SCANOUT"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(predecessor: dict[str, Any], runtime: dict[str, Any], frame_dir: Path) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    checks["predecessor_pass"] = predecessor.get("state") == "PASS_COMPACT_EAST_CURRENT_WORLD_EXACT_KEY_BINDING_AND_REAL_LOOP_DELIVERY_CHARACTERIZED"
    checks["predecessor_full_delivery_not_accepted"] = predecessor.get("full_source_state_delivery_accepted") is False
    checks["schema"] = runtime.get("schema") == SCHEMA
    checks["runtime_pass"] = runtime.get("state") == RUNTIME_RESULT
    checks["predecessor_head"] = runtime.get("exact_playback_predecessor_head") == PREDECESSOR_HEAD
    checks["parent_head"] = runtime.get("parent_vfx_receiving_head") == PARENT_HEAD
    checks["source_frozen"] = (
        float(runtime.get("duration_s", -1.0)) == 0.5
        and int(runtime.get("intervals", -1)) == 16
        and int(runtime.get("authored_endpoint_inclusive_states", -1)) == 17
        and int(runtime.get("loop_track_unique_states", -1)) == 16
        and abs(float(runtime.get("source_step_s", -1.0)) - 0.03125) <= 1e-12
        and runtime.get("source_motion_truth") == "DISCRETE_EXACT_VFX_STATES_NOT_SMOOTH_INTERPOLATION"
        and runtime.get("animation_track_interpolation") == "NEAREST"
        and runtime.get("animation_update_mode") == "DISCRETE"
        and runtime.get("animation_loop_mode") == "LOOP_LINEAR"
    )
    checks["endpoint_exact"] = float(runtime.get("source_endpoint_geometry_delta_m", 1.0)) <= 1e-12
    checks["warmup_then_two_loops"] = int(runtime.get("warmup_wraps", 0)) >= 1 and int(runtime.get("captured_complete_loops", -1)) == 2
    checks["capture_semantics"] = runtime.get("capture_semantics") == CAPTURE_SEMANTICS
    checks["persistent_receiver"] = int(runtime.get("persistent_receiver_instance_id", 0)) > 0 and int(runtime.get("persistent_animation_player_instance_id", 0)) > 0
    checks["unrelated_motion_frozen"] = int(runtime.get("frozen_weather_phase", -1)) == 0 and int(runtime.get("frozen_west_sapling_phase", -1)) == 0
    checks["acceptance_boundaries"] = (
        runtime.get("full_source_state_delivery_accepted") is False
        and runtime.get("visual_motion_naturalness_accepted") is False
        and runtime.get("display_scanout_accepted") is False
        and runtime.get("runtime_controller_accepted") is False
        and runtime.get("gameplay_accepted") is False
    )

    frames = runtime.get("rendered_frames", [])
    checks["frame_count"] = len(frames) == int(runtime.get("rendered_frame_count", -1)) and len(frames) >= 8
    timestamps = [float(row.get("timestamp_s", -1.0)) for row in frames]
    checks["timestamps_monotonic"] = bool(timestamps) and abs(timestamps[0]) <= 1e-12 and all(b >= a for a, b in zip(timestamps, timestamps[1:]))
    checks["valid_phase_identity"] = all(0 <= int(row.get("observed_phase", -1)) < 16 for row in frames)
    checks["valid_animation_position"] = all(-1e-9 <= float(row.get("animation_position_s", -1.0)) <= 0.500001 for row in frames)
    checks["frame_dimensions"] = all(int(row.get("width", 0)) == 1100 and int(row.get("height", 0)) == 720 for row in frames)

    files = sorted(frame_dir.glob("animation-wallclock-frame-*.png"))
    checks["frame_files_match"] = len(files) == len(frames)
    retained: list[dict[str, Any]] = []
    if len(files) == len(frames):
        for index, (row, path) in enumerate(zip(frames, files)):
            expected_name = Path(str(row.get("path", ""))).name
            file_ok = path.name == expected_name and path.is_file() and path.stat().st_size > 0
            if not file_ok:
                checks["frame_files_match"] = False
            retained.append({
                "sequence_index": index,
                "name": path.name,
                "bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": digest(path) if path.is_file() else "",
                "timestamp_s": row.get("timestamp_s"),
                "animation_position_s": row.get("animation_position_s"),
                "observed_phase": row.get("observed_phase"),
                "wrapped": row.get("wrapped"),
                "cycle_index": row.get("cycle_index"),
            })

    cycles = runtime.get("captured_cycles_observed_phases", [])
    missing = runtime.get("captured_cycles_missing_phases", [])
    expected_missing = [
        [phase for phase in range(16) if phase not in {int(v) for v in cycle}]
        for cycle in cycles
    ]
    checks["two_characterized_cycles"] = len(cycles) == 2 and all(len({int(v) for v in cycle}) >= 3 for cycle in cycles)
    checks["missing_phase_characterization_consistent"] = missing == expected_missing
    checks["closing_seam_frame_retained"] = sum(1 for row in frames if bool(row.get("wrapped", False))) >= 3
    checks["capture_intervals_recorded"] = (
        float(runtime.get("capture_frame_interval_min_ms", -1.0)) >= 0.0
        and float(runtime.get("capture_frame_interval_mean_ms", -1.0)) >= 0.0
        and float(runtime.get("capture_frame_interval_max_ms", -1.0)) >= float(runtime.get("capture_frame_interval_min_ms", -1.0))
    )

    if not all(checks.values()):
        failed = [key for key, value in checks.items() if not value]
        raise ValueError(f"compact-east wall-clock rendered-sequence evidence failed: {failed}")

    return {
        "schema": "axm.animation-compact-east-current-world-wallclock-sequence-evidence/v0.1",
        "state": RUNTIME_RESULT,
        "exact_playback_predecessor_head": PREDECESSOR_HEAD,
        "parent_vfx_receiving_head": PARENT_HEAD,
        "checks": checks,
        "warmup_wraps": runtime["warmup_wraps"],
        "captured_complete_loops": runtime["captured_complete_loops"],
        "rendered_frame_count": runtime["rendered_frame_count"],
        "captured_cycles_observed_phases": cycles,
        "captured_cycles_missing_phases": missing,
        "capture_frame_interval_min_ms": runtime["capture_frame_interval_min_ms"],
        "capture_frame_interval_mean_ms": runtime["capture_frame_interval_mean_ms"],
        "capture_frame_interval_max_ms": runtime["capture_frame_interval_max_ms"],
        "full_source_state_delivery_accepted": runtime["full_source_state_delivery_accepted"],
        "visual_motion_naturalness_accepted": runtime["visual_motion_naturalness_accepted"],
        "display_scanout_accepted": runtime["display_scanout_accepted"],
        "runtime_controller_accepted": runtime["runtime_controller_accepted"],
        "gameplay_accepted": runtime["gameplay_accepted"],
        "retained_frames": retained,
        "truth_boundary": runtime.get("truth_boundary"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predecessor-report", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--frame-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(load(args.predecessor_report), load(args.runtime), args.frame_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
