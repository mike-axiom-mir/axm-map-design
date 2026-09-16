from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

PARENT_SCHEMA = "axm.environment-current-world-object-readability-dressing-composition/v0.1"
PARENT_STATUS = "PASS_CURRENT_WORLD_OBJECT_READABILITY_DRESSING_STRUCTURE"
PARENT_HEAD = "a29aa1e3d2260e8eb5ab2ac78a95d35ce131214c"
PARENT_COMPOSITION_DIGEST = "8e22d33400effef66f5af79a19229cd5a4370d2a68563ecd1432f4ccb480b815"
PARENT_TARGET_STATUS = "PASS_CURRENT_WORLD_OBJECT_READABILITY_DRESSING_TARGET_HOST"

BUILDING_ASSET = "source:building:service-pavilion-001"
SOURCE_HEAD = "34124101e616c423c5a3ed5e122ddf09b98a1650"
MATERIAL_HEAD = "09a534d9d6d4cdaa1bab70cc2d01345b48d8fcc8"
SOURCE_SCHEMA = "axm.building-hard-surface/v0.2"
SOURCE_REVISION = "service-pavilion-001/closed-outward-box-shells-002"
SEGMENTATION_SCHEMA = "axm.building-header-segmentation/v0.1"
SEGMENTATION_REVISION = "service-pavilion-001/interpenetration-free-header-segmentation-003"
SEGMENTATION_RESULT = "PASS_SOURCE_OWNED_INTERPENETRATION_FREE_HEADER_SEGMENTATION_OVERLAY"
MATERIAL_PROFILE_SCHEMA = "axm.building-material-profile/v0.1"
ROLES = [
    "frame_galvanized",
    "infill_coating",
    "roof_membrane",
    "slab_mineral",
    "utility_panel_ochre",
]
EXPECTED_ROLE_BOX_COUNTS = {
    "frame_galvanized": 16,
    "infill_coating": 3,
    "roof_membrane": 1,
    "slab_mineral": 1,
    "utility_panel_ochre": 2,
}
EPS = 1e-9

SCHEMA = "axm.environment-current-world-building-header-segmentation-composition/v0.1"
STATUS = "PASS_CURRENT_WORLD_BUILDING_HEADER_SEGMENTATION_STRUCTURE"
TARGET_SCHEMA = "axm.environment-current-world-building-header-segmentation-target-host/v0.1"
TARGET_STATUS = "PASS_CURRENT_WORLD_BUILDING_HEADER_SEGMENTATION_TARGET_HOST"
CONTEXTS = ("path_eye", "elevated_oblique")
MODES = ("control", "candidate")


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def file_sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def scene_digest(scene: dict[str, Any]) -> str:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    return digest(value)


