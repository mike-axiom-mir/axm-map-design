#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

PASS_STATE = "PASS_OBJECT_STATIC_BATCH_ELIGIBILITY_SUCCESSOR_CONTINUITY__HOLD_FRESH_RUNTIME_VISUAL_DEVICE"
PRIOR_RUNTIME_RESULT = "PASS_OBJECT_CURRENT_WORLD_STATIC_COMPONENT_BATCHING__HOLD_ART_QA_TARGET_DEVICE_FUTURE_ARTICULATION"
SUCCESSOR_ANIMATION_RESULT = "PASS_OBJECT_CURRENT_WORLD_OWNER_ANIMATION_WALLCLOCK_REBOUND_TO_TA_E085_RECEIVER"
STABLE_PLAN_KEYS = [
    "animation_head",
    "coordinate_conversion",
    "duration_s",
    "lid_component",
    "object_source_sha256",
    "sample_count",
    "sample_rate_hz",
    "samples",
    "sequence_digest",
    "sequence_id",
    "stations",
]


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path}")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def moving_closure(component_map: dict) -> list[str]:
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--prior-runtime-root", required=True)
    parser.add_argument("--successor-animation-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    contract = load_json(Path(args.contract))
    if contract.get("schema") != "axm.runtime-object-static-batching-successor-continuity/v0.1":
        fail("contract schema drift")

    prior_root = Path(args.prior_runtime_root)
    successor_root = Path(args.successor_animation_root)

    prior_summary = load_json(prior_root / "SUMMARY.json")
    successor_summary = load_json(successor_root / "SUMMARY.json")
    prior_map_path = prior_root / "ta-parent" / "object-rigid-component-map.json"
    successor_map_path = successor_root / "ta-parent" / "object-rigid-component-map.json"
    prior_plan_path = prior_root / "ta-parent" / "object-motion-receiver-plan.json"
    successor_plan_path = successor_root / "ta-parent" / "object-motion-receiver-plan.json"
    prior_map = load_json(prior_map_path)
    successor_map = load_json(successor_map_path)
    prior_plan = load_json(prior_plan_path)
    successor_plan = load_json(successor_plan_path)

    if prior_summary.get("exact_head") != contract["prior_runtime_head"]:
        fail("prior Runtime exact-head drift")
    if prior_summary.get("result") != PRIOR_RUNTIME_RESULT:
        fail("prior Runtime result drift")
    if successor_summary.get("exact_head") != contract["successor_animation_head"]:
        fail("successor Animation exact-head drift")
    if successor_summary.get("result") != SUCCESSOR_ANIMATION_RESULT:
        fail("successor Animation result drift")
    if successor_summary.get("technical_art_parent_head") != contract["successor_technical_art_head"]:
        fail("successor Technical Art head drift")
    if successor_summary.get("animation_head") != contract["owner_animation_head"]:
        fail("owner Animation head drift")
    if successor_summary.get("predecessor_animation_evidence_head") != prior_summary.get("animation_parent_head"):
        fail("Animation successor does not explicitly point back to the prior Runtime Animation parent")
    if successor_summary.get("runtime_controller_accepted", True):
        fail("Animation successor inflated Runtime controller authority")
    if successor_summary.get("target_device_performance_accepted", True):
        fail("Animation successor inflated target-device authority")

    prior_map_bytes = prior_map_path.read_bytes()
    successor_map_bytes = successor_map_path.read_bytes()
    prior_map_sha = sha256_bytes(prior_map_bytes)
    successor_map_sha = sha256_bytes(successor_map_bytes)
    expected_map_sha = contract["expected_component_map_sha256"]
    if prior_map_sha != expected_map_sha or successor_map_sha != expected_map_sha:
        fail("component-map byte identity drift")
    if prior_map_bytes != successor_map_bytes:
        fail("successor rigid component map differs from prior Runtime map")

    prior_subset = {key: prior_plan.get(key) for key in STABLE_PLAN_KEYS}
    successor_subset = {key: successor_plan.get(key) for key in STABLE_PLAN_KEYS}
    prior_subset_sha = canonical_sha(prior_subset)
    successor_subset_sha = canonical_sha(successor_subset)
    expected_subset_sha = contract["expected_stable_motion_subset_sha256"]
    if prior_subset_sha != expected_subset_sha or successor_subset_sha != expected_subset_sha:
        fail("stable owner-motion subset identity drift")
    if prior_subset != successor_subset:
        fail("successor owner-motion subset differs from prior Runtime motion plan")
    if successor_plan.get("sequence_digest") != contract["owner_sequence_digest"]:
        fail("owner sequence digest drift")

    components = successor_map.get("components", [])
    if len(components) != contract["expected_component_count"]:
        fail("component count drift")
    moving = moving_closure(successor_map)
    static_count = len(components) - len(moving)
    if len(moving) != contract["expected_moving_component_count"]:
        fail("moving-component classification drift")
    if static_count != contract["expected_static_component_count"]:
        fail("static-component classification drift")

    if prior_summary.get("moving_component_count") != len(moving):
        fail("prior Runtime moving count disagrees with successor classification")
    if prior_summary.get("static_component_count") != static_count:
        fail("prior Runtime static count disagrees with successor classification")
    if prior_summary.get("candidate_render_surface_count") != contract["prior_measured_candidate_render_surface_count"]:
        fail("prior measured candidate surface count drift")
    if prior_summary.get("summary", {}).get("min_draw_calls_saved") != contract["prior_measured_min_draw_calls_saved"]:
        fail("prior measured draw-call result drift")
    if -int(prior_summary.get("summary", {}).get("buffer_delta_min_bytes", 0)) != contract["prior_measured_buffer_bytes_saved"]:
        fail("prior measured buffer saving drift")

    receipt = {
        "schema": "axm.runtime-object-static-batching-successor-continuity-observation/v0.1",
        "state": PASS_STATE,
        "prior_runtime_head": contract["prior_runtime_head"],
        "prior_runtime_artifact_id": contract["prior_runtime_artifact_id"],
        "successor_animation_head": contract["successor_animation_head"],
        "successor_animation_artifact_id": contract["successor_animation_artifact_id"],
        "successor_technical_art_head": contract["successor_technical_art_head"],
        "owner_animation_head": contract["owner_animation_head"],
        "owner_sequence_digest": contract["owner_sequence_digest"],
        "component_map_sha256": successor_map_sha,
        "stable_motion_subset_sha256": successor_subset_sha,
        "component_count": len(components),
        "moving_component_count": len(moving),
        "moving_components": moving,
        "static_component_count": static_count,
        "prior_measured_candidate_render_surface_count": prior_summary["candidate_render_surface_count"],
        "prior_measured_min_draw_calls_saved": prior_summary["summary"]["min_draw_calls_saved"],
        "prior_measured_buffer_bytes_saved": -int(prior_summary["summary"]["buffer_delta_min_bytes"]),
        "prior_visual_tradeoff": prior_summary["visual_tradeoff"],
        "classification_reuse_authorized": True,
        "prior_runtime_counter_transfer_authorized": False,
        "prior_visual_acceptance_transfer_authorized": False,
        "target_device_performance_accepted": False,
        "future_arbitrary_articulation_accepted": False,
        "art_qa_accepted": False,
        "canon": False,
        "truth_boundary": "The exact 31-component rigid map and exact owner-motion subset are unchanged across the current Animation/Technical-Art successor, so the prior 7-moving/24-static classification may be reused as the next Runtime rebind starting point. Prior draw-call, buffer-memory and shaded A/B measurements remain historical evidence on the prior receiver and do not transfer by ancestry.",
    }
    Path(args.output).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(PASS_STATE)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
