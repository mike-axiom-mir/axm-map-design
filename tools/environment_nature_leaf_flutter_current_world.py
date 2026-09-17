from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from typing import Any

import environment_nature_split_surface_culling_current_world as parent_tool

PARENT_HEAD = "10c6e29790b0b53b20abd603738cb54671af013c"
PARENT_STRUCTURE_RESULT = "PASS_CURRENT_WORLD_NATURE_SPLIT_SURFACE_CULLING_STRUCTURE"
PARENT_POLICY_ID = "source-woody-back__source-foliage-two-sided-001"
VFX_HEAD = "ecade64227ba1d3d1faf029ca7188ea63c2560ec"
GEOMETRY_LEAF_HEAD = "da3adbef4de8cddb8f3ebe841d39bb31a8936f5f"
VFX_SOURCE_RESULT = "PASS_BOUNDED_DETERMINISTIC_LEAF_FLUTTER_SOURCE_CANDIDATE"
STRUCTURE_RESULT = "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_STRUCTURE"
TARGET_RESULT = "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_TARGET_HOST"
SAPLING_ASSET_ID = "source:nature:sapling-neutral-001"
FRONT_VERTICES = 390
FRONT_TRIANGLES = 570


def load_json(path: Path) -> dict[str, Any]:
    return parent_tool.load_json(path)


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(a[i]) - float(b[i])) ** 2 for i in range(3)))


def _translated_residual(receiver: list[list[float]], donor: list[list[float]]) -> tuple[float, list[float]]:
    if len(receiver) != len(donor) or not receiver:
        return math.inf, []
    offset = [float(receiver[0][axis]) - float(donor[0][axis]) for axis in range(3)]
    residual = 0.0
    for current, source in zip(receiver, donor):
        for axis in range(3):
            residual = max(residual, abs((float(current[axis]) - float(source[axis])) - offset[axis]))
    return residual, offset


def _translate(vertices: list[list[float]], offset: list[float]) -> list[list[float]]:
    return [[float(v[i]) + float(offset[i]) for i in range(3)] for v in vertices]


def _front_mesh(candidate: dict[str, Any]) -> dict[str, Any]:
    vertices = candidate.get("vertices", [])
    triangles = candidate.get("triangles", [])
    regions = candidate.get("regions", [])
    if len(vertices) != 490 or len(triangles) != 620:
        raise ValueError("leaf-flutter donor candidate count drift")
    front_regions = [
        copy.deepcopy(region)
        for region in regions
        if str(region.get("kind", "")) != "leaf-blade-backface"
    ]
    front = {
        "schema": candidate.get("schema"),
        "vertices": copy.deepcopy(vertices[:FRONT_VERTICES]),
        "triangles": copy.deepcopy(triangles[:FRONT_TRIANGLES]),
        "regions": front_regions,
    }
    if len(front_regions) + 25 != len(regions):
        raise ValueError("expected exact 25 explicit backface regions in donor")
    return front


def _sapling(scene: dict[str, Any]) -> dict[str, Any]:
    sapling = scene.get("sapling", {})
    if not isinstance(sapling, dict) or sapling.get("asset_id") != SAPLING_ASSET_ID:
        raise ValueError("current-world sapling receiver missing")
    return sapling


def _foliage_vertices(sapling: dict[str, Any]) -> set[int]:
    proof = sapling.get("nature_material_family_receiving", {})
    partition = proof.get("surface_triangle_indices", {}) if isinstance(proof, dict) else {}
    foliage = partition.get("foliage", []) if isinstance(partition, dict) else []
    triangles = sapling.get("triangles", [])
    if len(foliage) != 50 or len(triangles) != FRONT_TRIANGLES:
        raise ValueError("current-world foliage partition drift")
    out: set[int] = set()
    for raw_index in foliage:
        tri_index = int(raw_index)
        if tri_index < 0 or tri_index >= len(triangles):
            raise ValueError("foliage triangle index drift")
        tri = triangles[tri_index]
        if len(tri) != 3:
            raise ValueError("foliage triangle arity drift")
        out.update(int(v) for v in tri)
    return out


