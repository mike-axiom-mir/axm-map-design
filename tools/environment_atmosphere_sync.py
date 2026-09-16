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

import environment_motion_scene as motion
import environment_real_slice as integration
import environment_weather_sequence as weather_sequence

SCHEMA = "axm.environment-atmosphere-sync-proof/v0.1"
EVIDENCE_SCHEMA = "axm.environment-atmosphere-sync-proof-evidence/v0.1"
SCENE_SCHEMA = "axm.environment-atmosphere-sync-scene/v0.1"
EXPECTED_WEATHER_SEQUENCE_HEAD = "10f1152b73240d0755bb14fa1c7744da3c544355"
EXPECTED_NATURE_RESPONSE_HEAD = "cee14f5b3feea78b0adcd044bad2ea3c97657fc6"
EXPECTED_WEATHER_HEAD = "ca2eaba519e8449835b0ea6ef944b7080c3caa6a"
VISUAL_ONLY_SEMANTICS = "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED"
MAX_DISPLACEMENT_M = 0.18
TOL = 1e-9


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _bounds(vertices: list[list[float]]) -> dict:
    return {
        "min": [min(float(v[i]) for v in vertices) for i in range(3)],
        "max": [max(float(v[i]) for v in vertices) for i in range(3)],
    }


def _footprint(bounds: dict) -> tuple[float, float, float, float]:
    return (
        float(bounds["min"][0]),
        float(bounds["max"][0]),
        float(bounds["min"][1]),
        float(bounds["max"][1]),
    )


def _item_footprint(item: dict) -> tuple[float, float, float, float]:
    x, y = float(item["position_m"][0]), float(item["position_m"][1])
    sx, sy = float(item["size_m"][0]), float(item["size_m"][1])
    return (x - sx * 0.5, x + sx * 0.5, y - sy * 0.5, y + sy * 0.5)


def _max_displacement(neutral: list[list[float]], candidate: list[list[float]]) -> float:
    if len(neutral) != len(candidate):
        raise ValueError("sapling vertex count drift")
    maximum = 0.0
    for before, after in zip(neutral, candidate):
        distance = sum((float(after[i]) - float(before[i])) ** 2 for i in range(3)) ** 0.5
        maximum = max(maximum, distance)
    return maximum


def _scene_static_digest(scene: dict) -> str:
    return digest({
        "items": scene["items"],
        "cameras": scene["cameras"],
        "readable_path": scene["readable_path"],
        "weather_presentation": scene["weather_presentation"],
        "source_integration": scene["source_integration"],
    })


