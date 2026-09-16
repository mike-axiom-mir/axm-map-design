import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_east_tree_replacement as east


class EnvironmentEastTreeReplacementTests(unittest.TestCase):
    def test_manifest_rejects_wrong_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps({"schema": "wrong"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                east.load_manifest(path)

    def test_world_mesh_preserves_target_center_and_grounds_source(self):
        mesh = {
            "vertices": [
                [-1.0, -0.5, -0.2],
                [1.0, -0.5, 2.8],
                [1.0, 0.5, 2.8],
                [-1.0, 0.5, -0.2],
            ],
            "triangles": [[0, 1, 2], [0, 2, 3]],
        }
        target = {"position": [7.2, -3.5, 2.0], "size": [2.4, 1.4, 4.0]}
        world, bounds = east._world_mesh(mesh, target)
        self.assertAlmostEqual(7.2, (bounds["min"][0] + bounds["max"][0]) * 0.5)
        self.assertAlmostEqual(-3.5, (bounds["min"][1] + bounds["max"][1]) * 0.5)
        self.assertAlmostEqual(0.0, bounds["min"][2])
        self.assertEqual(mesh["triangles"], world["triangles"])

    def test_preservation_gate_rejects_unrelated_item_mutation(self):
        baseline = [
            {"asset_id": "proxy:nature-tree-east-b", "kind": "nature-proxy", "size_m": [1, 1, 1]},
            {"asset_id": "proxy:building-a", "kind": "building-proxy", "size_m": [2, 2, 2]},
        ]
        candidate = [copy.deepcopy(baseline[1])]
        self.assertTrue(
            east._preserved_items_except_target(
                baseline, candidate, "proxy:nature-tree-east-b"
            )
        )
        candidate[0]["size_m"] = [3, 2, 2]
        self.assertFalse(
            east._preserved_items_except_target(
                baseline, candidate, "proxy:nature-tree-east-b"
            )
        )

    def test_clearance_intersection_fails_closed(self):
        source = (0.0, 1.0, 0.0, 1.0)
        neighbor = (1.25, 2.25, 0.0, 1.0)
        self.assertFalse(east._intersects(source, neighbor, 0.2))
        self.assertTrue(east._intersects(source, neighbor, 0.3))

    def test_inside_rejects_hidden_envelope_overflow(self):
        reserved = (0.0, 1.6, 0.0, 1.6)
        self.assertTrue(east._inside((0.05, 1.55, 0.2, 1.3), reserved))
        self.assertFalse(east._inside((-0.01, 1.55, 0.2, 1.3), reserved))


if __name__ == "__main__":
    unittest.main()
