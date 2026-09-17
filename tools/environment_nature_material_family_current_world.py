from __future__ import annotations

import argparse, copy, hashlib, importlib.util, json
from pathlib import Path
from typing import Any

PARENT_SCHEMA = "axm.environment-current-world-building-header-segmentation-composition/v0.1"
PARENT_STATUS = "PASS_CURRENT_WORLD_BUILDING_HEADER_SEGMENTATION_STRUCTURE"
PARENT_IMPLEMENTATION_HEAD = "dfd4e1d662ab7d6d9f1a5c8dd35b571418154f6e"
PARENT_COMPOSITION_DIGEST = "073aaba4066f223be2f298d631550acb724c30f6b17ee1d51a285e4d2bbeb8b2"
MATERIALS_HEAD = "8b2e0523d7a2b210c6404f15bafb08fbedcad4dd"
GEOMETRY_HEAD = "da3adbef4de8cddb8f3ebe841d39bb31a8936f5f"
FAMILY_SCHEMA = "axm.nature-woody-foliage-material-family/v0.1"
FAMILY_ID = "nature-woody-foliage-family-001"
STUDIES = {
    "sapling-neutral-001": "examples/sapling_neutral_001.json",
    "compact-east-tree-neutral-001": "examples/compact_east_tree_neutral_001.json",
    "east-rear-tree-neutral-001": "examples/east_rear_tree_neutral_001.json",
}
ASSET_TO_STUDY = {
    "source:nature:sapling-neutral-001": "sapling-neutral-001",
    "source:nature:compact-east-tree-neutral-001": "compact-east-tree-neutral-001",
    "source:nature:east-rear-tree-neutral-001": "east-rear-tree-neutral-001",
}
SCHEMA = "axm.environment-current-world-nature-material-family-composition/v0.1"
STATUS = "PASS_CURRENT_WORLD_NATURE_MATERIAL_FAMILY_STRUCTURE"
TARGET_SCHEMA = "axm.environment-current-world-nature-material-family-target-host/v0.1"
TARGET_STATUS = "PASS_CURRENT_WORLD_NATURE_MATERIAL_FAMILY_TARGET_HOST"
CONTEXTS = ("path_eye", "elevated_oblique")
MODES = ("control", "candidate")


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canon(value).encode()).hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def scene_digest(scene: dict[str, Any]) -> str:
    value = copy.deepcopy(scene)
    value.pop("scene_digest", None)
    return digest(value)


def membership(tri: list[int]) -> tuple[int, int, int]:
    return tuple(sorted(int(v) for v in tri))


def rgba(hex_rgba: str) -> list[float]:
    if not isinstance(hex_rgba, str) or len(hex_rgba) != 9 or not hex_rgba.startswith("#"):
        raise ValueError("material color must be #RRGGBBAA")
    return [int(hex_rgba[i:i + 2], 16) / 255.0 for i in (1, 3, 5, 7)]


