from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import statistics
from pathlib import Path
from typing import Any

try:
    from . import environment_weather_width_temporal_exposure as legacy
    from . import environment_weather_width_temporal_exposure_normalized as normalized
except ImportError:
    import environment_weather_width_temporal_exposure as legacy
    import environment_weather_width_temporal_exposure_normalized as normalized

SCHEMA = "axm.environment-current-world-weather-width-temporal-exposure-source-cadence-review/v0.1"
STATUS = "PASS_OPACITY_NORMALIZED_TEMPORAL_EXPOSURE_SOURCE_CADENCE_REVIEW_SURFACE"
OBSERVATION_SCHEMA = "axm.environment-current-world-weather-width-temporal-exposure-source-cadence-observation/v0.1"
OBSERVATION_STATE = "OBSERVED_OPACITY_NORMALIZED_TEMPORAL_EXPOSURE_SOURCE_CADENCE_REVIEW"
REVIEW_DECISION = "REVIEW_SURFACE_ONLY_NO_ART_OR_QA_PREFERENCE"
SOURCE_INTERVAL_US = 31_250
SOURCE_INTERVAL_MS = 31.25
SOURCE_CADENCE_HZ = 32.0
PHASES_US = tuple(index * SOURCE_INTERVAL_US for index in range(17))
EXPECTED_MEASURED_WIDTH_COUNT = 17 * len(legacy.CONTEXTS) * (36 + 72)
FORMULA_TOL = normalized.FORMULA_TOL


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_frame(frame: dict[str, Any], root: Path) -> bool:
    return legacy._verify_frame(frame, root)


def _formula_rows_exact(rows: list[dict[str, Any]]) -> tuple[bool, float, float]:
    if len(rows) != 36:
        return False, float("inf"), float("inf")
    max_formula_error = 0.0
    max_equal_source_error = 0.0
    ok = True
    for row in rows:
        current_source = float(row.get("current_source_alpha", -1.0))
        lagged_source = float(row.get("lagged_source_alpha", -1.0))
        current_tap = float(row.get("current_tap_alpha", -1.0))
        lagged_tap = float(row.get("lagged_tap_alpha", -1.0))
        effective = float(row.get("effective_alpha", -1.0))
        ceiling = float(row.get("alpha_ceiling", -1.0))
        expected_current = normalized._normalized_tap_alpha(current_source, 0.5)
        expected_lagged = normalized._normalized_tap_alpha(lagged_source, 0.5)
        expected_effective = 1.0 - (1.0 - expected_current) * (1.0 - expected_lagged)
        row_error = max(
            abs(current_tap - expected_current),
            abs(lagged_tap - expected_lagged),
            abs(effective - expected_effective),
        )
        max_formula_error = max(max_formula_error, row_error)
        if row_error > FORMULA_TOL:
            ok = False
        expected_ceiling = max(current_source, lagged_source)
        if abs(ceiling - expected_ceiling) > FORMULA_TOL or effective - expected_ceiling > FORMULA_TOL:
            ok = False
        equal_source = abs(current_source - lagged_source) <= FORMULA_TOL
        if bool(row.get("equal_source", False)) != equal_source:
            ok = False
        if equal_source:
            equal_error = abs(effective - current_source)
            max_equal_source_error = max(max_equal_source_error, equal_error)
            if equal_error > FORMULA_TOL:
                ok = False
    return ok, max_formula_error, max_equal_source_error


def _frame_ref(mode: str, context: str, sample_index: int) -> str:
    return f"frames/{mode}-{context}-{sample_index:02d}.png"


def build_review_html(report: dict[str, Any], output: str | Path) -> None:
    manifest = {
        context: {
            "control": [_frame_ref("control", context, i) for i in range(17)],
            "candidate": [_frame_ref("candidate", context, i) for i in range(17)],
        }
        for context in legacy.CONTEXTS
    }
    manifest_json = json.dumps(manifest, separators=(",", ":"))
    metrics_json = json.dumps(report.get("context_metrics", {}), separators=(",", ":"))
    body = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AXM Weather exact source-cadence A/B review</title>
