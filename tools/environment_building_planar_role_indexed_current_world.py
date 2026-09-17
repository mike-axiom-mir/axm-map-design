#!/usr/bin/env python3
"""Environment gate for the exact indexed planar-role Building receiver.

This consumes the already-proven Runtime storage rewrite as a donor and verifies
that the exact current-world observation remains inside Environment's receiving
boundary.  It does not make the receiver the default and does not replace
independent Art/QA/Runtime/Technical-Art authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "axm.environment-building-planar-role-indexed-current-world/v0.1"
RUNTIME_SCHEMA = "axm.runtime-building-planar-role-surface-index-budget/v0.1"
RUNTIME_DONOR_HEAD = "8d5860c308c244d314ede5b79021e46f35c4040d"
UNINDEXED_ENVIRONMENT_HEAD = "b758f9ca006ec5885ff1c2c52e2fb09e9ccdd464"
ACTIVE_ROLLBACK_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
HARD_SURFACE_HEAD = "93f22e4eeb9bb32516d4b11f8d8bcf47d9792910"
MATERIALS_HEAD = "4179aa1401f5a9114399e2f998c96809d4b8ed2e"
REPRESENTATION_ID = "boundary-only-planar-role-rectangle-render-001"
RUNTIME_RECEIPT_SCHEMA = "axm.runtime-building-planar-role-surface-indexing-observation/v0.1"
RUNTIME_PASS = "PASS_BUILDING_PLANAR_ROLE_POST_NORMAL_INDEX_REMOVES_BUFFER_PENALTY__HOLD_PRIMITIVE_AND_VISUAL_REVIEW"
ENVIRONMENT_PASS = "PASS_CURRENT_WORLD_INDEXED_PLANAR_ROLE_RECEIVER_REVIEW_READY"
ENVIRONMENT_HOLD = "HOLD_DEFAULT_ADOPTION_PENDING_INDEPENDENT_QA_TECHNICAL_ART_AND_RESIDUAL_PRIMITIVE_ACCEPTANCE"
BUILDING_ASSET_ID = "source:building:service-pavilion-001"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_building(sample: dict) -> dict:
    rows = [
        row for row in sample.get("static_source_meshes", [])
        if row.get("asset_id") == BUILDING_ASSET_ID
    ]
    if len(rows) != 1:
        raise ValueError(f"expected one Building row, got {len(rows)}")
    return rows[0]


def require_exact_delta(report: dict) -> None:
    proof = report.get("proof_host", {})
    if proof.get("observation_count") != 68:
        raise ValueError("expected 68 current-world observations")

    indexed_vs_unindexed = proof.get("indexed_vs_unindexed_delta_sets", {})
    if indexed_vs_unindexed.get("buffer_mem_bytes") != [-11904]:
        raise ValueError(f"indexed/unindexed buffer delta drift: {indexed_vs_unindexed}")
    for field in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "texture_mem_bytes"):
        if indexed_vs_unindexed.get(field) != [0]:
            raise ValueError(f"indexed/unindexed {field} drift: {indexed_vs_unindexed.get(field)}")

    indexed_vs_active = proof.get("indexed_vs_active_delta_sets", {})
    if indexed_vs_active.get("buffer_mem_bytes") != [-8304]:
        raise ValueError(f"indexed/active buffer delta drift: {indexed_vs_active}")
    if indexed_vs_active.get("primitives_in_frame") != [180]:
        raise ValueError(f"indexed/active primitive delta drift: {indexed_vs_active}")
    for field in ("draw_calls_in_frame", "objects_in_frame", "texture_mem_bytes"):
        if indexed_vs_active.get(field) != [0]:
            raise ValueError(f"indexed/active {field} drift: {indexed_vs_active.get(field)}")


def verify(runtime_report: dict, indexed_runtime: dict, exact_head: str) -> dict:
    if runtime_report.get("schema") != RUNTIME_SCHEMA:
        raise ValueError("Runtime report schema drift")
    if runtime_report.get("state") != RUNTIME_PASS:
        raise ValueError(f"Runtime donor is not at the expected scoped PASS: {runtime_report.get('state')}")
    if runtime_report.get("environment_parent_head") != UNINDEXED_ENVIRONMENT_HEAD:
        raise ValueError("unindexed Environment parent drift")
    if runtime_report.get("active_parent_head") != ACTIVE_ROLLBACK_HEAD:
        raise ValueError("active rollback parent drift")
    if runtime_report.get("representation_id") != REPRESENTATION_ID:
        raise ValueError("planar-role representation drift")

    representation = runtime_report.get("building_representation", {})
    before = representation.get("before", {})
    after = representation.get("after", {})
    if representation.get("surface_count") != 5 or representation.get("triangle_count") != 336:
        raise ValueError("five-surface / 336-triangle identity drift")
    if before.get("total_vertices") != 1008 or before.get("total_indices") != 0 or before.get("total_primitives") != 336:
        raise ValueError("unindexed planar-role storage identity drift")
    if after.get("total_vertices") != 312 or after.get("total_indices") != 1008 or after.get("total_primitives") != 336:
        raise ValueError("indexed planar-role storage identity drift")
    if representation.get("modeled_saved_bytes") != 12672:
        raise ValueError("modeled indexed storage saving drift")

    require_exact_delta(runtime_report)

    visuals = runtime_report.get("visuals", {})
    if visuals.get("frame_count") != 68 or visuals.get("changed_frame_count") != 68:
        raise ValueError("indexed/unindexed retained frame-set drift")
    if int(visuals.get("max_changed_pixels", 999999)) > 55:
        raise ValueError("indexed raster delta exceeds reviewed pixel bound")
    if int(visuals.get("max_pixels_over_1_lsb", 999999)) != 0:
        raise ValueError("indexed raster delta exceeds one-LSB review boundary")
    if int(visuals.get("max_channel_delta_lsb", 999999)) > 1:
        raise ValueError("indexed raster channel delta exceeds one LSB")

    if indexed_runtime.get("runtime_building_planar_role_surface_indexing_result") != "CANDIDATE_INDEXED_AFTER_FINAL_NORMAL_GENERATION":
        raise ValueError("indexed target-host marker missing")
    if indexed_runtime.get("environment_building_planar_role_representation_id") != REPRESENTATION_ID:
        raise ValueError("indexed runtime representation drift")
    if indexed_runtime.get("environment_building_planar_role_hard_surface_head") != HARD_SURFACE_HEAD:
        raise ValueError("indexed runtime Hard-Surface provenance drift")
    if indexed_runtime.get("environment_building_planar_role_materials_head") != MATERIALS_HEAD:
        raise ValueError("indexed runtime Materials provenance drift")

    samples = indexed_runtime.get("samples", [])
    if len(samples) != 17:
        raise ValueError(f"expected 17 current-world states, got {len(samples)}")

    context_count = 0
    receipt_after = None
    for sample in samples:
        row = find_building(sample)
        receipt = row.get("runtime_building_planar_role_surface_indexing", {})
        if receipt.get("schema") != RUNTIME_RECEIPT_SCHEMA:
            raise ValueError("per-state indexing receipt schema drift")
        if receipt.get("environment_parent_head") != UNINDEXED_ENVIRONMENT_HEAD:
            raise ValueError("per-state Environment parent drift")
        if receipt.get("building_hard_surface_head") != HARD_SURFACE_HEAD:
            raise ValueError("per-state Hard-Surface identity drift")
        if receipt.get("building_materials_head") != MATERIALS_HEAD:
            raise ValueError("per-state Materials identity drift")
        if receipt.get("representation_id") != REPRESENTATION_ID:
            raise ValueError("per-state representation identity drift")
        this_after = receipt.get("after", {})
        if this_after.get("surface_count") != 5 or this_after.get("total_vertices") != 312 or this_after.get("total_indices") != 1008 or this_after.get("total_primitives") != 336:
            raise ValueError("per-state indexed storage drift")
        if receipt_after is None:
            receipt_after = this_after
        elif this_after != receipt_after:
            raise ValueError("indexed storage changed across current-world states")
        for modes in sample.get("contexts", {}).values():
            context_count += len(modes)
    if context_count != 68:
        raise ValueError(f"expected 68 state/camera/presentation contexts, got {context_count}")

    return {
        "schema": SCHEMA,
        "state": ENVIRONMENT_PASS,
        "hold": ENVIRONMENT_HOLD,
        "exact_environment_head": exact_head,
        "runtime_donor_head": RUNTIME_DONOR_HEAD,
        "unindexed_environment_parent_head": UNINDEXED_ENVIRONMENT_HEAD,
        "active_segmented_rollback_head": ACTIVE_ROLLBACK_HEAD,
        "building_hard_surface_head": HARD_SURFACE_HEAD,
        "building_materials_head": MATERIALS_HEAD,
        "representation_id": REPRESENTATION_ID,
        "review_target": "INDEXED_POST_NORMAL_PER_SURFACE_PLANAR_ROLE_RECEIVER",
        "environment_adoption": False,
        "world_observations": {
            "state_count": 17,
            "context_count": 68,
            "building_surface_count": 5,
            "building_triangle_count": 336,
            "stored_vertices": 312,
            "indices": 1008,
            "indexed_vs_unindexed_buffer_bytes": -11904,
            "indexed_vs_active_buffer_bytes": -8304,
            "indexed_vs_active_primitives": 180,
            "max_indexing_changed_pixels_per_frame": int(visuals["max_changed_pixels"]),
            "max_indexing_pixels_over_1_lsb": int(visuals["max_pixels_over_1_lsb"]),
            "max_indexing_channel_delta_lsb": int(visuals["max_channel_delta_lsb"]),
        },
        "authority": {
            "environment": "receiving composition / rollback / review-target selection only",
            "hard_surface": "representation identity and manufactured-surface intent",
            "materials": "five-role material profile",
            "runtime": "storage / primitive / device-cost evidence",
            "art_direction": "visual preference",
            "visual_qa": "independent perceptual acceptance",
            "technical_art": "transport/import equivalence",
        },
        "handoff": [
            "Independent Visual QA: inspect exact indexed planar-role current-world frames and verify the <=1-LSB storage rewrite does not introduce hard-edge/highlight/camera regressions.",
            "Technical Art: prove exact indexed planar-role transport/import identity if the representation leaves this procedural Godot receiver path.",
            "Runtime: retain +180 primitive residual and target-device performance as separate acceptance gates.",
        ],
        "truth_boundary": (
            "Environment now binds the exact Runtime-proven post-normal indexed planar-role Building as the current review target in the existing multi-asset world. "
            "The active segmented receiver remains the rollback/default baseline. The exact five material roles, Nature, indexed Object, visible footprint cue, Weather, route, cameras and lighting are not reauthored here. "
            "A review-ready Environment PASS does not substitute for independent QA, Technical-Art transport, residual primitive/device acceptance, CANON or production readiness."
        ),
        "four_root_gate": {
            "truth": "Nonzero one-LSB raster differences and the +180 primitive residual remain explicit beside the buffer win.",
            "agency_non_domination": "Environment selects a review target only; Art, QA, Runtime, Hard Surface, Materials and Technical Art retain their authorities.",
            "continuity": "Active segmented, unindexed planar-role and indexed planar-role identities remain separately named and rollbackable.",
            "wisdom_before_speed": "Use the cheaper indexed review receiver without silently defaulting it before the remaining independent gates close.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-report", type=Path, required=True)
    parser.add_argument("--indexed-runtime", type=Path, required=True)
    parser.add_argument("--exact-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(load(args.runtime_report), load(args.indexed_runtime), args.exact_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
