from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image

PARENT_ENV_HEAD = "ef2cb9cc84edc10ab66c2230daca625623e0b00d"
PARENT_RUN_ID = 35179857526
PARENT_ARTIFACT_ID = 10478624997
COMPACT_RUN_ID = 35179857530
COMPACT_ARTIFACT_ID = 10480305129
COMPACT_REPRESENTATION_ID = "boundary-only-union-shell-conforming-compact-v2-001"
EXPECTED_SAMPLE_COUNT = 17
EXPECTED_OBSERVATIONS = 68
EXPECTED_BUFFER_DELTA_BYTES = 106560
EXPECTED_PRIMITIVE_DELTA = 5328
SIGNIFICANT_LSB_THRESHOLD = 1
SIGNIFICANT_FRACTION_LIMIT = 0.001
RESULT = "HOLD_CURRENT_WORLD_BUILDING_COMPACT_V2__RUNTIME_AND_VISUAL_REGRESSION"
DECISION = "KEEP_CURRENT_184V_276T_SEGMENTED_RECEIVER_AS_RUNTIME_BASELINE__COMPACT_V2_REQUIRES_NON_RUNTIME_JUSTIFICATION_BEFORE_ADOPTION"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _runtime_rows(payload: dict[str, Any]) -> dict[tuple[int, str, str], dict[str, int]]:
    samples = payload.get("samples", [])
    if len(samples) != EXPECTED_SAMPLE_COUNT:
        raise ValueError(f"expected {EXPECTED_SAMPLE_COUNT} samples, found {len(samples)}")
    rows: dict[tuple[int, str, str], dict[str, int]] = {}
    for fallback_index, sample in enumerate(samples):
        raw_state = sample.get("state_index", sample.get("index", fallback_index))
        state = int(raw_state)
        contexts = sample.get("contexts", {})
        for camera in ("path_eye", "elevated_oblique"):
            if camera not in contexts:
                raise ValueError(f"missing camera {camera} at state {state}")
            for mode in ("control", "candidate"):
                runtime = contexts[camera].get(mode, {}).get("runtime", {})
                required = {
                    "buffer_mem_bytes",
                    "draw_calls_in_frame",
                    "objects_in_frame",
                    "primitives_in_frame",
                    "texture_mem_bytes",
                }
                if set(runtime) < required:
                    raise ValueError(f"runtime counters missing at {(state, camera, mode)}")
                rows[(state, camera, mode)] = {key: int(runtime[key]) for key in sorted(required)}
    if len(rows) != EXPECTED_OBSERVATIONS:
        raise ValueError(f"expected {EXPECTED_OBSERVATIONS} runtime observations, found {len(rows)}")
    return rows


def _compare_runtime(parent: dict[str, Any], compact: dict[str, Any]) -> dict[str, Any]:
    parent_rows = _runtime_rows(parent)
    compact_rows = _runtime_rows(compact)
    if set(parent_rows) != set(compact_rows):
        raise ValueError("runtime observation key drift")
    deltas = []
    for key in sorted(parent_rows):
        before = parent_rows[key]
        after = compact_rows[key]
        delta = {name: after[name] - before[name] for name in before}
        deltas.append({"state": key[0], "camera": key[1], "weather_mode": key[2], "delta": delta})
    unique = {tuple(sorted(row["delta"].items())) for row in deltas}
    if len(unique) != 1:
        raise ValueError(f"runtime deltas are not stable across all observations: {len(unique)} unique sets")
    stable = dict(next(iter(unique)))
    expected = {
        "buffer_mem_bytes": EXPECTED_BUFFER_DELTA_BYTES,
        "draw_calls_in_frame": 0,
        "objects_in_frame": 0,
        "primitives_in_frame": EXPECTED_PRIMITIVE_DELTA,
        "texture_mem_bytes": 0,
    }
    if stable != expected:
        raise ValueError(f"runtime delta changed: expected {expected}, observed {stable}")
    return {
        "observation_count": len(deltas),
        "stable_delta": stable,
        "rows": deltas,
    }


