from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.environment-selected-roughness-compact-east-composition/v0.1"
RESULT = "PASS_CURRENT_WORLD_SELECTED_ROUGHNESS_PLUS_COMPACT_EAST_COMPOSITION_REVIEW_READY__DUAL_ADOPTION_HELD"
RULE = "CROSS_ASSET_WORLD_STACKING_SHOULD_HOLD_ONE_REVIEW_CANDIDATE_EXACT_WHILE_PROVING_THE_SECOND_AGAINST_THE_EXACT_ALREADY_REVIEWABLE_PARENT"

ROUGHNESS_HEAD = "d8a1d950ed5f21e6ad356404f46407c99c160017"
ROUGHNESS_STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_APPEARANCE_CANDIDATE_REVIEW_READY__ENVIRONMENT_ADOPTION_HELD"
ROUGHNESS_BIND_STATE = "PASS_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_APPEARANCE_CANDIDATE_BOUND__ENVIRONMENT_ADOPTION_HELD"
ROUGHNESS_PNG_SHA256 = "57cf746a9a7e0615884fe3c45c6c4df677c2bd0631def61b3ccb1684daa26949"
ROUGHNESS_SCALAR_SHA256 = "b8d13c07f9b71278042b0d42d44b84579a3f327c6adf6723cae4c8c8f06dd38e"

VFX_HEAD = "29ef2d4cc4398b3f26290e4e1f1f10398ca9898c"
NATURE_VFX_HEAD = "cef2ad78d8e36a55ada5dad07329f1a7125d48de"
VFX_RESULT = "PASS_CURRENT_WORLD_COMPACT_EAST_VISUAL_RESPONSE_TARGET_HOST"
VFX_OBSERVER_BLOB = "67a3aa1f1932a99de1b6e835ad308630bff282a5"
WEATHER_SEMANTICS = "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED"
WORLD_PARENT_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"

OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
COMPACT_ASSET_ID = "source:nature:compact-east-tree-neutral-001"

PARENT_EXTENDS = 'extends "res://atmosphere_current_world_nature_leaf_flutter_observe.gd"'
COMBINED_EXTENDS = 'extends "res://atmosphere_current_world_object_selected_roughness_observe.gd"'


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def find(rows: Any, asset_id: str) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise ValueError("runtime static_source_meshes missing")
    matches = [row for row in rows if isinstance(row, dict) and row.get("asset_id") == asset_id]
    if len(matches) != 1:
        raise ValueError(f"expected one {asset_id} runtime row, got {len(matches)}")
    return matches[0]


def verify_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema") != SCHEMA:
        raise ValueError("Environment composition contract schema drift")
    if contract.get("reusable_rule") != RULE:
        raise ValueError("Environment composition reusable rule drift")
    parent = contract.get("selected_roughness_parent", {})
    if parent.get("head") != ROUGHNESS_HEAD or parent.get("state") != ROUGHNESS_STATE:
        raise ValueError("selected-roughness parent identity drift")
    compact = contract.get("compact_east_vfx_receiver", {})
    if compact.get("map_head") != VFX_HEAD or compact.get("nature_vfx_head") != NATURE_VFX_HEAD:
        raise ValueError("compact-east VFX identity drift")
    if compact.get("state") != VFX_RESULT or compact.get("observer_blob") != VFX_OBSERVER_BLOB:
        raise ValueError("compact-east VFX evidence drift")
    decision = contract.get("decision", {})
    if decision.get("environment_selected_roughness_adoption") is not False:
        raise ValueError("selected roughness adoption must remain held")
    if decision.get("environment_compact_east_adoption") is not False:
        raise ValueError("compact-east adoption must remain held")
    if decision.get("art_qa_acceptance_required") is not True or decision.get("runtime_acceptance_required") is not True:
        raise ValueError("Environment owner boundary drift")


