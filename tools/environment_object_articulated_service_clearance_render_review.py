from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

SCHEMA = "axm.environment-object-articulated-service-clearance-render-review/v0.2"
VISIBLE_RESULT = "PASS_CURRENT_WORLD_OBJECT_ARTICULATED_SERVICE_CLEARANCE_SUCCESSOR_RENDERED__LOCALIZED_VISUAL_DELTA__ADOPTION_HELD"
ZERO_RESULT = "PASS_CURRENT_WORLD_OBJECT_ARTICULATED_SERVICE_CLEARANCE_SUCCESSOR_RENDERED__ZERO_RASTER_DELTA_CHARACTERIZED__ADOPTION_HELD"
RULE = "SPATIALLY_PROVEN_ENVIRONMENT_DRESSING_SUCCESSOR_MUST_BE_RENDERED_AGAINST_THE_EXACT_PREDECESSOR_WORLD_WITH_OWNER_MOTION_CAMERAS_LIGHTS_AND_UNRELATED_ASSETS_HELD"

EXPECTED_SPATIAL_RESULT = "PASS_CURRENT_WORLD_OBJECT_ARTICULATED_SERVICE_CLEARANCE_SUCCESSOR__20MM_REAR_DRESSING_EXPANSION_RESTORES_60MM_SWEEP_CLEARANCE__ADOPTION_HELD"
EXPECTED_TA_HEAD = "e085437f6cc958bbf7c5c6464578923d542962b0"
EXPECTED_ANIMATION_HEAD = "c688936a84f80f292e43587c9d3386bd717f8178"
EXPECTED_SEQUENCE_DIGEST = "0a3523cf792264f610881552fd2ebd438aabdfd05e30e92af9dbb33ded1fa2d3"
EXPECTED_OBJECT_SHA = "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
FRAME_ASSET_ID = "environment:dressing:west-object-service-footprint-frame-001"
OLD = [-4.025387, -2.890757, 3.736077, 4.8707069999999995]
NEW = [-4.025387, -2.890757, 3.736077, 4.890707]
STRIP_WIDTH_M = 0.045
FRAME_HEIGHT_M = 0.02
EXPECTED_SAMPLES = [0, 40]
EXPECTED_STATE_COUNT = 17
EXPECTED_FRAME_COUNT = 68
PIXEL_LOCALITY_PAD = 2

# Godot instance IDs are process-local handles. Separate predecessor/successor
# executions must not be treated as content drift merely because these handles
# differ. No authored/source/runtime scalar is ignored.
PROCESS_LOCAL_KEYS = {"node_instance_id", "mesh_instance_id", "material_instance_id"}

IDENTITY_KEYS = [
    "godot_version",
    "environment_building_current_source_variant_id",
    "environment_building_header_segmentation_revision",
    "environment_building_utility_panel_clearance_current_world_state",
    "environment_compact_east_visual_response_vfx_head",
    "environment_compact_east_visual_response_phase_count",
    "environment_nature_source_migration_head",
    "environment_nature_materials_head",
    "environment_nature_material_family_id",
    "environment_object_materials_head",
    "environment_object_material_source_head",
    "environment_object_material_source_sha256",
    "environment_object_selected_roughness_materials_head",
    "environment_object_selected_roughness_technical_art_head",
    "environment_object_selected_roughness_png_sha256",
    "environment_object_selected_uv0_current_world_state",
    "source_width_profile_digest",
    "weather_variant_head",
    "weather_variant_layout_digest",
    "weather_variant_seed",
    "technical_art_object_motion_animation_head",
    "technical_art_object_motion_sequence_digest",
    "technical_art_object_motion_owner_to_host_frame_rule",
    "technical_art_object_motion_current_world_state",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def same_float_list(a: Any, b: list[float], eps: float = 1e-6) -> bool:
    return isinstance(a, list) and len(a) == len(b) and all(abs(float(x) - float(y)) <= eps for x, y in zip(a, b))


def semantic_runtime_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: semantic_runtime_value(v) for k, v in value.items() if k not in PROCESS_LOCAL_KEYS}
    if isinstance(value, list):
        return [semantic_runtime_value(v) for v in value]
    return value


def frame_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hits = [r for r in rows if r.get("asset_id") == FRAME_ASSET_ID]
    if len(hits) != 1:
        raise AssertionError(f"expected one Environment service frame, got {len(hits)}")
    return hits[0]


def other_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if r.get("asset_id") != FRAME_ASSET_ID]


