import copy
import json
import os
import pathlib
import tempfile
import unittest

from tools import environment_building_material_receiving as mod

ROOT = pathlib.Path(__file__).resolve().parents[1]


class EnvironmentBuildingMaterialReceivingTests(unittest.TestCase):
    def roots(self):
        names = {
            "base": "AXM_BASE_NATURE_ROOT",
            "compact": "AXM_COMPACT_NATURE_ROOT",
            "weather": "AXM_WEATHER_ROOT",
            "source": "AXM_BUILDING_SOURCE_ROOT",
            "materials": "AXM_BUILDING_MATERIAL_ROOT",
        }
        values = {key: os.environ.get(env) for key, env in names.items()}
        if not all(values.values()):
            self.skipTest("exact cross-repo roots are supplied only by the dedicated Materials workflow")
        return values

    def build(self, manifest=None):
        roots = self.roots()
        return mod.build_payloads(
            manifest or ROOT / "examples/environment_building_material_receiving_001.json",
            roots["base"],
            roots["compact"],
            roots["weather"],
            roots["source"],
            roots["materials"],
        )

    def test_exact_building_material_family_changes_only_surface_response(self):
        baseline, candidate, report = self.build()
        self.assertEqual(report["status"], "PASS_RECEIVING_SCENE_BUILDING_MATERIAL_TRANSFER_STRUCTURE")
        self.assertTrue(all(report["checks"].values()), report)
        self.assertEqual(report["building_source_head"], "4faa769b406bf3ad0ba9489a77141c27f122ce51")
        self.assertEqual(report["building_material_head"], "484ced313ba0337ea27eebd01c5677e72e8456af")
        self.assertEqual(report["pavilion_source_sha256"], "852038d2288ead9a0ee271e09f1a7f7207ec8fd74668e0c52e739e9a224f87d7")
        self.assertEqual(report["panel_source_sha256"], "df59fa135abc89f8c85317db1d6b9ce3d03920efc91271de61bfb6289a24c253")
        self.assertEqual(report["material_profile_sha256"], "85650897cde5bceaf1eb2d389c2a61d47c3d50a2000e429cac8a7846c8c153c4")
        self.assertEqual(report["placement_translation_max_error_m"], 0.0)
        self.assertEqual(report["component_alignment"]["component_alignment_max_error_m"], 0.0)
        self.assertEqual(sum(report["component_alignment"]["triangles_by_surface_role"].values()), 228)
        self.assertEqual(len(baseline["building_material_receiving"]["vertices_source_xyz_m"]), 152)
        self.assertEqual(len(candidate["building_material_receiving"]["vertices_source_xyz_m"]), 152)
        self.assertEqual(
            [row["triangles"] for row in baseline["building_material_receiving"]["surfaces"]],
            [row["triangles"] for row in candidate["building_material_receiving"]["surfaces"]],
        )
        self.assertEqual(
            [row["surface_role"] for row in candidate["building_material_receiving"]["surfaces"]],
            [
                "frame_galvanized",
                "infill_coating",
                "roof_membrane",
                "slab_mineral",
                "utility_panel_ochre",
            ],
        )
        self.assertNotEqual(baseline["scene_digest"], candidate["scene_digest"])

    def test_wrong_material_profile_digest_fails_closed(self):
        roots = self.roots()
        manifest_path = ROOT / "examples/environment_building_material_receiving_001.json"
        manifest = copy.deepcopy(json.loads(manifest_path.read_text(encoding="utf-8")))
        manifest["building_materials"]["expected_profile_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            probe = pathlib.Path(tmp) / "manifest.json"
            probe.write_text(json.dumps(manifest), encoding="utf-8")
            baseline, candidate, report = mod.build_payloads(
                probe,
                roots["base"],
                roots["compact"],
                roots["weather"],
                roots["source"],
                roots["materials"],
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["material_profile_digest_matches"])
        self.assertEqual(
            baseline["building_material_receiving"]["vertices_source_xyz_m"],
            candidate["building_material_receiving"]["vertices_source_xyz_m"],
        )


if __name__ == "__main__":
    unittest.main()
