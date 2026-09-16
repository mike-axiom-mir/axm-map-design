from __future__ import annotations

import argparse
import copy
import json
import statistics
from pathlib import Path
from typing import Any

try:
    from . import environment_weather_width_current_world as width
    from . import environment_weather_width_coalesced as coalesced
except ImportError:
    import environment_weather_width_current_world as width
    import environment_weather_width_coalesced as coalesced

SCHEMA = "axm.runtime-weather-width-latest-due-cache-target-host/v0.1"
STATUS = "PASS_LATEST_DUE_PREBUILT_CACHE_RUNTIME_CHARACTERIZED"
OBSERVATION_SCHEMA = "axm.runtime-weather-width-latest-due-cache-observation/v0.1"
OBSERVATION_STATE = "OBSERVED_LATEST_DUE_REBUILD_VS_PREBUILT_CACHE"
MODE_STATE = "OBSERVED_LATEST_DUE_RUNTIME_MODE"
CACHE_STATE = "PASS_EXACT_17_STATE_NATIVE_TYPE_CACHE"
VISUAL_STATE = "PASS_RETAINED_RUNTIME_VISUAL_PAIRS"
EXACT_VFX_LATEST_DUE_HEAD = "e95910c8c5c45cd8d51be3b259825cf85064efc2"
VFX_BASELINE_STATE = "PASS_LATEST_DUE_EXACT_SOURCE_STATE_PRESENTATION_FALLBACK"
CONTEXTS = ("path_eye", "elevated_oblique")
MODES = ("rebuild", "cached_swap")
REVIEW_INDICES = (0, 8, 16)


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _increasing(values: list[int]) -> bool:
    return all(b > a for a, b in zip(values, values[1:]))