def validate_frame(row: dict[str, Any], expected: list[float], successor: bool) -> None:
    if not same_float_list(row.get("outer_footprint_source_xy_m"), expected):
        raise AssertionError(f"service-frame footprint drift: {row.get('outer_footprint_source_xy_m')} != {expected}")
    if int(row.get("triangles", -1)) != 48 or int(row.get("surface_count", -1)) != 1:
        raise AssertionError("service-frame topology drift")
    if abs(float(row.get("strip_width_m", -1.0)) - STRIP_WIDTH_M) > 1e-6:
        raise AssertionError("service-frame strip-width drift")
    if abs(float(row.get("frame_height_m", -1.0)) - FRAME_HEIGHT_M) > 1e-6:
        raise AssertionError("service-frame height drift")
    if successor:
        if abs(float(row.get("rear_outer_edge_expansion_m", -1.0)) - 0.02) > 1e-6:
            raise AssertionError("successor service-frame expansion metadata drift")
        if row.get("environment_adoption") is not False:
            raise AssertionError("successor service-frame adoption authority inflated")
        if not same_float_list(row.get("predecessor_outer_footprint_source_xy_m"), OLD):
            raise AssertionError("successor predecessor identity drift")


def selected_motion_index(runtime: dict[str, Any]) -> int:
    found: set[int] = set()
    for state in runtime.get("samples", []):
        obj = [r for r in state.get("static_source_meshes", []) if r.get("asset_id") == "source:object:modular-equipment-case-001"]
        if len(obj) != 1:
            raise AssertionError("current-world Object source missing or duplicated")
        row = obj[0]
        if row.get("source_sha256") != EXPECTED_OBJECT_SHA or int(row.get("vertices", -1)) != 468 or int(row.get("triangles", -1)) != 812 or int(row.get("surface_count", -1)) != 7:
            raise AssertionError("current-world Object identity drift")
        motion = row.get("environment_object_motion_receiver", {})
        if motion.get("state") != "PASS_CURRENT_WORLD_OBJECT_ANIMATION_OWNER_SAMPLE_RECEIVER__VFX_RUNTIME_ENV_ADOPTION_HELD":
            raise AssertionError("current-world Object motion receiver state drift")
        if motion.get("environment_adoption") is not False or motion.get("runtime_acceptance") is not False or motion.get("vfx_adoption") is not False:
            raise AssertionError("current-world Object motion authority inflation")
        found.add(int(motion.get("selected_sample", {}).get("index", -1)))
    if len(found) != 1:
        raise AssertionError(f"selected motion sample inconsistent across world states: {sorted(found)}")
    return next(iter(found))


