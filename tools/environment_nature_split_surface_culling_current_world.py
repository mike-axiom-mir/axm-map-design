from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

PARENT_HEAD = "b0fa28733d77cad79d78f29e7ef76ccb9ab0b399"
PARENT_COMPOSITION_DIGEST = "6a7c4fa18d24d739b879d0fa8ecf76eb9ec8103ada0e771b65d401afe375adfb"
PARENT_SCHEMA = "axm.environment-current-world-nature-source-winding-migration/v0.1"
PARENT_STATUS = "PASS_CURRENT_WORLD_NATURE_SOURCE_WINDING_MIGRATION_STRUCTURE"
BUILDING_POLICY_HEAD = "a976af429b0ea90e0f0cc72d4a8bd4eb8fef22d3"
NATURE_MATERIALS_HEAD = "8b2e0523d7a2b210c6404f15bafb08fbedcad4dd"
NATURE_SIDEDNESS_REVIEW_HEAD = "0b7fdfac3be4d9c25236fa8733108e7d32533657"
NATURE_SIDEDNESS_REVIEW_ARTIFACT = 10443379564
NATURE_SIDEDNESS_REVIEW_SHA256 = "2d45af990804bfb03e1d6950bb5440a57948ff6bc8b413d0b92e8462e107a514"
NATURE_VFX_HEAD = "4e5211d14286f9c292e769a78971f24d59194141"
NATURE_GEOMETRY_LEAF_HEAD = "da3adbef4de8cddb8f3ebe841d39bb31a8936f5f"
NATURE_FAMILY_ID = "nature-woody-foliage-family-001"
POLICY_SCHEMA = "axm.environment-nature-surface-culling-policy/v0.1"
POLICY_ID = "source-woody-back__source-foliage-two-sided-001"
STRUCTURE_RESULT = "PASS_CURRENT_WORLD_NATURE_SPLIT_SURFACE_CULLING_STRUCTURE"
TARGET_RESULT = "PASS_CURRENT_WORLD_NATURE_SPLIT_SURFACE_CULLING_TARGET_HOST"
EXPECTED_ASSETS = {
    "source:nature:sapling-neutral-001",
    "source:nature:compact-east-tree-neutral-001",
    "source:nature:east-rear-tree-neutral-001",
}


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def scene_digest(scene: dict[str, Any]) -> str:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    return digest(value)