def _mode_metrics(payload: dict[str, Any], block: dict[str, Any], expected_mode: str) -> tuple[dict[str, Any], bool]:
    states = {int(row["index"]): row for row in payload.get("states", [])}
    samples = block.get("samples", [])
    indices = [int(row.get("index", -1)) for row in samples]
    dropped = [int(v) for v in block.get("dropped_indices", [])]
    complement = [i for i in range(17) if i not in indices]
    valid = (
        block.get("state") == MODE_STATE
        and block.get("mode") == expected_mode
        and block.get("presentation_policy") == coalesced.PRESENTATION_POLICY
        and block.get("selection_semantics") == coalesced.SELECTION_SEMANTICS
        and abs(float(block.get("source_interval_s", -1.0)) - coalesced.SOURCE_INTERVAL_S) <= 1e-9
        and int(block.get("source_interval_us", -1)) == coalesced.SOURCE_INTERVAL_US
        and 2 <= len(samples) <= 17
        and indices[0] == 0
        and indices[-1] == 16
        and _increasing(indices)
        and dropped == complement
    )
    update_ms: list[float] = []
    selection_age: list[float] = []
    submit_age: list[float] = []
    draw_age: list[float] = []
    post_draw_ms: list[float] = []
    weather_mesh_ids: list[int] = []
    sapling_mesh_ids: list[int] = []
    max_residual = 0.0
    measured_widths = 0
    previous = -1
    for sample in samples:
        index = int(sample.get("index", -1))
        source = states.get(index, {})
        exact = (
            bool(source)
            and abs(float(sample.get("scheduled_time_s", -1.0)) - float(source.get("time_s", -2.0))) <= 1e-9
            and str(sample.get("weather_field_digest", "")) == str(source.get("weather_field_digest", ""))
            and str(sample.get("weather_width_profile_digest", "")) == str(source.get("weather_width_profile_digest", ""))
            and str(sample.get("sapling_mesh_digest", "")) == str(source.get("sapling_mesh_digest", ""))
            and int(sample.get("latest_due_index_at_selection", -1)) == index
            and [int(v) for v in sample.get("skipped_before", [])] == list(range(previous + 1, index))
        )
        selection = float(sample.get("selection_time_s", -1.0))
        submit = float(sample.get("submit_time_s", -1.0))
        draw = float(sample.get("draw_time_s", -1.0))
        exact = exact and 0.0 <= selection <= submit <= draw
        weather = sample.get("weather_update", {})
        sapling = sample.get("sapling_update", {})
        residual = float(weather.get("maximum_projected_width_residual_px", 999.0))
        exact = exact and (
            weather.get("state") == "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS"
            and int(weather.get("measured_width_count", 0)) == 36
            and residual <= width.WIDTH_RESIDUAL_TOL_PX
            and int(sapling.get("surface_count", 0)) > 0
            and int(sapling.get("source_vertex_count", 0)) > 0
            and int(sapling.get("source_triangle_count", 0)) > 0
        )
        frame = sample.get("frame", {})
        exact = exact and (
            frame.get("state") == "PASS_CAPTURED_FRAME"
            and int(frame.get("width", 0)) == 1100
            and int(frame.get("height", 0)) == 720
            and bool(frame.get("sha256"))
        )
        valid = valid and exact
        previous = index
        update_ms.append(float(sample.get("update_duration_ms", 999.0)))
        selection_age.append(float(sample.get("source_age_at_selection_ms", 999.0)))
        submit_age.append(float(sample.get("source_age_at_submit_ms", 999.0)))
        draw_age.append(float(sample.get("source_age_at_draw_ms", 999.0)))
        post_draw_ms.append(float(sample.get("post_draw_wait_ms", 999.0)))
        weather_mesh_ids.append(int(weather.get("mesh_instance_id", -1)))
        sapling_mesh_ids.append(int(sapling.get("mesh_instance_id", -1)))
        max_residual = max(max_residual, residual)
        measured_widths += int(weather.get("measured_width_count", 0))
    metrics = {
        "presented_state_count": len(indices),
        "presented_indices": indices,
        "dropped_state_count": len(dropped),
        "dropped_indices": dropped,
        "mean_update_duration_ms": statistics.fmean(update_ms) if update_ms else None,
        "maximum_update_duration_ms": max(update_ms) if update_ms else None,
        "maximum_source_age_at_selection_ms": max(selection_age) if selection_age else None,
        "maximum_source_age_at_submit_ms": max(submit_age) if submit_age else None,
        "maximum_source_age_at_draw_ms": max(draw_age) if draw_age else None,
        "mean_post_draw_wait_ms": statistics.fmean(post_draw_ms) if post_draw_ms else None,
        "maximum_projected_width_residual_px": max_residual,
        "measured_width_count": measured_widths,
        "weather_mesh_identity_count": len(set(weather_mesh_ids)),
        "sapling_mesh_identity_count": len(set(sapling_mesh_ids)),
    }
    return metrics, valid


