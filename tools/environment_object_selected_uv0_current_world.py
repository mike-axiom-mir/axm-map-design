from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT_SCHEMA = "axm.environment-object-selected-uv0-current-world/v0.1"
OBS_SCHEMA = "axm.environment-object-selected-uv0-current-world-observation/v0.1"
PASS_STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACE_UV0_BOUND__ROUGHNESS_ADOPTION_HELD"
RULE = "EXACT_RECEIVER_UV_BINDING_MUST_MATCH_PINNED_SOURCE_SURFACE_POSITION_TO_TEXCOORD_IDENTITY_BEFORE_SPATIAL_MATERIAL_FIELD_REVIEW"
OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
PARENT_HEAD = "8856745aa0f3de626599afa35fe16a92ae68fa50"
TA_HEAD = "1bcdbae786e02f3ca46a89e4e0ff608d74f364b4"
MATERIALS_HEAD = "0515a2d5ad2c7a1eb545f2b7b327b7367530dfca"
TA_ARTIFACT_SHA256 = "0e24efcbfefb129ef24c153b50020ac321a9789dbf8c148794dfc45f5c9f5f90"
TA_SURFACE_SHA256 = "1f87a7b287c7caa138deee64b687d0aba67a3485ddeae6f80a38ebd906a86aec"
TA_GLB_SHA256 = "9327291569a04bcb22016dc2ac4292499531b141a19e4bfceb291122e20ac3f4"
SELECTED_SCALAR_SHA256 = "b8d13c07f9b71278042b0d42d44b84579a3f327c6adf6723cae4c8c8f06dd38e"
SELECTED_PNG_SHA256 = "57cf746a9a7e0615884fe3c45c6c4df677c2bd0631def61b3ccb1684daa26949"
SELECTED = {
    "lid_inner_service_surface": {"surface_index": 1, "triangles": [12, 13]},
    "front_service_panel_outer_service_surface": {"surface_index": 3, "triangles": [28, 29]},
}


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


def verify_ta(receipt_path: Path, surface_path: Path) -> dict[str, Any]:
    receipt = load(receipt_path)
    if receipt.get("technical_art_head") != TA_HEAD:
        raise ValueError("Technical Art head drift")
    if receipt.get("materials_authority_head") != MATERIALS_HEAD:
        raise ValueError("Materials authority head drift")
    if receipt.get("result") != "PASS_OBJECT_SERVICE_DARK_SELECTED_ROUGHNESS_SCALAR_TO_CURRENT_UC_TEXTURED_GLB":
        raise ValueError("Technical Art semantic selected-roughness transport result drift")
    if receipt.get("glb_sha256") != TA_GLB_SHA256:
        raise ValueError("Technical Art selected-roughness GLB identity drift")
    if receipt.get("selected_scalar_r8_sha256") != SELECTED_SCALAR_SHA256:
        raise ValueError("selected roughness scalar identity drift")
    if receipt.get("selected_materials_png_sha256") != SELECTED_PNG_SHA256:
        raise ValueError("selected roughness historical PNG identity drift")
    if receipt.get("truth_boundary", {}).get("technical_art_exact_roughness_transport_accepted") is not True:
        raise ValueError("Technical Art exact roughness transport is not accepted")
    if sha256(surface_path) != TA_SURFACE_SHA256:
        raise ValueError("Technical Art surface spec digest drift")
    spec = load(surface_path)
    if spec.get("schema") != "axm.surface-3d/v0.1":
        raise ValueError("Technical Art surface spec schema drift")
    primitives = spec.get("primitives")
    if not isinstance(primitives, list) or [p.get("id") for p in primitives] != list(SELECTED):
        raise ValueError("Technical Art selected-surface primitive order/identity drift")
    summary: dict[str, Any] = {}
    for primitive in primitives:
        sid = str(primitive["id"])
        positions = primitive.get("positions")
        texcoords = primitive.get("texcoords")
        indices = primitive.get("indices")
        if not isinstance(positions, list) or not isinstance(texcoords, list) or len(positions) != 4 or len(texcoords) != 4:
            raise ValueError(f"Technical Art exact four-corner position/UV identity drift for {sid}")
        if indices != [0, 2, 1, 0, 3, 2]:
            raise ValueError(f"Technical Art exact two-triangle index identity drift for {sid}")
        summary[sid] = {"positions": positions, "texcoords": texcoords, "indices": indices}
    return {"receipt": receipt, "surface_spec": spec, "selected_surfaces": summary}


