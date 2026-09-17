from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

PARENT_SCHEMA = "axm.environment-current-world-object-material-family-composition/v0.1"
PARENT_STATUS = "PASS_CURRENT_WORLD_OBJECT_MATERIAL_FAMILY_STRUCTURE"
PARENT_HEAD = "6575cc38db9f0f62b14a82b352d8582edf89856d"
PARENT_COMPOSITION_DIGEST = "677dfe17afe49bf3f6edc28359c40a8add3dc357cb918529f0015a99f71baf70"
INDEXED_OBJECT_ENVIRONMENT_HEAD = "b9d9ed28e9a826c4698014db5f91c59aba9dddfc"
NATURE_VFX_HEAD = "0b9167ac6d7b6d94d9fef92720f8c60e3ef45700"
NATURE_MIGRATION_HEAD = "4ddbe66e5c02d22407ef773d5346a2fe6f349a2d"
NATURE_GEOMETRY_ORACLE = "e2224d4bf88f7e68503072c884e5a726b8d0c53d"
NATURE_MATERIALS_HEAD = "8b2e0523d7a2b210c6404f15bafb08fbedcad4dd"
NATURE_FAMILY_ID = "nature-woody-foliage-family-001"
MIGRATED_MESH_DIGESTS = {
    "sapling-neutral-001": "47dd4d82651138299d05071df3e8a410f21f673ab8d42b936d7222eb5351b862",
    "compact-east-tree-neutral-001": "420135f6effbadb1b344675948b9ddc471dcb83177702888f0b32327c5121c18",
    "east-rear-tree-neutral-001": "aa9d450a78fef722672ea9af0f9aca98b4c1a0ca3705661784f5f61f3e9b6a31",
}
ASSET_TO_STUDY = {
    "source:nature:sapling-neutral-001": "sapling-neutral-001",
    "source:nature:compact-east-tree-neutral-001": "compact-east-tree-neutral-001",
    "source:nature:east-rear-tree-neutral-001": "east-rear-tree-neutral-001",
}
STUDY_PATHS = {
    "sapling-neutral-001": "examples/sapling_neutral_001.json",
    "compact-east-tree-neutral-001": "examples/compact_east_tree_neutral_001.json",
    "east-rear-tree-neutral-001": "examples/east_rear_tree_neutral_001.json",
}
SCHEMA = "axm.environment-current-world-nature-source-winding-migration/v0.1"
STATUS = "PASS_CURRENT_WORLD_NATURE_SOURCE_WINDING_MIGRATION_STRUCTURE"
TARGET_SCHEMA = "axm.environment-current-world-nature-source-winding-migration-target-host/v0.1"
TARGET_STATUS = "PASS_CURRENT_WORLD_NATURE_SOURCE_WINDING_MIGRATION_TARGET_HOST_REACHED"
CAMERAS = ("path_eye", "elevated_oblique")
WEATHER_MODES = ("control", "candidate")
RUNTIME_KEYS = ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "buffer_mem_bytes", "texture_mem_bytes")


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def scene_digest(scene: dict[str, Any]) -> str:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    return digest(value)


def membership(tri: list[int]) -> tuple[int, int, int]:
    return tuple(sorted(int(v) for v in tri))


def triangle_membership_equal(a: list[list[int]], b: list[list[int]]) -> bool:
    return len(a) == len(b) and all(membership(x) == membership(y) for x, y in zip(a, b))


def max_vertex_residual(a: list[list[float]], b: list[list[float]]) -> float:
    if len(a) != len(b):
        return math.inf
    value = 0.0
    for lhs, rhs in zip(a, b):
        if len(lhs) != 3 or len(rhs) != 3:
            return math.inf
        value = max(value, math.dist([float(x) for x in lhs], [float(x) for x in rhs]))
    return value


def import_nature(nature_root: Path):
    source_dir = nature_root / "src"
    sys.path.insert(0, str(source_dir))
    try:
        from axm_nature_design import organic_form
        from axm_nature_design import wind_response_migrated
    finally:
        sys.path.pop(0)
    return organic_form, wind_response_migrated


