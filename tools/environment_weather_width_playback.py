from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from . import environment_weather_width_current_world as width
except ImportError:
    import environment_weather_width_current_world as width

SCHEMA = "axm.environment-current-world-weather-width-wall-clock-target-host/v0.1"
STATUS = "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_BOUNDED_WALL_CLOCK_PRESENTATION"
OBSERVATION_SCHEMA = "axm.environment-current-world-weather-width-wall-clock-observation/v0.1"
OBSERVATION_STATE = "OBSERVED_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_WALL_CLOCK_SEQUENCE"
CONTEXTS = ("path_eye", "elevated_oblique")
SOURCE_INTERVAL_S = 0.03125
SOURCE_INTERVAL_MS = 31.25
DEADLINE_EPSILON_MS = 0.5
TARGET_REAR_ASSET_ID = "source:nature:east-rear-tree-neutral-001"
VIEWPORT_UPDATE_POLICY = "UPDATE_ALWAYS_PIPELINED"
SUBMIT_SEMANTICS = "AFTER_STATE_GEOMETRY_UPDATE_BEFORE_POST_DRAW_OBSERVATION"


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _strictly_non_decreasing(values: list[float]) -> bool:
    return all(b >= a for a, b in zip(values, values[1:]))


def verify_playback(payload: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    states = payload.get("states", [])
    expected_indices = list(range(17))
    expected_times = [index * SOURCE_INTERVAL_S for index in expected_indices]
    expected_weather = [str(row.get("weather_field_digest", "")) for row in states]
    expected_width = [str(row.get("weather_width_profile_digest", "")) for row in states]
    expected_sapling = [str(row.get("sapling_mesh_digest", "")) for row in states]

    context_metrics: dict[str, Any] = {}
    all_exact_samples = True
    all_schedule_exact = True
    all_monotonic = True
    all_submit_before_draw = True
    all_submit_deadlines = True
    all_draw_deadlines = True
    all_widths = True
    all_context_policies = True
    weather_ids: set[tuple[int, int, int]] = set()
    sapling_ids: set[tuple[int, int, int]] = set()
    measured_width_count = 0
    maximum_width_residual_px = 0.0
    near_clip_totals: dict[str, int] = {}

    receipt_contexts = receipt.get("contexts", {})
    for context in CONTEXTS:
        block = receipt_contexts.get(context, {})
        samples = block.get("samples", [])
        indices = [int(row.get("index", -1)) for row in samples]
        scheduled_times = [float(row.get("scheduled_time_s", -1.0)) for row in samples]
        submit_times = [float(row.get("submit_time_s", -1.0)) for row in samples]
        draw_times = [float(row.get("draw_time_s", -1.0)) for row in samples]
        submit_lateness = [float(row.get("submit_lateness_ms", 999999.0)) for row in samples]
        draw_lateness = [float(row.get("draw_lateness_ms", 999999.0)) for row in samples]
        submit_misses = [
            int(row.get("index", -1))
            for row in samples
            if float(row.get("submit_lateness_ms", 999999.0)) > SOURCE_INTERVAL_MS + DEADLINE_EPSILON_MS
        ]
        draw_misses = [
            int(row.get("index", -1))
            for row in samples
            if float(row.get("draw_lateness_ms", 999999.0)) > SOURCE_INTERVAL_MS + DEADLINE_EPSILON_MS
        ]

        exact_samples = (
            len(samples) == 17
            and indices == expected_indices
            and [str(row.get("weather_field_digest", "")) for row in samples] == expected_weather
            and [str(row.get("weather_width_profile_digest", "")) for row in samples] == expected_width
            and [str(row.get("sapling_mesh_digest", "")) for row in samples] == expected_sapling
        )
        schedule_exact = (
            len(scheduled_times) == 17
            and all(abs(a - b) <= 1e-9 for a, b in zip(scheduled_times, expected_times))
            and abs(float(block.get("interval_s", -1.0)) - SOURCE_INTERVAL_S) <= 1e-9
            and int(block.get("interval_us", -1)) == 31250
        )
        context_policy_exact = (
            block.get("viewport_update_policy") == VIEWPORT_UPDATE_POLICY
            and block.get("submit_semantics") == SUBMIT_SEMANTICS
        )
        monotonic = _strictly_non_decreasing(submit_times) and _strictly_non_decreasing(draw_times)
        submit_before_draw = len(samples) == 17 and all(submit <= draw for submit, draw in zip(submit_times, draw_times))
        submit_deadline = len(samples) == 17 and not submit_misses
        draw_deadline = len(samples) == 17 and not draw_misses

        near_clips = 0
        for row in samples:
            weather_update = row.get("weather_update", {})
            sapling_update = row.get("sapling_update", {})
            if weather_update.get("state") != "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
                all_widths = False
            residual = float(weather_update.get("maximum_projected_width_residual_px", 999.0))
            maximum_width_residual_px = max(maximum_width_residual_px, residual)
            measured_width_count += int(weather_update.get("measured_width_count", 0))
            all_widths = all_widths and residual <= width.WIDTH_RESIDUAL_TOL_PX
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
            near_clips += int(weather_update.get("near_clipped_endpoint_count", 0))
        near_clip_totals[context] = near_clips

        all_exact_samples = all_exact_samples and exact_samples
        all_schedule_exact = all_schedule_exact and schedule_exact
        all_context_policies = all_context_policies and context_policy_exact
        all_monotonic = all_monotonic and monotonic
        all_submit_before_draw = all_submit_before_draw and submit_before_draw
        all_submit_deadlines = all_submit_deadlines and submit_deadline
        all_draw_deadlines = all_draw_deadlines and draw_deadline

        context_metrics[context] = {
            "sample_count": len(samples),
            "maximum_submit_lateness_ms": max(submit_lateness, default=None),
            "maximum_draw_lateness_ms": max(draw_lateness, default=None),
            "submission_deadline_miss_count": len(submit_misses),
            "submission_deadline_miss_indices": submit_misses,
            "post_draw_deadline_miss_count": len(draw_misses),
            "post_draw_deadline_miss_indices": draw_misses,
            "final_draw_time_s": draw_times[-1] if draw_times else None,
            "near_clipped_endpoint_count": near_clips,
            "viewport_update_policy": block.get("viewport_update_policy"),
            "submit_semantics": block.get("submit_semantics"),
        }

    rear_modes = {
        str(row.get("proof_culling", ""))
        for row in receipt.get("static_source_meshes", [])
        if row.get("asset_id") == TARGET_REAR_ASSET_ID
    }

    checks = {
        "structure_passed_before_playback": payload.get("status") == width.STATUS and all(payload.get("checks", {}).values()),
        "observation_schema_exact": receipt.get("schema") == OBSERVATION_SCHEMA and receipt.get("state") == OBSERVATION_STATE,
        "exact_receiving_head_matches": receipt.get("receiving_head") == payload.get("receiving_head"),
        "exact_parent_variant_head_matches": receipt.get("parent_variant_head") == width.EXPECTED_PARENT_VARIANT_HEAD,
        "both_fixed_contexts_observed": set(receipt_contexts) == set(CONTEXTS),
        "all_17_exact_source_states_presented_per_context": all_exact_samples,
        "exact_0p03125_source_schedule_preserved": all_schedule_exact,
        "pipelined_viewport_policy_and_post_geometry_submit_semantics_exact": (
            receipt.get("viewport_update_policy") == VIEWPORT_UPDATE_POLICY
            and receipt.get("submit_semantics") == SUBMIT_SEMANTICS
            and all_context_policies
        ),
        "submit_and_post_draw_times_monotonic": all_monotonic and all_submit_before_draw,
        "all_state_submissions_within_one_source_interval": all_submit_deadlines,
        "all_post_draw_observations_within_one_source_interval": all_draw_deadlines,
        "all_source_widths_remain_within_projection_tolerance": all_widths and maximum_width_residual_px <= width.WIDTH_RESIDUAL_TOL_PX and measured_width_count == 17 * 2 * 36,
        "one_weather_resource_identity_stable": len(weather_ids) == 1 and next(iter(weather_ids), (-1, -1, -1))[0] > 0,
        "one_sapling_resource_identity_stable": len(sapling_ids) == 1 and next(iter(sapling_ids), (-1, -1, -1))[0] > 0,
        "near_plane_boundary_reproduced_exactly": near_clip_totals == {"path_eye": 5, "elevated_oblique": 0},
        "rear_tree_culling_state_preserved": rear_modes == {"CULL_BACK"},
    }

    return {
        "schema": SCHEMA,
        "state": STATUS if all(checks.values()) else "FAIL",
        "receiving_head": payload.get("receiving_head"),
        "parent_variant_head": width.EXPECTED_PARENT_VARIANT_HEAD,
        "source_interval_s": SOURCE_INTERVAL_S,
        "viewport_update_policy": VIEWPORT_UPDATE_POLICY,
        "submit_semantics": SUBMIT_SEMANTICS,
        "submission_cadence_state": "PASS" if all_submit_deadlines else "FAIL",
        "post_draw_cadence_state": "PASS" if all_draw_deadlines else "FAIL",
        "deadline_policy": "EACH_POST_GEOMETRY_SOURCE_STATE_SUBMISSION_AND_ITS_NEXT_PIPELINED_POST_DRAW_OBSERVATION_MUST_COMPLETE_WITHIN_ONE_0P03125_SECOND_SOURCE_INTERVAL_OF_ITS_EXACT_SOURCE_TIME",
        "deadline_epsilon_ms": DEADLINE_EPSILON_MS,
        "checks": checks,
        "context_metrics": context_metrics,
        "maximum_projected_width_residual_px": maximum_width_residual_px,
        "measured_width_count": measured_width_count,
        "near_clip_totals": near_clip_totals,
        "truth_boundary": (
            "PASS proves only that the exact 17 already-authored Weather-width + sapling states were materialized and submitted in order at their exact 0.03125 s source-evaluation schedule while the proof SubViewport rendered continuously, and each exact post-geometry submission was followed by a Godot post-draw observation within one source interval in both fixed 1100x720 cameras. "
            "The submit timestamp is taken after source-state geometry update, not at scheduler wake. No interpolated states are invented. This is not a frame-time benchmark, target-device performance certification, physical-weather simulation, gameplay/controller authority, arbitrary-camera guarantee, final Art Direction acceptance, CANON, production readiness, or VFX mastery."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = verify_playback(_load(args.payload), _load(args.receipt))
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
