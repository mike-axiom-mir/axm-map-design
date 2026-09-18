from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

RESULT = "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_MATERIAL_BOUND_RECEIVER__VISIBLE_DELTA_CHARACTERIZED__ADOPTION_HELD"
STATE = "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_MATERIAL_BOUND_RECEIVER__A_B_REVIEW_ONLY__ADOPTION_HELD"
PNG_SHA = "e932cdd94d370184c7361862d5064149cc193e3a8fd80b269cab6543c0919198"
RGBA_SHA = "02f8f464eabc734a3be687a7706edf8b8f62ece834fa981c8c993fbb8227bb4b"
TA_HEAD = "1434bc4a64faa04db10f47723c37ab7925aaa163"
MATERIALS_HEAD = "0ae911792929eaa38b2c2f32239ebfdce8967251"


def load(path: Path):
    return json.loads(path.read_text())


def canonical_runtime(runtime: dict) -> dict:
    drop = {
        "environment_building_utility_panel_material_current_world_state",
        "environment_building_utility_panel_material_current_world_rule",
        "environment_building_utility_panel_material_technical_art_head",
        "environment_building_utility_panel_material_materials_head",
        "environment_building_utility_panel_material_png_sha256",
        "environment_building_utility_panel_material_rgba8_sha256",
        "environment_building_utility_panel_material_environment_adoption",
        "environment_building_utility_panel_material_art_qa_acceptance",
        "environment_building_utility_panel_material_runtime_acceptance",
        "environment_building_utility_panel_material_truth_boundary",
    }

    def scrub(value, path=()):
        if isinstance(value, dict):
            out = {}
            for k, v in value.items():
                if k in drop:
                    continue
                if k in {"node_instance_id", "mesh_instance_id", "material_instance_id"}:
                    continue
                if k == "environment_building_utility_panel_material_current_world":
                    continue
                # These are intentionally process/presentation-sensitive. The exact
                # material adds one texture and changes PNG compressibility, so they
                # are characterized separately rather than mistaken for scene drift.
                if path and path[-1] == "capture" and k == "bytes":
                    continue
                if path and path[-1] == "runtime" and k in {"buffer_mem_bytes", "texture_mem_bytes"}:
                    continue
                out[k] = scrub(v, path + (k,))
            return out
        if isinstance(value, list):
            return [scrub(v, path + (str(i),)) for i, v in enumerate(value)]
        return value

    return scrub(runtime)


def presentation_metrics(control: dict, candidate: dict) -> dict:
    cs = control.get("samples", [])
    ds = candidate.get("samples", [])
    assert len(cs) == len(ds) == 17
    capture_deltas = []
    buffer_deltas = []
    texture_deltas = []
    observations = 0
    for c_state, d_state in zip(cs, ds):
        assert c_state.get("index") == d_state.get("index")
        c_contexts = c_state.get("contexts", {})
        d_contexts = d_state.get("contexts", {})
        assert set(c_contexts) == set(d_contexts)
        for context_name in sorted(c_contexts):
            c_context = c_contexts[context_name]
            d_context = d_contexts[context_name]
            assert set(c_context) == set(d_context)
            for presentation_name in sorted(c_context):
                c_row = c_context[presentation_name]
                d_row = d_context[presentation_name]
                capture_deltas.append(int(d_row["capture"]["bytes"]) - int(c_row["capture"]["bytes"]))
                buffer_deltas.append(int(d_row["runtime"]["buffer_mem_bytes"]) - int(c_row["runtime"]["buffer_mem_bytes"]))
                texture_deltas.append(int(d_row["runtime"]["texture_mem_bytes"]) - int(c_row["runtime"]["texture_mem_bytes"]))
                observations += 1
    assert observations == 68
    # The exact review texture is expected to increase these process metrics. Keep
    # the values visible rather than silently normalizing them out of the evidence.
    assert all(v > 0 for v in capture_deltas)
    assert all(v > 0 for v in buffer_deltas)
    assert all(v > 0 for v in texture_deltas)
    return {
        "observations": observations,
        "capture_png_bytes_delta_min": min(capture_deltas),
        "capture_png_bytes_delta_max": max(capture_deltas),
        "capture_png_bytes_delta_mean": float(sum(capture_deltas) / observations),
        "buffer_mem_bytes_delta_values": sorted(set(buffer_deltas)),
        "texture_mem_bytes_delta_values": sorted(set(texture_deltas)),
    }


