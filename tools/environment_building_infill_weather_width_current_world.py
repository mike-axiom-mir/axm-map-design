from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

PARENT_SCHEMA = "axm.environment-current-world-building-successor-weather-width-composition/v0.1"
PARENT_STATUS = "PASS_CURRENT_WORLD_BUILDING_SUCCESSOR_WEATHER_WIDTH_STRUCTURE"
PARENT_HEAD = "0d8b2279ecbba47b9696a951db9513883fbef6c5"
PARENT_COMPOSITION_DIGEST = "132e877c8016d833f43d7a4cfe303ad2595913c757b85dd212192eafafed1973"
MATERIAL_SCHEMA = "axm.building-material-current-world-infill-repair/v0.1"
MATERIAL_STATUS = "PASS_BUILDING_CURRENT_WORLD_INFILL_REPAIR_STRUCTURE"
MATERIAL_HEAD = "225cf82a61ec1512553fda2785ca101a54a6bd30"
PREDECESSOR_PROFILE = "e8dd0c33b9b2aea108194af57a8fe8de39c7e67bb86109af6dbf3895f22c010b"
MATERIAL_PROFILE = "0c4834bf0fc9c0b7aa1a053f35f307b64596e13f305287ca3018b6182b2f6fe9"
MATERIAL_COMPOSITION_DIGEST = "e6b17071175ce950e90bd12d62792297591fa57363131acfb41cbd2c796130f0"
BUILDING_HEAD = "57f66b1245812f0c3d402232a046b86c0b5c72d8"
BUILDING_ASSET = "source:building:service-pavilion-001"
OBJECT_ASSET = "source:object:modular-equipment-case-001"
REAR_TREE_ASSET = "source:nature:east-rear-tree-neutral-001"
ROLE = "infill_coating"
ROLES = ["frame_galvanized", "infill_coating", "roof_membrane", "slab_mineral", "utility_panel_ochre"]
POLICY = "EXACT_SOURCE_OWNED_BUILDING_PLUS_INFILL_ALBEDO_SUCCESSOR_AND_SOURCE_WIDTH_WEATHER"
CONTEXTS = ("path_eye", "elevated_oblique")
WIDTH_TOLERANCE_PX = 0.05

SCHEMA = "axm.environment-current-world-building-infill-weather-width-composition/v0.1"
STATUS = "PASS_CURRENT_WORLD_BUILDING_INFILL_WEATHER_WIDTH_STRUCTURE"
TARGET_SCHEMA = "axm.environment-current-world-building-infill-weather-width-target-host/v0.1"
TARGET_STATUS = "PASS_CURRENT_WORLD_BUILDING_INFILL_WEATHER_WIDTH_TARGET_HOST"


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


