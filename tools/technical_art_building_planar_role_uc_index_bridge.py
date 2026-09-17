#!/usr/bin/env python3
"""Verify the exact Building post-normal per-surface index path against UC.

Technical Art owns only this cross-repo comparison. Building keeps representation
semantics, Runtime keeps cost evidence, Art/QA keep appearance acceptance, and UC
remains an observer rather than a mesh mutator.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from axm_uc.indexed_surface_eligibility import (
    CROSS_SOURCE_TUPLE_POLICY,
    INPUT_SCHEMA,
    SOURCE_LINEAGE_POLICY,
    observe_indexed_surface_eligibility,
)

SCHEMA = "axm.technical-art-building-planar-role-uc-index-bridge/v0.1"
BUNDLE_SCHEMA = "axm.technical-art-building-planar-role-index-bundle/v0.1"
RUNTIME_SCHEMA = "axm.runtime-building-planar-role-surface-index-budget/v0.1"
RUNTIME_HEAD = "8d5860c308c244d314ede5b79021e46f35c4040d"
HARD_SURFACE_HEAD = "93f22e4eeb9bb32516d4b11f8d8bcf47d9792910"
MATERIALS_HEAD = "4179aa1401f5a9114399e2f998c96809d4b8ed2e"
REPRESENTATION_ID = "boundary-only-planar-role-rectangle-render-001"
EXPECTED_PARTITIONS = [
    "frame_galvanized",
    "infill_coating",
    "roof_membrane",
    "slab_mineral",
    "utility_panel_ochre",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_number(value):
    if isinstance(value, float) and value == 0.0:
        return 0.0
    return value


def normalize_rows(rows):
    return [[normalize_number(value) for value in row] for row in rows]


def candidate_rows(before: dict, report: dict) -> tuple[list[list[float]], list[list[float]]]:
    candidate_map = report["candidate"]["render_vertex_to_candidate"]
    candidate_count = report["candidate"]["vertex_count"]
    positions = [None] * candidate_count
    normals = [None] * candidate_count
    source_positions = normalize_rows(before["positions"])
    source_normals = normalize_rows(before["normals"])
    for render_index, candidate_index in enumerate(candidate_map):
        if positions[candidate_index] is None:
            positions[candidate_index] = source_positions[render_index]
            normals[candidate_index] = source_normals[render_index]
    if any(row is None for row in positions) or any(row is None for row in normals):
        raise ValueError("UC candidate map left an unreachable candidate vertex")
    return positions, normals


def build_spec(partition: str, before: dict) -> dict:
    count = int(before["vertex_count"])
    indices = [int(value) for value in before["triangle_corner_indices"]]
    if indices != list(range(count)):
        raise ValueError(f"{partition}: expected exact unindexed triangle-corner domain")
    return {
        "schema": INPUT_SCHEMA,
        "source_identity": f"{REPRESENTATION_ID}:{partition}:godot-triangle-corners",
        "surface_identity": f"{REPRESENTATION_ID}:{partition}",
        "candidate_identity_policy": CROSS_SOURCE_TUPLE_POLICY,
        "source": {"vertex_count": count, "indices": indices},
        "render": {
            "vertex_count": count,
            "indices": indices,
            "protected_split_ids": [f"partition:{partition}"] * count,
            "channels": {
                "POSITION": normalize_rows(before["positions"]),
                "NORMAL": normalize_rows(before["normals"]),
            },
        },
    }


def verify(bundle_path: Path, runtime_report_path: Path, output: Path, technical_art_head: str, uc_head: str, uc_observer_path: Path) -> dict:
    bundle = load_json(bundle_path)
    runtime = load_json(runtime_report_path)

    if bundle.get("schema") != BUNDLE_SCHEMA:
        raise ValueError("Technical Art Godot bundle schema drift")
    if bundle.get("runtime_parent_head") != RUNTIME_HEAD:
        raise ValueError("Technical Art bundle Runtime parent drift")
    if bundle.get("building_hard_surface_head") != HARD_SURFACE_HEAD:
        raise ValueError("Technical Art bundle Hard-Surface owner drift")
    if bundle.get("building_materials_head") != MATERIALS_HEAD:
        raise ValueError("Technical Art bundle Materials owner drift")
    if bundle.get("representation_id") != REPRESENTATION_ID:
        raise ValueError("Technical Art bundle representation drift")
    if bundle.get("material_partitions") != EXPECTED_PARTITIONS:
        raise ValueError("Technical Art bundle partition order drift")

    before_bundle = bundle["before"]
    after_bundle = bundle["after"]
    if before_bundle.get("surface_count") != 5 or before_bundle.get("total_vertices") != 1008 or before_bundle.get("total_storage_indices") != 0 or before_bundle.get("total_triangles") != 336:
        raise ValueError(f"unexpected exact Godot before bundle: {before_bundle}")
    if after_bundle.get("surface_count") != 5 or after_bundle.get("total_vertices") != 312 or after_bundle.get("total_storage_indices") != 1008 or after_bundle.get("total_triangles") != 336:
        raise ValueError(f"unexpected exact Godot after bundle: {after_bundle}")

    if runtime.get("schema") != RUNTIME_SCHEMA or runtime.get("exact_runtime_head") != RUNTIME_HEAD:
        raise ValueError("retained Runtime report identity drift")
    if runtime.get("representation_id") != REPRESENTATION_ID:
        raise ValueError("retained Runtime representation drift")
    runtime_representation = runtime["building_representation"]
    if runtime_representation.get("surface_count") != 5 or runtime_representation.get("triangle_count") != 336:
        raise ValueError("retained Runtime surface/triangle identity drift")
    if runtime_representation["before"] != {
        key: runtime_representation["before"][key]
        for key in runtime_representation["before"]
    }:
        raise ValueError("unreachable Runtime before receipt")
    if int(runtime_representation["before"]["total_vertices"]) != 1008 or int(runtime_representation["after"]["total_vertices"]) != 312:
        raise ValueError("retained Runtime before/after vertex count drift")
    if int(runtime_representation["after"]["total_indices"]) != 1008:
        raise ValueError("retained Runtime post-index count drift")

    runtime_before_surfaces = runtime_representation["before"]["surfaces"]
    runtime_after_surfaces = runtime_representation["after"]["surfaces"]
    if len(runtime_before_surfaces) != 5 or len(runtime_after_surfaces) != 5:
        raise ValueError("retained Runtime surface receipt count drift")

    surface_reports = []
    total_candidate_vertices = 0
    total_candidate_indices = 0
    total_cross_source_groups = 0

    for surface_index, partition in enumerate(EXPECTED_PARTITIONS):
        before = before_bundle["surfaces"][surface_index]
        after = after_bundle["surfaces"][surface_index]
        runtime_before = runtime_before_surfaces[surface_index]
        runtime_after = runtime_after_surfaces[surface_index]

        if before.get("partition_identity") != partition or after.get("partition_identity") != partition:
            raise ValueError(f"{partition}: Godot partition identity drift")
        if runtime_before.get("material_id") != partition or runtime_after.get("material_id") != partition:
            raise ValueError(f"{partition}: retained Runtime partition identity drift")
        if int(before["vertex_count"]) != int(runtime_before["vertex_count"]):
            raise ValueError(f"{partition}: exact before vertex count differs from retained Runtime")
        if int(after["vertex_count"]) != int(runtime_after["vertex_count"]):
            raise ValueError(f"{partition}: exact after vertex count differs from retained Runtime")
        if int(after["storage_index_count"]) != int(runtime_after["index_count"]):
            raise ValueError(f"{partition}: exact after index count differs from retained Runtime")
        if int(after["triangle_count"]) != int(runtime_after["primitive_count"]):
            raise ValueError(f"{partition}: exact after triangle count differs from retained Runtime")

        spec = build_spec(partition, before)
        report = observe_indexed_surface_eligibility(spec)
        if report["eligibility_state"] != "POST_ATTRIBUTE_TUPLE_DEDUP_CANDIDATE":
            raise ValueError(f"{partition}: UC did not produce tuple dedup candidate: {report['eligibility_state']}")
        if report["render_domain_state"] != "RENDER_DOMAIN_CROSS_SOURCE_DEDUP_CANDIDATE":
            raise ValueError(f"{partition}: UC did not expose cross-source candidate state")
        if int(report["candidate"]["vertex_count"]) != int(after["vertex_count"]):
            raise ValueError(f"{partition}: UC candidate vertex count differs from exact Godot indexed surface")
        if report["candidate"]["indices"] != [int(value) for value in after["storage_indices"]]:
            raise ValueError(f"{partition}: UC candidate index stream differs from exact Godot SurfaceTool.index() output")

        expected_positions, expected_normals = candidate_rows(before, report)
        if expected_positions != normalize_rows(after["positions"]):
            raise ValueError(f"{partition}: UC candidate POSITION order differs from exact Godot indexed surface")
        if expected_normals != normalize_rows(after["normals"]):
            raise ValueError(f"{partition}: UC candidate NORMAL order differs from exact Godot indexed surface")

        source_preserving = copy.deepcopy(spec)
        source_preserving.pop("candidate_identity_policy")
        conservative = observe_indexed_surface_eligibility(source_preserving)
        if conservative["candidate_identity_policy"] != SOURCE_LINEAGE_POLICY:
            raise ValueError(f"{partition}: conservative policy identity drift")
        if int(conservative["candidate"]["vertex_count"]) != int(before["vertex_count"]):
            raise ValueError(f"{partition}: conservative source-lineage mode unexpectedly merged source corners")

        missing_split = copy.deepcopy(spec)
        del missing_split["render"]["protected_split_ids"]
        held = observe_indexed_surface_eligibility(missing_split)
        if held["eligibility_state"] != "HOLD_CROSS_SOURCE_SPLIT_DECLARATION_REQUIRED" or held["candidate"] is not None:
            raise ValueError(f"{partition}: UC cross-source mode did not fail closed without split declaration")

        total_candidate_vertices += int(report["candidate"]["vertex_count"])
        total_candidate_indices += int(report["candidate"]["index_count"])
        total_cross_source_groups += int(report["cross_source_observation"]["candidate_groups_spanning_multiple_source_vertices"])
        write_json(output / f"surface-{surface_index:02d}-{partition}.input.json", spec)
        write_json(output / f"surface-{surface_index:02d}-{partition}.report.json", report)
        surface_reports.append({
            "surface_index": surface_index,
            "partition_identity": partition,
            "before_vertices": int(before["vertex_count"]),
            "after_vertices": int(after["vertex_count"]),
            "triangles": int(after["triangle_count"]),
            "indices": int(after["storage_index_count"]),
            "uc_candidate_vertex_count": int(report["candidate"]["vertex_count"]),
            "uc_index_stream_exact_match": True,
            "uc_position_order_exact_match": True,
            "uc_normal_order_exact_match": True,
            "cross_source_candidate_groups": int(report["cross_source_observation"]["candidate_groups_spanning_multiple_source_vertices"]),
            "conservative_source_lineage_vertex_count": int(conservative["candidate"]["vertex_count"]),
            "missing_split_control": held["eligibility_state"],
        })

    if total_candidate_vertices != 312 or total_candidate_indices != 1008:
        raise ValueError("aggregate UC candidate counts do not reproduce exact Godot indexed receiver")

    receipt = {
        "schema": SCHEMA,
        "result": "PASS_BUILDING_EXACT_GODOT_POST_NORMAL_PER_SURFACE_INDEX_MATCHES_UC_CROSS_SOURCE_TUPLE_CANDIDATE",
        "technical_art_head": technical_art_head,
        "runtime_parent_head": RUNTIME_HEAD,
        "building_hard_surface_head": HARD_SURFACE_HEAD,
        "building_materials_head": MATERIALS_HEAD,
        "representation_id": REPRESENTATION_ID,
        "uc_head": uc_head,
        "uc_observer_sha256": sha256_file(uc_observer_path),
        "exact_godot_receiver": {
            "surface_count": 5,
            "triangle_count": 336,
            "before_vertices": 1008,
            "after_vertices": 312,
            "after_indices": 1008,
        },
        "uc_candidate": {
            "candidate_identity_policy": CROSS_SOURCE_TUPLE_POLICY,
            "surface_count": 5,
            "triangle_count": 336,
            "candidate_vertices": total_candidate_vertices,
            "candidate_indices": total_candidate_indices,
            "cross_source_candidate_groups": total_cross_source_groups,
            "exact_index_stream_match_all_surfaces": True,
            "exact_position_order_match_all_surfaces": True,
            "exact_normal_order_match_all_surfaces": True,
        },
        "surfaces": surface_reports,
        "negative_controls": {
            "default_source_lineage_mode_preserves_all_1008_triangle_corners": sum(row["conservative_source_lineage_vertex_count"] for row in surface_reports) == 1008,
            "cross_source_mode_without_explicit_split_declaration": "HOLD_CROSS_SOURCE_SPLIT_DECLARATION_REQUIRED",
        },
        "retained_runtime_result": runtime["state"],
        "retained_runtime_visual_tradeoff": runtime["visuals"]["tradeoff"],
        "truth_boundary": {
            "uc_surface_mutation": False,
            "building_semantics_centralized_in_uc": False,
            "material_partitions_crossed": False,
            "runtime_savings_remeasured_here": False,
            "visual_acceptance_claimed_here": False,
            "environment_adoption_authorized": False,
            "target_device_acceptance": False,
            "arbitrary_mesh_indexing_safety": False,
            "canon_or_production_readiness": False,
        },
    }
    write_json(output / "receipt.json", receipt)
    write_json(output / "godot-index-bundle.json", bundle)
    write_json(output / "retained-runtime-report.json", runtime)
    manifest = {
        path.name: sha256_file(path)
        for path in sorted(output.iterdir())
        if path.is_file()
    }
    write_json(output / "sha256-manifest.json", manifest)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--runtime-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--technical-art-head", required=True)
    parser.add_argument("--uc-head", required=True)
    parser.add_argument("--uc-observer", type=Path, required=True)
    args = parser.parse_args()
    receipt = verify(
        args.bundle,
        args.runtime_report,
        args.output,
        args.technical_art_head,
        args.uc_head,
        args.uc_observer,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
