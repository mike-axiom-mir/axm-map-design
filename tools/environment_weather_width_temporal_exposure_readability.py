from __future__ import annotations

import argparse
import copy
import json
import statistics
from pathlib import Path
from typing import Any

try:
    from . import environment_weather_width_temporal_exposure_normalized as normalized
except ImportError:
    import environment_weather_width_temporal_exposure_normalized as normalized

legacy = normalized.legacy

SCHEMA = "axm.environment-current-world-weather-width-temporal-exposure-readability-review/v0.1"
STATUS = "PASS_OPACITY_NORMALIZED_TEMPORAL_EXPOSURE_READABILITY_REVIEW_SURFACE"
DECISION = "REVIEW_SURFACE_ONLY_NO_ART_OR_QA_PREFERENCE"
PAIR_COUNT = len(legacy.CONTEXTS) * len(legacy.REVIEW_PHASES_US)


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _pair_metrics(raw_control: Path, raw_candidate: Path) -> dict[str, Any]:
    control = raw_control.read_bytes()
    candidate = raw_candidate.read_bytes()
    if len(control) != legacy.RAW_BYTES or len(candidate) != legacy.RAW_BYTES:
        raise ValueError("unexpected RGBA8 frame byte count")

    changed = 0
    abs_rgb = 0
    max_channel = 0
    min_x = legacy.WIDTH
    min_y = legacy.HEIGHT
    max_x = -1
    max_y = -1
    sum_x = 0
    sum_y = 0

    for offset in range(0, legacy.RAW_BYTES, 4):
        dr = abs(control[offset] - candidate[offset])
        dg = abs(control[offset + 1] - candidate[offset + 1])
        db = abs(control[offset + 2] - candidate[offset + 2])
        if not (dr or dg or db):
            continue
        pixel_index = offset // 4
        x = pixel_index % legacy.WIDTH
        y = pixel_index // legacy.WIDTH
        changed += 1
        abs_rgb += dr + dg + db
        max_channel = max(max_channel, dr, dg, db)
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)
        sum_x += x
        sum_y += y

    if changed:
        bbox = [min_x, min_y, max_x, max_y]
        bbox_pixels = (max_x - min_x + 1) * (max_y - min_y + 1)
        centroid = [sum_x / changed, sum_y / changed]
        bbox_fill_ratio = changed / float(bbox_pixels)
    else:
        bbox = None
        centroid = None
        bbox_fill_ratio = 0.0

    return {
        "changed_pixels": changed,
        "changed_fraction": changed / float(legacy.WIDTH * legacy.HEIGHT),
        "mean_abs_rgb_lsb": abs_rgb / float(legacy.WIDTH * legacy.HEIGHT * 3),
        "maximum_rgb_channel_delta_lsb": max_channel,
        "changed_pixel_bbox_xyxy": bbox,
        "changed_pixel_centroid_xy": centroid,
        "changed_pixel_bbox_fill_ratio": bbox_fill_ratio,
    }


