from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT_SCHEMA = "axm.environment-object-selected-surface-segmentation-receiver/v0.1"
OBS_SCHEMA = "axm.environment-object-selected-surface-segmentation-observation/v0.1"
PASS_STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACES_INDEPENDENTLY_ADDRESSABLE__UV0_AND_SELECTED_ROUGHNESS_ADOPTION_HELD"
RULE = "EXACT_SOURCE_SURFACE_SEGMENTATION_MAY_PRECEDE_UV_BINDING_ONLY_WHEN_PARENT_MATERIAL_AND_DIRECTION_FIELDS_ARE_PRESERVED_AND_REAL_SCENE_CONTINUITY_IS_RETESTED"
OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
CORRESPONDENCE_HEAD = "be4e0dbf245c4658c48b902024cf397cc6557b5f"
READINESS_HEAD = "1fcc9727012d156f8d1c4658c48b902024cf397cc6557b5f"
CURRENT_MATERIALS_HEAD = "c85517446a769e0d5f880fc0e9e32f47124f7b5e"
CURRENT_PROFILE_SHA = "dc200229d6c25fa84063aa51f66103abc022efa54b2167e4432a5b47fc40360c"
LID = [12, 13]
FRONT = [28, 29]
EXPECTED_SEGMENTS = [
    ("shell_coating_remainder", "shell_coating", 22),
    ("lid_inner_service_surface", "shell_coating", 2),
    ("service_dark_remainder", "service_dark", 10),
    ("front_service_panel_outer_service_surface", "service_dark", 2),
    ("hardware_steel", "hardware_steel", 656),
    ("rubber_guard", "rubber_guard", 96),
    ("interface_orange", "interface_orange", 24),
]


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def find_object(rows: Any) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise ValueError("runtime static_source_meshes missing")
    matches = [row for row in rows if isinstance(row, dict) and row.get("asset_id") == OBJECT_ASSET_ID]
    if len(matches) != 1:
        raise ValueError(f"expected one Object receiver row, got {len(matches)}")
    return matches[0]


def verify_correspondence(report: dict[str, Any]) -> None:
    if report.get("environment_head") != CORRESPONDENCE_HEAD:
        raise ValueError("source-surface correspondence head drift")
    if report.get("source_surface_triangle_indices", {}).get("lid_inner_service_surface") != LID:
        raise ValueError("lid selected source-triangle identity drift")
    if report.get("source_surface_triangle_indices", {}).get("front_service_panel_outer_service_surface") != FRONT:
        raise ValueError("front selected source-triangle identity drift")
    current = report.get("current_world_receiver_correspondence", {})
    if current.get("exact_two_surface_material_segmentation_present") is not False:
        raise ValueError("parent correspondence no longer represents unsplit receiver")
    if current.get("current_service_dark_triangle_count") != 12 or current.get("current_service_dark_selected_target_triangle_count") != 2:
        raise ValueError("parent service_dark correspondence cardinality drift")
    if report.get("environment_adoption") is not False:
        raise ValueError("parent correspondence unexpectedly adopted selected roughness")


def verify_observation(row: dict[str, Any]) -> dict[str, Any]:
    obs = row.get("environment_object_selected_surface_segmentation")
    if not isinstance(obs, dict):
        raise ValueError("Object selected-surface segmentation observation missing")
    if obs.get("schema") != OBS_SCHEMA or obs.get("state") != PASS_STATE:
        raise ValueError("selected-surface segmentation schema/state drift")
    if obs.get("reusable_rule") != RULE:
        raise ValueError("selected-surface segmentation rule drift")
    if obs.get("source_surface_correspondence_head") != CORRESPONDENCE_HEAD:
        raise ValueError("selected-surface correspondence provenance drift")
    if obs.get("current_receiver_materials_head") != CURRENT_MATERIALS_HEAD or obs.get("current_receiver_material_profile_sha256") != CURRENT_PROFILE_SHA:
        raise ValueError("current Object material receiver identity drift")
    if [obs.get("pre_split_surface_count"), obs.get("post_split_surface_count"), obs.get("unique_material_count"), obs.get("total_triangles")] != [5, 7, 5, 812]:
        raise ValueError("selected-surface receiver cardinality drift")
    if obs.get("uv0_total_count") != 0:
        raise ValueError("segmentation receiver unexpectedly gained UV0")
    if obs.get("selected_roughness_adopted") is not False or obs.get("environment_adoption") is not False:
        raise ValueError("selected roughness/adoption must remain held after segmentation-only pass")
    if obs.get("parent_material_objects_reused") is not True or obs.get("parent_vertex_and_normal_fields_reused") is not True:
        raise ValueError("segmentation receiver did not preserve parent material/direction fields")
    segments = obs.get("segments")
    if not isinstance(segments, list) or len(segments) != 7:
        raise ValueError("expected exact seven receiver segments")
    observed = [(x.get("segment_id"), x.get("material_id"), x.get("triangle_count")) for x in segments]
    if observed != EXPECTED_SEGMENTS:
        raise ValueError(f"receiver segment identity/cardinality drift: {observed}")
    selected = obs.get("selected_surface_segments", {})
    lid = selected.get("lid_inner_service_surface", {})
    front = selected.get("front_service_panel_outer_service_surface", {})
    if lid.get("surface_index") != 1 or lid.get("material_id") != "shell_coating" or lid.get("source_triangle_indices") != LID:
        raise ValueError("lid selected receiver segment drift")
    if front.get("surface_index") != 3 or front.get("material_id") != "service_dark" or front.get("source_triangle_indices") != FRONT:
        raise ValueError("front selected receiver segment drift")
    return obs


