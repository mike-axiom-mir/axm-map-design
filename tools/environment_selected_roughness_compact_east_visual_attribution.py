from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageOps

SCHEMA = "axm.environment-selected-roughness-compact-east-visual-attribution/v0.1"
RESULT = "PASS_CURRENT_WORLD_SELECTED_ROUGHNESS_COMPACT_EAST_VISUAL_ATTRIBUTION__DUAL_ADOPTION_HELD"
RULE = "SEQUENTIAL_WORLD_CANDIDATES_REQUIRE_PIXEL_ATTRIBUTION_AGAINST_EXACT_RETAINED_PARENTS_BEFORE_COMBINED_ADOPTION"

UV0_HEAD = "4eed6da68f746ca2849c89fa88533f82bc836b26"
UV0_STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACE_UV0_BOUND__ROUGHNESS_ADOPTION_HELD"
UV0_ARTIFACT = 10501901585
UV0_ARCHIVE_SHA256 = "a3e3c3adc794877d84f3735f4f4ff69e3120843588da5c8aaa259d7ab7b965e3"

ROUGHNESS_HEAD = "d8a1d950ed5f21e6ad356404f46407c99c160017"
ROUGHNESS_STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_APPEARANCE_CANDIDATE_REVIEW_READY__ENVIRONMENT_ADOPTION_HELD"
ROUGHNESS_ARTIFACT = 10502588586
ROUGHNESS_ARCHIVE_SHA256 = "60c1e589e3e1c3a7dab5430b55ef59542dd7ca35dad8b13653d165c79eee3a1e"

COMBINED_HEAD = "4bd7eaf6970716dde4159448c92556785f47e954"
COMBINED_STATE = "PASS_CURRENT_WORLD_SELECTED_ROUGHNESS_PLUS_COMPACT_EAST_COMPOSITION_REVIEW_READY__DUAL_ADOPTION_HELD"
COMBINED_ARTIFACT = 10509037278
COMBINED_ARCHIVE_SHA256 = "8f2f8aa4bb11e2f868a6ce36dd381933ba1ea6c59be7b82ed00d1dfe5402ee97"

EXPECTED_FRAME_COUNT = 68
EXPECTED_ROUGHNESS_RAW_PIXELS = 6426
EXPECTED_ROUGHNESS_GT1_PIXELS = 1666
EXPECTED_ROUGHNESS_MAX_LSB = 7
EXPECTED_COMPACT_SEQUENTIAL_RAW_PIXELS = 197697
EXPECTED_COMPACT_SEQUENTIAL_GT1_PIXELS = 185888
EXPECTED_COMPACT_SEQUENTIAL_MAX_LSB = 191


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def frame_files(root: Path) -> dict[str, Path]:
    rendered = root / "candidate" / "rendered"
    files = {p.name: p for p in rendered.glob("atmosphere-width-*.png")}
    if len(files) != EXPECTED_FRAME_COUNT:
        raise ValueError(f"expected {EXPECTED_FRAME_COUNT} retained frames in {rendered}, got {len(files)}")
    return files


def max_channel_mask(a: Image.Image, b: Image.Image) -> tuple[Image.Image, Image.Image, int]:
    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    r, g, bl = diff.split()
    maximum = ImageChops.lighter(ImageChops.lighter(r, g), bl)
    changed = maximum.point(lambda value: 255 if value else 0)
    gt1 = maximum.point(lambda value: 255 if value > 1 else 0)
    extrema = diff.getextrema()
    max_lsb = max(channel[1] for channel in extrema)
    return changed, gt1, max_lsb


def count_mask(mask: Image.Image) -> int:
    hist = mask.histogram()
    return int(sum(hist[1:]))


def union_bbox(current: tuple[int, int, int, int] | None, new: tuple[int, int, int, int] | None):
    if new is None:
        return current
    if current is None:
        return new
    return (
        min(current[0], new[0]),
        min(current[1], new[1]),
        max(current[2], new[2]),
        max(current[3], new[3]),
    )


def parse_frame_name(name: str) -> tuple[str, str, int]:
    stem = Path(name).stem
    prefix = "atmosphere-width-"
    if not stem.startswith(prefix):
        raise ValueError(f"unexpected retained frame name {name}")
    tail = stem[len(prefix):]
    mode, rest = tail.split("-", 1)
    context, phase_text = rest.rsplit("-", 1)
    if mode not in {"control", "candidate"} or context not in {"path_eye", "elevated_oblique"}:
        raise ValueError(f"unexpected retained frame identity {name}")
    phase = int(phase_text)
    if phase < 0 or phase > 16:
        raise ValueError(f"unexpected phase in {name}")
    return mode, context, phase


