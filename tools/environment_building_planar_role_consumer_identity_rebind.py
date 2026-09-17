#!/usr/bin/env python3
"""Environment gate for explicit Building source-intent vs consumer-receiver identity.

The Hard-Surface source owner now declares an exact cardinal-normal split domain of
604 equivalence groups. The current reviewed Godot receiver stores 312 vertices only
after consumer-side normal generation and indexing. This gate prevents Environment
from silently calling those identities equivalent while re-proving the same real
multi-asset current-world receiver and inherited Weather-width contract.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "axm.environment-building-planar-role-consumer-identity-rebind/v0.1"
CONTRACT_SCHEMA = "axm.environment-building-consumer-representation/v0.1"
SOURCE_EVIDENCE_SCHEMA = "axm.building-planar-role-render-split-evidence/v0.1"
RUNTIME_SCHEMA = "axm.runtime-building-planar-role-surface-index-budget/v0.1"
RUNTIME_RECEIPT_SCHEMA = "axm.runtime-building-planar-role-surface-indexing-observation/v0.1"
SOURCE_SPLIT_HEAD = "0caa9ac9644f027350935240476bd0bf3bb66e18"
SOURCE_PARENT_HEAD = "93f22e4eeb9bb32516d4b11f8d8bcf47d9792910"
RUNTIME_DONOR_HEAD = "8d5860c308c244d314ede5b79021e46f35c4040d"
ACTIVE_ROLLBACK_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
REPRESENTATION_ID = "boundary-only-planar-role-rectangle-render-001"
CONSUMER_ID = "map-consumer:service-pavilion-001:planar-role-post-normal-indexed-001"
RUNTIME_PASS = "PASS_BUILDING_PLANAR_ROLE_POST_NORMAL_INDEX_REMOVES_BUFFER_PENALTY__HOLD_PRIMITIVE_AND_VISUAL_REVIEW"
ENVIRONMENT_PASS = "PASS_CURRENT_WORLD_BUILDING_CONSUMER_IDENTITY_REBOUND_TO_SOURCE_SPLIT_POLICY"
ENVIRONMENT_HOLD = "HOLD_DEFAULT_ADOPTION_PENDING_TARGET_DEVICE_RESIDUAL_PRIMITIVE_ACCEPTANCE"
EXPECTED_WIDTH_PROFILE_DIGEST = "8d61b2dc11f2508d186a1e469185badda7217803f7c4634fb2d951d8579c0dd5"
WEATHER_WIDTH_RESIDUAL_LIMIT_PX = 0.05
EXPECTED_WEATHER_WIDTH_OBSERVATIONS = 1224
BUILDING_ASSET_ID = "source:building:service-pavilion-001"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_building(sample: dict) -> dict:
    rows = [row for row in sample.get("static_source_meshes", []) if row.get("asset_id") == BUILDING_ASSET_ID]
    if len(rows) != 1:
        raise ValueError(f"expected one Building row, got {len(rows)}")
    return rows[0]


def verify_contract(contract: dict) -> None:
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ValueError("consumer identity contract schema drift")
    if contract.get("consumer_representation_id") != CONSUMER_ID:
        raise ValueError("consumer representation ID drift")
    if contract.get("owner") != "Map Environment / World Art":
        raise ValueError("consumer representation owner drift")

    source = contract.get("source_representation", {})
    if source.get("representation_id") != REPRESENTATION_ID:
        raise ValueError("source representation ID drift")
    if source.get("hard_surface_parent_head") != SOURCE_PARENT_HEAD:
        raise ValueError("source parent head drift")
    if source.get("hard_surface_split_policy_head") != SOURCE_SPLIT_HEAD:
        raise ValueError("source split-policy head drift")
    if source.get("source_triangle_corners") != 1008 or source.get("source_intent_equivalence_groups") != 604:
        raise ValueError("source split-domain identity drift")
    if source.get("source_cardinal_hard_normal_equivalence_is_consumer_identity") is not False:
        raise ValueError("contract silently equates source and consumer identity")

    consumer = contract.get("consumer_derivation", {})
    if consumer.get("kind") != "GODOT_POST_NORMAL_PER_MATERIAL_SURFACE_INDEX":
        raise ValueError("consumer derivation kind drift")
    if consumer.get("runtime_donor_head") != RUNTIME_DONOR_HEAD:
        raise ValueError("Runtime donor head drift")
    expected = {"material_surface_count": 5, "triangle_count": 336, "stored_vertices": 312, "indices": 1008}
    for key, value in expected.items():
        if consumer.get(key) != value:
            raise ValueError(f"consumer {key} drift: {consumer.get(key)}")
    if consumer.get("consumer_generated_normal_index_domain") is not True:
        raise ValueError("consumer-generated normal/index identity must stay explicit")
    if consumer.get("source_owner_equivalence_identity_claimed") is not False:
        raise ValueError("consumer contract falsely claims source equivalence")
    if consumer.get("post_index_normal_byte_identity_claimed") is not False:
        raise ValueError("consumer contract falsely claims exact post-index normals")

    world = contract.get("current_world", {})
    if world.get("active_segmented_rollback_head") != ACTIVE_ROLLBACK_HEAD:
        raise ValueError("active rollback identity drift")
    if world.get("environment_adoption") is not False or world.get("review_target_only") is not True:
        raise ValueError("consumer contract inflated Environment adoption authority")


def verify_source_evidence(source_evidence: dict) -> None:
    if source_evidence.get("schema") != SOURCE_EVIDENCE_SCHEMA:
        raise ValueError("source split evidence schema drift")
    if source_evidence.get("result") != "PASS_SOURCE_OWNED_PLANAR_ROLE_RENDER_SPLIT_INTENT":
        raise ValueError("source split owner evidence is not PASS")
    if source_evidence.get("exact_head") != SOURCE_SPLIT_HEAD:
        raise ValueError("source split exact head drift")
    if source_evidence.get("representation_id") != REPRESENTATION_ID:
        raise ValueError("source representation drift")
    if source_evidence.get("parent_owner_head") != SOURCE_PARENT_HEAD:
        raise ValueError("source parent owner head drift")
    if source_evidence.get("rectangle_count") != 168 or source_evidence.get("triangle_count") != 336:
        raise ValueError("source rectangle/triangle identity drift")
    if source_evidence.get("material_role_count") != 5:
        raise ValueError("source material-role count drift")
    intent = source_evidence.get("source_intent", {})
    if intent.get("triangle_corner_count") != 1008 or intent.get("equivalence_group_count") != 604:
        raise ValueError("source owner split-domain count drift")
    if intent.get("all_protected_split_ids_explicit") is not True or intent.get("all_current_protected_split_ids_null") is not True:
        raise ValueError("source protected-split declaration drift")
    if intent.get("material_role_in_equivalence_key") is not True or intent.get("cardinal_hard_normal_in_equivalence_key") is not True:
        raise ValueError("source equivalence key lost material or hard-normal boundary")


def verify_runtime(runtime_report: dict, indexed_runtime: dict) -> dict:
    if runtime_report.get("schema") != RUNTIME_SCHEMA or runtime_report.get("state") != RUNTIME_PASS:
        raise ValueError("Runtime donor report drift")
    if runtime_report.get("representation_id") != REPRESENTATION_ID:
        raise ValueError("Runtime source representation drift")
    after = runtime_report.get("building_representation", {}).get("after", {})
    if after.get("total_vertices") != 312 or after.get("total_indices") != 1008 or after.get("total_primitives") != 336:
        raise ValueError("consumer final storage identity drift")
    if runtime_report.get("building_representation", {}).get("surface_count") != 5:
        raise ValueError("consumer five-surface identity drift")

    proof = runtime_report.get("proof_host", {})
    if proof.get("observation_count") != 68:
        raise ValueError("expected 68 current-world observations")
    active_delta = proof.get("indexed_vs_active_delta_sets", {})
    if active_delta.get("buffer_mem_bytes") != [-8304] or active_delta.get("primitives_in_frame") != [180]:
        raise ValueError("active-relative Runtime trade space drift")
    for field in ("draw_calls_in_frame", "objects_in_frame", "texture_mem_bytes"):
        if active_delta.get(field) != [0]:
            raise ValueError(f"unexpected active-relative {field} drift")

    visuals = runtime_report.get("visuals", {})
    if visuals.get("frame_count") != 68 or visuals.get("changed_frame_count") != 68:
        raise ValueError("retained indexing frame-set drift")
    if int(visuals.get("max_changed_pixels", 999999)) > 55:
        raise ValueError("indexing raster delta exceeded retained bound")
    if int(visuals.get("max_pixels_over_1_lsb", 999999)) != 0 or int(visuals.get("max_channel_delta_lsb", 999999)) > 1:
        raise ValueError("indexing raster delta exceeded one-LSB boundary")

    if indexed_runtime.get("runtime_building_planar_role_surface_indexing_result") != "CANDIDATE_INDEXED_AFTER_FINAL_NORMAL_GENERATION":
        raise ValueError("consumer indexed target-host marker missing")
    if indexed_runtime.get("environment_building_planar_role_representation_id") != REPRESENTATION_ID:
        raise ValueError("indexed runtime parent representation drift")
    if indexed_runtime.get("environment_building_planar_role_hard_surface_head") != SOURCE_PARENT_HEAD:
        raise ValueError("indexed runtime provenance no longer matches its actual parent source head")
    if indexed_runtime.get("source_width_profile_digest") != EXPECTED_WIDTH_PROFILE_DIGEST:
        raise ValueError("Weather source-width profile digest drift")

    samples = indexed_runtime.get("samples", [])
    if len(samples) != 17:
        raise ValueError(f"expected 17 current-world states, got {len(samples)}")
    context_count = 0
    width_count = 0
    max_residual = 0.0
    for sample in samples:
        row = find_building(sample)
        receipt = row.get("runtime_building_planar_role_surface_indexing", {})
        if receipt.get("schema") != RUNTIME_RECEIPT_SCHEMA:
            raise ValueError("per-state consumer receipt schema drift")
        if receipt.get("building_hard_surface_head") != SOURCE_PARENT_HEAD:
            raise ValueError("per-state consumer parent provenance drift")
        state_after = receipt.get("after", {})
        if state_after.get("surface_count") != 5 or state_after.get("total_vertices") != 312 or state_after.get("total_indices") != 1008 or state_after.get("total_primitives") != 336:
            raise ValueError("per-state consumer storage drift")
        if sample.get("weather_width_profile_digest") != EXPECTED_WIDTH_PROFILE_DIGEST:
            raise ValueError("per-state Weather width digest drift")
        for camera_context in sample.get("contexts", {}).values():
            context_count += len(camera_context)
            weather = camera_context.get("candidate", {}).get("weather_update", {})
            measured = int(weather.get("measured_width_count", -1))
            residual = float(weather.get("maximum_projected_width_residual_px", 999999.0))
            if measured != 36 or residual > WEATHER_WIDTH_RESIDUAL_LIMIT_PX:
                raise ValueError("Weather width receiving contract drift")
            width_count += measured
            max_residual = max(max_residual, residual)
    if context_count != 68 or width_count != EXPECTED_WEATHER_WIDTH_OBSERVATIONS:
        raise ValueError("current-world/Weather observation cardinality drift")

    return {
        "context_count": context_count,
        "weather_width_observation_count": width_count,
        "maximum_weather_width_residual_px": max_residual,
        "indexed_vs_active_buffer_bytes": -8304,
        "indexed_vs_active_primitives": 180,
        "max_indexing_changed_pixels_per_frame": int(visuals["max_changed_pixels"]),
        "max_indexing_pixels_over_1_lsb": int(visuals["max_pixels_over_1_lsb"]),
        "max_indexing_channel_delta_lsb": int(visuals["max_channel_delta_lsb"]),
    }


def verify(contract: dict, source_evidence: dict, runtime_report: dict, indexed_runtime: dict, exact_head: str) -> dict:
    verify_contract(contract)
    verify_source_evidence(source_evidence)
    observations = verify_runtime(runtime_report, indexed_runtime)

    source_groups = int(source_evidence["source_intent"]["equivalence_group_count"])
    consumer_vertices = int(contract["consumer_derivation"]["stored_vertices"])
    if source_groups == consumer_vertices:
        raise ValueError("source/consumer distinction collapsed unexpectedly")

    return {
        "schema": SCHEMA,
        "state": ENVIRONMENT_PASS,
        "hold": ENVIRONMENT_HOLD,
        "exact_environment_head": exact_head,
        "consumer_representation_id": CONSUMER_ID,
        "source_representation_id": REPRESENTATION_ID,
        "source_split_policy_head": SOURCE_SPLIT_HEAD,
        "source_parent_head": SOURCE_PARENT_HEAD,
        "runtime_donor_head": RUNTIME_DONOR_HEAD,
        "source_intent": {
            "triangle_corners": 1008,
            "equivalence_groups": source_groups,
            "normal_contract": "EXACT_CARDINAL_HARD_NORMAL_PER_RECTANGLE",
        },
        "consumer_identity": {
            "stored_vertices": consumer_vertices,
            "indices": 1008,
            "triangles": 336,
            "material_surfaces": 5,
            "derivation": "GODOT_POST_NORMAL_PER_MATERIAL_SURFACE_INDEX",
            "source_equivalence_identity_claimed": False,
            "post_index_normal_byte_identity_claimed": False,
        },
        "identity_delta": {
            "source_intent_groups_minus_consumer_vertices": source_groups - consumer_vertices,
            "consumer_is_distinct_receiving_identity": True,
        },
        "environment_adoption": False,
        "active_segmented_rollback_head": ACTIVE_ROLLBACK_HEAD,
        "world_observations": observations,
        "authority": contract["authority"],
        "truth_boundary": (
            "The exact source owner now permits 604 cardinal-normal/material-role render equivalence groups, while the reviewed Godot current-world receiver stores 312 vertices only in a distinct consumer-generated normal/index domain. "
            "Environment explicitly binds those as separate identities and re-verifies the real 68-observation Building+Nature+Object+Weather world without changing the scene. "
            "Art and independent QA retained-view acceptance remain valid for the 312 consumer identity, while the measured Technical-Art normal repack remains non-exact and Runtime/target-device residual +180 primitive acceptance remains open."
        ),
        "four_root_gate": {
            "truth": "604 source-intent groups and 312 consumer vertices remain separate facts; neither is renamed to make the other look exact.",
            "agency_non_domination": "Hard Surface keeps source split intent; Environment names only its receiving identity; Runtime, Technical Art, Art and QA keep their gates.",
            "continuity": "The active segmented rollback and prior reviewed 312 consumer remain pinned; this rebind changes identity/provenance, not scene art.",
            "wisdom_before_speed": "Close the provenance ambiguity before any default adoption decision; do not change normals or source policy merely to make counts match."
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--source-evidence", type=Path, required=True)
    parser.add_argument("--runtime-report", type=Path, required=True)
    parser.add_argument("--indexed-runtime", type=Path, required=True)
    parser.add_argument("--exact-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(load(args.contract), load(args.source_evidence), load(args.runtime_report), load(args.indexed_runtime), args.exact_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
