from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

SCHEMA = "axm.technical-art-exact-rgba-frame-compare/v0.1"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixel_difference(control: Path, candidate: Path) -> tuple[int, tuple[int, int, int, int] | None]:
    with Image.open(control).convert("RGBA") as a, Image.open(candidate).convert("RGBA") as b:
        if a.size != b.size:
            raise ValueError(f"frame size drift: {control.name} {a.size} != {b.size}")
        width, height = a.size
        changed = 0
        min_x, min_y = width, height
        max_x = max_y = -1
        for offset, (before, after) in enumerate(zip(a.getdata(), b.getdata())):
            if before == after:
                continue
            changed += 1
            x = offset % width
            y = offset // width
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        if changed == 0:
            return 0, None
        return changed, (min_x, min_y, max_x + 1, max_y + 1)


def compare_dirs(control_dir: Path, candidate_dir: Path, pattern: str, expected_count: int) -> dict:
    control_names = sorted(path.name for path in control_dir.glob(pattern))
    candidate_names = sorted(path.name for path in candidate_dir.glob(pattern))
    if len(control_names) != expected_count or candidate_names != control_names:
        raise ValueError(
            f"frame set drift: expected={expected_count} control={len(control_names)} candidate={len(candidate_names)}"
        )
    changed_frames = 0
    changed_pixels = 0
    changed = []
    for name in control_names:
        pixels, bbox = pixel_difference(control_dir / name, candidate_dir / name)
        if pixels:
            changed_frames += 1
            changed_pixels += pixels
            changed.append({"frame": name, "changed_pixels": pixels, "bbox": bbox})
    return {
        "schema": SCHEMA,
        "result": "PASS_EXACT_RGBA_FRAME_SET_EQUAL" if changed_pixels == 0 else "FAIL_RGBA_FRAME_SET_CHANGED",
        "expected_count": expected_count,
        "frame_count": len(control_names),
        "changed_frames": changed_frames,
        "changed_pixels": changed_pixels,
        "pixel_exact": changed_pixels == 0,
        "first_changes": changed[:8],
        "control_manifest_sha256": hashlib.sha256(
            "\n".join(f"{name} {sha256_file(control_dir / name)}" for name in control_names).encode("utf-8")
        ).hexdigest(),
        "candidate_manifest_sha256": hashlib.sha256(
            "\n".join(f"{name} {sha256_file(candidate_dir / name)}" for name in candidate_names).encode("utf-8")
        ).hexdigest(),
        "truth_boundary": (
            "Exact RGBA tuple comparison. Every channel is compared directly; transparency does not mask RGB deltas. "
            "No perceptual threshold, alpha shortcut, or aesthetic acceptance is inferred."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-dir", required=True)
    parser.add_argument("--candidate-dir", required=True)
    parser.add_argument("--pattern", default="atmosphere-width-*.png")
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = compare_dirs(Path(args.control_dir), Path(args.candidate_dir), args.pattern, args.expected_count)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["pixel_exact"]:
        raise SystemExit(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
