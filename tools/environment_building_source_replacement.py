from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_east_tree_replacement as east
import environment_eye_level as eye

SCHEMA = "axm.environment-building-source-replacement/v0.1"
EVIDENCE_SCHEMA = "axm.environment-building-source-replacement-evidence/v0.1"
CANDIDATE_SCENE_SCHEMA = "axm.environment-building-source-replacement-proof/v0.1"
PLACEMENT_POLICY = "PRESERVE_TARGET_CENTER_XY__GROUND_SOURCE_MIN_Z__NO_SOURCE_SCALE__NO_EXTRA_ROTATION"


def load_manifest(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unsupported building replacement schema")
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bounds(vertices: list[list[float]]) -> dict:
    if not vertices:
        raise ValueError("mesh has no vertices")
    mins = [min(float(v[i]) for v in vertices) for i in range(3)]
    maxs = [max(float(v[i]) for v in vertices) for i in range(3)]
    return {"min": mins, "max": maxs, "size": [maxs[i] - mins[i] for i in range(3)]}


def _footprint(bounds: dict) -> tuple[float, float, float, float]:
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
    return _footprint(_bounds(source["vertices_source_xyz_m"]))


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


def _load_building_module(building_root: Path):
    module_path = building_root / "tools" / "build_service_pavilion.py"
    spec = importlib.util.spec_from_file_location("axm_building_service_pavilion", module_path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load Building source evaluator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_obj(lines: list[str]) -> dict:
    vertices: list[list[float]] = []
    triangles: list[list[int]] = []
    for line in lines:
        if line.startswith("v "):
            _, x, y, z = line.split()
            vertices.append([float(x), float(y), float(z)])
        elif line.startswith("f "):
            parts = line.split()[1:]
            if len(parts) != 3:
                raise ValueError("building proof OBJ must remain triangulated")
            triangles.append([int(part.split("/")[0]) - 1 for part in parts])
    if not vertices or not triangles:
        raise ValueError("building proof OBJ contains no usable mesh")
    return {"vertices": vertices, "triangles": triangles}


def _world_mesh(local_mesh: dict, target: dict) -> tuple[dict, dict]:
    local_bounds = _bounds(local_mesh["vertices"])
    p = [float(value) for value in target["position_m"]]
    s = [float(value) for value in target["size_m"]]
    if abs(float(target.get("rotation_deg", 0.0))) > 1e-12:
        raise ValueError("v0.1 building replacement does not accept rotated receiving slots")
    target_ground_z = p[2] - s[2] * 0.5
    tx = p[0]
    ty = p[1]
    tz = target_ground_z - float(local_bounds["min"][2])
    vertices = [
        [float(v[0]) + tx, float(v[1]) + ty, float(v[2]) + tz]
        for v in local_mesh["vertices"]
    ]
    world = {"vertices": vertices, "triangles": copy.deepcopy(local_mesh["triangles"])}
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
) -> tuple[dict, dict, dict]:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(manifest_path)
    baseline_cfg = manifest["baseline_environment"]
    replacement_cfg = manifest["replacement"]

    east_manifest = root / baseline_cfg["east_tree_manifest"]
    _, baseline, east_report = east.build_payloads(
        east_manifest,
        base_nature_root,
        compact_nature_root,
        weather_root,
    )
    if east_report["status"] != "PASS_EAST_FOREGROUND_SOURCE_REPLACEMENT_STRUCTURE":
        raise ValueError("accepted east-tree Environment state must PASS first")

    target_id = replacement_cfg["target_asset_id"]
    targets = [row for row in baseline["items"] if row["asset_id"] == target_id]
    if len(targets) != 1:
        raise ValueError("building replacement target must exist exactly once")
    target = copy.deepcopy(targets[0])
    if target.get("kind") != "building-proxy" or target.get("evidence") != "PROXY_ONLY":
        raise ValueError("building replacement target must remain an explicit building proxy")

    building_root = Path(building_root)
    pavilion_path = building_root / replacement_cfg["pavilion_source_path"]
    panel_path = building_root / replacement_cfg["panel_source_path"]
    building = _load_building_module(building_root)
    pavilion, panel, fits, obj_lines, mins, maxs, source_path_gap, negatives = building.build()

    local_mesh = _parse_obj(obj_lines)
    world_mesh, world_bounds = _world_mesh(local_mesh, target)
    world_footprint = _footprint(world_bounds)
    reserved_bounds = {
        "min": [
            float(target["position_m"][0]) - float(target["size_m"][0]) * 0.5,
            float(target["position_m"][1]) - float(target["size_m"][1]) * 0.5,
            float(target["position_m"][2]) - float(target["size_m"][2]) * 0.5,
        ],
        "max": [
            float(target["position_m"][0]) + float(target["size_m"][0]) * 0.5,
            float(target["position_m"][1]) + float(target["size_m"][1]) * 0.5,
            float(target["position_m"][2]) + float(target["size_m"][2]) * 0.5,
        ],
    }
    reserved_bounds["size"] = [reserved_bounds["max"][i] - reserved_bounds["min"][i] for i in range(3)]
    reserved_footprint = _footprint(reserved_bounds)

    path = baseline["readable_path"]
    path_box = (float(path["x_min"]), float(path["x_max"]), float(path["y_min"]), float(path["y_max"]))
    minimum_gap = 0.35

    spacing_conflicts: list[str] = []
    for item in baseline["items"]:
        if item["asset_id"] == target_id or item["kind"] == "map-surface":
            continue
        if _intersects(world_footprint, _item_footprint(item), minimum_gap):
            spacing_conflicts.append(item["asset_id"])
    if _intersects(world_footprint, _mesh_footprint(baseline["sapling"]), minimum_gap):
        spacing_conflicts.append(baseline["sapling"]["asset_id"])
    for source in baseline.get("additional_source_meshes", []):
        if _intersects(world_footprint, _mesh_footprint(source), minimum_gap):
            spacing_conflicts.append(source["asset_id"])

    candidate = copy.deepcopy(baseline)
    candidate["schema"] = CANDIDATE_SCENE_SCHEMA
    candidate["study_id"] = manifest["study_id"]
    candidate["receiving_head"] = os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD")
    candidate["items"] = [row for row in candidate["items"] if row["asset_id"] != target_id]
    candidate.setdefault("additional_source_meshes", []).append(
        {
            "asset_id": f"source:building:{pavilion['asset_id']}",
            "kind": "building-source",
            "truth_state": replacement_cfg["truth_state"],
            "source_repository": replacement_cfg["repository"],
            "source_head": replacement_cfg["head"],
            "pavilion_source_sha256": _sha256(pavilion_path),
            "panel_source_sha256": _sha256(panel_path),
            "vertices_source_xyz_m": world_mesh["vertices"],
            "triangles": world_mesh["triangles"],
            "proof_render_culling": "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_MATERIAL_ACCEPTANCE",
        }
    )
    candidate["environment_building_replacement"] = {
        "target_asset_id": target_id,
        "reserved_proxy_position_m": copy.deepcopy(target["position_m"]),
        "reserved_proxy_size_m": copy.deepcopy(target["size_m"]),
        "reserved_proxy_footprint_m": list(reserved_footprint),
        "source_world_bounds_m": world_bounds,
        "source_world_footprint_m": list(world_footprint),
        "source_repository": replacement_cfg["repository"],
        "source_head": replacement_cfg["head"],
        "pavilion_source_sha256": _sha256(pavilion_path),
        "panel_source_sha256": _sha256(panel_path),
        "placement_policy": replacement_cfg["placement_policy"],
        "relationship": "BUILDING_PROXY_TO_EXACT_BUILDING_SOURCE_ONLY",
        "receiver_count": len(fits),
    }
    candidate["truth_boundary"] = manifest["truth_boundary"]
    candidate.pop("scene_digest", None)
    candidate["scene_digest"] = eye.digest(candidate)

    observed_building_head = os.environ.get("AXM_BUILDING_HEAD", replacement_cfg["head"])
    source_slot_size = [float(value) for value in pavilion["provenance"]["map_slot_size_m"]]
    source_slot_position = [float(value) for value in pavilion["provenance"]["map_slot_position_m"]]
    target_size = [float(value) for value in target["size_m"]]
    target_position = [float(value) for value in target["position_m"]]
    source_world_path_gap = float(world_bounds["min"][1]) - float(path["y_max"])

    checks = {
        "east_tree_baseline_passes_first": east_report["status"] == "PASS_EAST_FOREGROUND_SOURCE_REPLACEMENT_STRUCTURE",
        "seed_matches": int(east_report["preserved_context"]["seed"]) == int(baseline_cfg["seed"]),
        "target_is_exact_building_proxy": target["asset_id"] == target_id and target["kind"] == "building-proxy" and target.get("evidence") == "PROXY_ONLY",
        "building_checkout_head_matches": observed_building_head == replacement_cfg["head"],
        "pavilion_asset_id_matches": pavilion.get("asset_id") == replacement_cfg["expected_pavilion_asset_id"],
        "panel_asset_id_matches": panel.get("asset_id") == replacement_cfg["expected_panel_asset_id"],
        "pavilion_source_digest_matches": _sha256(pavilion_path) == replacement_cfg["expected_pavilion_source_sha256"],
        "panel_source_digest_matches": _sha256(panel_path) == replacement_cfg["expected_panel_source_sha256"],
        "building_source_slot_size_matches_target": source_slot_size == replacement_cfg["expected_reserved_slot_size_m"] == target_size,
        "building_source_slot_position_matches_target": source_slot_position == replacement_cfg["expected_reserved_slot_position_m"] == target_position,
        "placement_policy_is_exact": replacement_cfg["placement_policy"] == PLACEMENT_POLICY,
        "source_build_succeeds_with_two_receivers": len(fits) == int(replacement_cfg["expected_receiver_count"]),
        "source_negative_controls_remain_rejected": all(str(value).startswith("REJECTED") for value in negatives.values()),
        "source_vertex_count_matches": len(local_mesh["vertices"]) == int(replacement_cfg["expected_vertices"]),
        "source_triangle_count_matches": len(local_mesh["triangles"]) == int(replacement_cfg["expected_triangles"]),
        "source_inside_reserved_proxy_footprint": _inside(world_footprint, reserved_footprint),
        "source_inside_reserved_proxy_height": float(world_bounds["min"][2]) >= float(reserved_bounds["min"][2]) - 1e-9 and float(world_bounds["max"][2]) <= float(reserved_bounds["max"][2]) + 1e-9,
        "source_grounded_at_reserved_ground": abs(float(world_bounds["min"][2]) - float(reserved_bounds["min"][2])) <= 1e-9,
        "source_readable_path_gap_preserved": source_world_path_gap + 1e-9 >= minimum_gap and not _intersects(world_footprint, path_box),
        "building_source_path_gap_matches_own_evidence": abs(source_world_path_gap - float(source_path_gap)) <= 1e-9,
        "minimum_spacing_preserved": not spacing_conflicts,
        "unrelated_items_preserved_exactly": _preserved_items_except_target(baseline["items"], candidate["items"], target_id),
        "west_sapling_preserved_exactly": baseline["sapling"] == candidate["sapling"],
        "accepted_east_tree_preserved_exactly": baseline.get("additional_source_meshes", []) == candidate.get("additional_source_meshes", [])[:-1],
        "weather_preserved_exactly": baseline["weather_lines"] == candidate["weather_lines"] and baseline["weather_presentation"] == candidate["weather_presentation"],
        "cameras_preserved_exactly": baseline["cameras"] == candidate["cameras"],
        "readable_path_preserved_exactly": baseline["readable_path"] == candidate["readable_path"],
        "one_building_source_mesh_added": len(candidate.get("additional_source_meshes", [])) == len(baseline.get("additional_source_meshes", [])) + 1,
        "candidate_scene_digest_differs": candidate["scene_digest"] != baseline["scene_digest"],
        "comparison_policy_isolated": manifest["comparison_policy"].get("isolate_delta") == "BUILDING_PROXY_TO_EXACT_BUILDING_SOURCE_ONLY",
        "building_materials_not_consumed": manifest["comparison_policy"].get("building_materials_pr3_consumed") is False,
    }

    report = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": manifest["study_id"],
        "status": "PASS_BUILDING_SOURCE_REPLACEMENT_STRUCTURE" if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": candidate["receiving_head"],
        "baseline_scene_digest": baseline["scene_digest"],
        "candidate_scene_digest": candidate["scene_digest"],
        "baseline_exact_environment_head": baseline_cfg["exact_head"],
        "replacement": copy.deepcopy(candidate["environment_building_replacement"]),
        "building_source": {
            "pavilion_asset_id": pavilion["asset_id"],
            "panel_asset_id": panel["asset_id"],
            "vertices": len(local_mesh["vertices"]),
            "triangles": len(local_mesh["triangles"]),
            "component_boxes": len(pavilion["components"]),
            "receiver_count": len(fits),
            "local_bounds_m": {"min": mins, "max": maxs, "size": [maxs[i] - mins[i] for i in range(3)]},
            "source_path_gap_m": float(source_path_gap),
            "world_path_gap_m": source_world_path_gap,
            "receiver_fits": fits,
        },
        "spacing_conflicts": spacing_conflicts,
        "preserved_context": {
            "seed": east_report["preserved_context"]["seed"],
            "west_sapling_source_digest": east_report["preserved_context"]["west_sapling_source_digest"],
            "weather_source_digest": east_report["preserved_context"]["weather_source_digest"],
            "accepted_east_tree_source_digest": east_report["replacement"]["source_digest"],
            "camera_names": sorted(baseline["cameras"]),
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
    output_dir: str | Path,
) -> dict:
    baseline, candidate, report = build_payloads(
        manifest_path,
        base_nature_root,
        compact_nature_root,
        weather_root,
        building_root,
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "baseline_scene_runtime.json").write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "candidate_scene_runtime.json").write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "replacement_evidence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_building_source_replacement_001.json")
    parser.add_argument("--base-nature-root", required=True)
    parser.add_argument("--compact-nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--building-root", required=True)
    parser.add_argument("--output", default="evidence/environment_building_source_replacement_001")
    args = parser.parse_args()
    report = build(
        args.manifest,
        args.base_nature_root,
        args.compact_nature_root,
        args.weather_root,
        args.building_root,
        args.output,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS_BUILDING_SOURCE_REPLACEMENT_STRUCTURE" else 1)


if __name__ == "__main__":
    main()
