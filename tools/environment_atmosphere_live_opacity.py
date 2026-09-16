from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-atmosphere-live-opacity-fidelity-evidence/v0.1"
EXPECTED_STATE_COUNT = 17
EXPECTED_STREAK_COUNT = 36
EXPECTED_WEATHER_SOURCE_HEAD = "ca2eaba519e8449835b0ea6ef944b7080c3caa6a"
EXPECTED_FIDELITY_DONOR_HEAD = "1d24506e1d5f37cad32c878a15ac6908bf096329"
EXPECTED_OPACITY_MODE = "SOURCE_STREAK_OPACITY_VERTEX_ALPHA"
EXPECTED_SEQUENCE_DIGEST = "f7f2cad01184e8651bcc722b755a2f3c2292ca13e81c7399579d7f42e0c19b30"
TOL = 1e-12


def _close(a: float, b: float) -> bool:
    return abs(float(a) - float(b)) <= TOL


def _source_profile(states: list[dict[str, Any]]) -> tuple[list[tuple[str, float]], float, float, float]:
    if len(states) != EXPECTED_STATE_COUNT:
        raise ValueError(f"expected {EXPECTED_STATE_COUNT} dense states, got {len(states)}")
    profiles: list[list[tuple[str, float]]] = []
    for state in states:
        lines = state.get("candidate_scene", {}).get("weather_lines", [])
        if len(lines) != EXPECTED_STREAK_COUNT:
            raise ValueError(f"expected {EXPECTED_STREAK_COUNT} Weather streaks per state")
        profile: list[tuple[str, float]] = []
        for row in lines:
            streak_id = str(row.get("id", ""))
            opacity = float(row.get("opacity", -1.0))
            if not streak_id:
                raise ValueError("Weather streak identity missing")
            if opacity < 0.0 or opacity > 1.0:
                raise ValueError(f"Weather streak opacity outside [0,1]: {opacity}")
            profile.append((streak_id, opacity))
        if len({row[0] for row in profile}) != EXPECTED_STREAK_COUNT:
            raise ValueError("Weather streak identities must be unique")
        profiles.append(profile)
    first = profiles[0]
    if any(profile != first for profile in profiles[1:]):
        raise ValueError("source-owned streak identity/opacity profile drifted across dense motion states")
    values = [row[1] for row in first]
    return first, min(values), max(values), sum(values) / len(values)


def verify(payload: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    states = payload.get("states", [])
    samples = receipt.get("samples", [])
    source_error = None
    profile: list[tuple[str, float]] = []
    source_min = source_max = source_mean = -1.0
    try:
        profile, source_min, source_max, source_mean = _source_profile(states)
    except (TypeError, ValueError, KeyError) as exc:
        source_error = str(exc)

    checks: dict[str, bool] = {
        "dense_source_sequence_pass": payload.get("status") == "PASS_DENSE_INTERMEDIATE_SOURCE_SEQUENCE",
        "exact_weather_source_head_preserved": payload.get("weather_source_head") == EXPECTED_WEATHER_SOURCE_HEAD,
        "exact_dense_sequence_digest_preserved": payload.get("sequence_digest") == EXPECTED_SEQUENCE_DIGEST,
        "source_opacity_profile_valid": source_error is None,
        "source_opacity_has_authored_variation": source_error is None and source_min < source_max,
        "target_host_observation_pass": receipt.get("state") == "PASS_DENSE_INTERMEDIATE_LIVE_OBSERVATION",
        "exact_fidelity_donor_provenance": receipt.get("weather_opacity_fidelity_head") == EXPECTED_FIDELITY_DONOR_HEAD,
        "exact_opacity_mode_declared": receipt.get("weather_opacity_mode") == EXPECTED_OPACITY_MODE,
        "seventeen_target_host_updates": len(samples) == EXPECTED_STATE_COUNT,
    }

    runtime_rows: list[dict[str, Any]] = []
    runtime_ok = len(samples) == EXPECTED_STATE_COUNT and source_error is None
    if runtime_ok:
        for sample in samples:
            update = sample.get("weather_update", {})
            row = {
                "index": sample.get("index"),
                "state": update.get("state"),
                "opacity_mode": update.get("opacity_mode"),
                "source_opacity_consumed": update.get("source_opacity_consumed"),
                "streak_count": update.get("streak_count"),
                "surface_count": update.get("surface_count"),
                "source_opacity_min": update.get("source_opacity_min"),
                "source_opacity_max": update.get("source_opacity_max"),
                "source_opacity_mean": update.get("source_opacity_mean"),
                "opacity_fidelity_provenance_head": update.get("opacity_fidelity_provenance_head"),
                "width_policy": update.get("width_policy"),
            }
            runtime_rows.append(row)
            try:
                row_ok = (
                    update.get("state") == "PASS_SOURCE_STREAK_OPACITY_CONSUMED"
                    and update.get("opacity_mode") == EXPECTED_OPACITY_MODE
                    and update.get("source_opacity_consumed") is True
                    and int(update.get("streak_count", -1)) == EXPECTED_STREAK_COUNT
                    and int(update.get("surface_count", -1)) == 1
                    and _close(float(update.get("source_opacity_min", -2.0)), source_min)
                    and _close(float(update.get("source_opacity_max", -2.0)), source_max)
                    and _close(float(update.get("source_opacity_mean", -2.0)), source_mean)
                    and update.get("opacity_fidelity_provenance_head") == EXPECTED_FIDELITY_DONOR_HEAD
                    and update.get("width_policy") == "SOURCE_WIDTH_PX_NOT_MAPPED_TO_3D_LINE_WIDTH_IN_THIS_PROOF"
                )
            except (TypeError, ValueError):
                row_ok = False
            runtime_ok = runtime_ok and row_ok

    checks["every_live_update_consumes_exact_source_opacity"] = runtime_ok

    result = {
        "schema": SCHEMA,
        "state": "PASS_DENSE_LIVE_SOURCE_OPACITY_FIDELITY" if all(checks.values()) else "FAIL",
        "weather_source_head": payload.get("weather_source_head"),
        "fidelity_donor": {
            "repository": "mike-axiom-mir/axm-map-design",
            "pr": 9,
            "head": EXPECTED_FIDELITY_DONOR_HEAD,
            "role": "PROVEN_RECEIVING_MECHANISM_PROVENANCE_NOT_SOURCE_AUTHORITY",
        },
        "sequence_digest": payload.get("sequence_digest"),
        "checks": checks,
        "source_opacity": {
            "streak_count": len(profile),
            "minimum": source_min if source_error is None else None,
            "maximum": source_max if source_error is None else None,
            "mean": source_mean if source_error is None else None,
            "profile_stable_across_all_states": source_error is None,
            "error": source_error,
        },
        "runtime_updates": runtime_rows,
        "truth_boundary": (
            "PASS proves only that the exact source-owned per-streak opacity already present in all 17 dense Weather states is consumed by the same-process Godot proof host through one stable Weather material/mesh resource path, using the previously proven PR #9 vertex-alpha mechanism. "
            "The exact dense Weather/Nature geometry sequence remains unchanged. This does not prove final atmosphere quality, source width_px fidelity, wall-clock pacing, renderer interpolation, physical wind, precipitation/fog/volumetrics, gameplay visibility, target-device performance, CANON, production readiness, or VFX mastery."
        ),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    result = verify(payload, receipt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": result["state"], "checks": result["checks"], "source_opacity": result["source_opacity"]}, indent=2, sort_keys=True))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
