from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw

PARENT_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
CANDIDATE_HEAD = "29ef2d4cc4398b3f26290e4e1f1f10398ca9898c"
PARENT_RESULT = "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_TARGET_HOST"
CANDIDATE_RESULT = "PASS_CURRENT_WORLD_COMPACT_EAST_VISUAL_RESPONSE_TARGET_HOST"
RESULT = "PASS_COMPACT_EAST_CURRENT_WORLD_PARENT_ISOLATED_EFFECT_READABILITY_REVIEW"
CONTEXTS = ("path_eye", "elevated_oblique")
MODES = ("control", "candidate")
PHASES = tuple(range(17))
SELECTED_PHASES = (0, 2, 4, 6, 8, 10, 12, 14, 16)
EXPECTED_SIZE = (1100, 720)
DIFF_AMPLIFICATION = 8


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"expected object JSON at {path}")
    return value


def read_head(root: Path) -> str:
    return (root / "exact-head.txt").read_text(encoding="utf-8").strip()


def frame_path(root: Path, mode: str, context: str, phase: int) -> Path:
    return root / "candidate" / "rendered" / f"atmosphere-width-{mode}-{context}-{phase:02d}.png"


def bbox_from_diff(diff: Image.Image) -> tuple[int, int, int, int] | None:
    rgb = diff.convert("RGB")
    mask = rgb.getchannel("R").point(lambda v: 255 if v else 0)
    for channel_name in ("G", "B"):
        channel = rgb.getchannel(channel_name).point(lambda v: 255 if v else 0)
        mask = ImageChops.lighter(mask, channel)
    return mask.getbbox()


def pixel_metrics(parent: Image.Image, candidate: Image.Image) -> dict[str, Any]:
    if parent.size != EXPECTED_SIZE or candidate.size != EXPECTED_SIZE:
        raise ValueError(f"unexpected image size: parent={parent.size} candidate={candidate.size}")
    diff = ImageChops.difference(parent.convert("RGB"), candidate.convert("RGB"))
    changed = 0
    above_1 = 0
    max_delta = 0
    px = diff.load()
    w, h = diff.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            m = max(r, g, b)
            if m:
                changed += 1
                max_delta = max(max_delta, m)
            if m > 1:
                above_1 += 1
    bbox = bbox_from_diff(diff)
    return {
        "changed_pixels": changed,
        "pixels_above_1_lsb": above_1,
        "max_rgb_channel_delta_lsb": max_delta,
        "bbox": list(bbox) if bbox else None,
    }


def union_bbox(boxes: list[list[int] | None]) -> list[int] | None:
    present = [b for b in boxes if b is not None]
    if not present:
        return None
    return [
        min(b[0] for b in present),
        min(b[1] for b in present),
        max(b[2] for b in present),
        max(b[3] for b in present),
    ]


def pad_bbox(box: list[int], padding: int = 16) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    w, h = EXPECTED_SIZE
    return max(0, x0 - padding), max(0, y0 - padding), min(w, x1 + padding), min(h, y1 + padding)


def outside_roi_count(diff: Image.Image, roi: list[int]) -> int:
    x0, y0, x1, y1 = roi
    rgb = diff.convert("RGB")
    px = rgb.load()
    w, h = rgb.size
    count = 0
    for y in range(h):
        for x in range(w):
            if x0 <= x < x1 and y0 <= y < y1:
                continue
            if max(px[x, y]) > 0:
                count += 1
    return count


def diagnostic_diff(parent: Image.Image, candidate: Image.Image) -> Image.Image:
    diff = ImageChops.difference(parent.convert("RGB"), candidate.convert("RGB"))
    lut = [min(255, value * DIFF_AMPLIFICATION) for value in range(256)]
    return diff.point(lut * 3)


def make_grid(tiles: list[tuple[str, Image.Image]], title: str, output: Path) -> None:
    if not tiles:
        raise ValueError("cannot make an empty review grid")
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    tile_w = max(img.width for _, img in tiles)
    tile_h = max(img.height for _, img in tiles)
    label_h = 40
    title_h = 48
    canvas = Image.new("RGB", (cols * tile_w, title_h + rows * (tile_h + label_h)), "black")
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 14), title, fill="white")
    for index, (label, img) in enumerate(tiles):
        col = index % cols
        row = index // cols
        x = col * tile_w
        y = title_h + row * (tile_h + label_h)
        canvas.paste(img, (x, y))
        draw.text((x + 8, y + tile_h + 10), label, fill="white")
    canvas.save(output)


