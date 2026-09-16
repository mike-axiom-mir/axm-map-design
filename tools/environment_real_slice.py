from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_composition as composition
import environment_variation as variation

SCHEMA = "axm.environment-source-integration/v0.1"
EVIDENCE_SCHEMA = "axm.environment-source-integration-evidence/v0.1"


def load_manifest(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unsupported environment integration schema")
    return data


def _load_module(name: str, path: str | Path):
    spec = importlib.util.spec_from_file_location(name, Path(path))
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load dependency module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bounds(vertices):
    if not vertices:
        raise ValueError("mesh has no vertices")
    mins = [min(float(v[i]) for v in vertices) for i in range(3)]
    maxs = [max(float(v[i]) for v in vertices) for i in range(3)]
    return {
        "min": mins,
        "max": maxs,
        "size": [maxs[i] - mins[i] for i in range(3)],
    }


def _intersects(a, b, clearance=0.0):
    return not (
        a[1] + clearance <= b[0]
        or b[1] + clearance <= a[0]
        or a[3] + clearance <= b[2]
        or b[3] + clearance <= a[2]
    )


def _inside(inner, outer, tolerance=1e-9):
    return (
        inner[0] >= outer[0] - tolerance
        and inner[1] <= outer[1] + tolerance
        and inner[2] >= outer[2] - tolerance
        and inner[3] <= outer[3] + tolerance
    )


def _unique_edges(triangles):
    edges = set()
    for a, b, c in triangles:
        for x, y in ((a, b), (b, c), (c, a)):
            edges.add(tuple(sorted((int(x), int(y)))))
    return sorted(edges)


def _world_nature_mesh(mesh: dict, target_item: dict) -> tuple[dict, dict]:
    local = _bounds(mesh["vertices"])
    local_center_x = (local["min"][0] + local["max"][0]) * 0.5
    local_center_y = (local["min"][1] + local["max"][1]) * 0.5
    tx = float(target_item["position"][0]) - local_center_x
    ty = float(target_item["position"][1]) - local_center_y
    tz = -local["min"][2]
    vertices = [[float(v[0]) + tx, float(v[1]) + ty, float(v[2]) + tz] for v in mesh["vertices"]]
    world = {
        "schema": mesh.get("schema"),
        "vertices": vertices,
        "triangles": copy.deepcopy(mesh["triangles"]),
        "regions": copy.deepcopy(mesh.get("regions", [])),
    }
    return world, _bounds(vertices)


def _world_footprint(bounds: dict):
    return (bounds["min"][0], bounds["max"][0], bounds["min"][1], bounds["max"][1])


def _load_dependencies(manifest: dict, nature_root: str | Path, weather_root: str | Path):
    nature_root = Path(nature_root)
    weather_root = Path(weather_root)
    nature_cfg = manifest["nature_replacement"]
    weather_cfg = manifest["weather_overlay"]
    nature_module = _load_module("axm_nature_source_for_environment", nature_root / nature_cfg["module_path"])
    weather_module = _load_module("axm_weather_source_for_environment", weather_root / weather_cfg["module_path"])
    nature_source = nature_module.load_source(nature_root / nature_cfg["source_path"])
    weather_source = weather_module.load_study(weather_root / weather_cfg["source_path"])
    return nature_module, nature_source, weather_module, weather_source


def _load_variant(root: Path, manifest: dict):
    base = composition.load_study(root / "examples/environment_baseline_001.json")
    family = variation.load_family(root / "examples/environment_variation_family_001.json")
    seed = int(manifest["base_variant"]["seed"])
    result = variation.generate_variant(base, family, seed)
    if result["status"] != "PASS" or result["study"] is None:
        raise ValueError("pinned procedural base variant no longer passes")
    return base, family, result


def evaluate_integration(
    root: str | Path,
    manifest: dict,
    nature_root: str | Path,
    weather_root: str | Path,
    placement_xy: tuple[float, float] | None = None,
):
    root = Path(root)
    _, _, variant_result = _load_variant(root, manifest)
    variant = variant_result["study"]
    variant_evidence = composition.evaluate(variant)

    nature_module, nature_source, weather_module, weather_source = _load_dependencies(
        manifest, nature_root, weather_root
    )
    nature_evidence = nature_module.build_evidence(nature_source)
    nature_mesh = nature_module.build_mesh(nature_source)
    weather_evidence = weather_module.evaluate(weather_source)

    nature_cfg = manifest["nature_replacement"]
    target_id = nature_cfg["replacement_target"]
    targets = [item for item in variant["items"] if item["asset_id"] == target_id]
    if len(targets) != 1:
        raise ValueError("replacement target must exist exactly once")
    target = copy.deepcopy(targets[0])
    if target.get("kind") != "nature-proxy" or target.get("evidence") != "PROXY_ONLY":
        raise ValueError("replacement target must still be the explicit nature proxy")
    if nature_cfg.get("placement_policy") != "PRESERVE_VARIANT_CENTER_XY__GROUND_SOURCE_MIN_Z__NO_FORM_SCALE__NO_EXTRA_ROTATION":
        raise ValueError("unsupported placement policy")
    if placement_xy is not None:
        target["position"][0] = float(placement_xy[0])
        target["position"][1] = float(placement_xy[1])

    world_mesh, world_bounds = _world_nature_mesh(nature_mesh, target)
    real_footprint = _world_footprint(world_bounds)
    reserved_footprint = composition._footprint(target)

    path = variant["readable_path"]
    path_box = (path["x_min"], path["x_max"], path["y_min"], path["y_max"])
    remaining_solids = [
        item for item in variant["items"]
        if item["kind"] != "map-surface" and item["asset_id"] != target_id
    ]
    spacing_conflicts = [
        item["asset_id"]
        for item in remaining_solids
        if _intersects(real_footprint, composition._footprint(item), float(variant["minimum_gap_m"]))
    ]

    wx, wy = map(float, variant["weather_context"]["wind_xy"])
    swx, swy = map(float, weather_source["wind_xy"])
    sample_time = float(manifest["weather_overlay"]["sample_time_s"])
    target_vertical_top = float(target["position"][2]) + float(target["size"][2]) * 0.5

    checks = {
        "base_variant_structural_pass": variant_evidence["status"] == "PASS",
        "base_variant_digest_matches": variant_result["study_digest"] == manifest["base_variant"]["expected_study_digest"],
        "nature_source_revalidated": nature_evidence.get("state") == "PASS_AUTHORED_ORGANIC_FORM_INTENT",
        "nature_source_digest_matches": nature_module.digest(nature_source) == nature_cfg["expected_source_digest"],
        "nature_mesh_digest_matches": nature_module.digest(nature_mesh) == nature_cfg["expected_mesh_digest"],
        "real_footprint_inside_reserved_proxy_envelope": _inside(real_footprint, reserved_footprint),
        "real_height_inside_reserved_proxy_envelope": world_bounds["min"][2] >= -1e-9 and world_bounds["max"][2] <= target_vertical_top + 1e-9,
        "readable_path_unblocked_after_replacement": not _intersects(real_footprint, path_box),
        "minimum_spacing_preserved_after_replacement": not spacing_conflicts,
        "weather_source_revalidated": weather_evidence.get("status") == "PASS",
        "weather_source_digest_matches": weather_module.digest(weather_source) == manifest["weather_overlay"]["expected_source_digest"],
        "weather_scene_extent_matches": list(map(float, weather_source["scene_size_m"])) == list(map(float, variant["scene_size_m"])),
        "weather_direction_matches_map_context": abs(wx - swx) <= 1e-12 and abs(wy - swy) <= 1e-12,
        "weather_stays_visual_only": weather_source.get("wind_semantics") == "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED" and manifest["weather_overlay"].get("relationship") == "VISUAL_OVERLAY_ONLY_NOT_PHYSICAL_WEATHER",
        "weather_sample_is_authored": any(abs(float(t) - sample_time) <= 1e-12 for t in weather_source["times_s"]),
        "source_owned_candidate_truth_state_preserved": nature_cfg.get("evidence") == "SOURCE_OWNED_CANDIDATE_NOT_FINAL",
    }

    status = "PASS" if all(checks.values()) else "FAIL"
    report = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": manifest["study_id"],
        "status": status,
        "checks": checks,
        "base_variant": {
            "seed": manifest["base_variant"]["seed"],
            "study_digest": variant_result["study_digest"],
            "attempt_index": variant_result["receipt"]["attempt_index"],
            "source_evidence_status": variant_evidence["status"],
        },
        "replacement": {
            "target_asset_id": target_id,
            "reserved_proxy_position_m": target["position"],
            "reserved_proxy_size_m": target["size"],
            "reserved_proxy_rotation_deg": target.get("rotation_deg", 0.0),
            "reserved_proxy_footprint_m": list(reserved_footprint),
            "real_world_bounds_m": world_bounds,
            "real_world_footprint_m": list(real_footprint),
            "nature_vertices": len(nature_mesh["vertices"]),
            "nature_triangles": len(nature_mesh["triangles"]),
            "spacing_conflicts": spacing_conflicts,
            "source_repository": nature_cfg["repository"],
            "source_head": nature_cfg["head"],
            "source_digest": nature_module.digest(nature_source),
            "mesh_digest": nature_module.digest(nature_mesh),
        },
        "weather_overlay": {
            "source_repository": manifest["weather_overlay"]["repository"],
            "source_head": manifest["weather_overlay"]["head"],
            "source_digest": weather_module.digest(weather_source),
            "sample_time_s": sample_time,
            "particle_count": weather_evidence["particle_count"],
            "semantics": weather_source["wind_semantics"],
        },
        "truth_boundary": manifest["truth_boundary"],
    }
    return report, variant, target, world_mesh, world_bounds, weather_module, weather_source


