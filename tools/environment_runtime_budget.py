from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_eye_level as eye

SCHEMA = "axm.environment-runtime-budget/v0.1"
EVIDENCE_SCHEMA = "axm.environment-runtime-budget-evidence/v0.1"
RUNTIME_SCHEMA = "axm.environment-runtime-budget-observation/v0.1"
VARIANTS = ("proxy_baseline", "source_sapling_only", "source_sapling_weather")
CONTEXTS = ("path_eye", "elevated_oblique")
RUNTIME_METRICS = (
    "objects_in_frame",
    "primitives_in_frame",
    "draw_calls_in_frame",
    "texture_mem_bytes",
    "buffer_mem_bytes",
)
WEATHER_AUTHORED_STREAKS = 36
WEATHER_EXPECTED_DRAW_DELTA = 1
WEATHER_EXPECTED_RENDERER_PRIMITIVE_DELTA = 144


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def build_payload(manifest_path: str | Path, nature_root: str | Path, weather_root: str | Path) -> dict:
    scene = eye.build_scene_payload(manifest_path, nature_root, weather_root)
    replacement = scene["source_integration"]["replacement"]
    proxy = {
        "asset_id": replacement["target_asset_id"],
        "kind": "nature-proxy",
        "evidence": "PROXY_ONLY",
        "position_m": [float(x) for x in replacement["reserved_proxy_position_m"]],
        "size_m": [float(x) for x in replacement["reserved_proxy_size_m"]],
        "rotation_deg": float(replacement["reserved_proxy_rotation_deg"]),
    }
    payload = {
        "schema": SCHEMA,
        "study_id": "environment-runtime-budget-001",
        "receiving_head": os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD"),
        "scene_digest": scene["scene_digest"],
        "base_variant": scene["source_integration"]["base_variant"],
        "proxy_baseline_item": proxy,
        "scene": scene,
        "variants": {
            "proxy_baseline": {
                "semantics": "EXACT_PINNED_SEED_29_PROXY_COMPOSITION_NO_SOURCE_SAPLING_NO_WEATHER",
                "measurement_role": "BEFORE_BASELINE",
            },
            "source_sapling_only": {
                "semantics": "MEASUREMENT_ABLATION_EXACT_SOURCE_SAPLING_NO_WEATHER",
                "measurement_role": "ABLATION_ONLY_NOT_PRODUCT_CANDIDATE",
            },
            "source_sapling_weather": {
                "semantics": "EXACT_CURRENT_ENVIRONMENT_SOURCE_SLICE",
                "measurement_role": "CURRENT_SOURCE_SLICE",
            },
        },
        "runtime_contract": {
            "proof_host": "Godot 4.7.2 GL Compatibility",
            "weather_authored_streaks": WEATHER_AUTHORED_STREAKS,
            "weather_expected_draw_delta": WEATHER_EXPECTED_DRAW_DELTA,
            "weather_expected_renderer_primitive_delta": WEATHER_EXPECTED_RENDERER_PRIMITIVE_DELTA,
            "weather_batch_expectation": (
                "The 36 retained source-owned streaks remain one ImmediateMesh surface. The exact first proof-host measurement showed +1 draw call and +144 RenderingServer-reported primitives versus the sapling-only ablation in both fixed cameras. "
                "The 144 value is a renderer counter observation on pinned Godot 4.7.2 GL Compatibility, not a claim that the source authored 144 streaks or line primitives."
            ),
            "absolute_budget": "NOT_SET_MISSING_TARGET_DEVICE_BUDGET",
            "promotion_effect": "NONE",
        },
        "truth_boundary": (
            "This packet compares the exact seed-29 proxy composition, a measurement-only sapling/no-weather ablation, and the exact current source-owned Nature+Weather scene in one pinned Godot proof host. "
            "It establishes comparative proof-host runtime counters and a one-surface weather batching regression contract only. RenderingServer primitive counters are retained with their observed backend semantics and are not relabelled as authored triangle/line counts. "
            "It does not establish target-device FPS/frame-time, production budgets, final LOD policy, final scene art, gameplay, physical weather, CANON, or Runtime mastery."
        ),
    }
    payload["payload_digest"] = digest(payload)
    return payload


