from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

CONTRACT_SCHEMA = "axm.environment-object-selected-roughness-current-world/v0.1"
OBS_SCHEMA = "axm.environment-object-selected-roughness-current-world-observation/v0.1"
BOUND_STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_APPEARANCE_CANDIDATE_BOUND__ENVIRONMENT_ADOPTION_HELD"
REVIEW_READY = "PASS_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_APPEARANCE_CANDIDATE_REVIEW_READY__ENVIRONMENT_ADOPTION_HELD"
HOLD_NOT_VISIBLE = "HOLD_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_APPEARANCE_NOT_RESOLVED_ABOVE_1LSB__ENVIRONMENT_ADOPTION_HELD"
RULE = "SPATIAL_MATERIAL_FIELD_MAY_ENTER_CURRENT_WORLD_REVIEW_ONLY_AFTER_EXACT_SURFACE_AND_UV_IDENTITY__APPEARANCE_AND_RUNTIME_ACCEPTANCE_REMAIN_SEPARATE"
OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
PARENT_HEAD = "4eed6da68f746ca2849c89fa88533f82bc836b26"
MATERIALS_HEAD = "0515a2d5ad2c7a1eb545f2b7b327b7367530dfca"
TA_HEAD = "1bcdbae786e02f3ca46a89e4e0ff608d74f364b4"
SELECTED_SCALAR_SHA256 = "b8d13c07f9b71278042b0d42d44b84579a3f327c6adf6723cae4c8c8f06dd38e"
SELECTED_PNG_SHA256 = "57cf746a9a7e0615884fe3c45c6c4df677c2bd0631def61b3ccb1684daa26949"
TA_SURFACE_SHA256 = "1f87a7b287c7caa138deee64b687d0aba67a3485ddeae6f80a38ebd906a86aec"
SELECTED = {
    "lid_inner_service_surface": 1,
    "front_service_panel_outer_service_surface": 3,
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


def verify_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ValueError("selected roughness Environment contract schema drift")
    if contract.get("parent_environment_head") != PARENT_HEAD or contract.get("reusable_rule") != RULE:
        raise ValueError("selected roughness Environment lineage/rule drift")
    if contract.get("materials", {}).get("head") != MATERIALS_HEAD:
        raise ValueError("selected roughness Materials authority drift")
    if contract.get("technical_art", {}).get("head") != TA_HEAD:
        raise ValueError("selected roughness Technical Art authority drift")
    selected = contract.get("selected_field", {})
    if selected.get("scalar_r8_sha256") != SELECTED_SCALAR_SHA256 or selected.get("png_sha256") != SELECTED_PNG_SHA256:
        raise ValueError("selected roughness field identity drift")
    if selected.get("width_px") != 512 or selected.get("height_px") != 512:
        raise ValueError("selected roughness field dimensions drift")
    decision = contract.get("decision", {})
    if decision.get("environment_adoption") is not False or decision.get("art_qa_acceptance_required") is not True or decision.get("runtime_acceptance_required") is not True:
        raise ValueError("selected roughness Environment decision boundary drift")


def verify_png(path: Path) -> dict[str, Any]:
    if sha256(path) != SELECTED_PNG_SHA256:
        raise ValueError("selected roughness PNG identity drift")
    image = Image.open(path).convert("RGBA")
    if image.size != (512, 512):
        raise ValueError("selected roughness PNG dimensions drift")
    arr = np.asarray(image, dtype=np.uint8)
    red = arr[:, :, 0]
    scalar_digest = hashlib.sha256(red.tobytes(order="C")).hexdigest()
    if scalar_digest != SELECTED_SCALAR_SHA256:
        raise ValueError("selected roughness scalar R8 identity drift")
    unique = np.unique(red)
    if int(red.min()) != 153 or int(red.max()) != 183 or int(unique.size) != 31:
        raise ValueError("selected roughness scalar observation drift")
    return {"png_sha256": SELECTED_PNG_SHA256, "scalar_r8_sha256": scalar_digest, "min": 153, "max": 183, "unique": 31}


def verify_ta(receipt_path: Path, surface_path: Path) -> None:
    receipt = load(receipt_path)
    if receipt.get("technical_art_head") != TA_HEAD or receipt.get("materials_authority_head") != MATERIALS_HEAD:
        raise ValueError("selected roughness Technical Art provenance drift")
    if receipt.get("selected_scalar_r8_sha256") != SELECTED_SCALAR_SHA256:
        raise ValueError("selected roughness Technical Art scalar identity drift")
    if receipt.get("result") != "PASS_OBJECT_SERVICE_DARK_SELECTED_ROUGHNESS_SCALAR_TO_CURRENT_UC_TEXTURED_GLB":
        raise ValueError("selected roughness Technical Art transport result drift")
    if sha256(surface_path) != TA_SURFACE_SHA256:
        raise ValueError("Technical Art surface spec digest drift")


def verify_observation(row: dict[str, Any]) -> dict[str, Any]:
    uv = row.get("environment_object_selected_uv0_current_world")
    if not isinstance(uv, dict) or uv.get("selected_roughness_adopted") is not False:
        raise ValueError("selected roughness parent UV0 boundary missing")
    obs = row.get("environment_object_selected_roughness_current_world")
    if not isinstance(obs, dict):
        raise ValueError("selected roughness current-world observation missing")
    if obs.get("schema") != OBS_SCHEMA or obs.get("state") != BOUND_STATE or obs.get("reusable_rule") != RULE:
        raise ValueError("selected roughness observation schema/state/rule drift")
    if obs.get("parent_environment_head") != PARENT_HEAD or obs.get("materials_authority_head") != MATERIALS_HEAD or obs.get("technical_art_head") != TA_HEAD:
        raise ValueError("selected roughness observation provenance drift")
    if obs.get("selected_png_sha256") != SELECTED_PNG_SHA256 or obs.get("selected_scalar_r8_sha256") != SELECTED_SCALAR_SHA256:
        raise ValueError("selected roughness observation field identity drift")
    if obs.get("selected_surface_count") != 2 or obs.get("non_selected_surfaces_roughness_texture_absent") is not True:
        raise ValueError("selected roughness surface isolation drift")
    if obs.get("geometry_positions_normals_indices_uv0_reused") is not True or obs.get("selected_roughness_bound") is not True:
        raise ValueError("selected roughness receiver reuse/binding drift")
    if obs.get("environment_adoption") is not False:
        raise ValueError("selected roughness Environment adoption must remain held")
    surfaces = obs.get("selected_surfaces")
    if not isinstance(surfaces, dict) or set(surfaces) != set(SELECTED):
        raise ValueError("selected roughness exact selected surface set drift")
    for sid, index in SELECTED.items():
        item = surfaces[sid]
        if item.get("surface_index") != index or item.get("uv0_count", 0) <= 0:
            raise ValueError(f"selected roughness exact UV-bound surface drift for {sid}")
        if item.get("selected_roughness_texture_bound") is not True or item.get("selected_roughness_texture_channel") != "RED":
            raise ValueError(f"selected roughness texture binding drift for {sid}")
        if item.get("base_color_and_metallic_preserved") is not True:
            raise ValueError(f"selected roughness base color/metallic changed for {sid}")
        if abs(float(item.get("candidate_roughness_scalar_multiplier", -1.0)) - 1.0) > 1e-9:
            raise ValueError(f"selected roughness scalar multiplier drift for {sid}")
    return obs


def frame_map(root: Path) -> dict[str, Path]:
    return {p.name: p for p in root.glob("atmosphere-width-*.png")}


def parse_frame_name(name: str) -> tuple[str, str, int]:
    stem = name.removesuffix(".png")
    prefix = "atmosphere-width-"
    if not stem.startswith(prefix):
        raise ValueError(f"unexpected frame name: {name}")
    rest = stem[len(prefix):]
    mode, tail = rest.split("-", 1)
    context, state = tail.rsplit("-", 1)
    return mode, context, int(state)


def compare_frames(parent_root: Path, candidate_root: Path) -> dict[str, Any]:
    parent = frame_map(parent_root)
    candidate = frame_map(candidate_root)
    if len(parent) != 68 or set(parent) != set(candidate):
        raise ValueError(f"expected exact 68-frame selected-roughness A/B; parent={len(parent)} candidate={len(candidate)}")
    aggregate: dict[str, dict[str, int]] = {}
    per_frame: dict[str, Any] = {}
    total_gt1 = 0
    total_raw = 0
    max_lsb = 0
    changed_frames = 0
    for name in sorted(parent):
        a = np.asarray(Image.open(parent[name]).convert("RGBA"), dtype=np.int16)
        b = np.asarray(Image.open(candidate[name]).convert("RGBA"), dtype=np.int16)
        if a.shape != b.shape:
            raise ValueError(f"frame dimensions drift: {name}")
        delta = np.abs(a[:, :, :3] - b[:, :, :3])
        raw_mask = np.any(delta > 0, axis=2)
        gt1_mask = np.any(delta > 1, axis=2)
        raw = int(raw_mask.sum())
        gt1 = int(gt1_mask.sum())
        frame_max = int(delta.max(initial=0))
        mode, context, state = parse_frame_name(name)
        key = f"{mode}/{context}"
        agg = aggregate.setdefault(key, {"frames": 0, "changed_frames": 0, "changed_pixels_raw": 0, "changed_pixels_gt_1lsb": 0, "max_channel_delta_lsb": 0})
        agg["frames"] += 1
        agg["changed_pixels_raw"] += raw
        agg["changed_pixels_gt_1lsb"] += gt1
        agg["max_channel_delta_lsb"] = max(agg["max_channel_delta_lsb"], frame_max)
        bbox = None
        if raw:
            ys, xs = np.where(raw_mask)
            bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            changed_frames += 1
            agg["changed_frames"] += 1
        per_frame[name] = {"mode": mode, "context": context, "state": state, "changed_pixels_raw": raw, "changed_pixels_gt_1lsb": gt1, "max_channel_delta_lsb": frame_max, "bbox": bbox}
        total_raw += raw
        total_gt1 += gt1
        max_lsb = max(max_lsb, frame_max)
    context_gt1 = {ctx: sum(v["changed_pixels_gt_1lsb"] for k, v in aggregate.items() if k.endswith("/" + ctx)) for ctx in ("path_eye", "elevated_oblique")}
    state = REVIEW_READY if total_gt1 > 0 else HOLD_NOT_VISIBLE
    return {
        "state": state,
        "matched_frames": 68,
        "changed_frames": changed_frames,
        "changed_pixels_raw_total": total_raw,
        "changed_pixels_gt_1lsb_total": total_gt1,
        "maximum_channel_delta_lsb": max_lsb,
        "changed_pixels_gt_1lsb_by_context": context_gt1,
        "aggregate": aggregate,
        "per_frame": per_frame,
    }


def runtime_trade(parent: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    fields = ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "buffer_mem_bytes", "texture_mem_bytes")
    deltas: dict[str, list[int]] = {f: [] for f in fields}
    for p_sample, c_sample in zip(parent.get("samples", []), candidate.get("samples", []), strict=True):
        for context in ("path_eye", "elevated_oblique"):
            for mode in ("control", "candidate"):
                p = p_sample["contexts"][context][mode]["runtime"]
                c = c_sample["contexts"][context][mode]["runtime"]
                for field in fields:
                    deltas[field].append(int(c[field]) - int(p[field]))
    for field in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame"):
        if any(d != 0 for d in deltas[field]):
            raise ValueError(f"selected roughness changed structural runtime submission field: {field}")
    return {field: {"min_delta": min(values), "max_delta": max(values), "unique_deltas": sorted(set(values))} for field, values in deltas.items()}


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
    field = verify_png(Path(args.selected_png))
    verify_ta(Path(args.ta_receipt), Path(args.ta_surface))
    parent_report = load(args.parent_report)
    if parent_report.get("environment_head") != PARENT_HEAD:
        raise ValueError("selected roughness parent UV0 Environment head drift")
    if parent_report.get("state") != "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACE_UV0_BOUND__ROUGHNESS_ADOPTION_HELD":
        raise ValueError("selected roughness parent UV0 state drift")
    parent_runtime = load(args.parent_runtime)
    runtime = load(args.runtime)
    if runtime.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError("selected roughness current-world observer did not retain inherited target-host PASS")
    if runtime.get("environment_object_selected_roughness_current_world_state") != BOUND_STATE:
        raise ValueError("selected roughness runtime top-level state drift")
    top = verify_observation(find_object(runtime.get("static_source_meshes")))
    frames = compare_frames(Path(args.parent_rendered), Path(args.candidate_rendered))
    weather = weather_summary(runtime)
    trade = runtime_trade(parent_runtime, runtime)
    report = {
        "schema": "axm.environment-object-selected-roughness-current-world-result/v0.1",
        "state": frames["state"],
        "binding_state": BOUND_STATE,
        "environment_head": args.environment_head,
        "parent_environment_head": PARENT_HEAD,
        "reusable_rule": RULE,
        "selected_field": field,
        "receiver_observation": top,
        "real_scene_appearance_delta": frames,
        "weather_width_continuity": weather,
        "proof_host_runtime_trade": trade,
        "environment_adoption": False,
        "art_qa_acceptance_required": True,
        "runtime_acceptance_required": True,
        "checks": {
            "exact_parent_uv0_receiver_bound": True,
            "exact_materials_selected_field_bound": True,
            "exact_technical_art_surface_transport_bound": True,
            "selected_surface_only_texture_binding": True,
            "real_68_frame_current_world_rerendered": True,
            "weather_width_continuity_retained": True,
            "structural_runtime_submission_shape_unchanged": True,
            "environment_adoption_held": True,
        },
        "truth_boundary": "This result establishes only exact Materials-selected roughness binding and measured current-world raster/runtime deltas on the pinned proof host. It does not grant Art/QA preference, Runtime/device acceptance, Object source/material CANON, production readiness, or Environment mastery.",
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--contract", required=True)
    p.add_argument("--selected-png", required=True)
    p.add_argument("--ta-receipt", required=True)
    p.add_argument("--ta-surface", required=True)
    p.add_argument("--parent-report", required=True)
    p.add_argument("--parent-runtime", required=True)
    p.add_argument("--parent-rendered", required=True)
    p.add_argument("--runtime", required=True)
    p.add_argument("--candidate-rendered", required=True)
    p.add_argument("--environment-head", required=True)
    p.add_argument("--output", required=True)
    args = parser.parse_args()
    report = verify(args)
    print(json.dumps({"state": report["state"], "environment_head": report["environment_head"], "changed_pixels_gt_1lsb_total": report["real_scene_appearance_delta"]["changed_pixels_gt_1lsb_total"], "max_channel_delta_lsb": report["real_scene_appearance_delta"]["maximum_channel_delta_lsb"], "environment_adoption": report["environment_adoption"]}, sort_keys=True))


if __name__ == "__main__":
    main()
