from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

PARENT_SCHEMA = "axm.environment-current-world-building-infill-weather-width-composition/v0.1"
PARENT_STATUS = "PASS_CURRENT_WORLD_BUILDING_INFILL_WEATHER_WIDTH_STRUCTURE"
PARENT_HEAD = "5b9b55ec67e31655f51d1acc67284816067e5be6"
PARENT_COMPOSITION_DIGEST = "e6cea4098c4946dcfa80573d3e30d6d07a1e7c7b4c037b5962eeb3105ac8dfe1"
OBJECT_ASSET = "source:object:modular-equipment-case-001"
OBJECT_SOURCE_HEAD = "d3fa10a270faae7925811f44f03381fe5c5d0215"
OBJECT_SOURCE_SHA256 = "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
OBJECT_OBJ_SHA256 = "3e01ef3bf4935ee6aee7c56c03dc0b7f54c308e5ac2eb6a7583252a366901106"
TARGET_PROXY = "proxy:object-crate-west"
RESERVED_POSITION = [-3.458072, 4.303392, 0.567315]
RESERVED_SIZE = [1.13463, 1.13463, 1.13463]
RESERVED_FOOTPRINT = [-4.025387, -2.890757, 3.736077, 4.8707069999999995]
OBJECT_FOOTPRINT = [-3.9146410265823866, -3.0015029734176135, 3.984236328921255, 4.6225476710787445]
OBJECT_BOUNDS_MIN = [-3.9146410265823866, 3.984236328921255, 0.0]
OBJECT_BOUNDS_MAX = [-3.0015029734176135, 4.6225476710787445, 0.422]
DRESSING_ASSET = "environment:dressing:west-object-service-footprint-frame-001"
STRIP_WIDTH_M = 0.045
FRAME_HEIGHT_M = 0.02
FRAME_ALBEDO = [0.16, 0.19, 0.21, 1.0]
FRAME_METALLIC = 0.0
FRAME_ROUGHNESS = 0.9
MIN_OBJECT_TO_FRAME_CLEARANCE_M = 0.06
MIN_PATH_SEPARATION_M = 1.0

SCHEMA = "axm.environment-current-world-object-readability-dressing-composition/v0.1"
STATUS = "PASS_CURRENT_WORLD_OBJECT_READABILITY_DRESSING_STRUCTURE"
TARGET_SCHEMA = "axm.environment-current-world-object-readability-dressing-target-host/v0.1"
TARGET_STATUS = "PASS_CURRENT_WORLD_OBJECT_READABILITY_DRESSING_TARGET_HOST"
CONTEXTS = ("path_eye", "elevated_oblique")
MODES = ("control", "candidate")


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


def _almost_list(actual: Any, expected: list[float], eps: float = 1e-9) -> bool:
    return isinstance(actual, list) and len(actual) == len(expected) and all(abs(float(a) - float(b)) <= eps for a, b in zip(actual, expected))


def _object_source(scene: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in scene.get("additional_source_meshes", []) if row.get("asset_id") == OBJECT_ASSET]
    if len(rows) != 1:
        raise ValueError("exact current world must contain one Object source")
    row = rows[0]
    if row.get("source_head") != OBJECT_SOURCE_HEAD or row.get("source_sha256") != OBJECT_SOURCE_SHA256 or row.get("obj_sha256") != OBJECT_OBJ_SHA256:
        raise ValueError("Object source identity drift")
    verts = row.get("vertices_source_xyz_m", [])
    if len(verts) != 468 or len(row.get("triangles", [])) != 812:
        raise ValueError("Object source structural count drift")
    mins = [min(float(v[i]) for v in verts) for i in range(3)]
    maxs = [max(float(v[i]) for v in verts) for i in range(3)]
    if not _almost_list(mins, OBJECT_BOUNDS_MIN) or not _almost_list(maxs, OBJECT_BOUNDS_MAX):
        raise ValueError(f"Object source world bounds drift: {mins} / {maxs}")
    return row