def _write_svg(report: dict[str, Any], path: str | Path) -> None:
    width = 960
    height = 440
    margin_left = 82
    margin_right = 28
    margin_top = 54
    margin_bottom = 72
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom

    rows: list[tuple[str, list[dict[str, Any]]]] = []
    max_fraction = 0.0
    for context in legacy.CONTEXTS:
        samples = report.get("contexts", {}).get(context, {}).get("samples", [])
        rows.append((context, samples))
        for sample in samples:
            max_fraction = max(max_fraction, float(sample.get("changed_fraction", 0.0)))
    if max_fraction <= 0.0:
        max_fraction = 1.0

    def x_for(index: int) -> float:
        count = len(legacy.REVIEW_PHASES_US)
        return margin_left + (chart_w * index / float(max(1, count - 1)))

    def y_for(value: float) -> float:
        return margin_top + chart_h * (1.0 - value / max_fraction)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="30" font-family="sans-serif" font-size="18">Opacity-normalized Weather temporal-exposure readability review</text>',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + chart_h}" stroke="black"/>',
        f'<line x1="{margin_left}" y1="{margin_top + chart_h}" x2="{margin_left + chart_w}" y2="{margin_top + chart_h}" stroke="black"/>',
        f'<text x="16" y="{margin_top + 14}" font-family="sans-serif" font-size="12">changed</text>',
        f'<text x="16" y="{margin_top + 30}" font-family="sans-serif" font-size="12">fraction</text>',
        f'<text x="{margin_left + chart_w / 2 - 42}" y="{height - 20}" font-family="sans-serif" font-size="12">review phase (ms)</text>',
    ]
    patterns = ("", 'stroke-dasharray="8 5"')
    labels_y = 54
    for row_index, (context, samples) in enumerate(rows):
        points = []
        for index, sample in enumerate(samples):
            points.append(f"{x_for(index):.2f},{y_for(float(sample.get('changed_fraction', 0.0))):.2f}")
        dash = patterns[row_index % len(patterns)]
        parts.append(
            f'<polyline fill="none" stroke="black" stroke-width="2" {dash} points="{" ".join(points)}"/>'
        )
        parts.append(
            f'<text x="{width - 220}" y="{labels_y + row_index * 18}" font-family="sans-serif" font-size="12">{context}</text>'
        )

    for index, phase_us in enumerate(legacy.REVIEW_PHASES_US):
        x = x_for(index)
        parts.append(
            f'<line x1="{x:.2f}" y1="{margin_top + chart_h}" x2="{x:.2f}" y2="{margin_top + chart_h + 5}" stroke="black"/>'
        )
        parts.append(
            f'<text x="{x - 12:.2f}" y="{margin_top + chart_h + 22}" font-family="sans-serif" font-size="10">{phase_us / 1000:g}</text>'
        )

    parts.append(
        f'<text x="{margin_left}" y="{height - 44}" font-family="sans-serif" font-size="11">Review-only raster attribution; no aesthetic preference or smoothing claim.</text>'
    )
    parts.append("</svg>")
    Path(path).write_text("\n".join(parts) + "\n", encoding="utf-8")


