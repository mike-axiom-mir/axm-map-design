import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_eye_level as eye


class EnvironmentEyeLevelTests(unittest.TestCase):
    def payload(self):
        payload = {
            "schema": eye.SCHEMA,
            "study_id": "environment-eye-level-001",
            "receiving_head": "test-head",
            "source_integration": {
                "status": "PASS",
                "weather_overlay": {"particle_count": 2},
            },
            "items": [
                {"kind": "map-surface"},
                {"kind": "building-proxy"},
                {"kind": "nature-proxy"},
                {"kind": "object-proxy"},
            ],
            "sapling": {
                "vertices_source_xyz_m": [[0, 0, 0]] * 390,
                "triangles": [[0, 0, 0]] * 570,
                "proof_render_culling": "DISABLED_FOR_OBSERVATION_HOST_ONLY_NOT_MATERIAL_ACCEPTANCE",
            },
            "weather_lines": [{}, {}],
            "weather_presentation": {
                "semantics": "RENDER_PRESENTATION_ONLY_OF_SOURCE_OWNED_2D_VISUAL_FIELD_NOT_PHYSICAL_ALTITUDE"
            },
            "cameras": {
                "path_eye": {},
                "elevated_oblique": {},
            },
            "truth_boundary": "test only",
        }
        payload["scene_digest"] = eye.digest(payload)
        return payload

    def test_bounded_mixed_scene_contract_passes(self):
        report = eye.evaluate(self.payload())
        self.assertEqual("PASS", report["status"])
        self.assertTrue(all(report["checks"].values()))

    def test_missing_asset_type_fails_closed(self):
        payload = self.payload()
        payload["items"] = [row for row in payload["items"] if row["kind"] != "object-proxy"]
        report = eye.evaluate(payload)
        self.assertEqual("FAIL", report["status"])
        self.assertFalse(report["checks"]["object_proxy_present"])

    def test_weather_relabel_fails_closed(self):
        payload = copy.deepcopy(self.payload())
        payload["weather_presentation"]["semantics"] = "PHYSICAL_ALTITUDE"
        report = eye.evaluate(payload)
        self.assertEqual("FAIL", report["status"])
        self.assertFalse(report["checks"]["weather_truth_boundary_preserved"])


if __name__ == "__main__":
    unittest.main()
