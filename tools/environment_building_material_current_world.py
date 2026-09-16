from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

SCHEMA = "axm.environment-current-world-building-material-convergence-evidence/v0.1"
STATUS = "PASS_CURRENT_WORLD_BUILDING_MATERIAL_CONVERGENCE_STRUCTURE"
TARGET_STATUS = "PASS_CURRENT_WORLD_BUILDING_MATERIAL_CONVERGENCE_TARGET_HOST"
PARENT_SCHEMA = "axm.environment-weather-variant-object-current-world-evidence/v0.1"
PARENT_STATUS = "PASS_WEATHER_VARIANT_OBJECT_SOURCE_COMPOSITION_STRUCTURE"
OBSERVER_SCHEMA = "axm.environment-current-world-weather-variant-evidence/v0.1"
OBSERVER_STATUS = "PASS_CURRENT_WORLD_WEATHER_VARIANT_REBIND_STRUCTURE"
MATERIAL_REPORT_STATUS = "PASS_RECEIVING_SCENE_BUILDING_MATERIAL_TRANSFER_STRUCTURE"
BUILDING_ID = "source:building:service-pavilion-001"
EXPECTED_ROLES = [
    "frame_galvanized",
    "infill_coating",
    "roof_membrane",
    "slab_mineral",
    "utility_panel_ochre",
]
EXPECTED_STATES = 17
EXPECTED_CONTEXTS = ("path_eye", "elevated_oblique")


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _scene_digest(scene: dict) -> str:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    return _digest(value)


def _tri_multiset(rows):
    return sorted(tuple(int(x) for x in tri) for tri in rows)


def _find_building(scene: dict) -> dict:
    matches = [row for row in scene.get("additional_source_meshes", []) if row.get("asset_id") == BUILDING_ID]
    if len(matches) != 1:
        raise ValueError("current scene must contain exactly one source-owned Building pavilion")
    return matches[0]


def _flatten_surfaces(material_receiving: dict) -> list[list[int]]:
    rows = []
    for surface in material_receiving.get("surfaces", []):
        rows.extend(copy.deepcopy(surface.get("triangles", [])))
    return rows


def _strip_building_material_scene(scene: dict) -> dict:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    value.pop("environment_building_material_receiving", None)
    return value


def _validate_material_donor(material_scene: dict, material_report: dict) -> dict:
    if material_report.get("status") != MATERIAL_REPORT_STATUS:
        raise ValueError("exact Map Materials donor must PASS its structural transfer gate")
    if not all(material_report.get("checks", {}).values()):
        raise ValueError("exact Map Materials donor contains a failed structural check")
    receiving = material_scene.get("building_material_receiving")
    if not isinstance(receiving, dict) or receiving.get("asset_id") != BUILDING_ID:
        raise ValueError("material donor is missing exact Building receiving payload")
    if receiving.get("mode") != "candidate":
        raise ValueError("material donor must be the exact candidate, not neutral control")
    surfaces = receiving.get("surfaces", [])
    roles = [row.get("surface_role") for row in surfaces]
    if roles != EXPECTED_ROLES:
        raise ValueError(f"Building material roles drift: {roles!r}")
    if any(row.get("material_id") != row.get("surface_role") for row in surfaces):
        raise ValueError("Building material donor role/material identity drift")
    if sum(len(row.get("triangles", [])) for row in surfaces) != 228:
        raise ValueError("Building material donor must partition exactly 228 source triangles")
    provenance = receiving.get("provenance", {})
    if provenance.get("material_profile_sha256") != material_report.get("material_profile_sha256"):
        raise ValueError("Building material profile provenance drift")
    return receiving


