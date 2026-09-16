from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_eye_level as eye

SCHEMA = "axm.environment-sapling-motion-proof/v0.1"
EVIDENCE_SCHEMA = "axm.environment-sapling-motion-proof-evidence/v0.1"
EXPECTED_ENVIRONMENT_BASE_HEAD = "d52cb54a2aeb3eb4f5668e3d6ba4b05ddcc02899"
EXPECTED_NATURE_SOURCE_HEAD = "fbc202449981f2bac153951c561ed0ed6120c936"
EXPECTED_NATURE_VFX_HEAD = "cee14f5b3feea78b0adcd044bad2ea3c97657fc6"
EXPECTED_WEATHER_HEAD = "ca2eaba519e8449835b0ea6ef944b7080c3caa6a"
EXPECTED_ART_DIRECTION_RESULT = "PASS_ART_DIRECTION_LOCAL_SWAY_HIERARCHY_001 / RELEASE_TO_SCENE_INTEGRATION"
EXPECTED_VFX_ARTIFACT_ID = 10429159566
NEUTRAL_TIME_S = 0.0
PEAK_TIME_S = 0.25
TOL = 1e-9


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _git_head(root: str | Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_nature_vfx(root: str | Path):
    root = Path(root)
    src = root / "src"
    old = list(sys.path)
    sys.path.insert(0, str(src))
    try:
        from axm_nature_design import organic_form, wind_response
    finally:
        sys.path[:] = old
    return organic_form, wind_response


def _translation(local_vertices: list[list[float]], world_vertices: list[list[float]]) -> list[float]:
    if len(local_vertices) != len(world_vertices) or not local_vertices:
        raise ValueError("local/world sapling vertex identity mismatch")
    delta = [float(world_vertices[0][i]) - float(local_vertices[0][i]) for i in range(3)]
    for local, world in zip(local_vertices, world_vertices):
        for axis in range(3):
            expected = float(local[axis]) + delta[axis]
            if abs(expected - float(world[axis])) > TOL:
                raise ValueError("environment placement is not a pure source-preserving translation")
    return delta


def _translate(vertices: list[list[float]], delta: list[float]) -> list[list[float]]:
    return [[float(v[i]) + float(delta[i]) for i in range(3)] for v in vertices]


def _max_vertex_delta(a: list[list[float]], b: list[list[float]]) -> float:
    maximum = 0.0
    for before, after in zip(a, b):
        d = sum((float(after[i]) - float(before[i])) ** 2 for i in range(3)) ** 0.5
        maximum = max(maximum, d)
    return maximum


def _xy_bounds(vertices: list[list[float]]) -> dict:
    xs = [float(v[0]) for v in vertices]
    ys = [float(v[1]) for v in vertices]
    return {"x_min": min(xs), "x_max": max(xs), "y_min": min(ys), "y_max": max(ys)}


def _rects_overlap(a: dict, b: dict) -> bool:
    return not (
        float(a["x_max"]) <= float(b["x_min"]) or
        float(a["x_min"]) >= float(b["x_max"]) or
        float(a["y_max"]) <= float(b["y_min"]) or
        float(a["y_min"]) >= float(b["y_max"])
    )


def _state_payload(base: dict, vertices: list[list[float]], sample_time_s: float, state: str, translation: list[float], wind_module, source: dict, spec: dict) -> dict:
    payload = copy.deepcopy(base)
    payload["schema"] = SCHEMA
    payload["study_id"] = "environment-sapling-motion-001"
    payload["environment_base_head"] = EXPECTED_ENVIRONMENT_BASE_HEAD
    payload["sapling"]["vertices_source_xyz_m"] = vertices
    payload["sapling"]["motion_state"] = state
    payload["sapling"]["sample_time_s"] = sample_time_s
    payload["sapling"]["placement_translation_xyz_m"] = translation
    payload["sapling"]["vfx_provenance"] = {
        "repository": "mike-axiom-mir/axm-nature-design",
        "pr": 2,
        "head": EXPECTED_NATURE_VFX_HEAD,
        "artifact_id": EXPECTED_VFX_ARTIFACT_ID,
        "profile": wind_module.PROFILE,
        "source_head": EXPECTED_NATURE_SOURCE_HEAD,
        "weather_head": EXPECTED_WEATHER_HEAD,
        "weather_semantics": wind_module.WEATHER_SEMANTICS,
        "max_displacement_ceiling_m": float(spec["response"]["max_displacement_ceiling_m"]),
        "art_direction_gate": EXPECTED_ART_DIRECTION_RESULT,
    }
    payload["truth_boundary"] = (
        "This state is a receiving-scene observation of the exact locally accepted Nature visual-only response. "
        "It preserves seed-29 placement, fixed Environment cameras, source-owned Weather presentation, and the existing proof material. "
        "A PASS proves only bounded neutral/peak scene integration and direct renderability in the pinned proof host; it does not prove physical wind, continuous playback quality, shaded production deformation, gameplay, collision, performance budgets, final world art, CANON, or mastery."
    )
    payload.pop("scene_digest", None)
    payload["scene_digest"] = digest(payload)
    return payload


def build_motion_payloads(manifest_path: str | Path, nature_source_root: str | Path, nature_vfx_root: str | Path, weather_root: str | Path) -> tuple[dict, dict, dict]:
    if _git_head(nature_source_root) != EXPECTED_NATURE_SOURCE_HEAD:
        raise ValueError("Nature source checkout head mismatch")
    if _git_head(nature_vfx_root) != EXPECTED_NATURE_VFX_HEAD:
        raise ValueError("Nature VFX checkout head mismatch")
    if _git_head(weather_root) != EXPECTED_WEATHER_HEAD:
        raise ValueError("Weather checkout head mismatch")

    base = eye.build_scene_payload(manifest_path, nature_source_root, weather_root)
    organic_form, wind_response = _load_nature_vfx(nature_vfx_root)
    source = _load_json(Path(nature_vfx_root) / "examples" / "sapling_neutral_001.json")
    spec = _load_json(Path(nature_vfx_root) / "examples" / "sapling_wind_response_001.json")
    wind_response.validate_spec(spec, source)

    neutral_local = organic_form.build_mesh(source)
    peak_local = wind_response.deform_mesh(source, spec, PEAK_TIME_S)
    if neutral_local["triangles"] != peak_local["triangles"]:
        raise ValueError("VFX peak may not alter sapling topology")
    if neutral_local["triangles"] != base["sapling"]["triangles"]:
        raise ValueError("Environment sapling topology differs from VFX source topology")

    translation = _translation(neutral_local["vertices"], base["sapling"]["vertices_source_xyz_m"])
    neutral_world = _translate(neutral_local["vertices"], translation)
    peak_world = _translate(peak_local["vertices"], translation)
    maximum = _max_vertex_delta(neutral_world, peak_world)
    ceiling = float(spec["response"]["max_displacement_ceiling_m"])
    if maximum > ceiling + TOL or abs(maximum - ceiling) > 1e-7:
        raise ValueError("scene peak does not preserve exact Nature VFX displacement ceiling")

    readable_path = base["readable_path"]
    neutral_bounds = _xy_bounds(neutral_world)
    peak_bounds = _xy_bounds(peak_world)
    neutral_path_overlap = _rects_overlap(neutral_bounds, readable_path)
    peak_path_overlap = _rects_overlap(peak_bounds, readable_path)
    if neutral_path_overlap or peak_path_overlap:
        raise ValueError("neutral or peak sapling AABB intrudes into declared readable path")

    neutral = _state_payload(base, neutral_world, NEUTRAL_TIME_S, "neutral", translation, wind_response, source, spec)
    peak = _state_payload(base, peak_world, PEAK_TIME_S, "peak", translation, wind_response, source, spec)

    checks = {
        "environment_source_integration_pass": base["source_integration"]["status"] == "PASS",
        "fixed_cameras_preserved": set(base["cameras"]) == {"path_eye", "elevated_oblique"},
        "weather_field_preserved": len(base["weather_lines"]) == 36,
        "topology_preserved": neutral["sapling"]["triangles"] == peak["sapling"]["triangles"],
        "placement_translation_preserved": neutral["sapling"]["placement_translation_xyz_m"] == peak["sapling"]["placement_translation_xyz_m"],
        "exact_peak_ceiling_preserved": abs(maximum - ceiling) <= 1e-7,
        "neutral_path_clear": not neutral_path_overlap,
        "peak_path_clear": not peak_path_overlap,
        "material_lane_not_combined": neutral["sapling"]["proof_render_culling"] == "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_MATERIAL_ACCEPTANCE",
        "visual_only_weather_semantics_preserved": peak["sapling"]["vfx_provenance"]["weather_semantics"] == "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED",
    }
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": "environment-sapling-motion-001",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD"),
        "environment_base_head": EXPECTED_ENVIRONMENT_BASE_HEAD,
        "nature_source_head": EXPECTED_NATURE_SOURCE_HEAD,
        "nature_vfx_head": EXPECTED_NATURE_VFX_HEAD,
        "weather_head": EXPECTED_WEATHER_HEAD,
        "art_direction_gate": EXPECTED_ART_DIRECTION_RESULT,
        "vfx_artifact_id": EXPECTED_VFX_ARTIFACT_ID,
        "neutral_scene_digest": neutral["scene_digest"],
        "peak_scene_digest": peak["scene_digest"],
        "placement_translation_xyz_m": translation,
        "neutral_xy_bounds_m": neutral_bounds,
        "peak_xy_bounds_m": peak_bounds,
        "max_scene_vertex_displacement_m": maximum,
        "declared_vfx_ceiling_m": ceiling,
        "cameras": base["cameras"],
        "truth_boundary": peak["truth_boundary"],
    }
    return neutral, peak, evidence


def build(manifest_path: str | Path, nature_source_root: str | Path, nature_vfx_root: str | Path, weather_root: str | Path, output_dir: str | Path) -> dict:
    neutral, peak, evidence = build_motion_payloads(manifest_path, nature_source_root, nature_vfx_root, weather_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "neutral_scene_runtime.json").write_text(json.dumps(neutral, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "peak_scene_runtime.json").write_text(json.dumps(peak, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "motion_evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_real_slice_001.json")
    parser.add_argument("--nature-source-root", required=True)
    parser.add_argument("--nature-vfx-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--output", default="evidence/environment_sapling_motion_001")
    args = parser.parse_args()
    report = build(args.manifest, args.nature_source_root, args.nature_vfx_root, args.weather_root, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
