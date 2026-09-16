from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_eye_level as eye
import environment_rear_tree_normal_culling as rear_culling

SCHEMA = "axm.environment-object-source-replacement/v0.1"
EVIDENCE_SCHEMA = "axm.environment-object-source-replacement-evidence/v0.1"
CANDIDATE_SCENE_SCHEMA = "axm.environment-object-source-replacement-proof/v0.1"
STATUS = "PASS_WEST_OBJECT_SOURCE_REPLACEMENT_STRUCTURE"
PLACEMENT_POLICY = "PRESERVE_TARGET_CENTER_XY__PRESERVE_TARGET_Z_ROTATION__GROUND_SOURCE_MIN_Z__NO_SOURCE_SCALE"


def load_manifest(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unsupported Object source replacement schema")
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bounds(vertices: list[list[float]]) -> dict:
    if not vertices:
        raise ValueError("mesh has no vertices")
    mins = [min(float(v[i]) for v in vertices) for i in range(3)]
    maxs = [max(float(v[i]) for v in vertices) for i in range(3)]
    return {"min": mins, "max": maxs, "size": [maxs[i] - mins[i] for i in range(3)]}


def _footprint_from_bounds(bounds: dict) -> tuple[float, float, float, float]:
    return (
        float(bounds["min"][0]),
        float(bounds["max"][0]),
        float(bounds["min"][1]),
        float(bounds["max"][1]),
    )


def _item_footprint(item: dict) -> tuple[float, float, float, float]:
    p = item["position_m"]
    s = item["size_m"]
    x, y = float(p[0]), float(p[1])
    sx, sy = float(s[0]), float(s[1])
    return (x - sx * 0.5, x + sx * 0.5, y - sy * 0.5, y + sy * 0.5)


def _mesh_footprint(source: dict) -> tuple[float, float, float, float]:
    return _footprint_from_bounds(_bounds(source["vertices_source_xyz_m"]))


def _intersects(a, b, clearance: float = 0.0) -> bool:
    return not (
        a[1] + clearance <= b[0]
        or b[1] + clearance <= a[0]
        or a[3] + clearance <= b[2]
        or b[3] + clearance <= a[2]
    )


def _inside(inner, outer, tolerance: float = 1e-9) -> bool:
    return (
        inner[0] >= outer[0] - tolerance
        and inner[1] <= outer[1] + tolerance
        and inner[2] >= outer[2] - tolerance
        and inner[3] <= outer[3] + tolerance
    )


def _vector_matches(actual, expected, tolerance: float = 1e-9) -> bool:
    return (
        isinstance(actual, list)
        and len(actual) == len(expected)
        and all(abs(float(actual[i]) - float(expected[i])) <= tolerance for i in range(len(expected)))
    )


def _parse_obj(path: Path) -> dict:
    vertices: list[list[float]] = []
    triangles: list[list[int]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("v "):
            _, x, y, z = line.split()
            vertices.append([float(x), float(y), float(z)])
        elif line.startswith("f "):
            parts = line.split()[1:]
            if len(parts) != 3:
                raise ValueError("Object proof OBJ must remain triangulated")
            triangles.append([int(part.split("/")[0]) - 1 for part in parts])
    if not vertices or not triangles:
        raise ValueError("Object proof OBJ contains no usable mesh")
    return {"vertices": vertices, "triangles": triangles}


def _load_object_source(object_root: str | Path, cfg: dict) -> tuple[dict, dict, dict, str, str]:
    root = Path(object_root).resolve()
    source_path = root / cfg["source_path"]
    builder_path = root / cfg["builder_path"]
    if not source_path.exists() or not builder_path.exists():
        raise ValueError("exact Object source checkout is incomplete")
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "object-source-evidence"
        subprocess.run(
            [
                sys.executable,
                str(builder_path),
                "--source",
                str(source_path),
                "--out-dir",
                str(output),
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        obj_path = output / "modular-equipment-case-001.obj"
        receipt_path = output / "structural-receipt.json"
        if not obj_path.exists() or not receipt_path.exists():
            raise ValueError("Object source builder did not retain its expected outputs")
        source = json.loads(source_path.read_text(encoding="utf-8"))
        mesh = _parse_obj(obj_path)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        source_sha = _sha256(source_path)
        obj_sha = _sha256(obj_path)
    return source, mesh, receipt, source_sha, obj_sha


def _world_mesh(local_mesh: dict, target: dict) -> tuple[dict, dict]:
    local_bounds = _bounds(local_mesh["vertices"])
    p = [float(value) for value in target["position_m"]]
    s = [float(value) for value in target["size_m"]]
    rotation_deg = float(target.get("rotation_deg", 0.0))
    angle = math.radians(rotation_deg)
    ca, sa = math.cos(angle), math.sin(angle)
    center_x = (float(local_bounds["min"][0]) + float(local_bounds["max"][0])) * 0.5
    center_y = (float(local_bounds["min"][1]) + float(local_bounds["max"][1])) * 0.5
    target_ground_z = p[2] - s[2] * 0.5
    tz = target_ground_z - float(local_bounds["min"][2])
    vertices: list[list[float]] = []
    for v in local_mesh["vertices"]:
        lx = float(v[0]) - center_x
        ly = float(v[1]) - center_y
        rx = lx * ca - ly * sa
        ry = lx * sa + ly * ca
        vertices.append([p[0] + rx, p[1] + ry, float(v[2]) + tz])
    world = {
        "vertices": vertices,
        "triangles": copy.deepcopy(local_mesh["triangles"]),
    }
    return world, _bounds(vertices)


def _preserved_items_except_target(baseline: list[dict], candidate: list[dict], target_id: str) -> bool:
    before = {row["asset_id"]: row for row in baseline if row["asset_id"] != target_id}
    after = {row["asset_id"]: row for row in candidate}
    return before == after and target_id not in after


def build_payloads(
    manifest_path: str | Path,
    base_nature_root: str | Path,
    compact_nature_root: str | Path,
    weather_root: str | Path,
    building_root: str | Path,
    historical_rear_root: str | Path,
    migrated_rear_root: str | Path,
    object_root: str | Path,
) -> tuple[dict, dict, dict]:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(manifest_path)
    base_cfg = manifest["base_environment"]
    replacement = manifest["replacement"]

    rear_manifest = root / base_cfg["rear_culling_manifest"]
    _, baseline, rear_report = rear_culling.build_payloads(
        rear_manifest,
        base_nature_root,
        compact_nature_root,
        weather_root,
        building_root,
        historical_rear_root,
        migrated_rear_root,
    )
    if rear_report.get("status") != rear_culling.STATUS:
        raise ValueError("exact migrated rear-tree Environment scene must PASS first")

    target_id = replacement["target_asset_id"]
    targets = [row for row in baseline["items"] if row.get("asset_id") == target_id]
    if len(targets) != 1:
        raise ValueError("Object replacement target must exist exactly once")
    target = copy.deepcopy(targets[0])
    if target.get("kind") != replacement["expected_target_kind"] or target.get("evidence") != "PROXY_ONLY":
        raise ValueError("Object replacement target must remain an explicit Object proxy")

    object_source, local_mesh, object_receipt, source_sha, obj_sha = _load_object_source(object_root, replacement)
    world_mesh, world_bounds = _world_mesh(local_mesh, target)
    world_footprint = _footprint_from_bounds(world_bounds)

    p = [float(value) for value in target["position_m"]]
    s = [float(value) for value in target["size_m"]]
    reserved_bounds = {
        "min": [p[0] - s[0] * 0.5, p[1] - s[1] * 0.5, p[2] - s[2] * 0.5],
        "max": [p[0] + s[0] * 0.5, p[1] + s[1] * 0.5, p[2] + s[2] * 0.5],
    }
    reserved_bounds["size"] = [reserved_bounds["max"][i] - reserved_bounds["min"][i] for i in range(3)]
    reserved_footprint = _footprint_from_bounds(reserved_bounds)

    path = baseline["readable_path"]
    path_box = (
        float(path["x_min"]),
        float(path["x_max"]),
        float(path["y_min"]),
        float(path["y_max"]),
    )
    minimum_gap = 0.35
    spacing_conflicts: list[str] = []
    for item in baseline["items"]:
        if item.get("asset_id") == target_id or item.get("kind") == "map-surface":
            continue
        if _intersects(world_footprint, _item_footprint(item), minimum_gap):
            spacing_conflicts.append(str(item.get("asset_id")))
    if _intersects(world_footprint, _mesh_footprint(baseline["sapling"]), minimum_gap):
        spacing_conflicts.append(str(baseline["sapling"].get("asset_id")))
    for source_mesh in baseline.get("additional_source_meshes", []):
        if _intersects(world_footprint, _mesh_footprint(source_mesh), minimum_gap):
            spacing_conflicts.append(str(source_mesh.get("asset_id")))

    candidate = copy.deepcopy(baseline)
    candidate["schema"] = CANDIDATE_SCENE_SCHEMA
    candidate["study_id"] = manifest["study_id"]
    candidate["receiving_head"] = os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD")
    candidate["items"] = [row for row in candidate["items"] if row.get("asset_id") != target_id]
    source_asset_id = f"source:object:{object_source['asset_id']}"
    candidate.setdefault("additional_source_meshes", []).append(
        {
            "asset_id": source_asset_id,
            "kind": replacement["source_render_kind"],
            "truth_state": replacement["truth_state"],
            "source_repository": replacement["repository"],
            "source_head": replacement["head"],
            "source_sha256": source_sha,
            "obj_sha256": obj_sha,
            "vertices_source_xyz_m": [[float(v) for v in row] for row in world_mesh["vertices"]],
            "triangles": [[int(v) for v in tri] for tri in world_mesh["triangles"]],
            "proof_render_culling": "DISABLED_FOR_ENVIRONMENT_OBSERVATION_ONLY_NOT_OBJECT_MATERIAL_OR_TOPOLOGY_ACCEPTANCE",
        }
    )
    candidate["environment_object_replacement"] = {
        "target_asset_id": target_id,
        "source_asset_id": source_asset_id,
        "reserved_proxy_position_m": copy.deepcopy(target["position_m"]),
        "reserved_proxy_size_m": copy.deepcopy(target["size_m"]),
        "reserved_proxy_rotation_deg": float(target.get("rotation_deg", 0.0)),
        "reserved_proxy_footprint_m": list(reserved_footprint),
        "source_world_bounds_m": world_bounds,
        "source_world_footprint_m": list(world_footprint),
        "source_repository": replacement["repository"],
        "source_head": replacement["head"],
        "source_sha256": source_sha,
        "obj_sha256": obj_sha,
        "placement_policy": replacement["placement_policy"],
        "relationship": "WEST_OBJECT_PROXY_TO_EXACT_OBJECT_SOURCE_ONLY",
        "source_structural_result": object_receipt.get("result"),
    }
    candidate["truth_boundary"] = manifest["truth_boundary"]
    candidate.pop("scene_digest", None)
    candidate["scene_digest"] = eye.digest(candidate)

    observed_object_head = os.environ.get("AXM_OBJECT_HEAD", replacement["head"])
    expected_rotation = float(replacement["expected_reserved_rotation_deg"])
    east_proxy_before = [row for row in baseline["items"] if row.get("asset_id") == "proxy:object-crate-east"]
    east_proxy_after = [row for row in candidate["items"] if row.get("asset_id") == "proxy:object-crate-east"]

    checks = {
        "migrated_rear_tree_baseline_passes_first": rear_report.get("status") == rear_culling.STATUS,
        "declared_base_environment_head_matches": base_cfg["exact_head"] == "f548f98959bf6769716a6d7c87bac69f9f548389",
        "seed_matches": int(rear_report["preserved_context"]["seed"]) == int(base_cfg["seed"]),
        "target_is_exact_west_object_proxy": target.get("asset_id") == target_id and target.get("kind") == replacement["expected_target_kind"] and target.get("evidence") == "PROXY_ONLY",
        "target_position_matches": _vector_matches(target.get("position_m"), replacement["expected_reserved_position_m"]),
        "target_size_matches": _vector_matches(target.get("size_m"), replacement["expected_reserved_size_m"]),
        "target_rotation_matches": abs(float(target.get("rotation_deg", 0.0)) - expected_rotation) <= 1e-9,
        "object_checkout_head_matches": observed_object_head == replacement["head"],
        "object_asset_id_matches": object_source.get("asset_id") == replacement["expected_asset_id"],
        "object_source_digest_matches": source_sha == replacement["expected_source_sha256"],
        "object_obj_digest_matches": obj_sha == replacement["expected_obj_sha256"],
        "object_source_structural_result_passes": object_receipt.get("result") == replacement["expected_structural_result"],
        "object_source_has_zero_degenerate_triangles": int(object_receipt.get("degenerate_triangles", -1)) == 0,
        "object_vertex_count_matches": len(local_mesh["vertices"]) == int(replacement["expected_vertices"]) == int(object_receipt.get("vertex_count", -1)),
        "object_triangle_count_matches": len(local_mesh["triangles"]) == int(replacement["expected_triangles"]) == int(object_receipt.get("triangle_count", -1)),
        "placement_policy_is_exact": replacement["placement_policy"] == PLACEMENT_POLICY,
        "source_inside_reserved_proxy_footprint_after_authored_rotation": _inside(world_footprint, reserved_footprint),
        "source_inside_reserved_proxy_height": float(world_bounds["min"][2]) >= float(reserved_bounds["min"][2]) - 1e-9 and float(world_bounds["max"][2]) <= float(reserved_bounds["max"][2]) + 1e-9,
        "source_grounded_at_reserved_ground": abs(float(world_bounds["min"][2]) - float(reserved_bounds["min"][2])) <= 1e-9,
        "readable_path_unblocked_after_replacement": not _intersects(world_footprint, path_box),
        "minimum_spacing_preserved_after_replacement": not spacing_conflicts,
        "unrelated_items_preserved_exactly": _preserved_items_except_target(baseline["items"], candidate["items"], target_id),
        "east_object_proxy_preserved_exactly": len(east_proxy_before) == 1 and east_proxy_before == east_proxy_after,
        "west_sapling_preserved_exactly": baseline["sapling"] == candidate["sapling"],
        "existing_source_meshes_preserved_exactly": candidate.get("additional_source_meshes", [])[:-1] == baseline.get("additional_source_meshes", []),
        "building_nature_source_count_preserved": len(baseline.get("additional_source_meshes", [])) == len(candidate.get("additional_source_meshes", [])) - 1,
        "weather_preserved_exactly": baseline["weather_lines"] == candidate["weather_lines"] and baseline["weather_presentation"] == candidate["weather_presentation"],
        "readable_path_preserved_exactly": baseline["readable_path"] == candidate["readable_path"],
        "cameras_preserved_exactly": baseline["cameras"] == candidate["cameras"],
        "rear_tree_culling_review_preserved_exactly": baseline.get("environment_rear_tree_culling_review") == candidate.get("environment_rear_tree_culling_review"),
        "one_object_source_mesh_added": len(candidate.get("additional_source_meshes", [])) == len(baseline.get("additional_source_meshes", [])) + 1,
        "candidate_scene_digest_differs": candidate["scene_digest"] != baseline["scene_digest"],
        "comparison_policy_isolated": manifest["comparison_policy"].get("isolate_delta") == "WEST_OBJECT_PROXY_TO_EXACT_OBJECT_SOURCE_ONLY",
        "object_materials_not_consumed": manifest["comparison_policy"].get("consume_object_materials_pr6") is False,
        "object_rigging_not_consumed": manifest["comparison_policy"].get("consume_object_rigging_pr15") is False,
        "object_animation_not_consumed": manifest["comparison_policy"].get("consume_object_animation_pr10") is False,
        "object_runtime_not_consumed": manifest["comparison_policy"].get("consume_object_runtime_pr13") is False,
        "object_uc_target_handoff_not_consumed": manifest["comparison_policy"].get("consume_object_uc_target_handoff_pr7") is False,
        "map_materials_not_consumed": manifest["comparison_policy"].get("consume_map_materials_pr14") is False,
        "map_vfx_not_consumed": manifest["comparison_policy"].get("consume_map_vfx_pr16") is False,
        "map_runtime_not_consumed": manifest["comparison_policy"].get("consume_map_runtime_pr17") is False,
    }

    report = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": manifest["study_id"],
        "status": STATUS if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": candidate["receiving_head"],
        "base_environment_head": base_cfg["exact_head"],
        "baseline_scene_digest": baseline["scene_digest"],
        "candidate_scene_digest": candidate["scene_digest"],
        "target": {
            "asset_id": target_id,
            "position_m": copy.deepcopy(target["position_m"]),
            "size_m": copy.deepcopy(target["size_m"]),
            "rotation_deg": float(target.get("rotation_deg", 0.0)),
            "reserved_bounds_m": reserved_bounds,
        },
        "object_source": {
            "repository": replacement["repository"],
            "head": replacement["head"],
            "asset_id": object_source.get("asset_id"),
            "source_sha256": source_sha,
            "obj_sha256": obj_sha,
            "vertices": len(local_mesh["vertices"]),
            "triangles": len(local_mesh["triangles"]),
            "structural_result": object_receipt.get("result"),
            "world_bounds_m": world_bounds,
            "world_footprint_m": list(world_footprint),
            "placement_policy": replacement["placement_policy"],
        },
        "spacing_conflicts": spacing_conflicts,
        "preserved_context": {
            "seed": int(base_cfg["seed"]),
            "source_meshes_before": len(baseline.get("additional_source_meshes", [])),
            "source_meshes_after": len(candidate.get("additional_source_meshes", [])),
            "remaining_object_proxy": "proxy:object-crate-east",
            "weather_streaks": len(baseline["weather_lines"]),
            "camera_names": sorted(baseline["cameras"]),
            "rear_tree_culling_target": baseline.get("environment_rear_tree_culling_review", {}).get("target_asset_id"),
        },
        "truth_boundary": manifest["truth_boundary"],
    }
    return baseline, candidate, report


def build(
    manifest_path: str | Path,
    base_nature_root: str | Path,
    compact_nature_root: str | Path,
    weather_root: str | Path,
    building_root: str | Path,
    historical_rear_root: str | Path,
    migrated_rear_root: str | Path,
    object_root: str | Path,
    output_dir: str | Path,
) -> dict:
    baseline, candidate, report = build_payloads(
        manifest_path,
        base_nature_root,
        compact_nature_root,
        weather_root,
        building_root,
        historical_rear_root,
        migrated_rear_root,
        object_root,
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "baseline_scene_runtime.json").write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "candidate_scene_runtime.json").write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "object_receiving_evidence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_object_source_replacement_001.json")
    parser.add_argument("--base-nature-root", required=True)
    parser.add_argument("--compact-nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--building-root", required=True)
    parser.add_argument("--historical-rear-root", required=True)
    parser.add_argument("--migrated-rear-root", required=True)
    parser.add_argument("--object-root", required=True)
    parser.add_argument("--output", default="evidence/environment_object_source_replacement_001")
    args = parser.parse_args()
    report = build(
        args.manifest,
        args.base_nature_root,
        args.compact_nature_root,
        args.weather_root,
        args.building_root,
        args.historical_rear_root,
        args.migrated_rear_root,
        args.object_root,
        args.output,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == STATUS else 1)


if __name__ == "__main__":
    main()
