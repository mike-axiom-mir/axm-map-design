from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import environment_building_compact_v2_current_world as compact_tool

PARENT_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
HARD_SURFACE_HEAD = "93f22e4eeb9bb32516d4b11f8d8bcf47d9792910"
MATERIALS_HEAD = "4179aa1401f5a9114399e2f998c96809d4b8ed2e"
MATERIAL_PROFILE_BLOB = "f7945f4c17b7720f176c1b0ac4e1baa298691b25"
SEMANTIC_SOURCE_ID = "header-segmented-23"
CANDIDATE_ID = "boundary-only-planar-role-rectangle-render-001"
POLICY_SCHEMA = "axm.building-planar-role-render-receiver-policy/v0.1"
SELECTION_POLICY = "EXPLICIT_RECEIVING_REPRESENTATION_ID_REQUIRED__NO_DEFAULT_OR_IMPLICIT_FALLBACK"
EVIDENCE_TRANSFER_POLICY = "NO_PASS_TRANSFER_FROM_COMPACT_V2_OR_SEGMENTED_RECEIVER__EXACT_ENVIRONMENT_RUNTIME_ART_QA_REBIND_REQUIRED"
DONOR_RESULT = "PASS_STRUCTURAL_PLANAR_ROLE_RECTANGLE_RENDER_RECEIVER_CANDIDATE"
BUILDING_ASSET_ID = "source:building:service-pavilion-001"
ROLES = compact_tool.ROLES
STRUCTURE_RESULT = "PASS_CURRENT_WORLD_BUILDING_PLANAR_ROLE_RENDER_RECEIVER_STRUCTURE"
TARGET_RESULT = "PASS_CURRENT_WORLD_BUILDING_PLANAR_ROLE_RENDER_RECEIVER_REVIEW_READY"
EXPECTED_VERTICES = 672
EXPECTED_TRIANGLES = 336
EXPECTED_RECTANGLES = 168
EXPECTED_OWNERS = 19
EPS = 1e-9


def load_json(path: Path) -> dict[str, Any]:
    return compact_tool.load_json(path)


def _validate_donor(candidate: dict[str, Any], evidence: dict[str, Any], policy: dict[str, Any]) -> None:
    if evidence.get("result") != DONOR_RESULT:
        raise ValueError("planar-role donor evidence is not green")
    if evidence.get("exact_hard_surface_head") != HARD_SURFACE_HEAD:
        raise ValueError("planar-role Hard-Surface head drift")
    if evidence.get("schema") != POLICY_SCHEMA or policy.get("schema") != POLICY_SCHEMA:
        raise ValueError("planar-role policy schema drift")
    if evidence.get("representation_id") != CANDIDATE_ID:
        raise ValueError("planar-role evidence identity drift")
    if policy.get("candidate", {}).get("representation_id") != CANDIDATE_ID:
        raise ValueError("planar-role policy identity drift")
    if policy.get("candidate", {}).get("status") != "SOURCE_OWNED_DERIVED_RENDER_RECEIVING_OPTION_NOT_DEFAULT":
        raise ValueError("planar-role donor unexpectedly became default")
    if policy.get("selection_policy") != SELECTION_POLICY:
        raise ValueError("planar-role selection policy drift")
    if policy.get("evidence_transfer_policy") != EVIDENCE_TRANSFER_POLICY:
        raise ValueError("planar-role evidence-transfer policy drift")
    if policy.get("semantic_source", {}).get("variant_id") != SEMANTIC_SOURCE_ID:
        raise ValueError("planar-role semantic source drift")
    material = policy.get("material_role_binding", {})
    if material.get("donor_head") != MATERIALS_HEAD or material.get("profile_git_blob_sha") != MATERIAL_PROFILE_BLOB:
        raise ValueError("planar-role pinned Materials identity drift")
    role_map = material.get("source_component_material_roles", {})
    if len(role_map) != EXPECTED_OWNERS or set(role_map.values()) != set(ROLES):
        raise ValueError("planar-role five-role Materials partition drift")
    metrics = evidence.get("candidate", {})
    if (
        metrics.get("vertex_count") != EXPECTED_VERTICES
        or metrics.get("triangle_count") != EXPECTED_TRIANGLES
        or metrics.get("rectangle_count") != EXPECTED_RECTANGLES
        or metrics.get("source_owner_count") != EXPECTED_OWNERS
        or metrics.get("role_count") != 5
        or not metrics.get("atomic_coverage_complete", False)
        or metrics.get("atomic_overlap_count") != 0
        or not metrics.get("cardinal_hard_normals_only", False)
    ):
        raise ValueError("planar-role donor metrics drift")
    if candidate.get("representation_id") != CANDIDATE_ID or candidate.get("schema") != POLICY_SCHEMA:
        raise ValueError("planar-role retained candidate identity drift")
    if (
        len(candidate.get("vertices", [])) != EXPECTED_VERTICES
        or len(candidate.get("triangles", [])) != EXPECTED_TRIANGLES
        or len(candidate.get("triangle_roles", [])) != EXPECTED_TRIANGLES
        or len(candidate.get("rectangles", [])) != EXPECTED_RECTANGLES
    ):
        raise ValueError("planar-role retained candidate cardinality drift")
    if set(candidate.get("triangle_roles", [])) != set(ROLES):
        raise ValueError("planar-role retained candidate lost material roles")


