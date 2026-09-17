#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from PIL import Image, ImageChops

SCHEMA = "axm.runtime-building-planar-role-direct-indexed-import-budget/v0.2"
ENVIRONMENT_HEAD = "038925282240441c475651bdc3737d1749c31d06"
REPRESENTATION_ID = "boundary-only-planar-role-rectangle-render-001"
DIRECT_SCHEMA = "axm.runtime-building-planar-role-direct-indexed-receiver/v0.2"
BUILDING_ID = "source:building:service-pavilion-001"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_building(sample: dict) -> dict:
    rows = [r for r in sample.get("static_source_meshes", []) if r.get("asset_id") == BUILDING_ID]
    if len(rows) != 1:
        raise ValueError(f"expected one Building row, got {len(rows)}")
    return rows[0]


def runtime_rows(runtime: dict) -> dict[tuple[int, str, str], dict]:
    rows: dict[tuple[int, str, str], dict] = {}
    for sample in runtime.get("samples", []):
        idx = int(sample["index"])
        for camera, modes in sample.get("contexts", {}).items():
            for mode, payload in modes.items():
                rows[(idx, camera, mode)] = payload["runtime"]
    return rows


def delta_sets(candidate: dict, control: dict) -> dict[str, list[int]]:
    if set(candidate) != set(control):
        raise ValueError("runtime observation key drift")
    fields = ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "buffer_mem_bytes", "texture_mem_bytes")
    out = {field: set() for field in fields}
    for key in sorted(candidate):
        for field in fields:
            out[field].add(int(candidate[key][field]) - int(control[key][field]))
    return {field: sorted(values) for field, values in out.items()}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def image_delta(a_path: Path, b_path: Path) -> dict:
    with Image.open(a_path).convert("RGB") as a, Image.open(b_path).convert("RGB") as b:
        if a.size != b.size:
            raise ValueError("image size drift")
        diff = ImageChops.difference(a, b)
        bbox = diff.getbbox()
        changed = 0
        over_one = 0
        max_channel = 0
        if bbox is not None:
            for px in diff.getdata():
                m = max(px)
                if m:
                    changed += 1
                    max_channel = max(max_channel, m)
                if m > 1:
                    over_one += 1
        return {
            "byte_identical": bbox is None,
            "changed_pixels": changed,
            "pixels_over_1_lsb": over_one,
            "max_channel_delta_lsb": max_channel,
            "bbox": list(bbox) if bbox is not None else None,
            "control_sha256": sha256_file(a_path),
            "candidate_sha256": sha256_file(b_path),
        }


