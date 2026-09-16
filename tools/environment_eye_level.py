from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_real_slice as integration

SCHEMA = "axm.environment-eye-level-proof/v0.1"
EVIDENCE_SCHEMA = "axm.environment-eye-level-proof-evidence/v0.1"


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def build_scene_payload(manifest_path: str | Path, nature_root: str | Path, weather_root: str | Path) -> dict:
    root = Path(__file__).resolve().parents[1]
    manifest = integration.load_manifest(manifest_path)
    report, variant, target, world_mesh, _, weather_module, weather_source = integration.evaluate_integration(
        root, manifest, nature_root, weather_root
    )
    if report["status"] != "PASS":
        raise ValueError("environment source integration must PASS before eye-level proof")

    sample_time = float(manifest["weather_overlay"]["sample_time_s"])
    particles = weather_module.make_particles(weather_source)
    weather_lines = []
    for index, particle in enumerate(particles):
        sample = weather_module.sample_particle(particle, weather_source, sample_time)
        weather_lines.append({
            "id": particle["id"],
            "tail_xy": [float(sample["tail_x"]), float(sample["tail_y"])],
            "head_xy": [float(sample["x"]), float(sample["y"])],
            "opacity": float(particle["opacity"]),
            "presentation_height_m": 3.0,
            "source_order": index,
        })

    items = []
    for item in variant["items"]:
        if item["asset_id"] == target["asset_id"]:
            continue
        items.append({
            "asset_id": item["asset_id"],
            "kind": item["kind"],
            "evidence": item.get("evidence"),
            "position_m": [float(x) for x in item["position"]],
            "size_m": [float(x) for x in item["size"]],
            "rotation_deg": float(item.get("rotation_deg", 0.0)),
        })

    path = variant["readable_path"]
    width, height = map(float, variant["scene_size_m"])
    path_x = (float(path["x_min"]) + float(path["x_max"])) * 0.5
    path_y0, path_y1 = float(path["y_min"]), float(path["y_max"])
    cameras = {
        "path_eye": {
            "position_source_xyz_m": [path_x, path_y0 + 1.0, 1.7],
            "target_source_xyz_m": [path_x, min(path_y1 - 0.8, path_y0 + 9.0), 1.55],
            "fov_deg": 54.0,
            "purpose": "eye-level readable-path depth/occlusion evidence",
        },
        "elevated_oblique": {
            "position_source_xyz_m": [width * 0.42, -height * 0.62, 8.5],
            "target_source_xyz_m": [0.0, 0.0, 1.2],
            "fov_deg": 50.0,
            "purpose": "cross-asset composition and source-replacement context",
        },
    }

    payload = {
        "schema": SCHEMA,
        "study_id": "environment-eye-level-001",
        "receiving_head": os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD"),
        "source_integration": {
            "study_id": report["study_id"],
            "status": report["status"],
            "base_variant": report["base_variant"],
            "replacement": report["replacement"],
            "weather_overlay": report["weather_overlay"],
        },
        "scene_size_m": [width, height],
        "readable_path": {
            "x_min": float(path["x_min"]),
            "x_max": float(path["x_max"]),
            "y_min": path_y0,
            "y_max": path_y1,
        },
        "items": items,
        "sapling": {
            "asset_id": "source:nature:sapling-neutral-001",
            "truth_state": "SOURCE_OWNED_CANDIDATE_NOT_FINAL",
            "vertices_source_xyz_m": [[float(x) for x in v] for v in world_mesh["vertices"]],
            "triangles": [[int(i) for i in tri] for tri in world_mesh["triangles"]],
            "proof_render_culling": "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_MATERIAL_ACCEPTANCE",
        },
        "weather_lines": weather_lines,
        "weather_presentation": {
            "height_m": 3.0,
            "semantics": "RENDER_PRESENTATION_ONLY_OF_SOURCE_OWNED_2D_VISUAL_FIELD_NOT_PHYSICAL_ALTITUDE",
        },
        "cameras": cameras,
        "truth_boundary": (
            "This payload preserves the exact environment integration sources and creates two fixed observation cameras. "
            "A rendered PASS proves only that the current mixed scene can be captured from those views in the pinned proof host. "
            "It does not prove final environment art, traversal, collision, physical weather altitude, final materials/lighting, runtime performance, Art Director acceptance, CANON, or mastery."
        ),
    }
    payload["scene_digest"] = digest(payload)
    return payload


def evaluate(payload: dict) -> dict:
    kinds = {item["kind"] for item in payload["items"]}
    checks = {
        "source_integration_pass": payload["source_integration"]["status"] == "PASS",
        "map_surface_present": "map-surface" in kinds,
        "building_proxy_present": "building-proxy" in kinds,
        "remaining_nature_proxy_present": "nature-proxy" in kinds,
        "object_proxy_present": "object-proxy" in kinds,
        "real_sapling_present": len(payload["sapling"]["vertices_source_xyz_m"]) == 390 and len(payload["sapling"]["triangles"]) == 570,
        "weather_field_present": len(payload["weather_lines"]) == int(payload["source_integration"]["weather_overlay"]["particle_count"]),
        "two_fixed_views_present": set(payload["cameras"]) == {"path_eye", "elevated_oblique"},
        "weather_truth_boundary_preserved": payload["weather_presentation"]["semantics"] == "RENDER_PRESENTATION_ONLY_OF_SOURCE_OWNED_2D_VISUAL_FIELD_NOT_PHYSICAL_ALTITUDE",
        "sapling_material_truth_boundary_preserved": payload["sapling"]["proof_render_culling"] == "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_MATERIAL_ACCEPTANCE",
    }
    return {
        "schema": EVIDENCE_SCHEMA,
        "study_id": payload["study_id"],
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "scene_digest": payload["scene_digest"],
        "receiving_head": payload["receiving_head"],
        "asset_type_counts": {
            kind: sum(1 for item in payload["items"] if item["kind"] == kind)
            for kind in sorted(kinds)
        },
        "sapling_vertices": len(payload["sapling"]["vertices_source_xyz_m"]),
        "sapling_triangles": len(payload["sapling"]["triangles"]),
        "weather_streaks": len(payload["weather_lines"]),
        "cameras": payload["cameras"],
        "truth_boundary": payload["truth_boundary"],
    }


def build(manifest_path: str | Path, nature_root: str | Path, weather_root: str | Path, output_dir: str | Path) -> dict:
    payload = build_scene_payload(manifest_path, nature_root, weather_root)
    report = evaluate(payload)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "scene_runtime.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "eye_level_evidence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_real_slice_001.json")
    parser.add_argument("--nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--output", default="evidence/environment_eye_level_001")
    args = parser.parse_args()
    report = build(args.manifest, args.nature_root, args.weather_root, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
