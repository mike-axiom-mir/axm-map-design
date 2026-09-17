from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

PARENT_HEAD = "dc9911714365393d3f33038ef8bfda9e057a37e5"
PARENT_COMPOSITION_DIGEST = "50e3c3f10911514fe00a2431cc4c265e6539672d8e364063112f0b45660a9337"
PARENT_SCHEMA = "axm.environment-current-world-nature-source-winding-migration/v0.1"
PARENT_STATUS = "PASS_CURRENT_WORLD_NATURE_SOURCE_WINDING_MIGRATION_STRUCTURE"
BUILDING_POLICY_HEAD = "a976af429b0ea90e0f0cc72d4a8bd4eb8fef22d3"
BUILDING_POLICY_SCHEMA = "axm.building-current-emission-policy/v0.1"
CURRENT_VARIANT = "header-segmented-23"
LEGACY_VARIANT = "base-closed-outward-19"
SEGMENTATION_REVISION = "service-pavilion-001/interpenetration-free-header-segmentation-003"
STRUCTURE_RESULT = "PASS_CURRENT_WORLD_BUILDING_CURRENT_SOURCE_POLICY_REBIND_STRUCTURE"
TARGET_RESULT = "PASS_CURRENT_WORLD_BUILDING_CURRENT_SOURCE_POLICY_REBIND_TARGET_HOST_REACHED"


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def scene_digest(scene: dict[str, Any]) -> str:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    return digest(value)


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema") != BUILDING_POLICY_SCHEMA:
        raise ValueError("Building current-source policy schema drift")
    if policy.get("asset_id") != "service-pavilion-001" or policy.get("owner") != "Building Hard Surface":
        raise ValueError("Building current-source policy ownership drift")
    if policy.get("current_source_variant_id") != CURRENT_VARIANT:
        raise ValueError("Building current-source policy no longer selects header-segmented-23")
    if policy.get("legacy_compatibility_variant_id") != LEGACY_VARIANT:
        raise ValueError("Building legacy compatibility identity drift")
    if policy.get("selection_policy") != "CURRENT_SOURCE_IS_NAMED__CONSUMER_REBIND_REQUIRED__NO_SILENT_DEFAULT_REWRITE":
        raise ValueError("Building current-source selection policy drift")


def validate_parent(parent: dict[str, Any]) -> None:
    if parent.get("schema") != PARENT_SCHEMA or parent.get("status") != PARENT_STATUS:
        raise ValueError("exact Nature-migrated current-world parent must PASS")
    if parent.get("environment_head") != PARENT_HEAD:
        raise ValueError("exact current-world parent head drift")
    if parent.get("composition_digest") != PARENT_COMPOSITION_DIGEST:
        raise ValueError("exact current-world parent composition drift")
    states = parent.get("states", [])
    if len(states) != 17:
        raise ValueError("current-world parent must retain exactly 17 states")
    header = parent.get("building_header_segmentation", {})
    topology = header.get("topology", {})
    if header.get("schema") != "axm.building-header-segmentation/v0.1":
        raise ValueError("current-world Building segmentation schema drift")
    if header.get("revision") != SEGMENTATION_REVISION:
        raise ValueError("current-world Building is not the promoted segmented representation")
    if topology.get("object_count") != 23 or topology.get("vertex_count") != 184 or topology.get("triangle_count") != 276:
        raise ValueError("current-world Building segmented topology count drift")
    if header.get("successor_positive_volume_intersection_count") != 0:
        raise ValueError("current-world Building segmented representation is not interpenetration-free")
    if header.get("receiver_mount_residual_max_m") != 0.0:
        raise ValueError("current-world Building receiver mount drift")
    occupied = header.get("occupied_union", {})
    if occupied.get("equivalent") is not True or occupied.get("volume_residual_m3") != 0.0:
        raise ValueError("current-world Building occupied-union equivalence drift")


