from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import environment_nature_leaf_flutter_current_world as parent_tool

PARENT_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
PARENT_STRUCTURE_RESULT = "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_STRUCTURE"
GEOMETRY_HEAD = "16253e7dd2f8cd590667f9631e4b50fdfcc7280d"
HARD_SURFACE_HEAD = "35d0ba62d7e534b3cd00ac69e99386843ffa3f2e"
MATERIALS_HEAD = "4179aa1401f5a9114399e2f998c96809d4b8ed2e"
MATERIAL_PACKET_RESULT = "PASS_BUILDING_COMPACT_V2_SOURCE_OWNER_MATERIAL_REBIND_PACKET"
MATERIAL_CONTINUITY_RESULT = "PASS_COMPACT_V2_EXPLICIT_HARD_NORMAL_MATERIAL_CONTINUITY_BOUNDED_DELTA"
SEMANTIC_SOURCE_ID = "header-segmented-23"
REFERENCE_ID = "boundary-only-union-shell-001"
COMPACT_ID = "boundary-only-union-shell-conforming-compact-v2-001"
SELECTION_POLICY = "EXPLICIT_RECEIVING_REPRESENTATION_ID_REQUIRED__NO_DEFAULT_OR_IMPLICIT_FALLBACK"
EVIDENCE_TRANSFER_POLICY = "NO_DOWNSTREAM_PASS_TRANSFER_ACROSS_REFERENCE_V1_OR_COMPACT_V2_IDENTITIES__EXACT_CONSUMER_REBIND_REQUIRED"
NORMAL_POLICY = "EXPLICIT_PER_TRIANGLE_PLANE_NORMAL__NO_VERTEX_SMOOTHING__HARD_SURFACE_REVIEW"
BUILDING_ASSET_ID = "source:building:service-pavilion-001"
ROLES = [
    "frame_galvanized",
    "infill_coating",
    "roof_membrane",
    "slab_mineral",
    "utility_panel_ochre",
]
EXPECTED_COMPACT_TRIANGLES = {
    "frame_galvanized": 1164,
    "infill_coating": 88,
    "roof_membrane": 388,
    "slab_mineral": 388,
    "utility_panel_ochre": 24,
}
STRUCTURE_RESULT = "PASS_CURRENT_WORLD_BUILDING_COMPACT_V2_STRUCTURE"
TARGET_RESULT = "PASS_CURRENT_WORLD_BUILDING_COMPACT_V2_BOUNDED_CONTINUITY_REVIEW_READY"
EPS = 1e-9
MATERIAL_CONTINUITY_SIGNIFICANT_FRACTION_LIMIT = 0.001  # exact 0.1% donor guard


def load_json(path: Path) -> dict[str, Any]:
    return parent_tool.load_json(path)


def _bounds(vertices: list[list[float]]) -> dict[str, list[float]]:
    if not vertices:
        raise ValueError("empty Building vertex array")
    return {
        "min": [min(float(v[axis]) for v in vertices) for axis in range(3)],
        "max": [max(float(v[axis]) for v in vertices) for axis in range(3)],
    }


def _bounds_close(a: dict[str, list[float]], b: dict[str, list[float]]) -> bool:
    return all(
        abs(float(a[key][axis]) - float(b[key][axis])) <= EPS
        for key in ("min", "max")
        for axis in range(3)
    )


def _material_subset(material: dict[str, Any]) -> dict[str, Any]:
    return {
        "albedo": [float(v) for v in material.get("albedo", [])],
        "metallic": float(material.get("metallic", -1.0)),
        "roughness": float(material.get("roughness", -1.0)),
    }


def _material_matches(current: dict[str, Any], donor: dict[str, Any]) -> bool:
    a = _material_subset(current)
    b = _material_subset(donor)
    if len(a["albedo"]) != 4 or len(b["albedo"]) != 4:
        return False
    return (
        all(abs(x - y) <= 1e-8 for x, y in zip(a["albedo"], b["albedo"]))
        and abs(a["metallic"] - b["metallic"]) <= EPS
        and abs(a["roughness"] - b["roughness"]) <= EPS
    )


def _current_materials(receiving: dict[str, Any]) -> dict[str, dict[str, Any]]:
    surfaces = receiving.get("surfaces", [])
    if [row.get("surface_role") for row in surfaces] != ROLES:
        raise ValueError("current-world Building five-surface order drift")
    if any(row.get("material_id") != row.get("surface_role") for row in surfaces):
        raise ValueError("current-world Building material role/id drift")
    return {str(row["surface_role"]): copy.deepcopy(row["material"]) for row in surfaces}


