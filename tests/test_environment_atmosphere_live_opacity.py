import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "environment_atmosphere_live_opacity",
    ROOT / "tools" / "environment_atmosphere_live_opacity.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    lines = [
        {"id": f"streak-{index:02d}", "opacity": 0.30 + index * 0.01}
        for index in range(MODULE.EXPECTED_STREAK_COUNT)
    ]
    states = [
        {"candidate_scene": {"weather_lines": [dict(row) for row in lines]}}
        for _ in range(MODULE.EXPECTED_STATE_COUNT)
    ]
    payload = {
        "status": "PASS_DENSE_INTERMEDIATE_SOURCE_SEQUENCE",
        "weather_source_head": MODULE.EXPECTED_WEATHER_SOURCE_HEAD,
        "sequence_digest": MODULE.EXPECTED_SEQUENCE_DIGEST,
        "states": states,
    }
    minimum = min(row["opacity"] for row in lines)
    maximum = max(row["opacity"] for row in lines)
    mean = sum(row["opacity"] for row in lines) / len(lines)
    samples = []
    for index in range(MODULE.EXPECTED_STATE_COUNT):
        samples.append({
            "index": index,
            "weather_update": {
                "state": "PASS_SOURCE_STREAK_OPACITY_CONSUMED",
                "opacity_mode": MODULE.EXPECTED_OPACITY_MODE,
                "source_opacity_consumed": True,
                "streak_count": MODULE.EXPECTED_STREAK_COUNT,
                "surface_count": 1,
                "source_opacity_min": minimum,
                "source_opacity_max": maximum,
                "source_opacity_mean": mean,
                "opacity_fidelity_provenance_head": MODULE.EXPECTED_FIDELITY_DONOR_HEAD,
                "width_policy": "SOURCE_WIDTH_PX_NOT_MAPPED_TO_3D_LINE_WIDTH_IN_THIS_PROOF",
            },
        })
    receipt = {
        "state": "PASS_DENSE_INTERMEDIATE_LIVE_OBSERVATION",
        "weather_opacity_fidelity_head": MODULE.EXPECTED_FIDELITY_DONOR_HEAD,
        "weather_opacity_mode": MODULE.EXPECTED_OPACITY_MODE,
        "samples": samples,
    }
    return payload, receipt


class DenseLiveOpacityVerifierTests(unittest.TestCase):
    def test_exact_fixture_passes(self):
        payload, receipt = fixture()
        result = MODULE.verify(payload, receipt)
        self.assertEqual(result["state"], "PASS_DENSE_LIVE_SOURCE_OPACITY_FIDELITY")
        self.assertTrue(all(result["checks"].values()))

    def test_uniform_or_unconsumed_runtime_fails(self):
        payload, receipt = fixture()
        receipt["samples"][4]["weather_update"]["source_opacity_consumed"] = False
        result = MODULE.verify(payload, receipt)
        self.assertEqual(result["state"], "FAIL")
        self.assertFalse(result["checks"]["every_live_update_consumes_exact_source_opacity"])

    def test_source_opacity_identity_drift_fails(self):
        payload, receipt = fixture()
        payload["states"][8]["candidate_scene"]["weather_lines"][0]["opacity"] += 0.1
        result = MODULE.verify(payload, receipt)
        self.assertEqual(result["state"], "FAIL")
        self.assertFalse(result["checks"]["source_opacity_profile_valid"])

    def test_sequence_digest_drift_fails(self):
        payload, receipt = fixture()
        payload["sequence_digest"] = "drift"
        result = MODULE.verify(payload, receipt)
        self.assertEqual(result["state"], "FAIL")
        self.assertFalse(result["checks"]["exact_dense_sequence_digest_preserved"])


if __name__ == "__main__":
    unittest.main()