def build_obj(variant: dict, target: dict, world_mesh: dict) -> str:
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]
    lines = [
        "# AXM environment real slice 001",
        "# map/building/remaining nature/object geometry remains PROXY_ONLY",
        "# source:nature sapling geometry is SOURCE_OWNED_CANDIDATE_NOT_FINAL",
    ]
    start = 1
    for item in variant["items"]:
        if item["asset_id"] == target["asset_id"]:
            continue
        lines.append(f'o {item["asset_id"]}')
        vertices = composition._box_vertices(item)
        lines.extend(f"v {x:.9f} {y:.9f} {z:.9f}" for x, y, z in vertices)
        lines.extend("f " + " ".join(str(start + v) for v in face) for face in faces)
        start += len(vertices)

    lines.append('o source:nature:sapling-neutral-001')
    lines.extend(f"v {v[0]:.9f} {v[1]:.9f} {v[2]:.9f}" for v in world_mesh["vertices"])
    lines.extend(
        "f " + " ".join(str(start + int(index)) for index in tri)
        for tri in world_mesh["triangles"]
    )
    return "\n".join(lines) + "\n"


def build_after_svg(variant: dict, target: dict, world_mesh: dict, weather_module, weather_source: dict, sample_time: float) -> str:
    width, height = map(float, variant["scene_size_m"])
    scale, pad = 30.0, 24.0
    total_w, total_h = width * scale + pad * 2, height * scale + pad * 2
    sx = lambda x: pad + (float(x) + width / 2.0) * scale
    sy = lambda y: pad + (height / 2.0 - float(y)) * scale
    colors = {
        "map-surface": "#d9d0bd",
        "building-proxy": "#6f7782",
        "nature-proxy": "#78956d",
        "object-proxy": "#a07a55",
    }
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}" viewBox="0 0 {total_w:.0f} {total_h:.0f}">',
        '<rect width="100%" height="100%" fill="#f5f3ee"/>',
        f'<text x="{pad}" y="18" font-family="sans-serif" font-size="13">Environment real slice 001 — seed 29 / source-owned sapling + visual weather overlay</text>',
    ]
    path = variant["readable_path"]
    lines.append(
        f'<rect x="{sx(path["x_min"]):.1f}" y="{sy(path["y_max"]):.1f}" '
        f'width="{(path["x_max"]-path["x_min"])*scale:.1f}" height="{(path["y_max"]-path["y_min"])*scale:.1f}" '
        'fill="#dbe6ef" stroke="#53758a" stroke-dasharray="6 4"/>'
    )
    for item in variant["items"]:
        if item["asset_id"] == target["asset_id"]:
            continue
        x0, x1, y0, y1 = composition._footprint(item)
        lines.append(
            f'<rect x="{sx(x0):.1f}" y="{sy(y1):.1f}" width="{(x1-x0)*scale:.1f}" height="{(y1-y0)*scale:.1f}" '
            f'fill="{colors[item["kind"]]}" fill-opacity="0.72" stroke="#222"/>'
        )

    rx0, rx1, ry0, ry1 = composition._footprint(target)
    lines.append(
        f'<rect x="{sx(rx0):.1f}" y="{sy(ry1):.1f}" width="{(rx1-rx0)*scale:.1f}" height="{(ry1-ry0)*scale:.1f}" '
        'fill="none" stroke="#2b6e3f" stroke-width="1.2" stroke-dasharray="4 3"/>'
    )
    for a, b in _unique_edges(world_mesh["triangles"]):
        va, vb = world_mesh["vertices"][a], world_mesh["vertices"][b]
        lines.append(
            f'<line x1="{sx(va[0]):.2f}" y1="{sy(va[1]):.2f}" x2="{sx(vb[0]):.2f}" y2="{sy(vb[1]):.2f}" '
            'stroke="#1f5f35" stroke-width="0.65" stroke-opacity="0.62"/>'
        )

    particles = weather_module.make_particles(weather_source)
    for particle in particles:
        sample = weather_module.sample_particle(particle, weather_source, sample_time)
        lines.append(
            f'<line x1="{sx(sample["tail_x"]):.2f}" y1="{sy(sample["tail_y"]):.2f}" '
            f'x2="{sx(sample["x"]):.2f}" y2="{sy(sample["y"]):.2f}" '
            f'stroke="#3a69a8" stroke-width="{float(particle["width_px"]):.2f}" opacity="{float(particle["opacity"])*0.62:.3f}" stroke-linecap="round"/>'
        )
    lines.extend([
        f'<text x="{sx(target["position"][0]):.1f}" y="{sy(target["position"][1])-8:.1f}" font-family="sans-serif" font-size="8" text-anchor="middle">source:nature:sapling-neutral-001</text>',
        f'<text x="{pad}" y="{total_h-8:.1f}" font-family="sans-serif" font-size="10">weather overlay: source-owned visual streak field at t={sample_time:.2f}s — not physical wind</text>',
        '</svg>',
    ])
    return "\n".join(lines) + "\n"


