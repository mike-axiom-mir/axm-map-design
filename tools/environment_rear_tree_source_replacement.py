from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_building_source_replacement as building
import environment_eye_level as eye

SCHEMA = "axm.environment-rear-tree-source-replacement/v0.1"
EVIDENCE_SCHEMA = "axm.environment-rear-tree-source-replacement-evidence/v0.1"
CANDIDATE_SCENE_SCHEMA = "axm.environment-rear-tree-source-replacement-proof/v0.1"
PLACEMENT_POLICY = "PRESERVE_TARGET_CENTER_XY__GROUND_SOURCE_MIN_Z__NO_FORM_SCALE__NO_EXTRA_ROTATION"


def load_manifest(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unsupported rear-tree replacement schema")
    return data


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


def _footprint_from_item(item: dict) -> tuple[float, float, float, float]:
    x, y = float(item["position_m"][0]), float(item["position_m"][1])
    sx, sy = float(item["size_m"][0]), float(item["size_m"][1])
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


def _load_rear_source(rear_nature_root: str | Path, cfg: dict) -> tuple[dict, dict, dict]:
    root = Path(rear_nature_root)
    builder = root / "tools" / "build_rear_tree.py"
    source_path = root / cfg["source_path"]
    if not builder.exists() or not source_path.exists():
        raise ValueError("exact rear Nature source checkout is incomplete")
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "rear-tree-evidence"
        subprocess.run(
            [sys.executable, str(builder), str(output)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        source = json.loads((output / "source.json").read_text(encoding="utf-8"))
        mesh = json.loads((output / "mesh.json").read_text(encoding="utf-8"))
        evidence = json.loads((output / "evidence.json").read_text(encoding="utf-8"))
    return source, mesh, evidence


def _world_mesh(mesh: dict, target: dict) -> tuple[dict, dict]:
    local = _bounds(mesh["vertices"])
    center_x = (local["min"][0] + local["max"][0]) * 0.5
    center_y = (local["min"][1] + local["max"][1]) * 0.5
    position = [float(v) for v in target["position_m"]]
    size = [float(v) for v in target["size_m"]]
    target_ground_z = position[2] - size[2] * 0.5
    tx = position[0] - center_x
    ty = position[1] - center_y
    tz = target_ground_z - float(local["min"][2])
    vertices = [
        [float(v[0]) + tx, float(v[1]) + ty, float(v[2]) + tz]
        for v in mesh["vertices"]
    ]
    world = {
        "schema": mesh.get("schema"),
        "vertices": vertices,
        "triangles": copy.deepcopy(mesh["triangles"]),
        "regions": copy.deepcopy(mesh.get("regions", [])),
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
    rear_nature_root: str | Path,
) -> tuple[dict, dict, dict]:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(manifest_path)
    baseline_cfg = manifest["baseline_environment"]
    replacement_cfg = manifest["replacement"]

    building_manifest = root / baseline_cfg["building_manifest"]
    _, baseline, building_report = building.build_payloads(
        building_manifest,
        base_nature_root,
        compact_nature_root,
        weather_root,
        building_root,
    )
    if building_report["status"] != "PASS_BUILDING_SOURCE_REPLACEMENT_STRUCTURE":
        raise ValueError("accepted Building Environment state must PASS first")

    target_id = replacement_cfg["target_asset_id"]
    targets = [row for row in baseline["items"] if row["asset_id"] == target_id]
    if len(targets) != 1:
        raise ValueError("rear Nature replacement target must exist exactly once")
    target = copy.deepcopy(targets[0])
    if target.get("kind") != "nature-proxy" or target.get("evidence") != "PROXY_ONLY":
        raise ValueError("rear Nature replacement target must remain an explicit nature proxy")

    rear_source, rear_mesh, rear_evidence = _load_rear_source(rear_nature_root, replacement_cfg)
    world_mesh, world_bounds = _world_mesh(rear_mesh, target)
    world_footprint = _footprint_from_bounds(world_bounds)
    reserved_footprint = _footprint_from_item(target)
    target_size = [float(v) for v in target["size_m"]]
    target_position = [float(v) for v in target["position_m"]]
    target_ground_z = target_position[2] - target_size[2] * 0.5
    target_top_z = target_position[2] + target_size[2] * 0.5

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
        if item["asset_id"] == target_id or item["kind"] == "map-surface":
            continue
        if _intersects(world_footprint, _footprint_from_item(item), minimum_gap):
            spacing_conflicts.append(item["asset_id"])
    if _intersects(world_footprint, _mesh_footprint(baseline["sapling"]), minimum_gap):
        spacing_conflicts.append(baseline["sapling"]["asset_id"])
    for source_mesh in baseline.get("additional_source_meshes", []):
        if _intersects(world_footprint, _mesh_footprint(source_mesh), minimum_gap):
            spacing_conflicts.append(source_mesh["asset_id"])

    handoff = rear_source.get("environment_handoff", {})
    observed_rear_head = os.environ.get("AXM_REAR_NATURE_HEAD", replacement_cfg["head"])

    candidate = copy.deepcopy(baseline)
    candidate["schema"] = CANDIDATE_SCENE_SCHEMA
    candidate["study_id"] = manifest["study_id"]
    candidate["receiving_head"] = os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD")
    candidate["items"] = [row for row in candidate["items"] if row["asset_id"] != target_id]
    candidate.setdefault("additional_source_meshes", []).append(
        {
            "asset_id": f"source:nature:{replacement_cfg['expected_study_id']}",
            "kind": "nature-source",
            "truth_state": replacement_cfg["truth_state"],
            "source_repository": replacement_cfg["repository"],
            "source_head": replacement_cfg["head"],
            "source_digest": rear_evidence["source_digest"],
            "mesh_digest": rear_evidence["mesh_digest"],
            "vertices_source_xyz_m": [[float(v) for v in vertex] for vertex in world_mesh["vertices"]],
            "triangles": [[int(v) for v in tri] for tri in world_mesh["triangles"]],
            "proof_render_culling": "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_TOPOLOGY_OR_MATERIAL_ACCEPTANCE",
            "topology_state": replacement_cfg["topology_state"],
        }
    )
    candidate["environment_rear_tree_replacement"] = {
        "target_asset_id": target_id,
        "reserved_proxy_position_m": target_position,
        "reserved_proxy_size_m": target_size,
        "reserved_proxy_rotation_deg": float(target.get("rotation_deg", 0.0)),
        "reserved_proxy_footprint_m": list(reserved_footprint),
        "source_world_bounds_m": world_bounds,
        "source_world_footprint_m": list(world_footprint),
        "source_repository": replacement_cfg["repository"],
        "source_head": replacement_cfg["head"],
        "source_digest": rear_evidence["source_digest"],
        "mesh_digest": rear_evidence["mesh_digest"],
        "placement_policy": replacement_cfg["placement_policy"],
        "relationship": "REAR_NATURE_PROXY_TO_EXACT_SOURCE_ONLY",
        "topology_state": replacement_cfg["topology_state"],
    }
    candidate["truth_boundary"] = manifest["truth_boundary"]
    candidate.pop("scene_digest", None)
    candidate["scene_digest"] = eye.digest(candidate)

    expected_position = replacement_cfg["expected_reserved_position_m"]
    expected_size = replacement_cfg["expected_reserved_size_m"]
    expected_rotation = float(replacement_cfg["expected_reserved_rotation_deg"])
    source_handoff_size = [float(v) for v in handoff.get("proxy_size_m", [])]

    baseline_sources = copy.deepcopy(baseline.get("additional_source_meshes", []))
    building_sources = [row for row in baseline_sources if row["asset_id"] == "source:building:service-pavilion-001"]
    compact_sources = [row for row in baseline_sources if row["asset_id"] == "source:nature:compact-east-tree-neutral-001"]

    checks = {
        "building_baseline_passes_first": building_report["status"] == "PASS_BUILDING_SOURCE_REPLACEMENT_STRUCTURE",
        "seed_matches": int(building_report["preserved_context"]["seed"]) == int(baseline_cfg["seed"]),
        "target_is_exact_rear_nature_proxy": target["asset_id"] == target_id and target["kind"] == "nature-proxy" and target.get("evidence") == "PROXY_ONLY",
        "target_position_matches_source_handoff": _vector_matches(target_position, expected_position) and _vector_matches(handoff.get("proxy_position_m"), expected_position),
        "target_size_matches_source_handoff": _vector_matches(target_size, expected_size) and _vector_matches(source_handoff_size, expected_size),
        "target_rotation_metadata_matches_source_handoff": abs(float(target.get("rotation_deg", 0.0)) - expected_rotation) <= 1e-9 and abs(float(handoff.get("proxy_rotation_deg", 999.0)) - expected_rotation) <= 1e-9,
        "rear_checkout_head_matches": observed_rear_head == replacement_cfg["head"],
        "rear_source_revalidated": rear_evidence.get("status") == "PASS_REAR_SOURCE_ENVELOPE",
        "rear_study_id_matches": rear_source.get("study_id") == replacement_cfg["expected_study_id"],
        "rear_source_digest_matches": rear_evidence.get("source_digest") == replacement_cfg["expected_source_digest"],
        "rear_mesh_digest_matches": rear_evidence.get("mesh_digest") == replacement_cfg["expected_mesh_digest"],
        "rear_vertex_count_matches": int(rear_evidence.get("vertices", -1)) == int(replacement_cfg["expected_vertices"]),
        "rear_triangle_count_matches": int(rear_evidence.get("triangles", -1)) == int(replacement_cfg["expected_triangles"]),
        "source_handoff_target_matches": handoff.get("replacement_target") == target_id,
        "source_handoff_seed_matches": int(handoff.get("seed", -1)) == int(baseline_cfg["seed"]),
        "no_hidden_scale_or_extra_rotation": replacement_cfg["placement_policy"] == PLACEMENT_POLICY and handoff.get("placement_policy") == PLACEMENT_POLICY,
        "source_footprint_inside_reserved_proxy": _inside(world_footprint, reserved_footprint),
        "source_grounded_at_reserved_ground": abs(float(world_bounds["min"][2]) - target_ground_z) <= 1e-9,
        "source_height_inside_reserved_proxy": float(world_bounds["max"][2]) <= target_top_z + 1e-9,
        "readable_path_unblocked_after_replacement": not _intersects(world_footprint, path_box),
        "minimum_spacing_preserved_after_replacement": not spacing_conflicts,
        "unrelated_items_preserved_exactly": _preserved_items_except_target(baseline["items"], candidate["items"], target_id),
        "west_sapling_preserved_exactly": baseline["sapling"] == candidate["sapling"],
        "existing_source_meshes_preserved_exactly": candidate.get("additional_source_meshes", [])[:-1] == baseline_sources,
        "accepted_compact_east_tree_preserved": len(compact_sources) == 1,
        "accepted_building_source_preserved": len(building_sources) == 1,
        "weather_preserved_exactly": baseline["weather_lines"] == candidate["weather_lines"] and baseline["weather_presentation"] == candidate["weather_presentation"],
        "cameras_preserved_exactly": baseline["cameras"] == candidate["cameras"],
        "readable_path_preserved_exactly": baseline["readable_path"] == candidate["readable_path"],
        "one_rear_source_mesh_added": len(candidate.get("additional_source_meshes", [])) == len(baseline_sources) + 1,
        "candidate_scene_digest_differs": candidate["scene_digest"] != baseline["scene_digest"],
        "comparison_policy_isolated": manifest["comparison_policy"].get("isolate_delta") == "REAR_NATURE_PROXY_TO_EXACT_SOURCE_ONLY",
        "building_materials_pr14_not_consumed": manifest["comparison_policy"].get("building_materials_pr14_consumed") is False,
        "geometry_reindex_candidate_not_consumed": manifest["comparison_policy"].get("geometry_reindex_candidate_consumed") is False,
    }

    report = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": manifest["study_id"],
        "status": "PASS_REAR_RIGHT_NATURE_SOURCE_REPLACEMENT_STRUCTURE" if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": candidate["receiving_head"],
        "baseline_scene_digest": baseline["scene_digest"],
        "candidate_scene_digest": candidate["scene_digest"],
        "baseline_exact_environment_head": baseline_cfg["exact_head"],
        "replacement": copy.deepcopy(candidate["environment_rear_tree_replacement"]),
        "rear_source": {
            "study_id": rear_source.get("study_id"),
            "vertices": int(rear_evidence.get("vertices", 0)),
            "triangles": int(rear_evidence.get("triangles", 0)),
            "source_size_m": [float(v) for v in rear_evidence["source_size_m"]],
            "reserved_proxy_size_m": target_size,
            "reserved_margin_m": [float(v) for v in rear_evidence["reserved_margin_m"]],
            "lowest_primary_branch_root_z_m": float(rear_evidence["lowest_primary_branch_root_z_m"]),
            "evidence_status": rear_evidence.get("status"),
        },
        "spacing_conflicts": spacing_conflicts,
        "preserved_context": {
            "seed": building_report["preserved_context"]["seed"],
            "west_sapling_source_digest": building_report["preserved_context"]["west_sapling_source_digest"],
            "weather_source_digest": building_report["preserved_context"]["weather_source_digest"],
            "accepted_compact_east_tree_source_digest": building_report["preserved_context"]["accepted_east_tree_source_digest"],
            "building_pavilion_source_sha256": building_report["replacement"]["pavilion_source_sha256"],
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
    rear_nature_root: str | Path,
    output_dir: str | Path,
) -> dict:
    baseline, candidate, report = build_payloads(
        manifest_path,
        base_nature_root,
        compact_nature_root,
        weather_root,
        building_root,
        rear_nature_root,
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "baseline_scene_runtime.json").write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "candidate_scene_runtime.json").write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "replacement_evidence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_rear_tree_source_replacement_001.json")
    parser.add_argument("--base-nature-root", required=True)
    parser.add_argument("--compact-nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--building-root", required=True)
    parser.add_argument("--rear-nature-root", required=True)
    parser.add_argument("--output", default="evidence/environment_rear_tree_source_replacement_001")
    args = parser.parse_args()
    report = build(
        args.manifest,
        args.base_nature_root,
        args.compact_nature_root,
        args.weather_root,
        args.building_root,
        args.rear_nature_root,
        args.output,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS_REAR_RIGHT_NATURE_SOURCE_REPLACEMENT_STRUCTURE" else 1)


if __name__ == "__main__":
    main()
