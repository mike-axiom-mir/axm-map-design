from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-object-articulated-service-clearance/v0.1"
RESULT = "PASS_CURRENT_WORLD_OBJECT_ARTICULATED_SERVICE_CLEARANCE_SUCCESSOR__20MM_REAR_DRESSING_EXPANSION_RESTORES_60MM_SWEEP_CLEARANCE__ADOPTION_HELD"
RULE = "DYNAMIC_WORLD_PROPS_REQUIRE_THEIR_FULL_OWNER_MOTION_SWEEP_TO_FIT_THE_ENVIRONMENT_SERVICE_ZONE__DRESSING_MAY_EXPAND_ONLY_WITH_EXPLICIT_PATH_BUILDING_AND_SOURCE_CONTINUITY_EVIDENCE"

EXPECTED_TA_HEAD = "e085437f6cc958bbf7c5c6464578923d542962b0"
EXPECTED_OBJECT_TA_HEAD = "965fb2f24dbd0b0cbb748d9f8b8712d62966315f"
EXPECTED_OBJECT_SOURCE_HEAD = "d3fa10a270faae7925811f44f03381fe5c5d0215"
EXPECTED_OBJECT_SHA256 = "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
EXPECTED_ANIMATION_HEAD = "c688936a84f80f292e43587c9d3386bd717f8178"
EXPECTED_SEQUENCE_DIGEST = "0a3523cf792264f610881552fd2ebd438aabdfd05e30e92af9dbb33ded1fa2d3"
EXPECTED_FRAME_RULE = "UC_GLTF_TO_GODOT_CURRENT_WORLD_REFLECTION_Z__NEGATE_OWNER_ROTATION_ANGLE_AFTER_WORLD_AXIS_PLACEMENT"
EXPECTED_FRAME_ASSET = "environment:dressing:west-object-service-footprint-frame-001"
EXPECTED_OLD_OUTER = [-4.025387, -2.890757, 3.736077, 4.8707069999999995]
EXPECTED_STRIP_WIDTH_M = 0.045
EXPECTED_FRAME_HEIGHT_M = 0.02
TARGET_CLEARANCE_M = 0.06
DEFAULT_REAR_EXPANSION_M = 0.02

LID_GROUPS = {
    "lid_shell",
    "latch_0_keeper",
    "latch_1_keeper",
    "hinge_lid_l0",
    "hinge_lid_l1",
}
LEVER_TO_STATION = {
    "latch_0_lever": "front-latch-left",
    "latch_1_lever": "front-latch-right",
}

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def almost(a: float, b: float, eps: float = 1e-8) -> bool:
    return abs(float(a) - float(b)) <= eps

def same_list(a: Any, b: list[float], eps: float = 1e-8) -> bool:
    return isinstance(a, list) and len(a) == len(b) and all(almost(x, y, eps) for x, y in zip(a, b))

def host_to_world(v: list[float]) -> list[float]:
    # Current Godot host gvec() is source/world [x,y,z] -> [x,z,-y].
    return [float(v[0]), -float(v[2]), float(v[1])]

def vsub(a: list[float], b: list[float]) -> list[float]:
    return [a[i] - b[i] for i in range(3)]

def vadd(a: list[float], b: list[float]) -> list[float]:
    return [a[i] + b[i] for i in range(3)]

def vscale(a: list[float], s: float) -> list[float]:
    return [x * s for x in a]

def dot(a: list[float], b: list[float]) -> float:
    return sum(a[i] * b[i] for i in range(3))

def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]

def norm(a: list[float]) -> float:
    return math.sqrt(dot(a, a))

def normalize(a: list[float]) -> list[float]:
    n = norm(a)
    if n <= 1e-12:
        raise AssertionError("zero rotation axis")
    return [x / n for x in a]

