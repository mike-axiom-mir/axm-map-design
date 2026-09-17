from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

SCHEMA = "axm.environment-building-material-runtime-budget/v0.1"
STATUS = "PASS_EXACT_BUILDING_FIVE_SURFACE_SUBMISSION_COST_CHARACTERIZED"
BUDGET_DECISION = "HOLD_RUNTIME_NEUTRALITY_CLAIM__FIVE_SURFACE_ADDS_12_SUBMISSION_SLOTS_IN_EXACT_PROOF_HOST"
EXPECTED_CONTROL_HEAD = "94918f362226994e3ff5c2a1412a2bc2a8bce49b"
EXPECTED_ENVIRONMENT_HEAD = "48bc157ad9c3ecb7ef8e9fb08fb4721ac76013c5"
EXPECTED_PARENT_ARTIFACT_ID = 10447016718
EXPECTED_PARENT_ARTIFACT_SHA256 = "aeda6e564ae8ac99906c61ac56a692792c4227f2539b0c453e66914b9d15f1ff"
EXPECTED_MATERIAL_PROFILE_SHA256 = "e8dd0c33b9b2aea108194af57a8fe8de39c7e67bb86109af6dbf3895f22c010b"
BUILDING_ASSET_ID = "source:building:service-pavilion-001"
EXPECTED_SURFACES = 5
EXPECTED_VERTICES = 152
EXPECTED_TRIANGLES = 228
EXPECTED_DRAW_OBJECT_DELTA = 12
EXPECTED_VISUAL_CHANGED_PIXELS = {
    "path_eye": 67_221,
    "elevated_oblique": 37_182,
}
CONTEXTS = ("path_eye", "elevated_oblique")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _one(rows: list[dict[str, Any]], asset_id: str) -> dict[str, Any]:
    hits = [row for row in rows if row.get("asset_id") == asset_id]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one {asset_id}, found {len(hits)}")
    return hits[0]


def _runtime(row: dict[str, Any], context: str) -> dict[str, int]:
    runtime = row["contexts"][context]["runtime"]
    return {
        "draw_calls": int(runtime["draw_calls_in_frame"]),
        "objects": int(runtime["objects_in_frame"]),
        "primitives": int(runtime["primitives_in_frame"]),
        "buffer_bytes": int(runtime["buffer_mem_bytes"]),
        "texture_bytes": int(runtime["texture_mem_bytes"]),
    }


def _pixel_diff(a: Path, b: Path) -> dict[str, Any]:
    with Image.open(a).convert("RGB") as ia, Image.open(b).convert("RGB") as ib:
        if ia.size != ib.size:
            raise ValueError(f"image size drift: {a}={ia.size}, {b}={ib.size}")
        diff = ImageChops.difference(ia, ib)
        bbox = diff.getbbox()
        changed = 0
        if bbox is not None:
            pixels = diff.load()
            for y in range(ia.height):
                for x in range(ia.width):
                    if pixels[x, y] != (0, 0, 0):
                        changed += 1
        return {
            "changed_pixels": changed,
            "total_pixels": ia.width * ia.height,
            "changed_fraction": changed / float(ia.width * ia.height),
            "bbox_xyxy": list(bbox) if bbox is not None else None,
            "control_sha256": sha256(a),
            "candidate_sha256": sha256(b),
        }


