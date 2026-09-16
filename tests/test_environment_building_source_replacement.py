import copy
import json
import os
import pathlib
import tempfile
import unittest

from tools import environment_building_source_replacement as mod

ROOT = pathlib.Path(__file__).resolve().parents[1]


class EnvironmentBuildingSourceReplacementTests(unittest.TestCase):
    def roots(self):
        names = {
            "base": "AXM_BASE_NATURE_ROOT",
            "compact": "AXM_COMPACT_NATURE_ROOT",
            "weather": "AXM_WEATHER_ROOT",
            "building": "AXM_BUILDING_ROOT",
        }
        values = {key: os.environ.get(env) for key, env in names.items()}
        if not all(values.values()):
            self.skipTest("exact cross-repo roots are supplied only by the dedicated Environment workflow")
        return values

    def test_exact_building_source_replaces_only_building_proxy(self):
        roots = self.roots()
        baseline, candidate, report = mod.build_payloads(
            ROOT / "examples/environment_building_source_replacement_001.json",
            roots["base"], roots["compact"], roots["weather"], roots["building"],
        )
        self.assertEqual(report["status"], "PASS_BUILDING_SOURCE_REPLACEMENT_STRUCTURE")
        self.assertTrue(all(report["checks"].values()), report)
        self.assertTrue(any(row["asset_id"] == "proxy:building-pavilion" for row in baseline["items"]))
        self.assertFalse(any(row["asset_id"] == "proxy:building-pavilion" for row in candidate["items"]))
        self.assertEqual(len(candidate["additional_source_meshes"]), len(baseline["additional_source_meshes"]) + 1)
        building = candidate["additional_source_meshes"][-1]
        self.assertEqual(building["asset_id"], "source:building:service-pavilion-001")
        self.assertEqual(len(building["vertices_source_xyz_m"]), 152)
        self.assertEqual(len(building["triangles"]), 228)
        self.assertEqual(candidate["additional_source_meshes"][:-1], baseline["additional_source_meshes"])
        self.assertEqual(candidate["sapling"], baseline["sapling"])
        self.assertEqual(candidate["weather_lines"], baseline["weather_lines"])
        self.assertEqual(candidate["cameras"], baseline["cameras"])
        self.assertEqual(candidate["readable_path"], baseline["readable_path"])

    def test_wrong_source_digest_fails_closed_without_mutating_source(self):
        roots = self.roots()
        manifest_path = ROOT / "examples/environment_building_source_replacement_001.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = copy.deepcopy(manifest)
        manifest["replacement"]["expected_pavilion_source_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            probe = pathlib.Path(tmp) / "manifest.json"
            probe.write_text(json.dumps(manifest), encoding="utf-8")
            _, _, report = mod.build_payloads(
                probe, roots["base"], roots["compact"], roots["weather"], roots["building"],
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["pavilion_source_digest_matches"])


if __name__ == "__main__":
    unittest.main()
