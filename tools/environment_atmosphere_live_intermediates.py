from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_atmosphere_sync as sync
import environment_motion_scene as motion
import environment_real_slice as integration
import environment_weather_sequence as weather_sequence

SCHEMA = "axm.environment-atmosphere-live-intermediates-evidence/v0.1"
TARGET_HOST_SCHEMA = "axm.environment-atmosphere-live-intermediates-target-host-evidence/v0.1"
EXPECTED_RUNTIME_HEAD = "f0c72b9dd4688bdb01ac40aa33f469afffd7ec0a"
EXPECTED_SYNC_HEAD = "d476cf7c11de74c53397cb21e6f40f90a51c0356"
EXPECTED_NATURE_HEAD = "cee14f5b3feea78b0adcd044bad2ea3c97657fc6"
EXPECTED_WEATHER_HEAD = "ca2eaba519e8449835b0ea6ef944b7080c3caa6a"
RELATIONSHIP = "SHARED_EVIDENCE_CLOCK_AND_EXACT_VISUAL_DIRECTION_NOT_PHYSICAL_COUPLING"
DENSE_TIMES_S = [i / 32.0 for i in range(17)]
TOL = 1e-9
CONTEXTS = ("path_eye", "elevated_oblique")


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bounds(vertices: list[list[float]]) -> dict[str, list[float]]:
    return {
        "min": [min(float(v[i]) for v in vertices) for i in range(3)],
        "max": [max(float(v[i]) for v in vertices) for i in range(3)],
    }


def _footprint(bounds: dict[str, list[float]]) -> tuple[float, float, float, float]:
    return (
        float(bounds["min"][0]), float(bounds["max"][0]),
        float(bounds["min"][1]), float(bounds["max"][1]),
    )


def _item_footprint(item: dict[str, Any]) -> tuple[float, float, float, float]:
    x, y = float(item["position_m"][0]), float(item["position_m"][1])
    sx, sy = float(item["size_m"][0]), float(item["size_m"][1])
    return (x - sx * 0.5, x + sx * 0.5, y - sy * 0.5, y + sy * 0.5)


def _max_displacement(neutral: list[list[float]], candidate: list[list[float]]) -> float:
    if len(neutral) != len(candidate):
        raise ValueError("sapling vertex count drift")
    result = 0.0
    for before, after in zip(neutral, candidate):
        result = max(result, sum((float(after[i]) - float(before[i])) ** 2 for i in range(3)) ** 0.5)
    return result


def _monotonic(values: list[float], rising: bool) -> bool:
    pairs = zip(values, values[1:])
    if rising:
        return all(b + TOL >= a for a, b in pairs)
    return all(b <= a + TOL for a, b in pairs)


