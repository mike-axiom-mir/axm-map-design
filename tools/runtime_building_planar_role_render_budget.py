#!/usr/bin/env python3
"""Characterize the exact Building planar-role render receiver in the real Map path.

The exact Hard-Surface candidate is compared against both the actual active segmented
receiver and the best currently measured indexed compact-v2 receiver. Runtime owns only
the consumer cost characterization; Art/Visual QA retain appearance preference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

SCHEMA = "axm.runtime-building-planar-role-render-budget/v0.1"
ENVIRONMENT_HEAD = "ef2cb9cc84edc10ab66c2230daca625623e0b00d"
HARD_SURFACE_HEAD = "93f22e4eeb9bb32516d4b11f8d8bcf47d9792910"
REPRESENTATION_ID = "boundary-only-planar-role-rectangle-render-001"
PAYLOAD_SHA256 = "cf086f2446b8f915378007b4402a5e4f83da09ecd05818b890a3e918563f8b12"
OBS_SCHEMA = "axm.runtime-building-planar-role-render-receiver-observation/v0.1"
ACTIVE_RUN = 35179857526
ACTIVE_ARTIFACT = 10478624997
INDEXED_COMPACT_RUN = 35182141875
INDEXED_COMPACT_ARTIFACT = 10481020383


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def runtime_path(root: Path) -> Path:
    for candidate in (root / "candidate" / "runtime.json", root / "runtime.json", root / "indexed" / "runtime.json"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"runtime.json not found under {root}")


def rendered_dir(root: Path) -> Path:
    for candidate in (root / "candidate" / "rendered", root / "rendered", root / "indexed" / "rendered"):
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
    rows: dict[tuple[int, str, str], dict] = {}
    for sample in runtime.get("samples", []):
        index = int(sample["index"])
        for camera, modes in sample.get("contexts", {}).items():
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
        over_one = 0
        max_channel = 0
        if bbox is not None:
            for px in diff.getdata():
                local = max(px)
                if local:
                    changed += 1
                    max_channel = max(max_channel, local)
                if local > 1:
                    over_one += 1
        return {
            "byte_identical": bbox is None,
            "changed_pixels": changed,
            "pixels_over_1_lsb": over_one,
            "max_channel_delta_lsb": max_channel,
            "bbox": list(bbox) if bbox is not None else None,
            "size": list(a.size),
            "sha256_a": sha256_file(a_path),
            "sha256_b": sha256_file(b_path),
        }


def summarize_visual(reference_dir: Path, candidate_dir: Path) -> dict:
    ref_names = sorted(p.name for p in reference_dir.glob("atmosphere-width-*.png"))
    cand_names = sorted(p.name for p in candidate_dir.glob("atmosphere-width-*.png"))
    if ref_names != cand_names or len(cand_names) != 68:
        raise ValueError("rendered frame-set drift")
    rows = {name: image_delta(reference_dir / name, candidate_dir / name) for name in cand_names}
    changed = [name for name, row in rows.items() if not row["byte_identical"]]
    return {
        "frame_count": len(rows),
        "changed_frame_count": len(changed),
        "max_changed_pixels": max(row["changed_pixels"] for row in rows.values()),
        "max_pixels_over_1_lsb": max(row["pixels_over_1_lsb"] for row in rows.values()),
        "max_channel_delta_lsb": max(row["max_channel_delta_lsb"] for row in rows.values()),
        "per_frame": rows,
    }


def delta_sets(candidate_rows: dict, reference_rows: dict) -> dict:
    if set(candidate_rows) != set(reference_rows):
        raise ValueError("runtime observation key drift")
    keys = ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "buffer_mem_bytes", "texture_mem_bytes")
    rows = []
    for key in sorted(candidate_rows):
        cand = candidate_rows[key]
        ref = reference_rows[key]
        rows.append({name: int(cand[name]) - int(ref[name]) for name in keys})
    return {name: sorted({row[name] for row in rows}) for name in keys}


def verify(active_root: Path, indexed_compact_root: Path, candidate_root: Path, donor_payload: Path, exact_head: str, output: Path) -> None:
    active = load_json(runtime_path(active_root))
    compact = load_json(runtime_path(indexed_compact_root))
    candidate = load_json(runtime_path(candidate_root))
    donor = load_json(donor_payload)

    if len(active.get("samples", [])) != 17 or len(compact.get("samples", [])) != 17 or len(candidate.get("samples", [])) != 17:
        raise ValueError("expected 17 samples in all runtime receipts")
    if donor.get("representation_id") != REPRESENTATION_ID or donor.get("schema") != "axm.building-planar-role-render-receiver-policy/v0.1":
        raise ValueError("Hard-Surface donor identity drift")
    if len(donor.get("vertices", [])) != 672 or len(donor.get("triangles", [])) != 336 or len(donor.get("rectangles", [])) != 168:
        raise ValueError("Hard-Surface donor count drift")
    if candidate.get("runtime_building_planar_role_receiver_result") != "CANDIDATE_EXACT_HARD_SURFACE_PLANAR_ROLE_RENDER_RECEIVER":
        raise ValueError("candidate runtime receipt marker missing")
    if candidate.get("runtime_building_planar_role_receiver_hard_surface_head") != HARD_SURFACE_HEAD:
        raise ValueError("candidate Hard-Surface head drift")
    if candidate.get("runtime_building_planar_role_receiver_representation_id") != REPRESENTATION_ID:
        raise ValueError("candidate representation identity drift")

    receipts = []
    for sample in candidate["samples"]:
        building = find_building(sample)
        receipt = building.get("runtime_building_planar_role_receiver", {})
        if receipt.get("schema") != OBS_SCHEMA:
            raise ValueError("candidate Building runtime receipt missing/schema drift")
        if receipt.get("building_hard_surface_head") != HARD_SURFACE_HEAD or receipt.get("source_payload_sha256") != PAYLOAD_SHA256:
            raise ValueError("candidate Building donor identity drift")
        if receipt.get("representation_id") != REPRESENTATION_ID:
            raise ValueError("candidate Building representation drift")
        storage = receipt.get("map_render_storage", {})
        if storage.get("surface_count") != 5 or storage.get("total_vertices") != 1008 or storage.get("total_indices") != 0 or storage.get("total_primitives") != 336:
            raise ValueError(f"unexpected Map render storage: {storage}")
        receipts.append(receipt)
    first = receipts[0]
    if any(row.get("map_render_storage") != first.get("map_render_storage") for row in receipts[1:]):
        raise ValueError("candidate Building render storage changed across states")

    active_rows = runtime_rows(active)
    compact_rows = runtime_rows(compact)
    candidate_rows = runtime_rows(candidate)
    if len(candidate_rows) != 68:
        raise ValueError(f"expected 68 runtime observations, got {len(candidate_rows)}")
    vs_active = delta_sets(candidate_rows, active_rows)
    vs_compact = delta_sets(candidate_rows, compact_rows)

    for field in ("draw_calls_in_frame", "objects_in_frame", "texture_mem_bytes"):
        if vs_active[field] != [0]:
            raise ValueError(f"planar candidate changed active non-geometry counter {field}: {vs_active[field]}")
    if max(vs_compact["buffer_mem_bytes"]) >= 0 or max(vs_compact["primitives_in_frame"]) >= 0:
        raise ValueError(f"planar candidate did not reduce compact-v2 proof-host geometry cost: {vs_compact}")

    candidate_dir = rendered_dir(candidate_root)
    active_visual = summarize_visual(rendered_dir(active_root), candidate_dir)
    compact_visual = summarize_visual(rendered_dir(indexed_compact_root), candidate_dir)

    modeled_active = 276 * 3 * 24
    modeled_candidate = 336 * 3 * 24
    modeled_indexed_compact = 53328

    report = {
        "schema": SCHEMA,
        "state": "PASS_BUILDING_PLANAR_ROLE_CURRENT_WORLD_RUNTIME_COST_CHARACTERIZED__HOLD_ART_QA_VISUAL_ADOPTION",
        "exact_runtime_head": exact_head,
        "environment_parent_head": ENVIRONMENT_HEAD,
        "hard_surface_head": HARD_SURFACE_HEAD,
        "representation_id": REPRESENTATION_ID,
        "source_payload_sha256": PAYLOAD_SHA256,
        "comparison_artifacts": {
            "active_segmented": {"run": ACTIVE_RUN, "artifact": ACTIVE_ARTIFACT},
            "indexed_compact_v2": {"run": INDEXED_COMPACT_RUN, "artifact": INDEXED_COMPACT_ARTIFACT},
        },
        "building_representation": {
            "semantic_source": "header-segmented-23",
            "candidate_rectangles": 168,
            "candidate_source_vertices": 672,
            "candidate_triangles": 336,
            "map_render_storage": first["map_render_storage"],
            "modeled_payload_scope": "Map triangle-corner FLOAT32 position3 + generated normal3; candidate is intentionally unindexed",
            "modeled_active_bytes": modeled_active,
            "modeled_candidate_bytes": modeled_candidate,
            "modeled_delta_vs_active_bytes": modeled_candidate - modeled_active,
            "modeled_indexed_compact_v2_bytes": modeled_indexed_compact,
            "modeled_delta_vs_indexed_compact_v2_bytes": modeled_candidate - modeled_indexed_compact,
        },
        "proof_host": {
            "observation_count": len(candidate_rows),
            "candidate_vs_active_delta_sets": vs_active,
            "candidate_vs_indexed_compact_v2_delta_sets": vs_compact,
        },
        "visuals": {
            "candidate_vs_active": {k: v for k, v in active_visual.items() if k != "per_frame"},
            "candidate_vs_indexed_compact_v2": {k: v for k, v in compact_visual.items() if k != "per_frame"},
            "tradeoff": "MEASURED_CURRENT_WORLD_A_B__ART_AND_VISUAL_QA_REVIEW_REQUIRED__RUNTIME_DOES_NOT_SELECT_LOOK",
        },
        "decision": "PLANAR_ROLE_RENDER_COVER_IS_A_DISTINCT_LOW_PRIMITIVE_BUILDING_RECEIVER__KEEP_RUNTIME_COST_AND_VISUAL_PREFERENCE_AS_SEPARATE_GATES",
        "truth_boundary": "This characterizes only the exact render-only Hard-Surface candidate through the pinned current-world Godot proof path. It does not grant Environment adoption, transport/collision/manufacturing semantics, target-device CPU/GPU/FPS/VRAM acceptance, Art preference, CANON or production readiness.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--active-root", type=Path, required=True)
    p.add_argument("--indexed-compact-root", type=Path, required=True)
    p.add_argument("--candidate-root", type=Path, required=True)
    p.add_argument("--donor-payload", type=Path, required=True)
    p.add_argument("--exact-head", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    verify(args.active_root, args.indexed_compact_root, args.candidate_root, args.donor_payload, args.exact_head, args.output)


if __name__ == "__main__":
    main()