def image_metrics(a: Path, b: Path) -> dict:
    ai = np.asarray(Image.open(a).convert("RGB"), dtype=np.int16)
    bi = np.asarray(Image.open(b).convert("RGB"), dtype=np.int16)
    if ai.shape != bi.shape:
        raise AssertionError(f"dimension drift {a.name} {ai.shape} != {bi.shape}")
    d = np.abs(ai - bi)
    per = d.max(axis=2)
    ys, xs = np.nonzero(per > 0)
    gt1 = per > 1
    return {
        "raw_changed_pixels": int((per > 0).sum()),
        "changed_pixels_gt_1lsb": int(gt1.sum()),
        "max_rgb_channel_delta_lsb": int(per.max()),
        "changed_bbox_px": None if xs.size == 0 else [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "mean_abs_rgb_delta_lsb": float(d.mean()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--control-runtime", type=Path, required=True)
    ap.add_argument("--candidate-runtime", type=Path, required=True)
    ap.add_argument("--control-rendered", type=Path, required=True)
    ap.add_argument("--candidate-rendered", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    contract = load(args.contract)
    assert contract["schema"] == "axm.environment-building-utility-panel-material-current-world-ab/v0.1"
    assert contract["technical_art"]["head"] == TA_HEAD
    assert contract["materials"]["head"] == MATERIALS_HEAD
    assert contract["materials"]["retained_png_sha256"] == PNG_SHA
    assert contract["materials"]["retained_rgba8_sha256"] == RGBA_SHA
    assert contract["promotion"]["environment_adoption"] is False

    control = load(args.control_runtime)
    candidate = load(args.candidate_runtime)
    assert candidate.get("environment_building_utility_panel_material_current_world_state") == STATE
    assert candidate.get("environment_building_utility_panel_material_technical_art_head") == TA_HEAD
    assert candidate.get("environment_building_utility_panel_material_materials_head") == MATERIALS_HEAD
    assert candidate.get("environment_building_utility_panel_material_png_sha256") == PNG_SHA
    assert candidate.get("environment_building_utility_panel_material_rgba8_sha256") == RGBA_SHA
    assert candidate.get("environment_building_utility_panel_material_environment_adoption") is False
    assert candidate.get("environment_building_utility_panel_material_art_qa_acceptance") is False
    assert candidate.get("environment_building_utility_panel_material_runtime_acceptance") is False

    process_metrics = presentation_metrics(control, candidate)
    c0 = canonical_runtime(control)
    c1 = canonical_runtime(candidate)
    assert c0 == c1, "unrelated current-world runtime identity changed outside bounded material binding receipt and expected presentation metrics"

    control_files = sorted(args.control_rendered.glob("atmosphere-width-*.png"))
    candidate_files = sorted(args.candidate_rendered.glob("atmosphere-width-*.png"))
    assert len(control_files) == len(candidate_files) == 68
    assert [p.name for p in control_files] == [p.name for p in candidate_files]

    frames = []
    total_raw = total_gt1 = 0
    max_delta = 0
    frames_with_delta = 0
    frames_gt1 = 0
    for a, b in zip(control_files, candidate_files):
        m = image_metrics(a, b)
        m["frame"] = a.name
        frames.append(m)
        total_raw += m["raw_changed_pixels"]
        total_gt1 += m["changed_pixels_gt_1lsb"]
        max_delta = max(max_delta, m["max_rgb_channel_delta_lsb"])
        frames_with_delta += int(m["raw_changed_pixels"] > 0)
        frames_gt1 += int(m["changed_pixels_gt_1lsb"] > 0)
    assert total_raw > 0, "exact material binding produced no observable raster delta"
    assert total_gt1 > 0, "exact material binding never exceeded 1 LSB; observer activity not demonstrated"

    report = {
        "schema": "axm.environment-building-utility-panel-material-current-world-ab-report/v0.1",
        "result": RESULT,
        "reusable_rule": contract["reusable_rule"],
        "owner_motion_sample_index": contract["environment"]["object_motion_sample_index"],
        "current_world": {
            "rendered_frames_per_variant": 68,
            "building_vertices": 184,
            "building_triangles": 276,
            "building_surfaces": 5,
            "runtime_identity_equal_outside_material_binding_receipt_and_expected_presentation_metrics": True,
            "presentation_metrics": process_metrics,
        },
        "material_binding": {
            "technical_art_head": TA_HEAD,
            "materials_head": MATERIALS_HEAD,
            "png_sha256": PNG_SHA,
            "rgba8_sha256": RGBA_SHA,
            "environment_adoption": False,
            "art_qa_acceptance": False,
            "runtime_acceptance": False,
        },
        "raster_delta": {
            "total_raw_changed_pixels": total_raw,
            "total_changed_pixels_gt_1lsb": total_gt1,
            "max_rgb_channel_delta_lsb": max_delta,
            "frames_with_any_delta": frames_with_delta,
            "frames_with_gt_1lsb_delta": frames_gt1,
            "aesthetic_minimum_delta": None,
        },
        "frames": frames,
        "truth_boundary": contract["truth_boundary"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(RESULT)
    print(json.dumps(report["raster_delta"], sort_keys=True))
    print(json.dumps(process_metrics, sort_keys=True))


if __name__ == "__main__":
    main()