def import_organic(root: Path):
    path = root / "src/axm_nature_design/organic_form.py"
    spec = importlib.util.spec_from_file_location("axm_env_nature_organic", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load exact Nature generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def partition(mesh: dict[str, Any]) -> dict[str, list[int]]:
    out = {"woody": [], "foliage": []}
    seen = set()
    for region in mesh.get("regions", []):
        role = "foliage" if region.get("kind") == "leaf-blade" else "woody" if region.get("kind") == "tapered-segment" else None
        if role is None:
            raise ValueError(f"unsupported Nature region kind {region.get('kind')}")
        start = int(region["triangle_start"])
        count = int(region["triangle_count"])
        for idx in range(start, start + count):
            if idx in seen:
                raise ValueError("Nature region triangle overlap")
            seen.add(idx)
            out[role].append(idx)
    if seen != set(range(len(mesh.get("triangles", [])))):
        raise ValueError("Nature regions do not partition all triangles")
    if (len(out["woody"]), len(out["foliage"])) != (520, 50):
        raise ValueError("exact Nature 520/50 surface partition drift")
    return out


def exact_geometry_packets(root: Path) -> dict[str, dict[str, Any]]:
    organic = import_organic(root)
    packets = {}
    for study, path in STUDIES.items():
        source = load_json(root / path)
        if source.get("study_id") != study:
            raise ValueError(f"Nature source identity drift: {study}")
        mesh = organic.build_mesh(source)
        if len(mesh["vertices"]) != 390 or len(mesh["triangles"]) != 570:
            raise ValueError(f"Nature mesh count drift: {study}")
        packets[study] = {
            "source_digest": digest(source),
            "mesh_digest": digest(mesh),
            "vertices": mesh["vertices"],
            "triangles": mesh["triangles"],
            "surface_triangle_indices": partition(mesh),
        }
    return packets


def validate_family(profile: dict[str, Any]) -> dict[str, Any]:
    if profile.get("schema") != FAMILY_SCHEMA or profile.get("family_id") != FAMILY_ID:
        raise ValueError("Nature material-family identity drift")
    if profile.get("supported_source_scope") != list(STUDIES):
        raise ValueError("Nature material-family source scope drift")
    if profile.get("intent", {}).get("variation_policy") != "NO_PER_SOURCE_VARIATION_YET__ESTABLISH_SHARED_FAMILY_BASELINE_FIRST":
        raise ValueError("Nature family variation policy drift")
    mats = profile.get("materials", {})
    if set(mats) != {"woody", "foliage"}:
        raise ValueError("Nature family must define woody and foliage only")
    result = {}
    for role in ("woody", "foliage"):
        material = mats[role]
        if float(material.get("metallic", -1)) != 0.0:
            raise ValueError("Nature family must remain non-metallic")
        roughness = float(material.get("roughness", -1))
        if not 0 <= roughness <= 1:
            raise ValueError("Nature roughness out of range")
        result[role] = {"albedo": rgba(material["color"]), "metallic": 0.0, "roughness": roughness}
    return result


def triangles_match_membership(current: list[list[int]], donor: list[list[int]]) -> bool:
    return len(current) == len(donor) and all(membership(a) == membership(b) for a, b in zip(current, donor))


def attach(receiver: dict[str, Any], study: str, packet: dict[str, Any], materials: dict[str, Any], cull: str) -> None:
    if len(receiver.get("vertices_source_xyz_m", [])) != 390 or len(receiver.get("triangles", [])) != 570:
        raise ValueError(f"current-world Nature geometry count drift: {study}")
    if not triangles_match_membership(receiver["triangles"], packet["triangles"]):
        raise ValueError(f"current-world Nature triangle membership drift: {study}")
    receiver["nature_material_family_receiving"] = {
        "schema": "axm.environment-nature-material-family-receiving/v0.1",
        "family_id": FAMILY_ID,
        "study_id": study,
        "materials_head": MATERIALS_HEAD,
        "geometry_reference_head": GEOMETRY_HEAD,
        "surface_triangle_indices": copy.deepcopy(packet["surface_triangle_indices"]),
        "materials": copy.deepcopy(materials),
        "preserved_proof_culling": cull,
        "triangle_membership_relation": "EXACT_PER_TRIANGLE_MEMBERSHIP__WINDING_MAY_REMAIN_RECEIVER_LINEAGE",
        "truth_boundary": "Environment applies only the exact Materials-owned woody/foliage scalar family to the existing current-world Nature geometry. Source form, triangle membership, motion, placement and current proof culling remain unchanged.",
    }


def build(parent: dict[str, Any], profile: dict[str, Any], geometry_root: Path, receiving_head: str) -> dict[str, Any]:
    if parent.get("schema") != PARENT_SCHEMA or parent.get("status") != PARENT_STATUS or not all(parent.get("checks", {}).values()):
        raise ValueError("exact segmented Building parent must structurally PASS")
    if parent.get("receiving_head") != PARENT_IMPLEMENTATION_HEAD or parent.get("composition_digest") != PARENT_COMPOSITION_DIGEST:
        raise ValueError("exact segmented Building parent identity drift")
    if len(parent.get("states", [])) != 17:
        raise ValueError("Environment parent state count drift")
    materials = validate_family(profile)
    packets = exact_geometry_packets(geometry_root)
    states = []
    for oldrow in parent["states"]:
        row = copy.deepcopy(oldrow)
        scene = row["scene"]
        before = copy.deepcopy(scene)
        before.pop("scene_digest", None)
        sapling = scene.get("sapling", {})
        if sapling.get("asset_id") != "source:nature:sapling-neutral-001":
            raise ValueError("exact current-world sapling identity drift")
        attach(sapling, "sapling-neutral-001", packets["sapling-neutral-001"], materials, str(sapling.get("proof_render_culling", "")))
        found = set()
        for source in scene.get("additional_source_meshes", []):
            asset = source.get("asset_id")
            if asset in ("source:nature:compact-east-tree-neutral-001", "source:nature:east-rear-tree-neutral-001"):
                study = ASSET_TO_STUDY[asset]
                found.add(study)
                attach(source, study, packets[study], materials, str(source.get("proof_render_culling", "")))
        if found != {"compact-east-tree-neutral-001", "east-rear-tree-neutral-001"}:
            raise ValueError("exact two static Nature sources not found")
        check = copy.deepcopy(scene)
        check.pop("scene_digest", None)
        receivers = [check.get("sapling", {})] + [x for x in check.get("additional_source_meshes", []) if x.get("asset_id") in ASSET_TO_STUDY]
        for blob in receivers:
            blob.pop("nature_material_family_receiving", None)
        if check != before:
            raise ValueError("unrelated current-world state drift during Nature material-family composition")
        scene["scene_digest"] = scene_digest(scene)
        states.append(row)
    checks = {
        "exact_segmented_building_parent": True,
        "all_17_states_preserved": len(states) == 17,
        "weather_sequence_preserved": [x["weather_field_digest"] for x in states] == [x["weather_field_digest"] for x in parent["states"]],
        "sapling_motion_sequence_preserved": [x["sapling_mesh_digest"] for x in states] == [x["sapling_mesh_digest"] for x in parent["states"]],
        "building_object_dressing_path_cameras_lighting_preserved": all(
            all(a["scene"].get(k) == b["scene"].get(k) for k in ("environment_building_material_receiving", "environment_object_replacement", "environment_object_readability_dressing", "readable_path", "cameras", "lighting"))
            for a, b in zip(states, parent["states"])
        ),
        "exact_three_source_family_scope": profile.get("supported_source_scope") == list(STUDIES),
        "exact_woody_foliage_partition": all(len(packet["surface_triangle_indices"]["woody"]) == 520 and len(packet["surface_triangle_indices"]["foliage"]) == 50 for packet in packets.values()),
        "no_source_form_or_triangle_membership_change": True,
        "existing_receiver_culling_preserved": True,
    }
    if not all(checks.values()):
        raise ValueError(f"Nature material-family composition checks failed: {checks}")
    out = copy.deepcopy(parent)
    out.update({
        "schema": SCHEMA,
        "status": STATUS,
        "study_id": "environment-current-world-nature-material-family-001",
        "receiving_head": receiving_head,
        "parent_environment_head": PARENT_IMPLEMENTATION_HEAD,
        "parent_composition_digest": PARENT_COMPOSITION_DIGEST,
        "nature_materials_head": MATERIALS_HEAD,
        "nature_geometry_reference_head": GEOMETRY_HEAD,
        "nature_material_family": copy.deepcopy(profile),
        "nature_surface_partitions": {k: v["surface_triangle_indices"] for k, v in packets.items()},
        "checks": checks,
        "states": states,
        "truth_boundary": "PASS proves only that the exact three-source Materials-owned woody/foliage scalar family is attached to the existing current-world sapling, compact east tree and migrated rear tree without changing their form, triangle membership, motion, placement or existing proof culling, while Building/Object/dressing/Weather/path/cameras/lighting remain fixed. Visual preference and runtime acceptance remain separate.",
        "non_claims": ["FINAL_NATURE_MATERIAL_OR_SIDEDNESS_ACCEPTANCE", "UV_TEXTURE_SUBSURFACE_TRANSMISSION_OR_NORMAL_MAP_QUALITY", "PHYSICAL_BOTANICAL_CORRECTNESS", "TARGET_DEVICE_PERFORMANCE", "GAMEPLAY_COLLISION_NAVIGATION", "CANON_PRODUCTION_READY_OR_ENVIRONMENT_MASTERY"],
    })
    out["composition_digest"] = digest({"parent": PARENT_COMPOSITION_DIGEST, "materials_head": MATERIALS_HEAD, "geometry_reference_head": GEOMETRY_HEAD, "family": digest(profile), "scenes": [x["scene"]["scene_digest"] for x in states]})
    return out


def verify(payload: dict[str, Any], receipt: dict[str, Any], parent_receipt: dict[str, Any], candidate_root: Path, parent_root: Path) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA or payload.get("status") != STATUS or not all(payload.get("checks", {}).values()):
        raise ValueError("Nature family structure must PASS first")
    if receipt.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION" or receipt.get("receiving_head") != payload.get("receiving_head"):
        raise ValueError("candidate live receipt drift")
    if parent_receipt.get("state") != "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION" or parent_receipt.get("receiving_head") != PARENT_IMPLEMENTATION_HEAD:
        raise ValueError("parent live receipt drift")
    from PIL import Image
    import numpy as np
    changed = {c: [] for c in CONTEXTS}
    mean_delta = {c: [] for c in CONTEXTS}
    max_delta = 0
    measured_width = 0
    width_resid = 0.0
    runtime_deltas = {c: {m: [] for m in MODES} for c in CONTEXTS}
    samples = receipt.get("samples", [])
    psamples = parent_receipt.get("samples", [])
    if len(samples) != 17 or len(psamples) != 17:
        raise ValueError("live sample count drift")
    for sample, psample in zip(samples, psamples):
        if (sample.get("index"), sample.get("weather_field_digest"), sample.get("sapling_mesh_digest")) != (psample.get("index"), psample.get("weather_field_digest"), psample.get("sapling_mesh_digest")):
            raise ValueError("dynamic source sequence drift")
        static = {row.get("asset_id"): row for row in sample.get("static_source_meshes", [])}
        for asset in ("source:nature:compact-east-tree-neutral-001", "source:nature:east-rear-tree-neutral-001"):
            if static.get(asset, {}).get("surface_count") != 2 or static.get(asset, {}).get("material_family_id") != FAMILY_ID:
                raise ValueError(f"live Nature material family missing: {asset}")
        if sample.get("sapling_update", {}).get("surface_count") != 2 or sample.get("sapling_update", {}).get("material_family_id") != FAMILY_ID:
            raise ValueError("live sapling material family missing")
        for context in CONTEXTS:
            for mode in MODES:
                block = sample["contexts"][context][mode]
                pblock = psample["contexts"][context][mode]
                if mode == "candidate":
                    weather = block.get("weather_update", {})
                    measured_width += int(weather.get("measured_width_count", 0))
                    width_resid = max(width_resid, float(weather.get("maximum_projected_width_residual_px", 0)))
                a = np.asarray(Image.open(parent_root / f"atmosphere-width-{mode}-{context}-{int(sample['index']):02d}.png").convert("RGB"), dtype=np.int16)
                b = np.asarray(Image.open(candidate_root / f"atmosphere-width-{mode}-{context}-{int(sample['index']):02d}.png").convert("RGB"), dtype=np.int16)
                delta = np.abs(a - b)
                mask = np.any(delta > 1, axis=2)
                changed[context].append(int(mask.sum()))
                mean_delta[context].append(float(delta.mean()))
                max_delta = max(max_delta, int(delta.max()))
                current_runtime = block["runtime"]
                parent_runtime = pblock["runtime"]
                runtime_deltas[context][mode].append({key: int(current_runtime.get(key, 0)) - int(parent_runtime.get(key, 0)) for key in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "buffer_mem_bytes", "texture_mem_bytes")})
    checks = {
        "all_68_parent_candidate_pairs_compared": sum(len(v) for v in changed.values()) == 68,
        "material_delta_visible_in_both_cameras": all(max(v) > 0 for v in changed.values()),
        "weather_width_measurements_preserved": measured_width == 1224 and width_resid <= 0.05,
        "candidate_live_three_source_material_family": True,
        "dynamic_source_sequence_exact": True,
    }
    if not all(checks.values()):
        raise ValueError(f"Nature material-family target checks failed: {checks}")
    return {
        "schema": TARGET_SCHEMA,
        "state": TARGET_STATUS,
        "receiving_head": payload["receiving_head"],
        "checks": checks,
        "pair_counts": {c: len(v) for c, v in changed.items()},
        "changed_pixels_gt_1_lsb": changed,
        "mean_abs_rgb_delta": mean_delta,
        "maximum_rgb_channel_delta_lsb": max_delta,
        "measured_width_count": measured_width,
        "maximum_projected_width_residual_px": width_resid,
        "runtime_counter_deltas_vs_segmented_parent": runtime_deltas,
        "truth_boundary": "Direct Godot 4.7.2 fixed-camera comparison against the exact segmented-Building parent proves the receiving-scene consequence of the bounded three-source Nature material family while the current geometry/motion/culling and non-Nature world remain fixed. It does not establish final Art Direction/QA preference, final sidedness, arbitrary cameras, or target-device performance.",
    }


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--parent", required=True)
    build_parser.add_argument("--profile", required=True)
    build_parser.add_argument("--geometry-root", required=True)
    build_parser.add_argument("--receiving-head", required=True)
    build_parser.add_argument("--output", required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--payload", required=True)
    verify_parser.add_argument("--receipt", required=True)
    verify_parser.add_argument("--parent-receipt", required=True)
    verify_parser.add_argument("--candidate-root", required=True)
    verify_parser.add_argument("--parent-root", required=True)
    verify_parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.cmd == "build":
        out = build(load_json(args.parent), load_json(args.profile), Path(args.geometry_root), args.receiving_head)
    else:
        out = verify(load_json(args.payload), load_json(args.receipt), load_json(args.parent_receipt), Path(args.candidate_root), Path(args.parent_root))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: out.get(k) for k in ("schema", "status", "state", "composition_digest", "checks")}, indent=2))


if __name__ == "__main__":
    main()
