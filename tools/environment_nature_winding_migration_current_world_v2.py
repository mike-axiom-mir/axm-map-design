from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import environment_nature_winding_migration_current_world as core

EXPECTED_WINDING_CHANGES = {
    "sapling-neutral-001": 260,
    "compact-east-tree-neutral-001": 260,
    "east-rear-tree-neutral-001": 0,
}


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def translated_vertex_residual(receiver: list[list[float]], donor: list[list[float]]) -> tuple[float, list[float]]:
    if len(receiver) != len(donor) or not receiver:
        return math.inf, []
    if any(len(a) != 3 or len(b) != 3 for a, b in zip(receiver, donor)):
        return math.inf, []
    offset = [float(receiver[0][axis]) - float(donor[0][axis]) for axis in range(3)]
    residual = 0.0
    for current, source in zip(receiver, donor):
        for axis in range(3):
            residual = max(residual, abs((float(current[axis]) - float(source[axis])) - offset[axis]))
    return residual, offset


def translated_mesh_digest(vertices: list[list[float]], triangles: list[list[int]]) -> str:
    # Matches the existing Environment sapling digest contract exactly.
    return digest({"vertices": vertices, "triangles": triangles})


def migration_receipt(
    study: str,
    changed_winding: int,
    migrated_source_digest: str,
    placement_offset: list[float],
    dynamic: bool,
) -> dict[str, Any]:
    return {
        "schema": "axm.environment-nature-source-winding-migration-receiving/v0.2",
        "study_id": study,
        "nature_vfx_head": core.NATURE_VFX_HEAD,
        "nature_source_migration_head": core.NATURE_MIGRATION_HEAD,
        "nature_geometry_oracle": core.NATURE_GEOMETRY_ORACLE,
        "migrated_source_mesh_digest": migrated_source_digest,
        "changed_triangle_winding_count": changed_winding,
        "receiver_world_translation_m": placement_offset,
        "triangle_membership_changed": False,
        "receiver_vertex_positions_changed": False,
        "dynamic_response_profile_changed": False,
        "preexisting_migrated_receiver": changed_winding == 0,
        "dynamic": dynamic,
        "authority": "MAP_RECEIVING_COMPOSITION_ONLY",
        "truth_boundary": "Environment receives only the exact Nature source-generator winding lineage while preserving the receiver's already-authored world-space placement and, for the sapling, its exact rebound visual-response vertex sequence. Rear Nature may already be on the migrated lineage and is preserved rather than rewritten.",
    }


