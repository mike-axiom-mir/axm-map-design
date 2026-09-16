#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
CONTROL_MODE = "UNINDEXED_CONTROL"
CANDIDATE_MODE = "INDEXED_CANDIDATE"
EXPECTED_SURFACES = 5
EXPECTED_TRIANGLES = 812
EXPECTED_MATERIALS = [
    "shell_coating",
    "service_dark",
    "hardware_steel",
    "rubber_guard",
    "interface_orange",
]
RUNTIME_KEYS = (
    "draw_calls_in_frame",
    "objects_in_frame",
    "primitives_in_frame",
    "buffer_mem_bytes",
    "texture_mem_bytes",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def object_index_diag(receipt: dict[str, Any]) -> dict[str, Any]:
    rows = receipt.get("static_source_meshes", [])
    matches = [r for r in rows if r.get("asset_id") == OBJECT_ASSET_ID]
    if len(matches) != 1:
        raise ValueError(f"expected one Object static source, found {len(matches)}")
    diag = matches[0].get("runtime_surface_indexing")
    if not isinstance(diag, dict):
        raise ValueError("missing runtime_surface_indexing diagnostic")
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
    files = sorted(root.glob("atmosphere-width-*.png"))
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in files
    }


def modeled_bytes(diag: dict[str, Any]) -> int:
    # Logical payload model only: this proof generates position + normal for every
    # vertex and 32-bit indices when indexed. It is not a claim about driver/VRAM
    # allocation or Godot's backend packing/alignment.
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


def verify(control_receipt: Path, candidate_receipt: Path, control_root: Path, candidate_root: Path) -> dict[str, Any]:
    control = load(control_receipt)
    candidate = load(candidate_receipt)
    for label, receipt in (("control", control), ("candidate", candidate)):
        if receipt.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
            raise ValueError(f"{label} inherited current-world observation did not PASS")
        if receipt.get("receiving_head") != "6575cc38db9f0f62b14a82b352d8582edf89856d":
            raise ValueError(f"{label} exact Environment parent drift")
        if len(receipt.get("samples", [])) != 17:
            raise ValueError(f"{label} requires exact 17-state receipt")

    cdiag = object_index_diag(control)
    idiag = object_index_diag(candidate)
    if cdiag.get("mode") != CONTROL_MODE or idiag.get("mode") != CANDIDATE_MODE:
        raise ValueError("runtime mode identity drift")
    for diag in (cdiag, idiag):
        if diag.get("material_ids") != EXPECTED_MATERIALS:
            raise ValueError("Object material identity/order drift")
        if diag.get("source_object_head") != "d3fa10a270faae7925811f44f03381fe5c5d0215":
            raise ValueError("Object source head drift")
        if diag.get("materials_head") != "c85517446a769e0d5f880fc0e9e32f47124f7b5e":
            raise ValueError("Object Materials head drift")

    cbefore = cdiag["before"]
    cafter = cdiag["after"]
    ibefore = idiag["before"]
    iafter = idiag["after"]
    if cbefore != cafter:
        raise ValueError("control unexpectedly changed mesh representation")
    if cbefore != ibefore:
        raise ValueError("candidate did not start from exact control representation")
    if int(cbefore["surface_count"]) != EXPECTED_SURFACES or int(iafter["surface_count"]) != EXPECTED_SURFACES:
        raise ValueError("five-surface material boundary changed")
    if int(cbefore["total_primitives"]) != EXPECTED_TRIANGLES or int(iafter["total_primitives"]) != EXPECTED_TRIANGLES:
        raise ValueError("triangle count changed")
    if int(cbefore["total_indices"]) != 0:
        raise ValueError("control unexpectedly indexed")
    if int(iafter["total_indices"]) != int(cbefore["total_vertices"]):
        raise ValueError("candidate index stream does not cover exact original triangle corners")
    if int(iafter["total_vertices"]) >= int(cbefore["total_vertices"]):
        raise ValueError("candidate failed to reduce repeated vertex payload")
    if any(int(s["index_count"]) <= 0 for s in iafter["surfaces"]):
        raise ValueError("candidate left an Object material surface unindexed")

    control_logical = modeled_bytes(cbefore)
    candidate_logical = modeled_bytes(iafter)
    if candidate_logical >= control_logical:
        raise ValueError("candidate did not reduce modeled position/normal/index payload")

    control_pngs = png_map(control_root)
    candidate_pngs = png_map(candidate_root)
    if len(control_pngs) != 68 or set(control_pngs) != set(candidate_pngs):
        raise ValueError(f"expected exact 68 matched retained frames, got {len(control_pngs)} / {len(candidate_pngs)}")
    mismatches = [name for name in control_pngs if control_pngs[name] != candidate_pngs[name]]
    if mismatches:
        raise ValueError(f"indexed candidate changed retained pixels: {mismatches[:5]}")

    control_runtime = flatten_runtime(control)
    candidate_runtime = flatten_runtime(candidate)
    if len(control_runtime) != 68 or len(candidate_runtime) != 68:
        raise ValueError("expected 68 exact runtime observations per mode")
    deltas = summarize_deltas(control_runtime, candidate_runtime)
    for field in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame"):
        if deltas[field]["unique_deltas"] != [0]:
            raise ValueError(f"indexed representation changed {field}: {deltas[field]}")

    saved = control_logical - candidate_logical
    return {
        "schema": "axm.runtime-object-material-index-budget-report/v0.1",
        "state": "PASS_OBJECT_MATERIAL_INDEXED_SURFACE_PAYLOAD_REDUCTION",
        "decision": "INDEXED_SURFACE_VERTEX_PAYLOAD_WIN__DRAW_OBJECT_PRIMITIVE_COUNTS_STABLE",
        "exact_environment_parent": "6575cc38db9f0f62b14a82b352d8582edf89856d",
        "object_source_head": cdiag["source_object_head"],
        "object_materials_head": cdiag["materials_head"],
        "material_ids": EXPECTED_MATERIALS,
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
        "truth_boundary": (
            "PASS proves only that SurfaceTool.index() can deduplicate exact repeated position+normal vertices inside the already-proven five-surface Object receiver while retaining five material surfaces, 812 triangles, stable draw/object/primitive counters and byte-identical retained proof-host frames. The modeled byte figure is a logical position+normal+32-bit-index payload model, not driver allocation, VRAM, heap, CPU/GPU frame time, target-device performance, gameplay, final Art Direction, CANON or production readiness."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--control-receipt", type=Path, required=True)
    p.add_argument("--candidate-receipt", type=Path, required=True)
    p.add_argument("--control-root", type=Path, required=True)
    p.add_argument("--candidate-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = verify(args.control_receipt, args.candidate_receipt, args.control_root, args.candidate_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
