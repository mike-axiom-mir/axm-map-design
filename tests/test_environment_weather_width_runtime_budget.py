from __future__ import annotations

import copy
import struct
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.environment_weather_width_runtime_budget import (  # noqa: E402
    EXPECTED_CANDIDATE,
    EXPECTED_COMPOSITION_DIGEST,
    EXPECTED_CONTROL,
    EXPECTED_DELTA,
    EXPECTED_ENVIRONMENT_HEAD,
    EXPECTED_STATES,
    STATUS,
    characterize,
)


def write_minimal_png(path: Path, marker: int) -> None:
    header = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 1100, 720)
    path.write_bytes(header + bytes([marker]))


def fixtures(root: Path):
    payload = {
        "status": "PASS_CURRENT_WORLD_BUILDING_SUCCESSOR_WEATHER_WIDTH_STRUCTURE",
        "receiving_head": EXPECTED_ENVIRONMENT_HEAD,
        "composition_digest": EXPECTED_COMPOSITION_DIGEST,
        "states": [{} for _ in range(EXPECTED_STATES)],
        "source_width_summary": {"count": 36, "min_px": 1.02, "mean_px": 1.70, "max_px": 2.35},
    }
    samples = []
    for index in range(EXPECTED_STATES):
        contexts = {}
        for context in ("path_eye", "elevated_oblique"):
            contexts[context] = {
                "control": {"runtime": copy.deepcopy(EXPECTED_CONTROL[context])},
                "candidate": {"runtime": copy.deepcopy(EXPECTED_CANDIDATE[context])},
            }
            write_minimal_png(root / f"atmosphere-width-control-{context}-{index:02d}.png", 1)
            write_minimal_png(root / f"atmosphere-width-candidate-{context}-{index:02d}.png", 2)
        samples.append({"contexts": contexts})
    runtime = {
        "state": "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION",
        "receiving_head": EXPECTED_ENVIRONMENT_HEAD,
        "proof_runtime": "Godot 4.7.2 GL Compatibility",
        "samples": samples,
    }
    target = {
        "state": "PASS_CURRENT_WORLD_BUILDING_SUCCESSOR_WEATHER_WIDTH_TARGET_HOST",
        "receiving_head": EXPECTED_ENVIRONMENT_HEAD,
        "composition_digest": EXPECTED_COMPOSITION_DIGEST,
        "checks": {"example": True},
        "changed_pair_counts": {"path_eye": 17, "elevated_oblique": 17},
        "frame_counts": {
            "control": {"path_eye": 17, "elevated_oblique": 17},
            "candidate": {"path_eye": 17, "elevated_oblique": 17},
        },
        "measured_width_count": 1224,
        "maximum_projected_width_residual_px": 0.01,
        "near_clipped_endpoint_count": 5,
        "near_clipped_streak_ids": {"wind-streak-001": 2, "wind-streak-005": 3},
    }
    return payload, runtime, target


class RuntimeWeatherWidthBudgetTests(unittest.TestCase):
    def test_exact_bounded_budget_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload, runtime, target = fixtures(Path(tmp))
            result = characterize(payload, runtime, target, Path(tmp))
            self.assertEqual(result["state"], STATUS)
            self.assertEqual(result["contexts"]["path_eye"]["delta"], EXPECTED_DELTA)
            self.assertEqual(result["contexts"]["elevated_oblique"]["delta"], EXPECTED_DELTA)

    def test_extra_draw_call_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload, runtime, target = fixtures(Path(tmp))
            runtime["samples"][0]["contexts"]["path_eye"]["candidate"]["runtime"]["draw_calls_in_frame"] += 1
            result = characterize(payload, runtime, target, Path(tmp))
            self.assertEqual(result["state"], "FAIL")
            self.assertFalse(result["checks"]["path_eye_candidate_counters_stable"])

    def test_parent_head_drift_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload, runtime, target = fixtures(Path(tmp))
            payload["receiving_head"] = "drifted"
            with self.assertRaises(ValueError):
                characterize(payload, runtime, target, Path(tmp))

    def test_visual_identity_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload, runtime, target = fixtures(Path(tmp))
            for context in ("path_eye", "elevated_oblique"):
                for index in range(EXPECTED_STATES):
                    src = Path(tmp) / f"atmosphere-width-control-{context}-{index:02d}.png"
                    dst = Path(tmp) / f"atmosphere-width-candidate-{context}-{index:02d}.png"
                    dst.write_bytes(src.read_bytes())
            result = characterize(payload, runtime, target, Path(tmp))
            self.assertEqual(result["state"], "FAIL")
            self.assertFalse(result["checks"]["path_eye_all_retained_pairs_byte_different"])


if __name__ == "__main__":
    unittest.main()
