import copy
import json
import os
import pathlib
import tempfile
import unittest

from tools import environment_rear_tree_source_replacement as mod

ROOT = pathlib.Path(__file__).resolve().parents[1]


class EnvironmentRearTreeSourceReplacementTests(unittest.TestCase):
    def roots(self):
        names = {
            "base": "AXM_BASE_NATURE_ROOT",
            "compact": "AXM_COMPACT_NATURE_ROOT",
            "weather": "AXM_WEATHER_ROOT",
            "building": "AXM_BUILDING_ROOT",
            "rear": "AXM_REAR_NATURE_ROOT",
        }
        values = {key: os.environ.get(env) for key, env in names.items()}
        if not all(values.values()):
            self.skipTest("exact cross-repo roots are supplied only by the dedicated Environment workflow")
        return values

    def test_exact_rear_source_replaces_only_rear_proxy_after_building_state(self):
        roots = self.roots()
        baseline, candidate, report = mod.build_payloads(
            ROOT / "examples/environment_rear_tree_source_replacement_001.json",
            roots["base"], roots["compact"], roots["weather"], roots["building"], roots["rear"],
        )
        self.assertEqual(report["status"], "PASS_REAR_RIGHT_NATURE_SOURCE_REPLACEMENT_STRUCTURE")
        self.assertTrue(all(report["checks"].values()), report)
        self.assertTrue(any(row["asset_id"] == "proxy:nature-tree-east-a" for row in baseline["items"]))
        self.assertFalse(any(row["asset_id"] == "proxy:nature-tree-east-a" for row in candidate["items"]))
        self.assertEqual(candidate["items"], [row for row in baseline["items"] if row["asset_id"] != "proxy:nature-tree-east-a"])
        self.assertEqual(candidate["additional_source_meshes"][:-1], baseline["additional_source_meshes"])
        rear = candidate["additional_source_meshes"][-1]
        self.assertEqual(rear["asset_id"], "source:nature:east-rear-tree-neutral-001")
        self.assertEqual(len(rear["vertices_source_xyz_m"]), 390)
        self.assertEqual(len(rear["triangles"]), 570)
        self.assertEqual(rear["mesh_digest"], "d7fc5deaa1c12d1d8c7d7b6dc95bf1e8544ce26140ee2e4a7d2c67a2c4133e48")
        self.assertEqual(candidate["sapling"], baseline["sapling"])
        self.assertEqual(candidate["weather_lines"], baseline["weather_lines"])
        self.assertEqual(candidate["cameras"], baseline["cameras"])
        self.assertEqual(candidate["readable_path"], baseline["readable_path"])
        self.assertTrue(any(row["asset_id"] == "source:building:service-pavilion-001" for row in candidate["additional_source_meshes"]))
        self.assertTrue(any(row["asset_id"] == "source:nature:compact-east-tree-neutral-001" for row in candidate["additional_source_meshes"]))

    def test_wrong_rear_source_digest_fails_closed_without_mutating_source(self):
        roots = self.roots()
        manifest_path = ROOT / "examples/environment_rear_tree_source_replacement_001.json"
        manifest = copy.deepcopy(json.loads(manifest_path.read_text(encoding="utf-8")))
        manifest["replacement"]["expected_source_digest"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            probe = pathlib.Path(tmp) / "manifest.json"
            probe.write_text(json.dumps(manifest), encoding="utf-8")
            _, _, report = mod.build_payloads(
                probe,
                roots["base"], roots["compact"], roots["weather"], roots["building"], roots["rear"],
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["rear_source_digest_matches"])

    def test_geometry_reindex_candidate_cannot_be_silently_relabelled_as_consumed(self):
        roots = self.roots()
        manifest_path = ROOT / "examples/environment_rear_tree_source_replacement_001.json"
        manifest = copy.deepcopy(json.loads(manifest_path.read_text(encoding="utf-8")))
        manifest["comparison_policy"]["geometry_reindex_candidate_consumed"] = True
        with tempfile.TemporaryDirectory() as tmp:
            probe = pathlib.Path(tmp) / "manifest.json"
            probe.write_text(json.dumps(manifest), encoding="utf-8")
            _, _, report = mod.build_payloads(
                probe,
                roots["base"], roots["compact"], roots["weather"], roots["building"], roots["rear"],
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["geometry_reindex_candidate_not_consumed"])


if __name__ == "__main__":
    unittest.main()
