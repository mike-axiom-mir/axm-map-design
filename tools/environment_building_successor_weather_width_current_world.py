from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ENV_SCHEMA = "axm.environment-current-world-building-source-successor-evidence/v0.1"
ENV_STATUS = "PASS_CURRENT_WORLD_BUILDING_SOURCE_SUCCESSOR_STRUCTURE"
ENV_HEAD = "43d89a7cac48e57ebede0db8fc9983e8144222a0"
ENV_COMPOSITION_DIGEST = "f1507e8969a0343bcabad3078136a29f99d670b9261750e001f0ed500b4c8f6d"
VFX_SCHEMA = "axm.environment-current-world-weather-width-evidence/v0.1"
VFX_STATUS = "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE"
VFX_HEAD = "15a03b7c3ba3aaa7c0475ca1a3091c15581f559b"
PARENT_VARIANT_HEAD = "e482d003853e52fc835f1797ddfb6506a50083ef"
WEATHER_HEAD = "05b26c4e82bbe0a4de0ee7bee34179efc58b9719"
WEATHER_SEED = 44021
WEATHER_LAYOUT = "7ed55e93ea9445345016685320716006bc52960b33784cb620ca5670a74cc26f"
BUILDING_HEAD = "57f66b1245812f0c3d402232a046b86c0b5c72d8"
BUILDING_POLICY = "EXACT_SOURCE_OWNED_CLOSED_OUTWARD_TOPOLOGY_REBIND_NO_MATERIAL_RETUNE"
MATERIAL_PROFILE = "e8dd0c33b9b2aea108194af57a8fe8de39c7e67bb86109af6dbf3895f22c010b"
BUILDING_ASSET = "source:building:service-pavilion-001"
OBJECT_ASSET = "source:object:modular-equipment-case-001"
REAR_TREE_ASSET = "source:nature:east-rear-tree-neutral-001"
ROLES = ["frame_galvanized", "infill_coating", "roof_membrane", "slab_mineral", "utility_panel_ochre"]
CONTEXTS = ("path_eye", "elevated_oblique")
WIDTH_TOLERANCE_PX = 0.05

SCHEMA = "axm.environment-current-world-building-successor-weather-width-composition/v0.1"
STATUS = "PASS_CURRENT_WORLD_BUILDING_SUCCESSOR_WEATHER_WIDTH_STRUCTURE"
TARGET_SCHEMA = "axm.environment-current-world-building-successor-weather-width-target-host/v0.1"
TARGET_STATUS = "PASS_CURRENT_WORLD_BUILDING_SUCCESSOR_WEATHER_WIDTH_TARGET_HOST"


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def scene_digest(scene: dict[str, Any]) -> str:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    return digest(value)


def material_rows(scene: dict[str, Any]) -> list[dict[str, Any]]:
    receiving = scene.get("environment_building_material_receiving", {})
    rows = receiving.get("surfaces", [])
    if [row.get("surface_role") for row in rows] != ROLES:
        raise ValueError("Building five-surface role order drift")
    if [row.get("material_id") for row in rows] != ROLES:
        raise ValueError("Building material identity drift")
    return rows


def validate_environment_parent(env: dict[str, Any]) -> None:
    if env.get("schema") != ENV_SCHEMA or env.get("status") != ENV_STATUS:
        raise ValueError("Environment source-successor parent must PASS exactly")
    if env.get("receiving_head") != ENV_HEAD or env.get("composition_digest") != ENV_COMPOSITION_DIGEST:
        raise ValueError("Environment source-successor exact identity drift")
    if env.get("building_source_head") != BUILDING_HEAD:
        raise ValueError("Building source successor head drift")
    if env.get("building_material_profile_sha256") != MATERIAL_PROFILE:
        raise ValueError("Building material profile drift")
    if env.get("weather_variant_head") != WEATHER_HEAD or int(env.get("weather_variant_seed", -1)) != WEATHER_SEED:
        raise ValueError("Environment Weather source identity drift")
    if env.get("weather_variant_layout_digest") != WEATHER_LAYOUT:
        raise ValueError("Environment Weather layout drift")
    if len(env.get("states", [])) != 17:
        raise ValueError("Environment parent must retain 17 states")

    first_material_digest = None
    for row in env["states"]:
        scene = row["scene"]
        receiving = scene.get("environment_building_material_receiving", {})
        if receiving.get("asset_id") != BUILDING_ASSET:
            raise ValueError("Environment parent missing exact Building receiving asset")
        if receiving.get("receiving_policy") != BUILDING_POLICY:
            raise ValueError("Environment parent Building receiving policy drift")
        rebind = receiving.get("source_successor_rebind", {})
        if rebind.get("source_head") != BUILDING_HEAD:
            raise ValueError("Environment parent Building successor provenance drift")
        if receiving.get("provenance", {}).get("material_profile_sha256") != MATERIAL_PROFILE:
            raise ValueError("Environment parent material provenance drift")
        mats = [{"role": r["surface_role"], "material": r["material"]} for r in material_rows(scene)]
        current = digest(mats)
        first_material_digest = current if first_material_digest is None else first_material_digest
        if current != first_material_digest:
            raise ValueError("Building materials must remain static across environment states")


