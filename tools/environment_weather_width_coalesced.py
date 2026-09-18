from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

try:
    from . import environment_weather_width_current_world as width
except ImportError:
    import environment_weather_width_current_world as width

SCHEMA = "axm.environment-current-world-weather-width-latest-due-target-host/v0.1"
STATUS = "PASS_LATEST_DUE_EXACT_SOURCE_STATE_PRESENTATION_FALLBACK"
OBSERVATION_SCHEMA = "axm.environment-current-world-weather-width-latest-due-observation/v0.1"
OBSERVATION_STATE = "OBSERVED_LATEST_DUE_SOURCE_STATE_PRESENTATION"
CONTEXT_STATE = "OBSERVED_LATEST_DUE_SOURCE_STATE_SEQUENCE"
CONTEXTS = ("path_eye", "elevated_oblique")
SOURCE_INTERVAL_S = 0.03125
SOURCE_INTERVAL_US = 31250
PRESENTATION_POLICY = "LATEST_DUE_EXACT_SOURCE_STATE_NO_INTERPOLATION"
SELECTION_SEMANTICS = "SELECT_FRESHEST_DUE_SOURCE_STATE_WHEN_RENDERER_RETURNS_CONTROL"
TARGET_REAR_ASSET_ID = "source:nature:east-rear-tree-neutral-001"


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _strictly_increasing(values: list[int]) -> bool:
    return all(b > a for a, b in zip(values, values[1:]))