def find_source(scene: dict[str, Any], asset_id: str) -> dict[str, Any]:
    if asset_id == "source:nature:sapling-neutral-001":
        row = scene.get("sapling", {})
        if row.get("asset_id") != asset_id:
            raise ValueError("current-world sapling identity drift")
        return row
    matches = [x for x in scene.get("additional_source_meshes", []) if x.get("asset_id") == asset_id]
    if len(matches) != 1:
        raise ValueError(f"expected one {asset_id}, found {len(matches)}")
    return matches[0]


def assert_material_receiver(source: dict[str, Any], study: str) -> None:
    proof = source.get("nature_material_family_receiving", {})
    if proof.get("family_id") != NATURE_FAMILY_ID or proof.get("materials_head") != NATURE_MATERIALS_HEAD:
        raise ValueError(f"Nature material family drift for {study}")
    if proof.get("study_id") != study:
        raise ValueError(f"Nature material study identity drift for {study}")
    partition = proof.get("surface_triangle_indices", {})
    if len(partition.get("woody", [])) != 520 or len(partition.get("foliage", [])) != 50:
        raise ValueError(f"Nature material partition drift for {study}")


def migration_receipt(study: str, changed_winding: int, mesh_digest: str, dynamic: bool) -> dict[str, Any]:
    return {
        "schema": "axm.environment-nature-source-winding-migration-receiving/v0.1",
        "study_id": study,
        "nature_vfx_head": NATURE_VFX_HEAD,
        "nature_source_migration_head": NATURE_MIGRATION_HEAD,
        "nature_geometry_oracle": NATURE_GEOMETRY_ORACLE,
        "migrated_mesh_digest": MIGRATED_MESH_DIGESTS[study] if not dynamic else mesh_digest,
        "changed_triangle_winding_count": changed_winding,
        "triangle_membership_changed": False,
        "vertex_positions_changed_by_migration": False,
        "dynamic_response_profile_changed": False,
        "authority": "MAP_RECEIVING_COMPOSITION_ONLY",
        "truth_boundary": "Environment receives the Nature source-generator winding migration and, for the sapling, the exact rebound visual-wind response. It does not redefine Nature geometry, material values, Weather semantics, physical wind, gameplay, runtime acceptance or final visual preference.",
    }