def validate_vfx_donor(vfx: dict[str, Any]) -> None:
    if vfx.get("schema") != VFX_SCHEMA or vfx.get("status") != VFX_STATUS:
        raise ValueError("VFX source-width donor must PASS exactly")
    if vfx.get("receiving_head") != VFX_HEAD:
        raise ValueError("VFX source-width exact head drift")
    if vfx.get("parent_variant_head") != PARENT_VARIANT_HEAD:
        raise ValueError("VFX parent Weather-variant identity drift")
    if vfx.get("weather_variant_head") != WEATHER_HEAD or int(vfx.get("weather_variant_seed", -1)) != WEATHER_SEED:
        raise ValueError("VFX Weather source identity drift")
    if vfx.get("weather_variant_layout_digest") != WEATHER_LAYOUT:
        raise ValueError("VFX Weather layout drift")
    if len(vfx.get("states", [])) != 17:
        raise ValueError("VFX donor must retain 17 states")
    profile = vfx.get("source_width_profile", [])
    if len(profile) != 36 or len({row.get("id") for row in profile}) != 36:
        raise ValueError("VFX donor must retain 36 unique source widths")
    widths = [float(row.get("width_px", -1.0)) for row in profile]
    if min(widths) < 1.0 or max(widths) > 2.4 or len({round(v, 12) for v in widths}) <= 1:
        raise ValueError("VFX donor source-width profile drift")