def compose_observer(donor: Path, output: Path, receipt: Path) -> dict[str, Any]:
    text = donor.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != PARENT_EXTENDS:
        raise ValueError("exact VFX donor observer parent drift")
    if text.count(PARENT_EXTENDS) != 1:
        raise ValueError("VFX donor observer parent declaration is not unique")
    out_lines = [COMBINED_EXTENDS, *lines[1:]]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(out_lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    rebuilt = output.read_text(encoding="utf-8").splitlines()
    if rebuilt[0] != COMBINED_EXTENDS or rebuilt[1:] != lines[1:]:
        raise ValueError("combined observer changed donor body beyond the exact parent receiver")
    result = {
        "schema": "axm.environment-observer-composition/v0.1",
        "state": "PASS_EXACT_VFX_OBSERVER_BODY_COMPOSED_OVER_SELECTED_ROUGHNESS_RECEIVER",
        "vfx_map_head": VFX_HEAD,
        "vfx_observer_git_blob": VFX_OBSERVER_BLOB,
        "original_parent": PARENT_EXTENDS,
        "combined_parent": COMBINED_EXTENDS,
        "donor_body_after_extends_byte_semantics_preserved": True,
        "authority": "ENVIRONMENT_RECEIVING_COMPOSITION_ONLY",
        "truth_boundary": (
            "Environment composes the already-green compact-east VFX observer over the already-reviewable "
            "selected-roughness receiver by changing only the GDScript parent receiver. The donor VFX body "
            "remains otherwise identical; this does not transfer Nature, VFX, Materials, Technical-Art, Runtime, "
            "Art/QA or CANON authority."
        ),
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def roughness_observation(row: dict[str, Any]) -> dict[str, Any]:
    obs = row.get("environment_object_selected_roughness_current_world")
    if not isinstance(obs, dict):
        raise ValueError("selected-roughness Object observation missing")
    if obs.get("state") != ROUGHNESS_BIND_STATE:
        raise ValueError("selected-roughness Object bind state drift")
    if obs.get("selected_png_sha256") != ROUGHNESS_PNG_SHA256:
        raise ValueError("selected-roughness PNG identity drift")
    if obs.get("selected_scalar_r8_sha256") != ROUGHNESS_SCALAR_SHA256:
        raise ValueError("selected-roughness scalar identity drift")
    if obs.get("selected_surface_count") != 2 or obs.get("environment_adoption") is not False:
        raise ValueError("selected-roughness surface/adoption boundary drift")
    return obs


def runtime_submission_trade(parent: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "draw_calls_in_frame",
        "objects_in_frame",
        "primitives_in_frame",
        "buffer_mem_bytes",
        "texture_mem_bytes",
    )
    values: dict[str, list[int]] = {field: [] for field in fields}
    parent_samples = parent.get("samples", [])
    candidate_samples = candidate.get("samples", [])
    if len(parent_samples) != 17 or len(candidate_samples) != 17:
        raise ValueError("current-world Runtime sample count drift")
    for before, after in zip(parent_samples, candidate_samples, strict=True):
        if int(before.get("index", -1)) != int(after.get("index", -1)):
            raise ValueError("current-world Runtime sample identity drift")
        for context in ("path_eye", "elevated_oblique"):
            for mode in ("control", "candidate"):
                a = before["contexts"][context][mode]["runtime"]
                b = after["contexts"][context][mode]["runtime"]
                for field in fields:
                    values[field].append(int(b[field]) - int(a[field]))
    structural = ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame")
    for field in structural:
        if any(value != 0 for value in values[field]):
            raise ValueError(f"compact-east composition changed structural Runtime submission field: {field}")
    return {
        field: {
            "min_delta": min(rows),
            "max_delta": max(rows),
            "unique_deltas": sorted(set(rows)),
        }
        for field, rows in values.items()
    }


def verify_weather(runtime: dict[str, Any]) -> dict[str, Any]:
    count = 0
    maximum = 0.0
    samples = runtime.get("samples", [])
    if len(samples) != 17:
        raise ValueError("current-world Weather sample count drift")
    for sample in samples:
        for context in ("path_eye", "elevated_oblique"):
            update = sample["contexts"][context]["candidate"]["weather_update"]
            count += int(update.get("measured_width_count", 0))
            maximum = max(maximum, float(update.get("maximum_projected_width_residual_px", 999.0)))
    if count != 1224 or maximum > 0.05:
        raise ValueError(f"Weather source-width continuity failed: count={count} max={maximum}")
    return {
        "measurements": count,
        "maximum_projected_width_residual_px": maximum,
        "tolerance_px": 0.05,
    }


def verify(args: argparse.Namespace) -> dict[str, Any]:
    contract = load(args.contract)
    verify_contract(contract)

    roughness_report = load(args.roughness_report)
    if roughness_report.get("environment_head") != ROUGHNESS_HEAD:
        raise ValueError("selected-roughness parent head drift")
    if roughness_report.get("state") != ROUGHNESS_STATE:
        raise ValueError("selected-roughness parent review state drift")
    if roughness_report.get("environment_adoption") is not False:
        raise ValueError("selected-roughness parent adoption drift")

    vfx_report = load(args.vfx_report)
    if vfx_report.get("state") != VFX_RESULT:
        raise ValueError("compact-east target-host result drift")
    if vfx_report.get("nature_vfx_head") != NATURE_VFX_HEAD:
        raise ValueError("compact-east Nature VFX owner drift")
    if vfx_report.get("matched_frames") != 68 or vfx_report.get("neutral_endpoint_changed_pixels") != 0:
        raise ValueError("compact-east frame/neutral proof drift")
    if vfx_report.get("fully_observing_contexts") != ["elevated_oblique"]:
        raise ValueError("compact-east observing-context boundary drift")
    if vfx_report.get("non_observing_contexts") != ["path_eye"]:
        raise ValueError("compact-east non-observing-context boundary drift")
    if vfx_report.get("partial_contexts") not in ([], None):
        raise ValueError("compact-east partial camera evidence appeared")
    if vfx_report.get("interior_changed_frames") != 30:
        raise ValueError("compact-east interior visible-frame count drift")

    parent_runtime = load(args.parent_runtime)
    runtime = load(args.runtime)
    if runtime.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError("combined target-host inherited runtime state drift")
    if runtime.get("environment_object_selected_roughness_current_world_state") != ROUGHNESS_BIND_STATE:
        raise ValueError("combined target-host selected-roughness top-level state drift")
    if runtime.get("environment_compact_east_visual_response_vfx_head") != NATURE_VFX_HEAD:
        raise ValueError("combined target-host compact-east VFX provenance drift")
    if runtime.get("environment_compact_east_visual_response_weather_semantics") != WEATHER_SEMANTICS:
        raise ValueError("combined target-host Weather semantics drift")
    if int(runtime.get("environment_compact_east_visual_response_phase_count", -1)) != 17:
        raise ValueError("combined target-host compact-east phase-count drift")

    parent_samples = parent_runtime.get("samples", [])
    samples = runtime.get("samples", [])
    if len(parent_samples) != 17 or len(samples) != 17:
        raise ValueError("combined current-world sample count drift")

    roughness_exact_matches = 0
    compact_phases: list[int] = []
    for index, (before, after) in enumerate(zip(parent_samples, samples, strict=True)):
        if int(after.get("index", -1)) != index:
            raise ValueError(f"combined current-world phase index drift at {index}")
        before_object = find(before.get("static_source_meshes"), OBJECT_ASSET_ID)
        after_object = find(after.get("static_source_meshes"), OBJECT_ASSET_ID)
        before_obs = roughness_observation(before_object)
        after_obs = roughness_observation(after_object)
        if before_obs != after_obs:
            raise ValueError(f"selected-roughness Object receiver changed while stacking compact-east at phase {index}")
        roughness_exact_matches += 1

        compact = find(after.get("static_source_meshes"), COMPACT_ASSET_ID)
        phase = int(compact.get("compact_east_visual_response_phase_index", -1))
        if phase != index:
            raise ValueError(f"compact-east runtime phase identity drift at {index}")
        if compact.get("compact_east_visual_response_vfx_head") != NATURE_VFX_HEAD:
            raise ValueError(f"compact-east runtime VFX identity drift at {index}")
        if compact.get("compact_east_visual_response_weather_semantics") != WEATHER_SEMANTICS:
            raise ValueError(f"compact-east runtime Weather semantics drift at {index}")
        compact_phases.append(phase)

    if compact_phases != list(range(17)):
        raise ValueError("compact-east exact 17-phase runtime sequence drift")

    weather = verify_weather(runtime)
    trade = runtime_submission_trade(parent_runtime, runtime)

    report = {
        "schema": SCHEMA,
        "state": RESULT,
        "environment_head": args.environment_head,
        "selected_roughness_parent_head": ROUGHNESS_HEAD,
        "compact_east_vfx_map_head": VFX_HEAD,
        "compact_east_nature_vfx_head": NATURE_VFX_HEAD,
        "reusable_rule": RULE,
        "real_world_scope": {
            "states": 17,
            "matched_target_host_frames": 68,
            "assets_present": [
                "Building",
                "Nature west-sapling",
                "Nature compact-east",
                "Object selected roughness",
                "Map footprint cue",
                "Weather source-width presentation",
            ],
        },
        "selected_roughness_continuity": {
            "exact_runtime_observation_matches": roughness_exact_matches,
            "expected": 17,
            "png_sha256": ROUGHNESS_PNG_SHA256,
            "scalar_r8_sha256": ROUGHNESS_SCALAR_SHA256,
        },
        "compact_east_continuity": {
            "phase_indices": compact_phases,
            "matched_frames": vfx_report["matched_frames"],
            "neutral_endpoint_changed_pixels": vfx_report["neutral_endpoint_changed_pixels"],
            "interior_changed_frames": vfx_report["interior_changed_frames"],
            "fully_observing_contexts": vfx_report["fully_observing_contexts"],
            "non_observing_contexts": vfx_report["non_observing_contexts"],
            "maximum_changed_frame_fraction": vfx_report.get("maximum_changed_frame_fraction"),
        },
        "weather_width_continuity": weather,
        "proof_host_runtime_trade_vs_exact_selected_roughness_parent": trade,
        "environment_selected_roughness_adoption": False,
        "environment_compact_east_adoption": False,
        "art_qa_acceptance_required": True,
        "runtime_acceptance_required": True,
        "checks": {
            "selected_roughness_exactly_preserved_all_17_states": roughness_exact_matches == 17,
            "compact_east_exact_17_phase_sequence_received": compact_phases == list(range(17)),
            "compact_east_target_host_evidence_preserved": vfx_report.get("state") == VFX_RESULT,
            "weather_width_exact_measurement_count_preserved": weather["measurements"] == 1224,
            "structural_submission_counts_unchanged": all(
                trade[field]["unique_deltas"] == [0]
                for field in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame")
            ),
            "dual_environment_adoption_held": True,
        },
        "truth_boundary": (
            "Environment proves coexistence of the exact already-reviewable Object selected-roughness candidate and the exact "
            "already-green compact-east Nature VFX receiver in the retained real current world. The selected-roughness parent "
            "is held exact while compact-east is the only newly stacked visual-response variable. This does not grant Art/QA "
            "preference, Runtime/device acceptance, physical-wind semantics, gameplay/physics, CANON or production readiness."
        ),
    }
    if not all(report["checks"].values()):
        raise ValueError(f"Environment composition checks failed: {report['checks']}")
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    compose = sub.add_parser("compose-observer")
    compose.add_argument("--donor", required=True)
    compose.add_argument("--output", required=True)
    compose.add_argument("--receipt", required=True)

    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--contract", required=True)
    verify_parser.add_argument("--roughness-report", required=True)
    verify_parser.add_argument("--vfx-report", required=True)
    verify_parser.add_argument("--parent-runtime", required=True)
    verify_parser.add_argument("--runtime", required=True)
    verify_parser.add_argument("--environment-head", required=True)
    verify_parser.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "compose-observer":
        result = compose_observer(Path(args.donor), Path(args.output), Path(args.receipt))
    else:
        result = verify(args)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
