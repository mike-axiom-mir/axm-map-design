import tempfile
import unittest
from pathlib import Path

from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import environment_live_object_runtime_budget as mod


def runtime(head: str, with_object: bool, primitive_add: int = 0):
    static = [
        {"asset_id": "source:nature:compact-east-tree-neutral-001", "mesh_digest": "a", "proof_culling": "CULL_DISABLED", "triangles": 570, "vertices": 390},
        {"asset_id": "source:building:service-pavilion-001", "mesh_digest": "", "proof_culling": "CULL_DISABLED", "triangles": 228, "vertices": 152},
        {"asset_id": "source:nature:east-rear-tree-neutral-001", "mesh_digest": "b", "proof_culling": "CULL_BACK", "triangles": 570, "vertices": 390},
    ]
    if with_object:
        static.append({"asset_id": mod.EXPECTED_OBJECT_SOURCE_ID, "mesh_digest": "", "proof_culling": "CULL_DISABLED", "triangles": 812, "vertices": 468})
    samples = []
    for i in range(17):
        contexts = {}
        for name, draw, obj, prim in [("path_eye", 20, 20, 4392), ("elevated_oblique", 27, 27, 6150)]:
            contexts[name] = {
                "runtime": {
                    "draw_calls_in_frame": draw,
                    "objects_in_frame": obj,
                    "primitives_in_frame": prim + (mod.EXPECTED_PRIMITIVE_DELTA + primitive_add if with_object else 0),
                    "buffer_mem_bytes": 6532344 + (mod.EXPECTED_BUFFER_DELTA if with_object else 0),
                    "texture_mem_bytes": 12875715,
                }
            }
        samples.append({
            "index": i,
            "time_s": i / 32,
            "sampling_role": "TEST",
            "weather_field_digest": f"w{i}",
            "sapling_mesh_digest": f"s{i}",
            "contexts": contexts,
        })
    return {
        "receiving_head": head,
        "proof_runtime": "Godot 4.7.2 GL Compatibility",
        "samples": samples,
        "static_source_meshes": static,
    }


def payload(head: str):
    return {
        "receiving_head": head,
        "status": "PASS_LIVE_WORLD_OBJECT_SOURCE_COMPOSITION_STRUCTURE",
        "object_source_head": mod.EXPECTED_OBJECT_SOURCE_HEAD,
        "atmosphere_donor_head": mod.EXPECTED_BASELINE_HEAD,
    }


class BudgetTests(unittest.TestCase):
    def make_images(self, root: Path):
        baseline = root / "baseline"
        candidate = root / "candidate"
        baseline.mkdir()
        candidate.mkdir()
        for context in mod.CONTEXTS:
            for i in range(17):
                Image.new("RGB", (2, 2), (0, 0, 0)).save(baseline / f"atmosphere-current-{context}-{i:02d}.png")
                Image.new("RGB", (2, 2), (255, 0, 0)).save(candidate / f"atmosphere-current-{context}-{i:02d}.png")
        return baseline, candidate

    def test_exact_one_slot_budget_passes(self):
        with tempfile.TemporaryDirectory() as td:
            baseline_images, candidate_images = self.make_images(Path(td))
            head = "candidate-head"
            result = mod.compare(
                runtime(mod.EXPECTED_BASELINE_HEAD, False),
                runtime(head, True),
                payload(head),
                baseline_images,
                candidate_images,
                head,
            )
            self.assertEqual(result["state"], mod.STATUS)
            self.assertTrue(all(result["checks"].values()))

    def test_primitive_budget_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            baseline_images, candidate_images = self.make_images(Path(td))
            head = "candidate-head"
            result = mod.compare(
                runtime(mod.EXPECTED_BASELINE_HEAD, False),
                runtime(head, True, primitive_add=1),
                payload(head),
                baseline_images,
                candidate_images,
                head,
            )
            self.assertEqual(result["state"], "FAIL")
            self.assertFalse(result["checks"]["path_eye_primitive_delta_exact"])
            self.assertFalse(result["checks"]["elevated_oblique_primitive_delta_exact"])


if __name__ == "__main__":
    unittest.main()