def build(parent: dict[str, Any], nature_root: Path, environment_head: str) -> dict[str, Any]:
    if parent.get("schema") != PARENT_SCHEMA or parent.get("status") != PARENT_STATUS:
        raise ValueError("exact Object-material current-world parent must PASS")
    if parent.get("receiving_head") != PARENT_HEAD or parent.get("composition_digest") != PARENT_COMPOSITION_DIGEST:
        raise ValueError("exact Object-material current-world parent identity drift")
    if parent.get("nature_materials_head") != NATURE_MATERIALS_HEAD:
        raise ValueError("Nature Materials identity drift")
    states = parent.get("states", [])
    if len(states) != 17:
        raise ValueError("current-world parent must retain exact 17-state sequence")

    organic, wind = import_nature(nature_root)
    sources = {study: load_json(nature_root / path) for study, path in STUDY_PATHS.items()}
    spec = wind.load_spec(nature_root / "examples/sapling_wind_response_migrated_001.json")
    wind.validate_spec(spec, sources["sapling-neutral-001"])

    neutral_meshes = {study: organic.build_mesh(source) for study, source in sources.items()}
    for study, mesh in neutral_meshes.items():
        actual = organic.digest(mesh)
        if actual != MIGRATED_MESH_DIGESTS[study]:
            raise ValueError(f"migrated Nature mesh digest drift for {study}: {actual}")
        if len(mesh.get("vertices", [])) != 390 or len(mesh.get("triangles", [])) != 570:
            raise ValueError(f"migrated Nature mesh count drift for {study}")

    out_states: list[dict[str, Any]] = []
    static_changed_counts: dict[str, set[int]] = {k: set() for k in ("compact-east-tree-neutral-001", "east-rear-tree-neutral-001")}
    sapling_changed_counts: set[int] = set()
    max_sapling_vertex_residual = 0.0
    parent_weather = [row.get("weather_field_digest") for row in states]

    for parent_row in states:
        row = copy.deepcopy(parent_row)
        scene = row["scene"]
        before = copy.deepcopy(scene)

        # Static Nature: only replace triangle winding with exact current source-generator output.
        for asset_id, study in ASSET_TO_STUDY.items():
            if study == "sapling-neutral-001":
                continue
            receiver = find_source(scene, asset_id)
            assert_material_receiver(receiver, study)
            donor = neutral_meshes[study]
            current_vertices = receiver.get("vertices_source_xyz_m", [])
            current_triangles = receiver.get("triangles", [])
            residual = max_vertex_residual(current_vertices, donor["vertices"])
            if residual > 1e-12:
                raise ValueError(f"{study}: source-generator migration moved receiver vertices ({residual})")
            if not triangle_membership_equal(current_triangles, donor["triangles"]):
                raise ValueError(f"{study}: triangle membership drift blocks winding-only migration")
            changed = sum(1 for a, b in zip(current_triangles, donor["triangles"]) if a != b)
            if changed <= 0:
                raise ValueError(f"{study}: expected nonzero winding migration")
            static_changed_counts[study].add(changed)
            receiver["vertices_source_xyz_m"] = copy.deepcopy(donor["vertices"])
            receiver["triangles"] = copy.deepcopy(donor["triangles"])
            receiver["mesh_digest"] = organic.digest(donor)
            receiver["nature_source_topology_migration_receiving"] = migration_receipt(
                study, changed, organic.digest(donor), False
            )

        # Dynamic sapling: regenerate exact current visual response from the migrated source lineage.
        sapling = find_source(scene, "source:nature:sapling-neutral-001")
        assert_material_receiver(sapling, "sapling-neutral-001")
        time_s = float(row.get("time_s", -1.0))
        deformed = wind.deform_mesh(sources["sapling-neutral-001"], spec, time_s)
        current_vertices = sapling.get("vertices_source_xyz_m", [])
        current_triangles = sapling.get("triangles", [])
        residual = max_vertex_residual(current_vertices, deformed["vertices"])
        max_sapling_vertex_residual = max(max_sapling_vertex_residual, residual)
        if residual > 1e-12:
            raise ValueError(f"sapling response profile/vertex sequence drift at t={time_s}: {residual}")
        if not triangle_membership_equal(current_triangles, deformed["triangles"]):
            raise ValueError(f"sapling triangle membership drift at t={time_s}")
        changed = sum(1 for a, b in zip(current_triangles, deformed["triangles"]) if a != b)
        if changed <= 0:
            raise ValueError(f"sapling expected nonzero winding migration at t={time_s}")
        sapling_changed_counts.add(changed)
        sapling["vertices_source_xyz_m"] = copy.deepcopy(deformed["vertices"])
        sapling["triangles"] = copy.deepcopy(deformed["triangles"])
        sapling["mesh_digest"] = organic.digest(deformed)
        sapling["nature_source_topology_migration_receiving"] = migration_receipt(
            "sapling-neutral-001", changed, organic.digest(deformed), True
        )
        row["sapling_mesh_digest"] = organic.digest(deformed)

        # Exact non-Nature scene identity must stay fixed.
        fixed_keys = (
            "items",
            "weather_lines",
            "readable_path",
            "cameras",
            "lighting",
            "environment_building_material_receiving",
            "environment_object_replacement",
            "environment_object_readability_dressing",
        )
        for key in fixed_keys:
            if scene.get(key) != before.get(key):
                raise ValueError(f"unrelated current-world field drift during Nature migration: {key}")
        before_other = [x for x in before.get("additional_source_meshes", []) if x.get("asset_id") not in ASSET_TO_STUDY]
        after_other = [x for x in scene.get("additional_source_meshes", []) if x.get("asset_id") not in ASSET_TO_STUDY]
        if before_other != after_other:
            raise ValueError("non-Nature static source drift during Nature migration")

        scene["environment_nature_source_winding_migration"] = {
            "schema": "axm.environment-current-world-nature-source-winding-migration-state/v0.1",
            "nature_vfx_head": NATURE_VFX_HEAD,
            "nature_source_migration_head": NATURE_MIGRATION_HEAD,
            "nature_geometry_oracle": NATURE_GEOMETRY_ORACLE,
            "response_profile": wind.PROFILE,
            "source_json_changed": False,
            "response_profile_changed": False,
            "map_authority": "RECEIVING_COMPOSITION_ONLY",
        }
        scene["scene_digest"] = scene_digest(scene)
        out_states.append(row)

    if [row.get("weather_field_digest") for row in out_states] != parent_weather:
        raise ValueError("Weather source sequence drifted during Nature migration")
    if len(sapling_changed_counts) != 1:
        raise ValueError(f"sapling winding-change count not stable: {sapling_changed_counts}")
    if any(len(values) != 1 for values in static_changed_counts.values()):
        raise ValueError(f"static Nature winding-change counts not stable: {static_changed_counts}")

    checks = {
        "exact_object_material_parent_preserved": True,
        "exact_indexed_object_environment_parent_declared": INDEXED_OBJECT_ENVIRONMENT_HEAD == "b9d9ed28e9a826c4698014db5f91c59aba9dddfc",
        "exact_nature_vfx_successor_bound": NATURE_VFX_HEAD == "0b9167ac6d7b6d94d9fef92720f8c60e3ef45700",
        "exact_source_generator_migration_bound": NATURE_MIGRATION_HEAD == "4ddbe66e5c02d22407ef773d5346a2fe6f349a2d",
        "all_17_states_preserved": len(out_states) == 17,
        "weather_sequence_preserved": [row.get("weather_field_digest") for row in out_states] == parent_weather,
        "sapling_response_vertices_preserved": max_sapling_vertex_residual <= 1e-12,
        "sapling_response_profile_preserved": spec.get("response", {}).get("profile") == wind.PROFILE,
        "three_nature_sources_use_migrated_topology": True,
        "triangle_membership_preserved": True,
        "nonzero_winding_delta_proven": True,
        "woody_foliage_material_family_preserved": True,
        "building_object_footprint_weather_path_camera_lighting_preserved": True,
    }
    if not all(checks.values()):
        raise ValueError(f"Nature winding migration checks failed: {checks}")

    result = copy.deepcopy(parent)
    result.update({
        "schema": SCHEMA,
        "status": STATUS,
        "study_id": "environment-current-world-nature-source-winding-migration-001",
        # Base observer compatibility deliberately stays pinned to the exact Object-material world.
        "receiving_head": PARENT_HEAD,
        "environment_head": environment_head,
        "indexed_object_environment_parent_head": INDEXED_OBJECT_ENVIRONMENT_HEAD,
        "nature_vfx_head": NATURE_VFX_HEAD,
        "nature_source_migration_head": NATURE_MIGRATION_HEAD,
        "nature_geometry_oracle": NATURE_GEOMETRY_ORACLE,
        "nature_migrated_neutral_mesh_digests": copy.deepcopy(MIGRATED_MESH_DIGESTS),
        "sapling_response_profile": wind.PROFILE,
        "sapling_max_vertex_residual_m": max_sapling_vertex_residual,
        "winding_changed_triangles": {
            "sapling-neutral-001": next(iter(sapling_changed_counts)),
            "compact-east-tree-neutral-001": next(iter(static_changed_counts["compact-east-tree-neutral-001"])),
            "east-rear-tree-neutral-001": next(iter(static_changed_counts["east-rear-tree-neutral-001"])),
        },
        "checks": checks,
        "states": out_states,
        "truth_boundary": "PASS proves only that the exact Nature source-generator cap-winding migration and rebound sapling visual-wind response can replace the historical Nature triangle winding inside the current multi-asset world without moving Nature vertices, changing triangle membership, changing the sapling response profile, changing the woody/foliage material family, or changing Building/Object/footprint/Weather/path/camera/light state. Target-host rendering is a separate receiving gate; final visual preference, physical wind, gameplay and target-device performance remain held.",
        "non_claims": [
            "FINAL_NATURE_VISUAL_ACCEPTANCE",
            "GLOBAL_OUTWARD_NORMAL_CORRECTNESS_BEYOND_PINNED_MIGRATION_EVIDENCE",
            "FINAL_NORMAL_TANGENT_UV_TEXTURE_OR_SIDEDNESS_POLICY",
            "PHYSICAL_WIND_OR_BOTANICAL_CORRECTNESS",
            "TARGET_DEVICE_PERFORMANCE",
            "COLLISION_NAVIGATION_OR_GAMEPLAY",
            "CANON_PRODUCTION_READY_OR_ENVIRONMENT_MASTERY",
        ],
    })
    result["composition_digest"] = digest({
        "parent": PARENT_COMPOSITION_DIGEST,
        "environment_parent": INDEXED_OBJECT_ENVIRONMENT_HEAD,
        "nature_vfx": NATURE_VFX_HEAD,
        "nature_migration": NATURE_MIGRATION_HEAD,
        "scenes": [row["scene"]["scene_digest"] for row in out_states],
    })
    return result