def verify_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema") != SCHEMA:
        raise ValueError("visual-attribution contract schema drift")
    if contract.get("reusable_rule") != RULE:
        raise ValueError("visual-attribution reusable rule drift")
    exact = contract.get("exact_retained_evidence", {})
    expected = {
        "uv0_parent": (UV0_HEAD, UV0_ARTIFACT, UV0_ARCHIVE_SHA256),
        "roughness_only": (ROUGHNESS_HEAD, ROUGHNESS_ARTIFACT, ROUGHNESS_ARCHIVE_SHA256),
        "roughness_plus_compact_east": (COMBINED_HEAD, COMBINED_ARTIFACT, COMBINED_ARCHIVE_SHA256),
    }
    for key, (head, artifact, digest) in expected.items():
        row = exact.get(key, {})
        if row.get("head") != head or row.get("artifact_id") != artifact or row.get("archive_sha256") != digest:
            raise ValueError(f"exact retained evidence drift for {key}")
    decision = contract.get("decision", {})
    if decision.get("environment_selected_roughness_adoption") is not False:
        raise ValueError("selected roughness adoption must remain held")
    if decision.get("environment_compact_east_adoption") is not False:
        raise ValueError("compact-east adoption must remain held")
    if decision.get("art_qa_acceptance_required") is not True:
        raise ValueError("Art/QA acceptance boundary drift")
    if decision.get("runtime_acceptance_required") is not True:
        raise ValueError("Runtime acceptance boundary drift")


def verify_owner_reports(uv0_root: Path, roughness_root: Path, combined_root: Path) -> None:
    uv0 = load(uv0_root / "selected-uv0-report.json")
    if uv0.get("environment_head") != UV0_HEAD or uv0.get("state") != UV0_STATE or uv0.get("environment_adoption") is not False:
        raise ValueError("UV0 retained parent report drift")

    roughness = load(roughness_root / "selected-roughness-report.json")
    if roughness.get("environment_head") != ROUGHNESS_HEAD or roughness.get("state") != ROUGHNESS_STATE:
        raise ValueError("selected-roughness retained report drift")
    if roughness.get("environment_adoption") is not False:
        raise ValueError("selected-roughness retained adoption boundary drift")

    combined = load(combined_root / "composition-report.json")
    if combined.get("environment_head") != COMBINED_HEAD or combined.get("state") != COMBINED_STATE:
        raise ValueError("combined retained composition report drift")
    if combined.get("environment_selected_roughness_adoption") is not False:
        raise ValueError("combined selected-roughness adoption boundary drift")
    if combined.get("environment_compact_east_adoption") is not False:
        raise ValueError("combined compact-east adoption boundary drift")
    scope = combined.get("real_world_scope", {})
    if scope.get("states") != 17 or scope.get("matched_target_host_frames") != 68:
        raise ValueError("combined real-world scope drift")


