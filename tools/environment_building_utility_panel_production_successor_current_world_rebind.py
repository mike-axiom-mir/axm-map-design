from __future__ import annotations

import argparse
import json
from pathlib import Path

RESULT = "PASS_BUILDING_UTILITY_PANEL_PRODUCTION_SUCCESSOR_ENVIRONMENT_CURRENT_WORLD_REBIND__OWNER_ART_QA_RUNTIME_IDENTITIES_CONVERGED__FINAL_ADOPTION_HELD"
RULE = "ENVIRONMENT_REBIND_MAY_ACCEPT_AN_EXACT_REVIEWED_WORLD_SUCCESSOR_ONLY_WHEN_OWNER_ART_QA_AND_RUNTIME_IDENTITIES_CONVERGE__CURRENT_WORLD_RECEIVING_DOES_NOT_TRANSFER_TARGET_DEVICE_CLOSE_RANGE_OR_CANON_AUTHORITY"
MATERIALS_HEAD = "75bf511be8a89778ab40868707a68e80a210608a"
PNG_SHA256 = "fdf56d0c0b2e65a181a23cb5db4067555f188cce28ef2479fd5a71c8e11d220c"
OWNER_ARTIFACT_SHA256 = "75369c8d71ce5491eec2e058ecacc56948ca94662cc0b34d123b82273f2b4b8b"
QA_REVIEW_ID = 5244398076
ART_RESULT = "PASS_ART_DIRECTION_BUILDING_UTILITY_PANEL_PRODUCTION_SURFACE_SUCCESSOR_001_043"
QA_RESULT = "PASS_BUILDING_UTILITY_PANEL_PRODUCTION_SURFACE_CURRENT_WORLD_VISUAL_QA__LOCALIZED_STABLE_SUBORDINATE__68_PAIRS"
QA_DEPATTERN = "PASS_BUILDING_UTILITY_PANEL_PRODUCTION_SURFACE_DEPATTERNS_CHECKER__TWO_EXISTING_CAMERAS"
RUNTIME_HEAD = "cb4a4c7b4b8e77eba1195f0032d318d27588fd12"
RUNTIME_RUN = 35304987658


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--qa-review", type=Path, required=True)
    ap.add_argument("--art-packet", type=Path, required=True)
    ap.add_argument("--runtime-run", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    contract = load(args.contract)
    qa = load(args.qa_review)
    runtime_run = load(args.runtime_run)
    art_text = args.art_packet.read_text(encoding="utf-8")

    assert contract["schema"] == "axm.environment-building-utility-panel-production-successor-current-world-rebind/v0.1"
    assert contract["expected_result"] == RESULT
    assert contract["reusable_rule"] == RULE

    env = contract["environment"]
    materials = contract["materials_owner"]
    art = contract["art_direction"]
    visual_qa = contract["visual_qa"]
    runtime = contract["runtime"]
    held = contract["held_world_identity"]
    promotion = contract["promotion"]

    assert env["prior_current_world_head"] == "595df99daf866b5e3dcaa4be87eeb650af637919"
    assert env["direct_parent_head"] == "07f04aa9b5d1620907240acb12c97759fd7c77f4"
    assert (env["building_vertices"], env["building_triangles"], env["building_surfaces"]) == (184, 276, 5)
    assert env["object_motion_sample_index"] == 40
    assert env["retained_current_world_frames_per_variant"] == 68
    assert env["current_world_rebind"] is True
    assert env["environment_adoption"] is False

    assert materials["head"] == MATERIALS_HEAD
    assert materials["workflow_result"] == "SUCCESS"
    assert materials["artifact_sha256"] == OWNER_ARTIFACT_SHA256
    assert materials["png_sha256"] == PNG_SHA256
    assert materials["frames_per_variant"] == 68
    assert materials["successor_visible_frames"] == 68
    assert materials["scalar_to_successor_pixels_gt_1lsb"] == 182257
    assert materials["scalar_to_successor_max_delta_lsb"] == 10
    assert materials["localization_minimum"] >= 0.98

    assert art["result"] == ART_RESULT
    assert art["materials_head_reviewed"] == MATERIALS_HEAD
    assert art["successor_png_sha256_reviewed"] == PNG_SHA256
    assert art["accepted_for_direction"] is True
    assert art["final_adoption"] is False
    for token in (ART_RESULT, MATERIALS_HEAD, PNG_SHA256, "HOLD_FINAL_BUILDING_SURFACE_ADOPTION__INDEPENDENT_QA_ENVIRONMENT_TARGET_DEVICE_PENDING"):
        assert token in art_text, f"Art packet missing exact token: {token}"

    assert int(qa["id"]) == QA_REVIEW_ID
    assert qa["commit_id"] == MATERIALS_HEAD
    qa_body = str(qa.get("body", ""))
    for token in (QA_RESULT, QA_DEPATTERN, MATERIALS_HEAD, PNG_SHA256, OWNER_ARTIFACT_SHA256):
        assert token in qa_body, f"QA review missing exact token: {token}"
    assert visual_qa["review_id"] == QA_REVIEW_ID
    assert visual_qa["review_commit_id"] == MATERIALS_HEAD
    assert visual_qa["result"] == QA_RESULT
    assert visual_qa["depattern_result"] == QA_DEPATTERN
    assert visual_qa["reviewed_png_sha256"] == PNG_SHA256
    assert visual_qa["reviewed_artifact_sha256"] == OWNER_ARTIFACT_SHA256
    assert visual_qa["pairs_remeasured"] == 68
    assert visual_qa["scalar_to_successor_pixels_gt_1lsb"] == 182257
    assert visual_qa["scalar_to_successor_max_delta_lsb"] == 10
    assert visual_qa["close_range_acceptance"] is False
    assert visual_qa["final_adoption"] is False

    assert runtime["head"] == RUNTIME_HEAD
    assert runtime["workflow_run"] == RUNTIME_RUN
    assert runtime["workflow_result"] == "SUCCESS"
    assert runtime["materials_head_rebound"] == MATERIALS_HEAD
    assert runtime["successor_png_sha256_rebound"] == PNG_SHA256
    assert runtime["rgba8_to_rgb8_pairs"] == 68
    assert runtime["changed_pixels"] == 0
    assert runtime["texture_full_mip_bytes_before"] - runtime["texture_full_mip_bytes_after"] == runtime["exact_texture_saving_bytes"] == 349525
    assert runtime["target_device_acceptance"] is False
    assert int(runtime_run["id"]) == RUNTIME_RUN
    assert runtime_run["head_sha"] == RUNTIME_HEAD
    assert runtime_run["status"] == "completed"
    assert runtime_run["conclusion"] == "success"

    assert held["building"].startswith("184V_276T_5_SURFACE")
    assert held["object"] == "ARTICULATED_OBJECT_AT_OWNER_SAMPLE_40"
    assert held["nature"] == ["COMPACT_EAST_CURRENT_RECEIVER", "EAST_REAR_CURRENT_RECEIVER"]
    assert held["weather"] == "CURRENT_SOURCE_WIDTH_PRESENTATION"
    assert held["environment_dressing"] == "OBJECT_SERVICE_FRAME_REAR_EDGE_PLUS_20MM_SUCCESSOR"
    assert held["cameras"] == ["path_eye", "elevated_oblique"]
    assert held["checker_retained_as_diagnostic_rollback"] is True

    assert promotion["materials_owner_green"] is True
    assert promotion["art_direction_green"] is True
    assert promotion["independent_visual_qa_green"] is True
    assert promotion["runtime_representation_green"] is True
    assert promotion["environment_current_world_rebind"] is True
    assert promotion["runtime_target_device_green"] is False
    assert promotion["close_range_surface_stack_green"] is False
    assert promotion["environment_adoption"] is False
    assert promotion["canon"] is False
    assert promotion["production_ready"] is False

    report = {
        "schema": "axm.environment-building-utility-panel-production-successor-current-world-rebind-report/v0.1",
        "result": RESULT,
        "reusable_rule": RULE,
        "exact_identity_convergence": {
            "materials_head": MATERIALS_HEAD,
            "production_png_sha256": PNG_SHA256,
            "materials_owner_green": True,
            "art_direction_green": True,
            "independent_visual_qa_green": True,
            "runtime_representation_green": True,
        },
        "current_world_receive": {
            "environment_current_world_rebind": True,
            "prior_current_world_head": env["prior_current_world_head"],
            "frames_per_owner_variant": materials["frames_per_variant"],
            "held_asset_types": ["Building", "Object", "Nature", "Weather", "Environment dressing"],
            "cameras": held["cameras"],
            "checker_retained_as_diagnostic_rollback": True,
        },
        "remaining_holds": {
            "environment_adoption": False,
            "runtime_target_device_acceptance": False,
            "close_range_surface_stack_acceptance": False,
            "canon": False,
            "production_ready": False,
        },
        "truth_boundary": contract["truth_boundary"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(RESULT)
    print(json.dumps(report["exact_identity_convergence"], sort_keys=True))


if __name__ == "__main__":
    main()
