from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "axm.environment-weather-dynamic-runtime-comparison/v0.1"
EXPECTED_OBSERVATION_SCHEMA = "axm.environment-weather-dynamic-runtime-observation/v0.1"
EXPECTED_WEATHER_HEAD = "ca2eaba519e8449835b0ea6ef944b7080c3caa6a"
EXPECTED_SAMPLE_COUNT = 9
EXPECTED_STREAKS = 36
CONTEXTS = ("path_eye", "elevated_oblique")


def _load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _memory_summary(receipt: dict) -> dict:
    rows = receipt["stress"]["cycle_memory"]
    buffer_values = [int(row["buffer_mem_bytes"]) for row in rows]
    texture_values = [int(row["texture_mem_bytes"]) for row in rows]
    return {
        "samples": len(rows),
        "buffer_min_bytes": min(buffer_values),
        "buffer_max_bytes": max(buffer_values),
        "buffer_last_minus_first_bytes": buffer_values[-1] - buffer_values[0],
        "texture_min_bytes": min(texture_values),
        "texture_max_bytes": max(texture_values),
        "texture_last_minus_first_bytes": texture_values[-1] - texture_values[0],
    }


def _ratio_delta(before: int | float, after: int | float) -> float | None:
    before = float(before)
    if before == 0.0:
        return None
    return (float(after) - before) / before


