from __future__ import annotations

import argparse
import copy
import importlib
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_eye_level as eye
import environment_real_slice as integration

SCHEMA = "axm.environment-east-tree-replacement/v0.1"
EVIDENCE_SCHEMA = "axm.environment-east-tree-replacement-evidence/v0.1"
CANDIDATE_SCENE_SCHEMA = "axm.environment-east-tree-replacement-proof/v0.1"
PLACEMENT_POLICY = "PRESERVE_TARGET_CENTER_XY__GROUND_SOURCE_MIN_Z__NO_FORM_SCALE__NO_EXTRA_ROTATION"


def load_manifest(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unsupported east-tree replacement schema")
    return data


def _bounds(vertices: list[list[float]]) -> dict:
    if not vertices:
        raise ValueError("mesh has no vertices")
    mins = [min(float(v[i]) for v in vertices) for i in range(3)]
    maxs = [max(float(v[i]) for v in vertices) for i in range(3)]
    return {"min": mins, "max": maxs, "size": [maxs[i] - mins[i] for i in range(3)]}


def _world_mesh(mesh: dict, target: dict) -> tuple[dict, dict]:
    local = _bounds(mesh["vertices"])
    center_x = (local["min"][0] + local["max"][0]) * 0.5
    center_y = (local["min"][1] + local["max"][1]) * 0.5
    position = [float(value) for value in target["position"]]
    tx = position[0] - center_x
    ty = position[1] - center_y
    tz = -local["min"][2]
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


def _footprint_from_bounds(bounds: dict) -> tuple[float, float, float, float]:
    return (
        float(bounds["min"][0]),
        float(bounds["max"][0]),
        float(bounds["min"][1]),
        float(bounds["max"][1]),
    )


def _footprint_from_item(item: dict) -> tuple[float, float, float, float]:
    x, y = float(item["position"][0]), float(item["position"][1])
    sx, sy = float(item["size"][0]), float(item["size"][1])
    return (x - sx * 0.5, x + sx * 0.5, y - sy * 0.5, y + sy * 0.5)


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


def _payload_item(item: dict) -> dict:
    return {
        "asset_id": item["asset_id"],
        "kind": item["kind"],
        "evidence": item.get("evidence"),
        "position_m": [float(value) for value in item["position"]],
        "size_m": [float(value) for value in item["size"]],
        "rotation_deg": float(item.get("rotation_deg", 0.0)),
    }


def _preserved_items_except_target(baseline_items: list[dict], candidate_items: list[dict], target_id: str) -> bool:
    baseline = {row["asset_id"]: row for row in baseline_items if row["asset_id"] != target_id}
    candidate = {row["asset_id"]: row for row in candidate_items}
    return baseline == candidate and target_id not in candidate


def _load_compact_source(nature_root: str | Path, cfg: dict):
    nature_root = Path(nature_root)
    source_root = str(nature_root / "src")
    if source_root not in sys.path:
        sys.path.insert(0, source_root)
    organic = importlib.import_module("axm_nature_design.organic_form")
    compact = importlib.import_module("axm_nature_design.compact_tree_study")
    source = organic.load_source(nature_root / cfg["source_path"])
    evidence = compact.evaluate(source)
    mesh = organic.build_mesh(source)
    return organic, source, evidence, mesh


def build_payloads(
    manifest_path: str | Path,
    base_nature_root: str | Path,
    compact_nature_root: str | Path,
    weather_root: str | Path,
) -> tuple[dict, dict, dict]:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(manifest_path)
    baseline_cfg = manifest["baseline_environment"]
    replacement_cfg = manifest["replacement"]

    baseline_manifest_path = root / baseline_cfg["base_manifest"]
    baseline_manifest = integration.load_manifest(baseline_manifest_path)
    baseline_report, variant, _, _, _, _, _ = integration.evaluate_integration(
        root, baseline_manifest, base_nature_root, weather_root
    )
    if baseline_report["status"] != "PASS":
        raise ValueError("existing Environment source integration must PASS first")

    baseline = eye.build_scene_payload(baseline_manifest_path, base_nature_root, weather_root)
    baseline_eye = eye.evaluate(baseline)
    if baseline_eye["status"] != "PASS":
        raise ValueError("existing fixed-camera Environment payload must PASS first")

    target_id = replacement_cfg["target_asset_id"]
    targets = [item for item in variant["items"] if item["asset_id"] == target_id]
    if len(targets) != 1:
        raise ValueError("east-tree replacement target must exist exactly once")
    target = copy.deepcopy(targets[0])
    if target.get("kind") != "nature-proxy" or target.get("evidence") != "PROXY_ONLY":
        raise ValueError("east-tree replacement target must remain an explicit nature proxy")

    organic, compact_source, compact_evidence, compact_mesh = _load_compact_source(
        compact_nature_root, replacement_cfg
    )
    world_mesh, world_bounds = _world_mesh(compact_mesh, target)
    world_footprint = _footprint_from_bounds(world_bounds)
    reserved_footprint = _footprint_from_item(target)

    path = variant["readable_path"]
    path_box = (
        float(path["x_min"]),
        float(path["x_max"]),
        float(path["y_min"]),
        float(path["y_max"]),
    )
    clearance = float(variant["minimum_gap_m"])

    remaining_conflicts = []
    for item in variant["items"]:
        if item["kind"] == "map-surface" or item["asset_id"] in {
            target_id,
            baseline_manifest["nature_replacement"]["replacement_target"],
        }:
            continue
        if _intersects(world_footprint, _footprint_from_item(item), clearance):
            remaining_conflicts.append(item["asset_id"])

    west_footprint = tuple(float(value) for value in baseline_report["replacement"]["real_world_footprint_m"])
    if _intersects(world_footprint, west_footprint, clearance):
        remaining_conflicts.append("source:nature:sapling-neutral-001")

    expected_size = [float(value) for value in replacement_cfg["expected_proxy_size_m"]]
    target_size = [float(value) for value in target["size"]]
    target_top = float(target["position"][2]) + target_size[2] * 0.5
    handoff = compact_source.get("environment_handoff", {})

    candidate = copy.deepcopy(baseline)
    candidate["schema"] = CANDIDATE_SCENE_SCHEMA
    candidate["study_id"] = manifest["study_id"]
    candidate["receiving_head"] = os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD")
    candidate["items"] = [
        row for row in candidate["items"] if row["asset_id"] != target_id
    ]
    candidate["additional_source_meshes"] = [
        {
            "asset_id": f"source:nature:{replacement_cfg['expected_study_id']}",
            "kind": "nature-source",
            "truth_state": replacement_cfg["truth_state"],
            "source_repository": replacement_cfg["repository"],
            "source_head": replacement_cfg["head"],
            "source_digest": compact_evidence["source_digest"],
            "mesh_digest": compact_evidence["mesh_digest"],
            "vertices_source_xyz_m": [[float(value) for value in vertex] for vertex in world_mesh["vertices"]],
            "triangles": [[int(value) for value in tri] for tri in world_mesh["triangles"]],
            "proof_render_culling": "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_MATERIAL_ACCEPTANCE",
        }
    ]
    candidate["environment_replacement"] = {
        "target_asset_id": target_id,
        "reserved_proxy_position_m": [float(value) for value in target["position"]],
        "reserved_proxy_size_m": target_size,
        "reserved_proxy_rotation_deg": float(target.get("rotation_deg", 0.0)),
        "reserved_proxy_footprint_m": list(reserved_footprint),
        "source_world_bounds_m": world_bounds,
        "source_world_footprint_m": list(world_footprint),
        "source_repository": replacement_cfg["repository"],
        "source_head": replacement_cfg["head"],
        "source_digest": compact_evidence["source_digest"],
        "mesh_digest": compact_evidence["mesh_digest"],
        "placement_policy": replacement_cfg["placement_policy"],
        "relationship": "PROXY_TO_EXACT_SOURCE_ONLY",
    }
    candidate["truth_boundary"] = manifest["truth_boundary"]
    candidate.pop("scene_digest", None)
    candidate["scene_digest"] = eye.digest(candidate)

    checks = {
        "baseline_source_integration_pass": baseline_report["status"] == "PASS",
        "baseline_fixed_camera_payload_pass": baseline_eye["status"] == "PASS",
        "baseline_seed_matches": int(baseline_report["base_variant"]["seed"]) == int(baseline_cfg["seed"]),
        "target_is_exact_remaining_nature_proxy": target["asset_id"] == target_id and target["kind"] == "nature-proxy" and target.get("evidence") == "PROXY_ONLY",
        "target_reserved_size_matches": all(abs(target_size[i] - expected_size[i]) <= 1e-12 for i in range(3)),
        "compact_source_revalidated": compact_evidence.get("status") == "PASS_COMPACT_SOURCE_ENVELOPE",
        "compact_study_id_matches": compact_source.get("study_id") == replacement_cfg["expected_study_id"],
        "compact_source_digest_matches": compact_evidence.get("source_digest") == replacement_cfg["expected_source_digest"],
        "compact_mesh_digest_matches": compact_evidence.get("mesh_digest") == replacement_cfg["expected_mesh_digest"],
        "compact_vertex_count_matches": int(compact_evidence.get("vertices", -1)) == int(replacement_cfg["expected_vertices"]),
        "compact_triangle_count_matches": int(compact_evidence.get("triangles", -1)) == int(replacement_cfg["expected_triangles"]),
        "source_handoff_target_matches": handoff.get("replacement_target") == target_id,
        "source_handoff_predecessor_head_matches": handoff.get("head") == baseline_cfg["exact_predecessor_head"],
        "no_hidden_scale_or_extra_rotation": replacement_cfg.get("placement_policy") == PLACEMENT_POLICY and handoff.get("placement_policy") == PLACEMENT_POLICY,
        "source_footprint_inside_reserved_proxy": _inside(world_footprint, reserved_footprint),
        "source_grounded_at_zero": abs(float(world_bounds["min"][2])) <= 1e-9,
        "source_height_inside_reserved_proxy": float(world_bounds["max"][2]) <= target_top + 1e-9,
        "readable_path_unblocked_after_replacement": not _intersects(world_footprint, path_box),
        "minimum_spacing_preserved_after_replacement": not remaining_conflicts,
        "unrelated_items_preserved_exactly": _preserved_items_except_target(baseline["items"], candidate["items"], target_id),
        "west_sapling_preserved_exactly": baseline["sapling"] == candidate["sapling"],
        "weather_preserved_exactly": baseline["weather_lines"] == candidate["weather_lines"] and baseline["weather_presentation"] == candidate["weather_presentation"],
        "cameras_preserved_exactly": baseline["cameras"] == candidate["cameras"],
        "readable_path_preserved_exactly": baseline["readable_path"] == candidate["readable_path"],
        "one_source_mesh_replaces_target": len(candidate["additional_source_meshes"]) == 1 and target_id not in {row["asset_id"] for row in candidate["items"]},
        "candidate_scene_digest_differs": candidate["scene_digest"] != baseline["scene_digest"],
        "comparison_policy_isolated": manifest["comparison_policy"].get("isolate_delta") == "PROXY_TO_EXACT_SOURCE_ONLY",
    }

    report = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": manifest["study_id"],
        "status": "PASS_EAST_FOREGROUND_SOURCE_REPLACEMENT_STRUCTURE" if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": candidate["receiving_head"],
        "baseline_scene_digest": baseline["scene_digest"],
        "candidate_scene_digest": candidate["scene_digest"],
        "replacement": copy.deepcopy(candidate["environment_replacement"]),
        "compact_source": {
            "study_id": compact_source.get("study_id"),
            "vertices": int(compact_evidence.get("vertices", 0)),
            "triangles": int(compact_evidence.get("triangles", 0)),
            "source_size_m": [float(value) for value in compact_evidence["source_size_m"]],
            "reserved_margin_m": [float(value) for value in compact_evidence["reserved_margin_m"]],
            "evidence_status": compact_evidence.get("status"),
        },
        "spacing_conflicts": remaining_conflicts,
        "preserved_context": {
            "west_sapling_source_digest": baseline["source_integration"]["replacement"]["source_digest"],
            "weather_source_digest": baseline["source_integration"]["weather_overlay"]["source_digest"],
            "camera_names": sorted(baseline["cameras"]),
            "seed": baseline_report["base_variant"]["seed"],
        },
        "truth_boundary": manifest["truth_boundary"],
    }
    return baseline, candidate, report


def build(
    manifest_path: str | Path,
    base_nature_root: str | Path,
    compact_nature_root: str | Path,
    weather_root: str | Path,
    output_dir: str | Path,
) -> dict:
    baseline, candidate, report = build_payloads(
        manifest_path, base_nature_root, compact_nature_root, weather_root
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "baseline_scene_runtime.json").write_text(
        json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "candidate_scene_runtime.json").write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "replacement_evidence.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_east_tree_replacement_001.json")
    parser.add_argument("--base-nature-root", required=True)
    parser.add_argument("--compact-nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--output", default="evidence/environment_east_tree_replacement_001")
    args = parser.parse_args()
    report = build(
        args.manifest,
        args.base_nature_root,
        args.compact_nature_root,
        args.weather_root,
        args.output,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS_EAST_FOREGROUND_SOURCE_REPLACEMENT_STRUCTURE" else 1)


if __name__ == "__main__":
    main()