def build_sync_payload(
    manifest_path: str | Path,
    nature_root: str | Path,
    weather_root: str | Path,
    nature_response_head: str,
) -> dict:
    if nature_response_head != EXPECTED_NATURE_RESPONSE_HEAD:
        raise ValueError("Nature response head mismatch")

    root = Path(__file__).resolve().parents[1]
    manifest = integration.load_manifest(manifest_path)
    weather_payload = weather_sequence.build_sequence_payload(manifest_path, nature_root, weather_root)
    if weather_payload["status"] != "PASS":
        raise ValueError("sampled Weather receiving sequence must PASS first")

    motion_payload = motion.build_scene_payload(
        manifest_path,
        nature_root,
        weather_root,
        nature_response_head,
    )
    motion_report = motion.evaluate(motion_payload)
    if motion_report["status"] != "PASS":
        raise ValueError("existing neutral/peak Environment motion proof must PASS first")

    integration_report, variant, _, neutral_world, _, weather_module, weather_source = integration.evaluate_integration(
        root, manifest, nature_root, weather_root
    )
    if integration_report["status"] != "PASS":
        raise ValueError("Environment source integration must PASS first")

    response, source, spec, response_evidence, neutral_local, _ = motion._load_response(nature_root)
    if response_evidence.get("state") != "PASS_BOUNDED_VISUAL_WIND_RESPONSE":
        raise ValueError("Nature response must re-pass before atmosphere synchronization")

    source_wind = [float(v) for v in weather_source["wind_xy"]]
    response_wind = [float(v) for v in spec["weather_provenance"]["visual_wind_xy"]]
    response_duration = float(spec["response"]["duration_s"])
    source_times = [float(v) for v in weather_source["times_s"]]
    schedule = [float(v) for v in weather_payload["sampling_schedule_s"]]

    static_world = {
        "vertices": weather_payload["states"][0]["scene"]["sapling"]["vertices_source_xyz_m"]
    }
    translation = motion._translation(neutral_local, static_world)
    neutral_world_vertices = [[float(x) for x in v] for v in neutral_world["vertices"]]
    if static_world["vertices"] != neutral_world_vertices:
        raise ValueError("Weather sequence and motion proof do not share the same neutral sapling placement")

    path = variant["readable_path"]
    path_box = (
        float(path["x_min"]),
        float(path["x_max"]),
        float(path["y_min"]),
        float(path["y_max"]),
    )
    clearance = float(variant["minimum_gap_m"])
    static_digest = _scene_static_digest(weather_payload["states"][0]["scene"])

    states = []
    for weather_row in weather_payload["states"]:
        index = int(weather_row["index"])
        time_s = float(weather_row["time_s"])
        if time_s < -TOL or time_s > response_duration + TOL:
            raise ValueError("shared sample time falls outside Nature response window")

        local_mesh = response.deform_mesh(source, spec, time_s)
        world_mesh = motion._translate_mesh(local_mesh, translation)
        world_vertices = [[float(x) for x in v] for v in world_mesh["vertices"]]
        bounds = _bounds(world_vertices)
        footprint = _footprint(bounds)

        control = copy.deepcopy(weather_row["scene"])
        candidate = copy.deepcopy(control)
        candidate["schema"] = SCENE_SCHEMA
        candidate["study_id"] = f"environment-atmosphere-sync-001-{index:02d}"
        candidate["sapling"]["vertices_source_xyz_m"] = world_vertices
        candidate["sapling"]["triangles"] = [[int(v) for v in tri] for tri in world_mesh["triangles"]]
        candidate["sapling"]["visual_response"] = {
            "repository": "mike-axiom-mir/axm-nature-design",
            "pr": 2,
            "head": nature_response_head,
            "profile": spec["response"]["profile"],
            "sample_time_s": time_s,
            "semantics": spec["weather_provenance"]["semantics"],
        }
        candidate["atmosphere_sync"] = {
            "sample_index": index,
            "sample_time_s": time_s,
            "weather_sequence_head": EXPECTED_WEATHER_SEQUENCE_HEAD,
            "weather_source_head": EXPECTED_WEATHER_HEAD,
            "nature_response_head": nature_response_head,
            "relationship": "SHARED_EVIDENCE_CLOCK_AND_EXACT_VISUAL_DIRECTION_NOT_PHYSICAL_COUPLING",
        }
        candidate["truth_boundary"] = (
            "This exact receiving state samples the already-authored Weather visual field and already-accepted Nature visual sway response at one shared evidence time and direction. "
            "It proves neither physical wind coupling nor forces, gameplay, collision, continuous playback, final atmosphere quality, runtime performance, CANON, or mastery."
        )
        candidate.pop("scene_digest", None)
        candidate["scene_digest"] = digest(candidate)

        spacing_conflicts = []
        for item in control["items"]:
            if item["kind"] == "map-surface":
                continue
            if integration._intersects(footprint, _item_footprint(item), clearance):
                spacing_conflicts.append(item["asset_id"])

        states.append({
            "index": index,
            "time_s": time_s,
            "weather_field_digest": weather_row["field_digest"],
            "control_scene_digest": control["scene_digest"],
            "candidate_scene_digest": candidate["scene_digest"],
            "sapling_mesh_digest": digest({"vertices": world_vertices, "triangles": world_mesh["triangles"]}),
            "sapling_max_neutral_displacement_m": _max_displacement(neutral_world_vertices, world_vertices),
            "sapling_bounds_source_xyz_m": bounds,
            "sapling_path_unblocked": not integration._intersects(footprint, path_box),
            "sapling_spacing_conflicts": spacing_conflicts,
            "control_scene": control,
            "candidate_scene": candidate,
        })

    first_vertices = states[0]["candidate_scene"]["sapling"]["vertices_source_xyz_m"]
    last_vertices = states[-1]["candidate_scene"]["sapling"]["vertices_source_xyz_m"]
    midpoint = states[len(states) // 2]
    peak_displacement = max(row["sapling_max_neutral_displacement_m"] for row in states)

    checks = {
        "weather_sequence_prerequisite_pass": weather_payload["status"] == "PASS",
        "motion_prerequisite_pass": motion_report["status"] == "PASS",
        "environment_source_integration_pass": integration_report["status"] == "PASS",
        "weather_source_revalidated": weather_module.evaluate(weather_source).get("status") == "PASS",
        "nature_response_revalidated": response_evidence.get("state") == "PASS_BOUNDED_VISUAL_WIND_RESPONSE",
        "nature_response_head_pinned": nature_response_head == EXPECTED_NATURE_RESPONSE_HEAD,
        "weather_source_head_pinned": weather_payload["weather_source"]["head"] == EXPECTED_WEATHER_HEAD,
        "visual_only_semantics_match": spec["weather_provenance"]["semantics"] == VISUAL_ONLY_SEMANTICS and weather_source["wind_semantics"] == VISUAL_ONLY_SEMANTICS,
        "visual_direction_matches_exactly": response_wind == source_wind,
        "shared_nine_sample_clock": schedule == weather_sequence.SAMPLE_TIMES_S and len(states) == 9,
        "shared_clock_inside_both_authored_windows": schedule[0] >= source_times[0] - TOL and schedule[-1] <= source_times[-1] + TOL and schedule[0] >= -TOL and schedule[-1] <= response_duration + TOL,
        "weather_field_preserved_exactly_per_sample": all(row["candidate_scene"]["weather_lines"] == row["control_scene"]["weather_lines"] for row in states),
        "static_receiving_context_preserved": all(_scene_static_digest(row["candidate_scene"]) == static_digest for row in states),
        "sapling_topology_preserved": all(len(row["candidate_scene"]["sapling"]["vertices_source_xyz_m"]) == 390 and len(row["candidate_scene"]["sapling"]["triangles"]) == 570 for row in states),
        "sapling_path_unblocked_all_samples": all(row["sapling_path_unblocked"] for row in states),
        "sapling_spacing_preserved_all_samples": all(not row["sapling_spacing_conflicts"] for row in states),
        "sapling_displacement_bounded_all_samples": peak_displacement <= MAX_DISPLACEMENT_M + TOL,
        "exact_neutral_start_return": first_vertices == weather_payload["states"][0]["scene"]["sapling"]["vertices_source_xyz_m"],
        "exact_neutral_end_return": last_vertices == weather_payload["states"][-1]["scene"]["sapling"]["vertices_source_xyz_m"],
        "midpoint_sapling_visibly_changed_in_payload": midpoint["candidate_scene"]["sapling"]["vertices_source_xyz_m"] != midpoint["control_scene"]["sapling"]["vertices_source_xyz_m"],
        "weather_fields_remain_distinct": len({row["weather_field_digest"] for row in states}) == 9,
    }

    payload = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": "environment-atmosphere-sync-001",
        "status": "PASS_SYNCHRONIZED_VISUAL_ATMOSPHERE_SEQUENCE" if all(checks.values()) else "FAIL",
        "receiving_head": os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD"),
        "stacked_on_weather_sequence_head": EXPECTED_WEATHER_SEQUENCE_HEAD,
        "nature_response": {
            "repository": "mike-axiom-mir/axm-nature-design",
            "pr": 2,
            "head": nature_response_head,
            "profile": spec["response"]["profile"],
            "duration_s": response_duration,
            "visual_wind_xy": response_wind,
            "semantics": spec["weather_provenance"]["semantics"],
            "max_displacement_ceiling_m": float(spec["response"]["max_displacement_ceiling_m"]),
        },
        "weather_source": weather_payload["weather_source"],
        "sampling_schedule_s": schedule,
        "shared_relationship": "SHARED_EVIDENCE_CLOCK_AND_EXACT_VISUAL_DIRECTION_NOT_PHYSICAL_COUPLING",
        "checks": checks,
        "measurements": {
            "maximum_sampled_sapling_displacement_m": peak_displacement,
            "neutral_endpoint_indices": [0, len(states) - 1],
            "peak_sample_index": max(range(len(states)), key=lambda i: states[i]["sapling_max_neutral_displacement_m"]),
            "weather_field_count": len(states),
            "weather_streaks_per_state": len(states[0]["candidate_scene"]["weather_lines"]),
        },
        "states": states,
        "truth_boundary": (
            "PASS means only that the exact source-owned Weather visual field and exact accepted Nature visual sway response can be sampled on one shared 0.0-0.5 s evidence clock and exact visual direction in the same receiving scene, while preserving Weather field identity, sapling topology, path/spacing gates, visual-only semantics and exact neutral return. "
            "It does not establish physical wind/force coupling, precipitation, continuous interpolation or frame pacing, target performance, final Art Direction, gameplay, collision, CANON, production readiness, or VFX mastery."
        ),
    }
    payload["sequence_digest"] = digest({k: v for k, v in payload.items() if k != "states"} | {
        "state_digests": [row["candidate_scene_digest"] for row in states]
    })
    return payload


def build(manifest_path, nature_root, weather_root, nature_response_head, output_dir) -> dict:
    payload = build_sync_payload(manifest_path, nature_root, weather_root, nature_response_head)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "atmosphere_sync.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for row in payload["states"]:
        index = int(row["index"])
        (output / f"control_scene_{index:02d}.json").write_text(json.dumps(row["control_scene"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (output / f"candidate_scene_{index:02d}.json").write_text(json.dumps(row["candidate_scene"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_real_slice_001.json")
    parser.add_argument("--nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--nature-response-head", required=True)
    parser.add_argument("--output", default="evidence/environment_atmosphere_sync_001")
    args = parser.parse_args()
    report = build(args.manifest, args.nature_root, args.weather_root, args.nature_response_head, args.output)
    print(json.dumps({k: report[k] for k in ("schema", "study_id", "status", "checks", "measurements", "sequence_digest")}, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS_SYNCHRONIZED_VISUAL_ATMOSPHERE_SEQUENCE" else 1)


if __name__ == "__main__":
    main()
