#!/usr/bin/env python3
"""Rebuild the exact retained Materials review PNG from owner-provenanced RGBA8 values.

This is a transport reproducer, not a visual-authoring tool. The checker colors, period,
size, raw RGBA8 digest and serialized PNG digest are bound to Materials retained evidence.
The PNG encoder mirrors the deterministic filter selection + zlib stream used by the
retained Godot 4.7.2 artifact and fails closed unless both owner digests match exactly.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import struct
import zlib
from pathlib import Path
from typing import Iterable


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def filter_row(kind: int, row: bytes, previous: bytes | None, bpp: int = 4) -> bytes:
    out = bytearray(len(row))
    for index, value in enumerate(row):
        left = row[index - bpp] if index >= bpp else 0
        up = previous[index] if previous is not None else 0
        upper_left = previous[index - bpp] if previous is not None and index >= bpp else 0
        if kind == 0:
            predictor = 0
        elif kind == 1:
            predictor = left
        elif kind == 2:
            predictor = up
        elif kind == 3:
            predictor = (left + up) // 2
        elif kind == 4:
            predictor = paeth(left, up, upper_left)
        else:
            raise ValueError(f"unsupported PNG filter {kind}")
        out[index] = (value - predictor) & 0xFF
    return bytes(out)


def signed_abs_cost(values: Iterable[int]) -> int:
    return sum(min(value, 256 - value) for value in values)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def build_png(width: int, height: int, period: int, dark: bytes, light: bytes) -> tuple[bytes, bytes, list[int]]:
    require(width > 0 and height > 0 and period > 0, "invalid review-image dimensions/period")
    require(len(dark) == 4 and len(light) == 4, "checker colors must be RGBA8")
    rows: list[bytes] = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            odd = ((x // period) + (y // period)) % 2
            row += light if odd == 0 else dark
        rows.append(bytes(row))
    rgba = b"".join(rows)

    filtered = bytearray()
    selected_filters: list[int] = []
    for y, row in enumerate(rows):
        previous = rows[y - 1] if y else None
        candidates = [filter_row(kind, row, previous) for kind in range(5)]
        costs = [signed_abs_cost(candidate) for candidate in candidates]
        selected = min(range(5), key=lambda kind: costs[kind])
        selected_filters.append(selected)
        filtered.append(selected)
        filtered += candidates[selected]

    compressed = zlib.compress(bytes(filtered), 6)
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += png_chunk(b"sRGB", b"\x00")
    png += png_chunk(b"IDAT", compressed)
    png += png_chunk(b"IEND", b"")
    return png, rgba, selected_filters


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    provenance = json.loads(args.provenance.read_text(encoding="utf-8"))
    require(provenance.get("schema") == "axm.technical-art-materials-retained-image-provenance/v0.1", "provenance schema drift")
    image_size = provenance["image_size_px"]
    period = int(provenance["checker_period_px"])
    dark = bytes(int(value) for value in provenance["checker_dark_rgba8"])
    light = bytes(int(value) for value in provenance["checker_light_rgba8"])
    png, rgba, filters = build_png(int(image_size[0]), int(image_size[1]), period, dark, light)

    require(len(rgba) == int(provenance["base_rgba8_bytes"]), "rebuilt RGBA8 byte count drift")
    require(sha256(rgba) == provenance["base_rgba8_sha256"], "rebuilt RGBA8 owner identity drift")
    require(len(png) == int(provenance["materials_png_bytes"]), "rebuilt serialized PNG byte count drift")
    require(sha256(png) == provenance["materials_png_sha256"], "rebuilt serialized PNG owner identity drift")
    require(filters[0] == 1, "retained PNG first-row filter drift")
    require(filters.count(2) == 480 and filters.count(4) == 31, "retained PNG adaptive-filter identity drift")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(png)
    print("PASS_REBUILT_EXACT_MATERIALS_REVIEW_PNG_FROM_OWNER_PROVENANCE")
    print(json.dumps({
        "bytes": len(png),
        "sha256": sha256(png),
        "rgba8_bytes": len(rgba),
        "rgba8_sha256": sha256(rgba),
        "filter_counts": {str(kind): filters.count(kind) for kind in sorted(set(filters))},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