def _validate_parent(parent: dict[str, Any]) -> None:
    if parent.get("environment_head") != PARENT_HEAD:
        raise ValueError("exact split-culling parent head drift")
    if parent.get("nature_surface_culling_structure_result") != PARENT_STRUCTURE_RESULT:
        raise ValueError("split-culling parent structure result missing")
    policy = parent.get("nature_surface_culling_policy", {})
    if not isinstance(policy, dict) or policy.get("policy_id") != PARENT_POLICY_ID:
        raise ValueError("accepted split-culling policy drift")
    if policy.get("woody_surface_cull") != "CULL_BACK" or policy.get("foliage_surface_cull") != "CULL_DISABLED":
        raise ValueError("accepted split-culling modes drift")
    if bool(policy.get("explicit_leaf_backface_geometry_adopted", True)):
        raise ValueError("current-world parent unexpectedly adopted explicit leaf geometry")
    if len(parent.get("states", [])) != 17:
        raise ValueError("current-world parent must retain 17 states")


def _validate_flutter_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    if summary.get("state") != VFX_SOURCE_RESULT:
        raise ValueError("Nature VFX flutter donor is not green")
    if summary.get("geometry_leaf_head") != GEOMETRY_LEAF_HEAD:
        raise ValueError("Nature Geometry leaf donor drift")
    if int(summary.get("front_vertices", -1)) != FRONT_VERTICES or int(summary.get("front_triangles", -1)) != FRONT_TRIANGLES:
        raise ValueError("Nature VFX front-source counts drift")
    samples = summary.get("samples", [])
    if not isinstance(samples, list) or len(samples) != 17:
        raise ValueError("Nature VFX flutter donor must retain exact 17 source phases")
    if float(summary.get("max_observed_non_leaf_vertex_delta_m", 1.0)) > 1e-12:
        raise ValueError("Nature VFX donor moved non-leaf geometry")
    if float(summary.get("max_observed_duplicate_position_gap_m", 1.0)) > 1e-12:
        raise ValueError("Nature VFX donor detached explicit review backfaces")
    return samples


