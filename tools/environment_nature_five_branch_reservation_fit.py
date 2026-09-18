from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

SCHEMA = "axm.environment-nature-five-branch-reservation-fit/v0.1"
RESULT = "PASS_CURRENT_WORLD_NATURE_FIVE_PRIMARY_BRANCH_DIAGNOSTIC_SWEEP_FITS_EXISTING_EAST_REAR_RESERVATION__VISUAL_WIND_RUNTIME_ADOPTION_HELD"
RULE = "DYNAMIC_NATURE_RECEIVERS_MUST_PROVE_THE_FULL_OWNER_SAMPLE_SWEEP_FITS_THE_EXISTING_WORLD_RESERVATION_BEFORE_ENVIRONMENT_REBIND__FITTING_THE_RESERVATION_DOES_NOT_GRANT_VISUAL_WIND_RUNTIME_OR_CANON_AUTHORITY"

EXPECTED_ENVIRONMENT_PARENT_HEAD = "4826db5d3a595bbeefdfd58d5541b2d78247e290"
EXPECTED_TA_HEAD = "b83c7d71759213d96c57874282e60705402540f5"
EXPECTED_ANIMATION_HEAD = "b0771b3319b783103c8e4677d062c00419df7559"
EXPECTED_RIGGING_HEAD = "898529f602893c8f6be179bd3e9b6821fc099904"
EXPECTED_UC_HEAD = "5c772b65eeba75abd0eb7a6c9c471b2d9975019d"
EXPECTED_SOURCE_DIGEST = "178cd8cfb1a859bff411f60e13154109528062cf0ad2384b343d406cc0cc9d61"
EXPECTED_MESH_DIGEST = "aa9d450a78fef722672ea9af0f9aca98b4c1a0ca3705661784f5f61f3e9b6a31"
EXPECTED_GLB_SHA256 = "3e3283a1f623ee8fc19bb00cf2fbe0a2cb3941da46bc913a062bf5bc19ad1d15"
EXPECTED_REBIND_RESULT = "PASS_BUILDING_UTILITY_PANEL_PRODUCTION_SUCCESSOR_ENVIRONMENT_CURRENT_WORLD_REBIND__OWNER_ART_QA_RUNTIME_IDENTITIES_CONVERGED__FINAL_ADOPTION_HELD"
EXPECTED_BRANCHES = ["south-low", "north-low", "east-mid", "west-high", "north-top"]
TARGET_ASSET = "source:nature:east-rear-tree-neutral-001"
TOL = 1e-6


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def exact_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def rx(degrees: float) -> np.ndarray:
    theta = math.radians(float(degrees))
    c, s = math.cos(theta), math.sin(theta)
    out = np.eye(4)
    out[1, 1] = c
    out[1, 2] = -s
    out[2, 1] = s
    out[2, 2] = c
    return out


def gltf_to_source(points: np.ndarray) -> np.ndarray:
    # Exact TA contract: source [x,y,z] -> UC/glTF [x,z,y].
    return points[:, [0, 2, 1]]