def validate_runtime_pair(sample: int, predecessor: dict[str, Any], successor: dict[str, Any]) -> dict[str, Any]:
    if len(predecessor.get("samples", [])) != EXPECTED_STATE_COUNT or len(successor.get("samples", [])) != EXPECTED_STATE_COUNT:
        raise AssertionError("exact current-world state count drift")
    if predecessor.get("technical_art_object_motion_animation_head") != EXPECTED_ANIMATION_HEAD or successor.get("technical_art_object_motion_animation_head") != EXPECTED_ANIMATION_HEAD:
        raise AssertionError("Animation owner identity drift")
    if predecessor.get("technical_art_object_motion_sequence_digest") != EXPECTED_SEQUENCE_DIGEST or successor.get("technical_art_object_motion_sequence_digest") != EXPECTED_SEQUENCE_DIGEST:
        raise AssertionError("Animation sequence digest drift")
    if predecessor.get("technical_art_object_motion_environment_adoption") is not False or successor.get("technical_art_object_motion_environment_adoption") is not False:
        raise AssertionError("Technical Art/Environment adoption authority inflated")
    if successor.get("environment_object_articulated_service_clearance_environment_adoption") is not False:
        raise AssertionError("render successor environment adoption must remain false")
    if successor.get("environment_object_articulated_service_clearance_art_qa_acceptance") is not False:
        raise AssertionError("render successor Art/QA authority inflated")
    if successor.get("environment_object_articulated_service_clearance_runtime_acceptance") is not False:
        raise AssertionError("render successor Runtime authority inflated")
    if not same_float_list(successor.get("environment_object_articulated_service_clearance_predecessor_outer_footprint_world_xy_m"), OLD):
        raise AssertionError("successor receipt predecessor footprint drift")
    if not same_float_list(successor.get("environment_object_articulated_service_clearance_successor_outer_footprint_world_xy_m"), NEW):
        raise AssertionError("successor receipt footprint drift")

    for key in IDENTITY_KEYS:
        if predecessor.get(key) != successor.get(key):
            raise AssertionError(f"unrelated current-world identity drift at top-level key {key}")

    p_index = selected_motion_index(predecessor)
    s_index = selected_motion_index(successor)
    if p_index != sample or s_index != sample:
        raise AssertionError(f"rendered sample identity drift: expected {sample}, got predecessor={p_index} successor={s_index}")

    projected: dict[str, dict[str, list[int]]] = {}
    for state_idx, (ps, ss) in enumerate(zip(predecessor["samples"], successor["samples"])):
        if ps.get("index") != ss.get("index") or ps.get("time_s") != ss.get("time_s"):
            raise AssertionError(f"world state identity drift at state {state_idx}")
        if ps.get("weather_field_digest") != ss.get("weather_field_digest") or ps.get("weather_width_profile_digest") != ss.get("weather_width_profile_digest"):
            raise AssertionError(f"Weather state identity drift at state {state_idx}")
        if ps.get("sapling_mesh_digest") != ss.get("sapling_mesh_digest"):
            raise AssertionError(f"Nature mesh digest drift at state {state_idx}")
        if semantic_runtime_value(ps.get("sapling_update")) != semantic_runtime_value(ss.get("sapling_update")):
            raise AssertionError(f"Nature authored/runtime state drift at state {state_idx}")

        prows = ps.get("static_source_meshes", [])
        srows = ss.get("static_source_meshes", [])
        validate_frame(frame_row(prows), OLD, False)
        validate_frame(frame_row(srows), NEW, True)
        if other_rows(prows) != other_rows(srows):
            raise AssertionError(f"non-Environment static source changed at state {state_idx}")

        pctx = ps.get("contexts", {})
        sctx = ss.get("contexts", {})
        if set(pctx) != set(sctx) or set(pctx) != {"path_eye", "elevated_oblique"}:
            raise AssertionError(f"camera context identity drift at state {state_idx}")
        for context in sorted(pctx):
            for mode in ("control", "candidate"):
                if mode not in pctx[context] or mode not in sctx[context]:
                    raise AssertionError(f"presentation mode drift at state {state_idx} {context}")
                pa = pctx[context][mode]
                sa = sctx[context][mode]
                if pa.get("runtime") != sa.get("runtime"):
                    raise AssertionError(f"runtime counter drift at state {state_idx} {context} {mode}")
                if semantic_runtime_value(pa.get("weather_update")) != semantic_runtime_value(sa.get("weather_update")):
                    raise AssertionError(f"Weather authored/runtime observation drift at state {state_idx} {context} {mode}")
                pc = pa.get("capture", {})
                sc = sa.get("capture", {})
                for key in ("state", "width", "height", "dressing_asset_id", "path"):
                    if pc.get(key) != sc.get(key):
                        raise AssertionError(f"capture identity drift at state {state_idx} {context} {mode} key {key}")
                if pc.get("state") != "PASS" or int(pc.get("width", -1)) != 1100 or int(pc.get("height", -1)) != 720:
                    raise AssertionError("capture surface drift")
                pb = [int(x) for x in pc.get("dressing_projected_bbox_px", [])]
                sb = [int(x) for x in sc.get("dressing_projected_bbox_px", [])]
                if len(pb) != 4 or len(sb) != 4:
                    raise AssertionError("projected dressing bbox missing")
                projected[f"{context}:{mode}:{state_idx:02d}"] = {"predecessor": pb, "successor": sb}

    if predecessor.get("static_source_meshes") and successor.get("static_source_meshes"):
        validate_frame(frame_row(predecessor["static_source_meshes"]), OLD, False)
        validate_frame(frame_row(successor["static_source_meshes"]), NEW, True)
        if other_rows(predecessor["static_source_meshes"]) != other_rows(successor["static_source_meshes"]):
            raise AssertionError("top-level non-Environment static source changed")

    return {"selected_sample_index": sample, "projected_bboxes": projected}


def expanded_union_bbox(a: list[int], b: list[int], pad: int) -> tuple[int, int, int, int]:
    return (
        max(0, min(a[0], b[0]) - pad),
        max(0, min(a[1], b[1]) - pad),
        min(1099, max(a[2], b[2]) + pad),
        min(719, max(a[3], b[3]) + pad),
    )


