from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import environment_eye_level as eye

EVIDENCE_SCHEMA = "axm.environment-weather-opacity-fidelity-evidence/v0.1"
CONTROL_MODE = "UNIFORM_PROOF_ALPHA_0P62"
CANDIDATE_MODE = "SOURCE_STREAK_OPACITY_VERTEX_ALPHA"
SUPPORTED_MODES = {CONTROL_MODE, CANDIDATE_MODE}


def _without_profile(payload: dict) -> dict:
    value = copy.deepcopy(payload)
    value.pop("weather_render_profile", None)
    value.pop("scene_digest", None)
    return value


def _refresh_scene_digest(payload: dict) -> dict:
    value = copy.deepcopy(payload)
    value.pop("scene_digest", None)
    value["scene_digest"] = eye.digest(value)
    return value


def _profile_payload(base: dict, mode: str) -> dict:
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"unsupported weather opacity mode: {mode}")
    value = copy.deepcopy(base)
    value["study_id"] = f"environment-weather-opacity-fidelity-001-{mode.lower()}"
    value["weather_render_profile"] = {
        "schema": "axm.environment-weather-render-profile/v0.1",
        "opacity_mode": mode,
        "uniform_control_alpha": 0.62 if mode == CONTROL_MODE else None,
        "source_opacity_consumed": mode == CANDIDATE_MODE,
        "width_policy": "SOURCE_WIDTH_PX_NOT_MAPPED_TO_3D_LINE_WIDTH_IN_THIS_PROOF",
        "truth_boundary": (
            "This profile changes only how the existing source-owned per-streak opacity is represented by the pinned Godot proof host. "
            "It does not change streak geometry, source motion, physical weather semantics, line-width semantics, gameplay, or performance policy."
        ),
    }
    value["truth_boundary"] = (
        str(base["truth_boundary"])
        + " This VFX fidelity comparison changes only the target-host Weather opacity representation; all source geometry and receiving-scene state remain fixed."
    )
    return _refresh_scene_digest(value)


def build_pair(manifest_path: str | Path, nature_root: str | Path, weather_root: str | Path) -> tuple[dict, dict, dict]:
    base = eye.build_scene_payload(manifest_path, nature_root, weather_root)
    base_report = eye.evaluate(base)
    if base_report["status"] != "PASS":
        raise ValueError("environment eye-level source payload must PASS before Weather opacity fidelity proof")

    lines = base["weather_lines"]
    if not lines:
        raise ValueError("Weather opacity fidelity proof requires source Weather lines")
    opacities = [float(row["opacity"]) for row in lines]
    if any(value < 0.0 or value > 1.0 for value in opacities):
        raise ValueError("source Weather opacity must stay in [0,1]")

    control = _profile_payload(base, CONTROL_MODE)
    candidate = _profile_payload(base, CANDIDATE_MODE)
    receiving_head = os.environ.get("AXM_RECEIVING_HEAD", "UNSET_LOCAL_HEAD")
    control["receiving_head"] = receiving_head
    candidate["receiving_head"] = receiving_head
    control = _refresh_scene_digest(control)
    candidate = _refresh_scene_digest(candidate)

    ids = [str(row["id"]) for row in lines]
    checks = {
        "environment_source_payload_pass": base_report["status"] == "PASS",
        "weather_field_has_36_source_streaks": len(lines) == 36,
        "streak_identity_unique": len(set(ids)) == len(ids),
        "source_opacity_present_for_every_streak": len(opacities) == len(lines),
        "source_opacity_in_unit_interval": all(0.0 <= value <= 1.0 for value in opacities),
        "source_opacity_has_authored_variation": min(opacities) < max(opacities),
        "control_and_candidate_scene_equal_except_render_profile": _without_profile(control) == _without_profile(candidate),
        "control_keeps_historical_uniform_alpha": control["weather_render_profile"]["opacity_mode"] == CONTROL_MODE and control["weather_render_profile"]["uniform_control_alpha"] == 0.62,
        "candidate_consumes_source_opacity": candidate["weather_render_profile"]["opacity_mode"] == CANDIDATE_MODE and candidate["weather_render_profile"]["source_opacity_consumed"] is True,
        "source_line_payload_identical": control["weather_lines"] == candidate["weather_lines"] == base["weather_lines"],
        "weather_semantics_remain_visual_only": base["source_integration"]["weather_overlay"]["semantics"] == "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED",
    }

    report = {
        "schema": EVIDENCE_SCHEMA,
        "study_id": "environment-weather-opacity-fidelity-001",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "receiving_head": receiving_head,
        "checks": checks,
        "source_weather": {
            "repository": base["source_integration"]["weather_overlay"]["source_repository"],
            "head": base["source_integration"]["weather_overlay"]["source_head"],
            "source_digest": base["source_integration"]["weather_overlay"]["source_digest"],
            "semantics": base["source_integration"]["weather_overlay"]["semantics"],
            "sample_time_s": base["source_integration"]["weather_overlay"]["sample_time_s"],
            "streak_count": len(lines),
            "source_opacity_min": min(opacities),
            "source_opacity_max": max(opacities),
            "source_opacity_mean": sum(opacities) / len(opacities),
        },
        "control": {
            "scene_digest": control["scene_digest"],
            "opacity_mode": CONTROL_MODE,
            "uniform_alpha": 0.62,
        },
        "candidate": {
            "scene_digest": candidate["scene_digest"],
            "opacity_mode": CANDIDATE_MODE,
            "source_opacity_consumed": True,
        },
        "renderer_boundary": {
            "host": "Godot 4.7.2 GL Compatibility",
            "mechanism": "ImmediateMesh vertex color alpha with BaseMaterial3D.vertex_color_use_as_albedo",
            "line_width": "SOURCE_WIDTH_PX_NOT_MAPPED_TO_3D_LINE_WIDTH_IN_THIS_PROOF",
        },
        "truth_boundary": (
            "PASS proves only that the exact current Environment payload already carries source-owned per-streak opacity and that a bounded target-host profile can consume it without changing Weather geometry or unrelated scene state. "
            "Render evidence is required separately to prove a visible target-host delta. This does not prove better art direction, physical atmosphere, line-width fidelity, continuous playback, runtime performance, gameplay, CANON, or VFX mastery."
        ),
    }
    return control, candidate, report


def build(manifest_path: str | Path, nature_root: str | Path, weather_root: str | Path, output_dir: str | Path) -> dict:
    control, candidate, report = build_pair(manifest_path, nature_root, weather_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "control_scene.json").write_text(json.dumps(control, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "candidate_scene.json").write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "comparison.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="examples/environment_real_slice_001.json")
    parser.add_argument("--nature-root", required=True)
    parser.add_argument("--weather-root", required=True)
    parser.add_argument("--output", default="evidence/environment_weather_opacity_fidelity_001")
    args = parser.parse_args()
    report = build(args.manifest, args.nature_root, args.weather_root, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
