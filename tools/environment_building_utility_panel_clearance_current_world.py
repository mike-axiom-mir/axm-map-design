from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

SCHEMA = "axm.environment-building-utility-panel-clearance-current-world/v0.1"
RESULT = "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_CLEARANCE_REBIND_RECEIVER__VISUAL_OBSERVABILITY_CHARACTERIZED__ADOPTION_HELD"
RULE = "SOURCE_OWNED_RECEIVER_PLACEMENT_SUCCESSOR_MUST_BE_REBOUND_EXPLICITLY_IN_THE_REAL_WORLD_WHILE_UNRELATED_ASSET_CANDIDATES_REMAIN_EXACT_AND_ADOPTION_STAYS_HELD"
BUILDING_ASSET = "source:building:service-pavilion-001"
OBJECT_ASSET = "source:object:modular-equipment-case-001"
COMPACT_ASSET = "source:nature:compact-east-tree-neutral-001"
ROUGHNESS_STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_APPEARANCE_CANDIDATE_BOUND__ENVIRONMENT_ADOPTION_HELD"
SOURCE_HEAD = "fbfa3b47048755b45dac91451171d5511c8d4f47"
SOURCE_CONTENT_HEAD = "32bbdd54f00aaac87ba8139bf932d8aff6109a66"
PROCEDURAL_HEAD = "0c458e19cda73e26e90531d24fe7697b5a8d14fc"
CURRENT_POLICY_HEAD = "a976af429b0ea90e0f0cc72d4a8bd4eb8fef22d3"
CURRENT_VARIANT = "header-segmented-23"
SEGMENTATION_SOURCE_HEAD = "34124101e616c423c5a3ed5e122ddf09b98a1650"
SEGMENTATION_REVISION = "service-pavilion-001/interpenetration-free-header-segmentation-003"
PARENT_HEAD = "4bd7eaf6970716dde4159448c92556785f47e954"
PARENT_ARTIFACT_SHA256 = "8f2f8aa4bb11e2f868a6ce36dd381933ba1ea6c59be7b82ed00d1dfe5402ee97"
CONTEXTS = ("path_eye", "elevated_oblique")
MODES = ("control", "candidate")
FRAME_RE = re.compile(r"^atmosphere-width-(control|candidate)-(path_eye|elevated_oblique)-(\d\d)\.png$")
EPS = 1e-6


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def approx_vec(actual: Any, expected: list[float], eps: float = EPS) -> bool:
    return isinstance(actual, list) and len(actual) == 3 and all(
        abs(float(a) - float(b)) <= eps for a, b in zip(actual, expected, strict=True)
    )


def find(rows: Any, asset_id: str) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise ValueError("runtime static_source_meshes missing")
    matches = [row for row in rows if isinstance(row, dict) and row.get("asset_id") == asset_id]
    if len(matches) != 1:
        raise ValueError(f"expected one {asset_id}, got {len(matches)}")
    return matches[0]


