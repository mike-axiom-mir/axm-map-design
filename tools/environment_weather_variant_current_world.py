from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_atmosphere_current_world_rebind as base

SCHEMA = "axm.environment-current-world-weather-variant-evidence/v0.1"
TARGET_SCHEMA = "axm.environment-current-world-weather-variant-target-host/v0.1"
STATUS = "PASS_CURRENT_WORLD_WEATHER_VARIANT_REBIND_STRUCTURE"
TARGET_STATUS = "PASS_CURRENT_WORLD_WEATHER_VARIANT_LIVE_TARGET_HOST"
EXPECTED_PARENT_VFX_HEAD = "3e641a5ea7b2507a53e5ff1a8fba0f0f9c94abaf"
EXPECTED_WEATHER_BASE_HEAD = "ca2eaba519e8449835b0ea6ef944b7080c3caa6a"
EXPECTED_WEATHER_VARIANT_HEAD = "05b26c4e82bbe0a4de0ee7bee34179efc58b9719"
EXPECTED_VARIANT_SEED = 44021
EXPECTED_LAYOUT_DIGEST = "7ed55e93ea9445345016685320716006bc52960b33784cb620ca5670a74cc26f"
EXPECTED_VARIANT_SOURCE_DIGEST = ""
CONTEXTS = ("path_eye", "elevated_oblique")
TARGET_REAR_ASSET_ID = "source:nature:east-rear-tree-neutral-001"
TOL = 1e-9


