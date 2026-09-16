from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-weather-source-width-runtime-budget/v0.1"
STATUS = "PASS_WEATHER_SOURCE_WIDTH_FIXED_CAMERA_RUNTIME_BUDGET_CHARACTERIZED"
BUDGET_DECISION = (
    "PASS_BOUNDED_SOURCE_WIDTH_PRESENTATION_COST__PLUS_144_PRIMITIVES_"
    "PLUS_2304_BUFFER_BYTES_NO_DRAW_OBJECT_TEXTURE_DELTA"
)

EXPECTED_ENVIRONMENT_HEAD = "0d8b2279ecbba47b9696a951db9513883fbef6c5"
EXPECTED_COMPOSITION_DIGEST = "132e877c8016d833f43d7a4cfe303ad2595913c757b85dd212192eafafed1973"
EXPECTED_PARENT_ARTIFACT_ID = 10452505109
EXPECTED_PARENT_ARTIFACT_SHA256 = "4ffc52fc421d38a92829d3bf663ab5a48dfc144d16f31028f742ce19855512f4"
EXPECTED_TARGET_STATE = "PASS_CURRENT_WORLD_BUILDING_SUCCESSOR_WEATHER_WIDTH_TARGET_HOST"
EXPECTED_RUNTIME_STATE = "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION"
EXPECTED_PROOF_RUNTIME = "Godot 4.7.2 GL Compatibility"
EXPECTED_STATES = 17
EXPECTED_STREAKS = 36
EXPECTED_IMAGE_SIZE = (1100, 720)
CONTEXTS = ("path_eye", "elevated_oblique")
COUNTER_KEYS = (
    "draw_calls_in_frame",
    "objects_in_frame",
    "primitives_in_frame",
    "buffer_mem_bytes",
    "texture_mem_bytes",
)
EXPECTED_CONTROL = {
    "path_eye": {
        "draw_calls_in_frame": 32,
        "objects_in_frame": 32,
        "primitives_in_frame": 5992,
        "buffer_mem_bytes": 6580320,
        "texture_mem_bytes": 12875715,
    },
    "elevated_oblique": {
        "draw_calls_in_frame": 39,
        "objects_in_frame": 39,
        "primitives_in_frame": 7750,
        "buffer_mem_bytes": 6580320,
        "texture_mem_bytes": 12875715,
    },
}
EXPECTED_CANDIDATE = {
    "path_eye": {
        "draw_calls_in_frame": 32,
        "objects_in_frame": 32,
        "primitives_in_frame": 6136,
        "buffer_mem_bytes": 6582624,
        "texture_mem_bytes": 12875715,
    },
    "elevated_oblique": {
        "draw_calls_in_frame": 39,
        "objects_in_frame": 39,
        "primitives_in_frame": 7894,
        "buffer_mem_bytes": 6582624,
        "texture_mem_bytes": 12875715,
    },
}
EXPECTED_DELTA = {
    "draw_calls_in_frame": 0,
    "objects_in_frame": 0,
    "primitives_in_frame": 144,
    "buffer_mem_bytes": 2304,
    "texture_mem_bytes": 0,
}


def _counter_row(stats: dict[str, Any]) -> dict[str, int]:
    return {key: int(stats[key]) for key in COUNTER_KEYS}


def _tuple(row: dict[str, int]) -> tuple[int, ...]:
    return tuple(row[key] for key in COUNTER_KEYS)


def _png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"not a valid PNG header: {path}")
    return struct.unpack(">II", header[16:24])


