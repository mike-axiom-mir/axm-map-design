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

import environment_building_source_replacement as env_building
import environment_eye_level as eye

SCHEMA = "axm.environment-building-material-receiving/v0.1"
EVIDENCE_SCHEMA = "axm.environment-building-material-receiving-evidence/v0.1"
SCENE_SCHEMA = "axm.environment-building-material-receiving-proof/v0.1"
EPS = 1e-9


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_digest(value) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_manifest(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unsupported Building receiving-material schema")
    return data


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _material_modules(material_root: Path):
    tools = material_root / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    source_module = _load_module(tools / "build_service_pavilion.py", "axm_receiving_building_source")
    material_module = _load_module(
        tools / "build_building_material_lookdev_evidence.py",
        "axm_receiving_building_materials",
    )
    return source_module, material_module


def _building_source(scene: dict) -> dict:
    matches = [
        row for row in scene.get("additional_source_meshes", [])
        if row.get("asset_id") == "source:building:service-pavilion-001"
    ]
    if len(matches) != 1:
        raise ValueError("exact PR #11 scene must contain one Building source mesh")
    return matches[0]


def _without_building_source(scene: dict) -> list[dict]:
    return [
        copy.deepcopy(row) for row in scene.get("additional_source_meshes", [])
        if row.get("asset_id") != "source:building:service-pavilion-001"
    ]


def _max_translation_error(local_vertices: list[list[float]], world_vertices: list[list[float]]) -> tuple[list[float], float]:
    if len(local_vertices) != len(world_vertices) or not local_vertices:
        raise ValueError("local/world Building vertex count mismatch")
    delta = [float(world_vertices[0][i]) - float(local_vertices[0][i]) for i in range(3)]
    max_error = 0.0
    for local, world in zip(local_vertices, world_vertices):
        for axis in range(3):
            expected = float(local[axis]) + delta[axis]
            max_error = max(max_error, abs(float(world[axis]) - expected))
    return delta, max_error


def _surface_groups(
    material_payload: dict,
    source_module,
    local_vertices: list[list[float]],
    local_triangles: list[list[int]],
    expected_material_ids: list[str],
) -> tuple[list[dict], dict]:
    components = material_payload["components"]
    if len(components) * 8 != len(local_vertices) or len(components) * 12 != len(local_triangles):
        raise ValueError("Building material components no longer align with exact box proof geometry")

    grouped: dict[str, list[list[int]]] = {name: [] for name in expected_material_ids}
    component_alignment_error = 0.0
    for index, component in enumerate(components):
        basis = tuple(component["source_basis"])
        expected_vertices = source_module.box_vertices(
            component["center_m"], component["size_local_xyz_m"], basis
        )
        actual_vertices = local_vertices[index * 8 : (index + 1) * 8]
        for expected, actual in zip(expected_vertices, actual_vertices):
            for axis in range(3):
                component_alignment_error = max(
                    component_alignment_error,
                    abs(float(expected[axis]) - float(actual[axis])),
                )
        role = component["candidate_material"]
        if role not in grouped:
            raise ValueError(f"unexpected Building material role {role!r}")
        grouped[role].extend(copy.deepcopy(local_triangles[index * 12 : (index + 1) * 12]))

    if component_alignment_error > EPS:
        raise ValueError(f"Building component/material geometry drift: {component_alignment_error}")
    if any(not grouped[name] for name in expected_material_ids):
        raise ValueError("every expected Building material role must own real triangles")

    baseline_material = material_payload["materials"]["baseline"]["neutral_proof"]
    candidate_materials = material_payload["materials"]["candidate"]
    surfaces = []
    for role in expected_material_ids:
        surfaces.append({
            "surface_role": role,
            "triangles": grouped[role],
            "baseline_material_id": "neutral_proof",
            "baseline_material": copy.deepcopy(baseline_material),
            "candidate_material_id": role,
            "candidate_material": copy.deepcopy(candidate_materials[role]),
        })
    return surfaces, {
        "component_count": len(components),
        "component_alignment_max_error_m": component_alignment_error,
        "triangles_by_surface_role": {name: len(grouped[name]) for name in expected_material_ids},
    }


def _render_surface_payload(
    exact_world_vertices: list[list[float]],
    surfaces: list[dict],
    mode: str,
    provenance: dict,
) -> dict:
    if mode not in {"baseline", "candidate"}:
        raise ValueError("unknown material render mode")
    rows = []
    for surface in surfaces:
        if mode == "baseline":
            material_id = surface["baseline_material_id"]
            material = surface["baseline_material"]
        else:
            material_id = surface["candidate_material_id"]
            material = surface["candidate_material"]
        rows.append({
            "surface_role": surface["surface_role"],
            "material_id": material_id,
            "material": copy.deepcopy(material),
            "triangles": copy.deepcopy(surface["triangles"]),
        })
    return {
        "asset_id": "source:building:service-pavilion-001",
        "kind": "building-source-material-receiving-proof",
        "vertices_source_xyz_m": copy.deepcopy(exact_world_vertices),
        "surfaces": rows,
        "provenance": copy.deepcopy(provenance),
        "proof_render_culling": "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_FINAL_MATERIAL_ACCEPTANCE",
    }


def _strip_material_response(scene: dict) -> dict:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    value.pop("receiving_head", None)
    surface = value.get("building_material_receiving")
    if isinstance(surface, dict):
        for row in surface.get("surfaces", []):
            row.pop("material_id", None)
            row.pop("material", None)
        surface.pop("mode", None)
    return value


def build_payloads(
    manifest_path: str | Path,
    base_nature_root: str | Path,
    compact_nature_root: str | Path,
    weather_root: str | Path,
    building_source_root: str | Path,
    building_material_root: str | Path,
) -> tuple[dict, dict, dict]:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(manifest_path)
    receiving = manifest["receiving_environment"]
    source_cfg = manifest["building_source"]
    material_cfg = manifest["building_materials"]

    observed_receiving_base = os.environ.get("AXM_RECEIVING_BASE_HEAD", receiving["exact_head"])
    observed_source_head = os.environ.get("AXM_BUILDING_SOURCE_HEAD", source_cfg["exact_head"])
    observed_material_head = os.environ.get("AXM_BUILDING_MATERIAL_HEAD", material_cfg["exact_head"])

    # Rebuild the exact PR #11 source scene through its own contract first.
    prior_building_head = os.environ.get("AXM_BUILDING_HEAD")
    os.environ["AXM_BUILDING_HEAD"] = source_cfg["exact_head"]
    try:
        _proxy_scene, exact_scene, exact_report = env_building.build_payloads(
            root / receiving["manifest"],
            base_nature_root,
            compact_nature_root,
            weather_root,
            building_source_root,
        )
    finally:
        if prior_building_head is None:
            os.environ.pop("AXM_BUILDING_HEAD", None)
        else:
            os.environ["AXM_BUILDING_HEAD"] = prior_building_head
    if exact_report["status"] != "PASS_BUILDING_SOURCE_REPLACEMENT_STRUCTURE":
        raise ValueError("exact Map PR #11 Building prerequisite must PASS first")

    exact_source = _building_source(exact_scene)
    exact_world_vertices = exact_source["vertices_source_xyz_m"]
    exact_triangles = exact_source["triangles"]

    source_root = Path(building_source_root)
    material_root = Path(building_material_root)
    source_pavilion = source_root / source_cfg["pavilion_source_path"]
    source_panel = source_root / source_cfg["panel_source_path"]
    material_pavilion = material_root / source_cfg["pavilion_source_path"]
    material_panel = material_root / source_cfg["panel_source_path"]
    profile_path = material_root / material_cfg["profile_path"]

    source_module, material_module = _material_modules(material_root)
    _pav, _panel, _fits, obj_lines, _mins, _maxs, _path_gap, _negatives = source_module.build()
    local_mesh = env_building._parse_obj(obj_lines)
    material_payload, material_receipt = material_module.build_payload(
        material_pavilion, material_panel, profile_path
    )

    expected_material_ids = list(material_cfg["expected_material_ids"])
    surfaces, alignment = _surface_groups(
        material_payload,
        source_module,
        local_mesh["vertices"],
        local_mesh["triangles"],
        expected_material_ids,
    )
    translation, translation_error = _max_translation_error(local_mesh["vertices"], exact_world_vertices)

    provenance = {
        "receiving_repository": receiving["repository"],
        "receiving_pr": receiving["pull_request"],
        "receiving_base_head": receiving["exact_head"],
        "building_source_repository": source_cfg["repository"],
        "building_source_pr": source_cfg["pull_request"],
        "building_source_head": source_cfg["exact_head"],
        "building_material_repository": material_cfg["repository"],
        "building_material_pr": material_cfg["pull_request"],
        "building_material_head": material_cfg["exact_head"],
        "pavilion_source_sha256": _sha256(material_pavilion),
        "panel_source_sha256": _sha256(material_panel),
        "material_profile_sha256": _sha256(profile_path),
        "placement_translation_source_xyz_m": translation,
    }

    baseline = copy.deepcopy(exact_scene)
    candidate = copy.deepcopy(exact_scene)
    for scene, mode in ((baseline, "baseline"), (candidate, "candidate")):
        scene["schema"] = SCENE_SCHEMA
        scene["study_id"] = manifest["study_id"]
        scene["receiving_head"] = os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD")
        scene["additional_source_meshes"] = _without_building_source(scene)
        scene["building_material_receiving"] = _render_surface_payload(
            exact_world_vertices,
            surfaces,
            mode,
            provenance,
        )
        scene["building_material_receiving"]["mode"] = mode
        scene["truth_boundary"] = manifest["truth_boundary"]
        scene.pop("scene_digest", None)
        scene["scene_digest"] = eye.digest(scene)

    checks = {
        "receiving_base_head_matches": observed_receiving_base == receiving["exact_head"],
        "building_source_checkout_head_matches": observed_source_head == source_cfg["exact_head"],
        "building_material_checkout_head_matches": observed_material_head == material_cfg["exact_head"],
        "pr11_prerequisite_passes_first": exact_report["status"] == "PASS_BUILDING_SOURCE_REPLACEMENT_STRUCTURE",
        "source_pavilion_digest_matches": _sha256(source_pavilion) == source_cfg["expected_pavilion_source_sha256"],
        "source_panel_digest_matches": _sha256(source_panel) == source_cfg["expected_panel_source_sha256"],
        "material_pavilion_digest_matches_source": _sha256(material_pavilion) == _sha256(source_pavilion),
        "material_panel_digest_matches_source": _sha256(material_panel) == _sha256(source_panel),
        "material_profile_digest_matches": _sha256(profile_path) == material_cfg["expected_profile_sha256"],
        "material_payload_passes_source_gate": material_receipt["result"] == "PASS_SOURCE_BOUND_BUILDING_SURFACE_PAYLOAD",
        "material_payload_source_hashes_match": material_receipt["pavilion_source_sha256"] == source_cfg["expected_pavilion_source_sha256"] and material_receipt["panel_source_sha256"] == source_cfg["expected_panel_source_sha256"],
        "material_ids_match_exact_profile": sorted(material_payload["materials"]["candidate"]) == sorted(expected_material_ids),
        "source_vertex_count_preserved": len(exact_world_vertices) == len(local_mesh["vertices"]) == int(source_cfg["expected_vertices"]),
        "source_triangle_count_preserved": len(exact_triangles) == len(local_mesh["triangles"]) == int(source_cfg["expected_triangles"]),
        "source_triangle_indices_preserved": exact_triangles == local_mesh["triangles"],
        "source_world_transform_is_translation_only": translation_error <= EPS,
        "component_material_geometry_alignment_exact": alignment["component_alignment_max_error_m"] <= EPS,
        "all_five_surface_roles_have_triangles": len(alignment["triangles_by_surface_role"]) == len(expected_material_ids) and all(value > 0 for value in alignment["triangles_by_surface_role"].values()),
        "all_triangles_partitioned_once": sum(alignment["triangles_by_surface_role"].values()) == len(exact_triangles),
        "neutral_and_candidate_scene_equal_except_building_material_response": _strip_material_response(baseline) == _strip_material_response(candidate),
        "baseline_candidate_building_vertices_identical": baseline["building_material_receiving"]["vertices_source_xyz_m"] == candidate["building_material_receiving"]["vertices_source_xyz_m"],
        "baseline_candidate_surface_triangle_partition_identical": [row["triangles"] for row in baseline["building_material_receiving"]["surfaces"]] == [row["triangles"] for row in candidate["building_material_receiving"]["surfaces"]],
        "unrelated_source_meshes_preserved": baseline["additional_source_meshes"] == candidate["additional_source_meshes"] == _without_building_source(exact_scene),
        "west_sapling_preserved": baseline["sapling"] == candidate["sapling"] == exact_scene["sapling"],
        "weather_preserved": baseline["weather_lines"] == candidate["weather_lines"] == exact_scene["weather_lines"],
        "items_preserved": baseline["items"] == candidate["items"] == exact_scene["items"],
        "cameras_preserved": baseline["cameras"] == candidate["cameras"] == exact_scene["cameras"],
        "path_preserved": baseline["readable_path"] == candidate["readable_path"] == exact_scene["readable_path"],
        "candidate_scene_digest_differs_only_after_material_response": baseline["scene_digest"] != candidate["scene_digest"],
        "comparison_is_surface_only": manifest["comparison_policy"]["isolate_delta"] == "BUILDING_NEUTRAL_PROOF_TO_EXACT_FIVE_SURFACE_FAMILY_ONLY",
        "no_uv_texture_decal_weathering_promotion": all(manifest["comparison_policy"][key] == "NOT_AUTHORED" for key in ("uvs", "textures", "decals", "weathering")),
    }

    report = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": manifest["study_id"],
        "status": "PASS_RECEIVING_SCENE_BUILDING_MATERIAL_TRANSFER_STRUCTURE" if all(checks.values()) else "FAIL",
        "receiving_head": candidate["receiving_head"],
        "receiving_base_head": receiving["exact_head"],
        "building_source_head": source_cfg["exact_head"],
        "building_material_head": material_cfg["exact_head"],
        "pavilion_source_sha256": _sha256(material_pavilion),
        "panel_source_sha256": _sha256(material_panel),
        "material_profile_sha256": _sha256(profile_path),
        "material_payload_geometry_contract_sha256": material_receipt["geometry_contract_sha256"],
        "exact_world_geometry_sha256": _canonical_digest({"vertices": exact_world_vertices, "triangles": exact_triangles}),
        "surface_partition_sha256": _canonical_digest([{ "surface_role": row["surface_role"], "triangles": row["triangles"] } for row in baseline["building_material_receiving"]["surfaces"]]),
        "baseline_scene_digest": baseline["scene_digest"],
        "candidate_scene_digest": candidate["scene_digest"],
        "placement_translation_source_xyz_m": translation,
        "placement_translation_max_error_m": translation_error,
        "component_alignment": alignment,
        "candidate_materials": material_payload["materials"]["candidate"],
        "art_direction_constraints": manifest["art_direction_constraints"],
        "checks": checks,
        "truth_boundary": manifest["truth_boundary"],
        "non_claims": [
            "FINAL_ART_DIRECTION_ACCEPTANCE",
            "FINAL_VISUAL_QA_ACCEPTANCE",
            "UV_OR_TEXTURE_QUALITY",
            "PHYSICALLY_MEASURED_SURFACES",
            "FINAL_LIGHTING",
            "TARGET_DEVICE_RUNTIME_BUDGET",
            "ARCHITECTURAL_ENGINEERING",
            "GAMEPLAY",
            "CANON_OR_MASTERY",
        ],
    }
    return baseline, candidate, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_building_material_receiving_001.json")
    parser.add_argument("--base-nature-root", required=True)
    parser.add_argument("--compact-nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--building-source-root", required=True)
    parser.add_argument("--building-material-root", required=True)
    parser.add_argument("--output", default="evidence/environment_building_material_receiving_001")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    baseline, candidate, report = build_payloads(
        args.manifest,
        args.base_nature_root,
        args.compact_nature_root,
        args.weather_root,
        args.building_source_root,
        args.building_material_root,
    )
    (out / "neutral_scene_runtime.json").write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "candidate_scene_runtime.json").write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "material_transfer_evidence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    material_root = Path(args.building_material_root)
    profile = material_root / load_manifest(args.manifest)["building_materials"]["profile_path"]
    (out / "building_material_profile_001.json").write_bytes(profile.read_bytes())
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS_RECEIVING_SCENE_BUILDING_MATERIAL_TRANSFER_STRUCTURE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