def make_review_board(
    uv0_path: Path,
    roughness_path: Path,
    combined_path: Path,
    roughness_mask: Image.Image,
    compact_mask: Image.Image,
    combined_mask: Image.Image,
    output: Path,
) -> None:
    a = Image.open(uv0_path).convert("RGB")
    b = Image.open(roughness_path).convert("RGB")
    d = Image.open(combined_path).convert("RGB")
    width, height = a.size
    label_h = 28
    canvas = Image.new("RGB", (width * 3, height * 2 + label_h * 2), (0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    panels = [(a, "UV0 parent"), (b, "roughness only"), (d, "roughness + compact-east")]
    for index, (image, label) in enumerate(panels):
        x = index * width
        draw.text((x + 8, 7), label, fill=(255, 255, 255))
        canvas.paste(image, (x, label_h))
    masks = [(roughness_mask, "roughness delta mask"), (compact_mask, "compact-east delta mask"), (combined_mask, "combined delta mask")]
    y0 = height + label_h
    for index, (mask, label) in enumerate(masks):
        x = index * width
        draw.text((x + 8, y0 + 7), label, fill=(255, 255, 255))
        canvas.paste(mask.convert("RGB"), (x, y0 + label_h))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def verify(args: argparse.Namespace) -> dict[str, Any]:
    contract = load(args.contract)
    verify_contract(contract)

    uv0_root = Path(args.uv0_root)
    roughness_root = Path(args.roughness_root)
    combined_root = Path(args.combined_root)
    verify_owner_reports(uv0_root, roughness_root, combined_root)

    uv0_files = frame_files(uv0_root)
    roughness_files = frame_files(roughness_root)
    combined_files = frame_files(combined_root)
    if set(uv0_files) != set(roughness_files) or set(uv0_files) != set(combined_files):
        raise ValueError("retained frame identity sets differ")

    totals = {
        "roughness": {"raw_changed_pixels": 0, "pixels_gt_1_lsb": 0, "max_lsb": 0, "bbox": None},
        "compact_sequential": {"raw_changed_pixels": 0, "pixels_gt_1_lsb": 0, "max_lsb": 0, "bbox": None},
        "combined": {"raw_changed_pixels": 0, "pixels_gt_1_lsb": 0, "max_lsb": 0, "bbox": None},
    }
    by_context: dict[str, dict[str, Any]] = {}
    overlap_pixels = 0
    emergent_pixels = 0
    missing_union_pixels = 0
    per_frame: list[dict[str, Any]] = []
    review_dir = Path(args.review_dir) if args.review_dir else None

    for name in sorted(uv0_files):
        mode, context, phase = parse_frame_name(name)
        a = Image.open(uv0_files[name]).convert("RGB")
        b = Image.open(roughness_files[name]).convert("RGB")
        d = Image.open(combined_files[name]).convert("RGB")
        if a.size != b.size or a.size != d.size:
            raise ValueError(f"frame dimensions drift at {name}")

        rough_mask, rough_gt1, rough_max = max_channel_mask(a, b)
        compact_mask, compact_gt1, compact_max = max_channel_mask(b, d)
        combined_mask, combined_gt1, combined_max = max_channel_mask(a, d)

        rough_count = count_mask(rough_mask)
        compact_count = count_mask(compact_mask)
        combined_count = count_mask(combined_mask)
        rough_gt1_count = count_mask(rough_gt1)
        compact_gt1_count = count_mask(compact_gt1)
        combined_gt1_count = count_mask(combined_gt1)

        union = ImageChops.lighter(rough_mask, compact_mask)
        overlap = ImageChops.darker(rough_mask, compact_mask)
        emergent = ImageChops.darker(combined_mask, ImageOps.invert(union))
        missing = ImageChops.darker(union, ImageOps.invert(combined_mask))

        frame_overlap = count_mask(overlap)
        frame_emergent = count_mask(emergent)
        frame_missing = count_mask(missing)
        overlap_pixels += frame_overlap
        emergent_pixels += frame_emergent
        missing_union_pixels += frame_missing

        for key, mask, count, gt1_count, max_lsb in (
            ("roughness", rough_mask, rough_count, rough_gt1_count, rough_max),
            ("compact_sequential", compact_mask, compact_count, compact_gt1_count, compact_max),
            ("combined", combined_mask, combined_count, combined_gt1_count, combined_max),
        ):
            totals[key]["raw_changed_pixels"] += count
            totals[key]["pixels_gt_1_lsb"] += gt1_count
            totals[key]["max_lsb"] = max(totals[key]["max_lsb"], max_lsb)
            totals[key]["bbox"] = union_bbox(totals[key]["bbox"], mask.getbbox())

        context_key = f"{context}:{mode}"
        row = by_context.setdefault(
            context_key,
            {
                "frames": 0,
                "roughness_raw_changed_pixels": 0,
                "compact_sequential_raw_changed_pixels": 0,
                "combined_raw_changed_pixels": 0,
                "roughness_bbox": None,
                "compact_bbox": None,
            },
        )
        row["frames"] += 1
        row["roughness_raw_changed_pixels"] += rough_count
        row["compact_sequential_raw_changed_pixels"] += compact_count
        row["combined_raw_changed_pixels"] += combined_count
        row["roughness_bbox"] = union_bbox(row["roughness_bbox"], rough_mask.getbbox())
        row["compact_bbox"] = union_bbox(row["compact_bbox"], compact_mask.getbbox())

        per_frame.append(
            {
                "name": name,
                "mode": mode,
                "context": context,
                "phase": phase,
                "roughness_raw_changed_pixels": rough_count,
                "compact_sequential_raw_changed_pixels": compact_count,
                "combined_raw_changed_pixels": combined_count,
                "roughness_compact_overlap_pixels": frame_overlap,
                "combined_emergent_outside_sequential_union_pixels": frame_emergent,
                "sequential_union_missing_from_combined_pixels": frame_missing,
            }
        )

        if review_dir is not None and context == "elevated_oblique" and phase == 8:
            make_review_board(
                uv0_files[name],
                roughness_files[name],
                combined_files[name],
                rough_mask,
                compact_mask,
                combined_mask,
                review_dir / f"attribution-{mode}-elevated_oblique-08.png",
            )

    rough = totals["roughness"]
    compact = totals["compact_sequential"]

    # Attribution is checked before exact visual-identity pins so the negative control
    # proves the cross-asset boundary itself fails closed.
    if overlap_pixels != 0:
        raise ValueError(f"retained roughness and compact-east raster contributions overlap at {overlap_pixels} pixels")
    if emergent_pixels != 0:
        raise ValueError(f"combined world contains {emergent_pixels} unexplained pixels outside sequential contribution union")
    if missing_union_pixels != 0:
        raise ValueError(f"combined world suppresses {missing_union_pixels} pixels from sequential contribution union")

    # Bind the exact previously retained owner evidence instead of letting a later archive
    # with different pixels pass under the same labels.
    if rough["raw_changed_pixels"] != EXPECTED_ROUGHNESS_RAW_PIXELS:
        raise ValueError(f"roughness raw-pixel identity drift: {rough['raw_changed_pixels']}")
    if rough["pixels_gt_1_lsb"] != EXPECTED_ROUGHNESS_GT1_PIXELS or rough["max_lsb"] != EXPECTED_ROUGHNESS_MAX_LSB:
        raise ValueError("roughness retained visual identity drift")
    if compact["raw_changed_pixels"] != EXPECTED_COMPACT_SEQUENTIAL_RAW_PIXELS:
        raise ValueError(f"compact-east sequential raw-pixel identity drift: {compact['raw_changed_pixels']}")
    if compact["pixels_gt_1_lsb"] != EXPECTED_COMPACT_SEQUENTIAL_GT1_PIXELS or compact["max_lsb"] != EXPECTED_COMPACT_SEQUENTIAL_MAX_LSB:
        raise ValueError("compact-east retained visual identity drift")

    combined = totals["combined"]
    if combined["raw_changed_pixels"] != rough["raw_changed_pixels"] + compact["raw_changed_pixels"]:
        raise ValueError("combined changed-pixel total is not the exact disjoint sum of retained contributions")

    report = {
        "schema": SCHEMA,
        "state": RESULT,
        "environment_head": args.environment_head,
        "reusable_rule": RULE,
        "evidence_mode": "DERIVED_FROM_THREE_EXACT_RETAINED_REAL_GODOT_CURRENT_WORLD_ARTIFACTS__NO_RERENDER_OR_SOURCE_MUTATION",
        "exact_retained_evidence": {
            "uv0_parent": {"head": UV0_HEAD, "artifact_id": UV0_ARTIFACT, "archive_sha256": UV0_ARCHIVE_SHA256},
            "roughness_only": {"head": ROUGHNESS_HEAD, "artifact_id": ROUGHNESS_ARTIFACT, "archive_sha256": ROUGHNESS_ARCHIVE_SHA256},
            "roughness_plus_compact_east": {"head": COMBINED_HEAD, "artifact_id": COMBINED_ARTIFACT, "archive_sha256": COMBINED_ARCHIVE_SHA256},
        },
        "real_world_scope": {
            "states": 17,
            "matched_frames": EXPECTED_FRAME_COUNT,
            "contexts": ["path_eye", "elevated_oblique"],
            "weather_review_modes": ["control", "candidate"],
            "assets_present": ["Building", "Nature west-sapling", "Nature compact-east", "Object selected roughness", "Map footprint cue", "Weather source-width presentation"],
        },
        "pixel_attribution": {
            "roughness_vs_uv0_parent": rough,
            "compact_east_added_after_roughness": compact,
            "combined_vs_uv0_parent": combined,
            "roughness_compact_overlap_pixels": overlap_pixels,
            "combined_emergent_outside_sequential_union_pixels": emergent_pixels,
            "sequential_union_missing_from_combined_pixels": missing_union_pixels,
            "exact_disjoint_union": overlap_pixels == 0 and emergent_pixels == 0 and missing_union_pixels == 0,
        },
        "by_context": by_context,
        "per_frame": per_frame,
        "environment_selected_roughness_adoption": False,
        "environment_compact_east_adoption": False,
        "art_qa_acceptance_required": True,
        "runtime_acceptance_required": True,
        "truth_boundary": (
            "This PASS proves exact pixel attribution only for the three pinned retained Godot current-world artifacts. "
            "The selected-roughness delta and the subsequently stacked compact-east delta occupy disjoint retained pixels, "
            "and the final combined raster is their exact changed-pixel union against the UV0 parent. It does not prove "
            "continuous playback, arbitrary cameras/lights, target-device performance, final aesthetic preference, physical wind, CANON or production readiness."
        ),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--uv0-root", required=True)
    parser.add_argument("--roughness-root", required=True)
    parser.add_argument("--combined-root", required=True)
    parser.add_argument("--environment-head", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--review-dir")
    args = parser.parse_args()
    report = verify(args)
    print(report["state"])


if __name__ == "__main__":
    main()