def evaluate_payload(payload: dict) -> dict:
    scene = payload["scene"]
    replacement = scene["source_integration"]["replacement"]
    proxy = payload["proxy_baseline_item"]
    contract = payload.get("runtime_contract", {})
    checks = {
        "schema": payload.get("schema") == SCHEMA,
        "source_integration_pass": scene["source_integration"]["status"] == "PASS",
        "scene_digest_preserved": payload["scene_digest"] == scene["scene_digest"],
        "receiving_head_preserved": payload["receiving_head"] == scene["receiving_head"],
        "pinned_seed_preserved": int(payload["base_variant"]["seed"]) == 29,
        "proxy_identity_preserved": proxy["asset_id"] == replacement["target_asset_id"] and proxy["kind"] == "nature-proxy" and proxy["evidence"] == "PROXY_ONLY",
        "proxy_transform_preserved": proxy["position_m"] == [float(x) for x in replacement["reserved_proxy_position_m"]] and proxy["size_m"] == [float(x) for x in replacement["reserved_proxy_size_m"]] and proxy["rotation_deg"] == float(replacement["reserved_proxy_rotation_deg"]),
        "source_sapling_preserved": len(scene["sapling"]["vertices_source_xyz_m"]) == 390 and len(scene["sapling"]["triangles"]) == 570,
        "weather_field_preserved": len(scene["weather_lines"]) == WEATHER_AUTHORED_STREAKS,
        "fixed_cameras_preserved": set(scene["cameras"]) == set(CONTEXTS),
        "variant_roles_complete": set(payload["variants"]) == set(VARIANTS),
        "measured_weather_counter_contract_preserved": int(contract.get("weather_authored_streaks", -1)) == WEATHER_AUTHORED_STREAKS and int(contract.get("weather_expected_draw_delta", -1)) == WEATHER_EXPECTED_DRAW_DELTA and int(contract.get("weather_expected_renderer_primitive_delta", -1)) == WEATHER_EXPECTED_RENDERER_PRIMITIVE_DELTA,
    }
    return {
        "schema": EVIDENCE_SCHEMA,
        "study_id": payload["study_id"],
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "receiving_head": payload["receiving_head"],
        "scene_digest": payload["scene_digest"],
        "payload_digest": payload["payload_digest"],
        "truth_boundary": payload["truth_boundary"],
    }


def prepare(manifest_path: str | Path, nature_root: str | Path, weather_root: str | Path, output_dir: str | Path) -> dict:
    payload = build_payload(manifest_path, nature_root, weather_root)
    report = evaluate_payload(payload)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "runtime_budget_scene.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "runtime_budget_prepare_evidence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _delta(before: dict, after: dict) -> dict:
    return {metric: int(after[metric]) - int(before[metric]) for metric in RUNTIME_METRICS}


