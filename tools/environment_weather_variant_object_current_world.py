from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-weather-variant-object-current-world-evidence/v0.1"
STATUS = "PASS_WEATHER_VARIANT_OBJECT_SOURCE_COMPOSITION_STRUCTURE"
TARGET_SCHEMA = "axm.environment-weather-variant-object-current-world-target-host/v0.1"
TARGET_STATUS = "PASS_WEATHER_VARIANT_OBJECT_SOURCE_COMPOSITION_TARGET_HOST"

EXPECTED_VARIANT_MAP_HEAD = "e482d003853e52fc835f1797ddfb6506a50083ef"
EXPECTED_OBJECT_MAP_HEAD = "85a2a0be959b4e39f9ffcf83da89078b604f9881"
EXPECTED_OBJECT_SOURCE_HEAD = "d3fa10a270faae7925811f44f03381fe5c5d0215"
EXPECTED_OBJECT_SOURCE_SHA256 = "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
EXPECTED_OBJECT_OBJ_SHA256 = "3e01ef3bf4935ee6aee7c56c03dc0b7f54c308e5ac2eb6a7583252a366901106"
EXPECTED_WEATHER_VARIANT_HEAD = "05b26c4e82bbe0a4de0ee7bee34179efc58b9719"
EXPECTED_WEATHER_VARIANT_SEED = 44021
EXPECTED_WEATHER_LAYOUT_DIGEST = "7ed55e93ea9445345016685320716006bc52960b33784cb620ca5670a74cc26f"

