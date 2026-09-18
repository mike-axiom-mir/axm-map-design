from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-building-utility-panel-clearance-successor-review-convergence/v0.1"
RESULT = "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_CLEARANCE_SUCCESSOR_QA_PROVENANCE_CONVERGENCE__NO_WORLD_RERENDER_REQUIRED__ART_RUNTIME_FINAL_ADOPTION_HELD"
RULE = "INDEPENDENT_REVIEW_MAY_REBIND_TO_AN_ALREADY_PROVEN_WORLD_SUBJECT_WITHOUT_RERENDER_ONLY_WHEN_EXACT_OWNER_HEAD_SEMANTIC_BYTES_PLACEMENT_AND_REVIEW_SCOPE_CONVERGE__OTHER_REVIEW_OR_DEVICE_AUTHORITY_DOES_NOT_TRANSFER"
PRIOR_CONVERGENCE_RESULT = "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_PRODUCTION_CLEARANCE_PROVENANCE_CONVERGENCE__NO_WORLD_RERENDER_REQUIRED__REVIEW_AUTHORITY_HELD"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_one(root: Path, name: str) -> Path:
    hits = list(root.rglob(name))
    if len(hits) != 1:
        raise AssertionError(f"expected exactly one {name} under {root}, got {len(hits)}")
    return hits[0]


def require_body(body: str, needle: str, label: str) -> None:
    if needle not in body:
        raise AssertionError(f"QA review missing {label}: {needle}")


