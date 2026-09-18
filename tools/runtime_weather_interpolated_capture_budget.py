from __future__ import annotations

import argparse
import copy
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

try:
    from . import environment_weather_width_current_world as width
    from . import environment_weather_width_interpolated as interpolated
except ImportError:
    import environment_weather_width_current_world as width
    import environment_weather_width_interpolated as interpolated

SCHEMA = "axm.runtime-weather-interpolated-capture-budget/v0.1"
STATUS = "PASS_DEFERRED_CAPTURE_REDUCES_INTERPOLATION_OBSERVER_PERTURBATION"
DECISION = "INLINE_PNG_READBACK_IS_MATERIAL_PROOF_HARNESS_COST"
CAPTURE_POLICY = "DEFER_PNG_READBACK_UNTIL_AFTER_TIMED_SEQUENCE"
TIMED_FRAME_STATE = "DEFERRED_FROM_TIMED_LOOP"
CONTEXTS = ("path_eye", "elevated_oblique")
GAP_RATIO_LIMIT = 0.25
MIN_SAMPLE_GAIN = 2


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _median(values: list[float]) -> float:
    return float(statistics.median(values)) if values else 0.0


def _mean(values: list[float]) -> float:
    return float(statistics.mean(values)) if values else 0.0


def _gap_metrics(samples: list[dict[str, Any]]) -> dict[str, float]:
    selection_submit = [
        (float(row["submit_time_s"]) - float(row["selection_time_s"])) * 1000.0
        for row in samples
    ]
    submit_draw = [
        (float(row["draw_time_s"]) - float(row["submit_time_s"])) * 1000.0
        for row in samples
    ]
    draw_next_selection = [
        (float(samples[index]["selection_time_s"]) - float(samples[index - 1]["draw_time_s"])) * 1000.0
        for index in range(1, len(samples))
    ]
    draw_intervals = [
        (float(samples[index]["draw_time_s"]) - float(samples[index - 1]["draw_time_s"])) * 1000.0
        for index in range(1, len(samples))
    ]
    return {
        "mean_selection_to_submit_ms": _mean(selection_submit),
        "median_selection_to_submit_ms": _median(selection_submit),
        "mean_submit_to_draw_ms": _mean(submit_draw),
        "median_submit_to_draw_ms": _median(submit_draw),
        "mean_draw_to_next_selection_ms": _mean(draw_next_selection),
        "median_draw_to_next_selection_ms": _median(draw_next_selection),
        "mean_draw_interval_ms": _mean(draw_intervals),
        "median_draw_interval_ms": _median(draw_intervals),
    }


