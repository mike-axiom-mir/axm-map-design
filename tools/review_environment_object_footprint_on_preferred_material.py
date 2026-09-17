#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

WORLD_HEAD = "6575cc38db9f0f62b14a82b352d8582edf89856d"
WORLD_DIGEST = "677dfe17afe49bf3f6edc28359c40a8add3dc357cb918529f0015a99f71baf70"
OBJECT_SOURCE_HEAD = "d3fa10a270faae7925811f44f03381fe5c5d0215"
OBJECT_SOURCE_SHA256 = "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
OBJECT_MATERIALS_HEAD = "c85517446a769e0d5f880fc0e9e32f47124f7b5e"
OBJECT_PROFILE_SHA256 = "dc200229d6c25fa84063aa51f66103abc022efa54b2167e4432a5b47fc40360c"
DRESSING_ASSET_ID = "environment:dressing:west-object-service-footprint-frame-001"
CONTROL_MODE = "CONTROL_HIDDEN"
CANDIDATE_MODE = "CANDIDATE_VISIBLE"
CAMERAS = ("path_eye", "elevated_oblique")
WEATHER_MODES = ("control", "candidate")
EXPECTED_FRAME_COUNT = 17 * 2 * 2
EXPECTED_WIDTH_COUNT = 17 * 2 * 36
MAX_WIDTH_RESIDUAL_PX = 0.05
PIXEL_THRESHOLD = 1
BBOX_MARGIN = 2


class ReviewFailure(RuntimeError):
    pass


def load_json(path: Path):
    return json.loads(path.read_text())


def require(condition: bool, message: str):
    if not condition:
        raise ReviewFailure(message)


def image_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def frame_name(weather_mode: str, camera: str, index: int) -> str:
    return f"atmosphere-width-{weather_mode}-{camera}-{index:02d}.png"


def runtime_signature(row: dict) -> dict:
    keys = ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "buffer_mem_bytes", "texture_mem_bytes")
    return {k: int(row[k]) for k in keys}


def runtime_delta(candidate: dict, control: dict) -> dict:
    a = runtime_signature(candidate)
    b = runtime_signature(control)
    return {k: a[k] - b[k] for k in a}


def bbox_contains(mask_y: np.ndarray, mask_x: np.ndarray, bbox: list, margin: int = BBOX_MARGIN) -> bool:
    if mask_x.size == 0:
        return False
    x0, y0, x1, y1 = [int(v) for v in bbox]
    return (
        int(mask_x.min()) >= x0 - margin
        and int(mask_x.max()) <= x1 + margin
        and int(mask_y.min()) >= y0 - margin
        and int(mask_y.max()) <= y1 + margin
    )