def validate_parent(parent: dict[str, Any]) -> dict[str, float]:
    if parent.get("schema") != PARENT_SCHEMA or parent.get("status") != PARENT_STATUS:
        raise ValueError("exact Environment parent must PASS first")
    if parent.get("receiving_head") != PARENT_HEAD or parent.get("composition_digest") != PARENT_COMPOSITION_DIGEST:
        raise ValueError("Environment parent exact identity drift")
    if len(parent.get("states", [])) != 17 or not all(parent.get("checks", {}).values()):
        raise ValueError("Environment parent state/check drift")

    min_frame_clearance = float("inf")
    path_separation = float("inf")
    building_separation = float("inf")
    for row in parent["states"]:
        scene = row["scene"]
        _object_source(scene)
        repl = scene.get("environment_object_replacement", {})
        if repl.get("source_asset_id") != OBJECT_ASSET or repl.get("target_asset_id") != TARGET_PROXY:
            raise ValueError("Object receiver identity drift")
        if not _almost_list(repl.get("reserved_proxy_position_m"), RESERVED_POSITION):
            raise ValueError("Object receiver position drift")
        if not _almost_list(repl.get("reserved_proxy_size_m"), RESERVED_SIZE):
            raise ValueError("Object receiver size drift")
        if not _almost_list(repl.get("reserved_proxy_footprint_m"), RESERVED_FOOTPRINT):
            raise ValueError("Object receiver reserved footprint drift")
        if not _almost_list(repl.get("source_world_footprint_m"), OBJECT_FOOTPRINT):
            raise ValueError("Object source footprint drift")

        xmin, xmax, ymin, ymax = RESERVED_FOOTPRINT
        oxmin, oxmax, oymin, oymax = OBJECT_FOOTPRINT
        inner = [xmin + STRIP_WIDTH_M, xmax - STRIP_WIDTH_M, ymin + STRIP_WIDTH_M, ymax - STRIP_WIDTH_M]
        clearances = [oxmin - inner[0], inner[1] - oxmax, oymin - inner[2], inner[3] - oymax]
        min_frame_clearance = min(min_frame_clearance, *clearances)
        if min(clearances) < MIN_OBJECT_TO_FRAME_CLEARANCE_M:
            raise ValueError(f"service-footprint frame would overlap/crowd exact Object source: {clearances}")

        path = scene.get("readable_path", {})
        x_sep = float(path.get("x_min", 0.0)) - xmax
        path_separation = min(path_separation, x_sep)
        if x_sep < MIN_PATH_SEPARATION_M:
            raise ValueError(f"service-footprint frame intrudes too close to readable path: {x_sep}")

        receiving = scene.get("environment_building_material_receiving", {})
        bverts = receiving.get("vertices_source_xyz_m", [])
        if len(bverts) != 152:
            raise ValueError("Building receiving identity drift")
        bmin_y = min(float(v[1]) for v in bverts)
        building_separation = min(building_separation, bmin_y - ymax)
        if bmin_y - ymax <= 0.0:
            raise ValueError("service-footprint frame overlaps Building footprint in source Y")
    return {
        "minimum_object_to_frame_clearance_m": min_frame_clearance,
        "minimum_readable_path_separation_m": path_separation,
        "minimum_building_y_separation_m": building_separation,
    }


