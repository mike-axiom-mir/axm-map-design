from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

SCHEMA = "axm.environment-live-object-current-world-runtime-budget/v0.1"
STATUS = "PASS_CURRENT_WORLD_OBJECT_SOURCE_ONE_SLOT_PROOF_HOST_BUDGET"
EXPECTED_BASELINE_HEAD = "3e641a5ea7b2507a53e5ff1a8fba0f0f9c94abaf"
EXPECTED_ENVIRONMENT_DONOR_HEAD = "5ad4ef48a33eaaf76f6fefef315896da10b17eb4"
EXPECTED_OBJECT_SOURCE_ID = "source:object:modular-equipment-case-001"
EXPECTED_OBJECT_SOURCE_HEAD = "d3fa10a270faae7925811f44f03381fe5c5d0215"
EXPECTED_OBJECT_VERTICES = 468
EXPECTED_OBJECT_TRIANGLES = 812
EXPECTED_BUFFER_DELTA = 47_976
EXPECTED_PRIMITIVE_DELTA = 1_600
CONTEXTS = ("path_eye", "elevated_oblique")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _one(rows: list[dict[str, Any]], asset_id: str) -> dict[str, Any]:
    hits = [row for row in rows if row.get("asset_id") == asset_id]
    if len(hits) != 1:
        raise ValueError(f"expected one {asset_id}, found {len(hits)}")
    return hits[0]


def _runtime_tuple(sample: dict[str, Any], context: str) -> tuple[int, int, int, int, int]:
    row = sample["contexts"][context]["runtime"]
    return (
        int(row["draw_calls_in_frame"]),
        int(row["objects_in_frame"]),
        int(row["primitives_in_frame"]),
        int(row["buffer_mem_bytes"]),
        int(row["texture_mem_bytes"]),
    )


def _pixel_diff(a: Path, b: Path) -> dict[str, Any]:
    with Image.open(a).convert("RGB") as ia, Image.open(b).convert("RGB") as ib:
        if ia.size != ib.size:
            raise ValueError(f"image size drift: {a}={ia.size}, {b}={ib.size}")
        diff = ImageChops.difference(ia, ib)
        pixels = diff.load()
        changed = 0
        bbox = None
        min_x, min_y = ia.size[0], ia.size[1]
        max_x = max_y = -1
        for y in range(ia.size[1]):
            for x in range(ia.size[0]):
                if pixels[x, y] != (0, 0, 0):
                    changed += 1
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        if changed:
            bbox = [min_x, min_y, max_x, max_y]
        total = ia.size[0] * ia.size[1]
        return {
            "changed_pixels": changed,
            "total_pixels": total,
            "changed_fraction": changed / total,
            "bbox_xyxy": bbox,
            "baseline_sha256": sha256(a),
            "candidate_sha256": sha256(b),
        }