def build_payload(manifest_path: str | Path, nature_root: str | Path, weather_root: str | Path) -> dict[str, Any]:
    base = sync.build_sync_payload(manifest_path, nature_root, weather_root, EXPECTED_NATURE_HEAD)
    if base.get("status") != "PASS_SYNCHRONIZED_VISUAL_ATMOSPHERE_SEQUENCE":
        raise ValueError("exact synchronized atmosphere prerequisite must PASS")
    if base.get("receiving_head") != EXPECTED_SYNC_HEAD:
        raise ValueError("synchronized prerequisite must be rebuilt with exact VFX receiving head")
    if base.get("shared_relationship") != RELATIONSHIP:
        raise ValueError("visual-only synchronization relationship drift")

    root = Path(__file__).resolve().parents[1]
    manifest = integration.load_manifest(manifest_path)
    report, variant, _, neutral_world, _, weather_module, weather_source = integration.evaluate_integration(
        root, manifest, nature_root, weather_root
    )
    if report.get("status") != "PASS":
        raise ValueError("Environment source integration must PASS")
    if weather_module.evaluate(weather_source).get("status") != "PASS":
        raise ValueError("Weather source must re-pass")

    response, source, spec, response_evidence, neutral_local, _ = motion._load_response(nature_root)
    if response_evidence.get("state") != "PASS_BOUNDED_VISUAL_WIND_RESPONSE":
        raise ValueError("Nature visual response must re-pass")
    if spec["weather_provenance"]["head"] != EXPECTED_WEATHER_HEAD:
        raise ValueError("Nature response Weather head drift")
    if spec["weather_provenance"]["semantics"] != "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED":
        raise ValueError("Nature response semantics must remain visual-only")

    particles = weather_module.make_particles(weather_source)
    neutral_world_vertices = [[float(x) for x in v] for v in neutral_world["vertices"]]
    translation = motion._translation(neutral_local, {"vertices": neutral_world_vertices})
    control_template = copy.deepcopy(base["states"][0]["control_scene"])
    path = variant["readable_path"]
    path_box = (
        float(path["x_min"]), float(path["x_max"]),
        float(path["y_min"]), float(path["y_max"]),
    )
    clearance = float(variant["minimum_gap_m"])

    states: list[dict[str, Any]] = []
    for index, time_s in enumerate(DENSE_TIMES_S):
        lines = weather_sequence._weather_lines(weather_module, weather_source, particles, time_s)
        field_digest = weather_sequence._field_digest(lines)

        control = copy.deepcopy(control_template)
        control["schema"] = "axm.environment-atmosphere-live-intermediate-scene/v0.1"
        control["study_id"] = f"environment-atmosphere-live-intermediates-001-{index:02d}"
        control["weather_lines"] = lines
        control["weather_sequence"] = {
            "sample_index": index,
            "sample_time_s": time_s,
            "sampling_role": "DENSE_INTERMEDIATE_VFX_EVIDENCE_ONLY_NOT_NEW_SOURCE_SEMANTICS",
            "source_repository": "mike-axiom-mir/axm-weather-design",
            "source_pr": 2,
            "source_head": EXPECTED_WEATHER_HEAD,
            "source_digest": weather_module.digest(weather_source),
            "visual_speed_m_per_s": float(weather_source["visual_speed_m_per_s"]),
            "wind_semantics": weather_source["wind_semantics"],
        }
        control.pop("scene_digest", None)
        control["scene_digest"] = digest(control)

        local_mesh = response.deform_mesh(source, spec, time_s)
        world_mesh = motion._translate_mesh(local_mesh, translation)
        world_vertices = [[float(x) for x in v] for v in world_mesh["vertices"]]
        bounds = _bounds(world_vertices)
        footprint = _footprint(bounds)

        candidate = copy.deepcopy(control)
        candidate["sapling"]["vertices_source_xyz_m"] = world_vertices
        candidate["sapling"]["triangles"] = [[int(v) for v in tri] for tri in world_mesh["triangles"]]
        candidate["sapling"]["visual_response"] = {
            "repository": "mike-axiom-mir/axm-nature-design",
            "pr": 2,
            "head": EXPECTED_NATURE_HEAD,
            "profile": spec["response"]["profile"],
            "sample_time_s": time_s,
            "semantics": spec["weather_provenance"]["semantics"],
        }
        candidate["atmosphere_live_intermediate"] = {
            "sample_index": index,
            "sample_time_s": time_s,
            "stacked_on_runtime_head": EXPECTED_RUNTIME_HEAD,
            "stacked_on_sync_head": EXPECTED_SYNC_HEAD,
            "relationship": RELATIONSHIP,
        }
        candidate["truth_boundary"] = (
            "This state directly evaluates the already-authored Weather field and accepted Nature visual response at one dense intermediate evidence time. "
            "It is visual-only evidence and does not establish physical wind, real-time pacing, renderer interpolation, gameplay, collision, final art, CANON, or mastery."
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
            "inherited_nine_sample_index": index // 2 if index % 2 == 0 else None,
            "sampling_role": "INHERITED_EXACT_SAMPLE" if index % 2 == 0 else "NEW_HALF_STEP_INTERMEDIATE",
            "weather_field_digest": field_digest,
            "sapling_mesh_digest": digest({"vertices": world_vertices, "triangles": world_mesh["triangles"]}),
            "sapling_max_neutral_displacement_m": _max_displacement(neutral_world_vertices, world_vertices),
            "sapling_path_unblocked": not integration._intersects(footprint, path_box),
            "sapling_spacing_conflicts": spacing_conflicts,
            "candidate_scene": candidate,
        })

    even_rows = states[::2]
    inherited_rows = base["states"]
    even_exact = len(even_rows) == len(inherited_rows) and all(
        row["time_s"] == inherited["time_s"]
        and row["weather_field_digest"] == inherited["weather_field_digest"]
        and row["sapling_mesh_digest"] == inherited["sapling_mesh_digest"]
        and row["candidate_scene"]["weather_lines"] == inherited["candidate_scene"]["weather_lines"]
        and row["candidate_scene"]["sapling"]["vertices_source_xyz_m"] == inherited["candidate_scene"]["sapling"]["vertices_source_xyz_m"]
        for row, inherited in zip(even_rows, inherited_rows)
    )

    odd_rows = states[1::2]
    odd_are_new = all(
        row["weather_field_digest"] not in {states[row["index"] - 1]["weather_field_digest"], states[row["index"] + 1]["weather_field_digest"]}
        and row["sapling_mesh_digest"] not in {states[row["index"] - 1]["sapling_mesh_digest"], states[row["index"] + 1]["sapling_mesh_digest"]}
        for row in odd_rows
    )

    displacement = [float(row["sapling_max_neutral_displacement_m"]) for row in states]
    weather_motion = weather_sequence._motion_metrics(
        [{"time_s": row["time_s"], "scene": {"weather_lines": row["candidate_scene"]["weather_lines"]}} for row in states],
        weather_source["wind_xy"],
        float(weather_source["visual_speed_m_per_s"]),
    )
    symmetric = all(abs(displacement[i] - displacement[-1 - i]) <= TOL for i in range(len(displacement)))

    checks = {
        "exact_runtime_prerequisite_declared": EXPECTED_RUNTIME_HEAD == "f0c72b9dd4688bdb01ac40aa33f469afffd7ec0a",
        "exact_sync_prerequisite_pass": base.get("status") == "PASS_SYNCHRONIZED_VISUAL_ATMOSPHERE_SEQUENCE",
        "visual_only_relationship_preserved": base.get("shared_relationship") == RELATIONSHIP,
        "seventeen_sorted_samples_inside_authored_window": DENSE_TIMES_S == sorted(DENSE_TIMES_S) and len(states) == 17 and states[0]["time_s"] == 0.0 and states[-1]["time_s"] == 0.5,
        "all_eight_new_half_steps_are_materially_distinct": len(odd_rows) == 8 and odd_are_new,
        "all_nine_inherited_samples_reproduce_exactly": even_exact,
        "weather_source_motion_matches_visual_speed": weather_motion["maximum_adjacent_projected_displacement_error_m"] <= TOL,
        "weather_source_crosswind_drift_zero": weather_motion["maximum_adjacent_crosswind_drift_m"] <= TOL,
        "weather_particle_identity_preserved": not weather_motion["identity_errors"],
        "all_weather_fields_distinct": len({row["weather_field_digest"] for row in states}) == 17,
        "sapling_topology_preserved": all(len(row["candidate_scene"]["sapling"]["vertices_source_xyz_m"]) == 390 and len(row["candidate_scene"]["sapling"]["triangles"]) == 570 for row in states),
        "sapling_displacement_bounded": max(displacement) <= 0.18 + TOL,
        "sapling_dense_rise_monotonic": _monotonic(displacement[:9], True),
        "sapling_dense_fall_monotonic": _monotonic(displacement[8:], False),
        "sapling_dense_response_symmetric": symmetric,
        "exact_neutral_start_return": states[0]["candidate_scene"]["sapling"]["vertices_source_xyz_m"] == neutral_world_vertices,
        "exact_neutral_end_return": states[-1]["candidate_scene"]["sapling"]["vertices_source_xyz_m"] == neutral_world_vertices,
        "path_unblocked_all_dense_samples": all(row["sapling_path_unblocked"] for row in states),
        "spacing_preserved_all_dense_samples": all(not row["sapling_spacing_conflicts"] for row in states),
    }

    payload = {
        "schema": SCHEMA,
        "study_id": "environment-atmosphere-live-intermediates-001",
        "status": "PASS_DENSE_INTERMEDIATE_SOURCE_SEQUENCE" if all(checks.values()) else "FAIL",
        "receiving_head": os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD"),
        "stacked_on_runtime_head": EXPECTED_RUNTIME_HEAD,
        "stacked_on_sync_head": EXPECTED_SYNC_HEAD,
        "nature_response_head": EXPECTED_NATURE_HEAD,
        "weather_source_head": EXPECTED_WEATHER_HEAD,
        "shared_relationship": RELATIONSHIP,
        "sampling_schedule_s": DENSE_TIMES_S,
        "checks": checks,
        "measurements": {
            "sample_count": len(states),
            "new_half_step_count": len(odd_rows),
            "maximum_sapling_displacement_m": max(displacement),
            "peak_sample_index": max(range(len(displacement)), key=lambda i: displacement[i]),
            "maximum_adjacent_weather_projection_error_m": weather_motion["maximum_adjacent_projected_displacement_error_m"],
            "maximum_adjacent_weather_crosswind_drift_m": weather_motion["maximum_adjacent_crosswind_drift_m"],
        },
        "states": states,
        "truth_boundary": (
            "PASS proves direct source evaluation at eight new half-step times between the nine already-retained synchronized samples, exact reproduction of all inherited samples, bounded sapling response, exact neutral return, and source-owned Weather motion semantics. "
            "It does not prove mathematical continuity of arbitrary future effects, wall-clock frame pacing, renderer interpolation, target performance, physical wind, gameplay, final Art Direction, CANON, production readiness, or VFX mastery."
        ),
    }
    payload["sequence_digest"] = digest({
        "schema": payload["schema"],
        "schedule": payload["sampling_schedule_s"],
        "weather": [row["weather_field_digest"] for row in states],
        "sapling": [row["sapling_mesh_digest"] for row in states],
    })
    return payload