def verify_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema") != SCHEMA or contract.get("reusable_rule") != RULE:
        raise ValueError("Environment clearance contract identity drift")
    parent = contract.get("parent_environment", {})
    if parent.get("head") != PARENT_HEAD or parent.get("artifact_sha256") != PARENT_ARTIFACT_SHA256:
        raise ValueError("exact multi-asset parent identity drift")
    source = contract.get("building_source_authority", {})
    if source.get("current_head") != SOURCE_HEAD or source.get("source_content_head") != SOURCE_CONTENT_HEAD:
        raise ValueError("Building source authority drift")
    procedural = contract.get("procedural_rebind_authority", {})
    if procedural.get("head") != PROCEDURAL_HEAD or procedural.get("automatic_receiver_adoption") is not False:
        raise ValueError("Building Procedural authority/adoption boundary drift")
    current = contract.get("current_receiver_authority", {})
    if current.get("source_policy_head") != CURRENT_POLICY_HEAD:
        raise ValueError("current Building receiver policy head drift")
    if current.get("current_source_variant_id") != CURRENT_VARIANT:
        raise ValueError("current Building receiver variant drift")
    if current.get("segmentation_source_head") != SEGMENTATION_SOURCE_HEAD:
        raise ValueError("current Building segmentation source head drift")
    if current.get("segmentation_revision") != SEGMENTATION_REVISION:
        raise ValueError("current Building segmentation revision drift")
    if current.get("placement_translation_source_xyz_m") != [0.0, 7.2, 0.0]:
        raise ValueError("current Building placement translation drift")
    receiver = contract.get("receiver_rebind", {})
    if receiver.get("expected_vertex_count") != 184 or receiver.get("expected_triangle_count") != 276 or receiver.get("expected_surface_count") != 5:
        raise ValueError("current Building receiver structural identity drift")
    if receiver.get("current_receiver_vertex_groups", {}).get("front-utility-bay") != list(range(168, 176)):
        raise ValueError("front current receiver vertex group drift")
    if receiver.get("current_receiver_vertex_groups", {}).get("east-utility-bay") != list(range(176, 184)):
        raise ValueError("east current receiver vertex group drift")
    decision = contract.get("decision", {})
    for key in (
        "environment_building_clearance_adoption",
        "environment_selected_roughness_adoption",
        "environment_compact_east_adoption",
    ):
        if decision.get(key) is not False:
            raise ValueError(f"automatic Environment adoption forbidden: {key}")


def verify_source(
    contract: dict[str, Any], pavilion: dict[str, Any], panel: dict[str, Any], procedural: dict[str, Any]
) -> dict[str, Any]:
    source = contract["building_source_authority"]
    if pavilion.get("asset_id") != "service-pavilion-001" or panel.get("asset_id") != "utility-access-panel-001":
        raise ValueError("Building source asset identity drift")
    if abs(float(panel.get("standoff_from_receiver_origin_m", -1)) - 0.10) > EPS:
        raise ValueError("corrected panel standoff drift")
    if abs(float(panel.get("body_depth_m", -1)) - 0.08) > EPS:
        raise ValueError("panel body depth drift")
    if abs(float(panel.get("required_body_clearance_beyond_plate_m", -1)) - 0.02) > EPS:
        raise ValueError("panel required body clearance drift")
    interfaces = {row.get("id"): row for row in pavilion.get("interfaces", []) if isinstance(row, dict)}
    expected = {
        "front-utility-bay": {"origin": [-2.45, -1.00, 1.65], "normal": [0.0, -1.0, 0.0]},
        "east-utility-bay": {"origin": [3.80, 0.10, 1.65], "normal": [1.0, 0.0, 0.0]},
    }
    for receiver_id, truth in expected.items():
        row = interfaces.get(receiver_id)
        if not row or row.get("origin") != truth["origin"] or row.get("normal") != truth["normal"]:
            raise ValueError(f"Building receiver frame drift: {receiver_id}")
        if abs(float(row.get("plate_thickness_m", -1)) - float(source["receiver_plate_thickness_m"])) > EPS:
            raise ValueError(f"receiver plate thickness drift: {receiver_id}")
    physical_gap = 0.10 - 0.04 - 0.5 * 0.08
    if abs(physical_gap - 0.02) > EPS:
        raise ValueError("source physical body gap arithmetic drift")

    if procedural.get("schema") != "axm.building-utility-panel-clearance-rebind-family/v0.1":
        raise ValueError("Procedural clearance family schema drift")
    if procedural.get("receiver_ids") != ["front-utility-bay", "east-utility-bay"]:
        raise ValueError("Procedural receiver identity/order drift")
    if abs(float(procedural.get("required_standoff_delta_m", -1)) - 0.02) > EPS:
        raise ValueError("Procedural standoff delta drift")
    if procedural.get("automatic_receiver_adoption") is not False:
        raise ValueError("Procedural automatic adoption boundary drift")
    return {"physical_body_gap_m": physical_gap, "receiver_count": 2}