def bounds(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return points.min(axis=0), points.max(axis=0)


def load_scene(glb: Path) -> trimesh.Scene:
    scene = trimesh.load(glb, force="scene", process=False)
    if not isinstance(scene, trimesh.Scene):
        raise AssertionError("exact TA receiver did not import as a scene")
    return scene


def derive_environment_translation(
    scene: trimesh.Scene, current_vertices: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    neutral: list[np.ndarray] = []
    for node in scene.graph.nodes_geometry:
        transform, geom_name = scene.graph[node]
        verts = np.asarray(scene.geometry[geom_name].vertices, dtype=float)
        neutral.append(gltf_to_source(trimesh.transform_points(verts, transform)))
    expanded = np.vstack(neutral)
    src_min, src_max = bounds(expanded)
    world_min, world_max = bounds(current_vertices)
    if np.max(np.abs((src_max - src_min) - (world_max - world_min))) > TOL:
        raise AssertionError(
            "TA neutral receiver size does not match exact current east-rear Environment receiver"
        )
    from_min = world_min - src_min
    from_max = world_max - src_max
    if np.max(np.abs(from_min - from_max)) > TOL:
        raise AssertionError(
            "current east-rear receiver is not a pure translation of the exact TA neutral receiver"
        )
    translation = (from_min + from_max) * 0.5
    predicted_min = src_min + translation
    predicted_max = src_max + translation
    if (
        np.max(np.abs(predicted_min - world_min)) > TOL
        or np.max(np.abs(predicted_max - world_max)) > TOL
    ):
        raise AssertionError(
            "derived current-world east-rear translation does not reconstruct neutral bounds"
        )
    return translation, src_min, src_max


def build_report(
    contract: dict[str, Any],
    combined: dict[str, Any],
    ta_root: Path,
    rebind_report: dict[str, Any],
    rear_contraction_m: float,
) -> dict[str, Any]:
    if contract.get("schema") != SCHEMA:
        raise AssertionError("Environment Nature reservation-fit contract schema drift")
    if contract.get("environment", {}).get("parent_head") != EXPECTED_ENVIRONMENT_PARENT_HEAD:
        raise AssertionError("Environment parent head drift")
    if contract.get("technical_art", {}).get("head") != EXPECTED_TA_HEAD:
        raise AssertionError("Technical Art head drift")
    if rear_contraction_m < 0:
        raise AssertionError("negative rear contraction is invalid")

    expected_texts = {
        "exact-technical-art-head.txt": EXPECTED_TA_HEAD,
        "exact-animation-head.txt": EXPECTED_ANIMATION_HEAD,
        "exact-rigging-head.txt": EXPECTED_RIGGING_HEAD,
        "exact-uc-head.txt": EXPECTED_UC_HEAD,
    }
    for name, expected in expected_texts.items():
        got = exact_text(ta_root / name)
        if got != expected:
            raise AssertionError(f"{name} drift: {got}")

    target_contract = read_json(ta_root / "nature-primary-branch-animation-target-001.json")
    if target_contract.get("exact_inputs", {}).get("source_digest") != EXPECTED_SOURCE_DIGEST:
        raise AssertionError("TA target contract source digest drift")
    if (
        target_contract.get("exact_inputs", {}).get("geometry_migrated_mesh_digest")
        != EXPECTED_MESH_DIGEST
    ):
        raise AssertionError("TA target contract migrated mesh digest drift")
    if target_contract.get("acceptance", {}).get("one_branch_at_a_time_only") is not True:
        raise AssertionError("TA target contract one-branch-at-a-time boundary drift")

    godot_receipt = read_json(ta_root / "nature-primary-branch-animation-godot-target-receipt.json")
    if (
        godot_receipt.get("state")
        != "PASS_NATURE_FIVE_PRIMARY_BRANCH_ANIMATION_CURRENT_UC_GODOT_TARGET_RECEIVER"
    ):
        raise AssertionError("TA Godot target receiver is not green")
    if godot_receipt.get("receiver_glb_sha256") != EXPECTED_GLB_SHA256:
        raise AssertionError("TA Godot receiver GLB identity drift")
    if int(godot_receipt.get("samples_verified", -1)) != 205 or int(
        godot_receipt.get("receiver_nodes_verified", -1)
    ) != 12:
        raise AssertionError("TA Godot target receiver coverage drift")
    if (
        godot_receipt.get("truth_boundary", {}).get("simultaneous_multi_branch_motion_proven")
        is not False
    ):
        raise AssertionError("TA truth boundary unexpectedly grants simultaneous motion")

    glb = ta_root / "nature-primary-branch-receiver-rigid.glb"
    if sha256_file(glb) != EXPECTED_GLB_SHA256:
        raise AssertionError("exact TA receiver GLB byte identity drift")
    scene = load_scene(glb)
    if len(scene.graph.nodes_geometry) != 12:
        raise AssertionError("TA receiver scene node count drift")
    if sum(len(scene.geometry[g].faces) for g in scene.geometry) != 620:
        raise AssertionError("TA receiver triangle count drift")

    oracle = read_json(ta_root / "nature-primary-branch-animation-target-oracle.json")
    if oracle.get("branch_ids") != EXPECTED_BRANCHES:
        raise AssertionError("TA oracle branch identity/order drift")
    if sum(len(oracle["branches"][b]["samples"]) for b in EXPECTED_BRANCHES) != 205:
        raise AssertionError("TA oracle sample count drift")

    if rebind_report.get("result") != EXPECTED_REBIND_RESULT:
        raise AssertionError(
            "current Environment parent production rebind is not the exact green predecessor"
        )
    held = rebind_report.get("current_world_receive", {}).get("held_asset_types", [])
    if held != ["Building", "Object", "Nature", "Weather", "Environment dressing"]:
        raise AssertionError("current Environment parent held-asset identity drift")
    if rebind_report.get("remaining_holds", {}).get("environment_adoption") is not False:
        raise AssertionError("current Environment parent unexpectedly grants final adoption")

    states = combined.get("states", [])
    if len(states) != 17:
        raise AssertionError("current world must retain exact 17 Weather states")
    scene0 = states[0]["scene"]
    additional = scene0.get("additional_source_meshes", [])
    target_rows = [r for r in additional if r.get("asset_id") == TARGET_ASSET]
    if len(target_rows) != 1:
        raise AssertionError("current world must contain exactly one east-rear Nature receiver")
    target = target_rows[0]
    if (
        target.get("mesh_digest") != EXPECTED_MESH_DIGEST
        or len(target.get("vertices_source_xyz_m", [])) != 390
        or len(target.get("triangles", [])) != 570
    ):
        raise AssertionError("current east-rear Nature receiver identity drift")
    current_vertices = np.asarray(target["vertices_source_xyz_m"], dtype=float)

    replacement = scene0.get("environment_rear_tree_replacement", {})
    if replacement.get("target_asset_id") != "proxy:nature-tree-east-a":
        raise AssertionError("east-rear Environment reservation identity drift")
    if (
        replacement.get("placement_policy")
        != "PRESERVE_TARGET_CENTER_XY__GROUND_SOURCE_MIN_Z__NO_FORM_SCALE__NO_EXTRA_ROTATION"
    ):
        raise AssertionError("east-rear Environment placement policy drift")
    reserved = [float(v) for v in replacement.get("reserved_proxy_footprint_m", [])]
    if len(reserved) != 4:
        raise AssertionError("east-rear Environment reserved footprint missing")
    reserved[3] -= rear_contraction_m
    reserved_height = float(replacement.get("reserved_proxy_size_m", [0.0, 0.0, -1.0])[2])

    translation, neutral_src_min, neutral_src_max = derive_environment_translation(
        scene, current_vertices
    )

    # Trimesh has already flattened child transforms; branch woody and foliage
    # share the same exact pivot translation in this receiver.
    node_rows: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for node in scene.graph.nodes_geometry:
        transform, geom_name = scene.graph[node]
        node_rows[str(node)] = (
            np.asarray(scene.geometry[geom_name].vertices, dtype=float),
            np.asarray(transform, dtype=float),
        )

    sample_rows: list[dict[str, Any]] = []
    union_min = np.array([np.inf, np.inf, np.inf], dtype=float)
    union_max = np.array([-np.inf, -np.inf, -np.inf], dtype=float)
    minimum_reservation_margin = float("inf")
    minimum_reserved_envelope_margin = float("inf")
    minimum_ground_residual = float("inf")
    minimum_witness: dict[str, Any] | None = None
    minimum_envelope_witness: dict[str, Any] | None = None

    for branch in EXPECTED_BRANCHES:
        samples = oracle["branches"][branch]["samples"]
        if [int(r["index"]) for r in samples] != list(range(41)):
            raise AssertionError(f"{branch}: exact 41-sample index sequence drift")
        for sample in samples:
            angle = float(sample["target_receiver_angle_deg"])
            posed: list[np.ndarray] = []
            for node, (verts, base_transform) in node_rows.items():
                transform = base_transform
                if node.startswith(branch + "-"):
                    transform = base_transform @ rx(angle)
                posed.append(
                    gltf_to_source(trimesh.transform_points(verts, transform)) + translation
                )
            points = np.vstack(posed)
            pmin, pmax = bounds(points)
            union_min = np.minimum(union_min, pmin)
            union_max = np.maximum(union_max, pmax)
            margins = [
                float(pmin[0] - reserved[0]),
                float(reserved[1] - pmax[0]),
                float(pmin[1] - reserved[2]),
                float(reserved[3] - pmax[1]),
                float(pmin[2]),
                float(reserved_height - pmax[2]),
            ]
            local_min = min(margins)
            envelope_min = min(margins[0], margins[1], margins[2], margins[3], margins[5])
            witness = {
                "branch": branch,
                "sample_index": int(sample["index"]),
                "time_s": float(sample["time_s"]),
                "source_owner_angle_deg": float(sample["source_owner_angle_deg"]),
                "target_receiver_angle_deg": angle,
                "world_bounds_xyz_minmax_m": [pmin.tolist(), pmax.tolist()],
                "reservation_margins_left_right_front_rear_ground_top_m": margins,
            }
            sample_rows.append(witness)
            if local_min < minimum_reservation_margin:
                minimum_reservation_margin = local_min
                minimum_witness = witness
            if envelope_min < minimum_reserved_envelope_margin:
                minimum_reserved_envelope_margin = envelope_min
                minimum_envelope_witness = witness
            minimum_ground_residual = min(minimum_ground_residual, margins[4])

    if minimum_witness is None or minimum_envelope_witness is None:
        raise AssertionError("no Nature owner samples evaluated")
    if minimum_reservation_margin < -TOL:
        raise AssertionError(
            "exact Nature owner diagnostic sweep escapes current east-rear Environment "
            f"reservation: {minimum_reservation_margin:.9f} m"
        )

    # Coarse AABB separations are Environment composition guards only; they do
    # not claim collision, navigation or gameplay authority.
    readable_path = scene0.get("readable_path", {})
    path_separation_x = float(union_min[0] - float(readable_path["x_max"]))

    building_fp = np.asarray(
        scene0["environment_building_replacement"]["source_world_footprint_m"], dtype=float
    )
    building_y_gap = float(building_fp[2] - union_max[1])

    compact_fp = np.asarray(
        scene0["environment_replacement"]["source_world_footprint_m"], dtype=float
    )
    compact_y_gap = float(union_min[1] - compact_fp[3])

    object_fp = np.asarray(
        scene0["environment_object_replacement"]["source_world_footprint_m"], dtype=float
    )
    object_x_gap = float(union_min[0] - object_fp[1])

    if (
        path_separation_x <= 0.0
        or building_y_gap <= 0.0
        or compact_y_gap <= 0.0
        or object_x_gap <= 0.0
    ):
        raise AssertionError(
            "Nature diagnostic sweep crosses an existing current-world composition guard"
        )

    # All 17 retained states must keep the same target receiver and reservation.
    for state in states[1:]:
        sc = state["scene"]
        rows = [r for r in sc.get("additional_source_meshes", []) if r.get("asset_id") == TARGET_ASSET]
        if len(rows) != 1 or rows[0].get("mesh_digest") != EXPECTED_MESH_DIGEST:
            raise AssertionError(
                "east-rear Nature receiver identity drifts across retained Weather states"
            )
        if sc.get("environment_rear_tree_replacement", {}) != replacement:
            raise AssertionError(
                "east-rear Environment reservation drifts across retained Weather states"
            )

    return {
        "schema": SCHEMA,
        "result": RESULT,
        "reusable_rule": RULE,
        "exact_inputs": {
            "environment_parent_head": EXPECTED_ENVIRONMENT_PARENT_HEAD,
            "technical_art_head": EXPECTED_TA_HEAD,
            "animation_head": EXPECTED_ANIMATION_HEAD,
            "rigging_head": EXPECTED_RIGGING_HEAD,
            "uc_head": EXPECTED_UC_HEAD,
            "source_digest": EXPECTED_SOURCE_DIGEST,
            "neutral_mesh_digest": EXPECTED_MESH_DIGEST,
            "receiver_glb_sha256": EXPECTED_GLB_SHA256,
        },
        "current_world_identity": {
            "retained_weather_states": 17,
            "held_asset_types": held,
            "nature_target_asset": TARGET_ASSET,
            "neutral_vertices": 390,
            "neutral_triangles": 570,
            "target_receiver_nodes": 12,
            "target_receiver_triangles": 620,
            "receiver_world_translation_source_xyz_m": translation.tolist(),
        },
        "diagnostic_sweep": {
            "branch_ids": EXPECTED_BRANCHES,
            "samples_per_branch": 41,
            "owner_samples_evaluated": 205,
            "one_branch_at_a_time_only": True,
            "union_world_bounds_xyz_minmax_m": [union_min.tolist(), union_max.tolist()],
            "neutral_source_bounds_xyz_minmax_m": [
                neutral_src_min.tolist(),
                neutral_src_max.tolist(),
            ],
            "reserved_proxy_footprint_world_xy_m": reserved,
            "reserved_proxy_height_m": reserved_height,
            "minimum_reservation_margin_m_including_ground_numeric_residual": minimum_reservation_margin,
            "minimum_reserved_envelope_margin_m": minimum_reserved_envelope_margin,
            "minimum_ground_residual_m": minimum_ground_residual,
            "minimum_margin_witness": minimum_witness,
            "minimum_envelope_margin_witness": minimum_envelope_witness,
            "rear_contraction_negative_control_m": rear_contraction_m,
        },
        "composition_guards": {
            "readable_path_x_separation_m": path_separation_x,
            "building_y_separation_m": building_y_gap,
            "compact_east_tree_y_separation_m": compact_y_gap,
            "object_x_separation_m": object_x_gap,
            "collision_or_navigation_authority": False,
        },
        "decision": {
            "spatial_receive_ready": True,
            "scene_mutated": False,
            "environment_adoption": False,
            "visual_qa_acceptance": False,
            "wind_or_vfx_adoption": False,
            "runtime_target_device_acceptance": False,
            "simultaneous_multi_branch_motion_accepted": False,
            "canon": False,
            "production_ready": False,
        },
        "truth_boundary": (
            "PASS proves only that every exact one-branch-at-a-time owner sample already proven by Technical Art in Godot 4.7.2 can fit spatially inside the existing east-rear Map reservation without moving the tree, cameras, Building, Object, compact-east Nature receiver, Weather presentation or Environment dressing. "
            "The gate reconstructs all 205 exact target-receiver samples from the pinned TA GLB/oracle and the exact current-world placement. It does not render or aesthetically accept the motion, does not prove simultaneous multi-branch motion, natural wind timing, VFX behavior, collisions/navigation, Runtime target-device performance, CANON or production readiness."
        ),
        "samples": sample_rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", required=True)
    ap.add_argument("--combined-world", required=True)
    ap.add_argument("--ta-root", required=True)
    ap.add_argument("--parent-rebind-report", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--reservation-rear-contraction-m", type=float, default=0.0)
    args = ap.parse_args()

    report = build_report(
        read_json(Path(args.contract)),
        read_json(Path(args.combined_world)),
        Path(args.ta_root),
        read_json(Path(args.parent_rebind_report)),
        float(args.reservation_rear_contraction_m),
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(RESULT)
    print(
        json.dumps(
            {
                "owner_samples_evaluated": report["diagnostic_sweep"]["owner_samples_evaluated"],
                "minimum_reserved_envelope_margin_m": report["diagnostic_sweep"]["minimum_reserved_envelope_margin_m"],
                "minimum_ground_residual_m": report["diagnostic_sweep"]["minimum_ground_residual_m"],
                "readable_path_x_separation_m": report["composition_guards"]["readable_path_x_separation_m"],
                "building_y_separation_m": report["composition_guards"]["building_y_separation_m"],
                "compact_east_tree_y_separation_m": report["composition_guards"]["compact_east_tree_y_separation_m"],
                "object_x_separation_m": report["composition_guards"]["object_x_separation_m"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
