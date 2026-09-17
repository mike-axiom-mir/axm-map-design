from __future__ import annotations

import argparse
import json
from pathlib import Path

PASS_STATE = "PASS_OBJECT_CURRENT_WORLD_OWNER_ANIMATION_WALLCLOCK_REBOUND_TO_TA_E085_RECEIVER"
SCHEMA = "axm.animation-object-current-world-wallclock-observation/v0.2"
TA_PARENT = "e085437f6cc958bbf7c5c6464578923d542962b0"
PREDECESSOR_EVIDENCE_HEAD = "c2695f654f9dd44312ca5d205eceb27f7c2680ee"
ANIMATION_HEAD = "c688936a84f80f292e43587c9d3386bd717f8178"
SEQUENCE_DIGEST = "0a3523cf792264f610881552fd2ebd438aabdfd05e30e92af9dbb33ded1fa2d3"
FRAME_RULE = "MATCH_ACTUAL_PIVOT_QUATERNIONS_ABOUT_THE_EXACT_TECHNICAL_ART_HOST_AXIS_THEN_MAP_HOST_ANGLE_BACK_TO_OWNER_CONVENTION__DO_NOT_ASSUME_SOURCE_EULER_X_EQUALS_HOST_EULER_X"


def verify(data: dict) -> None:
    assert data["schema"] == SCHEMA
    assert data["state"] == PASS_STATE
    assert data["technical_art_parent_head"] == TA_PARENT
    assert data["predecessor_animation_evidence_head"] == PREDECESSOR_EVIDENCE_HEAD
    assert data["animation_head"] == ANIMATION_HEAD
    assert data["sequence_digest"] == SEQUENCE_DIGEST
    assert data["receiver_frame_matching_rule"] == FRAME_RULE
    assert data["acceptance_pose_match_uses_host_quaternion_projected_to_exact_receiver_axis"] is True
    assert data["legacy_lid_rotation_deg_x_fields_are_host_euler_diagnostics_only"] is True
    assert float(data["duration_s"]) == 2.5
    assert float(data["sample_rate_hz"]) == 40.0
    assert int(data["sample_count"]) == 101
    assert data["source_motion_retimed"] is False
    assert data["source_keys_changed"] is False
    assert data["source_easing_changed"] is False
    assert data["source_amplitude_changed"] is False

    timed = data["timed_playback"]
    assert timed["observation_semantics"] == "FRAME_POST_DRAW_METADATA_ONLY_NO_VIEWPORT_READBACK_NO_DISK_WRITE"
    assert timed["natural_stop"] is True
    assert int(timed["phase_order_violations"]) == 0
    assert float(timed["max_owner_sample_error_deg"]) <= 0.0002
    # These two values are host diagnostic Euler/owner-angle summaries only;
    # exact membership above is quaternion/receiver-axis based on v0.2.
    assert float(timed["max_abs_lid_angle_deg"]) >= 99.0
    assert float(timed["min_latch_angle_deg"]) <= -49.9
    assert float(timed["endpoint_keeper_drift_m"]) <= 1e-6
    assert float(timed["endpoint_lever_drift_m"]) <= 1e-6
    assert int(timed["process_frame_count"]) >= 12
    assert int(timed["observed_owner_sample_count"]) >= 12
    assert timed["performance_authority"] is False
    observed = timed["observed_owner_sample_indices"]
    assert observed == sorted(set(observed))
    assert min(observed) >= 0 and max(observed) <= 100

    review = data["shaded_review_playback"]
    assert review["observation_semantics"] == "SECOND_REAL_ANIMATIONPLAYER_PLAYBACK_WITH_VIEWPORT_READBACK_AND_PNG_IO__TIMING_NOT_PERFORMANCE_EVIDENCE"
    assert review["camera_context"] == "path_eye"
    assert int(review["frame_count"]) >= 12
    assert len(review["frames"]) == int(review["frame_count"])
    assert review["capture_timing_accepted"] is False
    assert review["display_scanout_accepted"] is False
    assert int(review["frames"][0]["matched_owner_sample_index"]) == 0
    assert all(float(row.get("max_owner_sample_error_deg", 0.0)) <= 0.0002 for row in review["frames"][1:])

    for flag in (
        "vfx_adoption",
        "environment_adoption",
        "runtime_controller_accepted",
        "target_device_performance_accepted",
        "gameplay_accepted",
        "physics_accepted",
        "art_qa_accepted",
        "canon",
        "production_ready",
    ):
        assert data[flag] is False, flag


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.receipt).read_text())
    verify(data)
    print("PASS_OBJECT_CURRENT_WORLD_OWNER_ANIMATION_WALLCLOCK_SUCCESSOR_RECEIPT_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
