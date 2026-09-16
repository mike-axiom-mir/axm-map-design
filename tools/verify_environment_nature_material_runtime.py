from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CONTEXTS = ("path_eye", "elevated_oblique")
CONTROL_MODE = "per_mesh_material_control"
CANDIDATE_MODE = "shared_nature_material"
STATE = "PASS_TARGET_HOST_NATURE_MATERIAL_SHARING_OBSERVATION_READY"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _nature_ids(row: dict[str, Any]) -> list[int]:
    return [int(value) for value in row["nature_material_instance_ids"]]


def verify(
    control: dict[str, Any],
    candidate: dict[str, Any],
    artifact_root: Path,
    expected_nature_meshes: int = 3,
) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    checks["control_state"] = control.get("state") == STATE
    checks["candidate_state"] = candidate.get("state") == STATE
    checks["control_mode"] = control.get("mode") == CONTROL_MODE
    checks["candidate_mode"] = candidate.get("mode") == CANDIDATE_MODE
    checks["same_scene_digest"] = bool(control.get("scene_digest")) and control.get("scene_digest") == candidate.get("scene_digest")
    checks["same_receiving_head"] = bool(control.get("receiving_head")) and control.get("receiving_head") == candidate.get("receiving_head")
    checks["same_source_integration"] = control.get("source_integration") == candidate.get("source_integration")
    checks["same_weather_presentation"] = control.get("weather_presentation") == candidate.get("weather_presentation")

    control_contexts = control.get("contexts", {})
    candidate_contexts = candidate.get("contexts", {})
    checks["exact_context_set"] = set(control_contexts) == set(CONTEXTS) == set(candidate_contexts)

    context_rows: dict[str, Any] = {}
    candidate_shared_ids: list[int] = []
    for context in CONTEXTS:
        c_row = control_contexts.get(context, {})
        s_row = candidate_contexts.get(context, {})
        c_ids = _nature_ids(c_row) if c_row else []
        s_ids = _nature_ids(s_row) if s_row else []
        c_unique = set(c_ids)
        s_unique = set(s_ids)
        c_runtime = c_row.get("runtime", {})
        s_runtime = s_row.get("runtime", {})
        renderer_equal = all(
            c_runtime.get(key) == s_runtime.get(key)
            for key in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame")
        )
        source_identity_equal = (
            c_row.get("sapling") == s_row.get("sapling")
            and c_row.get("additional_source_meshes") == s_row.get("additional_source_meshes")
            and c_row.get("weather") == s_row.get("weather")
            and c_row.get("proxy_count") == s_row.get("proxy_count")
        )
        # Material instance IDs are intentionally different between modes, so compare
        # source rows after removing only that runtime identity field.
        def strip_material_id(row: dict[str, Any]) -> dict[str, Any]:
            return {k: v for k, v in row.items() if k != "material_instance_id"}

        source_identity_equal = (
            strip_material_id(c_row.get("sapling", {})) == strip_material_id(s_row.get("sapling", {}))
            and [strip_material_id(x) for x in c_row.get("additional_source_meshes", [])]
            == [strip_material_id(x) for x in s_row.get("additional_source_meshes", [])]
            and c_row.get("weather") == s_row.get("weather")
            and c_row.get("proxy_count") == s_row.get("proxy_count")
        )
        context_rows[context] = {
            "control_nature_meshes": int(c_row.get("nature_source_mesh_count", -1)),
            "candidate_nature_meshes": int(s_row.get("nature_source_mesh_count", -1)),
            "control_unique_nature_material_ids": len(c_unique),
            "candidate_unique_nature_material_ids": len(s_unique),
            "renderer_submission_counters_equal": renderer_equal,
            "source_rows_equal_except_material_instance_id": source_identity_equal,
            "control_runtime": c_runtime,
            "candidate_runtime": s_runtime,
        }
        checks[f"{context}_nature_mesh_count"] = (
            c_row.get("nature_source_mesh_count") == expected_nature_meshes
            and s_row.get("nature_source_mesh_count") == expected_nature_meshes
        )
        checks[f"{context}_control_one_material_per_nature_mesh"] = len(c_ids) == expected_nature_meshes and len(c_unique) == expected_nature_meshes
        checks[f"{context}_candidate_one_shared_nature_material"] = len(s_ids) == expected_nature_meshes and len(s_unique) == 1
        checks[f"{context}_renderer_submission_counters_equal"] = renderer_equal
        checks[f"{context}_source_rows_equal_except_material_instance_id"] = source_identity_equal
        if len(s_unique) == 1:
            candidate_shared_ids.extend(s_unique)

        control_image = artifact_root / f"control_{context}.png"
        candidate_image = artifact_root / f"candidate_{context}.png"
        image_exists = control_image.is_file() and candidate_image.is_file()
        checks[f"{context}_images_exist"] = image_exists
        if image_exists:
            checks[f"{context}_images_byte_identical"] = control_image.read_bytes() == candidate_image.read_bytes()
            context_rows[context]["control_image_sha256"] = _sha256(control_image)
            context_rows[context]["candidate_image_sha256"] = _sha256(candidate_image)
        else:
            checks[f"{context}_images_byte_identical"] = False

    expected_control_constructions = expected_nature_meshes * len(CONTEXTS)
    control_constructions = int(control.get("created_nature_materials", -1))
    candidate_constructions = int(candidate.get("created_nature_materials", -1))
    checks["control_construction_count"] = control_constructions == expected_control_constructions
    checks["candidate_construction_count"] = candidate_constructions == 1
    checks["candidate_material_identity_shared_across_contexts"] = len(candidate_shared_ids) == len(CONTEXTS) and len(set(candidate_shared_ids)) == 1

    reduction = None
    if control_constructions > 0 and candidate_constructions >= 0:
        reduction = 100.0 * (control_constructions - candidate_constructions) / control_constructions

    status = "PASS_SHARE_ONE_IMMUTABLE_NATURE_MATERIAL_RESOURCE" if all(checks.values()) else "FAIL_NATURE_MATERIAL_SHARING_EVIDENCE"
    return {
        "schema": "axm.environment-nature-material-runtime-evidence/v0.1",
        "status": status,
        "scene_digest": control.get("scene_digest", ""),
        "receiving_head": control.get("receiving_head", ""),
        "expected_nature_source_meshes_per_context": expected_nature_meshes,
        "observation_contexts": list(CONTEXTS),
        "control_nature_material_constructions": control_constructions,
        "candidate_nature_material_constructions": candidate_constructions,
        "nature_material_construction_reduction_percent": reduction,
        "contexts": context_rows,
        "checks": checks,
        "visual_tradeoff": "NONE_OBSERVED_IN_EXACT_RETAINED_PROOF_FRAMES" if all(checks.get(f"{ctx}_images_byte_identical", False) for ctx in CONTEXTS) else "REVIEW_REQUIRED",
        "truth_boundary": (
            "PASS proves only that the exact current three-source Nature receiving scene can reuse one immutable proof-host Nature StandardMaterial3D across all three Nature meshes and both fixed observation contexts, while retained images and draw/object/primitive counters remain identical. It does not prove target-device FPS, GPU time, VRAM, production allocator behavior, LOD/streaming policy, final materials, gameplay, CANON, production readiness, or Runtime mastery."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-nature-meshes", type=int, default=3)
    args = parser.parse_args()

    evidence = verify(_load(args.control), _load(args.candidate), args.artifact_root, args.expected_nature_meshes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
