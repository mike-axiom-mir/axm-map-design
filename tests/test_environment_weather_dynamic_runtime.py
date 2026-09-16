from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from tools.environment_weather_dynamic_runtime import compare


class WeatherDynamicRuntimeComparisonTests(unittest.TestCase):
    def make_receipt(self, mode: str) -> dict:
        samples = []
        for index in range(9):
            runtime = {
                "objects_in_frame": 20,
                "primitives_in_frame": 2070,
                "draw_calls_in_frame": 20,
                "texture_mem_bytes": 12875715,
                "buffer_mem_bytes": 6452208,
            }
            update = {
                "submission_usec": 10,
                "node_instance_id": 100 if mode == "reuse_single_mesh" else 100 + index,
                "mesh_instance_id": 200 if mode == "reuse_single_mesh" else 200 + index,
                "material_instance_id": 300 if mode == "reuse_single_mesh" else 300 + index,
                "surface_count": 1,
                "streak_count": 36,
            }
            samples.append(
                {
                    "index": index,
                    "time_s": index / 16.0,
                    "field_digest": f"field-{index}",
                    "update": update,
                    "contexts": {
                        "path_eye": {"runtime": dict(runtime), "capture": {"state": "PASS"}},
                        "elevated_oblique": {"runtime": dict(runtime), "capture": {"state": "PASS"}},
                    },
                }
            )
        updates = 432
        control_creations = 9 + updates
        creations = 1 if mode == "reuse_single_mesh" else control_creations
        cycle_memory = [
            {
                "cycle": index,
                "buffer_mem_bytes": 6452208,
                "texture_mem_bytes": 12875715,
                "draw_calls_in_frame": 20,
                "primitives_in_frame": 2070,
                "objects_in_frame": 20,
            }
            for index in range(48)
        ]
        return {
            "schema": "axm.environment-weather-dynamic-runtime-observation/v0.1",
            "state": "PASS_SCOPED_SAME_PROCESS_WEATHER_UPDATE_OBSERVATION",
            "mode": mode,
            "receiving_head": "head",
            "environment_base_head": "environment-head",
            "sequence_digest": "sequence",
            "sampling_schedule_s": [0.0, 0.0625, 0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5],
            "static_receiving_state_digest": "static",
            "weather_source": {
                "head": "ca2eaba519e8449835b0ea6ef944b7080c3caa6a",
                "semantics": "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED",
            },
            "evidence_samples": samples,
            "stress": {
                "updates": updates,
                "submission": {
                    "count": updates,
                    "min_usec": 5,
                    "median_usec": 10,
                    "p95_usec": 20,
                    "max_usec": 40,
                    "total_usec": 4320,
                },
                "cycle_memory": cycle_memory,
            },
            "resource_creations": {
                "weather_nodes": creations,
                "weather_meshes": creations,
                "weather_materials": creations,
            },
            "update_semantics": mode,
        }

    def write_images(self, root: Path, mutate_candidate: tuple[str, int] | None = None) -> None:
        for context in ("path_eye", "elevated_oblique"):
            for index in range(9):
                body = f"{context}-{index}".encode("utf-8")
                (root / f"weather-dynamic-rebuild_control-{context}-{index:02d}.png").write_bytes(body)
                if mutate_candidate == (context, index):
                    body += b"-different"
                (root / f"weather-dynamic-reuse_single_mesh-{context}-{index:02d}.png").write_bytes(body)

    def test_passes_exact_resource_reuse_with_identical_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_images(root)
            result = compare(self.make_receipt("rebuild_control"), self.make_receipt("reuse_single_mesh"), root)
        self.assertEqual(result["state"], "PASS_REUSE_SINGLE_MESH_RESOURCE_CHURN_CONTRACT")
        self.assertTrue(all(result["checks"].values()), result)
        self.assertEqual(result["candidate"]["resource_creations"]["weather_nodes"], 1)
        self.assertEqual(result["visual_tradeoff"], "NONE_OBSERVED_IN_EXACT_RETAINED_PROOF_FRAMES")

    def test_holds_when_candidate_render_differs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_images(root, mutate_candidate=("path_eye", 4))
            result = compare(self.make_receipt("rebuild_control"), self.make_receipt("reuse_single_mesh"), root)
        self.assertEqual(result["state"], "HOLD_DYNAMIC_RUNTIME_COMPARISON")
        self.assertFalse(result["checks"]["render_bytes_identical_per_sample"])
        self.assertEqual(result["visual_tradeoff"], "REVIEW_REQUIRED_RENDER_OUTPUT_DIFFERS")

    def test_holds_on_candidate_resource_identity_churn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_images(root)
            candidate = self.make_receipt("reuse_single_mesh")
            candidate["evidence_samples"][5]["update"]["mesh_instance_id"] = 999
            result = compare(self.make_receipt("rebuild_control"), candidate, root)
        self.assertEqual(result["state"], "HOLD_DYNAMIC_RUNTIME_COMPARISON")
        self.assertFalse(result["checks"]["candidate_one_mesh_identity_across_samples"])

    def test_holds_on_runtime_counter_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_images(root)
            candidate = self.make_receipt("reuse_single_mesh")
            candidate["evidence_samples"][2]["contexts"]["elevated_oblique"]["runtime"]["draw_calls_in_frame"] += 1
            result = compare(self.make_receipt("rebuild_control"), candidate, root)
        self.assertEqual(result["state"], "HOLD_DYNAMIC_RUNTIME_COMPARISON")
        self.assertFalse(result["checks"]["runtime_counters_identical_per_sample"])

    def test_holds_on_source_identity_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_images(root)
            candidate = self.make_receipt("reuse_single_mesh")
            candidate["weather_source"] = copy.deepcopy(candidate["weather_source"])
            candidate["weather_source"]["head"] = "wrong"
            result = compare(self.make_receipt("rebuild_control"), candidate, root)
        self.assertEqual(result["state"], "HOLD_DYNAMIC_RUNTIME_COMPARISON")
        self.assertFalse(result["checks"]["weather_source_identity_preserved"])


if __name__ == "__main__":
    unittest.main()