VARIANT_STATUS = "PASS_CURRENT_WORLD_WEATHER_VARIANT_REBIND_STRUCTURE"
RUNTIME_OBSERVATION_STATUS = "PASS_CURRENT_WORLD_WEATHER_VARIANT_LIVE_OBSERVATION"
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
    weather_variant: dict[str, Any],
    object_candidate: dict[str, Any],
    object_report: dict[str, Any],
    receiving_head: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if weather_variant.get("status") != VARIANT_STATUS:
        raise ValueError("exact PR22 Weather-variant structure must PASS first")
    if not all(weather_variant.get("checks", {}).values()):
        raise ValueError("exact PR22 Weather-variant checks must all PASS")
    if weather_variant.get("receiving_head") != EXPECTED_VARIANT_MAP_HEAD:
        raise ValueError("Weather-variant Map donor head drift")
    if weather_variant.get("weather_variant_head") != EXPECTED_WEATHER_VARIANT_HEAD:
        raise ValueError("Weather variation donor head drift")
    if int(weather_variant.get("weather_variant_seed", -1)) != EXPECTED_WEATHER_VARIANT_SEED:
        raise ValueError("Weather variant seed drift")
    if weather_variant.get("weather_variant_layout_digest") != EXPECTED_WEATHER_LAYOUT_DIGEST:
        raise ValueError("Weather layout digest drift")

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

    states = weather_variant.get("states", [])
    if len(states) != 17:
        raise ValueError("exact Weather-variant donor must retain 17 states")

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
            "west_proxy_present_in_variant_donor": len(
                [item for item in base.get("items", []) if item.get("asset_id") == WEST_PROXY_ID]
            ) == 1,
            "object_candidate_items_are_exact_variant_minus_west_proxy": object_candidate.get("items")
            == expected_items,
            "object_candidate_static_sources_are_exact_variant_plus_object": candidate_without_object
            == base_sources,
            "fixed_scene_fields_match": _fixed_scene_fields_match(base, object_candidate),
            "east_object_proxy_preserved": len(
                [item for item in object_candidate.get("items", []) if item.get("asset_id") == EAST_PROXY_ID]
            ) == 1,
            "rear_tree_culling_contract_preserved": base.get("environment_rear_tree_culling_review")
            == object_candidate.get("environment_rear_tree_culling_review"),
            "weather_variant_identity_present": base.get("weather_variant", {}).get("seed")
            == EXPECTED_WEATHER_VARIANT_SEED
            and base.get("weather_variant", {}).get("particle_layout_digest")
            == EXPECTED_WEATHER_LAYOUT_DIGEST,
        }
        if not all(checks.values()):
            raise ValueError(
                f"state {row.get('index')} cannot safely compose PR19 Object into PR22 Weather variant: {checks}"
            )

        scene = copy.deepcopy(base)
        scene["schema"] = "axm.environment-weather-variant-object-current-world-state/v0.1"
        scene["study_id"] = (
            f"environment-weather-variant-object-current-world-001-{int(row['index']):02d}"
        )
        scene["items"] = copy.deepcopy(object_candidate["items"])
        scene["additional_source_meshes"] = copy.deepcopy(object_sources)
        scene["environment_object_replacement"] = copy.deepcopy(replacement)
        scene["environment_weather_variant_object_composition"] = {
            "weather_variant_map_donor_pr": 22,
            "weather_variant_map_donor_head": EXPECTED_VARIANT_MAP_HEAD,
            "object_environment_donor_pr": 19,
            "object_environment_donor_head": EXPECTED_OBJECT_MAP_HEAD,
            "object_source_head": EXPECTED_OBJECT_SOURCE_HEAD,
            "weather_variant_head": EXPECTED_WEATHER_VARIANT_HEAD,
            "weather_variant_seed": EXPECTED_WEATHER_VARIANT_SEED,
            "weather_variant_layout_digest": EXPECTED_WEATHER_LAYOUT_DIGEST,
            "relationship": "EXACT_PR19_STATIC_OBJECT_REPLACEMENT_COMPOSED_INTO_EXACT_PR22_WEATHER_VARIANT_WORLD",
            "authority": "MAP_RECEIVING_COMPOSITION_ONLY",
        }
        scene["truth_boundary"] = (
            "This state composes the already-proven exact west Object structural source replacement into the "
            "already-proven exact source-owned Weather seed-44021 current-world visual sequence. It does not "
            "promote Object materials/articulation, Weather aesthetic preference or physics, gameplay, target-device "
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
        "exact_weather_variant_map_identity_preserved": weather_variant.get("receiving_head")
        == EXPECTED_VARIANT_MAP_HEAD,
        "exact_object_environment_identity_declared": EXPECTED_OBJECT_MAP_HEAD
        == "85a2a0be959b4e39f9ffcf83da89078b604f9881",
        "exact_object_source_identity_preserved": replacement.get("source_head")
        == EXPECTED_OBJECT_SOURCE_HEAD
        and replacement.get("source_sha256") == EXPECTED_OBJECT_SOURCE_SHA256
        and replacement.get("obj_sha256") == EXPECTED_OBJECT_OBJ_SHA256,
        "exact_weather_variant_identity_preserved": weather_variant.get("weather_variant_head")
        == EXPECTED_WEATHER_VARIANT_HEAD
        and int(weather_variant.get("weather_variant_seed", -1)) == EXPECTED_WEATHER_VARIANT_SEED
        and weather_variant.get("weather_variant_layout_digest") == EXPECTED_WEATHER_LAYOUT_DIGEST,
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
            digest(_one(row["scene"]["additional_source_meshes"], OBJECT_SOURCE_ID))
            == object_source_digest
            for row in composed_states
        ),
        "object_source_counts_exact": len(first_object["vertices_source_xyz_m"]) == 468
        and len(first_object["triangles"]) == 812,
        "weather_variant_sequence_preserved_exactly": [
            row["weather_field_digest"] for row in composed_states
        ]
        == [row["weather_field_digest"] for row in states]
        and all(
            row["scene"]["weather_lines"] == donor["scene"]["weather_lines"]
            for row, donor in zip(composed_states, states)
        ),
        "sapling_sequence_preserved_exactly": [
            row["sapling_mesh_digest"] for row in composed_states
        ]
        == [row["sapling_mesh_digest"] for row in states]
        and all(
            row["scene"]["sapling"] == donor["scene"]["sapling"]
            for row, donor in zip(composed_states, states)
        ),
        "neutral_return_keeps_same_object_identity": digest(
            _one(last_scene["additional_source_meshes"], OBJECT_SOURCE_ID)
        )
        == object_source_digest,
        "rear_tree_culling_target_preserved": first_scene.get(
            "environment_rear_tree_culling_review", {}
        ).get("target_asset_id")
        == REAR_SOURCE_ID
        and first_scene.get("environment_rear_tree_culling_review", {}).get("target_cull_mode")
        == "BACK",
    }

    payload = {
        "schema": SCHEMA,
        "study_id": "environment-weather-variant-object-current-world-001",
        "status": STATUS if all(checks.values()) else "FAIL",
        "receiving_head": receiving_head,
        "weather_variant_map_donor_pr": 22,
        "weather_variant_map_donor_head": EXPECTED_VARIANT_MAP_HEAD,
        "weather_variant_head": EXPECTED_WEATHER_VARIANT_HEAD,
        "weather_variant_seed": EXPECTED_WEATHER_VARIANT_SEED,
        "weather_variant_layout_digest": EXPECTED_WEATHER_LAYOUT_DIGEST,
        "weather_variant_rebind_digest": weather_variant.get("variant_rebind_digest"),
        "object_environment_donor_pr": 19,
        "object_environment_donor_head": EXPECTED_OBJECT_MAP_HEAD,
        "object_source_head": EXPECTED_OBJECT_SOURCE_HEAD,
        "object_source_sha256": EXPECTED_OBJECT_SOURCE_SHA256,
        "object_obj_sha256": EXPECTED_OBJECT_OBJ_SHA256,
        "rear_migration_head": weather_variant.get("rear_migration_head"),
        "rear_migrated_mesh_digest": weather_variant.get("rear_migrated_mesh_digest"),
        "source_opacity": copy.deepcopy(weather_variant.get("source_opacity")),
        "sampling_schedule_s": copy.deepcopy(weather_variant.get("sampling_schedule_s")),
        "checks": checks,
        "states": composed_states,
        "truth_boundary": (
            "PASS proves only exact receiving composition of the already-proven PR19 west Object source replacement "
            "inside the already-proven PR22 source-owned Weather seed-44021 17-state current-world sequence while "
            "Weather/sapling sequence identity, unrelated static scene state and rear-tree culling isolation remain "
            "fixed. It does not prove Object materials or articulation, Weather aesthetic preference, physical weather, "
            "gameplay, target-device performance, final dressing, final Art Direction, CANON, production readiness, "
            "or Environment mastery."
        ),
    }
    payload["composition_digest"] = digest(
        {
            "weather_variant_map_head": EXPECTED_VARIANT_MAP_HEAD,
            "weather_variant_head": EXPECTED_WEATHER_VARIANT_HEAD,
            "weather_variant_seed": EXPECTED_WEATHER_VARIANT_SEED,
            "weather_variant_layout": EXPECTED_WEATHER_LAYOUT_DIGEST,
            "object_environment_head": EXPECTED_OBJECT_MAP_HEAD,
            "object_source": object_source_digest,
            "scenes": [row["scene"]["scene_digest"] for row in composed_states],
        }
    )

    # Compatibility projection only: the unchanged PR22 Godot observer consumes its own schema,
    # but canonical acceptance is always evaluated against the Environment schema above.
    observer_projection = copy.deepcopy(weather_variant)
    observer_projection["receiving_head"] = receiving_head
    observer_projection["states"] = copy.deepcopy(composed_states)
    observer_projection["observer_projection"] = {
        "source_schema": SCHEMA,
        "composition_digest": payload["composition_digest"],
        "weather_variant_map_donor_head": EXPECTED_VARIANT_MAP_HEAD,
        "object_environment_donor_head": EXPECTED_OBJECT_MAP_HEAD,
        "object_source_head": EXPECTED_OBJECT_SOURCE_HEAD,
        "truth_boundary": (
            "Compatibility projection for the unchanged PR22 Godot observer only. The inherited PR22 structural "
            "checks are donor evidence, not acceptance of this changed static scene; canonical Environment evidence "
            "and the Environment target verifier are authoritative for this convergence."
        ),
    }
    observer_projection["variant_rebind_digest"] = digest(
        {
            "weather_variant_map_head": EXPECTED_VARIANT_MAP_HEAD,
            "weather_variant_head": EXPECTED_WEATHER_VARIANT_HEAD,
            "seed": EXPECTED_WEATHER_VARIANT_SEED,
            "layout": EXPECTED_WEATHER_LAYOUT_DIGEST,
            "object_source": object_source_digest,
            "scenes": [row["scene"]["scene_digest"] for row in composed_states],
        }
    )
    return payload, observer_projection


