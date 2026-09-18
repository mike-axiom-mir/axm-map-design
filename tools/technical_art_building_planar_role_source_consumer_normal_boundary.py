#!/usr/bin/env python3
"""Bind the exact Building 312 Godot consumer to source hard-normal authority.

This is a Technical Art evidence adapter, not a mesh or UC feature. Building Hard
Surface owns the 604 source render-equivalence classes and the fact that the 312
role/position quotient drops EXACT_CARDINAL_HARD_NORMAL. The Map/Godot receiver
owns its own generated-normal representation. This verifier makes that boundary
explicit and fail-closed while preserving the existing real-receiver evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "axm.technical-art-building-source-consumer-normal-boundary/v0.1"
RESULT = (
    "PASS_BUILDING_312_GODOT_CONSUMER_NORMAL_IDENTITY_BOUND_TO_SOURCE_HARD_NORMAL_AUTHORITY__"
    "HOLD_NORMAL_NUMERIC_EXACTNESS_RUNTIME_VISUAL"
)
TA_SCHEMA = "axm.technical-art-building-planar-role-uc-index-bridge/v0.3"
TA_RESULT = (
    "PASS_BUILDING_EXACT_GODOT_INDEX_GROUPING_MATCHES_UC_CROSS_SOURCE_TUPLE_CANDIDATE__"
    "HOLD_GODOT_NORMAL_REPACK_EXACTNESS_AND_VISUAL_REVIEW"
)
HS_SCHEMA = "axm.building-planar-role-hard-normal-authority-evidence/v0.1"
HS_RESULT = "PASS_SOURCE_OWNED_PLANAR_ROLE_HARD_NORMAL_AUTHORITY_BOUNDARY"
POLICY_SCHEMA = "axm.building-planar-role-hard-normal-authority-policy/v0.1"
POLICY_ID = "service-pavilion-planar-role-hard-normal-authority-001"
EXPECTED_HARD_SURFACE_HEAD = "7b86b1a9da1ef8dc670ca01cf4918728e68ece92"
EXPECTED_GEOMETRY_HEAD = "7dfb1153dc5f80bcbf1b48803f044236d4ebb030"
EXPECTED_NORMAL_GENERATOR_BLOB = "7dcc111bde180ef34ee9b9d3958796a6634994ee"
EXPECTED_POST_NORMAL_INDEXER_BLOB = "53e040e279f6acaaf4483546f5faf5206f5536ca"
EXPECTED_UC_OBSERVER_BLOB = "cea48b2326813de6bd09430beafdac5315638657"
CONSUMER_NORMAL_IDENTITY = (
    "GODOT_4_7_2_SURFACETOOL_GENERATE_NORMALS_PER_MATERIAL_SURFACE__"
    "THEN_SURFACETOOL_INDEX"
)
DROPPED_SOURCE_ATTRIBUTE = "EXACT_CARDINAL_HARD_NORMAL"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def require_ordered_tokens(path: Path, tokens: list[str], label: str) -> None:
    text = path.read_text(encoding="utf-8")
    cursor = -1
    for token in tokens:
        location = text.find(token, cursor + 1)
        if location < 0:
            raise ValueError(f"{label} missing exact receiver token: {token}")
        if location <= cursor:
            raise ValueError(f"{label} receiver token order drift")
        cursor = location


def require_uc_observer_continuity(proven: bytes, current: bytes) -> None:
    if proven != current:
        raise ValueError("current UC indexed-surface observer bytes differ from the proven observer")
    if git_blob_sha1_bytes(proven) != EXPECTED_UC_OBSERVER_BLOB:
        raise ValueError("proven UC indexed-surface observer blob drift")
    if git_blob_sha1_bytes(current) != EXPECTED_UC_OBSERVER_BLOB:
        raise ValueError("current UC indexed-surface observer blob drift")


def git_blob_sha1_bytes(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def validate_source_authority(policy: dict[str, Any], evidence: dict[str, Any], hard_surface_head: str) -> None:
    if hard_surface_head != EXPECTED_HARD_SURFACE_HEAD:
        raise ValueError("Hard Surface exact head drift")
    if policy.get("schema") != POLICY_SCHEMA or policy.get("policy_id") != POLICY_ID:
        raise ValueError("Hard Surface authority policy identity drift")
    if evidence.get("schema") != HS_SCHEMA or evidence.get("result") != HS_RESULT:
        raise ValueError("Hard Surface authority evidence is not the exact PASS")
    if evidence.get("exact_head") != hard_surface_head:
        raise ValueError("Hard Surface authority evidence head drift")
    if evidence.get("geometry_diagnostic_head") != EXPECTED_GEOMETRY_HEAD:
        raise ValueError("Geometry quotient donor head drift")

    boundary = policy.get("observed_identity_boundary", {})
    if boundary.get("source_intent_render_vertex_count") != 604:
        raise ValueError("source-authorized render class count drift")
    if boundary.get("role_position_quotient_group_count") != 312:
        raise ValueError("role/position quotient count drift")
    if boundary.get("source_render_vertex_identities_removed") != 292:
        raise ValueError("source identity loss count drift")
    if boundary.get("groups_crossing_source_hard_normal_boundaries") != 188:
        raise ValueError("hard-normal-crossing quotient count drift")
    if boundary.get("dropped_attribute") != DROPPED_SOURCE_ATTRIBUTE:
        raise ValueError("dropped source hard-normal attribute is no longer explicit")
    if boundary.get("source_intent_partition_status") != "SOURCE_AUTHORIZED_RENDER_EQUIVALENCE":
        raise ValueError("604 source authority classification drift")
    if boundary.get("role_position_quotient_status") != "DERIVED_ATTRIBUTE_DROPPING_PARTITION_NOT_SOURCE_EQUIVALENT":
        raise ValueError("312 quotient was silently promoted to source equivalence")

    consumer = policy.get("consumer_policy", {})
    if consumer.get("consumer_must_declare_own_normal_storage_or_generation_identity") is not True:
        raise ValueError("source authority no longer requires consumer normal identity")
    if consumer.get("consumer_must_declare_dropped_source_attributes") is not True:
        raise ValueError("source authority no longer requires dropped-attribute declaration")
    if consumer.get("consumer_may_claim_source_hard_normal_preservation_from_this_policy") is not False:
        raise ValueError("source authority incorrectly transfers source normal preservation")
    if consumer.get("automatic_receiver_adoption") is not False:
        raise ValueError("source authority incorrectly enables automatic receiver adoption")


def validate_consumer_receipt(receipt: dict[str, Any]) -> None:
    if receipt.get("schema") != TA_SCHEMA or receipt.get("result") != TA_RESULT:
        raise ValueError("Technical Art real-receiver evidence identity drift")
    receiver = receipt.get("exact_godot_receiver", {})
    if receiver.get("surface_count") != 5 or receiver.get("triangle_count") != 336:
        raise ValueError("Godot receiver surface/triangle identity drift")
    if receiver.get("before_vertices") != 1008 or receiver.get("after_vertices") != 312:
        raise ValueError("Godot receiver 1008 -> 312 identity drift")
    if receiver.get("after_indices") != 1008:
        raise ValueError("Godot receiver index count drift")
    candidate = receipt.get("uc_candidate", {})
    if candidate.get("candidate_vertices") != 312:
        raise ValueError("UC observer candidate no longer matches the 312 receiver partition")
    if candidate.get("exact_corner_grouping_isomorphic_to_godot_all_surfaces") is not True:
        raise ValueError("UC/Godot exact corner grouping proof is not green")
    normal = receipt.get("godot_postindex_normal_transport", {})
    if normal.get("exact") is not False or normal.get("changed_corner_count") != 120:
        raise ValueError("Godot post-index normal repack observation drift")
    for key in ("max_abs_component_delta", "max_angular_delta_degrees"):
        value = normal.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"Godot normal observation {key} must stay finite")
    truth = receipt.get("truth_boundary", {})
    if truth.get("postindex_normal_exactness_claimed") is not False:
        raise ValueError("Technical Art receiver evidence silently claimed post-index normal exactness")
    if truth.get("building_semantics_centralized_in_uc") is not False:
        raise ValueError("Building domain semantics were centralized into UC")


def validate_contract(contract: dict[str, Any]) -> None:
    source = contract.get("source_authority", {})
    consumer = contract.get("consumer_representation", {})
    if source.get("source_render_equivalence_classes") != 604:
        raise ValueError("contract source class count drift")
    if source.get("role_position_quotient_groups") != 312:
        raise ValueError("contract quotient group count drift")
    if source.get("quotient_status") != "DERIVED_ATTRIBUTE_DROPPING_PARTITION_NOT_SOURCE_EQUIVALENT":
        raise ValueError("contract promoted 312 quotient to source equivalence")
    if source.get("dropped_source_attribute") != DROPPED_SOURCE_ATTRIBUTE:
        raise ValueError("contract omitted exact dropped source hard-normal attribute")
    if consumer.get("stored_vertices") != 312:
        raise ValueError("consumer stored-vertex identity drift")
    if consumer.get("normal_generation_identity") != CONSUMER_NORMAL_IDENTITY:
        raise ValueError("consumer normal-generation identity drift")
    if consumer.get("dropped_source_attributes") != [DROPPED_SOURCE_ATTRIBUTE]:
        raise ValueError("consumer did not declare the exact dropped source attribute")
    if consumer.get("source_equivalence_claimed") is not False:
        raise ValueError("consumer incorrectly claims source equivalence")
    if consumer.get("source_hard_normal_preservation_claimed") is not False:
        raise ValueError("consumer incorrectly claims source hard-normal preservation")
    if consumer.get("postindex_normal_numeric_exactness_claimed") is not False:
        raise ValueError("consumer incorrectly claims post-index normal numeric exactness")
    if contract.get("universal_creation", {}).get("building_policy_moved_into_uc") is not False:
        raise ValueError("Building policy was moved into UC")


def rejected(contract: dict[str, Any]) -> dict[str, str]:
    try:
        validate_contract(contract)
    except ValueError as exc:
        return {"status": "PASS_REJECTED", "observed_error": str(exc)}
    return {"status": "UNEXPECTED_PASS", "observed_error": ""}


def build_contract(
    *,
    receipt: dict[str, Any],
    policy: dict[str, Any],
    evidence: dict[str, Any],
    technical_art_head: str,
    hard_surface_head: str,
    current_uc_head: str,
    normal_generator_path: Path,
    post_normal_indexer_path: Path,
    proven_uc_observer_path: Path,
    current_uc_observer_path: Path,
) -> dict[str, Any]:
    validate_source_authority(policy, evidence, hard_surface_head)
    validate_consumer_receipt(receipt)
    if receipt.get("technical_art_head") != technical_art_head:
        raise ValueError("Technical Art receipt head drift")

    if git_blob_sha1(normal_generator_path) != EXPECTED_NORMAL_GENERATOR_BLOB:
        raise ValueError("exact Godot normal-generator source blob drift")
    if git_blob_sha1(post_normal_indexer_path) != EXPECTED_POST_NORMAL_INDEXER_BLOB:
        raise ValueError("exact Godot post-normal indexer source blob drift")
    require_ordered_tokens(
        normal_generator_path,
        ["st.add_vertex", "st.generate_normals()", "st.commit(mesh)"],
        "Godot normal generator",
    )
    require_ordered_tokens(
        post_normal_indexer_path,
        ["st.create_from(source_mesh,surface_index)", "st.index()", "st.commit(indexed_mesh)"],
        "Godot post-normal indexer",
    )

    proven_uc = proven_uc_observer_path.read_bytes()
    current_uc = current_uc_observer_path.read_bytes()
    require_uc_observer_continuity(proven_uc, current_uc)

    normal_observation = receipt["godot_postindex_normal_transport"]
    contract: dict[str, Any] = {
        "schema": SCHEMA,
        "result": RESULT,
        "technical_art_head": technical_art_head,
        "source_authority": {
            "repository": "mike-axiom-mir/axm-building-design",
            "hard_surface_head": hard_surface_head,
            "geometry_diagnostic_head": EXPECTED_GEOMETRY_HEAD,
            "policy_id": POLICY_ID,
            "source_render_equivalence_classes": 604,
            "role_position_quotient_groups": 312,
            "source_render_vertex_identities_removed": 292,
            "groups_crossing_source_hard_normal_boundaries": 188,
            "source_status": "SOURCE_AUTHORIZED_RENDER_EQUIVALENCE",
            "quotient_status": "DERIVED_ATTRIBUTE_DROPPING_PARTITION_NOT_SOURCE_EQUIVALENT",
            "dropped_source_attribute": DROPPED_SOURCE_ATTRIBUTE,
        },
        "consumer_representation": {
            "repository": "mike-axiom-mir/axm-map-design",
            "representation_id": receipt.get("representation_id"),
            "normal_generation_identity": CONSUMER_NORMAL_IDENTITY,
            "normal_generator_git_blob": EXPECTED_NORMAL_GENERATOR_BLOB,
            "post_normal_indexer_git_blob": EXPECTED_POST_NORMAL_INDEXER_BLOB,
            "generation_order": "triangle vertices -> SurfaceTool.generate_normals() -> commit -> SurfaceTool.create_from() -> index() -> commit",
            "stored_vertices": 312,
            "indices": 1008,
            "triangles": 336,
            "material_surfaces": 5,
            "dropped_source_attributes": [DROPPED_SOURCE_ATTRIBUTE],
            "source_equivalence_claimed": False,
            "source_hard_normal_preservation_claimed": False,
            "postindex_normal_numeric_exactness_claimed": False,
            "observed_postindex_normal_repack": {
                "changed_corner_count": normal_observation["changed_corner_count"],
                "total_corner_count": normal_observation["total_corner_count"],
                "max_abs_component_delta": normal_observation["max_abs_component_delta"],
                "max_angular_delta_degrees": normal_observation["max_angular_delta_degrees"],
                "acceptance_tolerance_inferred": False,
            },
        },
        "universal_creation": {
            "proven_observer_head": receipt.get("uc_head"),
            "current_head": current_uc_head,
            "indexed_surface_observer_git_blob": EXPECTED_UC_OBSERVER_BLOB,
            "current_observer_byte_identical_to_proven_observer": True,
            "building_policy_moved_into_uc": False,
            "product_modified": False,
            "role": "generic structural observer only",
        },
        "authority_split": {
            "source_render_and_hard_normal_intent": "BUILDING_HARD_SURFACE",
            "source_attribute_quotient_diagnostic": "BUILDING_GEOMETRY_TOPOLOGY",
            "consumer_normal_generation_repacking_and_transport": "TECHNICAL_ART_MAP_RECEIVER",
            "runtime_device_acceptance": "RUNTIME_OPTIMIZATION",
            "appearance_acceptance": "ART_DIRECTION_AND_VISUAL_QA",
        },
        "truth_boundary": {
            "source_mesh_rewritten": False,
            "source_normal_field_rewritten": False,
            "consumer_312_promoted_to_source_equivalence": False,
            "normal_repack_tolerance_inferred": False,
            "runtime_acceptance_claimed": False,
            "visual_acceptance_claimed": False,
            "environment_adoption_claimed": False,
            "canon_claimed": False,
            "production_ready": False,
        },
    }
    validate_contract(contract)

    mutations: dict[str, dict[str, Any]] = {}
    promoted = copy.deepcopy(contract)
    promoted["source_authority"]["quotient_status"] = "SOURCE_AUTHORIZED_RENDER_EQUIVALENCE"
    mutations["quotient_promoted_to_source_equivalence"] = rejected(promoted)
    preserved = copy.deepcopy(contract)
    preserved["consumer_representation"]["source_hard_normal_preservation_claimed"] = True
    mutations["consumer_claims_source_hard_normal_preservation"] = rejected(preserved)
    omitted = copy.deepcopy(contract)
    omitted["consumer_representation"]["dropped_source_attributes"] = []
    mutations["consumer_omits_dropped_source_attribute"] = rejected(omitted)
    anonymous = copy.deepcopy(contract)
    anonymous["consumer_representation"]["normal_generation_identity"] = "UNDECLARED"
    mutations["consumer_normal_generation_identity_removed"] = rejected(anonymous)
    moved = copy.deepcopy(contract)
    moved["universal_creation"]["building_policy_moved_into_uc"] = True
    mutations["building_policy_centralized_into_uc"] = rejected(moved)
    try:
        require_uc_observer_continuity(proven_uc, current_uc + b"\n# deliberate drift\n")
    except ValueError as exc:
        mutations["current_uc_observer_byte_drift"] = {"status": "PASS_REJECTED", "observed_error": str(exc)}
    else:
        mutations["current_uc_observer_byte_drift"] = {"status": "UNEXPECTED_PASS", "observed_error": ""}

    if any(value.get("status") != "PASS_REJECTED" for value in mutations.values()):
        raise ValueError(f"one or more source/consumer boundary negative controls did not fail closed: {mutations}")
    contract["negative_controls"] = mutations
    return contract


def write_retained(output: Path, contract: dict[str, Any], sources: dict[str, Path]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = output / "source-consumer-normal-boundary-receipt.json"
    receipt_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, source in sources.items():
        (output / name).write_bytes(source.read_bytes())
    manifest = {
        path.name: sha256_bytes(path.read_bytes())
        for path in sorted(output.iterdir())
        if path.is_file() and path.name != "sha256-manifest.json"
    }
    (output / "sha256-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--technical-art-receipt", type=Path, required=True)
    parser.add_argument("--hard-surface-policy", type=Path, required=True)
    parser.add_argument("--hard-surface-evidence", type=Path, required=True)
    parser.add_argument("--normal-generator-source", type=Path, required=True)
    parser.add_argument("--post-normal-indexer-source", type=Path, required=True)
    parser.add_argument("--proven-uc-observer", type=Path, required=True)
    parser.add_argument("--current-uc-observer", type=Path, required=True)
    parser.add_argument("--technical-art-head", required=True)
    parser.add_argument("--hard-surface-head", required=True)
    parser.add_argument("--current-uc-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    receipt = load_json(args.technical_art_receipt)
    policy = load_json(args.hard_surface_policy)
    evidence = load_json(args.hard_surface_evidence)
    contract = build_contract(
        receipt=receipt,
        policy=policy,
        evidence=evidence,
        technical_art_head=args.technical_art_head,
        hard_surface_head=args.hard_surface_head,
        current_uc_head=args.current_uc_head,
        normal_generator_path=args.normal_generator_source,
        post_normal_indexer_path=args.post_normal_indexer_source,
        proven_uc_observer_path=args.proven_uc_observer,
        current_uc_observer_path=args.current_uc_observer,
    )
    write_retained(
        args.output,
        contract,
        {
            "hard-normal-authority-policy.json": args.hard_surface_policy,
            "hard-normal-authority-evidence.json": args.hard_surface_evidence,
            "normal-generator-source.gd": args.normal_generator_source,
            "post-normal-indexer-source.gd": args.post_normal_indexer_source,
            "proven-uc-indexed-surface-observer.py": args.proven_uc_observer,
            "current-uc-indexed-surface-observer.py": args.current_uc_observer,
        },
    )
    print(json.dumps(contract, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