def _verify_candidate_context(
    payload: dict[str, Any],
    block: dict[str, Any],
    candidate_image_root: Path,
) -> tuple[bool, dict[str, Any]]:
    states = {int(row.get("index", -1)): row for row in payload.get("states", [])}
    samples = block.get("samples", [])
    valid = (
        block.get("state") == interpolated.CONTEXT_STATE
        and block.get("presentation_policy") == interpolated.PRESENTATION_POLICY
        and block.get("interpolation_semantics") == interpolated.INTERPOLATION_SEMANTICS
        and block.get("runtime_capture_policy") == CAPTURE_POLICY
        and len(samples) >= 5
    )

    previous_source_time = -1.0
    weather_ids: set[tuple[int, int, int]] = set()
    sapling_ids: set[tuple[int, int, int]] = set()
    maximum_width_residual = 0.0
    inline_capture_absent = True
    brackets_exact = True
    phase_exact = True
    ordered = True

    for sample in samples:
        lower_index = int(sample.get("lower_index", -1))
        upper_index = int(sample.get("upper_index", -1))
        alpha = float(sample.get("alpha", -1.0))
        source_time = float(sample.get("source_time_s", -1.0))
        selection_time = float(sample.get("selection_time_s", -1.0))
        submit_time = float(sample.get("submit_time_s", -1.0))
        draw_time = float(sample.get("draw_time_s", -1.0))
        lower = states.get(lower_index, {})
        upper = states.get(upper_index, {})

        bracket_ok = bool(lower) and bool(upper) and 0.0 <= alpha <= 1.0
        if lower_index == interpolated.LAST_SOURCE_INDEX:
            bracket_ok = bracket_ok and upper_index == interpolated.LAST_SOURCE_INDEX and abs(alpha) <= 1e-9
        else:
            bracket_ok = bracket_ok and upper_index == lower_index + 1
            bracket_ok = bracket_ok and abs(source_time - (lower_index + alpha) * interpolated.SOURCE_INTERVAL_S) <= 1e-6
        bracket_ok = bracket_ok and (
            str(sample.get("lower_weather_field_digest", "")) == str(lower.get("weather_field_digest", ""))
            and str(sample.get("upper_weather_field_digest", "")) == str(upper.get("weather_field_digest", ""))
            and str(sample.get("lower_weather_width_profile_digest", "")) == str(lower.get("weather_width_profile_digest", ""))
            and str(sample.get("upper_weather_width_profile_digest", "")) == str(upper.get("weather_width_profile_digest", ""))
            and str(sample.get("lower_sapling_mesh_digest", "")) == str(lower.get("sapling_mesh_digest", ""))
            and str(sample.get("upper_sapling_mesh_digest", "")) == str(upper.get("sapling_mesh_digest", ""))
        )
        brackets_exact = brackets_exact and bracket_ok

        phase_target = min(max(selection_time, 0.0), interpolated.LAST_SOURCE_TIME_S)
        phase_ok = abs(source_time - phase_target) <= interpolated.PHASE_TOL_S and source_time > previous_source_time
        phase_exact = phase_exact and phase_ok
        previous_source_time = source_time
        ordered = ordered and selection_time <= submit_time <= draw_time
        inline_capture_absent = inline_capture_absent and sample.get("frame", {}).get("state") == TIMED_FRAME_STATE

        weather_update = sample.get("weather_update", {})
        sapling_update = sample.get("sapling_update", {})
        residual = float(weather_update.get("maximum_projected_width_residual_px", 999.0))
        maximum_width_residual = max(maximum_width_residual, residual)
        valid = valid and (
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

    stable_resources = len(weather_ids) == 1 and len(sapling_ids) == 1
    final_exact = bool(samples) and int(samples[-1].get("lower_index", -1)) == interpolated.LAST_SOURCE_INDEX

    deferred = block.get("deferred_capture", {})
    deferred_path = candidate_image_root / str(deferred.get("path", ""))
    deferred_ok = (
        deferred.get("state") == "PASS_CAPTURED_FRAME"
        and int(deferred.get("width", 0)) == 1100
        and int(deferred.get("height", 0)) == 720
        and deferred_path.exists()
        and bool(deferred.get("sha256"))
        and _sha256(deferred_path) == str(deferred.get("sha256"))
    )

    valid = valid and brackets_exact and phase_exact and ordered and inline_capture_absent and stable_resources and final_exact and deferred_ok
    metrics = _gap_metrics(samples)
    metrics.update({
        "sample_count": len(samples),
        "maximum_projected_width_residual_px": maximum_width_residual,
        "timed_sequence_duration_ms": float(block.get("timed_sequence_duration_ms", -1.0)),
        "deferred_capture_duration_ms": float(block.get("deferred_capture_duration_ms", -1.0)),
        "deferred_capture_sha256": str(deferred.get("sha256", "")),
        "deferred_capture_path": str(deferred.get("path", "")),
        "inline_capture_absent": inline_capture_absent,
        "stable_resources": stable_resources,
        "final_exact_source_state_reached": final_exact,
    })
    return valid, metrics


def verify(
    payload: dict[str, Any],
    control_receipt: dict[str, Any],
    control_report: dict[str, Any],
    candidate_receipt: dict[str, Any],
    control_image_root: str | Path,
    candidate_image_root: str | Path,
) -> dict[str, Any]:
    control_root = Path(control_image_root)
    candidate_root = Path(candidate_image_root)
    checks: dict[str, bool] = {
        "source_width_structure_passed": payload.get("status") == width.STATUS and all(payload.get("checks", {}).values()),
        "control_vfx_interpolation_proof_passed": control_report.get("state") == interpolated.STATUS and all(control_report.get("checks", {}).values()),
        "control_and_candidate_share_exact_receiving_head": control_receipt.get("receiving_head") == payload.get("receiving_head") == candidate_receipt.get("receiving_head"),
        "candidate_preserves_vfx_interpolation_schema_state_policy": (
            candidate_receipt.get("schema") == interpolated.OBSERVATION_SCHEMA
            and candidate_receipt.get("state") == interpolated.OBSERVATION_STATE
            and candidate_receipt.get("presentation_policy") == interpolated.PRESENTATION_POLICY
            and candidate_receipt.get("interpolation_semantics") == interpolated.INTERPOLATION_SEMANTICS
        ),
        "both_fixed_contexts_present_in_both_modes": set(control_receipt.get("contexts", {})) == set(CONTEXTS) == set(candidate_receipt.get("contexts", {})),
    }

    context_metrics: dict[str, Any] = {}
    candidate_contexts_valid = True
    observer_gap_reduced = True
    sample_count_improved = True
    final_frames_identical = True

    for context in CONTEXTS:
        control_block = control_receipt["contexts"][context]
        candidate_block = candidate_receipt["contexts"][context]
        control_samples = control_block.get("samples", [])
        candidate_valid, candidate_metrics = _verify_candidate_context(payload, candidate_block, candidate_root)
        candidate_contexts_valid = candidate_contexts_valid and candidate_valid
        control_metrics = _gap_metrics(control_samples)
        control_metrics["sample_count"] = len(control_samples)

        control_gap = float(control_metrics["median_draw_to_next_selection_ms"])
        candidate_gap = float(candidate_metrics["median_draw_to_next_selection_ms"])
        gap_ratio = candidate_gap / control_gap if control_gap > 0.0 else 999.0
        sample_gain = int(candidate_metrics["sample_count"]) - int(control_metrics["sample_count"])
        observer_gap_reduced = observer_gap_reduced and gap_ratio <= GAP_RATIO_LIMIT
        sample_count_improved = sample_count_improved and sample_gain >= MIN_SAMPLE_GAIN

        control_final = control_samples[-1].get("frame", {}) if control_samples else {}
        control_final_path = control_root / str(control_final.get("path", ""))
        control_final_ok = (
            control_final.get("state") == "PASS_CAPTURED_FRAME"
            and control_final_path.exists()
            and _sha256(control_final_path) == str(control_final.get("sha256", ""))
        )
        candidate_final_hash = str(candidate_metrics.get("deferred_capture_sha256", ""))
        frame_equal = control_final_ok and candidate_final_hash == str(control_final.get("sha256", ""))
        final_frames_identical = final_frames_identical and frame_equal

        context_metrics[context] = {
            "control": control_metrics,
            "candidate": candidate_metrics,
            "median_draw_to_next_selection_ratio": gap_ratio,
            "timed_sample_gain": sample_gain,
            "final_exact_frame_byte_identical": frame_equal,
        }

    checks.update({
        "candidate_context_contract_valid": candidate_contexts_valid,
        "deferred_capture_cuts_post_draw_observer_gap_to_at_most_quarter_control": observer_gap_reduced,
        "deferred_capture_yields_at_least_two_more_timed_samples_per_context": sample_count_improved,
        "final_exact_source_frame_remains_byte_identical_per_context": final_frames_identical,
    })

    state = STATUS if all(checks.values()) else "FAIL"
    return {
        "schema": SCHEMA,
        "state": state,
        "decision": DECISION if state == STATUS else "NO_DECISION",
        "receiving_head": payload.get("receiving_head"),
        "vfx_parent_head": "03beb813a852d3c019cc10c41cabe161ac5f50b5",
        "capture_policy": CAPTURE_POLICY,
        "checks": checks,
        "context_metrics": context_metrics,
        "tradeoff": (
            "Timed presentation measurement no longer retains a PNG for every presented sample. One exact final frame per fixed camera is captured only after the timed sequence, preserving a direct byte-identical visual anchor while removing evidence readback/PNG encoding from the timed critical path."
        ),
        "truth_boundary": (
            "PASS proves only that inline PNG readback/encoding materially perturbs this exact Godot proof harness and that deferring it reduces the post-draw observer gap while preserving the final exact rendered state in both fixed cameras. It does not prove authored 32 Hz delivery, a product-runtime speedup, target-device CPU/GPU/FPS/VRAM behavior, temporal visual equivalence, arbitrary cameras/resolutions, VFX adoption, physical Weather, gameplay, CANON, production readiness, or Runtime mastery."
        ),
    }


def exercise_capture_policy_negative_control(
    payload: dict[str, Any],
    control_receipt: dict[str, Any],
    control_report: dict[str, Any],
    candidate_receipt: dict[str, Any],
    control_image_root: str | Path,
    candidate_image_root: str | Path,
) -> dict[str, Any]:
    mutated = copy.deepcopy(candidate_receipt)
    first = CONTEXTS[0]
    mutated["contexts"][first]["runtime_capture_policy"] = "DRIFTED_CAPTURE_POLICY"
    return verify(payload, control_receipt, control_report, mutated, control_image_root, candidate_image_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--control-receipt", required=True)
    parser.add_argument("--control-report", required=True)
    parser.add_argument("--candidate-receipt", required=True)
    parser.add_argument("--control-image-root", required=True)
    parser.add_argument("--candidate-image-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = _load(args.payload)
    control_receipt = _load(args.control_receipt)
    control_report = _load(args.control_report)
    candidate_receipt = _load(args.candidate_receipt)
    report = verify(
        payload,
        control_receipt,
        control_report,
        candidate_receipt,
        args.control_image_root,
        args.candidate_image_root,
    )
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
