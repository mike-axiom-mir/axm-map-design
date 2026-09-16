from __future__ import annotations

import json
import math
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_object_source_replacement as object_env


ROOT_KEYS = (
    "AXM_BASE_NATURE_ROOT",
    "AXM_COMPACT_NATURE_ROOT",
    "AXM_WEATHER_ROOT",
    "AXM_BUILDING_ROOT",
    "AXM_REAR_NATURE_ROOT",
    "AXM_MIGRATED_REAR_NATURE_ROOT",
    "AXM_OBJECT_ROOT",
)
HAS_EXACT_ROOTS = all(os.environ.get(key) for key in ROOT_KEYS)


class ObjectEnvironmentContractTests(unittest.TestCase):
    def test_manifest_keeps_object_replacement_narrow(self):
        manifest = object_env.load_manifest(ROOT / "examples" / "environment_object_source_replacement_001.json")
        replacement = manifest["replacement"]
        policy = manifest["comparison_policy"]
        self.assertEqual(replacement["target_asset_id"], "proxy:object-crate-west")
        self.assertEqual(replacement["expected_reserved_rotation_deg"], 18.0)
        self.assertEqual(replacement["placement_policy"], object_env.PLACEMENT_POLICY)
        self.assertEqual(policy["isolate_delta"], "WEST_OBJECT_PROXY_TO_EXACT_OBJECT_SOURCE_ONLY")
        self.assertFalse(policy["consume_object_materials_pr6"])
        self.assertFalse(policy["consume_object_rigging_pr15"])
        self.assertFalse(policy["consume_object_animation_pr10"])
        self.assertFalse(policy["consume_object_runtime_pr13"])
        self.assertFalse(policy["consume_object_uc_target_handoff_pr7"])
        self.assertFalse(policy["consume_map_materials_pr14"])
        self.assertFalse(policy["consume_map_vfx_pr16"])
        self.assertFalse(policy["consume_map_runtime_pr17"])

    def test_world_mesh_preserves_authored_rotation_without_scale(self):
        mesh = {
            "vertices": [
                [-0.4, -0.2, 0.0],
                [0.4, -0.2, 0.0],
                [0.4, 0.2, 0.4],
                [-0.4, 0.2, 0.4],
            ],
            "triangles": [[0, 1, 2], [0, 2, 3]],
        }
        target = {
            "position_m": [-3.4, 4.6, 0.55],
            "size_m": [1.1, 1.1, 1.1],
            "rotation_deg": 18.0,
        }
        world, bounds = object_env._world_mesh(mesh, target)
        self.assertEqual(world["triangles"], mesh["triangles"])
        self.assertAlmostEqual(bounds["min"][2], 0.0, places=9)
        self.assertAlmostEqual(bounds["max"][2], 0.4, places=9)
        expected_w = 0.8 * math.cos(math.radians(18.0)) + 0.4 * math.sin(math.radians(18.0))
        expected_d = 0.8 * math.sin(math.radians(18.0)) + 0.4 * math.cos(math.radians(18.0))
        self.assertAlmostEqual(bounds["size"][0], expected_w, places=9)
        self.assertAlmostEqual(bounds["size"][1], expected_d, places=9)
        self.assertAlmostEqual((bounds["min"][0] + bounds["max"][0]) * 0.5, -3.4, places=9)
        self.assertAlmostEqual((bounds["min"][1] + bounds["max"][1]) * 0.5, 4.6, places=9)

    @unittest.skipUnless(HAS_EXACT_ROOTS, "exact cross-repo roots are only provided by the dedicated receiving workflow")
    def test_exact_receiving_build_passes(self):
        baseline, candidate, report = object_env.build_payloads(
            ROOT / "examples" / "environment_object_source_replacement_001.json",
            os.environ["AXM_BASE_NATURE_ROOT"],
            os.environ["AXM_COMPACT_NATURE_ROOT"],
            os.environ["AXM_WEATHER_ROOT"],
            os.environ["AXM_BUILDING_ROOT"],
            os.environ["AXM_REAR_NATURE_ROOT"],
            os.environ["AXM_MIGRATED_REAR_NATURE_ROOT"],
            os.environ["AXM_OBJECT_ROOT"],
        )
        self.assertEqual(report["status"], object_env.STATUS)
        self.assertTrue(all(report["checks"].values()), json.dumps(report, indent=2))
        self.assertEqual(report["object_source"]["vertices"], 468)
        self.assertEqual(report["object_source"]["triangles"], 812)
        self.assertEqual(report["spacing_conflicts"], [])
        self.assertEqual(len(candidate["additional_source_meshes"]), len(baseline["additional_source_meshes"]) + 1)
        self.assertEqual(candidate["environment_object_replacement"]["reserved_proxy_rotation_deg"], 18.0)
        self.assertEqual(
            candidate["environment_rear_tree_culling_review"],
            baseline["environment_rear_tree_culling_review"],
        )
        self.assertEqual(
            [row for row in candidate["items"] if row["asset_id"] == "proxy:object-crate-east"],
            [row for row in baseline["items"] if row["asset_id"] == "proxy:object-crate-east"],
        )


if __name__ == "__main__":
    unittest.main()
