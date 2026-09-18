from __future__ import annotations

import argparse
import json
from pathlib import Path

RESULT = "HOLD_BUILDING_UTILITY_PANEL_PRODUCTION_SUCCESSOR_ENVIRONMENT_REBIND__INDEPENDENT_VISUAL_QA_PENDING"
RULE = "WORLD_ADOPTION_REQUIRES_EXACT_IDENTITY_CONVERGENCE_ACROSS_OWNER_ART_QA_RUNTIME_RECEIPTS__MISSING_ONE_GATE_HOLDS_REBIND_WITHOUT_DISCARDING_GREEN_EVIDENCE"

EXPECTED_MATERIALS_HEAD = "75bf511be8a89778ab40868707a68e80a210608a"
EXPECTED_PNG_SHA256 = "fdf56d0c0b2e65a181a23cb5db4067555f188cce28ef2479fd5a71c8e11d220c"
EXPECTED_RGBA8_SHA256 = "408a6eaecf99fa328487785f85d089c93da2b84c3ae9ead0bf6e1f8d2a0bdcad"
EXPECTED_ART_RESULT = "PASS_ART_DIRECTION_BUILDING_UTILITY_PANEL_PRODUCTION_SURFACE_SUCCESSOR_001_043"
EXPECTED_RUNTIME_HEAD = "cb4a4c7b4b8e77eba1195f0032d318d27588fd12"
EXPECTED_CURRENT_WORLD_HEAD = "595df99daf866b5e3dcaa4be87eeb650af637919"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(contract: dict) -> dict:
    assert contract["schema"] == "axm.environment-building-utility-panel-production-successor-adoption-readiness/v0.1"
    assert contract["expected_result"] == RESULT
    assert contract["reusable_rule"] == RULE

    env = contract["environment"]
    materials = contract["materials_owner"]
    art = contract["art_direction"]
    qa = contract["visual_qa"]
    runtime = contract["runtime"]
    promotion = contract["promotion"]

    assert env["current_world_head"] == EXPECTED_CURRENT_WORLD_HEAD
    assert env["building_vertices"] == 184
    assert env["building_triangles"] == 276
    assert env["building_surfaces"] == 5
    assert env["object_motion_sample_index"] == 40
    assert env["retained_current_world_frames_per_variant"] == 68

    assert materials["head"] == EXPECTED_MATERIALS_HEAD
    assert materials["workflow_result"] == "SUCCESS"
    assert materials["png_sha256"] == EXPECTED_PNG_SHA256
    assert materials["rgba8_sha256"] == EXPECTED_RGBA8_SHA256
    assert materials["frames_per_variant"] == 68
    assert materials["successor_visible_frames"] == 68
    assert materials["localization_minimum"] >= 0.98

    assert art["result"] == EXPECTED_ART_RESULT
    assert art["materials_head_reviewed"] == EXPECTED_MATERIALS_HEAD
    assert art["successor_png_sha256_reviewed"] == EXPECTED_PNG_SHA256
    assert art["accepted_for_direction"] is True
    assert art["final_adoption"] is False

    assert runtime["head"] == EXPECTED_RUNTIME_HEAD
    assert runtime["workflow_result"] == "SUCCESS"
    assert runtime["materials_head_rebound"] == EXPECTED_MATERIALS_HEAD
    assert runtime["successor_png_sha256_rebound"] == EXPECTED_PNG_SHA256
    assert runtime["rgba8_to_rgb8_pairs"] == 68
    assert runtime["changed_pixels"] == 0
    assert runtime["texture_full_mip_bytes_before"] - runtime["texture_full_mip_bytes_after"] == runtime["exact_texture_saving_bytes"] == 349525
    assert runtime["target_device_acceptance"] is False

    assert qa["materials_head_required"] == EXPECTED_MATERIALS_HEAD
    assert qa["successor_png_sha256_required"] == EXPECTED_PNG_SHA256
    if qa["accepted"]:
        assert qa["status"] == "PASS"
        assert isinstance(qa["review_id"], int) and qa["review_id"] > 0
        assert isinstance(qa["evidence_sha256"], str) and len(qa["evidence_sha256"]) == 64
        raise AssertionError("contract has a QA PASS receipt but this HOLD gate was not advanced to an Environment rebind review")
    else:
        assert qa["status"] == "PENDING"
        assert qa["review_id"] is None
        assert qa["evidence_sha256"] is None

    assert promotion["materials_owner_green"] is True
    assert promotion["art_direction_green"] is True
    assert promotion["independent_visual_qa_green"] is False
    assert promotion["runtime_representation_green"] is True
    assert promotion["runtime_target_device_green"] is False
    assert promotion["environment_rebind_authorized"] is False
    assert promotion["environment_adoption"] is False
    assert promotion["canon"] is False
    assert promotion["production_ready"] is False
    assert env["environment_adoption"] is False
    assert env["rebind_authorized"] is False

    return {
        "schema": "axm.environment-building-utility-panel-production-successor-adoption-readiness-report/v0.1",
        "result": RESULT,
        "reusable_rule": RULE,
        "exact_identity_convergence": {
            "materials_head": EXPECTED_MATERIALS_HEAD,
            "production_png_sha256": EXPECTED_PNG_SHA256,
            "materials_owner_green": True,
            "art_direction_green": True,
            "runtime_representation_green": True,
            "independent_visual_qa_green": False,
        },
        "retained_real_world_evidence": {
            "current_world_head": EXPECTED_CURRENT_WORLD_HEAD,
            "frames_per_material_variant": materials["frames_per_variant"],
            "production_successor_visible_frames": materials["successor_visible_frames"],
            "building": f'{env["building_vertices"]}v/{env["building_triangles"]}t/{env["building_surfaces"]}-surface',
            "articulated_object_sample_index": env["object_motion_sample_index"],
            "held_asset_types": ["Building", "Object", "Nature", "Weather", "Environment dressing"],
            "cameras": contract["held_world_identity"]["cameras"],
        },
        "remaining_gate": {
            "owner": "Visual Observer / QA",
            "scope": qa["required_scope"],
            "status": qa["status"],
        },
        "decision": {
            "environment_rebind_authorized": False,
            "environment_adoption": False,
            "preserve_checker_as_diagnostic_rollback": contract["held_world_identity"]["checker_retained_as_diagnostic_rollback"],
            "runtime_target_device_acceptance": False,
        },
        "truth_boundary": contract["truth_boundary"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    report = validate(load(args.contract))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(RESULT)
    print(json.dumps(report["exact_identity_convergence"], sort_keys=True))


if __name__ == "__main__":
    main()