<style>
body{{font-family:system-ui,sans-serif;background:#111;color:#eee;margin:0;padding:18px}}
.controls{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:12px 0}}
button,select{{font:inherit;padding:7px 10px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
figure{{margin:0;background:#1b1b1b;padding:8px}}
img{{display:block;width:100%;height:auto;background:#000}}
figcaption{{padding-top:6px;font-weight:650}}
.note{{max-width:1100px;line-height:1.45;color:#ccc}}
code{{color:#fff}}
@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<h1>Weather exact source-cadence A/B review</h1>
<p class="note">Control is the Direction-005-style single-tap source-width presentation. Candidate is the unchanged opacity-normalized two-tap presentation with a 15.625 ms lag. The 17 image pairs are exact real-Godot captures at the authored 31.25 ms source evaluation points from 0 to 500 ms. This page advances frames against a nominal 32 Hz clock only for human review; browser timing, display cadence and target-device performance are <strong>not measured</strong>. Playback is one-shot so no unproven end-to-start loop seam is implied.</p>
<div class="controls">
<label>Camera <select id="context"><option value="path_eye">path_eye</option><option value="elevated_oblique">elevated_oblique</option></select></label>
<button id="play">Play one-shot</button>
<button id="pause">Pause</button>
<button id="reset">Reset</button>
<span id="clock">0.00 ms · frame 0/16</span>
</div>
<div class="grid">
<figure><img id="control" alt="single-tap control"><figcaption>Control · single tap source width</figcaption></figure>
<figure><img id="candidate" alt="normalized two-tap candidate"><figcaption>Candidate · normalized two tap</figcaption></figure>
</div>
<p class="note">Decision boundary: this is a review surface only. It does not establish perceptual smoothness, aesthetic superiority, authored display delivery, physical precipitation/wind behavior, gameplay/physics behavior, target-device performance, Runtime adoption, CANON or production readiness.</p>
<script>
const manifest={manifest_json};
const metrics={metrics_json};
const interval=31.25;
let index=0,playing=false,start=0,pausedElapsed=0,raf=0;
const context=document.getElementById('context');
const control=document.getElementById('control');
const candidate=document.getElementById('candidate');
const clock=document.getElementById('clock');
function show(i){{
  index=Math.max(0,Math.min(16,i));
  const c=context.value;
  control.src=manifest[c].control[index];
  candidate.src=manifest[c].candidate[index];
  clock.textContent=(index*interval).toFixed(2)+' ms · frame '+index+'/16';
}}
function tick(now){{
  if(!playing)return;
  const elapsed=now-start;
  const next=Math.min(16,Math.floor(elapsed/interval));
  if(next!==index)show(next);
  if(elapsed>=16*interval){{playing=false;show(16);return;}}
  raf=requestAnimationFrame(tick);
}}
document.getElementById('play').onclick=()=>{{
  if(playing)return;
  if(index>=16){{index=0;pausedElapsed=0;show(0);}}
  playing=true;
  start=performance.now()-index*interval;
  raf=requestAnimationFrame(tick);
}};
document.getElementById('pause').onclick=()=>{{playing=false;cancelAnimationFrame(raf);}};
document.getElementById('reset').onclick=()=>{{playing=false;cancelAnimationFrame(raf);show(0);}};
context.onchange=()=>show(index);
show(0);
</script>
</body>
</html>
"""
    Path(output).write_text(body, encoding="utf-8")


def verify_source_cadence_review(
    payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path
) -> dict[str, Any]:
    root = Path(image_root)
    states = payload.get("states", [])
    expected = {int(row.get("index", -1)): row for row in states}
    contexts = receipt.get("contexts", {})

    schema_ok = (
        receipt.get("schema") == OBSERVATION_SCHEMA
        and receipt.get("state") == OBSERVATION_STATE
        and receipt.get("presentation_policy") == normalized.POLICY
        and tuple(int(value) for value in receipt.get("review_phases_us", [])) == PHASES_US
        and int(receipt.get("source_cadence_interval_us", -1)) == SOURCE_INTERVAL_US
    )
    all_contexts = set(contexts) == set(legacy.CONTEXTS)
    all_phases = True
    all_brackets = True
    all_formula = True
    all_alpha_ceiling = True
    all_widths = True
    all_frames = True
    all_resources = True
    phase0_equivalence = True
    any_nonzero_direct_delta = False
    maximum_formula_error = 0.0
    maximum_equal_source_error = 0.0
    maximum_width_residual_px = 0.0
    measured_width_count = 0
    context_metrics: dict[str, Any] = {}

    for context in legacy.CONTEXTS:
        block = contexts.get(context, {})
        samples = block.get("samples", [])
        context_ok = (
            block.get("state") == legacy.CONTEXT_STATE
            and block.get("presentation_policy") == normalized.POLICY
            and tuple(int(value) for value in block.get("review_phases_us", [])) == PHASES_US
            and int(block.get("configured_lag_us", -1)) == legacy.EXPOSURE_LAG_US
            and len(samples) == len(PHASES_US)
        )
        all_phases = all_phases and context_ok

        weather_ids: set[tuple[int, int, int]] = set()
        sapling_ids: set[tuple[int, int, int]] = set()
        pair_deltas: list[dict[str, float | int]] = []
        control_raw_paths: list[Path] = []
        candidate_raw_paths: list[Path] = []

        for sample_index, phase_us in enumerate(PHASES_US):
            if sample_index >= len(samples):
                all_phases = False
                continue
            sample = samples[sample_index]
            actual_phase = int(sample.get("phase_us", -1))
            lagged_phase = int(sample.get("lagged_phase_us", -1))
            expected_lagged = max(0, phase_us - legacy.EXPOSURE_LAG_US)
            all_phases = all_phases and actual_phase == phase_us and lagged_phase == expected_lagged
            all_brackets = all_brackets and legacy._verify_bracket(sample.get("current_bracket", {}), phase_us, expected, True)
            all_brackets = all_brackets and legacy._verify_bracket(sample.get("lagged_bracket", {}), expected_lagged, expected, False)

            exposure = sample.get("exposure_build", {})
            rows = exposure.get("opacity_rows", [])
            formula_ok, formula_error, equal_error = _formula_rows_exact(rows)
            maximum_formula_error = max(maximum_formula_error, formula_error)
            maximum_equal_source_error = max(maximum_equal_source_error, equal_error)
            all_formula = all_formula and (
                exposure.get("state") == "PASS_BOUNDED_TEMPORAL_EXPOSURE_LINES"
                and exposure.get("opacity_mapping") == normalized.MAPPING
                and int(exposure.get("source_streak_count", 0)) == 36
                and int(exposure.get("presentation_tap_count", 0)) == 72
                and formula_ok
            )
            all_alpha_ceiling = all_alpha_ceiling and float(exposure.get("maximum_combined_alpha_over_source", 1.0)) <= FORMULA_TOL

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
                and control_residual <= legacy.width.WIDTH_RESIDUAL_TOL_PX
                and exposure_residual <= legacy.width.WIDTH_RESIDUAL_TOL_PX
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
                delta = legacy._frame_delta(control_raw, candidate_raw)
                pair_deltas.append(delta)
                if sample_index == 0:
                    phase0_equivalence = phase0_equivalence and (
                        float(delta["mean_abs_rgb_lsb"]) <= normalized.PHASE0_MEAN_ABS_RGB_MAX_LSB
                        and int(delta["maximum_rgb_channel_delta_lsb"]) <= normalized.PHASE0_MAX_CHANNEL_DELTA_LSB
                        and float(delta["changed_fraction"]) <= normalized.PHASE0_CHANGED_FRACTION_MAX
                    )
                elif int(delta["changed_pixels"]) > 0:
                    any_nonzero_direct_delta = True

        all_resources = all_resources and (
            len(weather_ids) == 1
            and len(sapling_ids) == 1
            and next(iter(weather_ids), (-1, -1, -1))[0] > 0
            and next(iter(sapling_ids), (-1, -1, -1))[0] > 0
        )

        control_transition: list[float] = []
        candidate_transition: list[float] = []
        if len(control_raw_paths) == len(PHASES_US) and len(candidate_raw_paths) == len(PHASES_US):
            for index in range(1, len(PHASES_US)):
                control_transition.append(float(legacy._frame_delta(control_raw_paths[index - 1], control_raw_paths[index])["mean_abs_rgb_lsb"]))
                candidate_transition.append(float(legacy._frame_delta(candidate_raw_paths[index - 1], candidate_raw_paths[index])["mean_abs_rgb_lsb"]))
        else:
            all_frames = False

        control_median = statistics.median(control_transition) if control_transition else 0.0
        candidate_median = statistics.median(candidate_transition) if candidate_transition else 0.0
        context_metrics[context] = {
            "review_frame_pairs": len(pair_deltas),
            "source_cadence_hz": SOURCE_CADENCE_HZ,
            "source_interval_ms": SOURCE_INTERVAL_MS,
            "candidate_control_changed_pixel_mean": statistics.fmean(float(row["changed_pixels"]) for row in pair_deltas) if pair_deltas else 0.0,
            "candidate_control_changed_fraction_mean": statistics.fmean(float(row["changed_fraction"]) for row in pair_deltas) if pair_deltas else 0.0,
            "control_interframe_mean_abs_rgb_median_lsb": control_median,
            "candidate_interframe_mean_abs_rgb_median_lsb": candidate_median,
            "candidate_to_control_interframe_median_ratio": (candidate_median / control_median) if control_median > 0 else None,
            "interframe_delta_direction": "LOWER" if candidate_median < control_median else ("EQUAL" if candidate_median == control_median else "HIGHER"),
            "pair_deltas": pair_deltas,
        }

    checks = {
        "source_width_structure_passes_before_review": payload.get("status") == legacy.width.STATUS and all(payload.get("checks", {}).values()),
        "source_cadence_observation_schema_state_policy_exact": schema_ok,
        "both_fixed_contexts_cover_all_17_exact_source_cadence_phases": all_contexts and all_phases,
        "current_and_half_interval_lagged_samples_bind_exact_source_brackets": all_brackets,
        "normalized_transmittance_formula_remains_exact": all_formula and maximum_formula_error <= FORMULA_TOL,
        "combined_alpha_never_exceeds_larger_source_alpha": all_alpha_ceiling,
        "source_width_fidelity_preserved_for_control_and_candidate": all_widths and measured_width_count == EXPECTED_MEASURED_WIDTH_COUNT,
        "direct_png_and_raw_rgba_evidence_is_hash_bound": all_frames,
        "phase0_remains_brightness_equivalent_within_existing_bound": phase0_equivalence,
        "at_least_one_nonzero_phase_has_direct_candidate_control_delta": any_nonzero_direct_delta,
        "weather_and_sapling_resources_remain_stable": all_resources,
    }

    return {
        "schema": SCHEMA,
        "state": STATUS if all(checks.values()) else "FAIL",
        "decision": REVIEW_DECISION,
        "receiving_head": payload.get("receiving_head"),
        "parent_variant_head": payload.get("parent_variant_head"),
        "presentation_policy": normalized.POLICY,
        "source_interval_us": SOURCE_INTERVAL_US,
        "source_interval_ms": SOURCE_INTERVAL_MS,
        "source_cadence_hz": SOURCE_CADENCE_HZ,
        "review_phases_us": list(PHASES_US),
        "configured_lag_us": legacy.EXPOSURE_LAG_US,
        "checks": checks,
        "maximum_formula_error": maximum_formula_error,
        "maximum_equal_source_alpha_error": maximum_equal_source_error,
        "maximum_projected_width_residual_px": maximum_width_residual_px,
        "measured_width_count": measured_width_count,
        "context_metrics": context_metrics,
        "playback_review_semantics": (
            "The retained 17 control/candidate pairs are exact real-Godot captures at the authored 31.25 ms source evaluation points. The offline HTML advances those images against a nominal 32 Hz review clock, one-shot only. Browser/display cadence is not measured and no end-to-start loop seam is claimed."
        ),
        "visual_tradeoff_for_review": (
            "This surface lets Art Direction and independent Visual QA compare the current single-tap source-width reference against the unchanged opacity-normalized two-tap candidate as a complete source-cadence sequence. The verifier reports raster and inter-frame metrics only and does not convert them into perceptual smoothness or aesthetic preference."
        ),
        "truth_boundary": (
            "PASS proves only that this exact Godot proof host rendered both unchanged Weather presentations at all 17 authored source-cadence evaluation points with exact source-width/provenance and normalized-opacity contracts, and that the retained frames can be reviewed as a one-shot nominal-32-Hz image sequence. PASS does not prove browser/display 32 Hz delivery, target-device frame pacing or performance, human-perceived smoothness, aesthetic superiority, physical Weather, gameplay/physics, arbitrary cameras, Runtime adoption, CANON, production readiness, or mastery."
        ),
    }


def exercise_frame_identity_negative_control(
    payload: dict[str, Any], receipt: dict[str, Any], image_root: str | Path
) -> dict[str, Any]:
    mutated = copy.deepcopy(receipt)
    context = legacy.CONTEXTS[0]
    samples = mutated.get("contexts", {}).get(context, {}).get("samples", [])
    if samples:
        samples[0].get("candidate_frame", {})["png_sha256"] = "0" * 64
    return verify_source_cadence_review(payload, mutated, image_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--html-output")
    args = parser.parse_args()
    payload = _load(args.payload)
    receipt = _load(args.receipt)
    report = verify_source_cadence_review(payload, receipt, args.image_root)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.html_output:
        build_review_html(report, args.html_output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