def _git_head(root: str | Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(Path(root).resolve()), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_weather_variant(weather_variant_root: str | Path):
    root = Path(weather_variant_root).resolve()
    if _git_head(root) != EXPECTED_WEATHER_VARIANT_HEAD:
        raise ValueError("Weather variation donor checkout drift")
    wind = _load_module("axm_weather_variant_wind", root / "tools" / "wind_atmosphere.py")
    family_mod = _load_module("axm_weather_variant_family", root / "tools" / "weather_variation_family.py")
    source = wind.load_study(root / "examples" / "wind_atmosphere_baseline_001.json")
    family = family_mod.load_family(root / "examples" / "wind_atmosphere_variation_family_001.json")
    candidate, particles, receipt = family_mod.evaluate_variant(source, family, EXPECTED_VARIANT_SEED)
    if receipt.get("status") != "PASS":
        raise ValueError("selected Weather variant must PASS source-local family gate")
    if receipt.get("particle_layout_digest") != EXPECTED_LAYOUT_DIGEST:
        raise ValueError("selected Weather variant layout digest drift")
    if int(receipt.get("seed", -1)) != EXPECTED_VARIANT_SEED:
        raise ValueError("selected Weather variant seed drift")
    return wind, candidate, particles, receipt


def _weather_lines(wind, source: dict[str, Any], particles: list[dict[str, Any]], time_s: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, particle in enumerate(particles):
        sample = wind.sample_particle(particle, source, time_s)
        rows.append({
            "id": particle["id"],
            "tail_xy": [float(sample["tail_x"]), float(sample["tail_y"])],
            "head_xy": [float(sample["x"]), float(sample["y"])],
            "opacity": float(particle["opacity"]),
            "presentation_height_m": 3.0,
            "source_order": index,
        })
    return rows


def _field_digest(lines: list[dict[str, Any]]) -> str:
    return base.digest([
        {
            "id": row["id"],
            "tail_xy": row["tail_xy"],
            "head_xy": row["head_xy"],
            "source_order": row["source_order"],
        }
        for row in lines
    ])


def _motion_metrics(states: list[dict[str, Any]], wind_xy, visual_speed: float) -> dict[str, Any]:
    x, y = map(float, wind_xy)
    mag = (x * x + y * y) ** 0.5
    ux, uy = x / mag, y / mag
    cx, cy = -uy, ux
    projected_errors: list[float] = []
    crosswind: list[float] = []
    identity_errors: list[str] = []
    for before, after in zip(states, states[1:]):
        dt = float(after["time_s"]) - float(before["time_s"])
        expected = visual_speed * dt
        a_rows = before["scene"]["weather_lines"]
        b_rows = after["scene"]["weather_lines"]
        if [row["id"] for row in a_rows] != [row["id"] for row in b_rows]:
            identity_errors.append("particle identity/order drift")
            continue
        for a, b in zip(a_rows, b_rows):
            dx = float(b["head_xy"][0]) - float(a["head_xy"][0])
            dy = float(b["head_xy"][1]) - float(a["head_xy"][1])
            projected_errors.append(abs(dx * ux + dy * uy - expected))
            crosswind.append(abs(dx * cx + dy * cy))
    return {
        "maximum_adjacent_projected_displacement_error_m": max(projected_errors, default=0.0),
        "maximum_adjacent_crosswind_drift_m": max(crosswind, default=0.0),
        "identity_errors": identity_errors,
    }


def build_payload(
    vfx_donor_root: str | Path,
    base_nature_root: str | Path,
    compact_nature_root: str | Path,
    nature_response_root: str | Path,
    weather_base_root: str | Path,
    weather_variant_root: str | Path,
    building_root: str | Path,
    historical_rear_root: str | Path,
    migrated_rear_root: str | Path,
) -> dict[str, Any]:
    if _git_head(weather_base_root) != EXPECTED_WEATHER_BASE_HEAD:
        raise ValueError("baseline Weather checkout drift")

    inherited = base.build_payload(
        vfx_donor_root,
        base_nature_root,
        compact_nature_root,
        nature_response_root,
        weather_base_root,
        building_root,
        historical_rear_root,
        migrated_rear_root,
    )
    if inherited.get("status") != base.STATUS or not all(inherited.get("checks", {}).values()):
        raise ValueError("current-world VFX prerequisite must PASS exactly before variant substitution")

    wind, variant_source, particles, variant_receipt = _load_weather_variant(weather_variant_root)
    weather_evidence = wind.evaluate(variant_source)
    if weather_evidence.get("status") != "PASS":
        raise ValueError("selected Weather variant must re-pass Weather source evaluator")

    inherited_states = inherited.get("states", [])
    if len(inherited_states) != 17:
        raise ValueError("current-world VFX prerequisite must retain exactly 17 states")

    states: list[dict[str, Any]] = []
    opacity_profiles: list[list[tuple[str, float]]] = []
    for inherited_row in inherited_states:
        time_s = float(inherited_row["time_s"])
        lines = _weather_lines(wind, variant_source, particles, time_s)
        scene = copy.deepcopy(inherited_row["scene"])
        scene["schema"] = "axm.environment-current-world-weather-variant-state/v0.1"
        scene["study_id"] = f"environment-current-world-weather-variant-001-{int(inherited_row['index']):02d}"
        scene["weather_lines"] = lines
        scene["weather_variant"] = {
            "repository": "mike-axiom-mir/axm-weather-design",
            "source_pr": 2,
            "source_head": EXPECTED_WEATHER_BASE_HEAD,
            "variation_pr": 3,
            "variation_head": EXPECTED_WEATHER_VARIANT_HEAD,
            "seed": EXPECTED_VARIANT_SEED,
            "candidate_source_digest": variant_receipt["candidate_source_digest"],
            "particle_layout_digest": variant_receipt["particle_layout_digest"],
            "semantics": variant_source["wind_semantics"],
            "relationship": "SOURCE_OWNED_LAYOUT_VARIANT_SUBSTITUTION_ONLY_SAPLING_SEQUENCE_UNCHANGED",
        }
        scene["truth_boundary"] = (
            "This receiving state substitutes one exact source-owned Weather PR #3 layout variant into the already-proven current-world Weather + sapling sequence. "
            "Sapling deformation, Environment composition and Weather motion semantics are unchanged. This does not prove physical wind, arbitrary procedural quality, wall-clock playback, performance, gameplay, final art, CANON, or mastery."
        )
        scene.pop("scene_digest", None)
        scene["scene_digest"] = base.digest(scene)
        profile = [(str(line["id"]), float(line["opacity"])) for line in lines]
        opacity_profiles.append(profile)
        states.append({
            "index": int(inherited_row["index"]),
            "time_s": time_s,
            "sampling_role": inherited_row["sampling_role"],
            "weather_field_digest": _field_digest(lines),
            "sapling_mesh_digest": inherited_row["sapling_mesh_digest"],
            "scene": scene,
        })

    motion = _motion_metrics(states, variant_source["wind_xy"], float(variant_source["visual_speed_m_per_s"]))
    static_reference = base._static_signature(inherited_states[0]["scene"])
    checks = {
        "exact_parent_vfx_head_declared": EXPECTED_PARENT_VFX_HEAD == "3e641a5ea7b2507a53e5ff1a8fba0f0f9c94abaf",
        "exact_parent_current_world_vfx_rebuild_passes": inherited.get("status") == base.STATUS and all(inherited.get("checks", {}).values()),
        "exact_weather_variation_head_observed": _git_head(weather_variant_root) == EXPECTED_WEATHER_VARIANT_HEAD,
        "selected_weather_variant_source_gate_passes": variant_receipt.get("status") == "PASS" and weather_evidence.get("status") == "PASS",
        "selected_seed_exact": int(variant_receipt.get("seed", -1)) == EXPECTED_VARIANT_SEED,
        "selected_layout_digest_exact": variant_receipt.get("particle_layout_digest") == EXPECTED_LAYOUT_DIGEST,
        "seventeen_state_schedule_preserved": [row["time_s"] for row in states] == [row["time_s"] for row in inherited_states],
        "static_current_world_state_preserved": all(base._static_signature(row["scene"]) == static_reference for row in states),
        "sapling_sequence_preserved_exactly": [row["sapling_mesh_digest"] for row in states] == [row["sapling_mesh_digest"] for row in inherited_states]
        and all(row["scene"]["sapling"] == inherited_row["scene"]["sapling"] for row, inherited_row in zip(states, inherited_states)),
        "all_weather_fields_are_variant_not_baseline": all(row["scene"]["weather_lines"] != inherited_row["scene"]["weather_lines"] for row, inherited_row in zip(states, inherited_states)),
        "all_17_variant_weather_fields_distinct": len({row["weather_field_digest"] for row in states}) == 17,
        "all_36_variant_streaks_retained": all(len(row["scene"]["weather_lines"]) == 36 for row in states),
        "variant_particle_identity_order_stable": not motion["identity_errors"],
        "variant_motion_matches_existing_visual_speed": motion["maximum_adjacent_projected_displacement_error_m"] <= TOL,
        "variant_crosswind_drift_zero_in_v0": motion["maximum_adjacent_crosswind_drift_m"] <= TOL,
        "source_opacity_profile_present_and_stable": bool(opacity_profiles) and all(profile == opacity_profiles[0] for profile in opacity_profiles[1:]) and len({opacity for _, opacity in opacity_profiles[0]}) > 1,
        "source_opacity_values_bounded": all(0.0 <= opacity <= 1.0 for profile in opacity_profiles for _, opacity in profile),
    }

    values = [opacity for _, opacity in opacity_profiles[0]] if opacity_profiles else []
    payload = {
        "schema": SCHEMA,
        "study_id": "environment-current-world-weather-variant-001",
        "status": STATUS if all(checks.values()) else "FAIL",
        "receiving_head": os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD"),
        "parent_vfx_head": EXPECTED_PARENT_VFX_HEAD,
        "environment_donor_head": inherited["environment_donor_head"],
        "dense_vfx_donor_head": inherited["dense_vfx_donor_head"],
        "dense_vfx_sequence_digest": inherited["dense_vfx_sequence_digest"],
        "weather_base_head": EXPECTED_WEATHER_BASE_HEAD,
        "weather_variant_head": EXPECTED_WEATHER_VARIANT_HEAD,
        "weather_variant_seed": EXPECTED_VARIANT_SEED,
        "weather_variant_candidate_source_digest": variant_receipt["candidate_source_digest"],
        "weather_variant_layout_digest": variant_receipt["particle_layout_digest"],
        "weather_variant_family_digest": variant_receipt["family_digest"],
        "rear_migration_head": inherited["rear_migration_head"],
        "rear_migrated_mesh_digest": inherited["rear_migrated_mesh_digest"],
        "checks": checks,
        "measurements": {
            "maximum_adjacent_weather_projection_error_m": motion["maximum_adjacent_projected_displacement_error_m"],
            "maximum_adjacent_weather_crosswind_drift_m": motion["maximum_adjacent_crosswind_drift_m"],
        },
        "source_opacity": {
            "count": len(values),
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
            "mean": sum(values) / len(values) if values else None,
        },
        "sampling_schedule_s": [row["time_s"] for row in states],
        "states": states,
        "truth_boundary": (
            "PASS proves only that one exact source-owned Weather PR #3 seeded layout can replace the baseline Weather layout across the exact current-world 17-state VFX receiving sequence while static world state, sapling deformation sequence, visual wind semantics, particle identity and source opacity consumption remain bounded and explicit. "
            "It does not prove better art direction, arbitrary seeds, physical weather, renderer interpolation, wall-clock playback, target-device performance, gameplay, CANON, production readiness, or VFX mastery."
        ),
    }
    payload["variant_rebind_digest"] = base.digest({
        "parent_vfx_head": payload["parent_vfx_head"],
        "weather_variant_head": payload["weather_variant_head"],
        "seed": payload["weather_variant_seed"],
        "layout": payload["weather_variant_layout_digest"],
        "scenes": [row["scene"]["scene_digest"] for row in states],
    })
    return payload


def verify_target_host(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path) -> dict[str, Any]:
    root = Path(image_root)
    samples = receipt.get("samples", [])
    unique = {context: set() for context in CONTEXTS}
    counters = {context: set() for context in CONTEXTS}
    frame_rows: list[dict[str, Any]] = []
    weather_ids = set()
    sapling_ids = set()
    rear_modes = set()
    opacity_modes = set()
    all_frames = True

    for sample in samples:
        weather = sample.get("weather_update", {})
        sapling = sample.get("sapling_update", {})
        weather_ids.add((int(weather.get("node_instance_id", -1)), int(weather.get("mesh_instance_id", -1)), int(weather.get("material_instance_id", -1))))
        sapling_ids.add((int(sapling.get("node_instance_id", -1)), int(sapling.get("mesh_instance_id", -1)), int(sapling.get("material_instance_id", -1))))
        opacity_modes.add(str(weather.get("opacity_mode", "")))
        target = [row for row in sample.get("static_source_meshes", []) if row.get("asset_id") == TARGET_REAR_ASSET_ID]
        if len(target) == 1:
            rear_modes.add(str(target[0].get("proof_culling", "")))
        for context in CONTEXTS:
            row = sample.get("contexts", {}).get(context, {})
            capture = row.get("capture", {})
            path = root / Path(str(capture.get("path", ""))).name
            present = path.exists()
            all_frames = all_frames and present
            frame = {"index": int(sample.get("index", -1)), "context": context, "present": present}
            if present:
                digest = base.sha256(path)
                frame["sha256"] = digest
                unique[context].add(digest)
            runtime = row.get("runtime", {})
            counter = (int(runtime.get("draw_calls_in_frame", -1)), int(runtime.get("objects_in_frame", -1)), int(runtime.get("primitives_in_frame", -1)))
            counters[context].add(counter)
            frame["runtime"] = {"draw_calls": counter[0], "objects": counter[1], "primitives": counter[2]}
            frame_rows.append(frame)

    checks = {
        "structural_variant_payload_passes_first": payload.get("status") == STATUS and all(payload.get("checks", {}).values()),
        "proof_runtime_exact": receipt.get("proof_runtime") == "Godot 4.7.2 GL Compatibility",
        "receipt_variant_seed_exact": int(receipt.get("weather_variant_seed", -1)) == EXPECTED_VARIANT_SEED,
        "receipt_variant_layout_digest_exact": receipt.get("weather_variant_layout_digest") == EXPECTED_LAYOUT_DIGEST,
        "all_17_runtime_samples_present": len(samples) == 17,
        "all_34_frames_present": all_frames and len(frame_rows) == 34,
        "all_17_frames_distinct_per_camera": all(len(unique[context]) == 17 for context in CONTEXTS),
        "runtime_counters_stable_within_each_camera": all(len(counters[context]) == 1 for context in CONTEXTS),
        "weather_resource_identity_stable": len(weather_ids) == 1 and next(iter(weather_ids), (-1, -1, -1))[0] > 0,
        "sapling_resource_identity_stable": len(sapling_ids) == 1 and next(iter(sapling_ids), (-1, -1, -1))[0] > 0,
        "source_opacity_vertex_alpha_consumed": opacity_modes == {"SOURCE_STREAK_OPACITY_VERTEX_ALPHA"} and all(bool(sample.get("weather_update", {}).get("source_opacity_consumed")) for sample in samples),
        "rear_tree_backface_culling_retained": rear_modes == {"CULL_BACK"},
    }
    return {
        "schema": TARGET_SCHEMA,
        "study_id": "environment-current-world-weather-variant-target-host-001",
        "state": TARGET_STATUS if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": payload.get("receiving_head"),
        "parent_vfx_head": EXPECTED_PARENT_VFX_HEAD,
        "weather_variant_head": EXPECTED_WEATHER_VARIANT_HEAD,
        "weather_variant_seed": EXPECTED_VARIANT_SEED,
        "weather_variant_layout_digest": EXPECTED_LAYOUT_DIGEST,
        "proof_runtime": receipt.get("proof_runtime"),
        "runtime_counter_sets": {context: [list(row) for row in sorted(counters[context])] for context in CONTEXTS},
        "frames": frame_rows,
        "truth_boundary": (
            "PASS proves target-host consumption of the selected exact source-owned Weather seeded layout across the exact current-world 17-state visual sequence with stable proof resources and retained rear-tree culling in two fixed cameras. "
            "It does not prove arbitrary-seed quality, wall-clock playback, interpolation, physical weather, target-device performance, gameplay, final art direction, CANON, production readiness, or VFX mastery."
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
    build.add_argument("--weather-base-root", required=True)
    build.add_argument("--weather-variant-root", required=True)
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
            args.weather_base_root,
            args.weather_variant_root,
            args.building_root,
            args.historical_rear_root,
            args.migrated_rear_root,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": payload["status"], "checks": payload["checks"], "variant_rebind_digest": payload["variant_rebind_digest"], "source_opacity": payload["source_opacity"]}, indent=2, sort_keys=True))
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
