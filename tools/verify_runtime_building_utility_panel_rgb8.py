#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image

EXPECTED_RUNTIME_STATE = "PASS_BUILDING_UTILITY_PANEL_OPAQUE_ALPHA_ELISION_RGB8__HOLD_ART_QA_TARGET_DEVICE_GENERIC_POLICY"
EXPECTED_ENV_STATE = "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_MATERIAL_BOUND_RECEIVER__A_B_REVIEW_ONLY__ADOPTION_HELD"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assert_owner_texture(path: Path, contract: dict[str, Any], mutate_alpha: bool = False) -> dict[str, Any]:
    owner = contract["owner_texture"]
    raw = path.read_bytes()
    if sha256_bytes(raw) != owner["serialized_png_sha256"]:
        raise RuntimeError("owner serialized PNG identity drift")
    image = Image.open(path).convert("RGBA")
    rgba = bytearray(image.tobytes())
    if sha256_bytes(bytes(rgba)) != owner["decoded_rgba8_sha256"]:
        raise RuntimeError("owner decoded RGBA8 identity drift")
    if mutate_alpha:
        rgba[3] = 254
    alpha = rgba[3::4]
    if not alpha or min(alpha) != 255 or max(alpha) != 255:
        raise RuntimeError("RGB8_ALPHA_PRECONDITION_REJECTED_NON_OPAQUE_TEXTURE")
    rgb = bytearray()
    for i in range(0, len(rgba), 4):
        rgb.extend(rgba[i : i + 3])
    if sha256_bytes(bytes(rgb)) != owner["decoded_rgb8_sha256"]:
        raise RuntimeError("owner decoded RGB8 identity drift")
    return {
        "alpha_sample_count": len(alpha),
        "alpha_min": min(alpha),
        "alpha_max": max(alpha),
        "rgba8_bytes": len(rgba),
        "rgb8_bytes": len(rgb),
    }


def runtime_entries(runtime: dict[str, Any]) -> dict[tuple[int, str, str], dict[str, Any]]:
    out: dict[tuple[int, str, str], dict[str, Any]] = {}
    samples = runtime.get("samples", [])
    if not isinstance(samples, list):
        raise RuntimeError("runtime samples missing")
    for sample in samples:
        index = int(sample["index"])
        contexts = sample.get("contexts", {})
        for context_name, context in contexts.items():
            for presentation in ("control", "candidate"):
                entry = context.get(presentation)
                if not isinstance(entry, dict):
                    raise RuntimeError(f"runtime entry missing: {index}/{context_name}/{presentation}")
                out[(index, str(context_name), presentation)] = entry
    return out