def rotate_about_axis(point: list[float], pivot: list[float], axis: list[float], degrees: float) -> list[float]:
    # Rodrigues rotation in the Map source/world frame.
    p = vsub(point, pivot)
    k = normalize(axis)
    theta = math.radians(float(degrees))
    c = math.cos(theta)
    s = math.sin(theta)
    rotated = vadd(vadd(vscale(p, c), vscale(cross(k, p), s)), vscale(k, dot(k, p) * (1.0 - c)))
    return vadd(pivot, rotated)

def object_row_from_world(world: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    states = world.get("states", [])
    if len(states) != 17:
        raise AssertionError("exact combined-world payload state count drift")
    first_scene = states[0]["scene"]
    rows = [row for row in first_scene.get("additional_source_meshes", []) if row.get("asset_id") == "source:object:modular-equipment-case-001"]
    if len(rows) != 1:
        raise AssertionError("exact combined world must contain one Object source")
    obj = rows[0]
    if obj.get("source_head") != EXPECTED_OBJECT_SOURCE_HEAD or obj.get("source_sha256") != EXPECTED_OBJECT_SHA256:
        raise AssertionError("exact combined-world Object identity drift")
    if len(obj.get("vertices_source_xyz_m", [])) != 468 or len(obj.get("triangles", [])) != 812:
        raise AssertionError("exact combined-world Object structural count drift")
    for state in states[1:]:
        rows2 = [row for row in state["scene"].get("additional_source_meshes", []) if row.get("asset_id") == "source:object:modular-equipment-case-001"]
        if len(rows2) != 1 or rows2[0] != obj:
            raise AssertionError("neutral Object source row drift across exact 17-state world")
    return obj, first_scene

def component_vertex_indices(component_map: dict[str, Any], triangles: list[list[int]]) -> dict[str, set[int]]:
    if component_map.get("schema") != "axm.environment-object-rigid-component-map/v0.1":
        raise AssertionError("rigid component-map schema drift")
    if component_map.get("technical_art_head") != EXPECTED_OBJECT_TA_HEAD:
        raise AssertionError("Object Technical Art component-map head drift")
    if component_map.get("object_source_sha256") != EXPECTED_OBJECT_SHA256 or int(component_map.get("triangles", -1)) != 812:
        raise AssertionError("rigid component-map source identity drift")
    out: dict[str, set[int]] = {}
    total_triangles = 0
    for row in component_map.get("components", []):
        name = str(row.get("name", ""))
        first = int(row.get("first_triangle", -1))
        count = int(row.get("triangle_count", -1))
        if not name or first < 0 or count <= 0 or first + count > len(triangles):
            raise AssertionError("invalid rigid component triangle range")
        refs: set[int] = set()
        for tri in triangles[first:first + count]:
            if len(tri) != 3:
                raise AssertionError("Object triangle arity drift")
            refs.update(int(i) for i in tri)
        out[name] = refs
        total_triangles += count
    if len(out) != 31 or total_triangles != 812:
        raise AssertionError("rigid component partition count drift")
    if not LID_GROUPS.issubset(out) or not set(LEVER_TO_STATION).issubset(out):
        raise AssertionError("required articulated component identity missing")
    # Current exact source is primitive-partitioned: a vertex must not belong to multiple rigid components.
    ownership: dict[int, str] = {}
    for name, refs in out.items():
        for idx in refs:
            if idx in ownership and ownership[idx] != name:
                raise AssertionError(f"Object vertex {idx} shared by rigid groups {ownership[idx]} and {name}")
            ownership[idx] = name
    if len(ownership) != 468:
        raise AssertionError("rigid component map does not cover all exact Object vertices")
    return out

def find_object_source(sample: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in sample.get("static_source_meshes", []) if row.get("asset_id") == "source:object:modular-equipment-case-001"]
    if len(rows) != 1:
        raise AssertionError("real current-world sample must contain exactly one Object source")
    return rows[0]

def find_frame(sample: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in sample.get("static_source_meshes", []) if row.get("asset_id") == EXPECTED_FRAME_ASSET]
    if len(rows) != 1:
        raise AssertionError("real current-world sample must contain exactly one Environment service frame")
    return rows[0]

def validate_real_world_runtime(runtime_paths: list[Path]) -> tuple[list[float], list[float], dict[str, list[float]], dict[str, Any]]:
    hinge_pivot_world: list[float] | None = None
    hinge_axis_world: list[float] | None = None
    latch_pivots_world: dict[str, list[float]] | None = None
    common: dict[str, Any] | None = None
    expected_assets = {
        "source:nature:compact-east-tree-neutral-001",
        "source:nature:east-rear-tree-neutral-001",
        "source:object:modular-equipment-case-001",
        "source:building:service-pavilion-001",
        EXPECTED_FRAME_ASSET,
    }
    for path in runtime_paths:
        runtime = load_json(path)
        samples = runtime.get("samples", [])
        if len(samples) != 17:
            raise AssertionError(f"{path.name}: exact current-world state count drift")
        if runtime.get("technical_art_object_motion_animation_head") != EXPECTED_ANIMATION_HEAD:
            raise AssertionError(f"{path.name}: Animation identity drift")
        if runtime.get("technical_art_object_motion_sequence_digest") != EXPECTED_SEQUENCE_DIGEST:
            raise AssertionError(f"{path.name}: sequence identity drift")
        if runtime.get("technical_art_object_motion_owner_to_host_frame_rule") != EXPECTED_FRAME_RULE:
            raise AssertionError(f"{path.name}: owner-to-host frame rule drift")
        if runtime.get("technical_art_object_motion_environment_adoption") is not False:
            raise AssertionError(f"{path.name}: Environment adoption authority inflated")
        for state in samples:
            assets = {row.get("asset_id") for row in state.get("static_source_meshes", [])}
            if not expected_assets.issubset(assets):
                raise AssertionError(f"{path.name}: multi-asset current-world scope drift")
            obj = find_object_source(state)
            if obj.get("source_sha256") != EXPECTED_OBJECT_SHA256 or int(obj.get("vertices", -1)) != 468 or int(obj.get("triangles", -1)) != 812:
                raise AssertionError(f"{path.name}: Object receiver identity drift")
            if int(obj.get("surface_count", -1)) != 7:
                raise AssertionError(f"{path.name}: selected-surface Object receiver drift")
            motion = obj.get("environment_object_motion_receiver", {})
            if motion.get("state") != "PASS_CURRENT_WORLD_OBJECT_ANIMATION_OWNER_SAMPLE_RECEIVER__VFX_RUNTIME_ENV_ADOPTION_HELD":
                raise AssertionError(f"{path.name}: exact motion receiver state drift")
            if motion.get("environment_adoption") is not False:
                raise AssertionError(f"{path.name}: nested Environment adoption authority inflated")
            hp = host_to_world([float(v) for v in motion["current_world_receiver_hinge_pivot_xyz_m"]])
            ha = normalize(host_to_world([float(v) for v in motion["current_world_receiver_hinge_axis_xyz"]]))
            lp = {str(k): host_to_world([float(v) for v in val]) for k, val in motion["current_world_receiver_latch_pivots_xyz_m"].items()}
            if hinge_pivot_world is None:
                hinge_pivot_world, hinge_axis_world, latch_pivots_world = hp, ha, lp
            else:
                if not same_list(hp, hinge_pivot_world, 1e-6) or not same_list(ha, hinge_axis_world or [], 1e-6) or lp != latch_pivots_world:
                    raise AssertionError(f"{path.name}: articulated Object world pivot/axis drift across retained real scene")
            frame = find_frame(state)
            if not same_list(frame.get("outer_footprint_source_xy_m"), EXPECTED_OLD_OUTER, 1e-6):
                raise AssertionError(f"{path.name}: existing Environment service frame identity drift")
            if not almost(frame.get("strip_width_m"), EXPECTED_STRIP_WIDTH_M, 1e-6) or not almost(frame.get("frame_height_m"), EXPECTED_FRAME_HEIGHT_M, 1e-6):
                raise AssertionError(f"{path.name}: existing Environment service frame scalar drift")
            building = [row for row in state["static_source_meshes"] if row.get("asset_id") == "source:building:service-pavilion-001"][0]
            if int(building.get("vertices", -1)) != 184 or int(building.get("triangles", -1)) != 276 or int(building.get("surface_count", -1)) != 5:
                raise AssertionError(f"{path.name}: active Building current receiver drift")
            nature = [row for row in state["static_source_meshes"] if str(row.get("asset_id", "")).startswith("source:nature:")]
            if len(nature) != 2 or any(int(row.get("vertices", -1)) != 390 or int(row.get("triangles", -1)) != 570 for row in nature):
                raise AssertionError(f"{path.name}: Nature receiving identity drift")
        signature = {
            "source_width_profile_digest": runtime.get("source_width_profile_digest"),
            "weather_variant_seed": runtime.get("weather_variant_seed"),
            "weather_variant_layout_digest": runtime.get("weather_variant_layout_digest"),
            "building_current_variant": runtime.get("environment_building_current_source_variant_id"),
            "compact_east_vfx_head": runtime.get("environment_compact_east_visual_response_vfx_head"),
        }
        if common is None:
            common = signature
        elif signature != common:
            raise AssertionError(f"{path.name}: unrelated Weather/Nature/Building identity drift")
    if hinge_pivot_world is None or hinge_axis_world is None or latch_pivots_world is None or common is None:
        raise AssertionError("missing real current-world motion identity")
    return hinge_pivot_world, hinge_axis_world, latch_pivots_world, common

def validate_world_boundaries(world: dict[str, Any]) -> tuple[dict[str, float], list[float], dict[str, Any]]:
    obj, scene = object_row_from_world(world)
    path0 = scene.get("readable_path", {})
    path = {k: float(path0[k]) for k in ("x_min", "x_max", "y_min", "y_max")}
    building_vertices = scene.get("environment_building_material_receiving", {}).get("vertices_source_xyz_m", [])
    if len(building_vertices) != 184:
        raise AssertionError("combined-world Building receiver must be the 184-vertex current representation")
    building_bounds = [
        min(float(v[0]) for v in building_vertices),
        max(float(v[0]) for v in building_vertices),
        min(float(v[1]) for v in building_vertices),
        max(float(v[1]) for v in building_vertices),
    ]
    return path, building_bounds, obj

def build_report(
    contract: dict[str, Any],
    component_map: dict[str, Any],
    motion_plan: dict[str, Any],
    runtime_paths: list[Path],
    final_receipt: dict[str, Any],
    combined_world: dict[str, Any],
    rear_expansion_m: float,
) -> dict[str, Any]:
    if contract.get("schema") != SCHEMA:
        raise AssertionError("Environment service-clearance contract schema drift")
    if contract.get("technical_art_parent_head") != EXPECTED_TA_HEAD:
        raise AssertionError("Technical Art parent head drift")
    if contract.get("object_technical_art_head") != EXPECTED_OBJECT_TA_HEAD:
        raise AssertionError("Object Technical Art donor head drift")
    if not almost(rear_expansion_m, float(contract["candidate"]["rear_outer_edge_expansion_m"]), 1e-12):
        raise AssertionError("candidate rear expansion does not match contract")
    if rear_expansion_m <= 0.0 or rear_expansion_m > 0.02 + 1e-12:
        raise AssertionError("candidate expansion must remain positive and bounded to 20 mm")

    path, building_bounds, object_world = validate_world_boundaries(combined_world)
    vertices = [[float(c) for c in v] for v in object_world["vertices_source_xyz_m"]]
    triangles = [[int(i) for i in tri] for tri in object_world["triangles"]]
    group_refs = component_vertex_indices(component_map, triangles)

    if motion_plan.get("object_source_sha256") != EXPECTED_OBJECT_SHA256 or motion_plan.get("object_technical_art_head") != EXPECTED_OBJECT_TA_HEAD:
        raise AssertionError("motion-plan Object identity drift")
    if motion_plan.get("animation_head") != EXPECTED_ANIMATION_HEAD or motion_plan.get("sequence_digest") != EXPECTED_SEQUENCE_DIGEST:
        raise AssertionError("motion-plan Animation identity drift")
    samples = motion_plan.get("samples", [])
    if len(samples) != 101 or [int(row["index"]) for row in samples] != list(range(101)):
        raise AssertionError("motion-plan sample identity drift")

    hinge_pivot_world, hinge_axis_world, latch_pivots_world, multi_asset_signature = validate_real_world_runtime(runtime_paths)
    if set(latch_pivots_world) != set(LEVER_TO_STATION.values()):
        raise AssertionError("current-world latch pivot station identity drift")
    expected_hinge_world = host_to_world([-3.43774724006653, 0.305999994277954, -4.5545711517334])
    if not same_list(hinge_pivot_world, expected_hinge_world, 1e-6):
        raise AssertionError("current-world hinge pivot exact witness drift")

    if final_receipt.get("exact_head") != EXPECTED_TA_HEAD or final_receipt.get("result") != "PASS_CURRENT_WORLD_OBJECT_ANIMATION_OWNER_SAMPLES_THROUGH_RIGID_RECEIVER__VFX_RUNTIME_ENV_ADOPTION_HELD":
        raise AssertionError("Technical Art retained final receipt drift")
    if final_receipt.get("samples_proven") != [0, 10, 50, 100]:
        raise AssertionError("Technical Art real-scene sample proof set drift")
    if int(final_receipt["neutral_changed_pixels_vs_retained_parent"]) != 0 or int(final_receipt["endpoint_changed_pixels_vs_neutral"]) != 0:
        raise AssertionError("Technical Art neutral/endpoint exact closure drift")
    if int(final_receipt["release_changed_pixels"]) != 5644 or int(final_receipt["peak_changed_pixels"]) != 102748:
        raise AssertionError("Technical Art real-scene motion observability drift")

    old_outer = [float(v) for v in EXPECTED_OLD_OUTER]
    candidate_outer = [old_outer[0], old_outer[1], old_outer[2], old_outer[3] + float(rear_expansion_m)]
    old_inner = [old_outer[0] + EXPECTED_STRIP_WIDTH_M, old_outer[1] - EXPECTED_STRIP_WIDTH_M, old_outer[2] + EXPECTED_STRIP_WIDTH_M, old_outer[3] - EXPECTED_STRIP_WIDTH_M]
    candidate_inner = [
        candidate_outer[0] + EXPECTED_STRIP_WIDTH_M,
        candidate_outer[1] - EXPECTED_STRIP_WIDTH_M,
        candidate_outer[2] + EXPECTED_STRIP_WIDTH_M,
        candidate_outer[3] - EXPECTED_STRIP_WIDTH_M,
    ]

    moving_owner: dict[int, str] = {}
    for name in LID_GROUPS | set(LEVER_TO_STATION):
        for idx in group_refs[name]:
            if idx in moving_owner and moving_owner[idx] != name:
                raise AssertionError("moving Object vertex has ambiguous articulated owner")
            moving_owner[idx] = name

    rows: list[dict[str, Any]] = []
    old_min = float("inf")
    candidate_min = float("inf")
    old_witness: dict[str, Any] | None = None
    candidate_witness: dict[str, Any] | None = None
    overall_min_z = float("inf")
    overall_max_z = -float("inf")

    for row in samples:
        lid_world_deg = -float(row["lid_target_rotation_deg_x"])
        latch_world_deg = -float(row["latch_target_rotation_deg_x"])
        posed = [v[:] for v in vertices]
        for idx, owner in moving_owner.items():
            if owner in LID_GROUPS:
                posed[idx] = rotate_about_axis(vertices[idx], hinge_pivot_world, hinge_axis_world, lid_world_deg)
            else:
                sid = LEVER_TO_STATION[owner]
                posed[idx] = rotate_about_axis(vertices[idx], latch_pivots_world[sid], hinge_axis_world, latch_world_deg)
        xs = [v[0] for v in posed]
        ys = [v[1] for v in posed]
        zs = [v[2] for v in posed]
        bounds = [min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)]
        old_margins = [
            bounds[0] - old_inner[0],
            old_inner[1] - bounds[1],
            bounds[2] - old_inner[2],
            old_inner[3] - bounds[3],
        ]
        candidate_margins = [
            bounds[0] - candidate_inner[0],
            candidate_inner[1] - bounds[1],
            bounds[2] - candidate_inner[2],
            candidate_inner[3] - bounds[3],
        ]
        witness = {
            "sample_index": int(row["index"]),
            "time_s": float(row["time_s"]),
            "owner_lid_target_deg": float(row["lid_target_rotation_deg_x"]),
            "owner_latch_target_deg": float(row["latch_target_rotation_deg_x"]),
            "map_world_lid_rotation_deg": lid_world_deg,
            "map_world_latch_rotation_deg": latch_world_deg,
            "world_bounds_xyz_minmax_m": bounds,
            "old_inner_clearances_l_r_front_rear_m": old_margins,
            "candidate_inner_clearances_l_r_front_rear_m": candidate_margins,
        }
        rows.append(witness)
        if min(old_margins) < old_min:
            old_min = min(old_margins)
            old_witness = witness
        if min(candidate_margins) < candidate_min:
            candidate_min = min(candidate_margins)
            candidate_witness = witness
        overall_min_z = min(overall_min_z, bounds[4])
        overall_max_z = max(overall_max_z, bounds[5])

    if old_witness is None or candidate_witness is None:
        raise AssertionError("no articulated sweep samples evaluated")
    if old_min >= TARGET_CLEARANCE_M - 1e-9:
        raise AssertionError("predecessor frame does not expose the expected articulated-clearance regression")
    if candidate_min < TARGET_CLEARANCE_M - 1e-9:
        raise AssertionError(f"candidate frame does not restore 60 mm articulated clearance: {candidate_min:.9f} m")
    if overall_min_z < -1e-8:
        raise AssertionError("owner articulation drives exact Object below current-world ground")

    path_separation_x = path["x_min"] - candidate_outer[1]
    building_separation_y = building_bounds[2] - candidate_outer[3]
    if path_separation_x < 1.0 - 1e-9:
        raise AssertionError("candidate frame erodes the existing 1.0 m readable-path separation")
    if building_separation_y <= 0.0:
        raise AssertionError("candidate frame overlaps current Building footprint")

    return {
        "schema": SCHEMA,
        "result": RESULT,
        "reusable_rule": RULE,
        "technical_art_parent_head": EXPECTED_TA_HEAD,
        "object_technical_art_head": EXPECTED_OBJECT_TA_HEAD,
        "object_source_head": EXPECTED_OBJECT_SOURCE_HEAD,
        "object_source_sha256": EXPECTED_OBJECT_SHA256,
        "animation_head": EXPECTED_ANIMATION_HEAD,
        "sequence_digest": EXPECTED_SEQUENCE_DIGEST,
        "owner_to_host_frame_rule": EXPECTED_FRAME_RULE,
        "real_scene_evidence": {
            "retained_owner_samples_rendered": [0, 10, 50, 100],
            "retained_world_states_per_sample": 17,
            "retained_real_godot_frames_per_sample": 68,
            "neutral_changed_pixels_vs_parent": int(final_receipt["neutral_changed_pixels_vs_retained_parent"]),
            "release_changed_pixels": int(final_receipt["release_changed_pixels"]),
            "peak_changed_pixels": int(final_receipt["peak_changed_pixels"]),
            "endpoint_changed_pixels_vs_neutral": int(final_receipt["endpoint_changed_pixels_vs_neutral"]),
            "assets_bound": [
                "Building current 184v/276t/5-surface receiver",
                "Nature compact-east 390v/570t",
                "Nature east-rear 390v/570t",
                "Object articulated 468v/812t/7-surface receiver",
                "Environment service-footprint frame",
                "Weather source-width current-world presentation",
            ],
            "multi_asset_signature": multi_asset_signature,
        },
        "articulated_sweep": {
            "owner_samples_evaluated": 101,
            "hinge_pivot_world_xyz_m": hinge_pivot_world,
            "hinge_axis_world_xyz": hinge_axis_world,
            "latch_pivots_world_xyz_m": latch_pivots_world,
            "old_outer_footprint_world_xy_m": old_outer,
            "old_inner_footprint_world_xy_m": old_inner,
            "candidate_outer_footprint_world_xy_m": candidate_outer,
            "candidate_inner_footprint_world_xy_m": candidate_inner,
            "target_minimum_inner_clearance_m": TARGET_CLEARANCE_M,
            "predecessor_minimum_inner_clearance_m": old_min,
            "predecessor_minimum_witness": old_witness,
            "candidate_minimum_inner_clearance_m": candidate_min,
            "candidate_minimum_witness": candidate_witness,
            "overall_world_min_z_m": overall_min_z,
            "overall_world_max_z_m": overall_max_z,
            "rear_outer_edge_expansion_m": rear_expansion_m,
        },
        "world_relationships": {
            "readable_path": path,
            "candidate_service_frame_to_path_x_separation_m": path_separation_x,
            "current_building_world_xy_bounds_m": building_bounds,
            "candidate_service_frame_to_building_y_separation_m": building_separation_y,
        },
        "decision": {
            "environment_candidate": "EXPAND_ONLY_REAR_OUTER_EDGE_OF_EXISTING_MAP_OWNED_SERVICE_FRAME_BY_0.020_M",
            "object_source_changed": False,
            "object_world_placement_changed": False,
            "animation_changed": False,
            "technical_art_receiver_changed": False,
            "building_changed": False,
            "nature_changed": False,
            "weather_changed": False,
            "camera_or_light_changed": False,
            "environment_adoption": False,
            "art_qa_acceptance_required": True,
            "runtime_acceptance_required": True,
        },
        "truth_boundary": (
            "PASS proves that the exact 101-sample owner lid/latch sweep, reconstructed from the exact current-world Object vertices, exact rigid-component triangle ownership and the already-green Technical Art world pivots/frame rule, "
            "exposes a real Environment dressing-clearance regression in the historical neutral-only service frame and that one bounded Map-owned 20 mm rear-edge successor restores the existing 60 mm inner clearance while preserving the current readable-path separation and remaining clear of the current Building footprint. "
            "The proof consumes retained real Godot multi-asset scene evidence but does not render or aesthetically accept the successor frame itself. Environment adoption, Art/QA, Runtime/device, gameplay, collision/navigation, CANON and production readiness remain held."
        ),
        "samples": rows,
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", required=True)
    ap.add_argument("--component-map", required=True)
    ap.add_argument("--motion-plan", required=True)
    ap.add_argument("--runtime", action="append", required=True)
    ap.add_argument("--final-receipt", required=True)
    ap.add_argument("--combined-world", required=True)
    ap.add_argument("--rear-expansion-m", type=float, default=DEFAULT_REAR_EXPANSION_M)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    contract = load_json(Path(args.contract))
    report = build_report(
        contract,
        load_json(Path(args.component_map)),
        load_json(Path(args.motion_plan)),
        [Path(p) for p in args.runtime],
        load_json(Path(args.final_receipt)),
        load_json(Path(args.combined_world)),
        float(args.rear_expansion_m),
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(RESULT)
    print(json.dumps({
        "predecessor_minimum_inner_clearance_m": report["articulated_sweep"]["predecessor_minimum_inner_clearance_m"],
        "candidate_minimum_inner_clearance_m": report["articulated_sweep"]["candidate_minimum_inner_clearance_m"],
        "candidate_service_frame_to_path_x_separation_m": report["world_relationships"]["candidate_service_frame_to_path_x_separation_m"],
        "candidate_service_frame_to_building_y_separation_m": report["world_relationships"]["candidate_service_frame_to_building_y_separation_m"],
    }, sort_keys=True))

if __name__ == "__main__":
    main()