def verify_target_host(payload: dict[str, Any], receipt: dict[str, Any], image_root: Path, vfx_head: str) -> dict[str, Any]:
    samples = receipt.get("samples", [])
    checks: dict[str, bool] = {}
    checks["source_payload_pass"] = payload.get("status") == "PASS_DENSE_INTERMEDIATE_SOURCE_SEQUENCE"
    checks["target_host_observation_pass"] = receipt.get("state") == "PASS_DENSE_INTERMEDIATE_LIVE_OBSERVATION"
    checks["exact_sequence_digest"] = receipt.get("sequence_digest") == payload.get("sequence_digest")
    checks["exact_vfx_head_bound"] = vfx_head == payload.get("receiving_head")
    checks["seventeen_live_updates"] = len(samples) == 17
    checks["exact_schedule_preserved"] = [float(s.get("time_s", -1.0)) for s in samples] == [float(v) for v in DENSE_TIMES_S]

    weather_ids = {int(s["weather_update"][key]) for s in samples for key in ()} if samples else set()
    for prefix, field in (("weather", "weather_update"), ("sapling", "sapling_update")):
        for key in ("node_instance_id", "mesh_instance_id", "material_instance_id"):
            checks[f"stable_{prefix}_{key}"] = bool(samples) and len({int(s[field][key]) for s in samples}) == 1
    checks["source_counts_preserved"] = bool(samples) and all(
        int(s["weather_update"].get("streak_count", -1)) == 36
        and int(s["sapling_update"].get("source_vertex_count", -1)) == 390
        and int(s["sapling_update"].get("source_triangle_count", -1)) == 570
        and int(s["weather_update"].get("surface_count", -1)) == 1
        and int(s["sapling_update"].get("surface_count", -1)) == 1
        for s in samples
    )

    frame_rows = []
    all_present = True
    unique_by_context = {context: set() for context in CONTEXTS}
    counters_by_context = {context: set() for context in CONTEXTS}
    for sample in samples:
        index = int(sample["index"])
        for context in CONTEXTS:
            row = sample.get("contexts", {}).get(context, {})
            capture = row.get("capture", {})
            name = Path(str(capture.get("path", ""))).name
            path = image_root / name
            present = path.exists()
            all_present = all_present and present
            entry = {"index": index, "context": context, "present": present}
            if present:
                h = sha256(path)
                unique_by_context[context].add(h)
                entry["sha256"] = h
            runtime = row.get("runtime", {})
            counter_tuple = (
                int(runtime.get("draw_calls_in_frame", -1)),
                int(runtime.get("objects_in_frame", -1)),
                int(runtime.get("primitives_in_frame", -1)),
            )
            counters_by_context[context].add(counter_tuple)
            entry["runtime"] = {"draw_calls": counter_tuple[0], "objects": counter_tuple[1], "primitives": counter_tuple[2]}
            frame_rows.append(entry)

    checks["all_34_frames_present"] = all_present and len(frame_rows) == 34
    checks["all_dense_frames_visibly_distinct_by_hash"] = all(len(unique_by_context[c]) == 17 for c in CONTEXTS)
    checks["render_counters_stable_within_each_camera"] = all(len(counters_by_context[c]) == 1 for c in CONTEXTS)

    result = {
        "schema": TARGET_HOST_SCHEMA,
        "study_id": "environment-atmosphere-live-intermediates-target-host-001",
        "state": "PASS_DENSE_INTERMEDIATE_LIVE_UPDATE_PROOF_HOST" if all(checks.values()) else "FAIL",
        "vfx_head": vfx_head,
        "sequence_digest": payload.get("sequence_digest"),
        "proof_runtime": receipt.get("proof_runtime"),
        "checks": checks,
        "frames": frame_rows,
        "runtime_counter_sets": {k: [list(v) for v in sorted(values)] for k, values in counters_by_context.items()},
        "visual_observation_scope": "Seventeen directly evaluated synchronized Weather + sapling states were updated through stable proof-host resources in one process and rendered from both fixed cameras. Hash non-identity proves retained image change, not aesthetic quality.",
        "truth_boundary": (
            "PASS proves a same-process proof-host path can consume all 17 exact dense source-evaluated states through stable Weather and sapling resources and render every retained state. "
            "It does not prove wall-clock cadence, frame pacing, engine interpolation between these states, target-device performance, physical wind, gameplay, final visual quality, CANON, production readiness, or VFX mastery."
        ),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--manifest", default="examples/environment_real_slice_001.json")
    build.add_argument("--nature-root", required=True)
    build.add_argument("--weather-root", required=True)
    build.add_argument("--output", required=True, type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("--payload", required=True, type=Path)
    verify.add_argument("--receipt", required=True, type=Path)
    verify.add_argument("--image-root", required=True, type=Path)
    verify.add_argument("--vfx-head", required=True)
    verify.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.command == "build":
        payload = build_payload(args.manifest, args.nature_root, args.weather_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": payload["status"], "checks": payload["checks"], "measurements": payload["measurements"], "sequence_digest": payload["sequence_digest"]}, indent=2, sort_keys=True))
        return 0 if payload["status"].startswith("PASS_") else 1

    payload = json.loads(args.payload.read_text())
    receipt = json.loads(args.receipt.read_text())
    result = verify_target_host(payload, receipt, args.image_root, args.vfx_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": result["state"], "checks": result["checks"], "runtime_counter_sets": result["runtime_counter_sets"]}, indent=2, sort_keys=True))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
