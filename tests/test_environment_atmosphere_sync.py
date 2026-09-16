import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_atmosphere_sync as sync


@unittest.skipUnless(
    os.environ.get("AXM_NATURE_ROOT") and os.environ.get("AXM_WEATHER_ROOT"),
    "exact cross-repo roots are supplied only by the dedicated VFX atmosphere-sync workflow",
)
class EnvironmentAtmosphereSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nature_root = Path(os.environ["AXM_NATURE_ROOT"])
        cls.weather_root = Path(os.environ["AXM_WEATHER_ROOT"])
        cls.manifest = ROOT / "examples" / "environment_real_slice_001.json"

    def build_payload(self):
        return sync.build_sync_payload(
            self.manifest,
            self.nature_root,
            self.weather_root,
            sync.EXPECTED_NATURE_RESPONSE_HEAD,
        )

    def test_exact_shared_clock_contract(self):
        payload = self.build_payload()
        self.assertEqual("PASS_SYNCHRONIZED_VISUAL_ATMOSPHERE_SEQUENCE", payload["status"])
        self.assertTrue(all(payload["checks"].values()))
        self.assertEqual(sync.weather_sequence.SAMPLE_TIMES_S, payload["sampling_schedule_s"])
        self.assertEqual(9, len(payload["states"]))
        self.assertEqual(sync.EXPECTED_WEATHER_HEAD, payload["weather_source"]["head"])
        self.assertEqual(sync.EXPECTED_NATURE_RESPONSE_HEAD, payload["nature_response"]["head"])
        self.assertEqual(payload["weather_source"]["visual_wind_xy"], payload["nature_response"]["visual_wind_xy"])
        self.assertEqual(sync.VISUAL_ONLY_SEMANTICS, payload["weather_source"]["semantics"])
        self.assertEqual(sync.VISUAL_ONLY_SEMANTICS, payload["nature_response"]["semantics"])
        self.assertLessEqual(payload["measurements"]["maximum_sampled_sapling_displacement_m"], sync.MAX_DISPLACEMENT_M + sync.TOL)

    def test_only_weather_and_exact_sapling_response_change_over_shared_samples(self):
        payload = self.build_payload()
        first = payload["states"][0]["candidate_scene"]
        for row in payload["states"]:
            control = row["control_scene"]
            candidate = row["candidate_scene"]
            self.assertEqual(control["weather_lines"], candidate["weather_lines"])
            self.assertEqual(first["items"], candidate["items"])
            self.assertEqual(first["cameras"], candidate["cameras"])
            self.assertEqual(first["readable_path"], candidate["readable_path"])
            self.assertEqual(first["weather_presentation"], candidate["weather_presentation"])
            self.assertEqual(390, len(candidate["sapling"]["vertices_source_xyz_m"]))
            self.assertEqual(570, len(candidate["sapling"]["triangles"]))
            self.assertTrue(row["sapling_path_unblocked"])
            self.assertFalse(row["sapling_spacing_conflicts"])

        self.assertEqual(
            payload["states"][0]["control_scene"]["sapling"]["vertices_source_xyz_m"],
            payload["states"][0]["candidate_scene"]["sapling"]["vertices_source_xyz_m"],
        )
        self.assertNotEqual(
            payload["states"][4]["control_scene"]["sapling"]["vertices_source_xyz_m"],
            payload["states"][4]["candidate_scene"]["sapling"]["vertices_source_xyz_m"],
        )
        self.assertEqual(
            payload["states"][8]["control_scene"]["sapling"]["vertices_source_xyz_m"],
            payload["states"][8]["candidate_scene"]["sapling"]["vertices_source_xyz_m"],
        )

    def test_weather_field_keeps_nine_distinct_source_states(self):
        payload = self.build_payload()
        self.assertEqual(9, len({row["weather_field_digest"] for row in payload["states"]}))
        self.assertTrue(all(len(row["candidate_scene"]["weather_lines"]) == 36 for row in payload["states"]))

    def test_wrong_nature_response_head_fails_closed(self):
        with self.assertRaises(ValueError):
            sync.build_sync_payload(
                self.manifest,
                self.nature_root,
                self.weather_root,
                "0" * 40,
            )


if __name__ == "__main__":
    unittest.main()
