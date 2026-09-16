from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_eye_level as eye
import environment_real_slice as integration

SCHEMA = "axm.environment-weather-sequence-proof/v0.1"
EVIDENCE_SCHEMA = "axm.environment-weather-sequence-proof-evidence/v0.1"
EXPECTED_ENVIRONMENT_HEAD = "8f81c57d9169dc9faba0cb01b85f17dff92bad6f"
EXPECTED_WEATHER_HEAD = "ca2eaba519e8449835b0ea6ef944b7080c3caa6a"
EXPECTED_WEATHER_SEMANTICS = "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED"
SAMPLE_TIMES_S = [0.0, 0.0625, 0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5]
TOL = 1e-9


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _unit(vector):
    x, y = map(float, vector)
    length = (x * x + y * y) ** 0.5
    if length <= 0.0:
        raise ValueError("visual wind must be nonzero")
    return x / length, y / length


def _weather_lines(weather_module, weather_source: dict, particles: list[dict], time_s: float) -> list[dict]:
    rows = []
    for index, particle in enumerate(particles):
        sample = weather_module.sample_particle(particle, weather_source, time_s)
        rows.append({
            "id": particle["id"],
            "tail_xy": [float(sample["tail_x"]), float(sample["tail_y"])],
            "head_xy": [float(sample["x"]), float(sample["y"])],
            "opacity": float(particle["opacity"]),
            "presentation_height_m": 3.0,
            "source_order": index,
        })
    return rows


def _field_digest(lines: list[dict]) -> str:
    return digest([
        {
            "id": row["id"],
            "tail_xy": row["tail_xy"],
            "head_xy": row["head_xy"],
            "source_order": row["source_order"],
        }
        for row in lines
    ])


def _inside_extent(lines: list[dict], width: float, height: float) -> bool:
    xmin, xmax = -width / 2.0, width / 2.0
    ymin, ymax = -height / 2.0, height / 2.0
    for row in lines:
        for key in ("tail_xy", "head_xy"):
            x, y = map(float, row[key])
            if x < xmin - TOL or x > xmax + TOL or y < ymin - TOL or y > ymax + TOL:
                return False
    return True


def _motion_metrics(states: list[dict], visual_wind_xy, visual_speed: float) -> dict:
    ux, uy = _unit(visual_wind_xy)
    cross_x, cross_y = -uy, ux
    projected_errors = []
    crosswind = []
    identity_errors = []
    for before, after in zip(states, states[1:]):
        dt = float(after["time_s"]) - float(before["time_s"])
        expected = visual_speed * dt
        before_rows = before["weather_lines"]
        after_rows = after["weather_lines"]
        if [r["id"] for r in before_rows] != [r["id"] for r in after_rows]:
            identity_errors.append("particle identity/order drift")
            continue
        for a, b in zip(before_rows, after_rows):
            dx = float(b["head_xy"][0]) - float(a["head_xy"][0])
            dy = float(b["head_xy"][1]) - float(a["head_xy"][1])
            projected_errors.append(abs((dx * ux + dy * uy) - expected))
            crosswind.append(abs(dx * cross_x + dy * cross_y))
    return {
        "maximum_adjacent_projected_displacement_error_m": max(projected_errors, default=0.0),
        "maximum_adjacent_crosswind_drift_m": max(crosswind, default=0.0),
        "identity_errors": identity_errors,
    }


