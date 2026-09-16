from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-live-object-current-world-evidence/v0.1"
STATUS = "PASS_LIVE_WORLD_OBJECT_SOURCE_COMPOSITION_STRUCTURE"
TARGET_SCHEMA = "axm.environment-live-object-current-world-target-host/v0.1"
TARGET_STATUS = "PASS_LIVE_WORLD_OBJECT_SOURCE_COMPOSITION_TARGET_HOST"

EXPECTED_ATMOSPHERE_HEAD = "3e641a5ea7b2507a53e5ff1a8fba0f0f9c94abaf"
EXPECTED_OBJECT_MAP_HEAD = "85a2a0be959b4e39f9ffcf83da89078b604f9881"
EXPECTED_OBJECT_SOURCE_HEAD = "d3fa10a270faae7925811f44f03381fe5c5d0215"
EXPECTED_OBJECT_SOURCE_SHA256 = "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
EXPECTED_OBJECT_OBJ_SHA256 = "3e01ef3bf4935ee6aee7c56c03dc0b7f54c308e5ac2eb6a7583252a366901106"
EXPECTED_VFX_SEQUENCE_DIGEST = "f7f2cad01184e8651bcc722b755a2f3c2292ca13e81c7399579d7f42e0c19b30"
EXPECTED_REAR_MESH_DIGEST = "aa9d450a78fef722672ea9af0f9aca98b4c1a0ca3705661784f5f61f3e9b6a31"

WEST_PROXY_ID = "proxy:object-crate-west"
EAST_PROXY_ID = "proxy:object-crate-east"
OBJECT_SOURCE_ID = "source:object:modular-equipment-case-001"
REAR_SOURCE_ID = "source:nature:east-rear-tree-neutral-001"
CONTEXTS = ("path_eye", "elevated_oblique")


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _one(rows: list[dict[str, Any]], asset_id: str) -> dict[str, Any]:
    matches = [row for row in rows if row.get("asset_id") == asset_id]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {asset_id}, found {len(matches)}")
    return matches[0]


def _fixed_scene_fields_match(base: dict[str, Any], object_candidate: dict[str, Any]) -> bool:
    fields = (
        "readable_path",
        "cameras",
        "source_integration",
        "environment_replacement",
        "environment_rear_tree_culling_review",
        "weather_presentation",
    )
    return all(base.get(field) == object_candidate.get(field) for field in fields)