def dressing_contract() -> dict[str, Any]:
    xmin, xmax, ymin, ymax = RESERVED_FOOTPRINT
    return {
        "schema": "axm.environment-object-service-footprint-frame/v0.1",
        "asset_id": DRESSING_ASSET,
        "role": "ENVIRONMENT_OWNED_RECEIVER_FOOTPRINT_READABILITY_CUE",
        "source_object_asset_id": OBJECT_ASSET,
        "source_object_head": OBJECT_SOURCE_HEAD,
        "source_object_sha256": OBJECT_SOURCE_SHA256,
        "historical_receiver_proxy_asset_id": TARGET_PROXY,
        "derived_from": "EXACT_EXISTING_RESERVED_WEST_OBJECT_PROXY_FOOTPRINT_NOT_OBJECT_RESCALE",
        "outer_footprint_source_xy_m": [xmin, xmax, ymin, ymax],
        "center_source_xyz_m": [(xmin + xmax) * 0.5, (ymin + ymax) * 0.5, FRAME_HEIGHT_M * 0.5],
        "outer_size_source_xyz_m": [xmax - xmin, ymax - ymin, FRAME_HEIGHT_M],
        "strip_width_m": STRIP_WIDTH_M,
        "frame_height_m": FRAME_HEIGHT_M,
        "material": {
            "albedo": FRAME_ALBEDO,
            "metallic": FRAME_METALLIC,
            "roughness": FRAME_ROUGHNESS,
            "texture": None,
        },
        "geometry_policy": "ONE_STATIC_48_TRIANGLE_FRAME_MESH_FOUR_BARS_INSIDE_EXACT_RESERVED_FOOTPRINT",
        "source_object_transform_policy": "UNCHANGED_NO_SCALE_NO_REPOSITION_NO_ROTATION_CHANGE",
        "gameplay_collision_policy": "VISUAL_DRESSING_ONLY_NO_COLLISION_OR_NAVIGATION_AUTHORITY",
        "truth_boundary": (
            "This frame is Map Environment dressing derived only from the already-accepted reserved receiver footprint. "
            "It does not alter Object source scale/geometry/materials, imply a physical mount, or create gameplay collision."
        ),
    }


