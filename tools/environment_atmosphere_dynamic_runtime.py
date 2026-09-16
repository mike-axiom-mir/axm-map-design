#!/usr/bin/env python3
"""Compare exact proof-host resource lifecycle evidence for synchronized Weather + moving Nature sapling.

The bounded variable is sapling resource lifecycle. Weather is required to use the same stable
resource-reuse path in both modes. The comparator deliberately treats hosted CPU timings and
memory counters as observations, not target-device acceptance criteria.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-atmosphere-dynamic-runtime-evidence/v0.1"
CONTROL_MODE = "rebuild_sapling_control"
CANDIDATE_MODE = "reuse_sapling_mesh"
VFX_HEAD = "d476cf7c11de74c53397cb21e6f40f90a51c0356"
CONTEXTS = ("path_eye", "elevated_oblique")
EXPECTED_SAMPLES = 9
EXPECTED_STRESS_CYCLES = 48
EXPECTED_STRESS_UPDATES = EXPECTED_SAMPLES * EXPECTED_STRESS_CYCLES
EXPECTED_TOTAL_UPDATES = EXPECTED_SAMPLES + EXPECTED_STRESS_UPDATES
EXPECTED_VERTICES = 390
EXPECTED_TRIANGLES = 570
EXPECTED_STREAKS = 36


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _runtime_tuple(sample: dict[str, Any], context: str) -> tuple[int, int, int]:
    runtime = sample["contexts"][context]["runtime"]
    return (
        int(runtime["draw_calls_in_frame"]),
        int(runtime["objects_in_frame"]),
        int(runtime["primitives_in_frame"]),
    )


def _memory_summary(receipt: dict[str, Any]) -> dict[str, int]:
    rows = receipt["stress"]["cycle_memory"]
    if not rows:
        return {"first_buffer_bytes": 0, "last_buffer_bytes": 0, "buffer_drift_bytes": 0,
                "first_texture_bytes": 0, "last_texture_bytes": 0, "texture_drift_bytes": 0}
    first, last = rows[0], rows[-1]
    return {
        "first_buffer_bytes": int(first["buffer_mem_bytes"]),
        "last_buffer_bytes": int(last["buffer_mem_bytes"]),
        "buffer_drift_bytes": int(last["buffer_mem_bytes"]) - int(first["buffer_mem_bytes"]),
        "first_texture_bytes": int(first["texture_mem_bytes"]),
        "last_texture_bytes": int(last["texture_mem_bytes"]),
        "texture_drift_bytes": int(last["texture_mem_bytes"]) - int(first["texture_mem_bytes"]),
    }


def evaluate(control: dict[str, Any], candidate: dict[str, Any], image_root: Path, runtime_head: str) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    checks["control_observation_pass"] = control.get("state") == "PASS_SCOPED_SAME_PROCESS_SYNCHRONIZED_ATMOSPHERE_OBSERVATION"
    checks["candidate_observation_pass"] = candidate.get("state") == "PASS_SCOPED_SAME_PROCESS_SYNCHRONIZED_ATMOSPHERE_OBSERVATION"
    checks["expected_modes"] = control.get("mode") == CONTROL_MODE and candidate.get("mode") == CANDIDATE_MODE
    checks["exact_vfx_prerequisite_head"] = control.get("vfx_receiving_head") == VFX_HEAD and candidate.get("vfx_receiving_head") == VFX_HEAD
    checks["same_vfx_sequence"] = bool(control.get("sequence_digest")) and control.get("sequence_digest") == candidate.get("sequence_digest")
    checks["same_source_identity"] = control.get("nature_response") == candidate.get("nature_response") and control.get("weather_source") == candidate.get("weather_source")
    checks["same_sampling_schedule"] = control.get("sampling_schedule_s") == candidate.get("sampling_schedule_s") and len(control.get("sampling_schedule_s", [])) == EXPECTED_SAMPLES
    checks["same_visual_only_relationship"] = control.get("shared_relationship") == candidate.get("shared_relationship") == "SHARED_EVIDENCE_CLOCK_AND_EXACT_VISUAL_DIRECTION_NOT_PHYSICAL_COUPLING"

    control_samples = control.get("evidence_samples", [])
    candidate_samples = candidate.get("evidence_samples", [])
    checks["nine_evidence_samples"] = len(control_samples) == len(candidate_samples) == EXPECTED_SAMPLES
    checks["sample_identity_preserved"] = len(control_samples) == len(candidate_samples) and all(
        (a.get("index"), a.get("time_s"), a.get("weather_field_digest"), a.get("sapling_mesh_digest"))
        == (b.get("index"), b.get("time_s"), b.get("weather_field_digest"), b.get("sapling_mesh_digest"))
        for a, b in zip(control_samples, candidate_samples)
    )

    all_updates = [s.get("sapling_update", {}) for s in control_samples + candidate_samples]
    checks["sapling_topology_and_surface_preserved"] = bool(all_updates) and all(
        int(u.get("source_vertex_count", -1)) == EXPECTED_VERTICES
        and int(u.get("source_triangle_count", -1)) == EXPECTED_TRIANGLES
        and int(u.get("surface_count", -1)) == 1
        for u in all_updates
    )
    all_weather = [s.get("weather_update", {}) for s in control_samples + candidate_samples]
    checks["weather_surface_preserved"] = bool(all_weather) and all(
        int(u.get("streak_count", -1)) == EXPECTED_STREAKS and int(u.get("surface_count", -1)) == 1
        for u in all_weather
    )

    candidate_updates = [s["sapling_update"] for s in candidate_samples]
    checks["candidate_sapling_identity_stable"] = bool(candidate_updates) and all(
        len({int(u[key]) for u in candidate_updates}) == 1
        for key in ("node_instance_id", "mesh_instance_id", "material_instance_id")
    )
    control_updates = [s["sapling_update"] for s in control_samples]
    checks["control_sapling_identity_rebuilt"] = bool(control_updates) and all(
        len({int(u[key]) for u in control_updates}) == EXPECTED_SAMPLES
        for key in ("node_instance_id", "mesh_instance_id", "material_instance_id")
    )
    for label, samples in (("control", control_samples), ("candidate", candidate_samples)):
        weather_updates = [s["weather_update"] for s in samples]
        checks[f"{label}_weather_identity_stable"] = bool(weather_updates) and all(
            len({int(u[key]) for u in weather_updates}) == 1
            for key in ("node_instance_id", "mesh_instance_id", "material_instance_id")
        )

    control_creations = control.get("resource_creations", {})
    candidate_creations = candidate.get("resource_creations", {})
    checks["weather_construction_equal_and_single"] = all(
        int(control_creations.get(key, -1)) == int(candidate_creations.get(key, -1)) == 1
        for key in ("weather_nodes", "weather_meshes", "weather_materials")
    )
    checks["control_rebuild_count_exact"] = all(
        int(control_creations.get(key, -1)) == EXPECTED_TOTAL_UPDATES
        for key in ("sapling_nodes", "sapling_meshes", "sapling_materials")
    )
    checks["candidate_single_sapling_resource_set"] = all(
        int(candidate_creations.get(key, -1)) == 1
        for key in ("sapling_nodes", "sapling_meshes", "sapling_materials")
    )
    checks["stress_shape_exact"] = (
        int(control.get("stress", {}).get("cycles", -1)) == EXPECTED_STRESS_CYCLES
        and int(candidate.get("stress", {}).get("cycles", -1)) == EXPECTED_STRESS_CYCLES
        and int(control.get("stress", {}).get("updates", -1)) == EXPECTED_STRESS_UPDATES
        and int(candidate.get("stress", {}).get("updates", -1)) == EXPECTED_STRESS_UPDATES
    )

    frame_pairs: list[dict[str, Any]] = []
    counters_equal = True
    images_equal = True
    for a, b in zip(control_samples, candidate_samples):
        index = int(a["index"])
        for context in CONTEXTS:
            control_tuple = _runtime_tuple(a, context)
            candidate_tuple = _runtime_tuple(b, context)
            counters_equal = counters_equal and control_tuple == candidate_tuple
            control_capture = a["contexts"][context]["capture"]
            candidate_capture = b["contexts"][context]["capture"]
            control_path = image_root / Path(str(control_capture["path"])).name
            candidate_path = image_root / Path(str(candidate_capture["path"])).name
            if not control_path.exists() or not candidate_path.exists():
                images_equal = False
                frame_pairs.append({"index": index, "context": context, "files_present": False})
                continue
            control_hash = _sha256(control_path)
            candidate_hash = _sha256(candidate_path)
            equal = control_hash == candidate_hash
            images_equal = images_equal and equal
            frame_pairs.append({
                "index": index,
                "context": context,
                "files_present": True,
                "control_sha256": control_hash,
                "candidate_sha256": candidate_hash,
                "byte_identical": equal,
                "control_runtime": {"draw_calls": control_tuple[0], "objects": control_tuple[1], "primitives": control_tuple[2]},
                "candidate_runtime": {"draw_calls": candidate_tuple[0], "objects": candidate_tuple[1], "primitives": candidate_tuple[2]},
            })
    checks["per_frame_render_counters_equal"] = counters_equal and len(frame_pairs) == EXPECTED_SAMPLES * len(CONTEXTS)
    checks["all_control_candidate_frames_byte_identical"] = images_equal and len(frame_pairs) == EXPECTED_SAMPLES * len(CONTEXTS)

    reduction_pct = 100.0 * (EXPECTED_TOTAL_UPDATES - 1) / EXPECTED_TOTAL_UPDATES
    state = "PASS_REUSE_SINGLE_SAPLING_ARRAYMESH_RESOURCE_CHURN_CONTRACT" if all(checks.values()) else "FAIL"
    result = {
        "schema": SCHEMA,
        "study_id": "environment-atmosphere-dynamic-runtime-001",
        "state": state,
        "runtime_head": runtime_head,
        "stacked_on_vfx_head": VFX_HEAD,
        "bounded_variable": "SAPLING_NODE_ARRAYMESH_MATERIAL_RESOURCE_LIFECYCLE_ONLY; WEATHER_RESOURCE_REUSE_HELD_IDENTICAL_IN_BOTH_MODES",
        "checks": checks,
        "measurements": {
            "evidence_updates": EXPECTED_SAMPLES,
            "stress_cycles": EXPECTED_STRESS_CYCLES,
            "stress_updates": EXPECTED_STRESS_UPDATES,
            "total_sapling_updates_per_mode": EXPECTED_TOTAL_UPDATES,
            "control_sapling_resource_constructions_each": int(control_creations.get("sapling_nodes", -1)),
            "candidate_sapling_resource_constructions_each": int(candidate_creations.get("sapling_nodes", -1)),
            "resource_construction_reduction_percent": reduction_pct,
            "control_evidence_submission_usec": control.get("evidence_submission", {}),
            "candidate_evidence_submission_usec": candidate.get("evidence_submission", {}),
            "control_stress_submission_usec": control.get("stress", {}).get("submission", {}),
            "candidate_stress_submission_usec": candidate.get("stress", {}).get("submission", {}),
            "control_memory_observation": _memory_summary(control),
            "candidate_memory_observation": _memory_summary(candidate),
        },
        "visual_tradeoff_for_art_director": "NONE_OBSERVED_IN_EXACT_RETAINED_PROOF_FRAMES" if checks["all_control_candidate_frames_byte_identical"] else "CONTROL_AND_CANDIDATE_RENDER_BYTES_DIFFER; ART_DIRECTOR_REVIEW_REQUIRED",
        "frame_pairs": frame_pairs,
        "acceptance_boundary": "Acceptance is stable exact proof-host sapling resource identity/construction reduction while preserving exact synchronized source states, per-frame draw/object/primitive counters, and retained render bytes. Hosted CPU submission and memory counters are observations only and are not target-device budgets.",
        "non_claims": [
            "No target-device FPS, GPU frame-time, VRAM ceiling, streaming, mobile, console, or production memory budget is claimed.",
            "No physical wind coupling, physics, collision, gameplay, animation-controller, or continuous interpolation acceptance is claimed.",
            "No final Art Direction, Visual QA, CANON, promotion, or Runtime mastery is claimed.",
        ],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--image-root", type=Path, required=True)
    parser.add_argument("--runtime-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(_load(args.control), _load(args.candidate), args.image_root, args.runtime_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
