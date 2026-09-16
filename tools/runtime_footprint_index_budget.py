#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

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


def png_map(root: Path) -> dict[str, str]:
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.glob("atmosphere-width-*.png"))
    }


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

    control_pngs = png_map(control_root)
    candidate_pngs = png_map(candidate_root)
    if len(control_pngs) != 68 or set(control_pngs) != set(candidate_pngs):
        raise ValueError(f"expected exact 68 matched frames, got {len(control_pngs)} / {len(candidate_pngs)}")
    mismatches = [name for name in control_pngs if control_pngs[name] != candidate_pngs[name]]
    if mismatches:
        raise ValueError(f"indexed footprint candidate changed retained pixels: {mismatches[:5]}")

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
        "schema": "axm.runtime-footprint-index-budget-report/v0.1",
        "state": "PASS_FOOTPRINT_POST_NORMAL_INDEXED_PAYLOAD_REDUCTION",
        "decision": "SECOND_DOMAIN_POST_NORMAL_INDEXING_WIN__SUBMISSION_AND_PIXELS_STABLE",
        "exact_environment_parent": PARENT_HEAD,
        "asset_id": ASSET_ID,
        "control_mesh": cbefore,
        "candidate_mesh": iafter,
        "control_modeled_position_normal_index_bytes": control_logical,
        "candidate_modeled_position_normal_index_bytes": candidate_logical,
        "modeled_payload_bytes_saved": saved,
        "modeled_payload_reduction_fraction": saved / control_logical,
        "matched_frames": len(control_pngs),
        "byte_identical_frames": len(control_pngs),
        "runtime_counter_deltas": deltas,
        "visual_tradeoff": "NONE_OBSERVED_68_MATCHED_PNGS_BYTE_IDENTICAL",
        "reusable_learning": (
            "The same post-normal indexing mechanism that reduced an imported five-surface Object receiver also reduces a materially different Map-owned generated single-surface four-box cue without changing draw/object/primitive counts or retained pixels. This is second-domain evidence for capability placement review, not automatic UC promotion."
        ),
        "truth_boundary": (
            "PASS proves only exact proof-host payload reduction for the existing visible Map footprint cue after normals exist. The modeled byte figure is a logical position+normal+32-bit-index model; observed RenderingServer buffer deltas are reported separately. It does not establish target-device CPU/GPU/FPS/VRAM/heap improvement, arbitrary procedural-mesh safety, final Art Direction, gameplay, UC extraction, CANON or production readiness."
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
