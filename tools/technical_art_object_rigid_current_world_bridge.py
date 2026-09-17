from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

CONTRACT_SCHEMA = "axm.technical-art-object-rigid-current-world-bridge/v0.1"
MAP_SCHEMA = "axm.environment-object-rigid-component-map/v0.1"
REPORT_SCHEMA = "axm.technical-art-object-rigid-current-world-bridge-result/v0.1"
TARGET_STATE = "PASS_CURRENT_WORLD_OBJECT_RIGID_COMPONENT_BOUNDARY_NEUTRAL_EQUIVALENCE__ANIMATION_VFX_ADOPTION_HELD"
OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
TA_RESULT = "PASS_OBJECT_SOURCE_OWNED_RIGID_PARTS_THROUGH_UC_SCENE_GRAPH"
UC_GRAPH_SCHEMA = "axm.rigid-scene-graph/v0.1"


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path: str | Path, value: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_head(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def git_blob(root: Path, rev: str, path: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", f"{rev}:{path}"], text=True).strip()


def load_object_builder(object_root: Path):
    path = object_root / "tools" / "build_modular_case.py"
    if not path.is_file():
        raise ValueError("exact Object builder missing")
    spec = importlib.util.spec_from_file_location("axm_object_builder_for_map_ta", path)
    if spec is None or spec.loader is None:
        raise ValueError("could not load exact Object builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "build"):
        raise ValueError("exact Object builder has no build()")
    return module


def component_rows(object_root: Path, source_path: Path) -> list[dict[str, Any]]:
    source = load(source_path)
    builder = load_object_builder(object_root)
    built = builder.build(source)
    mesh = built.get("mesh", {})
    groups = mesh.get("groups", [])
    faces = mesh.get("faces", [])
    if len(faces) != 812:
        raise ValueError(f"exact Object face count drift: {len(faces)}")
    rows: list[dict[str, Any]] = []
    covered: set[int] = set()
    for raw in groups:
        name = str(raw.get("name", ""))
        first = int(raw.get("first_face", -1))
        count = int(raw.get("face_count", -1))
        if not name or first < 0 or count <= 0 or first + count > len(faces):
            raise ValueError(f"invalid Object source group range: {raw}")
        indices = set(range(first, first + count))
        overlap = covered & indices
        if overlap:
            raise ValueError(f"Object source groups overlap: {name} -> {sorted(overlap)[:8]}")
        covered |= indices
        rows.append({"name": name, "first_triangle": first, "triangle_count": count})
    if covered != set(range(812)):
        missing = sorted(set(range(812)) - covered)
        raise ValueError(f"Object source groups do not exactly partition 812 triangles: missing={missing[:8]}")
    if len({row["name"] for row in rows}) != len(rows):
        raise ValueError("Object source group names are not unique")
    return rows


def validate_map(component_map: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    if component_map.get("schema") != MAP_SCHEMA:
        raise ValueError("rigid component map schema drift")
    obj = contract["object_source"]
    ta = contract["technical_art_donor"]
    if component_map.get("object_source_head") != obj["head"] or component_map.get("object_source_sha256") != obj["sha256"]:
        raise ValueError("rigid component map Object source identity drift")
    if component_map.get("technical_art_head") != ta["head"]:
        raise ValueError("rigid component map Technical Art head drift")
    if component_map.get("technical_art_result") != TA_RESULT:
        raise ValueError("rigid component map Technical Art result drift")
    rows = component_map.get("components")
    if not isinstance(rows, list) or len(rows) != int(contract["receiver"]["required_component_count"]):
        raise ValueError("rigid component count drift")
    seen_names: set[str] = set()
    seen_triangles: set[int] = set()
    parent_by_name: dict[str, str | None] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("rigid component row is not an object")
        name = str(row.get("name", ""))
        first = int(row.get("first_triangle", -1))
        count = int(row.get("triangle_count", -1))
        parent = row.get("parent")
        if not name or name in seen_names or first < 0 or count <= 0 or first + count > 812:
            raise ValueError(f"invalid rigid component row: {row}")
        if parent is not None and not isinstance(parent, str):
            raise ValueError(f"invalid rigid component parent: {row}")
        seen_names.add(name)
        parent_by_name[name] = parent
        span = set(range(first, first + count))
        if seen_triangles & span:
            raise ValueError(f"rigid component triangle overlap: {name}")
        seen_triangles |= span
    if seen_triangles != set(range(812)):
        raise ValueError("rigid components do not exactly partition source triangles")
    for child, parent in parent_by_name.items():
        if parent is not None and parent not in seen_names:
            raise ValueError(f"rigid component parent missing: {child}->{parent}")
    if parent_by_name.get("lid_shell") is not None:
        raise ValueError("lid_shell must remain a root transform boundary")
    expected_children = set(ta["required_lid_owned_children"])
    observed_children = {name for name, parent in parent_by_name.items() if parent == "lid_shell"}
    if observed_children != expected_children:
        raise ValueError(f"lid-owned parent-edge drift: {sorted(observed_children)}")
    for lever in ta["required_fixed_levers"]:
        if parent_by_name.get(lever) is not None:
            raise ValueError(f"fixed lever unexpectedly parented under moving lid: {lever}")
    required = list(contract["receiver"]["required_moving_components"])
    if any(name not in seen_names for name in required):
        raise ValueError("required moving component boundary missing")
    pivot = component_map.get("hinge_pivot_receiver_xyz_m")
    if not isinstance(pivot, list) or len(pivot) != 3 or any(not isinstance(v, (int, float)) for v in pivot):
        raise ValueError("receiver hinge pivot drift")
    if int(component_map.get("triangles", -1)) != 812:
        raise ValueError("rigid component map total triangle drift")
    return {
        "component_count": len(rows),
        "triangles": len(seen_triangles),
        "lid_owned_children": sorted(observed_children),
        "required_moving_components": required,
        "hinge_pivot_receiver_xyz_m": [float(v) for v in pivot],
    }


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    contract = load(args.contract)
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ValueError("Technical Art bridge contract schema drift")
    object_root = Path(args.object_root).resolve()
    if git_head(object_root) != contract["technical_art_donor"]["head"]:
        raise ValueError("Object Technical Art checkout head drift")
    source_path = object_root / contract["object_source"]["path"]
    if sha256_file(source_path) != contract["object_source"]["sha256"]:
        raise ValueError("Object source byte identity drift")
    source_blob = git_blob(object_root, "HEAD", contract["object_source"]["path"])
    if source_blob != contract["object_source"]["blob"]:
        raise ValueError("Object source Git blob drift")

    ta_receipt = load(args.ta_receipt)
    if ta_receipt.get("schema") != "axm.object-uc-rigid-scene-handoff/v0.1" or ta_receipt.get("result") != TA_RESULT:
        raise ValueError("Technical Art donor receipt is not the exact rigid-scene PASS")
    if ta_receipt.get("source_repository_head") != contract["technical_art_donor"]["head"]:
        raise ValueError("Technical Art donor receipt head drift")
    if ta_receipt.get("source_sha256") != contract["object_source"]["sha256"]:
        raise ValueError("Technical Art donor receipt source drift")
    if ta_receipt.get("expected_uc_commit") != contract["uc"]["donor_head"]:
        raise ValueError("Technical Art donor UC commit drift")
    if ta_receipt.get("triangles") != 812 or ta_receipt.get("closed_static_localization_max_error_m") != 0.0:
        raise ValueError("Technical Art donor closed-state geometry prerequisite drift")

    ta_surface = load(args.ta_surface)
    if ta_surface.get("schema") != "axm.surface-3d/v0.1":
        raise ValueError("Technical Art donor surface schema drift")
    primitive_ids = [str(row.get("id", "")) for row in ta_surface.get("primitives", [])]

    rows = component_rows(object_root, source_path)
    group_names = [row["name"] for row in rows]
    if primitive_ids != group_names:
        raise ValueError("Technical Art transported primitive order no longer equals exact Object source-group order")

    uc_path = contract["uc"]["rigid_scene_graph_path"]
    donor_root = Path(args.uc_donor_root).resolve()
    current_root = Path(args.uc_current_root).resolve()
    if git_head(donor_root) != contract["uc"]["donor_head"]:
        raise ValueError("UC donor checkout head drift")
    if git_head(current_root) != contract["uc"]["inspected_current_head"]:
        raise ValueError("UC inspected-current checkout head drift")
    donor_blob = git_blob(donor_root, "HEAD", uc_path)
    current_blob = git_blob(current_root, "HEAD", uc_path)
    if donor_blob != current_blob:
        raise ValueError("current UC rigid-scene graph executable drift from tested donor")

    lid_children = list(ta_receipt["lid_owned_children"])
    fixed_levers = list(ta_receipt["source_owned_fixed_levers"])
    parent_by_name = {name: "lid_shell" for name in lid_children}
    localized = {"lid_shell", *lid_children}
    for row in rows:
        name = row["name"]
        row["parent"] = parent_by_name.get(name)
        row["localized_to_hinge_pivot"] = name in localized

    component_map = {
        "schema": MAP_SCHEMA,
        "result": "PASS_EXACT_OBJECT_TA_RIGID_COMPONENT_MAP_FOR_CURRENT_WORLD_RECEIVER",
        "object_source_head": contract["object_source"]["head"],
        "object_source_sha256": contract["object_source"]["sha256"],
        "technical_art_head": contract["technical_art_donor"]["head"],
        "technical_art_result": TA_RESULT,
        "tested_uc_head": contract["uc"]["donor_head"],
        "inspected_current_uc_head": contract["uc"]["inspected_current_head"],
        "rigid_scene_graph_blob": donor_blob,
        "hinge_pivot_receiver_xyz_m": [float(v) for v in ta_receipt["hinge_pivot_uc_m"]],
        "lid_owned_children": lid_children,
        "fixed_levers": fixed_levers,
        "required_moving_components": list(contract["receiver"]["required_moving_components"]),
        "components": rows,
        "triangles": 812,
        "truth_boundary": "Object source/ownership and Technical Art own component semantics and hinge ownership. This generated map only adapts those exact identities to the current Map receiver. UC remains a generic rigid-scene transport and receives no Object or Map policy.",
    }
    summary = validate_map(component_map, contract)
    write(args.output, component_map)
    receipt = {
        "schema": "axm.technical-art-object-rigid-component-map-receipt/v0.1",
        "result": component_map["result"],
        "map_sha256": sha256_file(args.output),
        "object_source_blob": source_blob,
        "uc_rigid_scene_graph_blob": donor_blob,
        "uc_donor_and_inspected_current_blob_identical": donor_blob == current_blob,
        **summary,
    }
    write(args.receipt, receipt)
    return receipt


def _find_object(sample: dict[str, Any]) -> dict[str, Any]:
    rows = sample.get("static_source_meshes")
    if not isinstance(rows, list):
        raise ValueError("runtime sample static_source_meshes missing")
    found = [row for row in rows if isinstance(row, dict) and row.get("asset_id") == OBJECT_ASSET_ID]
    if len(found) != 1:
        raise ValueError(f"expected exactly one Object receiver row, got {len(found)}")
    return found[0]


def _pixel_difference(control: Path, candidate: Path) -> tuple[int, tuple[int, int, int, int] | None]:
    with Image.open(control).convert("RGBA") as a, Image.open(candidate).convert("RGBA") as b:
        if a.size != b.size:
            raise ValueError(f"frame size drift: {control.name} {a.size} != {b.size}")
        diff = ImageChops.difference(a, b)
        bbox = diff.getbbox()
        if bbox is None:
            return 0, None
        # Count pixels where at least one RGBA channel differs.
        pixels = sum(1 for px in diff.getdata() if px != (0, 0, 0, 0))
        return pixels, bbox


def verify(args: argparse.Namespace) -> dict[str, Any]:
    contract = load(args.contract)
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ValueError("Technical Art bridge contract schema drift")
    component_map = load(args.component_map)
    map_summary = validate_map(component_map, contract)
    parent = load(args.parent_runtime)
    candidate = load(args.candidate_runtime)
    if parent.get("state") != contract["parent_current_world"]["required_runtime_state"]:
        raise ValueError("parent current-world runtime state drift")
    if len(parent.get("samples", [])) != 17 or len(candidate.get("samples", [])) != 17:
        raise ValueError("current-world runtime sample count drift")
    parent_samples = parent["samples"]
    candidate_samples = candidate["samples"]
    component_map_sha = sha256_file(args.component_map)

    receiver_rows: list[dict[str, Any]] = []
    for index, (before, after) in enumerate(zip(parent_samples, candidate_samples)):
        if int(before.get("index", -1)) != index or int(after.get("index", -1)) != index:
            raise ValueError("runtime state index sequence drift")
        for key in ("time_s", "weather_field_digest", "sapling_mesh_digest"):
            if before.get(key) != after.get(key):
                raise ValueError(f"unrelated current-world state drift at sample {index}: {key}")
        b_obj = _find_object(before)
        a_obj = _find_object(after)
        for key in (
            "source_head", "source_sha256", "source_scope", "vertices", "triangles", "surface_count",
            "material_profile_sha256", "materials_head", "material_ids", "proof_culling",
            "environment_object_selected_surface_segmentation", "environment_object_selected_uv0_current_world",
            "environment_object_selected_roughness_current_world",
        ):
            if b_obj.get(key) != a_obj.get(key):
                raise ValueError(f"existing Object receiver identity drift at sample {index}: {key}")
        obs = a_obj.get("environment_object_rigid_component_receiver")
        if not isinstance(obs, dict):
            raise ValueError(f"rigid component receiver observation missing at sample {index}")
        if obs.get("state") != TARGET_STATE:
            raise ValueError("rigid component receiver state drift")
        if obs.get("component_map_sha256") != component_map_sha:
            raise ValueError("candidate runtime is not bound to exact generated component map bytes")
        if int(obs.get("component_count", -1)) != map_summary["component_count"] or int(obs.get("triangles", -1)) != 812:
            raise ValueError("rigid component receiver cardinality drift")
        if obs.get("required_moving_components") != map_summary["required_moving_components"]:
            raise ValueError("rigid component receiver moving-boundary identity drift")
        if obs.get("animation_adoption") is not False or obs.get("vfx_adoption") is not False or obs.get("runtime_acceptance") is not False:
            raise ValueError("bounded Technical Art bridge silently widened downstream acceptance")
        receiver_rows.append(obs)

    parent_dir = Path(args.parent_frames)
    candidate_dir = Path(args.candidate_frames)
    parent_names = sorted(path.name for path in parent_dir.glob("atmosphere-width-*.png"))
    candidate_names = sorted(path.name for path in candidate_dir.glob("atmosphere-width-*.png"))
    if len(parent_names) != 68 or candidate_names != parent_names:
        raise ValueError(f"exact 68-frame neutral set drift: parent={len(parent_names)} candidate={len(candidate_names)}")
    changed_frames = 0
    changed_pixels = 0
    changed: list[dict[str, Any]] = []
    for name in parent_names:
        pixels, bbox = _pixel_difference(parent_dir / name, candidate_dir / name)
        if pixels:
            changed_frames += 1
            changed_pixels += pixels
            changed.append({"frame": name, "changed_pixels": pixels, "bbox": bbox})
    if changed_frames or changed_pixels:
        raise ValueError(f"neutral frame changed pixels: frames={changed_frames} pixels={changed_pixels} first={changed[:1]}")

    root_keys = (
        "weather_variant_head", "weather_variant_seed", "weather_variant_layout_digest",
        "environment_object_selected_roughness_current_world_state",
        "environment_object_selected_roughness_png_sha256",
        "environment_building_utility_panel_clearance_current_world_state",
        "environment_building_utility_panel_clearance_source_head",
    )
    for key in root_keys:
        if parent.get(key) != candidate.get(key):
            raise ValueError(f"current-world root identity drift: {key}")

    report = {
        "schema": REPORT_SCHEMA,
        "state": TARGET_STATE,
        "environment_head": args.environment_head,
        "parent_environment_head": contract["parent_current_world"]["head"],
        "technical_art_donor_head": contract["technical_art_donor"]["head"],
        "object_source_head": contract["object_source"]["head"],
        "object_source_sha256": contract["object_source"]["sha256"],
        "tested_uc_head": contract["uc"]["donor_head"],
        "inspected_current_uc_head": contract["uc"]["inspected_current_head"],
        "component_map_sha256": component_map_sha,
        "component_map": map_summary,
        "real_world_neutral_equivalence": {
            "states": 17,
            "frames": 68,
            "changed_frames": changed_frames,
            "changed_pixels": changed_pixels,
            "pixel_exact": True,
        },
        "receiver_observation": {
            "component_count": receiver_rows[0]["component_count"],
            "component_surface_instances": receiver_rows[0]["component_surface_instances"],
            "triangles": receiver_rows[0]["triangles"],
            "lid_hierarchy_edges": receiver_rows[0]["lid_hierarchy_edges"],
            "required_moving_components": receiver_rows[0]["required_moving_components"],
            "source_positions_reconstructed_at_neutral": receiver_rows[0]["source_positions_reconstructed_at_neutral"],
            "materials_reused": receiver_rows[0]["materials_reused"],
            "normals_reused": receiver_rows[0]["normals_reused"],
            "uv0_reused": receiver_rows[0]["uv0_reused"],
        },
        "environment_adoption": False,
        "animation_adoption": False,
        "vfx_adoption": False,
        "runtime_acceptance": False,
        "art_qa_acceptance": False,
        "canon": False,
        "truth_boundary": contract["truth_boundary"],
    }
    write(args.output, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare")
    p.add_argument("--contract", required=True)
    p.add_argument("--object-root", required=True)
    p.add_argument("--ta-receipt", required=True)
    p.add_argument("--ta-surface", required=True)
    p.add_argument("--uc-donor-root", required=True)
    p.add_argument("--uc-current-root", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--receipt", required=True)

    v = sub.add_parser("verify")
    v.add_argument("--contract", required=True)
    v.add_argument("--component-map", required=True)
    v.add_argument("--parent-runtime", required=True)
    v.add_argument("--candidate-runtime", required=True)
    v.add_argument("--parent-frames", required=True)
    v.add_argument("--candidate-frames", required=True)
    v.add_argument("--environment-head", required=True)
    v.add_argument("--output", required=True)

    m = sub.add_parser("validate-map")
    m.add_argument("--contract", required=True)
    m.add_argument("--component-map", required=True)

    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args)
    elif args.command == "verify":
        result = verify(args)
    else:
        contract = load(args.contract)
        result = validate_map(load(args.component_map), contract)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
