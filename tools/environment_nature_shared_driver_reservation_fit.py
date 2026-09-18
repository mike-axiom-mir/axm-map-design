from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA = "axm.environment-nature-shared-driver-reservation-fit/v0.2"
RESULT = "PASS_CURRENT_WORLD_NATURE_SHARED_DRIVER_SIMULTANEOUS_SAMPLED_SWEEP_FITS_EXISTING_EAST_REAR_RESERVATION__TARGET_HOST_VISUAL_WIND_RUNTIME_ADOPTION_HELD"
RULE = "SOURCE_MOTION_SUCCESSORS_MAY_REUSE_AN_EXISTING_WORLD_RESERVATION_ONLY_AFTER_THE_EXACT_NEW_SIMULTANEOUS_OWNER_SWEEP_IS_RETESTED__SPATIAL_FIT_DOES_NOT_TRANSFER_TARGET_HOST_WIND_VISUAL_OR_RUNTIME_ACCEPTANCE"

EXPECTED_ENVIRONMENT_PARENT_HEAD = "4826db5d3a595bbeefdfd58d5541b2d78247e290"
EXPECTED_ENVIRONMENT_PREDECESSOR_HEAD = "23decca57561ed8b77b3fa2e4d32faf854876d06"
EXPECTED_ANIMATION_HEAD = "bfb66da82bc358b14e52711bbdef7b58e4c943af"
EXPECTED_RIGGING_HEAD = "b4b480b415047fea90b4740f7702ced0dba9142d"
EXPECTED_ANIMATION_RESULT = "PASS_FIVE_SOCKET_SHARED_DRIVER_SIMULTANEOUS_DIAGNOSTIC_LOOP_SAMPLED_MOTION"
EXPECTED_RIGGING_RESULT = "PASS_FIVE_SOCKET_SHARED_DRIVER_RIG_COMPOSITION_CONTINUOUS_PARAMETER_MINUS5_TO_PLUS5"
EXPECTED_SOURCE_DIGEST = "178cd8cfb1a859bff411f60e13154109528062cf0ad2384b343d406cc0cc9d61"
EXPECTED_MESH_DIGEST = "aa9d450a78fef722672ea9af0f9aca98b4c1a0ca3705661784f5f61f3e9b6a31"
EXPECTED_REBIND_RESULT = "PASS_BUILDING_UTILITY_PANEL_PRODUCTION_SUCCESSOR_ENVIRONMENT_CURRENT_WORLD_REBIND__OWNER_ART_QA_RUNTIME_IDENTITIES_CONVERGED__FINAL_ADOPTION_HELD"
TARGET_ASSET = "source:nature:east-rear-tree-neutral-001"
EXPECTED_BRANCHES = ["south-low", "north-low", "east-mid", "west-high", "north-top"]
TOL = 1e-6


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bounds(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return points.min(axis=0), points.max(axis=0)


def derive_translation(neutral: np.ndarray, current: np.ndarray) -> np.ndarray:
    src_min, src_max = bounds(neutral)
    world_min, world_max = bounds(current)
    if np.max(np.abs((src_max - src_min) - (world_max - world_min))) > TOL:
        raise AssertionError("current east-rear receiver size drift from exact Nature neutral mesh")
    from_min = world_min - src_min
    from_max = world_max - src_max
    if np.max(np.abs(from_min - from_max)) > TOL:
        raise AssertionError("current east-rear receiver is not a pure translation of exact Nature neutral mesh")
    return (from_min + from_max) * 0.5


def load_owner(nature_root: Path):
    src = nature_root / "src"
    if not src.is_dir():
        raise AssertionError("exact Nature owner checkout missing src/")
    sys.path.insert(0, str(src))
    from axm_nature_design import organic_form
    from axm_nature_design import rear_tree_animation_shared_driver as animation
    from axm_nature_design import rear_tree_rigging_primary_branch_family as rig_family
    from axm_nature_design import rear_tree_rigging_shared_driver_composition as rig_composition
    return organic_form, animation, rig_family, rig_composition


def build_report(
    contract: dict[str, Any],
    combined: dict[str, Any],
    parent_rebind: dict[str, Any],
    nature_root: Path,
    rear_contraction_m: float,
    claim_target_host: bool,
) -> dict[str, Any]:
    if contract.get("schema") != SCHEMA:
        raise AssertionError("shared-driver Environment contract schema drift")
    if contract.get("environment", {}).get("parent_head") != EXPECTED_ENVIRONMENT_PARENT_HEAD:
        raise AssertionError("Environment parent head drift")
    if contract.get("environment", {}).get("predecessor_head") != EXPECTED_ENVIRONMENT_PREDECESSOR_HEAD:
        raise AssertionError("Environment predecessor head drift")
    if contract.get("animation", {}).get("head") != EXPECTED_ANIMATION_HEAD:
        raise AssertionError("Animation owner head drift")
    if contract.get("rigging", {}).get("head") != EXPECTED_RIGGING_HEAD:
        raise AssertionError("Rigging owner head drift")
    if rear_contraction_m < 0.0:
        raise AssertionError("negative rear contraction is invalid")
    if claim_target_host:
        raise AssertionError("source-mesh Environment spatial fit cannot claim target-host acceptance")

    organic_form, animation, rig_family, rig_composition = load_owner(nature_root)

    if animation.RIGGING_OWNER_HEAD != EXPECTED_RIGGING_HEAD:
        raise AssertionError("Animation module Rigging owner drift")
    if animation.RESULT != EXPECTED_ANIMATION_RESULT:
        raise AssertionError("Animation result identity drift")
    if rig_composition.RESULT != EXPECTED_RIGGING_RESULT:
        raise AssertionError("Rigging result identity drift")
    if list(rig_composition.BRANCH_IDS) != EXPECTED_BRANCHES:
        raise AssertionError("Rigging branch identity/order drift")

    source_path = nature_root / "examples" / "east_rear_tree_neutral_001.json"
    source = read_json(source_path)
    organic_form.validate_source(source)
    if organic_form.digest(source) != EXPECTED_SOURCE_DIGEST:
        raise AssertionError("Nature source digest drift")

    mesh = organic_form.build_mesh(source)
    if organic_form.digest(mesh) != EXPECTED_MESH_DIGEST:
        raise AssertionError("Nature migrated neutral mesh digest drift")
    neutral = np.asarray(mesh["vertices"], dtype=float)
    if neutral.shape != (390, 3) or len(mesh["triangles"]) != 570:
        raise AssertionError("Nature neutral receiver structural identity drift")

    animation_report = animation.evaluate(source)
    if animation_report.get("result") != EXPECTED_ANIMATION_RESULT:
        raise AssertionError("exact Animation owner prerequisite is not green")
    samples = animation_report.get("samples", [])
    if len(samples) != 41 or [int(row["index"]) for row in samples] != list(range(41)):
        raise AssertionError("exact 41-sample Animation sequence drift")
    if abs(float(samples[0]["shared_driver_deg"])) > 1e-12 or abs(float(samples[40]["shared_driver_deg"])) > 1e-12:
        raise AssertionError("Animation endpoint-neutral closure identity drift")

    probes = [
        rig_family._probe_branch(source, mesh, branch_id)
        for branch_id in rig_composition.BRANCH_IDS
    ]
    probes_by_branch = {probe["branch_id"]: probe for probe in probes}
    if set(probes_by_branch) != set(EXPECTED_BRANCHES):
        raise AssertionError("exact Rigging probe family drift")

    if parent_rebind.get("result") != EXPECTED_REBIND_RESULT:
        raise AssertionError("current Environment Building production rebind predecessor is not green")
    held = parent_rebind.get("current_world_receive", {}).get("held_asset_types", [])
    if held != ["Building", "Object", "Nature", "Weather", "Environment dressing"]:
        raise AssertionError("current Environment parent held-asset identity drift")
    if parent_rebind.get("remaining_holds", {}).get("environment_adoption") is not False:
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
    translation = derive_translation(neutral, current_vertices)

    replacement = scene0.get("environment_rear_tree_replacement", {})
    if replacement.get("target_asset_id") != "proxy:nature-tree-east-a":
        raise AssertionError("east-rear Environment reservation identity drift")
    if replacement.get("placement_policy") != "PRESERVE_TARGET_CENTER_XY__GROUND_SOURCE_MIN_Z__NO_FORM_SCALE__NO_EXTRA_ROTATION":
        raise AssertionError("east-rear Environment placement policy drift")
    reserved = [float(v) for v in replacement.get("reserved_proxy_footprint_m", [])]
    if len(reserved) != 4:
        raise AssertionError("east-rear Environment reserved footprint missing")
    reserved[3] -= rear_contraction_m
    reserved_height = float(replacement.get("reserved_proxy_size_m", [0.0, 0.0, -1.0])[2])

    for state in states[1:]:
        scene = state["scene"]
        rows = [r for r in scene.get("additional_source_meshes", []) if r.get("asset_id") == TARGET_ASSET]
        if len(rows) != 1 or rows[0] != target:
            raise AssertionError("east-rear Nature receiver drift across retained Weather states")
        if scene.get("environment_rear_tree_replacement", {}) != scene0.get("environment_rear_tree_replacement", {}):
            raise AssertionError("east-rear Environment reservation drift across retained Weather states")

    sample_rows: list[dict[str, Any]] = []
    union_min = np.array([np.inf, np.inf, np.inf], dtype=float)
    union_max = np.array([-np.inf, -np.inf, -np.inf], dtype=float)
    minimum_reservation_margin = float("inf")
    minimum_non_ground_margin = float("inf")
    minimum_ground_residual = float("inf")
    minimum_witness: dict[str, Any] | None = None
    minimum_non_ground_witness: dict[str, Any] | None = None

    neutral_list = [[float(v) for v in row] for row in neutral.tolist()]
    for sample in samples:
        shared_driver_deg = float(sample["shared_driver_deg"])
        posed = rig_composition._compose(
            neutral_list,
            probes_by_branch,
            shared_driver_deg,
            rig_composition.BRANCH_IDS,
        )
        world = np.asarray(posed, dtype=float) + translation
        pmin, pmax = bounds(world)
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
        non_ground_min = min(margins[0], margins[1], margins[2], margins[3], margins[5])
        witness = {
            "sample_index": int(sample["index"]),
            "time_s": float(sample["time_s"]),
            "shared_driver_deg": shared_driver_deg,
            "local_angles_deg": sample["local_angles_deg"],
            "world_bounds_xyz_minmax_m": [pmin.tolist(), pmax.tolist()],
            "reservation_margins_left_right_front_rear_ground_top_m": margins,
        }
        sample_rows.append(witness)
        if local_min < minimum_reservation_margin:
            minimum_reservation_margin = local_min
            minimum_witness = witness
        if non_ground_min < minimum_non_ground_margin:
            minimum_non_ground_margin = non_ground_min
            minimum_non_ground_witness = witness
        minimum_ground_residual = min(minimum_ground_residual, margins[4])

    if minimum_witness is None or minimum_non_ground_witness is None:
        raise AssertionError("no simultaneous Nature Animation samples evaluated")
    if minimum_reservation_margin < -TOL:
        raise AssertionError(
            "exact Nature simultaneous sampled sweep escapes current east-rear Environment "
            f"reservation: {minimum_reservation_margin:.9f} m"
        )

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

    if min(path_separation_x, building_y_gap, compact_y_gap, object_x_gap) <= 0.0:
        raise AssertionError("simultaneous Nature sampled sweep crosses an existing current-world composition guard")

    return {
        "schema": SCHEMA,
        "result": RESULT,
        "reusable_rule": RULE,
        "exact_inputs": {
            "environment_parent_head": EXPECTED_ENVIRONMENT_PARENT_HEAD,
            "environment_predecessor_head": EXPECTED_ENVIRONMENT_PREDECESSOR_HEAD,
            "animation_head": EXPECTED_ANIMATION_HEAD,
            "rigging_head": EXPECTED_RIGGING_HEAD,
            "source_digest": EXPECTED_SOURCE_DIGEST,
            "mesh_digest": EXPECTED_MESH_DIGEST,
        },
        "current_world": {
            "weather_states_retained": 17,
            "held_asset_types": held,
            "east_rear_translation_xyz_m": translation.tolist(),
            "environment_reservation_xy_m": reserved,
            "environment_reserved_height_m": reserved_height,
        },
        "simultaneous_sampled_sweep": {
            "samples_evaluated": len(sample_rows),
            "duration_s": float(animation.DURATION_S),
            "sample_rate_hz": int(animation.SAMPLE_RATE_HZ),
            "shared_driver_interval_deg": [-float(animation.AMPLITUDE_DEG), float(animation.AMPLITUDE_DEG)],
            "union_world_bounds_xyz_min_m": union_min.tolist(),
            "union_world_bounds_xyz_max_m": union_max.tolist(),
            "minimum_reservation_margin_m": minimum_reservation_margin,
            "minimum_reservation_witness": minimum_witness,
            "minimum_non_ground_reserved_envelope_margin_m": minimum_non_ground_margin,
            "minimum_non_ground_witness": minimum_non_ground_witness,
            "minimum_ground_residual_m": minimum_ground_residual,
        },
        "current_world_separation_guards": {
            "readable_path_x_separation_m": path_separation_x,
            "building_y_separation_m": building_y_gap,
            "compact_east_nature_y_separation_m": compact_y_gap,
            "articulated_object_x_separation_m": object_x_gap,
        },
        "decision": {
            "spatial_receive_ready_for_exact_source_motion_successor": True,
            "world_scene_changed": False,
            "tree_placement_changed": False,
            "reservation_changed": rear_contraction_m != 0.0,
            "target_host_acceptance": False,
            "visual_wind_acceptance": False,
            "runtime_acceptance": False,
            "art_direction_acceptance": False,
            "independent_visual_qa_acceptance": False,
            "environment_adoption": False,
            "canon": False,
        },
        "truth_boundary": (
            "PASS proves only that all 41 exact simultaneous source-mesh Animation samples from the pinned "
            "Animation/Rigging successor fit the existing east-rear Environment reservation at the unchanged "
            "current-world placement while preserving positive coarse separation from the readable path, Building, "
            "compact-east Nature and articulated Object. It does not transfer Technical-Art target-host playback, "
            "visual-wind semantics, Art/QA acceptance, Runtime/device behavior, collision/navigation, CANON or "
            "production readiness."
        ),
        "samples": sample_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--combined-world", required=True, type=Path)
    parser.add_argument("--parent-rebind-report", required=True, type=Path)
    parser.add_argument("--nature-root", required=True, type=Path)
    parser.add_argument("--reservation-rear-contraction-m", type=float, default=0.0)
    parser.add_argument("--claim-target-host", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    report = build_report(
        read_json(args.contract),
        read_json(args.combined_world),
        read_json(args.parent_rebind_report),
        args.nature_root,
        float(args.reservation_rear_contraction_m),
        bool(args.claim_target_host),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["result"])
    print(json.dumps({
        "minimum_reservation_margin_m": report["simultaneous_sampled_sweep"]["minimum_reservation_margin_m"],
        "minimum_non_ground_reserved_envelope_margin_m": report["simultaneous_sampled_sweep"]["minimum_non_ground_reserved_envelope_margin_m"],
        **report["current_world_separation_guards"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
