from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT_SCHEMA = "axm.environment-object-selected-roughness-receiver-readiness/v0.1"
OBS_SCHEMA = "axm.environment-object-selected-roughness-receiver-readiness-observation/v0.1"
HOLD_STATE = "HOLD_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_RECEIVER__EXACT_UV0_BINDING_NOT_PRESENT"
RULE = "SPATIAL_MATERIAL_FIELD_REQUIRES_EXACT_RECEIVER_UV_IDENTITY_BEFORE_CURRENT_WORLD_ADOPTION"
OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
ACCEPTED_WORLD_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
MATERIALS_HEAD = "0515a2d5ad2c7a1eb545f2b7b327b7367530dfca"
MATERIALS_BLOB = "16ab4ea07c41273e58b72f970d6bed383bbbfe33"
SELECTED_SCALAR = "b8d13c07f9b71278042b0d42d44b84579a3f327c6adf6723cae4c8c8f06dd38e"
TECHNICAL_ART_HEAD = "1bcdbae786e02f3ca46a89e4e0ff608d74f364b4"
TECHNICAL_ART_RESULT = "PASS_OBJECT_SERVICE_DARK_SELECTED_ROUGHNESS_SCALAR_TO_CURRENT_UC_TEXTURED_GLB_TO_GODOT_FRONT_VIEWS"
TECHNICAL_ART_GLB_SHA = "9327291569a04bcb22016dc2ac4292499531b141a19e4bfceb291122e20ac3f4"
CURRENT_RECEIVER_MATERIALS_HEAD = "c85517446a769e0d5f880fc0e9e32f47124f7b5e"
CURRENT_RECEIVER_PROFILE_SHA = "dc200229d6c25fa84063aa51f66103abc022efa54b2167e4432a5b47fc40360c"
MATERIAL_IDS = ["shell_coating", "service_dark", "hardware_steel", "rubber_guard", "interface_orange"]


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def find_object(rows: Any) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise ValueError("runtime static_source_meshes missing")
    matches = [row for row in rows if isinstance(row, dict) and row.get("asset_id") == OBJECT_ASSET_ID]
    if len(matches) != 1:
        raise ValueError(f"expected one current-world Object result, got {len(matches)}")
    return matches[0]


def verify_readiness_row(row: dict[str, Any]) -> dict[str, Any]:
    readiness = row.get("environment_object_selected_roughness_receiver_readiness")
    if not isinstance(readiness, dict):
        raise ValueError("current-world Object readiness observation missing")
    if readiness.get("schema") != OBS_SCHEMA or readiness.get("state") != HOLD_STATE:
        raise ValueError("current-world Object readiness state/schema drift")
    if readiness.get("reusable_rule") != RULE:
        raise ValueError("current-world Object readiness rule drift")
    if readiness.get("current_receiver_materials_head") != CURRENT_RECEIVER_MATERIALS_HEAD:
        raise ValueError("current Map Object receiver Materials identity drift")
    if readiness.get("current_receiver_material_profile_sha256") != CURRENT_RECEIVER_PROFILE_SHA:
        raise ValueError("current Map Object material profile identity drift")
    if readiness.get("selected_materials_head") != MATERIALS_HEAD:
        raise ValueError("selected Materials authority head drift")
    if readiness.get("selected_scalar_r8_sha256") != SELECTED_SCALAR:
        raise ValueError("selected roughness scalar identity drift")
    if readiness.get("technical_art_head") != TECHNICAL_ART_HEAD or readiness.get("technical_art_result") != TECHNICAL_ART_RESULT:
        raise ValueError("Technical Art selected roughness transport identity drift")
    if readiness.get("selected_roughness_adopted") is not False or readiness.get("environment_adoption") is not False:
        raise ValueError("receiver adoption must remain false while UV0 identity is absent")
    uv = readiness.get("uv0")
    if not isinstance(uv, dict) or uv.get("surface_count") != 5:
        raise ValueError("current receiver UV0 diagnostic surface count drift")
    surfaces = uv.get("surfaces")
    if not isinstance(surfaces, list) or len(surfaces) != 5:
        raise ValueError("current receiver UV0 diagnostic rows missing")
    if uv.get("total_uv0_count") != 0 or uv.get("all_surfaces_uv0_absent") is not True:
        raise ValueError("current receiver unexpectedly has UV0; HOLD contract must be re-evaluated")
    if [x.get("material_id") for x in surfaces] != MATERIAL_IDS:
        raise ValueError("current receiver five-surface material order drift")
    if any(int(x.get("uv0_count", -1)) != 0 or x.get("uv0_present") is not False for x in surfaces):
        raise ValueError("one or more current receiver surfaces unexpectedly carry UV0")
    return readiness


