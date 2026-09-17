from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

PARENT_SCHEMA = "axm.environment-current-world-nature-material-family-composition/v0.1"
PARENT_STATUS = "PASS_CURRENT_WORLD_NATURE_MATERIAL_FAMILY_STRUCTURE"
PARENT_HEAD = "72d4128b602e27c886a0731ddd670ec8c14aaa7e"
PARENT_DIGEST = "5d050b2d628f73d7e1b738e900eaba22f56ac7bcdd5fc46a5bf781e1d9058866"
OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
OBJECT_SOURCE_HEAD = "d3fa10a270faae7925811f44f03381fe5c5d0215"
OBJECT_SOURCE_SHA256 = "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
OBJECT_MATERIALS_HEAD = "c85517446a769e0d5f880fc0e9e32f47124f7b5e"
OBJECT_PROFILE_SHA256 = "dc200229d6c25fa84063aa51f66103abc022efa54b2167e4432a5b47fc40360c"
PROFILE_SCHEMA = "axm.object-material-profile/v0.1"
RECEIVING_SCHEMA = "axm.environment-object-material-family-receiving/v0.1"
SCHEMA = "axm.environment-current-world-object-material-family-composition/v0.1"
STATUS = "PASS_CURRENT_WORLD_OBJECT_MATERIAL_FAMILY_STRUCTURE"
TARGET_SCHEMA = "axm.environment-current-world-object-material-family-target-host/v0.1"
TARGET_STATUS = "PASS_CURRENT_WORLD_OBJECT_MATERIAL_FAMILY_TARGET_HOST"
HOST_MATERIAL_IDS = (
    "shell_coating",
    "service_dark",
    "hardware_steel",
    "rubber_guard",
    "interface_orange",
)
CONTEXTS = ("path_eye", "elevated_oblique")
MODES = ("control", "candidate")


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def scene_digest(scene: dict[str, Any]) -> str:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    return digest(value)


def rgba(hex_rgba: str) -> list[float]:
    if not isinstance(hex_rgba, str) or len(hex_rgba) != 9 or not hex_rgba.startswith("#"):
        raise ValueError("material color must be #RRGGBBAA")
    try:
        return [int(hex_rgba[i : i + 2], 16) / 255.0 for i in (1, 3, 5, 7)]
    except ValueError as exc:
        raise ValueError("invalid material RGBA") from exc


