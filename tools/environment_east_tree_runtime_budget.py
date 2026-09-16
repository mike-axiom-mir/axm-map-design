from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "axm.environment-east-tree-runtime-budget-evidence/v0.1"
RECEIPT_SCHEMA = "axm.environment-east-tree-runtime-observation/v0.1"
CONTEXTS = ("path_eye", "elevated_oblique")
RUNTIME_KEYS = (
    "objects_in_frame",
    "primitives_in_frame",
    "draw_calls_in_frame",
    "texture_mem_bytes",
    "buffer_mem_bytes",
)


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _runtime_deltas(baseline: dict, candidate: dict) -> dict:
    result: dict[str, dict[str, int]] = {}
    for context in CONTEXTS:
        b = baseline["contexts"][context]["runtime"]
        c = candidate["contexts"][context]["runtime"]
        result[context] = {key: int(c[key]) - int(b[key]) for key in RUNTIME_KEYS}
    return result


def evaluate(replacement: dict, baseline: dict, candidate: dict, runtime_dir: str | Path) -> dict:
    runtime_dir = Path(runtime_dir)
    image_hashes = {
        f"baseline_{context}": sha256(runtime_dir / f"runtime-east-tree-baseline-{context}.png")
        for context in CONTEXTS
    }
    image_hashes.update(
        {
            f"candidate_{context}": sha256(runtime_dir / f"runtime-east-tree-candidate-{context}.png")
            for context in CONTEXTS
        }
    )

    deltas = _runtime_deltas(baseline, candidate)
    checks = {
        "replacement_structure_passes_first": replacement.get("status") == "PASS_EAST_FOREGROUND_SOURCE_REPLACEMENT_STRUCTURE",
        "baseline_receipt_schema_matches": baseline.get("schema") == RECEIPT_SCHEMA,
        "candidate_receipt_schema_matches": candidate.get("schema") == RECEIPT_SCHEMA,
        "baseline_runtime_observation_passes": baseline.get("state") == "PASS_SCOPED_EAST_TREE_RUNTIME_OBSERVATION",
        "candidate_runtime_observation_passes": candidate.get("state") == "PASS_SCOPED_EAST_TREE_RUNTIME_OBSERVATION",
        "exact_receiving_head_matches": baseline.get("receiving_head") == candidate.get("receiving_head") == replacement.get("receiving_head"),
        "baseline_scene_digest_matches": baseline.get("scene_digest") == replacement.get("baseline_scene_digest"),
        "candidate_scene_digest_matches": candidate.get("scene_digest") == replacement.get("candidate_scene_digest"),
        "godot_version_matches": baseline.get("godot_version") == candidate.get("godot_version"),
        "west_sapling_identity_preserved": baseline.get("sapling") == candidate.get("sapling"),
        "weather_identity_preserved": baseline.get("weather") == candidate.get("weather"),
        "baseline_has_no_additional_source": baseline.get("additional_source_meshes") == [],
        "candidate_has_one_exact_compact_source": len(candidate.get("additional_source_meshes", [])) == 1
        and candidate["additional_source_meshes"][0].get("vertices") == 390
        and candidate["additional_source_meshes"][0].get("triangles") == 570
        and candidate["additional_source_meshes"][0].get("surfaces") == 1,
        "one_proxy_replaced_by_one_source": int(baseline.get("proxy_count", -1)) == int(candidate.get("proxy_count", -1)) + 1,
        "camera_contract_preserved": all(
            baseline["contexts"][context].get("camera") == candidate["contexts"][context].get("camera")
            for context in CONTEXTS
        ),
        "draw_slot_preserved_both_cameras": all(deltas[context]["draw_calls_in_frame"] == 0 for context in CONTEXTS),
        "visible_object_slot_preserved_both_cameras": all(deltas[context]["objects_in_frame"] == 0 for context in CONTEXTS),
        "no_texture_residency_delta": all(deltas[context]["texture_mem_bytes"] == 0 for context in CONTEXTS),
        "path_eye_render_remains_identical": image_hashes["baseline_path_eye"] == image_hashes["candidate_path_eye"],
        "elevated_oblique_render_contains_expected_delta": image_hashes["baseline_elevated_oblique"] != image_hashes["candidate_elevated_oblique"],
    }

    status = "PASS_EAST_TREE_ONE_SLOT_RUNTIME_BUDGET" if all(checks.values()) else "FAIL"
    return {
        "schema": SCHEMA,
        "status": status,
        "receiving_head": candidate.get("receiving_head"),
        "baseline_scene_digest": baseline.get("scene_digest"),
        "candidate_scene_digest": candidate.get("scene_digest"),
        "checks": checks,
        "runtime_deltas_candidate_minus_proxy": deltas,
        "baseline_runtime": {context: baseline["contexts"][context]["runtime"] for context in CONTEXTS},
        "candidate_runtime": {context: candidate["contexts"][context]["runtime"] for context in CONTEXTS},
        "image_hashes": image_hashes,
        "budget_contract": {
            "draw_calls": "NO_INCREASE_BOTH_FIXED_CAMERAS",
            "visible_objects": "NO_INCREASE_BOTH_FIXED_CAMERAS",
            "texture_memory": "NO_INCREASE_BOTH_FIXED_CAMERAS",
            "buffer_memory": "MEASURE_AND_REPORT_NOT_TARGET_BUDGET",
            "renderer_primitives": "MEASURE_AND_REPORT_NOT_SOURCE_TOPOLOGY",
        },
        "visual_tradeoff": {
            "path_eye": "NO_VISIBLE_DELTA_IN_FIXED_VIEW_BY_BYTE_IDENTITY",
            "elevated_oblique": "SOURCE_REPLACEMENT_VISIBLE_BY_BYTE_DIFFERENCE_ART_DIRECTION_ACCEPTANCE_SEPARATE",
        },
        "truth_boundary": "This proves only the comparative proof-host cost of replacing the exact seed-29 east Nature proxy with the exact compact source while preserving the current scene, renderer and cameras. It does not prove target-device FPS/GPU time, a production memory budget, final LOD policy, Art Direction acceptance, gameplay, CANON, or Runtime mastery.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replacement-evidence", required=True)
    parser.add_argument("--baseline-receipt", required=True)
    parser.add_argument("--candidate-receipt", required=True)
    parser.add_argument("--runtime-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    row = evaluate(
        load_json(args.replacement_evidence),
        load_json(args.baseline_receipt),
        load_json(args.candidate_receipt),
        args.runtime_dir,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(row, indent=2, sort_keys=True))
    return 0 if row["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
