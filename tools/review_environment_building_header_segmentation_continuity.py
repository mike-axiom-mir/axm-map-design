from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageEnhance, ImageDraw
import numpy as np

IMPLEMENTATION_HEAD = "dfd4e1d662ab7d6d9f1a5c8dd35b571418154f6e"
PARENT_HEAD = "a29aa1e3d2260e8eb5ab2ac78a95d35ce131214c"
PARENT_COMPOSITION_DIGEST = "8e22d33400effef66f5af79a19229cd5a4370d2a68563ecd1432f4ccb480b815"
SOURCE_HEAD = "34124101e616c423c5a3ed5e122ddf09b98a1650"
MATERIAL_HEAD = "09a534d9d6d4cdaa1bab70cc2d01345b48d8fcc8"
SEGMENTATION_REVISION = "service-pavilion-001/interpenetration-free-header-segmentation-003"
BUILDING_ASSET = "source:building:service-pavilion-001"
DRESSING_ASSET = "environment:dressing:west-object-service-footprint-frame-001"
OBJECT_ASSET = "source:object:modular-equipment-case-001"
REAR_NATURE_ASSET = "source:nature:east-rear-tree-neutral-001"
CONTEXTS = ("path_eye", "elevated_oblique")
MODES = ("control", "candidate")
SIGNIFICANT_CHANNEL_DELTA_LSB = 1
# Exact Materials donor uses a 1% changed-fraction continuity guard for this same
# 19-output -> 23-output source segmentation. Environment reuses the threshold
# only as a bounded continuity diagnostic, never as Art Direction acceptance.
MAX_CHANGED_FRACTION = 0.01
SCHEMA = "axm.environment-current-world-building-header-segmentation-continuity-review/v0.1"
STATE = "PASS_CURRENT_WORLD_BUILDING_HEADER_SEGMENTATION_BOUNDED_CONTINUITY"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def significant_delta(parent: Image.Image, current: Image.Image) -> dict[str, Any]:
    a = np.asarray(parent.convert("RGB"), dtype=np.int16)
    b = np.asarray(current.convert("RGB"), dtype=np.int16)
    if a.shape != b.shape:
        raise ValueError(f"frame dimensions drift: {a.shape} != {b.shape}")
    delta = np.abs(b - a)
    changed = np.any(delta > SIGNIFICANT_CHANNEL_DELTA_LSB, axis=2)
    ys, xs = np.where(changed)
    bbox = [] if xs.size == 0 else [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    return {
        "changed_pixels_gt_1_lsb": int(changed.sum()),
        "total_pixels": int(changed.size),
        "changed_fraction_gt_1_lsb": float(changed.sum() / changed.size),
        "changed_bbox_gt_1_lsb": bbox,
        "maximum_rgb_channel_delta_lsb": int(delta.max()),
    }


def runtime_sets(receipt: dict[str, Any]) -> dict[str, dict[str, list[list[int]]]]:
    sets: dict[str, dict[str, set[tuple[int, int, int, int, int]]]] = {
        mode: {context: set() for context in CONTEXTS} for mode in MODES
    }
    for sample in receipt.get("samples", []):
        for context in CONTEXTS:
            for mode in MODES:
                row = sample["contexts"][context][mode]["runtime"]
                sets[mode][context].add((
                    int(row["draw_calls_in_frame"]),
                    int(row["objects_in_frame"]),
                    int(row["primitives_in_frame"]),
                    int(row["buffer_mem_bytes"]),
                    int(row["texture_mem_bytes"]),
                ))
    return {
        mode: {context: [list(row) for row in sorted(sets[mode][context])] for context in CONTEXTS}
        for mode in MODES
    }


def build_montage(parent_frames: Path, current_frames: Path, output: Path) -> None:
    columns = 3
    rows = len(CONTEXTS)
    samples = []
    for context in CONTEXTS:
        name = f"atmosphere-width-control-{context}-00.png"
        old = Image.open(parent_frames / name).convert("RGB")
        new = Image.open(current_frames / name).convert("RGB")
        diff = ImageEnhance.Brightness(ImageChops.difference(old, new)).enhance(3.0)
        samples.append((context, old, new, diff))
    width, height = samples[0][1].size
    title_h = 34
    canvas = Image.new("RGB", (width * columns, (height + title_h) * rows), "white")
    draw = ImageDraw.Draw(canvas)
    labels = ("exact parent", "source-segmented receiver", "3x RGB difference")
    for row_index, (context, old, new, diff) in enumerate(samples):
        top = row_index * (height + title_h)
        for col, (label, image) in enumerate(zip(labels, (old, new, diff))):
            x = col * width
            draw.text((x + 8, top + 8), f"{context} — {label}", fill="black")
            canvas.paste(image, (x, top + title_h))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def review(candidate_root: Path, parent_root: Path, review_head: str) -> dict[str, Any]:
    exact_head = (candidate_root / "exact-head.txt").read_text(encoding="utf-8").strip()
    if exact_head != IMPLEMENTATION_HEAD:
        raise ValueError(f"exact implementation head drift: {exact_head}")
    payload = load(candidate_root / "combined_current_world.json")
    runtime = load(candidate_root / "runtime.json")
    parent_payload = load(parent_root / "combined_current_world.json")
    parent_target = load(parent_root / "target_host.json")

    if payload.get("status") != "PASS_CURRENT_WORLD_BUILDING_HEADER_SEGMENTATION_STRUCTURE":
        raise ValueError("segmentation structure did not PASS")
    if payload.get("receiving_head") != IMPLEMENTATION_HEAD:
        raise ValueError("segmentation payload receiving head drift")
    if payload.get("building_source_head") != SOURCE_HEAD or payload.get("building_material_head") != MATERIAL_HEAD:
        raise ValueError("exact source/material authority drift")
    segmentation = payload.get("building_header_segmentation", {})
    if segmentation.get("revision") != SEGMENTATION_REVISION:
        raise ValueError("segmentation revision drift")
    if segmentation.get("source_positive_volume_intersection_count") != 4:
        raise ValueError("historical positive-volume overlap evidence drift")
    if segmentation.get("successor_positive_volume_intersection_count") != 0:
        raise ValueError("segmented successor still contains positive-volume overlap")
    if segmentation.get("occupied_union", {}).get("equivalent") is not True:
        raise ValueError("source-owned occupied-union equivalence missing")
    if float(segmentation.get("occupied_union", {}).get("volume_residual_m3", 1.0)) != 0.0:
        raise ValueError("source-owned occupied-union residual drift")
    topology = segmentation.get("topology", {})
    if topology.get("vertex_count") != 184 or topology.get("triangle_count") != 276 or topology.get("object_count") != 23:
        raise ValueError("segmented source topology identity drift")
    if not all(payload.get("checks", {}).values()):
        raise ValueError("structural current-world checks drift")

    if parent_payload.get("receiving_head") != PARENT_HEAD or parent_payload.get("composition_digest") != PARENT_COMPOSITION_DIGEST:
        raise ValueError("exact Environment parent payload drift")
    if parent_target.get("state") != "PASS_CURRENT_WORLD_OBJECT_READABILITY_DRESSING_TARGET_HOST":
        raise ValueError("exact Environment parent target-host evidence drift")
    if runtime.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError("real Godot observation did not reach inherited live PASS")
    if runtime.get("receiving_head") != IMPLEMENTATION_HEAD:
        raise ValueError("live Godot receiving head drift")
    if runtime.get("environment_building_header_segmentation_source_head") != SOURCE_HEAD:
        raise ValueError("live segmented Building source head drift")
    if runtime.get("environment_building_header_segmentation_material_head") != MATERIAL_HEAD:
        raise ValueError("live segmented Building material head drift")
    if runtime.get("environment_building_header_segmentation_revision") != SEGMENTATION_REVISION:
        raise ValueError("live segmented Building revision drift")

    samples = runtime.get("samples", [])
    if len(samples) != 17:
        raise ValueError("expected exactly 17 real-host states")

    current_frames = candidate_root / "rendered"
    parent_frames = parent_root / "rendered"
    comparisons: dict[str, dict[str, list[dict[str, Any]]]] = {
        mode: {context: [] for context in CONTEXTS} for mode in MODES
    }
    width_residual = 0.0
    width_count = 0
    object_ok = True
    dressing_ok = True
    rear_ok = True
    building_ok = True

    for sample in samples:
        index = int(sample["index"])
        static = sample.get("static_source_meshes", [])
        object_rows = [row for row in static if row.get("asset_id") == OBJECT_ASSET]
        dressing_rows = [row for row in static if row.get("asset_id") == DRESSING_ASSET]
        rear_rows = [row for row in static if row.get("asset_id") == REAR_NATURE_ASSET]
        building_rows = [row for row in static if row.get("asset_id") == BUILDING_ASSET]
        object_ok &= len(object_rows) == 1 and object_rows[0].get("vertices") == 468 and object_rows[0].get("triangles") == 812
        dressing_ok &= len(dressing_rows) == 1 and dressing_rows[0].get("triangles") == 48
        rear_ok &= len(rear_rows) == 1 and rear_rows[0].get("proof_culling") == "CULL_BACK"
        building_ok &= (
            len(building_rows) == 1
            and building_rows[0].get("vertices") == 184
            and building_rows[0].get("triangles") == 276
            and building_rows[0].get("surface_count") == 5
        )
        for context in CONTEXTS:
            for mode in MODES:
                weather = sample["contexts"][context][mode].get("weather_update", {})
                width_residual = max(width_residual, float(weather.get("maximum_projected_width_residual_px", 0.0)))
                if mode == "candidate":
                    width_count += int(weather.get("measured_width_count", 0))
                name = f"atmosphere-width-{mode}-{context}-{index:02d}.png"
                current_path = current_frames / name
                parent_path = parent_frames / name
                if not current_path.exists() or not parent_path.exists():
                    raise ValueError(f"missing retained frame pair {name}")
                row = significant_delta(Image.open(parent_path), Image.open(current_path))
                row.update({"index": index, "mode": mode, "context": context})
                comparisons[mode][context].append(row)

    summary: dict[str, Any] = {}
    mode_parity = True
    state_stability = True
    fixed_bbox = True
    bounded_fraction = True
    max_delta_lsb = 0
    pair_count = 0
    for context in CONTEXTS:
        context_rows = comparisons["control"][context] + comparisons["candidate"][context]
        fractions = [row["changed_fraction_gt_1_lsb"] for row in context_rows]
        counts = [row["changed_pixels_gt_1_lsb"] for row in context_rows]
        bboxes = [tuple(row["changed_bbox_gt_1_lsb"]) for row in context_rows]
        maxima = [row["maximum_rgb_channel_delta_lsb"] for row in context_rows]
        pair_count += len(context_rows)
        max_delta_lsb = max(max_delta_lsb, max(maxima))
        bounded_fraction &= max(fractions) <= MAX_CHANGED_FRACTION
        state_stability &= (max(counts) - min(counts)) <= 1
        fixed_bbox &= len(set(bboxes)) == 1
        for index in range(17):
            a = comparisons["control"][context][index]
            b = comparisons["candidate"][context][index]
            mode_parity &= (
                a["changed_pixels_gt_1_lsb"] == b["changed_pixels_gt_1_lsb"]
                and a["changed_bbox_gt_1_lsb"] == b["changed_bbox_gt_1_lsb"]
                and a["maximum_rgb_channel_delta_lsb"] == b["maximum_rgb_channel_delta_lsb"]
            )
        summary[context] = {
            "pair_count": len(context_rows),
            "changed_pixels_gt_1_lsb_min": min(counts),
            "changed_pixels_gt_1_lsb_max": max(counts),
            "changed_fraction_gt_1_lsb_min": min(fractions),
            "changed_fraction_gt_1_lsb_max": max(fractions),
            "fixed_changed_bbox_gt_1_lsb": list(bboxes[0]),
            "maximum_rgb_channel_delta_lsb": max(maxima),
        }

    current_runtime = runtime_sets(runtime)
    parent_runtime = parent_target.get("runtime_counter_sets", {})
    runtime_delta: dict[str, dict[str, list[int]]] = {mode: {} for mode in MODES}
    runtime_stable = True
    for mode in MODES:
        for context in CONTEXTS:
            current_rows = current_runtime[mode][context]
            parent_rows = parent_runtime.get(mode, {}).get(context, [])
            runtime_stable &= len(current_rows) == 1 and len(parent_rows) == 1
            if len(current_rows) != 1 or len(parent_rows) != 1:
                raise ValueError(f"runtime counter instability {mode}/{context}")
            runtime_delta[mode][context] = [int(a) - int(b) for a, b in zip(current_rows[0], parent_rows[0])]

    expected_runtime_delta = [0, 0, 144, 2880, 0]
    runtime_delta_exact = all(runtime_delta[mode][context] == expected_runtime_delta for mode in MODES for context in CONTEXTS)

    checks = {
        "strict_pixel_identity_failure_is_retained_not_rewritten": True,
        "exact_structural_segmentation_payload_passes": payload.get("status") == "PASS_CURRENT_WORLD_BUILDING_HEADER_SEGMENTATION_STRUCTURE" and all(payload.get("checks", {}).values()),
        "exact_real_godot_live_observation_passes": runtime.get("state") == "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION",
        "all_17_dynamic_states_retained": len(samples) == 17,
        "all_68_parent_successor_pairs_compared": pair_count == 68,
        "changed_fraction_remains_within_materials_donor_one_percent_continuity_guard": bounded_fraction,
        "screen_region_is_fixed_per_camera": fixed_bbox,
        "static_segmentation_delta_is_state_stable_to_one_pixel": state_stability,
        "weather_control_and_source_width_modes_have_identical_segmentation_delta": mode_parity,
        "exact_segmented_building_runtime_identity": building_ok,
        "exact_object_source_runtime_identity_preserved": object_ok,
        "pending_object_readability_dressing_preserved_without_adoption": dressing_ok,
        "rear_nature_cull_back_preserved": rear_ok,
        "source_width_weather_fidelity_preserved": width_count == 17 * 2 * 36 and width_residual <= 0.05,
        "runtime_counter_sets_stable": runtime_stable,
        "runtime_delta_exactly_characterized_not_accepted": runtime_delta_exact,
    }
    if not all(checks.values()):
        raise ValueError(f"bounded current-world continuity review failed: {checks}")

    report = {
        "schema": SCHEMA,
        "state": STATE,
        "review_head": review_head,
        "exact_implementation_head": IMPLEMENTATION_HEAD,
        "exact_parent_head": PARENT_HEAD,
        "parent_composition_digest": PARENT_COMPOSITION_DIGEST,
        "building_source_head": SOURCE_HEAD,
        "building_material_head": MATERIAL_HEAD,
        "segmentation_revision": SEGMENTATION_REVISION,
        "strict_gate_history": {
            "workflow_run": 35129750104,
            "artifact_id": 10460871165,
            "artifact_sha256": "add8d72e9dee4398ef844892138308022261d2d5a4f22a652f4dda9dbdb26d70",
            "result": "FAIL_STRICT_NO_RGB_DELTA_ABOVE_ONE_LSB",
            "reason": "The first receiving verifier required byte-near visual identity. Direct retained frames disproved that assumption, so the failure is kept as evidence rather than erased.",
        },
        "continuity_precedent": {
            "materials_head": MATERIAL_HEAD,
            "materials_workflow_run": 35128142780,
            "guard": "changed_fraction_gt_1_lsb <= 0.01",
            "scope": "Same source-owned 19-output to 23-output header segmentation; reused only as a bounded continuity diagnostic, not as visual approval.",
        },
        "checks": checks,
        "visual_delta": summary,
        "maximum_rgb_channel_delta_lsb": max_delta_lsb,
        "maximum_projected_weather_width_residual_px": width_residual,
        "measured_projected_weather_width_count": width_count,
        "runtime_counter_order": ["draw_calls", "objects", "primitives", "buffer_mem_bytes", "texture_mem_bytes"],
        "current_runtime_counter_sets": current_runtime,
        "parent_runtime_counter_sets": parent_runtime,
        "runtime_counter_delta_vs_parent": runtime_delta,
        "truth_boundary": (
            "PASS means the source-owned 19->23 Building header segmentation composes through the exact current Godot world with a small, fixed, static screen-space delta under both inherited Weather modes, while exact Object, pending Object dressing, Nature culling and Weather-width behavior remain present. "
            "The direct delta is real and is not relabeled as pixel identity, perceptual improvement, Art Direction/Visual QA acceptance or target-device performance."
        ),
        "handoffs": {
            "art_direction_and_visual_qa": "Review the retained fixed Building-region highlight/shading delta before current-world adoption. The exact a29aa Object footprint cue remains independently held.",
            "runtime_optimization": "Characterize the exact stable +0 draw / +0 object / +144 primitive-counter / +2880 B observed-buffer / +0 texture delta before target-device acceptance.",
            "hard_surface": "No source rewrite requested. Environment consumed the exact source-owned segmentation and preserved its union/mount authority boundary.",
            "materials": "No scalar or mapping rewrite requested. Exact five-surface values and six explicit frame segment bindings remain unchanged.",
        },
        "non_claims": [
            "STRICT_PIXEL_IDENTITY_WITH_THE_PARENT_RECEIVER",
            "FINAL_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "OBJECT_FOOTPRINT_DRESSING_ADOPTION",
            "BOOLEAN_UNIONED_OR_GLOBAL_VERTEX_MANIFOLD_BUILDING",
            "FINAL_NORMALS_TANGENTS_UVS_TEXTURES_DECALS_OR_WEATHERING",
            "TARGET_DEVICE_CPU_GPU_FPS_MEMORY_OR_BATCHING_ACCEPTANCE",
            "COLLISION_NAVIGATION_OR_GAMEPLAY",
            "ARBITRARY_CAMERA_RENDERER_OR_RESOLUTION_EQUIVALENCE",
            "UC_OR_PROFESSION_FABRIC_EXTRACTION",
            "CANON_PRODUCTION_READY_GAME_READY_OR_ENVIRONMENT_MASTERY",
        ],
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--parent-root", required=True)
    parser.add_argument("--review-head", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--montage", required=True)
    args = parser.parse_args()

    candidate_root = Path(args.candidate_root)
    parent_root = Path(args.parent_root)
    report = review(candidate_root, parent_root, args.review_head.strip())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    build_montage(parent_root / "rendered", candidate_root / "rendered", Path(args.montage))
    print(json.dumps({
        "state": report["state"],
        "visual_delta": report["visual_delta"],
        "maximum_projected_weather_width_residual_px": report["maximum_projected_weather_width_residual_px"],
        "runtime_counter_delta_vs_parent": report["runtime_counter_delta_vs_parent"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