def _image_stats(before_path: Path, after_path: Path) -> dict[str, Any]:
    before = Image.open(before_path).convert("RGB")
    after = Image.open(after_path).convert("RGB")
    if before.size != after.size:
        raise ValueError(f"image size drift for {before_path.name}: {before.size} vs {after.size}")
    a = before.load()
    b = after.load()
    changed = 0
    significant = 0
    max_delta = 0
    min_x = before.width
    min_y = before.height
    max_x = -1
    max_y = -1
    max_delta_pixel = None
    for y in range(before.height):
        for x in range(before.width):
            av = a[x, y]
            bv = b[x, y]
            diffs = tuple(abs(int(bv[i]) - int(av[i])) for i in range(3))
            local_max = max(diffs)
            if local_max:
                changed += 1
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
            if local_max > SIGNIFICANT_LSB_THRESHOLD:
                significant += 1
            if local_max > max_delta:
                max_delta = local_max
                max_delta_pixel = {
                    "x": x,
                    "y": y,
                    "before_rgb": list(av),
                    "after_rgb": list(bv),
                    "channel_abs_delta": list(diffs),
                }
    total = before.width * before.height
    return {
        "width": before.width,
        "height": before.height,
        "changed_pixels": changed,
        "changed_fraction": changed / total,
        "significant_gt1_lsb_pixels": significant,
        "significant_gt1_lsb_fraction": significant / total,
        "max_channel_delta_lsb": max_delta,
        "changed_bbox_xyxy": None if changed == 0 else [min_x, min_y, max_x, max_y],
        "max_delta_pixel": max_delta_pixel,
    }


def _compare_visuals(parent_dir: Path, compact_dir: Path) -> dict[str, Any]:
    parent_files = sorted(parent_dir.glob("*.png"))
    compact_names = {path.name for path in compact_dir.glob("*.png")}
    if len(parent_files) != EXPECTED_OBSERVATIONS or len(compact_names) != EXPECTED_OBSERVATIONS:
        raise ValueError("expected 68 rendered images in each exact Environment artifact")
    if {path.name for path in parent_files} != compact_names:
        raise ValueError("rendered image filename set drift")
    rows = []
    for before_path in parent_files:
        after_path = compact_dir / before_path.name
        row = {"name": before_path.name, **_image_stats(before_path, after_path)}
        rows.append(row)
    max_sig = max(row["significant_gt1_lsb_fraction"] for row in rows)
    max_changed = max(row["changed_pixels"] for row in rows)
    max_delta = max(row["max_channel_delta_lsb"] for row in rows)
    if max_sig <= SIGNIFICANT_FRACTION_LIMIT:
        raise ValueError(
            f"visual regression guard no longer triggered: max >1 LSB fraction {max_sig:.9f} <= {SIGNIFICANT_FRACTION_LIMIT:.9f}"
        )
    by_group: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = row["name"]
        if "-path_eye-" in name:
            camera = "path_eye"
        elif "-elevated_oblique-" in name:
            camera = "elevated_oblique"
        else:
            raise ValueError(f"unknown camera filename: {name}")
        weather_mode = "candidate" if "-candidate-" in name else "control"
        key = f"{weather_mode}/{camera}"
        bucket = by_group.setdefault(key, {"frames": 0, "changed_pixels": [], "significant_fraction": [], "max_delta": 0})
        bucket["frames"] += 1
        bucket["changed_pixels"].append(row["changed_pixels"])
        bucket["significant_fraction"].append(row["significant_gt1_lsb_fraction"])
        bucket["max_delta"] = max(bucket["max_delta"], row["max_channel_delta_lsb"])
    summary = {}
    for key, bucket in sorted(by_group.items()):
        summary[key] = {
            "frames": bucket["frames"],
            "changed_pixels_min": min(bucket["changed_pixels"]),
            "changed_pixels_max": max(bucket["changed_pixels"]),
            "significant_gt1_lsb_fraction_min": min(bucket["significant_fraction"]),
            "significant_gt1_lsb_fraction_max": max(bucket["significant_fraction"]),
            "max_channel_delta_lsb": bucket["max_delta"],
        }
    return {
        "frame_count": len(rows),
        "significant_fraction_limit": SIGNIFICANT_FRACTION_LIMIT,
        "max_significant_gt1_lsb_fraction": max_sig,
        "max_changed_pixels": max_changed,
        "max_channel_delta_lsb": max_delta,
        "groups": summary,
        "rows": rows,
    }