def verify(payload: dict[str, Any], receipt: dict[str, Any], vfx_baseline: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    checks["exact_structure_passed"] = payload.get("status") == width.STATUS and all(payload.get("checks", {}).values())
    checks["runtime_observation_schema_state_exact"] = receipt.get("schema") == OBSERVATION_SCHEMA and receipt.get("state") == OBSERVATION_STATE
    checks["runtime_receiving_head_matches_payload"] = receipt.get("receiving_head") == payload.get("receiving_head")
    checks["exact_vfx_latest_due_parent_bound"] = receipt.get("exact_vfx_latest_due_head") == EXACT_VFX_LATEST_DUE_HEAD
    checks["vfx_retained_baseline_bound"] = (
        vfx_baseline.get("state") == VFX_BASELINE_STATE
        and vfx_baseline.get("receiving_head") == EXACT_VFX_LATEST_DUE_HEAD
        and vfx_baseline.get("presentation_policy") == coalesced.PRESENTATION_POLICY
        and vfx_baseline.get("selection_semantics") == coalesced.SELECTION_SEMANTICS
    )
    checks["same_latest_due_policy_preserved"] = (
        receipt.get("presentation_policy") == coalesced.PRESENTATION_POLICY
        and receipt.get("selection_semantics") == coalesced.SELECTION_SEMANTICS
        and abs(float(receipt.get("source_interval_s", -1.0)) - coalesced.SOURCE_INTERVAL_S) <= 1e-9
    )

    contexts = receipt.get("contexts", {})
    checks["both_fixed_contexts_observed"] = set(contexts) == set(CONTEXTS)
    report_contexts: dict[str, Any] = {}
    all_modes_valid = True
    all_cache_valid = True
    all_visuals_identical = True
    all_update_cost_lower = True
    all_control_stable_mesh_identity = True
    all_candidate_swaps_mesh_identity = True

    for context in CONTEXTS:
        block = contexts.get(context, {})
        cache = block.get("cache", {})
        rebuild_metrics, rebuild_valid = _mode_metrics(payload, block.get("rebuild", {}), "rebuild")
        cached_metrics, cached_valid = _mode_metrics(payload, block.get("cached_swap", {}), "cached_swap")
        all_modes_valid = all_modes_valid and rebuild_valid and cached_valid
        cache_valid = (
            cache.get("state") == CACHE_STATE
            and cache.get("resource_policy") == "17_NATIVE_IMMEDIATEMESH_WEATHER_PLUS_17_NATIVE_ARRAYMESH_SAPLING_PER_FIXED_CAMERA_CONTEXT"
            and len(cache.get("source_receipts", [])) == 17
            and float(cache.get("maximum_projected_width_residual_px", 999.0)) <= width.WIDTH_RESIDUAL_TOL_PX
            and float(cache.get("build_duration_ms", -1.0)) >= 0.0
        )
        all_cache_valid = all_cache_valid and cache_valid

        visuals = block.get("visuals", {})
        pairs = visuals.get("pairs", [])
        visuals_identical = visuals.get("state") == VISUAL_STATE and [int(p.get("index", -1)) for p in pairs] == list(REVIEW_INDICES)
        for pair in pairs:
            a = pair.get("rebuild", {})
            b = pair.get("cached", {})
            visuals_identical = visuals_identical and (
                a.get("state") == "PASS_CAPTURED_FRAME"
                and b.get("state") == "PASS_CAPTURED_FRAME"
                and a.get("sha256") == b.get("sha256")
                and int(a.get("width", 0)) == 1100
                and int(a.get("height", 0)) == 720
                and int(b.get("width", 0)) == 1100
                and int(b.get("height", 0)) == 720
            )
        all_visuals_identical = all_visuals_identical and visuals_identical

        update_lower = (
            cached_metrics["mean_update_duration_ms"] is not None
            and rebuild_metrics["mean_update_duration_ms"] is not None
            and float(cached_metrics["mean_update_duration_ms"]) < float(rebuild_metrics["mean_update_duration_ms"]) * 0.5
            and float(cached_metrics["maximum_update_duration_ms"]) < float(rebuild_metrics["maximum_update_duration_ms"])
        )
        all_update_cost_lower = all_update_cost_lower and update_lower
        all_control_stable_mesh_identity = all_control_stable_mesh_identity and (
            rebuild_metrics["weather_mesh_identity_count"] == 1 and rebuild_metrics["sapling_mesh_identity_count"] == 1
        )
        all_candidate_swaps_mesh_identity = all_candidate_swaps_mesh_identity and (
            cached_metrics["weather_mesh_identity_count"] == cached_metrics["presented_state_count"]
            and cached_metrics["sapling_mesh_identity_count"] == cached_metrics["presented_state_count"]
        )

        drop_delta = int(cached_metrics["dropped_state_count"]) - int(rebuild_metrics["dropped_state_count"])
        submit_age_delta = float(cached_metrics["maximum_source_age_at_submit_ms"]) - float(rebuild_metrics["maximum_source_age_at_submit_ms"])
        draw_age_delta = float(cached_metrics["maximum_source_age_at_draw_ms"]) - float(rebuild_metrics["maximum_source_age_at_draw_ms"])
        report_contexts[context] = {
            "cache": {
                "build_duration_ms": cache.get("build_duration_ms"),
                "observed_buffer_delta_bytes": cache.get("observed_buffer_delta_bytes"),
                "observed_texture_delta_bytes": cache.get("observed_texture_delta_bytes"),
            },
            "rebuild": rebuild_metrics,
            "cached_swap": cached_metrics,
            "comparison": {
                "dropped_state_delta_cached_minus_rebuild": drop_delta,
                "maximum_submit_source_age_delta_ms_cached_minus_rebuild": submit_age_delta,
                "maximum_draw_source_age_delta_ms_cached_minus_rebuild": draw_age_delta,
                "mean_update_duration_ratio_cached_over_rebuild": float(cached_metrics["mean_update_duration_ms"]) / float(rebuild_metrics["mean_update_duration_ms"]),
                "retained_review_pairs_byte_identical": visuals_identical,
            },
        }

    checks["both_modes_preserve_exact_source_latest_due_semantics"] = all_modes_valid
    checks["exact_native_type_cache_built_before_timing"] = all_cache_valid
    checks["cached_swap_reduces_timed_update_cost_by_at_least_half_in_both_contexts"] = all_update_cost_lower
    checks["control_preserves_stable_mutable_mesh_identity"] = all_control_stable_mesh_identity
    checks["candidate_truthfully_swaps_distinct_cached_meshes"] = all_candidate_swaps_mesh_identity
    checks["six_fixed_review_pairs_are_byte_identical"] = all_visuals_identical

    total_drop_rebuild = sum(int(report_contexts[c]["rebuild"]["dropped_state_count"]) for c in CONTEXTS)
    total_drop_cached = sum(int(report_contexts[c]["cached_swap"]["dropped_state_count"]) for c in CONTEXTS)
    submit_better_both = all(
        float(report_contexts[c]["cached_swap"]["maximum_source_age_at_submit_ms"])
        < float(report_contexts[c]["rebuild"]["maximum_source_age_at_submit_ms"])
        for c in CONTEXTS
    )
    if total_drop_cached < total_drop_rebuild and submit_better_both:
        decision = "CACHE_UPDATE_COST_WIN_WITH_OBSERVED_LATEST_DUE_FRESHNESS_GAIN"
    elif total_drop_cached == total_drop_rebuild and submit_better_both:
        decision = "CACHE_UPDATE_COST_WIN_WITH_SUBMIT_AGE_GAIN_BUT_NO_DROP_COUNT_GAIN"
    elif total_drop_cached <= total_drop_rebuild:
        decision = "CACHE_UPDATE_COST_WIN_WITH_NO_ROBUST_FRESHNESS_GAIN"
    else:
        decision = "CACHE_UPDATE_COST_WIN_BUT_LATEST_DUE_DROP_COUNT_REGRESSED_IN_THIS_RUN"

    return {
        "schema": SCHEMA,
        "state": STATUS if all(checks.values()) else "FAIL",
        "decision": decision,
        "receiving_head": payload.get("receiving_head"),
        "exact_vfx_latest_due_head": EXACT_VFX_LATEST_DUE_HEAD,
        "presentation_policy": coalesced.PRESENTATION_POLICY,
        "checks": checks,
        "contexts": report_contexts,
        "vfx_retained_baseline_metrics": vfx_baseline.get("context_metrics", {}),
        "total_dropped_states_rebuild": total_drop_rebuild,
        "total_dropped_states_cached_swap": total_drop_cached,
        "truth_boundary": (
            "PASS means only that, on this exact Godot 4.7.2 proof-host A/B and the exact VFX latest-due policy, prebuilding the finite 17 Weather + 17 sapling native mesh resources before timing materially reduces selection-to-submit mesh update work while six fixed-state review pairs remain byte-identical. Drop counts/source-age changes are reported as observations and do not generalize to target devices or guarantee authored 32 Hz delivery. The cache costs memory and intentionally changes mesh-resource identity; VFX adoption remains held."
        ),
    }


def negative_control(payload: dict[str, Any], receipt: dict[str, Any], vfx_baseline: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(receipt)
    block = mutated.get("contexts", {}).get("path_eye", {}).get("cached_swap", {})
    samples = block.get("samples", [])
    if samples:
        samples[0]["weather_field_digest"] = "intentional-runtime-source-drift"
    return verify(payload, mutated, vfx_baseline)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--vfx-baseline", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    payload = _load(args.payload)
    receipt = _load(args.receipt)
    baseline = _load(args.vfx_baseline)
    report = negative_control(payload, receipt, baseline) if args.negative_control else verify(payload, receipt, baseline)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.negative_control:
        return 0 if report["state"] == "FAIL" else 1
    return 0 if report["state"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
