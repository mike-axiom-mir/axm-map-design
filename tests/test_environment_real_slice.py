import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_real_slice as real_slice


class EnvironmentRealSliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nature_root = Path(os.environ["AXM_NATURE_ROOT"])
        cls.weather_root = Path(os.environ["AXM_WEATHER_ROOT"])
        cls.manifest_path = ROOT / "examples/environment_real_slice_001.json"
        cls.manifest = real_slice.load_manifest(cls.manifest_path)

    def evaluate(self, manifest=None, placement_xy=None):
        return real_slice.evaluate_integration(
            ROOT,
            manifest or self.manifest,
            self.nature_root,
            self.weather_root,
            placement_xy=placement_xy,
        )

    def test_exact_source_owned_slice_passes(self):
        report, variant, target, world_mesh, _, _, _ = self.evaluate()
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["base_variant"]["seed"], 29)
        self.assertEqual(report["base_variant"]["attempt_index"], 0)
        self.assertEqual(report["replacement"]["nature_vertices"], 390)
        self.assertEqual(report["replacement"]["nature_triangles"], 570)
        self.assertEqual(target["asset_id"], "proxy:nature-tree-west-a")
        self.assertEqual(len(world_mesh["vertices"]), 390)
        self.assertEqual(len(world_mesh["triangles"]), 570)
        self.assertEqual(len(variant["items"]), 8)

    def test_generated_scene_replaces_only_target_proxy_with_real_triangles(self):
        report, variant, target, world_mesh, _, _, _ = self.evaluate()
        self.assertEqual(report["status"], "PASS")
        obj = real_slice.build_obj(variant, target, world_mesh)
        self.assertIn("o source:nature:sapling-neutral-001", obj)
        self.assertNotIn("o proxy:nature-tree-west-a\n", obj)
        self.assertIn("o proxy:nature-tree-west-b", obj)
        triangle_faces = [line for line in obj.splitlines() if line.startswith("f ") and len(line.split()) == 4]
        self.assertGreaterEqual(len(triangle_faces), 570)

    def test_wrong_pinned_nature_digest_fails_closed(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["nature_replacement"]["expected_source_digest"] = "0" * 64
        report, *_ = self.evaluate(manifest)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["nature_source_digest_matches"])

    def test_real_asset_moved_into_readable_path_fails(self):
        report, *_ = self.evaluate(placement_xy=(0.0, 0.0))
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["readable_path_unblocked_after_replacement"])

    def test_weather_cannot_be_relabelled_physical(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["weather_overlay"]["relationship"] = "PHYSICAL_WEATHER"
        report, *_ = self.evaluate(manifest)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["weather_stays_visual_only"])

    def test_evidence_build_retains_before_after_scene_and_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = real_slice.build(
                self.manifest_path,
                self.nature_root,
                self.weather_root,
                tmp,
            )
            self.assertEqual(report["status"], "PASS")
            for name in (
                "before_seed29_proxy.svg",
                "after_source_slice.svg",
                "comparison.svg",
                "scene.obj",
                "evidence.json",
            ):
                self.assertTrue((Path(tmp) / name).is_file(), name)
            retained = json.loads((Path(tmp) / "evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(retained["status"], "PASS")
            self.assertEqual(retained["replacement"]["source_head"], "fbc202449981f2bac153951c561ed0ed6120c936")
            self.assertEqual(retained["weather_overlay"]["source_head"], "ca2eaba519e8449835b0ea6ef944b7080c3caa6a")


if __name__ == "__main__":
    unittest.main()
