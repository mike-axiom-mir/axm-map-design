from __future__ import annotations

import argparse
import copy
import json
import statistics
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-weather-temporal-exposure-runtime-budget/v0.1"
STATUS = "PASS_TWO_TAP_TEMPORAL_EXPOSURE_RUNTIME_COST_CHARACTERIZED"
DECISION = "HOLD_PERFORMANCE_NEUTRALITY__TWO_TAP_RECEIVING_COST_IS_NONZERO"
SOURCE_VFX_HEAD = "92cfe5d0dc7e254c1c3e19c5fc168298dea3493a"
SOURCE_VFX_TARGET_STATE = "PASS_BOUNDED_TEMPORAL_EXPOSURE_VISUAL_CANDIDATE"
OBSERVATION_SCHEMA = "axm.environment-weather-temporal-exposure-runtime-observation/v0.1"
OBSERVATION_STATE = "PASS_TEMPORAL_EXPOSURE_RUNTIME_OBSERVATION"
POLICY = "TWO_TAP_HALF_OPACITY_RECEIVING_ONLY_TEMPORAL_EXPOSURE"
CONTROL_MODE = "single_tap_control"
CANDIDATE_MODE = "two_tap_temporal_exposure"
CONTEXTS = ("path_eye", "elevated_oblique")
REVIEW_PHASES_US = (0, 62500, 125000, 187500, 250000, 312500, 375000, 437500, 500000)
COUNTER_KEYS = (
    "draw_calls_in_frame",
    "objects_in_frame",
    "primitives_in_frame",
    "buffer_mem_bytes",
    "texture_mem_bytes",
)


def _median(values: list[int | float]) -> float:
    return float(statistics.median(values)) if values else 0.0


