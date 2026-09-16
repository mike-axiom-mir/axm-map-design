from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_eye_level as eye
import environment_rear_tree_source_replacement as rear

SCHEMA = "axm.environment-rear-tree-normal-culling-review/v0.1"
EVIDENCE_SCHEMA = "axm.environment-rear-tree-normal-culling-review-evidence/v0.1"
STATUS = "PASS_REAR_TREE_MIGRATED_SOURCE_RECEIVING_CULLING_STRUCTURE_READY"
CULLING_LABEL = "CULL_BACK_REAR_TREE_ONLY_FOR_RECEIVING_REVIEW"


def load_manifest(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unsupported rear-tree normal-culling review schema")
    return data


def _find_source(scene: dict, asset_id: str) -> dict:
    rows = [row for row in scene.get("additional_source_meshes", []) if row.get("asset_id") == asset_id]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one source mesh for {asset_id}")
    return rows[0]


def _find_item(scene: dict, asset_id: str) -> dict:
    rows = [row for row in scene.get("items", []) if row.get("asset_id") == asset_id]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one scene item for {asset_id}")
    return rows[0]


def _triangle_membership_equal(a: list[list[int]], b: list[list[int]]) -> bool:
    if len(a) != len(b):
        return False
    return all(sorted(int(v) for v in left) == sorted(int(v) for v in right) for left, right in zip(a, b))


def _changed_triangle_rows(a: list[list[int]], b: list[list[int]]) -> int:
    if len(a) != len(b):
        return -1
    return sum([int(v) for v in left] != [int(v) for v in right] for left, right in zip(a, b))


def _without_target_source(scene: dict, target_asset_id: str) -> list[dict]:
    return [copy.deepcopy(row) for row in scene.get("additional_source_meshes", []) if row.get("asset_id") != target_asset_id]


def build_payloads(
    manifest_path: str | Path,
    base_nature_root: str | Path,
    compact_nature_root: str | Path,
    weather_root: str | Path,
    building_root: str | Path,
    historical_rear_root: str | Path,
    migrated_rear_root: str | Path,
) -> tuple[dict, dict, dict]:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(manifest_path)
    base_cfg = manifest["base_environment"]
    target_cfg = manifest["target"]
    historical_cfg = manifest["historical_source"]
    migrated_cfg = manifest["migrated_source"]
    culling_cfg = manifest["culling_review"]

    prior_manifest = root / base_cfg["rear_replacement_manifest"]
    proxy_baseline, historical_scene, prior_report = rear.build_payloads(
        prior_manifest,
        base_nature_root,
        compact_nature_root,
        weather_root,
        building_root,
        historical_rear_root,
    )
    if prior_report.get("status") != "PASS_REAR_RIGHT_NATURE_SOURCE_REPLACEMENT_STRUCTURE":
        raise ValueError("exact Environment PR #15 rear-source composition must PASS first")

    target_asset_id = target_cfg["asset_id"]
    historical_row = _find_source(historical_scene, target_asset_id)
    target_proxy = _find_item(proxy_baseline, target_cfg["proxy_asset_id"])
    migrated_source, migrated_mesh, migrated_evidence = rear._load_rear_source(
        migrated_rear_root,
        {"source_path": target_cfg["source_path"]},
    )
    migrated_world_mesh, migrated_world_bounds = rear._world_mesh(migrated_mesh, target_proxy)

    receiving_head = os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD")
    migrated_observed_head = os.environ.get("AXM_MIGRATED_REAR_NATURE_HEAD", migrated_cfg["head"])
    historical_observed_head = os.environ.get("AXM_REAR_NATURE_HEAD", historical_cfg["head"])

    review = {
        "schema": "axm.environment-targeted-source-culling-review/v0.1",
        "target_asset_id": culling_cfg["target_asset_id"],
        "target_cull_mode": culling_cfg["target_cull_mode"],
        "other_source_mesh_cull_mode": culling_cfg["other_source_mesh_cull_mode"],
        "relationship": culling_cfg["relationship"],
        "renderer": culling_cfg["renderer"],
        "cameras": copy.deepcopy(culling_cfg["cameras"]),
        "truth_boundary": "Only the declared rear-tree source receives CULL_BACK in this review. Other source meshes remain CULL_DISABLED so their historical topology cannot confound the isolated rear-tree receiving comparison.",
    }

    historical = copy.deepcopy(historical_scene)
    historical["schema"] = "axm.environment-rear-tree-normal-culling-historical/v0.1"
    historical["study_id"] = manifest["study_id"] + "-historical"
    historical["receiving_head"] = receiving_head
    historical["environment_rear_tree_culling_review"] = copy.deepcopy(review)
    historical_target = _find_source(historical, target_asset_id)
    historical_target["proof_render_culling"] = CULLING_LABEL
    historical.pop("scene_digest", None)
    historical["scene_digest"] = eye.digest(historical)

    candidate = copy.deepcopy(historical)
    candidate["schema"] = "axm.environment-rear-tree-normal-culling-migrated/v0.1"
    candidate["study_id"] = manifest["study_id"] + "-migrated"
    candidate_target = _find_source(candidate, target_asset_id)
    candidate_target["source_repository"] = migrated_cfg["repository"]
    candidate_target["source_head"] = migrated_cfg["head"]
    candidate_target["source_digest"] = migrated_evidence.get("source_digest")
    candidate_target["mesh_digest"] = migrated_evidence.get("mesh_digest")
    candidate_target["vertices_source_xyz_m"] = [[float(v) for v in row] for row in migrated_world_mesh["vertices"]]
    candidate_target["triangles"] = [[int(v) for v in tri] for tri in migrated_world_mesh["triangles"]]
    candidate_target["proof_render_culling"] = CULLING_LABEL
    candidate_target["topology_state"] = migrated_cfg["topology_state"]
    candidate["environment_rear_tree_culling_review"]["candidate_source_head"] = migrated_cfg["head"]
    candidate["environment_rear_tree_culling_review"]["candidate_mesh_digest"] = migrated_cfg["mesh_digest"]
    candidate.pop("scene_digest", None)
    candidate["scene_digest"] = eye.digest(candidate)

    historical_triangles = historical_target["triangles"]
    migrated_triangles = candidate_target["triangles"]
    changed_rows = _changed_triangle_rows(historical_triangles, migrated_triangles)
    comparison_policy = manifest["comparison_policy"]

    checks = {
        "prior_environment_replacement_passes_first": prior_report.get("status") == "PASS_REAR_RIGHT_NATURE_SOURCE_REPLACEMENT_STRUCTURE",
        "base_environment_exact_head_matches": base_cfg["exact_head"] == "03e956475158a59d70cca08b73be23c141e4cb1f",
        "target_asset_matches_review": target_asset_id == culling_cfg["target_asset_id"],
        "historical_checkout_head_matches": historical_observed_head == historical_cfg["head"],
        "historical_source_head_matches": historical_target.get("source_head") == historical_cfg["head"],
        "historical_source_digest_matches": historical_target.get("source_digest") == target_cfg["expected_source_digest"],
        "historical_mesh_digest_matches": historical_target.get("mesh_digest") == historical_cfg["mesh_digest"],
        "migrated_checkout_head_matches": migrated_observed_head == migrated_cfg["head"],
        "migrated_source_revalidated": migrated_evidence.get("status") == "PASS_REAR_SOURCE_ENVELOPE",
        "migrated_study_id_matches": migrated_source.get("study_id") == target_cfg["expected_study_id"],
        "migrated_source_digest_matches": migrated_evidence.get("source_digest") == target_cfg["expected_source_digest"],
        "source_digest_unchanged_across_migration": historical_target.get("source_digest") == candidate_target.get("source_digest"),
        "migrated_mesh_digest_matches": migrated_evidence.get("mesh_digest") == migrated_cfg["mesh_digest"] == candidate_target.get("mesh_digest"),
        "vertex_count_preserved": len(candidate_target["vertices_source_xyz_m"]) == int(target_cfg["expected_vertices"]) == len(historical_target["vertices_source_xyz_m"]),
        "triangle_count_preserved": len(candidate_target["triangles"]) == int(target_cfg["expected_triangles"]) == len(historical_target["triangles"]),
        "world_vertices_preserved_exactly": candidate_target["vertices_source_xyz_m"] == historical_target["vertices_source_xyz_m"],
        "triangle_membership_preserved_exactly": _triangle_membership_equal(historical_triangles, migrated_triangles),
        "expected_triangle_rows_change": changed_rows == int(target_cfg["expected_changed_triangle_rows"]),
        "migrated_world_bounds_match_historical": migrated_world_bounds == rear._bounds(historical_target["vertices_source_xyz_m"]),
        "unrelated_items_preserved_exactly": historical["items"] == candidate["items"],
        "west_sapling_preserved_exactly": historical["sapling"] == candidate["sapling"],
        "other_source_meshes_preserved_exactly": _without_target_source(historical, target_asset_id) == _without_target_source(candidate, target_asset_id),
        "weather_preserved_exactly": historical["weather_lines"] == candidate["weather_lines"] and historical["weather_presentation"] == candidate["weather_presentation"],
        "path_preserved_exactly": historical["readable_path"] == candidate["readable_path"],
        "cameras_preserved_exactly": historical["cameras"] == candidate["cameras"],
        "target_only_backface_culling_declared": culling_cfg["target_cull_mode"] == "BACK" and culling_cfg["other_source_mesh_cull_mode"] == "DISABLED",
        "same_culling_review_in_both_scenes": historical["environment_rear_tree_culling_review"] == {k: v for k, v in candidate["environment_rear_tree_culling_review"].items() if k not in {"candidate_source_head", "candidate_mesh_digest"}},
        "building_material_lane_not_consumed": comparison_policy.get("consume_building_materials_pr14") is False,
        "runtime_lane_not_consumed": comparison_policy.get("consume_runtime_pr17") is False,
        "vfx_dense_lane_not_consumed": comparison_policy.get("consume_vfx_pr16") is False,
        "rear_vertices_not_authorized_to_change": comparison_policy.get("change_rear_vertices") is False,
        "rear_triangle_membership_not_authorized_to_change": comparison_policy.get("change_rear_triangle_membership") is False,
        "scene_digest_changes_with_explicit_source_migration": historical["scene_digest"] != candidate["scene_digest"],
    }

    report = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": manifest["study_id"],
        "status": STATUS if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": receiving_head,
        "base_environment_head": base_cfg["exact_head"],
        "target_asset_id": target_asset_id,
        "historical": {
            "source_head": historical_cfg["head"],
            "source_digest": historical_target.get("source_digest"),
            "mesh_digest": historical_target.get("mesh_digest"),
            "scene_digest": historical["scene_digest"],
        },
        "migrated": {
            "source_head": migrated_cfg["head"],
            "source_digest": candidate_target.get("source_digest"),
            "mesh_digest": candidate_target.get("mesh_digest"),
            "scene_digest": candidate["scene_digest"],
            "source_evidence_status": migrated_evidence.get("status"),
        },
        "topology_delta": {
            "changed_triangle_rows": changed_rows,
            "vertices_changed": candidate_target["vertices_source_xyz_m"] != historical_target["vertices_source_xyz_m"],
            "triangle_membership_changed": not _triangle_membership_equal(historical_triangles, migrated_triangles),
        },
        "culling_review": copy.deepcopy(review),
        "preserved_context": {
            "seed": prior_report["preserved_context"]["seed"],
            "building_pavilion_source_sha256": prior_report["preserved_context"]["building_pavilion_source_sha256"],
            "west_sapling_source_digest": prior_report["preserved_context"]["west_sapling_source_digest"],
            "accepted_compact_east_tree_source_digest": prior_report["preserved_context"]["accepted_compact_east_tree_source_digest"],
            "weather_source_digest": prior_report["preserved_context"]["weather_source_digest"],
            "camera_names": sorted(historical["cameras"]),
        },
        "truth_boundary": manifest["truth_boundary"],
    }
    return historical, candidate, report