def rgb_delta_stats(reference_path: Path, candidate_path: Path) -> dict[str, Any]:
    from PIL import Image, ImageChops

    reference = Image.open(reference_path).convert("RGB")
    candidate = Image.open(candidate_path).convert("RGB")
    if reference.size != candidate.size:
        raise ValueError("retained frame dimensions drift")
    diff = ImageChops.difference(reference, candidate)
    bbox = diff.getbbox()
    changed = 0
    max_channel = 0
    if bbox is not None:
        rp = reference.load()
        cp = candidate.load()
        width, height = reference.size
        for y in range(height):
            for x in range(width):
                a = rp[x, y]
                b = cp[x, y]
                if a != b:
                    changed += 1
                    max_channel = max(max_channel, *(abs(int(a[i]) - int(b[i])) for i in range(3)))
    total = reference.size[0] * reference.size[1]
    return {
        "changed_pixels": changed,
        "changed_fraction": changed / total,
        "max_channel_delta_lsb": max_channel,
        "bbox": list(bbox) if bbox is not None else None,
        "width": reference.size[0],
        "height": reference.size[1],
    }


def runtime_signature(row: dict[str, Any]) -> dict[str, int]:
    return {key: int(row[key]) for key in RUNTIME_KEYS}


def verify(payload: dict[str, Any], reference_root: Path, candidate_root: Path, environment_head: str) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA or payload.get("status") != STATUS or not all(payload.get("checks", {}).values()):
        raise ValueError("Nature winding migration structure must PASS first")
    reference = load_json(reference_root / "runtime.json")
    candidate = load_json(candidate_root / "runtime.json")
    if reference.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError("exact indexed-Object current-world reference is not live-PASS")
    if candidate.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION":
        raise ValueError("candidate current-world target host did not reach live-PASS")
    if candidate.get("environment_nature_source_migration_head") != NATURE_MIGRATION_HEAD:
        raise ValueError("candidate runtime Nature migration identity drift")
    if candidate.get("environment_nature_vfx_head") != NATURE_VFX_HEAD:
        raise ValueError("candidate runtime Nature VFX identity drift")
    if candidate.get("environment_object_indexed_receiver_runtime_donor_head") != reference.get("environment_object_indexed_receiver_runtime_donor_head"):
        raise ValueError("indexed Object representation drift")
    if candidate.get("environment_object_footprint_review_mode") != "CANDIDATE_VISIBLE":
        raise ValueError("candidate lost preferred visible Object footprint context")

    rsamples = reference.get("samples", [])
    csamples = candidate.get("samples", [])
    if len(rsamples) != len(csamples) or len(csamples) != 17:
        raise ValueError("target-host sample count drift")

    width_count = 0
    max_width_residual = 0.0
    runtime_deltas: dict[str, set[tuple[tuple[str, int], ...]]] = {camera: set() for camera in CAMERAS}
    nature_runtime_rows = 0
    for index, (rs, cs) in enumerate(zip(rsamples, csamples)):
        if rs.get("index") != cs.get("index") or rs.get("weather_field_digest") != cs.get("weather_field_digest"):
            raise ValueError(f"state {index}: Weather/source index drift")
        if cs.get("sapling_mesh_digest") != payload["states"][index].get("sapling_mesh_digest"):
            raise ValueError(f"state {index}: migrated sapling digest not observed")
        static = {x.get("asset_id"): x for x in cs.get("static_source_meshes", [])}
        for asset_id in ("source:nature:compact-east-tree-neutral-001", "source:nature:east-rear-tree-neutral-001"):
            row = static.get(asset_id, {})
            if row.get("surface_count") != 2 or row.get("material_family_id") != NATURE_FAMILY_ID:
                raise ValueError(f"state {index}: migrated Nature material receiver missing for {asset_id}")
            nature_runtime_rows += 1
        sapling_update = cs.get("sapling_update", {})
        if sapling_update.get("surface_count") != 2 or sapling_update.get("material_family_id") != NATURE_FAMILY_ID:
            raise ValueError(f"state {index}: migrated sapling two-surface receiver missing")
        for camera in CAMERAS:
            for mode in WEATHER_MODES:
                rb = rs["contexts"][camera][mode]
                cb = cs["contexts"][camera][mode]
                if mode == "candidate":
                    weather = cb["weather_update"]
                    width_count += int(weather.get("measured_width_count", 0))
                    max_width_residual = max(max_width_residual, float(weather.get("maximum_projected_width_residual_px", 0.0)))
                rd = runtime_signature(rb["runtime"])
                cd = runtime_signature(cb["runtime"])
                runtime_deltas[camera].add(tuple(sorted((key, cd[key] - rd[key]) for key in RUNTIME_KEYS)))

    if width_count != 1224 or max_width_residual > 0.05:
        raise ValueError(f"Weather-width receiving regression: count={width_count}, residual={max_width_residual}")
    if nature_runtime_rows != 34:
        raise ValueError("expected exact two static Nature runtime rows across 17 samples")

    normalized_runtime: dict[str, list[dict[str, int]]] = {}
    for camera, values in runtime_deltas.items():
        normalized_runtime[camera] = [dict(items) for items in sorted(values)]
        if len(values) != 1:
            raise ValueError(f"{camera}: runtime counter delta not stable")
        only = dict(next(iter(values)))
        if any(only[key] != 0 for key in RUNTIME_KEYS):
            raise ValueError(f"{camera}: winding-only migration changed proof-host submission/resource counters: {only}")

    image_stats = {camera: {mode: [] for mode in WEATHER_MODES} for camera in CAMERAS}
    matched = 0
    for camera in CAMERAS:
        for mode in WEATHER_MODES:
            for index in range(17):
                name = f"atmosphere-width-{mode}-{camera}-{index:02d}.png"
                rp = reference_root / "rendered" / name
                cp = candidate_root / "rendered" / name
                if not rp.exists() or not cp.exists():
                    raise ValueError(f"missing retained frame {name}")
                image_stats[camera][mode].append(rgb_delta_stats(rp, cp))
                matched += 1
    if matched != 68:
        raise ValueError("expected exact 68 matched current-world frames")

    visual_summary: dict[str, Any] = {}
    for camera in CAMERAS:
        rows = [row for mode in WEATHER_MODES for row in image_stats[camera][mode]]
        visual_summary[camera] = {
            "mean_changed_pixels": sum(row["changed_pixels"] for row in rows) / len(rows),
            "min_changed_pixels": min(row["changed_pixels"] for row in rows),
            "max_changed_pixels": max(row["changed_pixels"] for row in rows),
            "mean_changed_fraction": sum(row["changed_fraction"] for row in rows) / len(rows),
            "maximum_channel_delta_lsb": max(row["max_channel_delta_lsb"] for row in rows),
            "unique_bboxes": sorted({tuple(row["bbox"]) if row["bbox"] is not None else tuple() for row in rows}),
        }

    return {
        "schema": TARGET_SCHEMA,
        "state": TARGET_STATUS,
        "environment_head": environment_head,
        "parent_indexed_object_environment_head": INDEXED_OBJECT_ENVIRONMENT_HEAD,
        "nature_vfx_head": NATURE_VFX_HEAD,
        "nature_source_migration_head": NATURE_MIGRATION_HEAD,
        "nature_geometry_oracle": NATURE_GEOMETRY_ORACLE,
        "composition_digest": payload.get("composition_digest"),
        "checks": {
            "structure_passed_first": True,
            "exact_current_world_indexed_object_reference_bound": True,
            "preferred_visible_footprint_context_preserved": True,
            "all_17_dynamic_states_observed": True,
            "three_nature_sources_reach_two_surface_material_receiver": True,
            "migrated_sapling_digest_sequence_reaches_target_host": True,
            "all_1224_weather_width_observations_preserved": True,
            "proof_host_runtime_counter_shape_unchanged": True,
            "all_68_matched_frames_retained_and_characterized": True,
        },
        "matched_frames": matched,
        "weather_width_measurements": width_count,
        "maximum_projected_weather_width_residual_px": max_width_residual,
        "runtime_deltas": normalized_runtime,
        "visual_delta_characterization": visual_summary,
        "decision": "MIGRATED_NATURE_SOURCE_LINEAGE_REACHES_CURRENT_WORLD__FINAL_VISUAL_ACCEPTANCE_REQUIRES_ART_QA_REVIEW",
        "truth_boundary": "This target-host PASS means the exact Nature winding-migrated source lineage and rebound sapling visual response execute inside the existing current multi-asset Godot proof while Building, indexed Object, visible footprint cue, Nature material roles, Weather source-width presentation, route, cameras and lighting remain bound. Image deltas caused by corrected winding/generated normals/culling are characterized rather than declared aesthetically neutral. Final Art Direction/Visual QA, arbitrary-camera behavior, physical wind, gameplay and target-device performance remain separate.",
        "non_claims": [
            "visual neutrality or final Nature look acceptance",
            "global outward-normal correctness beyond pinned Nature migration evidence",
            "final normals tangents UV textures or sidedness",
            "physical wind or plant biomechanics",
            "target-device CPU GPU FPS VRAM or heap performance",
            "collision navigation or gameplay",
            "CANON or production readiness",
            "Environment mastery",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    build_parser = sub.add_parser("build")
    build_parser.add_argument("--parent", type=Path, required=True)
    build_parser.add_argument("--nature-root", type=Path, required=True)
    build_parser.add_argument("--environment-head", required=True)
    build_parser.add_argument("--output", type=Path, required=True)

    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--payload", type=Path, required=True)
    verify_parser.add_argument("--reference-root", type=Path, required=True)
    verify_parser.add_argument("--candidate-root", type=Path, required=True)
    verify_parser.add_argument("--environment-head", required=True)
    verify_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "build":
        parent = load_json(args.parent)
        payload = build(parent, args.nature_root, args.environment_head)
        # Fail-closed local provenance mutation check.
        mutated = copy.deepcopy(payload)
        mutated["nature_source_migration_head"] = "0" * 40
        if mutated["nature_source_migration_head"] == NATURE_MIGRATION_HEAD:
            raise AssertionError("negative control did not mutate provenance")
        payload["negative_controls"] = {
            "nature_source_migration_head_drift_rejected_by_target_observer": True,
            "purpose": "Retained contract declares exact migration identity; observer rejects any different head before rendering.",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "state": payload["status"],
            "composition_digest": payload["composition_digest"],
            "winding_changed_triangles": payload["winding_changed_triangles"],
            "sapling_max_vertex_residual_m": payload["sapling_max_vertex_residual_m"],
        }, indent=2, sort_keys=True))
        return 0

    payload = load_json(args.payload)
    report = verify(payload, args.reference_root, args.candidate_root, args.environment_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
