from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

SCHEMA = "axm.technical-art-building-source-map-rebind-evidence/v0.1"
STATUS = "PASS_MAP_BUILDING_SOURCE_OWNED_TOPOLOGY_REBIND_STRUCTURE"
TRANSFER_STATUS = "PASS_RECEIVING_SCENE_BUILDING_MATERIAL_TRANSFER_STRUCTURE"

HISTORICAL_SOURCE_HEAD = "4faa769b406bf3ad0ba9489a77141c27f122ce51"
HISTORICAL_MATERIAL_HEAD = "b08f683f1c3f75c474fb347e1d1990c1c4426a33"
HISTORICAL_PAVILION_SHA256 = "852038d2288ead9a0ee271e09f1a7f7207ec8fd74668e0c52e739e9a224f87d7"
SUCCESSOR_SOURCE_HEAD = "57f66b1245812f0c3d402232a046b86c0b5c72d8"
SUCCESSOR_MATERIAL_HEAD = "ca92ef79d65a2ba287b7a76464bedceb6a31a1b6"
SUCCESSOR_PAVILION_SHA256 = "5f89ec4109d48f452f9e887ad5ca5449e1d0f6d6ee4b1896be6f25bc0a80736a"
PANEL_SHA256 = "df59fa135abc89f8c85317db1d6b9ce3d03920efc91271de61bfb6289a24c253"
MATERIAL_PROFILE_SHA256 = "e8dd0c33b9b2aea108194af57a8fe8de39c7e67bb86109af6dbf3895f22c010b"
EXPECTED_ROLES = [
    "frame_galvanized",
    "infill_coating",
    "roof_membrane",
    "slab_mineral",
    "utility_panel_ochre",
]


def _digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _surface_rows(scene: dict) -> list[dict]:
    receiving = scene.get("building_material_receiving")
    if not isinstance(receiving, dict):
        raise ValueError("candidate scene is missing Building material receiving payload")
    rows = receiving.get("surfaces")
    if not isinstance(rows, list) or [row.get("surface_role") for row in rows] != EXPECTED_ROLES:
        raise ValueError("Building surface-role order drift")
    return rows


def _triangle_partition(scene: dict) -> list[dict]:
    return [
        {
            "surface_role": row["surface_role"],
            "triangles": copy.deepcopy(row.get("triangles", [])),
        }
        for row in _surface_rows(scene)
    ]


def _materials(scene: dict) -> list[dict]:
    return [
        {
            "surface_role": row["surface_role"],
            "material_id": row.get("material_id"),
            "material": copy.deepcopy(row.get("material")),
        }
        for row in _surface_rows(scene)
    ]


def _strip_building_receiving(scene: dict) -> dict:
    value = copy.deepcopy(scene)
    for key in (
        "scene_digest",
        "receiving_head",
        "study_id",
        "truth_boundary",
        "building_material_receiving",
        "environment_building_replacement",
    ):
        value.pop(key, None)
    return value


def _vertices(scene: dict) -> list[list[float]]:
    return copy.deepcopy(scene["building_material_receiving"]["vertices_source_xyz_m"])


def _triangle_count(scene: dict) -> int:
    return sum(len(row.get("triangles", [])) for row in _surface_rows(scene))