def build(parent: dict[str, Any], flutter_root: Path, environment_head: str) -> dict[str, Any]:
    _validate_parent(parent)
    summary = load_json(flutter_root / "leaf-flutter-summary.json")
    samples = _validate_flutter_summary(summary)
    out_states: list[dict[str, Any]] = []
    offsets: list[list[float]] = []
    max_parent_baseline_residual = 0.0
    max_current_world_flutter_delta = 0.0
    changed_vertex_counts: list[int] = []
    parent_weather = [row.get("weather_field_digest") for row in parent["states"]]

    for index, (parent_row, sample) in enumerate(zip(parent["states"], samples)):
        if int(parent_row.get("index", -1)) != index:
            raise ValueError("current-world state index drift")
        if abs(float(parent_row.get("time_s", -1.0)) - float(sample.get("time_s", -2.0))) > 1e-12:
            raise ValueError(f"Nature VFX phase time drift at state {index}")

        baseline_candidate = load_json(flutter_root / str(sample["baseline_payload"]))
        flutter_candidate = load_json(flutter_root / str(sample["flutter_payload"]))
        baseline_front = _front_mesh(baseline_candidate)
        flutter_front = _front_mesh(flutter_candidate)
        if baseline_front["triangles"] != flutter_front["triangles"] or baseline_front["regions"] != flutter_front["regions"]:
            raise ValueError(f"Nature VFX flutter changed front topology at state {index}")

        row = copy.deepcopy(parent_row)
        scene = row["scene"]
        before_scene = copy.deepcopy(scene)
        sapling = _sapling(scene)
        receiver_vertices = sapling.get("vertices_source_xyz_m", [])
        receiver_triangles = sapling.get("triangles", [])
        if receiver_triangles != baseline_front["triangles"]:
            raise ValueError(f"current-world sapling topology does not match exact VFX donor at state {index}")

        residual, offset = _translated_residual(receiver_vertices, baseline_front["vertices"])
        max_parent_baseline_residual = max(max_parent_baseline_residual, residual)
        if residual > 1e-12:
            raise ValueError(f"current-world sapling is not exact translated VFX baseline at state {index}: {residual}")
        offsets.append(offset)

        foliage_vertices = _foliage_vertices(sapling)
        changed = {
            i for i, (a, b) in enumerate(zip(baseline_front["vertices"], flutter_front["vertices"]))
            if a != b
        }
        if not changed.issubset(foliage_vertices):
            raise ValueError(f"flutter escaped foliage receiver domain at state {index}")
        if index in (0, 16) and changed:
            raise ValueError("flutter neutral endpoint changed source vertices")
        if index not in (0, 16) and not changed:
            raise ValueError(f"interior flutter phase {index} is a source no-op")
        changed_vertex_counts.append(len(changed))

        translated_flutter = _translate(flutter_front["vertices"], offset)
        state_delta = max(
            (_distance(a, b) for a, b in zip(receiver_vertices, translated_flutter)),
            default=0.0,
        )
        if state_delta > float(summary["effect"]["max_allowed_flutter_vertex_delta_m"]) + 1e-12:
            raise ValueError(f"current-world flutter exceeded donor displacement cap at state {index}")
        max_current_world_flutter_delta = max(max_current_world_flutter_delta, state_delta)

        old_mesh_digest = sapling.get("mesh_digest")
        sapling["vertices_source_xyz_m"] = translated_flutter
        sapling["mesh_digest"] = parent_tool.digest(flutter_front)
        sapling["environment_nature_leaf_flutter_receiving"] = {
            "schema": "axm.environment-nature-leaf-flutter-receiving/v0.1",
            "vfx_head": VFX_HEAD,
            "geometry_leaf_context_head": GEOMETRY_LEAF_HEAD,
            "source_phase_index": index,
            "source_time_s": float(sample["time_s"]),
            "receiver_world_translation_m": offset,
            "changed_front_vertex_count": len(changed),
            "maximum_added_vertex_displacement_m": state_delta,
            "explicit_leaf_backface_geometry_adopted": False,
            "woody_surface_cull": "CULL_BACK",
            "foliage_surface_cull": "CULL_DISABLED",
            "authority": "MAP_RECEIVING_COMPOSITION_ONLY",
        }
        row["sapling_mesh_digest"] = parent_tool.digest({"vertices": translated_flutter, "triangles": receiver_triangles})
        scene["scene_digest"] = parent_tool.scene_digest(scene)

        restored = copy.deepcopy(scene)
        restored_sapling = _sapling(restored)
        restored_sapling["vertices_source_xyz_m"] = copy.deepcopy(before_scene["sapling"]["vertices_source_xyz_m"])
        restored_sapling["mesh_digest"] = old_mesh_digest
        restored_sapling.pop("environment_nature_leaf_flutter_receiving", None)
        restored["scene_digest"] = before_scene.get("scene_digest")
        if restored != before_scene:
            raise ValueError(f"non-flutter current-world scene data drifted at state {index}")
        out_states.append(row)

    first_offset = offsets[0]
    if any(max(abs(a - b) for a, b in zip(first_offset, other)) > 1e-12 for other in offsets[1:]):
        raise ValueError("sapling world translation drifted across flutter phases")
    if [row.get("weather_field_digest") for row in out_states] != parent_weather:
        raise ValueError("Weather sequence drifted during leaf-flutter receiving build")

    checks = dict(parent.get("checks", {}))
    checks.update({
        "exact_split_culling_parent_bound": True,
        "exact_nature_vfx_flutter_head_bound": True,
        "exact_geometry_leaf_context_bound": True,
        "current_world_sapling_matches_exact_vfx_baseline_up_to_translation": max_parent_baseline_residual <= 1e-12,
        "flutter_changes_only_existing_foliage_vertex_domain": True,
        "explicit_leaf_backface_geometry_remains_not_adopted": True,
        "woody_back_foliage_two_sided_policy_preserved": True,
        "neutral_start_and_return_exact": changed_vertex_counts[0] == 0 and changed_vertex_counts[-1] == 0,
        "all_15_interior_source_phases_nonzero": all(value > 0 for value in changed_vertex_counts[1:-1]),
        "all_17_states_preserved": len(out_states) == 17,
        "weather_building_object_static_nature_path_camera_lighting_preserved": True,
    })
    if not all(checks.values()):
        raise ValueError(f"current-world Nature leaf-flutter structure checks failed: {checks}")

    result = copy.deepcopy(parent)
    result.update({
        "environment_head": environment_head,
        "nature_leaf_flutter_parent_environment_head": PARENT_HEAD,
        "nature_leaf_flutter_parent_composition_digest": parent.get("composition_digest"),
        "nature_leaf_flutter_vfx_head": VFX_HEAD,
        "nature_leaf_flutter_geometry_context_head": GEOMETRY_LEAF_HEAD,
        "nature_leaf_flutter_structure_result": STRUCTURE_RESULT,
        "nature_leaf_flutter_effect": copy.deepcopy(summary.get("effect", {})),
        "nature_leaf_flutter_maximum_current_world_vertex_delta_m": max_current_world_flutter_delta,
        "nature_leaf_flutter_maximum_parent_baseline_residual_m": max_parent_baseline_residual,
        "nature_leaf_flutter_receiver_world_translation_m": first_offset,
        "nature_leaf_flutter_changed_vertex_counts": changed_vertex_counts,
        "states": out_states,
        "checks": checks,
        "truth_boundary": (
            "Environment receives only Nature VFX PR #11's bounded deterministic leaf-local flutter into the exact Art-Direction-preferred split-culling current world. "
            "The existing 390v/570t source geometry, woody/foliage material family, woody CULL_BACK / foliage CULL_DISABLED policy, Building, indexed Object, visible footprint cue, static Nature, Weather, route, cameras and lighting remain fixed. "
            "This is receiving evidence only; perceptual naturalness, shaded backface response, continuous wall-clock timing, target-device performance, physical wind and final art remain separate gates."
        ),
        "non_claims": [
            "FINAL_NATURE_FLUTTER_OR_LOOK_ACCEPTANCE",
            "PHYSICAL_WIND_OR_BIOMECHANICS",
            "CONTINUOUS_INTERPOLATION_OR_WALL_CLOCK_TIMING",
            "TARGET_DEVICE_PERFORMANCE",
            "ARBITRARY_CAMERA_RENDERER_OR_DISPLAY_EQUIVALENCE",
            "COLLISION_NAVIGATION_OR_GAMEPLAY",
            "CANON_PRODUCTION_READY_OR_ENVIRONMENT_MASTERY",
        ],
    })
    result["composition_digest"] = parent_tool.digest({
        "parent": parent.get("composition_digest"),
        "vfx_head": VFX_HEAD,
        "geometry_context": GEOMETRY_LEAF_HEAD,
        "changed_vertex_counts": changed_vertex_counts,
        "scenes": [row["scene"]["scene_digest"] for row in out_states],
    })
    return result


