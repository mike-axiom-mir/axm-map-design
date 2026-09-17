from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT_SCHEMA = "axm.environment-object-selected-uv0-current-world/v0.2"
OBS_SCHEMA = "axm.environment-object-selected-uv0-current-world-observation/v0.2"
PASS_STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACE_UV0_BOUND__ROUGHNESS_ADOPTION_HELD"
RULE = "EXACT_RECEIVER_UV_BINDING_MUST_MATCH_PINNED_SOURCE_VERTEX_IDENTITY_TO_TEXCOORD_IDENTITY_BEFORE_SPATIAL_MATERIAL_FIELD_REVIEW"
OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
PARENT_HEAD = "8856745aa0f3de626599afa35fe16a92ae68fa50"
OBJECT_SOURCE_HEAD = "d3fa10a270faae7925811f44f03381fe5c5d0215"
OBJECT_SOURCE_SHA256 = "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
HARD_SURFACE_HEAD = "f7c64d08e4e2a0d6954291d8b4e064d7345ab658"
TA_HEAD = "1bcdbae786e02f3ca46a89e4e0ff608d74f364b4"
MATERIALS_HEAD = "0515a2d5ad2c7a1eb545f2b7b327b7367530dfca"
TA_ARTIFACT_SHA256 = "0e24efcbfefb129ef24c153b50020ac321a9789dbf8c148794dfc45f5c9f5f90"
TA_SURFACE_SHA256 = "1f87a7b287c7caa138deee64b687d0aba67a3485ddeae6f80a38ebd906a86aec"
TA_GLB_SHA256 = "9327291569a04bcb22016dc2ac4292499531b141a19e4bfceb291122e20ac3f4"
SELECTED_SCALAR_SHA256 = "b8d13c07f9b71278042b0d42d44b84579a3f327c6adf6723cae4c8c8f06dd38e"
SELECTED_PNG_SHA256 = "57cf746a9a7e0615884fe3c45c6c4df677c2bd0631def61b3ccb1684daa26949"
SELECTED = {
    "lid_inner_service_surface": {
        "surface_index": 1,
        "triangles": [12, 13],
        "source_vertex_to_ta_corner": {8: 0, 9: 3, 10: 2, 11: 1},
    },
    "front_service_panel_outer_service_surface": {
        "surface_index": 3,
        "triangles": [28, 29],
        "source_vertex_to_ta_corner": {16: 0, 17: 1, 20: 3, 21: 2},
    },
}


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize_int_map(value: Any) -> dict[int, int]:
    if not isinstance(value, dict):
        raise ValueError("expected integer-key mapping")
    return {int(k): int(v) for k, v in value.items()}


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
        if [int(v) for v in indices] != [0, 2, 1, 0, 3, 2]:
            raise ValueError(f"Technical Art exact two-triangle index identity drift for {sid}")
        summary[sid] = {"positions": positions, "texcoords": texcoords, "indices": indices}
    return {"receipt": receipt, "surface_spec": spec, "selected_surfaces": summary}


def verify_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ValueError("selected UV0 Environment contract schema drift")
    if contract.get("reusable_rule") != RULE or contract.get("parent_environment_head") != PARENT_HEAD:
        raise ValueError("selected UV0 Environment contract lineage/rule drift")
    source = contract.get("object_source", {})
    if source.get("head") != OBJECT_SOURCE_HEAD or source.get("host_source_sha256") != OBJECT_SOURCE_SHA256:
        raise ValueError("selected UV0 Object source authority drift")
    if contract.get("hard_surface", {}).get("head") != HARD_SURFACE_HEAD:
        raise ValueError("selected UV0 Hard Surface authority drift")
    if contract.get("technical_art", {}).get("artifact_archive_sha256") != TA_ARTIFACT_SHA256:
        raise ValueError("selected UV0 Technical Art artifact archive pin drift")
    if contract.get("materials", {}).get("head") != MATERIALS_HEAD:
        raise ValueError("selected UV0 Materials authority drift")
    configured = contract.get("selected_surfaces", {})
    if set(configured) != set(SELECTED):
        raise ValueError("selected UV0 contract surface set drift")
    for sid, expected in SELECTED.items():
        row = configured[sid]
        if row.get("receiver_surface_index") != expected["surface_index"] or row.get("source_triangle_indices") != expected["triangles"]:
            raise ValueError(f"selected UV0 contract surface identity drift for {sid}")
        if normalize_int_map(row.get("source_vertex_to_technical_art_corner")) != expected["source_vertex_to_ta_corner"]:
            raise ValueError(f"selected UV0 contract source-vertex/TA-corner adapter drift for {sid}")
    decision = contract.get("decision", {})
    if decision.get("pass_state") != PASS_STATE or decision.get("environment_adoption") is not False or decision.get("selected_roughness_adopted") is not False:
        raise ValueError("selected UV0 Environment contract decision drift")