def build(parent: dict[str, Any], candidate: dict[str, Any], evidence: dict[str, Any], policy: dict[str, Any], environment_head: str) -> dict[str, Any]:
    compact_tool._validate_parent(parent)
    _validate_donor(candidate, evidence, policy)

    first_receiving = parent["states"][0]["scene"].get("environment_building_material_receiving", {})
    if first_receiving.get("asset_id") != BUILDING_ASSET_ID:
        raise ValueError("current-world Building receiver missing")
    current_vertices = first_receiving.get("vertices_source_xyz_m", [])
    if len(current_vertices) != 184:
        raise ValueError("current-world parent must retain exact 184-vertex Building receiver")
    current_materials = compact_tool._current_materials(first_receiving)

    segmentation = first_receiving.get("source_header_segmentation_rebind", {})
    translation = segmentation.get("placement_translation_source_xyz_m", [])
    if not isinstance(translation, list) or len(translation) != 3:
        raise ValueError("current-world Building placement translation missing")
    translation = [float(v) for v in translation]

    local_vertices = candidate["vertices"]
    triangles = candidate["triangles"]
    triangle_roles = candidate["triangle_roles"]
    world_vertices = [
        [float(vertex[axis]) + translation[axis] for axis in range(3)]
        for vertex in local_vertices
    ]
    if not compact_tool._bounds_close(compact_tool._bounds(world_vertices), compact_tool._bounds(current_vertices)):
        raise ValueError("planar-role Building changed current-world assembled bounds")

    grouped: dict[str, list[list[int]]] = {role: [] for role in ROLES}
    for tri, role in zip(triangles, triangle_roles):
        if role not in grouped or not isinstance(tri, list) or len(tri) != 3:
            raise ValueError("planar-role triangle/material partition drift")
        if any(not isinstance(index, int) or index < 0 or index >= len(world_vertices) for index in tri):
            raise ValueError("planar-role triangle index drift")
        grouped[role].append([int(v) for v in tri])
    role_counts = {role: len(grouped[role]) for role in ROLES}
    if sum(role_counts.values()) != EXPECTED_TRIANGLES or any(value <= 0 for value in role_counts.values()):
        raise ValueError("planar-role current-world five-role triangle counts drift")

    candidate_surfaces = [
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
        before = compact_tool._strip_building(scene)
        old = scene.get("environment_building_material_receiving", {})
        if old.get("vertices_source_xyz_m") != current_vertices or compact_tool._current_materials(old) != current_materials:
            raise ValueError("current-world Building parent drift across 17-state sequence")
        receiving = copy.deepcopy(old)
        receiving["vertices_source_xyz_m"] = copy.deepcopy(world_vertices)
        receiving["surfaces"] = copy.deepcopy(candidate_surfaces)
        receiving["source_geometry_digest"] = compact_tool.parent_tool.parent_tool.digest({"vertices": world_vertices, "triangles": grouped})
        receiving["receiving_policy"] = "EXPLICIT_SOURCE_OWNED_PLANAR_ROLE_RENDER_RECEIVER__CURRENT_WORLD_REVIEW_ONLY"
        receiving["environment_building_planar_role_receiving"] = {
            "schema": "axm.environment-building-planar-role-receiving/v0.1",
            "hard_surface_head": HARD_SURFACE_HEAD,
            "materials_head": MATERIALS_HEAD,
            "material_profile_blob": MATERIAL_PROFILE_BLOB,
            "semantic_source_variant_id": SEMANTIC_SOURCE_ID,
            "selected_representation_id": CANDIDATE_ID,
            "selection_policy": SELECTION_POLICY,
            "evidence_transfer_policy": EVIDENCE_TRANSFER_POLICY,
            "placement_translation_source_xyz_m": translation,
            "vertex_count": EXPECTED_VERTICES,
            "triangle_count": EXPECTED_TRIANGLES,
            "rectangle_count": EXPECTED_RECTANGLES,
            "source_component_owner_count": EXPECTED_OWNERS,
            "material_triangle_counts": copy.deepcopy(role_counts),
            "environment_adoption": False,
            "authority": "MAP_ENVIRONMENT_RECEIVING_REVIEW_ONLY",
        }
        receiving.setdefault("provenance", {}).update({
            "building_planar_role_hard_surface_head": HARD_SURFACE_HEAD,
            "building_planar_role_materials_head": MATERIALS_HEAD,
            "building_planar_role_representation_id": CANDIDATE_ID,
        })
        receiving["truth_boundary"] = (
            "Environment selects the source-owned planar-role Building representation only for current-world review. "
            "The semantic header-segmented-23 source, exact existing five material scalars, Building placement, Nature, Object, footprint cue, Weather, route, cameras and lighting remain unchanged. "
            "This does not make the render receiver default or transfer Runtime, Art/QA or Technical-Art acceptance."
        )
        scene["environment_building_material_receiving"] = receiving
        scene["scene_digest"] = compact_tool.parent_tool.parent_tool.scene_digest(scene)
        if compact_tool._strip_building(scene) != before:
            raise ValueError("unrelated current-world scene data drifted during planar-role receiving build")
        states.append(row)

    checks = dict(parent.get("checks", {}))
    checks.update({
        "exact_nature_flutter_parent_bound": parent.get("environment_head") == PARENT_HEAD,
        "exact_planar_role_hard_surface_head_bound": evidence.get("exact_hard_surface_head") == HARD_SURFACE_HEAD,
        "exact_pinned_building_materials_identity_bound": policy.get("material_role_binding", {}).get("donor_head") == MATERIALS_HEAD,
        "exact_non_default_planar_role_representation_selected_for_review": candidate.get("representation_id") == CANDIDATE_ID,
        "semantic_source_remains_header_segmented_23": policy.get("semantic_source", {}).get("variant_id") == SEMANTIC_SOURCE_ID,
        "no_cross_representation_pass_transfer": policy.get("evidence_transfer_policy") == EVIDENCE_TRANSFER_POLICY,
        "exact_existing_five_material_scalars_preserved": all(compact_tool._material_matches(current_materials[role], current_materials[role]) for role in ROLES),
        "planar_role_exact_672_vertices_336_triangles_168_rectangles": len(world_vertices) == EXPECTED_VERTICES and sum(role_counts.values()) == EXPECTED_TRIANGLES and len(candidate["rectangles"]) == EXPECTED_RECTANGLES,
        "current_world_building_bounds_preserved": compact_tool._bounds_close(compact_tool._bounds(world_vertices), compact_tool._bounds(current_vertices)),
        "nature_object_footprint_weather_route_cameras_lighting_preserved": all(
            compact_tool._strip_building(row["scene"]) == compact_tool._strip_building(old["scene"])
            for row, old in zip(states, parent["states"])
        ),
        "all_17_states_preserved": len(states) == 17,
    })
    if not all(checks.values()):
        raise ValueError(f"current-world Building planar-role structure checks failed: {checks}")

    result = copy.deepcopy(parent)
    result.update({
        "environment_head": environment_head,
        "building_planar_role_parent_environment_head": PARENT_HEAD,
        "building_planar_role_parent_composition_digest": parent.get("composition_digest"),
        "building_planar_role_structure_result": STRUCTURE_RESULT,
        "building_planar_role_hard_surface_head": HARD_SURFACE_HEAD,
        "building_planar_role_materials_head": MATERIALS_HEAD,
        "building_planar_role_material_profile_blob": MATERIAL_PROFILE_BLOB,
        "building_planar_role_semantic_source_variant_id": SEMANTIC_SOURCE_ID,
        "building_planar_role_selected_representation_id": CANDIDATE_ID,
        "building_planar_role_selection_policy": SELECTION_POLICY,
        "building_planar_role_evidence_transfer_policy": EVIDENCE_TRANSFER_POLICY,
        "building_planar_role_current_world_translation_m": translation,
        "building_planar_role_material_triangle_counts": role_counts,
        "building_planar_role_source_payload_sha256": evidence.get("candidate", {}).get("payload_sha256"),
        "states": states,
        "checks": checks,
        "truth_boundary": (
            "Environment receives the exact source-owned planar-role Building render candidate into the exact accepted sampled Nature-flutter world and measures its real multi-asset consequence against both the active segmented receiver and compact-v2. "
            "No visual preference, default adoption, target-device performance or transport acceptance is implied by structural receiving success."
        ),
        "non_claims": [
            "BUILDING_PLANAR_ROLE_DEFAULT_OR_SEMANTIC_SOURCE_ADOPTION",
            "FINAL_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "TECHNICAL_ART_TRANSPORT_ACCEPTANCE",
            "UV_TEXTURE_TANGENT_NORMAL_MAP_OR_DECAL_EQUIVALENCE",
            "TARGET_DEVICE_CPU_GPU_FPS_VRAM_MEMORY_OR_BATCHING_ACCEPTANCE",
            "NATURE_FLUTTER_WALL_CLOCK_TIMING_OR_FINAL_NATURALNESS",
            "COLLISION_NAVIGATION_PHYSICS_MANUFACTURING_OR_GAMEPLAY",
            "CANON_PRODUCTION_READY_OR_ENVIRONMENT_MASTERY",
        ],
    })
    result["composition_digest"] = compact_tool.parent_tool.parent_tool.digest({
        "parent": parent.get("composition_digest"),
        "hard_surface_head": HARD_SURFACE_HEAD,
        "materials_head": MATERIALS_HEAD,
        "representation": CANDIDATE_ID,
        "material_partition": role_counts,
        "scenes": [row["scene"]["scene_digest"] for row in states],
    })
    return result


def _group_frame_deltas(rows: list[dict[str, Any]], significant: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for camera in ("path_eye", "elevated_oblique"):
        cam_rows = [row for row in rows if compact_tool.parent_tool.parent_tool._camera_name(row["file"]) == camera]
        sig_rows = [row for row in significant if compact_tool.parent_tool.parent_tool._camera_name(row["file"]) == camera]
        grouped[camera] = {
            "frame_count": len(cam_rows),
            "changed_pixels_min": min(row["changed_pixels"] for row in cam_rows),
            "changed_pixels_max": max(row["changed_pixels"] for row in cam_rows),
            "changed_pixels_mean": sum(row["changed_pixels"] for row in cam_rows) / len(cam_rows),
            "significant_pixels_gt_1_lsb_min": min(row["significant_pixels_gt_1_lsb"] for row in sig_rows),
            "significant_pixels_gt_1_lsb_max": max(row["significant_pixels_gt_1_lsb"] for row in sig_rows),
            "significant_fraction_gt_1_lsb_max": max(row["significant_fraction_gt_1_lsb"] for row in sig_rows),
            "maximum_channel_delta_8bit": max(row["maximum_channel_delta_8bit"] for row in sig_rows),
            "distinct_bboxes": sorted({str(row["bbox"]) for row in cam_rows if row["bbox"] is not None}),
        }
    return grouped


def _runtime_delta(before_runtime: dict[str, Any], after_runtime: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, list[int]]]]:
    before_sets = compact_tool._counter_sets(before_runtime)
    after_sets = compact_tool._counter_sets(after_runtime)
    if not all(len(before_sets[m][c]) == 1 and len(after_sets[m][c]) == 1 for m in before_sets for c in before_sets[m]):
        raise ValueError("proof-host runtime counter sets are not stable per mode/camera")
    delta: dict[str, dict[str, list[int]]] = {}
    for mode in before_sets:
        delta[mode] = {}
        for camera in before_sets[mode]:
            before = next(iter(before_sets[mode][camera]))
            after = next(iter(after_sets[mode][camera]))
            delta[mode][camera] = [int(a) - int(b) for a, b in zip(after, before)]
    return before_sets, after_sets, delta