def verify(payload: dict[str, Any], parent_root: Path, candidate_root: Path, environment_head: str) -> dict[str, Any]:
    if payload.get("environment_head") != environment_head:
        raise ValueError("Nature leaf-flutter payload head drift")
    if payload.get("nature_leaf_flutter_parent_environment_head") != PARENT_HEAD:
        raise ValueError("Nature leaf-flutter parent head drift")
    if payload.get("nature_leaf_flutter_vfx_head") != VFX_HEAD:
        raise ValueError("Nature VFX flutter head drift")
    if payload.get("nature_leaf_flutter_structure_result") != STRUCTURE_RESULT:
        raise ValueError("Nature leaf-flutter structural result missing")
    if not all(payload.get("checks", {}).values()):
        raise ValueError("Nature leaf-flutter payload checks are not all true")

    parent_frames = parent_tool.frame_files(parent_root)
    candidate_frames = parent_tool.frame_files(candidate_root)
    if len(parent_frames) != 68 or [p.name for p in parent_frames] != [p.name for p in candidate_frames]:
        raise ValueError("expected 68 matched current-world frames")
    deltas = [parent_tool._frame_delta(a, b) for a, b in zip(parent_frames, candidate_frames)]
    endpoint_rows = [row for row in deltas if row["file"].endswith("-00.png") or row["file"].endswith("-16.png")]
    if len(endpoint_rows) != 8 or any(row["changed_pixels"] != 0 for row in endpoint_rows):
        raise ValueError("leaf flutter failed exact rendered neutral endpoints")
    interior = [row for row in deltas if row not in endpoint_rows]
    if not any(row["changed_pixels"] > 0 for row in interior):
        raise ValueError("leaf flutter is a complete current-world visual no-op")

    parent_runtime = load_json(parent_root / "runtime.json")
    candidate_runtime = load_json(candidate_root / "runtime.json")
    if parent_tool.runtime_counters(parent_runtime) != parent_tool.runtime_counters(candidate_runtime):
        raise ValueError("leaf flutter changed proof-host submission/memory counters")
    if candidate_runtime.get("environment_nature_leaf_flutter_vfx_head") != VFX_HEAD:
        raise ValueError("target-host receipt missing exact Nature VFX flutter identity")
    if candidate_runtime.get("environment_nature_leaf_flutter_structure_result") != STRUCTURE_RESULT:
        raise ValueError("target-host receipt missing current-world flutter structure identity")

    weather_measurements = 0
    max_width_residual = 0.0
    for sample in candidate_runtime.get("samples", []):
        for context in sample.get("contexts", {}).values():
            weather = context["candidate"]["weather_update"]
            weather_measurements += int(weather.get("measured_width_count", 0))
            max_width_residual = max(max_width_residual, float(weather.get("maximum_projected_width_residual_px", 0.0)))
    if weather_measurements != 1224 or max_width_residual > 0.05:
        raise ValueError("inherited Weather-width evidence drift")

    grouped: dict[str, dict[str, Any]] = {}
    for camera in ("path_eye", "elevated_oblique"):
        rows = [row for row in deltas if parent_tool._camera_name(row["file"]) == camera]
        interior_rows = [row for row in rows if not (row["file"].endswith("-00.png") or row["file"].endswith("-16.png"))]
        if not any(row["changed_pixels"] > 0 for row in interior_rows):
            raise ValueError(f"leaf flutter not renderer-visible in current-world camera {camera}")
        grouped[camera] = {
            "frame_count": len(rows),
            "changed_frame_count": sum(1 for row in rows if row["changed_pixels"] > 0),
            "interior_changed_frame_count": sum(1 for row in interior_rows if row["changed_pixels"] > 0),
            "minimum_interior_changed_pixels": min(row["changed_pixels"] for row in interior_rows),
            "maximum_interior_changed_pixels": max(row["changed_pixels"] for row in interior_rows),
            "maximum_channel_delta_8bit": max(row["max_channel_delta_8bit"] for row in rows),
            "distinct_bboxes": sorted({str(row["bbox"]) for row in interior_rows if row["bbox"] is not None}),
        }

    report = {
        "schema": "axm.environment-nature-leaf-flutter-current-world-report/v0.1",
        "state": TARGET_RESULT,
        "environment_head": environment_head,
        "parent_environment_head": PARENT_HEAD,
        "composition_digest": payload["composition_digest"],
        "nature_vfx_head": VFX_HEAD,
        "matched_frames": 68,
        "neutral_endpoint_frames": 8,
        "neutral_endpoint_changed_pixels": 0,
        "changed_frames": sum(1 for row in deltas if row["changed_pixels"] > 0),
        "frame_delta_summary": grouped,
        "frame_deltas": deltas,
        "weather_width_measurements": weather_measurements,
        "maximum_weather_width_residual_px": max_width_residual,
        "runtime_counter_deltas": {
            "draw_calls_in_frame": 0,
            "objects_in_frame": 0,
            "primitives_in_frame": 0,
            "buffer_mem_bytes": 0,
            "texture_mem_bytes": 0,
        },
        "checks": {
            "exact_split_culling_parent_reused": True,
            "exact_vfx_flutter_source_bound": True,
            "all_68_real_scene_frames_compared": True,
            "neutral_start_and_return_render_byte_identical": True,
            "interior_flutter_renderer_visible_in_both_fixed_cameras": True,
            "proof_host_submission_and_memory_counters_unchanged": True,
            "all_1224_weather_width_measurements_preserved": True,
            "perceptual_naturalness_not_auto_accepted": True,
        },
        "truth_boundary": (
            "PASS proves only that the exact bounded leaf-local VFX source phases reach the full current-world Godot receiver on top of the accepted woody-back/foliage-two-sided policy, with exact neutral endpoints and preserved Weather/proof-host counters. "
            "Changed pixels are retained for Art Direction and Visual QA; this report does not label the motion natural, final, physical, continuously timed or production-ready."
        ),
    }
    if not all(report["checks"].values()):
        raise ValueError(f"Nature leaf-flutter target-host checks failed: {report['checks']}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build")
    p_build.add_argument("--parent", type=Path, required=True)
    p_build.add_argument("--flutter-root", type=Path, required=True)
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
        result = build(load_json(args.parent), args.flutter_root, args.environment_head)
    else:
        result = verify(load_json(args.payload), args.parent_root, args.candidate_root, args.environment_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