def compare(control: dict, candidate: dict, image_root: str | Path) -> dict:
    image_root = Path(image_root)
    checks: dict[str, bool] = {}

    checks["observation_schemas_match"] = (
        control.get("schema") == EXPECTED_OBSERVATION_SCHEMA
        and candidate.get("schema") == EXPECTED_OBSERVATION_SCHEMA
    )
    checks["observation_states_pass"] = (
        control.get("state") == "PASS_SCOPED_SAME_PROCESS_WEATHER_UPDATE_OBSERVATION"
        and candidate.get("state") == "PASS_SCOPED_SAME_PROCESS_WEATHER_UPDATE_OBSERVATION"
    )
    checks["mode_identity"] = control.get("mode") == "rebuild_control" and candidate.get("mode") == "reuse_single_mesh"

    identity_fields = (
        "receiving_head",
        "environment_base_head",
        "sequence_digest",
        "sampling_schedule_s",
        "static_receiving_state_digest",
    )
    checks["exact_input_identity_preserved"] = all(control.get(key) == candidate.get(key) for key in identity_fields)
    checks["weather_source_identity_preserved"] = (
        control.get("weather_source") == candidate.get("weather_source")
        and candidate.get("weather_source", {}).get("head") == EXPECTED_WEATHER_HEAD
    )

    control_samples = control.get("evidence_samples", [])
    candidate_samples = candidate.get("evidence_samples", [])
    checks["exact_nine_samples"] = len(control_samples) == EXPECTED_SAMPLE_COUNT and len(candidate_samples) == EXPECTED_SAMPLE_COUNT
    checks["sample_field_identity_preserved"] = [row.get("field_digest") for row in control_samples] == [
        row.get("field_digest") for row in candidate_samples
    ]

    candidate_nodes = {row.get("update", {}).get("node_instance_id") for row in candidate_samples}
    candidate_meshes = {row.get("update", {}).get("mesh_instance_id") for row in candidate_samples}
    candidate_materials = {row.get("update", {}).get("material_instance_id") for row in candidate_samples}
    checks["candidate_one_node_identity_across_samples"] = len(candidate_nodes) == 1 and None not in candidate_nodes
    checks["candidate_one_mesh_identity_across_samples"] = len(candidate_meshes) == 1 and None not in candidate_meshes
    checks["candidate_one_material_identity_across_samples"] = len(candidate_materials) == 1 and None not in candidate_materials
    checks["candidate_one_surface_36_streaks"] = all(
        row.get("update", {}).get("surface_count") == 1
        and row.get("update", {}).get("streak_count") == EXPECTED_STREAKS
        for row in candidate_samples
    )
    checks["control_one_surface_36_streaks"] = all(
        row.get("update", {}).get("surface_count") == 1
        and row.get("update", {}).get("streak_count") == EXPECTED_STREAKS
        for row in control_samples
    )

    candidate_creations = candidate.get("resource_creations", {})
    control_creations = control.get("resource_creations", {})
    checks["candidate_single_resource_creation"] = all(
        int(candidate_creations.get(key, -1)) == 1
        for key in ("weather_nodes", "weather_meshes", "weather_materials")
    )
    expected_control_updates = EXPECTED_SAMPLE_COUNT + int(control.get("stress", {}).get("updates", -1))
    checks["control_rebuilds_resources_each_update"] = all(
        int(control_creations.get(key, -1)) == expected_control_updates
        for key in ("weather_nodes", "weather_meshes", "weather_materials")
    )

    counter_mismatches = []
    image_mismatches = []
    image_hashes: dict[str, dict[str, list[str]]] = {
        "control": {context: [] for context in CONTEXTS},
        "candidate": {context: [] for context in CONTEXTS},
    }
    for control_row, candidate_row in zip(control_samples, candidate_samples):
        index = int(control_row["index"])
        if index != int(candidate_row["index"]):
            counter_mismatches.append({"index": index, "reason": "sample index mismatch"})
            continue
        for context in CONTEXTS:
            before_runtime = control_row["contexts"][context]["runtime"]
            after_runtime = candidate_row["contexts"][context]["runtime"]
            for metric in (
                "objects_in_frame",
                "primitives_in_frame",
                "draw_calls_in_frame",
                "texture_mem_bytes",
                "buffer_mem_bytes",
            ):
                if before_runtime.get(metric) != after_runtime.get(metric):
                    counter_mismatches.append(
                        {
                            "index": index,
                            "context": context,
                            "metric": metric,
                            "control": before_runtime.get(metric),
                            "candidate": after_runtime.get(metric),
                        }
                    )
            before_path = image_root / f"weather-dynamic-rebuild_control-{context}-{index:02d}.png"
            after_path = image_root / f"weather-dynamic-reuse_single_mesh-{context}-{index:02d}.png"
            if not before_path.is_file() or not after_path.is_file():
                image_mismatches.append({"index": index, "context": context, "reason": "missing image"})
                continue
            before_hash = _sha256(before_path)
            after_hash = _sha256(after_path)
            image_hashes["control"][context].append(before_hash)
            image_hashes["candidate"][context].append(after_hash)
            if before_hash != after_hash:
                image_mismatches.append(
                    {"index": index, "context": context, "control_sha256": before_hash, "candidate_sha256": after_hash}
                )

    checks["runtime_counters_identical_per_sample"] = not counter_mismatches
    checks["render_bytes_identical_per_sample"] = not image_mismatches
    checks["candidate_all_nine_frames_materially_distinct"] = all(
        len(set(image_hashes["candidate"][context])) == EXPECTED_SAMPLE_COUNT for context in CONTEXTS
    )

    control_submission = control["stress"]["submission"]
    candidate_submission = candidate["stress"]["submission"]
    control_memory = _memory_summary(control)
    candidate_memory = _memory_summary(candidate)

    resource_delta = {}
    for key in ("weather_nodes", "weather_meshes", "weather_materials"):
        before = int(control_creations[key])
        after = int(candidate_creations[key])
        resource_delta[key] = {
            "control_created": before,
            "candidate_created": after,
            "reduction": before - after,
            "reduction_fraction": (before - after) / before if before else None,
        }

    observations = {
        "resource_creation_delta": resource_delta,
        "cpu_side_submission": {
            "control": control_submission,
            "candidate": candidate_submission,
            "median_delta_fraction": _ratio_delta(control_submission["median_usec"], candidate_submission["median_usec"]),
            "p95_delta_fraction": _ratio_delta(control_submission["p95_usec"], candidate_submission["p95_usec"]),
            "truth_boundary": "CPU-side GDScript submission timings on one GitHub Actions proof host are observational only. They are not GPU frame time, target-device latency, or a production performance budget.",
        },
        "stress_memory": {
            "control": control_memory,
            "candidate": candidate_memory,
            "truth_boundary": "RenderingServer memory counters are proof-host observations after bounded update cycles. They are not complete process/GPU residency accounting and no universal leak threshold is inferred from this one run.",
        },
        "counter_mismatches": counter_mismatches,
        "image_mismatches": image_mismatches,
        "image_hashes": image_hashes,
    }

    result = {
        "schema": SCHEMA,
        "state": "PASS_REUSE_SINGLE_MESH_RESOURCE_CHURN_CONTRACT" if all(checks.values()) else "HOLD_DYNAMIC_RUNTIME_COMPARISON",
        "checks": checks,
        "control": {
            "mode": control["mode"],
            "semantics": control["update_semantics"],
            "resource_creations": control_creations,
        },
        "candidate": {
            "mode": candidate["mode"],
            "semantics": candidate["update_semantics"],
            "resource_creations": candidate_creations,
        },
        "exact_identity": {key: candidate.get(key) for key in identity_fields},
        "weather_source": candidate.get("weather_source"),
        "observations": observations,
        "visual_tradeoff": (
            "NONE_OBSERVED_IN_EXACT_RETAINED_PROOF_FRAMES" if checks["render_bytes_identical_per_sample"] else "REVIEW_REQUIRED_RENDER_OUTPUT_DIFFERS"
        ),
        "truth_boundary": (
            "PASS proves only that, for this exact nine-state visual-only Weather sequence in pinned Godot 4.7.2 GL Compatibility, one persistent MeshInstance3D + ImmediateMesh + material can replace a synthetic free/recreate-per-state control while preserving exact sample identity, one-surface/36-streak structure, matched proof-host counters, and byte-identical retained frames. It directly reduces proof-host node/mesh/material creation churn by construction. CPU submission and memory counters are observations, not target FPS/GPU timing or a production budget. No physical weather, final art direction, gameplay, generic engine policy, CANON, or Runtime mastery is claimed."
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = compare(_load(args.control), _load(args.candidate), args.image_root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["state"].startswith("PASS_") else 1)


if __name__ == "__main__":
    main()
