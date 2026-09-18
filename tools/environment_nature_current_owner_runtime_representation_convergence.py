from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-nature-current-owner-runtime-representation-convergence/v0.1"
RESULT = "PASS_CURRENT_WORLD_NATURE_CURRENT_OWNER_RUNTIME_RIGID_CONTROL_CONVERGENCE__PREDECESSOR_SHADER_TRANSFER_HELD__VISUAL_DEVICE_FINAL_ADOPTION_HELD"
RULE = "EXACT_RUNTIME_REPRESENTATION_DECISIONS_MAY_CONVERGE_WITH_AN_ALREADY_PROVEN_WORLD_RECEIVER_ONLY_WHEN_OWNER_CHAIN_TARGET_RECEIVER_AND_BUDGET_DECISION_MATCH__A_GREEN_RUNTIME_GATE_DOES_NOT_PROMOTE_A_HELD_SHADER_OR_TRANSFER_ART_QA_DEVICE_CANON_AUTHORITY"
PRIOR_RESULT = "PASS_CURRENT_WORLD_NATURE_NORTH_LOW_CURRENT_OWNER_TARGET_RECEIVER_ENVELOPE_FITS_EXISTING_EAST_REAR_RESERVATION__ART_RUNTIME_FINAL_ADOPTION_HELD"
RUNTIME_DECISION = "KEEP_CURRENT_TA_RIGID_NODE_CONTROL__HOLD_PREDECESSOR_SHADER_TRANSFER"
EXPECTED_SCOPE = ["Building", "Object", "Nature", "Weather", "Environment dressing"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(
    contract: dict[str, Any],
    target_envelope: dict[str, Any],
    prior: dict[str, Any],
    *,
    claim_shader_transfer: bool = False,
    claim_visual_acceptance: bool = False,
) -> dict[str, Any]:
    if contract.get("schema") != SCHEMA:
        raise AssertionError("Environment Runtime-convergence contract schema drift")
    if contract.get("expected_result") != RESULT or contract.get("reusable_rule") != RULE:
        raise AssertionError("Environment result/rule identity drift")
    if claim_shader_transfer:
        raise AssertionError("zero-win Runtime evidence cannot authorize predecessor shader transfer")
    if claim_visual_acceptance:
        raise AssertionError("Runtime representation convergence cannot claim Art Direction or Visual QA acceptance")

    env = contract.get("environment", {})
    if env.get("predecessor_result") != PRIOR_RESULT:
        raise AssertionError("exact predecessor Environment result drift")
    if any(
        bool(env.get(key))
        for key in (
            "allow_scene_mutation",
            "allow_tree_placement_change",
            "allow_reservation_change",
            "allow_environment_adoption",
        )
    ):
        raise AssertionError("Environment convergence gate must remain non-mutating and non-adopting")

    if prior.get("result") != PRIOR_RESULT:
        raise AssertionError("retained current target-receiver Environment PASS missing")
    decision = prior.get("decision", {})
    if decision.get("spatial_receive_ready_for_exact_current_target_receiver") is not True:
        raise AssertionError("current target receiver is not spatially receive-ready")
    if any(
        decision.get(key) is not False
        for key in (
            "world_scene_changed",
            "tree_placement_changed",
            "reservation_changed",
            "visual_acceptance",
            "runtime_target_device_acceptance",
            "environment_adoption",
            "canon",
        )
    ):
        raise AssertionError("predecessor spatial PASS authority boundary drift")

    current_world = prior.get("current_world", {})
    if current_world.get("weather_states_retained") != 17:
        raise AssertionError("current world no longer retains exact 17 Weather states")
    if current_world.get("multi_asset_scope") != EXPECTED_SCOPE:
        raise AssertionError("current multi-asset world scope drift")

    sweep = prior.get("target_receiver_sweep", {})
    if sweep.get("samples_evaluated") != 41 or sweep.get("receiver_nodes") != 12 or sweep.get("receiver_triangles") != 620:
        raise AssertionError("current target receiver structural/sample identity drift")
    if float(sweep.get("minimum_transport_adjusted_non_ground_margin_m", -1.0)) <= 0.0:
        raise AssertionError("current target receiver no longer has positive non-ground reservation margin")
    guards = prior.get("current_world_separation_guards", {})
    for key in (
        "readable_path_x_separation_m",
        "building_y_separation_m",
        "compact_east_nature_y_separation_m",
        "articulated_object_x_separation_m",
    ):
        if float(guards.get(key, -1.0)) <= 0.0:
            raise AssertionError(f"current-world separation guard is not positive: {key}")

    owner = contract.get("exact_owner_chain", {})
    fixture_owner = target_envelope.get("exact_owner_chain", {})
    prior_inputs = prior.get("exact_inputs", {})
    exact_pairs = {
        "animation_head": (owner.get("animation_head"), fixture_owner.get("animation_head"), prior_inputs.get("animation_head")),
        "rigging_head": (owner.get("rigging_head"), fixture_owner.get("rigging_head"), prior_inputs.get("rigging_head")),
        "uc_head": (owner.get("uc_head"), fixture_owner.get("uc_head"), prior_inputs.get("uc_head")),
        "technical_art_head": (owner.get("technical_art_head"), target_envelope.get("source_artifact", {}).get("technical_art_head"), prior_inputs.get("technical_art_head")),
    }
    for name, values in exact_pairs.items():
        if not values[0] or len(set(values)) != 1:
            raise AssertionError(f"exact current Nature owner identity mismatch: {name}")
    if owner.get("technical_art_artifact_id") != prior_inputs.get("target_artifact_id"):
        raise AssertionError("Technical Art artifact id drift")
    if owner.get("technical_art_artifact_sha256") != prior_inputs.get("target_artifact_sha256"):
        raise AssertionError("Technical Art artifact digest drift")

    runtime = contract.get("runtime_owner_evidence", {})
    if runtime.get("workflow_conclusion") != "success":
        raise AssertionError("current-owner Runtime workflow is not green")
    if runtime.get("contract_schema") != "axm.nature-runtime-current-owner-rigid-node-vs-shader/v0.1":
        raise AssertionError("Runtime owner contract schema drift")
    if runtime.get("technical_art_head", owner.get("technical_art_head")) != owner.get("technical_art_head"):
        raise AssertionError("Runtime Technical Art owner drift")
    for key in ("animation_head", "rigging_head", "uc_head"):
        runtime_value = runtime.get(key, owner.get(key))
        if runtime_value != owner.get(key):
            raise AssertionError(f"Runtime owner identity drift: {key}")
    if runtime.get("receiver_branch_id") != "north-low" or runtime.get("attachment_mode") != "DETACHED_DIAGNOSTIC_CHILD_SOCKET_ONLY":
        raise AssertionError("Runtime receiver authority identity drift")
    if runtime.get("receiver_nodes") != 12 or runtime.get("receiver_triangles") != 620:
        raise AssertionError("Runtime receiver structure drift")
    if runtime.get("endpoint_inclusive_samples") != 41 or runtime.get("visible_repeat_samples") != 40:
        raise AssertionError("Runtime receiver sample identity drift")
    if runtime.get("control_representation") != "CURRENT_TA_RIGID_PARENT_NODE_TRANSFORM":
        raise AssertionError("Runtime current control representation drift")
    if runtime.get("candidate_representation") != "CURRENT_OWNER_SHADER_REBIND_DIAGNOSTIC_ONLY":
        raise AssertionError("Runtime shader candidate authority drift")

    control_bytes = int(runtime.get("control_semantic_driver_bytes_per_visible_sample", -1))
    candidate_bytes = int(runtime.get("candidate_semantic_driver_bytes_per_visible_sample", -1))
    measured_saving = int(runtime.get("measured_semantic_payload_saving_bytes_per_visible_sample", -999))
    minimum_saving = int(runtime.get("minimum_semantic_payload_saving_bytes_per_visible_sample_for_transfer", -1))
    if control_bytes - candidate_bytes != measured_saving:
        raise AssertionError("Runtime semantic budget arithmetic drift")
    if measured_saving != 0 or minimum_saving != 1 or measured_saving >= minimum_saving:
        raise AssertionError("Runtime no-fresh-budget-win boundary drift")
    if runtime.get("decision") != RUNTIME_DECISION:
        raise AssertionError("Runtime decision no longer keeps current TA rigid control and holds shader transfer")

    acceptance = contract.get("acceptance", {})
    for key in (
        "require_exact_owner_chain_match_to_environment_target_receiver",
        "require_runtime_current_owner_gate_success",
        "require_zero_fresh_semantic_budget_win",
        "require_keep_current_ta_rigid_node_control",
        "require_predecessor_shader_transfer_held",
        "require_existing_environment_spatial_fit_retained",
    ):
        if acceptance.get(key) is not True:
            raise AssertionError(f"required convergence gate disabled: {key}")
    for key in (
        "allow_shader_transfer_claim",
        "allow_art_direction_transfer",
        "allow_visual_qa_transfer",
        "allow_target_device_acceptance_transfer",
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
            "runtime_head": runtime["head"],
            "runtime_workflow_run": runtime["workflow_run"],
            "runtime_artifact_id": runtime["artifact_id"],
            "runtime_artifact_sha256": runtime["artifact_sha256"],
            "technical_art_head": owner["technical_art_head"],
            "animation_head": owner["animation_head"],
            "rigging_head": owner["rigging_head"],
            "uc_head": owner["uc_head"],
        },
        "retained_world_evidence": {
            "weather_states": 17,
            "multi_asset_scope": EXPECTED_SCOPE,
            "minimum_transport_adjusted_non_ground_margin_m": sweep["minimum_transport_adjusted_non_ground_margin_m"],
            "minimum_transport_adjusted_ground_margin_m": sweep["minimum_transport_adjusted_ground_margin_m"],
            "separation_guards_m": guards,
        },
        "runtime_representation_decision": {
            "control": runtime["control_representation"],
            "candidate": runtime["candidate_representation"],
            "control_semantic_driver_bytes_per_visible_sample": control_bytes,
            "candidate_semantic_driver_bytes_per_visible_sample": candidate_bytes,
            "fresh_semantic_payload_saving_bytes_per_visible_sample": measured_saving,
            "minimum_saving_required_for_transfer": minimum_saving,
            "decision": runtime["decision"],
            "shader_transfer_authorized": False,
        },
        "decision": {
            "current_world_receiver_representation": "CURRENT_TA_RIGID_PARENT_NODE_TRANSFORM",
            "existing_spatial_receive_ready": True,
            "world_scene_changed": False,
            "tree_placement_changed": False,
            "reservation_changed": False,
            "predecessor_shader_transfer": False,
            "art_direction_acceptance": False,
            "visual_qa_acceptance": False,
            "runtime_target_device_acceptance": False,
            "environment_adoption": False,
            "canon": False,
        },
        "truth_boundary": (
            "PASS converges the exact current Nature owner chain and already-proven Environment target receiver with Runtime's exact current-owner representation decision. "
            "Runtime measured no fresh semantic payload saving (4 B control versus 4 B shader candidate per visible sample), so the current Technical-Art rigid parent-node transform remains the receiving representation and the predecessor shader transfer stays held. "
            "No scene rerender or world mutation was needed because this gate changes provenance/representation selection only. It does not transfer Art Direction, independent Visual QA, target-device performance, natural wind, connected attachment, collision/navigation, CANON or production readiness."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--target-envelope", type=Path, required=True)
    parser.add_argument("--prior-environment-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--claim-shader-transfer", action="store_true")
    parser.add_argument("--claim-visual-acceptance", action="store_true")
    args = parser.parse_args()

    report = build_report(
        read_json(args.contract),
        read_json(args.target_envelope),
        read_json(args.prior_environment_report),
        claim_shader_transfer=args.claim_shader_transfer,
        claim_visual_acceptance=args.claim_visual_acceptance,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": report["result"],
        "receiver_representation": report["decision"]["current_world_receiver_representation"],
        "shader_transfer": report["decision"]["predecessor_shader_transfer"],
        "minimum_non_ground_margin_m": report["retained_world_evidence"]["minimum_transport_adjusted_non_ground_margin_m"],
    }, indent=2))


if __name__ == "__main__":
    main()