def build(parent: dict[str, Any], receiving_head: str) -> dict[str, Any]:
    metrics = validate_parent(parent)
    contract = dressing_contract()
    states: list[dict[str, Any]] = []
    for parent_row in parent["states"]:
        row = copy.deepcopy(parent_row)
        scene = row["scene"]
        before = copy.deepcopy(scene)
        if "environment_object_readability_dressing" in scene:
            raise ValueError("parent already contains Object readability dressing")
        scene["environment_object_readability_dressing"] = copy.deepcopy(contract)
        scene["schema"] = "axm.environment-current-world-object-readability-dressing-state/v0.1"
        scene["parent_object_readability_scene_digest"] = before.get("scene_digest", "")
        scene.pop("scene_digest", None)
        scene["scene_digest"] = scene_digest(scene)

        normalized = copy.deepcopy(scene)
        normalized.pop("environment_object_readability_dressing", None)
        normalized["schema"] = before.get("schema")
        normalized.pop("parent_object_readability_scene_digest", None)
        normalized["scene_digest"] = before.get("scene_digest")
        if normalized != before:
            raise ValueError("unrelated current-world state drift while adding dressing")
        states.append(row)

    checks = {
        "exact_environment_parent_passes_first": parent.get("receiving_head") == PARENT_HEAD and parent.get("composition_digest") == PARENT_COMPOSITION_DIGEST,
        "all_17_states_preserved": len(states) == 17,
        "exact_object_source_identity_preserved": all(_object_source(row["scene"]).get("source_sha256") == OBJECT_SOURCE_SHA256 for row in states),
        "object_transform_and_scale_unchanged": all(row["scene"].get("environment_object_replacement") == p["scene"].get("environment_object_replacement") for row, p in zip(states, parent["states"])),
        "building_receiving_preserved": all(row["scene"].get("environment_building_material_receiving") == p["scene"].get("environment_building_material_receiving") for row, p in zip(states, parent["states"])),
        "weather_width_fields_preserved": all(row["scene"].get("weather_lines") == p["scene"].get("weather_lines") for row, p in zip(states, parent["states"])),
        "nature_sequence_preserved": [row.get("sapling_mesh_digest") for row in states] == [row.get("sapling_mesh_digest") for row in parent["states"]],
        "static_sources_preserved": all(row["scene"].get("additional_source_meshes") == p["scene"].get("additional_source_meshes") for row, p in zip(states, parent["states"])),
        "path_and_cameras_preserved": all(row["scene"].get("readable_path") == p["scene"].get("readable_path") and row["scene"].get("cameras") == p["scene"].get("cameras") for row, p in zip(states, parent["states"])),
        "frame_inside_historical_reserved_receiver": contract["outer_footprint_source_xy_m"] == RESERVED_FOOTPRINT,
        "frame_clear_of_exact_object_source": metrics["minimum_object_to_frame_clearance_m"] >= MIN_OBJECT_TO_FRAME_CLEARANCE_M,
        "frame_clear_of_readable_path": metrics["minimum_readable_path_separation_m"] >= MIN_PATH_SEPARATION_M,
        "frame_clear_of_building_footprint": metrics["minimum_building_y_separation_m"] > 0.0,
    }
    if not all(checks.values()):
        raise ValueError(f"Object readability dressing checks failed: {checks}")

    out = {
        "schema": SCHEMA,
        "study_id": "environment-current-world-object-readability-dressing-001",
        "status": STATUS,
        "receiving_head": receiving_head,
        "environment_parent_head": PARENT_HEAD,
        "environment_parent_composition_digest": PARENT_COMPOSITION_DIGEST,
        "building_source_head": parent.get("building_source_head"),
        "building_material_profile_sha256": parent.get("building_material_profile_sha256"),
        "weather_variant_head": parent.get("weather_variant_head"),
        "weather_variant_seed": parent.get("weather_variant_seed"),
        "weather_variant_layout_digest": parent.get("weather_variant_layout_digest"),
        "vfx_source_width_head": parent.get("vfx_source_width_head"),
        "source_width_profile": copy.deepcopy(parent.get("source_width_profile", [])),
        "source_width_profile_digest": parent.get("source_width_profile_digest"),
        "source_width_summary": copy.deepcopy(parent.get("source_width_summary", {})),
        "object_source": {
            "asset_id": OBJECT_ASSET,
            "source_head": OBJECT_SOURCE_HEAD,
            "source_sha256": OBJECT_SOURCE_SHA256,
            "obj_sha256": OBJECT_OBJ_SHA256,
            "world_bounds_min_m": OBJECT_BOUNDS_MIN,
            "world_bounds_max_m": OBJECT_BOUNDS_MAX,
            "world_footprint_m": OBJECT_FOOTPRINT,
        },
        "dressing": contract,
        "measurements": metrics,
        "checks": checks,
        "states": states,
        "truth_boundary": (
            "PASS proves only that one Environment-owned receiver-footprint frame can be added inside the exact accepted west Object slot "
            "without scaling or moving the exact Object source and without changing Building, Weather, Nature, path, camera or lighting state. "
            "It does not itself prove final Art Direction/Visual QA preference, physical mounting, collision/navigation, target-device performance, gameplay, CANON or production readiness."
        ),
        "non_claims": [
            "OBJECT_SOURCE_SCALE_OR_GEOMETRY_CHANGE",
            "FINAL_OBJECT_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "PHYSICAL_SERVICE_PAD_OR_MOUNTING",
            "COLLISION_NAVIGATION_OR_GAMEPLAY",
            "TARGET_DEVICE_PERFORMANCE",
            "CANON_PRODUCTION_READY_GAME_READY_OR_MASTERY",
        ],
    }
    out["composition_digest"] = digest({
        "environment_parent": PARENT_COMPOSITION_DIGEST,
        "dressing": contract,
        "scenes": [row["scene"]["scene_digest"] for row in states],
    })
    return out