def verify_materials(contract: dict[str, Any]) -> None:
    if contract.get("schema") != "axm.object-service-dark-roughness-selected-field/v0.1":
        raise ValueError("Materials selected-field contract schema drift")
    if contract.get("material_id") != "service_dark":
        raise ValueError("Materials selected-field material ID drift")
    selected = contract.get("selected_field")
    if not isinstance(selected, dict):
        raise ValueError("Materials selected field missing")
    expected = {
        "semantic_encoding": "BASE_LEVEL_R8_SCALAR_VALUES_ROW_MAJOR",
        "width_px": 512,
        "height_px": 512,
        "scalar_r8_sha256": SELECTED_SCALAR,
        "observed_r8_min": 153,
        "observed_r8_max": 183,
        "observed_unique_r8_values": 31,
    }
    for key, value in expected.items():
        if selected.get(key) != value:
            raise ValueError(f"Materials selected field drift: {key}")
    direction = contract.get("art_direction_reference")
    if not isinstance(direction, dict) or direction.get("decision") != "PASS_ART_DIRECTION_OBJECT_SERVICE_DARK_BOUNDED_ROUGHNESS_MICROVARIATION_PREFERENCE_024":
        raise ValueError("Art Direction selected roughness decision drift")


def verify_technical_art(receipt: dict[str, Any], target: dict[str, Any], glb_path: Path) -> dict[str, Any]:
    if receipt.get("result") != "PASS_OBJECT_SERVICE_DARK_SELECTED_ROUGHNESS_SCALAR_TO_CURRENT_UC_TEXTURED_GLB":
        raise ValueError("Technical Art transport receipt is not exact PASS")
    if receipt.get("technical_art_head") != TECHNICAL_ART_HEAD or receipt.get("materials_authority_head") != MATERIALS_HEAD:
        raise ValueError("Technical Art donor identity drift")
    if receipt.get("selected_scalar_r8_sha256") != SELECTED_SCALAR:
        raise ValueError("Technical Art selected scalar drift")
    if receipt.get("uc_uv_status") != "MEASURED" or receipt.get("uc_uv_findings") not in ([], None):
        raise ValueError("Technical Art UV observation is not clean/measured")
    primitive_rows = receipt.get("glb_selected_roughness", {}).get("primitives", [])
    if len(primitive_rows) != 2:
        raise ValueError("Technical Art selected roughness proof must retain two source-surface primitives")
    for row in primitive_rows:
        if row.get("orm_green_sha256") != SELECTED_SCALAR:
            raise ValueError("Technical Art ORM-green scalar drift")
        if [row.get("roughness_r8_min"), row.get("roughness_r8_max"), row.get("roughness_unique_r8_values")] != [153, 183, 31]:
            raise ValueError("Technical Art transported roughness statistics drift")
    if target.get("result") != TECHNICAL_ART_RESULT:
        raise ValueError("Technical Art Godot target result drift")
    if target.get("technical_art_head") != TECHNICAL_ART_HEAD or target.get("glb_sha256") != receipt.get("glb_sha256"):
        raise ValueError("Technical Art Godot target provenance drift")
    if receipt.get("glb_sha256") != TECHNICAL_ART_GLB_SHA or sha256(glb_path) != TECHNICAL_ART_GLB_SHA:
        raise ValueError("Technical Art exact GLB byte identity drift")
    if target.get("godot_status") != "PASS" or target.get("godot_observation_status") != "PASS":
        raise ValueError("Technical Art real Godot observation not PASS")
    return {
        "head": TECHNICAL_ART_HEAD,
        "result": TECHNICAL_ART_RESULT,
        "glb_sha256": TECHNICAL_ART_GLB_SHA,
        "mesh_count": receipt.get("glb_selected_roughness", {}).get("meshes"),
        "primitive_count": len(primitive_rows),
        "uv_status": receipt.get("uc_uv_status"),
    }


def compare_frames(parent_root: Path, candidate_root: Path) -> dict[str, Any]:
    parent = {p.name: p for p in parent_root.glob("atmosphere-width-*.png")}
    candidate = {p.name: p for p in candidate_root.glob("atmosphere-width-*.png")}
    if len(parent) != 68 or set(parent) != set(candidate):
        raise ValueError(f"expected exact 68-frame retained set; parent={len(parent)} candidate={len(candidate)}")
    changed = []
    for name in sorted(parent):
        if sha256(parent[name]) != sha256(candidate[name]):
            changed.append(name)
    if changed:
        raise ValueError(f"readiness instrumentation changed real scene pixels: {changed[:8]}")
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
        contexts = sample.get("contexts")
        if not isinstance(contexts, dict) or set(contexts) != {"path_eye", "elevated_oblique"}:
            raise ValueError("current-world camera contexts drift")
        verify_readiness_row(find_object(sample.get("static_source_meshes")))
        for context in contexts.values():
            update = context.get("candidate", {}).get("weather_update", {})
            count += int(update.get("measured_width_count", 0))
            max_residual = max(max_residual, float(update.get("maximum_projected_width_residual_px", 999.0)))
    if count != 1224 or max_residual > 0.05:
        raise ValueError(f"Weather width continuity failed: count={count} residual={max_residual}")
    return {"measurements": count, "maximum_projected_width_residual_px": max_residual, "tolerance_px": 0.05}


