import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_sapling_motion as motion


@unittest.skipUnless(
    os.environ.get("AXM_NATURE_SOURCE_ROOT") and os.environ.get("AXM_NATURE_VFX_ROOT") and os.environ.get("AXM_WEATHER_ROOT"),
    "exact cross-repo roots are supplied only by the dedicated VFX receiving workflow",
)
class EnvironmentSaplingMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nature_source_root = Path(os.environ["AXM_NATURE_SOURCE_ROOT"])
        cls.nature_vfx_root = Path(os.environ["AXM_NATURE_VFX_ROOT"])
        cls.weather_root = Path(os.environ["AXM_WEATHER_ROOT"])
        cls.manifest = ROOT / "examples" / "environment_real_slice_001.json"

    def test_exact_neutral_peak_contract(self):
        neutral, peak, evidence = motion.build_motion_payloads(
            self.manifest,
            self.nature_source_root,
            self.nature_vfx_root,
            self.weather_root,
        )
        self.assertEqual("PASS", evidence["status"])
        self.assertTrue(all(evidence["checks"].values()))
        self.assertEqual("neutral", neutral["sapling"]["motion_state"])
        self.assertEqual("peak", peak["sapling"]["motion_state"])
        self.assertEqual(0.0, neutral["sapling"]["sample_time_s"])
        self.assertEqual(0.25, peak["sapling"]["sample_time_s"])
        self.assertEqual(390, len(neutral["sapling"]["vertices_source_xyz_m"]))
        self.assertEqual(570, len(neutral["sapling"]["triangles"]))
        self.assertEqual(neutral["sapling"]["triangles"], peak["sapling"]["triangles"])
        self.assertAlmostEqual(0.18, evidence["max_scene_vertex_displacement_m"], places=7)
        self.assertFalse(motion._rects_overlap(evidence["peak_xy_bounds_m"], neutral["readable_path"]))
        self.assertEqual(neutral["items"], peak["items"])
        self.assertEqual(neutral["weather_lines"], peak["weather_lines"])
        self.assertEqual(neutral["cameras"], peak["cameras"])

    def test_evidence_builder_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = motion.build(self.manifest, self.nature_source_root, self.nature_vfx_root, self.weather_root, first)
            b = motion.build(self.manifest, self.nature_source_root, self.nature_vfx_root, self.weather_root, second)
            a = copy.deepcopy(a)
            b = copy.deepcopy(b)
            a["receiving_head"] = "IGNORED"
            b["receiving_head"] = "IGNORED"
            self.assertEqual(a, b)

    def test_path_intrusion_gate_fails_closed(self):
        path = {"x_min": -1.0, "x_max": 1.0, "y_min": -1.0, "y_max": 1.0}
        intruding = {"x_min": 0.9, "x_max": 1.2, "y_min": 0.0, "y_max": 0.5}
        clear = {"x_min": 1.1, "x_max": 1.4, "y_min": 0.0, "y_max": 0.5}
        self.assertTrue(motion._rects_overlap(intruding, path))
        self.assertFalse(motion._rects_overlap(clear, path))


if __name__ == "__main__":
    unittest.main()