def build(env: dict[str, Any], vfx: dict[str, Any], receiving_head: str) -> dict[str, Any]:
    validate_environment_parent(env)
    validate_vfx_donor(vfx)

    states: list[dict[str, Any]] = []
    width_profile = {str(row["id"]): float(row["width_px"]) for row in vfx["source_width_profile"]}
    exact_line_match = True
    building_identity_exact = True
    object_identity_exact = True
    rear_tree_identity_exact = True
    unrelated_environment_state_preserved = True

    for env_row, vfx_row in zip(env["states"], vfx["states"]):
        if (env_row.get("index"), env_row.get("time_s"), env_row.get("weather_field_digest"), env_row.get("sapling_mesh_digest")) != (
            vfx_row.get("index"), vfx_row.get("time_s"), vfx_row.get("weather_field_digest"), vfx_row.get("sapling_mesh_digest")
        ):
            raise ValueError("Environment/VFX retained state schedule drift")

        out_row = copy.deepcopy(env_row)
        scene = out_row["scene"]
        env_lines = scene.get("weather_lines", [])
        donor_lines = vfx_row.get("scene", {}).get("weather_lines", [])
        if len(env_lines) != 36 or len(donor_lines) != 36:
            raise ValueError("Weather streak count drift")
        new_lines = []
        for base_line, donor_line in zip(env_lines, donor_lines):
            donor_without_width = {k: copy.deepcopy(v) for k, v in donor_line.items() if k != "source_width_px"}
            exact_line_match = exact_line_match and donor_without_width == base_line
            streak_id = str(base_line.get("id", ""))
            if streak_id not in width_profile or str(donor_line.get("id", "")) != streak_id:
                raise ValueError("Weather streak identity/order drift")
            if float(donor_line.get("source_width_px", -1.0)) != width_profile[streak_id]:
                raise ValueError("Weather source width drift inside VFX donor")
            new_line = copy.deepcopy(base_line)
            new_line["source_width_px"] = width_profile[streak_id]
            new_lines.append(new_line)

        before = copy.deepcopy(scene)
        scene["schema"] = "axm.environment-current-world-building-successor-weather-width-state/v0.1"
        scene["weather_lines"] = new_lines
        scene["weather_width_binding"] = copy.deepcopy(vfx_row["scene"].get("weather_width_binding", {}))
        scene["weather_width_binding"]["vfx_receiving_head"] = VFX_HEAD
        scene["weather_width_binding"]["environment_parent_head"] = ENV_HEAD
        scene["parent_environment_scene_digest"] = before.get("scene_digest", "")
        scene.pop("scene_digest", None)
        scene["scene_digest"] = scene_digest(scene)
        out_row["scene"] = scene
        out_row["weather_width_profile_digest"] = vfx_row.get("weather_width_profile_digest")

        check_before = copy.deepcopy(before)
        check_after = copy.deepcopy(scene)
        check_after.pop("weather_width_binding", None)
        check_after.pop("parent_environment_scene_digest", None)
        check_after["schema"] = check_before.get("schema")
        check_after["weather_lines"] = [{k: copy.deepcopy(v) for k, v in line.items() if k != "source_width_px"} for line in check_after.get("weather_lines", [])]
        check_after["scene_digest"] = check_before.get("scene_digest")
        unrelated_environment_state_preserved = unrelated_environment_state_preserved and check_after == check_before

        receiving = scene.get("environment_building_material_receiving", {})
        building_identity_exact = building_identity_exact and receiving.get("asset_id") == BUILDING_ASSET and receiving.get("receiving_policy") == BUILDING_POLICY and receiving.get("source_successor_rebind", {}).get("source_head") == BUILDING_HEAD
        additional = scene.get("additional_source_meshes", [])
        object_identity_exact = object_identity_exact and sum(1 for x in additional if x.get("asset_id") == OBJECT_ASSET) == 1
        rear_tree_identity_exact = rear_tree_identity_exact and sum(1 for x in additional if x.get("asset_id") == REAR_TREE_ASSET) == 1
        states.append(out_row)

    checks = {
        "exact_environment_source_successor_parent": env.get("receiving_head") == ENV_HEAD and env.get("composition_digest") == ENV_COMPOSITION_DIGEST,
        "exact_vfx_source_width_donor": vfx.get("receiving_head") == VFX_HEAD,
        "weather_source_identity_shared": env.get("weather_variant_head") == vfx.get("weather_variant_head") == WEATHER_HEAD and env.get("weather_variant_layout_digest") == vfx.get("weather_variant_layout_digest") == WEATHER_LAYOUT,
        "all_17_state_schedules_match": len(states) == 17,
        "all_36_source_widths_match_exact_weather_lines": exact_line_match and all(len(row["scene"].get("weather_lines", [])) == 36 for row in states),
        "unrelated_environment_state_preserved": unrelated_environment_state_preserved,
        "building_successor_identity_preserved": building_identity_exact,
        "building_material_profile_preserved": all(row["scene"]["environment_building_material_receiving"].get("provenance", {}).get("material_profile_sha256") == MATERIAL_PROFILE for row in states),
        "object_source_identity_preserved": object_identity_exact,
        "rear_tree_identity_preserved": rear_tree_identity_exact,
        "cameras_preserved": all(a["scene"].get("cameras") == b["scene"].get("cameras") for a, b in zip(states, env["states"])),
        "path_preserved": all(a["scene"].get("readable_path") == b["scene"].get("readable_path") for a, b in zip(states, env["states"])),
    }
    if not all(checks.values()):
        raise ValueError(f"combined environment checks failed: {checks}")

    out = {
        "schema": SCHEMA,
        "study_id": "environment-current-world-building-successor-weather-source-width-001",
        "status": STATUS,
        "receiving_head": receiving_head,
        "environment_parent_head": ENV_HEAD,
        "environment_parent_composition_digest": ENV_COMPOSITION_DIGEST,
        "vfx_source_width_head": VFX_HEAD,
        "parent_variant_head": PARENT_VARIANT_HEAD,
        "weather_variant_head": WEATHER_HEAD,
        "weather_variant_seed": WEATHER_SEED,
        "weather_variant_layout_digest": WEATHER_LAYOUT,
        "source_width_profile": copy.deepcopy(vfx["source_width_profile"]),
        "source_width_profile_digest": vfx.get("source_width_profile_digest"),
        "source_width_summary": copy.deepcopy(vfx.get("source_width_summary", {})),
        "building_source_head": BUILDING_HEAD,
        "building_material_profile_sha256": MATERIAL_PROFILE,
        "building_receiving_policy": BUILDING_POLICY,
        "checks": checks,
        "states": states,
        "truth_boundary": "PASS proves only that the exact Art/QA-preferred Weather source-width presentation can be composed over the exact Environment source-successor current world while Building source/material identity, Object, Nature, path, cameras, lighting and the 17-state Weather/sapling schedule remain fixed. It does not repair the held Building infill hierarchy failure, prove arbitrary-camera Weather width fidelity, target-device performance, gameplay, CANON, production readiness or Environment mastery.",
        "non_claims": [
            "BUILDING_INFILL_VISUAL_HIERARCHY_REPAIRED_OR_ACCEPTED",
            "ARBITRARY_CAMERA_OR_RESOLUTION_WEATHER_WIDTH_FIDELITY",
            "TARGET_DEVICE_PERFORMANCE",
            "COLLISION_NAVIGATION_OR_GAMEPLAY",
            "CANON_PRODUCTION_READY_GAME_READY_OR_MASTERY",
        ],
    }
    out["composition_digest"] = digest({
        "environment_parent": ENV_COMPOSITION_DIGEST,
        "vfx_width_head": VFX_HEAD,
        "source_width_profile": out["source_width_profile_digest"],
        "building_source_head": BUILDING_HEAD,
        "scenes": [row["scene"]["scene_digest"] for row in states],
    })
    return out


