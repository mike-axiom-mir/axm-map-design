#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

EXPECTED_STATE = "PASS_TELEMETRY_BOUND_CLEAN_VS_IDEAL_REVIEW_SURFACE"
EXPECTED_RECEIVER = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
EXPECTED_EFFECT = "ecade64227ba1d3d1faf029ca7188ea63c2560ec"
EXPECTED_TIMING = "795d9e8862e895e506c756b9ea01cd6228fa7ab7"
EXPECTED_SKIPS = {"path_eye": [19], "elevated_oblique": [11, 23, 38]}
STEP_MS = 31.25
RASTER_HZ = 64
FRAME_MS = 1000.0 / RASTER_HZ
WINDOW_INTERVALS = 7
FRAME_COUNT = int(round((WINDOW_INTERVALS * STEP_MS) / FRAME_MS))
assert FRAME_COUNT == 14


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def state_at(events: list, t_ms: float) -> dict:
    out = events[0]
    for e in events[1:]:
        if float(e["time_ms"]) <= t_ms + 1e-9:
            out = e
        else:
            break
    return out


def verify_event_image(root: Path, event: dict) -> Path:
    path = root / event["png"]
    assert path.is_file(), path
    got = sha256(path)
    assert got == event["png_sha256"], (path, got, event["png_sha256"])
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    root = args.parent.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "frames").mkdir(exist_ok=True)

    manifest = json.loads((root / "comparison-manifest.json").read_text())
    assert manifest["state"] == EXPECTED_STATE, manifest
    assert manifest["accepted_receiver_head"] == EXPECTED_RECEIVER, manifest
    assert manifest["nature_vfx_effect_head"] == EXPECTED_EFFECT, manifest
    assert manifest["clean_timing_head"] == EXPECTED_TIMING, manifest
    assert manifest["clean_presented_total"] == 92 and manifest["clean_scheduled_total"] == 96, manifest
    assert manifest["interpolation_added"] is False, manifest
    assert manifest["source_retimed"] is False, manifest
    assert manifest["direct_live_capture_of_clean_stream"] is False, manifest
    assert manifest["ideal_schedule_is_counterfactual_reference_not_observed_runtime"] is True, manifest
    assert manifest["browser_is_timing_authority"] is False, manifest

    report = {
        "state": "PASS_TELEMETRY_BOUND_SKIPPED_STATE_TEMPORAL_AB_REVIEW_FRAMES_BUILT_PENDING_MEDIA",
        "accepted_receiver_head": EXPECTED_RECEIVER,
        "nature_vfx_effect_head": EXPECTED_EFFECT,
        "clean_timing_head": EXPECTED_TIMING,
        "parent_clean_vs_ideal_head": "9e3a7e64ebd50be175ef6866a0fa37960d589adb",
        "parent_clean_vs_ideal_workflow": 35206708371,
        "clean_scheduled_total": 96,
        "clean_presented_total": 92,
        "timing_authority": "RETAINED_CLEAN_FRAME_POST_DRAW_TELEMETRY_ONLY",
        "comparison_raster_hz": RASTER_HZ,
        "comparison_frame_ms": FRAME_MS,
        "maximum_review_raster_quantization_ms": FRAME_MS,
        "comparison_raster_semantics": "REVIEW_ONLY_SAMPLE_AND_HOLD_OF_EXACT_SOURCE_STATE_IMAGES_NO_MOTION_INTERPOLATION",
        "ideal_step_exact_review_frames": 2,
        "native_media_is_timing_authority": False,
        "slow_media_is_timing_authority": False,
        "slow_review_factor": 4.0,
        "source_interpolation_added": False,
        "source_retimed": False,
        "source_amplitude_modified": False,
        "clean_stream_direct_live_capture": False,
        "ideal_schedule_observed_runtime": False,
        "final_perceptual_acceptance_claimed": False,
        "gameplay_or_physics_claimed": False,
        "target_device_performance_claimed": False,
        "windows": [],
    }
    rows = []

    for context, skips in EXPECTED_SKIPS.items():
        context_data = manifest["contexts"][context]
        assert context_data["clean_skipped_slots"] == skips, context_data
        clean = context_data["cadence_aligned_clean_events"]
        ideal = context_data["ideal_events"]
        clean_slots = {
            int(e["absolute_slot"])
            for e in clean
            if e.get("absolute_slot") is not None
        }

        for slot in skips:
            assert slot not in clean_slots, (context, slot)
            phase = slot % 16
            start_slot = slot - 3
            start_ms = start_slot * STEP_MS
            duration_ms = WINDOW_INTERVALS * STEP_MS
            stem = f"{context}-slot-{slot:02d}-clean-left-ideal-right"
            frame_dir = out / "frames" / stem
            frame_dir.mkdir(parents=True, exist_ok=True)

            frame_rows = []
            differing = 0
            for frame_index in range(FRAME_COUNT):
                comparison_ms = start_ms + frame_index * FRAME_MS
                clean_event = state_at(clean, comparison_ms)
                ideal_event = state_at(ideal, comparison_ms)
                clean_path = verify_event_image(root, clean_event)
                ideal_path = verify_event_image(root, ideal_event)

                with Image.open(clean_path) as clean_image, Image.open(ideal_path) as ideal_image:
                    left = clean_image.convert("RGB")
                    right = ideal_image.convert("RGB")
                    assert left.size == (1100, 720), left.size
                    assert right.size == (1100, 720), right.size
                    canvas = Image.new("RGB", (2200, 720))
                    canvas.paste(left, (0, 0))
                    canvas.paste(right, (1100, 0))
                    frame_path = frame_dir / f"frame-{frame_index:03d}.png"
                    canvas.save(frame_path, compress_level=6)

                states_differ = int(clean_event["source_phase_index"]) != int(ideal_event["source_phase_index"])
                differing += int(states_differ)
                frame_rows.append({
                    "index": frame_index,
                    "window_time_ms": frame_index * FRAME_MS,
                    "comparison_time_ms": comparison_ms,
                    "clean_phase": int(clean_event["source_phase_index"]),
                    "clean_slot": clean_event.get("absolute_slot"),
                    "ideal_phase": int(ideal_event["source_phase_index"]),
                    "ideal_slot": ideal_event.get("absolute_slot"),
                    "source_states_differ": states_differ,
                    "frame_png": str(frame_path.relative_to(out)),
                    "frame_sha256": sha256(frame_path),
                })

            # The authored skipped state is exactly centered on the 64 Hz review
            # lattice because 31.25 ms is exactly two 64 Hz frames.
            assert frame_rows[6]["ideal_phase"] == phase, (context, slot, frame_rows[6])
            window = {
                "context": context,
                "skipped_slot": slot,
                "skipped_phase": phase,
                "start_slot": start_slot,
                "end_slot": slot + 3,
                "review_start_ms": start_ms,
                "review_duration_ms": duration_ms,
                "frame_count": FRAME_COUNT,
                "differing_source_state_review_frames": differing,
                "clean_side": "CADENCE_ALIGNED_RETAINED_CLEAN_FRAME_POST_DRAW_RECONSTRUCTION",
                "ideal_side": "UNOBSERVED_AUTHORED_31_25MS_SOURCE_SCHEDULE_REFERENCE",
                "stem": stem,
                "frames": frame_rows,
            }
            report["windows"].append(window)
            rows.append((context, slot, phase, stem, FRAME_COUNT))

    assert len(report["windows"]) == 4
    (out / "windows.tsv").write_text("\n".join("\t".join(map(str, row)) for row in rows) + "\n")
    (out / "temporal-ab-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "state": report["state"],
        "windows": [
            {key: window[key] for key in (
                "context", "skipped_slot", "skipped_phase", "frame_count", "differing_source_state_review_frames"
            )}
            for window in report["windows"]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