def build(parent_root: Path, candidate_root: Path, output_root: Path) -> dict[str, Any]:
    parent_head = read_head(parent_root)
    candidate_head = read_head(candidate_root)
    if parent_head != PARENT_HEAD:
        raise ValueError(f"accepted parent head drift: {parent_head}")
    if candidate_head != CANDIDATE_HEAD:
        raise ValueError(f"compact-east candidate head drift: {candidate_head}")

    parent_report = load_json(parent_root / "report.json")
    candidate_report = load_json(candidate_root / "report.json")
    if parent_report.get("state") != PARENT_RESULT:
        raise ValueError("accepted parent target-host result is not green")
    if candidate_report.get("state") != CANDIDATE_RESULT:
        raise ValueError("compact-east current-world target-host result is not green")
    if int(candidate_report.get("matched_frames", -1)) != 68:
        raise ValueError("compact-east retained frame count drift")
    if candidate_report.get("fully_observing_contexts") != ["elevated_oblique"]:
        raise ValueError("compact-east observing-camera classification drift")
    if candidate_report.get("non_observing_contexts") != ["path_eye"]:
        raise ValueError("compact-east non-observing-camera classification drift")

    candidate_payload = load_json(candidate_root / "combined_current_world.json")
    states = candidate_payload.get("states", [])
    if not isinstance(states, list) or len(states) != 17:
        raise ValueError("compact-east source phase payload count drift")
    phase_times = []
    for index, row in enumerate(states):
        if int(row.get("index", -1)) != index:
            raise ValueError(f"phase identity drift at {index}")
        phase_times.append(float(row.get("time_s", -1.0)))

    metrics: dict[str, dict[str, list[dict[str, Any]]]] = {}
    all_elevated_boxes: list[list[int] | None] = []
    images: dict[tuple[str, str, int, str], Image.Image] = {}

    for mode in MODES:
        metrics[mode] = {}
        for context in CONTEXTS:
            rows: list[dict[str, Any]] = []
            for phase in PHASES:
                pp = frame_path(parent_root, mode, context, phase)
                cp = frame_path(candidate_root, mode, context, phase)
                if not pp.is_file() or not cp.is_file():
                    raise ValueError(f"missing retained frame: {pp} or {cp}")
                pimg = Image.open(pp).convert("RGB")
                cimg = Image.open(cp).convert("RGB")
                images[(mode, context, phase, "parent")] = pimg
                images[(mode, context, phase, "candidate")] = cimg
                row = {"phase": phase, "time_s": phase_times[phase], **pixel_metrics(pimg, cimg)}
                rows.append(row)
                if context == "elevated_oblique":
                    all_elevated_boxes.append(row["bbox"])
            metrics[mode][context] = rows

    for mode in MODES:
        path_rows = metrics[mode]["path_eye"]
        if any(row["changed_pixels"] != 0 for row in path_rows):
            raise ValueError(f"path_eye is no longer a non-observing compact-east context in mode {mode}")
        elevated = metrics[mode]["elevated_oblique"]
        if elevated[0]["changed_pixels"] != 0 or elevated[-1]["changed_pixels"] != 0:
            raise ValueError(f"compact-east neutral endpoints changed in mode {mode}")
        if not all(row["changed_pixels"] > 0 for row in elevated[1:-1]):
            raise ValueError(f"compact-east interior visibility gap in mode {mode}")

    roi = union_bbox(all_elevated_boxes)
    if roi is None:
        raise ValueError("no compact-east current-world visual delta was observed")

    outside_counts: dict[str, list[int]] = {}
    for mode in MODES:
        outside_counts[mode] = []
        for phase in PHASES:
            pimg = images[(mode, "elevated_oblique", phase, "parent")]
            cimg = images[(mode, "elevated_oblique", phase, "candidate")]
            diff = ImageChops.difference(pimg, cimg)
            count = outside_roi_count(diff, roi)
            outside_counts[mode].append(count)
            if count != 0:
                raise ValueError(f"compact-east visual delta escaped fixed observed receiver envelope at {mode} phase {phase}: {count}")

    probe = Image.new("RGB", EXPECTED_SIZE, "black")
    px = probe.load()
    negative_xy = (0, 0)
    if roi[0] <= 0 < roi[2] and roi[1] <= 0 < roi[3]:
        negative_xy = (EXPECTED_SIZE[0] - 1, EXPECTED_SIZE[1] - 1)
    px[negative_xy[0], negative_xy[1]] = (1, 0, 0)
    negative_control_rejected = outside_roi_count(probe, roi) == 1
    if not negative_control_rejected:
        raise ValueError("outside-receiver negative control was not detected")

    output_root.mkdir(parents=True, exist_ok=True)
    crop_box = pad_bbox(roi, 20)
    for mode in MODES:
        motion_tiles: list[tuple[str, Image.Image]] = []
        diff_tiles: list[tuple[str, Image.Image]] = []
        for phase in SELECTED_PHASES:
            pimg = images[(mode, "elevated_oblique", phase, "parent")]
            cimg = images[(mode, "elevated_oblique", phase, "candidate")]
            crop = cimg.crop(crop_box)
            dd = diagnostic_diff(pimg, cimg).crop(crop_box)
            label = f"phase {phase:02d} / source t={phase_times[phase]:.5f}s"
            motion_tiles.append((label, crop))
            diff_tiles.append((label, dd))
        make_grid(
            motion_tiles,
            f"compact-east current-world receiver — {mode} Weather mode — exact candidate crop",
            output_root / f"compact-east-motion-strip-{mode}.png",
        )
        make_grid(
            diff_tiles,
            f"DIAGNOSTIC ONLY: {DIFF_AMPLIFICATION}x absolute RGB delta vs accepted parent — {mode} Weather mode",
            output_root / f"compact-east-parent-delta-strip-{mode}.png",
        )

    report = {
        "schema": "axm.map-vfx-compact-east-effect-readability-review/v0.1",
        "state": RESULT,
        "parent_head": PARENT_HEAD,
        "candidate_head": CANDIDATE_HEAD,
        "source_phase_count": 17,
        "source_phase_times_s": phase_times,
        "observing_context": "elevated_oblique",
        "non_observing_context": "path_eye",
        "weather_modes": list(MODES),
        "observed_receiver_union_bbox_xyxy": roi,
        "review_crop_bbox_xyxy": list(crop_box),
        "diagnostic_difference_amplification": DIFF_AMPLIFICATION,
        "metrics": metrics,
        "outside_receiver_changed_pixels": outside_counts,
        "negative_controls": {
            "synthetic_visible_pixel_outside_receiver_envelope_rejected": negative_control_rejected,
            "synthetic_pixel_xy": list(negative_xy),
        },
        "checks": {
            "exact_accepted_parent_bound": True,
            "exact_green_compact_east_candidate_bound": True,
            "all_68_parent_candidate_pairs_present": True,
            "path_eye_remains_non_observing_all_17_phases_both_weather_modes": True,
            "elevated_oblique_observes_all_15_interior_phases_both_weather_modes": True,
            "neutral_phases_00_16_pixel_exact_to_parent": True,
            "all_observed_compact_east_delta_inside_fixed_receiver_envelope": True,
            "outside_receiver_negative_control_rejected": negative_control_rejected,
        },
        "truth_boundary": (
            "Derived review surface from exact retained Godot current-world parent/candidate frames. "
            "It isolates the raster consequence of adding the compact-east visual response while Weather mode, west sapling, Building, Object, rear Nature, route, cameras and lighting stay inherited from the exact retained evidence. "
            "The x8 absolute-difference boards are diagnostic amplification only, not an authored look. "
            "This proves effect observability/readability in one fixed retained camera and preserves the explicit non-observing camera; it does not establish naturalness, preference, continuous wall-clock playback, physical wind/biomechanics, gameplay/physics, target-device performance, CANON or production readiness."
        ),
        "non_claims": [
            "ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "NATURAL_OR_DESIRABLE_MOTION",
            "CONTINUOUS_WALL_CLOCK_PLAYBACK",
            "PHYSICAL_WIND_FORCE_TURBULENCE_OR_BIOMECHANICS",
            "GAMEPLAY_COLLISION_DAMAGE_OR_NAVIGATION",
            "TARGET_DEVICE_PERFORMANCE",
            "CANON_OR_PRODUCTION_READINESS",
        ],
    }
    if not all(report["checks"].values()):
        raise ValueError("effect readability review checks failed")
    (output_root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.parent_root, args.candidate_root, args.output)
    print(json.dumps({
        "state": report["state"],
        "receiver_bbox": report["observed_receiver_union_bbox_xyxy"],
        "control_changed": [r["changed_pixels"] for r in report["metrics"]["control"]["elevated_oblique"]],
        "candidate_changed": [r["changed_pixels"] for r in report["metrics"]["candidate"]["elevated_oblique"]],
    }, indent=2))


if __name__ == "__main__":
    main()