def import_object_builder(root: Path):
    path = root / "tools/build_modular_case.py"
    spec = importlib.util.spec_from_file_location("axm_env_object_builder", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load exact Object source builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_profile(profile: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    if profile.get("schema") != PROFILE_SCHEMA:
        raise ValueError("Object material profile schema drift")
    if profile.get("asset_id") != "modular-equipment-case-001":
        raise ValueError("Object material profile asset drift")
    candidate = profile.get("candidate", {})
    role_materials = profile.get("role_materials", {})
    if not isinstance(candidate, dict) or not isinstance(role_materials, dict):
        raise ValueError("Object material profile payload missing")
    if set(HOST_MATERIAL_IDS) - set(candidate):
        raise ValueError("Object material host family missing expected material")
    normalized: dict[str, dict[str, Any]] = {}
    for material_id in HOST_MATERIAL_IDS:
        spec = candidate[material_id]
        metallic = float(spec.get("metallic", -1.0))
        roughness = float(spec.get("roughness", -1.0))
        if not 0.0 <= metallic <= 1.0 or not 0.0 <= roughness <= 1.0:
            raise ValueError(f"Object material scalar out of range: {material_id}")
        normalized[material_id] = {
            "albedo": rgba(spec["albedo"]),
            "albedo_hex": spec["albedo"],
            "metallic": metallic,
            "roughness": roughness,
        }
    if profile.get("provenance", {}).get("external_textures") not in ([], None):
        raise ValueError("Object material profile unexpectedly uses external textures")
    return normalized, {str(k): str(v) for k, v in role_materials.items()}


def exact_host_partition(object_root: Path, profile: dict[str, Any]) -> dict[str, Any]:
    source_path = object_root / "assets/modular-equipment-case-001/source.json"
    if sha256(source_path) != OBJECT_SOURCE_SHA256:
        raise ValueError("Object source byte identity drift")
    source = load_json(source_path)
    builder = import_object_builder(object_root)
    result = builder.build(source)
    mesh = result.get("mesh", {})
    vertices = mesh.get("vertices", [])
    faces = mesh.get("faces", [])
    groups = mesh.get("groups", [])
    components = result.get("components", [])
    if len(vertices) != 468 or len(faces) != 812:
        raise ValueError("exact Object host geometry count drift")
    if len(groups) != len(components):
        raise ValueError("Object source component/group cardinality drift")

    materials, role_materials = validate_profile(profile)
    partition = {material_id: [] for material_id in HOST_MATERIAL_IDS}
    component_roles: dict[str, str] = {}
    component_materials: dict[str, str] = {}
    seen_faces: set[int] = set()
    for component, group in zip(components, groups):
        name = str(component.get("name", ""))
        role = str(component.get("role", ""))
        if name != str(group.get("name", "")):
            raise ValueError("Object source component/group ordering drift")
        material_id = role_materials.get(role)
        if material_id not in HOST_MATERIAL_IDS:
            raise ValueError(f"Object host role lacks supported material mapping: {role}")
        start = int(group.get("first_face", -1))
        count = int(group.get("face_count", -1))
        if start < 0 or count <= 0 or start + count > len(faces):
            raise ValueError("Object source face group range drift")
        face_ids = list(range(start, start + count))
        if seen_faces.intersection(face_ids):
            raise ValueError("Object material face partition overlap")
        seen_faces.update(face_ids)
        partition[material_id].extend(face_ids)
        component_roles[name] = role
        component_materials[name] = material_id
    if seen_faces != set(range(812)):
        raise ValueError("Object material partition does not cover exact source faces")
    if any(not partition[material_id] for material_id in HOST_MATERIAL_IDS):
        raise ValueError("Object host material family contains empty surface")
    return {
        "vertices": vertices,
        "faces": faces,
        "partition": partition,
        "materials": materials,
        "component_roles": component_roles,
        "component_materials": component_materials,
    }


def one_object(scene: dict[str, Any]) -> dict[str, Any]:
    rows = [
        row
        for row in scene.get("additional_source_meshes", [])
        if row.get("asset_id") == OBJECT_ASSET_ID
    ]
    if len(rows) != 1:
        raise ValueError(f"expected one exact Object receiver, found {len(rows)}")
    return rows[0]


def attach_object_material_receiving(receiver: dict[str, Any], host: dict[str, Any]) -> None:
    vertices = receiver.get("vertices_source_xyz_m", [])
    triangles = receiver.get("triangles", [])
    if len(vertices) != 468 or len(triangles) != 812:
        raise ValueError("current-world Object geometry count drift")
    expected_faces = [list(face) for face in host["faces"]]
    if triangles != expected_faces:
        raise ValueError("current-world Object triangle ordering/membership drift")
    receiver["object_material_family_receiving"] = {
        "schema": RECEIVING_SCHEMA,
        "materials_head": OBJECT_MATERIALS_HEAD,
        "material_profile_schema": PROFILE_SCHEMA,
        "material_profile_sha256": OBJECT_PROFILE_SHA256,
        "source_head": OBJECT_SOURCE_HEAD,
        "source_sha256": OBJECT_SOURCE_SHA256,
        "materials": copy.deepcopy(host["materials"]),
        "surface_triangle_indices": copy.deepcopy(host["partition"]),
        "component_roles": copy.deepcopy(host["component_roles"]),
        "component_materials": copy.deepcopy(host["component_materials"]),
        "preserved_proof_culling": str(receiver.get("proof_render_culling", "")),
        "source_scope": "EXACT_STATIC_HOST_ONLY__NO_UTILITY_MODULE__NO_INNER_LID_REVIEW_SLOT",
        "truth_boundary": (
            "Map Environment receives only the exact Object source-role scalar PBR family on the already-present static host. "
            "No utility module, inner-lid candidate, articulation, source geometry, transform, scale, collision or gameplay semantics are introduced."
        ),
    }


def build(parent: dict[str, Any], profile_path: Path, object_root: Path, receiving_head: str) -> dict[str, Any]:
    if parent.get("schema") != PARENT_SCHEMA or parent.get("status") != PARENT_STATUS:
        raise ValueError("exact Nature-family Environment parent required")
    if parent.get("receiving_head") != PARENT_HEAD or parent.get("composition_digest") != PARENT_DIGEST:
        raise ValueError("exact Nature-family parent identity drift")
    if not all(parent.get("checks", {}).values()) or len(parent.get("states", [])) != 17:
        raise ValueError("exact Nature-family parent must structurally PASS")
    if sha256(profile_path) != OBJECT_PROFILE_SHA256:
        raise ValueError("Object material profile byte identity drift")
    profile = load_json(profile_path)
    host = exact_host_partition(object_root, profile)

    states: list[dict[str, Any]] = []
    source_receiver_digest: str | None = None
    for old_row in parent["states"]:
        row = copy.deepcopy(old_row)
        scene = row["scene"]
        before = copy.deepcopy(scene)
        before.pop("scene_digest", None)
        obj = one_object(scene)
        current = copy.deepcopy(obj)
        current.pop("object_material_family_receiving", None)
        current_digest = digest(current)
        if source_receiver_digest is None:
            source_receiver_digest = current_digest
        elif current_digest != source_receiver_digest:
            raise ValueError("Object receiver is not static across the 17-state parent")
        attach_object_material_receiving(obj, host)
        check = copy.deepcopy(scene)
        check.pop("scene_digest", None)
        check_obj = one_object(check)
        check_obj.pop("object_material_family_receiving", None)
        if check != before:
            raise ValueError("unrelated current-world state drift during Object material-family composition")
        scene["scene_digest"] = scene_digest(scene)
        states.append(row)

    first_scene = states[0]["scene"]
    replacement = first_scene.get("environment_object_replacement", {})
    checks = {
        "exact_nature_family_parent": True,
        "all_17_states_preserved": len(states) == 17,
        "weather_sequence_preserved": [x["weather_field_digest"] for x in states]
        == [x["weather_field_digest"] for x in parent["states"]],
        "sapling_sequence_preserved": [x["sapling_mesh_digest"] for x in states]
        == [x["sapling_mesh_digest"] for x in parent["states"]],
        "exact_object_source_identity_preserved": replacement.get("source_head") == OBJECT_SOURCE_HEAD
        and replacement.get("source_sha256") == OBJECT_SOURCE_SHA256,
        "exact_object_geometry_preserved": all(
            len(one_object(x["scene"]).get("vertices_source_xyz_m", [])) == 468
            and len(one_object(x["scene"]).get("triangles", [])) == 812
            for x in states
        ),
        "exact_five_host_material_surfaces": set(host["partition"]) == set(HOST_MATERIAL_IDS)
        and sum(len(v) for v in host["partition"].values()) == 812,
        "utility_module_not_introduced": all(
            all(source.get("asset_id") != "source:object:utility-module-001" for source in x["scene"].get("additional_source_meshes", []))
            for x in states
        ),
        "inner_lid_experiment_not_consumed": all(
            one_object(x["scene"])["object_material_family_receiving"]["source_scope"]
            == "EXACT_STATIC_HOST_ONLY__NO_UTILITY_MODULE__NO_INNER_LID_REVIEW_SLOT"
            for x in states
        ),
        "nature_building_dressing_weather_path_cameras_lighting_preserved": all(
            all(
                a["scene"].get(key) == b["scene"].get(key)
                for key in (
                    "sapling",
                    "environment_building_material_receiving",
                    "environment_object_readability_dressing",
                    "weather_lines",
                    "readable_path",
                    "cameras",
                    "lighting",
                )
            )
            for a, b in zip(states, parent["states"])
        ),
    }
    if not all(checks.values()):
        raise ValueError(f"Object material current-world checks failed: {checks}")

    out = copy.deepcopy(parent)
    out.update(
        {
            "schema": SCHEMA,
            "status": STATUS,
            "study_id": "environment-current-world-object-material-family-001",
            "receiving_head": receiving_head,
            "parent_environment_head": PARENT_HEAD,
            "parent_composition_digest": PARENT_DIGEST,
            "object_materials_head": OBJECT_MATERIALS_HEAD,
            "object_material_profile_sha256": OBJECT_PROFILE_SHA256,
            "object_source_head": OBJECT_SOURCE_HEAD,
            "object_source_sha256": OBJECT_SOURCE_SHA256,
            "object_host_material_ids": list(HOST_MATERIAL_IDS),
            "object_surface_triangle_counts": {k: len(v) for k, v in host["partition"].items()},
            "checks": checks,
            "states": states,
            "truth_boundary": (
                "PASS proves only exact receiving composition of the already-authored Object source-role scalar material family on the static west host inside the current Building + Nature + Weather + dressing world. "
                "It does not consume the utility module or the failing/unaccepted inner-lid review experiment and does not establish final aesthetic or runtime acceptance."
            ),
            "non_claims": [
                "OBJECT_INNER_LID_MATERIAL_SLOT_ACCEPTANCE",
                "OBJECT_ARTICULATION_OR_KEEPER_MOTION_ADOPTION",
                "UTILITY_MODULE_CURRENT_WORLD_ADOPTION",
                "UV_TEXTURE_DECAL_WEAR_OR_PHYSICAL_COATING_CORRECTNESS",
                "FINAL_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
                "TARGET_DEVICE_PERFORMANCE",
                "GAMEPLAY_COLLISION_NAVIGATION",
                "CANON_PRODUCTION_READY_OR_ENVIRONMENT_MASTERY",
            ],
        }
    )
    out["composition_digest"] = digest(
        {
            "parent": PARENT_DIGEST,
            "object_materials_head": OBJECT_MATERIALS_HEAD,
            "profile_sha256": OBJECT_PROFILE_SHA256,
            "source_head": OBJECT_SOURCE_HEAD,
            "source_sha256": OBJECT_SOURCE_SHA256,
            "receiver_digest": source_receiver_digest,
            "partition": host["partition"],
            "scenes": [x["scene"]["scene_digest"] for x in states],
        }
    )
    return out


def _runtime_numeric_delta(current: dict[str, Any], parent: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key in sorted(set(current).intersection(parent)):
        a = current.get(key)
        b = parent.get(key)
        if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
            out[key] = float(a) - float(b)
    return out


def verify(
    payload: dict[str, Any],
    receipt: dict[str, Any],
    parent_receipt: dict[str, Any],
    candidate_root: Path,
    parent_root: Path,
) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA or payload.get("status") != STATUS or not all(payload.get("checks", {}).values()):
        raise ValueError("Object material current-world structure must PASS first")
    if receipt.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError("candidate Godot current-world observation did not PASS")
    if receipt.get("receiving_head") != payload.get("receiving_head"):
        raise ValueError("candidate Godot receipt head drift")
    if parent_receipt.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION" or parent_receipt.get("receiving_head") != PARENT_HEAD:
        raise ValueError("exact Nature-family parent Godot receipt drift")
    if receipt.get("environment_object_materials_head") != OBJECT_MATERIALS_HEAD:
        raise ValueError("Object Materials head missing from live receipt")
    if receipt.get("environment_object_material_profile_sha256") != OBJECT_PROFILE_SHA256:
        raise ValueError("Object material profile identity missing from live receipt")

    samples = receipt.get("samples", [])
    parent_samples = parent_receipt.get("samples", [])
    if len(samples) != 17 or len(parent_samples) != 17:
        raise ValueError("live sample count drift")

    measured_width_count = 0
    maximum_width_residual = 0.0
    runtime_deltas: dict[str, dict[str, list[dict[str, float]]]] = {
        context: {mode: [] for mode in MODES} for context in CONTEXTS
    }
    for sample, parent_sample in zip(samples, parent_samples):
        if (
            sample.get("index"),
            sample.get("weather_field_digest"),
            sample.get("sapling_mesh_digest"),
        ) != (
            parent_sample.get("index"),
            parent_sample.get("weather_field_digest"),
            parent_sample.get("sapling_mesh_digest"),
        ):
            raise ValueError("dynamic current-world source sequence drift")
        object_rows = [x for x in sample.get("static_source_meshes", []) if x.get("asset_id") == OBJECT_ASSET_ID]
        if len(object_rows) != 1:
            raise ValueError("live Object material receiver missing")
        object_row = object_rows[0]
        if object_row.get("surface_count") != 5:
            raise ValueError("live Object material receiver is not exact five-surface host family")
        if object_row.get("material_ids") != list(HOST_MATERIAL_IDS):
            raise ValueError("live Object material surface ordering drift")
        if object_row.get("material_profile_sha256") != OBJECT_PROFILE_SHA256:
            raise ValueError("live Object material profile digest drift")
        for context in CONTEXTS:
            for mode in MODES:
                block = sample["contexts"][context][mode]
                pblock = parent_sample["contexts"][context][mode]
                if mode == "candidate":
                    weather = block["weather_update"]
                    measured_width_count += int(weather.get("measured_width_count", 0))
                    maximum_width_residual = max(
                        maximum_width_residual,
                        float(weather.get("maximum_projected_width_residual_px", 999.0)),
                    )
                runtime_deltas[context][mode].append(
                    _runtime_numeric_delta(block.get("runtime", {}), pblock.get("runtime", {}))
                )
    if measured_width_count != 1224 or maximum_width_residual > 0.05:
        raise ValueError("inherited Weather source-width observation drift")

    from PIL import Image
    import numpy as np

    candidate_files = sorted(candidate_root.glob("atmosphere-width-*.png"))
    parent_files = sorted(parent_root.glob("atmosphere-width-*.png"))
    if len(candidate_files) != 68 or len(parent_files) != 68:
        raise ValueError(f"expected exact 68/68 retained frames, got {len(candidate_files)}/{len(parent_files)}")
    parent_by_name = {p.name: p for p in parent_files}
    changed: dict[str, list[int]] = {context: [] for context in CONTEXTS}
    maximum_channel_delta = 0
    bounding_boxes: dict[str, list[list[int] | None]] = {context: [] for context in CONTEXTS}
    for candidate_path in candidate_files:
        if candidate_path.name not in parent_by_name:
            raise ValueError(f"parent frame missing: {candidate_path.name}")
        parts = candidate_path.stem.split("-")
        context = "path_eye" if "path_eye" in candidate_path.name else "elevated_oblique" if "elevated_oblique" in candidate_path.name else None
        if context is None:
            raise ValueError(f"unknown frame context: {candidate_path.name}")
        a = np.array(Image.open(parent_by_name[candidate_path.name]).convert("RGB"), dtype=np.int16)
        b = np.array(Image.open(candidate_path).convert("RGB"), dtype=np.int16)
        if a.shape != b.shape or a.shape[:2] != (720, 1100):
            raise ValueError("retained frame dimensions drift")
        delta = np.abs(b - a)
        mask = np.any(delta > 1, axis=2)
        count = int(mask.sum())
        if count <= 0:
            raise ValueError(f"Object material family produced no direct visual delta: {candidate_path.name}")
        changed[context].append(count)
        maximum_channel_delta = max(maximum_channel_delta, int(delta.max()))
        ys, xs = np.nonzero(mask)
        bounding_boxes[context].append([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None)

    total_pixels = 1100 * 720
    visual = {}
    for context in CONTEXTS:
        values = changed[context]
        if len(values) != 34:
            raise ValueError(f"expected 34 matched frames for {context}")
        visual[context] = {
            "pair_count": len(values),
            "changed_pixels_gt_1_lsb_min": min(values),
            "changed_pixels_gt_1_lsb_max": max(values),
            "changed_pixels_gt_1_lsb_mean": sum(values) / len(values),
            "changed_fraction_mean": (sum(values) / len(values)) / total_pixels,
            "bounding_boxes_px": bounding_boxes[context],
        }

    checks = {
        "structure_passed": True,
        "exact_17_state_live_sequence": len(samples) == 17,
        "exact_object_five_surface_family_live": True,
        "all_68_parent_candidate_frames_directly_compared": len(candidate_files) == 68,
        "all_68_frames_have_direct_visual_delta": all(v > 0 for values in changed.values() for v in values),
        "weather_source_width_gate_preserved": measured_width_count == 1224 and maximum_width_residual <= 0.05,
        "utility_module_and_inner_lid_not_promoted": True,
    }
    if not all(checks.values()):
        raise ValueError(f"target-host checks failed: {checks}")
    return {
        "schema": TARGET_SCHEMA,
        "state": TARGET_STATUS,
        "receiving_head": payload["receiving_head"],
        "parent_environment_head": PARENT_HEAD,
        "composition_digest": payload["composition_digest"],
        "object_materials_head": OBJECT_MATERIALS_HEAD,
        "object_material_profile_sha256": OBJECT_PROFILE_SHA256,
        "object_source_head": OBJECT_SOURCE_HEAD,
        "object_source_sha256": OBJECT_SOURCE_SHA256,
        "checks": checks,
        "measured_width_count": measured_width_count,
        "maximum_projected_width_residual_px": maximum_width_residual,
        "visual_delta": visual,
        "maximum_rgb_channel_delta": maximum_channel_delta,
        "runtime_numeric_deltas_vs_nature_family_parent": runtime_deltas,
        "truth_boundary": (
            "Direct 68-frame Godot A/B proves only the receiving-scene consequence of the exact static-host Object scalar material family over the exact current Nature-family parent. "
            "Runtime counters are diagnostic, and aesthetic preference remains Art Direction/Visual QA owned."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build_p = sub.add_parser("build")
    build_p.add_argument("--parent", required=True)
    build_p.add_argument("--profile", required=True)
    build_p.add_argument("--object-root", required=True)
    build_p.add_argument("--receiving-head", required=True)
    build_p.add_argument("--output", required=True)
    verify_p = sub.add_parser("verify")
    verify_p.add_argument("--payload", required=True)
    verify_p.add_argument("--receipt", required=True)
    verify_p.add_argument("--parent-receipt", required=True)
    verify_p.add_argument("--candidate-root", required=True)
    verify_p.add_argument("--parent-root", required=True)
    verify_p.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.command == "build":
        result = build(
            load_json(args.parent),
            Path(args.profile),
            Path(args.object_root),
            args.receiving_head,
        )
    else:
        result = verify(
            load_json(args.payload),
            load_json(args.receipt),
            load_json(args.parent_receipt),
            Path(args.candidate_root),
            Path(args.parent_root),
        )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": result.get("state", result.get("status")), "composition_digest": result.get("composition_digest")}, indent=2))


if __name__ == "__main__":
    main()