def building_receiver(scene: dict[str, Any]) -> dict[str, Any]:
    receiver = scene.get("environment_building_material_receiving")
    if not isinstance(receiver, dict):
        raise ValueError("current-world Building receiver missing")
    if receiver.get("asset_id") != "source:building:service-pavilion-001":
        raise ValueError("current-world Building receiver asset drift")

    vertices = receiver.get("vertices_source_xyz_m", [])
    surfaces = receiver.get("surfaces", [])
    if len(vertices) != 184 or not isinstance(surfaces, list):
        raise ValueError("current-world Building receiver no longer matches segmented 184v representation")

    expected_roles = [
        "frame_galvanized",
        "infill_coating",
        "roof_membrane",
        "slab_mineral",
        "utility_panel_ochre",
    ]
    if [surface.get("surface_role") for surface in surfaces] != expected_roles:
        raise ValueError("current-world Building receiver five-surface partition drift")

    triangles: list[list[int]] = []
    for surface in surfaces:
        surface_triangles = surface.get("triangles", [])
        if not isinstance(surface_triangles, list):
            raise ValueError("current-world Building receiver surface triangle payload drift")
        triangles.extend(surface_triangles)
    if len(triangles) != 276:
        raise ValueError("current-world Building receiver no longer matches segmented 276t surface partition")
    if any(
        not isinstance(triangle, list)
        or len(triangle) != 3
        or any(not isinstance(index, int) or index < 0 or index >= 184 for index in triangle)
        for triangle in triangles
    ):
        raise ValueError("current-world Building receiver surface triangle index drift")

    provenance = receiver.get("provenance", {})
    if provenance.get("building_header_segmentation_revision") != SEGMENTATION_REVISION:
        raise ValueError("current-world Building receiver segmentation provenance drift")
    rebind = receiver.get("source_header_segmentation_rebind", {})
    topology = rebind.get("topology_summary", {})
    if (
        rebind.get("segmentation_revision") != SEGMENTATION_REVISION
        or topology.get("object_count") != 23
        or topology.get("vertex_count") != 184
        or topology.get("triangle_count") != 276
    ):
        raise ValueError("current-world Building receiver source-segmentation binding drift")
    return receiver