def verify_observation(row: dict[str, Any]) -> dict[str, Any]:
    parent = row.get("environment_object_selected_surface_segmentation")
    if not isinstance(parent, dict):
        raise ValueError("parent selected-surface segmentation observation missing")
    if parent.get("state") != "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACES_INDEPENDENTLY_ADDRESSABLE__UV0_AND_SELECTED_ROUGHNESS_ADOPTION_HELD":
        raise ValueError("parent segmentation state drift")
    obs = row.get("environment_object_selected_uv0_current_world")
    if not isinstance(obs, dict):
        raise ValueError("selected UV0 current-world observation missing")
    if obs.get("schema") != OBS_SCHEMA or obs.get("state") != PASS_STATE:
        raise ValueError("selected UV0 schema/state drift")
    if obs.get("reusable_rule") != RULE:
        raise ValueError("selected UV0 reusable rule drift")
    if obs.get("parent_environment_head") != PARENT_HEAD or obs.get("technical_art_head") != TA_HEAD:
        raise ValueError("selected UV0 provenance drift")
    if obs.get("materials_authority_head") != MATERIALS_HEAD:
        raise ValueError("selected UV0 Materials authority drift")
    if obs.get("technical_art_surface_spec_sha256") != TA_SURFACE_SHA256:
        raise ValueError("selected UV0 Technical Art surface digest drift")
    if obs.get("receiver_surface_count") != 7 or obs.get("total_triangles") != 812:
        raise ValueError("selected UV0 receiver structure drift")
    if obs.get("selected_roughness_adopted") is not False or obs.get("environment_adoption") is not False:
        raise ValueError("selected roughness/adoption must remain held in UV-only pass")
    if obs.get("non_selected_surfaces_uv0_absent") is not True:
        raise ValueError("UV0 leaked onto non-selected surfaces")
    selected = obs.get("selected_surfaces")
    if not isinstance(selected, dict) or set(selected) != set(SELECTED):
        raise ValueError("selected UV0 surface set drift")
    for sid, expected in SELECTED.items():
        row_obs = selected[sid]
        if row_obs.get("surface_index") != expected["surface_index"]:
            raise ValueError(f"selected UV0 receiver surface index drift for {sid}")
        if row_obs.get("source_triangle_indices") != expected["triangles"]:
            raise ValueError(f"selected UV0 source triangle identity drift for {sid}")
        if row_obs.get("referenced_vertex_count") != 4 or row_obs.get("matched_ta_corner_count") != 4:
            raise ValueError(f"selected UV0 exact four-corner mapping not closed for {sid}")
        if row_obs.get("exact_position_to_texcoord_pairs_bound") is not True:
            raise ValueError(f"selected UV0 exact TA binding false for {sid}")
        if row_obs.get("unused_uv_values_zero") is not True:
            raise ValueError(f"selected UV0 unused UV slots are not deterministic zero for {sid}")
        if float(row_obs.get("maximum_position_match_delta_m", 999.0)) > 1e-6:
            raise ValueError(f"selected UV0 position match exceeded tolerance for {sid}")
    return obs


