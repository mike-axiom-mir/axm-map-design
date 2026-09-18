from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-nature-current-owner-art-direction-convergence/v0.1"
RESULT = "PASS_CURRENT_WORLD_NATURE_CURRENT_OWNER_ART_DIRECTION_CONVERGENCE__INDEPENDENT_QA_DEVICE_FINAL_ADOPTION_HELD"
RULE = "ART_DIRECTION_MAY_CONVERGE_WITH_AN_ALREADY_PROVEN_WORLD_RECEIVER_WITHOUT_RERENDER_ONLY_WHEN_EXACT_OWNER_CHAIN_SELECTED_REPRESENTATION_REVIEW_ARTIFACT_AND_DIRECTION_IDENTITY_MATCH__QA_DEVICE_FINAL_ADOPTION_DO_NOT_TRANSFER"
PRIOR_RESULT = "PASS_CURRENT_WORLD_NATURE_CURRENT_OWNER_RUNTIME_RIGID_CONTROL_CONVERGENCE__PREDECESSOR_SHADER_TRANSFER_HELD__VISUAL_DEVICE_FINAL_ADOPTION_HELD"
SELECTED_REPRESENTATION = "CURRENT_TA_RIGID_PARENT_NODE_TRANSFORM"
EXPECTED_SCOPE = ["Building", "Object", "Nature", "Weather", "Environment dressing"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_comment_fragment(body: str, fragment: str, label: str) -> None:
    if fragment not in body:
        raise AssertionError(f"Direction 052 handoff comment missing {label}")


def build_report(
    contract: dict[str, Any],
    prior: dict[str, Any],
    art_comment: dict[str, Any],
    *,
    claim_visual_qa_acceptance: bool = False,
    claim_environment_adoption: bool = False,
) -> dict[str, Any]:
    if contract.get("schema") != SCHEMA:
        raise AssertionError("Environment Art-convergence contract schema drift")
    if contract.get("expected_result") != RESULT or contract.get("reusable_rule") != RULE:
        raise AssertionError("Environment result/rule identity drift")
    if claim_visual_qa_acceptance:
        raise AssertionError("Art Direction convergence cannot claim independent Visual QA acceptance")
    if claim_environment_adoption:
        raise AssertionError("Art Direction convergence cannot authorize final Environment adoption")

    env = contract.get("environment", {})
    if env.get("predecessor_result") != PRIOR_RESULT:
        raise AssertionError("exact predecessor Environment Runtime-convergence result drift")
    if any(
        bool(env.get(key))
        for key in (
            "allow_scene_rerender",
            "allow_scene_mutation",
            "allow_tree_placement_change",
            "allow_reservation_change",
            "allow_environment_adoption",
        )
    ):
        raise AssertionError("Art convergence gate must remain non-rerendering, non-mutating and non-adopting")

    if prior.get("result") != PRIOR_RESULT:
        raise AssertionError("retained Environment Runtime convergence PASS missing")

    prior_inputs = prior.get("exact_inputs", {})
    owner = contract.get("exact_owner_chain", {})
    exact_keys = ("technical_art_head", "animation_head", "rigging_head", "uc_head")
    for key in exact_keys:
        if prior_inputs.get(key) != owner.get(key):
            raise AssertionError(f"exact current Nature owner identity mismatch: {key}")
    if prior_inputs.get("runtime_head") != owner.get("runtime_head"):
        raise AssertionError("Runtime head drift between Environment predecessor and Art direction")
    if prior_inputs.get("runtime_artifact_id") != owner.get("runtime_artifact_id"):
        raise AssertionError("Runtime artifact id drift between Environment predecessor and Art direction")
    if prior_inputs.get("runtime_artifact_sha256") != owner.get("runtime_artifact_sha256"):
        raise AssertionError("Runtime artifact digest drift between Environment predecessor and Art direction")

    decision = prior.get("decision", {})
    if decision.get("current_world_receiver_representation") != SELECTED_REPRESENTATION:
        raise AssertionError("Environment predecessor no longer selects the exact rigid-node receiver")
    if decision.get("existing_spatial_receive_ready") is not True:
        raise AssertionError("Environment predecessor lost exact target-receiver spatial readiness")
    for key in (
        "world_scene_changed",
        "tree_placement_changed",
        "reservation_changed",
        "predecessor_shader_transfer",
        "art_direction_acceptance",
        "visual_qa_acceptance",
        "runtime_target_device_acceptance",
        "environment_adoption",
        "canon",
    ):
        if decision.get(key) is not False:
            raise AssertionError(f"predecessor authority boundary drift: {key}")

    retained = prior.get("retained_world_evidence", {})
    if retained.get("weather_states") != 17:
        raise AssertionError("current world no longer retains exact 17 Weather states")
    if retained.get("multi_asset_scope") != EXPECTED_SCOPE:
        raise AssertionError("current multi-asset world scope drift")
    if float(retained.get("minimum_transport_adjusted_non_ground_margin_m", -1.0)) <= 0.0:
        raise AssertionError("current target receiver no longer has positive non-ground reservation margin")
    guards = retained.get("separation_guards_m", {})
    for key, value in guards.items():
        if float(value) <= 0.0:
            raise AssertionError(f"current-world separation guard is not positive: {key}")

    runtime_decision = prior.get("runtime_representation_decision", {})
    if runtime_decision.get("control") != SELECTED_REPRESENTATION:
        raise AssertionError("Runtime control representation drift")
    if runtime_decision.get("candidate") != owner.get("held_representation"):
        raise AssertionError("Runtime held shader-candidate identity drift")
    if runtime_decision.get("fresh_semantic_payload_saving_bytes_per_visible_sample") != 0:
        raise AssertionError("Direction 052 requires exact zero fresh Runtime representation saving")
    if runtime_decision.get("shader_transfer_authorized") is not False:
        raise AssertionError("predecessor shader transfer unexpectedly authorized")

    art = contract.get("art_direction", {})
    comment_id = int(art.get("map_pr_comment_id", -1))
    if int(art_comment.get("id", -2)) != comment_id:
        raise AssertionError("Direction 052 Map handoff comment identity drift")
    if art_comment.get("user", {}).get("login") != "mike-axiom-mir":
        raise AssertionError("Direction 052 handoff comment author identity drift")
    issue_url = str(art_comment.get("issue_url", ""))
    if not issue_url.endswith("/repos/mike-axiom-mir/axm-map-design/issues/53"):
        raise AssertionError("Direction 052 handoff comment is not anchored to Map PR #53")
    body = str(art_comment.get("body", ""))
    require_comment_fragment(body, owner["runtime_head"], "exact Runtime head")
    require_comment_fragment(body, str(owner["runtime_artifact_id"]), "exact Runtime artifact id")
    require_comment_fragment(body, owner["runtime_artifact_sha256"], "exact Runtime artifact digest")
    require_comment_fragment(body, art["coordination_commit"], "exact coordination commit")
    require_comment_fragment(body, art["packet_path"], "exact Direction 052 packet path")
    require_comment_fragment(body, "exact Nature current-owner fixed-view Art gate is now satisfied", "bounded Art PASS statement")
    require_comment_fragment(body, "rigid Technical-Art receiver already selected by Runtime", "selected representation statement")
    require_comment_fragment(body, "holds shader transfer", "shader hold statement")
    require_comment_fragment(body, "pending independent current-owner Visual QA", "independent QA hold statement")
    require_comment_fragment(body, "newer analytic-bridge Rigging lineage is outside Direction 052", "newer-owner non-transfer statement")

    if art.get("direction_id") != "052":
        raise AssertionError("Direction identity drift")
    if art.get("witness_indices") != [0, 5, 10, 15, 20, 25, 30, 35, 39]:
        raise AssertionError("Direction 052 witness identity drift")
    if art.get("aggregate_pixels_above_1_lsb") != 8156:
        raise AssertionError("Direction 052 aggregate raster count drift")
    if art.get("rendered_support_xor_pixels_each_pair") != 0:
        raise AssertionError("Direction 052 rendered-support identity drift")
    if art.get("runtime_fresh_semantic_saving_bytes_per_visible_sample") != 0:
        raise AssertionError("Direction 052 Runtime no-win premise drift")

    acceptance = contract.get("acceptance", {})
    for key in (
        "require_exact_environment_predecessor",
        "require_exact_owner_chain_match",
        "require_exact_runtime_artifact_match",
        "require_selected_rigid_representation",
        "require_shader_transfer_held",
        "require_exact_direction_052_comment_identity",
        "require_art_receiver_pass",
        "require_independent_qa_requested_not_transferred",
        "require_existing_world_evidence_retained",
    ):
        if acceptance.get(key) is not True:
            raise AssertionError(f"required Art convergence gate disabled: {key}")
    for key in (
        "allow_visual_qa_acceptance",
        "allow_target_device_acceptance",
        "allow_final_lookdev_acceptance",
        "allow_newer_analytic_bridge_transfer",
        "allow_environment_adoption",
        "allow_canon",
    ):
        if acceptance.get(key) is not False:
            raise AssertionError(f"authority inflation enabled: {key}")

    return {
        "schema": SCHEMA,
        "result": RESULT,
        "reusable_rule": RULE,
        "exact_inputs": {
            "environment_predecessor_head": env["predecessor_head"],
            "environment_predecessor_artifact_id": env["predecessor_artifact_id"],
            "environment_predecessor_artifact_sha256": env["predecessor_artifact_sha256"],
            "runtime_head": owner["runtime_head"],
            "runtime_artifact_id": owner["runtime_artifact_id"],
            "runtime_artifact_sha256": owner["runtime_artifact_sha256"],
            "technical_art_head": owner["technical_art_head"],
            "animation_head": owner["animation_head"],
            "rigging_head": owner["rigging_head"],
            "uc_head": owner["uc_head"],
            "art_direction_coordination_commit": art["coordination_commit"],
            "art_direction_packet_path": art["packet_path"],
            "art_direction_map_comment_id": comment_id,
        },
        "retained_world_evidence": retained,
        "art_direction_evidence": {
            "direction": art["direction_id"],
            "selected_representation": SELECTED_REPRESENTATION,
            "held_representation": owner["held_representation"],
            "witness_indices": art["witness_indices"],
            "aggregate_pixels_above_1_lsb": art["aggregate_pixels_above_1_lsb"],
            "rendered_support_xor_pixels_each_pair": art["rendered_support_xor_pixels_each_pair"],
            "runtime_fresh_semantic_saving_bytes_per_visible_sample": art["runtime_fresh_semantic_saving_bytes_per_visible_sample"],
            "art_direction_acceptance": True,
            "shader_transfer": False,
        },
        "decision": {
            "current_world_receiver_representation": SELECTED_REPRESENTATION,
            "existing_spatial_receive_ready": True,
            "world_scene_changed": False,
            "world_rerendered": False,
            "tree_placement_changed": False,
            "reservation_changed": False,
            "predecessor_shader_transfer": False,
            "art_direction_acceptance": True,
            "visual_qa_acceptance": False,
            "runtime_target_device_acceptance": False,
            "final_lookdev_acceptance": False,
            "newer_analytic_bridge_transfer": False,
            "environment_adoption": False,
            "canon": False,
        },
        "truth_boundary": (
            "PASS converges Direction 052 with the exact current-owner Nature receiver already selected by Runtime and already proven spatially compatible with the retained multi-asset Map world. "
            "The existing rigid Technical-Art receiver becomes the Art-accepted fixed-view reference for this exact lineage; the diagnostic shader remains held because it has no fresh Runtime budget win and no stated visual objective gain. "
            "No world rerender or scene mutation is required because the reviewed subject, owner chain, representation and retained Runtime artifact are unchanged. Independent Visual QA, target-device performance, final lookdev/normal-tangent quality, newer analytic-bridge owners, Environment adoption, CANON and production readiness remain separate."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--prior-environment-report", type=Path, required=True)
    parser.add_argument("--art-comment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--claim-visual-qa-acceptance", action="store_true")
    parser.add_argument("--claim-environment-adoption", action="store_true")
    args = parser.parse_args()

    report = build_report(
        read_json(args.contract),
        read_json(args.prior_environment_report),
        read_json(args.art_comment),
        claim_visual_qa_acceptance=args.claim_visual_qa_acceptance,
        claim_environment_adoption=args.claim_environment_adoption,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": report["result"],
        "receiver_representation": report["decision"]["current_world_receiver_representation"],
        "art_direction_acceptance": report["decision"]["art_direction_acceptance"],
        "visual_qa_acceptance": report["decision"]["visual_qa_acceptance"],
        "environment_adoption": report["decision"]["environment_adoption"],
    }, indent=2))


if __name__ == "__main__":
    main()
