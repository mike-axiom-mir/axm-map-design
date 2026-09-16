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


class EnvironmentMultiSourceAwareVariationTests(unittest.TestCase):
    def setUp(self):
        self.base_path = ROOT / "examples/environment_baseline_001.json"
        self.family_path = ROOT / "examples/environment_variation_family_001.json"
        self.gate_set_path = ROOT / "examples/environment_current_source_gate_set_001.json"
        self.base = composition.load_study(self.base_path)
        self.family = variation.load_family(self.family_path)
        self.gate_set = source_aware.load_gate_set(self.gate_set_path)

    def test_gate_set_names_four_independently_proven_receiving_dependencies(self):
        source_aware.validate_gate_set(self.base, self.family, self.gate_set)
        self.assertEqual(self.gate_set["schema"], source_aware.GATE_SET_SCHEMA)
        self.assertEqual(len(self.gate_set["gates"]), 4)
        self.assertEqual(
            {gate["target_asset_id"] for gate in self.gate_set["gates"]},
            {
                "proxy:nature-tree-west-a",
                "proxy:nature-tree-east-b",
                "proxy:nature-tree-east-a",
                "proxy:object-crate-west",
            },
        )
        by_id = {gate["gate_id"]: gate for gate in self.gate_set["gates"]}
        self.assertEqual(
            by_id["west-object-source-envelope-001"]["source_rotation_policy"],
            source_aware.FOLLOW_TARGET_Z_ROTATION,
        )
        self.assertEqual(
            by_id["compact-east-source-envelope-001"]["required_source_size_m"],
            [1.6, 1.6, 4.0],
        )

    def test_four_source_sweep_keeps_three_materially_distinct_outputs(self):
        summary, variants = source_aware.generate_source_aware_gate_set_sweep(
            self.base, self.family, self.gate_set, [7, 29, 83]
        )
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["gate_count"], 4)
        self.assertEqual(summary["variant_count"], 3)
        self.assertEqual(summary["unique_study_digest_count"], 3)
        self.assertEqual(summary["total_rejected_attempts"], 11)

        by_seed = {item["receipt"]["seed"]: item for item in variants}
        self.assertEqual(by_seed[7]["receipt"]["attempt_index"], 11)
        self.assertEqual(by_seed[7]["receipt"]["rejected_attempt_count"], 11)
        self.assertEqual(by_seed[29]["receipt"]["attempt_index"], 0)
        self.assertEqual(by_seed[83]["receipt"]["attempt_index"], 0)
        self.assertEqual(
            by_seed[29]["study_digest"],
            "6bb6a6436f2b13aff58a210b252bfcef310c8fd1cc76c2198d75cad819f0c499",
        )
        self.assertEqual(
            by_seed[83]["study_digest"],
            "fb06a593a65dc93ca619acf4288cea403aee3763573318d3be7c1e78cb8ecb7b",
        )

        for item in variants:
            self.assertEqual(item["status"], source_aware.PASS_STATUS)
            self.assertEqual(item["composition_evidence"]["status"], "PASS")
            self.assertEqual(len(item["source_envelope_evidence"]), 4)
            self.assertTrue(all(row["status"] == "PASS" for row in item["source_envelope_evidence"]))
            self.assertEqual(set(item["receipt"]["source_evidence"]), {
                "west-sapling-source-envelope-001",
                "compact-east-source-envelope-001",
                "rear-east-source-envelope-001",
                "west-object-source-envelope-001",
            })

    def test_seed7_rejection_trail_proves_multiple_source_dependencies_are_active(self):
        result = source_aware.generate_source_aware_gate_set_variant(
            self.base, self.family, self.gate_set, 7
        )
        self.assertEqual(result["status"], source_aware.PASS_STATUS)
        self.assertEqual(result["receipt"]["attempt_index"], 11)
        rejected = result["rejected_attempts"]
        self.assertEqual(len(rejected), 11)

        holding = {
            gate_id
            for row in rejected
            for gate_id, status in row["source_envelope_statuses"].items()
            if status == "HOLD"
        }
        self.assertIn("west-sapling-source-envelope-001", holding)
        self.assertIn("compact-east-source-envelope-001", holding)
        self.assertIn("rear-east-source-envelope-001", holding)
        self.assertNotIn("west-object-source-envelope-001", holding)
        self.assertTrue(any(row["composition_status"] == "FAIL" for row in rejected))

    def test_object_source_uses_target_z_rotation_without_mutating_candidate(self):
        candidate = variation.generate_variant(self.base, self.family, 29)["study"]
        before = copy.deepcopy(candidate)
        object_gate = next(
            gate for gate in self.gate_set["gates"]
            if gate["gate_id"] == "west-object-source-envelope-001"
        )
        evidence = source_aware.evaluate_source_envelope(candidate, object_gate)
        target = next(
            item for item in candidate["items"]
            if item["asset_id"] == "proxy:object-crate-west"
        )
        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(evidence["source_rotation_policy"], source_aware.FOLLOW_TARGET_Z_ROTATION)
        self.assertEqual(evidence["source_rotation_deg"], target["rotation_deg"])
        self.assertEqual(candidate, before)

    def test_unsupported_rotation_policy_fails_before_generation(self):
        changed = copy.deepcopy(self.gate_set)
        object_gate = next(
            gate for gate in changed["gates"]
            if gate["gate_id"] == "west-object-source-envelope-001"
        )
        object_gate["source_rotation_policy"] = "INFER_FROM_CATEGORY"
        with self.assertRaisesRegex(ValueError, "unsupported source_rotation_policy"):
            source_aware.generate_source_aware_gate_set_variant(
                self.base, self.family, changed, 29
            )

    def test_one_impossible_declared_dependency_holds_the_whole_set(self):
        control = source_aware.build_retained_gate_set_failure_control(
            self.base, self.family, self.gate_set
        )
        self.assertEqual(control["schema"], source_aware.GATE_SET_FAILURE_CONTROL_SCHEMA)
        self.assertEqual(control["observed_status"], source_aware.HOLD_STATUS)
        self.assertEqual(control["failure_probe_gate_id"], "compact-east-source-envelope-001")
        self.assertEqual(control["attempts_exhausted"], 3)
        self.assertEqual(control["rejected_attempt_count"], 3)
        self.assertEqual(control["probe_statuses"], ["HOLD", "HOLD", "HOLD"])

    def test_gate_set_builder_retains_receipts_geometry_views_and_failure_control(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = source_aware.build_source_aware_gate_set_family(
                self.base_path, self.family_path, self.gate_set_path, temp
            )
            output = Path(temp)
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["gate_count"], 4)
            self.assertEqual(summary["total_rejected_attempts"], 11)
            for seed in self.family["evidence_seeds"]:
                receipt_path = output / f"seed-{seed}-source-aware-receipt.json"
                self.assertTrue(receipt_path.exists())
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                self.assertEqual(receipt["status"], source_aware.PASS_STATUS)
                self.assertTrue((output / f"seed-{seed}.obj").exists())
                self.assertTrue((output / f"seed-{seed}-top.svg").exists())

            seed7 = json.loads((output / "seed-7-source-aware-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(seed7["receipt"]["attempt_index"], 11)
            self.assertEqual(len(seed7["rejected_attempts"]), 11)

            failure = json.loads(
                (output / "negative-control-one-impossible-source-dependency.json").read_text(encoding="utf-8")
            )
            self.assertEqual(failure["observed_status"], source_aware.HOLD_STATUS)
            self.assertEqual(failure["probe_statuses"], ["HOLD", "HOLD", "HOLD"])
            self.assertEqual(
                summary["retained_failure_control"]["failure_probe_gate_id"],
                "compact-east-source-envelope-001",
            )


if __name__ == "__main__":
    unittest.main()
