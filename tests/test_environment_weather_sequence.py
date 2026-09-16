import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_weather_sequence as sequence


@unittest.skipUnless(
    os.environ.get("AXM_NATURE_ROOT") and os.environ.get("AXM_WEATHER_ROOT"),
    "exact cross-repo roots are supplied only by the dedicated VFX Weather sequence workflow",
)
class EnvironmentWeatherSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nature_root = Path(os.environ["AXM_NATURE_ROOT"])
        cls.weather_root = Path(os.environ["AXM_WEATHER_ROOT"])
        cls.manifest = ROOT / "examples" / "environment_real_slice_001.json"

    def test_exact_sequence_contract(self):
        payload = sequence.build_sequence_payload(self.manifest, self.nature_root, self.weather_root)
        self.assertEqual("PASS", payload["status"])
        self.assertTrue(all(payload["checks"].values()))
        self.assertEqual(sequence.SAMPLE_TIMES_S, payload["sampling_schedule_s"])
        self.assertEqual(9, len(payload["states"]))
        self.assertEqual(9, len({row["field_digest"] for row in payload["states"]}))
        self.assertTrue(all(len(row["scene"]["weather_lines"]) == 36 for row in payload["states"]))
        self.assertLessEqual(payload["motion_metrics"]["maximum_adjacent_projected_displacement_error_m"], sequence.TOL)
        self.assertLessEqual(payload["motion_metrics"]["maximum_adjacent_crosswind_drift_m"], sequence.TOL)

    def test_receiving_scene_is_static_except_weather_field_and_sequence_metadata(self):
        payload = sequence.build_sequence_payload(self.manifest, self.nature_root, self.weather_root)
        first = payload["states"][0]["scene"]
        for row in payload["states"][1:]:
            scene = row["scene"]
            self.assertEqual(first["items"], scene["items"])
            self.assertEqual(first["sapling"], scene["sapling"])
            self.assertEqual(first["cameras"], scene["cameras"])
            self.assertEqual(first["readable_path"], scene["readable_path"])
            self.assertEqual(first["weather_presentation"], scene["weather_presentation"])
            self.assertNotEqual(first["weather_lines"], scene["weather_lines"])

    def test_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = sequence.build(self.manifest, self.nature_root, self.weather_root, first)
            b = sequence.build(self.manifest, self.nature_root, self.weather_root, second)
            a = dict(a)
            b = dict(b)
            a["receiving_head"] = "IGNORED"
            b["receiving_head"] = "IGNORED"
            self.assertEqual(a, b)

    def test_extent_gate_rejects_outside_endpoint(self):
        lines = [{"tail_xy": [-12.1, 0.0], "head_xy": [0.0, 0.0]}]
        self.assertFalse(sequence._inside_extent(lines, 24.0, 18.0))


if __name__ == "__main__":
    unittest.main()
