from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from typing import Any

try:
    from . import environment_weather_width_temporal_exposure as legacy
except ImportError:
    import environment_weather_width_temporal_exposure as legacy

SCHEMA = "axm.environment-current-world-weather-width-temporal-exposure-normalized-target-host/v0.1"
STATUS = "PASS_OPACITY_NORMALIZED_TEMPORAL_EXPOSURE_VISUAL_CANDIDATE"
OBSERVATION_SCHEMA = "axm.environment-current-world-weather-width-temporal-exposure-normalized-observation/v0.1"
OBSERVATION_STATE = "OBSERVED_OPACITY_NORMALIZED_TEMPORAL_EXPOSURE_CANDIDATE"
POLICY = "TWO_TAP_TRANSMITTANCE_NORMALIZED_RECEIVING_ONLY_TEMPORAL_EXPOSURE"
MAPPING = "SOURCE_ALPHA_TO_TRANSMITTANCE_EXPONENT"
FORMULA_TOL = 1e-9
PHASE0_MEAN_ABS_RGB_MAX_LSB = 0.01
PHASE0_MAX_CHANNEL_DELTA_LSB = 4
PHASE0_CHANGED_FRACTION_MAX = 0.005
PHASE0_CHANGED_PIXEL_SIGNED_LUMA_MAX_LSB = 1.0


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalized_tap_alpha(source_alpha: float, weight: float) -> float:
    bounded = min(1.0, max(0.0, source_alpha))
    return 1.0 - math.pow(1.0 - bounded, weight)


def _legacy_compatible_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    translated = copy.deepcopy(receipt)
    translated["schema"] = legacy.OBSERVATION_SCHEMA
    if translated.get("state") == OBSERVATION_STATE:
        translated["state"] = legacy.OBSERVATION_STATE
    translated["presentation_policy"] = legacy.POLICY
    for block in translated.get("contexts", {}).values():
        block["presentation_policy"] = legacy.POLICY
    return translated


def _signed_luma_delta(raw_control: Path, raw_candidate: Path) -> dict[str, float | int]:
    control = raw_control.read_bytes()
    candidate = raw_candidate.read_bytes()
    if len(control) != legacy.RAW_BYTES or len(candidate) != legacy.RAW_BYTES:
        raise ValueError("unexpected RGBA8 frame byte count")
    changed = 0
    signed_luma_sum = 0.0
    darker = 0
    lighter = 0
    for offset in range(0, legacy.RAW_BYTES, 4):
        cr, cg, cb = control[offset], control[offset + 1], control[offset + 2]
        rr, rg, rb = candidate[offset], candidate[offset + 1], candidate[offset + 2]
        if (cr, cg, cb) == (rr, rg, rb):
            continue
        changed += 1
        delta = 0.2126 * (rr - cr) + 0.7152 * (rg - cg) + 0.0722 * (rb - cb)
        signed_luma_sum += delta
        if delta < -1e-12:
            darker += 1
        elif delta > 1e-12:
            lighter += 1
    return {
        "changed_pixels": changed,
        "mean_changed_pixel_signed_luma_lsb": (signed_luma_sum / changed) if changed else 0.0,
        "darker_changed_pixels": darker,
        "lighter_changed_pixels": lighter,
    }


