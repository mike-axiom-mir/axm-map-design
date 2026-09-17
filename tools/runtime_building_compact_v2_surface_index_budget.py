#!/usr/bin/env python3
"""Verify post-normal surface indexing for the exact current-world Building compact-v2 receiver.

The candidate changes only receiver storage: the existing five compact-v2 surfaces are
built exactly as Environment already proved, normals are generated exactly as before,
and SurfaceTool.index() is applied afterwards per surface. This verifier compares the
candidate to the exact retained unindexed compact-v2 run and to the exact active-world
segmented receiver so a source-relative optimization cannot hide a consumer regression.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

SCHEMA = "axm.runtime-building-compact-v2-surface-index-budget/v0.1"
ENVIRONMENT_HEAD = "ef2cb9cc84edc10ab66c2230daca625623e0b00d"
UNINDEXED_RUN = 35179857530
UNINDEXED_ARTIFACT = 10480305129
ACTIVE_RUN = 35179857526
ACTIVE_ARTIFACT = 10478624997
INDEX_SCHEMA = "axm.runtime-building-compact-v2-surface-indexing-observation/v0.1"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def runtime_path(root: Path) -> Path:
    for candidate in (root / "candidate" / "runtime.json", root / "runtime.json"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"runtime.json not found under {root}")


def rendered_dir(root: Path) -> Path:
    for candidate in (root / "candidate" / "rendered", root / "rendered"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"rendered directory not found under {root}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def runtime_rows(runtime: dict) -> dict[tuple[int, str, str], dict]:
    rows = {}
    for sample in runtime.get("samples", []):
        index = int(sample["index"])
        contexts = sample.get("contexts", {})
        for camera, modes in contexts.items():
            for mode, payload in modes.items():
                rows[(index, camera, mode)] = payload["runtime"]
    return rows


def find_building(sample: dict) -> dict:
    matches = [row for row in sample.get("static_source_meshes", []) if row.get("asset_id") == "source:building:service-pavilion-001"]
    if len(matches) != 1:
        raise ValueError(f"expected one Building row, got {len(matches)}")
    return matches[0]


def image_delta(a_path: Path, b_path: Path) -> dict:
    with Image.open(a_path).convert("RGB") as a, Image.open(b_path).convert("RGB") as b:
        if a.size != b.size:
            raise ValueError(f"image size drift: {a_path.name}: {a.size} vs {b.size}")
        diff = ImageChops.difference(a, b)
        bbox = diff.getbbox()
        changed = 0
        max_channel = 0
        if bbox is not None:
            for px in diff.getdata():
                local = max(px)
                if local:
                    changed += 1
                    max_channel = max(max_channel, local)
        return {
            "byte_identical": bbox is None,
            "changed_pixels": changed,
            "max_channel_delta_lsb": max_channel,
            "bbox": list(bbox) if bbox is not None else None,
            "size": list(a.size),
            "sha256_a": sha256_file(a_path),
            "sha256_b": sha256_file(b_path),
        }


def verify(active_root: Path, unindexed_root: Path, indexed_root: Path, exact_head: str, output: Path) -> None:
    active = load_json(runtime_path(active_root))
    unindexed = load_json(runtime_path(unindexed_root))
    indexed = load_json(runtime_path(indexed_root))

    if unindexed.get("environment_building_compact_v2_representation_id") != "boundary-only-union-shell-conforming-compact-v2-001":
        raise ValueError("unindexed compact-v2 identity drift")
    if indexed.get("environment_building_compact_v2_representation_id") != unindexed.get("environment_building_compact_v2_representation_id"):
        raise ValueError("indexed representation identity drift")
    if indexed.get("runtime_building_compact_v2_surface_indexing_result") != "CANDIDATE_INDEXED_AFTER_FINAL_NORMAL_GENERATION":
        raise ValueError("indexed receipt marker missing")
    if len(active.get("samples", [])) != 17 or len(unindexed.get("samples", [])) != 17 or len(indexed.get("samples", [])) != 17:
        raise ValueError("expected 17 samples in all runtime receipts")

    index_receipts = []
    for sample in indexed["samples"]:
        building = find_building(sample)
        receipt = building.get("runtime_building_compact_v2_surface_indexing", {})
        if receipt.get("schema") != INDEX_SCHEMA:
            raise ValueError("candidate Building index receipt missing/schema drift")
        before = receipt["before"]
        after = receipt["after"]
        if before["surface_count"] != 5 or before["total_vertices"] != 6156 or before["total_indices"] != 0 or before["total_primitives"] != 2052:
            raise ValueError(f"unexpected unindexed Building render storage: {before}")
        if after["surface_count"] != 5 or after["total_indices"] != 6156 or after["total_primitives"] != 2052:
            raise ValueError(f"indexed Building identity drift: {after}")
        if after["total_vertices"] >= before["total_vertices"]:
            raise ValueError("indexing did not reduce stored vertices")
        index_receipts.append(receipt)
    first_receipt = index_receipts[0]
    if any(row["before"] != first_receipt["before"] or row["after"] != first_receipt["after"] for row in index_receipts[1:]):
        raise ValueError("Building indexing representation changed across states")

    before = first_receipt["before"]
    after = first_receipt["after"]
    modeled_control_bytes = int(before["total_vertices"]) * 24
    modeled_candidate_bytes = int(after["total_vertices"]) * 24 + int(after["total_indices"]) * 4
    modeled_saved = modeled_control_bytes - modeled_candidate_bytes
    if modeled_saved <= 0:
        raise ValueError("modeled indexed payload did not reduce")

    active_rows = runtime_rows(active)
    unindexed_rows = runtime_rows(unindexed)
    indexed_rows = runtime_rows(indexed)
    if set(active_rows) != set(unindexed_rows) or set(indexed_rows) != set(unindexed_rows):
        raise ValueError("runtime observation key drift")
    if len(indexed_rows) != 68:
        raise ValueError(f"expected 68 runtime observations, got {len(indexed_rows)}")

    keys = ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "buffer_mem_bytes", "texture_mem_bytes")
    indexed_vs_unindexed = []
    indexed_vs_active = []
    for key in sorted(indexed_rows):
        idx = indexed_rows[key]
        un = unindexed_rows[key]
        act = active_rows[key]
        d_un = {name: int(idx[name]) - int(un[name]) for name in keys}
        d_act = {name: int(idx[name]) - int(act[name]) for name in keys}
        if d_un["draw_calls_in_frame"] != 0 or d_un["objects_in_frame"] != 0 or d_un["primitives_in_frame"] != 0 or d_un["texture_mem_bytes"] != 0:
            raise ValueError(f"post-normal indexing changed non-buffer proof-host counters at {key}: {d_un}")
        if d_un["buffer_mem_bytes"] >= 0:
            raise ValueError(f"post-normal indexing did not reduce observed buffer memory at {key}: {d_un}")
        indexed_vs_unindexed.append(d_un)
        indexed_vs_active.append(d_act)

    stable_buffer_delta = sorted({row["buffer_mem_bytes"] for row in indexed_vs_unindexed})
    if len(stable_buffer_delta) != 1:
        raise ValueError(f"indexing buffer delta is not stable: {stable_buffer_delta}")

    unindexed_dir = rendered_dir(unindexed_root)
    indexed_dir = rendered_dir(indexed_root)
    unindexed_names = sorted(p.name for p in unindexed_dir.glob("atmosphere-width-*.png"))
    indexed_names = sorted(p.name for p in indexed_dir.glob("atmosphere-width-*.png"))
    if unindexed_names != indexed_names or len(indexed_names) != 68:
        raise ValueError("rendered frame-set drift")
    visual_rows = {name: image_delta(unindexed_dir / name, indexed_dir / name) for name in indexed_names}
    changed_frames = [name for name, row in visual_rows.items() if not row["byte_identical"]]
    max_changed_pixels = max(row["changed_pixels"] for row in visual_rows.values())
    max_channel_delta = max(row["max_channel_delta_lsb"] for row in visual_rows.values())
    if changed_frames:
        visual_tradeoff = f"MEASURED_POST_NORMAL_INDEXING_RENDER_DELTA__ART_REVIEW_REQUIRED__CHANGED_FRAMES_{len(changed_frames)}__MAX_PIXELS_{max_changed_pixels}__MAX_LSB_{max_channel_delta}"
        state = "PASS_BUILDING_COMPACT_V2_POST_NORMAL_INDEX_REDUCES_BUFFER__HOLD_VISUAL_REVIEW"
    else:
        visual_tradeoff = "NONE_OBSERVED__68_CURRENT_WORLD_FRAMES_BYTE_IDENTICAL"
        state = "PASS_BUILDING_COMPACT_V2_POST_NORMAL_INDEX_REDUCES_CURRENT_WORLD_BUFFER_WITH_NO_OBSERVED_VISUAL_DELTA"

    residual_sets = {name: sorted({row[name] for row in indexed_vs_active}) for name in keys}
    report = {
        "schema": SCHEMA,
        "state": state,
        "exact_runtime_head": exact_head,
        "environment_parent_head": ENVIRONMENT_HEAD,
        "comparison_artifacts": {
            "active_receiver": {"run": ACTIVE_RUN, "artifact": ACTIVE_ARTIFACT},
            "unindexed_compact_v2": {"run": UNINDEXED_RUN, "artifact": UNINDEXED_ARTIFACT},
        },
        "building_representation": {
            "representation_id": "boundary-only-union-shell-conforming-compact-v2-001",
            "surface_count": 5,
            "triangle_count": 2052,
            "before": before,
            "after": after,
            "modeled_payload_model": "POSITION_FLOAT32x3_PLUS_NORMAL_FLOAT32x3_PLUS_UINT32_INDEX__PER_SURFACE",
            "modeled_control_bytes": modeled_control_bytes,
            "modeled_candidate_bytes": modeled_candidate_bytes,
            "modeled_bytes_saved": modeled_saved,
            "modeled_reduction_percent": round(100.0 * modeled_saved / modeled_control_bytes, 9),
        },
        "proof_host": {
            "observation_count": len(indexed_rows),
            "indexed_vs_unindexed_stable_buffer_delta_bytes": stable_buffer_delta[0],
            "indexed_vs_unindexed_non_buffer_counter_delta": {
                "draw_calls_in_frame": 0,
                "objects_in_frame": 0,
                "primitives_in_frame": 0,
                "texture_mem_bytes": 0,
            },
            "indexed_vs_active_delta_sets": residual_sets,
        },
        "visuals": {
            "frame_count": len(indexed_names),
            "changed_frame_count": len(changed_frames),
            "max_changed_pixels": max_changed_pixels,
            "max_channel_delta_lsb": max_channel_delta,
            "tradeoff": visual_tradeoff,
        },
        "decision": "POST_NORMAL_PER_SURFACE_INDEXING_IS_A_REAL_RECEIVER_STORAGE_WIN__KEEP_ART_VISUAL_PREFERENCE_AND_ACTIVE_CONSUMER_BUDGET_AS_SEPARATE_GATES",
        "truth_boundary": "This proves only the exact current-world compact-v2 receiver storage change on the pinned Godot proof host. It does not alter source topology or material roles, does not claim target-device CPU/GPU/FPS/VRAM/heap gains, and does not authorize Environment adoption. Residual cost versus the active segmented receiver remains explicit.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--active-root", type=Path, required=True)
    p.add_argument("--unindexed-root", type=Path, required=True)
    p.add_argument("--indexed-root", type=Path, required=True)
    p.add_argument("--exact-head", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    verify(args.active_root, args.unindexed_root, args.indexed_root, args.exact_head, args.output)


if __name__ == "__main__":
    main()
