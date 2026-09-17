from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from typing import Any

import environment_nature_leaf_flutter_current_world as parent_tool
import environment_nature_split_surface_culling_current_world as surface_tool

PARENT_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
PARENT_STRUCTURE_RESULT = "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_STRUCTURE"
NATURE_VFX_HEAD = "cef2ad78d8e36a55ada5dad07329f1a7125d48de"
SOURCE_RESULT = "PASS_COMPACT_EAST_TREE_BOUNDED_VISUAL_RESPONSE_CANDIDATE"
STRUCTURE_RESULT = "PASS_CURRENT_WORLD_COMPACT_EAST_VISUAL_RESPONSE_STRUCTURE"
TARGET_RESULT = "PASS_CURRENT_WORLD_COMPACT_EAST_VISUAL_RESPONSE_TARGET_HOST"
RECEIVING_SCHEMA = "axm.environment-compact-east-visual-response-receiving/v0.1"
ASSET_ID = "source:nature:compact-east-tree-neutral-001"
EXPECTED_SOURCE_HEAD = "64116d63fc76daa1623b5fd5046a4e6074100bda"
EXPECTED_SOURCE_DIGEST = "9c87cf26f02f7adee832908652942218ec779c9029a0611aae1fb66eb0f62f54"
EXPECTED_NEUTRAL_DIGEST = "420135f6effbadb1b344675948b9ddc471dcb83177702888f0b32327c5121c18"
EXPECTED_WEATHER_HEAD = "ca2eaba519e8449835b0ea6ef944b7080c3caa6a"
EXPECTED_WEATHER_SEMANTICS = "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED"
VERTICES = 390
TRIANGLES = 570


def load_json(path: Path) -> dict[str, Any]:
    return parent_tool.load_json(path)


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(a[i]) - float(b[i])) ** 2 for i in range(3)))


def _translate(vertices: list[list[float]], offset: list[float]) -> list[list[float]]:
    return [[float(v[i]) + float(offset[i]) for i in range(3)] for v in vertices]


def _translated_residual(receiver: list[list[float]], donor: list[list[float]]) -> tuple[float, list[float]]:
    if len(receiver) != len(donor) or not receiver:
        return math.inf, []
    offset = [float(receiver[0][axis]) - float(donor[0][axis]) for axis in range(3)]
    residual = 0.0
    for current, source in zip(receiver, donor):
        for axis in range(3):
            residual = max(residual, abs((float(current[axis]) - float(source[axis])) - offset[axis]))
    return residual, offset


def _compact(scene: dict[str, Any]) -> dict[str, Any]:
    rows = [
        row for row in scene.get("additional_source_meshes", [])
        if isinstance(row, dict) and row.get("asset_id") == ASSET_ID
    ]
    if len(rows) != 1:
        raise ValueError(f"exact compact-east receiver count drift: {len(rows)}")
    return rows[0]


def _validate_parent(parent: dict[str, Any]) -> None:
    if parent.get("environment_head") != PARENT_HEAD:
        raise ValueError("exact accepted Nature leaf-flutter parent head drift")
    if parent.get("nature_leaf_flutter_structure_result") != PARENT_STRUCTURE_RESULT:
        raise ValueError("accepted current-world Nature leaf-flutter structure result missing")
    if len(parent.get("states", [])) != 17:
        raise ValueError("accepted current-world parent must retain exact 17 states")
    if parent.get("weather_variant_seed") != 44021:
        raise ValueError("accepted Weather seed drift")