def compare(
    control: dict[str, Any],
    candidate: dict[str, Any],
    target_host: dict[str, Any],
    render_root: Path,
) -> dict[str, Any]:
    if control.get("receiving_head") != EXPECTED_CONTROL_HEAD:
        raise ValueError("control runtime parent head drift")
    if candidate.get("receiving_head") != EXPECTED_ENVIRONMENT_HEAD:
        raise ValueError("candidate runtime head drift")
    if target_host.get("receiving_head") != EXPECTED_ENVIRONMENT_HEAD:
        raise ValueError("target-host receipt head drift")
    if control.get("proof_runtime") != "Godot 4.7.2 GL Compatibility":
        raise ValueError("control proof runtime drift")
    if candidate.get("proof_runtime") != control.get("proof_runtime"):
        raise ValueError("candidate proof runtime drift")
    if target_host.get("state") != "PASS_CURRENT_WORLD_BUILDING_MATERIAL_CONVERGENCE_TARGET_HOST":
        raise ValueError("Environment target-host prerequisite is not PASS")

    control_samples = control.get("samples", [])
    candidate_samples = candidate.get("samples", [])
    if len(control_samples) != 17 or len(candidate_samples) != 17:
        raise ValueError("exact comparison requires 17 control and 17 candidate states")

    control_building = _one(control.get("static_source_meshes", []), BUILDING_ASSET_ID)
    candidate_building = _one(candidate.get("static_source_meshes", []), BUILDING_ASSET_ID)

    checks: dict[str, bool] = {
        "exact_control_parent_head": control.get("receiving_head") == EXPECTED_CONTROL_HEAD,
        "exact_candidate_environment_head": candidate.get("receiving_head") == target_host.get("receiving_head") == EXPECTED_ENVIRONMENT_HEAD,
        "same_pinned_proof_runtime": control.get("proof_runtime") == candidate.get("proof_runtime") == "Godot 4.7.2 GL Compatibility",
        "exact_17_state_schedule": len(control_samples) == len(candidate_samples) == 17,
        "control_building_geometry_exact": int(control_building.get("vertices", -1)) == EXPECTED_VERTICES and int(control_building.get("triangles", -1)) == EXPECTED_TRIANGLES,
        "candidate_building_geometry_exact": int(candidate_building.get("vertices", -1)) == EXPECTED_VERTICES and int(candidate_building.get("triangles", -1)) == EXPECTED_TRIANGLES,
        "candidate_exact_five_surface_profile": int(candidate_building.get("surface_count", -1)) == EXPECTED_SURFACES and candidate_building.get("material_profile_sha256") == EXPECTED_MATERIAL_PROFILE_SHA256,
        "target_host_exact_five_surface_profile": target_host.get("building_material_profile_sha256") == EXPECTED_MATERIAL_PROFILE_SHA256 and len(target_host.get("material_ids", [])) == EXPECTED_SURFACES,
    }

    state_identity_ok = True
    context_rows: dict[str, list[dict[str, Any]]] = {context: [] for context in CONTEXTS}
    for control_row, candidate_row in zip(control_samples, candidate_samples):
        state_identity_ok = state_identity_ok and all(
            control_row.get(key) == candidate_row.get(key)
            for key in ("index", "time_s", "sampling_role", "weather_field_digest", "sapling_mesh_digest")
        )
        for context in CONTEXTS:
            before = _runtime(control_row, context)
            after = _runtime(candidate_row, context)
            delta = {key: after[key] - before[key] for key in before}
            context_rows[context].append({
                "index": int(control_row["index"]),
                "control": before,
                "candidate": after,
                "delta": delta,
            })
    checks["weather_sapling_state_identity_preserved"] = state_identity_ok

    contexts: dict[str, Any] = {}
    for context, rows in context_rows.items():
        control_set = {tuple(row["control"].values()) for row in rows}
        candidate_set = {tuple(row["candidate"].values()) for row in rows}
        delta_set = {tuple(row["delta"].values()) for row in rows}
        delta = rows[0]["delta"]
        control_first = rows[0]["control"]
        contexts[context] = {
            "control_counter_sets": [list(v) for v in sorted(control_set)],
            "candidate_counter_sets": [list(v) for v in sorted(candidate_set)],
            "delta": delta,
            "draw_call_increase_percent": (delta["draw_calls"] / control_first["draw_calls"]) * 100.0,
            "object_counter_increase_percent": (delta["objects"] / control_first["objects"]) * 100.0,
        }
        checks[f"{context}_counters_stable_all_17_states"] = len(control_set) == len(candidate_set) == len(delta_set) == 1
        checks[f"{context}_draw_call_delta_exact"] = delta["draw_calls"] == EXPECTED_DRAW_OBJECT_DELTA
        checks[f"{context}_object_counter_delta_exact"] = delta["objects"] == EXPECTED_DRAW_OBJECT_DELTA
        checks[f"{context}_primitive_delta_zero"] = delta["primitives"] == 0
        checks[f"{context}_buffer_delta_zero"] = delta["buffer_bytes"] == 0
        checks[f"{context}_texture_delta_zero"] = delta["texture_bytes"] == 0

    visual_comparison: dict[str, list[dict[str, Any]]] = {context: [] for context in CONTEXTS}
    for context in CONTEXTS:
        for index in range(17):
            control_path = render_root / f"control-{context}-{index:02d}.png"
            candidate_path = render_root / f"building-material-{context}-{index:02d}.png"
            visual_comparison[context].append({"index": index, **_pixel_diff(control_path, candidate_path)})
        changed = {row["changed_pixels"] for row in visual_comparison[context]}
        checks[f"{context}_visual_delta_stable_all_17_states"] = changed == {EXPECTED_VISUAL_CHANGED_PIXELS[context]}

    result = {
        "schema": SCHEMA,
        "study_id": "environment-building-material-runtime-budget-001",
        "state": STATUS if all(checks.values()) else "FAIL",
        "budget_decision": BUDGET_DECISION,
        "control_parent_head": EXPECTED_CONTROL_HEAD,
        "environment_head": EXPECTED_ENVIRONMENT_HEAD,
        "parent_artifact": {
            "id": EXPECTED_PARENT_ARTIFACT_ID,
            "sha256": EXPECTED_PARENT_ARTIFACT_SHA256,
            "name": "environment-current-world-building-material-001-48bc157ad9c3ecb7ef8e9fb08fb4721ac76013c5",
        },
        "building": {
            "asset_id": BUILDING_ASSET_ID,
            "vertices": EXPECTED_VERTICES,
            "triangles": EXPECTED_TRIANGLES,
            "control_surface_count": 1,
            "candidate_surface_count": EXPECTED_SURFACES,
            "added_logical_surfaces": EXPECTED_SURFACES - 1,
            "material_profile_sha256": EXPECTED_MATERIAL_PROFILE_SHA256,
        },
        "checks": checks,
        "contexts": contexts,
        "visual_comparison": visual_comparison,
        "observed_tradeoff": (
            "The exact five-surface Building response preserves the same 152-vertex/228-triangle geometry and shows zero observed proof-host primitive, buffer-memory and texture-memory delta, but adds exactly 12 draw-call and 12 objects-in-frame counter slots in both fixed cameras across all 17 states. This is a proof-host submission-cost observation, not a target-device performance verdict."
        ),
        "art_direction_handoff": (
            "Runtime changes no visual state. The retained parent A/B remains the visual tradeoff: Environment reports clearer galvanized-frame/service-panel separation while roof/infill become substantially darker and can approach one near-dark mass in path-eye. Art Direction / Materials / Visual QA should decide whether that value justifies this exact submission overhead or whether a lower-surface receiving representation deserves a separate visual-equivalence experiment."
        ),
        "next_runtime_question": (
            "If the five-surface response is visually preferred, test one explicitly separate lower-submission representation against this exact candidate. Do not collapse surface semantics before Art Direction/Materials acceptance and do not infer a generic 3x-per-surface rule from this one Godot GL Compatibility scene."
        ),
        "truth_boundary": (
            "PASS characterizes the exact retained Godot 4.7.2 GL Compatibility proof-host submission and memory counters for neutral one-surface parent versus exact five-surface Building receiving representations inside Environment PR24. The control retains its exact pre-material parent head rather than being relabelled as the candidate head. It does not prove CPU/GPU frame time, FPS, VRAM, allocator residency, renderer-independent batching/pass decomposition, target-device budgets, final material preference, LOD/streaming policy, gameplay, CANON, production readiness, or Runtime mastery."
        ),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-runtime", type=Path, required=True)
    parser.add_argument("--candidate-runtime", type=Path, required=True)
    parser.add_argument("--target-host", type=Path, required=True)
    parser.add_argument("--render-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = compare(
        json.loads(args.control_runtime.read_text()),
        json.loads(args.candidate_runtime.read_text()),
        json.loads(args.target_host.read_text()),
        args.render_root,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "state": result["state"],
        "budget_decision": result["budget_decision"],
        "contexts": result["contexts"],
        "visual_changed_pixels": {
            key: sorted({row["changed_pixels"] for row in rows})
            for key, rows in result["visual_comparison"].items()
        },
    }, indent=2, sort_keys=True))
    return 0 if result["state"] == STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