def verify_receipt(receipt: dict, mode: str):
    require(receipt.get("state") == "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION", f"{mode}: runtime state drift")
    require(receipt.get("receiving_head") == WORLD_HEAD, f"{mode}: world head drift")
    require(receipt.get("environment_object_footprint_review_world_head") == WORLD_HEAD, f"{mode}: review world head drift")
    require(receipt.get("environment_object_footprint_review_world_digest") == WORLD_DIGEST, f"{mode}: review world digest drift")
    require(receipt.get("environment_object_footprint_review_mode") == mode, f"{mode}: explicit visibility mode missing")
    require(receipt.get("environment_object_material_source_head") == OBJECT_SOURCE_HEAD, f"{mode}: Object source head drift")
    require(receipt.get("environment_object_material_source_sha256") == OBJECT_SOURCE_SHA256, f"{mode}: Object source digest drift")
    require(receipt.get("environment_object_materials_head") == OBJECT_MATERIALS_HEAD, f"{mode}: Object materials head drift")
    require(receipt.get("environment_object_material_profile_sha256") == OBJECT_PROFILE_SHA256, f"{mode}: Object material profile drift")
    require(receipt.get("environment_object_readability_dressing_asset_id") == DRESSING_ASSET_ID, f"{mode}: dressing identity drift")
    require(len(receipt.get("samples", [])) == 17, f"{mode}: expected 17 runtime samples")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--current-root", type=Path, required=True)
    ap.add_argument("--control-root", type=Path, required=True)
    ap.add_argument("--candidate-root", type=Path, required=True)
    ap.add_argument("--review-head", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    payload = load_json(args.current_root / "combined_current_world.json")
    reference_runtime = load_json(args.current_root / "runtime.json")
    reference_target = load_json(args.current_root / "target_host.json")
    control = load_json(args.control_root / "runtime.json")
    candidate = load_json(args.candidate_root / "runtime.json")

    require(payload.get("schema") == "axm.environment-current-world-object-material-family-composition/v0.1", "current-world schema drift")
    require(payload.get("status") == "PASS_CURRENT_WORLD_OBJECT_MATERIAL_FAMILY_STRUCTURE", "current-world structure state drift")
    require(payload.get("receiving_head") == WORLD_HEAD, "current-world head drift")
    require(payload.get("composition_digest") == WORLD_DIGEST, "current-world digest drift")
    require(payload.get("object_source_head") == OBJECT_SOURCE_HEAD and payload.get("object_source_sha256") == OBJECT_SOURCE_SHA256, "current Object source drift")
    require(payload.get("object_materials_head") == OBJECT_MATERIALS_HEAD and payload.get("object_material_profile_sha256") == OBJECT_PROFILE_SHA256, "current Object material authority drift")
    require(reference_target.get("state") == "PASS_CURRENT_WORLD_OBJECT_MATERIAL_FAMILY_TARGET_HOST", "current Object-material target-host PASS missing")
    require(reference_runtime.get("receiving_head") == WORLD_HEAD, "reference runtime world drift")

    verify_receipt(control, CONTROL_MODE)
    verify_receipt(candidate, CANDIDATE_MODE)

    identity_keys = (
        "weather_variant_head",
        "weather_variant_layout_digest",
        "weather_variant_seed",
        "source_width_profile_digest",
        "environment_building_header_segmentation_source_head",
        "environment_building_header_segmentation_material_head",
        "environment_building_header_segmentation_revision",
        "environment_nature_material_family_id",
        "environment_nature_materials_head",
        "environment_nature_geometry_reference_head",
        "environment_object_materials_head",
        "environment_object_material_profile_sha256",
        "environment_object_material_source_head",
        "environment_object_material_source_sha256",
        "environment_object_readability_dressing_asset_id",
    )
    for key in identity_keys:
        require(control.get(key) == candidate.get(key) == reference_runtime.get(key), f"runtime identity drift at {key}")

    changed_counts = {c: [] for c in CAMERAS}
    changed_bboxes = {c: [] for c in CAMERAS}
    exact_candidate_reference_pairs = 0
    localized_pairs = 0
    runtime_deltas = {c: {m: [] for m in WEATHER_MODES} for c in CAMERAS}
    width_count = 0
    max_width_residual = 0.0

    c_samples = control["samples"]
    v_samples = candidate["samples"]
    r_samples = reference_runtime["samples"]
    for index in range(17):
        cs, vs, rs = c_samples[index], v_samples[index], r_samples[index]
        for key in ("index", "time_s", "weather_field_digest", "sapling_mesh_digest", "weather_width_profile_digest"):
            require(cs.get(key) == vs.get(key) == rs.get(key), f"sample {index}: dynamic identity drift at {key}")

        for camera in CAMERAS:
            for weather_mode in WEATHER_MODES:
                cc = cs["contexts"][camera][weather_mode]
                vc = vs["contexts"][camera][weather_mode]
                rc = rs["contexts"][camera][weather_mode]
                for key in ("state", "streak_count", "surface_count", "source_opacity_consumed"):
                    require(cc["weather_update"].get(key) == vc["weather_update"].get(key) == rc["weather_update"].get(key), f"{index}/{camera}/{weather_mode}: Weather presentation drift at {key}")
                if weather_mode == "candidate":
                    width_count += int(vc["weather_update"].get("measured_width_count", 0))
                    max_width_residual = max(max_width_residual, float(vc["weather_update"].get("maximum_projected_width_residual_px", 0.0)))

                bbox = vc["capture"].get("dressing_projected_bbox_px")
                require(isinstance(bbox, list) and len(bbox) == 4, f"{index}/{camera}/{weather_mode}: candidate dressing bbox missing")
                require(bbox == cc["capture"].get("dressing_projected_bbox_px"), f"{index}/{camera}/{weather_mode}: projected dressing bbox changed between visibility modes")

                name = frame_name(weather_mode, camera, index)
                cpath = args.control_root / "rendered" / name
                vpath = args.candidate_root / "rendered" / name
                rpath = args.current_root / "rendered" / name
                require(cpath.is_file() and vpath.is_file() and rpath.is_file(), f"missing frame {name}")
                ci = image_rgb(cpath)
                vi = image_rgb(vpath)
                ri = image_rgb(rpath)
                require(ci.shape == vi.shape == ri.shape == (720, 1100, 3), f"{name}: frame shape drift")

                require(np.array_equal(vi, ri), f"{name}: candidate-visible review does not reproduce exact retained current world")
                exact_candidate_reference_pairs += 1

                diff = np.max(np.abs(vi - ci), axis=2)
                ys, xs = np.where(diff > PIXEL_THRESHOLD)
                require(xs.size > 0, f"{name}: footprint visibility produced no measurable pixel delta")
                require(bbox_contains(ys, xs, bbox), f"{name}: footprint visibility delta escaped projected dressing bounds")
                localized_pairs += 1
                changed_counts[camera].append(int(xs.size))
                changed_bboxes[camera].append([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())])

                runtime_deltas[camera][weather_mode].append(runtime_delta(vc["runtime"], cc["runtime"]))

    require(exact_candidate_reference_pairs == EXPECTED_FRAME_COUNT, "not all candidate frames reproduced the exact current-world artifact")
    require(localized_pairs == EXPECTED_FRAME_COUNT, "not all footprint A/B deltas stayed localized")
    require(width_count == EXPECTED_WIDTH_COUNT, f"expected {EXPECTED_WIDTH_COUNT} source-width measurements, got {width_count}")
    require(max_width_residual <= MAX_WIDTH_RESIDUAL_PX, f"source-width residual {max_width_residual} exceeds {MAX_WIDTH_RESIDUAL_PX}")

    unique_counts = {camera: sorted(set(values)) for camera, values in changed_counts.items()}
    require(unique_counts["path_eye"] == [161], f"path_eye footprint delta changed: {unique_counts['path_eye']}")
    require(unique_counts["elevated_oblique"] == [106], f"elevated footprint delta changed: {unique_counts['elevated_oblique']}")

    unique_runtime = {}
    for camera in CAMERAS:
        unique_runtime[camera] = {}
        for weather_mode in WEATHER_MODES:
            normalized = sorted({tuple(sorted(d.items())) for d in runtime_deltas[camera][weather_mode]})
            unique_runtime[camera][weather_mode] = [dict(items) for items in normalized]

    result = {
        "schema": "axm.environment-current-world-object-footprint-on-preferred-material-review/v0.1",
        "state": "PASS_CURRENT_WORLD_OBJECT_FOOTPRINT_ON_PREFERRED_MATERIAL_REVIEW_READY",
        "review_head": args.review_head,
        "reviewed_world_head": WORLD_HEAD,
        "reviewed_world_composition_digest": WORLD_DIGEST,
        "checks": {
            "exact_current_world_object_material_target_host_parent": True,
            "same_object_geometry_transform_scale_and_material_family": True,
            "same_building_nature_weather_path_cameras_lighting": True,
            "same_dressing_mesh_present_in_both_review_modes": True,
            "visibility_is_the_only_review_toggle": True,
            "all_68_candidate_frames_exactly_reproduce_retained_current_world": True,
            "all_68_visibility_deltas_localized_to_projected_dressing_bounds": True,
            "historical_footprint_pixel_extent_preserved_on_preferred_object_material": True,
            "all_1224_weather_width_observations_preserved": True,
        },
        "visual_delta": {
            "threshold_rgb_lsb": PIXEL_THRESHOLD,
            "path_eye_changed_pixels_unique": unique_counts["path_eye"],
            "elevated_oblique_changed_pixels_unique": unique_counts["elevated_oblique"],
            "path_eye_bboxes_unique": sorted({tuple(x) for x in changed_bboxes["path_eye"]}),
            "elevated_oblique_bboxes_unique": sorted({tuple(x) for x in changed_bboxes["elevated_oblique"]}),
            "candidate_reference_exact_frame_pairs": exact_candidate_reference_pairs,
            "localized_visibility_pairs": localized_pairs,
        },
        "weather_width": {
            "measurement_count": width_count,
            "maximum_projected_width_residual_px": max_width_residual,
            "gate_px": MAX_WIDTH_RESIDUAL_PX,
        },
        "review_visibility_runtime_deltas": unique_runtime,
        "truth_boundary": "This PASS establishes an attribution-clean visual review surface for the existing Map-owned footprint cue on the exact Art-Direction-preferred five-surface Object material world. It does not grant aesthetic adoption of the cue, solve Object scale semantics, replace prior creation-cost evidence, establish target-device performance, or change Object/Building/Nature/Weather source authority.",
        "non_claims": [
            "final Art Direction or Visual QA preference for the footprint cue",
            "Object rescale or source geometry change",
            "physical service-pad meaning",
            "collision/navigation/gameplay",
            "target-device CPU/GPU/FPS/VRAM/batching acceptance",
            "arbitrary camera/FOV/resolution/renderer equivalence",
            "CANON or production readiness",
            "Environment mastery",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