def surface_map(receiving: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = receiving.get("surfaces", [])
    if [row.get("surface_role") for row in rows] != ROLES or [row.get("material_id") for row in rows] != ROLES:
        raise ValueError("Building five-surface role/material order drift")
    return {str(row["surface_role"]): row for row in rows}


def validate_parent(parent: dict[str, Any]) -> None:
    if parent.get("schema") != PARENT_SCHEMA or parent.get("status") != PARENT_STATUS:
        raise ValueError("exact Environment parent must PASS first")
    if parent.get("receiving_head") != PARENT_HEAD or parent.get("composition_digest") != PARENT_COMPOSITION_DIGEST:
        raise ValueError("Environment parent exact identity drift")
    expected_parent_digest = digest({
        "environment_parent": parent.get("environment_parent_composition_digest"),
        "vfx_width_head": parent.get("vfx_source_width_head"),
        "source_width_profile": parent.get("source_width_profile_digest"),
        "building_source_head": BUILDING_HEAD,
        "scenes": [row.get("scene", {}).get("scene_digest") for row in parent.get("states", [])],
    })
    if expected_parent_digest != PARENT_COMPOSITION_DIGEST:
        raise ValueError("Environment parent composition digest no longer reproduces")
    if parent.get("building_source_head") != BUILDING_HEAD:
        raise ValueError("Building source head drift")
    if parent.get("building_material_profile_sha256") != PREDECESSOR_PROFILE:
        raise ValueError("Environment parent material profile drift")
    if not all(parent.get("checks", {}).values()) or len(parent.get("states", [])) != 17:
        raise ValueError("Environment parent checks/state count drift")
    for row in parent["states"]:
        scene = row["scene"]
        receiving = scene.get("environment_building_material_receiving", {})
        if receiving.get("asset_id") != BUILDING_ASSET:
            raise ValueError("Environment parent missing Building")
        if receiving.get("provenance", {}).get("material_profile_sha256") != PREDECESSOR_PROFILE:
            raise ValueError("Environment parent state material provenance drift")
        if receiving.get("source_successor_rebind", {}).get("source_head") != BUILDING_HEAD:
            raise ValueError("Environment parent Building source rebind drift")
        if len(scene.get("weather_lines", [])) != 36 or not all("source_width_px" in x for x in scene.get("weather_lines", [])):
            raise ValueError("Environment parent Weather source-width binding missing")
        surface_map(receiving)


def validate_material(material: dict[str, Any]) -> dict[str, Any]:
    if material.get("schema") != MATERIAL_SCHEMA or material.get("status") != MATERIAL_STATUS:
        raise ValueError("exact Building Materials donor must PASS first")
    if material.get("receiving_head") != MATERIAL_HEAD or material.get("material_head") != MATERIAL_HEAD:
        raise ValueError("Building Materials donor exact head drift")
    if material.get("composition_digest") != MATERIAL_COMPOSITION_DIGEST:
        raise ValueError("Building Materials composition digest drift")
    if material.get("building_source_head") != BUILDING_HEAD:
        raise ValueError("Building Materials source head drift")
    if material.get("predecessor_material_profile_sha256") != PREDECESSOR_PROFILE:
        raise ValueError("Building Materials predecessor profile drift")
    if material.get("material_profile_sha256") != MATERIAL_PROFILE:
        raise ValueError("Building Materials candidate profile drift")
    if not all(material.get("checks", {}).values()):
        raise ValueError("Building Materials donor checks must PASS")
    candidate = copy.deepcopy(material.get("candidate_infill", {}))
    if candidate.get("albedo_hex") != "#59666DFF" or float(candidate.get("metallic", -1)) != 0.16 or float(candidate.get("roughness", -1)) != 0.68:
        raise ValueError("Building Materials candidate infill identity drift")
    return candidate


def build(parent: dict[str, Any], material: dict[str, Any], receiving_head: str) -> dict[str, Any]:
    validate_parent(parent)
    candidate_infill = validate_material(material)
    states: list[dict[str, Any]] = []
    changed = 0
    for parent_row in parent["states"]:
        row = copy.deepcopy(parent_row)
        scene = row["scene"]
        before = copy.deepcopy(scene)
        receiving = scene["environment_building_material_receiving"]
        surfaces = surface_map(receiving)
        old = {role: copy.deepcopy(surfaces[role]["material"]) for role in ROLES}
        if old[ROLE].get("albedo_hex") != "#344047FF" or float(old[ROLE].get("metallic", -1)) != 0.16 or float(old[ROLE].get("roughness", -1)) != 0.68:
            raise ValueError("predecessor infill identity drift")
        surfaces[ROLE]["material"] = copy.deepcopy(candidate_infill)
        changed += 1
        for role in ROLES:
            if role == ROLE:
                if surfaces[role]["material"] == old[role]:
                    raise ValueError("infill failed to change")
            elif surfaces[role]["material"] != old[role]:
                raise ValueError(f"unrelated Building surface changed: {role}")

        provenance = receiving.setdefault("provenance", {})
        provenance["material_profile_sha256"] = MATERIAL_PROFILE
        provenance["building_material_head"] = MATERIAL_HEAD
        rebind = receiving.setdefault("source_successor_rebind", {})
        rebind["material_head"] = MATERIAL_HEAD
        rebind["material_profile_sha256"] = MATERIAL_PROFILE
        receiving["receiving_policy"] = POLICY
        receiving["truth_boundary"] = (
            "Environment composes the exact Art/QA-preferred Building infill-albedo successor over the exact "
            "source-correct current world that already carries the preferred Weather source-width presentation. "
            "Only infill_coating material response changes; Building geometry, all other Building surfaces, Weather, "
            "Nature, Object, path, cameras and lighting remain fixed."
        )
        scene["schema"] = "axm.environment-current-world-building-infill-weather-width-state/v0.1"
        scene["parent_infill_environment_scene_digest"] = before.get("scene_digest", "")
        scene.pop("scene_digest", None)
        scene["scene_digest"] = scene_digest(scene)

        normalized_before = copy.deepcopy(before)
        normalized_after = copy.deepcopy(scene)
        normalized_after["schema"] = normalized_before.get("schema")
        normalized_after.pop("parent_infill_environment_scene_digest", None)
        normalized_after["scene_digest"] = normalized_before.get("scene_digest")
        a_recv = normalized_after["environment_building_material_receiving"]
        b_recv = normalized_before["environment_building_material_receiving"]
        a_surfaces = surface_map(a_recv)
        b_surfaces = surface_map(b_recv)
        a_surfaces[ROLE]["material"] = copy.deepcopy(b_surfaces[ROLE]["material"])
        a_recv["receiving_policy"] = b_recv.get("receiving_policy")
        a_recv["truth_boundary"] = b_recv.get("truth_boundary")
        for key in ("material_profile_sha256", "building_material_head"):
            a_recv.setdefault("provenance", {})[key] = b_recv.get("provenance", {}).get(key)
        for key in ("material_head", "material_profile_sha256"):
            if key in b_recv.get("source_successor_rebind", {}):
                a_recv.setdefault("source_successor_rebind", {})[key] = b_recv["source_successor_rebind"][key]
            else:
                a_recv.setdefault("source_successor_rebind", {}).pop(key, None)
        if normalized_after != normalized_before:
            raise ValueError("unrelated Environment state drift")
        states.append(row)

    checks = {
        "exact_environment_parent_passes_first": parent.get("receiving_head") == PARENT_HEAD and parent.get("composition_digest") == PARENT_COMPOSITION_DIGEST,
        "exact_building_material_donor_passes_first": material.get("receiving_head") == MATERIAL_HEAD and material.get("material_profile_sha256") == MATERIAL_PROFILE,
        "all_17_states_preserved": len(states) == 17 and changed == 17,
        "building_source_identity_preserved": all(r["scene"]["environment_building_material_receiving"].get("source_successor_rebind", {}).get("source_head") == BUILDING_HEAD for r in states),
        "only_infill_material_changed": changed == 17,
        "candidate_material_profile_bound": all(r["scene"]["environment_building_material_receiving"].get("provenance", {}).get("material_profile_sha256") == MATERIAL_PROFILE for r in states),
        "weather_source_width_fields_preserved": all(r["scene"].get("weather_lines") == p["scene"].get("weather_lines") for r, p in zip(states, parent["states"])),
        "nature_sequence_preserved": [r.get("sapling_mesh_digest") for r in states] == [r.get("sapling_mesh_digest") for r in parent["states"]],
        "object_and_static_sources_preserved": all(r["scene"].get("additional_source_meshes") == p["scene"].get("additional_source_meshes") for r, p in zip(states, parent["states"])),
        "path_preserved": all(r["scene"].get("readable_path") == p["scene"].get("readable_path") for r, p in zip(states, parent["states"])),
        "cameras_preserved": all(r["scene"].get("cameras") == p["scene"].get("cameras") for r, p in zip(states, parent["states"])),
    }
    if not all(checks.values()):
        raise ValueError(f"combined Environment checks failed: {checks}")

    out = {
        "schema": SCHEMA,
        "study_id": "environment-current-world-building-infill-weather-width-001",
        "status": STATUS,
        "receiving_head": receiving_head,
        "environment_parent_head": PARENT_HEAD,
        "environment_parent_composition_digest": PARENT_COMPOSITION_DIGEST,
        "material_head": MATERIAL_HEAD,
        "predecessor_material_profile_sha256": PREDECESSOR_PROFILE,
        "building_material_profile_sha256": MATERIAL_PROFILE,
        "building_source_head": BUILDING_HEAD,
        "building_receiving_policy": POLICY,
        "weather_variant_head": parent.get("weather_variant_head"),
        "weather_variant_seed": parent.get("weather_variant_seed"),
        "weather_variant_layout_digest": parent.get("weather_variant_layout_digest"),
        "vfx_source_width_head": parent.get("vfx_source_width_head"),
        "source_width_profile": copy.deepcopy(parent.get("source_width_profile", [])),
        "source_width_profile_digest": parent.get("source_width_profile_digest"),
        "source_width_summary": copy.deepcopy(parent.get("source_width_summary", {})),
        "checks": checks,
        "states": states,
        "truth_boundary": (
            "PASS proves only that the exact accepted Building infill-albedo successor is composed over the exact "
            "source-correct, source-width-Weather current world with every declared unrelated world input fixed. "
            "It does not itself establish combined-world Art Direction/Visual QA acceptance, target-device performance, "
            "physical material/weather correctness, gameplay, CANON, production readiness or Environment mastery."
        ),
        "non_claims": [
            "FINAL_COMBINED_WORLD_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "TARGET_DEVICE_PERFORMANCE",
            "PHYSICAL_MATERIAL_OR_WEATHER_CORRECTNESS",
            "ARBITRARY_CAMERA_OR_RESOLUTION_EQUIVALENCE",
            "COLLISION_NAVIGATION_OR_GAMEPLAY",
            "CANON_PRODUCTION_READY_GAME_READY_OR_MASTERY",
        ],
    }
    out["composition_digest"] = digest({
        "environment_parent": PARENT_COMPOSITION_DIGEST,
        "material_head": MATERIAL_HEAD,
        "material_profile": MATERIAL_PROFILE,
        "scenes": [row["scene"]["scene_digest"] for row in states],
    })
    return out


def verify(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path, parent_frame_root: str | Path) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA or payload.get("status") != STATUS or not all(payload.get("checks", {}).values()):
        raise ValueError("combined structure must PASS before target-host verification")
    from PIL import Image
    import numpy as np

    root = Path(image_root)
    parent_root = Path(parent_frame_root)
    samples = receipt.get("samples", [])
    frame_counts = {"control": {c: 0 for c in CONTEXTS}, "candidate": {c: 0 for c in CONTEXTS}}
    material_delta_pairs = {c: 0 for c in CONTEXTS}
    material_changed_counts = {c: [] for c in CONTEXTS}
    material_bboxes = {c: [] for c in CONTEXTS}
    old_luma_values = {c: [] for c in CONTEXTS}
    new_luma_values = {c: [] for c in CONTEXTS}
    max_residual = 0.0
    measured = 0
    building_ok = True
    object_ok = True
    rear_ok = True
    weather_ids: set[tuple[int, int, int]] = set()
    sapling_ids: set[tuple[int, int, int]] = set()
    counter_sets = {"control": {c: set() for c in CONTEXTS}, "candidate": {c: set() for c in CONTEXTS}}

    for sample in samples:
        sap = sample.get("sapling_update", {})
        sapling_ids.add((int(sap.get("node_instance_id", -1)), int(sap.get("mesh_instance_id", -1)), int(sap.get("material_instance_id", -1))))
        static = sample.get("static_source_meshes", [])
        buildings = [x for x in static if x.get("asset_id") == BUILDING_ASSET]
        building_ok = building_ok and len(buildings) == 1
        if buildings:
            b = buildings[0]
            building_ok = building_ok and b.get("vertices") == 152 and b.get("triangles") == 228 and b.get("surface_count") == 5 and b.get("material_ids") == ROLES and b.get("material_profile_sha256") == MATERIAL_PROFILE and b.get("receiving_policy") == POLICY
        object_ok = object_ok and sum(1 for x in static if x.get("asset_id") == OBJECT_ASSET) == 1
        rear = [x for x in static if x.get("asset_id") == REAR_TREE_ASSET]
        rear_ok = rear_ok and len(rear) == 1 and rear[0].get("proof_culling") == "CULL_BACK"
        index = int(sample.get("index", -1))
        for context in CONTEXTS:
            pair = sample.get("contexts", {}).get(context, {})
            candidate = pair.get("candidate", {})
            cw = candidate.get("weather_update", {})
            weather_ids.add((int(cw.get("node_instance_id", -1)), int(cw.get("mesh_instance_id", -1)), int(cw.get("material_instance_id", -1))))
            max_residual = max(max_residual, float(cw.get("maximum_projected_width_residual_px", 999.0)))
            measured += int(cw.get("measured_width_count", 0))
            for mode in ("control", "candidate"):
                row = pair.get(mode, {})
                capture = row.get("capture", {})
                path = root / Path(str(capture.get("path", ""))).name
                if path.exists() and path.stat().st_size > 2000:
                    frame_counts[mode][context] += 1
                stats = row.get("runtime", {})
                counter_sets[mode][context].add((int(stats.get("draw_calls_in_frame", -1)), int(stats.get("objects_in_frame", -1)), int(stats.get("primitives_in_frame", -1))))
            new_path = root / Path(str(candidate.get("capture", {}).get("path", ""))).name
            old_path = parent_root / f"atmosphere-width-candidate-{context}-{index:02d}.png"
            if new_path.exists() and old_path.exists():
                old = np.asarray(Image.open(old_path).convert("RGB"), dtype=np.int16)
                new = np.asarray(Image.open(new_path).convert("RGB"), dtype=np.int16)
                mask = np.any(old != new, axis=2)
                count = int(mask.sum())
                if count > 0:
                    material_delta_pairs[context] += 1
                    ys, xs = np.where(mask)
                    material_changed_counts[context].append(count)
                    material_bboxes[context].append([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())])
                    old_luma = 0.2126 * old[:, :, 0] + 0.7152 * old[:, :, 1] + 0.0722 * old[:, :, 2]
                    new_luma = 0.2126 * new[:, :, 0] + 0.7152 * new[:, :, 1] + 0.0722 * new[:, :, 2]
                    old_luma_values[context].append(old_luma[mask])
                    new_luma_values[context].append(new_luma[mask])

    checks = {
        "structure_passes_before_target_host": payload.get("status") == STATUS and all(payload.get("checks", {}).values()),
        "exact_receiving_head_reaches_target_host": receipt.get("receiving_head") == payload.get("receiving_head"),
        "all_17_live_samples_retained": len(samples) == 17,
        "all_68_thinline_sourcewidth_frames_retained": all(frame_counts[m][c] == 17 for m in frame_counts for c in CONTEXTS),
        "all_1224_projected_width_measurements_within_tolerance": measured == 17 * 2 * 36 and max_residual <= WIDTH_TOLERANCE_PX,
        "all_34_sourcewidth_material_successor_frames_differ_from_exact_parent": all(material_delta_pairs[c] == 17 for c in CONTEXTS),
        "building_material_successor_reaches_target_host": building_ok,
        "object_source_identity_reaches_target_host": object_ok,
        "rear_nature_identity_and_culling_reach_target_host": rear_ok,
        "one_weather_resource_identity_stable": len(weather_ids) == 1 and next(iter(weather_ids), (-1, -1, -1))[0] > 0,
        "one_sapling_resource_identity_stable": len(sapling_ids) == 1 and next(iter(sapling_ids), (-1, -1, -1))[0] > 0,
        "runtime_counter_sets_stable_per_camera": all(len(counter_sets[m][c]) == 1 for m in counter_sets for c in CONTEXTS),
    }
    result = {
        "schema": TARGET_SCHEMA,
        "state": TARGET_STATUS if all(checks.values()) else "FAIL",
        "receiving_head": payload.get("receiving_head"),
        "composition_digest": payload.get("composition_digest"),
        "environment_parent_head": PARENT_HEAD,
        "material_head": MATERIAL_HEAD,
        "building_source_head": BUILDING_HEAD,
        "material_profile_sha256": MATERIAL_PROFILE,
        "checks": checks,
        "maximum_projected_width_residual_px": max_residual,
        "measured_width_count": measured,
        "frame_counts": frame_counts,
        "material_delta_pair_counts": material_delta_pairs,
        "material_changed_pixel_counts": {c: {"min": min(v) if v else 0, "max": max(v) if v else 0, "unique": sorted(set(v))} for c, v in material_changed_counts.items()},
        "material_bbox_unique": {c: sorted({tuple(x) for x in v}) for c, v in material_bboxes.items()},
        "material_luma_diagnostics": {
            c: ({
                "predecessor_changed_pixel_median_luma": float(np.median(np.concatenate(old_luma_values[c]))),
                "successor_changed_pixel_median_luma": float(np.median(np.concatenate(new_luma_values[c]))),
                "predecessor_changed_pixel_below_32_fraction": float(np.mean(np.concatenate(old_luma_values[c]) < 32.0)),
                "successor_changed_pixel_below_32_fraction": float(np.mean(np.concatenate(new_luma_values[c]) < 32.0)),
            } if old_luma_values[c] else {}) for c in CONTEXTS
        },
        "runtime_counter_sets": {m: {c: sorted(counter_sets[m][c]) for c in CONTEXTS} for m in counter_sets},
        "truth_boundary": (
            "Target-host PASS proves only that Godot 4.7.2 GL Compatibility consumed the exact Building infill successor "
            "inside the exact source-width Weather current world, retained the full bounded observation set and kept the "
            "source-width projection within the inherited tolerance. It does not establish final visual acceptance, "
            "target-device performance, arbitrary camera equivalence, gameplay, CANON or production readiness."
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    bp = sub.add_parser("build")
    bp.add_argument("--environment", required=True)
    bp.add_argument("--material", required=True)
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
        result = build(load_json(args.environment), load_json(args.material), args.receiving_head)
    else:
        result = verify(load_json(args.payload), load_json(args.receipt), args.image_root, args.parent_frame_root)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