def verify(args: argparse.Namespace) -> dict[str, Any]:
    contract = load(args.contract)
    if contract.get("schema") != CONTRACT_SCHEMA or contract.get("decision", {}).get("state") != HOLD_STATE:
        raise ValueError("Environment readiness contract drift")
    if contract.get("reusable_rule") != RULE or contract.get("environment", {}).get("accepted_real_scene_evidence_head") != ACCEPTED_WORLD_HEAD:
        raise ValueError("Environment readiness contract identity drift")
    if contract.get("selected_materials_authority", {}).get("head") != MATERIALS_HEAD:
        raise ValueError("Environment contract selected Materials head drift")
    if contract.get("selected_materials_authority", {}).get("contract_git_blob") != MATERIALS_BLOB:
        raise ValueError("Environment contract selected Materials blob drift")
    if contract.get("technical_art_transport", {}).get("head") != TECHNICAL_ART_HEAD:
        raise ValueError("Environment contract Technical Art head drift")
    if contract.get("decision", {}).get("environment_adoption") is not False:
        raise ValueError("Environment contract must remain non-adopting")

    materials = load(args.materials_contract)
    verify_materials(materials)
    ta = verify_technical_art(load(args.technical_art_receipt), load(args.technical_art_target), Path(args.technical_art_glb))

    parent_report = load(args.parent_report)
    if parent_report.get("state") != "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_TARGET_HOST":
        raise ValueError("exact accepted real-scene parent is not the expected PASS")
    if parent_report.get("matched_frames") != 68 or parent_report.get("weather_width_measurements") != 1224:
        raise ValueError("exact accepted real-scene parent evidence cardinality drift")

    runtime = load(args.runtime)
    if runtime.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError("real current-world observer did not reach target-host PASS")
    if runtime.get("environment_object_selected_roughness_readiness_state") != HOLD_STATE:
        raise ValueError("runtime top-level readiness state drift")
    if runtime.get("environment_object_selected_roughness_scalar_sha256") != SELECTED_SCALAR:
        raise ValueError("runtime top-level selected scalar drift")
    top_readiness = verify_readiness_row(find_object(runtime.get("static_source_meshes")))
    frames = compare_frames(Path(args.parent_rendered), Path(args.candidate_rendered))
    weather = weather_summary(runtime)

    report = {
        "schema": "axm.environment-object-selected-roughness-receiver-readiness-result/v0.1",
        "state": HOLD_STATE,
        "environment_head": args.environment_head,
        "accepted_real_scene_evidence_head": ACCEPTED_WORLD_HEAD,
        "object_asset_id": OBJECT_ASSET_ID,
        "current_receiver_materials_head": CURRENT_RECEIVER_MATERIALS_HEAD,
        "current_receiver_material_profile_sha256": CURRENT_RECEIVER_PROFILE_SHA,
        "selected_materials_head": MATERIALS_HEAD,
        "selected_scalar_r8_sha256": SELECTED_SCALAR,
        "technical_art": ta,
        "receiver_uv0": top_readiness["uv0"],
        "real_scene_frame_continuity": frames,
        "weather_width_continuity": weather,
        "environment_adoption": False,
        "reusable_rule": RULE,
        "next_receiving_requirement": contract["decision"]["next_receiving_requirement"],
        "checks": {
            "exact_selected_materials_identity": True,
            "exact_technical_art_transport_identity": True,
            "real_current_world_receiver_observed": True,
            "exact_five_surface_object_receiver": True,
            "uv0_absent_on_all_five_surfaces": True,
            "selected_roughness_not_silently_adopted": True,
            "all_68_real_scene_frames_byte_identical": True,
            "all_1224_weather_width_measurements_preserved": True,
            "environment_coordination_boundary_preserved": True,
        },
        "truth_boundary": (
            "HOLD proves a concrete receiving gap, not a material failure: the exact Art-selected Object roughness scalar and exact Technical Art GLB/Godot transport exist upstream, while the real current Map five-surface Object receiver has zero TEXCOORD_0 values. The readiness observer changes no scene pixels and does not authorize Environment-authored UVs, Runtime storage adoption, Art/QA acceptance, CANON or production readiness."
        ),
    }
    if not all(report["checks"].values()):
        raise ValueError("readiness checks unexpectedly false")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--contract", required=True)
    p.add_argument("--materials-contract", required=True)
    p.add_argument("--technical-art-receipt", required=True)
    p.add_argument("--technical-art-target", required=True)
    p.add_argument("--technical-art-glb", required=True)
    p.add_argument("--parent-report", required=True)
    p.add_argument("--parent-rendered", required=True)
    p.add_argument("--runtime", required=True)
    p.add_argument("--candidate-rendered", required=True)
    p.add_argument("--environment-head", required=True)
    p.add_argument("--output", required=True)
    args = parser.parse_args()
    report = verify(args)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
