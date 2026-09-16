import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "environment_building_material_runtime_budget",
    ROOT / "tools" / "environment_building_material_runtime_budget.py",
)
M = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(M)


def runtime(draw, objects, primitives, buffer_bytes=6_580_320, texture_bytes=12_875_715):
    return {
        "draw_calls_in_frame": draw,
        "objects_in_frame": objects,
        "primitives_in_frame": primitives,
        "buffer_mem_bytes": buffer_bytes,
        "texture_mem_bytes": texture_bytes,
    }


def sample(index, path_runtime, elevated_runtime):
    return {
        "index": index,
        "time_s": index * 0.03125,
        "sampling_role": "sample",
        "weather_field_digest": f"weather-{index}",
        "sapling_mesh_digest": f"sapling-{index}",
        "contexts": {
            "path_eye": {"runtime": path_runtime},
            "elevated_oblique": {"runtime": elevated_runtime},
        },
    }


def fixture():
    control_samples = []
    candidate_samples = []
    for index in range(17):
        control_samples.append(sample(index, runtime(20, 20, 5992), runtime(27, 27, 7750)))
        candidate_samples.append(sample(index, runtime(32, 32, 5992), runtime(39, 39, 7750)))

    control = {
        "receiving_head": M.EXPECTED_CONTROL_HEAD,
        "proof_runtime": "Godot 4.7.2 GL Compatibility",
        "samples": control_samples,
        "static_source_meshes": [{
            "asset_id": M.BUILDING_ASSET_ID,
            "vertices": 152,
            "triangles": 228,
            "proof_culling": "CULL_DISABLED",
        }],
    }
    candidate = {
        "receiving_head": M.EXPECTED_ENVIRONMENT_HEAD,
        "proof_runtime": "Godot 4.7.2 GL Compatibility",
        "samples": candidate_samples,
        "static_source_meshes": [{
            "asset_id": M.BUILDING_ASSET_ID,
            "vertices": 152,
            "triangles": 228,
            "surface_count": 5,
            "material_profile_sha256": M.EXPECTED_MATERIAL_PROFILE_SHA256,
            "proof_culling": "CULL_DISABLED",
        }],
    }
    target = {
        "receiving_head": M.EXPECTED_ENVIRONMENT_HEAD,
        "state": "PASS_CURRENT_WORLD_BUILDING_MATERIAL_CONVERGENCE_TARGET_HOST",
        "building_material_profile_sha256": M.EXPECTED_MATERIAL_PROFILE_SHA256,
        "material_ids": ["a", "b", "c", "d", "e"],
    }
    return control, candidate, target


class RuntimeBuildingMaterialBudgetTests(unittest.TestCase):
    def _pixel_side_effect(self, a, b):
        context = "path_eye" if "path_eye" in a.name else "elevated_oblique"
        changed = M.EXPECTED_VISUAL_CHANGED_PIXELS[context]
        return {
            "changed_pixels": changed,
            "total_pixels": 792000,
            "changed_fraction": changed / 792000.0,
            "bbox_xyxy": [0, 0, 1, 1],
            "control_sha256": "a" * 64,
            "candidate_sha256": "b" * 64,
        }

    @patch.object(M, "_pixel_diff")
    def test_exact_fixture_passes(self, pixel_diff):
        pixel_diff.side_effect = self._pixel_side_effect
        control, candidate, target = fixture()
        result = M.compare(control, candidate, target, Path("rendered"))
        self.assertEqual(result["state"], M.STATUS)
        self.assertEqual(result["budget_decision"], M.BUDGET_DECISION)
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["contexts"]["path_eye"]["delta"]["draw_calls"], 12)
        self.assertEqual(result["contexts"]["elevated_oblique"]["delta"]["buffer_bytes"], 0)

    @patch.object(M, "_pixel_diff")
    def test_extra_submission_drift_fails_closed(self, pixel_diff):
        pixel_diff.side_effect = self._pixel_side_effect
        control, candidate, target = fixture()
        candidate["samples"][7]["contexts"]["path_eye"]["runtime"]["draw_calls_in_frame"] = 33
        result = M.compare(control, candidate, target, Path("rendered"))
        self.assertEqual(result["state"], "FAIL")
        self.assertFalse(result["checks"]["path_eye_counters_stable_all_17_states"])

    @patch.object(M, "_pixel_diff")
    def test_surface_profile_drift_fails_closed(self, pixel_diff):
        pixel_diff.side_effect = self._pixel_side_effect
        control, candidate, target = fixture()
        candidate["static_source_meshes"][0]["surface_count"] = 4
        result = M.compare(control, candidate, target, Path("rendered"))
        self.assertEqual(result["state"], "FAIL")
        self.assertFalse(result["checks"]["candidate_exact_five_surface_profile"])

    @patch.object(M, "_pixel_diff")
    def test_geometry_drift_fails_closed(self, pixel_diff):
        pixel_diff.side_effect = self._pixel_side_effect
        control, candidate, target = fixture()
        candidate["static_source_meshes"][0]["triangles"] = 227
        result = M.compare(control, candidate, target, Path("rendered"))
        self.assertEqual(result["state"], "FAIL")
        self.assertFalse(result["checks"]["candidate_building_geometry_exact"])


if __name__ == "__main__":
    unittest.main()
