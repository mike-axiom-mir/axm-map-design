import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("environment_composition", ROOT / "tools/environment_composition.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EnvironmentCompositionTests(unittest.TestCase):
    def setUp(self):
        self.source = ROOT / "examples/environment_baseline_001.json"
        self.data = MODULE.load_study(self.source)

    def test_exact_baseline_passes_bounded_checks(self):
        report = MODULE.evaluate(self.data)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(
            set(report["asset_kinds_observed"]),
            {"map-surface", "building-proxy", "nature-proxy", "object-proxy"},
        )

    def test_path_blocker_is_detected(self):
        changed = copy.deepcopy(self.data)
        changed["items"][-1]["position"] = [0.0, 0.0, 0.55]
        report = MODULE.evaluate(changed)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("proxy:object-crate-east", report["path_blockers"])

    def test_non_proxy_item_fails_truth_boundary(self):
        changed = copy.deepcopy(self.data)
        changed["items"][1]["evidence"] = "FINAL_ASSET"
        report = MODULE.evaluate(changed)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["all_items_explicitly_proxy_only"])

    def test_generated_scene_is_deterministic_and_spans_asset_types(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            report_a = MODULE.build(self.source, first)
            report_b = MODULE.build(self.source, second)
            self.assertEqual(report_a["source_digest"], report_b["source_digest"])
            obj_a = (Path(first) / "scene.obj").read_text(encoding="utf-8")
            obj_b = (Path(second) / "scene.obj").read_text(encoding="utf-8")
            svg_a = (Path(first) / "top.svg").read_text(encoding="utf-8")
            svg_b = (Path(second) / "top.svg").read_text(encoding="utf-8")
            self.assertEqual(obj_a, obj_b)
            self.assertEqual(svg_a, svg_b)
            self.assertGreater(obj_a.count("\nv "), 50)
            self.assertGreater(obj_a.count("\nf "), 30)
            self.assertIn("proxy:building-pavilion", obj_a)
            self.assertIn("proxy:nature-tree-west-a", obj_a)
            self.assertIn("proxy:object-crate-west", obj_a)
            self.assertIn('stroke="#3a69a8"', svg_a)
            self.assertIn('stroke-dasharray="6 4"', svg_a)

    def test_weather_context_must_have_direction(self):
        changed = copy.deepcopy(self.data)
        changed["weather_context"]["wind_xy"] = [0.0, 0.0]
        report = MODULE.evaluate(changed)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["weather_context_has_nonzero_direction"])


if __name__ == "__main__":
    unittest.main()
