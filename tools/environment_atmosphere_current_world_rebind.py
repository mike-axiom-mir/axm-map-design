from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_rear_tree_normal_culling as current_world

SCHEMA = "axm.environment-current-world-atmosphere-rebind-evidence/v0.1"
TARGET_SCHEMA = "axm.environment-current-world-atmosphere-rebind-target-host/v0.1"
STATUS = "PASS_CURRENT_WORLD_DENSE_ATMOSPHERE_REBIND_STRUCTURE"
TARGET_STATUS = "PASS_CURRENT_WORLD_DENSE_ATMOSPHERE_LIVE_TARGET_HOST"

EXPECTED_ENVIRONMENT_HEAD = "f548f98959bf6769716a6d7c87bac69f9f548389"
EXPECTED_VFX_DONOR_HEAD = "6e386d513c0b2e821a89fb066b2e3ab58a0d6868"
EXPECTED_VFX_SEQUENCE_DIGEST = "f7f2cad01184e8651bcc722b755a2f3c2292ca13e81c7399579d7f42e0c19b30"
EXPECTED_NATURE_RESPONSE_HEAD = "cee14f5b3feea78b0adcd044bad2ea3c97657fc6"
EXPECTED_WEATHER_HEAD = "ca2eaba519e8449835b0ea6ef944b7080c3caa6a"
EXPECTED_REAR_MIGRATION_HEAD = "4ddbe66e5c02d22407ef773d5346a2fe6f349a2d"
EXPECTED_REAR_MESH_DIGEST = "aa9d450a78fef722672ea9af0f9aca98b4c1a0ca3705661784f5f61f3e9b6a31"
EXPECTED_OPACITY_PROVENANCE_HEAD = "1d24506e1d5f37cad32c878a15ac6908bf096329"
EXPECTED_SYNC_HEAD = "d476cf7c11de74c53397cb21e6f40f90a51c0356"
TARGET_REAR_ASSET_ID = "source:nature:east-rear-tree-neutral-001"
CONTEXTS = ("path_eye", "elevated_oblique")


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head(root: str | Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(Path(root).resolve()), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _build_exact_vfx_donor(
    donor_root: str | Path,
    nature_response_root: str | Path,
    weather_root: str | Path,
) -> dict[str, Any]:
    donor = Path(donor_root).resolve()
    if _git_head(donor) != EXPECTED_VFX_DONOR_HEAD:
        raise ValueError("dense VFX donor checkout drift")
    script = donor / "tools" / "environment_atmosphere_live_intermediates.py"
    manifest = donor / "examples" / "environment_real_slice_001.json"
    if not script.exists() or not manifest.exists():
        raise ValueError("dense VFX donor files missing")
    with tempfile.TemporaryDirectory(prefix="axm-vfx-donor-") as tmp:
        output = Path(tmp) / "dense.json"
        env = dict(os.environ)
        # The donor rebuilds its exact historical synchronized prerequisite first.
        env["AXM_RECEIVING_HEAD"] = EXPECTED_SYNC_HEAD
        subprocess.run(
            [
                sys.executable,
                str(script),
                "build",
                "--manifest",
                str(manifest),
                "--nature-root",
                str(Path(nature_response_root).resolve()),
                "--weather-root",
                str(Path(weather_root).resolve()),
                "--output",
                str(output),
            ],
            cwd=str(donor),
            env=env,
            check=True,
        )
        return json.loads(output.read_text(encoding="utf-8"))


def _find_source(scene: dict[str, Any], asset_id: str) -> dict[str, Any]:
    rows = [row for row in scene.get("additional_source_meshes", []) if row.get("asset_id") == asset_id]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one current-world source mesh for {asset_id}")
    return rows[0]


def _static_signature(scene: dict[str, Any]) -> dict[str, Any]:
    return {
        "items": scene.get("items"),
        "additional_source_meshes": scene.get("additional_source_meshes"),
        "readable_path": scene.get("readable_path"),
        "cameras": scene.get("cameras"),
        "source_integration": scene.get("source_integration"),
        "environment_replacement": scene.get("environment_replacement"),
        "environment_rear_tree_culling_review": scene.get("environment_rear_tree_culling_review"),
        "weather_presentation": scene.get("weather_presentation"),
    }


def build_payload(
    vfx_donor_root: str | Path,
    base_nature_root: str | Path,
    compact_nature_root: str | Path,
    nature_response_root: str | Path,
    weather_root: str | Path,
    building_root: str | Path,
    historical_rear_root: str | Path,
    migrated_rear_root: str | Path,
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    _, receiving_scene, environment_report = current_world.build_payloads(
        repo_root / "examples" / "environment_rear_tree_normal_culling_001.json",
        base_nature_root,
        compact_nature_root,
        weather_root,
        building_root,
        historical_rear_root,
        migrated_rear_root,
    )
    if environment_report.get("status") != "PASS_REAR_TREE_MIGRATED_SOURCE_RECEIVING_CULLING_STRUCTURE_READY":
        raise ValueError("current normal-culling Environment prerequisite must PASS")

    donor = _build_exact_vfx_donor(vfx_donor_root, nature_response_root, weather_root)
    if donor.get("status") != "PASS_DENSE_INTERMEDIATE_SOURCE_SEQUENCE":
        raise ValueError("exact dense VFX donor source sequence must PASS")
    if donor.get("sequence_digest") != EXPECTED_VFX_SEQUENCE_DIGEST:
        raise ValueError("dense VFX donor sequence digest drift")
    if donor.get("nature_response_head") != EXPECTED_NATURE_RESPONSE_HEAD:
        raise ValueError("dense VFX donor Nature response drift")
    if donor.get("weather_source_head") != EXPECTED_WEATHER_HEAD:
        raise ValueError("dense VFX donor Weather source drift")

    rear = _find_source(receiving_scene, TARGET_REAR_ASSET_ID)
    states = donor.get("states", [])
    if len(states) != 17:
        raise ValueError("exact dense VFX donor must contain 17 states")

    current_neutral_vertices = receiving_scene["sapling"]["vertices_source_xyz_m"]
    current_triangles = receiving_scene["sapling"]["triangles"]
    composed_states: list[dict[str, Any]] = []
    opacity_profiles: list[list[tuple[str, float]]] = []
    for donor_row in states:
        donor_scene = donor_row["candidate_scene"]
        if donor_scene["sapling"]["triangles"] != current_triangles:
            raise ValueError("dense VFX donor sapling triangle identity does not match current world")
        scene = copy.deepcopy(receiving_scene)
        scene["schema"] = "axm.environment-current-world-atmosphere-state/v0.1"
        scene["study_id"] = f"environment-current-world-atmosphere-rebind-001-{int(donor_row['index']):02d}"
        scene["weather_lines"] = copy.deepcopy(donor_scene["weather_lines"])
        scene["sapling"]["vertices_source_xyz_m"] = copy.deepcopy(donor_scene["sapling"]["vertices_source_xyz_m"])
        scene["sapling"]["triangles"] = copy.deepcopy(donor_scene["sapling"]["triangles"])
        if "visual_response" in donor_scene["sapling"]:
            scene["sapling"]["visual_response"] = copy.deepcopy(donor_scene["sapling"]["visual_response"])
        scene["current_world_atmosphere_rebind"] = {
            "environment_pr": 18,
            "environment_head": EXPECTED_ENVIRONMENT_HEAD,
            "dense_vfx_pr": 16,
            "dense_vfx_head": EXPECTED_VFX_DONOR_HEAD,
            "dense_sequence_digest": EXPECTED_VFX_SEQUENCE_DIGEST,
            "weather_source_head": EXPECTED_WEATHER_HEAD,
            "nature_response_head": EXPECTED_NATURE_RESPONSE_HEAD,
            "opacity_fidelity_provenance_head": EXPECTED_OPACITY_PROVENANCE_HEAD,
            "relationship": "EXACT_DENSE_VISUAL_SEQUENCE_REBOUND_INTO_CURRENT_ACCEPTED_WORLD_NOT_PHYSICAL_COUPLING",
        }
        scene["truth_boundary"] = (
            "This receiving state composes the already-proven exact dense visual-only Weather + sapling sequence into the current migrated rear-tree Map world. "
            "It does not create physical wind, transfer deformation semantics to other vegetation, prove wall-clock pacing, gameplay, target-device performance, final art, CANON, or mastery."
        )
        scene.pop("scene_digest", None)
        scene["scene_digest"] = digest(scene)
        profile = [(str(line["id"]), float(line["opacity"])) for line in scene["weather_lines"]]
        opacity_profiles.append(profile)
        composed_states.append(
            {
                "index": int(donor_row["index"]),
                "time_s": float(donor_row["time_s"]),
                "sampling_role": donor_row["sampling_role"],
                "weather_field_digest": donor_row["weather_field_digest"],
                "sapling_mesh_digest": donor_row["sapling_mesh_digest"],
                "scene": scene,
            }
        )

    static_signature = _static_signature(receiving_scene)
    culling = receiving_scene.get("environment_rear_tree_culling_review", {})
    checks = {
        "exact_environment_pr18_structure_passes": environment_report.get("status") == "PASS_REAR_TREE_MIGRATED_SOURCE_RECEIVING_CULLING_STRUCTURE_READY",
        "exact_environment_donor_head_declared": EXPECTED_ENVIRONMENT_HEAD == "f548f98959bf6769716a6d7c87bac69f9f548389",
        "exact_dense_vfx_donor_head_observed": _git_head(vfx_donor_root) == EXPECTED_VFX_DONOR_HEAD,
        "dense_vfx_sequence_digest_exact": donor.get("sequence_digest") == EXPECTED_VFX_SEQUENCE_DIGEST,
        "seventeen_exact_states_retained": len(composed_states) == 17,
        "all_static_current_world_state_preserved": all(_static_signature(row["scene"]) == static_signature for row in composed_states),
        "rear_migrated_source_identity_preserved": rear.get("source_head") == EXPECTED_REAR_MIGRATION_HEAD and rear.get("mesh_digest") == EXPECTED_REAR_MESH_DIGEST,
        "rear_target_backface_culling_preserved": culling.get("target_asset_id") == TARGET_REAR_ASSET_ID and culling.get("target_cull_mode") == "BACK",
        "other_source_culling_isolation_preserved": culling.get("other_source_mesh_cull_mode") == "DISABLED",
        "sapling_triangle_identity_preserved_all_states": all(row["scene"]["sapling"]["triangles"] == current_triangles for row in composed_states),
        "sapling_neutral_start_matches_current_world": composed_states[0]["scene"]["sapling"]["vertices_source_xyz_m"] == current_neutral_vertices,
        "sapling_neutral_return_matches_current_world": composed_states[-1]["scene"]["sapling"]["vertices_source_xyz_m"] == current_neutral_vertices,
        "weather_count_36_all_states": all(len(row["scene"]["weather_lines"]) == 36 for row in composed_states),
        "source_opacity_profile_present_and_stable": bool(opacity_profiles) and all(profile == opacity_profiles[0] for profile in opacity_profiles[1:]) and len({opacity for _, opacity in opacity_profiles[0]}) > 1,
        "source_opacity_values_bounded": all(0.0 <= opacity <= 1.0 for profile in opacity_profiles for _, opacity in profile),
        "weather_field_sequence_preserved_exactly": [row["weather_field_digest"] for row in composed_states] == [row["weather_field_digest"] for row in states],
        "sapling_mesh_sequence_preserved_exactly": [row["sapling_mesh_digest"] for row in composed_states] == [row["sapling_mesh_digest"] for row in states],
    }

    profile_values = [opacity for _, opacity in opacity_profiles[0]] if opacity_profiles else []
    payload = {
        "schema": SCHEMA,
        "study_id": "environment-current-world-atmosphere-rebind-001",
        "status": STATUS if all(checks.values()) else "FAIL",
        "receiving_head": os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD"),
        "environment_donor_head": EXPECTED_ENVIRONMENT_HEAD,
        "dense_vfx_donor_head": EXPECTED_VFX_DONOR_HEAD,
        "dense_vfx_sequence_digest": EXPECTED_VFX_SEQUENCE_DIGEST,
        "nature_response_head": EXPECTED_NATURE_RESPONSE_HEAD,
        "weather_source_head": EXPECTED_WEATHER_HEAD,
        "rear_migration_head": EXPECTED_REAR_MIGRATION_HEAD,
        "rear_migrated_mesh_digest": EXPECTED_REAR_MESH_DIGEST,
        "checks": checks,
        "source_opacity": {
            "count": len(profile_values),
            "minimum": min(profile_values) if profile_values else None,
            "maximum": max(profile_values) if profile_values else None,
            "mean": sum(profile_values) / len(profile_values) if profile_values else None,
        },
        "sampling_schedule_s": [row["time_s"] for row in composed_states],
        "states": composed_states,
        "truth_boundary": (
            "PASS proves only that the exact already-proven 17-state visual-only Weather + sapling sequence, including source-owned per-streak opacity, can be rebound without source drift into the exact migrated-rear-tree current Map receiving state while its static world and culling contract remain fixed. "
            "It does not prove physical weather, deformation for compact/rear vegetation, renderer interpolation, wall-clock playback, target-device performance, gameplay, final Art Direction, CANON, production readiness, or VFX mastery."
        ),
    }
    payload["rebind_digest"] = digest(
        {
            "environment_head": payload["environment_donor_head"],
            "dense_vfx_head": payload["dense_vfx_donor_head"],
            "dense_sequence": payload["dense_vfx_sequence_digest"],
            "rear_mesh": payload["rear_migrated_mesh_digest"],
            "scenes": [row["scene"]["scene_digest"] for row in composed_states],
        }
    )
    return payload


def verify_target_host(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path) -> dict[str, Any]:
    root = Path(image_root)
    samples = receipt.get("samples", [])
    frame_rows: list[dict[str, Any]] = []
    unique = {context: set() for context in CONTEXTS}
    counters = {context: set() for context in CONTEXTS}
    static_ids: set[tuple[int, int, int]] = set()
    rear_modes: set[str] = set()
    other_modes: set[tuple[str, ...]] = set()
    opacity_modes: set[str] = set()
    all_frames = True

    for sample in samples:
        weather = sample.get("weather_update", {})
        sapling = sample.get("sapling_update", {})
        static_ids.add((
            int(weather.get("node_instance_id", -1)),
            int(weather.get("mesh_instance_id", -1)),
            int(weather.get("material_instance_id", -1)),
        ))
        opacity_modes.add(str(weather.get("opacity_mode", "")))
        static_sources = sample.get("static_source_meshes", [])
        target = [row for row in static_sources if row.get("asset_id") == TARGET_REAR_ASSET_ID]
        if len(target) == 1:
            rear_modes.add(str(target[0].get("proof_culling", "")))
        others = sorted(str(row.get("proof_culling", "")) for row in static_sources if row.get("asset_id") != TARGET_REAR_ASSET_ID)
        other_modes.add(tuple(others))
        for context in CONTEXTS:
            row = sample.get("contexts", {}).get(context, {})
            capture = row.get("capture", {})
            path = root / Path(str(capture.get("path", ""))).name
            present = path.exists()
            all_frames = all_frames and present
            frame = {"index": int(sample.get("index", -1)), "context": context, "present": present}
            if present:
                frame["sha256"] = sha256(path)
                unique[context].add(frame["sha256"])
            runtime = row.get("runtime", {})
            counter = (
                int(runtime.get("draw_calls_in_frame", -1)),
                int(runtime.get("objects_in_frame", -1)),
                int(runtime.get("primitives_in_frame", -1)),
            )
            counters[context].add(counter)
            frame["runtime"] = {"draw_calls": counter[0], "objects": counter[1], "primitives": counter[2]}
            frame_rows.append(frame)

    checks = {
        "structural_payload_passes_first": payload.get("status") == STATUS and all(payload.get("checks", {}).values()),
        "proof_runtime_exact": receipt.get("proof_runtime") == "Godot 4.7.2 GL Compatibility",
        "all_17_runtime_samples_present": len(samples) == 17,
        "all_34_frames_present": all_frames and len(frame_rows) == 34,
        "all_17_frames_distinct_per_camera": all(len(unique[context]) == 17 for context in CONTEXTS),
        "runtime_counters_stable_within_each_camera": all(len(counters[context]) == 1 for context in CONTEXTS),
        "weather_resource_identity_stable": len(static_ids) == 1 and next(iter(static_ids), (-1, -1, -1))[0] > 0,
        "sapling_resource_identity_stable": len({(
            int(sample.get("sapling_update", {}).get("node_instance_id", -1)),
            int(sample.get("sapling_update", {}).get("mesh_instance_id", -1)),
            int(sample.get("sapling_update", {}).get("material_instance_id", -1)),
        ) for sample in samples}) == 1,
        "source_opacity_vertex_alpha_consumed": opacity_modes == {"SOURCE_STREAK_OPACITY_VERTEX_ALPHA"} and all(bool(sample.get("weather_update", {}).get("source_opacity_consumed")) for sample in samples),
        "rear_tree_backface_culling_retained": rear_modes == {"CULL_BACK"},
        "other_static_sources_remain_cull_disabled": bool(other_modes) and all(all(mode == "CULL_DISABLED" for mode in modes) for modes in other_modes),
        "sequence_digest_retained": receipt.get("dense_vfx_sequence_digest") == EXPECTED_VFX_SEQUENCE_DIGEST,
    }
    return {
        "schema": TARGET_SCHEMA,
        "study_id": "environment-current-world-atmosphere-rebind-target-host-001",
        "state": TARGET_STATUS if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": payload.get("receiving_head"),
        "environment_donor_head": EXPECTED_ENVIRONMENT_HEAD,
        "dense_vfx_donor_head": EXPECTED_VFX_DONOR_HEAD,
        "dense_vfx_sequence_digest": EXPECTED_VFX_SEQUENCE_DIGEST,
        "proof_runtime": receipt.get("proof_runtime"),
        "runtime_counter_sets": {context: [list(row) for row in sorted(counters[context])] for context in CONTEXTS},
        "frames": frame_rows,
        "truth_boundary": (
            "PASS proves retained target-host consumption of the exact rebound 17-state visual-only sequence in the exact current Map world with stable Weather/sapling proof resources and preserved rear-tree culling isolation. "
            "It does not prove wall-clock playback, interpolation, physical weather, target-device performance, gameplay, final atmosphere quality, CANON, production readiness, or VFX mastery."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--vfx-donor-root", required=True)
    build.add_argument("--base-nature-root", required=True)
    build.add_argument("--compact-nature-root", required=True)
    build.add_argument("--nature-response-root", required=True)
    build.add_argument("--weather-root", required=True)
    build.add_argument("--building-root", required=True)
    build.add_argument("--historical-rear-root", required=True)
    build.add_argument("--migrated-rear-root", required=True)
    build.add_argument("--output", required=True, type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("--payload", required=True, type=Path)
    verify.add_argument("--receipt", required=True, type=Path)
    verify.add_argument("--image-root", required=True, type=Path)
    verify.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.command == "build":
        payload = build_payload(
            args.vfx_donor_root,
            args.base_nature_root,
            args.compact_nature_root,
            args.nature_response_root,
            args.weather_root,
            args.building_root,
            args.historical_rear_root,
            args.migrated_rear_root,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": payload["status"], "checks": payload["checks"], "rebind_digest": payload["rebind_digest"]}, indent=2, sort_keys=True))
        return 0 if payload["status"] == STATUS else 1

    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    result = verify_target_host(payload, receipt, args.image_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": result["state"], "checks": result["checks"], "runtime_counter_sets": result["runtime_counter_sets"]}, indent=2, sort_keys=True))
    return 0 if result["state"] == TARGET_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