def verify_coalesced(payload: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    states = payload.get("states", [])
    expected_by_index = {int(row.get("index", -1)): row for row in states}
    context_metrics: dict[str, Any] = {}
    all_contexts_valid = True
    all_exact_source_rows = True
    all_freshest_due = True
    all_monotonic = True
    all_frame_evidence = True
    all_widths = True
    all_resources_stable = True
    measured_width_count = 0
    maximum_width_residual_px = 0.0

    receipt_contexts = receipt.get("contexts", {})
    for context in CONTEXTS:
        block = receipt_contexts.get(context, {})
        samples = block.get("samples", [])
        indices = [int(row.get("index", -1)) for row in samples]
        dropped = [int(value) for value in block.get("dropped_indices", [])]
        complement = [index for index in range(17) if index not in indices]

        context_valid = (
            block.get("state") == CONTEXT_STATE
            and block.get("presentation_policy") == PRESENTATION_POLICY
            and block.get("selection_semantics") == SELECTION_SEMANTICS
            and abs(float(block.get("source_interval_s", -1.0)) - SOURCE_INTERVAL_S) <= 1e-9
            and int(block.get("source_interval_us", -1)) == SOURCE_INTERVAL_US
            and 2 <= len(samples) <= 17
            and indices[0] == 0
            and indices[-1] == 16
            and _strictly_increasing(indices)
            and dropped == complement
        )
        all_contexts_valid = all_contexts_valid and context_valid

        weather_ids: set[tuple[int, int, int]] = set()
        sapling_ids: set[tuple[int, int, int]] = set()
        frame_hashes: list[str] = []
        previous_index = -1
        max_selection_age = 0.0
        max_submit_age = 0.0
        max_draw_age = 0.0

        for row in samples:
            index = int(row.get("index", -1))
            source = expected_by_index.get(index, {})
            exact_source = (
                bool(source)
                and abs(float(row.get("scheduled_time_s", -1.0)) - float(source.get("time_s", -2.0))) <= 1e-9
                and str(row.get("weather_field_digest", "")) == str(source.get("weather_field_digest", ""))
                and str(row.get("weather_width_profile_digest", "")) == str(source.get("weather_width_profile_digest", ""))
                and str(row.get("sapling_mesh_digest", "")) == str(source.get("sapling_mesh_digest", ""))
            )
            all_exact_source_rows = all_exact_source_rows and exact_source

            freshest_due = int(row.get("latest_due_index_at_selection", -1)) == index
            all_freshest_due = all_freshest_due and freshest_due

            selection_time = float(row.get("selection_time_s", -1.0))
            submit_time = float(row.get("submit_time_s", -1.0))
            draw_time = float(row.get("draw_time_s", -1.0))
            ordered = selection_time <= submit_time <= draw_time
            all_monotonic = all_monotonic and ordered
            max_selection_age = max(max_selection_age, float(row.get("source_age_at_selection_ms", -1.0)))
            max_submit_age = max(max_submit_age, float(row.get("source_age_at_submit_ms", -1.0)))
            max_draw_age = max(max_draw_age, float(row.get("source_age_at_draw_ms", -1.0)))

            expected_skipped = list(range(previous_index + 1, index))
            all_contexts_valid = all_contexts_valid and [int(v) for v in row.get("skipped_before", [])] == expected_skipped
            previous_index = index

            weather_update = row.get("weather_update", {})
            sapling_update = row.get("sapling_update", {})
            residual = float(weather_update.get("maximum_projected_width_residual_px", 999.0))
            maximum_width_residual_px = max(maximum_width_residual_px, residual)
            measured_width_count += int(weather_update.get("measured_width_count", 0))
            all_widths = all_widths and (
                weather_update.get("state") == "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS"
                and residual <= width.WIDTH_RESIDUAL_TOL_PX
                and int(weather_update.get("measured_width_count", 0)) == 36
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

            frame = row.get("frame", {})
            frame_hash = str(frame.get("sha256", ""))
            frame_ok = (
                frame.get("state") == "PASS_CAPTURED_FRAME"
                and int(frame.get("width", 0)) == 1100
                and int(frame.get("height", 0)) == 720
                and bool(frame_hash)
                and str(frame.get("path", "")).endswith(f"state-{index:02d}.png")
            )
            all_frame_evidence = all_frame_evidence and frame_ok
            frame_hashes.append(frame_hash)

        resources_stable = (
            len(weather_ids) == 1
            and len(sapling_ids) == 1
            and next(iter(weather_ids), (-1, -1, -1))[0] > 0
            and next(iter(sapling_ids), (-1, -1, -1))[0] > 0
        )
        all_resources_stable = all_resources_stable and resources_stable
        frames_distinct = len(frame_hashes) == len(set(frame_hashes))
        all_frame_evidence = all_frame_evidence and frames_distinct

        context_metrics[context] = {
            "presented_state_count": len(samples),
            "presented_indices": indices,
            "dropped_state_count": len(dropped),
            "dropped_indices": dropped,
            "maximum_source_age_at_selection_ms": max_selection_age,
            "maximum_source_age_at_submit_ms": max_submit_age,
            "maximum_source_age_at_draw_ms": max_draw_age,
            "final_draw_time_s": float(samples[-1].get("draw_time_s", -1.0)) if samples else None,
            "retained_frame_count": len(frame_hashes),
            "retained_frame_hashes_unique": frames_distinct,
        }

    rear_modes = {
        str(row.get("proof_culling", ""))
        for row in receipt.get("static_source_meshes", [])
        if row.get("asset_id") == TARGET_REAR_ASSET_ID
    }

    checks = {
        "structure_passed_before_presentation": payload.get("status") == width.STATUS and all(payload.get("checks", {}).values()),
        "observation_schema_and_state_exact": receipt.get("schema") == OBSERVATION_SCHEMA and receipt.get("state") == OBSERVATION_STATE,
        "exact_receiving_head_matches": receipt.get("receiving_head") == payload.get("receiving_head"),
        "exact_parent_variant_head_matches": receipt.get("parent_variant_head") == width.EXPECTED_PARENT_VARIANT_HEAD,
        "both_fixed_contexts_observed": set(receipt_contexts) == set(CONTEXTS),
        "latest_due_policy_exact": receipt.get("presentation_policy") == PRESENTATION_POLICY and receipt.get("selection_semantics") == SELECTION_SEMANTICS,
        "each_context_starts_at_0_finishes_at_16_and_skips_only_stale_intermediates": all_contexts_valid,
        "every_presented_row_is_exact_source_owned_state": all_exact_source_rows,
        "every_selection_was_freshest_state_due_at_selection_time": all_freshest_due,
        "selection_submit_draw_order_preserved": all_monotonic,
        "presented_source_widths_remain_within_projection_tolerance": all_widths and maximum_width_residual_px <= width.WIDTH_RESIDUAL_TOL_PX,
        "stable_weather_and_sapling_resource_identity": all_resources_stable,
        "direct_retained_1100x720_frame_evidence_present_and_distinct": all_frame_evidence,
        "rear_tree_culling_state_preserved": rear_modes == {"CULL_BACK"},
    }

    return {
        "schema": SCHEMA,
        "state": STATUS if all(checks.values()) else "FAIL",
        "receiving_head": payload.get("receiving_head"),
        "parent_variant_head": width.EXPECTED_PARENT_VARIANT_HEAD,
        "source_interval_s": SOURCE_INTERVAL_S,
        "presentation_policy": PRESENTATION_POLICY,
        "selection_semantics": SELECTION_SEMANTICS,
        "checks": checks,
        "context_metrics": context_metrics,
        "measured_width_count": measured_width_count,
        "maximum_projected_width_residual_px": maximum_width_residual_px,
        "truth_boundary": (
            "PASS proves an optional latest-due VFX presentation fallback for this exact proof host: whenever the renderer returns control, the receiver selects the freshest already-due exact authored Weather + sapling source state, may skip stale intermediate visual states, never invents interpolation, preserves exact source digests and projected width tolerance, and retains the actually presented 1100x720 frames. It deliberately does not prove or claim authored 32 Hz presentation, zero frame drops, target-device performance, physical weather, gameplay/physics authority, arbitrary cameras, final Art Direction, CANON, production readiness, or mastery."
        ),
    }


def exercise_stale_selection_negative_control(payload: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(receipt)
    for context in CONTEXTS:
        samples = mutated.get("contexts", {}).get(context, {}).get("samples", [])
        if len(samples) >= 2:
            samples[1]["latest_due_index_at_selection"] = int(samples[1].get("index", 0)) + 1
            break
    return verify_coalesced(payload, mutated)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = _load(args.payload)
    receipt = _load(args.receipt)
    report = verify_coalesced(payload, receipt)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
