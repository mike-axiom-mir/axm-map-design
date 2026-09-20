#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

TOOL_ID = "axm.map.object.receiver.packet"
REQUEST_SCHEMA = "axm.map-object-receiver-tool-request/v0.1"
PACKET_SCHEMA = "axm.map-object-receiver-packet/v0.1"
RECEIPT_SCHEMA = "axm.map-object-receiver-tool-receipt/v0.1"
PASS_STATE = "PASS_MAP_OBJECT_RECEIVER_PACKET"

EXPECTED = {
    "component_map_sha256": "c94511765180804e1195618475ef80a77b07721065526afdb90ae0ab72d3cf53",
    "motion_plan_sha256": "efab1b6409048d3763ba1a53ada10044dcc9f74592c7d6aae6af76d0af6f667e",
    "environment_report_sha256": "f0f12dcbc4a88c15e426573dd23e49c8b8cf7ad57d4844693563e66989f90380",
    "runtime_receipt_sha256": "5cf4e2c98eb49060e94b02201ab47ecb66d32e208878a8b878fde6e497ec9bdf",
    "map_technical_art_head": "fc567fd6dd061ccb5e8232bd17ee0af3d2e064b7",
    "map_animation_head": "51f1c0002f58f138911cce7d95a30add9a1e03af",
    "object_animation_head": "86bdbe9771bf9eb1bc92bd4160442941763fab1d",
    "object_technical_art_head": "b9848c62b2adde84e9e0afc219088113216799d6",
    "object_source_head": "d3fa10a270faae7925811f44f03381fe5c5d0215",
    "sequence_digest": "0a3523cf792264f610881552fd2ebd438aabdfd05e30e92af9dbb33ded1fa2d3",
    "environment_core_head": "04c7f27a749c634daef4bde98dc330fb83e13f91",
    "environment_review_head": "fe30c647933107aa4c535590a4238de009156842",
    "runtime_head": "3c675de8a6aacf0e318312a985168dc4d6362c78",
}
EXPECTED_REQUEST_KEYS = {"schema", "tool_id", "sample_index", "service_frame", "static_batching"}

HOLDS = [
    "Object final Art Direction and independent Visual QA remain open",
    "Environment production adoption remains false",
    "target-device CPU/GPU/FPS/VRAM/thermal/battery acceptance remains open",
    "future owner sequences that move a currently-static component require debatch/rebind and fresh Runtime evidence",
    "gameplay, physics, collision/navigation, CANON and production readiness remain open",
]
NONCLAIMS = [
    "No source geometry or motion authorship",
    "No automatic Environment adoption",
    "No final visual or art-direction acceptance",
    "No target-device performance certification",
    "No arbitrary future-articulation safety",
    "No gameplay, physics, collision/navigation or CANON acceptance",
]

def fail(message: str) -> None:
    raise SystemExit(message)

def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path}")
    return value

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())

def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))

def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

def moving_closure(component_map: dict[str, Any]) -> list[str]:
    components = component_map.get("components")
    required = component_map.get("required_moving_components")
    if not isinstance(components, list) or not isinstance(required, list):
        fail("component map missing components or required_moving_components")
    moving = {str(name) for name in required}
    changed = True
    while changed:
        changed = False
        for raw in components:
            if not isinstance(raw, dict):
                fail("component entry is not an object")
            name = str(raw.get("name", ""))
            parent = raw.get("parent")
            if parent is not None and str(parent) in moving and name not in moving:
                moving.add(name)
                changed = True
    return sorted(moving)

def validate_request(request: dict[str, Any]) -> None:
    keys = set(request)
    if keys != EXPECTED_REQUEST_KEYS:
        fail(f"request fields drift: expected {sorted(EXPECTED_REQUEST_KEYS)}, got {sorted(keys)}")
    if request.get("schema") != REQUEST_SCHEMA:
        fail("request schema drift")
    if request.get("tool_id") != TOOL_ID:
        fail("tool id drift")
    sample = request.get("sample_index")
    if isinstance(sample, bool) or not isinstance(sample, int) or not (0 <= sample <= 100):
        fail("sample_index must be an integer from 0 through 100")
    if request.get("service_frame") not in {"historical", "successor_20mm"}:
        fail("unsupported service_frame")
    if request.get("static_batching") not in {"none", "current_sequence_static_24"}:
        fail("unsupported static_batching")

