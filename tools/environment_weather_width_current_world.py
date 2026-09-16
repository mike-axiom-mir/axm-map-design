from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-current-world-weather-width-evidence/v0.1"
STATUS = "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE"
TARGET_SCHEMA = "axm.environment-current-world-weather-width-target-host/v0.1"
TARGET_STATUS = "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_TARGET_HOST"
EXPECTED_PARENT_VARIANT_HEAD = "e482d003853e52fc835f1797ddfb6506a50083ef"
EXPECTED_PARENT_SCHEMA = "axm.environment-current-world-weather-variant-evidence/v0.1"
EXPECTED_PARENT_STATUS = "PASS_CURRENT_WORLD_WEATHER_VARIANT_REBIND_STRUCTURE"
EXPECTED_WEATHER_VARIANT_HEAD = "05b26c4e82bbe0a4de0ee7bee34179efc58b9719"
EXPECTED_VARIANT_SEED = 44021
EXPECTED_LAYOUT_DIGEST = "7ed55e93ea9445345016685320716006bc52960b33784cb620ca5670a74cc26f"
CONTEXTS = ("path_eye", "elevated_oblique")
TARGET_REAR_ASSET_ID = "source:nature:east-rear-tree-neutral-001"
WIDTH_MIN_PX = 1.0
WIDTH_MAX_PX = 2.4
WIDTH_RESIDUAL_TOL_PX = 0.05


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _git_head(root: str | Path) -> str:
    return subprocess.run(
        ["git", "-C", str(Path(root).resolve()), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_exact_width_profile(weather_variant_root: str | Path) -> tuple[dict[str, float], dict[str, Any]]:
    root = Path(weather_variant_root).resolve()
    if _git_head(root) != EXPECTED_WEATHER_VARIANT_HEAD:
        raise ValueError("Weather variation donor checkout drift")
    wind = _load_module("axm_weather_width_wind", root / "tools" / "wind_atmosphere.py")
    family_mod = _load_module("axm_weather_width_family", root / "tools" / "weather_variation_family.py")
    source = wind.load_study(root / "examples" / "wind_atmosphere_baseline_001.json")
    family = family_mod.load_family(root / "examples" / "wind_atmosphere_variation_family_001.json")
    _candidate, particles, receipt = family_mod.evaluate_variant(source, family, EXPECTED_VARIANT_SEED)
    if receipt.get("status") != "PASS":
        raise ValueError("selected Weather variant must PASS source-local family gate")
    if receipt.get("particle_layout_digest") != EXPECTED_LAYOUT_DIGEST:
        raise ValueError("selected Weather layout digest drift")
    profile = {str(row["id"]): float(row["width_px"]) for row in particles}
    if len(profile) != len(particles):
        raise ValueError("Weather streak IDs must be unique")
    return profile, receipt


def _load_parent(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != EXPECTED_PARENT_SCHEMA:
        raise ValueError("parent Weather variant schema drift")
    if data.get("status") != EXPECTED_PARENT_STATUS or not all(data.get("checks", {}).values()):
        raise ValueError("parent Weather variant proof must PASS exactly")
    if data.get("receiving_head") != EXPECTED_PARENT_VARIANT_HEAD:
        raise ValueError("parent Weather variant exact-head drift")
    if data.get("weather_variant_head") != EXPECTED_WEATHER_VARIANT_HEAD:
        raise ValueError("parent Weather variation head drift")
    if int(data.get("weather_variant_seed", -1)) != EXPECTED_VARIANT_SEED:
        raise ValueError("parent Weather seed drift")
    if data.get("weather_variant_layout_digest") != EXPECTED_LAYOUT_DIGEST:
        raise ValueError("parent Weather layout digest drift")
    if len(data.get("states", [])) != 17:
        raise ValueError("parent proof must retain exactly 17 states")
    return data


def build_payload(parent_path: str | Path, weather_variant_root: str | Path) -> dict[str, Any]:
    parent = _load_parent(parent_path)
    width_profile, source_receipt = _load_exact_width_profile(weather_variant_root)
    ordered_ids = list(width_profile)
    widths = list(width_profile.values())

    states: list[dict[str, Any]] = []
    all_line_ids_exact = True
    all_non_width_fields_preserved = True
    all_profiles_exact = True
    for parent_state in parent["states"]:
        state = copy.deepcopy(parent_state)
        scene = state["scene"]
        parent_lines = parent_state["scene"]["weather_lines"]
        line_ids = [str(row["id"]) for row in parent_lines]
        all_line_ids_exact = all_line_ids_exact and line_ids == ordered_ids
        new_lines: list[dict[str, Any]] = []
        for row in parent_lines:
            new_row = copy.deepcopy(row)
            streak_id = str(row["id"])
            if streak_id not in width_profile:
                raise ValueError(f"unknown Weather streak ID {streak_id}")
            new_row["source_width_px"] = width_profile[streak_id]
            new_lines.append(new_row)
            reduced = {key: value for key, value in new_row.items() if key != "source_width_px"}
            all_non_width_fields_preserved = all_non_width_fields_preserved and reduced == row
        scene["schema"] = "axm.environment-current-world-weather-width-state/v0.1"
        scene["weather_lines"] = new_lines
        scene["weather_width_binding"] = {
            "repository": "mike-axiom-mir/axm-weather-design",
            "variation_head": EXPECTED_WEATHER_VARIANT_HEAD,
            "seed": EXPECTED_VARIANT_SEED,
            "particle_layout_digest": EXPECTED_LAYOUT_DIGEST,
            "semantics": "SOURCE_AUTHORED_SCREEN_PIXEL_STREAK_WIDTH_PRESENTATION_ONLY",
            "receiving_policy": "CAMERA_PROJECTED_RIBBON_MATCH_EXACT_FIXED_VIEW_PIXEL_WIDTH",
        }
        scene["parent_scene_digest"] = parent_state["scene"].get("scene_digest", "")
        scene.pop("scene_digest", None)
        scene["scene_digest"] = digest(scene)
        state["scene"] = scene
        state["weather_width_profile_digest"] = digest([(row["id"], row["source_width_px"]) for row in new_lines])
        states.append(state)
        all_profiles_exact = all_profiles_exact and [float(row["source_width_px"]) for row in new_lines] == widths

    checks = {
        "exact_parent_variant_head_observed": parent.get("receiving_head") == EXPECTED_PARENT_VARIANT_HEAD,
        "exact_weather_variant_head_observed": _git_head(weather_variant_root) == EXPECTED_WEATHER_VARIANT_HEAD,
        "exact_seed_and_layout_observed": int(source_receipt.get("seed", -1)) == EXPECTED_VARIANT_SEED and source_receipt.get("particle_layout_digest") == EXPECTED_LAYOUT_DIGEST,
        "all_17_parent_states_retained": len(states) == 17,
        "all_36_source_widths_retained": len(width_profile) == 36 and all(len(row["scene"]["weather_lines"]) == 36 for row in states),
        "weather_streak_identity_order_exact": all_line_ids_exact,
        "all_parent_line_fields_preserved": all_non_width_fields_preserved,
        "source_width_profile_stable_all_states": all_profiles_exact and len({row["weather_width_profile_digest"] for row in states}) == 1,
        "source_widths_within_authored_range": bool(widths) and min(widths) >= WIDTH_MIN_PX and max(widths) <= WIDTH_MAX_PX,
        "source_widths_materially_nonuniform": len({round(value, 12) for value in widths}) > 1,
        "sapling_sequence_preserved": [row["sapling_mesh_digest"] for row in states] == [row["sapling_mesh_digest"] for row in parent["states"]],
        "weather_field_sequence_preserved": [row["weather_field_digest"] for row in states] == [row["weather_field_digest"] for row in parent["states"]],
    }
    payload = {
        "schema": SCHEMA,
        "study_id": "environment-current-world-weather-source-width-001",
        "status": STATUS if all(checks.values()) else "FAIL",
        "receiving_head": os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD"),
        "parent_variant_head": EXPECTED_PARENT_VARIANT_HEAD,
        "parent_variant_rebind_digest": parent.get("variant_rebind_digest", ""),
        "weather_variant_head": EXPECTED_WEATHER_VARIANT_HEAD,
        "weather_variant_seed": EXPECTED_VARIANT_SEED,
        "weather_variant_layout_digest": EXPECTED_LAYOUT_DIGEST,
        "source_width_profile": [{"id": key, "width_px": value} for key, value in width_profile.items()],
        "source_width_profile_digest": digest(list(width_profile.items())),
        "source_width_summary": {
            "count": len(widths),
            "minimum_px": min(widths) if widths else None,
            "mean_px": sum(widths) / len(widths) if widths else None,
            "maximum_px": max(widths) if widths else None,
        },
        "checks": checks,
        "states": states,
        "truth_boundary": (
            "PASS proves only exact source-width identity binding for the already-proven Weather seed 44021 current-world sequence. "
            "The source width is authored in screen pixels and is presented only as a fixed-view camera-projected ribbon target. "
            "This does not prove arbitrary resolution/camera equivalence, physical precipitation size, volumetrics, gameplay visibility, target-device performance, final art, CANON, production readiness, or VFX mastery."
        ),
    }
    payload["weather_width_binding_digest"] = digest({
        "parent": payload["parent_variant_head"],
        "weather": payload["weather_variant_head"],
        "layout": payload["weather_variant_layout_digest"],
        "width_profile": payload["source_width_profile_digest"],
        "scenes": [row["scene"]["scene_digest"] for row in states],
    })
    return payload


def verify_target_host(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path) -> dict[str, Any]:
    root = Path(image_root)
    samples = receipt.get("samples", [])
    control_hashes: dict[str, set[str]] = {context: set() for context in CONTEXTS}
    candidate_hashes: dict[str, set[str]] = {context: set() for context in CONTEXTS}
    control_counter_sets: dict[str, set[tuple[int, int, int]]] = {context: set() for context in CONTEXTS}
    candidate_counter_sets: dict[str, set[tuple[int, int, int]]] = {context: set() for context in CONTEXTS}
    weather_ids: set[tuple[int, int, int]] = set()
    sapling_ids: set[tuple[int, int, int]] = set()
    rear_modes: set[str] = set()
    all_frames = True
    all_pairwise_different = True
    max_width_residual = 0.0
    measured_width_count = 0

    for sample in samples:
        sapling = sample.get("sapling_update", {})
        sapling_ids.add((int(sapling.get("node_instance_id", -1)), int(sapling.get("mesh_instance_id", -1)), int(sapling.get("material_instance_id", -1))))
        for source in sample.get("static_source_meshes", []):
            if source.get("asset_id") == TARGET_REAR_ASSET_ID:
                rear_modes.add(str(source.get("proof_culling", "")))
        for context in CONTEXTS:
            row = sample.get("contexts", {}).get(context, {})
            control = row.get("control", {})
            candidate = row.get("candidate", {})
            candidate_weather = candidate.get("weather_update", {})
            weather_ids.add((int(candidate_weather.get("node_instance_id", -1)), int(candidate_weather.get("mesh_instance_id", -1)), int(candidate_weather.get("material_instance_id", -1))))
            max_width_residual = max(max_width_residual, float(candidate_weather.get("maximum_projected_width_residual_px", 999.0)))
            measured_width_count += int(candidate_weather.get("measured_width_count", 0))
            for mode_name, mode, hash_sets, counter_sets in (
                ("control", control, control_hashes, control_counter_sets),
                ("candidate", candidate, candidate_hashes, candidate_counter_sets),
            ):
                shot = mode.get("capture", {})
                path = root / Path(str(shot.get("path", ""))).name
                if not path.exists():
                    all_frames = False
                    continue
                sha = hashlib.sha256(path.read_bytes()).hexdigest()
                hash_sets[context].add(sha)
                stats = mode.get("runtime", {})
                counter_sets[context].add((
                    int(stats.get("draw_calls_in_frame", -1)),
                    int(stats.get("objects_in_frame", -1)),
                    int(stats.get("primitives_in_frame", -1)),
                ))
            cpath = root / Path(str(control.get("capture", {}).get("path", ""))).name
            wpath = root / Path(str(candidate.get("capture", {}).get("path", ""))).name
            if cpath.exists() and wpath.exists():
                all_pairwise_different = all_pairwise_different and hashlib.sha256(cpath.read_bytes()).digest() != hashlib.sha256(wpath.read_bytes()).digest()

    checks = {
        "structure_passed_before_target_host": payload.get("status") == STATUS and all(payload.get("checks", {}).values()),
        "exact_receiving_head_matches": receipt.get("receiving_head") == payload.get("receiving_head"),
        "exact_parent_variant_head_matches": receipt.get("parent_variant_head") == EXPECTED_PARENT_VARIANT_HEAD,
        "seventeen_live_samples_retained": len(samples) == 17,
        "all_68_control_candidate_frames_retained": all_frames and sum(len(v) for v in control_hashes.values()) == 34 and sum(len(v) for v in candidate_hashes.values()) == 34,
        "all_control_candidate_pairs_visibly_different_by_bytes": all_pairwise_different,
        "candidate_source_width_projection_within_tolerance": max_width_residual <= WIDTH_RESIDUAL_TOL_PX and measured_width_count == 17 * 2 * 36,
        "one_weather_resource_identity_stable": len(weather_ids) == 1 and next(iter(weather_ids), (-1, -1, -1))[0] > 0,
        "one_sapling_resource_identity_stable": len(sapling_ids) == 1 and next(iter(sapling_ids), (-1, -1, -1))[0] > 0,
        "rear_tree_culling_state_preserved": rear_modes == {"CULL_BACK"},
        "control_counter_sets_stable_per_camera": all(len(values) == 1 for values in control_counter_sets.values()),
        "candidate_counter_sets_stable_per_camera": all(len(values) == 1 for values in candidate_counter_sets.values()),
    }
    return {
        "schema": TARGET_SCHEMA,
        "state": TARGET_STATUS if all(checks.values()) else "FAIL",
        "receiving_head": payload.get("receiving_head"),
        "parent_variant_head": EXPECTED_PARENT_VARIANT_HEAD,
        "checks": checks,
        "maximum_projected_width_residual_px": max_width_residual,
        "measured_width_count": measured_width_count,
        "control_runtime_counter_sets": {key: sorted([list(row) for row in values]) for key, values in control_counter_sets.items()},
        "candidate_runtime_counter_sets": {key: sorted([list(row) for row in values]) for key, values in candidate_counter_sets.items()},
        "truth_boundary": (
            "PASS proves the exact 36 source-authored Weather screen-pixel widths are represented within the declared pixel tolerance across all 17 states and both fixed 1100x720 cameras in pinned Godot 4.7.2 GL Compatibility, while source opacity, Weather/Sapling resource identity and rear-tree culling remain explicit. "
            "It does not prove arbitrary camera/resolution fidelity, target-device performance, physical weather dimensions, gameplay visibility, final art, CANON, or VFX mastery."
        ),
    }


def _write_json(path: str | Path, value: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--parent", required=True)
    build_parser.add_argument("--weather-variant-root", required=True)
    build_parser.add_argument("--output", required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--payload", required=True)
    verify_parser.add_argument("--receipt", required=True)
    verify_parser.add_argument("--image-root", required=True)
    verify_parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.command == "build":
        result = build_payload(args.parent, args.weather_variant_root)
    else:
        payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
        result = verify_target_host(payload, receipt, args.image_root)
    _write_json(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
