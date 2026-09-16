from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import environment_runtime_budget as runtime_budget


class EnvironmentRuntimeBudgetTests(unittest.TestCase):
    def payload(self) -> dict:
        scene = {
            "scene_digest": "scene-001",
            "receiving_head": "head-001",
            "source_integration": {
                "status": "PASS",
                "base_variant": {"seed": 29, "study_digest": "variant-001"},
                "replacement": {
                    "target_asset_id": "proxy:nature-tree-west-a",
                    "reserved_proxy_position_m": [-5.0, 1.5, 2.5],
                    "reserved_proxy_size_m": [2.2, 2.2, 5.2],
                    "reserved_proxy_rotation_deg": 4.0,
                },
            },
            "cameras": {"path_eye": {}, "elevated_oblique": {}},
            "sapling": {
                "vertices_source_xyz_m": [[0.0, 0.0, 0.0] for _ in range(390)],
                "triangles": [[0, 1, 2] for _ in range(570)],
            },
            "weather_lines": [{} for _ in range(36)],
        }
        payload = {
            "schema": runtime_budget.SCHEMA,
            "study_id": "environment-runtime-budget-001",
            "receiving_head": "head-001",
            "scene_digest": "scene-001",
            "base_variant": scene["source_integration"]["base_variant"],
            "proxy_baseline_item": {
                "asset_id": "proxy:nature-tree-west-a",
                "kind": "nature-proxy",
                "evidence": "PROXY_ONLY",
                "position_m": [-5.0, 1.5, 2.5],
                "size_m": [2.2, 2.2, 5.2],
                "rotation_deg": 4.0,
            },
            "scene": scene,
            "variants": {name: {} for name in runtime_budget.VARIANTS},
            "runtime_contract": {
                "weather_authored_streaks": runtime_budget.WEATHER_AUTHORED_STREAKS,
                "weather_expected_draw_delta": runtime_budget.WEATHER_EXPECTED_DRAW_DELTA,
                "weather_expected_renderer_primitive_delta": runtime_budget.WEATHER_EXPECTED_RENDERER_PRIMITIVE_DELTA,
            },
            "truth_boundary": "fixture",
        }
        payload["payload_digest"] = runtime_budget.digest(payload)
        return payload

    def runtime_receipt(self, payload: dict, variant: str, draw: int, primitives: int) -> dict:
        contexts = {}
        for context in runtime_budget.CONTEXTS:
            contexts[context] = {
                "state": "PASS",
                "runtime": {
                    "objects_in_frame": 10,
                    "primitives_in_frame": primitives,
                    "draw_calls_in_frame": draw,
                    "texture_mem_bytes": 1000,
                    "buffer_mem_bytes": 2000,
                },
                "capture": {"bytes": 4000},
            }
        return {
            "schema": runtime_budget.RUNTIME_SCHEMA,
            "state": "PASS_SCOPED_RUNTIME_OBSERVATION",
            "variant": variant,
            "scene_digest": payload["scene_digest"],
            "receiving_head": payload["receiving_head"],
            "contexts": contexts,
        }

    def test_payload_evidence_preserves_exact_proxy_source_weather_and_counter_scope(self) -> None:
        report = runtime_budget.evaluate_payload(self.payload())
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(all(report["checks"].values()))

    def test_aggregate_accepts_measured_one_surface_weather_delta(self) -> None:
        payload = self.payload()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload_path = root / "payload.json"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")
            rows = {
                "proxy_baseline": self.runtime_receipt(payload, "proxy_baseline", 9, 120),
                "source_sapling_only": self.runtime_receipt(payload, "source_sapling_only", 9, 678),
                "source_sapling_weather": self.runtime_receipt(payload, "source_sapling_weather", 10, 822),
            }
            for variant, row in rows.items():
                (root / f"runtime-budget-{variant}.json").write_text(json.dumps(row), encoding="utf-8")
            report = runtime_budget.aggregate(payload_path, root, root / "aggregate.json")
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["weather_batch_gate"], "PASS_EXACT_ONE_DRAW_CALL_144_RENDERER_PRIMITIVES_FOR_36_LINES_BOTH_CAMERAS")
            self.assertEqual(report["deltas"]["path_eye"]["weather_vs_source_sapling_only"]["draw_calls_in_frame"], 1)
            self.assertEqual(report["deltas"]["path_eye"]["weather_vs_source_sapling_only"]["primitives_in_frame"], 144)

    def test_aggregate_holds_when_weather_expands_to_multiple_draws(self) -> None:
        payload = self.payload()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload_path = root / "payload.json"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")
            rows = {
                "proxy_baseline": self.runtime_receipt(payload, "proxy_baseline", 9, 120),
                "source_sapling_only": self.runtime_receipt(payload, "source_sapling_only", 9, 678),
                "source_sapling_weather": self.runtime_receipt(payload, "source_sapling_weather", 11, 822),
            }
            for variant, row in rows.items():
                (root / f"runtime-budget-{variant}.json").write_text(json.dumps(row), encoding="utf-8")
            report = runtime_budget.aggregate(payload_path, root, root / "aggregate.json")
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["weather_batch_gate"], "HOLD_WEATHER_BATCH_RUNTIME_DELTA")

    def test_aggregate_holds_when_renderer_primitive_counter_drifts(self) -> None:
        payload = self.payload()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload_path = root / "payload.json"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")
            rows = {
                "proxy_baseline": self.runtime_receipt(payload, "proxy_baseline", 9, 120),
                "source_sapling_only": self.runtime_receipt(payload, "source_sapling_only", 9, 678),
                "source_sapling_weather": self.runtime_receipt(payload, "source_sapling_weather", 10, 714),
            }
            for variant, row in rows.items():
                (root / f"runtime-budget-{variant}.json").write_text(json.dumps(row), encoding="utf-8")
            report = runtime_budget.aggregate(payload_path, root, root / "aggregate.json")
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["weather_batch_gate"], "HOLD_WEATHER_BATCH_RUNTIME_DELTA")


if __name__ == "__main__":
    unittest.main()
