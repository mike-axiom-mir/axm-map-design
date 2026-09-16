from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

try:
    from . import environment_weather_width_current_world as width
except ImportError:
    import environment_weather_width_current_world as width

SCHEMA = "axm.environment-current-world-weather-width-continuous-phase-target-host/v0.1"
STATUS = "PASS_CONTINUOUS_PHASE_VISUAL_INTERPOLATION_PRESENTATION_CANDIDATE"
OBSERVATION_SCHEMA = "axm.environment-current-world-weather-width-continuous-phase-observation/v0.1"
OBSERVATION_STATE = "OBSERVED_CONTINUOUS_PHASE_VISUAL_INTERPOLATION"
CONTEXT_STATE = "OBSERVED_CONTINUOUS_PHASE_CONTEXT"
CONTEXTS = ("path_eye", "elevated_oblique")
SOURCE_INTERVAL_S = 0.03125
LAST_SOURCE_INDEX = 16
LAST_SOURCE_TIME_S = 0.5
PRESENTATION_POLICY = "CONTINUOUS_PHASE_LINEAR_VISUAL_INTERPOLATION_PRESENTATION_ONLY"
INTERPOLATION_SEMANTICS = "INTERPOLATE_ONLY_RECEIVING_WEATHER_GEOMETRY_OPACITY_AND_SAPLING_VERTICES_BETWEEN_EXACT_AUTHORED_BRACKETS"
TARGET_REAR_ASSET_ID = "source:nature:east-rear-tree-neutral-001"
PHASE_TOL_S = 0.001


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_interpolated(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path) -> dict[str, Any]:
    root = Path(image_root)
    states = payload.get("states", [])
    expected = {int(row.get("index", -1)): row for row in states}
    receipt_contexts = receipt.get("contexts", {})

    all_contexts_valid = True
    all_brackets_exact = True
    all_phase_exact = True
    all_ordered = True
    all_widths = True
    all_resources_stable = True
    all_frames = True
    maximum_width_residual_px = 0.0
    measured_width_count = 0
    context_metrics: dict[str, Any] = {}

    for context in CONTEXTS:
        block = receipt_contexts.get(context, {})
        samples = block.get("samples", [])
        context_valid = (
            block.get("state") == CONTEXT_STATE
            and block.get("presentation_policy") == PRESENTATION_POLICY
            and block.get("interpolation_semantics") == INTERPOLATION_SEMANTICS
            and abs(float(block.get("source_interval_s", -1.0)) - SOURCE_INTERVAL_S) <= 1e-9
            and len(samples) >= 5
        )
        all_contexts_valid = all_contexts_valid and context_valid

        previous_source_time = -1.0
        previous_selection_time = -1.0
        phase_step_errors: list[float] = []
        fractional_count = 0
        max_selection_phase_error = 0.0
        max_submit_age = 0.0
        max_draw_age = 0.0
        weather_ids: set[tuple[int, int, int]] = set()
        sapling_ids: set[tuple[int, int, int]] = set()
        frame_hashes: list[str] = []

        for sample in samples:
            lower_index = int(sample.get("lower_index", -1))
            upper_index = int(sample.get("upper_index", -1))
            alpha = float(sample.get("alpha", -1.0))
            source_time = float(sample.get("source_time_s", -1.0))
            selection_time = float(sample.get("selection_time_s", -1.0))
            submit_time = float(sample.get("submit_time_s", -1.0))
            draw_time = float(sample.get("draw_time_s", -1.0))

            lower = expected.get(lower_index, {})
            upper = expected.get(upper_index, {})
            bracket_ok = bool(lower) and bool(upper) and 0.0 <= alpha <= 1.0
            if lower_index == LAST_SOURCE_INDEX:
                bracket_ok = bracket_ok and upper_index == LAST_SOURCE_INDEX and abs(alpha) <= 1e-9 and abs(source_time - LAST_SOURCE_TIME_S) <= 1e-9
            else:
                expected_source_time = (lower_index + alpha) * SOURCE_INTERVAL_S
                bracket_ok = bracket_ok and upper_index == lower_index + 1 and abs(source_time - expected_source_time) <= 1e-6
                if 1e-4 < alpha < 1.0 - 1e-4:
                    fractional_count += 1

            bracket_ok = bracket_ok and (
                str(sample.get("lower_weather_field_digest", "")) == str(lower.get("weather_field_digest", ""))
                and str(sample.get("upper_weather_field_digest", "")) == str(upper.get("weather_field_digest", ""))
                and str(sample.get("lower_weather_width_profile_digest", "")) == str(lower.get("weather_width_profile_digest", ""))
                and str(sample.get("upper_weather_width_profile_digest", "")) == str(upper.get("weather_width_profile_digest", ""))
                and str(sample.get("lower_sapling_mesh_digest", "")) == str(lower.get("sapling_mesh_digest", ""))
                and str(sample.get("upper_sapling_mesh_digest", "")) == str(upper.get("sapling_mesh_digest", ""))
            )
            all_brackets_exact = all_brackets_exact and bracket_ok

            phase_target = min(max(selection_time, 0.0), LAST_SOURCE_TIME_S)
            phase_error = abs(source_time - phase_target)
            max_selection_phase_error = max(max_selection_phase_error, phase_error)
            phase_ok = phase_error <= PHASE_TOL_S and source_time > previous_source_time
            if previous_selection_time >= 0.0 and source_time < LAST_SOURCE_TIME_S - 1e-9:
                phase_step_errors.append(abs((source_time - previous_source_time) - (selection_time - previous_selection_time)))
            all_phase_exact = all_phase_exact and phase_ok
            previous_source_time = source_time
            previous_selection_time = selection_time

            ordered = selection_time <= submit_time <= draw_time
            all_ordered = all_ordered and ordered
            max_submit_age = max(max_submit_age, float(sample.get("source_age_at_submit_ms", -1.0)))
            max_draw_age = max(max_draw_age, float(sample.get("source_age_at_draw_ms", -1.0)))

            weather_update = sample.get("weather_update", {})
            sapling_update = sample.get("sapling_update", {})
            residual = float(weather_update.get("maximum_projected_width_residual_px", 999.0))
            maximum_width_residual_px = max(maximum_width_residual_px, residual)
            measured_width_count += int(weather_update.get("measured_width_count", 0))
            all_widths = all_widths and (
                weather_update.get("state") == "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS"
                and int(weather_update.get("measured_width_count", 0)) == 36
                and residual <= width.WIDTH_RESIDUAL_TOL_PX
            )
            weather_ids.add((
                int(weather_update.get("node_instance_id", -1)),
                int(weather_update.get("mesh_instance_id", -1)),
                int(weather_update.get("material_instance_id", -1)),
            ))
            sapling_ids.add((
                int(sapling_update.get("node_instance_id", -1)),
                int(sapling_update.get("mesh_instance_id", -1)),
                int(sapling_update.get("material_instance_id", -1)),
            ))

            frame = sample.get("frame", {})
            path = root / str(frame.get("path", ""))
            frame_hash = str(frame.get("sha256", ""))
            frame_ok = (
                frame.get("state") == "PASS_CAPTURED_FRAME"
                and int(frame.get("width", 0)) == 1100
                and int(frame.get("height", 0)) == 720
                and path.exists()
                and bool(frame_hash)
                and _sha256(path) == frame_hash
            )
            all_frames = all_frames and frame_ok
            frame_hashes.append(frame_hash)

        resources_stable = (
            len(weather_ids) == 1
            and len(sapling_ids) == 1
            and next(iter(weather_ids), (-1, -1, -1))[0] > 0
            and next(iter(sapling_ids), (-1, -1, -1))[0] > 0
        )
        all_resources_stable = all_resources_stable and resources_stable
        frames_distinct = len(frame_hashes) == len(set(frame_hashes))
        all_frames = all_frames and frames_distinct
        context_valid = context_valid and fractional_count >= 2 and samples[-1].get("lower_index") == LAST_SOURCE_INDEX
        all_contexts_valid = all_contexts_valid and context_valid

        context_metrics[context] = {
            "presented_frame_count": len(samples),
            "fractional_interpolated_frame_count": fractional_count,
            "maximum_selection_phase_error_ms": max_selection_phase_error * 1000.0,
            "maximum_source_phase_step_error_ms": (max(phase_step_errors) * 1000.0) if phase_step_errors else 0.0,
            "maximum_source_age_at_submit_ms": max_submit_age,
            "maximum_source_age_at_draw_ms": max_draw_age,
            "retained_frame_hashes_unique": frames_distinct,
        }

    rear_modes = {
        str(row.get("proof_culling", ""))
        for row in receipt.get("static_source_meshes", [])
        if row.get("asset_id") == TARGET_REAR_ASSET_ID
    }

    checks = {
        "structure_passed_before_interpolation": payload.get("status") == width.STATUS and all(payload.get("checks", {}).values()),
        "observation_schema_and_state_exact": receipt.get("schema") == OBSERVATION_SCHEMA and receipt.get("state") == OBSERVATION_STATE,
        "exact_receiving_head_matches": receipt.get("receiving_head") == payload.get("receiving_head"),
        "exact_parent_variant_head_matches": receipt.get("parent_variant_head") == width.EXPECTED_PARENT_VARIANT_HEAD,
        "both_fixed_contexts_observed": set(receipt_contexts) == set(CONTEXTS),
        "presentation_policy_and_interpolation_semantics_exact": receipt.get("presentation_policy") == PRESENTATION_POLICY and receipt.get("interpolation_semantics") == INTERPOLATION_SEMANTICS,
        "continuous_phase_contexts_have_fractional_live_samples_and_reach_final_exact_state": all_contexts_valid,
        "every_interpolation_bracket_binds_adjacent_exact_source_rows": all_brackets_exact,
        "continuous_source_phase_tracks_selection_clock_without_discrete_state_quantization": all_phase_exact and all(metric["maximum_source_phase_step_error_ms"] <= 1.0 for metric in context_metrics.values()),
        "selection_submit_draw_order_preserved": all_ordered,
        "source_widths_remain_within_projection_tolerance": all_widths and maximum_width_residual_px <= width.WIDTH_RESIDUAL_TOL_PX,
        "stable_weather_and_sapling_resource_identity": all_resources_stable,
        "direct_retained_1100x720_frame_evidence_present_and_distinct": all_frames,
        "rear_tree_culling_state_preserved": rear_modes == {"CULL_BACK"},
    }

    return {
        "schema": SCHEMA,
        "state": STATUS if all(checks.values()) else "FAIL",
        "receiving_head": payload.get("receiving_head"),
        "parent_variant_head": width.EXPECTED_PARENT_VARIANT_HEAD,
        "presentation_policy": PRESENTATION_POLICY,
        "interpolation_semantics": INTERPOLATION_SEMANTICS,
        "checks": checks,
        "context_metrics": context_metrics,
        "measured_width_count": measured_width_count,
        "maximum_projected_width_residual_px": maximum_width_residual_px,
        "truth_boundary": (
            "PASS proves only that this exact Godot proof can synthesize receiving-only continuous-phase visual states between adjacent exact Weather + sapling brackets, while preserving source-authored streak width and direct frame evidence. The source states remain authority and every synthetic sample is bracketed by exact source digests. PASS does not prove authored 32 Hz delivery, final temporal aesthetics, physical weather, gameplay/physics, target-device performance, arbitrary cameras, CANON, production readiness, or mastery."
        ),
    }


def exercise_phase_drift_negative_control(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path) -> dict[str, Any]:
    mutated = copy.deepcopy(receipt)
    for context in CONTEXTS:
        samples = mutated.get("contexts", {}).get(context, {}).get("samples", [])
        if len(samples) >= 3:
            samples[1]["alpha"] = min(0.99, float(samples[1].get("alpha", 0.0)) + 0.2)
            break
    return verify_interpolated(payload, mutated, image_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = _load(args.payload)
    receipt = _load(args.receipt)
    report = verify_interpolated(payload, receipt, args.image_root)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