def verify_target_host(
    payload: dict[str, Any], runtime_receipt: dict[str, Any], image_root: Path
) -> dict[str, Any]:
    samples = runtime_receipt.get("samples", [])
    object_rows: list[dict[str, Any]] = []
    rear_rows: list[dict[str, Any]] = []
    frame_hashes = {context: set() for context in CONTEXTS}
    counter_sets = {context: set() for context in CONTEXTS}
    weather_ids = set()
    sapling_ids = set()
    opacity_modes = set()
    all_frames = True

    for sample in samples:
        static_sources = sample.get("static_source_meshes", [])
        object_match = [row for row in static_sources if row.get("asset_id") == OBJECT_SOURCE_ID]
        rear_match = [row for row in static_sources if row.get("asset_id") == REAR_SOURCE_ID]
        if len(object_match) == 1:
            object_rows.append(object_match[0])
        if len(rear_match) == 1:
            rear_rows.append(rear_match[0])

        weather = sample.get("weather_update", {})
        sapling = sample.get("sapling_update", {})
        weather_ids.add(
            (
                int(weather.get("node_instance_id", -1)),
                int(weather.get("mesh_instance_id", -1)),
                int(weather.get("material_instance_id", -1)),
            )
        )
        sapling_ids.add(
            (
                int(sapling.get("node_instance_id", -1)),
                int(sapling.get("mesh_instance_id", -1)),
                int(sapling.get("material_instance_id", -1)),
            )
        )
        opacity_modes.add(str(weather.get("opacity_mode", "")))

        for context in CONTEXTS:
            context_row = sample.get("contexts", {}).get(context, {})
            capture = context_row.get("capture", {})
            path = image_root / Path(str(capture.get("path", ""))).name
            present = path.exists()
            all_frames = all_frames and present
            if present:
                frame_hashes[context].add(sha256(path))
            runtime = context_row.get("runtime", {})
            counter_sets[context].add(
                (
                    int(runtime.get("draw_calls_in_frame", -1)),
                    int(runtime.get("objects_in_frame", -1)),
                    int(runtime.get("primitives_in_frame", -1)),
                )
            )

    object_signatures = {
        (
            int(row.get("vertices", -1)),
            int(row.get("triangles", -1)),
            str(row.get("proof_culling", "")),
        )
        for row in object_rows
    }
    sample_weather_digests = [row.get("weather_field_digest") for row in samples]
    sample_sapling_digests = [row.get("sapling_mesh_digest") for row in samples]
    payload_weather_digests = [row.get("weather_field_digest") for row in payload.get("states", [])]
    payload_sapling_digests = [row.get("sapling_mesh_digest") for row in payload.get("states", [])]

    checks = {
        "canonical_structure_passes_first": payload.get("status") == STATUS
        and all(payload.get("checks", {}).values()),
        "runtime_observer_state_exact": runtime_receipt.get("state") == RUNTIME_OBSERVATION_STATUS,
        "proof_runtime_exact": runtime_receipt.get("proof_runtime") == "Godot 4.7.2 GL Compatibility",
        "receipt_receiving_head_exact": runtime_receipt.get("receiving_head") == payload.get("receiving_head"),
        "receipt_weather_variant_identity_exact": int(runtime_receipt.get("weather_variant_seed", -1))
        == EXPECTED_WEATHER_VARIANT_SEED
        and runtime_receipt.get("weather_variant_layout_digest") == EXPECTED_WEATHER_LAYOUT_DIGEST,
        "all_17_runtime_samples_present": len(samples) == 17,
        "weather_sequence_matches_canonical_payload": sample_weather_digests == payload_weather_digests,
        "sapling_sequence_matches_canonical_payload": sample_sapling_digests == payload_sapling_digests,
        "object_source_rendered_all_17_states": len(object_rows) == 17,
        "object_source_target_counts_and_culling_exact": object_signatures
        == {(468, 812, "CULL_DISABLED")},
        "rear_tree_backface_culling_retained_all_states": len(rear_rows) == 17
        and {str(row.get("proof_culling", "")) for row in rear_rows} == {"CULL_BACK"},
        "weather_resource_identity_stable": len(weather_ids) == 1
        and next(iter(weather_ids), (-1, -1, -1))[0] > 0,
        "sapling_resource_identity_stable": len(sapling_ids) == 1
        and next(iter(sapling_ids), (-1, -1, -1))[0] > 0,
        "source_opacity_vertex_alpha_consumed": opacity_modes == {"SOURCE_STREAK_OPACITY_VERTEX_ALPHA"}
        and all(bool(sample.get("weather_update", {}).get("source_opacity_consumed")) for sample in samples),
        "runtime_counters_stable_within_each_camera": all(
            len(counter_sets[context]) == 1 for context in CONTEXTS
        ),
        "all_34_frames_present": all_frames and len(samples) == 17,
        "all_17_frames_distinct_per_camera": all(
            len(frame_hashes[context]) == 17 for context in CONTEXTS
        ),
    }

    return {
        "schema": TARGET_SCHEMA,
        "study_id": "environment-weather-variant-object-current-world-target-host-001",
        "state": TARGET_STATUS if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": payload.get("receiving_head"),
        "composition_digest": payload.get("composition_digest"),
        "weather_variant_map_donor_head": EXPECTED_VARIANT_MAP_HEAD,
        "weather_variant_head": EXPECTED_WEATHER_VARIANT_HEAD,
        "weather_variant_seed": EXPECTED_WEATHER_VARIANT_SEED,
        "weather_variant_layout_digest": EXPECTED_WEATHER_LAYOUT_DIGEST,
        "object_environment_donor_head": EXPECTED_OBJECT_MAP_HEAD,
        "object_source_head": EXPECTED_OBJECT_SOURCE_HEAD,
        "object_source_runtime_signature": sorted([list(row) for row in object_signatures]),
        "runtime_counter_sets": {
            context: [list(row) for row in sorted(counter_sets[context])] for context in CONTEXTS
        },
        "proof_runtime": runtime_receipt.get("proof_runtime"),
        "truth_boundary": (
            "PASS proves only that the exact static Object source replacement and exact source-owned Weather seed-44021 "
            "visual sequence coexist in all 17 retained Godot states while Weather/sapling runtime identities, source "
            "opacity consumption, rear-tree culling isolation and retained frame distinctness remain bounded. It does "
            "not prove aesthetic preference, Object articulation/materials, physical weather, gameplay, target-device "
            "budgets, final world-art acceptance, CANON, production readiness, or Environment mastery."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("--weather-variant", required=True, type=Path)
    build.add_argument("--object-candidate", required=True, type=Path)
    build.add_argument("--object-report", required=True, type=Path)
    build.add_argument("--receiving-head", required=True)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--observer-output", required=True, type=Path)

    verify = sub.add_parser("verify")
    verify.add_argument("--payload", required=True, type=Path)
    verify.add_argument("--runtime-receipt", required=True, type=Path)
    verify.add_argument("--image-root", required=True, type=Path)
    verify.add_argument("--output", required=True, type=Path)

    args = parser.parse_args()

    if args.command == "build":
        weather_variant = json.loads(args.weather_variant.read_text(encoding="utf-8"))
        object_candidate = json.loads(args.object_candidate.read_text(encoding="utf-8"))
        object_report = json.loads(args.object_report.read_text(encoding="utf-8"))
        payload, projection = build_payload(
            weather_variant,
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
    result = verify_target_host(payload, runtime_receipt, args.image_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "state": result["state"],
                "checks": result["checks"],
                "runtime_counter_sets": result["runtime_counter_sets"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["state"] == TARGET_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
