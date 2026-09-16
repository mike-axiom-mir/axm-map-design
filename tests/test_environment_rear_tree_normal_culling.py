import copy
import json
import os
import pathlib
import tempfile
import unittest

from tools import environment_rear_tree_normal_culling as mod

ROOT = pathlib.Path(__file__).resolve().parents[1]


class EnvironmentRearTreeNormalCullingTests(unittest.TestCase):
    def roots(self):
        names = {
            "base": "AXM_BASE_NATURE_ROOT",
            "compact": "AXM_COMPACT_NATURE_ROOT",
            "weather": "AXM_WEATHER_ROOT",
            "building": "AXM_BUILDING_ROOT",
            "historical": "AXM_REAR_NATURE_ROOT",
            "migrated": "AXM_MIGRATED_REAR_NATURE_ROOT",
        }
        values = {key: os.environ.get(env) for key, env in names.items()}
        if not all(values.values()):
            self.skipTest("exact cross-repo roots are supplied only by the dedicated Environment workflow")
        return values

    def build(self, manifest=None):
        roots = self.roots()
        return mod.build_payloads(
            manifest or ROOT / "examples/environment_rear_tree_normal_culling_001.json",
            roots["base"],
            roots["compact"],
            roots["weather"],
            roots["building"],
            roots["historical"],
            roots["migrated"],
        )

    def test_migrated_source_changes_only_rear_triangle_winding_and_lineage(self):
        historical, migrated, report = self.build()
        self.assertEqual(report["status"], mod.STATUS)
        self.assertTrue(all(report["checks"].values()), report)
        target = report["target_asset_id"]
        old = [row for row in historical["additional_source_meshes"] if row["asset_id"] == target][0]
        new = [row for row in migrated["additional_source_meshes"] if row["asset_id"] == target][0]
        self.assertEqual(old["source_digest"], new["source_digest"])
        self.assertEqual(old["mesh_digest"], "d7fc5deaa1c12d1d8c7d7b6dc95bf1e8544ce26140ee2e4a7d2c67a2c4133e48")
        self.assertEqual(new["mesh_digest"], "aa9d450a78fef722672ea9af0f9aca98b4c1a0ca3705661784f5f61f3e9b6a31")
        self.assertEqual(old["vertices_source_xyz_m"], new["vertices_source_xyz_m"])
        self.assertEqual(report["topology_delta"]["changed_triangle_rows"], 260)
        self.assertFalse(report["topology_delta"]["vertices_changed"])
        self.assertFalse(report["topology_delta"]["triangle_membership_changed"])
        self.assertEqual(historical["items"], migrated["items"])
        self.assertEqual(historical["sapling"], migrated["sapling"])
        self.assertEqual(historical["weather_lines"], migrated["weather_lines"])
        self.assertEqual(historical["cameras"], migrated["cameras"])
        self.assertEqual(historical["readable_path"], migrated["readable_path"])

    def test_culling_review_targets_only_rear_tree(self):
        historical, migrated, report = self.build()
        self.assertEqual(report["status"], mod.STATUS)
        for scene in (historical, migrated):
            review = scene["environment_rear_tree_culling_review"]
            self.assertEqual(review["target_asset_id"], "source:nature:east-rear-tree-neutral-001")
            self.assertEqual(review["target_cull_mode"], "BACK")
            self.assertEqual(review["other_source_mesh_cull_mode"], "DISABLED")
        target = report["target_asset_id"]
        old_others = [row for row in historical["additional_source_meshes"] if row["asset_id"] != target]
        new_others = [row for row in migrated["additional_source_meshes"] if row["asset_id"] != target]
        self.assertEqual(old_others, new_others)

    def test_wrong_migrated_digest_fails_closed(self):
        roots = self.roots()
        manifest_path = ROOT / "examples/environment_rear_tree_normal_culling_001.json"
        manifest = copy.deepcopy(json.loads(manifest_path.read_text(encoding="utf-8")))
        manifest["migrated_source"]["mesh_digest"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            probe = pathlib.Path(tmp) / "manifest.json"
            probe.write_text(json.dumps(manifest), encoding="utf-8")
            _, _, report = mod.build_payloads(
                probe,
                roots["base"], roots["compact"], roots["weather"], roots["building"], roots["historical"], roots["migrated"],
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["migrated_mesh_digest_matches"])

    def test_vertex_change_is_not_accepted_as_winding_only(self):
        roots = self.roots()
        manifest_path = ROOT / "examples/environment_rear_tree_normal_culling_001.json"
        manifest = copy.deepcopy(json.loads(manifest_path.read_text(encoding="utf-8")))
        manifest["target"]["expected_vertices"] = 391
        with tempfile.TemporaryDirectory() as tmp:
            probe = pathlib.Path(tmp) / "manifest.json"
            probe.write_text(json.dumps(manifest), encoding="utf-8")
            _, _, report = mod.build_payloads(
                probe,
                roots["base"], roots["compact"], roots["weather"], roots["building"], roots["historical"], roots["migrated"],
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["vertex_count_preserved"])


if __name__ == "__main__":
    unittest.main()