def aggregate(payload_path: str | Path, runtime_dir: str | Path, output_path: str | Path) -> dict:
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    prep = evaluate_payload(payload)
    runtime_root = Path(runtime_dir)
    receipts: dict[str, dict] = {}
    validation: dict[str, bool] = {"prepare_payload_pass": prep["status"] == "PASS"}

    for variant in VARIANTS:
        path = runtime_root / f"runtime-budget-{variant}.json"
        row = json.loads(path.read_text(encoding="utf-8"))
        receipts[variant] = row
        validation[f"{variant}_schema"] = row.get("schema") == RUNTIME_SCHEMA
        validation[f"{variant}_state"] = row.get("state") == "PASS_SCOPED_RUNTIME_OBSERVATION"
        validation[f"{variant}_identity"] = row.get("variant") == variant and row.get("scene_digest") == payload["scene_digest"] and row.get("receiving_head") == payload["receiving_head"]
        validation[f"{variant}_contexts"] = set(row.get("contexts", {})) == set(CONTEXTS)

    deltas: dict[str, dict] = {}
    weather_batch_checks: dict[str, bool] = {}
    for context in CONTEXTS:
        baseline = receipts["proxy_baseline"]["contexts"][context]["runtime"]
        sapling = receipts["source_sapling_only"]["contexts"][context]["runtime"]
        full = receipts["source_sapling_weather"]["contexts"][context]["runtime"]
        deltas[context] = {
            "source_sapling_vs_proxy": _delta(baseline, sapling),
            "weather_vs_source_sapling_only": _delta(sapling, full),
            "full_source_slice_vs_proxy": _delta(baseline, full),
        }
        weather = deltas[context]["weather_vs_source_sapling_only"]
        weather_batch_checks[context] = weather["draw_calls_in_frame"] == WEATHER_EXPECTED_DRAW_DELTA and weather["primitives_in_frame"] == WEATHER_EXPECTED_RENDERER_PRIMITIVE_DELTA

    validation.update({f"weather_single_surface_{context}": value for context, value in weather_batch_checks.items()})
    passed = all(validation.values())
    report = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": payload["study_id"],
        "status": "PASS" if passed else "FAIL",
        "state": "PASS_SCOPED_FIRST_ENVIRONMENT_RUNTIME_BASELINE" if passed else "HOLD_ENVIRONMENT_RUNTIME_BASELINE",
        "receiving_head": payload["receiving_head"],
        "scene_digest": payload["scene_digest"],
        "payload_digest": payload["payload_digest"],
        "checks": validation,
        "measurements": {variant: receipts[variant]["contexts"] for variant in VARIANTS},
        "deltas": deltas,
        "weather_batch_gate": "PASS_EXACT_ONE_DRAW_CALL_144_RENDERER_PRIMITIVES_FOR_36_LINES_BOTH_CAMERAS" if all(weather_batch_checks.values()) else "HOLD_WEATHER_BATCH_RUNTIME_DELTA",
        "counter_semantics": {
            "authored_weather_streaks": WEATHER_AUTHORED_STREAKS,
            "measured_weather_draw_call_delta": WEATHER_EXPECTED_DRAW_DELTA,
            "measured_weather_renderer_primitive_delta": WEATHER_EXPECTED_RENDERER_PRIMITIVE_DELTA,
            "interpretation": "Pinned Godot RenderingServer reports +144 primitives for the one-surface 36-line Weather field in this GL Compatibility proof. Preserve this as a renderer observation; do not rename it as authored streak/line count."
        },
        "source_replacement_budget_gate": "MEASURED_COMPARATIVE_ONLY_NO_TARGET_BUDGET",
        "texture_memory_interpretation": "OBSERVATIONAL_ONLY_RENDERER_CACHE_AND_SHARED_RESOURCES_NOT_DECOMPOSED",
        "visual_tradeoff": {
            "full_scene_geometry_or_materials_changed_by_runtime_lane": False,
            "proxy_baseline": "Historical/procedural before-state for cost comparison, not a proposed visual rollback.",
            "source_sapling_only": "Measurement ablation only; removing Weather is not proposed as an optimization.",
            "source_sapling_weather": "Exact current Environment source slice. Future optimization must preserve Art Director/Environment visual acceptance independently.",
        },
        "target_device_budget": "BLOCKED_MISSING_TARGET_DEVICE_AND_BUDGET",
        "frame_time_fps": "NOT_MEASURED_BY_THIS_COUNTER_PROBE",
        "production_readiness": "NOT_CLAIMED",
        "truth_boundary": payload["truth_boundary"],
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare")
    prep.add_argument("--manifest", default="examples/environment_real_slice_001.json")
    prep.add_argument("--nature-root", required=True)
    prep.add_argument("--weather-root", required=True)
    prep.add_argument("--output", default="evidence/environment_runtime_budget_001")

    agg = sub.add_parser("aggregate")
    agg.add_argument("--payload", default="evidence/environment_runtime_budget_001/runtime_budget_scene.json")
    agg.add_argument("--runtime-dir", default="environment-proof")
    agg.add_argument("--output", default="evidence/environment_runtime_budget_001/runtime_budget_evidence.json")

    args = parser.parse_args()
    if args.command == "prepare":
        report = prepare(args.manifest, args.nature_root, args.weather_root, args.output)
    else:
        report = aggregate(args.payload, args.runtime_dir, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
