import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "environment_weather_opacity_fidelity",
    ROOT / "tools" / "environment_weather_opacity_fidelity.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

NATURE_ROOT = Path(os.environ.get("AXM_NATURE_ROOT", ROOT / ".nature"))
WEATHER_ROOT = Path(os.environ.get("AXM_WEATHER_ROOT", ROOT / ".weather"))
DEPS_AVAILABLE = NATURE_ROOT.exists() and WEATHER_ROOT.exists()


class WeatherOpacityProfileUnitTests(unittest.TestCase):
    def test_unknown_mode_fails_closed(self):
        with self.assertRaises(ValueError):
            MODULE._profile_payload({"truth_boundary": "x"}, "UNKNOWN")


@unittest.skipUnless(DEPS_AVAILABLE, "requires exact Nature and Weather dependency checkouts")
class WeatherOpacityFidelityIntegrationTests(unittest.TestCase):
    def build_pair(self):
        return MODULE.build_pair(
            ROOT / "examples" / "environment_real_slice_001.json",
            NATURE_ROOT,
            WEATHER_ROOT,
        )

    def test_pair_preserves_exact_scene_except_render_profile(self):
        control, candidate, report = self.build_pair()
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(
            MODULE._without_profile(control),
            MODULE._without_profile(candidate),
        )
        self.assertNotEqual(control["scene_digest"], candidate["scene_digest"])

    def test_exact_source_opacity_is_carried_for_all_streaks(self):
        control, candidate, report = self.build_pair()
        self.assertEqual(len(candidate["weather_lines"]), 36)
        self.assertEqual(control["weather_lines"], candidate["weather_lines"])
        opacities = [float(row["opacity"]) for row in candidate["weather_lines"]]
        self.assertEqual(len(opacities), 36)
        self.assertTrue(all(0.0 <= value <= 1.0 for value in opacities))
        self.assertLess(min(opacities), max(opacities))
        self.assertAlmostEqual(report["source_weather"]["source_opacity_min"], min(opacities))
        self.assertAlmostEqual(report["source_weather"]["source_opacity_max"], max(opacities))

    def test_candidate_does_not_invent_line_width_mapping(self):
        _, candidate, report = self.build_pair()
        self.assertEqual(
            candidate["weather_render_profile"]["width_policy"],
            "SOURCE_WIDTH_PX_NOT_MAPPED_TO_3D_LINE_WIDTH_IN_THIS_PROOF",
        )
        self.assertEqual(
            report["renderer_boundary"]["line_width"],
            "SOURCE_WIDTH_PX_NOT_MAPPED_TO_3D_LINE_WIDTH_IN_THIS_PROOF",
        )

    def test_build_is_deterministic_for_same_receiving_head(self):
        old = os.environ.get("AXM_RECEIVING_HEAD")
        os.environ["AXM_RECEIVING_HEAD"] = "test-head"
        try:
            with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
                report_a = MODULE.build(
                    ROOT / "examples" / "environment_real_slice_001.json",
                    NATURE_ROOT,
                    WEATHER_ROOT,
                    first,
                )
                report_b = MODULE.build(
                    ROOT / "examples" / "environment_real_slice_001.json",
                    NATURE_ROOT,
                    WEATHER_ROOT,
                    second,
                )
                self.assertEqual(report_a, report_b)
                for name in ("control_scene.json", "candidate_scene.json", "comparison.json"):
                    self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())
        finally:
            if old is None:
                os.environ.pop("AXM_RECEIVING_HEAD", None)
            else:
                os.environ["AXM_RECEIVING_HEAD"] = old


if __name__ == "__main__":
    unittest.main()