def build_report(parent_root: Path, compact_root: Path) -> dict[str, Any]:
    parent_runtime = load_json(parent_root / "candidate" / "runtime.json")
    compact_runtime = load_json(compact_root / "candidate" / "runtime.json")
    if compact_runtime.get("environment_building_compact_v2_representation_id") != COMPACT_REPRESENTATION_ID:
        raise ValueError("compact-v2 representation identity drift")
    runtime = _compare_runtime(parent_runtime, compact_runtime)
    visuals = _compare_visuals(parent_root / "candidate" / "rendered", compact_root / "candidate" / "rendered")
    return {
        "schema": "axm.runtime-building-compact-v2-current-world-budget/v0.1",
        "result": RESULT,
        "decision": DECISION,
        "exact_environment_head": PARENT_ENV_HEAD,
        "source_evidence": {
            "parent_run_id": PARENT_RUN_ID,
            "parent_artifact_id": PARENT_ARTIFACT_ID,
            "compact_run_id": COMPACT_RUN_ID,
            "compact_artifact_id": COMPACT_ARTIFACT_ID,
            "compact_environment_workflow_conclusion": "failure_at_visual_continuity_verifier_after_successful_godot_observation",
        },
        "representations": {
            "current_world_parent": {"vertices": 184, "triangles": 276, "surfaces": 5},
            "compact_v2_review": {"vertices": 1004, "triangles": 2052, "surfaces": 5},
        },
        "runtime": runtime,
        "visuals": visuals,
        "truth_boundary": (
            "This gate compares the exact same-head Environment current-world parent and compact-v2 review artifacts on the pinned Godot 4.7.2 GL Compatibility proof host. "
            "It proves a proof-host runtime-counter and fixed-view visual regression for this receiving choice only. It does not prove target-device FPS/GPU time/VRAM, arbitrary-view appearance, or final Art preference."
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    delta = report["runtime"]["stable_delta"]
    vis = report["visuals"]
    lines = [
        "# Runtime Building compact-v2 current-world budget gate",
        "",
        f"Result: **{report['result']}**",
        "",
        f"Decision: **{report['decision']}**",
        "",
        "## Exact current-world comparison",
        "",
        "The source-owned compact-v2 shell is smaller than the 1420v/2884t boundary reference used by the isolated Building Runtime pass, but it is larger than the actual Map receiver it would replace: 1004v/2052t versus 184v/276t, both five-surface.",
        "",
        "Across all 68 matched state × camera × Weather-mode observations on the same proof host:",
        "",
        f"- buffer memory: **+{delta['buffer_mem_bytes']:,} B**;",
        f"- RenderingServer primitives: **+{delta['primitives_in_frame']:,}**;",
        f"- draw calls: **{delta['draw_calls_in_frame']:+d}**;",
        f"- objects: **{delta['objects_in_frame']:+d}**;",
        f"- texture memory: **{delta['texture_mem_bytes']:+d} B**.",
        "",
        "## Visual tradeoff for Art Direction / Visual QA",
        "",
        f"The exact compact-v2 Environment workflow correctly failed its inherited 0.1% (>1 LSB) full-frame continuity guard after successful Godot observation. Runtime independently compares the same 68 retained parent/candidate frames and observes a maximum significant-pixel fraction of **{vis['max_significant_gt1_lsb_fraction']*100:.4f}%**, with maximum channel delta **{vis['max_channel_delta_lsb']} LSB**.",
        "",
    ]
    for group, row in report["visuals"]["groups"].items():
        lines.append(
            f"- `{group}`: {row['changed_pixels_min']:,}–{row['changed_pixels_max']:,} changed pixels/frame; "
            f">1 LSB fraction {row['significant_gt1_lsb_fraction_min']*100:.4f}%–{row['significant_gt1_lsb_fraction_max']*100:.4f}%; "
            f"max {row['max_channel_delta_lsb']} LSB."
        )
    lines += [
        "",
        "Runtime therefore does **not** recommend replacing the current 184v/276t segmented Building receiver with compact-v2 on performance grounds. Any future adoption would need a non-Runtime reason plus a new exact consumer proof; the word `compact` is relative to the larger boundary reference, not to the actual current-world receiver.",
        "",
        "## Non-claims",
        "",
        "No target-device CPU/GPU frame-time, FPS, VRAM/heap, thermal, arbitrary-camera, transport/import, gameplay, CANON or production-readiness claim is made.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-root", type=Path, required=True)
    parser.add_argument("--compact-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.parent_root, args.compact_root)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.out / "report.md")
    print(json.dumps({
        "result": report["result"],
        "decision": report["decision"],
        "runtime_delta": report["runtime"]["stable_delta"],
        "max_significant_gt1_lsb_fraction": report["visuals"]["max_significant_gt1_lsb_fraction"],
        "max_channel_delta_lsb": report["visuals"]["max_channel_delta_lsb"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
