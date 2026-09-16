from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import environment_composition as composition

FAMILY_SCHEMA = "axm.environment-variation-family/v0.1"
RECEIPT_SCHEMA = "axm.environment-variation-receipt/v0.1"
SUMMARY_SCHEMA = "axm.environment-variation-sweep/v0.1"
FAILURE_CONTROL_SCHEMA = "axm.environment-variation-failure-control/v0.1"
VARIADIC_KINDS = {"nature-proxy", "object-proxy"}


def load_family(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != FAMILY_SCHEMA:
        raise ValueError("unsupported variation family schema")
    return data


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_family(base, family):
    if family.get("schema") != FAMILY_SCHEMA:
        raise ValueError("unsupported variation family schema")
    if family.get("base_study_id") != base.get("study_id"):
        raise ValueError("variation family base_study_id does not match source study")

    max_attempts = family.get("max_attempts")
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or not 1 <= max_attempts <= 256:
        raise ValueError("max_attempts must be an integer in [1, 256]")

    items = {item["asset_id"]: item for item in base["items"]}
    seen = set()
    rules = family.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("variation family must declare at least one rule")

    for rule in rules:
        asset_id = rule.get("asset_id")
        if asset_id in seen:
            raise ValueError(f"duplicate variation rule for {asset_id}")
        seen.add(asset_id)
        if asset_id not in items:
            raise ValueError(f"variation rule references unknown asset {asset_id}")
        if items[asset_id]["kind"] not in VARIADIC_KINDS:
            raise ValueError(f"variation rule cannot modify owned kind {items[asset_id]['kind']}")

        jitter = rule.get("xy_jitter_m")
        if not (
            isinstance(jitter, list)
            and len(jitter) == 2
            and all(_number(value) and 0.0 <= float(value) <= 4.0 for value in jitter)
        ):
            raise ValueError(f"{asset_id} xy_jitter_m must contain two values in [0, 4]")

        scale = rule.get("uniform_scale")
        if not (
            isinstance(scale, list)
            and len(scale) == 2
            and all(_number(value) for value in scale)
            and 0.0 < float(scale[0]) <= float(scale[1]) <= 2.0
        ):
            raise ValueError(f"{asset_id} uniform_scale must be a positive ordered range <= 2")

        rotation = rule.get("rotation_deg")
        if not (
            isinstance(rotation, list)
            and len(rotation) == 2
            and all(_number(value) for value in rotation)
            and -180.0 <= float(rotation[0]) <= float(rotation[1]) <= 180.0
        ):
            raise ValueError(f"{asset_id} rotation_deg must be an ordered range inside [-180, 180]")


def _apply_attempt(base, family, rng, seed, attempt_index):
    candidate = copy.deepcopy(base)
    base_items = {item["asset_id"]: item for item in base["items"]}
    candidate_items = {item["asset_id"]: item for item in candidate["items"]}

    for rule in family["rules"]:
        source = base_items[rule["asset_id"]]
        item = candidate_items[rule["asset_id"]]
        jitter_x, jitter_y = (float(value) for value in rule["xy_jitter_m"])
        scale_low, scale_high = (float(value) for value in rule["uniform_scale"])
        rotation_low, rotation_high = (float(value) for value in rule["rotation_deg"])

        scale = rng.uniform(scale_low, scale_high)
        item["position"][0] = round(float(source["position"][0]) + rng.uniform(-jitter_x, jitter_x), 6)
        item["position"][1] = round(float(source["position"][1]) + rng.uniform(-jitter_y, jitter_y), 6)
        item["size"] = [round(float(value) * scale, 6) for value in source["size"]]
        item["position"][2] = round(item["size"][2] / 2.0, 6)
        item["rotation_deg"] = round(rng.uniform(rotation_low, rotation_high), 6)

    candidate["study_id"] = f"{base['study_id']}-procedural-seed-{seed}"
    candidate["procedural_provenance"] = {
        "schema": RECEIPT_SCHEMA,
        "family_id": family["family_id"],
        "base_source_digest": composition.digest(base),
        "family_digest": composition.digest(family),
        "seed": seed,
        "attempt_index": attempt_index,
    }
    return candidate


def generate_variant(base, family, seed):
    validate_family(base, family)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer")

    rng = random.Random(seed)
    last_evidence = None
    for attempt_index in range(family["max_attempts"]):
        candidate = _apply_attempt(base, family, rng, seed, attempt_index)
        evidence = composition.evaluate(candidate)
        last_evidence = evidence
        if evidence["status"] == "PASS":
            return {
                "status": "PASS",
                "study": candidate,
                "study_digest": composition.digest(candidate),
                "evidence": evidence,
                "receipt": candidate["procedural_provenance"],
            }

    return {
        "status": "HOLD",
        "study": None,
        "study_digest": None,
        "evidence": last_evidence,
        "receipt": {
            "schema": RECEIPT_SCHEMA,
            "family_id": family["family_id"],
            "base_source_digest": composition.digest(base),
            "family_digest": composition.digest(family),
            "seed": seed,
            "attempts_exhausted": family["max_attempts"],
        },
    }


def generate_sweep(base, family, seeds):
    if not isinstance(seeds, list) or len(seeds) < 2 or len(set(seeds)) != len(seeds):
        raise ValueError("seed sweep must contain at least two unique seeds")
    variants = [generate_variant(base, family, seed) for seed in seeds]
    return {
        "schema": SUMMARY_SCHEMA,
        "family_id": family["family_id"],
        "base_source_digest": composition.digest(base),
        "family_digest": composition.digest(family),
        "status": "PASS" if all(item["status"] == "PASS" for item in variants) else "HOLD",
        "variant_count": len(variants),
        "unique_study_digest_count": len({item["study_digest"] for item in variants if item["study_digest"]}),
        "variants": [
            {
                "seed": item["receipt"]["seed"],
                "status": item["status"],
                "study_digest": item["study_digest"],
                "attempt_index": item["receipt"].get("attempt_index"),
            }
            for item in variants
        ],
        "truth_boundary": family["truth_boundary"],
    }, variants


def build_retained_failure_control(base, family):
    impossible = copy.deepcopy(family)
    impossible["max_attempts"] = 3
    for rule in impossible["rules"]:
        rule["xy_jitter_m"] = [0.0, 0.0]
        rule["uniform_scale"] = [2.0, 2.0]
        rule["rotation_deg"] = [0.0, 0.0]

    result = generate_variant(base, impossible, 11)
    control = {
        "schema": FAILURE_CONTROL_SCHEMA,
        "control_id": "impossible-double-scale-001",
        "purpose": "Retain the bounded rejection path used by the source-owned procedural family.",
        "expected_status": "HOLD",
        "observed_status": result["status"],
        "seed": 11,
        "attempts_exhausted": result["receipt"].get("attempts_exhausted"),
        "last_evidence_status": result["evidence"].get("status") if result["evidence"] else None,
        "base_source_digest": composition.digest(base),
        "failure_family_digest": composition.digest(impossible),
        "receipt": result["receipt"],
        "truth_boundary": "SYNTHETIC_NEGATIVE_CONTROL_ONLY_NOT_A_RETAINED_ASSET_VARIANT",
    }
    if not (
        control["observed_status"] == "HOLD"
        and control["attempts_exhausted"] == 3
        and control["last_evidence_status"] == "FAIL"
    ):
        raise RuntimeError("bounded failure control did not fail closed as required")
    return control


def build_family(base_source, family_source, output_dir):
    base = composition.load_study(base_source)
    family = load_family(family_source)
    seeds = family.get("evidence_seeds")
    if not isinstance(seeds, list):
        raise ValueError("family evidence_seeds must be a list")
    summary, variants = generate_sweep(base, family, seeds)
    failure_control = build_retained_failure_control(base, family)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for variant in variants:
        seed = variant["receipt"]["seed"]
        (output / f"seed-{seed}-receipt.json").write_text(
            json.dumps(variant, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if variant["study"] is not None:
            (output / f"seed-{seed}.obj").write_text(
                composition.build_obj(variant["study"]),
                encoding="utf-8",
            )
            (output / f"seed-{seed}-top.svg").write_text(
                composition.build_top_svg(variant["study"]),
                encoding="utf-8",
            )

    failure_path = output / "negative-control-impossible-double-scale.json"
    failure_path.write_text(
        json.dumps(failure_control, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary["retained_failure_control"] = {
        "control_id": failure_control["control_id"],
        "path": failure_path.name,
        "observed_status": failure_control["observed_status"],
        "attempts_exhausted": failure_control["attempts_exhausted"],
        "last_evidence_status": failure_control["last_evidence_status"],
        "failure_family_digest": failure_control["failure_family_digest"],
    }

    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    report = build_family(
        root / "examples/environment_baseline_001.json",
        root / "examples/environment_variation_family_001.json",
        root / "evidence/environment_variation_001",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    failure = report.get("retained_failure_control", {})
    ok = (
        report["status"] == "PASS"
        and report["unique_study_digest_count"] == report["variant_count"]
        and failure.get("observed_status") == "HOLD"
        and failure.get("last_evidence_status") == "FAIL"
    )
    raise SystemExit(0 if ok else 1)