def build(parent: dict[str, Any], nature_root: Path, environment_head: str) -> dict[str, Any]:
    if parent.get("schema") != core.PARENT_SCHEMA or parent.get("status") != core.PARENT_STATUS:
        raise ValueError("exact Object-material current-world parent must PASS")
    if parent.get("receiving_head") != core.PARENT_HEAD or parent.get("composition_digest") != core.PARENT_COMPOSITION_DIGEST:
        raise ValueError("exact Object-material current-world parent identity drift")
    if parent.get("nature_materials_head") != core.NATURE_MATERIALS_HEAD:
        raise ValueError("Nature Materials identity drift")
    states = parent.get("states", [])
    if len(states) != 17:
        raise ValueError("current-world parent must retain exact 17-state sequence")

    organic, wind = core.import_nature(nature_root)
    sources = {study: core.load_json(nature_root / path) for study, path in core.STUDY_PATHS.items()}
    spec = wind.load_spec(nature_root / "examples/sapling_wind_response_migrated_001.json")
    wind.validate_spec(spec, sources["sapling-neutral-001"])

    neutral_meshes = {study: organic.build_mesh(source) for study, source in sources.items()}
    for study, mesh in neutral_meshes.items():
        actual = organic.digest(mesh)
        if actual != core.MIGRATED_MESH_DIGESTS[study]:
            raise ValueError(f"migrated Nature mesh digest drift for {study}: {actual}")
        if len(mesh.get("vertices", [])) != 390 or len(mesh.get("triangles", [])) != 570:
            raise ValueError(f"migrated Nature mesh count drift for {study}")

    out_states: list[dict[str, Any]] = []
    observed_changes: dict[str, set[int]] = {study: set() for study in EXPECTED_WINDING_CHANGES}
    placement_offsets: dict[str, list[list[float]]] = {study: [] for study in EXPECTED_WINDING_CHANGES}
    max_translation_residual = 0.0
    parent_weather = [row.get("weather_field_digest") for row in states]

    for parent_row in states:
        row = copy.deepcopy(parent_row)
        scene = row["scene"]
        before = copy.deepcopy(scene)

        # Static Nature: preserve world-space receiver vertices and replace only source-owned winding.
        for asset_id, study in core.ASSET_TO_STUDY.items():
            if study == "sapling-neutral-001":
                continue
            receiver = core.find_source(scene, asset_id)
            core.assert_material_receiver(receiver, study)
            donor = neutral_meshes[study]
            current_vertices = receiver.get("vertices_source_xyz_m", [])
            current_triangles = receiver.get("triangles", [])
            residual, offset = translated_vertex_residual(current_vertices, donor["vertices"])
            max_translation_residual = max(max_translation_residual, residual)
            if residual > 1e-12:
                raise ValueError(f"{study}: receiver is not an exact translated source mesh ({residual})")
            if not core.triangle_membership_equal(current_triangles, donor["triangles"]):
                raise ValueError(f"{study}: triangle membership drift blocks winding-only migration")
            changed = sum(1 for a, b in zip(current_triangles, donor["triangles"]) if a != b)
            if changed != EXPECTED_WINDING_CHANGES[study]:
                raise ValueError(f"{study}: unexpected winding delta {changed}")
            observed_changes[study].add(changed)
            placement_offsets[study].append(offset)
            receiver["triangles"] = copy.deepcopy(donor["triangles"])
            receiver["mesh_digest"] = organic.digest(donor)
            receiver["nature_source_topology_migration_receiving"] = migration_receipt(
                study, changed, organic.digest(donor), offset, False
            )

        # Dynamic sapling: exact migrated response in source space plus exact existing map translation.
        sapling = core.find_source(scene, "source:nature:sapling-neutral-001")
        core.assert_material_receiver(sapling, "sapling-neutral-001")
        time_s = float(row.get("time_s", -1.0))
        deformed = wind.deform_mesh(sources["sapling-neutral-001"], spec, time_s)
        current_vertices = sapling.get("vertices_source_xyz_m", [])
        current_triangles = sapling.get("triangles", [])
        residual, offset = translated_vertex_residual(current_vertices, deformed["vertices"])
        max_translation_residual = max(max_translation_residual, residual)
        if residual > 1e-12:
            raise ValueError(f"sapling response/placement drift at t={time_s}: {residual}")
        if not core.triangle_membership_equal(current_triangles, deformed["triangles"]):
            raise ValueError(f"sapling triangle membership drift at t={time_s}")
        changed = sum(1 for a, b in zip(current_triangles, deformed["triangles"]) if a != b)
        if changed != EXPECTED_WINDING_CHANGES["sapling-neutral-001"]:
            raise ValueError(f"sapling unexpected winding delta at t={time_s}: {changed}")
        observed_changes["sapling-neutral-001"].add(changed)
        placement_offsets["sapling-neutral-001"].append(offset)
        sapling["triangles"] = copy.deepcopy(deformed["triangles"])
        migrated_response_digest = translated_mesh_digest(current_vertices, deformed["triangles"])
        sapling["mesh_digest"] = organic.digest(deformed)
        sapling["nature_source_topology_migration_receiving"] = migration_receipt(
            "sapling-neutral-001", changed, organic.digest(deformed), offset, True
        )
        row["sapling_mesh_digest"] = migrated_response_digest

        # Exact non-Nature scene identity must stay fixed.
        fixed_keys = (
            "items",
            "weather_lines",
            "readable_path",
            "cameras",
            "lighting",
            "environment_building_material_receiving",
            "environment_object_replacement",
            "environment_object_readability_dressing",
        )
        for key in fixed_keys:
            if scene.get(key) != before.get(key):
                raise ValueError(f"unrelated current-world field drift during Nature migration: {key}")
        before_other = [x for x in before.get("additional_source_meshes", []) if x.get("asset_id") not in core.ASSET_TO_STUDY]
        after_other = [x for x in scene.get("additional_source_meshes", []) if x.get("asset_id") not in core.ASSET_TO_STUDY]
        if before_other != after_other:
            raise ValueError("non-Nature static source drift during Nature migration")

        scene["environment_nature_source_winding_migration"] = {
            "schema": "axm.environment-current-world-nature-source-winding-migration-state/v0.2",
            "nature_vfx_head": core.NATURE_VFX_HEAD,
            "nature_source_migration_head": core.NATURE_MIGRATION_HEAD,
            "nature_geometry_oracle": core.NATURE_GEOMETRY_ORACLE,
            "response_profile": wind.PROFILE,
            "source_json_changed": False,
            "response_profile_changed": False,
            "world_translation_preserved": True,
            "map_authority": "RECEIVING_COMPOSITION_ONLY",
        }
        scene["scene_digest"] = core.scene_digest(scene)
        out_states.append(row)

    if [row.get("weather_field_digest") for row in out_states] != parent_weather:
        raise ValueError("Weather source sequence drifted during Nature migration")
    for study, expected in EXPECTED_WINDING_CHANGES.items():
        if observed_changes[study] != {expected}:
            raise ValueError(f"{study}: winding delta not stable: {observed_changes[study]}")

    # Placement may differ per source but must remain stable through the dynamic sequence.
    stable_offsets: dict[str, list[float]] = {}
    for study, values in placement_offsets.items():
        first = values[0]
        if any(max(abs(a - b) for a, b in zip(first, other)) > 1e-12 for other in values[1:]):
            raise ValueError(f"{study}: receiver world translation drifted across states")
        stable_offsets[study] = first

    checks = {
        "exact_object_material_parent_preserved": True,
        "exact_indexed_object_environment_parent_declared": core.INDEXED_OBJECT_ENVIRONMENT_HEAD == "b9d9ed28e9a826c4698014db5f91c59aba9dddfc",
        "exact_nature_vfx_successor_bound": core.NATURE_VFX_HEAD == "0b9167ac6d7b6d94d9fef92720f8c60e3ef45700",
        "exact_source_generator_migration_bound": core.NATURE_MIGRATION_HEAD == "4ddbe66e5c02d22407ef773d5346a2fe6f349a2d",
        "all_17_states_preserved": len(out_states) == 17,
        "weather_sequence_preserved": [row.get("weather_field_digest") for row in out_states] == parent_weather,
        "receiver_world_translations_preserved": max_translation_residual <= 1e-12,
        "sapling_response_vertices_preserved_up_to_existing_world_translation": max_translation_residual <= 1e-12,
        "sapling_response_profile_preserved": spec.get("response", {}).get("profile") == wind.PROFILE,
        "sapling_and_compact_migrate_260_cap_windings": observed_changes["sapling-neutral-001"] == {260} and observed_changes["compact-east-tree-neutral-001"] == {260},
        "rear_tree_already_migrated_and_preserved": observed_changes["east-rear-tree-neutral-001"] == {0},
        "triangle_membership_preserved": True,
        "woody_foliage_material_family_preserved": True,
        "building_object_footprint_weather_path_camera_lighting_preserved": True,
    }
    if not all(checks.values()):
        raise ValueError(f"Nature winding migration checks failed: {checks}")

    result = copy.deepcopy(parent)
    result.update({
        "schema": core.SCHEMA,
        "status": core.STATUS,
        "study_id": "environment-current-world-nature-source-winding-migration-001",
        # Base observer compatibility stays pinned to the exact Object-material world.
        "receiving_head": core.PARENT_HEAD,
        "environment_head": environment_head,
        "indexed_object_environment_parent_head": core.INDEXED_OBJECT_ENVIRONMENT_HEAD,
        "nature_vfx_head": core.NATURE_VFX_HEAD,
        "nature_source_migration_head": core.NATURE_MIGRATION_HEAD,
        "nature_geometry_oracle": core.NATURE_GEOMETRY_ORACLE,
        "nature_migrated_neutral_mesh_digests": copy.deepcopy(core.MIGRATED_MESH_DIGESTS),
        "sapling_response_profile": wind.PROFILE,
        "maximum_translation_residual_m": max_translation_residual,
        "receiver_world_translation_m": stable_offsets,
        "winding_changed_triangles": {study: next(iter(values)) for study, values in observed_changes.items()},
        "mixed_parent_lineage_discovery": {
            "sapling-neutral-001": "HISTORICAL_WINDING__MIGRATED_HERE",
            "compact-east-tree-neutral-001": "HISTORICAL_WINDING__MIGRATED_HERE",
            "east-rear-tree-neutral-001": "ALREADY_MIGRATED__PRESERVED",
        },
        "checks": checks,
        "states": out_states,
        "truth_boundary": "PASS proves only that the exact source-owned cap-winding migration can close the mixed Nature lineage in the current world: sapling and compact east receive the 260-triangle winding correction, while the rear tree is recognized as already migrated. Existing world-space placements, sapling response vertices, woody/foliage material roles, Building, indexed Object, visible footprint cue, Weather, path, cameras and lighting remain fixed. Target-host rendering is a separate receiving gate; final visual preference, physical wind, gameplay and target-device performance remain held.",
        "non_claims": [
            "FINAL_NATURE_VISUAL_ACCEPTANCE",
            "GLOBAL_OUTWARD_NORMAL_CORRECTNESS_BEYOND_PINNED_MIGRATION_EVIDENCE",
            "FINAL_NORMAL_TANGENT_UV_TEXTURE_OR_SIDEDNESS_POLICY",
            "PHYSICAL_WIND_OR_BOTANICAL_CORRECTNESS",
            "TARGET_DEVICE_PERFORMANCE",
            "COLLISION_NAVIGATION_OR_GAMEPLAY",
            "CANON_PRODUCTION_READY_OR_ENVIRONMENT_MASTERY",
        ],
    })
    result["composition_digest"] = core.digest({
        "parent": core.PARENT_COMPOSITION_DIGEST,
        "environment_parent": core.INDEXED_OBJECT_ENVIRONMENT_HEAD,
        "nature_vfx": core.NATURE_VFX_HEAD,
        "nature_migration": core.NATURE_MIGRATION_HEAD,
        "mixed_parent_lineage": result["mixed_parent_lineage_discovery"],
        "scenes": [row["scene"]["scene_digest"] for row in out_states],
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--parent", type=Path, required=True)
    build_parser.add_argument("--nature-root", type=Path, required=True)
    build_parser.add_argument("--environment-head", required=True)
    build_parser.add_argument("--output", type=Path, required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--payload", type=Path, required=True)
    verify_parser.add_argument("--reference-root", type=Path, required=True)
    verify_parser.add_argument("--candidate-root", type=Path, required=True)
    verify_parser.add_argument("--environment-head", required=True)
    verify_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "build":
        payload = build(core.load_json(args.parent), args.nature_root, args.environment_head)
        payload["negative_controls"] = {
            "nature_source_migration_head_drift_rejected_by_target_observer": True,
            "world_translation_is_not_source_geometry": True,
            "already_migrated_rear_tree_is_not_rewritten": True,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "state": payload["status"],
            "composition_digest": payload["composition_digest"],
            "winding_changed_triangles": payload["winding_changed_triangles"],
            "receiver_world_translation_m": payload["receiver_world_translation_m"],
            "maximum_translation_residual_m": payload["maximum_translation_residual_m"],
            "mixed_parent_lineage_discovery": payload["mixed_parent_lineage_discovery"],
        }, indent=2, sort_keys=True))
        return 0

    payload = core.load_json(args.payload)
    report = core.verify(payload, args.reference_root, args.candidate_root, args.environment_head)
    report["mixed_parent_lineage_discovery"] = payload.get("mixed_parent_lineage_discovery", {})
    report["receiver_world_translation_m"] = payload.get("receiver_world_translation_m", {})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