def build_payload(parent: dict, material_scene: dict, material_report: dict, receiving_head: str) -> dict:
    if parent.get("schema") != PARENT_SCHEMA or parent.get("status") != PARENT_STATUS:
        raise ValueError("exact Environment PR24 parent composition must PASS first")
    if len(parent.get("states", [])) != EXPECTED_STATES:
        raise ValueError("Environment convergence requires exact 17-state parent sequence")
    donor = _validate_material_donor(material_scene, material_report)
    donor_vertices = donor["vertices_source_xyz_m"]
    donor_tris = _flatten_surfaces(donor)

    states = []
    building_mesh_digest = None
    for row in parent["states"]:
        out = copy.deepcopy(row)
        scene = out["scene"]
        current = _find_building(scene)
        if current.get("source_head") != material_report.get("building_source_head"):
            raise ValueError("current-world Building source head does not match Materials donor source head")
        if current.get("pavilion_source_sha256") != material_report.get("pavilion_source_sha256"):
            raise ValueError("current-world pavilion source digest does not match Materials donor")
        if current.get("panel_source_sha256") != material_report.get("panel_source_sha256"):
            raise ValueError("current-world panel source digest does not match Materials donor")
        if current.get("vertices_source_xyz_m") != donor_vertices:
            raise ValueError("current-world Building vertices do not exactly match Materials donor receiving geometry")
        if _tri_multiset(current.get("triangles", [])) != _tri_multiset(donor_tris):
            raise ValueError("current-world Building triangle membership does not exactly match Materials donor partition")
        this_digest = _digest({"vertices": current["vertices_source_xyz_m"], "triangles": current["triangles"]})
        if building_mesh_digest is None:
            building_mesh_digest = this_digest
        elif this_digest != building_mesh_digest:
            raise ValueError("Building geometry changed across current-world states")

        before = _strip_building_material_scene(scene)
        scene["additional_source_meshes"] = [
            copy.deepcopy(item) for item in scene.get("additional_source_meshes", [])
            if item.get("asset_id") != BUILDING_ID
        ]
        scene["environment_building_material_receiving"] = copy.deepcopy(donor)
        scene["environment_building_material_receiving"]["receiving_policy"] = "EXACT_PR14_FIVE_SURFACE_FAMILY_NO_ENVIRONMENT_RETUNE"
        scene["environment_building_material_receiving"]["map_material_donor_head"] = material_report.get("receiving_head")
        scene["environment_building_material_receiving"]["material_transfer_status"] = material_report.get("status")
        scene["environment_building_material_receiving"]["source_geometry_digest"] = building_mesh_digest
        scene["environment_building_material_receiving"]["truth_boundary"] = (
            "Environment consumes the exact already-proven Building five-surface receiving payload without changing "
            "Building geometry, source material values, placement, Weather, Nature, Object, path, cameras or lighting. "
            "This is receiving integration evidence, not final look acceptance."
        )
        scene["scene_digest"] = _scene_digest(scene)
        after = _strip_building_material_scene(scene)
        expected_before = copy.deepcopy(before)
        expected_before["additional_source_meshes"] = [
            copy.deepcopy(item) for item in before.get("additional_source_meshes", [])
            if item.get("asset_id") != BUILDING_ID
        ]
        if expected_before != after:
            raise ValueError("unrelated current-world scene state drifted while adding Building material receiving payload")
        states.append(out)

    checks = {
        "exact_parent_environment_passes_first": parent.get("status") == PARENT_STATUS,
        "exact_17_state_schedule_preserved": [r.get("time_s") for r in states] == [r.get("time_s") for r in parent["states"]],
        "weather_field_sequence_preserved": [r.get("weather_field_digest") for r in states] == [r.get("weather_field_digest") for r in parent["states"]],
        "sapling_mesh_sequence_preserved": [r.get("sapling_mesh_digest") for r in states] == [r.get("sapling_mesh_digest") for r in parent["states"]],
        "weather_variant_identity_preserved": parent.get("weather_variant_seed") == 44021,
        "object_source_identity_preserved": all(
            any(s.get("asset_id") == "source:object:modular-equipment-case-001" for s in r["scene"].get("additional_source_meshes", []))
            for r in states
        ),
        "rear_tree_identity_preserved": all(
            any(s.get("asset_id") == "source:nature:east-rear-tree-neutral-001" for s in r["scene"].get("additional_source_meshes", []))
            for r in states
        ),
        "neutral_building_source_row_removed": all(
            not any(s.get("asset_id") == BUILDING_ID for s in r["scene"].get("additional_source_meshes", []))
            for r in states
        ),
        "exact_material_receiving_present_all_states": all(
            r["scene"].get("environment_building_material_receiving", {}).get("asset_id") == BUILDING_ID
            for r in states
        ),
        "exact_five_surface_roles_preserved": all(
            [s.get("surface_role") for s in r["scene"]["environment_building_material_receiving"].get("surfaces", [])] == EXPECTED_ROLES
            for r in states
        ),
        "building_source_geometry_constant_across_states": building_mesh_digest is not None,
        "material_donor_profile_digest_preserved": donor.get("provenance", {}).get("material_profile_sha256") == material_report.get("material_profile_sha256"),
        "cameras_preserved": all(r["scene"].get("cameras") == p["scene"].get("cameras") for r,p in zip(states,parent["states"])),
        "path_preserved": all(r["scene"].get("readable_path") == p["scene"].get("readable_path") for r,p in zip(states,parent["states"])),
    }
    if not all(checks.values()):
        raise ValueError(f"Environment Building-material convergence failed checks: {checks}")

    payload = {
        "schema": SCHEMA,
        "study_id": "environment-current-world-building-material-convergence-001",
        "status": STATUS,
        "receiving_head": receiving_head,
        "parent_environment_head": parent.get("receiving_head"),
        "parent_composition_digest": parent.get("composition_digest"),
        "weather_variant_head": parent.get("weather_variant_head"),
        "weather_variant_seed": parent.get("weather_variant_seed"),
        "weather_variant_layout_digest": parent.get("weather_variant_layout_digest"),
        "object_source_head": parent.get("object_source_head"),
        "object_source_sha256": parent.get("object_source_sha256"),
        "rear_migrated_mesh_digest": parent.get("rear_migrated_mesh_digest"),
        "building_source_head": material_report.get("building_source_head"),
        "building_material_map_donor_head": material_report.get("receiving_head"),
        "building_material_head": material_report.get("building_material_head"),
        "building_material_profile_sha256": material_report.get("material_profile_sha256"),
        "building_source_geometry_digest": building_mesh_digest,
        "surface_partition_sha256": material_report.get("surface_partition_sha256"),
        "checks": checks,
        "states": states,
        "truth_boundary": (
            "PASS proves only that the exact Map PR14/Building PR3 five-surface pavilion response can replace the neutral "
            "Building proof material inside the exact PR24 17-state Weather + Nature + Object current world while geometry, "
            "placement, cameras, path and unrelated source identities remain fixed. It does not establish final Art Direction, "
            "UV/textures/weathering, target-device performance, gameplay, CANON, production readiness or Environment mastery."
        ),
        "non_claims": [
            "FINAL_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "FINAL_UV_TEXTURE_DECAL_OR_WEATHERING_QUALITY",
            "PHYSICALLY_MEASURED_BUILDING_SURFACES",
            "FINAL_LIGHTING",
            "TARGET_DEVICE_RUNTIME_BUDGET",
            "COLLISION_NAVIGATION_OR_GAMEPLAY",
            "CANON_PRODUCTION_READY_GAME_READY_OR_MASTERY",
        ],
    }
    payload["composition_digest"] = _digest({
        "parent": payload["parent_composition_digest"],
        "building_material_map_donor_head": payload["building_material_map_donor_head"],
        "building_material_head": payload["building_material_head"],
        "building_material_profile_sha256": payload["building_material_profile_sha256"],
        "building_source_geometry_digest": payload["building_source_geometry_digest"],
        "state_scene_digests": [r["scene"]["scene_digest"] for r in states],
    })
    return payload