def build_sequence_payload(manifest_path: str | Path, nature_root: str | Path, weather_root: str | Path) -> dict:
    root = Path(__file__).resolve().parents[1]
    manifest = integration.load_manifest(manifest_path)
    base_scene = eye.build_scene_payload(manifest_path, nature_root, weather_root)
    report, _, _, _, _, weather_module, weather_source = integration.evaluate_integration(
        root, manifest, nature_root, weather_root
    )
    if report["status"] != "PASS":
        raise ValueError("Environment source integration must PASS before Weather sequence proof")
    weather_evidence = weather_module.evaluate(weather_source)
    if weather_evidence.get("status") != "PASS":
        raise ValueError("Weather source must re-pass before receiving-scene sequence proof")
    if report["weather_overlay"]["source_head"] != EXPECTED_WEATHER_HEAD:
        raise ValueError("Weather source head mismatch")
    if weather_source.get("wind_semantics") != EXPECTED_WEATHER_SEMANTICS:
        raise ValueError("Weather semantics drifted from visual-only contract")

    authored_times = [float(t) for t in weather_source["times_s"]]
    if SAMPLE_TIMES_S[0] < authored_times[0] - TOL or SAMPLE_TIMES_S[-1] > authored_times[-1] + TOL:
        raise ValueError("evidence sequence may not extend beyond the authored Weather proof window")

    particles = weather_module.make_particles(weather_source)
    width, height = map(float, weather_source["scene_size_m"])
    states = []
    static_reference = {
        "items": base_scene["items"],
        "sapling": base_scene["sapling"],
        "cameras": base_scene["cameras"],
        "readable_path": base_scene["readable_path"],
        "weather_presentation": base_scene["weather_presentation"],
    }
    static_digest = digest(static_reference)

    for index, time_s in enumerate(SAMPLE_TIMES_S):
        lines = _weather_lines(weather_module, weather_source, particles, time_s)
        state = copy.deepcopy(base_scene)
        state["schema"] = SCHEMA
        state["study_id"] = f"environment-weather-sequence-001-{index:02d}"
        state["weather_lines"] = lines
        state["weather_sequence"] = {
            "sample_index": index,
            "sample_time_s": time_s,
            "sampling_role": "EVIDENCE_ONLY_INTERMEDIATE_SAMPLE_NOT_NEW_WEATHER_SOURCE_SEMANTICS",
            "source_repository": "mike-axiom-mir/axm-weather-design",
            "source_pr": 2,
            "source_head": EXPECTED_WEATHER_HEAD,
            "source_digest": weather_module.digest(weather_source),
            "visual_speed_m_per_s": float(weather_source["visual_speed_m_per_s"]),
            "wind_semantics": weather_source["wind_semantics"],
        }
        state["truth_boundary"] = (
            "This state preserves the exact Environment scene and source-owned Weather field while sampling the existing visual-only streak motion inside the already-authored 0.0-0.5 s proof window. "
            "It does not establish physical wind, precipitation, volumetrics, continuous playback quality, runtime update cost, final Environment art, gameplay, CANON, or mastery."
        )
        state.pop("scene_digest", None)
        state["scene_digest"] = digest(state)
        states.append({
            "index": index,
            "time_s": time_s,
            "field_digest": _field_digest(lines),
            "all_endpoints_inside_scene_extent": _inside_extent(lines, width, height),
            "scene": state,
        })

    metrics = _motion_metrics(states, weather_source["wind_xy"], float(weather_source["visual_speed_m_per_s"]))
    field_digests = [row["field_digest"] for row in states]
    checks = {
        "environment_source_integration_pass": report["status"] == "PASS",
        "weather_source_revalidated": weather_evidence.get("status") == "PASS",
        "weather_head_pinned": report["weather_overlay"]["source_head"] == EXPECTED_WEATHER_HEAD,
        "visual_only_semantics_preserved": weather_source.get("wind_semantics") == EXPECTED_WEATHER_SEMANTICS,
        "nine_sorted_samples_inside_authored_window": len(states) == 9 and SAMPLE_TIMES_S == sorted(SAMPLE_TIMES_S) and SAMPLE_TIMES_S[0] == 0.0 and SAMPLE_TIMES_S[-1] == 0.5,
        "all_36_streaks_preserved": all(len(row["scene"]["weather_lines"]) == 36 for row in states),
        "all_line_endpoints_inside_scene_extent": all(row["all_endpoints_inside_scene_extent"] for row in states),
        "all_sampled_fields_distinct": len(set(field_digests)) == len(field_digests),
        "adjacent_motion_matches_visual_speed": metrics["maximum_adjacent_projected_displacement_error_m"] <= TOL,
        "adjacent_crosswind_drift_zero": metrics["maximum_adjacent_crosswind_drift_m"] <= TOL,
        "particle_identity_order_preserved": not metrics["identity_errors"],
        "receiving_scene_static_state_preserved": all(
            digest({
                "items": row["scene"]["items"],
                "sapling": row["scene"]["sapling"],
                "cameras": row["scene"]["cameras"],
                "readable_path": row["scene"]["readable_path"],
                "weather_presentation": row["scene"]["weather_presentation"],
            }) == static_digest
            for row in states
        ),
    }

    payload = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": "environment-weather-sequence-001",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "receiving_head": os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD"),
        "environment_base_head": EXPECTED_ENVIRONMENT_HEAD,
        "weather_source": {
            "repository": "mike-axiom-mir/axm-weather-design",
            "pr": 2,
            "head": EXPECTED_WEATHER_HEAD,
            "source_digest": weather_module.digest(weather_source),
            "semantics": weather_source["wind_semantics"],
            "visual_speed_m_per_s": float(weather_source["visual_speed_m_per_s"]),
            "visual_wind_xy": [float(x) for x in weather_source["wind_xy"]],
            "source_authored_times_s": authored_times,
        },
        "sampling_schedule_s": SAMPLE_TIMES_S,
        "sampling_role": "VFX_EVIDENCE_ONLY_WITHIN_AUTHORED_SOURCE_WINDOW",
        "checks": checks,
        "motion_metrics": metrics,
        "static_receiving_state_digest": static_digest,
        "states": states,
        "truth_boundary": (
            "PASS means only that nine deterministic source-derived Weather field states inside the existing authored window preserve exact Environment scene state, particle identity, downwind visual displacement, no-wrap scene extent, and visual-only semantics. "
            "Target-host renders may prove those sampled states are renderable but not continuous live playback, runtime cost, physical weather, gameplay, final art direction, CANON, or mastery."
        ),
    }
    payload["sequence_digest"] = digest(payload)
    return payload


def build(manifest_path: str | Path, nature_root: str | Path, weather_root: str | Path, output_dir: str | Path) -> dict:
    payload = build_sequence_payload(manifest_path, nature_root, weather_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "weather_sequence.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for row in payload["states"]:
        (output / f"scene_{row['index']:02d}.json").write_text(json.dumps(row["scene"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_real_slice_001.json")
    parser.add_argument("--nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--output", default="evidence/environment_weather_sequence_001")
    args = parser.parse_args()
    report = build(args.manifest, args.nature_root, args.weather_root, args.output)
    print(json.dumps({k: report[k] for k in ("schema", "study_id", "status", "checks", "motion_metrics", "sequence_digest")}, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