def build_report(
    historical_report: dict,
    historical_candidate: dict,
    successor_report: dict,
    successor_candidate: dict,
    receiving_head: str,
) -> dict:
    if historical_report.get("status") != TRANSFER_STATUS or not all(historical_report.get("checks", {}).values()):
        raise ValueError("historical PR14 receiving evidence must PASS before successor comparison")
    if successor_report.get("status") != TRANSFER_STATUS or not all(successor_report.get("checks", {}).values()):
        raise ValueError("successor receiving evidence must PASS before Technical Art comparison")

    historical_partition = _triangle_partition(historical_candidate)
    successor_partition = _triangle_partition(successor_candidate)
    historical_materials = _materials(historical_candidate)
    successor_materials = _materials(successor_candidate)

    checks = {
        "historical_source_identity_exact": (
            historical_report.get("building_source_head") == HISTORICAL_SOURCE_HEAD
            and historical_report.get("pavilion_source_sha256") == HISTORICAL_PAVILION_SHA256
        ),
        "historical_material_identity_exact": historical_report.get("building_material_head") == HISTORICAL_MATERIAL_HEAD,
        "successor_source_identity_exact": (
            successor_report.get("building_source_head") == SUCCESSOR_SOURCE_HEAD
            and successor_report.get("pavilion_source_sha256") == SUCCESSOR_PAVILION_SHA256
        ),
        "successor_material_identity_exact": successor_report.get("building_material_head") == SUCCESSOR_MATERIAL_HEAD,
        "panel_source_identity_preserved": (
            historical_report.get("panel_source_sha256") == PANEL_SHA256
            and successor_report.get("panel_source_sha256") == PANEL_SHA256
        ),
        "material_profile_identity_preserved": (
            historical_report.get("material_profile_sha256") == MATERIAL_PROFILE_SHA256
            and successor_report.get("material_profile_sha256") == MATERIAL_PROFILE_SHA256
        ),
        "historical_builder_has_no_extension_outputs": historical_report.get("producer_extension_output_count") == 0,
        "successor_builder_has_one_additive_extension_output": successor_report.get("producer_extension_output_count") == 1,
        "five_surface_material_values_preserved": historical_materials == successor_materials,
        "world_vertices_preserved_exactly": _vertices(historical_candidate) == _vertices(successor_candidate),
        "world_vertex_budget_preserved": len(_vertices(successor_candidate)) == 152,
        "world_triangle_budget_preserved": _triangle_count(historical_candidate) == _triangle_count(successor_candidate) == 228,
        "surface_role_order_preserved": [row["surface_role"] for row in historical_materials] == EXPECTED_ROLES,
        "topology_partition_actually_migrated": historical_partition != successor_partition,
        "historical_and_successor_geometry_digests_differ": historical_report.get("exact_world_geometry_sha256") != successor_report.get("exact_world_geometry_sha256"),
        "historical_and_successor_surface_partition_digests_differ": historical_report.get("surface_partition_sha256") != successor_report.get("surface_partition_sha256"),
        "placement_translation_preserved": historical_report.get("placement_translation_source_xyz_m") == successor_report.get("placement_translation_source_xyz_m"),
        "unrelated_seed29_receiving_scene_preserved": _strip_building_receiving(historical_candidate) == _strip_building_receiving(successor_candidate),
    }
    if not all(checks.values()):
        raise ValueError(f"Technical Art Building source rebind failed: {checks}")

    return {
        "schema": SCHEMA,
        "study_id": "technical-art-building-source-rebind-001",
        "status": STATUS,
        "receiving_head": receiving_head,
        "historical": {
            "map_material_receiving_head": "0e2d571af4fd5772e9d48da013dc245914654660",
            "building_source_head": HISTORICAL_SOURCE_HEAD,
            "building_material_head": HISTORICAL_MATERIAL_HEAD,
            "pavilion_source_sha256": HISTORICAL_PAVILION_SHA256,
            "producer_extension_output_count": historical_report.get("producer_extension_output_count"),
            "exact_world_geometry_sha256": historical_report.get("exact_world_geometry_sha256"),
            "surface_partition_sha256": historical_report.get("surface_partition_sha256"),
        },
        "successor": {
            "building_source_head": SUCCESSOR_SOURCE_HEAD,
            "building_material_head": SUCCESSOR_MATERIAL_HEAD,
            "pavilion_source_sha256": SUCCESSOR_PAVILION_SHA256,
            "panel_source_sha256": PANEL_SHA256,
            "material_profile_sha256": MATERIAL_PROFILE_SHA256,
            "producer_extension_output_count": successor_report.get("producer_extension_output_count"),
            "exact_world_geometry_sha256": successor_report.get("exact_world_geometry_sha256"),
            "surface_partition_sha256": successor_report.get("surface_partition_sha256"),
        },
        "preserved": {
            "vertices": 152,
            "triangles": 228,
            "surface_roles": EXPECTED_ROLES,
            "candidate_materials_sha256": _digest(successor_materials),
            "unrelated_receiving_scene_sha256": _digest(_strip_building_receiving(successor_candidate)),
            "placement_translation_source_xyz_m": successor_report.get("placement_translation_source_xyz_m"),
        },
        "checks": checks,
        "handoff": {
            "environment_pr24": "REBIND_REQUIRED_BEFORE_SUCCESSOR_CURRENT_WORLD_CLAIM",
            "runtime_pr26": "REBIND_AND_REMEASURE_REQUIRED_AFTER_ENVIRONMENT_SUCCESSOR_ADOPTION",
            "materials": "VALUES_UNCHANGED_THIS_LANE; MATERIALS_OWNS_INFILL_VISUAL_REPAIR",
            "universal_creation": "UNCHANGED; NO_BUILDING_DOMAIN_KNOWLEDGE_PROMOTED",
        },
        "truth_boundary": (
            "PASS proves that the established Map seed-29 Building material receiver can consume the producer's stable "
            "eight-field receiving prefix despite one additive successor evidence output, and can be rebound from the historical "
            "Building source to the source-owned closed/outward successor while preserving world vertices, placement, "
            "five material values and unrelated receiving state, with the topology partition changing explicitly. "
            "Target-host rendering is a separate workflow observation over the exact successor scene digest."
        ),
        "non_claims": [
            "MAP_PR24_CURRENT_WORLD_SUCCESSOR_ADOPTION",
            "RUNTIME_PR26_SUCCESSOR_BUDGET",
            "FINAL_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "UV_TEXTURE_DECAL_OR_WEATHERING_QUALITY",
            "TARGET_DEVICE_PERFORMANCE",
            "COLLISION_NAVIGATION_OR_GAMEPLAY",
            "CANON_PRODUCTION_READY_OR_TECHNICAL_ART_MASTERY",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-report", required=True)
    parser.add_argument("--historical-candidate", required=True)
    parser.add_argument("--successor-report", required=True)
    parser.add_argument("--successor-candidate", required=True)
    parser.add_argument("--receiving-head", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build_report(
        _load(args.historical_report),
        _load(args.historical_candidate),
        _load(args.successor_report),
        _load(args.successor_candidate),
        args.receiving_head,
    )
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
