from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.environment_east_tree_runtime_budget import evaluate


def receipt(variant: str, *, draw: int = 20, objects: int = 20, primitives: int = 2070, buffer_bytes: int = 6452208) -> dict:
    additional = []
    proxy_count = 7
    if variant == "candidate":
        additional = [{"asset_id": "source:nature:compact-east-tree-neutral-001", "vertices": 390, "triangles": 570, "surfaces": 1}]
        proxy_count = 6
    return {
        "schema": "axm.environment-east-tree-runtime-observation/v0.1",
        "state": "PASS_SCOPED_EAST_TREE_RUNTIME_OBSERVATION",
        "variant": variant,
        "receiving_head": "head",
        "scene_digest": "candidate" if variant == "candidate" else "baseline",
        "godot_version": {"string": "4.7.2.stable"},
        "sapling": {"vertices": 390, "triangles": 570, "surfaces": 1},
        "additional_source_meshes": additional,
        "weather": {"streaks": 36, "surfaces": 1},
        "proxy_count": proxy_count,
        "contexts": {
            "path_eye": {
                "camera": {"id": "path"},
                "runtime": {
                    "objects_in_frame": objects,
                    "primitives_in_frame": primitives,
                    "draw_calls_in_frame": draw,
                    "texture_mem_bytes": 1000,
                    "buffer_mem_bytes": buffer_bytes,
                },
            },
            "elevated_oblique": {
                "camera": {"id": "oblique"},
                "runtime": {
                    "objects_in_frame": objects + 7,
                    "primitives_in_frame": primitives + 84,
                    "draw_calls_in_frame": draw + 7,
                    "texture_mem_bytes": 1000,
                    "buffer_mem_bytes": buffer_bytes,
                },
            },
        },
    }


class EastTreeRuntimeBudgetTests(unittest.TestCase):
    def replacement(self) -> dict:
        return {
            "status": "PASS_EAST_FOREGROUND_SOURCE_REPLACEMENT_STRUCTURE",
            "receiving_head": "head",
            "baseline_scene_digest": "baseline",
            "candidate_scene_digest": "candidate",
        }

    def render_files(self, root: Path) -> None:
        (root / "runtime-east-tree-baseline-path_eye.png").write_bytes(b"same")
        (root / "runtime-east-tree-candidate-path_eye.png").write_bytes(b"same")
        (root / "runtime-east-tree-baseline-elevated_oblique.png").write_bytes(b"proxy")
        (root / "runtime-east-tree-candidate-elevated_oblique.png").write_bytes(b"source")

    def test_passes_one_slot_contract_and_reports_cost(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.render_files(root)
            baseline = receipt("baseline")
            candidate = receipt("candidate", primitives=3744, buffer_bytes=6485664)
            candidate["contexts"]["elevated_oblique"]["runtime"]["primitives_in_frame"] += 1674
            row = evaluate(self.replacement(), baseline, candidate, root)
            self.assertEqual(row["status"], "PASS_EAST_TREE_ONE_SLOT_RUNTIME_BUDGET")
            self.assertEqual(row["runtime_deltas_candidate_minus_proxy"]["path_eye"]["draw_calls_in_frame"], 0)
            self.assertEqual(row["runtime_deltas_candidate_minus_proxy"]["path_eye"]["buffer_mem_bytes"], 33456)
            self.assertTrue(row["checks"]["path_eye_render_remains_identical"])
            self.assertTrue(row["checks"]["elevated_oblique_render_contains_expected_delta"])

    def test_rejects_draw_call_increase(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.render_files(root)
            baseline = receipt("baseline")
            candidate = receipt("candidate", draw=21)
            row = evaluate(self.replacement(), baseline, candidate, root)
            self.assertEqual(row["status"], "FAIL")
            self.assertFalse(row["checks"]["draw_slot_preserved_both_cameras"])

    def test_rejects_wrong_source_shape(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.render_files(root)
            baseline = receipt("baseline")
            candidate = receipt("candidate")
            candidate["additional_source_meshes"][0]["triangles"] = 569
            row = evaluate(self.replacement(), baseline, candidate, root)
            self.assertEqual(row["status"], "FAIL")
            self.assertFalse(row["checks"]["candidate_has_one_exact_compact_source"])


if __name__ == "__main__":
    unittest.main()
