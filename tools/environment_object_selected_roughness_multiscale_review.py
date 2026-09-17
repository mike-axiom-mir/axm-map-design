from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SCHEMA = "axm.environment-object-selected-roughness-multiscale-review/v0.1"
RESULT_SCHEMA = "axm.environment-object-selected-roughness-multiscale-review-result/v0.1"
STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_MULTI_SCALE_REVIEW_SURFACE__APPEARANCE_ACCEPTANCE_HELD"
SOURCE_STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_APPEARANCE_CANDIDATE_REVIEW_READY__ENVIRONMENT_ADOPTION_HELD"
RULE = "SUBTLE_WORLD_SURFACE_CHANGE_REVIEW_SHOULD_PRESERVE_FULL_SCENE_AUTHORITY_AND_ADD_DERIVED_MULTI_SCALE_INSPECTION_WITHOUT_REAUTHORING_CAMERA_LIGHT_OR_ASSET_STATE"
SOURCE_HEAD = "d8a1d950ed5f21e6ad356404f46407c99c160017"
PARENT_HEAD = "4eed6da68f746ca2849c89fa88533f82bc836b26"
EXPECTED_RAW_TOTAL = 6426
EXPECTED_GT1_TOTAL = 1666
EXPECTED_MAX_LSB = 7
EXPECTED_FRAMES = 68
EXPECTED_ENVELOPES = {
    "path_eye": [314, 440, 342, 448],
    "elevated_oblique": [549, 307, 559, 313],
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frame_name(name: str) -> tuple[str, str, int]:
    stem = name.removesuffix(".png")
    prefix = "atmosphere-width-"
    if not stem.startswith(prefix):
        raise ValueError(f"unexpected frame name: {name}")
    mode, tail = stem[len(prefix):].split("-", 1)
    context, state = tail.rsplit("-", 1)
    return mode, context, int(state)


def frame_map(root: Path) -> dict[str, Path]:
    return {p.name: p for p in root.glob("atmosphere-width-*.png")}


def bbox(mask: np.ndarray) -> list[int] | None:
    if not np.any(mask):
        return None
    ys, xs = np.where(mask)
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def contains(outer: list[int], inner: list[int] | None) -> bool:
    if inner is None:
        return True
    return outer[0] <= inner[0] and outer[1] <= inner[1] and outer[2] >= inner[2] and outer[3] >= inner[3]


def expand(box: list[int], padding: int, width: int, height: int) -> list[int]:
    return [max(0, box[0] - padding), max(0, box[1] - padding), min(width - 1, box[2] + padding), min(height - 1, box[3] + padding)]


def crop_inclusive(image: Image.Image, box: list[int]) -> Image.Image:
    return image.crop((box[0], box[1], box[2] + 1, box[3] + 1))


def fit_panel(image: Image.Image, size: tuple[int, int], nearest: bool = False) -> Image.Image:
    resample = Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS
    clone = image.copy()
    clone.thumbnail(size, resample=resample)
    canvas = Image.new("RGB", size, (24, 24, 24))
    canvas.paste(clone.convert("RGB"), ((size[0] - clone.width) // 2, (size[1] - clone.height) // 2))
    return canvas


def labelled(panel: Image.Image, label: str) -> Image.Image:
    header = 24
    out = Image.new("RGB", (panel.width, panel.height + header), (16, 16, 16))
    out.paste(panel, (0, header))
    ImageDraw.Draw(out).text((6, 6), label, fill=(235, 235, 235), font=ImageFont.load_default())
    return out


def make_sheet(parent: Image.Image, candidate: Image.Image, delta: np.ndarray, context: str, mode: str, state: int,
               local_box: list[int], neighborhood_box: list[int], amplification: int, output: Path) -> None:
    size = (300, 196)
    delta_image = Image.fromarray(np.clip(delta * amplification, 0, 255).astype(np.uint8), mode="RGB")
    panels = [
        labelled(fit_panel(parent, size), "parent full scene"),
        labelled(fit_panel(candidate, size), "candidate full scene"),
        labelled(fit_panel(crop_inclusive(candidate, neighborhood_box), size, nearest=True), "candidate neighborhood"),
        labelled(fit_panel(crop_inclusive(parent, local_box), size, nearest=True), "parent local"),
        labelled(fit_panel(crop_inclusive(candidate, local_box), size, nearest=True), "candidate local"),
        labelled(fit_panel(crop_inclusive(delta_image, local_box), size, nearest=True), f"abs diff x{amplification}"),
    ]
    margin, title_h, cols = 8, 30, 3
    cell_w, cell_h = max(p.width for p in panels), max(p.height for p in panels)
    sheet = Image.new("RGB", (margin + cols * (cell_w + margin), title_h + margin + 2 * (cell_h + margin)), (12, 12, 12))
    ImageDraw.Draw(sheet).text((margin, 8), f"derived review only | {mode} | {context} | state {state:02d}", fill=(240, 240, 240), font=ImageFont.load_default())
    for index, panel in enumerate(panels):
        row, col = divmod(index, cols)
        sheet.paste(panel, (margin + col * (cell_w + margin), title_h + margin + row * (cell_h + margin)))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def verify_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema") != SCHEMA:
        raise ValueError("multiscale review contract schema drift")
    if contract.get("source_environment_head") != SOURCE_HEAD or contract.get("parent_environment_head") != PARENT_HEAD:
        raise ValueError("multiscale review Environment lineage drift")
    if contract.get("source_state") != SOURCE_STATE or contract.get("reusable_rule") != RULE:
        raise ValueError("multiscale review state/rule drift")
    if contract.get("localized_raw_delta_envelopes") != EXPECTED_ENVELOPES:
        raise ValueError("multiscale review localized envelope drift")
    review = contract.get("review", {})
    if review.get("environment_adoption") is not False or review.get("art_qa_acceptance_required") is not True or review.get("runtime_acceptance_required") is not True:
        raise ValueError("multiscale review authority boundary drift")
    if review.get("derived_review_only") is not True or review.get("preserve_original_full_frames") is not True:
        raise ValueError("multiscale review derived-only boundary drift")


def verify_candidate_report(report: dict[str, Any]) -> None:
    if report.get("environment_head") != SOURCE_HEAD or report.get("parent_environment_head") != PARENT_HEAD:
        raise ValueError("selected roughness source report Environment identity drift")
    if report.get("state") != SOURCE_STATE or report.get("environment_adoption") is not False:
        raise ValueError("selected roughness source report state/adoption drift")
    appearance = report.get("real_scene_appearance_delta", {})
    if appearance.get("matched_frames") != EXPECTED_FRAMES:
        raise ValueError("selected roughness source report frame count drift")
    if appearance.get("changed_pixels_raw_total") != EXPECTED_RAW_TOTAL or appearance.get("changed_pixels_gt_1lsb_total") != EXPECTED_GT1_TOTAL or appearance.get("maximum_channel_delta_lsb") != EXPECTED_MAX_LSB:
        raise ValueError("selected roughness source report raster summary drift")
    weather = report.get("weather_width_continuity", {})
    if weather.get("measurements") != 1224 or float(weather.get("maximum_projected_width_residual_px", 999.0)) > 0.05:
        raise ValueError("selected roughness source report Weather continuity drift")


def run(args: argparse.Namespace) -> dict[str, Any]:
    contract = load(Path(args.contract))
    verify_contract(contract)
    source_report = load(Path(args.candidate_report))
    verify_candidate_report(source_report)
    parent, candidate = frame_map(Path(args.parent_rendered)), frame_map(Path(args.candidate_rendered))
    if len(parent) != EXPECTED_FRAMES or set(parent) != set(candidate):
        raise ValueError(f"multiscale review requires exact 68-frame A/B; parent={len(parent)} candidate={len(candidate)}")

    output = Path(args.output_dir)
    sheets = output / "review-sheets"
    output.mkdir(parents=True, exist_ok=True)
    representative_states = set(int(v) for v in contract["review"]["representative_states"])
    local_padding = int(contract["review"]["local_padding_px"])
    neighborhood_padding = int(contract["review"]["neighborhood_padding_px"])
    amplification = int(contract["review"]["difference_amplification"])
    aggregate: dict[str, Any] = {}
    raw_total = gt1_total = max_lsb = 0
    generated: list[str] = []
    inject_target = sorted(candidate)[0] if args.inject_outside_delta else None

    for name in sorted(parent):
        mode, context, state = parse_frame_name(name)
        if context not in EXPECTED_ENVELOPES:
            raise ValueError(f"unexpected review context: {context}")
        a_img, b_img = Image.open(parent[name]).convert("RGBA"), Image.open(candidate[name]).convert("RGBA")
        if a_img.size != (1100, 720) or b_img.size != a_img.size:
            raise ValueError(f"full-scene frame dimensions drift: {name}")
        a, b = np.asarray(a_img, dtype=np.int16), np.asarray(b_img, dtype=np.int16).copy()
        if name == inject_target:
            old = int(b[10, 10, 0])
            b[10, 10, 0] = old - 12 if old >= 244 else old + 12
        delta = np.abs(a[:, :, :3] - b[:, :, :3])
        raw_mask, gt1_mask = np.any(delta > 0, axis=2), np.any(delta > 1, axis=2)
        raw, gt1, frame_max = int(raw_mask.sum()), int(gt1_mask.sum()), int(delta.max(initial=0))
        raw_box, expected = bbox(raw_mask), EXPECTED_ENVELOPES[context]
        if not contains(expected, raw_box):
            raise ValueError(f"selected roughness raster change escaped localized Environment envelope: {name} bbox={raw_box} expected={expected}")
        key = f"{mode}/{context}"
        item = aggregate.setdefault(key, {"frames": 0, "raw_changed_pixels": 0, "gt1_changed_pixels": 0, "maximum_channel_delta_lsb": 0, "raw_envelope": expected})
        item["frames"] += 1
        item["raw_changed_pixels"] += raw
        item["gt1_changed_pixels"] += gt1
        item["maximum_channel_delta_lsb"] = max(item["maximum_channel_delta_lsb"], frame_max)
        raw_total, gt1_total, max_lsb = raw_total + raw, gt1_total + gt1, max(max_lsb, frame_max)
        if state in representative_states:
            local_box = expand(expected, local_padding, a_img.width, a_img.height)
            neighborhood_box = expand(expected, neighborhood_padding, a_img.width, a_img.height)
            sheet_name = f"review-{mode}-{context}-state-{state:02d}.png"
            make_sheet(a_img.convert("RGB"), Image.fromarray(b.astype(np.uint8), mode="RGBA").convert("RGB"), delta, context, mode, state,
                       local_box, neighborhood_box, amplification, sheets / sheet_name)
            generated.append(f"review-sheets/{sheet_name}")

    if raw_total != EXPECTED_RAW_TOTAL or gt1_total != EXPECTED_GT1_TOTAL or max_lsb != EXPECTED_MAX_LSB:
        raise ValueError(f"selected roughness exact raster totals drift: raw={raw_total} gt1={gt1_total} max={max_lsb}")
    if len(generated) != 12:
        raise ValueError(f"expected 12 representative multiscale review sheets, got {len(generated)}")

    report = {
        "schema": RESULT_SCHEMA,
        "state": STATE,
        "review_head": args.review_head,
        "source_environment_head": SOURCE_HEAD,
        "parent_environment_head": PARENT_HEAD,
        "reusable_rule": RULE,
        "evidence_identity": {k: contract["evidence"][k] for k in ("parent_artifact_id", "parent_artifact_sha256", "candidate_artifact_id", "candidate_artifact_sha256", "candidate_run_id")},
        "full_scene_proof": {
            "matched_frames": EXPECTED_FRAMES,
            "frame_dimensions": [1100, 720],
            "changed_pixels_raw_total": raw_total,
            "changed_pixels_gt_1lsb_total": gt1_total,
            "maximum_channel_delta_lsb": max_lsb,
            "localized_raw_delta_envelopes": EXPECTED_ENVELOPES,
            "weather_width_measurements": 1224,
            "weather_maximum_projected_width_residual_px": source_report["weather_width_continuity"]["maximum_projected_width_residual_px"],
            "building_nature_object_footprint_weather_scene_inherited": True,
        },
        "derived_review_surface": {
            "representative_states": sorted(representative_states),
            "modes_and_contexts": sorted(aggregate),
            "sheet_count": len(generated),
            "sheets": generated,
            "difference_amplification": amplification,
            "original_frames_unchanged": True,
            "new_camera_or_light_authorship": False,
            "new_asset_state_authorship": False,
        },
        "aggregate": aggregate,
        "environment_adoption": False,
        "art_qa_acceptance_required": True,
        "runtime_acceptance_required": True,
        "truth_boundary": "This pass adds only deterministic multi-scale inspection of the exact retained real-Godot current-world A/B. It does not rerender, crop-replace, retune, or reinterpret the original full-scene evidence; amplified difference panels are diagnostic only. Art/QA still own appearance acceptance and Runtime still owns representation/device acceptance.",
    }
    (output / "multiscale-review-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--candidate-report", required=True)
    parser.add_argument("--parent-rendered", required=True)
    parser.add_argument("--candidate-rendered", required=True)
    parser.add_argument("--review-head", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--inject-outside-delta", action="store_true")
    args = parser.parse_args()
    result = run(args)
    print(json.dumps({"state": result["state"], "sheets": result["derived_review_surface"]["sheet_count"], "raw": result["full_scene_proof"]["changed_pixels_raw_total"], "gt1": result["full_scene_proof"]["changed_pixels_gt_1lsb_total"], "max_lsb": result["full_scene_proof"]["maximum_channel_delta_lsb"], "environment_adoption": result["environment_adoption"]}, sort_keys=True))


if __name__ == "__main__":
    main()
