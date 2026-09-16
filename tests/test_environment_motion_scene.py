import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_motion_scene as motion


class EnvironmentMotionSceneTests(unittest.TestCase):
    def payload(self):
        triangles = [[0, 1, 2]]
        vertices = [[0.0, 0.0, 0.0]] * 390
        payload = {
            "schema": motion.SCHEMA,
            "study_id": "environment-motion-scene-001",
            "receiving_head": "test-head",
            "nature_response": {
                "head": motion.EXPECTED_NATURE_RESPONSE_HEAD,
                "state": "PASS_BOUNDED_VISUAL_WIND_RESPONSE",
                "weather_semantics": "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED",
            },
            "sapling": {
                "proof_render_culling": "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_MATERIAL_ACCEPTANCE",
                "states": {
                    "neutral": {"time_s": 0.0, "vertices_source_xyz_m": vertices, "triangles": triangles},
                    "peak": {"time_s": 0.25, "vertices_source_xyz_m": vertices, "triangles": triangles},
                },
            },
            "composition_measurements": {
                "max_neutral_to_peak_displacement_m": 0.18,
                "peak_path_unblocked": True,
                "peak_spacing_conflicts": [],
                "peak_inside_static_reserved_proxy_footprint": False,
            },
            "cameras": {"path_eye": {}, "elevated_oblique": {}},
            "weather_presentation": {
                "semantics": "RENDER_PRESENTATION_ONLY_OF_SOURCE_OWNED_2D_VISUAL_FIELD_NOT_PHYSICAL_ALTITUDE"
            },
            "truth_boundary": "test only",
        }
        payload["scene_digest"] = motion.digest(payload)
        return payload

    def test_bounded_scene_motion_contract_passes(self):
        report = motion.evaluate(self.payload())
        self.assertEqual("PASS", report["status"])
        self.assertTrue(all(report["checks"].values()))

    def test_path_intrusion_fails_closed(self):
        payload = copy.deepcopy(self.payload())
        payload["composition_measurements"]["peak_path_unblocked"] = False
        report = motion.evaluate(payload)
        self.assertEqual("FAIL", report["status"])
        self.assertFalse(report["checks"]["peak_path_unblocked"])

    def test_wrong_response_head_fails_closed(self):
        payload = copy.deepcopy(self.payload())
        payload["nature_response"]["head"] = "wrong"
        report = motion.evaluate(payload)
        self.assertEqual("FAIL", report["status"])
        self.assertFalse(report["checks"]["pinned_response_head"])

    def test_static_envelope_exit_is_recorded_not_silently_promoted_to_collision(self):
        payload = self.payload()
        self.assertFalse(payload["composition_measurements"]["peak_inside_static_reserved_proxy_footprint"])
        self.assertEqual("PASS", motion.evaluate(payload)["status"])


if __name__ == "__main__":
    unittest.main()