def compare_frames(pre_dir: Path, succ_dir: Path, projected: dict[str, dict[str, list[int]]]) -> dict[str, Any]:
    pred = sorted(p.name for p in pre_dir.glob("atmosphere-width-*.png"))
    succ = sorted(p.name for p in succ_dir.glob("atmosphere-width-*.png"))
    if pred != succ or len(pred) != EXPECTED_FRAME_COUNT:
        raise AssertionError(f"rendered frame-set identity drift: predecessor={len(pred)} successor={len(succ)}")

    total_raw = 0
    total_gt1 = 0
    max_lsb = 0
    changed_files = 0
    global_bbox: list[int] | None = None
    per_context: dict[str, dict[str, int]] = {}

    for name in pred:
        stem = name.removeprefix("atmosphere-width-").removesuffix(".png")
        mode, rest = stem.split("-", 1)
        context, state_token = rest.rsplit("-", 1)
        state_idx = int(state_token)
        key = f"{context}:{mode}:{state_idx:02d}"
        if key not in projected:
            raise AssertionError(f"projected bbox missing for {name}")
        p = np.asarray(Image.open(pre_dir / name).convert("RGBA"), dtype=np.int16)
        s = np.asarray(Image.open(succ_dir / name).convert("RGBA"), dtype=np.int16)
        if p.shape != s.shape or p.shape[:2] != (720, 1100):
            raise AssertionError(f"frame shape drift for {name}: {p.shape} {s.shape}")
        delta = np.abs(s[:, :, :3] - p[:, :, :3])
        raw = np.any(delta > 0, axis=2)
        gt1 = np.any(delta > 1, axis=2)
        raw_count = int(raw.sum())
        gt1_count = int(gt1.sum())
        local_max = int(delta.max())
        total_raw += raw_count
        total_gt1 += gt1_count
        max_lsb = max(max_lsb, local_max)
        bucket = per_context.setdefault(context, {"raw_changed_pixels": 0, "pixels_gt_1_lsb": 0, "changed_frames": 0})
        bucket["raw_changed_pixels"] += raw_count
        bucket["pixels_gt_1_lsb"] += gt1_count
        if raw_count:
            changed_files += 1
            bucket["changed_frames"] += 1
            ys, xs = np.nonzero(raw)
            bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            allowed = expanded_union_bbox(projected[key]["predecessor"], projected[key]["successor"], PIXEL_LOCALITY_PAD)
            if bbox[0] < allowed[0] or bbox[1] < allowed[1] or bbox[2] > allowed[2] or bbox[3] > allowed[3]:
                raise AssertionError(f"visual delta escaped dressing projection for {name}: delta={bbox} allowed={list(allowed)}")
            if global_bbox is None:
                global_bbox = bbox
            else:
                global_bbox = [min(global_bbox[0], bbox[0]), min(global_bbox[1], bbox[1]), max(global_bbox[2], bbox[2]), max(global_bbox[3], bbox[3])]

    return {
        "frame_count": len(pred),
        "changed_frames": changed_files,
        "raw_changed_pixels": total_raw,
        "pixels_gt_1_lsb": total_gt1,
        "maximum_rgb_channel_delta_lsb": max_lsb,
        "global_changed_bbox_px": global_bbox,
        "locality_padding_px": PIXEL_LOCALITY_PAD,
        "per_context": per_context,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", required=True)
    ap.add_argument("--spatial-report", required=True)
    for sample in EXPECTED_SAMPLES:
        ap.add_argument(f"--predecessor-runtime-{sample}", required=True)
        ap.add_argument(f"--successor-runtime-{sample}", required=True)
        ap.add_argument(f"--predecessor-rendered-{sample}", required=True)
        ap.add_argument(f"--successor-rendered-{sample}", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    contract = load_json(Path(args.contract))
    if contract.get("schema") != "axm.environment-object-articulated-service-clearance/v0.1":
        raise AssertionError("service-clearance contract schema drift")
    if contract.get("technical_art_parent_head") != EXPECTED_TA_HEAD:
        raise AssertionError("Technical Art parent identity drift")
    if contract.get("animation_head") != EXPECTED_ANIMATION_HEAD or contract.get("sequence_digest") != EXPECTED_SEQUENCE_DIGEST:
        raise AssertionError("Animation contract identity drift")
    if contract.get("candidate", {}).get("environment_adoption") is not False:
        raise AssertionError("contract Environment adoption authority inflated")
    if abs(float(contract.get("candidate", {}).get("rear_outer_edge_expansion_m", -1.0)) - 0.02) > 1e-9:
        raise AssertionError("contract rear-edge successor drift")
    if not same_float_list(contract.get("service_frame", {}).get("predecessor_outer_footprint_world_xy_m"), OLD):
        raise AssertionError("contract predecessor footprint drift")

    spatial = load_json(Path(args.spatial_report))
    if spatial.get("result") != EXPECTED_SPATIAL_RESULT:
        raise AssertionError("exact spatial predecessor evidence not green")
    if spatial.get("technical_art_parent_head") != EXPECTED_TA_HEAD:
        raise AssertionError("spatial evidence Technical Art parent drift")
    sweep = spatial.get("articulated_sweep", {})
    if float(sweep.get("predecessor_minimum_inner_clearance_m", 1.0)) >= 0.06:
        raise AssertionError("spatial predecessor regression is not reproduced")
    if float(sweep.get("candidate_minimum_inner_clearance_m", 0.0)) < 0.06:
        raise AssertionError("spatial successor no longer restores 60 mm clearance")
    if int(sweep.get("candidate_minimum_witness", {}).get("sample_index", -1)) != 40:
        raise AssertionError("spatial worst-case witness drift")
    if spatial.get("decision", {}).get("environment_adoption") is not False:
        raise AssertionError("spatial evidence Environment adoption authority inflated")

    samples_report: dict[str, Any] = {}
    total_raw = 0
    total_gt1 = 0
    max_lsb = 0
    changed_frames = 0
    for sample in EXPECTED_SAMPLES:
        predecessor = load_json(Path(getattr(args, f"predecessor_runtime_{sample}")))
        successor = load_json(Path(getattr(args, f"successor_runtime_{sample}")))
        structural = validate_runtime_pair(sample, predecessor, successor)
        visual = compare_frames(
            Path(getattr(args, f"predecessor_rendered_{sample}")),
            Path(getattr(args, f"successor_rendered_{sample}")),
            structural["projected_bboxes"],
        )
        samples_report[str(sample)] = {
            "owner_time_s": 0.0 if sample == 0 else 1.0,
            "structural": {"selected_sample_index": sample},
            "visual": visual,
        }
        total_raw += visual["raw_changed_pixels"]
        total_gt1 += visual["pixels_gt_1_lsb"]
        max_lsb = max(max_lsb, visual["maximum_rgb_channel_delta_lsb"])
        changed_frames += visual["changed_frames"]

    visible = total_raw > 0
    result = VISIBLE_RESULT if visible else ZERO_RESULT
    report = {
        "schema": SCHEMA,
        "result": result,
        "reusable_rule": RULE,
        "technical_art_parent_head": EXPECTED_TA_HEAD,
        "animation_head": EXPECTED_ANIMATION_HEAD,
        "sequence_digest": EXPECTED_SEQUENCE_DIGEST,
        "spatial_predecessor_result": EXPECTED_SPATIAL_RESULT,
        "spatial_predecessor_minimum_inner_clearance_m": sweep["predecessor_minimum_inner_clearance_m"],
        "spatial_successor_minimum_inner_clearance_m": sweep["candidate_minimum_inner_clearance_m"],
        "rendered_owner_samples": EXPECTED_SAMPLES,
        "frames_per_owner_sample_per_variant": EXPECTED_FRAME_COUNT,
        "visual_observability": "LOCALIZED_DELTA_OBSERVED" if visible else "ZERO_RASTER_DELTA_IN_EXISTING_CAMERAS",
        "aggregate_visual_delta": {
            "raw_changed_pixels": total_raw,
            "pixels_gt_1_lsb": total_gt1,
            "maximum_rgb_channel_delta_lsb": max_lsb,
            "changed_frames": changed_frames,
        },
        "samples": samples_report,
        "semantic_identity_note": "Only process-local Godot node/mesh/material instance handles are excluded from cross-process equality. All authored/source/runtime content remains strict.",
        "authority": {
            "environment_adoption": False,
            "art_qa_acceptance": False,
            "runtime_acceptance": False,
            "gameplay_collision_navigation_acceptance": False,
            "canon": False,
        },
        "truth_boundary": (
            "This review renders the exact spatially proven +20 mm rear-only Environment service-frame successor against the exact historical predecessor at neutral owner sample 0 and the exact worst-case opened-lid plateau sample 40. "
            "Building, Nature, Object source/material/roughness/motion, Weather, cameras, lighting and proof-host runtime counters must remain identical; only process-local Godot instance handles may differ between separate processes and only the Environment-owned dressing footprint may differ semantically. Pixel deltas are characterized and must remain inside the projected dressing envelope, but no minimum aesthetic delta is invented. "
            "The result is review-ready evidence only and does not grant Environment adoption, Art/QA acceptance, Runtime/device acceptance, gameplay/collision/navigation authority, CANON or production readiness."
        ),
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result)
    print(json.dumps(report["aggregate_visual_delta"], sort_keys=True))


if __name__ == "__main__":
    main()