def build(
    manifest_path: str | Path,
    base_nature_root: str | Path,
    compact_nature_root: str | Path,
    weather_root: str | Path,
    building_root: str | Path,
    historical_rear_root: str | Path,
    migrated_rear_root: str | Path,
    output_dir: str | Path,
) -> dict:
    historical, candidate, report = build_payloads(
        manifest_path,
        base_nature_root,
        compact_nature_root,
        weather_root,
        building_root,
        historical_rear_root,
        migrated_rear_root,
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "historical_scene_runtime.json").write_text(json.dumps(historical, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "migrated_scene_runtime.json").write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "migration_receiving_evidence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_rear_tree_normal_culling_001.json")
    parser.add_argument("--base-nature-root", required=True)
    parser.add_argument("--compact-nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--building-root", required=True)
    parser.add_argument("--historical-rear-root", required=True)
    parser.add_argument("--migrated-rear-root", required=True)
    parser.add_argument("--output", default="evidence/environment_rear_tree_normal_culling_001")
    args = parser.parse_args()
    report = build(
        args.manifest,
        args.base_nature_root,
        args.compact_nature_root,
        args.weather_root,
        args.building_root,
        args.historical_rear_root,
        args.migrated_rear_root,
        args.output,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == STATUS else 1)


if __name__ == "__main__":
    main()