def _validate_source(summary: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    if summary.get("state") != SOURCE_RESULT:
        raise ValueError("compact-east Nature VFX source candidate is not green")
    if summary.get("source_head") != EXPECTED_SOURCE_HEAD:
        raise ValueError("compact-east source head drift")
    if summary.get("source_digest") != EXPECTED_SOURCE_DIGEST:
        raise ValueError("compact-east source digest drift")
    if summary.get("migrated_neutral_mesh_digest") != EXPECTED_NEUTRAL_DIGEST:
        raise ValueError("compact-east migrated neutral identity drift")
    if summary.get("weather_head") != EXPECTED_WEATHER_HEAD:
        raise ValueError("compact-east Weather provenance drift")
    if summary.get("weather_semantics") != EXPECTED_WEATHER_SEMANTICS:
        raise ValueError("compact-east Weather semantics were promoted beyond visual-only")
    response = summary.get("response", {})
    if float(response.get("duration_s", -1.0)) != 0.5 or int(response.get("phase_count", -1)) != 16:
        raise ValueError("compact-east source timing contract drift")
    if abs(float(response.get("max_displacement_ceiling_m", -1.0)) - 0.135) > 1e-12:
        raise ValueError("compact-east source displacement ceiling drift")
    samples = summary.get("samples", [])
    if not isinstance(samples, list) or len(samples) != 17:
        raise ValueError("compact-east source must retain exact 17 phases")
    for index, sample in enumerate(samples):
        if int(sample.get("phase_index", -1)) != index:
            raise ValueError(f"compact-east source phase identity drift at {index}")
        phase_path = root / f"phase_{index:02d}_mesh.json"
        if not phase_path.is_file():
            raise ValueError(f"compact-east source phase mesh missing: {phase_path}")
    return samples


def _receiver_contract(source: dict[str, Any]) -> dict[str, Any]:
    return source.get("environment_compact_east_visual_response_receiving", {}) if isinstance(source, dict) else {}


def _validate_receiving_payload(payload: dict[str, Any], environment_head: str) -> None:
    if payload.get("environment_head") != environment_head:
        raise ValueError("compact-east current-world payload head drift")
    if payload.get("compact_east_visual_response_parent_environment_head") != PARENT_HEAD:
        raise ValueError("compact-east current-world parent identity drift")
    if payload.get("compact_east_visual_response_vfx_head") != NATURE_VFX_HEAD:
        raise ValueError("compact-east current-world VFX source head drift")
    if payload.get("compact_east_visual_response_structure_result") != STRUCTURE_RESULT:
        raise ValueError("compact-east current-world structure PASS missing")
    if len(payload.get("states", [])) != 17:
        raise ValueError("compact-east current-world state count drift")
    for index, row in enumerate(payload["states"]):
        source = _compact(row["scene"])
        receiving = _receiver_contract(source)
        if receiving.get("schema") != RECEIVING_SCHEMA:
            raise ValueError(f"compact-east receiving schema drift at phase {index}")
        if receiving.get("vfx_head") != NATURE_VFX_HEAD:
            raise ValueError(f"compact-east receiving VFX head drift at phase {index}")
        if int(receiving.get("source_phase_index", -1)) != index:
            raise ValueError(f"compact-east receiving phase drift at phase {index}")
        if receiving.get("weather_semantics") != EXPECTED_WEATHER_SEMANTICS:
            raise ValueError(f"compact-east receiving Weather semantics drift at phase {index}")


def build(parent: dict[str, Any], source_root: Path, environment_head: str) -> dict[str, Any]:
    _validate_parent(parent)
    summary = load_json(source_root / "summary.json")
    samples = _validate_source(summary, source_root)
    neutral = load_json(source_root / "phase_00_mesh.json")
    if len(neutral.get("vertices", [])) != VERTICES or len(neutral.get("triangles", [])) != TRIANGLES:
        raise ValueError("compact-east neutral topology count drift")
    if surface_tool.digest(neutral) != EXPECTED_NEUTRAL_DIGEST:
        raise ValueError("compact-east neutral mesh digest drift")

    out_states: list[dict[str, Any]] = []
    offsets: list[list[float]] = []
    phase_mesh_digests: list[str] = []
    max_parent_neutral_residual = 0.0
    max_current_world_delta = 0.0
    changed_vertex_counts: list[int] = []
    preserved_weather = [row.get("weather_field_digest") for row in parent["states"]]
    preserved_sapling = [row.get("sapling_mesh_digest") for row in parent["states"]]

    for index, (parent_row, sample) in enumerate(zip(parent["states"], samples)):
        if int(parent_row.get("index", -1)) != index:
            raise ValueError("current-world parent state index drift")
        expected_time = float(sample.get("time_s", -1.0))
        if abs(float(parent_row.get("time_s", -2.0)) - expected_time) > 1e-12:
            raise ValueError(f"compact-east/source current-world phase time drift at {index}")

        phase = load_json(source_root / f"phase_{index:02d}_mesh.json")
        if len(phase.get("vertices", [])) != VERTICES or len(phase.get("triangles", [])) != TRIANGLES:
            raise ValueError(f"compact-east phase topology count drift at {index}")
        if phase.get("triangles") != neutral.get("triangles") or phase.get("regions") != neutral.get("regions"):
            raise ValueError(f"compact-east phase topology/region identity drift at {index}")
        phase_digest = surface_tool.digest(phase)
        phase_mesh_digests.append(phase_digest)

        row = copy.deepcopy(parent_row)
        scene = row["scene"]
        before_scene = copy.deepcopy(scene)
        source = _compact(scene)
        receiver_vertices = source.get("vertices_source_xyz_m", [])
        receiver_triangles = source.get("triangles", [])
        if source.get("source_digest") != EXPECTED_SOURCE_DIGEST:
            raise ValueError(f"current-world compact-east source digest drift at {index}")
        if source.get("source_head") != EXPECTED_SOURCE_HEAD:
            raise ValueError(f"current-world compact-east source head drift at {index}")
        if source.get("mesh_digest") != EXPECTED_NEUTRAL_DIGEST:
            raise ValueError(f"current-world compact-east static neutral mesh identity drift at {index}")
        if receiver_triangles != neutral["triangles"]:
            raise ValueError(f"current-world compact-east topology differs from exact VFX source at {index}")

        residual, offset = _translated_residual(receiver_vertices, neutral["vertices"])
        max_parent_neutral_residual = max(max_parent_neutral_residual, residual)
        if residual > 1e-12:
            raise ValueError(f"current-world compact-east receiver is not an exact translated neutral source at {index}: {residual}")
        offsets.append(offset)

        translated = copy.deepcopy(receiver_vertices) if index in (0, 16) else _translate(phase["vertices"], offset)
        changed = sum(1 for before, after in zip(receiver_vertices, translated) if before != after)
        changed_vertex_counts.append(changed)
        delta = max((_distance(a, b) for a, b in zip(receiver_vertices, translated)), default=0.0)
        max_current_world_delta = max(max_current_world_delta, delta)
        ceiling = float(summary["response"]["max_displacement_ceiling_m"])
        if delta > ceiling + 1e-12:
            raise ValueError(f"current-world compact-east response exceeded source-local ceiling at phase {index}")
        if index in (0, 16) and (changed != 0 or delta > 1e-12):
            raise ValueError("compact-east neutral endpoints must remain exact")
        if index not in (0, 16) and changed <= 0:
            raise ValueError(f"compact-east interior source phase {index} became a receiver no-op")

        source["vertices_source_xyz_m"] = translated
        source["mesh_digest"] = phase_digest
        source["environment_compact_east_visual_response_receiving"] = {
            "schema": RECEIVING_SCHEMA,
            "vfx_head": NATURE_VFX_HEAD,
            "source_result": SOURCE_RESULT,
            "source_phase_index": index,
            "source_time_s": expected_time,
            "receiver_world_translation_m": offset,
            "changed_vertex_count": changed,
            "maximum_added_vertex_displacement_m": delta,
            "max_displacement_ceiling_m": ceiling,
            "weather_head": EXPECTED_WEATHER_HEAD,
            "weather_semantics": EXPECTED_WEATHER_SEMANTICS,
            "authority": "MAP_RECEIVING_COMPOSITION_ONLY",
        }
        scene["scene_digest"] = surface_tool.scene_digest(scene)

        restored = copy.deepcopy(scene)
        restored_source = _compact(restored)
        restored_source["vertices_source_xyz_m"] = copy.deepcopy(_compact(before_scene)["vertices_source_xyz_m"])
        restored_source["mesh_digest"] = _compact(before_scene)["mesh_digest"]
        restored_source.pop("environment_compact_east_visual_response_receiving", None)
        restored["scene_digest"] = before_scene.get("scene_digest")
        if restored != before_scene:
            raise ValueError(f"non-compact-east current-world scene data drifted at phase {index}")
        out_states.append(row)

    first_offset = offsets[0]
    if any(max(abs(a-b) for a,b in zip(first_offset, other)) > 1e-12 for other in offsets[1:]):
        raise ValueError("compact-east world translation drifted across response phases")
    if [row.get("weather_field_digest") for row in out_states] != preserved_weather:
        raise ValueError("Weather sequence drifted during compact-east receiving build")
    if [row.get("sapling_mesh_digest") for row in out_states] != preserved_sapling:
        raise ValueError("accepted west-sapling leaf-flutter sequence drifted during compact-east receiving build")

    checks = dict(parent.get("checks", {}))
    checks.update({
        "exact_accepted_leaf_flutter_parent_bound": True,
        "exact_compact_east_vfx_source_head_bound": True,
        "compact_east_parent_matches_exact_neutral_up_to_translation": max_parent_neutral_residual <= 1e-12,
        "all_17_compact_east_source_phases_received": len(out_states) == 17,
        "compact_east_neutral_start_and_return_exact": changed_vertex_counts[0] == 0 and changed_vertex_counts[-1] == 0,
        "compact_east_all_15_interior_phases_nonzero": all(value > 0 for value in changed_vertex_counts[1:-1]),
        "compact_east_source_local_displacement_ceiling_preserved": max_current_world_delta <= 0.135 + 1e-12,
        "weather_sequence_preserved": True,
        "accepted_west_sapling_leaf_flutter_sequence_preserved": True,
        "building_object_rear_nature_path_camera_lighting_preserved": True,
    })
    if not all(checks.values()):
        raise ValueError(f"compact-east current-world structure checks failed: {checks}")

    result = copy.deepcopy(parent)
    result.update({
        "environment_head": environment_head,
        "compact_east_visual_response_parent_environment_head": PARENT_HEAD,
        "compact_east_visual_response_parent_composition_digest": parent.get("composition_digest"),
        "compact_east_visual_response_vfx_head": NATURE_VFX_HEAD,
        "compact_east_visual_response_source_result": SOURCE_RESULT,
        "compact_east_visual_response_structure_result": STRUCTURE_RESULT,
        "compact_east_visual_response_receiver_world_translation_m": first_offset,
        "compact_east_visual_response_maximum_parent_neutral_residual_m": max_parent_neutral_residual,
        "compact_east_visual_response_maximum_current_world_vertex_delta_m": max_current_world_delta,
        "compact_east_visual_response_changed_vertex_counts": changed_vertex_counts,
        "compact_east_visual_response_phase_mesh_digests": phase_mesh_digests,
        "compact_east_visual_response_weather_semantics": EXPECTED_WEATHER_SEMANTICS,
        "states": out_states,
        "checks": checks,
        "truth_boundary": (
            "Map VFX receives only Nature VFX PR #11's exact compact-east 17-state bounded visual-response candidate into the exact accepted current-world Nature leaf-flutter receiver. "
            "Weather seed/layout/presentation, the west-sapling leaf-flutter sequence, Building, Object, rear Nature, route, cameras, lighting and source-owned topology/material roles remain unchanged. "
            "This is visual receiving evidence only; physical wind/biomechanics, continuous wall-clock playback, target-device performance, gameplay/physics and final Art/Visual-QA preference remain separate gates."
        ),
        "non_claims": [
            "PHYSICAL_WIND_SPEED_FORCE_OR_BIOMECHANICS",
            "CONTINUOUS_WALL_CLOCK_PLAYBACK_OR_INTERPOLATION",
            "TARGET_DEVICE_PERFORMANCE",
            "FINAL_MATERIALS_LEAF_SIDEDNESS_OR_LOOKDEV",
            "GAMEPLAY_COLLISION_NAVIGATION_OR_DAMAGE",
            "FINAL_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE",
            "CANON_OR_PRODUCTION_READINESS",
        ],
    })
    result["composition_digest"] = surface_tool.digest({
        "parent": parent.get("composition_digest"),
        "compact_east_vfx_head": NATURE_VFX_HEAD,
        "phase_mesh_digests": phase_mesh_digests,
        "scenes": [row["scene"]["scene_digest"] for row in out_states],
    })
    _validate_receiving_payload(result, environment_head)

    wrong = copy.deepcopy(result)
    _compact(wrong["states"][8]["scene"])["environment_compact_east_visual_response_receiving"]["weather_semantics"] = "PHYSICAL_WIND_SPEED"
    rejected = False
    try:
        _validate_receiving_payload(wrong, environment_head)
    except ValueError:
        rejected = True
    if not rejected:
        raise ValueError("deliberate physical Weather semantic promotion was not rejected")
    result["negative_controls"] = {"physical_weather_semantic_promotion_rejected": True}
    return result


def _png_files(root: Path) -> dict[str, Path]:
    return {path.name: path for path in sorted((root / "rendered").glob("*.png"))}


def _changed_pixels(a: Path, b: Path) -> tuple[int, list[int] | None, int]:
    from PIL import Image, ImageChops
    with Image.open(a).convert("RGB") as left, Image.open(b).convert("RGB") as right:
        if left.size != right.size:
            raise ValueError(f"frame size drift: {a.name}")
        diff = ImageChops.difference(left, right)
        bbox = diff.getbbox()
        if bbox is None:
            return 0, None, left.size[0] * left.size[1]
        count = sum(1 for pixel in diff.getdata() if pixel != (0, 0, 0))
        return count, [int(v) for v in bbox], left.size[0] * left.size[1]


def _frame_identity(name: str) -> tuple[str, str, int]:
    prefix = "atmosphere-width-"
    if not name.startswith(prefix) or not name.endswith(".png"):
        raise ValueError(f"unexpected target-host frame name: {name}")
    stem = name[len(prefix):-4]
    try:
        mode, remainder = stem.split("-", 1)
        context, phase_text = remainder.rsplit("-", 1)
        phase = int(phase_text)
    except Exception as exc:
        raise ValueError(f"unexpected target-host frame name: {name}") from exc
    if mode not in {"control", "candidate"}:
        raise ValueError(f"unexpected target-host Weather mode: {name}")
    if context not in {"path_eye", "elevated_oblique"}:
        raise ValueError(f"unexpected target-host camera context: {name}")
    if phase < 0 or phase > 16:
        raise ValueError(f"unexpected target-host source phase: {name}")
    return mode, context, phase


def verify(payload: dict[str, Any], parent_root: Path, candidate_root: Path, environment_head: str) -> dict[str, Any]:
    _validate_receiving_payload(payload, environment_head)
    parent_runtime = load_json(parent_root / "runtime.json")
    runtime = load_json(candidate_root / "runtime.json")
    if runtime.get("environment_compact_east_visual_response_vfx_head") != NATURE_VFX_HEAD:
        raise ValueError("Godot receipt compact-east VFX head drift")
    if runtime.get("environment_compact_east_visual_response_structure_result") != STRUCTURE_RESULT:
        raise ValueError("Godot receipt compact-east structure result drift")
    if runtime.get("environment_compact_east_visual_response_receiving_schema") != RECEIVING_SCHEMA:
        raise ValueError("Godot receipt compact-east receiving schema drift")
    if int(runtime.get("environment_compact_east_visual_response_phase_count", -1)) != 17:
        raise ValueError("Godot receipt compact-east phase count drift")
    samples = runtime.get("samples", [])
    if not isinstance(samples, list) or len(samples) != 17:
        raise ValueError("Godot receipt must retain exact 17 samples")

    expected_digests = payload["compact_east_visual_response_phase_mesh_digests"]
    runtime_digests: list[str] = []
    for index, sample in enumerate(samples):
        rows = [row for row in sample.get("static_source_meshes", []) if row.get("asset_id") == ASSET_ID]
        if len(rows) != 1:
            raise ValueError(f"Godot runtime compact-east source count drift at {index}")
        source = rows[0]
        if int(source.get("compact_east_visual_response_phase_index", -1)) != index:
            raise ValueError(f"Godot runtime compact-east phase identity drift at {index}")
        if source.get("compact_east_visual_response_vfx_head") != NATURE_VFX_HEAD:
            raise ValueError(f"Godot runtime compact-east VFX identity drift at {index}")
        runtime_digests.append(str(source.get("mesh_digest", "")))
    if runtime_digests != expected_digests:
        raise ValueError("Godot runtime compact-east mesh digest sequence differs from canonical payload")

    parent_frames = _png_files(parent_root)
    candidate_frames = _png_files(candidate_root)
    if len(parent_frames) != 68 or set(parent_frames) != set(candidate_frames):
        raise ValueError("expected exact 68 matched parent/candidate target-host frames")

    contexts = ("path_eye", "elevated_oblique")
    modes = ("control", "candidate")
    frame_rows: list[dict[str, Any]] = []
    neutral_changed = 0
    interior_changed_frames = 0
    max_changed_fraction = 0.0
    visible: dict[str, dict[str, set[int]]] = {
        context: {mode: set() for mode in modes} for context in contexts
    }
    for name in sorted(parent_frames):
        mode, context, phase = _frame_identity(name)
        changed, bbox, total = _changed_pixels(parent_frames[name], candidate_frames[name])
        fraction = changed / total if total else 0.0
        max_changed_fraction = max(max_changed_fraction, fraction)
        if phase in (0, 16):
            neutral_changed += changed
        elif changed > 0:
            interior_changed_frames += 1
            visible[context][mode].add(phase)
        frame_rows.append({
            "frame": name,
            "mode": mode,
            "context": context,
            "phase": phase,
            "changed_pixels": changed,
            "changed_fraction": fraction,
            "bbox": bbox,
        })
    if neutral_changed != 0:
        raise ValueError("compact-east neutral endpoint target-host frames changed")

    interior_phases = set(range(1, 16))
    fully_observing_contexts = [
        context for context in contexts
        if all(visible[context][mode] == interior_phases for mode in modes)
    ]
    non_observing_contexts = [
        context for context in contexts
        if all(not visible[context][mode] for mode in modes)
    ]
    partial_contexts = [
        context for context in contexts
        if context not in fully_observing_contexts and context not in non_observing_contexts
    ]
    if not fully_observing_contexts:
        raise ValueError("no retained current-world camera shows all 15 compact-east interior phases in both Weather review modes")
    if partial_contexts:
        raise ValueError(f"compact-east visibility is only partial in retained contexts: {partial_contexts}")
    covered_phases = set().union(*(
        visible[context][mode] for context in fully_observing_contexts for mode in modes
    ))
    if covered_phases != interior_phases:
        raise ValueError("not every compact-east interior source phase is visually evidenced in an observing context")

    parent_samples = parent_runtime.get("samples", [])
    if len(parent_samples) != 17:
        raise ValueError("accepted parent runtime sample count drift")
    preserved_non_compact = True
    for index, (before, after) in enumerate(zip(parent_samples, samples)):
        def stripped(sample: dict[str, Any]) -> list[dict[str, Any]]:
            return [row for row in sample.get("static_source_meshes", []) if row.get("asset_id") != ASSET_ID]
        if stripped(before) != stripped(after):
            preserved_non_compact = False
            raise ValueError(f"non-compact static source runtime identity drift at phase {index}")
        if before.get("weather_field_digest") != after.get("weather_field_digest"):
            raise ValueError(f"Weather runtime digest drift at phase {index}")
        if before.get("sapling_mesh_digest") != after.get("sapling_mesh_digest"):
            raise ValueError(f"west-sapling runtime digest drift at phase {index}")

    visibility_by_context = {
        context: {
            mode: sorted(visible[context][mode]) for mode in modes
        } for context in contexts
    }
    expected_visible_frame_count = 15 * len(modes) * len(fully_observing_contexts)
    checks = {
        "exact_68_target_host_frames_matched": len(frame_rows) == 68,
        "neutral_endpoint_frames_pixel_exact": neutral_changed == 0,
        "at_least_one_context_fully_observes_all_15_interior_phases_in_both_weather_modes": bool(fully_observing_contexts),
        "interior_changed_frame_count_matches_observing_contexts": interior_changed_frames == expected_visible_frame_count,
        "non_observing_contexts_remain_pixel_exact_to_parent": all(
            not visible[context][mode] for context in non_observing_contexts for mode in modes
        ),
        "runtime_compact_east_mesh_sequence_matches_canonical": runtime_digests == expected_digests,
        "runtime_non_compact_static_sources_preserved": preserved_non_compact,
        "visual_change_not_promoted_to_physical_or_gameplay_claim": True,
    }
    if not all(checks.values()):
        raise ValueError(f"compact-east target-host checks failed: {checks}")
    return {
        "schema": "axm.environment-compact-east-visual-response-target-host-report/v0.2",
        "state": TARGET_RESULT,
        "environment_head": environment_head,
        "parent_environment_head": PARENT_HEAD,
        "nature_vfx_head": NATURE_VFX_HEAD,
        "matched_frames": len(frame_rows),
        "neutral_endpoint_changed_pixels": neutral_changed,
        "interior_changed_frames": interior_changed_frames,
        "fully_observing_contexts": fully_observing_contexts,
        "non_observing_contexts": non_observing_contexts,
        "partial_contexts": partial_contexts,
        "visibility_by_context": visibility_by_context,
        "maximum_changed_frame_fraction": max_changed_fraction,
        "frame_differences": frame_rows,
        "checks": checks,
        "truth_boundary": (
            "Exact current-world A/B receiving evidence for one compact-east Nature visual-response candidate. Runtime phase identity and all 15 interior source states are visually demonstrated in at least one retained fixed camera and in both inherited Weather review modes; neutral endpoints and unrelated runtime identities remain fixed. A retained camera with zero pixel delta is explicitly reported as non-observing rather than being treated as failed motion or fabricated visibility. Pixel deltas do not establish natural-looking motion, physical wind, gameplay/physics, wall-clock timing, target-device performance or final Art/Visual-QA acceptance."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--parent", required=True)
    b.add_argument("--source-root", required=True)
    b.add_argument("--environment-head", required=True)
    b.add_argument("--output", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--payload", required=True)
    v.add_argument("--parent-root", required=True)
    v.add_argument("--candidate-root", required=True)
    v.add_argument("--environment-head", required=True)
    v.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.cmd == "build":
        result = build(load_json(Path(args.parent)), Path(args.source_root), args.environment_head)
    else:
        result = verify(load_json(Path(args.payload)), Path(args.parent_root), Path(args.candidate_root), args.environment_head)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
