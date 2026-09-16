from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

SCHEMA = "axm.environment-composition-study/v0.1"


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def load_study(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unsupported schema")
    return data


def _footprint(item):
    x, y, _ = item["position"]
    sx, sy, _ = item["size"]
    r = math.radians(float(item.get("rotation_deg", 0.0)))
    ex = abs(math.cos(r)) * sx / 2 + abs(math.sin(r)) * sy / 2
    ey = abs(math.sin(r)) * sx / 2 + abs(math.cos(r)) * sy / 2
    return (x - ex, x + ex, y - ey, y + ey)


def _intersects(a, b, clearance=0.0):
    return not (
        a[1] + clearance <= b[0]
        or b[1] + clearance <= a[0]
        or a[3] + clearance <= b[2]
        or b[3] + clearance <= a[2]
    )


def evaluate(data):
    items = data["items"]
    kinds = sorted({item["kind"] for item in items})
    missing = sorted(set(data["required_asset_kinds"]) - set(kinds))
    path = data["readable_path"]
    path_box = (path["x_min"], path["x_max"], path["y_min"], path["y_max"])
    blockers = [
        item["asset_id"]
        for item in items
        if item["kind"] != "map-surface" and _intersects(_footprint(item), path_box)
    ]
    solids = [item for item in items if item["kind"] != "map-surface"]
    spacing = []
    for index, first in enumerate(solids):
        for second in solids[index + 1 :]:
            if _intersects(_footprint(first), _footprint(second), float(data["minimum_gap_m"])):
                spacing.append([first["asset_id"], second["asset_id"]])
    wx, wy = data["weather_context"]["wind_xy"]
    checks = {
        "required_asset_kinds_present": not missing,
        "readable_path_unblocked": not blockers,
        "proxy_spacing_respects_minimum_gap": not spacing,
        "weather_context_has_nonzero_direction": math.hypot(wx, wy) > 0.0,
        "all_items_explicitly_proxy_only": all(item.get("evidence") == "PROXY_ONLY" for item in items),
    }
    return {
        "schema": "axm.environment-composition-evidence/v0.1",
        "study_id": data["study_id"],
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "missing_asset_kinds": missing,
        "path_blockers": blockers,
        "spacing_conflicts": spacing,
        "asset_kinds_observed": kinds,
        "source_digest": digest(data),
        "truth_boundary": data["truth_boundary"],
    }


def _box_vertices(item):
    x, y, z = item["position"]
    sx, sy, sz = item["size"]
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    points = [
        (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
        (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz),
    ]
    a = math.radians(float(item.get("rotation_deg", 0.0)))
    ca, sa = math.cos(a), math.sin(a)
    return [(x + px * ca - py * sa, y + px * sa + py * ca, z + pz) for px, py, pz in points]


def build_obj(data):
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]
    lines = ["# AXM environment composition baseline 001", "# all geometry is PROXY_ONLY"]
    start = 1
    for item in data["items"]:
        lines.append(f'o {item["asset_id"]}')
        vertices = _box_vertices(item)
        lines.extend(f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in vertices)
        lines.extend("f " + " ".join(str(start + v) for v in face) for face in faces)
        start += len(vertices)
    return "\n".join(lines) + "\n"


def build_top_svg(data):
    width, height = data["scene_size_m"]
    scale, pad = 30.0, 24.0
    total_w, total_h = width * scale + pad * 2, height * scale + pad * 2
    sx = lambda x: pad + (x + width / 2) * scale
    sy = lambda y: pad + (height / 2 - y) * scale
    colors = {
        "map-surface": "#d9d0bd",
        "building-proxy": "#6f7782",
        "nature-proxy": "#78956d",
        "object-proxy": "#a07a55",
    }
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}" viewBox="0 0 {total_w:.0f} {total_h:.0f}">',
        '<rect width="100%" height="100%" fill="#f5f3ee"/>',
        f'<text x="{pad}" y="18" font-family="sans-serif" font-size="13">Environment baseline 001 — PROXY composition evidence</text>',
    ]
    path = data["readable_path"]
    lines.append(
        f'<rect x="{sx(path["x_min"]):.1f}" y="{sy(path["y_max"]):.1f}" '
        f'width="{(path["x_max"]-path["x_min"])*scale:.1f}" height="{(path["y_max"]-path["y_min"])*scale:.1f}" '
        'fill="#dbe6ef" stroke="#53758a" stroke-dasharray="6 4"/>'
    )
    for item in data["items"]:
        x0, x1, y0, y1 = _footprint(item)
        lines.append(
            f'<rect x="{sx(x0):.1f}" y="{sy(y1):.1f}" width="{(x1-x0)*scale:.1f}" height="{(y1-y0)*scale:.1f}" '
            f'fill="{colors[item["kind"]]}" fill-opacity="0.78" stroke="#222"/>'
        )
        lines.append(
            f'<text x="{sx(item["position"][0]):.1f}" y="{sy(item["position"][1]):.1f}" font-family="sans-serif" '
            f'font-size="8" text-anchor="middle">{item["asset_id"]}</text>'
        )
    wx, wy = data["weather_context"]["wind_xy"]
    length = math.hypot(wx, wy)
    wx, wy = wx / length, wy / length
    ax, ay = sx(-width / 2 + 2), sy(height / 2 - 2)
    bx, by = ax + wx * 70, ay - wy * 70
    lines.extend([
        f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#3a69a8" stroke-width="4"/>',
        f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="5" fill="#3a69a8"/>',
        '</svg>',
    ])
    return "\n".join(lines) + "\n"


def build(source, output_dir):
    data = load_study(source)
    evidence = evaluate(data)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "scene.obj").write_text(build_obj(data), encoding="utf-8")
    (output / "top.svg").write_text(build_top_svg(data), encoding="utf-8")
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    report = build(root / "examples/environment_baseline_001.json", root / "evidence/environment_baseline_001")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
