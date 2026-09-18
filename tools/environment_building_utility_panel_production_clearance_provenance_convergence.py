from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-building-utility-panel-production-clearance-provenance-convergence/v0.1"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def eqf(a: float, b: float, eps: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= eps


def eqlist(a: Any, b: list[float], eps: float = 1e-6) -> bool:
    return isinstance(a, list) and len(a) == len(b) and all(eqf(x, y, eps) for x, y in zip(a, b))


def sha(path: Path) -> str:
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


def building_rows(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for sample in runtime.get("samples", []):
        found = [
            r
            for r in sample.get("static_source_meshes", [])
            if r.get("asset_id") == "source:building:service-pavilion-001"
        ]
        if len(found) != 1:
            raise AssertionError("each current-world state must contain exactly one Building receiver")
        rows.append(found[0])
    if len(rows) != 17:
        raise AssertionError(f"expected 17 current-world states, got {len(rows)}")
    return rows


def validate_runtime(runtime: dict[str, Any], c: dict[str, Any], label: str) -> dict[str, Any]:
    subj = c["semantic_subject"]
    fresh = c["fresh_owner"]
    required_assets = {
        "source:nature:compact-east-tree-neutral-001",
        "source:nature:east-rear-tree-neutral-001",
        "source:object:modular-equipment-case-001",
        "source:building:service-pavilion-001",
        "environment:dressing:west-object-service-footprint-frame-001",
    }
    if runtime.get("environment_building_current_source_variant_id") != subj["building_variant"]:
        raise AssertionError(f"{label}: Building receiver variant drift")
    if runtime.get("environment_building_utility_panel_clearance_source_head") != fresh["hard_surface_head"]:
        raise AssertionError(f"{label}: Hard Surface evidence head drift")
    if runtime.get("environment_building_utility_panel_clearance_source_content_head") != fresh["source_content_head"]:
        raise AssertionError(f"{label}: semantic source head drift")
    if runtime.get("environment_building_utility_panel_clearance_current_world_state") != "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_CLEARANCE_REBIND_RECEIVER__VISUAL_OBSERVABILITY_CHARACTERIZED__ADOPTION_HELD":
        raise AssertionError(f"{label}: current-world clearance receiver state drift")
    if runtime.get("environment_building_utility_panel_clearance_adoption") is not False:
        raise AssertionError(f"{label}: Environment adoption inflated")

    rows = building_rows(runtime)
    for i, (sample, row) in enumerate(zip(runtime["samples"], rows)):
        assets = {r.get("asset_id") for r in sample.get("static_source_meshes", [])}
        if not required_assets.issubset(assets):
            raise AssertionError(f"{label}: state {i} lost multi-asset current-world scope")
        if (
            int(row.get("vertices", -1)) != subj["building_vertices"]
            or int(row.get("triangles", -1)) != subj["building_triangles"]
            or int(row.get("surface_count", -1)) != subj["building_surfaces"]
        ):
            raise AssertionError(f"{label}: Building structural receiver drift")

        clearance = row.get("environment_building_utility_panel_clearance_current_world", {})
        if clearance.get("building_source_head") != fresh["hard_surface_head"]:
            raise AssertionError(f"{label}: nested Hard Surface head drift")
        if clearance.get("building_source_content_head") != fresh["source_content_head"]:
            raise AssertionError(f"{label}: nested semantic source head drift")
        if not eqlist(
            clearance.get("front_successor_center_source_xyz_m"),
            subj["front_successor_center_source_xyz_m"],
        ):
            raise AssertionError(f"{label}: front corrected panel center drift")
        if not eqlist(
            clearance.get("east_successor_center_source_xyz_m"),
            subj["east_successor_center_source_xyz_m"],
        ):
            raise AssertionError(f"{label}: east corrected panel center drift")
        if not eqlist(
            clearance.get("front_translation_source_xyz_m"),
            subj["front_translation_source_xyz_m"],
        ):
            raise AssertionError(f"{label}: front receiver-normal translation drift")
        if not eqlist(
            clearance.get("east_translation_source_xyz_m"),
            subj["east_translation_source_xyz_m"],
        ):
            raise AssertionError(f"{label}: east receiver-normal translation drift")
        if clearance.get("environment_adoption") is not False:
            raise AssertionError(f"{label}: nested Environment adoption inflated")

    return {
        "states": len(rows),
        "assets_per_state_minimum": len(required_assets),
        "weather_variant_seed": runtime.get("weather_variant_seed"),
        "weather_variant_layout_digest": runtime.get("weather_variant_layout_digest"),
        "source_width_profile_digest": runtime.get("source_width_profile_digest"),
        "object_animation_head": runtime.get("technical_art_object_motion_animation_head"),
        "object_sequence_digest": runtime.get("technical_art_object_motion_sequence_digest"),
        "compact_east_vfx_head": runtime.get("environment_compact_east_visual_response_vfx_head"),
        "procedural_head_retained_in_runtime": runtime.get(
            "environment_building_utility_panel_clearance_procedural_head"
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", required=True)
    ap.add_argument("--current-world-root", required=True)
    ap.add_argument("--reviewed-production-world-root", required=True)
    ap.add_argument("--fresh-owner-root", required=True)
    ap.add_argument("--current-environment-rebind-contract", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    c = load(Path(args.contract))
    if c.get("schema") != SCHEMA:
        raise AssertionError("contract schema drift")
    expected = c["expected_result"]
    subj = c["semantic_subject"]
    env = c["environment"]
    fresh = c["fresh_owner"]

    current_root = Path(args.current_world_root)
    reviewed_root = Path(args.reviewed_production_world_root)
    owner_root = Path(args.fresh_owner_root)

    current_head = find_one(current_root, "exact-head.txt").read_text().strip()
    owner_head = find_one(owner_root, "exact-head.txt").read_text().strip()
    reviewed_head = find_one(reviewed_root, "exact-head.txt").read_text().strip()
    if current_head != env["prior_head"]:
        raise AssertionError(f"current Environment artifact head drift: {current_head}")
    if owner_head != fresh["materials_head"]:
        raise AssertionError(f"fresh Materials artifact head drift: {owner_head}")
    if reviewed_head != "75bf511be8a89778ab40868707a68e80a210608a":
        raise AssertionError(f"reviewed production owner artifact head drift: {reviewed_head}")

    fresh_contract = load(
        find_one(owner_root, "building_utility_panel_production_surface_clearance_successor_001.json")
    )
    target = load(find_one(owner_root, "target_host_report.json"))
    proc = load(find_one(owner_root, "procedural_rebind_summary.json"))
    generation = load(find_one(owner_root, "production_surface_generation_report.json"))
    fresh_png = find_one(owner_root, "utility-panel-production-surface-001.png")

    if fresh_contract["surface_recipe"]["expected_png_sha256"] != subj["png_sha256"]:
        raise AssertionError("fresh owner production PNG identity drift")
    if fresh_contract["surface_recipe"]["expected_rgba8_sha256"] != subj["rgba8_sha256"]:
        raise AssertionError("fresh owner production RGBA8 identity drift")
    if fresh_contract["hard_surface_owner"]["current_evidence_head"] != fresh["hard_surface_head"]:
        raise AssertionError("fresh owner Hard Surface head drift")
    if fresh_contract["geometry_owner"]["current_head"] != fresh["geometry_head"]:
        raise AssertionError("fresh owner Geometry head drift")
    if fresh_contract["procedural_owner"]["current_head"] != fresh["procedural_head"]:
        raise AssertionError("fresh owner Procedural head drift")
    if (
        fresh_contract["truth_boundary"]["environment_adoption"] is not False
        or fresh_contract["truth_boundary"]["visual_qa_acceptance"] is not False
        or fresh_contract["truth_boundary"]["runtime_acceptance"] is not False
    ):
        raise AssertionError("fresh owner authority boundary weakened")
    if sha(fresh_png) != subj["png_sha256"]:
        raise AssertionError("fresh owner PNG bytes drift")
    if (
        generation["stats"]["png_sha256"] != subj["png_sha256"]
        or generation["stats"]["rgba8_sha256"] != subj["rgba8_sha256"]
    ):
        raise AssertionError("fresh owner generation identity drift")
    if target["state"] != "PASS_TARGET_HOST_BUILDING_UTILITY_PANEL_PRODUCTION_SURFACE_CLEARANCE_SUCCESSOR_REVIEW":
        raise AssertionError("fresh owner clearance-successor target-host review not green")
    if target["texture_png_sha256"] != subj["png_sha256"]:
        raise AssertionError("fresh owner target-host texture identity drift")
    if target["total_placement_shift_pixels_gt_1lsb"] <= 0:
        raise AssertionError("fresh owner placement successor was not visually observable")
    if proc["result"] != "PASS_BOUNDED_BUILDING_UTILITY_PANEL_CLEARANCE_REBIND_FAMILY":
        raise AssertionError("fresh Procedural family is not green")
    if proc["source_authority_head"] != fresh["hard_surface_head"]:
        raise AssertionError("fresh Procedural source-authority head drift")

    outputs = {row["receiver_id"]: row for row in proc["outputs"]}
    if set(outputs) != {"front-utility-bay", "east-utility-bay"}:
        raise AssertionError("fresh Procedural receiver family drift")
    if not eqlist(
        outputs["front-utility-bay"]["successor_panel_center_m"],
        subj["front_successor_center_source_xyz_m"],
    ):
        raise AssertionError("fresh Procedural front center drift")
    if not eqlist(
        outputs["east-utility-bay"]["successor_panel_center_m"],
        subj["east_successor_center_source_xyz_m"],
    ):
        raise AssertionError("fresh Procedural east center drift")
    if not eqf(
        outputs["front-utility-bay"]["successor_physical_body_gap_m"], 0.02
    ) or not eqf(outputs["east-utility-bay"]["successor_physical_body_gap_m"], 0.02):
        raise AssertionError("fresh source-owned physical body-gap drift")

    reviewed_report = load(find_one(reviewed_root, "current-world-three-way-report.json"))
    if (
        reviewed_report["result"]
        != "PASS_BUILDING_UTILITY_PANEL_PRODUCTION_SURFACE_SUCCESSOR_CURRENT_WORLD_THREE_WAY_REVIEW_READY__HOLD_ART_QA_ENV_RUNTIME_ADOPTION"
    ):
        raise AssertionError("reviewed production real-world result drift")
    if reviewed_report["environment_head"] != env["reviewed_production_world_environment_head"]:
        raise AssertionError("reviewed production Environment head drift")
    if (
        reviewed_report["texture"]["png_sha256"] != subj["png_sha256"]
        or reviewed_report["texture"]["rgba8_sha256"] != subj["rgba8_sha256"]
    ):
        raise AssertionError("reviewed real-world production texture identity drift")
    if (
        int(reviewed_report["review"]["rendered_frames_per_variant"]) != 68
        or int(reviewed_report["review"]["successor_visible_frames"]) != 68
    ):
        raise AssertionError("reviewed real-world frame coverage drift")
    if reviewed_report["review"]["unrelated_current_world_runtime_identity_equal"] is not True:
        raise AssertionError("reviewed production real-world unrelated identity equality lost")
    reviewed_runtime = load(
        reviewed_root
        / "evidence/building_utility_panel_production_surface_001/successor/runtime.json"
    )
    reviewed_sig = validate_runtime(reviewed_runtime, c, "reviewed-production-world")

    current_report = load(find_one(current_root, "report.json"))
    if int(current_report["current_world"]["rendered_frames_per_variant"]) != 68:
        raise AssertionError("current Environment real-world frame coverage drift")
    current_control = load(
        current_root
        / "evidence/environment_building_utility_panel_material_current_world_ab_001/control/runtime.json"
    )
    current_candidate = load(
        current_root
        / "evidence/environment_building_utility_panel_material_current_world_ab_001/candidate/runtime.json"
    )
    current_control_sig = validate_runtime(current_control, c, "current-environment-control")
    current_candidate_sig = validate_runtime(current_candidate, c, "current-environment-candidate")
    for key in (
        "weather_variant_seed",
        "weather_variant_layout_digest",
        "source_width_profile_digest",
        "object_animation_head",
        "object_sequence_digest",
        "compact_east_vfx_head",
    ):
        if (
            reviewed_sig[key] != current_control_sig[key]
            or reviewed_sig[key] != current_candidate_sig[key]
        ):
            raise AssertionError(f"unrelated multi-asset current-world identity drift: {key}")

    rebind = load(Path(args.current_environment_rebind_contract))
    old_png = rebind["materials_owner"]["png_sha256"]
    old_rgba = rebind["materials_owner"]["rgba8_sha256"]
    if old_png != subj["png_sha256"] or old_rgba != subj["rgba8_sha256"]:
        raise AssertionError("Environment current receiving production bytes differ from fresh owner")
    if rebind["environment"]["building_variant"] != subj["building_variant"]:
        raise AssertionError("Environment current receiving Building variant drift")
    if rebind["promotion"]["environment_adoption"] is not False:
        raise AssertionError("existing Environment adoption boundary weakened")

    old_proc = current_candidate_sig["procedural_head_retained_in_runtime"]
    if old_proc == fresh["procedural_head"]:
        raise AssertionError(
            "expected a stale evidence-head provenance seam, but current world already records fresh Procedural head"
        )

    report = {
        "schema": SCHEMA,
        "result": expected,
        "reusable_rule": c["reusable_rule"],
        "environment_prior_head": env["prior_head"],
        "fresh_materials_evidence_head": fresh["materials_head"],
        "reviewed_materials_content_head": reviewed_head,
        "hard_surface_head": fresh["hard_surface_head"],
        "geometry_head": fresh["geometry_head"],
        "procedural_evidence_head_before": old_proc,
        "procedural_evidence_head_after": fresh["procedural_head"],
        "semantic_subject": subj,
        "fresh_owner_evidence": {
            "target_host_result": target["state"],
            "target_host_total_placement_shift_pixels_gt_1lsb": target[
                "total_placement_shift_pixels_gt_1lsb"
            ],
            "procedural_family_digest": proc["canonical_family_digest"],
            "front_output_digest": outputs["front-utility-bay"]["output_digest"],
            "east_output_digest": outputs["east-utility-bay"]["output_digest"],
            "production_surface_bytes_changed": False,
            "source_geometry_changed_by_materials": False,
        },
        "real_scene_evidence": {
            "reviewed_production_world_environment_head": reviewed_report["environment_head"],
            "reviewed_production_world_frames_per_variant": reviewed_report["review"][
                "rendered_frames_per_variant"
            ],
            "reviewed_production_world_successor_visible_frames": reviewed_report["review"][
                "successor_visible_frames"
            ],
            "reviewed_production_world_scalar_to_successor_pixels_gt_1lsb": reviewed_report[
                "review"
            ]["total_changed_pixels_gt_1lsb"]["scalar_to_successor_gt1"],
            "current_environment_frames_per_variant": current_report["current_world"][
                "rendered_frames_per_variant"
            ],
            "current_environment_runtime_states_checked": 34,
            "current_environment_asset_scope": [
                "Building header-segmented-23 current receiver",
                "Nature compact-east current receiver",
                "Nature east-rear current receiver",
                "Object articulated current receiver",
                "Environment Object service dressing",
                "Weather source-width 17-state presentation",
            ],
            "unrelated_identity_signature": {
                k: reviewed_sig[k]
                for k in (
                    "weather_variant_seed",
                    "weather_variant_layout_digest",
                    "source_width_profile_digest",
                    "object_animation_head",
                    "object_sequence_digest",
                    "compact_east_vfx_head",
                )
            },
        },
        "decision": {
            "latest_owner_provenance_rebound": True,
            "current_world_semantic_content_changed": False,
            "new_world_rerender_required_for_this_provenance_rebind": False,
            "art_direction_head_transfer": False,
            "visual_qa_head_transfer": False,
            "runtime_target_device_transfer": False,
            "environment_adoption": False,
            "canon": False,
            "production_ready": False,
        },
        "truth_boundary": c["truth_boundary"],
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(expected)
    print(
        json.dumps(
            {
                "front_successor_center": subj["front_successor_center_source_xyz_m"],
                "east_successor_center": subj["east_successor_center_source_xyz_m"],
                "production_png_sha256": subj["png_sha256"],
                "fresh_placement_shift_pixels_gt_1lsb": target[
                    "total_placement_shift_pixels_gt_1lsb"
                ],
                "reviewed_production_world_frames": reviewed_report["review"][
                    "rendered_frames_per_variant"
                ],
                "current_environment_states_checked": 34,
                "stale_procedural_head": old_proc,
                "fresh_procedural_head": fresh["procedural_head"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