def validate(
    contract: dict[str, Any],
    prior_contract: dict[str, Any],
    current_rebind: dict[str, Any],
    prior_artifact_root: Path,
    owner_artifact_root: Path,
    qa_review: dict[str, Any],
) -> dict[str, Any]:
    if contract.get("schema") != SCHEMA:
        raise AssertionError("contract schema drift")
    if contract.get("expected_result") != RESULT:
        raise AssertionError("expected result drift")
    if contract.get("reusable_rule") != RULE:
        raise AssertionError("reusable rule drift")

    env = contract["environment"]
    owner = contract["fresh_owner"]
    qa = contract["independent_visual_qa"]
    art = contract["prior_art_direction"]
    promotion = contract["promotion"]

    if prior_contract.get("expected_result") != PRIOR_CONVERGENCE_RESULT:
        raise AssertionError("prior Environment convergence result drift")
    if prior_contract["fresh_owner"]["materials_head"] != owner["head"]:
        raise AssertionError("prior Environment convergence does not target fresh owner head")
    if prior_contract["semantic_subject"]["png_sha256"] != owner["png_sha256"]:
        raise AssertionError("prior Environment convergence production bytes drift")
    if prior_contract["semantic_subject"]["front_successor_center_source_xyz_m"] != owner["front_successor_center_source_xyz_m"]:
        raise AssertionError("prior Environment front receiver placement drift")
    if prior_contract["semantic_subject"]["east_successor_center_source_xyz_m"] != owner["east_successor_center_source_xyz_m"]:
        raise AssertionError("prior Environment east receiver placement drift")
    if prior_contract["authority"]["current_world_content_changed"] is not False:
        raise AssertionError("prior convergence unexpectedly changed world content")
    if prior_contract["authority"]["art_direction_head_transfer"] is not False:
        raise AssertionError("prior convergence already transferred Art authority")
    if prior_contract["authority"]["visual_qa_head_transfer"] is not False:
        raise AssertionError("prior convergence already transferred QA authority")
    if prior_contract["authority"]["environment_adoption"] is not False:
        raise AssertionError("prior convergence inflated Environment adoption")

    prior_head = find_one(prior_artifact_root, "exact-head.txt").read_text(encoding="utf-8").strip()
    prior_report = load(find_one(prior_artifact_root, "report.json"))
    if prior_head != env["prior_provenance_convergence_head"]:
        raise AssertionError(f"retained Environment convergence head drift: {prior_head}")
    if prior_report.get("result") != PRIOR_CONVERGENCE_RESULT:
        raise AssertionError("retained Environment convergence artifact is not green")

    owner_head = find_one(owner_artifact_root, "exact-head.txt").read_text(encoding="utf-8").strip()
    if owner_head != owner["head"]:
        raise AssertionError(f"fresh owner artifact head drift: {owner_head}")
    owner_png = find_one(owner_artifact_root, "utility-panel-production-surface-001.png")
    if sha256(owner_png) != owner["png_sha256"]:
        raise AssertionError("fresh owner production PNG bytes drift")
    target = load(find_one(owner_artifact_root, "target_host_report.json"))
    if target.get("state") != "PASS_TARGET_HOST_BUILDING_UTILITY_PANEL_PRODUCTION_SURFACE_CLEARANCE_SUCCESSOR_REVIEW":
        raise AssertionError("fresh owner target-host clearance review is not green")
    if int(target.get("total_placement_shift_pixels_gt_1lsb", -1)) != int(owner["placement_shift_pixels_gt_1lsb"]):
        raise AssertionError("fresh owner placement observability drift")
    if int(target.get("total_lit_vs_unshaded_pixels_gt_1lsb", -1)) != int(owner["successor_lit_vs_unshaded_pixels_gt_1lsb"]):
        raise AssertionError("fresh owner material-activity observability drift")

    if int(qa_review.get("id", -1)) != int(qa["review_id"]):
        raise AssertionError("QA review identity drift")
    if qa_review.get("commit_id") != qa["review_commit_id"] or qa["review_commit_id"] != owner["head"]:
        raise AssertionError("QA review is not anchored to the fresh owner head")
    if qa_review.get("state") != qa["state"]:
        raise AssertionError("QA review state drift")
    if qa_review.get("submitted_at") != qa["submitted_at"]:
        raise AssertionError("QA review timestamp drift")
    body = str(qa_review.get("body", ""))
    for needle, label in (
        (owner["head"], "fresh owner head"),
        (str(owner["artifact_id"]), "owner artifact id"),
        (owner["artifact_sha256"], "owner artifact digest"),
        (owner["png_sha256"], "production PNG digest"),
        (qa["coherence_result"], "coherence verdict"),
        (qa["activity_result"], "activity verdict"),
        (qa["adoption_result"], "adoption hold"),
        ("aggregate `10,202`", "placement aggregate"),
        ("aggregate `555,878`", "material activity aggregate"),
        ("`0` support-XOR pixels in both", "front/east support localization"),
        ("`689` pixels", "three-quarter support localization"),
        ("does not transfer Environment/Map adoption, create a new Art Direction acceptance event", "authority non-transfer boundary"),
    ):
        require_body(body, needle, label)

    if current_rebind["materials_owner"]["png_sha256"] != owner["png_sha256"]:
        raise AssertionError("current Environment receiving surface bytes drift")
    if current_rebind["promotion"]["environment_adoption"] is not False:
        raise AssertionError("current Environment adoption boundary weakened")
    if art["successor_png_sha256_reviewed"] != owner["png_sha256"]:
        raise AssertionError("prior Art direction does not concern same semantic surface bytes")
    if art["materials_head_reviewed"] == owner["head"]:
        raise AssertionError("expected fresh Art exact-head gate to remain open")
    if art["fresh_owner_exact_head_reviewed"] is not False:
        raise AssertionError("fresh Art acceptance was fabricated")
    if art["final_adoption"] is not False:
        raise AssertionError("prior Art direction already granted final adoption")

    if env["current_world_content_changed"] is not False or env["duplicate_world_rerender_required"] is not False:
        raise AssertionError("review convergence must not manufacture a world-content change")
    if qa["environment_adoption_transferred"] is not False or qa["art_direction_acceptance_event_transferred"] is not False or qa["target_device_acceptance_transferred"] is not False:
        raise AssertionError("QA review authority was inflated")
    if promotion["latest_owner_provenance_converged"] is not True or promotion["independent_visual_qa_exact_head_green"] is not True:
        raise AssertionError("bounded convergence facts missing")
    if promotion["art_direction_fresh_owner_exact_head_green"] is not False:
        raise AssertionError("fresh Art gate must remain open")
    for key in ("runtime_target_device_green", "close_range_surface_stack_green", "environment_adoption", "canon", "production_ready"):
        if promotion[key] is not False:
            raise AssertionError(f"authority inflation: {key}")

    return {
        "schema": "axm.environment-building-utility-panel-clearance-successor-review-convergence-report/v0.1",
        "result": RESULT,
        "reusable_rule": RULE,
        "environment_prior_convergence_head": prior_head,
        "fresh_owner_head": owner_head,
        "production_png_sha256": owner["png_sha256"],
        "current_world_reused_without_rerender": True,
        "multi_asset_world_scope_retained": ["Building", "Object", "Nature", "Weather", "Environment dressing"],
        "visual_qa": {
            "review_id": qa["review_id"],
            "review_commit_id": qa_review["commit_id"],
            "coherence_result": qa["coherence_result"],
            "activity_result": qa["activity_result"],
            "placement_pixels_gt_1lsb": qa["aggregate_pixels_gt_1lsb"],
            "material_activity_pixels_gt_1lsb": owner["successor_lit_vs_unshaded_pixels_gt_1lsb"],
            "front_support_xor_pixels": qa["front_support_xor_pixels"],
            "east_support_xor_pixels": qa["east_support_xor_pixels"],
            "three_quarter_support_xor_pixels": qa["three_quarter_support_xor_pixels"],
        },
        "held_gates": {
            "fresh_art_direction_exact_head_acceptance": True,
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
    ap.add_argument("--prior-convergence-contract", type=Path, required=True)
    ap.add_argument("--current-rebind-contract", type=Path, required=True)
    ap.add_argument("--prior-convergence-root", type=Path, required=True)
    ap.add_argument("--fresh-owner-root", type=Path, required=True)
    ap.add_argument("--qa-review", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    report = validate(
        load(args.contract),
        load(args.prior_convergence_contract),
        load(args.current_rebind_contract),
        args.prior_convergence_root,
        args.fresh_owner_root,
        load(args.qa_review),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(RESULT)
    print(json.dumps(report["held_gates"], sort_keys=True))


if __name__ == "__main__":
    main()
