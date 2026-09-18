from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-building-utility-panel-clearance-successor-art-direction-convergence/v0.1"
RESULT = "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_CLEARANCE_SUCCESSOR_ART_DIRECTION_PROVENANCE_CONVERGENCE__NO_WORLD_RERENDER_REQUIRED__RUNTIME_CLOSE_RANGE_FINAL_ADOPTION_HELD"
RULE = "ART_DIRECTION_MAY_REBIND_TO_AN_ALREADY_PROVEN_WORLD_SUBJECT_WITHOUT_RERENDER_ONLY_WHEN_EXACT_OWNER_HEAD_SURFACE_BYTES_PLACEMENT_QA_AND_DIRECTION_PACKET_CONVERGE__DEVICE_CLOSE_RANGE_AND_FINAL_ADOPTION_AUTHORITY_DO_NOT_TRANSFER"
PRIOR_RESULT = "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_CLEARANCE_SUCCESSOR_QA_PROVENANCE_CONVERGENCE__NO_WORLD_RERENDER_REQUIRED__ART_RUNTIME_FINAL_ADOPTION_HELD"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Art Direction packet missing {label}: {needle}")


def validate(contract: dict[str, Any], prior: dict[str, Any], art_packet: str, art_head: str) -> dict[str, Any]:
    if contract.get("schema") != SCHEMA:
        raise AssertionError("contract schema drift")
    if contract.get("expected_result") != RESULT:
        raise AssertionError("expected result drift")
    if contract.get("reusable_rule") != RULE:
        raise AssertionError("reusable rule drift")

    env = contract["environment"]
    owner = contract["fresh_owner"]
    qa = contract["independent_visual_qa"]
    art = contract["fresh_art_direction"]
    promotion = contract["promotion"]

    if prior.get("expected_result") != PRIOR_RESULT:
        raise AssertionError("prior Environment review convergence result drift")
    if prior["fresh_owner"]["head"] != owner["head"]:
        raise AssertionError("fresh owner head no longer matches prior Environment convergence")
    if prior["fresh_owner"]["png_sha256"] != owner["png_sha256"]:
        raise AssertionError("production surface bytes drift from prior convergence")
    if prior["fresh_owner"]["front_successor_center_source_xyz_m"] != owner["front_successor_center_source_xyz_m"]:
        raise AssertionError("front receiver placement drift")
    if prior["fresh_owner"]["east_successor_center_source_xyz_m"] != owner["east_successor_center_source_xyz_m"]:
        raise AssertionError("east receiver placement drift")
    if prior["independent_visual_qa"]["review_id"] != qa["review_id"]:
        raise AssertionError("independent QA review identity drift")
    if prior["independent_visual_qa"]["review_commit_id"] != qa["review_commit_id"]:
        raise AssertionError("independent QA owner-head binding drift")
    if prior["promotion"]["independent_visual_qa_exact_head_green"] is not True:
        raise AssertionError("prior exact-head QA convergence is not green")
    if prior["promotion"]["art_direction_fresh_owner_exact_head_green"] is not False:
        raise AssertionError("prior gate already claimed fresh Art authority")
    if prior["promotion"]["environment_adoption"] is not False:
        raise AssertionError("prior gate already inflated Environment adoption")

    if art_head != art["coordination_commit"]:
        raise AssertionError(f"Art Direction checkout head drift: {art_head}")
    if art["materials_head_reviewed"] != owner["head"]:
        raise AssertionError("Art Direction does not review the exact current owner head")
    if art["environment_convergence_head_reviewed"] != env["prior_review_convergence_head"]:
        raise AssertionError("Art Direction does not review the exact Environment convergence head")
    if art["successor_png_sha256_reviewed"] != owner["png_sha256"]:
        raise AssertionError("Art Direction reviewed different production surface bytes")
    if art["fresh_owner_exact_head_green"] is not True:
        raise AssertionError("fresh Art exact-head PASS missing")
    if art["surface_retune_requested"] is not False:
        raise AssertionError("unexpected Art-directed surface retune")
    if art["final_environment_adoption"] is not False:
        raise AssertionError("Art Direction improperly grants final Environment adoption")

    required = (
        (art["result"], "Direction 049 result"),
        (owner["head"], "exact current Materials head"),
        (env["prior_review_convergence_head"], "exact Environment convergence head"),
        (owner["artifact_sha256"], "fresh owner artifact digest"),
        (owner["png_sha256"], "production PNG digest"),
        (owner["rgba8_sha256"], "decoded RGBA8 digest"),
        ("metallic `0.18`", "metallic scalar"),
        ("roughness `0.62`", "roughness scalar"),
        ("aggregate: `10,202` pixels", "placement delta aggregate"),
        ("aggregate `555,878`", "material activity aggregate"),
        ("`0 / 0` pixels", "front/east QA localization"),
        ("`689` pixels", "three-quarter QA localization"),
        ("Release the fresh-Art-head hold for Environment provenance convergence", "Environment handoff release"),
        ("Target-device Runtime acceptance", "Runtime hold"),
        ("arbitrary close-range/anti-banding review", "close-range hold"),
        ("final Environment adoption remain separate gates", "final adoption hold"),
    )
    for needle, label in required:
        require(art_packet, needle, label)

    if env["current_world_content_changed"] is not False or env["duplicate_world_rerender_required"] is not False:
        raise AssertionError("Art convergence must not manufacture world-content change")
    if promotion["latest_owner_provenance_converged"] is not True:
        raise AssertionError("owner provenance convergence missing")
    if promotion["independent_visual_qa_exact_head_green"] is not True:
        raise AssertionError("independent exact-head QA missing")
    if promotion["art_direction_fresh_owner_exact_head_green"] is not True:
        raise AssertionError("fresh exact-head Art convergence missing")
    for key in ("runtime_target_device_green", "close_range_surface_stack_green", "environment_adoption", "canon", "production_ready"):
        if promotion[key] is not False:
            raise AssertionError(f"authority inflation: {key}")

    return {
        "schema": "axm.environment-building-utility-panel-clearance-successor-art-direction-convergence-report/v0.1",
        "result": RESULT,
        "reusable_rule": RULE,
        "environment_prior_review_convergence_head": env["prior_review_convergence_head"],
        "fresh_owner_head": owner["head"],
        "fresh_art_direction_commit": art_head,
        "fresh_art_direction_result": art["result"],
        "production_png_sha256": owner["png_sha256"],
        "current_world_reused_without_rerender": True,
        "multi_asset_world_scope_retained": ["Building", "Object", "Nature", "Weather", "Environment dressing"],
        "owner_and_review_observations": {
            "placement_pixels_gt_1lsb": owner["placement_shift_pixels_gt_1lsb"],
            "material_activity_pixels_gt_1lsb": owner["successor_lit_vs_unshaded_pixels_gt_1lsb"],
            "qa_front_support_xor_pixels": qa["front_support_xor_pixels"],
            "qa_east_support_xor_pixels": qa["east_support_xor_pixels"],
            "qa_three_quarter_support_xor_pixels": qa["three_quarter_support_xor_pixels"],
        },
        "held_gates": {
            "target_device_runtime": True,
            "close_range_surface_stack": True,
            "environment_final_adoption": True,
            "canon": True,
            "production_ready": True,
        },
        "truth_boundary": contract["truth_boundary"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--prior-review-contract", type=Path, required=True)
    ap.add_argument("--art-direction-packet", type=Path, required=True)
    ap.add_argument("--art-direction-head", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    report = validate(
        load(args.contract),
        load(args.prior_review_contract),
        args.art_direction_packet.read_text(encoding="utf-8"),
        args.art_direction_head.read_text(encoding="utf-8").strip(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(RESULT)
    print(json.dumps(report["held_gates"], sort_keys=True))


if __name__ == "__main__":
    main()
