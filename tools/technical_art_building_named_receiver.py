from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Mapping

SCHEMA = "axm.technical-art-building-named-receiver-evidence/v0.1"
STATUS = "PASS_BUILDING_NAMED_RESULT_TO_MAP_RECEIVER_PROJECTION"
BUILD_RESULT_SCHEMA = "axm.building-build-result/v0.1"
HEADER_SEGMENTATION_RESULT = "PASS_SOURCE_OWNED_INTERPENETRATION_FREE_HEADER_SEGMENTATION_OVERLAY"
REQUIRED_FIELDS = (
    "pavilion",
    "panel",
    "receiver_fits",
    "obj_lines",
    "bounds_min",
    "bounds_max",
    "readable_path_gap_m",
    "negative_controls",
    "topology_summary",
)
BASE_TOPOLOGY = {
    "revision": "closed-outward-12-triangle-v1",
    "object_count": 19,
    "vertex_count": 152,
    "triangle_count": 228,
    "boundary_edge_count": 0,
    "nonmanifold_edge_count": 0,
    "orientation_conflict_edge_count": 0,
    "degenerate_triangle_count": 0,
    "outward_triangle_count": 228,
    "inward_triangle_count": 0,
    "tangent_triangle_count": 0,
}
EXPECTED_PAVILION_SHA256 = "5f89ec4109d48f452f9e887ad5ca5449e1d0f6d6ee4b1896be6f25bc0a80736a"
EXPECTED_PANEL_SHA256 = "df59fa135abc89f8c85317db1d6b9ce3d03920efc91271de61bfb6289a24c253"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def _obj_counts(lines: list[str]) -> tuple[int, int]:
    vertices = sum(1 for line in lines if str(line).startswith("v "))
    triangles = sum(1 for line in lines if str(line).startswith("f "))
    return vertices, triangles


def _base_topology_exact(summary: Mapping[str, object]) -> bool:
    return all(summary.get(key) == value for key, value in BASE_TOPOLOGY.items())


def project_named_result(named: Mapping[str, object], contract_module) -> dict:
    contract_module.require_fields(named, REQUIRED_FIELDS)
    if named.get("schema") != BUILD_RESULT_SCHEMA:
        raise ValueError("unsupported Building named build-result schema")
    topology = named["topology_summary"]
    if not isinstance(topology, Mapping) or not _base_topology_exact(topology):
        raise ValueError("Map base receiver projection requires the exact 19-box closed/outward topology")
    vertices, triangles = _obj_counts(named["obj_lines"])
    if vertices != BASE_TOPOLOGY["vertex_count"] or triangles != BASE_TOPOLOGY["triangle_count"]:
        raise ValueError("named Building OBJ budget does not match the declared base topology")
    projection = {
        "schema": "axm.map-building-named-receiver-projection/v0.1",
        "producer_schema": named["schema"],
        "pavilion": copy.deepcopy(named["pavilion"]),
        "panel": copy.deepcopy(named["panel"]),
        "receiver_fits": copy.deepcopy(named["receiver_fits"]),
        "obj_lines": copy.deepcopy(named["obj_lines"]),
        "bounds_min": copy.deepcopy(named["bounds_min"]),
        "bounds_max": copy.deepcopy(named["bounds_max"]),
        "readable_path_gap_m": named["readable_path_gap_m"],
        "negative_controls": copy.deepcopy(named["negative_controls"]),
        "topology_summary": copy.deepcopy(named["topology_summary"]),
    }
    projection["projection_sha256"] = _digest(projection)
    return projection