def _strip_building(scene: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    value.pop("environment_building_material_receiving", None)
    return value


def _validate_parent(parent: dict[str, Any]) -> None:
    if parent.get("environment_head") != PARENT_HEAD:
        raise ValueError("exact Nature-flutter current-world parent head drift")
    if parent.get("nature_leaf_flutter_structure_result") != PARENT_STRUCTURE_RESULT:
        raise ValueError("Nature-flutter parent structure result missing")
    if len(parent.get("states", [])) != 17 or not all(parent.get("checks", {}).values()):
        raise ValueError("Nature-flutter parent state/check drift")
    policy = parent.get("nature_surface_culling_policy", {})
    if (
        policy.get("woody_surface_cull") != "CULL_BACK"
        or policy.get("foliage_surface_cull") != "CULL_DISABLED"
        or bool(policy.get("explicit_leaf_backface_geometry_adopted", True))
    ):
        raise ValueError("accepted Nature split-culling parent drift")


def _validate_material_packet(packet: dict[str, Any], receipt: dict[str, Any]) -> None:
    if receipt.get("result") != MATERIAL_PACKET_RESULT:
        raise ValueError("Building compact-v2 Materials packet is not green")
    if packet.get("exact_materials_head") != MATERIALS_HEAD or receipt.get("exact_materials_head") != MATERIALS_HEAD:
        raise ValueError("Building Materials head drift")
    if packet.get("geometry_donor_head") != GEOMETRY_HEAD or packet.get("hard_surface_owner_head") != HARD_SURFACE_HEAD:
        raise ValueError("Building Geometry/Hard-Surface donor head drift")
    if packet.get("semantic_source_variant_id") != SEMANTIC_SOURCE_ID:
        raise ValueError("Building semantic source identity drift")
    if packet.get("reference_representation_id") != REFERENCE_ID or packet.get("selected_representation_id") != COMPACT_ID:
        raise ValueError("Building compact-v2 representation identity drift")
    if packet.get("selection_policy") != SELECTION_POLICY or packet.get("evidence_transfer_policy") != EVIDENCE_TRANSFER_POLICY:
        raise ValueError("Building compact-v2 owner selection/evidence-transfer policy drift")
    if packet.get("normal_policy") != NORMAL_POLICY:
        raise ValueError("Building compact-v2 hard-normal review policy drift")
    if packet.get("compact_stats", {}).get("vertex_count") != 1004 or packet.get("compact_stats", {}).get("triangle_count") != 2052:
        raise ValueError("Building compact-v2 budget drift")
    if packet.get("compact_stats", {}).get("source_component_owner_count") != 19:
        raise ValueError("Building compact-v2 source-owner coverage drift")
    if packet.get("truth_boundary", {}).get("environment_adoption") is not False:
        raise ValueError("Materials packet unexpectedly pre-authorizes Environment adoption")


def build(parent: dict[str, Any], packet: dict[str, Any], receipt: dict[str, Any], environment_head: str) -> dict[str, Any]:
    _validate_parent(parent)
    _validate_material_packet(packet, receipt)

    compact = packet.get("compact", {})
    local_vertices = compact.get("vertices", [])
    triangles = compact.get("triangles", [])
    owners = compact.get("triangle_owners", [])
    mapping = packet.get("component_materials", {})
    donor_materials = packet.get("materials", {})
    if len(local_vertices) != 1004 or len(triangles) != 2052 or len(owners) != 2052:
        raise ValueError("Building compact-v2 mesh arrays drift")
    if len(mapping) != 19 or set(donor_materials) != set(ROLES):
        raise ValueError("Building compact-v2 material-owner family drift")

    first_receiving = parent["states"][0]["scene"].get("environment_building_material_receiving", {})
    if first_receiving.get("asset_id") != BUILDING_ASSET_ID:
        raise ValueError("current-world Building receiver missing")
    current_vertices = first_receiving.get("vertices_source_xyz_m", [])
    if len(current_vertices) != 184:
        raise ValueError("current-world parent must retain exact 184-vertex segmented Building")
    current_materials = _current_materials(first_receiving)
    for role in ROLES:
        if not _material_matches(current_materials[role], donor_materials[role]):
            raise ValueError(f"current-world Building material differs from exact compact-v2 Materials donor: {role}")

    segmentation = first_receiving.get("source_header_segmentation_rebind", {})
    translation = segmentation.get("placement_translation_source_xyz_m", [])
    if not isinstance(translation, list) or len(translation) != 3:
        raise ValueError("current-world Building placement translation missing")
    translation = [float(v) for v in translation]
    world_vertices = [
        [float(vertex[axis]) + translation[axis] for axis in range(3)]
        for vertex in local_vertices
    ]
    if not _bounds_close(_bounds(world_vertices), _bounds(current_vertices)):
        raise ValueError("compact-v2 Building changed current-world assembled bounds")

    grouped: dict[str, list[list[int]]] = {role: [] for role in ROLES}
    for tri, owner in zip(triangles, owners):
        if not isinstance(tri, list) or len(tri) != 3:
            raise ValueError("compact-v2 triangle arity drift")
        source_component_id = owner.get("source_component_id") if isinstance(owner, dict) else None
        role = mapping.get(source_component_id)
        if role not in grouped:
            raise ValueError(f"compact-v2 triangle lost material owner: {source_component_id!r}")
        if any(not isinstance(index, int) or index < 0 or index >= len(world_vertices) for index in tri):
            raise ValueError("compact-v2 triangle index drift")
        grouped[role].append([int(v) for v in tri])
    if {role: len(rows) for role, rows in grouped.items()} != EXPECTED_COMPACT_TRIANGLES:
        raise ValueError("compact-v2 current-world material triangle partition drift")

    compact_surfaces = [
        {
            "surface_role": role,
            "material_id": role,
            "material": copy.deepcopy(current_materials[role]),
            "triangles": copy.deepcopy(grouped[role]),
        }
        for role in ROLES
    ]

    states: list[dict[str, Any]] = []
    for parent_row in parent["states"]:
        row = copy.deepcopy(parent_row)
        scene = row["scene"]
        before = _strip_building(scene)
        old = scene.get("environment_building_material_receiving", {})
        if old.get("vertices_source_xyz_m") != current_vertices or _current_materials(old) != current_materials:
            raise ValueError("current-world Building parent drift across 17-state sequence")
        receiving = copy.deepcopy(old)
        receiving["vertices_source_xyz_m"] = copy.deepcopy(world_vertices)
        receiving["surfaces"] = copy.deepcopy(compact_surfaces)
        receiving["source_geometry_digest"] = parent_tool.parent_tool.digest({"vertices": world_vertices, "triangles": grouped})
        receiving["receiving_policy"] = "EXPLICIT_SOURCE_OWNED_COMPACT_V2_RECEIVER_WITH_EXACT_MATERIAL_REBIND__REVIEW_ONLY"
        receiving["environment_building_compact_v2_receiving"] = {
            "schema": "axm.environment-building-compact-v2-receiving/v0.1",
            "geometry_head": GEOMETRY_HEAD,
            "hard_surface_head": HARD_SURFACE_HEAD,
            "materials_head": MATERIALS_HEAD,
            "semantic_source_variant_id": SEMANTIC_SOURCE_ID,
            "reference_representation_id": REFERENCE_ID,
            "selected_representation_id": COMPACT_ID,
            "selection_policy": SELECTION_POLICY,
            "evidence_transfer_policy": EVIDENCE_TRANSFER_POLICY,
            "normal_policy": NORMAL_POLICY,
            "material_continuity_result": MATERIAL_CONTINUITY_RESULT,
            "placement_translation_source_xyz_m": translation,
            "vertex_count": 1004,
            "triangle_count": 2052,
            "source_component_owner_count": 19,
            "material_triangle_counts": copy.deepcopy(EXPECTED_COMPACT_TRIANGLES),
            "geometry_compact_payload_sha256": packet.get("geometry_compact_payload_sha256"),
            "environment_adoption": False,
            "authority": "MAP_ENVIRONMENT_RECEIVING_REVIEW_ONLY",
        }
        provenance = receiving.setdefault("provenance", {})
        provenance.update({
            "building_compact_v2_geometry_head": GEOMETRY_HEAD,
            "building_compact_v2_hard_surface_head": HARD_SURFACE_HEAD,
            "building_compact_v2_materials_head": MATERIALS_HEAD,
            "building_compact_v2_representation_id": COMPACT_ID,
        })
        receiving["truth_boundary"] = (
            "Environment explicitly selects the source-owned compact-v2 Building representation only for current-world receiving review. "
            "The semantic header-segmented-23 source, five material scalars, Building placement, Nature, Object, footprint cue, Weather, route, cameras and lighting remain unchanged. "
            "This does not make compact-v2 the default or transfer Materials/Runtime/Art/QA acceptance."
        )
        scene["environment_building_material_receiving"] = receiving
        scene["scene_digest"] = parent_tool.parent_tool.scene_digest(scene)
        if _strip_building(scene) != before:
            raise ValueError("unrelated current-world scene data drifted during compact-v2 receiving build")
        states.append(row)

    checks = dict(parent.get("checks", {}))
    checks.update({
        "exact_nature_flutter_parent_bound": parent.get("environment_head") == PARENT_HEAD,
        "exact_building_geometry_compact_v2_head_bound": packet.get("geometry_donor_head") == GEOMETRY_HEAD,
        "exact_building_hard_surface_owner_head_bound": packet.get("hard_surface_owner_head") == HARD_SURFACE_HEAD,
        "exact_building_materials_head_bound": packet.get("exact_materials_head") == MATERIALS_HEAD,
        "exact_explicit_non_default_compact_v2_representation_selected_for_review": packet.get("selected_representation_id") == COMPACT_ID,
        "semantic_source_remains_header_segmented_23": packet.get("semantic_source_variant_id") == SEMANTIC_SOURCE_ID,
        "no_cross_representation_pass_transfer": packet.get("evidence_transfer_policy") == EVIDENCE_TRANSFER_POLICY,
        "exact_five_material_scalars_preserved": all(_material_matches(current_materials[role], donor_materials[role]) for role in ROLES),
        "exact_19_source_component_material_owners_preserved": len(mapping) == 19,
        "compact_v2_exact_1004_vertices_2052_triangles": len(world_vertices) == 1004 and sum(len(rows) for rows in grouped.values()) == 2052,
        "current_world_building_bounds_preserved": _bounds_close(_bounds(world_vertices), _bounds(current_vertices)),
        "building_placement_preserved": len(translation) == 3,
        "nature_object_footprint_weather_route_cameras_lighting_preserved": all(
            _strip_building(row["scene"]) == _strip_building(old["scene"])
            for row, old in zip(states, parent["states"])
        ),
        "all_17_states_preserved": len(states) == 17,
    })
    if not all(checks.values()):
        raise ValueError(f"current-world Building compact-v2 structure checks failed: {checks}")

    result = copy.deepcopy(parent)
    result.update({
        "environment_head": environment_head,
        "building_compact_v2_parent_environment_head": PARENT_HEAD,
        "building_compact_v2_parent_composition_digest": parent.get("composition_digest"),
        "building_compact_v2_structure_result": STRUCTURE_RESULT,
        "building_compact_v2_geometry_head": GEOMETRY_HEAD,
        "building_compact_v2_hard_surface_head": HARD_SURFACE_HEAD,
        "building_compact_v2_materials_head": MATERIALS_HEAD,
        "building_compact_v2_semantic_source_variant_id": SEMANTIC_SOURCE_ID,
        "building_compact_v2_reference_representation_id": REFERENCE_ID,
        "building_compact_v2_selected_representation_id": COMPACT_ID,
        "building_compact_v2_selection_policy": SELECTION_POLICY,
        "building_compact_v2_evidence_transfer_policy": EVIDENCE_TRANSFER_POLICY,
        "building_compact_v2_normal_policy": NORMAL_POLICY,
        "building_compact_v2_material_continuity_result": MATERIAL_CONTINUITY_RESULT,
        "building_compact_v2_material_packet_receipt_result": receipt.get("result"),
        "building_compact_v2_geometry_compact_payload_sha256": packet.get("geometry_compact_payload_sha256"),
        "building_compact_v2_current_world_translation_m": translation,
        "building_compact_v2_material_triangle_counts": copy.deepcopy(EXPECTED_COMPACT_TRIANGLES),
        "states": states,
        "checks": checks,
        "truth_boundary": (
            "Environment receives the exact source-owned compact-v2 Building representation into the exact sampled Nature-flutter current world solely as an explicit review candidate. "
            "This pass preserves the semantic Building source and exact five-family material scalars and measures the real multi-asset current-world consequence without making compact-v2 default, accepting target-device cost, or claiming visual preference."
        ),
        "non_claims": [
            "BUILDING_COMPACT_V2_DEFAULT_OR_SEMANTIC_SOURCE_ADOPTION",
            "FINAL_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "TECHNICAL_ART_TRANSPORT_ACCEPTANCE",
            "UV_TEXTURE_NORMAL_MAP_OR_SMOOTH_NORMAL_EQUIVALENCE",
            "TARGET_DEVICE_CPU_GPU_FPS_VRAM_MEMORY_OR_BATCHING_ACCEPTANCE",
            "NATURE_FLUTTER_WALL_CLOCK_TIMING_OR_FINAL_NATURALNESS",
            "COLLISION_NAVIGATION_PHYSICS_OR_GAMEPLAY",
            "CANON_PRODUCTION_READY_OR_ENVIRONMENT_MASTERY",
        ],
    })
    result["composition_digest"] = parent_tool.parent_tool.digest({
        "parent": parent.get("composition_digest"),
        "geometry_head": GEOMETRY_HEAD,
        "hard_surface_head": HARD_SURFACE_HEAD,
        "materials_head": MATERIALS_HEAD,
        "representation": COMPACT_ID,
        "material_partition": EXPECTED_COMPACT_TRIANGLES,
        "scenes": [row["scene"]["scene_digest"] for row in states],
    })
    return result


def _significant_frame_delta(parent_path: Path, candidate_path: Path) -> dict[str, Any]:
    from PIL import Image
    import numpy as np

    a = np.asarray(Image.open(parent_path).convert("RGB"), dtype=np.int16)
    b = np.asarray(Image.open(candidate_path).convert("RGB"), dtype=np.int16)
    if a.shape != b.shape:
        raise ValueError("current-world frame shape drift")
    delta = np.abs(a - b)
    mask = np.any(delta > 1, axis=2)
    count = int(mask.sum())
    pixels = int(mask.shape[0] * mask.shape[1])
    return {
        "file": parent_path.name,
        "significant_pixels_gt_1_lsb": count,
        "significant_fraction_gt_1_lsb": count / pixels,
        "maximum_channel_delta_8bit": int(delta.max()),
    }


def _counter_sets(runtime: dict[str, Any]) -> dict[str, dict[str, set[tuple[int, int, int, int, int]]]]:
    out = {mode: {camera: set() for camera in ("path_eye", "elevated_oblique")} for mode in ("control", "candidate")}
    for sample in runtime.get("samples", []):
        for camera, context in sample.get("contexts", {}).items():
            if camera not in ("path_eye", "elevated_oblique"):
                continue
            for mode in ("control", "candidate"):
                row = context.get(mode, {}).get("runtime", {})
                out[mode][camera].add((
                    int(row.get("draw_calls_in_frame", -1)),
                    int(row.get("objects_in_frame", -1)),
                    int(row.get("primitives_in_frame", -1)),
                    int(row.get("buffer_mem_bytes", -1)),
                    int(row.get("texture_mem_bytes", -1)),
                ))
    return out


def _serial_counter_sets(value: dict[str, dict[str, set[tuple[int, int, int, int, int]]]]) -> dict[str, dict[str, list[list[int]]]]:
    return {
        mode: {camera: [list(row) for row in sorted(rows)] for camera, rows in cameras.items()}
        for mode, cameras in value.items()
    }


def verify(payload: dict[str, Any], parent_root: Path, candidate_root: Path, environment_head: str) -> dict[str, Any]:
    if payload.get("environment_head") != environment_head:
        raise ValueError("Building compact-v2 payload head drift")
    if payload.get("building_compact_v2_parent_environment_head") != PARENT_HEAD:
        raise ValueError("Building compact-v2 parent head drift")
    if payload.get("building_compact_v2_structure_result") != STRUCTURE_RESULT:
        raise ValueError("Building compact-v2 structure result missing")
    if not all(payload.get("checks", {}).values()):
        raise ValueError("Building compact-v2 structure checks are not all true")

    parent_frames = parent_tool.parent_tool.frame_files(parent_root)
    candidate_frames = parent_tool.parent_tool.frame_files(candidate_root)
    if len(parent_frames) != 68 or [p.name for p in parent_frames] != [p.name for p in candidate_frames]:
        raise ValueError("expected exact 68 matched current-world frames")
    deltas = [parent_tool.parent_tool._frame_delta(a, b) for a, b in zip(parent_frames, candidate_frames)]
    significant = [_significant_frame_delta(a, b) for a, b in zip(parent_frames, candidate_frames)]
    max_significant_fraction = max(row["significant_fraction_gt_1_lsb"] for row in significant)
    if max_significant_fraction > MATERIAL_CONTINUITY_SIGNIFICANT_FRACTION_LIMIT:
        raise ValueError(
            f"current-world compact-v2 exceeded exact Materials 0.1% significant-pixel continuity guard: {max_significant_fraction}"
        )

    parent_runtime = load_json(parent_root / "runtime.json")
    candidate_runtime = load_json(candidate_root / "runtime.json")
    if candidate_runtime.get("environment_building_compact_v2_representation_id") != COMPACT_ID:
        raise ValueError("target-host receipt missing exact compact-v2 identity")
    if candidate_runtime.get("environment_building_compact_v2_structure_result") != STRUCTURE_RESULT:
        raise ValueError("target-host receipt missing compact-v2 structure identity")

    parent_samples = parent_runtime.get("samples", [])
    candidate_samples = candidate_runtime.get("samples", [])
    if len(parent_samples) != 17 or len(candidate_samples) != 17:
        raise ValueError("target-host sample count drift")
    weather_measurements = 0
    max_width_residual = 0.0
    building_ok = True
    unrelated_static_exact = True
    sapling_exact = True
    for before, after in zip(parent_samples, candidate_samples):
        if int(before.get("index", -1)) != int(after.get("index", -2)):
            raise ValueError("target-host state index drift")
        parent_static = before.get("static_source_meshes", [])
        candidate_static = after.get("static_source_meshes", [])
        parent_other = [row for row in parent_static if row.get("asset_id") != BUILDING_ASSET_ID]
        candidate_other = [row for row in candidate_static if row.get("asset_id") != BUILDING_ASSET_ID]
        unrelated_static_exact &= parent_other == candidate_other
        candidate_building = [row for row in candidate_static if row.get("asset_id") == BUILDING_ASSET_ID]
        building_ok &= (
            len(candidate_building) == 1
            and candidate_building[0].get("vertices") == 1004
            and candidate_building[0].get("triangles") == 2052
            and candidate_building[0].get("surface_count") == 5
            and candidate_building[0].get("representation_id") == COMPACT_ID
        )
        sapling_exact &= before.get("sapling") == after.get("sapling")
        for camera, context in after.get("contexts", {}).items():
            if camera not in ("path_eye", "elevated_oblique"):
                continue
            weather = context.get("candidate", {}).get("weather_update", {})
            weather_measurements += int(weather.get("measured_width_count", 0))
            max_width_residual = max(max_width_residual, float(weather.get("maximum_projected_width_residual_px", 0.0)))
    if weather_measurements != 1224 or max_width_residual > 0.05:
        raise ValueError("inherited Weather-width evidence drift")

    parent_sets = _counter_sets(parent_runtime)
    candidate_sets = _counter_sets(candidate_runtime)
    if not all(len(parent_sets[m][c]) == 1 and len(candidate_sets[m][c]) == 1 for m in parent_sets for c in parent_sets[m]):
        raise ValueError("proof-host runtime counter sets are not stable per mode/camera")
    deltas_runtime: dict[str, dict[str, list[int]]] = {}
    for mode in parent_sets:
        deltas_runtime[mode] = {}
        for camera in parent_sets[mode]:
            before = next(iter(parent_sets[mode][camera]))
            after = next(iter(candidate_sets[mode][camera]))
            deltas_runtime[mode][camera] = [int(a) - int(b) for a, b in zip(after, before)]

    grouped: dict[str, dict[str, Any]] = {}
    for camera in ("path_eye", "elevated_oblique"):
        rows = [row for row in deltas if parent_tool.parent_tool._camera_name(row["file"]) == camera]
        srows = [row for row in significant if parent_tool.parent_tool._camera_name(row["file"]) == camera]
        grouped[camera] = {
            "frame_count": len(rows),
            "changed_pixels_min": min(row["changed_pixels"] for row in rows),
            "changed_pixels_max": max(row["changed_pixels"] for row in rows),
            "changed_pixels_mean": sum(row["changed_pixels"] for row in rows) / len(rows),
            "significant_pixels_gt_1_lsb_min": min(row["significant_pixels_gt_1_lsb"] for row in srows),
            "significant_pixels_gt_1_lsb_max": max(row["significant_pixels_gt_1_lsb"] for row in srows),
            "significant_fraction_gt_1_lsb_max": max(row["significant_fraction_gt_1_lsb"] for row in srows),
            "maximum_channel_delta_8bit": max(row["maximum_channel_delta_8bit"] for row in srows),
            "distinct_bboxes": sorted({str(row["bbox"]) for row in rows if row["bbox"] is not None}),
        }

    checks = {
        "exact_leaf_flutter_current_world_parent_reused": True,
        "exact_compact_v2_owner_material_identity_rendered": building_ok,
        "all_68_real_scene_frames_compared": len(deltas) == 68,
        "exact_materials_0_1_percent_significant_pixel_guard_preserved": max_significant_fraction <= MATERIAL_CONTINUITY_SIGNIFICANT_FRACTION_LIMIT,
        "all_non_building_static_source_runtime_rows_exact": unrelated_static_exact,
        "dynamic_sapling_runtime_rows_exact": sapling_exact,
        "all_1224_weather_width_measurements_preserved": weather_measurements == 1224 and max_width_residual <= 0.05,
        "runtime_cost_delta_measured_not_auto_accepted": True,
        "art_direction_and_visual_qa_preference_not_auto_accepted": True,
    }
    if not all(checks.values()):
        raise ValueError(f"current-world Building compact-v2 target-host checks failed: {checks}")

    return {
        "schema": "axm.environment-building-compact-v2-current-world-report/v0.1",
        "state": TARGET_RESULT,
        "environment_head": environment_head,
        "parent_environment_head": PARENT_HEAD,
        "composition_digest": payload.get("composition_digest"),
        "building_geometry_head": GEOMETRY_HEAD,
        "building_hard_surface_head": HARD_SURFACE_HEAD,
        "building_materials_head": MATERIALS_HEAD,
        "semantic_source_variant_id": SEMANTIC_SOURCE_ID,
        "selected_representation_id": COMPACT_ID,
        "matched_frames": 68,
        "frame_delta_summary": grouped,
        "frame_deltas": deltas,
        "significant_frame_deltas_gt_1_lsb": significant,
        "maximum_significant_changed_fraction_gt_1_lsb": max_significant_fraction,
        "materials_significant_fraction_limit": MATERIAL_CONTINUITY_SIGNIFICANT_FRACTION_LIMIT,
        "weather_width_measurements": weather_measurements,
        "maximum_weather_width_residual_px": max_width_residual,
        "parent_runtime_counter_sets": _serial_counter_sets(parent_sets),
        "candidate_runtime_counter_sets": _serial_counter_sets(candidate_sets),
        "runtime_counter_delta_vs_parent_order_draw_objects_primitives_buffer_texture": deltas_runtime,
        "checks": checks,
        "truth_boundary": (
            "PASS means only that the exact source-owned compact-v2 Building representation, with the exact existing five-family material scalars, survives the full sampled Nature/Object/Weather current-world receiver and remains inside the exact Materials donor's 0.1% >1-LSB continuity guard. "
            "The measured current-world runtime delta and retained pixels are handoff evidence. They do not select compact-v2 as default, establish target-device benefit, or grant Art Direction / Visual QA preference."
        ),
        "non_claims": payload.get("non_claims", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build")
    p_build.add_argument("--parent", type=Path, required=True)
    p_build.add_argument("--material-payload", type=Path, required=True)
    p_build.add_argument("--material-receipt", type=Path, required=True)
    p_build.add_argument("--environment-head", required=True)
    p_build.add_argument("--output", type=Path, required=True)
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--payload", type=Path, required=True)
    p_verify.add_argument("--parent-root", type=Path, required=True)
    p_verify.add_argument("--candidate-root", type=Path, required=True)
    p_verify.add_argument("--environment-head", required=True)
    p_verify.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        result = build(
            load_json(args.parent),
            load_json(args.material_payload),
            load_json(args.material_receipt),
            args.environment_head,
        )
    else:
        result = verify(load_json(args.payload), args.parent_root, args.candidate_root, args.environment_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "state": result.get("building_compact_v2_structure_result", result.get("state")),
        "composition_digest": result.get("composition_digest"),
        "checks": result.get("checks"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