def compare_frames(parent_root: Path, candidate_root: Path) -> dict[str, Any]:
    parent = {p.name: p for p in parent_root.glob("atmosphere-width-*.png")}
    candidate = {p.name: p for p in candidate_root.glob("atmosphere-width-*.png")}
    if len(parent) != 68 or set(parent) != set(candidate):
        raise ValueError(f"expected exact 68-frame comparison set; parent={len(parent)} candidate={len(candidate)}")
    changed = [name for name in sorted(parent) if sha256(parent[name]) != sha256(candidate[name])]
    if changed:
        raise ValueError(f"UV-only receiver changed rendered pixels before roughness adoption: {changed[:8]}")
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
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ValueError("selected UV0 Environment contract schema drift")
    decision = contract.get("decision", {})
    if decision.get("pass_state") != PASS_STATE or decision.get("environment_adoption") is not False or decision.get("selected_roughness_adopted") is not False:
        raise ValueError("selected UV0 Environment contract decision drift")
    if contract.get("reusable_rule") != RULE:
        raise ValueError("selected UV0 Environment contract reusable rule drift")
    if contract.get("parent_environment_head") != PARENT_HEAD:
        raise ValueError("selected UV0 parent Environment head drift")
    if contract.get("technical_art", {}).get("artifact_archive_sha256") != TA_ARTIFACT_SHA256:
        raise ValueError("selected UV0 Technical Art artifact archive pin drift")

    ta = verify_ta(Path(args.ta_receipt), Path(args.ta_surface))
    parent_report = load(args.parent_report)
    if parent_report.get("environment_head") != PARENT_HEAD:
        raise ValueError("selected UV0 parent segmentation head drift")
    if parent_report.get("state") != "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACES_INDEPENDENTLY_ADDRESSABLE__UV0_AND_SELECTED_ROUGHNESS_ADOPTION_HELD":
        raise ValueError("selected UV0 parent segmentation report state drift")

    runtime = load(args.runtime)
    if runtime.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError("real current-world observer did not retain inherited target-host PASS")
    if runtime.get("environment_object_selected_uv0_current_world_state") != PASS_STATE:
        raise ValueError("runtime top-level selected UV0 state drift")
    top = verify_observation(find_object(runtime.get("static_source_meshes")))
    frames = compare_frames(Path(args.parent_rendered), Path(args.candidate_rendered))
    weather = weather_summary(runtime)

    report = {
        "schema": "axm.environment-object-selected-uv0-current-world-result/v0.1",
        "state": PASS_STATE,
        "environment_head": args.environment_head,
        "parent_environment_head": PARENT_HEAD,
        "object_asset_id": OBJECT_ASSET_ID,
        "technical_art": {
            "head": TA_HEAD,
            "materials_authority_head": MATERIALS_HEAD,
            "surface_spec_sha256": TA_SURFACE_SHA256,
            "selected_glb_sha256": TA_GLB_SHA256,
            "selected_scalar_r8_sha256": SELECTED_SCALAR_SHA256,
            "selected_historical_png_sha256": SELECTED_PNG_SHA256,
            "selected_surfaces": ta["selected_surfaces"],
        },
        "uv0_observation": top,
        "real_scene_frame_continuity": frames,
        "weather_width_continuity": weather,
        "selected_roughness_adopted": False,
        "environment_adoption": False,
        "next_receiving_requirement": decision.get("next_receiving_requirement"),
        "reusable_rule": RULE,
        "checks": {
            "parent_selected_surface_segmentation_bound": True,
            "technical_art_exact_surface_spec_bound": True,
            "materials_selected_field_authority_bound": True,
            "exact_four_corner_position_to_uv_binding_closed_for_both_surfaces": True,
            "non_selected_surfaces_uv0_absent": True,
            "selected_roughness_remains_unadopted": True,
            "all_68_real_scene_frames_byte_identical_to_segmentation_parent": True,
            "all_1224_weather_width_measurements_preserved": True,
            "environment_adoption_remains_false": True,
        },
        "truth_boundary": contract.get("truth_boundary", {}),
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["verify"])
    parser.add_argument("--contract", required=True)
    parser.add_argument("--ta-receipt", required=True)
    parser.add_argument("--ta-surface", required=True)
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