def verify(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path, parent_frame_root: str | Path) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA or payload.get("status") != STATUS or not all(payload.get("checks", {}).values()):
        raise ValueError("Object readability structure must PASS before target-host verification")
    if receipt.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError(f"real target-host observation did not reach inherited width PASS: {receipt.get('state')}")
    if receipt.get("receiving_head") != payload.get("receiving_head"):
        raise ValueError("target-host receiving head drift")
    samples = receipt.get("samples", [])
    if len(samples) != 17:
        raise ValueError("target-host sample count drift")

    from PIL import Image
    import numpy as np

    root = Path(image_root)
    parent_root = Path(parent_frame_root)
    pair_counts = {c: 0 for c in CONTEXTS}
    changed_counts: dict[str, list[int]] = {c: [] for c in CONTEXTS}
    bbox_residuals: dict[str, list[float]] = {c: [] for c in CONTEXTS}
    frame_visibility_counts: dict[str, list[int]] = {c: [] for c in CONTEXTS}
    width_residual = 0.0
    width_measured = 0
    rear_cull_ok = True
    object_ok = True
    building_ok = True
    runtime_sets: dict[str, dict[str, set[tuple[int, int, int, int, int]]]] = {m: {c: set() for c in CONTEXTS} for m in MODES}

    for sample in samples:
        idx = int(sample["index"])
        static = sample.get("static_source_meshes", [])
        object_rows = [r for r in static if r.get("asset_id") == OBJECT_ASSET]
        dressing_rows = [r for r in static if r.get("asset_id") == DRESSING_ASSET]
        building_rows = [r for r in static if r.get("asset_id") == "source:building:service-pavilion-001"]
        rear_rows = [r for r in static if r.get("asset_id") == "source:nature:east-rear-tree-neutral-001"]
        object_ok &= len(object_rows) == 1 and object_rows[0].get("vertices") == 468 and object_rows[0].get("triangles") == 812
        dressing_rows_ok = len(dressing_rows) == 1 and dressing_rows[0].get("triangles") == 48 and dressing_rows[0].get("proof_role") == "ENVIRONMENT_OWNED_RECEIVER_FOOTPRINT_READABILITY_CUE"
        if not dressing_rows_ok:
            raise ValueError("target host missing exact Environment dressing mesh")
        building_ok &= len(building_rows) == 1 and building_rows[0].get("vertices") == 152 and building_rows[0].get("triangles") == 228
        rear_cull_ok &= len(rear_rows) == 1 and rear_rows[0].get("proof_culling") == "CULL_BACK"

        contexts = sample.get("contexts", {})
        for context in CONTEXTS:
            ctx = contexts.get(context, {})
            for mode in MODES:
                block = ctx.get(mode, {})
                weather = block.get("weather_update", {})
                width_residual = max(width_residual, float(weather.get("maximum_projected_width_residual_px", 0.0)))
                width_measured += int(weather.get("measured_width_count", 0)) if mode == "candidate" else 0
                rt = block.get("runtime", {})
                runtime_sets[mode][context].add((int(rt.get("draw_calls_in_frame", -1)), int(rt.get("objects_in_frame", -1)), int(rt.get("primitives_in_frame", -1)), int(rt.get("buffer_mem_bytes", -1)), int(rt.get("texture_mem_bytes", -1))))
                shot = block.get("capture", {})
                bbox = shot.get("dressing_projected_bbox_px")
                if not isinstance(bbox, list) or len(bbox) != 4:
                    raise ValueError("capture missing projected dressing bbox")
                new_path = root / f"atmosphere-width-{mode}-{context}-{idx:02d}.png"
                old_path = parent_root / f"atmosphere-width-{mode}-{context}-{idx:02d}.png"
                if not new_path.exists() or not old_path.exists():
                    raise ValueError(f"missing frame pair {mode}/{context}/{idx}")
                new = np.asarray(Image.open(new_path).convert("RGB"), dtype=np.int16)
                old = np.asarray(Image.open(old_path).convert("RGB"), dtype=np.int16)
                if new.shape != old.shape:
                    raise ValueError("frame shape drift")
                mask = np.any(new != old, axis=2)
                count = int(mask.sum())
                if count <= 0:
                    raise ValueError(f"dressing produced no visible target-host delta for {mode}/{context}/{idx}")
                ys, xs = np.where(mask)
                observed = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
                margin = 4
                allowed = [int(bbox[0]) - margin, int(bbox[1]) - margin, int(bbox[2]) + margin, int(bbox[3]) + margin]
                if observed[0] < allowed[0] or observed[1] < allowed[1] or observed[2] > allowed[2] or observed[3] > allowed[3]:
                    raise ValueError(f"visual delta escaped projected dressing bounds: observed={observed} allowed={allowed}")
                bbox_residuals[context].append(0.0)
                changed_counts[context].append(count)
                frame_visibility_counts[context].append(count)
                pair_counts[context] += 1

    stable_runtime = all(len(runtime_sets[m][c]) == 1 for m in MODES for c in CONTEXTS)
    checks = {
        "exact_structural_payload_passes_first": payload.get("status") == STATUS and all(payload.get("checks", {}).values()),
        "all_17_target_host_samples_retained": len(samples) == 17,
        "all_68_parent_candidate_pairs_visibly_distinct": sum(pair_counts.values()) == 68 and all(pair_counts[c] == 34 for c in CONTEXTS),
        "all_visual_deltas_localized_to_projected_dressing_bounds": all(v == 0.0 for values in bbox_residuals.values() for v in values),
        "object_source_runtime_identity_preserved": object_ok,
        "building_runtime_identity_preserved": building_ok,
        "rear_tree_cull_back_preserved": rear_cull_ok,
        "source_width_fidelity_preserved": width_measured == 17 * len(CONTEXTS) * 36 and width_residual <= 0.05,
        "runtime_counter_sets_stable_per_mode_camera": stable_runtime,
        "frame_visible_in_every_context_state_mode": all(min(frame_visibility_counts[c]) > 0 for c in CONTEXTS),
    }
    if not all(checks.values()):
        raise ValueError(f"target-host dressing checks failed: {checks}")

    serial_runtime = {m: {c: [list(row) for row in sorted(runtime_sets[m][c])] for c in CONTEXTS} for m in MODES}
    report = {
        "schema": TARGET_SCHEMA,
        "state": TARGET_STATUS,
        "receiving_head": payload.get("receiving_head"),
        "environment_parent_head": PARENT_HEAD,
        "composition_digest": payload.get("composition_digest"),
        "dressing_asset_id": DRESSING_ASSET,
        "checks": checks,
        "maximum_projected_width_residual_px": width_residual,
        "measured_width_count": width_measured,
        "pair_counts": pair_counts,
        "changed_pixel_counts": {c: {"min": min(v), "max": max(v), "mean": sum(v) / len(v)} for c, v in changed_counts.items()},
        "runtime_counter_sets": serial_runtime,
        "truth_boundary": (
            "Target-host PASS proves only that the exact Environment-owned receiver-footprint frame is visibly present and its delta stays localized to its own projected bounds across all 17 dynamic states, both fixed cameras and both inherited Weather presentation modes, while exact Object/Building/Nature/Weather identities remain bounded. Final visual preference remains Art Direction/QA-owned."
        ),
        "non_claims": payload.get("non_claims", []),
    }
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--environment", required=True)
    b.add_argument("--receiving-head", required=True)
    b.add_argument("--output", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--payload", required=True)
    v.add_argument("--receipt", required=True)
    v.add_argument("--image-root", required=True)
    v.add_argument("--parent-frame-root", required=True)
    v.add_argument("--output", required=True)
    args = ap.parse_args()
    if args.cmd == "build":
        out = build(load_json(args.environment), args.receiving_head)
    else:
        out = verify(load_json(args.payload), load_json(args.receipt), args.image_root, args.parent_frame_root)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": out.get("status", out.get("state")), "composition_digest": out.get("composition_digest"), "checks": out.get("checks")}, indent=2))


if __name__ == "__main__":
    main()
