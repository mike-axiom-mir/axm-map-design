from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_eye_level as eye
import environment_real_slice as integration

SCHEMA = "axm.environment-motion-scene-proof/v0.1"
EVIDENCE_SCHEMA = "axm.environment-motion-scene-proof-evidence/v0.1"
EXPECTED_NATURE_RESPONSE_HEAD = "cee14f5b3feea78b0adcd044bad2ea3c97657fc6"
NEUTRAL_TIME_S = 0.0
PEAK_TIME_S = 0.25
MAX_DISPLACEMENT_M = 0.18


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _bounds(vertices: list[list[float]]) -> dict:
    return {
        "min": [min(float(v[i]) for v in vertices) for i in range(3)],
        "max": [max(float(v[i]) for v in vertices) for i in range(3)],
    }


def _footprint(bounds: dict) -> tuple[float, float, float, float]:
    return (bounds["min"][0], bounds["max"][0], bounds["min"][1], bounds["max"][1])


def _inside(inner, outer, tolerance=1e-9) -> bool:
    return (
        inner[0] >= outer[0] - tolerance
        and inner[1] <= outer[1] + tolerance
        and inner[2] >= outer[2] - tolerance
        and inner[3] <= outer[3] + tolerance
    )


def _translation(local_mesh: dict, world_mesh: dict) -> list[float]:
    local = local_mesh["vertices"]
    world = world_mesh["vertices"]
    if len(local) != len(world):
        raise ValueError("neutral local/world vertex count mismatch")
    delta = [float(world[0][i]) - float(local[0][i]) for i in range(3)]
    for before, after in zip(local, world):
        for axis in range(3):
            if abs((float(after[axis]) - float(before[axis])) - delta[axis]) > 1e-9:
                raise ValueError("environment placement must remain a translation-only receiving transform")
    return delta


def _translate_mesh(mesh: dict, delta: list[float]) -> dict:
    return {
        "schema": mesh.get("schema"),
        "vertices": [
            [float(v[0]) + delta[0], float(v[1]) + delta[1], float(v[2]) + delta[2]]
            for v in mesh["vertices"]
        ],
        "triangles": [[int(i) for i in tri] for tri in mesh["triangles"]],
        "regions": mesh.get("regions", []),
    }


def _load_response(nature_root: str | Path):
    root = Path(nature_root).resolve()
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    organic = importlib.import_module("axm_nature_design.organic_form")
    response = importlib.import_module("axm_nature_design.wind_response")
    source = organic.load_source(root / "examples" / "sapling_neutral_001.json")
    spec = response.load_spec(root / "examples" / "sapling_wind_response_001.json")
    evidence = response.build_evidence(source, spec)
    if evidence.get("state") != "PASS_BOUNDED_VISUAL_WIND_RESPONSE":
        raise ValueError("pinned Nature response must re-pass before scene integration")
    neutral = response.deform_mesh(source, spec, NEUTRAL_TIME_S)
    peak = response.deform_mesh(source, spec, PEAK_TIME_S)
    return response, source, spec, evidence, neutral, peak