def verify(payload: dict[str, Any], parent_root: Path, compact_root: Path, candidate_root: Path, environment_head: str) -> dict[str, Any]:
    if payload.get("environment_head") != environment_head:
        raise ValueError("planar-role payload head drift")
    if payload.get("building_planar_role_parent_environment_head") != PARENT_HEAD:
        raise ValueError("planar-role parent head drift")
    if payload.get("building_planar_role_structure_result") != STRUCTURE_RESULT or not all(payload.get("checks", {}).values()):
        raise ValueError("planar-role structure evidence is not green")

    active_frames = compact_tool.parent_tool.parent_tool.frame_files(parent_root)
    compact_frames = compact_tool.parent_tool.parent_tool.frame_files(compact_root)
    candidate_frames = compact_tool.parent_tool.parent_tool.frame_files(candidate_root)
    names = [p.name for p in active_frames]
    if len(names) != 68 or names != [p.name for p in compact_frames] or names != [p.name for p in candidate_frames]:
        raise ValueError("expected exact 68 matched active/compact/planar current-world frames")

    active_deltas = [compact_tool.parent_tool.parent_tool._frame_delta(a, b) for a, b in zip(active_frames, candidate_frames)]
    active_significant = [compact_tool._significant_frame_delta(a, b) for a, b in zip(active_frames, candidate_frames)]
    compact_deltas = [compact_tool.parent_tool.parent_tool._frame_delta(a, b) for a, b in zip(compact_frames, candidate_frames)]
    compact_significant = [compact_tool._significant_frame_delta(a, b) for a, b in zip(compact_frames, candidate_frames)]

    active_runtime = load_json(parent_root / "runtime.json")
    compact_runtime = load_json(compact_root / "runtime.json")
    candidate_runtime = load_json(candidate_root / "runtime.json")
    if candidate_runtime.get("environment_building_planar_role_representation_id") != CANDIDATE_ID:
        raise ValueError("target-host receipt missing exact planar-role identity")
    if candidate_runtime.get("environment_building_planar_role_structure_result") != STRUCTURE_RESULT:
        raise ValueError("target-host receipt missing planar-role structure identity")

    active_samples = active_runtime.get("samples", [])
    candidate_samples = candidate_runtime.get("samples", [])
    if len(active_samples) != 17 or len(candidate_samples) != 17:
        raise ValueError("target-host sample count drift")
    weather_measurements = 0
    max_width_residual = 0.0
    building_ok = True
    unrelated_static_exact = True
    sapling_exact = True
    for before, after in zip(active_samples, candidate_samples):
        if int(before.get("index", -1)) != int(after.get("index", -2)):
            raise ValueError("target-host state index drift")
        before_static = before.get("static_source_meshes", [])
        after_static = after.get("static_source_meshes", [])
        unrelated_static_exact &= [r for r in before_static if r.get("asset_id") != BUILDING_ASSET_ID] == [r for r in after_static if r.get("asset_id") != BUILDING_ASSET_ID]
        buildings = [row for row in after_static if row.get("asset_id") == BUILDING_ASSET_ID]
        building_ok &= (
            len(buildings) == 1
            and buildings[0].get("vertices") == EXPECTED_VERTICES
            and buildings[0].get("triangles") == EXPECTED_TRIANGLES
            and buildings[0].get("surface_count") == 5
            and buildings[0].get("representation_id") == CANDIDATE_ID
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

    active_sets, candidate_sets, delta_vs_active = _runtime_delta(active_runtime, candidate_runtime)
    compact_sets, _, delta_vs_compact = _runtime_delta(compact_runtime, candidate_runtime)

    checks = {
        "exact_leaf_flutter_current_world_parent_reused": True,
        "exact_planar_role_owner_identity_rendered": building_ok,
        "all_68_active_vs_planar_real_scene_frames_compared": len(active_deltas) == 68,
        "all_68_compact_vs_planar_real_scene_frames_compared": len(compact_deltas) == 68,
        "all_non_building_static_source_runtime_rows_exact": unrelated_static_exact,
        "dynamic_sapling_runtime_rows_exact": sapling_exact,
        "all_1224_weather_width_measurements_preserved": weather_measurements == 1224 and max_width_residual <= 0.05,
        "runtime_cost_delta_measured_against_active_and_compact_not_auto_accepted": True,
        "art_direction_and_visual_qa_preference_not_auto_accepted": True,
    }
    if not all(checks.values()):
        raise ValueError(f"current-world planar-role target-host checks failed: {checks}")

    return {
        "schema": "axm.environment-building-planar-role-current-world-report/v0.1",
        "state": TARGET_RESULT,
        "environment_head": environment_head,
        "parent_environment_head": PARENT_HEAD,
        "composition_digest": payload.get("composition_digest"),
        "building_hard_surface_head": HARD_SURFACE_HEAD,
        "building_materials_head": MATERIALS_HEAD,
        "semantic_source_variant_id": SEMANTIC_SOURCE_ID,
        "selected_representation_id": CANDIDATE_ID,
        "matched_active_vs_planar_frames": 68,
        "matched_compact_vs_planar_frames": 68,
        "active_vs_planar_frame_delta_summary": _group_frame_deltas(active_deltas, active_significant),
        "compact_vs_planar_frame_delta_summary": _group_frame_deltas(compact_deltas, compact_significant),
        "active_vs_planar_frame_deltas": active_deltas,
        "active_vs_planar_significant_frame_deltas_gt_1_lsb": active_significant,
        "compact_vs_planar_frame_deltas": compact_deltas,
        "compact_vs_planar_significant_frame_deltas_gt_1_lsb": compact_significant,
        "weather_width_measurements": weather_measurements,
        "maximum_weather_width_residual_px": max_width_residual,
        "active_runtime_counter_sets": compact_tool._serial_counter_sets(active_sets),
        "compact_runtime_counter_sets": compact_tool._serial_counter_sets(compact_sets),
        "planar_runtime_counter_sets": compact_tool._serial_counter_sets(candidate_sets),
        "runtime_counter_delta_vs_active_order_draw_objects_primitives_buffer_texture": delta_vs_active,
        "runtime_counter_delta_vs_compact_order_draw_objects_primitives_buffer_texture": delta_vs_compact,
        "checks": checks,
        "truth_boundary": (
            "PASS means the exact source-owned planar-role render receiver structurally survives the full sampled Nature/Object/Weather current world while preserving inherited Weather and unrelated asset state, and that exact current-world visual/runtime differences versus both the active segmented receiver and compact-v2 were retained. "
            "PASS does not select the candidate aesthetically, make it default, certify target-device performance or authorize transport."
        ),
        "non_claims": payload.get("non_claims", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build")
    p_build.add_argument("--parent", type=Path, required=True)
    p_build.add_argument("--candidate", type=Path, required=True)
    p_build.add_argument("--evidence", type=Path, required=True)
    p_build.add_argument("--policy", type=Path, required=True)
    p_build.add_argument("--environment-head", required=True)
    p_build.add_argument("--output", type=Path, required=True)
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--payload", type=Path, required=True)
    p_verify.add_argument("--parent-root", type=Path, required=True)
    p_verify.add_argument("--compact-root", type=Path, required=True)
    p_verify.add_argument("--candidate-root", type=Path, required=True)
    p_verify.add_argument("--environment-head", required=True)
    p_verify.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        result = build(load_json(args.parent), load_json(args.candidate), load_json(args.evidence), load_json(args.policy), args.environment_head)
    else:
        result = verify(load_json(args.payload), args.parent_root, args.compact_root, args.candidate_root, args.environment_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "state": result.get("building_planar_role_structure_result", result.get("state")),
        "composition_digest": result.get("composition_digest"),
        "checks": result.get("checks"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
