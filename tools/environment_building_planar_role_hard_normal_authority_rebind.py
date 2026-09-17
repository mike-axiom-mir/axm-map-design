#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PASS = "PASS_CURRENT_WORLD_BUILDING_312_CONSUMER_REBOUND_TO_SOURCE_HARD_NORMAL_AUTHORITY"
HOLD = "HOLD_DEFAULT_ADOPTION__TECHNICAL_ART_TRANSPORT_RUNTIME_TARGET_DEVICE_AND_INDEPENDENT_VISUAL_GATES_REMAIN_SEPARATE"
PRIOR = "9c1fb7b1a53f06a6a8c3c72ce3d1c3e5e1354d3f"
ROLLBACK = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
HARD_SURFACE_HEAD = "7b86b1a9da1ef8dc670ca01cf4918728e68ece92"
HARD_SURFACE_BLOB = "826cc61a2e9fc172db5025f5b3ace6f566d5125a"
HARD_SURFACE_CANON = "607cd4a26d4a53da41d350bce056b2d6cb57fd5f05b750c200ade45cd4a9a9c9"
CONSUMER = "map-consumer:service-pavilion-001:planar-role-post-normal-indexed-001"
QHEAD = "7dfb1153dc5f80bcbf1b48803f044236d4ebb030"
QSHA = "7d9e0babf605e31ecb3e4edc92d06bd5460cf52a27f02ccbf32bbae44464688f"
ROLE = {
    "frame_galvanized": 200,
    "infill_coating": 24,
    "roof_membrane": 36,
    "slab_mineral": 36,
    "utility_panel_ochre": 16,
}


def load(path: Path):
    return json.loads(path.read_text())