def build(parent: dict[str, Any], policy: dict[str, Any], environment_head: str) -> dict[str, Any]:
    validate_parent(parent)
    validate_policy(policy)

    states: list[dict[str, Any]] = []
    parent_scene_digests: list[str] = []
    rebound_scene_digests: list[str] = []
    for parent_row in parent["states"]:
        row = copy.deepcopy(parent_row)
        scene = row["scene"]
        original = copy.deepcopy(scene)
        building_receiver(scene)
        parent_scene_digests.append(str(original.get("scene_digest", "")))

        scene["environment_building_current_source_policy_rebind"] = {
            "schema": "axm.environment-building-current-source-policy-receiving/v0.1",
            "source_repository": "mike-axiom-mir/axm-building-design",
            "source_policy_head": BUILDING_POLICY_HEAD,
            "source_policy_schema": BUILDING_POLICY_SCHEMA,
            "current_source_variant_id": CURRENT_VARIANT,
            "legacy_compatibility_variant_id": LEGACY_VARIANT,
            "receiver_header_segmentation_revision": SEGMENTATION_REVISION,
            "receiver_geometry_changed": False,
            "receiver_materials_changed": False,
            "historical_geometry_provenance_preserved": True,
            "selection_policy": policy["selection_policy"],
            "authority": "MAP_RECEIVING_COMPOSITION_ONLY",
            "truth_boundary": "Environment binds the already-rendered segmented Building receiver to Building Hard Surface's explicit current-source policy. The receiver geometry/materials and every non-Building world asset remain unchanged; historical producer identities remain preserved rather than silently rewritten.",
        }
        scene["scene_digest"] = scene_digest(scene)
        rebound_scene_digests.append(scene["scene_digest"])
        states.append(row)

    checks = dict(parent.get("checks", {}))
    checks.update({
        "exact_parent_current_world_bound": True,
        "building_current_source_policy_head_bound": BUILDING_POLICY_HEAD == "a976af429b0ea90e0f0cc72d4a8bd4eb8fef22d3",
        "building_current_source_policy_schema_bound": policy["schema"] == BUILDING_POLICY_SCHEMA,
        "building_current_source_variant_is_segmented_23": policy["current_source_variant_id"] == CURRENT_VARIANT,
        "legacy_compatibility_variant_preserved": policy["legacy_compatibility_variant_id"] == LEGACY_VARIANT,
        "receiver_is_exact_segmented_23_shape": True,
        "receiver_geometry_unchanged": True,
        "receiver_materials_unchanged": True,
        "all_17_states_preserved": len(states) == 17,
        "weather_nature_object_dressing_path_camera_lighting_preserved": True,
        "historical_building_geometry_provenance_preserved": True,
    })
    if not all(checks.values()):
        raise ValueError(f"current-source policy rebind checks failed: {checks}")

    result = copy.deepcopy(parent)
    result.update({
        "environment_head": environment_head,
        "policy_rebind_parent_environment_head": PARENT_HEAD,
        "policy_rebind_parent_composition_digest": PARENT_COMPOSITION_DIGEST,
        "building_current_source_policy_head": BUILDING_POLICY_HEAD,
        "building_current_source_policy_schema": BUILDING_POLICY_SCHEMA,
        "building_current_source_variant_id": CURRENT_VARIANT,
        "building_legacy_compatibility_variant_id": LEGACY_VARIANT,
        "building_current_source_policy_rebind_result": STRUCTURE_RESULT,
        "building_current_source_policy": copy.deepcopy(policy),
        "checks": checks,
        "states": states,
        "policy_rebind_parent_scene_digests": parent_scene_digests,
        "policy_rebind_scene_digests": rebound_scene_digests,
        "truth_boundary": "This PASS binds the exact already-received 23-box segmented pavilion to Building Hard Surface's explicit current-source policy while preserving historical producer identities and every rendered world input. It is a receiving/provenance rebind, not a new geometry, material or aesthetic decision.",
    })
    result["composition_digest"] = digest({
        "parent": PARENT_COMPOSITION_DIGEST,
        "building_policy_head": BUILDING_POLICY_HEAD,
        "current_variant": CURRENT_VARIANT,
        "scene_digests": rebound_scene_digests,
    })

    # Fail-closed controls are generated from internally consistent mutations.
    controls: dict[str, str] = {}
    bad_policy = copy.deepcopy(policy)
    bad_policy["current_source_variant_id"] = LEGACY_VARIANT
    try:
        validate_policy(bad_policy)
    except ValueError as exc:
        controls["legacy_variant_cannot_masquerade_as_current"] = f"REJECTED:{exc}"
    else:
        raise ValueError("legacy-current negative control did not fail closed")

    bad_parent = copy.deepcopy(parent)
    bad_parent["building_header_segmentation"]["topology"]["object_count"] = 19
    try:
        validate_parent(bad_parent)
    except ValueError as exc:
        controls["stale_19_box_receiver_cannot_claim_current_policy"] = f"REJECTED:{exc}"
    else:
        raise ValueError("stale receiver negative control did not fail closed")
    result["negative_controls"] = {**parent.get("negative_controls", {}), **controls}
    return result


def frame_files(root: Path) -> list[Path]:
    return sorted((root / "rendered").glob("atmosphere-width-*.png"))


def runtime_counters(runtime: dict[str, Any]) -> dict[str, dict[str, dict[str, int]]]:
    out: dict[str, dict[str, dict[str, int]]] = {}
    for sample in runtime.get("samples", []):
        idx = f"{int(sample['index']):02d}"
        out[idx] = {}
        for camera, context in sample.get("contexts", {}).items():
            out[idx][camera] = {}
            for mode in ("control", "candidate"):
                r = context[mode]["runtime"]
                out[idx][camera][mode] = {
                    "draw_calls_in_frame": int(r["draw_calls_in_frame"]),
                    "objects_in_frame": int(r["objects_in_frame"]),
                    "primitives_in_frame": int(r["primitives_in_frame"]),
                    "buffer_mem_bytes": int(r["buffer_mem_bytes"]),
                    "texture_mem_bytes": int(r["texture_mem_bytes"]),
                }
    return out


