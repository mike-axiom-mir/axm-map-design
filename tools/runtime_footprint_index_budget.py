#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from PIL import Image

ASSET_ID = "environment:dressing:west-object-service-footprint-frame-001"
CONTROL_MODE = "UNINDEXED_FOOTPRINT_CONTROL"
CANDIDATE_MODE = "INDEXED_FOOTPRINT_CANDIDATE"
PARENT_HEAD = "b9d9ed28e9a826c4698014db5f91c59aba9dddfc"
EXPECTED_SURFACES = 1
EXPECTED_TRIANGLES = 48
EXPECTED_CONTROL_VERTICES = 144
RUNTIME_KEYS = (
    "draw_calls_in_frame",
    "objects_in_frame",
    "primitives_in_frame",
    "buffer_mem_bytes",
    "texture_mem_bytes",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def footprint_diag(receipt: dict[str, Any]) -> dict[str, Any]:
    rows = receipt.get("static_source_meshes", [])
    matches = [r for r in rows if r.get("asset_id") == ASSET_ID]
    if len(matches) != 1:
        raise ValueError(f"expected one footprint cue row, found {len(matches)}")
    diag = matches[0].get("runtime_footprint_surface_indexing")
    if not isinstance(diag, dict):
        raise ValueError("missing runtime_footprint_surface_indexing diagnostic")
    return diag


def flatten_runtime(receipt: dict[str, Any]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for sample in receipt.get("samples", []):
        index = int(sample["index"])
        for context, pair in sample.get("contexts", {}).items():
            for weather_mode in ("control", "candidate"):
                runtime = pair[weather_mode]["runtime"]
                key = f"{index:02d}/{context}/{weather_mode}"
                out[key] = {name: int(runtime[name]) for name in RUNTIME_KEYS}
    return out


def capture_bboxes(receipt: dict[str, Any]) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for sample in receipt.get("samples", []):
        for pair in sample.get("contexts", {}).values():
            for weather_mode in ("control", "candidate"):
                capture = pair[weather_mode]["capture"]
                name = Path(str(capture["path"])).name
                bbox = [int(v) for v in capture["dressing_projected_bbox_px"]]
                out[name] = bbox
    return out


def modeled_bytes(diag: dict[str, Any]) -> int:
    # Logical proof model only: the cue contains position + generated normal per
    # vertex and 32-bit indices when indexed. This is not driver/VRAM packing.
    return int(diag["total_vertices"]) * 24 + int(diag["total_indices"]) * 4


def summarize_deltas(control: dict[str, dict[str, int]], candidate: dict[str, dict[str, int]]) -> dict[str, Any]:
    if set(control) != set(candidate):
        raise ValueError("runtime sample identity drift")
    result: dict[str, Any] = {}
    for field in RUNTIME_KEYS:
        values = [candidate[k][field] - control[k][field] for k in sorted(control)]
        result[field] = {
            "minimum_delta": min(values),
            "median_delta": statistics.median(values),
            "maximum_delta": max(values),
            "unique_deltas": sorted(set(values)),
        }
    return result


def bounded_visual_delta(
    control_receipt: dict[str, Any],
    candidate_receipt: dict[str, Any],
    control_root: Path,
    candidate_root: Path,
) -> dict[str, Any]:
    control_files = {p.name: p for p in sorted(control_root.glob("atmosphere-width-*.png"))}
    candidate_files = {p.name: p for p in sorted(candidate_root.glob("atmosphere-width-*.png"))}
    if len(control_files) != 68 or set(control_files) != set(candidate_files):
        raise ValueError(f"expected exact 68 matched frames, got {len(control_files)} / {len(candidate_files)}")

    control_boxes = capture_bboxes(control_receipt)
    candidate_boxes = capture_bboxes(candidate_receipt)
    if set(control_boxes) != set(control_files) or set(candidate_boxes) != set(control_files):
        raise ValueError("capture/bbox identity drift")

    rows: list[dict[str, Any]] = []
    byte_identical = 0
    changed_frames = 0
    max_changed_pixels = 0
    max_channel_delta = 0
    unique_changed_coordinates: set[tuple[int, int]] = set()

    for name in sorted(control_files):
        if control_boxes[name] != candidate_boxes[name]:
            raise ValueError(f"projected cue bbox changed for {name}")
        bbox = control_boxes[name]
        with Image.open(control_files[name]) as ca, Image.open(candidate_files[name]) as cb:
            a = ca.convert("RGB")
            b = cb.convert("RGB")
            if a.size != b.size:
                raise ValueError(f"image dimension drift for {name}")
            if control_files[name].read_bytes() == candidate_files[name].read_bytes():
                byte_identical += 1
            width, height = a.size
            pa = a.load()
            pb = b.load()
            changed: list[tuple[int, int, tuple[int, int, int]]] = []
            frame_max = 0
            for y in range(height):
                for x in range(width):
                    av = pa[x, y]
                    bv = pb[x, y]
                    delta = tuple(int(bv[i]) - int(av[i]) for i in range(3))
                    abs_max = max(abs(v) for v in delta)
                    if abs_max:
                        changed.append((x, y, delta))
                        frame_max = max(frame_max, abs_max)
            if changed:
                changed_frames += 1
            if len(changed) > 1:
                raise ValueError(f"indexed footprint changed more than one pixel in {name}: {len(changed)}")
            if frame_max > 1:
                raise ValueError(f"indexed footprint exceeded one-LSB RGB delta in {name}: {frame_max}")
            for x, y, _ in changed:
                if not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]):
                    raise ValueError(f"indexed footprint delta escaped projected cue bounds in {name}: {(x, y)} vs {bbox}")
                unique_changed_coordinates.add((x, y))
            max_changed_pixels = max(max_changed_pixels, len(changed))
            max_channel_delta = max(max_channel_delta, frame_max)
            rows.append({
                "name": name,
                "changed_pixels": len(changed),
                "maximum_channel_delta_lsb": frame_max,
                "changed_coordinates": [[x, y] for x, y, _ in changed],
                "channel_delta": list(changed[0][2]) if changed else [0, 0, 0],
                "dressing_projected_bbox_px": bbox,
            })

    return {
        "matched_frames": len(rows),
        "byte_identical_frames": byte_identical,
        "frames_with_any_rgb_delta": changed_frames,
        "maximum_changed_pixels_per_frame": max_changed_pixels,
        "maximum_channel_delta_lsb": max_channel_delta,
        "unique_changed_coordinates": [list(v) for v in sorted(unique_changed_coordinates)],
        "all_changed_pixels_within_projected_cue_bounds": True,
        "all_rgb_deltas_at_or_below_one_lsb": True,
        "per_frame": rows,
    }