def compare_frames(parent_root: Path, candidate_root: Path) -> dict[str, Any]:
    parent = {p.name: p for p in parent_root.glob("atmosphere-width-*.png")}
    candidate = {p.name: p for p in candidate_root.glob("atmosphere-width-*.png")}
    if len(parent) != 68 or set(parent) != set(candidate):
        raise ValueError(f"expected exact 68-frame comparison set; parent={len(parent)} candidate={len(candidate)}")
    changed = [name for name in sorted(parent) if sha256(parent[name]) != sha256(candidate[name])]
    if changed:
        raise ValueError(f"segmentation-only receiver changed rendered pixels: {changed[:8]}")
    digest = hashlib.sha256()
    for name in sorted(candidate):
        digest.update(name.encode("utf-8"))
        digest.update(bytes.fromhex(sha256(candidate[name])))
    return {"matched_frames": 68, "byte_identical_frames": 68, "changed_frames": 0, "frame_set_sha256": digest.hexdigest()}


def weather_summary(runtime: dict[str, Any]) -> dict[str, Any]:
    samples = runtime.get("samples")
    if not isinstance(samples, list) or len(samples) != 17:
        raise ValueError("real current-world runtime must retain 17 states")
    count = 0
    max_residual = 0.0
    for sample in samples:
        verify_observation(find_object(sample.get("static_source_meshes")))
        contexts = sample.get("contexts")
        if not isinstance(contexts, dict) or set(contexts) != {"path_eye", "elevated_oblique"}:
            raise ValueError("current-world camera contexts drift")
        for context in contexts.values():
            update = context.get("candidate", {}).get("weather_update", {})
            count += int(update.get("measured_width_count", 0))
            max_residual = max(max_residual, float(update.get("maximum_projected_width_residual_px", 999.0)))
    if count != 1224 or max_residual > 0.05:
        raise ValueError(f"Weather width continuity failed: count={count} residual={max_residual}")
    return {"measurements": count, "maximum_projected_width_residual_px": max_residual, "tolerance_px": 0.05}


def verify(args: argparse.Namespace) -> dict[str, Any]:
    contract = load(args.contract)
    if contract.get("schema") != CONTRACT_SCHEMA or contract.get("decision", {}).get("pass_state") != PASS_STATE:
        raise ValueError("Environment selected-surface segmentation contract drift")
    if contract.get("reusable_rule") != RULE:
        raise ValueError("Environment selected-surface segmentation reusable rule drift")
    if contract.get("decision", {}).get("environment_adoption") is not False or contract.get("decision", {}).get("selected_roughness_adopted") is not False:
        raise ValueError("Environment segmentation contract must remain non-adopting")
    verify_correspondence(load(args.correspondence_report))

    parent_report = load(args.parent_report)
    if parent_report.get("environment_head") != READINESS_HEAD:
        raise ValueError("receiver-readiness parent head drift")
    if parent_report.get("state") != "HOLD_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_RECEIVER__EXACT_UV0_BINDING_NOT_PRESENT":
        raise ValueError("receiver-readiness parent state drift")
    if parent_report.get("real_scene_frame_continuity", {}).get("byte_identical_frames") != 68:
        raise ValueError("receiver-readiness parent visual continuity drift")

    runtime = load(args.runtime)
    if runtime.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError("real current-world observer did not reach inherited target-host PASS")
    if runtime.get("environment_object_selected_surface_segmentation_state") != PASS_STATE:
        raise ValueError("runtime top-level selected-surface segmentation state drift")
    top = verify_observation(find_object(runtime.get("static_source_meshes")))
    frames = compare_frames(Path(args.parent_rendered), Path(args.candidate_rendered))
    weather = weather_summary(runtime)

    report = {
        "schema": "axm.environment-object-selected-surface-segmentation-receiver-result/v0.1",
        "state": PASS_STATE,
        "environment_head": args.environment_head,
        "parent_environment_head": contract["parent_environment_head"],
        "source_surface_correspondence_head": CORRESPONDENCE_HEAD,
        "receiver_readiness_parent_head": READINESS_HEAD,
        "object_asset_id": OBJECT_ASSET_ID,
        "segmentation_observation": top,
        "real_scene_frame_continuity": frames,
        "weather_width_continuity": weather,
        "environment_adoption": False,
        "selected_roughness_adopted": False,
        "next_receiving_requirement": contract["decision"]["next_receiving_requirement"],
        "reusable_rule": RULE,
        "checks": {
            "exact_source_surface_correspondence_bound": True,
            "exact_two_selected_source_faces_independently_addressable": True,
            "parent_material_objects_reused": True,
            "parent_vertex_and_normal_fields_reused": True,
            "all_812_object_triangles_preserved": True,
            "receiver_surface_count_is_exactly_7": True,
            "receiver_uv0_remains_absent": True,
            "selected_roughness_remains_unadopted": True,
            "all_68_real_scene_frames_byte_identical_to_five_surface_parent": True,
            "all_1224_weather_width_measurements_preserved": True,
            "environment_adoption_remains_false": True,
        },
        "truth_boundary": contract["truth_boundary"],
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["verify"])
    parser.add_argument("--contract", required=True)
    parser.add_argument("--correspondence-report", required=True)
    parser.add_argument("--parent-report", required=True)
    parser.add_argument("--parent-rendered", required=True)
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--candidate-rendered", required=True)
    parser.add_argument("--environment-head", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = verify(args)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