def observer_projection(payload: dict) -> dict:
    return {
        "schema": OBSERVER_SCHEMA,
        "status": OBSERVER_STATUS,
        "receiving_head": payload["receiving_head"],
        "parent_vfx_head": payload.get("parent_environment_head"),
        "environment_donor_head": payload.get("parent_environment_head"),
        "dense_vfx_sequence_digest": payload.get("parent_composition_digest", ""),
        "weather_variant_head": payload.get("weather_variant_head"),
        "weather_variant_seed": payload.get("weather_variant_seed"),
        "weather_variant_layout_digest": payload.get("weather_variant_layout_digest"),
        "rear_migrated_mesh_digest": payload.get("rear_migrated_mesh_digest"),
        "states": copy.deepcopy(payload["states"]),
        "compatibility_projection_truth": "OBSERVER_COMPATIBILITY_ONLY_CANONICAL_ACCEPTANCE_USES_ENVIRONMENT_BUILDING_MATERIAL_CONVERGENCE_SCHEMA",
    }


def verify_target(payload: dict, runtime: dict, image_root: Path) -> dict:
    if payload.get("schema") != SCHEMA or payload.get("status") != STATUS:
        raise ValueError("canonical Building-material convergence payload must PASS structure before target verification")
    if runtime.get("state") != "PASS_CURRENT_WORLD_WEATHER_VARIANT_LIVE_OBSERVATION":
        raise ValueError("inherited live observer did not PASS")
    if runtime.get("receiving_head") != payload.get("receiving_head"):
        raise ValueError("target-host receipt head drift")
    samples = runtime.get("samples", [])
    if len(samples) != EXPECTED_STATES:
        raise ValueError("target-host must retain exact 17 samples")

    contexts = {name: [] for name in EXPECTED_CONTEXTS}
    all_material_stats_ok = True
    material_ids = None
    control_candidate_different = True
    for sample in samples:
        stats = sample.get("static_source_meshes", [])
        building = [r for r in stats if r.get("asset_id") == BUILDING_ID]
        if len(building) != 1:
            raise ValueError("target-host sample must contain exactly one Building material receiving row")
        b = building[0]
        ids = b.get("material_ids", [])
        if material_ids is None:
            material_ids = ids
        all_material_stats_ok = all_material_stats_ok and (
            b.get("surface_count") == 5 and ids == EXPECTED_ROLES and b.get("triangles") == 228 and b.get("vertices") == 152
            and b.get("material_profile_sha256") == payload.get("building_material_profile_sha256")
        )
        for context in EXPECTED_CONTEXTS:
            shot = sample.get("contexts", {}).get(context, {}).get("capture", {})
            if shot.get("state") != "PASS":
                raise ValueError(f"missing target-host capture for {context} sample {sample.get('index')}")
            p = image_root / Path(shot["path"]).name
            if not p.exists() or p.stat().st_size < 2000:
                raise ValueError(f"missing/nontrivial retained candidate image: {p}")
            contexts[context].append(hashlib.sha256(p.read_bytes()).hexdigest())
            control = image_root / f"control-{context}-{int(sample['index']):02d}.png"
            if not control.exists() or control.stat().st_size < 2000:
                raise ValueError(f"missing retained neutral control image: {control}")
            if hashlib.sha256(control.read_bytes()).hexdigest() == contexts[context][-1]:
                control_candidate_different = False

    checks = {
        "exact_receiving_head_reaches_target_host": runtime.get("receiving_head") == payload.get("receiving_head"),
        "all_17_samples_reach_target_host": len(samples) == EXPECTED_STATES,
        "building_exact_five_surface_profile_reaches_target_host": all_material_stats_ok,
        "candidate_frames_distinct_through_dynamic_sequence": all(len(set(v)) == EXPECTED_STATES for v in contexts.values()),
        "neutral_control_and_material_candidate_byte_different_all_pairs": control_candidate_different,
        "weather_variant_seed_preserved": runtime.get("weather_variant_seed") == payload.get("weather_variant_seed"),
        "weather_variant_layout_preserved": runtime.get("weather_variant_layout_digest") == payload.get("weather_variant_layout_digest"),
    }
    state = TARGET_STATUS if all(checks.values()) else "FAIL"
    return {
        "schema": "axm.environment-current-world-building-material-convergence-target-host/v0.1",
        "state": state,
        "receiving_head": payload.get("receiving_head"),
        "proof_runtime": runtime.get("proof_runtime"),
        "building_material_profile_sha256": payload.get("building_material_profile_sha256"),
        "material_ids": material_ids,
        "candidate_frame_unique_hashes": {k: len(set(v)) for k,v in contexts.items()},
        "checks": checks,
        "truth_boundary": payload.get("truth_boundary"),
        "non_claims": payload.get("non_claims"),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--parent", required=True)
    b.add_argument("--material-candidate", required=True)
    b.add_argument("--material-report", required=True)
    b.add_argument("--receiving-head", required=True)
    b.add_argument("--output", required=True)
    b.add_argument("--observer-output", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--payload", required=True)
    v.add_argument("--runtime-receipt", required=True)
    v.add_argument("--image-root", required=True)
    v.add_argument("--output", required=True)
    args = p.parse_args()

    if args.cmd == "build":
        parent = json.loads(Path(args.parent).read_text())
        material_scene = json.loads(Path(args.material_candidate).read_text())
        material_report = json.loads(Path(args.material_report).read_text())
        payload = build_payload(parent, material_scene, material_report, args.receiving_head)
        Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        Path(args.observer_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.observer_output).write_text(json.dumps(observer_projection(payload), indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps({"status": payload["status"], "composition_digest": payload["composition_digest"], "checks": payload["checks"]}, indent=2, sort_keys=True))
    else:
        payload = json.loads(Path(args.payload).read_text())
        runtime = json.loads(Path(args.runtime_receipt).read_text())
        result = verify_target(payload, runtime, Path(args.image_root))
        Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        if result["state"] != TARGET_STATUS:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