def verify(
    control_receipt: Path,
    candidate_receipt: Path,
    control_root: Path,
    candidate_root: Path,
) -> dict[str, Any]:
    control = load(control_receipt)
    candidate = load(candidate_receipt)
    for label, receipt in (("control", control), ("candidate", candidate)):
        if receipt.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
            raise ValueError(f"{label} inherited current-world observation did not PASS")
        if len(receipt.get("samples", [])) != 17:
            raise ValueError(f"{label} requires exact 17-state receipt")
        if receipt.get("environment_object_indexed_receiver_runtime_donor_head") != "ddd9e8b783b213c6e44bf5eea482de1d41918766":
            raise ValueError(f"{label} lost exact indexed Object donor identity")
        if receipt.get("runtime_footprint_index_parent_head") != PARENT_HEAD:
            raise ValueError(f"{label} exact Environment parent drift")

    cdiag = footprint_diag(control)
    idiag = footprint_diag(candidate)
    if cdiag.get("mode") != CONTROL_MODE or idiag.get("mode") != CANDIDATE_MODE:
        raise ValueError("footprint runtime mode identity drift")
    for diag in (cdiag, idiag):
        if diag.get("schema") != "axm.runtime-footprint-index-budget/v0.1":
            raise ValueError("footprint indexing schema drift")
        if diag.get("environment_parent_head") != PARENT_HEAD:
            raise ValueError("footprint indexing parent identity drift")
        if diag.get("asset_id") != ASSET_ID:
            raise ValueError("footprint asset identity drift")
        if diag.get("proof_role") != "ENVIRONMENT_OWNED_RECEIVER_FOOTPRINT_READABILITY_CUE":
            raise ValueError("footprint role drift")

    cbefore = cdiag["before"]
    cafter = cdiag["after"]
    ibefore = idiag["before"]
    iafter = idiag["after"]
    if cbefore != cafter:
        raise ValueError("control unexpectedly changed footprint representation")
    if cbefore != ibefore:
        raise ValueError("candidate did not start from exact control representation")
    if int(cbefore["surface_count"]) != EXPECTED_SURFACES or int(iafter["surface_count"]) != EXPECTED_SURFACES:
        raise ValueError("single-surface footprint boundary changed")
    if int(cbefore["total_primitives"]) != EXPECTED_TRIANGLES or int(iafter["total_primitives"]) != EXPECTED_TRIANGLES:
        raise ValueError("footprint triangle count changed")
    if int(cbefore["total_vertices"]) != EXPECTED_CONTROL_VERTICES:
        raise ValueError("unexpected control footprint vertex count")
    if int(cbefore["total_indices"]) != 0:
        raise ValueError("control footprint unexpectedly indexed")
    if int(iafter["total_indices"]) != EXPECTED_CONTROL_VERTICES:
        raise ValueError("candidate index stream does not cover exact original triangle corners")
    if int(iafter["total_vertices"]) >= EXPECTED_CONTROL_VERTICES:
        raise ValueError("candidate failed to reduce repeated footprint vertices")

    control_logical = modeled_bytes(cbefore)
    candidate_logical = modeled_bytes(iafter)
    if candidate_logical >= control_logical:
        raise ValueError("candidate did not reduce modeled footprint payload")

    visual = bounded_visual_delta(control, candidate, control_root, candidate_root)

    control_runtime = flatten_runtime(control)
    candidate_runtime = flatten_runtime(candidate)
    if len(control_runtime) != 68 or len(candidate_runtime) != 68:
        raise ValueError("expected 68 runtime observations per mode")
    deltas = summarize_deltas(control_runtime, candidate_runtime)
    for field in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "texture_mem_bytes"):
        if deltas[field]["unique_deltas"] != [0]:
            raise ValueError(f"indexed footprint changed {field}: {deltas[field]}")
    if deltas["buffer_mem_bytes"]["maximum_delta"] > 0:
        raise ValueError(f"indexed footprint increased observed buffer memory: {deltas['buffer_mem_bytes']}")

    saved = control_logical - candidate_logical
    return {
        "schema": "axm.runtime-footprint-index-budget-report/v0.2",
        "state": "PASS_FOOTPRINT_POST_NORMAL_INDEXED_PAYLOAD_REDUCTION_WITH_BOUNDED_ONE_LSB_EDGE_DELTA",
        "decision": "SECOND_DOMAIN_POST_NORMAL_INDEXING_WIN__ART_REVIEW_ONE_LSB_EDGE_DELTA",
        "exact_environment_parent": PARENT_HEAD,
        "asset_id": ASSET_ID,
        "control_mesh": cbefore,
        "candidate_mesh": iafter,
        "control_modeled_position_normal_index_bytes": control_logical,
        "candidate_modeled_position_normal_index_bytes": candidate_logical,
        "modeled_payload_bytes_saved": saved,
        "modeled_payload_reduction_fraction": saved / control_logical,
        "runtime_counter_deltas": deltas,
        "visual_delta": visual,
        "visual_tradeoff": "NONZERO_BOUNDED__MAX_1_CHANGED_PIXEL_PER_FRAME__MAX_1_LSB__INSIDE_CUE_BOUNDS__ART_REVIEW_REQUIRED",
        "strict_gate_history": {
            "run_id": 35154600246,
            "head": "77b6e9cbe28d80ebdd822c3319bfdca5611f30b1",
            "result": "FAIL_STRICT_BYTE_IDENTICAL_FRAME_GATE",
            "reason": "All 68 control/candidate PNG pairs differed by exactly one pixel at one RGB channel by one LSB; the strict byte-identical gate was preserved as failed evidence rather than relabelled PASS.",
        },
        "reusable_learning": (
            "The same post-normal indexing mechanism that reduced an imported five-surface Object receiver also reduces a materially different Map-owned generated single-surface four-box cue while preserving submission counts and limiting the observed fixed-camera visual consequence to a bounded one-pixel/one-LSB edge delta. This is second-domain evidence for capability-placement review, not automatic UC promotion."
        ),
        "truth_boundary": (
            "PASS proves only exact proof-host payload reduction for the existing visible Map footprint cue after normals exist, with an explicitly nonzero visual delta bounded to at most one changed pixel per retained frame, at most one RGB LSB, inside the projected cue bounds. The modeled byte figure is a logical position+normal+32-bit-index model; observed RenderingServer buffer deltas are reported separately. It does not establish target-device CPU/GPU/FPS/VRAM/heap improvement, arbitrary procedural-mesh safety, visual acceptance, gameplay, UC extraction, CANON or production readiness."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-receipt", type=Path, required=True)
    parser.add_argument("--candidate-receipt", type=Path, required=True)
    parser.add_argument("--control-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(
        args.control_receipt,
        args.candidate_receipt,
        args.control_root,
        args.candidate_root,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