def _assert_building_structural_identity(before: dict[str, Any], after: dict[str, Any], index: int) -> None:
    expected = {"vertices": 184, "triangles": 276, "surface_count": 5}
    for key, value in expected.items():
        if int(before.get(key, -1)) != value or int(after.get(key, -1)) != value:
            raise ValueError(f"current Building {key} identity drift at state {index}")
    stable_keys = (
        "material_ids",
        "material_profile_sha256",
        "proof_culling",
        "receiving_policy",
        "header_segmentation_revision",
        "source_positive_volume_intersection_count",
        "successor_positive_volume_intersection_count",
    )
    for key in stable_keys:
        if before.get(key) != after.get(key):
            raise ValueError(f"current Building structural/material metadata changed during clearance rebind: {key} state {index}")
    if after.get("header_segmentation_revision") != SEGMENTATION_REVISION:
        raise ValueError(f"current Building segmentation revision drift at state {index}")


def verify_runtime(parent: dict[str, Any], candidate: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    samples_parent = parent.get("samples", [])
    samples_candidate = candidate.get("samples", [])
    if len(samples_parent) != 17 or len(samples_candidate) != 17:
        raise ValueError("current-world 17-state runtime sequence drift")
    rebound = 0
    roughness_exact = 0
    compact_exact = 0
    compact_phases: list[int] = []
    weather_measurements = 0
    weather_max_residual = 0.0
    runtime_delta: dict[str, set[int]] = {k: set() for k in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame")}

    receiver = contract["receiver_rebind"]
    current = contract["current_receiver_authority"]
    for index, (before, after) in enumerate(zip(samples_parent, samples_candidate, strict=True)):
        if int(before.get("index", -1)) != index or int(after.get("index", -1)) != index:
            raise ValueError(f"runtime state index drift at {index}")
        before_building = find(before.get("static_source_meshes"), BUILDING_ASSET)
        building = find(after.get("static_source_meshes"), BUILDING_ASSET)
        _assert_building_structural_identity(before_building, building, index)
        obs = building.get("environment_building_utility_panel_clearance_current_world")
        if not isinstance(obs, dict) or obs.get("state") != RESULT:
            raise ValueError(f"Building clearance observation missing at state {index}")
        if obs.get("building_source_head") != SOURCE_HEAD or obs.get("building_source_content_head") != SOURCE_CONTENT_HEAD:
            raise ValueError(f"Building source provenance drift at state {index}")
        if obs.get("building_procedural_head") != PROCEDURAL_HEAD:
            raise ValueError(f"Building Procedural provenance drift at state {index}")
        if obs.get("current_receiver_source_policy_head") != CURRENT_POLICY_HEAD or obs.get("current_receiver_source_variant_id") != CURRENT_VARIANT:
            raise ValueError(f"Building current receiver policy identity drift at state {index}")
        if obs.get("current_receiver_segmentation_source_head") != SEGMENTATION_SOURCE_HEAD or obs.get("current_receiver_segmentation_revision") != SEGMENTATION_REVISION:
            raise ValueError(f"Building current receiver segmentation identity drift at state {index}")
        if not approx_vec(obs.get("placement_translation_source_xyz_m"), current["placement_translation_source_xyz_m"]):
            raise ValueError(f"Building current receiver placement translation drift at state {index}")
        for prefix, receiver_id in (("front", "front-utility-bay"), ("east", "east-utility-bay")):
            checks = (
                (f"{prefix}_predecessor_center_source_xyz_m", receiver["predecessor_centers_source_xyz_m"][receiver_id]),
                (f"{prefix}_successor_center_source_xyz_m", receiver["successor_centers_source_xyz_m"][receiver_id]),
                (f"{prefix}_predecessor_center_receiver_xyz_m", receiver["predecessor_centers_current_receiver_xyz_m"][receiver_id]),
                (f"{prefix}_successor_center_receiver_xyz_m", receiver["successor_centers_current_receiver_xyz_m"][receiver_id]),
            )
            for key, expected in checks:
                if not approx_vec(obs.get(key), expected):
                    raise ValueError(f"{key} drift at state {index}")
        if obs.get("translated_source_vertex_count") != 16:
            raise ValueError(f"Building translated vertex count drift at state {index}")
        for key in ("topology_changed", "surface_partition_changed", "material_values_changed"):
            if obs.get(key) is not False:
                raise ValueError(f"Building bounded-rebind boundary drift: {key} state {index}")
        if obs.get("environment_adoption") is not False:
            raise ValueError(f"Building Environment adoption must remain held at state {index}")
        rebound += 1

        before_obj = find(before.get("static_source_meshes"), OBJECT_ASSET)
        after_obj = find(after.get("static_source_meshes"), OBJECT_ASSET)
        before_rough = before_obj.get("environment_object_selected_roughness_current_world")
        after_rough = after_obj.get("environment_object_selected_roughness_current_world")
        if not isinstance(after_rough, dict) or after_rough.get("state") != ROUGHNESS_STATE or after_rough.get("environment_adoption") is not False:
            raise ValueError(f"Object roughness held-state drift at state {index}")
        if before_rough != after_rough:
            raise ValueError(f"Object roughness receiver changed during Building rebind at state {index}")
        roughness_exact += 1

        before_compact = find(before.get("static_source_meshes"), COMPACT_ASSET)
        after_compact = find(after.get("static_source_meshes"), COMPACT_ASSET)
        compact_keys = (
            "compact_east_visual_response_phase_index",
            "compact_east_visual_response_vfx_head",
            "compact_east_visual_response_weather_semantics",
        )
        if any(before_compact.get(k) != after_compact.get(k) for k in compact_keys):
            raise ValueError(f"compact-east receiving identity drift at state {index}")
        phase = int(after_compact.get("compact_east_visual_response_phase_index", -1))
        if phase != index:
            raise ValueError(f"compact-east phase drift at state {index}")
        compact_phases.append(phase)
        compact_exact += 1

        for context in CONTEXTS:
            weather = after["contexts"][context]["candidate"]["weather_update"]
            weather_measurements += int(weather.get("measured_width_count", 0))
            weather_max_residual = max(
                weather_max_residual, float(weather.get("maximum_projected_width_residual_px", 999.0))
            )
            for mode in MODES:
                a = before["contexts"][context][mode]["runtime"]
                b = after["contexts"][context][mode]["runtime"]
                for field in runtime_delta:
                    runtime_delta[field].add(int(b[field]) - int(a[field]))

    if compact_phases != list(range(17)):
        raise ValueError("compact-east exact 17-phase sequence drift")
    if weather_measurements != 1224 or weather_max_residual > 0.05:
        raise ValueError(f"Weather width continuity failed: {weather_measurements=} {weather_max_residual=}")
    if any(values != {0} for values in runtime_delta.values()):
        raise ValueError(f"Building placement rebind changed structural submission counts: {runtime_delta}")
    top_level_exact = {
        "environment_building_utility_panel_clearance_current_receiver_source_policy_head": CURRENT_POLICY_HEAD,
        "environment_building_utility_panel_clearance_current_receiver_variant_id": CURRENT_VARIANT,
        "environment_building_utility_panel_clearance_current_receiver_segmentation_source_head": SEGMENTATION_SOURCE_HEAD,
        "environment_building_utility_panel_clearance_current_receiver_segmentation_revision": SEGMENTATION_REVISION,
    }
    for key, expected in top_level_exact.items():
        if candidate.get(key) != expected:
            raise ValueError(f"top-level current Building receiver identity drift: {key}")
    if candidate.get("environment_building_utility_panel_clearance_adoption") is not False:
        raise ValueError("top-level Building Environment adoption boundary drift")

    return {
        "building_rebound_states": rebound,
        "building_current_receiver_rebound_states": rebound,
        "building_current_receiver_identity": {
            "source_policy_head": CURRENT_POLICY_HEAD,
            "source_variant_id": CURRENT_VARIANT,
            "segmentation_source_head": SEGMENTATION_SOURCE_HEAD,
            "segmentation_revision": SEGMENTATION_REVISION,
            "vertices": 184,
            "triangles": 276,
            "surfaces": 5,
        },
        "object_roughness_exact_states": roughness_exact,
        "compact_east_exact_states": compact_exact,
        "compact_east_phase_indices": compact_phases,
        "weather_width_measurements": weather_measurements,
        "weather_width_maximum_residual_px": weather_max_residual,
        "structural_runtime_deltas": {k: sorted(v) for k, v in runtime_delta.items()},
    }


def image_delta(parent_root: str | Path, candidate_root: str | Path) -> dict[str, Any]:
    parent_dir = Path(parent_root)
    candidate_dir = Path(candidate_root)
    parent_files = sorted(p for p in parent_dir.glob("atmosphere-width-*.png") if FRAME_RE.match(p.name))
    if len(parent_files) != 68:
        raise ValueError(f"expected 68 exact parent frames, got {len(parent_files)}")
    total_changed = 0
    changed_frames = 0
    max_changed = 0
    by_context_mode: dict[str, dict[str, int]] = {}
    global_bbox: list[int] | None = None
    for parent_path in parent_files:
        match = FRAME_RE.match(parent_path.name)
        assert match is not None
        mode, context, _index = match.groups()
        candidate_path = candidate_dir / parent_path.name
        if not candidate_path.exists():
            raise ValueError(f"candidate frame missing: {candidate_path.name}")
        with Image.open(parent_path).convert("RGB") as a, Image.open(candidate_path).convert("RGB") as b:
            if a.size != b.size:
                raise ValueError(f"frame dimensions drift: {parent_path.name}")
            diff = ImageChops.difference(a, b)
            bbox = diff.getbbox()
            changed = 0
            if bbox is not None:
                changed = sum(1 for px in diff.getdata() if px != (0, 0, 0))
                bb = [bbox[0], bbox[1], bbox[2] - 1, bbox[3] - 1]
                if global_bbox is None:
                    global_bbox = bb
                else:
                    global_bbox = [
                        min(global_bbox[0], bb[0]),
                        min(global_bbox[1], bb[1]),
                        max(global_bbox[2], bb[2]),
                        max(global_bbox[3], bb[3]),
                    ]
            total_changed += changed
            changed_frames += int(changed > 0)
            max_changed = max(max_changed, changed)
            key = f"{mode}:{context}"
            row = by_context_mode.setdefault(key, {"frames": 0, "changed_frames": 0, "changed_pixels": 0})
            row["frames"] += 1
            row["changed_frames"] += int(changed > 0)
            row["changed_pixels"] += changed
    return {
        "matched_frames": 68,
        "changed_frames": changed_frames,
        "total_changed_pixels": total_changed,
        "maximum_changed_pixels_single_frame": max_changed,
        "global_changed_pixel_bbox_xyxy": global_bbox,
        "by_mode_context": by_context_mode,
        "observability_policy": "CHARACTERIZE_ONLY_NO_MINIMUM_PIXEL_DELTA_REQUIRED",
    }


def verify(args: argparse.Namespace) -> dict[str, Any]:
    contract = load(args.contract)
    verify_contract(contract)
    source = verify_source(contract, load(args.pavilion), load(args.panel), load(args.procedural_profile))
    parent_runtime = load(args.parent_runtime)
    candidate_runtime = load(args.candidate_runtime)
    runtime = verify_runtime(parent_runtime, candidate_runtime, contract)
    visual = image_delta(args.parent_frames, args.candidate_frames)
    report = {
        "schema": SCHEMA,
        "state": RESULT,
        "environment_head": args.environment_head,
        "parent_environment_head": PARENT_HEAD,
        "reusable_rule": RULE,
        "failed_predecessor": {
            "workflow_run": 35260357907,
            "head": "ce40c64bbfa07cd944bae6fac322986aea5307c5",
            "artifact_id": 10514557596,
            "artifact_sha256": "756719002b6658690b7e68713921a92687a3fd902e640455194e179d440352ce",
            "diagnosis": "FIRST_ATTEMPT_TARGETED_LEGACY_152_VERTEX_COMPATIBILITY_RECEIVER_WHILE_ACTIVE_WORLD_RENDERED_184_VERTEX_HEADER_SEGMENTED_RECEIVER",
            "failed_attempt_changed_pixels": 0
        },
        "source_authority": {
            "building_current_head": SOURCE_HEAD,
            "building_source_content_head": SOURCE_CONTENT_HEAD,
            "procedural_head": PROCEDURAL_HEAD,
            **source,
        },
        "real_world_scope": {
            "states": 17,
            "matched_frames": 68,
            "assets_present": [
                "Building current header-segmented receiver",
                "Nature west-sapling",
                "Nature compact-east",
                "Object selected roughness",
                "Map footprint cue",
                "Weather source-width presentation",
            ],
        },
        "runtime_continuity": runtime,
        "visual_observability": visual,
        "environment_building_clearance_adoption": False,
        "environment_selected_roughness_adoption": False,
        "environment_compact_east_adoption": False,
        "art_qa_acceptance_required": True,
        "runtime_acceptance_required": True,
        "truth_boundary": "PASS proves only that the exact source/procedural two-panel +0.02 m clearance successor is received by the active 184-vertex header-segmented-23 Building representation in the exact retained selected-roughness + compact-east + Weather current world without changing Object roughness identity, compact-east phase identity, Weather width behavior or structural submission counts. The failed predecessor remains evidence that a legacy compatibility-path mutation is insufficient. Pixel delta is characterized, not aesthetically accepted. Environment adoption, Art/QA acceptance, Runtime/device acceptance, gameplay, CANON and production readiness remain separate.",
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": report["state"], "visual_observability": visual, "runtime_continuity": runtime}, indent=2, sort_keys=True))
    return report


def negative_control(args: argparse.Namespace) -> None:
    contract = load(args.contract)
    parent = load(args.parent_runtime)
    candidate = load(args.candidate_runtime)
    mutated = copy.deepcopy(candidate)
    building = find(mutated["samples"][0].get("static_source_meshes"), BUILDING_ASSET)
    obs = building["environment_building_utility_panel_clearance_current_world"]
    obs["front_successor_center_receiver_xyz_m"] = [-2.45, 6.11, 1.65]
    try:
        verify_runtime(parent, mutated, contract)
    except ValueError as exc:
        print("PASS_REJECTED_MUTATED_BUILDING_CLEARANCE_CURRENT_RECEIVER:", exc)
        return
    raise SystemExit("negative control unexpectedly passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--contract", required=True)
    common.add_argument("--parent-runtime", required=True)
    common.add_argument("--candidate-runtime", required=True)

    p = sub.add_parser("verify", parents=[common])
    p.add_argument("--pavilion", required=True)
    p.add_argument("--panel", required=True)
    p.add_argument("--procedural-profile", required=True)
    p.add_argument("--parent-frames", required=True)
    p.add_argument("--candidate-frames", required=True)
    p.add_argument("--environment-head", required=True)
    p.add_argument("--output", required=True)

    sub.add_parser("negative-control", parents=[common])
    args = parser.parse_args()
    if args.command == "verify":
        verify(args)
    else:
        negative_control(args)


if __name__ == "__main__":
    main()
