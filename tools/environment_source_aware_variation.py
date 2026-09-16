from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import environment_composition as composition
import environment_variation as variation

GATE_SCHEMA = "axm.environment-source-aware-variation-gate/v0.1"
RECEIPT_SCHEMA = "axm.environment-source-aware-variation-receipt/v0.1"
SUMMARY_SCHEMA = "axm.environment-source-aware-variation-sweep/v0.1"
FAILURE_CONTROL_SCHEMA = "axm.environment-source-aware-variation-failure-control/v0.1"
PASS_STATUS = "PASS_SOURCE_AWARE_VARIATION"
HOLD_STATUS = "HOLD_SOURCE_AWARE_VARIATION"


def load_gate(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != GATE_SCHEMA:
        raise ValueError("unsupported source-aware variation gate schema")
    return data


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_gate(base, family, gate):
    if gate.get("schema") != GATE_SCHEMA:
        raise ValueError("unsupported source-aware variation gate schema")

    target_id = gate.get("target_asset_id")
    items = {item["asset_id"]: item for item in base["items"]}
    if target_id not in items:
        raise ValueError("source-aware gate references unknown target asset")
    if target_id not in {rule["asset_id"] for rule in family["rules"]}:
        raise ValueError("source-aware gate target is not varied by this family")
    if items[target_id]["kind"] not in variation.VARIADIC_KINDS:
        raise ValueError("source-aware gate target must remain a variadic proxy kind")

    size = gate.get("required_source_size_m")
    if not (
        isinstance(size, list)
        and len(size) == 3
        and all(_number(value) and float(value) > 0.0 for value in size)
    ):
        raise ValueError("required_source_size_m must contain three positive numbers")

    tolerance = gate.get("tolerance_m")
    if not _number(tolerance) or not 0.0 <= float(tolerance) <= 1e-3:
        raise ValueError("tolerance_m must be inside [0, 1e-3]")

    source = gate.get("source_evidence")
    if not isinstance(source, dict):
        raise ValueError("source_evidence must be an object")
    for field in (
        "repository",
        "head",
        "study_id",
        "source_digest",
        "mesh_digest",
        "receiving_repository",
        "receiving_head",
        "retained_seed_study_digest",
    ):
        if not isinstance(source.get(field), str) or not source[field]:
            raise ValueError(f"source_evidence.{field} must be a non-empty string")
    if not isinstance(source.get("retained_artifact_id"), int) or isinstance(source["retained_artifact_id"], bool):
        raise ValueError("source_evidence.retained_artifact_id must be an integer")


def _inside(inner, outer, tolerance):
    return (
        inner[0] >= outer[0] - tolerance
        and inner[1] <= outer[1] + tolerance
        and inner[2] >= outer[2] - tolerance
        and inner[3] <= outer[3] + tolerance
    )


def evaluate_source_envelope(candidate, gate):
    target_id = gate["target_asset_id"]
    targets = [item for item in candidate["items"] if item.get("asset_id") == target_id]
    if len(targets) != 1:
        raise ValueError("source-aware target must exist exactly once")
    target = targets[0]

    tolerance = float(gate["tolerance_m"])
    source_size = [float(value) for value in gate["required_source_size_m"]]
    x, y, _ = [float(value) for value in target["position"]]
    source_footprint = (
        x - source_size[0] * 0.5,
        x + source_size[0] * 0.5,
        y - source_size[1] * 0.5,
        y + source_size[1] * 0.5,
    )
    reserved_footprint = composition._footprint(target)
    source_footprint_fits = _inside(source_footprint, reserved_footprint, tolerance)
    source_height_fits = source_size[2] <= float(target["size"][2]) + tolerance

    x_margin = (reserved_footprint[1] - reserved_footprint[0]) - source_size[0]
    y_margin = (reserved_footprint[3] - reserved_footprint[2]) - source_size[1]
    z_margin = float(target["size"][2]) - source_size[2]
    checks = {
        "source_footprint_inside_reserved_proxy_aabb": source_footprint_fits,
        "source_height_inside_reserved_proxy_height": source_height_fits,
        "source_not_scaled_by_gate": True,
        "target_identity_preserved": target.get("asset_id") == target_id,
    }
    return {
        "schema": "axm.environment-source-aware-envelope-evidence/v0.1",
        "gate_id": gate["gate_id"],
        "target_asset_id": target_id,
        "status": "PASS" if all(checks.values()) else "HOLD",
        "checks": checks,
        "reserved_proxy_position_m": copy.deepcopy(target["position"]),
        "reserved_proxy_size_m": copy.deepcopy(target["size"]),
        "reserved_proxy_rotation_deg": float(target.get("rotation_deg", 0.0)),
        "reserved_proxy_footprint_m": list(reserved_footprint),
        "required_source_size_m": source_size,
        "source_footprint_m": list(source_footprint),
        "remaining_aabb_margin_m": [x_margin, y_margin, z_margin],
        "placement_policy": gate["placement_policy"],
        "fit_policy": gate["fit_policy"],
        "source_evidence": copy.deepcopy(gate["source_evidence"]),
    }


def generate_source_aware_variant(base, family, gate, seed):
    variation.validate_family(base, family)
    validate_gate(base, family, gate)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer")

    rng = random.Random(seed)
    rejected = []
    last_composition = None
    last_source = None

    for attempt_index in range(family["max_attempts"]):
        candidate = variation._apply_attempt(base, family, rng, seed, attempt_index)
        composition_evidence = composition.evaluate(candidate)
        source_evidence = evaluate_source_envelope(candidate, gate)
        last_composition = composition_evidence
        last_source = source_evidence

        if composition_evidence["status"] == "PASS" and source_evidence["status"] == "PASS":
            return {
                "status": PASS_STATUS,
                "study": candidate,
                "study_digest": composition.digest(candidate),
                "composition_evidence": composition_evidence,
                "source_envelope_evidence": source_evidence,
                "receipt": {
                    "schema": RECEIPT_SCHEMA,
                    "family_id": family["family_id"],
                    "gate_id": gate["gate_id"],
                    "base_source_digest": composition.digest(base),
                    "family_digest": composition.digest(family),
                    "gate_digest": composition.digest(gate),
                    "seed": seed,
                    "attempt_index": attempt_index,
                    "rejected_attempt_count": len(rejected),
                    "failure_policy": gate["failure_policy"],
                    "source_evidence": copy.deepcopy(gate["source_evidence"]),
                },
                "rejected_attempts": rejected,
            }

        rejected.append(
            {
                "attempt_index": attempt_index,
                "study_digest": composition.digest(candidate),
                "composition_status": composition_evidence["status"],
                "source_envelope_status": source_evidence["status"],
                "source_envelope_checks": copy.deepcopy(source_evidence["checks"]),
                "reserved_proxy_size_m": copy.deepcopy(source_evidence["reserved_proxy_size_m"]),
                "remaining_aabb_margin_m": copy.deepcopy(source_evidence["remaining_aabb_margin_m"]),
            }
        )

    return {
        "status": HOLD_STATUS,
        "study": None,
        "study_digest": None,
        "composition_evidence": last_composition,
        "source_envelope_evidence": last_source,
        "receipt": {
            "schema": RECEIPT_SCHEMA,
            "family_id": family["family_id"],
            "gate_id": gate["gate_id"],
            "base_source_digest": composition.digest(base),
            "family_digest": composition.digest(family),
            "gate_digest": composition.digest(gate),
            "seed": seed,
            "attempts_exhausted": family["max_attempts"],
            "rejected_attempt_count": len(rejected),
            "failure_policy": gate["failure_policy"],
            "source_evidence": copy.deepcopy(gate["source_evidence"]),
        },
        "rejected_attempts": rejected,
    }


def generate_source_aware_sweep(base, family, gate, seeds):
    if not isinstance(seeds, list) or len(seeds) < 2 or len(set(seeds)) != len(seeds):
        raise ValueError("source-aware seed sweep must contain at least two unique seeds")
    variants = [generate_source_aware_variant(base, family, gate, seed) for seed in seeds]
    accepted = [item for item in variants if item["study_digest"]]
    return {
        "schema": SUMMARY_SCHEMA,
        "status": "PASS" if all(item["status"] == PASS_STATUS for item in variants) else "HOLD",
        "family_id": family["family_id"],
        "gate_id": gate["gate_id"],
        "base_source_digest": composition.digest(base),
        "family_digest": composition.digest(family),
        "gate_digest": composition.digest(gate),
        "variant_count": len(variants),
        "unique_study_digest_count": len({item["study_digest"] for item in accepted}),
        "total_rejected_attempts": sum(len(item["rejected_attempts"]) for item in variants),
        "variants": [
            {
                "seed": item["receipt"]["seed"],
                "status": item["status"],
                "study_digest": item["study_digest"],
                "attempt_index": item["receipt"].get("attempt_index"),
                "rejected_attempt_count": item["receipt"]["rejected_attempt_count"],
            }
            for item in variants
        ],
        "source_evidence": copy.deepcopy(gate["source_evidence"]),
        "truth_boundary": gate["truth_boundary"],
    }, variants


def build_retained_source_failure_control(base, family, gate):
    impossible_family = copy.deepcopy(family)
    impossible_family["max_attempts"] = 3
    impossible_gate = copy.deepcopy(gate)
    impossible_gate["gate_id"] = "synthetic-impossible-source-envelope-001"
    impossible_gate["required_source_size_m"] = [100.0, 100.0, 100.0]
    result = generate_source_aware_variant(base, impossible_family, impossible_gate, 29)
    control = {
        "schema": FAILURE_CONTROL_SCHEMA,
        "control_id": "synthetic-impossible-source-envelope-001",
        "purpose": "Retain the source-aware fail-closed path without widening the existing variation family.",
        "expected_status": HOLD_STATUS,
        "observed_status": result["status"],
        "seed": 29,
        "attempts_exhausted": result["receipt"].get("attempts_exhausted"),
        "rejected_attempt_count": result["receipt"].get("rejected_attempt_count"),
        "last_source_envelope_status": result["source_envelope_evidence"].get("status") if result["source_envelope_evidence"] else None,
        "last_composition_status": result["composition_evidence"].get("status") if result["composition_evidence"] else None,
        "failure_policy": gate["failure_policy"],
        "truth_boundary": "SYNTHETIC_NEGATIVE_CONTROL_ONLY_NOT_A_RETAINED_ASSET_VARIANT_OR_SOURCE_REQUIREMENT",
    }
    if not (
        control["observed_status"] == HOLD_STATUS
        and control["attempts_exhausted"] == 3
        and control["rejected_attempt_count"] == 3
        and control["last_source_envelope_status"] == "HOLD"
    ):
        raise RuntimeError("source-aware failure control did not fail closed as required")
    return control


def build_source_aware_family(base_source, family_source, gate_source, output_dir):
    base = composition.load_study(base_source)
    family = variation.load_family(family_source)
    gate = load_gate(gate_source)
    seeds = family.get("evidence_seeds")
    if not isinstance(seeds, list):
        raise ValueError("family evidence_seeds must be a list")

    summary, variants = generate_source_aware_sweep(base, family, gate, seeds)
    failure_control = build_retained_source_failure_control(base, family, gate)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    for item in variants:
        seed = item["receipt"]["seed"]
        (output / f"seed-{seed}-source-aware-receipt.json").write_text(
            json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if item["study"] is not None:
            (output / f"seed-{seed}.obj").write_text(composition.build_obj(item["study"]), encoding="utf-8")
            (output / f"seed-{seed}-top.svg").write_text(composition.build_top_svg(item["study"]), encoding="utf-8")

    failure_path = output / "negative-control-impossible-source-envelope.json"
    failure_path.write_text(json.dumps(failure_control, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary["retained_failure_control"] = {
        "path": failure_path.name,
        "observed_status": failure_control["observed_status"],
        "attempts_exhausted": failure_control["attempts_exhausted"],
        "rejected_attempt_count": failure_control["rejected_attempt_count"],
        "last_source_envelope_status": failure_control["last_source_envelope_status"],
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    report = build_source_aware_family(
        root / "examples/environment_baseline_001.json",
        root / "examples/environment_variation_family_001.json",
        root / "examples/environment_west_sapling_source_gate_001.json",
        root / "evidence/environment_source_aware_variation_001",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    control = report.get("retained_failure_control", {})
    ok = (
        report["status"] == "PASS"
        and report["variant_count"] == 3
        and report["unique_study_digest_count"] == 3
        and control.get("observed_status") == HOLD_STATUS
        and control.get("last_source_envelope_status") == "HOLD"
    )
    raise SystemExit(0 if ok else 1)