def build_comparison_svg(before_svg: str, after_svg: str) -> str:
    def body(svg: str) -> str:
        return svg.split('>', 1)[1].rsplit('</svg>', 1)[0]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="588" viewBox="0 0 1536 588">\n'
        f'<svg x="0" y="0" width="768" height="588" viewBox="0 0 768 588">{body(before_svg)}</svg>\n'
        f'<svg x="768" y="0" width="768" height="588" viewBox="0 0 768 588">{body(after_svg)}</svg>\n'
        '</svg>\n'
    )


def build(manifest_path: str | Path, nature_root: str | Path, weather_root: str | Path, output_dir: str | Path):
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(manifest_path)
    report, variant, target, world_mesh, _, weather_module, weather_source = evaluate_integration(
        root, manifest, nature_root, weather_root
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    before_svg = composition.build_top_svg(variant)
    after_svg = build_after_svg(
        variant,
        target,
        world_mesh,
        weather_module,
        weather_source,
        float(manifest["weather_overlay"]["sample_time_s"]),
    )
    (output / "before_seed29_proxy.svg").write_text(before_svg, encoding="utf-8")
    (output / "after_source_slice.svg").write_text(after_svg, encoding="utf-8")
    (output / "comparison.svg").write_text(build_comparison_svg(before_svg, after_svg), encoding="utf-8")
    (output / "scene.obj").write_text(build_obj(variant, target, world_mesh), encoding="utf-8")
    (output / "evidence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_real_slice_001.json")
    parser.add_argument("--nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--output", default="evidence/environment_real_slice_001")
    args = parser.parse_args()
    report = build(args.manifest, args.nature_root, args.weather_root, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