def percentile_nearest(values: list[int], fraction: float) -> int:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def verify(control_root: Path, candidate_root: Path, exact_head: str, output: Path) -> None:
    control = load(control_root / "runtime.json")
    candidate = load(candidate_root / "runtime.json")
    if len(control.get("samples", [])) != 17 or len(candidate.get("samples", [])) != 17:
        raise ValueError("expected exact 17-state current-world sequence")
    if control.get("environment_building_planar_role_representation_id") != REPRESENTATION_ID:
        raise ValueError("control representation identity drift")
    if candidate.get("environment_building_planar_role_representation_id") != REPRESENTATION_ID:
        raise ValueError("candidate representation identity drift")
    if candidate.get("runtime_building_direct_indexed_schema") != DIRECT_SCHEMA:
        raise ValueError("candidate direct-indexed top-level marker missing")

    control_usec: list[int] = []
    candidate_usec: list[int] = []
    for c_sample, d_sample in zip(control["samples"], candidate["samples"]):
        if int(c_sample["index"]) != int(d_sample["index"]):
            raise ValueError("sample index drift")
        c_row = find_building(c_sample)
        d_row = find_building(d_sample)
        if c_row.get("runtime_building_prepare_mode") != "POST_NORMAL_SURFACETOOL_INDEX_CONTROL":
            raise ValueError("control timing marker drift")
        direct = d_row.get("runtime_building_direct_indexed", {})
        if d_row.get("runtime_building_prepare_mode") != "DIRECT_INDEXED_POSITION_DOMAIN_THEN_GENERATE_NORMALS":
            raise ValueError("candidate timing marker drift")
        if direct.get("schema") != DIRECT_SCHEMA:
            raise ValueError("candidate direct receipt schema drift")
        if direct.get("surface_count") != 5 or direct.get("stored_vertices") != 312 or direct.get("indices") != 1008 or direct.get("triangles") != 336:
            raise ValueError(f"candidate final storage drift: {direct}")
        if direct.get("source_payload_vertices") != 672:
            raise ValueError("candidate source payload vertex identity drift")
        cu = int(c_row.get("runtime_building_prepare_usec", 0))
        du = int(d_row.get("runtime_building_prepare_usec", 0))
        if cu <= 0 or du <= 0:
            raise ValueError("missing positive preparation timing")
        control_usec.append(cu)
        candidate_usec.append(du)

    c_median = float(statistics.median(control_usec))
    d_median = float(statistics.median(candidate_usec))
    median_delta = d_median - c_median
    median_reduction_pct = (100.0 * (c_median - d_median) / c_median) if c_median else 0.0
    faster_samples = sum(1 for c, d in zip(control_usec, candidate_usec) if d < c)

    control_rows = runtime_rows(control)
    candidate_rows = runtime_rows(candidate)
    if len(control_rows) != 68 or len(candidate_rows) != 68:
        raise ValueError("expected 68 renderer observations per representation")
    counter_delta = delta_sets(candidate_rows, control_rows)
    for field in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "texture_mem_bytes"):
        if counter_delta[field] != [0]:
            raise ValueError(f"direct receiver changed {field}: {counter_delta[field]}")
    if max(counter_delta["buffer_mem_bytes"]) > 0:
        raise ValueError(f"direct receiver increased observed buffer memory: {counter_delta['buffer_mem_bytes']}")

    control_dir = control_root / "rendered"
    candidate_dir = candidate_root / "rendered"
    names = sorted(p.name for p in control_dir.glob("atmosphere-width-*.png"))
    if len(names) != 68 or names != sorted(p.name for p in candidate_dir.glob("atmosphere-width-*.png")):
        raise ValueError("retained frame-set drift")
    visuals = {name: image_delta(control_dir / name, candidate_dir / name) for name in names}
    changed = [name for name, row in visuals.items() if not row["byte_identical"]]
    max_pixels = max(row["changed_pixels"] for row in visuals.values())
    max_over_one = max(row["pixels_over_1_lsb"] for row in visuals.values())
    max_lsb = max(row["max_channel_delta_lsb"] for row in visuals.values())

    preparation_improved = d_median < c_median
    if preparation_improved:
        state = "PASS_BUILDING_INDEX_BEFORE_NORMAL_RECEIVER_REDUCES_PROOF_HOST_PREPARATION_COST__HOLD_ART_QA_AND_TARGET_DEVICE"
        decision = "INDEX_FINAL_POSITION_DOMAIN_BEFORE_NORMAL_GENERATION_IS_A_REAL_PROOF_HOST_PREPARATION_WIN__RENDERER_AND_VISUAL_GATES_REMAIN_SEPARATE"
    else:
        state = "HOLD_BUILDING_INDEX_BEFORE_NORMAL_RECEIVER_PREPARATION_WIN_NOT_REPRODUCED"
        decision = "KEEP_POST_NORMAL_INDEX_CONTROL__INDEX_BEFORE_NORMAL_DID_NOT_REDUCE_MEDIAN_PREPARATION_ON_THIS_HOST"

    tradeoff = (
        "NONE_OBSERVED__68_FRAMES_BYTE_IDENTICAL"
        if not changed
        else f"MEASURED_INDEX_BEFORE_NORMAL_RENDER_DELTA__CHANGED_FRAMES_{len(changed)}__MAX_PIXELS_{max_pixels}__MAX_OVER_1_LSB_{max_over_one}__MAX_LSB_{max_lsb}__ART_QA_REVIEW_REQUIRED"
    )

    report = {
        "schema": SCHEMA,
        "state": state,
        "decision": decision,
        "exact_runtime_head": exact_head,
        "environment_parent_head": ENVIRONMENT_HEAD,
        "representation_id": REPRESENTATION_ID,
        "preparation_timing": {
            "measurement_boundary": "per-state proof-host wall-clock microseconds around Building receiver construction only; excludes PNG readback and whole-scene render",
            "sample_count_per_representation": 17,
            "control_usec": control_usec,
            "candidate_usec": candidate_usec,
            "control_median_usec": c_median,
            "candidate_median_usec": d_median,
            "median_delta_usec": median_delta,
            "median_reduction_percent": round(median_reduction_pct, 6),
            "candidate_faster_sample_pairs": faster_samples,
            "control_p90_usec": percentile_nearest(control_usec, 0.90),
            "candidate_p90_usec": percentile_nearest(candidate_usec, 0.90),
        },
        "representation": {
            "surface_count": 5,
            "triangle_count": 336,
            "stored_vertices": 312,
            "indices": 1008,
            "source_payload_vertices": 672,
            "control_path": "build 1008 unindexed triangle-corner vertices -> generate normals -> create_from -> SurfaceTool.index -> commit",
            "candidate_path": "deduplicate exact per-material position domain to 312 vertices -> add 1008 indices -> same SurfaceTool.generate_normals -> commit",
        },
        "proof_host_renderer_delta_sets_candidate_minus_control": counter_delta,
        "visuals": {
            "frame_count": 68,
            "changed_frame_count": len(changed),
            "max_changed_pixels": max_pixels,
            "max_pixels_over_1_lsb": max_over_one,
            "max_channel_delta_lsb": max_lsb,
            "tradeoff": tradeoff,
        },
        "truth_boundary": (
            "This compares only two receiver-construction paths for the exact five-surface / 336-triangle planar-role Building on the pinned Godot proof host. "
            "The candidate does not alter Building semantic source authority, material roles/scalars, current-world composition or triangle membership. "
            "It creates the exact per-material unique-position index domain before the same Godot normal-generation step instead of after it. "
            "Preparation microseconds are proof-host construction timing, not frame time, FPS, GPU cost, target-device CPU acceptance or import/export transport acceptance. "
            "The candidate proves no UV/tangent/color/skin/morph/custom-channel safety."
        ),
        "four_root_gate": {
            "truth": "Preparation, renderer counters and visual deltas are reported separately; a faster constructor cannot silently become a visual or production PASS.",
            "agency_non_domination": "Runtime owns this receiver-cost experiment only; Environment, Art/QA, Hard Surface, Materials and Technical Art retain adoption authority.",
            "continuity": "The post-normal indexed receiver remains the rollback control and exact parent identity is retained.",
            "wisdom_before_speed": "Prefer index-before-normal construction only if the measured host benefits and downstream attribute/transport gates remain explicit."
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--exact-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify(args.control_root, args.candidate_root, args.exact_head, args.output)


if __name__ == "__main__":
    main()
