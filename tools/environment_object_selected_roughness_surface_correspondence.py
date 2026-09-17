from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

CONTRACT_SCHEMA = "axm.environment-object-selected-roughness-surface-correspondence/v0.1"
RESULT_SCHEMA = "axm.environment-object-selected-roughness-surface-correspondence-result/v0.1"
HOLD_STATE = "HOLD_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_RECEIVER__SOURCE_SERVICE_SURFACE_SEGMENTATION_AND_UV0_BINDING_NOT_PRESENT"
RULE = "SPATIAL_MATERIAL_FIELD_REQUIRES_EXACT_SOURCE_SURFACE_SEGMENTATION_BEFORE_UV_BINDING_OR_TEXTURE_ADOPTION"
OBJECT_ASSET_ID = "source:object:modular-equipment-case-001"
OWNER_HEAD = "f7c64d08e4e2a0d6954291d8b4e064d7345ab658"
SOURCE_SHA = "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
MATERIALS_HEAD = "0515a2d5ad2c7a1eb545f2b7b327b7367530dfca"
CURRENT_MATERIALS_HEAD = "c85517446a769e0d5f880fc0e9e32f47124f7b5e"
CURRENT_PROFILE_SHA = "dc200229d6c25fa84063aa51f66103abc022efa54b2167e4432a5b47fc40360c"
READINESS_HEAD = "1fcc9727012d156f8d1c4658c8dca4f0e9dd3c33"
ACCEPTED_WORLD_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
SELECTED_SCALAR = "b8d13c07f9b71278042b0d42d44b84579a3f327c6adf6723cae4c8c8f06dd38e"
EXPECTED_COUNTS = {
    "shell_coating": 24,
    "service_dark": 12,
    "hardware_steel": 656,
    "rubber_guard": 96,
    "interface_orange": 24,
}


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_generator(path: str | Path):
    spec = importlib.util.spec_from_file_location("axm_object_owner_generator", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load exact Object source generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_object(rows: Any) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise ValueError("scene additional_source_meshes missing")
    matches = [row for row in rows if isinstance(row, dict) and row.get("asset_id") == OBJECT_ASSET_ID]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one Object source in scene, got {len(matches)}")
    return matches[0]


def select_component_face(result: dict[str, Any], component_name: str, selector: str) -> list[int]:
    mesh = result["mesh"]
    groups = [g for g in mesh["groups"] if g["name"] == component_name]
    if len(groups) != 1:
        raise ValueError(f"source component group missing or ambiguous: {component_name}")
    group = groups[0]
    first = int(group["first_face"])
    count = int(group["face_count"])
    if count != 12:
        raise ValueError(f"selected manufactured surface requires exact box component: {component_name}")
    axis_map = {"source_local_min_y_face": 1, "source_local_min_z_face": 2}
    if selector not in axis_map:
        raise ValueError(f"unsupported exact source selector: {selector}")
    axis = axis_map[selector]
    faces = mesh["faces"][first:first + count]
    vertex_ids = sorted({idx for face in faces for idx in face})
    minimum = min(float(mesh["vertices"][idx][axis]) for idx in vertex_ids)
    selected: list[int] = []
    for offset, face in enumerate(faces):
        if all(abs(float(mesh["vertices"][idx][axis]) - minimum) <= 1e-12 for idx in face):
            selected.append(first + offset)
    if len(selected) != 2:
        raise ValueError(f"exact source selector did not resolve two triangles: {component_name} -> {selected}")
    return selected


def verify_owner(source_path: Path, generator_path: Path, lid_path: Path, front_path: Path, frames_path: Path, metric_path: Path) -> tuple[dict[str, Any], dict[str, list[int]]]:
    source = load(source_path)
    lid = load(lid_path)
    front = load(front_path)
    frames = load(frames_path)
    metric = load(metric_path)
    if source.get("asset_id") != "modular-equipment-case-001":
        raise ValueError("Object owner source identity drift")
    for contract in (lid, front, frames, metric):
        if contract.get("host_source_sha256") != SOURCE_SHA:
            raise ValueError("Object source-surface authority host identity drift")
    if lid.get("surface_id") != "lid_inner_service_surface" or lid.get("component_name") != "lid_shell":
        raise ValueError("lid service-surface identity drift")
    if front.get("surface_id") != "front_service_panel_outer_service_surface" or front.get("component_name") != "front_service_panel":
        raise ValueError("front service-surface identity drift")
    generator = load_generator(generator_path)
    built = generator.build(source)
    if len(built["mesh"]["vertices"]) != 468 or len(built["mesh"]["faces"]) != 812:
        raise ValueError("exact Object owner generator topology drift")
    selected = {
        lid["surface_id"]: select_component_face(built, lid["component_name"], lid["selector"]["policy"]),
        front["surface_id"]: select_component_face(built, front["component_name"], front["selector"]["policy"]),
    }
    frame_rows = {row["surface_id"]: row for row in frames.get("frames", [])}
    if set(frame_rows) != set(selected):
        raise ValueError("source-owned service-surface frame coverage drift")
    domain_rows = {row["surface_id"]: row for row in metric.get("domains", [])}
    if set(domain_rows) != set(selected):
        raise ValueError("source-owned service-surface metric-domain coverage drift")
    return built, selected


def verify_materials(atlas: dict[str, Any], selected_ids: set[str]) -> dict[str, Any]:
    if atlas.get("schema") != "axm.object-service-dark-atlas-pack-review/v0.1":
        raise ValueError("Materials atlas contract schema drift")
    rows = atlas.get("surfaces")
    if not isinstance(rows, list) or {row.get("surface_id") for row in rows} != selected_ids:
        raise ValueError("Materials atlas no longer targets exact two source-owned service surfaces")
    expected_basis = {
        "lid_inner_service_surface": "SOURCE_LOCAL_X_TO_U__SOURCE_LOCAL_Y_TO_V",
        "front_service_panel_outer_service_surface": "SOURCE_LOCAL_X_TO_U__SOURCE_LOCAL_Z_TO_V",
    }
    for row in rows:
        if row.get("basis") != expected_basis[row["surface_id"]]:
            raise ValueError("Materials atlas source-basis drift")
    return {"surface_count": 2, "surface_ids": sorted(selected_ids), "atlas_size_px": [atlas["atlas"]["width_px"], atlas["atlas"]["height_px"]], "pixels_per_meter": atlas["atlas"]["pixels_per_meter"]}


def verify_current_world(combined: dict[str, Any], selected: dict[str, list[int]], owner_faces: list[Any]) -> dict[str, Any]:
    if combined.get("environment_head") != ACCEPTED_WORLD_HEAD:
        raise ValueError("accepted real-scene Environment head drift")
    states = combined.get("states")
    if not isinstance(states, list) or len(states) != 17:
        raise ValueError("accepted real world must retain 17 states")
    observations = []
    canonical_partition = None
    for state in states:
        obj = find_object(state.get("scene", {}).get("additional_source_meshes"))
        if obj.get("source_sha256") != SOURCE_SHA:
            raise ValueError("current-world Object source identity drift")
        if obj.get("triangles") != [list(face) for face in owner_faces]:
            raise ValueError("current-world Object triangle identity/order drift from exact source owner")
        proof = obj.get("object_material_family_receiving")
        if not isinstance(proof, dict):
            raise ValueError("current-world Object material receiving proof missing")
        if proof.get("materials_head") != CURRENT_MATERIALS_HEAD or proof.get("material_profile_sha256") != CURRENT_PROFILE_SHA:
            raise ValueError("current Map Object material-family identity drift")
        partition = proof.get("surface_triangle_indices")
        if not isinstance(partition, dict) or {k: len(v) for k, v in partition.items()} != EXPECTED_COUNTS:
            raise ValueError("current Map Object material partition cardinality drift")
        if canonical_partition is None:
            canonical_partition = partition
        elif partition != canonical_partition:
            raise ValueError("static Object material partition changed across Weather/Nature states")
    assert canonical_partition is not None
    reverse: dict[int, str] = {}
    for material_id, indices in canonical_partition.items():
        for raw in indices:
            idx = int(raw)
            if idx in reverse:
                raise ValueError("current Map Object material partition overlaps")
            reverse[idx] = material_id
    if len(reverse) != 812:
        raise ValueError("current Map Object material partition does not cover exact host")
    for surface_id, indices in selected.items():
        materials = sorted({reverse[idx] for idx in indices})
        observations.append({"surface_id": surface_id, "source_triangle_indices": indices, "current_material_ids": materials})
    lid_materials = next(row["current_material_ids"] for row in observations if row["surface_id"] == "lid_inner_service_surface")
    front_materials = next(row["current_material_ids"] for row in observations if row["surface_id"] == "front_service_panel_outer_service_surface")
    if lid_materials != ["shell_coating"]:
        raise ValueError("expected exact current lid-inner receiver to remain in shell_coating surface")
    if front_materials != ["service_dark"]:
        raise ValueError("expected exact current front service face to remain in service_dark surface")
    selected_all = {idx for values in selected.values() for idx in values}
    service_indices = {int(x) for x in canonical_partition["service_dark"]}
    selected_service = set(selected["front_service_panel_outer_service_surface"])
    extras = sorted(service_indices - selected_service)
    if len(extras) != 10 or selected_service - service_indices:
        raise ValueError("current service_dark surface is no longer exact whole-panel twelve-triangle receiver")
    lid_indices = set(selected["lid_inner_service_surface"])
    shell_indices = {int(x) for x in canonical_partition["shell_coating"]}
    if not lid_indices.issubset(shell_indices):
        raise ValueError("current lid-inner triangles no longer reside in shell_coating")
    return {
        "states_verified": 17,
        "source_service_surface_observations": observations,
        "selected_source_triangle_count": len(selected_all),
        "current_service_dark_triangle_count": len(service_indices),
        "current_service_dark_selected_target_triangle_count": len(selected_service),
        "current_service_dark_extra_nonselected_triangle_count": len(extras),
        "current_service_dark_extra_source_triangle_indices": extras,
        "lid_inner_currently_in_service_dark": False,
        "front_outer_currently_in_service_dark": True,
        "exact_two_surface_material_segmentation_present": False,
    }


def verify_readiness(report: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    if report.get("environment_head") != READINESS_HEAD:
        raise ValueError("selected-roughness readiness head drift")
    if report.get("real_scene_frame_continuity", {}).get("byte_identical_frames") != 68:
        raise ValueError("real-scene readiness frame continuity drift")
    if report.get("weather_width_continuity", {}).get("measurements") != 1224:
        raise ValueError("Weather continuity evidence drift")
    uv = report.get("receiver_uv0", {})
    if uv.get("total_uv0_count") != 0 or uv.get("all_surfaces_uv0_absent") is not True:
        raise ValueError("current receiver UV0 state changed; re-evaluate this correspondence HOLD")
    if runtime.get("environment_object_selected_roughness_readiness_state") != "HOLD_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_RECEIVER__EXACT_UV0_BINDING_NOT_PRESENT":
        raise ValueError("real Godot readiness runtime identity drift")
    return {
        "real_godot_frames": 68,
        "weather_width_measurements": 1224,
        "maximum_weather_width_residual_px": report["weather_width_continuity"]["maximum_projected_width_residual_px"],
        "receiver_uv0_count": 0,
        "readiness_artifact_state": report["state"],
    }


def verify(args: argparse.Namespace) -> dict[str, Any]:
    contract = load(args.contract)
    if contract.get("schema") != CONTRACT_SCHEMA or contract.get("decision", {}).get("state") != HOLD_STATE:
        raise ValueError("Environment surface-correspondence contract drift")
    if contract.get("reusable_rule") != RULE or contract.get("decision", {}).get("environment_adoption") is not False:
        raise ValueError("Environment surface-correspondence authority boundary drift")
    if contract.get("source_surface_authority", {}).get("head") != OWNER_HEAD:
        raise ValueError("Object source-surface owner head drift")
    if contract.get("selected_materials_authority", {}).get("head") != MATERIALS_HEAD:
        raise ValueError("selected Materials head drift")
    if contract.get("selected_materials_authority", {}).get("selected_scalar_r8_sha256") != SELECTED_SCALAR:
        raise ValueError("selected roughness scalar drift")

    built, selected = verify_owner(Path(args.object_source), Path(args.object_generator), Path(args.lid_contract), Path(args.front_contract), Path(args.frames_contract), Path(args.metric_contract))
    materials = verify_materials(load(args.atlas_contract), set(selected))
    world = verify_current_world(load(args.combined_world), selected, built["mesh"]["faces"])
    readiness = verify_readiness(load(args.readiness_report), load(args.readiness_runtime))

    report = {
        "schema": RESULT_SCHEMA,
        "state": HOLD_STATE,
        "environment_head": args.environment_head,
        "object_source_surface_authority_head": OWNER_HEAD,
        "selected_materials_head": MATERIALS_HEAD,
        "selected_scalar_r8_sha256": SELECTED_SCALAR,
        "current_receiver_materials_head": CURRENT_MATERIALS_HEAD,
        "current_receiver_material_profile_sha256": CURRENT_PROFILE_SHA,
        "source_surface_triangle_indices": selected,
        "materials_selected_surface_contract": materials,
        "current_world_receiver_correspondence": world,
        "real_scene_evidence": readiness,
        "environment_adoption": False,
        "reusable_rule": RULE,
        "next_receiving_requirement": contract["decision"]["next_receiving_requirement"],
        "checks": {
            "exact_source_owner_generator_rebuilt": True,
            "exact_source_surface_identities_frames_and_metric_domains_bound": True,
            "exact_materials_two_surface_atlas_contract_bound": True,
            "all_17_current_world_states_preserve_exact_object_topology_and_partition": True,
            "lid_inner_target_is_currently_shell_coating_not_service_dark": True,
            "front_outer_target_is_only_two_of_twelve_current_service_dark_triangles": True,
            "exact_two_surface_receiver_segmentation_is_absent": True,
            "current_receiver_uv0_is_still_absent": True,
            "real_68_frame_godot_and_1224_weather_measurement_evidence_bound": True,
            "environment_adoption_remains_false": True,
        },
        "truth_boundary": (
            "This HOLD refines the receiving diagnosis: the selected spatial roughness field is blocked not only by missing UV0, but by missing exact source-surface segmentation in the real Map receiver. The exact lid-inner target remains inside shell_coating, while service_dark is the entire 12-triangle front-panel component and only two of those triangles are the source-owned front service target. No scene, material scalar, UV, texture, source geometry, Nature, Weather, Building, Object placement, Art/QA decision, Runtime acceptance, CANON or production state is changed."
        ),
    }
    if not all(report["checks"].values()):
        raise ValueError("surface-correspondence checks unexpectedly false")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("verify")
    for name in ("contract", "object_source", "object_generator", "lid_contract", "front_contract", "frames_contract", "metric_contract", "atlas_contract", "combined_world", "readiness_report", "readiness_runtime", "environment_head", "output"):
        p.add_argument("--" + name.replace("_", "-"), required=True)
    args = parser.parse_args()
    if args.command == "verify":
        report = verify(args)
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