def build_payload(
    atmosphere: dict[str, Any],
    object_candidate: dict[str, Any],
    object_report: dict[str, Any],
    receiving_head: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if atmosphere.get("status") != "PASS_CURRENT_WORLD_DENSE_ATMOSPHERE_REBIND_STRUCTURE":
        raise ValueError("exact PR20 atmosphere structure must PASS first")
    if not all(atmosphere.get("checks", {}).values()):
        raise ValueError("exact PR20 atmosphere checks must all PASS")
    if atmosphere.get("dense_vfx_sequence_digest") != EXPECTED_VFX_SEQUENCE_DIGEST:
        raise ValueError("dense VFX sequence digest drift")
    if atmosphere.get("rear_migrated_mesh_digest") != EXPECTED_REAR_MESH_DIGEST:
        raise ValueError("rear-tree migrated mesh drift")

    if object_report.get("status") != "PASS_WEST_OBJECT_SOURCE_REPLACEMENT_STRUCTURE":
        raise ValueError("exact PR19 Object replacement structure must PASS first")
    if not all(object_report.get("checks", {}).values()):
        raise ValueError("exact PR19 Object replacement checks must all PASS")
    replacement = object_candidate.get("environment_object_replacement", {})
    if replacement.get("source_head") != EXPECTED_OBJECT_SOURCE_HEAD:
        raise ValueError("Object source donor head drift")
    if replacement.get("source_sha256") != EXPECTED_OBJECT_SOURCE_SHA256:
        raise ValueError("Object source digest drift")
    if replacement.get("obj_sha256") != EXPECTED_OBJECT_OBJ_SHA256:
        raise ValueError("Object OBJ digest drift")

    object_sources = object_candidate.get("additional_source_meshes", [])
    object_source = _one(object_sources, OBJECT_SOURCE_ID)
    if len(object_source.get("vertices_source_xyz_m", [])) != 468:
        raise ValueError("Object source vertex count drift")
    if len(object_source.get("triangles", [])) != 812:
        raise ValueError("Object source triangle count drift")

    states = atmosphere.get("states", [])
    if len(states) != 17:
        raise ValueError("exact atmosphere donor must retain 17 states")

    composed_states: list[dict[str, Any]] = []
    state_checks: list[dict[str, bool]] = []
    object_source_digest = digest(object_source)

    for row in states:
        base = row["scene"]
        expected_items = [item for item in base.get("items", []) if item.get("asset_id") != WEST_PROXY_ID]
        base_sources = base.get("additional_source_meshes", [])
        candidate_without_object = [
            source for source in object_sources if source.get("asset_id") != OBJECT_SOURCE_ID
        ]

        checks = {
            "west_proxy_present_in_atmosphere_donor": len(
                [item for item in base.get("items", []) if item.get("asset_id") == WEST_PROXY_ID]
            ) == 1,
            "object_candidate_items_are_exact_base_minus_west_proxy": object_candidate.get("items") == expected_items,
            "object_candidate_static_sources_are_exact_base_plus_object": candidate_without_object == base_sources,
            "fixed_scene_fields_match": _fixed_scene_fields_match(base, object_candidate),
            "east_object_proxy_preserved": len(
                [item for item in object_candidate.get("items", []) if item.get("asset_id") == EAST_PROXY_ID]
            ) == 1,
            "rear_tree_culling_contract_preserved": base.get("environment_rear_tree_culling_review")
            == object_candidate.get("environment_rear_tree_culling_review"),
        }
        if not all(checks.values()):
            raise ValueError(f"state {row.get('index')} cannot safely compose PR19 into PR20: {checks}")

        scene = copy.deepcopy(base)
        scene["schema"] = "axm.environment-live-object-current-world-state/v0.1"
        scene["study_id"] = f"environment-live-object-current-world-001-{int(row['index']):02d}"
        scene["items"] = copy.deepcopy(object_candidate["items"])
        scene["additional_source_meshes"] = copy.deepcopy(object_sources)
        scene["environment_object_replacement"] = copy.deepcopy(replacement)
        scene["environment_live_object_composition"] = {
            "atmosphere_donor_pr": 20,
            "atmosphere_donor_head": EXPECTED_ATMOSPHERE_HEAD,
            "object_environment_donor_pr": 19,
            "object_environment_donor_head": EXPECTED_OBJECT_MAP_HEAD,
            "object_source_head": EXPECTED_OBJECT_SOURCE_HEAD,
            "relationship": "EXACT_PR19_STATIC_OBJECT_REPLACEMENT_COMPOSED_INTO_EXACT_PR20_DYNAMIC_WORLD",
            "authority": "MAP_RECEIVING_COMPOSITION_ONLY",
        }
        scene["truth_boundary"] = (
            "This state composes the already-proven exact west Object structural source replacement into the "
            "already-proven exact 17-state visual-only Weather + west-sapling current-world sequence. It does not "
            "promote Object materials, articulation, attachments, physics, gameplay, physical weather, target-device "
            "performance, final art, CANON, production readiness, or Environment mastery."
        )
        scene.pop("scene_digest", None)
        scene["scene_digest"] = digest(scene)

        composed_states.append(
            {
                "index": int(row["index"]),
                "time_s": float(row["time_s"]),
                "sampling_role": row["sampling_role"],
                "weather_field_digest": row["weather_field_digest"],
                "sapling_mesh_digest": row["sapling_mesh_digest"],
                "scene": scene,
            }
        )
        state_checks.append(checks)

    first_scene = composed_states[0]["scene"]
    last_scene = composed_states[-1]["scene"]
    first_object = _one(first_scene["additional_source_meshes"], OBJECT_SOURCE_ID)
    checks = {
        "exact_atmosphere_pr20_identity_declared": EXPECTED_ATMOSPHERE_HEAD
        == "3e641a5ea7b2507a53e5ff1a8fba0f0f9c94abaf",
        "exact_object_environment_pr19_identity_declared": EXPECTED_OBJECT_MAP_HEAD
        == "85a2a0be959b4e39f9ffcf83da89078b604f9881",
        "exact_object_source_identity_preserved": replacement.get("source_head") == EXPECTED_OBJECT_SOURCE_HEAD
        and replacement.get("source_sha256") == EXPECTED_OBJECT_SOURCE_SHA256
        and replacement.get("obj_sha256") == EXPECTED_OBJECT_OBJ_SHA256,
        "all_17_states_composed": len(composed_states) == 17,
        "all_state_composition_checks_pass": len(state_checks) == 17
        and all(all(check.values()) for check in state_checks),
        "west_proxy_removed_all_states": all(
            not any(item.get("asset_id") == WEST_PROXY_ID for item in row["scene"].get("items", []))
            for row in composed_states
        ),
        "east_proxy_retained_all_states": all(
            len([item for item in row["scene"].get("items", []) if item.get("asset_id") == EAST_PROXY_ID]) == 1
            for row in composed_states
        ),
        "object_source_present_exactly_once_all_states": all(
            len(
                [
                    source
                    for source in row["scene"].get("additional_source_meshes", [])
                    if source.get("asset_id") == OBJECT_SOURCE_ID
                ]
            )
            == 1
            for row in composed_states
        ),
        "object_source_geometry_static_all_states": all(
            digest(_one(row["scene"]["additional_source_meshes"], OBJECT_SOURCE_ID)) == object_source_digest
            for row in composed_states
        ),
        "object_source_counts_exact": len(first_object["vertices_source_xyz_m"]) == 468
        and len(first_object["triangles"]) == 812,
        "weather_sequence_preserved_exactly": [
            row["weather_field_digest"] for row in composed_states
        ]
        == [row["weather_field_digest"] for row in states],
        "sapling_sequence_preserved_exactly": [
            row["sapling_mesh_digest"] for row in composed_states
        ]
        == [row["sapling_mesh_digest"] for row in states],
        "neutral_return_scene_keeps_same_object_identity": digest(
            _one(last_scene["additional_source_meshes"], OBJECT_SOURCE_ID)
        )
        == object_source_digest,
        "rear_tree_culling_target_preserved": first_scene.get(
            "environment_rear_tree_culling_review", {}
        ).get("target_asset_id")
        == REAR_SOURCE_ID
        and first_scene.get("environment_rear_tree_culling_review", {}).get("target_cull_mode") == "BACK",
    }

    payload = {
        "schema": SCHEMA,
        "study_id": "environment-live-object-current-world-001",
        "status": STATUS if all(checks.values()) else "FAIL",
        "receiving_head": receiving_head,
        "atmosphere_donor_pr": 20,
        "atmosphere_donor_head": EXPECTED_ATMOSPHERE_HEAD,
        "object_environment_donor_pr": 19,
        "object_environment_donor_head": EXPECTED_OBJECT_MAP_HEAD,
        "object_source_head": EXPECTED_OBJECT_SOURCE_HEAD,
        "object_source_sha256": EXPECTED_OBJECT_SOURCE_SHA256,
        "object_obj_sha256": EXPECTED_OBJECT_OBJ_SHA256,
        "dense_vfx_sequence_digest": EXPECTED_VFX_SEQUENCE_DIGEST,
        "environment_donor_head": atmosphere.get("environment_donor_head"),
        "dense_vfx_donor_head": atmosphere.get("dense_vfx_donor_head"),
        "nature_response_head": atmosphere.get("nature_response_head"),
        "weather_source_head": atmosphere.get("weather_source_head"),
        "rear_migration_head": atmosphere.get("rear_migration_head"),
        "rear_migrated_mesh_digest": atmosphere.get("rear_migrated_mesh_digest"),
        "source_opacity": copy.deepcopy(atmosphere.get("source_opacity")),
        "sampling_schedule_s": copy.deepcopy(atmosphere.get("sampling_schedule_s")),
        "checks": checks,
        "states": composed_states,
        "truth_boundary": (
            "PASS proves only exact receiving composition of the already-proven PR19 west Object source replacement "
            "inside the already-proven PR20 17-state current-world atmosphere sequence while unrelated Map state, "
            "Weather/sapling sequence identity and rear-tree culling isolation remain fixed. It does not prove Object "
            "materials or articulation, dynamic Object interaction, physical weather, gameplay, collision, target-device "
            "performance, final dressing, final Art Direction, CANON, production readiness, or Environment mastery."
        ),
    }
    payload["composition_digest"] = digest(
        {
            "atmosphere_head": EXPECTED_ATMOSPHERE_HEAD,
            "object_environment_head": EXPECTED_OBJECT_MAP_HEAD,
            "object_source": object_source_digest,
            "scenes": [row["scene"]["scene_digest"] for row in composed_states],
        }
    )

    observer_projection = copy.deepcopy(atmosphere)
    observer_projection["receiving_head"] = receiving_head
    observer_projection["states"] = copy.deepcopy(composed_states)
    observer_projection["observer_projection"] = {
        "source_schema": SCHEMA,
        "composition_digest": payload["composition_digest"],
        "object_environment_donor_head": EXPECTED_OBJECT_MAP_HEAD,
        "object_source_head": EXPECTED_OBJECT_SOURCE_HEAD,
        "truth_boundary": "Compatibility projection for the unchanged PR20 observer only; canonical evidence is the live-object schema.",
    }
    observer_projection["rebind_digest"] = digest(
        {
            "environment_head": observer_projection.get("environment_donor_head"),
            "dense_vfx_head": observer_projection.get("dense_vfx_donor_head"),
            "dense_sequence": observer_projection.get("dense_vfx_sequence_digest"),
            "rear_mesh": observer_projection.get("rear_migrated_mesh_digest"),
            "object_source": object_source_digest,
            "scenes": [row["scene"]["scene_digest"] for row in composed_states],
        }
    )
    return payload, observer_projection


def verify_target_host(
    payload: dict[str, Any],
    runtime_receipt: dict[str, Any],
    inherited_target_report: dict[str, Any],
    image_root: Path,
) -> dict[str, Any]:
    samples = runtime_receipt.get("samples", [])
    object_rows: list[dict[str, Any]] = []
    rear_rows: list[dict[str, Any]] = []
    frame_hashes = {context: set() for context in CONTEXTS}
    all_frames = True

    for sample in samples:
        static_sources = sample.get("static_source_meshes", [])
        object_match = [row for row in static_sources if row.get("asset_id") == OBJECT_SOURCE_ID]
        rear_match = [row for row in static_sources if row.get("asset_id") == REAR_SOURCE_ID]
        if len(object_match) == 1:
            object_rows.append(object_match[0])
        if len(rear_match) == 1:
            rear_rows.append(rear_match[0])
        for context in CONTEXTS:
            capture = sample.get("contexts", {}).get(context, {}).get("capture", {})
            path = image_root / Path(str(capture.get("path", ""))).name
            present = path.exists()
            all_frames = all_frames and present
            if present:
                frame_hashes[context].add(sha256(path))

    object_signatures = {
        (
            int(row.get("vertices", -1)),
            int(row.get("triangles", -1)),
            str(row.get("proof_culling", "")),
        )
        for row in object_rows
    }
    checks = {
        "canonical_structure_passes_first": payload.get("status") == STATUS
        and all(payload.get("checks", {}).values()),
        "inherited_pr20_target_host_gate_passes": inherited_target_report.get("state")
        == "PASS_CURRENT_WORLD_DENSE_ATMOSPHERE_LIVE_TARGET_HOST"
        and all(inherited_target_report.get("checks", {}).values()),
        "all_17_runtime_samples_present": len(samples) == 17,
        "object_source_rendered_all_17_states": len(object_rows) == 17,
        "object_source_target_counts_and_culling_exact": object_signatures
        == {(468, 812, "CULL_DISABLED")},
        "rear_tree_backface_culling_retained_all_states": len(rear_rows) == 17
        and {str(row.get("proof_culling", "")) for row in rear_rows} == {"CULL_BACK"},
        "all_34_frames_present": all_frames,
        "all_17_frames_distinct_per_camera": all(
            len(frame_hashes[context]) == 17 for context in CONTEXTS
        ),
    }
    return {
        "schema": TARGET_SCHEMA,
        "study_id": "environment-live-object-current-world-target-host-001",
        "state": TARGET_STATUS if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": payload.get("receiving_head"),
        "composition_digest": payload.get("composition_digest"),
        "object_source_runtime_signature": sorted([list(row) for row in object_signatures]),
        "inherited_runtime_counter_sets": inherited_target_report.get("runtime_counter_sets"),
        "proof_runtime": runtime_receipt.get("proof_runtime"),
        "truth_boundary": (
            "PASS proves only that the exact static Object source replacement is present in all 17 retained PR20-derived "
            "Godot states while the inherited dynamic atmosphere target-host gate, rear-tree culling isolation and retained "
            "frame distinctness remain green. It does not prove Object articulation/materials, wall-clock playback, physical "
            "weather, gameplay, target-device budgets, final world-art acceptance, CANON, production readiness, or mastery."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("--atmosphere", required=True, type=Path)
    build.add_argument("--object-candidate", required=True, type=Path)
    build.add_argument("--object-report", required=True, type=Path)
    build.add_argument("--receiving-head", required=True)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--observer-output", required=True, type=Path)

    verify = sub.add_parser("verify")
    verify.add_argument("--payload", required=True, type=Path)
    verify.add_argument("--runtime-receipt", required=True, type=Path)
    verify.add_argument("--inherited-target-report", required=True, type=Path)
    verify.add_argument("--image-root", required=True, type=Path)
    verify.add_argument("--output", required=True, type=Path)

    args = parser.parse_args()

    if args.command == "build":
        atmosphere = json.loads(args.atmosphere.read_text(encoding="utf-8"))
        object_candidate = json.loads(args.object_candidate.read_text(encoding="utf-8"))
        object_report = json.loads(args.object_report.read_text(encoding="utf-8"))
        payload, projection = build_payload(
            atmosphere,
            object_candidate,
            object_report,
            args.receiving_head,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.observer_output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.observer_output.write_text(
            json.dumps(projection, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "composition_digest": payload["composition_digest"],
                    "checks": payload["checks"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if payload["status"] == STATUS else 1

    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    runtime_receipt = json.loads(args.runtime_receipt.read_text(encoding="utf-8"))
    inherited = json.loads(args.inherited_target_report.read_text(encoding="utf-8"))
    result = verify_target_host(payload, runtime_receipt, inherited, args.image_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": result["state"], "checks": result["checks"]}, indent=2, sort_keys=True))
    return 0 if result["state"] == TARGET_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
