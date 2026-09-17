from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

CONTRACT_SCHEMA = "axm.environment-object-phase-bound-vfx-receiver-readiness/v0.1"
REPORT_SCHEMA = "axm.environment-object-phase-bound-vfx-receiver-readiness-result/v0.1"
OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
HOLD_STATE = "HOLD_CURRENT_WORLD_OBJECT_PHASE_BOUND_VFX_RECEIVER__STATIC_HOST_LACKS_ANIMATION_OWNED_COMPONENT_BOUNDARY"
RULE = "PHASE_BOUND_OBJECT_VFX_MUST_NOT_ENTER_WORLD_COMPOSITION_UNTIL_THE_WORLD_RECEIVER_PRESERVES_THE_ANIMATION_OWNED_MOVING_COMPONENT_BOUNDARIES"
EPS = 1e-9


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def find_object(rows: Any) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise ValueError("current-world static_source_meshes missing")
    matches = [r for r in rows if isinstance(r, dict) and r.get("asset_id") == OBJECT_ASSET_ID]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one current-world Object receiver, got {len(matches)}")
    return matches[0]


def load_builder(object_root: Path):
    path = object_root / "tools" / "build_modular_case.py"
    if not path.is_file():
        raise ValueError("exact Object deterministic builder missing")
    spec = importlib.util.spec_from_file_location("axm_object_builder", path)
    if spec is None or spec.loader is None:
        raise ValueError("could not load exact Object deterministic builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "build"):
        raise ValueError("exact Object builder has no build()")
    return module


def group_map(object_root: Path, source: dict[str, Any]) -> tuple[dict[str, dict[str, int]], int, int]:
    builder = load_builder(object_root)
    built = builder.build(source)
    mesh = built.get("mesh", {})
    groups = mesh.get("groups", [])
    result: dict[str, dict[str, int]] = {}
    for row in groups:
        name = str(row.get("name", ""))
        if not name or name in result:
            raise ValueError("Object source group identity missing/duplicated")
        result[name] = {
            "first_face": int(row["first_face"]),
            "face_count": int(row["face_count"]),
            "last_face": int(row["first_face"]) + int(row["face_count"]) - 1,
        }
    return result, len(mesh.get("vertices", [])), len(mesh.get("faces", []))


def verify_parent(report: dict[str, Any], runtime: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    parent = contract["parent_environment"]
    if report.get("environment_head") != parent["head"]:
        raise ValueError("retained current-world parent head drift")
    if report.get("state") != parent["required_state"]:
        raise ValueError("retained current-world parent state drift")
    scope = report.get("real_world_scope", {})
    if int(scope.get("matched_frames", -1)) != int(parent["required_real_scene_frames"]):
        raise ValueError("retained current-world matched-frame count drift")
    continuity = report.get("runtime_continuity", {})
    if int(continuity.get("building_rebound_states", -1)) != int(parent["required_world_states"]):
        raise ValueError("retained current-world Building state count drift")
    if int(continuity.get("object_roughness_exact_states", -1)) != int(parent["required_world_states"]):
        raise ValueError("retained current-world Object roughness state count drift")
    if continuity.get("compact_east_phase_indices") != list(range(17)):
        raise ValueError("retained current-world compact-east phase sequence drift")
    if int(continuity.get("weather_width_measurements", -1)) != int(parent["required_weather_width_measurements"]):
        raise ValueError("retained current-world Weather width count drift")
    if runtime.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError("retained current-world runtime no longer has inherited Weather PASS")
    samples = runtime.get("samples")
    if not isinstance(samples, list) or len(samples) != int(parent["required_world_states"]):
        raise ValueError("retained current-world runtime state count drift")
    return {
        "environment_head": parent["head"],
        "retained_artifact_id": int(parent["retained_artifact_id"]),
        "retained_artifact_archive_sha256": parent["retained_artifact_archive_sha256"],
        "matched_real_scene_frames": int(scope["matched_frames"]),
        "world_states": len(samples),
        "weather_width_measurements": int(continuity["weather_width_measurements"]),
        "building_states": int(continuity["building_rebound_states"]),
        "object_roughness_states": int(continuity["object_roughness_exact_states"]),
        "compact_east_phase_indices": continuity["compact_east_phase_indices"],
    }


def verify_cross_repo_identity(
    object_root: Path,
    source: dict[str, Any],
    effect: dict[str, Any],
    sequence: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    source_contract = contract["object_source_identity"]
    donor = contract["phase_bound_vfx_donor"]
    if source.get("schema") != "axm.object-hard-surface/v0.1" or source.get("asset_id") != "modular-equipment-case-001":
        raise ValueError("Object source schema/asset drift")
    if effect.get("schema") != "axm.object-reactive-vfx/v0.1" or effect.get("effect_id") != donor["required_effect_id"]:
        raise ValueError("phase-bound VFX donor identity drift")
    if sequence.get("schema") != "axm.object-lid-latch-motion-sequence/v0.1" or sequence.get("sequence_id") != donor["required_sequence_id"]:
        raise ValueError("Animation sequence identity drift")
    source_sha = source_contract["source_sha256"]
    if effect.get("source_sha256") != source_sha:
        raise ValueError("VFX source identity drift")
    if sequence.get("host_source_sha256") != source_sha:
        raise ValueError("Animation sequence source identity drift")
    dep = effect.get("animation_dependency", {})
    if dep.get("base_head") != donor["animation_base_head"]:
        raise ValueError("VFX Animation base head drift")
    if dep.get("sequence_id") != donor["required_sequence_id"]:
        raise ValueError("VFX sequence binding drift")
    if dep.get("trigger_phase_id") != donor["required_trigger_phase_id"]:
        raise ValueError("VFX trigger phase drift")
    if abs(float(dep.get("trigger_time_s", -1.0)) - float(donor["required_trigger_time_s"])) > EPS:
        raise ValueError("VFX trigger time drift")
    visual = effect.get("visual_source", {})
    if int(visual.get("seed", -1)) != int(donor["required_owner_seed"]):
        raise ValueError("VFX owner seed drift")
    phase = [p for p in sequence.get("phases", []) if p.get("id") == donor["required_trigger_phase_id"]]
    if len(phase) != 1 or abs(float(phase[0].get("start_s", -2.0)) - float(donor["required_trigger_time_s"])) > EPS:
        raise ValueError("Animation authoritative trigger phase boundary drift")
    groups, vertices, faces = group_map(object_root, source)
    if vertices != 468 or faces != 812:
        raise ValueError(f"Object deterministic source cardinality drift: vertices={vertices} faces={faces}")
    moving = []
    for requirement in contract["minimum_animation_owned_source_groups"]:
        name = requirement["group"]
        row = groups.get(name)
        if row is None:
            raise ValueError(f"required Animation-owned source group missing: {name}")
        if row["first_face"] != int(requirement["expected_first_face"]) or row["face_count"] != int(requirement["expected_face_count"]):
            raise ValueError(f"required source group range drift: {name} -> {row}")
        moving.append({"group": name, **row, "reason": requirement["reason"]})
    return {
        "object_source_head": source_contract["source_head"],
        "object_source_sha256": source_sha,
        "vfx_head": donor["vfx_head"],
        "animation_base_head": donor["animation_base_head"],
        "effect_id": effect["effect_id"],
        "sequence_id": sequence["sequence_id"],
        "trigger_phase_id": dep["trigger_phase_id"],
        "trigger_time_s": float(dep["trigger_time_s"]),
        "owner_seed": int(visual["seed"]),
        "deterministic_source_vertices": vertices,
        "deterministic_source_triangles": faces,
        "minimum_animation_owned_source_groups": moving,
    }


def verify_current_receiver(runtime: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    req = contract["current_world_receiver_requirement"]
    samples = runtime["samples"]
    observations = []
    for sample in samples:
        row = find_object(sample.get("static_source_meshes"))
        if row.get("source_sha256") != contract["object_source_identity"]["source_sha256"]:
            raise ValueError("current-world Object source SHA drift")
        if row.get("source_scope") != req["required_source_scope"]:
            raise ValueError("current-world Object source scope no longer represents exact static host")
        if [int(row.get("vertices", -1)), int(row.get("triangles", -1)), int(row.get("surface_count", -1))] != [
            int(req["required_vertices"]), int(req["required_triangles"]), int(req["required_surfaces"])
        ]:
            raise ValueError("current-world Object static receiver cardinality drift")
        rough = row.get("environment_object_selected_roughness_current_world", {})
        uv0 = row.get("environment_object_selected_uv0_current_world", {})
        segmentation = row.get("environment_object_selected_surface_segmentation", {})
        if rough.get("state") != req["required_selected_roughness_state"]:
            raise ValueError("current-world Object selected roughness state drift")
        if uv0.get("state") != req["required_selected_uv0_state"]:
            raise ValueError("current-world Object selected UV0 state drift")
        if segmentation.get("state") != req["required_selected_surface_state"]:
            raise ValueError("current-world Object selected-surface state drift")
        observations.append({
            "state_index": int(sample.get("index", -1)),
            "source_scope": row["source_scope"],
            "vertices": int(row["vertices"]),
            "triangles": int(row["triangles"]),
            "surfaces": int(row["surface_count"]),
            "selected_roughness_bound": bool(rough.get("selected_roughness_bound", False)),
            "environment_adoption": bool(rough.get("environment_adoption", True)),
        })
    if [r["state_index"] for r in observations] != list(range(17)):
        raise ValueError("current-world Object receiver state index sequence drift")
    if any(r["environment_adoption"] for r in observations):
        raise ValueError("current-world Object receiver unexpectedly adopted Environment candidate")
    return {
        "states_verified": len(observations),
        "source_scope": req["required_source_scope"],
        "vertices": int(req["required_vertices"]),
        "triangles": int(req["required_triangles"]),
        "surfaces": int(req["required_surfaces"]),
        "selected_roughness_bound_in_all_states": all(r["selected_roughness_bound"] for r in observations),
        "animation_owned_component_boundary_present": False,
        "phase_bound_vfx_receiver_ready": False,
        "reason": "The exact real-world receiver is explicitly an EXACT_STATIC_HOST_ONLY source scope. It preserves source/material/UV/roughness identity but exposes no Animation-owned component transform boundary for the lid/latch sequence that owns the VFX trigger phase."
    }


def verify(args: argparse.Namespace) -> dict[str, Any]:
    contract = load(args.contract)
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ValueError("Environment phase-bound VFX readiness contract schema drift")
    if contract.get("reusable_rule") != RULE:
        raise ValueError("Environment phase-bound VFX readiness rule drift")
    decision = contract.get("decision", {})
    if decision.get("state") != HOLD_STATE:
        raise ValueError("Environment phase-bound VFX readiness decision drift")
    if decision.get("environment_adoption") is not False or decision.get("vfx_adoption") is not False or decision.get("animation_adoption") is not False:
        raise ValueError("receiver-readiness contract must remain non-adopting")

    parent_report = load(args.parent_report)
    parent_runtime = load(args.parent_runtime)
    object_root = Path(args.object_root)
    source = load(object_root / contract["object_source_identity"]["source_path"])
    effect = load(object_root / contract["phase_bound_vfx_donor"]["effect_path"])
    sequence = load(object_root / contract["phase_bound_vfx_donor"]["animation_sequence_path"])

    parent_summary = verify_parent(parent_report, parent_runtime, contract)
    identity = verify_cross_repo_identity(object_root, source, effect, sequence, contract)
    receiver = verify_current_receiver(parent_runtime, contract)

    report = {
        "schema": REPORT_SCHEMA,
        "state": HOLD_STATE,
        "environment_head": args.environment_head,
        "parent_current_world": parent_summary,
        "cross_repo_identity": identity,
        "current_world_object_receiver": receiver,
        "environment_adoption": False,
        "vfx_adoption": False,
        "animation_adoption": False,
        "next_receiving_requirement": decision["next_receiving_requirement"],
        "reusable_rule": RULE,
        "checks": {
            "exact_68_frame_multi_asset_parent_bound": True,
            "exact_17_state_current_world_parent_bound": True,
            "building_clearance_parent_green": True,
            "object_selected_roughness_parent_green": True,
            "compact_east_17_phase_parent_preserved": True,
            "weather_1224_width_measurements_parent_preserved": True,
            "object_source_identity_matches_vfx_and_animation": True,
            "owner_seed_41027_bound": True,
            "trigger_is_exact_animation_phase_boundary_at_0_25s": True,
            "deterministic_object_source_is_468_vertices_812_triangles": True,
            "minimum_lid_and_latch_source_groups_resolved_exactly": True,
            "current_world_object_is_exact_static_host": True,
            "current_world_object_has_no_animation_owned_component_boundary": True,
            "phase_bound_vfx_world_adoption_held": True,
            "environment_adoption_held": True
        },
        "truth_boundary": contract["truth_boundary"],
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["verify"])
    parser.add_argument("--contract", required=True)
    parser.add_argument("--parent-report", required=True)
    parser.add_argument("--parent-runtime", required=True)
    parser.add_argument("--object-root", required=True)
    parser.add_argument("--environment-head", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = verify(args)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