def verify_readability_review(
    payload: dict[str, Any],
    receipt: dict[str, Any],
    normalized_report: dict[str, Any],
    image_root: str | Path,
) -> dict[str, Any]:
    root = Path(image_root)
    recomputed = normalized.verify_opacity_normalized_exposure(payload, receipt, root)
    contexts = receipt.get("contexts", {})

    report_identity_ok = (
        normalized_report.get("state") == normalized.STATUS
        and normalized_report.get("receiving_head") == payload.get("receiving_head")
        and normalized_report.get("presentation_policy") == normalized.POLICY
        and all(normalized_report.get("checks", {}).values())
    )
    normalized_contract_ok = (
        recomputed.get("state") == normalized.STATUS
        and all(recomputed.get("checks", {}).values())
    )

    context_reports: dict[str, Any] = {}
    all_pairs_measured = True
    all_after_start_visible = True
    pair_count = 0

    for context in legacy.CONTEXTS:
        samples = contexts.get(context, {}).get("samples", [])
        sample_reports: list[dict[str, Any]] = []
        if len(samples) != len(legacy.REVIEW_PHASES_US):
            all_pairs_measured = False
            all_after_start_visible = False
            context_reports[context] = {"samples": sample_reports}
            continue

        for index, sample in enumerate(samples):
            phase_us = int(sample.get("phase_us", -1))
            control_frame = sample.get("control_frame", {})
            candidate_frame = sample.get("candidate_frame", {})
            if (
                phase_us != legacy.REVIEW_PHASES_US[index]
                or not legacy._verify_frame(control_frame, root)
                or not legacy._verify_frame(candidate_frame, root)
            ):
                all_pairs_measured = False
                sample_reports.append({"phase_us": phase_us, "state": "FAIL_FRAME_OR_PHASE_IDENTITY"})
                continue

            metrics = _pair_metrics(
                root / str(control_frame["raw_path"]),
                root / str(candidate_frame["raw_path"]),
            )
            pair_count += 1
            if index > 0 and int(metrics["changed_pixels"]) <= 0:
                all_after_start_visible = False
            sample_reports.append(
                {
                    "phase_us": phase_us,
                    "state": "PASS_MEASURED_PAIR",
                    **metrics,
                }
            )

        measured = [row for row in sample_reports if row.get("state") == "PASS_MEASURED_PAIR"]
        changed_values = [int(row["changed_pixels"]) for row in measured]
        fraction_values = [float(row["changed_fraction"]) for row in measured]
        nonzero = [row for row in measured if int(row["changed_pixels"]) > 0]
        peak = max(nonzero, key=lambda row: int(row["changed_pixels"])) if nonzero else None
        union_boxes = [row["changed_pixel_bbox_xyxy"] for row in nonzero if row.get("changed_pixel_bbox_xyxy")]
        union_bbox = None
        if union_boxes:
            union_bbox = [
                min(box[0] for box in union_boxes),
                min(box[1] for box in union_boxes),
                max(box[2] for box in union_boxes),
                max(box[3] for box in union_boxes),
            ]

        context_reports[context] = {
            "samples": sample_reports,
            "pair_count": len(measured),
            "changed_pixels_mean": statistics.fmean(changed_values) if changed_values else 0.0,
            "changed_pixels_min": min(changed_values) if changed_values else 0,
            "changed_pixels_max": max(changed_values) if changed_values else 0,
            "changed_fraction_mean": statistics.fmean(fraction_values) if fraction_values else 0.0,
            "changed_fraction_max": max(fraction_values) if fraction_values else 0.0,
            "peak_changed_phase_us": int(peak["phase_us"]) if peak else None,
            "peak_changed_pixels": int(peak["changed_pixels"]) if peak else 0,
            "union_changed_pixel_bbox_xyxy": union_bbox,
        }

    phase0_report = normalized_report.get("phase0_metrics", {})
    phase0_equivalence_ok = (
        set(phase0_report) == set(legacy.CONTEXTS)
        and normalized_report.get("checks", {}).get(
            "phase0_direct_frame_is_brightness_equivalent_within_bound"
        ) is True
    )

    checks = {
        "opacity_normalized_candidate_contract_recomputes_green": normalized_contract_ok,
        "retained_normalized_report_matches_exact_receiving_identity": report_identity_ok,
        "all_18_fixed_context_review_pairs_are_hash_bound_and_measured": all_pairs_measured and pair_count == PAIR_COUNT,
        "zero_lag_brightness_equivalence_is_preserved": phase0_equivalence_ok,
        "every_nonzero_review_phase_has_direct_visual_delta": all_after_start_visible,
    }

    return {
        "schema": SCHEMA,
        "state": STATUS if all(checks.values()) else "FAIL",
        "decision": DECISION,
        "receiving_head": payload.get("receiving_head"),
        "presentation_policy": normalized.POLICY,
        "review_phases_us": list(legacy.REVIEW_PHASES_US),
        "contexts": context_reports,
        "checks": checks,
        "truth_boundary": (
            "PASS produces a deterministic effect-readability review surface from the already-rendered "
            "opacity-normalized Weather control/candidate pairs. It measures where and how much the candidate "
            "changes the retained raster, while leaving Weather source semantics, lag, tap weights, source width, "
            "density, cameras, lighting and world composition unchanged. These metrics do not establish perceptual "
            "smoothness, aesthetic preference, physical weather, gameplay or physics behavior, target-device "
            "performance, CANON, production readiness, or Art/Visual-QA acceptance."
        ),
    }


def exercise_identity_negative_control(
    payload: dict[str, Any],
    receipt: dict[str, Any],
    normalized_report: dict[str, Any],
    image_root: str | Path,
) -> dict[str, Any]:
    mutated = copy.deepcopy(normalized_report)
    mutated["receiving_head"] = "MUTATED_RECEIVING_HEAD"
    return verify_readability_review(payload, receipt, mutated, image_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--normalized-report", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--svg")
    args = parser.parse_args()

    report = verify_readability_review(
        _load(args.payload),
        _load(args.receipt),
        _load(args.normalized_report),
        args.image_root,
    )
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.svg:
        _write_svg(report, args.svg)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