def _nature_sources(scene: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    sapling = scene.get("sapling", {})
    if isinstance(sapling, dict):
        asset_id = str(sapling.get("asset_id", ""))
        if asset_id in EXPECTED_ASSETS:
            rows[asset_id] = sapling
    for item in scene.get("additional_source_meshes", []):
        if not isinstance(item, dict):
            continue
        asset_id = str(item.get("asset_id", ""))
        if asset_id in EXPECTED_ASSETS:
            rows[asset_id] = item
    if set(rows) != EXPECTED_ASSETS:
        raise ValueError(f"current-world Nature source set drift: {sorted(rows)}")
    return rows


def _source_identity(source: dict[str, Any]) -> str:
    value = copy.deepcopy(source)
    value.pop("environment_nature_surface_culling_policy", None)
    return digest(value)


def validate_parent(parent: dict[str, Any]) -> None:
    if parent.get("schema") != PARENT_SCHEMA or parent.get("status") != PARENT_STATUS:
        raise ValueError("exact current-world parent must retain Nature-migration PASS schema/state")
    if parent.get("environment_head") != PARENT_HEAD:
        raise ValueError("exact current-world parent head drift")
    if parent.get("composition_digest") != PARENT_COMPOSITION_DIGEST:
        raise ValueError("exact current-world parent composition drift")
    if parent.get("building_current_source_policy_head") != BUILDING_POLICY_HEAD:
        raise ValueError("Building current-source policy identity drift")
    if parent.get("nature_materials_head") != NATURE_MATERIALS_HEAD:
        raise ValueError("Nature material-family head drift")
    family = parent.get("nature_material_family", {})
    if not isinstance(family, dict) or family.get("family_id") != NATURE_FAMILY_ID:
        raise ValueError("Nature woody/foliage family identity drift")
    states = parent.get("states", [])
    if len(states) != 17:
        raise ValueError("current-world parent must retain exactly 17 states")
    for row in states:
        if not isinstance(row, dict) or not isinstance(row.get("scene"), dict):
            raise ValueError("current-world state/scene shape drift")
        sources = _nature_sources(row["scene"])
        for asset_id, source in sources.items():
            if len(source.get("vertices_source_xyz_m", [])) != 390 or len(source.get("triangles", [])) != 570:
                raise ValueError(f"{asset_id}: current Nature source count drift")
            proof = source.get("nature_material_family_receiving", {})
            if not isinstance(proof, dict):
                raise ValueError(f"{asset_id}: Nature material-family proof missing")
            if proof.get("family_id") != NATURE_FAMILY_ID or proof.get("materials_head") != NATURE_MATERIALS_HEAD:
                raise ValueError(f"{asset_id}: Nature material-family proof identity drift")
            partition = proof.get("surface_triangle_indices", {})
            if not isinstance(partition, dict):
                raise ValueError(f"{asset_id}: Nature surface partition missing")
            woody = partition.get("woody", [])
            foliage = partition.get("foliage", [])
            if len(woody) != 520 or len(foliage) != 50:
                raise ValueError(f"{asset_id}: Nature woody/foliage partition drift")
            if set(woody).intersection(foliage) or len(woody) + len(foliage) != 570:
                raise ValueError(f"{asset_id}: Nature surface partition no longer covers exact mesh")


def policy_payload() -> dict[str, Any]:
    return {
        "schema": POLICY_SCHEMA,
        "policy_id": POLICY_ID,
        "woody_surface_cull": "CULL_BACK",
        "foliage_surface_cull": "CULL_DISABLED",
        "geometry_strategy": "PRESERVE_CURRENT_390V_570T_SOURCE_GEOMETRY",
        "explicit_leaf_backface_geometry_adopted": False,
        "nature_materials_head": NATURE_MATERIALS_HEAD,
        "sidedness_review_head": NATURE_SIDEDNESS_REVIEW_HEAD,
        "sidedness_review_artifact_id": NATURE_SIDEDNESS_REVIEW_ARTIFACT,
        "sidedness_review_archive_sha256": NATURE_SIDEDNESS_REVIEW_SHA256,
        "vfx_dynamic_leaf_review_head": NATURE_VFX_HEAD,
        "geometry_leaf_candidate_head": NATURE_GEOMETRY_LEAF_HEAD,
        "authority": "MAP_RECEIVING_COMPOSITION_ONLY",
        "truth_boundary": (
            "Environment preserves the exact current Nature geometry, source winding, woody/foliage scalar PBR family and dynamic sapling vertices, "
            "and changes only target-host culling by existing material role: woody is backface culled while foliage remains two-sided. "
            "The historical explicit-backface candidate remains review evidence and is not adopted. Final appearance, runtime value and source policy remain owner decisions."
        ),
    }


def validate_policy(policy: dict[str, Any]) -> None:
    expected = policy_payload()
    for key in (
        "schema", "policy_id", "woody_surface_cull", "foliage_surface_cull",
        "geometry_strategy", "explicit_leaf_backface_geometry_adopted",
        "nature_materials_head", "sidedness_review_head",
        "vfx_dynamic_leaf_review_head", "geometry_leaf_candidate_head",
    ):
        if policy.get(key) != expected[key]:
            raise ValueError(f"Nature surface-culling policy drift: {key}")
    if policy["woody_surface_cull"] == policy["foliage_surface_cull"]:
        raise ValueError("split Nature surface-culling policy collapsed to one whole-mesh mode")


def build(parent: dict[str, Any], environment_head: str) -> dict[str, Any]:
    validate_parent(parent)
    policy = policy_payload()
    validate_policy(policy)
    states: list[dict[str, Any]] = []
    parent_scene_digests: list[str] = []
    candidate_scene_digests: list[str] = []
    source_identity_checks: list[dict[str, str]] = []
    parent_weather = [row.get("weather_field_digest") for row in parent["states"]]

    for parent_row in parent["states"]:
        row = copy.deepcopy(parent_row)
        original_scene = copy.deepcopy(parent_row["scene"])
        scene = row["scene"]
        before_sources = _nature_sources(original_scene)
        after_sources = _nature_sources(scene)
        before_ids = {asset: _source_identity(source) for asset, source in before_sources.items()}
        after_ids = {asset: _source_identity(source) for asset, source in after_sources.items()}
        if before_ids != after_ids:
            raise ValueError("Nature source bytes drifted before policy annotation")
        parent_scene_digests.append(str(original_scene.get("scene_digest", "")))
        scene["environment_nature_surface_culling_policy"] = copy.deepcopy(policy)
        scene["scene_digest"] = scene_digest(scene)
        candidate_scene_digests.append(scene["scene_digest"])
        source_identity_checks.append(before_ids)
        states.append(row)
        stripped = copy.deepcopy(scene)
        stripped.pop("environment_nature_surface_culling_policy", None)
        stripped["scene_digest"] = original_scene.get("scene_digest")
        if stripped != original_scene:
            raise ValueError("non-policy current-world scene data drifted")

    if [row.get("weather_field_digest") for row in states] != parent_weather:
        raise ValueError("Weather sequence drifted during Nature culling-policy receiving build")

    checks = dict(parent.get("checks", {}))
    checks.update({
        "exact_parent_current_world_bound": True,
        "exact_nature_material_family_bound": True,
        "exact_material_side_sidedness_review_bound_as_context_only": True,
        "exact_current_vfx_dynamic_leaf_review_bound_as_context_only": True,
        "explicit_leaf_backface_geometry_not_adopted": True,
        "all_three_nature_sources_remain_390v_570t": True,
        "all_three_nature_source_payloads_unchanged": True,
        "woody_surface_cull_is_back": policy["woody_surface_cull"] == "CULL_BACK",
        "foliage_surface_cull_is_two_sided": policy["foliage_surface_cull"] == "CULL_DISABLED",
        "all_17_states_preserved": len(states) == 17,
        "weather_building_object_dressing_path_camera_lighting_preserved": True,
    })
    if not all(checks.values()):
        raise ValueError(f"Nature split surface-culling structure checks failed: {checks}")

    result = copy.deepcopy(parent)
    result.update({
        "environment_head": environment_head,
        "nature_surface_culling_parent_environment_head": PARENT_HEAD,
        "nature_surface_culling_parent_composition_digest": PARENT_COMPOSITION_DIGEST,
        "nature_surface_culling_policy": policy,
        "nature_surface_culling_structure_result": STRUCTURE_RESULT,
        "checks": checks,
        "states": states,
        "nature_surface_culling_parent_scene_digests": parent_scene_digests,
        "nature_surface_culling_scene_digests": candidate_scene_digests,
        "nature_surface_source_identity_checks": source_identity_checks,
        "truth_boundary": (
            "This structural PASS changes no world geometry, placement, material scalar/color value, Nature animation vertex, Building, Object, footprint dressing, Weather, route, camera or lighting input. "
            "It only binds a current-world target-host review policy to the already-separated Nature material roles: woody CULL_BACK and foliage CULL_DISABLED. "
            "Target-host rendering and final visual preference remain separate gates."
        ),
        "non_claims": [
            "FINAL_NATURE_VISUAL_ACCEPTANCE", "SOURCE_LEVEL_SIDEDNESS_POLICY_ADOPTION",
            "EXPLICIT_LEAF_BACKFACE_GEOMETRY_REJECTION_OUTSIDE_THIS_REVIEW",
            "NORMAL_TANGENT_UV_TEXTURE_TRANSLUCENCY_OR_SUBSURFACE_ACCEPTANCE",
            "TARGET_DEVICE_PERFORMANCE", "PHYSICAL_WIND_OR_BOTANICAL_CORRECTNESS",
            "COLLISION_NAVIGATION_OR_GAMEPLAY", "CANON_PRODUCTION_READY_OR_ENVIRONMENT_MASTERY",
        ],
    })
    result["composition_digest"] = digest({
        "parent": PARENT_COMPOSITION_DIGEST,
        "policy": policy,
        "scene_digests": candidate_scene_digests,
    })

    controls: dict[str, str] = {}
    bad_same_mode = copy.deepcopy(policy)
    bad_same_mode["foliage_surface_cull"] = "CULL_BACK"
    try:
        validate_policy(bad_same_mode)
    except ValueError as exc:
        controls["whole_mesh_backface_cull_cannot_masquerade_as_split_policy"] = f"REJECTED:{exc}"
    else:
        raise ValueError("whole-mesh culling negative control did not fail closed")
    bad_geometry = copy.deepcopy(policy)
    bad_geometry["explicit_leaf_backface_geometry_adopted"] = True
    try:
        validate_policy(bad_geometry)
    except ValueError as exc:
        controls["explicit_leaf_geometry_cannot_be_silently_adopted"] = f"REJECTED:{exc}"
    else:
        raise ValueError("explicit leaf-geometry adoption negative control did not fail closed")
    result["negative_controls"] = {**parent.get("negative_controls", {}), **controls}
    return result


def frame_files(root: Path) -> list[Path]:
    return sorted((root / "rendered").glob("atmosphere-width-*.png"))


def runtime_counters(runtime: dict[str, Any]) -> dict[str, dict[str, dict[str, int]]]:
    out: dict[str, dict[str, dict[str, int]]] = {}
    for sample in runtime.get("samples", []):
        idx = f"{int(sample['index']):02d}"
        out[idx] = {}
        for camera, context in sample.get("contexts", {}).items():
            out[idx][camera] = {}
            for mode in ("control", "candidate"):
                r = context[mode]["runtime"]
                out[idx][camera][mode] = {
                    "draw_calls_in_frame": int(r["draw_calls_in_frame"]),
                    "objects_in_frame": int(r["objects_in_frame"]),
                    "primitives_in_frame": int(r["primitives_in_frame"]),
                    "buffer_mem_bytes": int(r["buffer_mem_bytes"]),
                    "texture_mem_bytes": int(r["texture_mem_bytes"]),
                }
    return out


def _frame_delta(a: Path, b: Path) -> dict[str, Any]:
    from PIL import Image, ImageChops
    ia = Image.open(a).convert("RGB")
    ib = Image.open(b).convert("RGB")
    if ia.size != ib.size:
        raise ValueError(f"frame size drift: {a.name}")
    diff = ImageChops.difference(ia, ib)
    bbox = diff.getbbox()
    extrema = diff.getextrema()
    maximum = max(channel[1] for channel in extrema)
    masks = [channel.point(lambda value: 255 if value else 0) for channel in diff.split()]
    changed_mask = ImageChops.lighter(ImageChops.lighter(masks[0], masks[1]), masks[2])
    changed = changed_mask.histogram()[255]
    total = ia.size[0] * ia.size[1]
    return {
        "file": a.name,
        "width": ia.size[0], "height": ia.size[1],
        "changed_pixels": changed,
        "changed_fraction": changed / total,
        "bbox": list(bbox) if bbox is not None else None,
        "max_channel_delta_8bit": maximum,
    }


def _camera_name(filename: str) -> str:
    if "path_eye" in filename:
        return "path_eye"
    if "elevated_oblique" in filename:
        return "elevated_oblique"
    return "unknown"


def verify(payload: dict[str, Any], parent_root: Path, candidate_root: Path, environment_head: str) -> dict[str, Any]:
    if payload.get("environment_head") != environment_head:
        raise ValueError("Nature split-culling payload head drift")
    if payload.get("nature_surface_culling_parent_environment_head") != PARENT_HEAD:
        raise ValueError("Nature split-culling parent head drift")
    if payload.get("nature_surface_culling_structure_result") != STRUCTURE_RESULT:
        raise ValueError("Nature split-culling structural result missing")
    validate_policy(payload.get("nature_surface_culling_policy", {}))
    if not all(payload.get("checks", {}).values()):
        raise ValueError("Nature split-culling payload checks are not all true")

    parent_frames = frame_files(parent_root)
    candidate_frames = frame_files(candidate_root)
    if len(parent_frames) != 68 or [p.name for p in parent_frames] != [p.name for p in candidate_frames]:
        raise ValueError("expected 68 matched current-world frames")
    deltas = [_frame_delta(a, b) for a, b in zip(parent_frames, candidate_frames)]
    changed_frames = [row for row in deltas if row["changed_pixels"] > 0]
    if not changed_frames:
        raise ValueError("split Nature surface-culling policy was a complete visual no-op in retained current-world views")

    parent_runtime = load_json(parent_root / "runtime.json")
    candidate_runtime = load_json(candidate_root / "runtime.json")
    if runtime_counters(parent_runtime) != runtime_counters(candidate_runtime):
        raise ValueError("split Nature culling policy changed proof-host submission/memory counters")
    if candidate_runtime.get("environment_nature_surface_culling_policy_id") != POLICY_ID:
        raise ValueError("target-host receipt missing exact Nature surface-culling policy identity")
    if candidate_runtime.get("environment_nature_woody_surface_cull") != "CULL_BACK":
        raise ValueError("target-host woody culling receipt drift")
    if candidate_runtime.get("environment_nature_foliage_surface_cull") != "CULL_DISABLED":
        raise ValueError("target-host foliage culling receipt drift")

    weather_measurements = 0
    max_width_residual = 0.0
    for sample in candidate_runtime.get("samples", []):
        for context in sample.get("contexts", {}).values():
            weather = context["candidate"]["weather_update"]
            weather_measurements += int(weather.get("measured_width_count", 0))
            max_width_residual = max(max_width_residual, float(weather.get("maximum_projected_width_residual_px", 0.0)))
    if weather_measurements != 1224 or max_width_residual > 0.05:
        raise ValueError("inherited Weather-width evidence drift")

    grouped: dict[str, dict[str, Any]] = {}
    for camera in ("path_eye", "elevated_oblique", "unknown"):
        rows = [row for row in deltas if _camera_name(row["file"]) == camera]
        if not rows:
            continue
        grouped[camera] = {
            "frame_count": len(rows),
            "changed_frame_count": sum(1 for row in rows if row["changed_pixels"] > 0),
            "minimum_changed_pixels": min(row["changed_pixels"] for row in rows),
            "maximum_changed_pixels": max(row["changed_pixels"] for row in rows),
            "minimum_changed_fraction": min(row["changed_fraction"] for row in rows),
            "maximum_changed_fraction": max(row["changed_fraction"] for row in rows),
            "maximum_channel_delta_8bit": max(row["max_channel_delta_8bit"] for row in rows),
            "distinct_bboxes": sorted({str(row["bbox"]) for row in rows}),
        }

    report = {
        "schema": "axm.environment-nature-split-surface-culling-report/v0.1",
        "state": TARGET_RESULT,
        "environment_head": environment_head,
        "parent_environment_head": PARENT_HEAD,
        "composition_digest": payload["composition_digest"],
        "policy": copy.deepcopy(payload["nature_surface_culling_policy"]),
        "matched_frames": 68,
        "changed_frames": len(changed_frames),
        "frame_delta_summary": grouped,
        "frame_deltas": deltas,
        "weather_width_measurements": weather_measurements,
        "maximum_weather_width_residual_px": max_width_residual,
        "runtime_counter_deltas": {
            "draw_calls_in_frame": 0, "objects_in_frame": 0, "primitives_in_frame": 0,
            "buffer_mem_bytes": 0, "texture_mem_bytes": 0,
        },
        "checks": {
            "exact_parent_current_world_reused": True,
            "exact_material_role_split_policy_bound": True,
            "explicit_leaf_backface_geometry_not_adopted": True,
            "all_68_real_scene_frames_compared": True,
            "policy_has_renderer_visible_effect": len(changed_frames) > 0,
            "proof_host_submission_and_memory_counters_unchanged": True,
            "all_1224_weather_width_measurements_preserved": True,
            "final_visual_preference_not_auto_accepted": True,
        },
        "truth_boundary": (
            "PASS proves only that the exact role-split Nature culling policy can be received by the full current-world Godot proof while preserving source geometry, dynamic state, Weather width and proof-host submission/memory counters. "
            "Pixel deltas are retained for Art Direction/Visual QA review; this report does not label them aesthetically better or production-ready."
        ),
    }
    if not all(report["checks"].values()):
        raise ValueError(f"Nature split-culling target-host checks failed: {report['checks']}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build")
    p_build.add_argument("--parent", type=Path, required=True)
    p_build.add_argument("--environment-head", required=True)
    p_build.add_argument("--output", type=Path, required=True)
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--payload", type=Path, required=True)
    p_verify.add_argument("--parent-root", type=Path, required=True)
    p_verify.add_argument("--candidate-root", type=Path, required=True)
    p_verify.add_argument("--environment-head", required=True)
    p_verify.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        result = build(load_json(args.parent), args.environment_head)
    else:
        result = verify(load_json(args.payload), args.parent_root, args.candidate_root, args.environment_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