def verify(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path, parent_frame_root: str | Path) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA or payload.get("status") != STATUS or not all(payload.get("checks", {}).values()):
        raise ValueError("combined structural proof must PASS before target-host verification")
    root = Path(image_root)
    parent_root = Path(parent_frame_root)
    samples = receipt.get("samples", [])
    frame_counts = {"control": {c: 0 for c in CONTEXTS}, "candidate": {c: 0 for c in CONTEXTS}}
    changed_pairs = {c: 0 for c in CONTEXTS}
    exact_parent_control_matches = {c: 0 for c in CONTEXTS}
    counter_sets = {"control": {c: set() for c in CONTEXTS}, "candidate": {c: set() for c in CONTEXTS}}
    weather_ids: set[tuple[int, int, int]] = set()
    sapling_ids: set[tuple[int, int, int]] = set()
    max_residual = 0.0
    measured = 0
    clipped = 0
    clip_ids: dict[str, int] = {}
    building_ok = True
    object_ok = True
    rear_ok = True

    for sample in samples:
        sap = sample.get("sapling_update", {})
        sapling_ids.add((int(sap.get("node_instance_id", -1)), int(sap.get("mesh_instance_id", -1)), int(sap.get("material_instance_id", -1))))
        static = sample.get("static_source_meshes", [])
        buildings = [x for x in static if x.get("asset_id") == BUILDING_ASSET]
        building_ok = building_ok and len(buildings) == 1
        if buildings:
            b = buildings[0]
            building_ok = building_ok and b.get("vertices") == 152 and b.get("triangles") == 228 and b.get("surface_count") == 5 and b.get("material_ids") == ROLES and b.get("material_profile_sha256") == MATERIAL_PROFILE and b.get("receiving_policy") == BUILDING_POLICY
        object_ok = object_ok and sum(1 for x in static if x.get("asset_id") == OBJECT_ASSET) == 1
        rear_rows = [x for x in static if x.get("asset_id") == REAR_TREE_ASSET]
        rear_ok = rear_ok and len(rear_rows) == 1 and rear_rows[0].get("proof_culling") == "CULL_BACK"

        index = int(sample.get("index", -1))
        for context in CONTEXTS:
            pair = sample.get("contexts", {}).get(context, {})
            control = pair.get("control", {})
            candidate = pair.get("candidate", {})
            cw = candidate.get("weather_update", {})
            weather_ids.add((int(cw.get("node_instance_id", -1)), int(cw.get("mesh_instance_id", -1)), int(cw.get("material_instance_id", -1))))
            max_residual = max(max_residual, float(cw.get("maximum_projected_width_residual_px", 999.0)))
            measured += int(cw.get("measured_width_count", 0))
            clipped += int(cw.get("near_clipped_endpoint_count", 0))
            for sid in cw.get("near_clipped_streak_ids", []):
                clip_ids[str(sid)] = clip_ids.get(str(sid), 0) + 1

            paths = {}
            for mode, row in (("control", control), ("candidate", candidate)):
                capture = row.get("capture", {})
                path = root / Path(str(capture.get("path", ""))).name
                paths[mode] = path
                if path.exists() and path.stat().st_size > 2000:
                    frame_counts[mode][context] += 1
                stats = row.get("runtime", {})
                counter_sets[mode][context].add((int(stats.get("draw_calls_in_frame", -1)), int(stats.get("objects_in_frame", -1)), int(stats.get("primitives_in_frame", -1))))
            if all(path.exists() for path in paths.values()):
                if hashlib.sha256(paths["control"].read_bytes()).digest() != hashlib.sha256(paths["candidate"].read_bytes()).digest():
                    changed_pairs[context] += 1
                historical = parent_root / f"building-material-{context}-{index:02d}.png"
                if historical.exists() and hashlib.sha256(historical.read_bytes()).digest() == hashlib.sha256(paths["control"].read_bytes()).digest():
                    exact_parent_control_matches[context] += 1

    checks = {
        "structure_passes_before_target_host": payload.get("status") == STATUS and all(payload.get("checks", {}).values()),
        "exact_receiving_head_reaches_target_host": receipt.get("receiving_head") == payload.get("receiving_head"),
        "all_17_live_samples_retained": len(samples) == 17,
        "all_68_control_candidate_frames_retained": all(frame_counts[m][c] == 17 for m in frame_counts for c in CONTEXTS),
        "all_34_width_pairs_visibly_different_by_bytes": all(changed_pairs[c] == 17 for c in CONTEXTS),
        "all_34_control_frames_match_exact_environment_parent": all(exact_parent_control_matches[c] == 17 for c in CONTEXTS),
        "all_1224_projected_width_measurements_within_tolerance": measured == 17 * 2 * 36 and max_residual <= WIDTH_TOLERANCE_PX,
        "one_weather_resource_identity_stable": len(weather_ids) == 1 and next(iter(weather_ids), (-1, -1, -1))[0] > 0,
        "one_sapling_resource_identity_stable": len(sapling_ids) == 1 and next(iter(sapling_ids), (-1, -1, -1))[0] > 0,
        "building_source_successor_reaches_target_host": building_ok,
        "object_source_identity_reaches_target_host": object_ok,
        "rear_nature_identity_and_culling_reach_target_host": rear_ok,
        "control_counter_sets_stable_per_camera": all(len(counter_sets["control"][c]) == 1 for c in CONTEXTS),
        "candidate_counter_sets_stable_per_camera": all(len(counter_sets["candidate"][c]) == 1 for c in CONTEXTS),
    }
    result = {
        "schema": TARGET_SCHEMA,
        "state": TARGET_STATUS if all(checks.values()) else "FAIL",
        "receiving_head": payload.get("receiving_head"),
        "composition_digest": payload.get("composition_digest"),
        "environment_parent_head": ENV_HEAD,
        "vfx_source_width_head": VFX_HEAD,
        "building_source_head": BUILDING_HEAD,
        "checks": checks,
        "maximum_projected_width_residual_px": max_residual,
        "measured_width_count": measured,
        "near_clipped_endpoint_count": clipped,
        "near_clipped_streak_ids": clip_ids,
        "frame_counts": frame_counts,
        "changed_pair_counts": changed_pairs,
        "exact_parent_control_match_counts": exact_parent_control_matches,
        "control_runtime_counter_sets": {c: sorted(counter_sets["control"][c]) for c in CONTEXTS},
        "candidate_runtime_counter_sets": {c: sorted(counter_sets["candidate"][c]) for c in CONTEXTS},
        "truth_boundary": "Target-host PASS proves only that Godot 4.7.2 GL Compatibility reproduced the exact Environment source-successor world as the thin-line control and then carried the exact source-authored Weather width profile over that same Building/Nature/Object/path/camera composition. It does not establish final atmosphere, repair the held Building infill hierarchy failure, arbitrary-camera correctness, target-device runtime budgets, gameplay, CANON or mastery.",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    bp = sub.add_parser("build")
    bp.add_argument("--environment", required=True)
    bp.add_argument("--vfx", required=True)
    bp.add_argument("--receiving-head", required=True)
    bp.add_argument("--output", required=True)
    vp = sub.add_parser("verify")
    vp.add_argument("--payload", required=True)
    vp.add_argument("--receipt", required=True)
    vp.add_argument("--image-root", required=True)
    vp.add_argument("--parent-frame-root", required=True)
    vp.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.command == "build":
        result = build(load_json(args.environment), load_json(args.vfx), args.receiving_head)
    else:
        result = verify(load_json(args.payload), load_json(args.receipt), args.image_root, args.parent_frame_root)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