def validate_evidence(component_map: dict[str, Any], plan: dict[str, Any], env: dict[str, Any], runtime: dict[str, Any]) -> tuple[list[str], list[str]]:
    if component_map.get("schema") != "axm.environment-object-rigid-component-map/v0.1":
        fail("component-map schema drift")
    if component_map.get("result") != "PASS_EXACT_OBJECT_TA_RIGID_COMPONENT_MAP_FOR_CURRENT_WORLD_RECEIVER":
        fail("component-map result is not green")
    if component_map.get("technical_art_head") != EXPECTED["object_technical_art_head"]:
        fail("component-map Object Technical Art provenance drift")
    if component_map.get("object_source_head") != EXPECTED["object_source_head"]:
        fail("component-map Object source provenance drift")
    if int(component_map.get("triangles", -1)) != 812:
        fail("component-map triangle identity drift")
    components = component_map.get("components", [])
    if not isinstance(components, list) or len(components) != 31:
        fail("component-map component count drift")

    if plan.get("schema") != "axm.environment-object-motion-receiver-plan/v0.1":
        fail("motion-plan schema drift")
    if plan.get("result") != "PASS_OBJECT_ANIMATION_OWNER_SAMPLES_ADAPTED_TO_CURRENT_WORLD_RIGID_RECEIVER":
        fail("motion-plan result is not green")
    if plan.get("object_technical_art_head") != EXPECTED["object_technical_art_head"]:
        fail("motion-plan Object Technical Art provenance drift")
    if plan.get("animation_head") != EXPECTED["object_animation_head"]:
        fail("motion-plan owner Animation provenance drift")
    if plan.get("sequence_digest") != EXPECTED["sequence_digest"]:
        fail("motion-plan sequence digest drift")
    if int(plan.get("sample_count", -1)) != 101 or float(plan.get("sample_rate_hz", -1)) != 40.0 or float(plan.get("duration_s", -1)) != 2.5:
        fail("motion-plan timing identity drift")
    samples = plan.get("samples", [])
    if not isinstance(samples, list) or len(samples) != 101 or [int(row.get("index", -1)) for row in samples] != list(range(101)):
        fail("motion-plan sample identity drift")

    if env.get("schema") != "axm.environment-object-articulated-service-clearance/v0.1":
        fail("Environment report schema drift")
    if env.get("result") != "PASS_CURRENT_WORLD_OBJECT_ARTICULATED_SERVICE_CLEARANCE_SUCCESSOR__20MM_REAR_DRESSING_EXPANSION_RESTORES_60MM_SWEEP_CLEARANCE__ADOPTION_HELD":
        fail("Environment clearance result is not green")
    if env.get("technical_art_parent_head") != EXPECTED["map_technical_art_head"]:
        fail("Environment Map Technical Art provenance drift")
    if env.get("object_technical_art_head") != EXPECTED["object_technical_art_head"]:
        fail("Environment Object Technical Art provenance drift")
    if env.get("animation_head") != EXPECTED["object_animation_head"] or env.get("sequence_digest") != EXPECTED["sequence_digest"]:
        fail("Environment owner Animation identity drift")
    decision = env.get("decision", {})
    if not isinstance(decision, dict) or decision.get("environment_adoption") is not False or decision.get("runtime_acceptance_required") is not True or decision.get("art_qa_acceptance_required") is not True:
        fail("Environment authority boundary drift")

    if runtime.get("schema") != "axm.runtime-object-static-batching-successor-rebind-observation/v0.1":
        fail("Runtime receipt schema drift")
    if runtime.get("state") != "PASS_OBJECT_STATIC_BATCHING_SUCCESSOR_REBIND__HOLD_ART_QA_TARGET_DEVICE_FUTURE_ARTICULATION":
        fail("Runtime receipt is not green")
    if runtime.get("animation_parent_head") != EXPECTED["map_animation_head"]:
        fail("Runtime Map Animation provenance drift")
    if runtime.get("technical_art_parent_head") != EXPECTED["map_technical_art_head"]:
        fail("Runtime Map Technical Art provenance drift")
    if runtime.get("component_nodes_preserved") is not True:
        fail("Runtime semantic component nodes were not preserved")
    if runtime.get("target_device_performance_accepted") is not False or runtime.get("art_qa_accepted") is not False or runtime.get("future_arbitrary_articulation_accepted") is not False:
        fail("Runtime authority boundary drift")
    if int(runtime.get("component_count", -1)) != 31 or int(runtime.get("moving_component_count", -1)) != 7 or int(runtime.get("static_component_count", -1)) != 24:
        fail("Runtime moving/static classification drift")

    moving = moving_closure(component_map)
    static = sorted(str(row["name"]) for row in components if str(row["name"]) not in set(moving))
    if len(moving) != 7 or len(static) != 24:
        fail("component map no longer yields the verified 7-moving / 24-static closure")
    return moving, static

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--component-map", required=True)
    ap.add_argument("--motion-plan", required=True)
    ap.add_argument("--environment-report", required=True)
    ap.add_argument("--runtime-receipt", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    exact_head = git(root, "rev-parse", "HEAD")
    dirty = git(root, "status", "--porcelain", "--untracked-files=no")
    if dirty:
        fail("tracked repository state is dirty; deterministic receipt would be ambiguous")

    request_path = Path(args.request).resolve()
    component_path = Path(args.component_map).resolve()
    plan_path = Path(args.motion_plan).resolve()
    env_path = Path(args.environment_report).resolve()
    runtime_path = Path(args.runtime_receipt).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        fail("output directory already exists; refusing silent replacement")

    actual_hashes = {
        "component_map_sha256": sha256_file(component_path),
        "motion_plan_sha256": sha256_file(plan_path),
        "environment_report_sha256": sha256_file(env_path),
        "runtime_receipt_sha256": sha256_file(runtime_path),
    }
    for key, actual in actual_hashes.items():
        if actual != EXPECTED[key]:
            fail(f"{key} mismatch: {actual} != {EXPECTED[key]}")

    request = read_json(request_path)
    validate_request(request)
    component_map = read_json(component_path)
    plan = read_json(plan_path)
    env = read_json(env_path)
    runtime = read_json(runtime_path)
    moving, static = validate_evidence(component_map, plan, env, runtime)

    sample = plan["samples"][request["sample_index"]]
    sweep = env.get("articulated_sweep", {})
    if request["service_frame"] == "historical":
        frame = {
            "mode": "historical",
            "outer_footprint_world_xy_m": sweep["old_outer_footprint_world_xy_m"],
            "inner_footprint_world_xy_m": sweep["old_inner_footprint_world_xy_m"],
            "minimum_inner_clearance_m": sweep["predecessor_minimum_inner_clearance_m"],
            "meets_60mm_contract": False,
        }
    else:
        frame = {
            "mode": "successor_20mm",
            "outer_footprint_world_xy_m": sweep["candidate_outer_footprint_world_xy_m"],
            "inner_footprint_world_xy_m": sweep["candidate_inner_footprint_world_xy_m"],
            "rear_outer_edge_expansion_m": sweep["rear_outer_edge_expansion_m"],
            "minimum_inner_clearance_m": sweep["candidate_minimum_inner_clearance_m"],
            "meets_60mm_contract": float(sweep["candidate_minimum_inner_clearance_m"]) >= 0.06,
        }

    if request["static_batching"] == "none":
        rendering = {
            "mode": "none",
            "semantic_component_count": 31,
            "render_surface_count": runtime["control_component_surface_instances"],
            "triangles": runtime["control_triangles"],
            "fresh_runtime_measurement_required_for_other_hosts": True,
        }
    else:
        rendering = {
            "mode": "current_sequence_static_24",
            "semantic_component_count": 31,
            "moving_component_count": 7,
            "static_component_count": 24,
            "static_batch_surface_count": runtime["static_batch_surface_count"],
            "render_surface_count": runtime["candidate_render_surface_count"],
            "triangles": runtime["candidate_triangles"],
            "proof_host_min_draw_calls_saved": runtime["summary"]["min_draw_calls_saved"],
            "proof_host_buffer_delta_min_bytes": runtime["summary"]["buffer_delta_min_bytes"],
            "proof_host_visual_changed_pixels": runtime["summary"]["total_changed_pixels_across_pairs"],
            "future_arbitrary_articulation_accepted": False,
            "target_device_performance_accepted": False,
        }

    packet = {
        "schema": PACKET_SCHEMA,
        "tool_id": TOOL_ID,
        "implementation_head": exact_head,
        "asset_id": "source:object:modular-equipment-case-001",
        "selection": {
            "sample_index": int(sample["index"]),
            "time_s": float(sample["time_s"]),
            "lid_target_rotation_deg_x": float(sample["lid_target_rotation_deg_x"]),
            "latch_target_rotation_deg_x": float(sample["latch_target_rotation_deg_x"]),
        },
        "component_hierarchy": {
            "component_count": 31,
            "triangle_count": 812,
            "moving_components": moving,
            "static_components": static,
            "components": component_map["components"],
        },
        "environment_service_frame": frame,
        "runtime_representation": rendering,
        "dependencies": {
            "map_technical_art_head": EXPECTED["map_technical_art_head"],
            "map_animation_head": EXPECTED["map_animation_head"],
            "object_animation_head": EXPECTED["object_animation_head"],
            "object_technical_art_head": EXPECTED["object_technical_art_head"],
            "object_source_head": EXPECTED["object_source_head"],
            "environment_core_head": EXPECTED["environment_core_head"],
            "environment_review_head": EXPECTED["environment_review_head"],
            "runtime_head": EXPECTED["runtime_head"],
            "sequence_digest": EXPECTED["sequence_digest"],
        },
        "authority": {
            "environment_adoption": False,
            "art_qa_acceptance": False,
            "target_device_performance_accepted": False,
            "future_arbitrary_articulation_accepted": False,
            "gameplay_accepted": False,
            "canon": False,
        },
        "holds": HOLDS,
        "nonclaims": NONCLAIMS,
    }

    out.mkdir(parents=True)
    packet_path = out / "receiver-packet.json"
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest_path = root / "tooling" / "map-object-receiver-packet.manifest.json"
    script_path = Path(__file__).resolve()
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "result": PASS_STATE,
        "tool_id": TOOL_ID,
        "exact_tool_head": exact_head,
        "request_sha256": sha256_file(request_path),
        "request_canonical_sha256": canonical_sha(request),
        "packet_sha256": sha256_file(packet_path),
        "manifest_sha256": sha256_file(manifest_path),
        "entrypoint_sha256": sha256_file(script_path),
        "dependency_sha256": actual_hashes,
        "evidence_scopes": ["structural"],
        "layers": read_json(manifest_path).get("layers", {}),
        "holds": HOLDS,
        "nonclaims": NONCLAIMS,
        "authority": packet["authority"],
        "truth_boundary": "This receipt proves deterministic assembly and validation of one exact current Map/Object receiver packet from already-proven dependency evidence. It does not transfer the dependencies' visual or proof-host Runtime observations into final Art, Environment adoption, target-device performance, gameplay, physics or production acceptance.",
    }
    receipt_path = out / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(PASS_STATE)
    print(json.dumps({"exact_tool_head": exact_head, "sample_index": request["sample_index"], "service_frame": request["service_frame"], "static_batching": request["static_batching"], "packet_sha256": receipt["packet_sha256"]}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