def compare_pixels(a_path: Path, b_path: Path) -> dict[str, int]:
    a = Image.open(a_path).convert("RGBA")
    b = Image.open(b_path).convert("RGBA")
    if a.size != b.size:
        raise RuntimeError(f"raster size drift: {a_path.name}")
    aa = a.tobytes()
    bb = b.tobytes()
    changed = 0
    over1 = 0
    maximum = 0
    for offset in range(0, len(aa), 4):
        delta = max(abs(aa[offset + c] - bb[offset + c]) for c in range(4))
        changed += int(delta > 0)
        over1 += int(delta > 1)
        maximum = max(maximum, delta)
    return {"changed_pixels": changed, "pixels_over_1_lsb": over1, "max_channel_delta_lsb": maximum}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--baseline-runtime", type=Path, required=True)
    parser.add_argument("--candidate-runtime", type=Path, required=True)
    parser.add_argument("--baseline-rendered", type=Path, required=True)
    parser.add_argument("--candidate-rendered", type=Path, required=True)
    parser.add_argument("--owner-png", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mutate-alpha", action="store_true")
    args = parser.parse_args()

    contract = load_json(args.contract)
    if contract.get("schema") != "axm.runtime-building-utility-panel-rgb8-alpha-elision/v0.1":
        raise RuntimeError("runtime RGB8 contract schema drift")

    owner_receipt = assert_owner_texture(args.owner_png, contract, mutate_alpha=args.mutate_alpha)
    if args.mutate_alpha:
        raise RuntimeError("negative control unexpectedly accepted non-opaque alpha")

    baseline = load_json(args.baseline_runtime)
    candidate = load_json(args.candidate_runtime)
    if baseline.get("environment_building_utility_panel_material_current_world_state") != EXPECTED_ENV_STATE:
        raise RuntimeError("baseline Environment material state drift")
    if candidate.get("runtime_building_utility_panel_rgb8_state") != EXPECTED_RUNTIME_STATE:
        raise RuntimeError("candidate Runtime RGB8 state drift")
    if candidate.get("runtime_building_utility_panel_rgb8_environment_parent_head") != contract["environment_parent"]["head"]:
        raise RuntimeError("candidate Environment parent head drift")

    texture_receipt = candidate.get("runtime_building_utility_panel_rgb8_texture_receipt", {})
    if texture_receipt.get("decoded_rgb8_sha256") != contract["owner_texture"]["decoded_rgb8_sha256"]:
        raise RuntimeError("candidate RGB8 receipt identity drift")
    if int(texture_receipt.get("alpha_min", -1)) != 255 or int(texture_receipt.get("alpha_max", -1)) != 255:
        raise RuntimeError("candidate Runtime did not prove opaque alpha")

    before_entries = runtime_entries(baseline)
    after_entries = runtime_entries(candidate)
    if set(before_entries) != set(after_entries) or len(before_entries) != int(contract["acceptance"]["rendered_frame_pairs"]):
        raise RuntimeError("runtime observation key/count drift")

    texture_savings: list[int] = []
    buffer_deltas: list[int] = []
    for key in sorted(before_entries):
        before = before_entries[key]["runtime"]
        after = after_entries[key]["runtime"]
        for metric in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame"):
            if int(before[metric]) != int(after[metric]):
                raise RuntimeError(f"runtime structural metric drift {metric}: {key}")
        texture_savings.append(int(before["texture_mem_bytes"]) - int(after["texture_mem_bytes"]))
        buffer_deltas.append(int(after["buffer_mem_bytes"]) - int(before["buffer_mem_bytes"]))
    if min(texture_savings) <= 0:
        raise RuntimeError("RGB8 candidate did not reduce texture memory for every retained observation")

    baseline_files = {p.name: p for p in args.baseline_rendered.glob("*.png")}
    candidate_files = {p.name: p for p in args.candidate_rendered.glob("*.png")}
    expected_pairs = int(contract["acceptance"]["rendered_frame_pairs"])
    if set(baseline_files) != set(candidate_files) or len(baseline_files) != expected_pairs:
        raise RuntimeError("rendered A/B file set drift")

    total_changed = 0
    total_over1 = 0
    max_delta = 0
    per_frame: list[dict[str, Any]] = []
    for name in sorted(baseline_files):
        delta = compare_pixels(baseline_files[name], candidate_files[name])
        total_changed += delta["changed_pixels"]
        total_over1 += delta["pixels_over_1_lsb"]
        max_delta = max(max_delta, delta["max_channel_delta_lsb"])
        per_frame.append({"frame": name, **delta})
    if total_over1 > int(contract["acceptance"]["max_pixels_over_1_lsb"]):
        raise RuntimeError("RGB8 candidate exceeded retained >1-LSB pixel boundary")
    if max_delta > int(contract["acceptance"]["max_channel_delta_lsb"]):
        raise RuntimeError("RGB8 candidate exceeded retained maximum channel delta")

    result = {
        "schema": "axm.runtime-building-utility-panel-rgb8-evidence/v0.1",
        "state": "PASS_BUILDING_UTILITY_PANEL_RGB8_TEXTURE_MEMORY_REDUCTION__RASTER_EQUIVALENT_RETAINED_68__HOLD_ART_QA_TARGET_DEVICE_GENERIC_POLICY",
        "environment_parent_head": contract["environment_parent"]["head"],
        "owner_texture": owner_receipt,
        "observations": len(before_entries),
        "texture_memory_bytes_saved_values": sorted(set(texture_savings)),
        "texture_memory_bytes_saved_min": min(texture_savings),
        "texture_memory_bytes_saved_max": max(texture_savings),
        "buffer_memory_delta_values": sorted(set(buffer_deltas)),
        "rendered_pairs": expected_pairs,
        "total_changed_pixels": total_changed,
        "total_pixels_over_1_lsb": total_over1,
        "max_channel_delta_lsb": max_delta,
        "byte_identical_pair_count": sum(1 for row in per_frame if row["changed_pixels"] == 0),
        "frames": per_frame,
        "visual_tradeoff": "NONE_OBSERVED_ABOVE_1_LSB_ACROSS_EXACT_68_RETAINED_CURRENT_WORLD_PAIRS__ART_QA_AND_TARGET_DEVICE_STILL_HELD",
        "representation_tradeoff": "ALPHA_CHANNEL_IS_DROPPED_ONLY_FOR_THIS EXACT OWNER TEXTURE AFTER ALL 262144 ALPHA SAMPLES PROVE 255; ANY FUTURE NON_OPAQUE OWNER TEXTURE MUST REJECT THIS REPRESENTATION",
        "target_device_acceptance": False,
        "art_qa_acceptance": False,
        "generic_rgb8_policy": False,
        "environment_adoption": False,
        "canon": False,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["state"])
    print(json.dumps({k: result[k] for k in (
        "observations",
        "texture_memory_bytes_saved_values",
        "buffer_memory_delta_values",
        "rendered_pairs",
        "total_changed_pixels",
        "total_pixels_over_1_lsb",
        "max_channel_delta_lsb",
        "byte_identical_pair_count",
        "visual_tradeoff",
    )}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
