#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

WORLD_HEAD = "6575cc38db9f0f62b14a82b352d8582edf89856d"
FOOTPRINT_REVIEW_HEAD = "2755dd3b275de9e62c933bd5d0653ddf9aa6fbcd"
RUNTIME_DONOR_HEAD = "ddd9e8b783b213c6e44bf5eea482de1d41918766"
OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
DRESSING_ASSET_ID = "environment:dressing:west-object-service-footprint-frame-001"
OBJECT_SOURCE_HEAD = "d3fa10a270faae7925811f44f03381fe5c5d0215"
OBJECT_MATERIALS_HEAD = "c85517446a769e0d5f880fc0e9e32f47124f7b5e"
OBJECT_PROFILE_SHA256 = "dc200229d6c25fa84063aa51f66103abc022efa54b2167e4432a5b47fc40360c"
EXPECTED_MATERIALS = ["shell_coating", "service_dark", "hardware_steel", "rubber_guard", "interface_orange"]
RUNTIME_KEYS = ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "buffer_mem_bytes", "texture_mem_bytes")
CAMERAS = ("path_eye", "elevated_oblique")
WEATHER_MODES = ("control", "candidate")
WEATHER_RESOURCE_ID_KEYS = ("node_instance_id", "mesh_instance_id", "material_instance_id")


class VerificationFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationFailure(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def png_map(root: Path) -> dict[str, str]:
    files = sorted(root.glob("atmosphere-width-*.png"))
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def runtime_signature(row: dict[str, Any]) -> dict[str, int]:
    return {key: int(row[key]) for key in RUNTIME_KEYS}


def weather_semantics(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in WEATHER_RESOURCE_ID_KEYS}


def weather_resource_identity(row: dict[str, Any]) -> tuple[int, int, int]:
    return tuple(int(row[key]) for key in WEATHER_RESOURCE_ID_KEYS)


def object_diag(receipt: dict[str, Any]) -> dict[str, Any]:
    rows = receipt.get("static_source_meshes", [])
    matches = [row for row in rows if row.get("asset_id") == OBJECT_ASSET_ID]
    require(len(matches) == 1, f"expected one Object source row, found {len(matches)}")
    diag = matches[0].get("environment_object_surface_indexing")
    require(isinstance(diag, dict), "indexed Object receiving diagnostic missing")
    return diag


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--environment-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reference = load(args.reference_root / "runtime.json")
    candidate = load(args.candidate_root / "runtime.json")

    require(reference.get("state") == "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION", "reference live observation not PASS")
    require(candidate.get("state") == "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION", "candidate live observation not PASS")
    require(reference.get("receiving_head") == candidate.get("receiving_head") == WORLD_HEAD, "underlying current-world authority drift")
    require(reference.get("environment_object_footprint_review_mode") == "CANDIDATE_VISIBLE", "reference is not exact visible-cue world")
    require(candidate.get("environment_object_footprint_review_mode") == "CANDIDATE_VISIBLE", "candidate visible-cue context drift")
    require(candidate.get("environment_object_indexed_receiver_runtime_donor_head") == RUNTIME_DONOR_HEAD, "Runtime donor head drift")
    require(candidate.get("environment_object_indexed_receiver_runtime_donor_pr") == 33, "Runtime donor PR drift")
    require(reference.get("environment_object_readability_dressing_asset_id") == candidate.get("environment_object_readability_dressing_asset_id") == DRESSING_ASSET_ID, "footprint cue identity drift")
    require(reference.get("environment_object_material_source_head") == candidate.get("environment_object_material_source_head") == OBJECT_SOURCE_HEAD, "Object source head drift")
    require(reference.get("environment_object_materials_head") == candidate.get("environment_object_materials_head") == OBJECT_MATERIALS_HEAD, "Object Materials head drift")
    require(reference.get("environment_object_material_profile_sha256") == candidate.get("environment_object_material_profile_sha256") == OBJECT_PROFILE_SHA256, "Object material profile drift")

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
        require(reference.get(key) == candidate.get(key), f"world identity drift at {key}")

    diag = object_diag(candidate)
    require(diag.get("schema") == "axm.environment-current-world-object-indexed-surface-receiving/v0.1", "indexed receiving schema drift")
    require(diag.get("runtime_donor_head") == RUNTIME_DONOR_HEAD, "indexed diagnostic donor drift")
    require(diag.get("source_object_head") == OBJECT_SOURCE_HEAD, "indexed diagnostic Object source drift")
    require(diag.get("materials_head") == OBJECT_MATERIALS_HEAD, "indexed diagnostic Materials head drift")
    require(diag.get("material_ids") == EXPECTED_MATERIALS, "material surface identity/order drift")

    before = diag["before"]
    after = diag["after"]
    require(int(before["surface_count"]) == int(after["surface_count"]) == 5, "five-surface boundary changed")
    require(int(before["total_vertices"]) == 2436 and int(before["total_indices"]) == 0, "pre-index representation drift")
    require(int(before["total_primitives"]) == 812, "pre-index triangle count drift")
    require(int(after["total_vertices"]) == 468 and int(after["total_indices"]) == 2436, "indexed representation does not match proven Runtime donor shape")
    require(int(after["total_primitives"]) == 812, "indexed triangle count drift")
    require(all(int(surface["index_count"]) > 0 for surface in after["surfaces"]), "an indexed Object surface has no index stream")

    reference_pngs = png_map(args.reference_root / "rendered")
    candidate_pngs = png_map(args.candidate_root / "rendered")
    require(len(reference_pngs) == len(candidate_pngs) == 68, f"expected 68 exact frames, got {len(reference_pngs)} / {len(candidate_pngs)}")
    require(set(reference_pngs) == set(candidate_pngs), "frame identity set drift")
    mismatches = [name for name, digest in reference_pngs.items() if candidate_pngs[name] != digest]
    require(not mismatches, f"indexed current-world receiver changed retained pixels: {mismatches[:5]}")

    rsamples = reference.get("samples", [])
    csamples = candidate.get("samples", [])
    require(len(rsamples) == len(csamples) == 17, "expected exact 17-state world sequence")

    runtime_deltas: dict[str, set[tuple[tuple[str, int], ...]]] = {camera: set() for camera in CAMERAS}
    reference_weather_resources: set[tuple[int, int, int]] = set()
    candidate_weather_resources: set[tuple[int, int, int]] = set()
    width_count = 0
    max_width_residual = 0.0
    projected_cue_bboxes_equal = 0

    for index, (rs, cs) in enumerate(zip(rsamples, csamples)):
        for key in ("index", "time_s", "weather_field_digest", "sapling_mesh_digest", "weather_width_profile_digest"):
            require(rs.get(key) == cs.get(key), f"state {index}: dynamic identity drift at {key}")
        for camera in CAMERAS:
            for weather_mode in WEATHER_MODES:
                rctx = rs["contexts"][camera][weather_mode]
                cctx = cs["contexts"][camera][weather_mode]
                rweather = rctx["weather_update"]
                cweather = cctx["weather_update"]
                reference_weather_resources.add(weather_resource_identity(rweather))
                candidate_weather_resources.add(weather_resource_identity(cweather))
                require(weather_semantics(rweather) == weather_semantics(cweather), f"{index}/{camera}/{weather_mode}: Weather semantic observation drift")
                require(rctx["capture"].get("dressing_projected_bbox_px") == cctx["capture"].get("dressing_projected_bbox_px"), f"{index}/{camera}/{weather_mode}: cue projection drift")
                projected_cue_bboxes_equal += 1
                if weather_mode == "candidate":
                    width_count += int(cweather.get("measured_width_count", 0))
                    max_width_residual = max(max_width_residual, float(cweather.get("maximum_projected_width_residual_px", 0.0)))
                rrun = runtime_signature(rctx["runtime"])
                crun = runtime_signature(cctx["runtime"])
                delta = {key: crun[key] - rrun[key] for key in RUNTIME_KEYS}
                runtime_deltas[camera].add(tuple(sorted(delta.items())))

    require(len(reference_weather_resources) == 1, "reference Weather resource identity is not stable in-process")
    require(len(candidate_weather_resources) == 1, "candidate Weather resource identity is not stable in-process")
    require(projected_cue_bboxes_equal == 68, "not all cue projections remained identical")
    require(width_count == 1224, f"Weather width measurement count drift: {width_count}")
    require(max_width_residual <= 0.05, f"Weather width residual exceeded inherited gate: {max_width_residual}")

    normalized_runtime: dict[str, list[dict[str, int]]] = {}
    for camera, values in runtime_deltas.items():
        normalized_runtime[camera] = [dict(items) for items in sorted(values)]
        require(len(values) == 1, f"{camera}: runtime delta not stable")
        only = dict(next(iter(values)))
        require(only["draw_calls_in_frame"] == 0, f"{camera}: draw-call drift")
        require(only["objects_in_frame"] == 0, f"{camera}: object-count drift")
        require(only["primitives_in_frame"] == 0, f"{camera}: primitive drift")
        require(only["texture_mem_bytes"] == 0, f"{camera}: texture-memory drift")
        require(only["buffer_mem_bytes"] == -34488, f"{camera}: expected exact proven -34488 B buffer delta, got {only['buffer_mem_bytes']}")

    result = {
        "schema": "axm.environment-current-world-indexed-object-footprint-composition/v0.1",
        "state": "PASS_CURRENT_WORLD_INDEXED_OBJECT_WITH_FOOTPRINT_COMPOSITION",
        "environment_head": args.environment_head,
        "underlying_world_head": WORLD_HEAD,
        "reference_footprint_review_head": FOOTPRINT_REVIEW_HEAD,
        "runtime_donor_pr": 33,
        "runtime_donor_head": RUNTIME_DONOR_HEAD,
        "object_source_head": OBJECT_SOURCE_HEAD,
        "object_materials_head": OBJECT_MATERIALS_HEAD,
        "object_material_profile_sha256": OBJECT_PROFILE_SHA256,
        "footprint_asset_id": DRESSING_ASSET_ID,
        "checks": {
            "exact_visible_footprint_reference_preserved": True,
            "five_object_material_surfaces_preserved": True,
            "object_triangles_preserved": True,
            "indexed_object_representation_matches_runtime_donor": True,
            "all_68_frames_byte_identical": True,
            "all_68_cue_projections_identical": True,
            "all_1224_weather_width_observations_preserved": True,
            "weather_resource_identity_stable_within_each_process": True,
            "building_nature_weather_route_camera_lighting_identities_preserved": True,
            "draw_object_primitive_texture_counters_unchanged": True,
            "observed_buffer_delta_matches_runtime_donor": True,
        },
        "before_object_mesh": before,
        "after_object_mesh": after,
        "matched_frames": 68,
        "byte_identical_frames": 68,
        "weather_width_measurements": width_count,
        "maximum_projected_weather_width_residual_px": max_width_residual,
        "runtime_deltas": normalized_runtime,
        "visual_tradeoff": "NONE_OBSERVED__68_CURRENT_WORLD_FRAMES_BYTE_IDENTICAL_TO_EXACT_VISIBLE_CUE_REFERENCE",
        "decision": "ADOPTION_READY_FOR_RECEIVER_REPRESENTATION__FOOTPRINT_VISUAL_QA_AND_TARGET_DEVICE_PERF_REMAIN_SEPARATE",
        "truth_boundary": "This PASS proves only that the exact Runtime PR #33 post-normal indexing mechanism can be received in the current Environment world while preserving the exact Art-preferred visible footprint-cue frames, five Object material roles, 812 Object triangles, Building/Nature/Weather identities and Weather-width evidence. Cross-process Godot instance IDs are process-local and are not treated as semantic identity; each receipt must still prove one stable Weather node/mesh/material identity within its own process. It does not grant independent Visual-QA acceptance of the footprint cue, target-device performance acceptance, arbitrary-asset indexing safety, Object scale acceptance, gameplay meaning, CANON or production readiness.",
        "non_claims": [
            "independent Visual QA acceptance of the footprint cue",
            "target-device CPU/GPU/FPS/VRAM or heap performance",
            "draw-call reduction",
            "arbitrary-asset indexing safety",
            "Object source scale/transform/mechanics changes",
            "physical service-pad semantics",
            "collision/navigation/gameplay",
            "CANON or production readiness",
            "Environment mastery",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