def build_scene_payload(
    manifest_path: str | Path,
    nature_root: str | Path,
    weather_root: str | Path,
    nature_response_head: str,
) -> dict:
    if nature_response_head != EXPECTED_NATURE_RESPONSE_HEAD:
        raise ValueError("Nature response head does not match the locally accepted Art Direction candidate")

    base = eye.build_scene_payload(manifest_path, nature_root, weather_root)
    manifest = integration.load_manifest(manifest_path)
    report, variant, target, neutral_world_from_integration, _, _, _ = integration.evaluate_integration(
        Path(__file__).resolve().parents[1], manifest, nature_root, weather_root
    )
    if report["status"] != "PASS":
        raise ValueError("static Environment source integration must re-pass before scene motion proof")

    response, source, spec, response_evidence, neutral_local, peak_local = _load_response(nature_root)
    translation = _translation(neutral_local, neutral_world_from_integration)
    neutral_world = _translate_mesh(neutral_local, translation)
    peak_world = _translate_mesh(peak_local, translation)

    if neutral_world["triangles"] != peak_world["triangles"]:
        raise ValueError("scene motion proof may not alter sapling topology")

    neutral_bounds = _bounds(neutral_world["vertices"])
    peak_bounds = _bounds(peak_world["vertices"])
    peak_footprint = _footprint(peak_bounds)
    reserved = tuple(float(x) for x in report["replacement"]["reserved_proxy_footprint_m"])
    path = variant["readable_path"]
    path_box = (float(path["x_min"]), float(path["x_max"]), float(path["y_min"]), float(path["y_max"]))
    spacing_conflicts = [
        item["asset_id"]
        for item in variant["items"]
        if item["kind"] != "map-surface" and item["asset_id"] != target["asset_id"]
        and integration._intersects(peak_footprint, integration.composition._footprint(item), float(variant["minimum_gap_m"]))
    ]

    max_displacement = 0.0
    for before, after in zip(neutral_world["vertices"], peak_world["vertices"]):
        d = sum((float(after[i]) - float(before[i])) ** 2 for i in range(3)) ** 0.5
        max_displacement = max(max_displacement, d)

    states = {
        "neutral": {
            "time_s": NEUTRAL_TIME_S,
            "vertices_source_xyz_m": neutral_world["vertices"],
            "triangles": neutral_world["triangles"],
            "bounds_source_xyz_m": neutral_bounds,
        },
        "peak": {
            "time_s": PEAK_TIME_S,
            "vertices_source_xyz_m": peak_world["vertices"],
            "triangles": peak_world["triangles"],
            "bounds_source_xyz_m": peak_bounds,
        },
    }

    payload = {
        "schema": SCHEMA,
        "study_id": "environment-motion-scene-001",
        "receiving_head": os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD"),
        "nature_response": {
            "repository": "mike-axiom-mir/axm-nature-design",
            "pr": 2,
            "head": nature_response_head,
            "profile": spec["response"]["profile"],
            "state": response_evidence["state"],
            "max_displacement_ceiling_m": float(spec["response"]["max_displacement_ceiling_m"]),
            "weather_semantics": spec["weather_provenance"]["semantics"],
        },
        "source_integration": base["source_integration"],
        "scene_size_m": base["scene_size_m"],
        "readable_path": base["readable_path"],
        "items": base["items"],
        "weather_lines": base["weather_lines"],
        "weather_presentation": base["weather_presentation"],
        "cameras": base["cameras"],
        "sapling": {
            "asset_id": "source:nature:sapling-neutral-001",
            "truth_state": "SOURCE_OWNED_CANDIDATE_NOT_FINAL",
            "proof_render_culling": "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_MATERIAL_ACCEPTANCE",
            "placement_translation_m": translation,
            "states": states,
        },
        "composition_measurements": {
            "neutral_footprint_m": list(_footprint(neutral_bounds)),
            "peak_footprint_m": list(peak_footprint),
            "static_reserved_proxy_footprint_m": list(reserved),
            "peak_inside_static_reserved_proxy_footprint": _inside(peak_footprint, reserved),
            "peak_path_unblocked": not integration._intersects(peak_footprint, path_box),
            "peak_spacing_conflicts": spacing_conflicts,
            "max_neutral_to_peak_displacement_m": max_displacement,
        },
        "truth_boundary": (
            "This proof integrates the exact locally accepted Nature visual-response candidate into the existing seed-29 Environment scene at neutral and peak while preserving placement, cameras, Weather presentation and proxy context. "
            "A PASS proves bounded receiving-scene structural compatibility and successful target-host captures only. It does not prove physical wind, final motion quality, final world-art hierarchy, final materials, gameplay, collision, performance, CANON, or mastery."
        ),
    }
    payload["scene_digest"] = digest(payload)
    return payload


def evaluate(payload: dict) -> dict:
    states = payload["sapling"]["states"]
    measurement = payload["composition_measurements"]
    checks = {
        "schema_matches": payload.get("schema") == SCHEMA,
        "pinned_response_head": payload["nature_response"].get("head") == EXPECTED_NATURE_RESPONSE_HEAD,
        "response_revalidated": payload["nature_response"].get("state") == "PASS_BOUNDED_VISUAL_WIND_RESPONSE",
        "visual_only_weather_semantics_preserved": payload["nature_response"].get("weather_semantics") == "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED",
        "neutral_and_peak_states_present": set(states) == {"neutral", "peak"},
        "fixed_times_preserved": float(states["neutral"]["time_s"]) == NEUTRAL_TIME_S and float(states["peak"]["time_s"]) == PEAK_TIME_S,
        "topology_preserved": states["neutral"]["triangles"] == states["peak"]["triangles"],
        "vertex_count_preserved": len(states["neutral"]["vertices_source_xyz_m"]) == 390 and len(states["peak"]["vertices_source_xyz_m"]) == 390,
        "peak_displacement_bounded": float(measurement["max_neutral_to_peak_displacement_m"]) <= MAX_DISPLACEMENT_M + 1e-9,
        "peak_path_unblocked": bool(measurement["peak_path_unblocked"]),
        "peak_spacing_preserved": not measurement["peak_spacing_conflicts"],
        "same_two_fixed_cameras": set(payload["cameras"]) == {"path_eye", "elevated_oblique"},
        "weather_presentation_boundary_preserved": payload["weather_presentation"]["semantics"] == "RENDER_PRESENTATION_ONLY_OF_SOURCE_OWNED_2D_VISUAL_FIELD_NOT_PHYSICAL_ALTITUDE",
        "proof_material_boundary_preserved": payload["sapling"]["proof_render_culling"] == "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_MATERIAL_ACCEPTANCE",
    }
    return {
        "schema": EVIDENCE_SCHEMA,
        "study_id": payload["study_id"],
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "scene_digest": payload["scene_digest"],
        "receiving_head": payload["receiving_head"],
        "nature_response": payload["nature_response"],
        "composition_measurements": measurement,
        "cameras": payload["cameras"],
        "truth_boundary": payload["truth_boundary"],
    }


def build(manifest_path, nature_root, weather_root, nature_response_head, output_dir) -> dict:
    payload = build_scene_payload(manifest_path, nature_root, weather_root, nature_response_head)
    report = evaluate(payload)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "motion_scene_runtime.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "motion_scene_evidence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_real_slice_001.json")
    parser.add_argument("--nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--nature-response-head", required=True)
    parser.add_argument("--output", default="evidence/environment_motion_scene_001")
    args = parser.parse_args()
    report = build(args.manifest, args.nature_root, args.weather_root, args.nature_response_head, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