def load_module(path: str | Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_obj(lines: list[str]) -> tuple[list[list[float]], list[list[int]], list[str]]:
    vertices: list[list[float]] = []
    triangles: list[list[int]] = []
    objects: list[str] = []
    for line in lines:
        if line.startswith("o "):
            objects.append(line[2:].strip())
        elif line.startswith("v "):
            _, x, y, z = line.split()
            vertices.append([float(x), float(y), float(z)])
        elif line.startswith("f "):
            triangles.append([int(v.split("/")[0]) - 1 for v in line.split()[1:]])
    if (len(vertices), len(triangles), len(objects)) != (152, 228, 19):
        raise ValueError("current logical Building source geometry drift")
    return vertices, triangles, objects


def material_map(receiving: dict[str, Any]) -> dict[str, dict[str, Any]]:
    surfaces = receiving.get("surfaces", [])
    if [row.get("surface_role") for row in surfaces] != ROLES:
        raise ValueError("Building five-surface role order drift")
    if any(row.get("material_id") != row.get("surface_role") for row in surfaces):
        raise ValueError("Building material role/id drift")
    return {row["surface_role"]: copy.deepcopy(row["material"]) for row in surfaces}


def rgba(hex_rgba: str) -> list[float]:
    if not isinstance(hex_rgba, str) or len(hex_rgba) != 9 or not hex_rgba.startswith("#"):
        raise ValueError(f"invalid RGBA hex {hex_rgba!r}")
    return [int(hex_rgba[i:i + 2], 16) / 255.0 for i in (1, 3, 5, 7)]


def material_matches_profile(material: dict[str, Any], profile: dict[str, Any]) -> bool:
    values = material.get("albedo", [])
    expected = rgba(profile.get("albedo", ""))
    return (
        isinstance(values, list)
        and len(values) == 4
        and all(abs(float(a) - float(b)) <= 1e-8 for a, b in zip(values, expected))
        and abs(float(material.get("metallic", -1.0)) - float(profile.get("metallic", -2.0))) <= EPS
        and abs(float(material.get("roughness", -1.0)) - float(profile.get("roughness", -2.0))) <= EPS
    )


def translation_error(local: list[list[float]], world: list[list[float]]) -> tuple[list[float], float]:
    if len(local) != len(world) or not local:
        raise ValueError("Building placement vertex count drift")
    translation = [float(world[0][axis]) - float(local[0][axis]) for axis in range(3)]
    maximum = 0.0
    for source, target in zip(local, world):
        for axis in range(3):
            maximum = max(maximum, abs(float(source[axis]) + translation[axis] - float(target[axis])))
    return translation, maximum


def strip_building(scene: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    value.pop("environment_building_material_receiving", None)
    return value


def bounds(vertices: list[list[float]]) -> dict[str, list[float]]:
    return {
        "min": [min(float(vertex[axis]) for vertex in vertices) for axis in range(3)],
        "max": [max(float(vertex[axis]) for vertex in vertices) for axis in range(3)],
    }


def validate_parent(parent: dict[str, Any]) -> None:
    if parent.get("schema") != PARENT_SCHEMA or parent.get("status") != PARENT_STATUS:
        raise ValueError("exact Object-dressing Environment parent must PASS first")
    if parent.get("receiving_head") != PARENT_HEAD or parent.get("composition_digest") != PARENT_COMPOSITION_DIGEST:
        raise ValueError("exact Environment parent identity drift")
    if len(parent.get("states", [])) != 17 or not all(parent.get("checks", {}).values()):
        raise ValueError("Environment parent state/check drift")
    dressing = parent.get("dressing", {})
    if dressing.get("asset_id") != "environment:dressing:west-object-service-footprint-frame-001":
        raise ValueError("Environment Object readability dressing identity drift")


def build(
    parent: dict[str, Any],
    source_root: str | Path,
    material_profile: dict[str, Any],
    source_head: str,
    material_head: str,
    receiving_head: str,
) -> dict[str, Any]:
    validate_parent(parent)
    if source_head != SOURCE_HEAD or material_head != MATERIAL_HEAD:
        raise ValueError("exact Building/Materials donor head drift")
    if material_profile.get("schema") != MATERIAL_PROFILE_SCHEMA or material_profile.get("asset_id") != "service-pavilion-001":
        raise ValueError("Building Materials profile identity drift")

    successor_binding = material_profile.get("successor_representation_materials", {})
    if (
        successor_binding.get("contract") != SEGMENTATION_SCHEMA
        or successor_binding.get("source_head") != SOURCE_HEAD
        or successor_binding.get("successor_revision") != SEGMENTATION_REVISION
        or successor_binding.get("fallback_policy") != "NONE_EXPLICIT_IDS_ONLY"
    ):
        raise ValueError("source-owned header-segmentation material binding drift")
    explicit_segment_materials = successor_binding.get("emitted_component_materials", {})
    expected_segment_ids = {
        f"front-header::segment-{index}" for index in range(3)
    } | {
        f"rear-header::segment-{index}" for index in range(3)
    }
    if set(explicit_segment_materials) != expected_segment_ids:
        raise ValueError("exact six header-segment material bindings required")
    if any(explicit_segment_materials[row] != "frame_galvanized" for row in expected_segment_ids):
        raise ValueError("all exact header segments must retain frame_galvanized")

    source_root = Path(source_root)
    segmentation = load_module(source_root / "tools" / "build_service_pavilion_header_segmentation.py", "axm_env_header_segmentation")
    base, candidate_boxes, segmentation_receipt = segmentation.build(source_head)
    if segmentation_receipt.get("result") != SEGMENTATION_RESULT or segmentation_receipt.get("exact_hard_surface_head") != SOURCE_HEAD:
        raise ValueError("Building source-owned header segmentation did not PASS")
    if segmentation_receipt.get("successor_revision") != SEGMENTATION_REVISION:
        raise ValueError("Building header-segmentation revision drift")
    if segmentation_receipt.get("source_positive_volume_intersection_count") != 4:
        raise ValueError("historical positive-volume intersection count drift")
    if abs(float(segmentation_receipt.get("source_positive_double_covered_volume_m3", -1.0)) - 0.02592) > EPS:
        raise ValueError("historical double-covered volume drift")
    if segmentation_receipt.get("successor_positive_volume_intersection_count") != 0:
        raise ValueError("source-owned successor retains positive-volume intersections")
    union = segmentation_receipt.get("occupied_union", {})
    if union.get("equivalent") is not True or abs(float(union.get("volume_residual_m3", 1.0))) > EPS:
        raise ValueError("source-owned successor changed occupied union")
    topology = segmentation_receipt.get("topology", {})
    required_topology = {
        "object_count": 23,
        "vertex_count": 184,
        "triangle_count": 276,
        "boundary_edge_count": 0,
        "nonmanifold_edge_count": 0,
        "orientation_conflict_edge_count": 0,
        "degenerate_triangle_count": 0,
        "outward_triangle_count": 276,
        "inward_triangle_count": 0,
    }
    if any(topology.get(key) != value for key, value in required_topology.items()):
        raise ValueError("source-owned successor topology metrics drift")
    if abs(float(segmentation_receipt.get("receiver_mount_residual_max_m", 1.0))) > EPS:
        raise ValueError("source-owned successor receiver mount drift")

    base_built = base.build()
    local_parent_vertices, _, _ = parse_obj(base_built[3])
    first_receiving = parent["states"][0]["scene"].get("environment_building_material_receiving", {})
    if first_receiving.get("asset_id") != BUILDING_ASSET:
        raise ValueError("current-world Building receiving identity drift")
    parent_world_vertices = first_receiving.get("vertices_source_xyz_m", [])
    if len(parent_world_vertices) != 152:
        raise ValueError("current-world Building predecessor must remain 152 vertices")
    translation, placement_error = translation_error(local_parent_vertices, parent_world_vertices)
    if placement_error > EPS:
        raise ValueError(f"Building source placement drift before segmentation: {placement_error}")

    current_materials = material_map(first_receiving)
    candidate_profile = material_profile.get("candidate", {})
    if set(candidate_profile) != set(ROLES):
        raise ValueError("Building five-surface material family drift")
    for role in ROLES:
        if not material_matches_profile(current_materials[role], candidate_profile[role]):
            raise ValueError(f"current accepted {role} material differs from exact successor Materials profile")

    component_materials = material_profile.get("component_materials", {})
    world_vertices: list[list[float]] = []
    grouped_triangles: dict[str, list[list[int]]] = {role: [] for role in ROLES}
    component_rows: list[dict[str, Any]] = []
    role_box_counts = {role: 0 for role in ROLES}
    for box in candidate_boxes:
        box_id = str(box.get("id", ""))
        role = explicit_segment_materials.get(box_id, component_materials.get(box_id))
        if role not in grouped_triangles:
            raise ValueError(f"no exact material binding for emitted Building box {box_id}")
        offset = len(world_vertices)
        local_vertices = box.get("vertices", [])
        if len(local_vertices) != 8:
            raise ValueError(f"emitted box {box_id} vertex count drift")
        world_vertices.extend([
            [float(vertex[axis]) + translation[axis] for axis in range(3)]
            for vertex in local_vertices
        ])
        triangles = [[offset + int(index) - 1 for index in face] for face in base.FACES]
        grouped_triangles[role].extend(triangles)
        role_box_counts[role] += 1
        component_rows.append({
            "emitted_component_id": box_id,
            "source_component_id": box.get("source_component_id", box_id),
            "surface_role": role,
            "vertex_count": 8,
            "triangle_count": 12,
        })

    if len(world_vertices) != 184 or sum(len(rows) for rows in grouped_triangles.values()) != 276:
        raise ValueError("segmented current-world Building geometry count drift")
    if role_box_counts != EXPECTED_ROLE_BOX_COUNTS:
        raise ValueError(f"segmented Building material role count drift: {role_box_counts}")
    if bounds(world_vertices) != {
        "min": [float(value) + translation[axis] for axis, value in enumerate(segmentation_receipt["bounds"]["min"])],
        "max": [float(value) + translation[axis] for axis, value in enumerate(segmentation_receipt["bounds"]["max"])],
    }:
        raise ValueError("segmented current-world Building bounds drift")
    if bounds(world_vertices) != bounds(parent_world_vertices):
        raise ValueError("segmented current-world Building changed assembled world bounds")

    profile_path = Path(material_profile.get("_profile_path", ""))
    profile_sha = file_sha(profile_path) if profile_path.is_file() else digest(material_profile)
    surfaces = [
        {
            "surface_role": role,
            "material_id": role,
            "material": copy.deepcopy(current_materials[role]),
            "triangles": grouped_triangles[role],
        }
        for role in ROLES
    ]
    surface_partition_sha = digest(grouped_triangles)

    states: list[dict[str, Any]] = []
    for parent_row in parent["states"]:
        row = copy.deepcopy(parent_row)
        scene = row["scene"]
        before = strip_building(scene)
        old = scene.get("environment_building_material_receiving", {})
        if old.get("vertices_source_xyz_m") != parent_world_vertices or material_map(old) != current_materials:
            raise ValueError("current-world Building state drift across parent sequence")
        receiving = copy.deepcopy(old)
        receiving["vertices_source_xyz_m"] = copy.deepcopy(world_vertices)
        receiving["surfaces"] = copy.deepcopy(surfaces)
        receiving["source_geometry_digest"] = digest({"vertices": world_vertices, "triangles": grouped_triangles})
        receiving["receiving_policy"] = "EXACT_SOURCE_OWNED_INTERPENETRATION_FREE_HEADER_SEGMENTATION_WITH_EXPLICIT_MATERIAL_BINDING"
        receiving["source_header_segmentation_rebind"] = {
            "source_head": SOURCE_HEAD,
            "source_schema": SOURCE_SCHEMA,
            "source_revision": SOURCE_REVISION,
            "segmentation_schema": SEGMENTATION_SCHEMA,
            "segmentation_revision": SEGMENTATION_REVISION,
            "segmentation_result": SEGMENTATION_RESULT,
            "material_head": MATERIAL_HEAD,
            "material_profile_sha256": profile_sha,
            "placement_translation_source_xyz_m": translation,
            "historical_positive_volume_intersection_count": 4,
            "historical_positive_double_covered_volume_m3": 0.02592,
            "successor_positive_volume_intersection_count": 0,
            "occupied_union_equivalent": True,
            "occupied_union_volume_residual_m3": 0.0,
            "receiver_mount_residual_max_m": 0.0,
            "topology_summary": copy.deepcopy(topology),
            "segment_map": copy.deepcopy(segmentation_receipt.get("segment_map", {})),
            "explicit_segment_materials": copy.deepcopy(explicit_segment_materials),
        }
        provenance = receiving.setdefault("provenance", {})
        provenance.update({
            "building_source_head": SOURCE_HEAD,
            "building_material_head": MATERIAL_HEAD,
            "material_profile_sha256": profile_sha,
            "building_header_segmentation_revision": SEGMENTATION_REVISION,
            "placement_translation_source_xyz_m": translation,
        })
        receiving["truth_boundary"] = (
            "Environment replaces only the current-world Building emitted representation with the exact source-owned interpenetration-free header segmentation and exact Materials-owned emitted-ID mapping. "
            "Occupied union, world bounds, material scalars, Object dressing, Weather, Nature, path, cameras, lighting and receiver placement remain fixed."
        )
        scene["environment_building_material_receiving"] = receiving
        scene["scene_digest"] = scene_digest(scene)
        if strip_building(scene) != before:
            raise ValueError("unrelated current-world state drift while rebinding Building segmentation")
        states.append(row)

    checks = {
        "exact_object_dressing_parent_passes_first": parent.get("receiving_head") == PARENT_HEAD and parent.get("composition_digest") == PARENT_COMPOSITION_DIGEST,
        "all_17_states_preserved": len(states) == 17,
        "exact_weather_state_sequence_preserved": [row.get("weather_field_digest") for row in states] == [row.get("weather_field_digest") for row in parent["states"]],
        "exact_sapling_state_sequence_preserved": [row.get("sapling_mesh_digest") for row in states] == [row.get("sapling_mesh_digest") for row in parent["states"]],
        "object_source_and_dressing_preserved": all(
            row["scene"].get("environment_object_replacement") == old["scene"].get("environment_object_replacement")
            and row["scene"].get("environment_object_readability_dressing") == old["scene"].get("environment_object_readability_dressing")
            for row, old in zip(states, parent["states"])
        ),
        "additional_sources_and_rear_nature_preserved": all(
            row["scene"].get("additional_source_meshes") == old["scene"].get("additional_source_meshes")
            for row, old in zip(states, parent["states"])
        ),
        "path_cameras_and_lighting_preserved": all(
            row["scene"].get("readable_path") == old["scene"].get("readable_path")
            and row["scene"].get("cameras") == old["scene"].get("cameras")
            and row["scene"].get("lighting") == old["scene"].get("lighting")
            for row, old in zip(states, parent["states"])
        ),
        "accepted_building_material_scalars_preserved": all(material_map(row["scene"]["environment_building_material_receiving"]) == current_materials for row in states),
        "exact_six_segment_material_bindings_consumed": set(explicit_segment_materials) == expected_segment_ids,
        "no_material_fallback_or_prefix_inference": successor_binding.get("fallback_policy") == "NONE_EXPLICIT_IDS_ONLY",
        "source_owned_segmentation_passes": segmentation_receipt.get("result") == SEGMENTATION_RESULT,
        "historical_four_positive_volume_intersections_retained_as_before_evidence": segmentation_receipt.get("source_positive_volume_intersection_count") == 4,
        "successor_zero_positive_volume_intersections": segmentation_receipt.get("successor_positive_volume_intersection_count") == 0,
        "successor_occupied_union_exact": union.get("equivalent") is True and abs(float(union.get("volume_residual_m3", 1.0))) <= EPS,
        "receiver_mounts_unchanged": abs(float(segmentation_receipt.get("receiver_mount_residual_max_m", 1.0))) <= EPS,
        "successor_exact_184_vertices_276_triangles": len(world_vertices) == 184 and sum(len(rows) for rows in grouped_triangles.values()) == 276,
        "successor_world_bounds_exactly_preserved": bounds(world_vertices) == bounds(parent_world_vertices),
        "current_source_placement_preserved": placement_error <= EPS,
    }
    if not all(checks.values()):
        raise ValueError(f"current-world Building header-segmentation checks failed: {checks}")

    out = copy.deepcopy(parent)
    out.update({
        "schema": SCHEMA,
        "study_id": "environment-current-world-building-header-segmentation-001",
        "status": STATUS,
        "receiving_head": receiving_head,
        "parent_environment_head": PARENT_HEAD,
        "parent_composition_digest": PARENT_COMPOSITION_DIGEST,
        "predecessor_building_source_head": parent.get("building_source_head"),
        "building_source_head": SOURCE_HEAD,
        "building_material_head": MATERIAL_HEAD,
        "building_material_profile_sha256": profile_sha,
        "building_header_segmentation": {
            "schema": SEGMENTATION_SCHEMA,
            "revision": SEGMENTATION_REVISION,
            "source_result": SEGMENTATION_RESULT,
            "source_positive_volume_intersection_count": 4,
            "source_positive_double_covered_volume_m3": 0.02592,
            "successor_positive_volume_intersection_count": 0,
            "occupied_union": copy.deepcopy(union),
            "receiver_mount_residual_max_m": 0.0,
            "topology": copy.deepcopy(topology),
            "surface_partition_sha256": surface_partition_sha,
            "role_box_counts": role_box_counts,
            "component_surface_rows": component_rows,
        },
        "checks": checks,
        "states": states,
        "truth_boundary": (
            "PASS proves only that the exact source-owned interpenetration-free Building header segmentation and exact Materials-owned emitted-ID mapping compose into the existing Object-dressed, Weather-width, moving-Nature current world while occupied union, world bounds, accepted material scalars and every unrelated scene dependency remain fixed. "
            "It does not itself accept the still-pending Object footprint cue, establish target-device performance, final visuals, gameplay, CANON or production readiness."
        ),
        "non_claims": [
            "FINAL_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "OBJECT_FOOTPRINT_DRESSING_ADOPTION",
            "BOOLEAN_UNIONED_OR_GLOBAL_VERTEX_MANIFOLD_BUILDING",
            "FINAL_NORMALS_TANGENTS_UVS_TEXTURES_DECALS_OR_WEATHERING",
            "TARGET_DEVICE_CPU_GPU_FPS_MEMORY_OR_BATCHING_ACCEPTANCE",
            "COLLISION_NAVIGATION_OR_GAMEPLAY",
            "UC_OR_PROFESSION_FABRIC_EXTRACTION",
            "CANON_PRODUCTION_READY_GAME_READY_OR_ENVIRONMENT_MASTERY",
        ],
    })
    out["composition_digest"] = digest({
        "parent": PARENT_COMPOSITION_DIGEST,
        "source_head": SOURCE_HEAD,
        "material_head": MATERIAL_HEAD,
        "segmentation_revision": SEGMENTATION_REVISION,
        "surface_partition": surface_partition_sha,
        "scenes": [row["scene"]["scene_digest"] for row in states],
    })
    return out


def verify(
    payload: dict[str, Any],
    receipt: dict[str, Any],
    image_root: str | Path,
    parent_frame_root: str | Path,
    parent_report: dict[str, Any],
) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA or payload.get("status") != STATUS or not all(payload.get("checks", {}).values()):
        raise ValueError("Building header-segmentation structure must PASS before target-host verification")
    if receipt.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError(f"real target-host observation did not reach inherited width PASS: {receipt.get('state')}")
    if receipt.get("receiving_head") != payload.get("receiving_head"):
        raise ValueError("target-host receiving head drift")
    if parent_report.get("state") != PARENT_TARGET_STATUS or parent_report.get("receiving_head") != PARENT_HEAD:
        raise ValueError("exact parent target-host report drift")
    samples = receipt.get("samples", [])
    if len(samples) != 17:
        raise ValueError("target-host sample count drift")

    from PIL import Image
    import numpy as np

    root = Path(image_root)
    parent_root = Path(parent_frame_root)
    pair_counts = {context: 0 for context in CONTEXTS}
    changed_counts: dict[str, list[int]] = {context: [] for context in CONTEXTS}
    significant_counts: dict[str, list[int]] = {context: [] for context in CONTEXTS}
    max_channel_delta = 0
    width_residual = 0.0
    width_measured = 0
    object_ok = True
    dressing_ok = True
    rear_cull_ok = True
    building_ok = True
    runtime_sets: dict[str, dict[str, set[tuple[int, int, int, int, int]]]] = {
        mode: {context: set() for context in CONTEXTS} for mode in MODES
    }

    for sample in samples:
        index = int(sample["index"])
        static = sample.get("static_source_meshes", [])
        object_rows = [row for row in static if row.get("asset_id") == "source:object:modular-equipment-case-001"]
        dressing_rows = [row for row in static if row.get("asset_id") == "environment:dressing:west-object-service-footprint-frame-001"]
        rear_rows = [row for row in static if row.get("asset_id") == "source:nature:east-rear-tree-neutral-001"]
        building_rows = [row for row in static if row.get("asset_id") == BUILDING_ASSET]
        object_ok &= len(object_rows) == 1 and object_rows[0].get("vertices") == 468 and object_rows[0].get("triangles") == 812
        dressing_ok &= len(dressing_rows) == 1 and dressing_rows[0].get("triangles") == 48
        rear_cull_ok &= len(rear_rows) == 1 and rear_rows[0].get("proof_culling") == "CULL_BACK"
        building_ok &= (
            len(building_rows) == 1
            and building_rows[0].get("vertices") == 184
            and building_rows[0].get("triangles") == 276
            and building_rows[0].get("surface_count") == 5
        )

        contexts = sample.get("contexts", {})
        for context in CONTEXTS:
            block_context = contexts.get(context, {})
            for mode in MODES:
                block = block_context.get(mode, {})
                weather = block.get("weather_update", {})
                width_residual = max(width_residual, float(weather.get("maximum_projected_width_residual_px", 0.0)))
                if mode == "candidate":
                    width_measured += int(weather.get("measured_width_count", 0))
                runtime = block.get("runtime", {})
                runtime_sets[mode][context].add((
                    int(runtime.get("draw_calls_in_frame", -1)),
                    int(runtime.get("objects_in_frame", -1)),
                    int(runtime.get("primitives_in_frame", -1)),
                    int(runtime.get("buffer_mem_bytes", -1)),
                    int(runtime.get("texture_mem_bytes", -1)),
                ))
                new_path = root / f"atmosphere-width-{mode}-{context}-{index:02d}.png"
                old_path = parent_root / f"atmosphere-width-{mode}-{context}-{index:02d}.png"
                if not new_path.exists() or not old_path.exists():
                    raise ValueError(f"missing exact frame pair {mode}/{context}/{index}")
                new = np.asarray(Image.open(new_path).convert("RGB"), dtype=np.int16)
                old = np.asarray(Image.open(old_path).convert("RGB"), dtype=np.int16)
                if new.shape != old.shape:
                    raise ValueError("frame shape drift")
                delta = np.abs(new - old)
                changed = int(np.any(delta > 0, axis=2).sum())
                significant = int(np.any(delta > 1, axis=2).sum())
                local_max = int(delta.max())
                max_channel_delta = max(max_channel_delta, local_max)
                changed_counts[context].append(changed)
                significant_counts[context].append(significant)
                pair_counts[context] += 1

    stable_runtime = all(len(runtime_sets[mode][context]) == 1 for mode in MODES for context in CONTEXTS)
    all_significant_zero = all(value == 0 for values in significant_counts.values() for value in values)
    checks = {
        "exact_structural_payload_passes_first": payload.get("status") == STATUS and all(payload.get("checks", {}).values()),
        "all_17_target_host_samples_retained": len(samples) == 17,
        "all_68_parent_successor_pairs_compared": sum(pair_counts.values()) == 68 and all(pair_counts[context] == 34 for context in CONTEXTS),
        "no_rgb_delta_above_one_lsb_in_any_pair": all_significant_zero,
        "exact_segmented_building_runtime_identity": building_ok,
        "object_source_runtime_identity_preserved": object_ok,
        "object_readability_dressing_runtime_identity_preserved": dressing_ok,
        "rear_tree_cull_back_preserved": rear_cull_ok,
        "source_width_fidelity_preserved": width_measured == 17 * len(CONTEXTS) * 36 and width_residual <= 0.05,
        "runtime_counter_sets_stable_per_mode_camera": stable_runtime,
    }
    if not all(checks.values()):
        raise ValueError(f"target-host Building header-segmentation checks failed: {checks}")

    serial_runtime = {
        mode: {
            context: [list(row) for row in sorted(runtime_sets[mode][context])]
            for context in CONTEXTS
        }
        for mode in MODES
    }
    runtime_delta_vs_parent: dict[str, dict[str, list[int] | None]] = {}
    parent_runtime = parent_report.get("runtime_counter_sets", {})
    for mode in MODES:
        runtime_delta_vs_parent[mode] = {}
        for context in CONTEXTS:
            current_rows = serial_runtime[mode][context]
            parent_rows = parent_runtime.get(mode, {}).get(context, [])
            if len(current_rows) == 1 and len(parent_rows) == 1 and len(current_rows[0]) == len(parent_rows[0]) == 5:
                runtime_delta_vs_parent[mode][context] = [int(a) - int(b) for a, b in zip(current_rows[0], parent_rows[0])]
            else:
                runtime_delta_vs_parent[mode][context] = None

    report = {
        "schema": TARGET_SCHEMA,
        "state": TARGET_STATUS,
        "receiving_head": payload.get("receiving_head"),
        "environment_parent_head": PARENT_HEAD,
        "composition_digest": payload.get("composition_digest"),
        "building_source_head": SOURCE_HEAD,
        "building_material_head": MATERIAL_HEAD,
        "building_header_segmentation_revision": SEGMENTATION_REVISION,
        "checks": checks,
        "maximum_projected_width_residual_px": width_residual,
        "measured_width_count": width_measured,
        "pair_counts": pair_counts,
        "changed_pixel_counts": {
            context: {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
            }
            for context, values in changed_counts.items()
        },
        "significant_pixel_counts_gt_1_lsb": {
            context: {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
            }
            for context, values in significant_counts.items()
        },
        "maximum_rgb_channel_delta_lsb": max_channel_delta,
        "runtime_counter_sets": serial_runtime,
        "parent_runtime_counter_sets": parent_runtime,
        "runtime_counter_delta_vs_parent_order_draw_objects_primitives_buffer_texture": runtime_delta_vs_parent,
        "truth_boundary": (
            "Target-host PASS proves only that the exact source-owned interpenetration-free Building header segmentation reaches this exact Godot current-world receiver with no RGB delta above one 8-bit channel step across the retained fixed-camera/state/mode pairs, while Object dressing, Weather width, moving Nature and rear-tree culling remain present. "
            "Runtime counter deltas are diagnostic handoff evidence, not target-device acceptance."
        ),
        "non_claims": payload.get("non_claims", []),
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    build_parser = sub.add_parser("build")
    build_parser.add_argument("--environment", required=True)
    build_parser.add_argument("--building-source-root", required=True)
    build_parser.add_argument("--material-profile", required=True)
    build_parser.add_argument("--source-head", required=True)
    build_parser.add_argument("--material-head", required=True)
    build_parser.add_argument("--receiving-head", required=True)
    build_parser.add_argument("--output", required=True)

    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--payload", required=True)
    verify_parser.add_argument("--receipt", required=True)
    verify_parser.add_argument("--image-root", required=True)
    verify_parser.add_argument("--parent-frame-root", required=True)
    verify_parser.add_argument("--parent-report", required=True)
    verify_parser.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.cmd == "build":
        profile = load_json(args.material_profile)
        profile["_profile_path"] = str(Path(args.material_profile))
        out = build(
            load_json(args.environment),
            args.building_source_root,
            profile,
            args.source_head,
            args.material_head,
            args.receiving_head,
        )
    else:
        out = verify(
            load_json(args.payload),
            load_json(args.receipt),
            args.image_root,
            args.parent_frame_root,
            load_json(args.parent_report),
        )
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "state": out.get("status", out.get("state")),
        "composition_digest": out.get("composition_digest"),
        "checks": out.get("checks"),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