def build_report(building_root: str | Path, building_head: str, receiving_head: str, uc_head: str) -> tuple[dict, dict]:
    root = Path(building_root)
    observed_head = _git_head(root)
    contract = _load_module(root / "tools" / "service_pavilion_build_result.py", "axm_building_named_result")
    named = contract.build_named()
    projection = project_named_result(named, contract)

    pavilion_path = root / "assets" / "service_pavilion_001.json"
    panel_path = root / "assets" / "utility_access_panel_001.json"
    pavilion_sha = _sha256(pavilion_path)
    panel_sha = _sha256(panel_path)

    # Pressure-test additive legacy evolution through the producer-owned adapter.
    extended_legacy = list(contract.builder.build()) + [{"future_extension": "OPAQUE_TO_MAP"}]
    extended_named = contract.from_legacy_output(extended_legacy)
    extended_projection = project_named_result(extended_named, contract)

    # The newest Hard-Surface head also carries a separate opt-in header segmentation overlay.
    # Build it directly, but do not feed it into the Map base receiver projection.
    header_module = _load_module(
        root / "tools" / "build_service_pavilion_header_segmentation.py",
        "axm_building_header_segmentation",
    )
    _header_base, _header_candidate, header = header_module.build(exact_head=building_head)

    fail_closed = {}
    bad_schema = copy.deepcopy(named)
    bad_schema["schema"] = "axm.building-build-result/v999"
    try:
        project_named_result(bad_schema, contract)
        fail_closed["schema_drift"] = "UNEXPECTED_PASS"
    except ValueError as exc:
        fail_closed["schema_drift"] = "REJECTED: " + str(exc)

    missing = copy.deepcopy(named)
    missing.pop("topology_summary", None)
    try:
        project_named_result(missing, contract)
        fail_closed["missing_declared_field"] = "UNEXPECTED_PASS"
    except ValueError as exc:
        fail_closed["missing_declared_field"] = "REJECTED: " + str(exc)

    overlay_as_base = copy.deepcopy(named)
    overlay_as_base["topology_summary"] = {
        **copy.deepcopy(named["topology_summary"]),
        "object_count": 23,
        "vertex_count": 184,
        "triangle_count": 276,
    }
    try:
        project_named_result(overlay_as_base, contract)
        fail_closed["silent_header_overlay_promotion"] = "UNEXPECTED_PASS"
    except ValueError as exc:
        fail_closed["silent_header_overlay_promotion"] = "REJECTED: " + str(exc)

    checks = {
        "building_checkout_head_exact": observed_head == building_head,
        "named_contract_schema_exact": named.get("schema") == BUILD_RESULT_SCHEMA,
        "named_contract_declared_fields_available": all(field in named for field in REQUIRED_FIELDS),
        "source_pavilion_identity_exact": pavilion_sha == EXPECTED_PAVILION_SHA256,
        "source_panel_identity_exact": panel_sha == EXPECTED_PANEL_SHA256,
        "base_topology_exact": _base_topology_exact(named["topology_summary"]),
        "base_receiver_projection_uses_named_fields": projection["producer_schema"] == BUILD_RESULT_SCHEMA,
        "base_receiver_projection_budget_exact": _obj_counts(projection["obj_lines"]) == (152, 228),
        "opaque_tenth_legacy_extension_observed": extended_named.get("legacy_output_count_observed") == 10,
        "opaque_tenth_extension_count_is_one": extended_named.get("opaque_trailing_extension_count") == 1,
        "opaque_tenth_extension_leaves_projection_identical": extended_projection["projection_sha256"] == projection["projection_sha256"],
        "header_overlay_exists_as_separate_source_owned_contract": header.get("result") == HEADER_SEGMENTATION_RESULT,
        "header_overlay_is_materially_different_emission": (
            header.get("emitted_successor_box_count_with_panels") == 23
            and header.get("topology", {}).get("vertex_count") == 184
            and header.get("topology", {}).get("triangle_count") == 276
        ),
        "header_overlay_not_silently_consumed_by_base_projection": (
            projection["topology_summary"]["object_count"] == 19
            and projection["topology_summary"]["vertex_count"] == 152
            and projection["topology_summary"]["triangle_count"] == 228
        ),
        "all_negative_controls_rejected": all(str(value).startswith("REJECTED") for value in fail_closed.values()),
    }
    if not all(checks.values()):
        raise ValueError(f"named Building receiver contract failed: {checks}")

    report = {
        "schema": SCHEMA,
        "study_id": "technical-art-building-named-receiver-001",
        "status": STATUS,
        "receiving_head": receiving_head,
        "building": {
            "repository": "mike-axiom-mir/axm-building-design",
            "pull_request": 2,
            "exact_head": building_head,
            "build_result_schema": BUILD_RESULT_SCHEMA,
            "pavilion_source_sha256": pavilion_sha,
            "panel_source_sha256": panel_sha,
            "legacy_output_count_observed": named.get("legacy_output_count_observed"),
            "opaque_trailing_extension_count": named.get("opaque_trailing_extension_count"),
            "base_topology": copy.deepcopy(named["topology_summary"]),
        },
        "map_receiver_projection": {
            "schema": projection["schema"],
            "declared_fields": list(REQUIRED_FIELDS),
            "projection_sha256": projection["projection_sha256"],
            "vertices": 152,
            "triangles": 228,
            "receiver_count": len(projection["receiver_fits"]),
        },
        "extension_pressure": {
            "opaque_tenth_legacy_extension": "PASS_UNCHANGED_NAMED_PROJECTION",
            "header_segmentation_overlay_result": header.get("result"),
            "header_segmentation_successor_revision": header.get("successor_revision"),
            "header_segmentation_emitted_boxes": header.get("emitted_successor_box_count_with_panels"),
            "header_segmentation_vertices": header.get("topology", {}).get("vertex_count"),
            "header_segmentation_triangles": header.get("topology", {}).get("triangle_count"),
            "map_adoption": "NOT_ADOPTED_BY_THIS_PROOF",
        },
        "universal_creation": {
            "inspected_main_head": uc_head,
            "dependency": "NONE",
            "change_required": False,
            "reason": "Building producer naming and Map receiver dependency declaration remain domain-bound handoff plumbing; no generic UC primitive is missing.",
        },
        "checks": checks,
        "negative_controls": fail_closed,
        "truth_boundary": (
            "PASS proves only that Map Technical Art can bind the current Building producer by the source-owned "
            "axm.building-build-result/v0.1 field names, reproduce the exact existing 19-box/152-vertex/228-triangle "
            "base receiver projection, ignore an opaque later legacy tuple extension through the producer-owned adapter, "
            "and keep the newer source-owned 23-box header-segmentation overlay explicitly opt-in rather than silently "
            "promoting it into the base receiver."
        ),
        "non_claims": [
            "MAP_ENVIRONMENT_HEADER_SEGMENTATION_ADOPTION",
            "MAP_CURRENT_WORLD_HEADER_SEGMENTATION_RENDER_ACCEPTANCE",
            "BUILDING_HEADER_SEGMENTATION_MATERIAL_MAPPING",
            "RUNTIME_OR_TARGET_DEVICE_ACCEPTANCE",
            "FINAL_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "UC_EXTRACTION_OR_GENERIC_CROSS_DOMAIN_RESULT_STANDARD",
            "COLLISION_NAVIGATION_GAMEPLAY_CANON_PRODUCTION_READINESS_OR_TECHNICAL_ART_MASTERY",
        ],
    }
    return projection, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--building-root", required=True)
    parser.add_argument("--building-head", required=True)
    parser.add_argument("--receiving-head", required=True)
    parser.add_argument("--uc-head", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    projection, report = build_report(args.building_root, args.building_head, args.receiving_head, args.uc_head)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "map_named_receiver_projection.json").write_text(
        json.dumps(projection, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "technical_art_named_receiver_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "building-head.txt").write_text(args.building_head + "\n", encoding="utf-8")
    (out / "uc-inspected-head.txt").write_text(args.uc_head + "\n", encoding="utf-8")
    (out / "receiving-head.txt").write_text(args.receiving_head + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