def verify_opacity_normalized_exposure(
    payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path
) -> dict[str, Any]:
    root = Path(image_root)
    base_report = legacy.verify_temporal_exposure(payload, _legacy_compatible_receipt(receipt), root)
    contexts = receipt.get("contexts", {})

    all_context_policy = True
    all_rows_present = True
    all_formula_exact = True
    all_alpha_ceiling = True
    all_equal_source_rows_exact = True
    phase0_source_identity = True
    phase0_frame_equivalence = True
    total_opacity_rows = 0
    maximum_formula_error = 0.0
    maximum_equal_source_alpha_error = 0.0
    phase0_metrics: dict[str, Any] = {}

    for context in legacy.CONTEXTS:
        block = contexts.get(context, {})
        all_context_policy = all_context_policy and block.get("presentation_policy") == POLICY
        samples = block.get("samples", [])
        if len(samples) != len(legacy.REVIEW_PHASES_US):
            all_rows_present = False
            phase0_source_identity = False
            continue

        for sample_index, sample in enumerate(samples):
            exposure = sample.get("exposure_build", {})
            rows = exposure.get("opacity_rows", [])
            if exposure.get("opacity_mapping") != MAPPING or len(rows) != 36:
                all_rows_present = False
                continue
            total_opacity_rows += len(rows)
            if float(exposure.get("maximum_combined_alpha_over_source", 1.0)) > FORMULA_TOL:
                all_alpha_ceiling = False
            if float(exposure.get("maximum_equal_source_combined_alpha_error", 1.0)) > FORMULA_TOL:
                all_equal_source_rows_exact = False

            for row in rows:
                current_source = float(row.get("current_source_alpha", -1.0))
                lagged_source = float(row.get("lagged_source_alpha", -1.0))
                current_tap = float(row.get("current_tap_alpha", -1.0))
                lagged_tap = float(row.get("lagged_tap_alpha", -1.0))
                effective = float(row.get("effective_alpha", -1.0))
                ceiling = float(row.get("alpha_ceiling", -1.0))
                expected_current = _normalized_tap_alpha(current_source, 0.5)
                expected_lagged = _normalized_tap_alpha(lagged_source, 0.5)
                expected_effective = 1.0 - (1.0 - expected_current) * (1.0 - expected_lagged)
                row_error = max(
                    abs(current_tap - expected_current),
                    abs(lagged_tap - expected_lagged),
                    abs(effective - expected_effective),
                )
                maximum_formula_error = max(maximum_formula_error, row_error)
                if row_error > FORMULA_TOL:
                    all_formula_exact = False
                expected_ceiling = max(current_source, lagged_source)
                if abs(ceiling - expected_ceiling) > FORMULA_TOL or effective - expected_ceiling > FORMULA_TOL:
                    all_alpha_ceiling = False
                equal_source = abs(current_source - lagged_source) <= FORMULA_TOL
                if bool(row.get("equal_source", False)) != equal_source:
                    all_equal_source_rows_exact = False
                if equal_source:
                    equal_error = abs(effective - current_source)
                    maximum_equal_source_alpha_error = max(maximum_equal_source_alpha_error, equal_error)
                    if equal_error > FORMULA_TOL:
                        all_equal_source_rows_exact = False

            if sample_index == 0:
                current_bracket = sample.get("current_bracket", {})
                lagged_bracket = sample.get("lagged_bracket", {})
                phase0_source_identity = phase0_source_identity and (
                    int(sample.get("lag_us", -1)) == 0
                    and int(current_bracket.get("lower_index", -1)) == int(lagged_bracket.get("lower_index", -2))
                    and int(current_bracket.get("upper_index", -1)) == int(lagged_bracket.get("upper_index", -2))
                    and abs(float(current_bracket.get("alpha", -1.0)) - float(lagged_bracket.get("alpha", -2.0))) <= FORMULA_TOL
                    and all(bool(row.get("equal_source", False)) for row in rows)
                )
                control_frame = sample.get("control_frame", {})
                candidate_frame = sample.get("candidate_frame", {})
                if legacy._verify_frame(control_frame, root) and legacy._verify_frame(candidate_frame, root):
                    control_raw = root / str(control_frame["raw_path"])
                    candidate_raw = root / str(candidate_frame["raw_path"])
                    delta = legacy._frame_delta(control_raw, candidate_raw)
                    luma = _signed_luma_delta(control_raw, candidate_raw)
                    metrics = {**delta, **luma}
                    phase0_metrics[context] = metrics
                    equivalent = (
                        float(delta["mean_abs_rgb_lsb"]) <= PHASE0_MEAN_ABS_RGB_MAX_LSB
                        and int(delta["maximum_rgb_channel_delta_lsb"]) <= PHASE0_MAX_CHANNEL_DELTA_LSB
                        and float(delta["changed_fraction"]) <= PHASE0_CHANGED_FRACTION_MAX
                        and abs(float(luma["mean_changed_pixel_signed_luma_lsb"])) <= PHASE0_CHANGED_PIXEL_SIGNED_LUMA_MAX_LSB
                    )
                    phase0_frame_equivalence = phase0_frame_equivalence and equivalent
                else:
                    phase0_frame_equivalence = False

    checks = {
        "legacy_source_width_and_direct_ab_contract_still_passes": base_report.get("state") == legacy.STATUS and all(base_report.get("checks", {}).values()),
        "normalized_observation_schema_state_and_policy_exact": receipt.get("schema") == OBSERVATION_SCHEMA and receipt.get("state") == OBSERVATION_STATE and receipt.get("presentation_policy") == POLICY and all_context_policy,
        "all_36_per_sample_opacity_rows_are_retained": all_rows_present and total_opacity_rows == len(legacy.CONTEXTS) * len(legacy.REVIEW_PHASES_US) * 36,
        "per_streak_tap_alpha_matches_transmittance_exponent_formula": all_formula_exact and maximum_formula_error <= FORMULA_TOL,
        "combined_alpha_never_exceeds_larger_source_alpha": all_alpha_ceiling,
        "equal_source_taps_reconstruct_source_alpha": all_equal_source_rows_exact and maximum_equal_source_alpha_error <= FORMULA_TOL,
        "phase0_has_exact_zero_lag_source_identity": phase0_source_identity,
        "phase0_direct_frame_is_brightness_equivalent_within_bound": phase0_frame_equivalence and set(phase0_metrics) == set(legacy.CONTEXTS),
    }

    return {
        "schema": SCHEMA,
        "state": STATUS if all(checks.values()) else "FAIL",
        "receiving_head": payload.get("receiving_head"),
        "parent_variant_head": payload.get("parent_variant_head"),
        "presentation_policy": POLICY,
        "opacity_mapping": MAPPING,
        "configured_lag_us": legacy.EXPOSURE_LAG_US,
        "review_phases_us": list(legacy.REVIEW_PHASES_US),
        "checks": checks,
        "maximum_formula_error": maximum_formula_error,
        "maximum_equal_source_alpha_error": maximum_equal_source_alpha_error,
        "phase0_equivalence_bounds": {
            "mean_abs_rgb_lsb_max": PHASE0_MEAN_ABS_RGB_MAX_LSB,
            "maximum_rgb_channel_delta_lsb_max": PHASE0_MAX_CHANNEL_DELTA_LSB,
            "changed_fraction_max": PHASE0_CHANGED_FRACTION_MAX,
            "absolute_mean_changed_pixel_signed_luma_lsb_max": PHASE0_CHANGED_PIXEL_SIGNED_LUMA_MAX_LSB,
        },
        "phase0_metrics": phase0_metrics,
        "context_metrics": base_report.get("context_metrics", {}),
        "measured_width_count": base_report.get("measured_width_count", 0),
        "maximum_projected_width_residual_px": base_report.get("maximum_projected_width_residual_px", 0.0),
        "visual_tradeoff_for_review": (
            "The prior half-opacity candidate is preserved as historical evidence. This successor keeps the same two source-bound presentation taps and 15.625 ms lag but maps each source alpha through a weighted transmittance exponent. Coincident equal-source taps therefore reconstruct the single-tap source alpha instead of introducing static dimming. Nonzero-lag frames can still broaden or trail the Weather footprint; perceptual smoothness and final atmosphere prominence remain Art/Visual-QA decisions."
        ),
        "truth_boundary": (
            "PASS proves only that this exact Godot proof host can render the opacity-normalized, source-bound two-tap Weather candidate at deterministic review phases while preserving the legacy source-width/provenance contract and removing the prior zero-lag static-opacity attenuation within the declared direct-frame bounds. PASS does not prove authored 32 Hz delivery, human-perceived smoothness, final Art Direction or Visual QA acceptance, target-device performance, physical weather, gameplay/physics, arbitrary cameras, CANON, production readiness, or mastery."
        ),
    }


def exercise_normalization_negative_control(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path) -> dict[str, Any]:
    mutated = copy.deepcopy(receipt)
    for context in legacy.CONTEXTS:
        samples = mutated.get("contexts", {}).get(context, {}).get("samples", [])
        if samples:
            rows = samples[0].get("exposure_build", {}).get("opacity_rows", [])
            if rows:
                rows[0]["current_tap_alpha"] = float(rows[0].get("current_tap_alpha", 0.0)) + 0.1
                break
    return verify_opacity_normalized_exposure(payload, mutated, image_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = _load(args.payload)
    receipt = _load(args.receipt)
    report = verify_opacity_normalized_exposure(payload, receipt, args.image_root)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