def _mean(values: list[int | float]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def _counter(sample: dict[str, Any]) -> dict[str, int]:
    runtime = sample.get("runtime", {})
    return {key: int(runtime.get(key, -1)) for key in COUNTER_KEYS}


def _resource_set(block: dict[str, Any], key: str) -> set[tuple[int, int, int]]:
    return {
        tuple(int(value) for value in row)
        for row in block.get(key, [])
        if isinstance(row, list) and len(row) == 3
    }


def _context_ok(receipt: dict[str, Any], context: str, expected_count: int) -> bool:
    block = receipt.get("contexts", {}).get(context, {})
    samples = block.get("samples", [])
    if block.get("state") != "PASS_TEMPORAL_EXPOSURE_RUNTIME_CONTEXT_OBSERVED":
        return False
    if len(samples) != len(REVIEW_PHASES_US):
        return False
    if [int(row.get("phase_us", -1)) for row in samples] != list(REVIEW_PHASES_US):
        return False
    if any(int(row.get("source_streak_count", -1)) != 36 for row in samples):
        return False
    if any(int(row.get("presentation_streak_count", -1)) != expected_count for row in samples):
        return False
    if any(row.get("weather_update", {}).get("state") != "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS" for row in samples):
        return False
    if any(int(row.get("weather_update", {}).get("streak_count", -1)) != expected_count for row in samples):
        return False
    if any(int(row.get("weather_update", {}).get("measured_width_count", -1)) != expected_count for row in samples):
        return False
    if any(float(row.get("weather_update", {}).get("maximum_projected_width_residual_px", 999.0)) > 0.05 for row in samples):
        return False
    if len(_resource_set(block, "weather_resource_ids")) != 1:
        return False
    if len(_resource_set(block, "sapling_resource_ids")) != 1:
        return False
    return True


def _compare_context(control: dict[str, Any], candidate: dict[str, Any], context: str) -> dict[str, Any]:
    c_samples = control["contexts"][context]["samples"]
    t_samples = candidate["contexts"][context]["samples"]
    control_counters = [_counter(row) for row in c_samples]
    candidate_counters = [_counter(row) for row in t_samples]
    deltas = [
        {key: candidate_counters[index][key] - control_counters[index][key] for key in COUNTER_KEYS}
        for index in range(len(c_samples))
    ]

    counter_summary: dict[str, Any] = {}
    for key in COUNTER_KEYS:
        c_values = [row[key] for row in control_counters]
        t_values = [row[key] for row in candidate_counters]
        d_values = [row[key] for row in deltas]
        counter_summary[key] = {
            "control_min": min(c_values),
            "control_median": _median(c_values),
            "control_max": max(c_values),
            "candidate_min": min(t_values),
            "candidate_median": _median(t_values),
            "candidate_max": max(t_values),
            "delta_min": min(d_values),
            "delta_median": _median(d_values),
            "delta_max": max(d_values),
            "delta_unique": sorted(set(d_values)),
        }

    c_prepare = [int(row.get("prepare_usec", -1)) for row in c_samples]
    t_prepare = [int(row.get("prepare_usec", -1)) for row in t_samples]
    c_fill = [int(row.get("fill_usec", -1)) for row in c_samples]
    t_fill = [int(row.get("fill_usec", -1)) for row in t_samples]
    t_build = [int(row.get("build_usec", -1)) for row in t_samples]
    c_postdraw = [int(row.get("postdraw_wait_usec", -1)) for row in c_samples]
    t_postdraw = [int(row.get("postdraw_wait_usec", -1)) for row in t_samples]

    brackets_match = all(
        c_samples[index].get("current_bracket") == t_samples[index].get("current_bracket")
        for index in range(len(c_samples))
    )
    candidate_exposure_contract = all(
        row.get("exposure_build", {}).get("state") == "PASS_BOUNDED_TEMPORAL_EXPOSURE_LINES"
        and int(row.get("exposure_build", {}).get("source_streak_count", -1)) == 36
        and int(row.get("exposure_build", {}).get("presentation_tap_count", -1)) == 72
        for row in t_samples
    )

    control_prepare_median = _median(c_prepare)
    candidate_prepare_median = _median(t_prepare)
    return {
        "phase_and_current_brackets_match": brackets_match,
        "candidate_exposure_contract_exact": candidate_exposure_contract,
        "counters": counter_summary,
        "weather_prepare_usec": {
            "control_median": control_prepare_median,
            "control_mean": _mean(c_prepare),
            "control_min": min(c_prepare),
            "control_max": max(c_prepare),
            "candidate_median": candidate_prepare_median,
            "candidate_mean": _mean(t_prepare),
            "candidate_min": min(t_prepare),
            "candidate_max": max(t_prepare),
            "candidate_to_control_median_ratio": (
                candidate_prepare_median / control_prepare_median if control_prepare_median > 0 else None
            ),
            "candidate_build_median": _median(t_build),
            "control_fill_median": _median(c_fill),
            "candidate_fill_median": _median(t_fill),
        },
        "postdraw_wait_usec": {
            "control_median": _median(c_postdraw),
            "candidate_median": _median(t_postdraw),
            "control_mean": _mean(c_postdraw),
            "candidate_mean": _mean(t_postdraw),
        },
    }


def characterize(
    payload: dict[str, Any],
    parent_target: dict[str, Any],
    control: dict[str, Any],
    candidate: dict[str, Any],
    exact_runtime_head: str,
) -> dict[str, Any]:
    checks: dict[str, bool] = {
        "exact_source_vfx_head": payload.get("receiving_head") == SOURCE_VFX_HEAD,
        "source_width_structure_pass": payload.get("status") == "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE" and all(payload.get("checks", {}).values()),
        "vfx_parent_visual_candidate_pass": parent_target.get("state") == SOURCE_VFX_TARGET_STATE and all(parent_target.get("checks", {}).values()),
        "vfx_parent_identity_matches_payload": parent_target.get("receiving_head") == SOURCE_VFX_HEAD,
        "control_observation_contract": control.get("schema") == OBSERVATION_SCHEMA and control.get("state") == OBSERVATION_STATE and control.get("mode") == CONTROL_MODE,
        "candidate_observation_contract": candidate.get("schema") == OBSERVATION_SCHEMA and candidate.get("state") == OBSERVATION_STATE and candidate.get("mode") == CANDIDATE_MODE,
        "both_observations_bind_exact_vfx_head": control.get("source_vfx_head") == candidate.get("source_vfx_head") == SOURCE_VFX_HEAD,
        "policy_identity_preserved": control.get("presentation_policy") == candidate.get("presentation_policy") == POLICY,
        "measurement_loop_excludes_image_readback": control.get("capture_policy") == candidate.get("capture_policy") == "NO_IMAGE_READBACK_OR_ENCODING_IN_MEASUREMENT_LOOP",
        "exact_review_phases_preserved": tuple(int(v) for v in control.get("review_phases_us", [])) == REVIEW_PHASES_US and tuple(int(v) for v in candidate.get("review_phases_us", [])) == REVIEW_PHASES_US,
        "control_exact_36_ribbons": int(control.get("expected_presentation_streak_count", -1)) == 36,
        "candidate_exact_72_ribbons": int(candidate.get("expected_presentation_streak_count", -1)) == 72,
        "both_fixed_contexts_present": set(control.get("contexts", {})) == set(CONTEXTS) and set(candidate.get("contexts", {})) == set(CONTEXTS),
        "runtime_head_is_distinct_child": bool(exact_runtime_head) and exact_runtime_head != SOURCE_VFX_HEAD,
    }

    contexts: dict[str, Any] = {}
    for context in CONTEXTS:
        checks[f"{context}_control_context_exact"] = _context_ok(control, context, 36)
        checks[f"{context}_candidate_context_exact"] = _context_ok(candidate, context, 72)
        if checks[f"{context}_control_context_exact"] and checks[f"{context}_candidate_context_exact"]:
            contexts[context] = _compare_context(control, candidate, context)
            counters = contexts[context]["counters"]
            checks[f"{context}_current_phase_identity_same"] = contexts[context]["phase_and_current_brackets_match"]
            checks[f"{context}_candidate_exposure_build_exact"] = contexts[context]["candidate_exposure_contract_exact"]
            checks[f"{context}_single_mesh_keeps_draw_call_count"] = counters["draw_calls_in_frame"]["delta_unique"] == [0]
            checks[f"{context}_single_node_keeps_object_count"] = counters["objects_in_frame"]["delta_unique"] == [0]
            checks[f"{context}_extra_temporal_geometry_is_rendered"] = counters["primitives_in_frame"]["delta_min"] > 0
        else:
            contexts[context] = {}
            checks[f"{context}_current_phase_identity_same"] = False
            checks[f"{context}_candidate_exposure_build_exact"] = False
            checks[f"{context}_single_mesh_keeps_draw_call_count"] = False
            checks[f"{context}_single_node_keeps_object_count"] = False
            checks[f"{context}_extra_temporal_geometry_is_rendered"] = False

    state = STATUS if all(checks.values()) else "FAIL"
    return {
        "schema": SCHEMA,
        "state": state,
        "decision": DECISION if state == STATUS else "HOLD_FAILED_RUNTIME_COST_GATE",
        "runtime_head": exact_runtime_head,
        "source_vfx_head": SOURCE_VFX_HEAD,
        "source_vfx_target_state": parent_target.get("state"),
        "presentation_policy": POLICY,
        "control_presentation_streak_count": 36,
        "candidate_presentation_streak_count": 72,
        "checks": checks,
        "contexts": contexts,
        "parent_visual_metrics": parent_target.get("context_metrics", {}),
        "visual_tradeoff_for_art_direction": (
            "Runtime changes no VFX pixels or temporal-exposure semantics. The exact VFX parent reports a small Weather-local direct delta and lower deterministic inter-frame mean-absolute-RGB medians, while explicitly retaining possible short ghosting / broader atmospheric footprint as an Art Direction and Visual QA decision. This Runtime pass only measures the representation cost of carrying 72 receiving ribbons for 36 source streaks."
        ),
        "reuse_boundary": (
            "The reusable contract is that a presentation effect which preserves draw/object counts by batching into one mutable mesh can still add primitive work, buffer pressure and CPU-side materialization cost. Runtime acceptance must therefore bind the complete observed counter/timing tuple rather than treating unchanged draw calls as performance neutrality."
        ),
        "truth_boundary": (
            "PASS characterizes only the exact two-process Godot 4.7.2 GL Compatibility proof-host A/B at the nine deterministic VFX review phases. It does not prove authored 32 Hz delivery, target-device CPU/GPU frame time, FPS, VRAM/heap residency, arbitrary cameras/resolutions, physical Weather, gameplay, final visual preference, VFX adoption, CANON, production readiness or Runtime mastery. Timing values are proof-host observations and not target-device budgets."
        ),
    }


def exercise_presentation_count_negative_control(
    payload: dict[str, Any],
    parent_target: dict[str, Any],
    control: dict[str, Any],
    candidate: dict[str, Any],
    exact_runtime_head: str,
) -> dict[str, Any]:
    mutated = copy.deepcopy(candidate)
    first_context = CONTEXTS[0]
    mutated["contexts"][first_context]["samples"][0]["presentation_streak_count"] = 71
    return characterize(payload, parent_target, control, mutated, exact_runtime_head)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--parent-target", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--exact-head", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text())
    parent_target = json.loads(args.parent_target.read_text())
    control = json.loads(args.control.read_text())
    candidate = json.loads(args.candidate.read_text())
    exact_runtime_head = args.exact_head.read_text().strip()
    result = characterize(payload, parent_target, control, candidate, exact_runtime_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "state": result["state"],
        "decision": result["decision"],
        "contexts": result["contexts"],
    }, indent=2, sort_keys=True))
    return 0 if result["state"] == STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
