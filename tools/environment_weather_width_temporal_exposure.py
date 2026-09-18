from __future__ import annotations

import argparse
import copy
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

try:
    from . import environment_weather_width_current_world as width
except ImportError:
    import environment_weather_width_current_world as width

SCHEMA = "axm.environment-current-world-weather-width-temporal-exposure-target-host/v0.1"
STATUS = "PASS_BOUNDED_TEMPORAL_EXPOSURE_VISUAL_CANDIDATE"
OBSERVATION_SCHEMA = "axm.environment-current-world-weather-width-temporal-exposure-observation/v0.1"
OBSERVATION_STATE = "OBSERVED_BOUNDED_TEMPORAL_EXPOSURE_CANDIDATE"
CONTEXT_STATE = "OBSERVED_BOUNDED_TEMPORAL_EXPOSURE_CONTEXT"
CONTEXTS = ("path_eye", "elevated_oblique")
POLICY = "TWO_TAP_HALF_OPACITY_RECEIVING_ONLY_TEMPORAL_EXPOSURE"
REVIEW_PHASES_US = (0, 62500, 125000, 187500, 250000, 312500, 375000, 437500, 500000)
EXPOSURE_LAG_US = 15625
WIDTH = 1100
HEIGHT = 720
RAW_BYTES = WIDTH * HEIGHT * 4
TARGET_REAR_ASSET_ID = "source:nature:east-rear-tree-neutral-001"


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_bracket(block: dict[str, Any], phase_us: int, expected: dict[int, dict[str, Any]], include_sapling: bool) -> bool:
    lower_index = int(block.get("lower_index", -1))
    upper_index = int(block.get("upper_index", -1))
    alpha = float(block.get("alpha", -1.0))
    if lower_index not in expected or upper_index not in expected or not (0.0 <= alpha <= 1.0):
        return False
    if phase_us >= 500000:
        if lower_index != 16 or upper_index != 16 or abs(alpha) > 1e-9:
            return False
    else:
        expected_lower = phase_us // 31250
        expected_alpha = (phase_us - expected_lower * 31250) / 31250.0
        if lower_index != expected_lower or upper_index != lower_index + 1 or abs(alpha - expected_alpha) > 1e-9:
            return False
    lower = expected[lower_index]
    upper = expected[upper_index]
    digest_checks = (
        str(block.get("lower_weather_field_digest", "")) == str(lower.get("weather_field_digest", ""))
        and str(block.get("upper_weather_field_digest", "")) == str(upper.get("weather_field_digest", ""))
        and str(block.get("lower_weather_width_profile_digest", "")) == str(lower.get("weather_width_profile_digest", ""))
        and str(block.get("upper_weather_width_profile_digest", "")) == str(upper.get("weather_width_profile_digest", ""))
    )
    if include_sapling:
        digest_checks = digest_checks and (
            str(block.get("lower_sapling_mesh_digest", "")) == str(lower.get("sapling_mesh_digest", ""))
            and str(block.get("upper_sapling_mesh_digest", "")) == str(upper.get("sapling_mesh_digest", ""))
        )
    return digest_checks


def _verify_frame(frame: dict[str, Any], root: Path) -> bool:
    png = root / str(frame.get("png_path", ""))
    raw = root / str(frame.get("raw_path", ""))
    return (
        frame.get("state") == "PASS_CAPTURED_EXPOSURE_FRAME"
        and int(frame.get("width", 0)) == WIDTH
        and int(frame.get("height", 0)) == HEIGHT
        and frame.get("format") == "RGBA8"
        and png.exists()
        and raw.exists()
        and raw.stat().st_size == RAW_BYTES
        and _sha256(png) == str(frame.get("png_sha256", ""))
        and _sha256(raw) == str(frame.get("raw_sha256", ""))
    )