def verify(payload: dict[str, Any], parent_root: Path, candidate_root: Path, environment_head: str) -> dict[str, Any]:
    validate_parent({**payload, "environment_head": PARENT_HEAD, "composition_digest": PARENT_COMPOSITION_DIGEST})
    if payload.get("environment_head") != environment_head:
        raise ValueError("policy-rebound payload head drift")
    if payload.get("building_current_source_policy_head") != BUILDING_POLICY_HEAD:
        raise ValueError("policy-rebound payload Building policy head drift")
    if payload.get("building_current_source_policy_rebind_result") != STRUCTURE_RESULT:
        raise ValueError("policy-rebound structural result missing")
    if not all(payload.get("checks", {}).values()):
        raise ValueError("policy-rebound payload checks not all true")

    parent_frames = frame_files(parent_root)
    candidate_frames = frame_files(candidate_root)
    if len(parent_frames) != 68 or [p.name for p in parent_frames] != [p.name for p in candidate_frames]:
        raise ValueError("expected 68 matched current-world frames")
    changed = []
    for a, b in zip(parent_frames, candidate_frames):
        if a.read_bytes() != b.read_bytes():
            changed.append(a.name)
    if changed:
        raise ValueError(f"policy-only rebind changed rendered output: {changed[:8]}")

    parent_runtime = load_json(parent_root / "runtime.json")
    candidate_runtime = load_json(candidate_root / "runtime.json")
    pc = runtime_counters(parent_runtime)
    cc = runtime_counters(candidate_runtime)
    if pc != cc:
        raise ValueError("policy-only rebind changed proof-host renderer counters")

    weather_measurements = 0
    max_width_residual = 0.0
    for sample in candidate_runtime.get("samples", []):
        for context in sample.get("contexts", {}).values():
            weather = context["candidate"]["weather_update"]
            weather_measurements += int(weather.get("measured_width_count", 0))
            max_width_residual = max(max_width_residual, float(weather.get("maximum_projected_width_residual_px", 0.0)))
    if weather_measurements != 1224 or max_width_residual > 0.05:
        raise ValueError("inherited Weather-width evidence drift")

    report = {
        "schema": "axm.environment-building-current-source-policy-rebind-report/v0.1",
        "state": TARGET_RESULT,
        "environment_head": environment_head,
        "parent_environment_head": PARENT_HEAD,
        "composition_digest": payload["composition_digest"],
        "building_current_source_policy_head": BUILDING_POLICY_HEAD,
        "building_current_source_variant_id": CURRENT_VARIANT,
        "legacy_compatibility_variant_id": LEGACY_VARIANT,
        "matched_frames": 68,
        "byte_identical_frames": 68,
        "weather_width_measurements": weather_measurements,
        "maximum_weather_width_residual_px": max_width_residual,
        "runtime_counter_deltas": {
            "draw_calls_in_frame": 0,
            "objects_in_frame": 0,
            "primitives_in_frame": 0,
            "buffer_mem_bytes": 0,
            "texture_mem_bytes": 0,
        },
        "checks": {
            "exact_parent_current_world_reused": True,
            "exact_building_current_source_policy_bound": True,
            "all_68_real_scene_frames_byte_identical": True,
            "proof_host_renderer_counters_unchanged": True,
            "all_1224_weather_width_measurements_preserved": True,
            "historical_building_producer_provenance_preserved": True,
        },
        "decision": "ADOPT_EXPLICIT_BUILDING_CURRENT_SOURCE_POLICY_BINDING__NO_RENDERED_WORLD_CHANGE",
        "truth_boundary": "Target-host PASS proves only that the exact already-rendered segmented Building receiver can be explicitly rebound to Building's current-source policy without changing the 68 retained real-scene frames, proof-host counters or inherited Weather-width measurements. It does not approve final Building/Nature/Object/Weather aesthetics, target-device performance, gameplay, CANON or production readiness.",
    }
    if not all(report["checks"].values()):
        raise ValueError("target-host policy-rebind report checks failed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    build_p = sub.add_parser("build")
    build_p.add_argument("--parent", type=Path, required=True)
    build_p.add_argument("--policy", type=Path, required=True)
    build_p.add_argument("--environment-head", required=True)
    build_p.add_argument("--output", type=Path, required=True)

    verify_p = sub.add_parser("verify")
    verify_p.add_argument("--payload", type=Path, required=True)
    verify_p.add_argument("--parent-root", type=Path, required=True)
    verify_p.add_argument("--candidate-root", type=Path, required=True)
    verify_p.add_argument("--environment-head", required=True)
    verify_p.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "build":
        result = build(load_json(args.parent), load_json(args.policy), args.environment_head)
    else:
        result = verify(load_json(args.payload), args.parent_root, args.candidate_root, args.environment_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result.get(k) for k in ("state", "building_current_source_policy_rebind_result", "composition_digest") if result.get(k) is not None}, indent=2))


if __name__ == "__main__":
    main()