def canonical_sha(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def frame_manifest(root: Path):
    rows = []
    for path in sorted(root.glob("atmosphere-width-*.png")):
        rows.append({"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    if len(rows) != 68:
        raise ValueError(f"expected 68 retained current-world frames, got {len(rows)}")
    aggregate = hashlib.sha256("\n".join(f"{r['name']}:{r['sha256']}:{r['bytes']}" for r in rows).encode()).hexdigest()
    return rows, aggregate


def verify(contract, consumer_identity, quotient_contract, hard_surface_policy, prior, runtime, runtime_report, frames_root: Path, exact_head: str):
    if contract.get("schema") != "axm.environment-building-planar-role-hard-normal-authority-rebind/v0.1":
        raise ValueError("contract schema drift")
    if contract.get("owner") != "Map Environment / World Art" or contract.get("asset_id") != "service-pavilion-001":
        raise ValueError("contract ownership/asset drift")
    if contract.get("consumer_representation_id") != CONSUMER or contract.get("prior_environment_head") != PRIOR or contract.get("active_segmented_rollback_head") != ROLLBACK:
        raise ValueError("contract lineage drift")

    authority = contract.get("hard_surface_authority", {})
    if authority.get("repository") != "mike-axiom-mir/axm-building-design" or authority.get("pr") != 14 or authority.get("head") != HARD_SURFACE_HEAD:
        raise ValueError("Hard Surface authority pin drift")
    if authority.get("policy_path") != "assets/service_pavilion_001_planar_role_hard_normal_authority_policy.json" or authority.get("policy_git_blob_sha") != HARD_SURFACE_BLOB or authority.get("policy_canonical_sha256") != HARD_SURFACE_CANON:
        raise ValueError("Hard Surface authority policy identity drift")

    source = contract.get("source_authority_boundary", {})
    expected_source = {
        "source_intent_render_classes": 604,
        "derived_role_position_groups": 312,
        "source_render_vertex_identities_removed": 292,
        "groups_crossing_source_hard_normal_boundaries": 188,
        "dropped_source_attributes": ["EXACT_CARDINAL_HARD_NORMAL"],
        "source_partition_status": "SOURCE_AUTHORIZED_RENDER_EQUIVALENCE",
        "derived_partition_status": "DERIVED_ATTRIBUTE_DROPPING_PARTITION_NOT_SOURCE_EQUIVALENT",
    }
    if source != expected_source:
        raise ValueError("declared source authority boundary drift")

    consumer = contract.get("consumer_declaration", {})
    required_consumer = {
        "derivation_kind": "GODOT_POST_NORMAL_PER_MATERIAL_SURFACE_INDEX",
        "stored_vertices": 312,
        "indices": 1008,
        "triangles": 336,
        "material_surfaces": 5,
        "consumer_generated_normal_index_domain": True,
        "source_hard_normal_identity_preserved": False,
        "consumer_generated_normals_are_source_normals": False,
        "source_owner_equivalence_identity_claimed": False,
        "source_collapse_authorized": False,
        "environment_adoption": False,
        "review_target_only": True,
    }
    if consumer != required_consumer:
        raise ValueError("consumer declaration drift or authority inflation")
    if contract.get("required_independent_gates") != {"technical_art_transport": True, "runtime_target_device": True, "art_direction": True, "visual_qa": True}:
        raise ValueError("independent-gate ownership drift")

    if canonical_sha(hard_surface_policy) != HARD_SURFACE_CANON:
        raise ValueError("Hard Surface policy canonical digest drift")
    if hard_surface_policy.get("schema") != "axm.building-planar-role-hard-normal-authority-policy/v0.1" or hard_surface_policy.get("owner") != "Building Hard Surface" or hard_surface_policy.get("policy_id") != "service-pavilion-planar-role-hard-normal-authority-001":
        raise ValueError("Hard Surface policy identity drift")
    split = hard_surface_policy.get("source_render_split_authority", {})
    if split.get("owner_head") != "0caa9ac9644f027350935240476bd0bf3bb66e18" or split.get("policy_git_blob_sha") != "5f2130d6286e2ee1b67395b1a753fbfc3eac22ea":
        raise ValueError("source render-split authority drift")
    if split.get("equivalence_key") != ["MATERIAL_ROLE", "EXACT_POSITION", "EXACT_CARDINAL_HARD_NORMAL", "EXPLICIT_PROTECTED_SPLIT_ID"] or split.get("cross_hard_normal_sharing") != "FORBIDDEN":
        raise ValueError("source equivalence policy drift")
    gd = hard_surface_policy.get("geometry_diagnostic_donor", {})
    if gd.get("head") != QHEAD or gd.get("quotient_sha256") != QSHA or gd.get("required_result") != "PASS_HARD_NORMAL_IDENTITY_REMOVAL_YIELDS_EXACT_312_GROUP_STRUCTURAL_QUOTIENT":
        raise ValueError("Hard Surface Geometry diagnostic binding drift")
    observed = hard_surface_policy.get("observed_identity_boundary", {})
    if observed.get("source_intent_render_vertex_count") != 604 or observed.get("role_position_quotient_group_count") != 312 or observed.get("source_render_vertex_identities_removed") != 292 or observed.get("groups_crossing_source_hard_normal_boundaries") != 188:
        raise ValueError("Hard Surface observed identity boundary drift")
    if observed.get("dropped_attribute") != "EXACT_CARDINAL_HARD_NORMAL" or observed.get("source_intent_partition_status") != "SOURCE_AUTHORIZED_RENDER_EQUIVALENCE" or observed.get("role_position_quotient_status") != "DERIVED_ATTRIBUTE_DROPPING_PARTITION_NOT_SOURCE_EQUIVALENT":
        raise ValueError("Hard Surface boundary classification drift")
    hp = hard_surface_policy.get("consumer_policy", {})
    false_fields = (
        "equal_312_count_is_source_equivalence",
        "exact_role_position_partition_match_is_source_normal_equivalence",
        "consumer_may_claim_source_hard_normal_preservation_from_this_policy",
        "source_owner_normal_field_rewrite",
        "source_owner_312_mesh_emitted",
        "automatic_receiver_adoption",
        "implicit_fallback",
    )
    if any(hp.get(k) is not False for k in false_fields):
        raise ValueError("Hard Surface consumer policy authority inflation")
    true_fields = (
        "consumer_must_declare_own_normal_storage_or_generation_identity",
        "consumer_must_declare_dropped_source_attributes",
        "consumer_must_retest_transport_runtime_and_visual_acceptance",
    )
    if any(hp.get(k) is not True for k in true_fields):
        raise ValueError("Hard Surface consumer obligation drift")

    if consumer_identity.get("schema") != "axm.environment-building-consumer-representation/v0.1" or consumer_identity.get("consumer_representation_id") != CONSUMER:
        raise ValueError("Environment consumer identity drift")
    deriv = consumer_identity.get("consumer_derivation", {})
    if deriv.get("kind") != "GODOT_POST_NORMAL_PER_MATERIAL_SURFACE_INDEX" or deriv.get("stored_vertices") != 312 or deriv.get("indices") != 1008 or deriv.get("triangle_count") != 336 or deriv.get("material_surface_count") != 5:
        raise ValueError("Environment consumer derivation drift")
    if deriv.get("consumer_generated_normal_index_domain") is not True or deriv.get("source_owner_equivalence_identity_claimed") is not False or deriv.get("post_index_normal_byte_identity_claimed") is not False:
        raise ValueError("Environment consumer normal/identity boundary drift")
    if consumer_identity.get("current_world", {}).get("environment_adoption") is not False:
        raise ValueError("Environment consumer adoption drift")

    if quotient_contract.get("schema") != "axm.environment-building-planar-role-quotient-receiving/v0.1" or quotient_contract.get("consumer_representation_id") != CONSUMER or quotient_contract.get("geometry_quotient_head") != QHEAD or quotient_contract.get("geometry_quotient_sha256") != QSHA:
        raise ValueError("Environment quotient contract identity drift")
    for k in ("source_hard_normal_identity_preserved_by_consumer", "consumer_generated_normals_are_source_normals", "quotient_authorizes_source_collapse", "environment_adoption"):
        if quotient_contract.get(k) is not False:
            raise ValueError(f"Environment quotient authority inflation: {k}")
    if quotient_contract.get("expected_role_vertex_counts") != ROLE:
        raise ValueError("Environment quotient role partition drift")

    if prior.get("state") != "PASS_CURRENT_WORLD_BUILDING_312_CONSUMER_EXACT_POSITION_QUOTIENT_REBIND" or prior.get("exact_environment_head") != PRIOR or prior.get("consumer_representation_id") != CONSUMER:
        raise ValueError("prior Environment quotient receipt drift")
    if prior.get("environment_adoption") is not False:
        raise ValueError("prior Environment adoption drift")
    q = prior.get("geometry_quotient", {})
    if q.get("head") != QHEAD or q.get("quotient_sha256") != QSHA or q.get("parent_source_intent_vertices") != 604 or q.get("quotient_groups") != 312 or q.get("removed_source_vertex_identities") != 292 or q.get("hard_normal_crossing_groups") != 188:
        raise ValueError("prior Environment quotient evidence drift")
    cw = prior.get("current_world_consumer", {})
    if cw.get("stored_vertices") != 312 or cw.get("indices") != 1008 or cw.get("triangles") != 336 or cw.get("material_surfaces") != 5 or cw.get("exact_role_position_partition_matches_geometry_quotient") is not True or cw.get("source_hard_normal_identity_preserved") is not False or cw.get("consumer_generated_normals_are_source_normals") is not False:
        raise ValueError("prior current-world consumer receipt drift")
    world = prior.get("world_observations", {})
    if world.get("state_count") != 17 or world.get("context_count") != 68 or world.get("weather_width_observation_count") != 1224 or float(world.get("maximum_weather_width_residual_px", 999.0)) > 0.05 or world.get("role_vertex_counts") != ROLE:
        raise ValueError("prior multi-asset world evidence drift")

    if len(runtime.get("samples", [])) != 17:
        raise ValueError("retained runtime state cardinality drift")
    if runtime.get("environment_building_planar_role_quotient_receiving_result") != "CANDIDATE_EXACT_POSITION_QUOTIENT_REBOUND" or runtime.get("environment_building_planar_role_consumer_id") != CONSUMER:
        raise ValueError("retained runtime Environment provenance drift")
    if runtime_report.get("state") != "PASS_BUILDING_PLANAR_ROLE_POST_NORMAL_INDEX_REMOVES_BUFFER_PENALTY__HOLD_PRIMITIVE_AND_VISUAL_REVIEW":
        raise ValueError("retained Runtime comparison drift")
    trade = prior.get("runtime_trade_space", {})
    if trade.get("indexed_vs_active_buffer_bytes") != -8304 or trade.get("indexed_vs_active_primitives") != 180 or trade.get("max_indexing_pixels_over_1_lsb") != 0 or trade.get("max_indexing_channel_delta_lsb") != 1:
        raise ValueError("retained Runtime trade-space drift")

    frames, frames_sha = frame_manifest(frames_root)

    return {
        "schema": "axm.environment-building-planar-role-hard-normal-authority-rebind-evidence/v0.1",
        "state": PASS,
        "hold": HOLD,
        "exact_environment_head": exact_head,
        "prior_environment_head": PRIOR,
        "active_segmented_rollback_head": ROLLBACK,
        "consumer_representation_id": CONSUMER,
        "source_authority": {
            "hard_surface_head": HARD_SURFACE_HEAD,
            "policy_git_blob_sha": HARD_SURFACE_BLOB,
            "policy_canonical_sha256": HARD_SURFACE_CANON,
            "source_intent_render_classes": 604,
            "derived_role_position_groups": 312,
            "source_render_vertex_identities_removed": 292,
            "groups_crossing_source_hard_normal_boundaries": 188,
            "dropped_source_attributes": ["EXACT_CARDINAL_HARD_NORMAL"],
            "source_partition_status": "SOURCE_AUTHORIZED_RENDER_EQUIVALENCE",
            "derived_partition_status": "DERIVED_ATTRIBUTE_DROPPING_PARTITION_NOT_SOURCE_EQUIVALENT",
        },
        "consumer_declaration": required_consumer,
        "multi_asset_current_world": {
            "retained_real_godot_frames": len(frames),
            "frame_set_sha256": frames_sha,
            "state_count": 17,
            "context_count": 68,
            "weather_width_observation_count": 1224,
            "maximum_weather_width_residual_px": world.get("maximum_weather_width_residual_px"),
            "building_role_vertex_counts": ROLE,
            "nature_object_weather_receiving_state_reauthored": False,
        },
        "runtime_trade_space": trade,
        "environment_adoption": False,
        "reusable_receiving_rule": contract.get("reusable_receiving_rule"),
        "truth_boundary": "The existing 312-vertex Map consumer is now rebound to the exact source-owner hard-normal authority policy as an explicit attribute-dropping consumer. The retained real-Godot Building + Nature + Object + footprint + Weather scene evidence remains the receiving evidence; this pass changes provenance/authority binding only. It does not recreate source hard normals, authorize source collapse, certify Technical-Art transport, accept the +180 primitive residual on target hardware, replace Art/QA, or adopt the receiver as default.",
        "four_root_gate": {
            "truth": "Source-authorized 604 hard-normal classes, the 312 attribute-dropping quotient and the 312 consumer remain separately named and executable.",
            "agency_non_domination": "Hard Surface owns source hard-normal authority; Environment owns receiving identity/rollback; Technical Art, Runtime and Art/QA retain independent gates.",
            "continuity": "The exact prior 68-frame current-world evidence and active segmented rollback remain pinned; no source or scene asset is rewritten.",
            "wisdom_before_speed": "Bind the new source-owner policy to the existing receiver before proposing another representation or smoothing rewrite.",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--consumer-identity", type=Path, required=True)
    ap.add_argument("--quotient-contract", type=Path, required=True)
    ap.add_argument("--hard-surface-policy", type=Path, required=True)
    ap.add_argument("--prior-environment-report", type=Path, required=True)
    ap.add_argument("--runtime", type=Path, required=True)
    ap.add_argument("--runtime-report", type=Path, required=True)
    ap.add_argument("--frames-root", type=Path, required=True)
    ap.add_argument("--exact-head", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    out = verify(
        load(args.contract),
        load(args.consumer_identity),
        load(args.quotient_contract),
        load(args.hard_surface_policy),
        load(args.prior_environment_report),
        load(args.runtime),
        load(args.runtime_report),
        args.frames_root,
        args.exact_head,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
