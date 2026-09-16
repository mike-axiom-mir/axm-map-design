import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import environment_composition as composition
import environment_variation as variation


class EnvironmentVariationTests(unittest.TestCase):
    def setUp(self):
        self.base_path = ROOT / "examples/environment_baseline_001.json"
        self.family_path = ROOT / "examples/environment_variation_family_001.json"
        self.base = composition.load_study(self.base_path)
        self.family = variation.load_family(self.family_path)

    def test_same_seed_is_byte_stable_and_preserves_provenance(self):
        first = variation.generate_variant(self.base, self.family, 29)
        second = variation.generate_variant(self.base, self.family, 29)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "PASS")
        self.assertEqual(first["receipt"]["base_source_digest"], composition.digest(self.base))
        self.assertEqual(first["receipt"]["family_digest"], composition.digest(self.family))
        self.assertEqual(first["receipt"]["seed"], 29)

    def test_three_materially_different_seeds_pass_the_same_composition_gate(self):
        seeds = [7, 29, 83]
        outputs = [variation.generate_variant(self.base, self.family, seed) for seed in seeds]
        self.assertTrue(all(item["status"] == "PASS" for item in outputs))
        self.assertEqual(len({item["study_digest"] for item in outputs}), 3)

        rule_ids = {rule["asset_id"] for rule in self.family["rules"]}
        position_signatures = []
        for output in outputs:
            report = composition.evaluate(output["study"])
            self.assertEqual(report["status"], "PASS")
            by_id = {item["asset_id"]: item for item in output["study"]["items"]}
            baseline_by_id = {item["asset_id"]: item for item in self.base["items"]}
            changed = 0
            for asset_id in rule_ids:
                before = baseline_by_id[asset_id]["position"]
                after = by_id[asset_id]["position"]
                if abs(before[0] - after[0]) + abs(before[1] - after[1]) > 0.05:
                    changed += 1
            self.assertGreaterEqual(changed, 5)
            position_signatures.append(
                tuple((asset_id, tuple(by_id[asset_id]["position"][:2])) for asset_id in sorted(rule_ids))
            )
        self.assertEqual(len(set(position_signatures)), 3)

    def test_generator_only_changes_declared_nature_and_object_rules(self):
        output = variation.generate_variant(self.base, self.family, 7)
        rule_ids = {rule["asset_id"] for rule in self.family["rules"]}
        baseline_by_id = {item["asset_id"]: item for item in self.base["items"]}
        output_by_id = {item["asset_id"]: item for item in output["study"]["items"]}

        for asset_id, baseline in baseline_by_id.items():
            if asset_id not in rule_ids:
                self.assertEqual(output_by_id[asset_id], baseline)

        self.assertEqual(output["study"]["weather_context"], self.base["weather_context"])
        self.assertEqual(output["study"]["readable_path"], self.base["readable_path"])
        self.assertEqual(output["study"]["required_asset_kinds"], self.base["required_asset_kinds"])

    def test_impossible_scale_exhausts_bounded_attempts_and_holds(self):
        impossible = copy.deepcopy(self.family)
        impossible["max_attempts"] = 3
        for rule in impossible["rules"]:
            rule["xy_jitter_m"] = [0.0, 0.0]
            rule["uniform_scale"] = [2.0, 2.0]
            rule["rotation_deg"] = [0.0, 0.0]
        result = variation.generate_variant(self.base, impossible, 11)
        self.assertEqual(result["status"], "HOLD")
        self.assertIsNone(result["study"])
        self.assertEqual(result["receipt"]["attempts_exhausted"], 3)
        self.assertEqual(result["evidence"]["status"], "FAIL")

    def test_rule_cannot_modify_building_or_map_authority(self):
        changed = copy.deepcopy(self.family)
        changed["rules"][0]["asset_id"] = "proxy:building-pavilion"
        with self.assertRaisesRegex(ValueError, "cannot modify owned kind"):
            variation.generate_variant(self.base, changed, 7)

    def test_evidence_build_retains_three_distinct_variants_and_views(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = variation.build_family(self.base_path, self.family_path, temp)
            output = Path(temp)
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["variant_count"], 3)
            self.assertEqual(summary["unique_study_digest_count"], 3)
            for seed in self.family["evidence_seeds"]:
                receipt = json.loads((output / f"seed-{seed}-receipt.json").read_text(encoding="utf-8"))
                self.assertEqual(receipt["status"], "PASS")
                self.assertIn("proxy:nature-tree-west-a", (output / f"seed-{seed}.obj").read_text(encoding="utf-8"))
                svg = (output / f"seed-{seed}-top.svg").read_text(encoding="utf-8")
                self.assertIn('stroke-dasharray="6 4"', svg)
                self.assertIn("proxy:object-crate-east", svg)


if __name__ == "__main__":
    unittest.main()