def verify_observation(row: dict[str, Any]) -> dict[str, Any]:
    parent = row.get("environment_object_selected_surface_segmentation")
    if not isinstance(parent, dict):
        raise ValueError("parent selected-surface segmentation observation missing")
    if parent.get("state") != "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACES_INDEPENDENTLY_ADDRESSABLE__UV0_AND_SELECTED_ROUGHNESS_ADOPTION_HELD":
        raise ValueError("parent segmentation state drift")
    obs = row.get("environment_object_selected_uv0_current_world")
    if not isinstance(obs, dict):
        raise ValueError("selected UV0 current-world observation missing")
    if obs.get("schema") != OBS_SCHEMA or obs.get("state") != PASS_STATE or obs.get("reusable_rule") != RULE:
        raise ValueError("selected UV0 schema/state/rule drift")
    if obs.get("parent_environment_head") != PARENT_HEAD or obs.get("technical_art_head") != TA_HEAD:
        raise ValueError("selected UV0 provenance drift")
    if obs.get("object_source_head") != OBJECT_SOURCE_HEAD or obs.get("object_host_source_sha256") != OBJECT_SOURCE_SHA256:
        raise ValueError("selected UV0 Object source identity drift")
    if obs.get("materials_authority_head") != MATERIALS_HEAD or obs.get("technical_art_surface_spec_sha256") != TA_SURFACE_SHA256:
        raise ValueError("selected UV0 Materials/Technical Art authority drift")
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
        if row_obs.get("surface_index") != expected["surface_index"] or row_obs.get("source_triangle_indices") != expected["triangles"]:
            raise ValueError(f"selected UV0 source/surface identity drift for {sid}")
        if set(int(v) for v in row_obs.get("source_vertex_indices", [])) != set(expected["source_vertex_to_ta_corner"]):
            raise ValueError(f"selected UV0 source vertex identity drift for {sid}")
        if row_obs.get("referenced_vertex_count") != 4 or row_obs.get("matched_source_vertex_count") != 4 or row_obs.get("matched_ta_corner_count") != 4:
            raise ValueError(f"selected UV0 exact four-corner source binding not closed for {sid}")
        if row_obs.get("exact_source_vertex_to_texcoord_identity_bound") is not True:
            raise ValueError(f"selected UV0 exact source-vertex to texcoord binding false for {sid}")
        if normalize_int_map(row_obs.get("source_vertex_to_technical_art_corner")) != expected["source_vertex_to_ta_corner"]:
            raise ValueError(f"selected UV0 source-vertex/TA-corner observation drift for {sid}")
        if row_obs.get("ta_transport_positions_used_as_source_positions") is not False:
            raise ValueError(f"selected UV0 wrongly promoted TA transport positions for {sid}")
        if row_obs.get("unused_uv_values_zero") is not True:
            raise ValueError(f"selected UV0 unused UV slots are not deterministic zero for {sid}")
        if float(row_obs.get("maximum_source_world_position_delta_m", 999.0)) > 1e-6:
            raise ValueError(f"selected UV0 current-world source position match exceeded tolerance for {sid}")
        pairs = row_obs.get("source_vertex_to_texcoord_pairs", [])
        if not isinstance(pairs, list) or len(pairs) != 4:
            raise ValueError(f"selected UV0 source vertex/texcoord pairs missing for {sid}")
        seen_source = {int(p["source_vertex_index"]) for p in pairs}
        seen_ta = {int(p["technical_art_corner_index"]) for p in pairs}
        if seen_source != set(expected["source_vertex_to_ta_corner"]) or seen_ta != {0, 1, 2, 3}:
            raise ValueError(f"selected UV0 source/TA pair coverage drift for {sid}")
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
    verify_contract(contract)
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
        "schema": "axm.environment-object-selected-uv0-current-world-result/v0.2",
        "state": PASS_STATE,
        "environment_head": args.environment_head,
        "parent_environment_head": PARENT_HEAD,
        "object_asset_id": OBJECT_ASSET_ID,
        "object_source": {"head": OBJECT_SOURCE_HEAD, "host_source_sha256": OBJECT_SOURCE_SHA256},
        "hard_surface_head": HARD_SURFACE_HEAD,
        "technical_art": {
            "head": TA_HEAD,
            "materials_authority_head": MATERIALS_HEAD,
            "surface_spec_sha256": TA_SURFACE_SHA256,
            "selected_glb_sha256": TA_GLB_SHA256,
            "selected_scalar_r8_sha256": SELECTED_SCALAR_SHA256,
            "selected_historical_png_sha256": SELECTED_PNG_SHA256,
            "selected_surfaces": ta["selected_surfaces"],
            "transport_positions_promoted_to_source_positions": False,
        },
        "uv0_observation": top,
        "real_scene_frame_continuity": frames,
        "weather_width_continuity": weather,
        "selected_roughness_adopted": False,
        "environment_adoption": False,
        "next_receiving_requirement": contract["decision"].get("next_receiving_requirement"),
        "reusable_rule": RULE,
        "checks": {
            "parent_selected_surface_segmentation_bound": True,
            "pinned_object_source_vertex_identity_bound": True,
            "technical_art_exact_surface_texcoord_spec_bound": True,
            "technical_art_transport_positions_not_promoted_to_source_positions": True,
            "materials_selected_field_authority_bound": True,
            "exact_four_corner_source_vertex_to_uv_binding_closed_for_both_surfaces": True,
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
