import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import environment_composition as composition
import environment_source_aware_variation as source_aware
import environment_variation as variation


class EnvironmentSourceAwareVariationTests(unittest.TestCase):
    def setUp(self):
        self.base_path = ROOT / "examples/environment_baseline_001.json"
        self.family_path = ROOT / "examples/environment_variation_family_001.json"
        self.gate_path = ROOT / "examples/environment_west_sapling_source_gate_001.json"
        self.base = composition.load_study(self.base_path)
        self.family = variation.load_family(self.family_path)
        self.gate = source_aware.load_gate(self.gate_path)

    def test_historical_proxy_only_outputs_remain_unchanged(self):
        expected = {
            7: "37d7bce32e2a555f603fe5a03fe1886d1735c083bdba1d590244ceb171a5e224",
            29: "6bb6a6436f2b13aff58a210b252bfcef310c8fd1cc76c2198d75cad819f0c499",
            83: "fb06a593a65dc93ca619acf4288cea403aee3763573318d3be7c1e78cb8ecb7b",
        }
        for seed, digest in expected.items():
            result = variation.generate_variant(self.base, self.family, seed)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["study_digest"], digest)
            self.assertEqual(result["receipt"]["attempt_index"], 0)

    def test_source_aware_sweep_keeps_three_distinct_outputs_and_rejects_seed7_until_safe(self):
        summary, variants = source_aware.generate_source_aware_sweep(
            self.base, self.family, self.gate, [7, 29, 83]
        )
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["variant_count"], 3)
        self.assertEqual(summary["unique_study_digest_count"], 3)
        self.assertEqual(summary["total_rejected_attempts"], 3)

        by_seed = {item["receipt"]["seed"]: item for item in variants}
        self.assertEqual(by_seed[7]["receipt"]["attempt_index"], 3)
        self.assertEqual(by_seed[7]["receipt"]["rejected_attempt_count"], 3)
        self.assertNotEqual(
            by_seed[7]["study_digest"],
            "37d7bce32e2a555f603fe5a03fe1886d1735c083bdba1d590244ceb171a5e224",
        )

        self.assertEqual(by_seed[29]["receipt"]["attempt_index"], 0)
        self.assertEqual(
            by_seed[29]["study_digest"],
            "6bb6a6436f2b13aff58a210b252bfcef310c8fd1cc76c2198d75cad819f0c499",
        )
        self.assertEqual(by_seed[83]["receipt"]["attempt_index"], 0)
        self.assertEqual(
            by_seed[83]["study_digest"],
            "fb06a593a65dc93ca619acf4288cea403aee3763573318d3be7c1e78cb8ecb7b",
        )

        for item in variants:
            self.assertEqual(item["status"], source_aware.PASS_STATUS)
            self.assertEqual(item["composition_evidence"]["status"], "PASS")
            self.assertEqual(item["source_envelope_evidence"]["status"], "PASS")
            self.assertTrue(all(item["source_envelope_evidence"]["checks"].values()))
            self.assertEqual(
                item["receipt"]["source_evidence"]["source_digest"],
                "a61207b23c441b2cc0becd165fa62289bb7e51065ae0d6fa56bf9f3cab036cc1",
            )
            self.assertEqual(item["receipt"]["source_evidence"]["retained_artifact_id"], 10428450742)

        seed7_rejections = by_seed[7]["rejected_attempts"]
        self.assertEqual(seed7_rejections[0]["composition_status"], "PASS")
        self.assertEqual(seed7_rejections[0]["source_envelope_status"], "HOLD")
        self.assertEqual(seed7_rejections[1]["composition_status"], "PASS")
        self.assertEqual(seed7_rejections[1]["source_envelope_status"], "HOLD")
        self.assertEqual(seed7_rejections[2]["composition_status"], "FAIL")
        self.assertEqual(seed7_rejections[2]["source_envelope_status"], "PASS")

    def test_source_gate_is_deterministic_for_same_seed(self):
        first = source_aware.generate_source_aware_variant(self.base, self.family, self.gate, 7)
        second = source_aware.generate_source_aware_variant(self.base, self.family, self.gate, 7)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], source_aware.PASS_STATUS)
        self.assertEqual(first["receipt"]["attempt_index"], 3)

    def test_unknown_target_fails_closed_before_generation(self):
        changed = copy.deepcopy(self.gate)
        changed["target_asset_id"] = "proxy:nature-tree-unknown"
        with self.assertRaisesRegex(ValueError, "unknown target asset"):
            source_aware.generate_source_aware_variant(self.base, self.family, changed, 29)

    def test_impossible_source_envelope_exhausts_without_bound_widening(self):
        control = source_aware.build_retained_source_failure_control(self.base, self.family, self.gate)
        self.assertEqual(control["schema"], source_aware.FAILURE_CONTROL_SCHEMA)
        self.assertEqual(control["observed_status"], source_aware.HOLD_STATUS)
        self.assertEqual(control["attempts_exhausted"], 3)
        self.assertEqual(control["rejected_attempt_count"], 3)
        self.assertEqual(control["last_source_envelope_status"], "HOLD")
        self.assertEqual(
            control["truth_boundary"],
            "SYNTHETIC_NEGATIVE_CONTROL_ONLY_NOT_A_RETAINED_ASSET_VARIANT_OR_SOURCE_REQUIREMENT",
        )

    def test_evidence_builder_retains_source_aware_variants_and_rejections(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = source_aware.build_source_aware_family(
                self.base_path, self.family_path, self.gate_path, temp
            )
            output = Path(temp)
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["variant_count"], 3)
            self.assertEqual(summary["unique_study_digest_count"], 3)
            self.assertEqual(summary["total_rejected_attempts"], 3)
            for seed in self.family["evidence_seeds"]:
                receipt_path = output / f"seed-{seed}-source-aware-receipt.json"
                self.assertTrue(receipt_path.exists())
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                self.assertEqual(receipt["status"], source_aware.PASS_STATUS)
                self.assertIn("proxy:nature-tree-west-a", (output / f"seed-{seed}.obj").read_text(encoding="utf-8"))
                self.assertIn("proxy:nature-tree-west-a", (output / f"seed-{seed}-top.svg").read_text(encoding="utf-8"))

            seed7 = json.loads((output / "seed-7-source-aware-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(seed7["receipt"]["attempt_index"], 3)
            self.assertEqual(len(seed7["rejected_attempts"]), 3)

            failure = json.loads(
                (output / "negative-control-impossible-source-envelope.json").read_text(encoding="utf-8")
            )
            self.assertEqual(failure["observed_status"], source_aware.HOLD_STATUS)
            self.assertEqual(failure["attempts_exhausted"], 3)
            self.assertEqual(summary["retained_failure_control"]["last_source_envelope_status"], "HOLD")


if __name__ == "__main__":
    unittest.main()