def _frame_pair(control_path: Path, candidate_path: Path) -> dict[str, Any]:
    if not control_path.exists() or not candidate_path.exists():
        raise ValueError(f"missing retained A/B frame: {control_path} / {candidate_path}")
    control_size = _png_size(control_path)
    candidate_size = _png_size(candidate_path)
    if control_size != candidate_size or control_size != EXPECTED_IMAGE_SIZE:
        raise ValueError(f"frame dimension drift: {control_size} / {candidate_size}")
    control_bytes = control_path.read_bytes()
    candidate_bytes = candidate_path.read_bytes()
    return {
        "width": control_size[0],
        "height": control_size[1],
        "control_bytes": len(control_bytes),
        "candidate_bytes": len(candidate_bytes),
        "control_sha256": hashlib.sha256(control_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "byte_different": control_bytes != candidate_bytes,
    }


def characterize(
    payload: dict[str, Any],
    runtime: dict[str, Any],
    target: dict[str, Any],
    render_root: Path,
) -> dict[str, Any]:
    if payload.get("status") != "PASS_CURRENT_WORLD_BUILDING_SUCCESSOR_WEATHER_WIDTH_STRUCTURE":
        raise ValueError("Environment structural parent is not exact PASS")
    if payload.get("receiving_head") != EXPECTED_ENVIRONMENT_HEAD:
        raise ValueError("Environment parent head drift")
    if payload.get("composition_digest") != EXPECTED_COMPOSITION_DIGEST:
        raise ValueError("Environment composition digest drift")
    if len(payload.get("states", [])) != EXPECTED_STATES:
        raise ValueError("Environment parent must retain exact 17 states")
    if int(payload.get("source_width_summary", {}).get("count", -1)) != EXPECTED_STREAKS:
        raise ValueError("Weather source-width streak count drift")

    if runtime.get("state") != EXPECTED_RUNTIME_STATE:
        raise ValueError("live Godot receipt is not exact PASS")
    if runtime.get("receiving_head") != EXPECTED_ENVIRONMENT_HEAD:
        raise ValueError("live Godot receipt head drift")
    if runtime.get("proof_runtime") != EXPECTED_PROOF_RUNTIME:
        raise ValueError("proof runtime drift")
    if len(runtime.get("samples", [])) != EXPECTED_STATES:
        raise ValueError("runtime receipt must retain exact 17 states")

    if target.get("state") != EXPECTED_TARGET_STATE:
        raise ValueError("Environment target-host verifier is not exact PASS")
    if target.get("receiving_head") != EXPECTED_ENVIRONMENT_HEAD:
        raise ValueError("target-host head drift")
    if target.get("composition_digest") != EXPECTED_COMPOSITION_DIGEST:
        raise ValueError("target-host composition digest drift")
    if not all(target.get("checks", {}).values()):
        raise ValueError("target-host prerequisite contains a failed check")

    checks: dict[str, bool] = {
        "exact_environment_head": payload.get("receiving_head") == runtime.get("receiving_head") == target.get("receiving_head") == EXPECTED_ENVIRONMENT_HEAD,
        "exact_composition_digest": payload.get("composition_digest") == target.get("composition_digest") == EXPECTED_COMPOSITION_DIGEST,
        "exact_17_state_runtime_sequence": len(runtime.get("samples", [])) == EXPECTED_STATES,
        "exact_36_streak_source_width_profile": int(payload.get("source_width_summary", {}).get("count", -1)) == EXPECTED_STREAKS,
        "target_host_parent_pass": target.get("state") == EXPECTED_TARGET_STATE and all(target.get("checks", {}).values()),
        "all_34_control_candidate_pairs_changed": all(int(target.get("changed_pair_counts", {}).get(context, -1)) == EXPECTED_STATES for context in CONTEXTS),
        "all_34_frames_per_mode_retained": all(
            int(target.get("frame_counts", {}).get(mode, {}).get(context, -1)) == EXPECTED_STATES
            for mode in ("control", "candidate") for context in CONTEXTS
        ),
        "all_1224_width_measurements_retained": int(target.get("measured_width_count", -1)) == EXPECTED_STATES * len(CONTEXTS) * EXPECTED_STREAKS,
        "projected_width_residual_within_existing_gate": float(target.get("maximum_projected_width_residual_px", 999.0)) <= 0.05,
        "five_near_plane_endpoint_clips_explicit": int(target.get("near_clipped_endpoint_count", -1)) == 5,
    }

    contexts: dict[str, Any] = {}
    visual: dict[str, Any] = {}
    for context in CONTEXTS:
        control_rows: list[dict[str, int]] = []
        candidate_rows: list[dict[str, int]] = []
        delta_rows: list[dict[str, int]] = []
        for sample in runtime["samples"]:
            context_row = sample["contexts"][context]
            control = _counter_row(context_row["control"]["runtime"])
            candidate = _counter_row(context_row["candidate"]["runtime"])
            delta = {key: candidate[key] - control[key] for key in COUNTER_KEYS}
            control_rows.append(control)
            candidate_rows.append(candidate)
            delta_rows.append(delta)

        control_set = {_tuple(row) for row in control_rows}
        candidate_set = {_tuple(row) for row in candidate_rows}
        delta_set = {_tuple(row) for row in delta_rows}
        checks[f"{context}_control_counters_stable"] = len(control_set) == 1
        checks[f"{context}_candidate_counters_stable"] = len(candidate_set) == 1
        checks[f"{context}_delta_stable"] = len(delta_set) == 1
        checks[f"{context}_exact_control_budget"] = control_rows[0] == EXPECTED_CONTROL[context]
        checks[f"{context}_exact_candidate_budget"] = candidate_rows[0] == EXPECTED_CANDIDATE[context]
        checks[f"{context}_exact_delta"] = delta_rows[0] == EXPECTED_DELTA

        contexts[context] = {
            "control": control_rows[0],
            "candidate": candidate_rows[0],
            "delta": delta_rows[0],
            "primitive_increase_percent": EXPECTED_DELTA["primitives_in_frame"] / float(EXPECTED_CONTROL[context]["primitives_in_frame"]) * 100.0,
            "buffer_increase_percent": EXPECTED_DELTA["buffer_mem_bytes"] / float(EXPECTED_CONTROL[context]["buffer_mem_bytes"]) * 100.0,
        }

        frame_rows = []
        for index in range(EXPECTED_STATES):
            frame_rows.append({
                "index": index,
                **_frame_pair(
                    render_root / f"atmosphere-width-control-{context}-{index:02d}.png",
                    render_root / f"atmosphere-width-candidate-{context}-{index:02d}.png",
                ),
            })
        checks[f"{context}_all_retained_pairs_byte_different"] = all(row["byte_different"] for row in frame_rows)
        checks[f"{context}_all_retained_frames_exact_dimensions"] = all((row["width"], row["height"]) == EXPECTED_IMAGE_SIZE for row in frame_rows)
        visual[context] = {
            "pair_count": len(frame_rows),
            "all_pairs_byte_different": all(row["byte_different"] for row in frame_rows),
            "control_bytes_min": min(row["control_bytes"] for row in frame_rows),
            "control_bytes_max": max(row["control_bytes"] for row in frame_rows),
            "candidate_bytes_min": min(row["candidate_bytes"] for row in frame_rows),
            "candidate_bytes_max": max(row["candidate_bytes"] for row in frame_rows),
        }

    state = STATUS if all(checks.values()) else "FAIL"
    return {
        "schema": SCHEMA,
        "study_id": "environment-weather-source-width-runtime-budget-001",
        "state": state,
        "budget_decision": BUDGET_DECISION if state == STATUS else "HOLD_FAILED_RUNTIME_BUDGET_GATE",
        "environment_head": EXPECTED_ENVIRONMENT_HEAD,
        "environment_composition_digest": EXPECTED_COMPOSITION_DIGEST,
        "parent_artifact": {
            "id": EXPECTED_PARENT_ARTIFACT_ID,
            "sha256": EXPECTED_PARENT_ARTIFACT_SHA256,
            "name": "environment-building-successor-weather-width-001-0d8b2279ecbba47b9696a951db9513883fbef6c5",
        },
        "proof_runtime": EXPECTED_PROOF_RUNTIME,
        "source_width_summary": payload.get("source_width_summary", {}),
        "near_plane_boundary": {
            "clipped_endpoint_count": target.get("near_clipped_endpoint_count"),
            "streak_ids": target.get("near_clipped_streak_ids"),
        },
        "checks": checks,
        "contexts": contexts,
        "visual_comparison": visual,
        "observed_tradeoff": (
            "The exact Art/QA-preferred source-width Weather representation preserves draw-call, object and texture-memory counters in both fixed cameras, while adding exactly 144 RenderingServer primitives and 2,304 observed buffer bytes versus the thin-line control across all 17 retained states."
        ),
        "art_direction_handoff": (
            "Runtime changes no visual state. The retained Environment A/B remains the visual evidence: all 34 source-width pairs remain byte-different while the broader Building/Nature/Object/path composition is producer-owned. Existing Art Direction / Visual QA preference for the authored-width presentation is not reclassified as a Runtime aesthetic judgment."
        ),
        "reuse_boundary": (
            "This exact proof may be used as a fail-closed fixed-camera budget contract for this Map receiving representation. The +144 primitive and +2,304 B buffer deltas must not be generalized into a renderer-independent per-streak cost model because backend primitive accounting can include renderer/pass behavior."
        ),
        "truth_boundary": (
            "PASS characterizes only the exact retained Godot 4.7.2 GL Compatibility thin-line versus camera-projected source-width ribbon representation over Environment PR24 head 0d8b2279. It does not establish CPU/GPU frame time, FPS, overdraw, VRAM, heap residency, arbitrary-camera/resolution cost, mobile/browser/console budgets, physical Weather dimensions, gameplay visibility, final Art Direction, CANON, production readiness or Runtime mastery."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--target-host", type=Path, required=True)
    parser.add_argument("--render-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = characterize(
        json.loads(args.payload.read_text()),
        json.loads(args.runtime.read_text()),
        json.loads(args.target_host.read_text()),
        args.render_root,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "state": result["state"],
        "budget_decision": result["budget_decision"],
        "contexts": result["contexts"],
        "visual_comparison": result["visual_comparison"],
    }, indent=2, sort_keys=True))
    return 0 if result["state"] == STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
