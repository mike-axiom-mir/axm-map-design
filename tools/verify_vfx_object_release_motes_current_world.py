#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

PASS_STATE = "PASS_CURRENT_WORLD_OBJECT_VFX_V2_RECEIVING_EVIDENCE"
PASS_DECISION = "PASS_V2_VISUALLY_OBSERVABLE_IN_EXISTING_CURRENT_WORLD_CONTEXT__HOLD_ART_QA_RUNTIME_AND_ADOPTION"
HOLD_DECISION = "HOLD_V2_NOT_OBSERVABLE_IN_EXISTING_CURRENT_WORLD_CAMERAS__DO_NOT_AMPLIFY_AUTOMATICALLY"


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def close(a: float, b: float, eps: float = 1e-6) -> bool:
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=eps)


def verify(receipt: dict, contract: dict) -> None:
    require(receipt.get("schema") == "axm.vfx-object-current-world-receiving-evidence/v0.1", "receipt schema drift")
    require(contract.get("schema") == "axm.vfx-object-current-world-receiving-contract/v0.1", "contract schema drift")
    require(receipt.get("state") == PASS_STATE, "current-world VFX evidence did not reach scoped PASS state")
    require(receipt.get("animation_parent_head") == contract["exact_animation_parent_head"], "Animation parent head drift")
    require(receipt.get("object_vfx_head") == contract["exact_object_vfx_head"], "Object VFX head drift")
    require(receipt.get("effect_id") == contract["effect_id"], "effect identity drift")
    require(receipt.get("owner_seed") == contract["owner_seed"], "owner seed drift")
    require(close(receipt.get("trigger_time_s", -1), contract["trigger_time_s"]), "trigger time drift")
    require(receipt.get("trigger_semantics") == contract["trigger_semantics"], "trigger semantics drift")
    require(receipt.get("effect_source_label") == contract["effect_semantics"], "effect semantics drift")
    require(receipt.get("parameter_sampling") == "DECORRELATED_INTEGER_MIX_V2_IRREGULAR_MARKS", "V2 sampler drift")

    for key in (
        "vfx_owner_replaced",
        "animation_timing_or_easing_modified",
        "weather_semantics_modified",
        "world_composition_modified",
        "gameplay_event_semantics_claimed",
        "physics_accepted",
        "gameplay_accepted",
        "runtime_performance_accepted",
        "art_direction_accepted",
        "visual_qa_accepted",
        "canon",
        "production_ready",
    ):
        require(receipt.get(key) is False, f"authority boundary inflated: {key}")
    require(contract.get("automatic_adoption") is False, "contract silently enables adoption")

    timed = receipt.get("timed_playback", {})
    require(timed.get("natural_stop") is True, "owner AnimationPlayer did not stop naturally")
    require(int(timed.get("process_frame_count", 0)) >= 10, "timed playback evidence too sparse")
    require(float(timed.get("max_owner_sample_error_deg", 999)) <= 0.0002, "owner Animation pose escaped exact sample envelope")
    require(float(timed.get("endpoint_keeper_drift_m", 999)) <= 1e-6, "keeper endpoint closure drift")
    require(float(timed.get("endpoint_lever_drift_m", 999)) <= 1e-6, "lever endpoint closure drift")
    require(timed.get("vfx_pre_trigger_inactive_seen") is True, "pre-trigger inactive VFX state missing")
    require(timed.get("vfx_active_window_seen") is True, "active VFX state missing")
    require(timed.get("vfx_post_effect_inactive_seen") is True, "post-effect inactive VFX state missing")
    require(int(timed.get("vfx_maximum_active_count", -1)) == int(contract["particle_count"]), "real playback did not reach exact owner mote count")
    require(timed.get("timing_is_target_device_performance_evidence") is False, "proof-host timing promoted to device performance")

    checks = receipt.get("static_ab_checks", [])
    contexts = contract["existing_camera_contexts"]
    times = [float(v) for v in contract["static_ab_times_s"]]
    require(len(checks) == len(contexts) * len(times), "static A/B check count drift")
    by_key = {(row["context_id"], round(float(row["time_s"]), 6)): row for row in checks}
    observed = set()
    for context in contexts:
        for time_s in times:
            key = (context, round(time_s, 6))
            require(key in by_key, f"missing static A/B sample: {key}")
            row = by_key[key]
            active = int(row.get("active_particle_count", -1))
            diff = row.get("diff", {})
            changed = int(diff.get("changed_pixels", -1))
            fraction = float(diff.get("changed_fraction", -1.0))
            require(changed >= 0 and 0.0 <= fraction <= 1.0, f"invalid raster metrics: {key}")
            if close(time_s, 0.2) or close(time_s, 0.8):
                require(active == 0, f"inactive mote closure count drift: {key}")
                require(changed <= int(contract["inactive_changed_pixels_max"]), f"inactive raster closure drift: {key}")
            else:
                require(fraction <= float(contract["maximum_active_changed_frame_fraction"]) + 1e-12, f"active VFX escaped bounded raster envelope: {key}")
                if changed > 0:
                    observed.add(context)
                if close(time_s, 0.4):
                    require(active == int(contract["particle_count"]), f"0.40 s owner mote count drift: {context}")

    receipt_observed = set(receipt.get("visually_observing_existing_camera_contexts", []))
    require(receipt_observed == observed, "camera observability summary does not match retained A/B evidence")
    expected_decision = PASS_DECISION if observed else HOLD_DECISION
    require(receipt.get("decision") == expected_decision, "observability decision does not match evidence")

    require("physical" in receipt.get("truth_boundary", "").lower(), "truth boundary missing physical non-claim")
    require("not" in receipt.get("visual_truth_boundary", "").lower(), "visual hold boundary missing")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--contract", required=True)
    args = parser.parse_args()
    receipt = load(args.receipt)
    contract = load(args.contract)
    verify(receipt, contract)
    print(PASS_STATE)
    print(receipt["decision"])


if __name__ == "__main__":
    main()
