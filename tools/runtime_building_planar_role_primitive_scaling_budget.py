#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

SCHEMA = "axm.runtime-building-planar-role-primitive-scaling/v0.1"
REPORT_SCHEMA = "axm.runtime-building-planar-role-primitive-scaling-budget/v0.1"
COUNTS = [1, 16, 64, 256]
TRIALS = 41


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def percentile_nearest(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return float(ordered[index])


def counter_delta(candidate: dict, control: dict) -> dict[str, int]:
    fields = (
        "draw_calls_in_frame",
        "objects_in_frame",
        "primitives_in_frame",
        "buffer_mem_bytes",
        "texture_mem_bytes",
    )
    return {field: int(candidate[field]) - int(control[field]) for field in fields}


def verify(raw: dict, exact_head: str) -> dict:
    if raw.get("schema") != SCHEMA or raw.get("state") != "PASS_RAW_PRIMITIVE_SCALING_MEASUREMENT":
        raise ValueError("raw primitive-scaling measurement is not the expected PASS")
    if raw.get("instance_counts") != COUNTS:
        raise ValueError(f"instance-count schedule drift: {raw.get('instance_counts')}")
    if int(raw.get("paired_trials_per_count", 0)) != TRIALS:
        raise ValueError("paired-trial count drift")
    if int(raw.get("frames_per_sample", 0)) != 3:
        raise ValueError("frames-per-sample drift")

    active = raw.get("active_identity", {})
    candidate = raw.get("candidate_identity", {})
    if active.get("surface_count") != 5 or active.get("vertices") != 828 or active.get("indices") != 0 or active.get("primitives") != 276:
        raise ValueError(f"active segmented identity drift: {active}")
    if candidate.get("surface_count") != 5 or candidate.get("vertices") != 312 or candidate.get("indices") != 1008 or candidate.get("primitives") != 336:
        raise ValueError(f"indexed planar-role identity drift: {candidate}")
    logical_extra_triangles = int(candidate["primitives"]) - int(active["primitives"])
    if logical_extra_triangles != 60:
        raise ValueError(f"logical residual primitive identity drift: {logical_extra_triangles}")

    rows = raw.get("results", [])
    if [int(row.get("instance_count", -1)) for row in rows] != COUNTS:
        raise ValueError("result instance-count ordering drift")

    summaries = []
    primitive_delta_per_instance = []
    for row in rows:
        count = int(row["instance_count"])
        control = [float(v) for v in row.get("control_frame_ms", [])]
        candidate_ms = [float(v) for v in row.get("candidate_frame_ms", [])]
        paired = [float(v) for v in row.get("paired_delta_candidate_minus_control_ms", [])]
        if len(control) != TRIALS or len(candidate_ms) != TRIALS or len(paired) != TRIALS:
            raise ValueError(f"timing sample-count drift at {count}")
        recomputed = [d - c for c, d in zip(control, candidate_ms)]
        if any(abs(a - b) > 1e-9 for a, b in zip(paired, recomputed)):
            raise ValueError(f"paired timing receipt drift at {count}")
        if any(v <= 0 for v in control + candidate_ms):
            raise ValueError(f"non-positive frame timing at {count}")

        delta = counter_delta(row["candidate_runtime"], row["control_runtime"])
        if delta["draw_calls_in_frame"] != 0:
            raise ValueError(f"draw-call shape changed at {count}: {delta}")
        if delta["objects_in_frame"] != 0:
            raise ValueError(f"object count changed at {count}: {delta}")
        if delta["texture_mem_bytes"] != 0:
            raise ValueError(f"texture memory changed at {count}: {delta}")
        if delta["primitives_in_frame"] <= 0:
            raise ValueError(f"candidate did not expose positive primitive residual at {count}: {delta}")
        if delta["primitives_in_frame"] % count != 0:
            raise ValueError(f"primitive residual does not scale cleanly with instance count {count}: {delta}")
        primitive_delta_per_instance.append(delta["primitives_in_frame"] // count)

        c_med = float(statistics.median(control))
        d_med = float(statistics.median(candidate_ms))
        paired_med = float(statistics.median(paired))
        slower_pairs = sum(1 for value in paired if value > 0)
        faster_pairs = sum(1 for value in paired if value < 0)
        equal_pairs = TRIALS - slower_pairs - faster_pairs
        summaries.append(
            {
                "instance_count": count,
                "control_median_ms": c_med,
                "candidate_median_ms": d_med,
                "median_delta_candidate_minus_control_ms": d_med - c_med,
                "paired_delta_median_ms": paired_med,
                "control_p90_ms": percentile_nearest(control, 0.90),
                "candidate_p90_ms": percentile_nearest(candidate_ms, 0.90),
                "candidate_slower_pairs": slower_pairs,
                "candidate_faster_pairs": faster_pairs,
                "equal_pairs": equal_pairs,
                "renderer_delta_candidate_minus_control": delta,
            }
        )

    if len(set(primitive_delta_per_instance)) != 1:
        raise ValueError(f"renderer primitive residual per instance is not stable: {primitive_delta_per_instance}")
    observed_rs_primitive_delta_per_instance = primitive_delta_per_instance[0]

    high = summaries[-1]
    high_stress_cost_detected = (
        high["paired_delta_median_ms"] > 0.0
        and high["candidate_slower_pairs"] >= 25
        and high["median_delta_candidate_minus_control_ms"] > 0.0
    )
    if high_stress_cost_detected:
        state = "PASS_BUILDING_PLANAR_ROLE_RESIDUAL_PRIMITIVE_STRESS_COST_CHARACTERIZED__HOLD_TARGET_DEVICE"
        decision = "RESIDUAL_PRIMITIVE_COST_BECOMES_MEASURABLE_UNDER_256X_IDENTICAL_STRESS__KEEP_TARGET_DEVICE_GATE_AND_CONSIDER_DISTANCE_LOD_OR_SOURCE_TOPOLOGY_REDUCTION"
    else:
        state = "PASS_BUILDING_PLANAR_ROLE_RESIDUAL_PRIMITIVE_COST_BELOW_PROOF_HOST_STRESS_DETECTION__HOLD_TARGET_DEVICE"
        decision = "NO_ROBUST_256X_STRESS_COST_DETECTED_ON_PROOF_HOST__DO_NOT_INVENT_A_TOPOLOGY_REWRITE__KEEP_TARGET_DEVICE_GATE"

    high_extra_primitives = int(high["renderer_delta_candidate_minus_control"]["primitives_in_frame"])
    high_delta_ms = float(high["paired_delta_median_ms"])
    normalized = high_delta_ms / high_extra_primitives if high_extra_primitives else 0.0

    return {
        "schema": REPORT_SCHEMA,
        "state": state,
        "decision": decision,
        "exact_runtime_head": exact_head,
        "active_segmented_environment_head": "7713cbe5863c3bc38dabb6236eb4b393401224b6",
        "indexed_planar_environment_head": "038925282240441c475651bdc3737d1749c31d06",
        "active_building": active,
        "indexed_planar_building": candidate,
        "logical_extra_triangles_per_building": logical_extra_triangles,
        "observed_renderingserver_extra_primitives_per_instance": observed_rs_primitive_delta_per_instance,
        "stress_schedule": {
            "instance_counts": COUNTS,
            "paired_trials_per_count": TRIALS,
            "frames_per_sample": int(raw["frames_per_sample"]),
            "measurement_mode": raw.get("measurement_mode"),
        },
        "results": summaries,
        "high_stress_256x": {
            "candidate_slower_pairs": int(high["candidate_slower_pairs"]),
            "candidate_faster_pairs": int(high["candidate_faster_pairs"]),
            "paired_delta_median_ms": high_delta_ms,
            "renderer_extra_primitives": high_extra_primitives,
            "empirical_paired_delta_ms_per_extra_renderingserver_primitive": normalized,
            "robust_cost_detected_by_declared_gate": high_stress_cost_detected,
        },
        "visual_tradeoff": raw.get("visual_tradeoff"),
        "art_director_review_note": "Runtime introduces no new visual representation in this pass. The stress pair is the exact active segmented rollback versus the already independently Art-reviewed indexed planar-role receiver. Any future LOD/topology change remains a separate Art/QA review lane.",
        "truth_boundary": (
            "This is a same-process Godot 4.7.2 GL Compatibility proof-host microbenchmark, not target-device acceptance. "
            "Identical MultiMesh transforms amplify the exact 60-logical-triangle per-Building residual so a small steady render cost can be detected without multiplying draw calls. "
            "The result does not prove current-world FPS/GPU time, mobile/desktop target cost, VRAM/thermal/battery behavior, arbitrary density, Art preference, Environment adoption, CANON or production readiness."
        ),
        "four_root_gate": {
            "truth": "Report measured paired timings and exact renderer-counter scaling; do not promote a proof-host stress slope into target-device FPS claims.",
            "agency_non_domination": "Runtime characterizes cost only; Art/QA retain visual authority and Environment retains receiver adoption authority.",
            "continuity": "The active segmented receiver and indexed planar-role review receiver remain separately identified and rollbackable.",
            "wisdom_before_speed": "Only recommend a new LOD/topology lane if measured stress cost justifies it; otherwise keep the target-device gate instead of rewriting accepted art speculatively.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--exact-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(load(args.raw), args.exact_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["state"])
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