def _frame_delta(raw_a: Path, raw_b: Path) -> dict[str, float | int]:
    a = raw_a.read_bytes()
    b = raw_b.read_bytes()
    if len(a) != RAW_BYTES or len(b) != RAW_BYTES:
        raise ValueError("unexpected RGBA8 frame byte count")
    changed = 0
    abs_rgb = 0
    max_channel = 0
    for offset in range(0, RAW_BYTES, 4):
        dr = abs(a[offset] - b[offset])
        dg = abs(a[offset + 1] - b[offset + 1])
        db = abs(a[offset + 2] - b[offset + 2])
        if dr or dg or db:
            changed += 1
        abs_rgb += dr + dg + db
        max_channel = max(max_channel, dr, dg, db)
    return {
        "changed_pixels": changed,
        "changed_fraction": changed / float(WIDTH * HEIGHT),
        "mean_abs_rgb_lsb": abs_rgb / float(WIDTH * HEIGHT * 3),
        "maximum_rgb_channel_delta_lsb": max_channel,
    }


def verify_temporal_exposure(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path) -> dict[str, Any]:
    root = Path(image_root)
    states = payload.get("states", [])
    expected = {int(row.get("index", -1)): row for row in states}
    contexts = receipt.get("contexts", {})

    all_contexts = True
    all_brackets = True
    all_opacity_budget = True
    all_widths = True
    all_frames = True
    all_resources = True
    all_visual_deltas = True
    maximum_width_residual_px = 0.0
    measured_width_count = 0
    context_metrics: dict[str, Any] = {}

    for context in CONTEXTS:
        block = contexts.get(context, {})
        samples = block.get("samples", [])
        context_ok = (
            block.get("state") == CONTEXT_STATE
            and block.get("presentation_policy") == POLICY
            and tuple(int(v) for v in block.get("review_phases_us", [])) == REVIEW_PHASES_US
            and int(block.get("configured_lag_us", -1)) == EXPOSURE_LAG_US
            and len(samples) == len(REVIEW_PHASES_US)
        )
        all_contexts = all_contexts and context_ok
        weather_ids: set[tuple[int, int, int]] = set()
        sapling_ids: set[tuple[int, int, int]] = set()
        pair_deltas: list[dict[str, float | int]] = []
        control_transition: list[float] = []
        candidate_transition: list[float] = []
        control_raw_paths: list[Path] = []
        candidate_raw_paths: list[Path] = []

        for sample_index, sample in enumerate(samples):
            phase_us = int(sample.get("phase_us", -1))
            lagged_phase_us = int(sample.get("lagged_phase_us", -1))
            expected_phase = REVIEW_PHASES_US[sample_index]
            expected_lagged = max(0, expected_phase - EXPOSURE_LAG_US)
            if phase_us != expected_phase or lagged_phase_us != expected_lagged:
                all_brackets = False
            all_brackets = all_brackets and _verify_bracket(sample.get("current_bracket", {}), phase_us, expected, True)
            all_brackets = all_brackets and _verify_bracket(sample.get("lagged_bracket", {}), lagged_phase_us, expected, False)

            exposure = sample.get("exposure_build", {})
            opacity_ok = (
                exposure.get("state") == "PASS_BOUNDED_TEMPORAL_EXPOSURE_LINES"
                and int(exposure.get("source_streak_count", 0)) == 36
                and int(exposure.get("presentation_tap_count", 0)) == 72
                and abs(float(exposure.get("current_weight", -1.0)) - 0.5) <= 1e-9
                and abs(float(exposure.get("lagged_weight", -1.0)) - 0.5) <= 1e-9
                and abs(float(exposure.get("weight_sum", -1.0)) - 1.0) <= 1e-9
                and float(exposure.get("maximum_combined_alpha_over_source", 1.0)) <= 1e-9
                and float(exposure.get("maximum_theoretical_combined_alpha", 2.0)) <= 1.0
            )
            all_opacity_budget = all_opacity_budget and opacity_ok

            control_weather = sample.get("control_weather_update", {})
            exposure_weather = sample.get("exposure_weather_update", {})
            control_residual = float(control_weather.get("maximum_projected_width_residual_px", 999.0))
            exposure_residual = float(exposure_weather.get("maximum_projected_width_residual_px", 999.0))
            maximum_width_residual_px = max(maximum_width_residual_px, control_residual, exposure_residual)
            measured_width_count += int(control_weather.get("measured_width_count", 0)) + int(exposure_weather.get("measured_width_count", 0))
            widths_ok = (
                control_weather.get("state") == "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS"
                and exposure_weather.get("state") == "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS"
                and int(control_weather.get("measured_width_count", 0)) == 36
                and int(exposure_weather.get("measured_width_count", 0)) == 72
                and control_residual <= width.WIDTH_RESIDUAL_TOL_PX
                and exposure_residual <= width.WIDTH_RESIDUAL_TOL_PX
                and abs(float(control_weather.get("source_width_min_px", -1.0)) - float(exposure_weather.get("source_width_min_px", -2.0))) <= 1e-9
                and abs(float(control_weather.get("source_width_max_px", -1.0)) - float(exposure_weather.get("source_width_max_px", -2.0))) <= 1e-9
            )
            all_widths = all_widths and widths_ok

            weather_ids.add((
                int(exposure_weather.get("node_instance_id", -1)),
                int(exposure_weather.get("mesh_instance_id", -1)),
                int(exposure_weather.get("material_instance_id", -1)),
            ))
            sapling_update = sample.get("sapling_update", {})
            sapling_ids.add((
                int(sapling_update.get("node_instance_id", -1)),
                int(sapling_update.get("mesh_instance_id", -1)),
                int(sapling_update.get("material_instance_id", -1)),
            ))

            control_frame = sample.get("control_frame", {})
            candidate_frame = sample.get("candidate_frame", {})
            frames_ok = _verify_frame(control_frame, root) and _verify_frame(candidate_frame, root)
            all_frames = all_frames and frames_ok
            if frames_ok:
                control_raw = root / str(control_frame["raw_path"])
                candidate_raw = root / str(candidate_frame["raw_path"])
                control_raw_paths.append(control_raw)
                candidate_raw_paths.append(candidate_raw)
                delta = _frame_delta(control_raw, candidate_raw)
                pair_deltas.append(delta)
                if sample_index > 0 and int(delta["changed_pixels"]) <= 0:
                    all_visual_deltas = False

        resources_ok = (
            len(weather_ids) == 1
            and len(sapling_ids) == 1
            and next(iter(weather_ids), (-1, -1, -1))[0] > 0
            and next(iter(sapling_ids), (-1, -1, -1))[0] > 0
        )
        all_resources = all_resources and resources_ok

        if len(control_raw_paths) == len(REVIEW_PHASES_US) and len(candidate_raw_paths) == len(REVIEW_PHASES_US):
            for index in range(1, len(REVIEW_PHASES_US)):
                control_transition.append(float(_frame_delta(control_raw_paths[index - 1], control_raw_paths[index])["mean_abs_rgb_lsb"]))
                candidate_transition.append(float(_frame_delta(candidate_raw_paths[index - 1], candidate_raw_paths[index])["mean_abs_rgb_lsb"]))
        else:
            all_frames = False

        control_median = statistics.median(control_transition) if control_transition else 0.0
        candidate_median = statistics.median(candidate_transition) if candidate_transition else 0.0
        context_metrics[context] = {
            "review_frame_pairs": len(pair_deltas),
            "candidate_control_changed_pixel_mean": statistics.fmean(float(row["changed_pixels"]) for row in pair_deltas) if pair_deltas else 0.0,
            "candidate_control_changed_fraction_mean": statistics.fmean(float(row["changed_fraction"]) for row in pair_deltas) if pair_deltas else 0.0,
            "candidate_control_mean_abs_rgb_lsb": statistics.fmean(float(row["mean_abs_rgb_lsb"]) for row in pair_deltas) if pair_deltas else 0.0,
            "control_interframe_mean_abs_rgb_median_lsb": control_median,
            "candidate_interframe_mean_abs_rgb_median_lsb": candidate_median,
            "candidate_to_control_interframe_median_ratio": (candidate_median / control_median) if control_median > 0 else None,
            "interframe_delta_direction": "LOWER" if candidate_median < control_median else ("EQUAL" if candidate_median == control_median else "HIGHER"),
        }

    rear_modes = {
        str(row.get("proof_culling", ""))
        for row in receipt.get("static_source_meshes", [])
        if row.get("asset_id") == TARGET_REAR_ASSET_ID
    }

    checks = {
        "source_width_structure_passes_before_candidate": payload.get("status") == width.STATUS and all(payload.get("checks", {}).values()),
        "observation_schema_state_and_policy_exact": receipt.get("schema") == OBSERVATION_SCHEMA and receipt.get("state") == OBSERVATION_STATE and receipt.get("presentation_policy") == POLICY,
        "exact_receiving_and_parent_identity_preserved": receipt.get("receiving_head") == payload.get("receiving_head") and receipt.get("parent_variant_head") == width.EXPECTED_PARENT_VARIANT_HEAD,
        "both_fixed_contexts_cover_exact_review_phases": set(contexts) == set(CONTEXTS) and all_contexts,
        "current_and_lagged_samples_bind_exact_adjacent_source_rows": all_brackets,
        "two_tap_opacity_budget_never_exceeds_source_alpha": all_opacity_budget,
        "source_width_fidelity_preserved_for_control_and_both_exposure_taps": all_widths and maximum_width_residual_px <= width.WIDTH_RESIDUAL_TOL_PX,
        "weather_and_sapling_resources_remain_stable": all_resources,
        "direct_png_and_raw_rgba_evidence_is_hash_bound": all_frames,
        "temporal_exposure_produces_direct_visible_delta_after_start": all_visual_deltas,
        "rear_tree_culling_state_preserved": rear_modes == {"CULL_BACK"},
    }

    return {
        "schema": SCHEMA,
        "state": STATUS if all(checks.values()) else "FAIL",
        "receiving_head": payload.get("receiving_head"),
        "parent_variant_head": width.EXPECTED_PARENT_VARIANT_HEAD,
        "presentation_policy": POLICY,
        "configured_lag_us": EXPOSURE_LAG_US,
        "review_phases_us": list(REVIEW_PHASES_US),
        "checks": checks,
        "context_metrics": context_metrics,
        "measured_width_count": measured_width_count,
        "maximum_projected_width_residual_px": maximum_width_residual_px,
        "visual_tradeoff_for_review": (
            "Each source streak becomes two half-opacity presentation taps separated by at most 15.625 ms. This may soften temporal stepping but can read as short ghosting or broaden the apparent atmospheric footprint. The verifier reports inter-frame pixel metrics only; it does not promote them to an aesthetic judgment."
        ),
        "truth_boundary": (
            "PASS proves only that this exact Godot proof host can render a source-bound, receiving-only two-tap temporal-exposure Weather candidate at deterministic review phases while preserving exact source-width projection, source-bracket provenance, single-phase sapling motion, capped opacity contribution, static world identity and direct A/B evidence. PASS does not prove wall-clock 32 Hz delivery, perceptual smoothness, final Art Direction or Visual QA acceptance, physical weather, gameplay/physics, target-device performance, arbitrary cameras, CANON, production readiness, or mastery."
        ),
    }


def exercise_opacity_budget_negative_control(payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path) -> dict[str, Any]:
    mutated = copy.deepcopy(receipt)
    for context in CONTEXTS:
        samples = mutated.get("contexts", {}).get(context, {}).get("samples", [])
        if samples:
            samples[0].setdefault("exposure_build", {})["weight_sum"] = 1.2
            break
    return verify_temporal_exposure(payload, mutated, image_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = _load(args.payload)
    receipt = _load(args.receipt)
    report = verify_temporal_exposure(payload, receipt, args.image_root)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
