from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PLAN_SCHEMA = "axm.environment-object-motion-receiver-plan/v0.1"
RESULT = "PASS_OBJECT_ANIMATION_OWNER_SAMPLES_ADAPTED_TO_CURRENT_WORLD_RIGID_RECEIVER"


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def write(path: str | Path, value: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_to_receiver(v: list[Any]) -> list[float]:
    if len(v) != 3:
        raise AssertionError("source vec3 arity drift")
    return [float(v[0]), float(v[2]), float(v[1])]


def validate(
    contract: dict[str, Any],
    cmap: dict[str, Any],
    seq: dict[str, Any],
    rig: dict[str, Any],
    target: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assert contract["schema"] == "axm.technical-art-object-motion-current-world-bridge/v0.1"
    assert cmap["schema"] == "axm.environment-object-rigid-component-map/v0.1"
    assert cmap["result"] == "PASS_EXACT_OBJECT_TA_RIGID_COMPONENT_MAP_FOR_CURRENT_WORLD_RECEIVER"
    assert cmap["object_source_sha256"] == contract["object_source_sha256"]
    assert cmap["technical_art_head"] == contract["object_technical_art_head"]
    assert int(cmap["triangles"]) == 812
    assert seq["schema"] == "axm.object-lid-latch-motion-evidence/v0.1"
    assert seq["result"] == "PASS_ORDERED_LATCH_RELEASE_LID_CLIP_REENGAGE_SEQUENCE"
    assert seq["exact_receiving_head"] == contract["animation_head"]
    assert seq["host_source_sha256"] == contract["object_source_sha256"]
    assert seq["sequence_id"] == contract["sequence_id"]
    assert seq["sequence_digest"] == contract["sequence_digest"]
    assert int(seq["sample_rate_hz"]) == 40 and float(seq["duration_s"]) == 2.5
    assert int(seq["endpoint_inclusive_sample_count"]) == 101 and len(seq["samples"]) == 101
    assert rig["schema"] == "axm.object-front-latch-articulation-evidence/v0.1"
    assert rig["result"] == "PASS_BOUNDED_FRONT_LATCH_LEVER_ARTICULATION"
    assert rig["host_source_sha256"] == contract["object_source_sha256"]
    assert len(rig["station_results"]) == 2

    components = {row["name"]: row for row in cmap["components"]}
    for name in ("lid_shell", "latch_0_keeper", "latch_1_keeper", "latch_0_lever", "latch_1_lever"):
        assert name in components, f"missing component {name}"
    assert components["latch_0_keeper"]["parent"] == "lid_shell"
    assert components["latch_1_keeper"]["parent"] == "lid_shell"
    assert components["latch_0_lever"]["parent"] is None
    assert components["latch_1_lever"]["parent"] is None

    sample0 = seq["samples"][0]
    station0 = {row["station_id"]: row for row in sample0["stations"]}
    rig_by = {row["station_id"]: row for row in rig["station_results"]}
    assert set(station0) == set(rig_by)
    station_plan = []
    for sid in sorted(station0):
        sample_station = station0[sid]
        rig_station = rig_by[sid]
        assert sample_station["lever_component"] in ("latch_0_lever", "latch_1_lever")
        station_plan.append(
            {
                "station_id": sid,
                "lever_component": sample_station["lever_component"],
                "keeper_component": sample_station["keeper_component"],
                "pivot_receiver_xyz_m": source_to_receiver(rig_station["pivot_m"]),
            }
        )

    samples = []
    for index, row in enumerate(seq["samples"]):
        assert int(row["index"]) == index
        assert abs(float(row["time_s"]) - index / 40.0) < 1e-9
        stations = {station["station_id"]: station for station in row["stations"]}
        assert set(stations) == set(station0)
        for sid in stations:
            assert stations[sid]["lever_component"] == station0[sid]["lever_component"]
            assert stations[sid]["keeper_component"] == station0[sid]["keeper_component"]
        samples.append(
            {
                "index": index,
                "time_s": float(row["time_s"]),
                "lid_target_rotation_deg_x": -float(row["lid_mathematical_rotation_deg"]),
                "latch_target_rotation_deg_x": -float(row["latch_lever_angle_deg"]),
            }
        )

    for index, lid, latch in ((0, 0.0, 0.0), (10, 0.0, -50.0), (50, 100.0, -50.0), (100, 0.0, 0.0)):
        row = samples[index]
        assert abs(row["lid_target_rotation_deg_x"] - lid) < 1e-9
        assert abs(row["latch_target_rotation_deg_x"] - latch) < 1e-9

    owner_motion_invariants: dict[str, float] = {}
    if target is not None:
        assert target["schema"] == "axm.object-animationplayer-target-proof/v0.1"
        assert target["animation_sequence_head"] == contract["animation_head"]
        assert target["coordinate_conversion"] == contract["coordinate_conversion"]
        assert target["animationplayer_track_count"] == 3
        assert target["animationplayer_key_counts"] == [101, 101, 101]
        assert int(target["closed_to_endpoint_changed_pixels"]) == 0
        assert float(target["neutral_pivot_wrapper_max_drift_m"]) == 0.0
        assert target["truth_boundary"]["discrete_exact_authored_sample_seek_equivalence_observed"] is True
        owner_motion_invariants = {
            "neutral_pivot_wrapper_max_drift_m": float(target["neutral_pivot_wrapper_max_drift_m"]),
            "release_keeper_drift_m": float(target["release_keeper_drift_m"]),
            "release_min_lever_move_m": float(target["release_min_lever_move_m"]),
            "peak_min_keeper_move_m": float(target["peak_min_keeper_move_m"]),
            "endpoint_keeper_drift_m": float(target["endpoint_keeper_drift_m"]),
            "endpoint_lever_drift_m": float(target["endpoint_lever_drift_m"]),
        }
        assert owner_motion_invariants["release_min_lever_move_m"] > 0.001
        assert owner_motion_invariants["peak_min_keeper_move_m"] > 0.03

    return {
        "schema": PLAN_SCHEMA,
        "result": RESULT,
        "object_source_sha256": contract["object_source_sha256"],
        "object_technical_art_head": contract["object_technical_art_head"],
        "animation_head": contract["animation_head"],
        "sequence_id": contract["sequence_id"],
        "sequence_digest": contract["sequence_digest"],
        "sample_rate_hz": 40,
        "duration_s": 2.5,
        "sample_count": 101,
        "coordinate_conversion": contract["coordinate_conversion"],
        "lid_component": "lid_shell",
        "stations": station_plan,
        "samples": samples,
        "owner_target_motion_invariants": owner_motion_invariants,
        "environment_adoption": False,
        "vfx_adoption": False,
        "runtime_acceptance": False,
        "art_qa_acceptance": False,
        "canon": False,
        "truth_boundary": "Receiver-only transform adapter from exact Object Animation evidence onto the already-proven current-world rigid component boundary. Owner-target center-displacement invariants are retained because a rigid Environment placement must preserve those distances. It does not author timing/easing, infer mechanics, adopt VFX, claim Runtime/device performance, final visual acceptance, CANON or production readiness.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd", required=True)
    prepare = subs.add_parser("prepare")
    for name in ("contract", "component-map", "sequence", "rig", "target-receipt", "output", "receipt"):
        prepare.add_argument("--" + name, required=True)
    validate_plan = subs.add_parser("validate-plan")
    validate_plan.add_argument("--contract", required=True)
    validate_plan.add_argument("--plan", required=True)
    args = parser.parse_args()

    if args.cmd == "prepare":
        contract = load(args.contract)
        component_map = load(args.component_map)
        sequence = load(args.sequence)
        rig = load(args.rig)
        target = load(args.target_receipt)
        plan = validate(contract, component_map, sequence, rig, target)
        write(args.output, plan)
        receipt = {key: plan[key] for key in (
            "schema", "result", "object_source_sha256", "object_technical_art_head", "animation_head",
            "sequence_id", "sequence_digest", "sample_count", "coordinate_conversion", "owner_target_motion_invariants",
            "environment_adoption", "vfx_adoption", "runtime_acceptance", "art_qa_acceptance", "canon", "truth_boundary",
        )}
        receipt["component_map_sha256"] = sha256(args.component_map)
        receipt["sequence_evidence_sha256"] = sha256(args.sequence)
        receipt["rig_receipt_sha256"] = sha256(args.rig)
        receipt["target_receipt_sha256"] = sha256(args.target_receipt)
        receipt["plan_sha256"] = hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        write(args.receipt, receipt)
        print(receipt["result"])
        return 0

    contract = load(args.contract)
    plan = load(args.plan)
    assert plan["schema"] == PLAN_SCHEMA and plan["result"] == RESULT
    assert plan["object_source_sha256"] == contract["object_source_sha256"]
    assert plan["animation_head"] == contract["animation_head"]
    assert plan["sequence_digest"] == contract["sequence_digest"]
    assert plan["sample_count"] == 101 and len(plan["samples"]) == 101 and len(plan["stations"]) == 2
    invariants = plan["owner_target_motion_invariants"]
    assert invariants["release_min_lever_move_m"] > 0.001
    assert invariants["peak_min_keeper_move_m"] > 0.03
    print("PASS_OBJECT_MOTION_RECEIVER_PLAN_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