def compare(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    payload: dict[str, Any],
    baseline_images: Path,
    candidate_images: Path,
    expected_candidate_head: str,
) -> dict[str, Any]:
    if baseline.get("receiving_head") != EXPECTED_BASELINE_HEAD:
        raise ValueError("baseline runtime is not exact PR20 head")
    if candidate.get("receiving_head") != expected_candidate_head:
        raise ValueError("candidate runtime head drift")
    if payload.get("receiving_head") != expected_candidate_head:
        raise ValueError("candidate payload head drift")
    if payload.get("status") != "PASS_LIVE_WORLD_OBJECT_SOURCE_COMPOSITION_STRUCTURE":
        raise ValueError("candidate Environment structure must PASS first")
    if payload.get("object_source_head") != EXPECTED_OBJECT_SOURCE_HEAD:
        raise ValueError("Object source donor drift")
    if payload.get("atmosphere_donor_head") != EXPECTED_BASELINE_HEAD:
        raise ValueError("candidate atmosphere donor drift")
    if baseline.get("proof_runtime") != "Godot 4.7.2 GL Compatibility" or candidate.get("proof_runtime") != baseline.get("proof_runtime"):
        raise ValueError("proof runtime drift")

    bs = baseline.get("samples", [])
    cs = candidate.get("samples", [])
    if len(bs) != 17 or len(cs) != 17:
        raise ValueError("expected 17 baseline and candidate samples")

    base_static = baseline.get("static_source_meshes", [])
    cand_static = candidate.get("static_source_meshes", [])
    object_row = _one(cand_static, EXPECTED_OBJECT_SOURCE_ID)
    cand_without_object = [row for row in cand_static if row.get("asset_id") != EXPECTED_OBJECT_SOURCE_ID]

    checks: dict[str, bool] = {
        "candidate_environment_donor_identity_known": EXPECTED_ENVIRONMENT_DONOR_HEAD == "5ad4ef48a33eaaf76f6fefef315896da10b17eb4",
        "baseline_exact_pr20": baseline.get("receiving_head") == EXPECTED_BASELINE_HEAD,
        "candidate_exact_head": candidate.get("receiving_head") == expected_candidate_head,
        "same_pinned_proof_runtime": baseline.get("proof_runtime") == candidate.get("proof_runtime") == "Godot 4.7.2 GL Compatibility",
        "exact_17_state_schedule_retained": len(bs) == len(cs) == 17,
        "candidate_static_sources_are_baseline_plus_object": cand_without_object == base_static,
        "object_runtime_signature_exact": int(object_row.get("vertices", -1)) == EXPECTED_OBJECT_VERTICES and int(object_row.get("triangles", -1)) == EXPECTED_OBJECT_TRIANGLES and object_row.get("proof_culling") == "CULL_DISABLED",
    }

    state_identity_ok = True
    counter_rows: dict[str, list[dict[str, Any]]] = {c: [] for c in CONTEXTS}
    for b, c in zip(bs, cs):
        state_identity_ok = state_identity_ok and all(
            b.get(k) == c.get(k)
            for k in ("index", "time_s", "sampling_role", "weather_field_digest", "sapling_mesh_digest")
        )
        for context in CONTEXTS:
            bt = _runtime_tuple(b, context)
            ct = _runtime_tuple(c, context)
            counter_rows[context].append({
                "index": int(b["index"]),
                "baseline": {
                    "draw_calls": bt[0], "objects": bt[1], "primitives": bt[2], "buffer_bytes": bt[3], "texture_bytes": bt[4]
                },
                "candidate": {
                    "draw_calls": ct[0], "objects": ct[1], "primitives": ct[2], "buffer_bytes": ct[3], "texture_bytes": ct[4]
                },
                "delta": {
                    "draw_calls": ct[0]-bt[0], "objects": ct[1]-bt[1], "primitives": ct[2]-bt[2], "buffer_bytes": ct[3]-bt[3], "texture_bytes": ct[4]-bt[4]
                },
            })
    checks["dynamic_weather_sapling_state_identity_exact"] = state_identity_ok

    context_summary: dict[str, Any] = {}
    for context, rows in counter_rows.items():
        deltas = {tuple(r["delta"].values()) for r in rows}
        baseline_sets = {tuple(r["baseline"].values()) for r in rows}
        candidate_sets = {tuple(r["candidate"].values()) for r in rows}
        delta = rows[0]["delta"]
        context_summary[context] = {
            "baseline_counter_sets": [list(v) for v in sorted(baseline_sets)],
            "candidate_counter_sets": [list(v) for v in sorted(candidate_sets)],
            "delta": delta,
        }
        checks[f"{context}_counters_stable_across_17_states"] = len(deltas) == len(baseline_sets) == len(candidate_sets) == 1
        checks[f"{context}_one_slot_draw_object_budget"] = delta["draw_calls"] == 0 and delta["objects"] == 0
        checks[f"{context}_no_texture_residency_delta"] = delta["texture_bytes"] == 0
        checks[f"{context}_buffer_delta_exact"] = delta["buffer_bytes"] == EXPECTED_BUFFER_DELTA
        checks[f"{context}_primitive_delta_exact"] = delta["primitives"] == EXPECTED_PRIMITIVE_DELTA

    visuals: dict[str, list[dict[str, Any]]] = {c: [] for c in CONTEXTS}
    for context in CONTEXTS:
        for i in range(17):
            name = f"atmosphere-current-{context}-{i:02d}.png"
            visuals[context].append({"index": i, **_pixel_diff(baseline_images / name, candidate_images / name)})
        changed_values = {row["changed_pixels"] for row in visuals[context]}
        checks[f"{context}_static_visual_delta_stable_all_17_states"] = len(changed_values) == 1 and next(iter(changed_values)) > 0

    result = {
        "schema": SCHEMA,
        "study_id": "environment-live-object-current-world-runtime-budget-001",
        "state": STATUS if all(checks.values()) else "FAIL",
        "baseline_head": EXPECTED_BASELINE_HEAD,
        "environment_donor_head": EXPECTED_ENVIRONMENT_DONOR_HEAD,
        "candidate_head": expected_candidate_head,
        "object_source_head": EXPECTED_OBJECT_SOURCE_HEAD,
        "object_source_runtime_signature": object_row,
        "checks": checks,
        "contexts": context_summary,
        "visual_comparison": visuals,
        "art_direction_tradeoff": "INTENTIONAL_STATIC_OBJECT_SOURCE_REPLACEMENT_DELTA_ONLY; RUNTIME BUDGET LANE CHANGES NO SCENE GEOMETRY, MATERIAL, CAMERA, LIGHTING, OR MOTION",
        "truth_boundary": (
            "PASS proves only an exact proof-host import/runtime budget for replacing the west Object proxy with the exact 468-vertex/812-triangle Object source in the exact 17-state current-world scene: no extra draw-call slot, no extra visible-object slot, no texture-residency delta, and stable measured buffer/RenderingServer primitive deltas on pinned Godot 4.7.2 GL Compatibility. It does not prove target-device FPS/GPU time/VRAM, generic primitive semantics, production allocator behavior, LOD/streaming policy, final art, gameplay, CANON, production readiness, or Runtime mastery."
        ),
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-runtime", type=Path, required=True)
    ap.add_argument("--candidate-runtime", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-image-root", type=Path, required=True)
    ap.add_argument("--candidate-image-root", type=Path, required=True)
    ap.add_argument("--expected-candidate-head", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = compare(
        json.loads(args.baseline_runtime.read_text()),
        json.loads(args.candidate_runtime.read_text()),
        json.loads(args.candidate_payload.read_text()),
        args.baseline_image_root,
        args.candidate_image_root,
        args.expected_candidate_head,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"state": result["state"], "contexts": result["contexts"], "visual_changed_pixels": {k: sorted({r['changed_pixels'] for r in v}) for k,v in result['visual_comparison'].items()}}, indent=2, sort_keys=True))
    return 0 if result["state"] == STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
