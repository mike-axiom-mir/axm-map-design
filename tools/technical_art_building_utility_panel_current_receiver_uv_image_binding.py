#!/usr/bin/env python3
"""Bind owner UV/image transport to the exact current Environment utility-panel receiver.

Technical Art owns only the receiving bridge. Building Hard Surface owns the manufactured
service frame, Geometry owns chart coordinates, Materials owns the retained review image
and atlas placement, and Environment owns the current-world receiver identity/placement.
UC remains a generic observer and is not modified by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "axm.technical-art-building-utility-panel-current-receiver-uv-image-binding/v0.1"
RESULT = "PASS_CURRENT_184V_BUILDING_RECEIVER_UTILITY_PANEL_SERVICE_FACE_UV_IMAGE_BINDING__HOLD_ENVIRONMENT_VISUAL_RUNTIME_ADOPTION"
EPS = 1e-9


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def add(a: list[float], b: list[float]) -> list[float]:
    return [float(x) + float(y) for x, y in zip(a, b)]


def mul(a: list[float], scale: float) -> list[float]:
    return [float(x) * float(scale) for x in a]


def dot(a: list[float], b: list[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        float(a[1]) * float(b[2]) - float(a[2]) * float(b[1]),
        float(a[2]) * float(b[0]) - float(a[0]) * float(b[2]),
        float(a[0]) * float(b[1]) - float(a[1]) * float(b[0]),
    ]


def norm(a: list[float]) -> float:
    return math.sqrt(dot(a, a))


def frame_ok(normal: list[float], lateral: list[float], up: list[float]) -> bool:
    return (
        abs(norm(normal) - 1.0) <= EPS
        and abs(norm(lateral) - 1.0) <= EPS
        and abs(norm(up) - 1.0) <= EPS
        and abs(dot(normal, lateral)) <= EPS
        and abs(dot(normal, up)) <= EPS
        and abs(dot(lateral, up)) <= EPS
        and dot(cross(normal, lateral), up) > 1.0 - EPS
    )


def map_chart_uv(chart_uv: list[float], image_size: list[int], origin: list[int], active: list[int]) -> list[float]:
    return [
        (float(origin[0]) + float(chart_uv[0]) * float(active[0])) / float(image_size[0]),
        (float(origin[1]) + float(chart_uv[1]) * float(active[1])) / float(image_size[1]),
    ]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binding-contract", required=True, type=Path)
    ap.add_argument("--environment-contract", required=True, type=Path)
    ap.add_argument("--pavilion-source", required=True, type=Path)
    ap.add_argument("--panel-source", required=True, type=Path)
    ap.add_argument("--surface-domain", required=True, type=Path)
    ap.add_argument("--geometry-chart", required=True, type=Path)
    ap.add_argument("--materials-contract", required=True, type=Path)
    ap.add_argument("--materials-profile", required=True, type=Path)
    ap.add_argument("--materials-provenance", required=True, type=Path)
    ap.add_argument("--materials-png", required=True, type=Path)
    ap.add_argument("--glb-helper", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--technical-art-head", required=True)
    ap.add_argument("--environment-head", required=True)
    ap.add_argument("--hard-surface-head", required=True)
    ap.add_argument("--geometry-head", required=True)
    ap.add_argument("--materials-head", required=True)
    ap.add_argument("--uc-head", required=True)
    ap.add_argument("--uc-module-blob", required=True)
    args = ap.parse_args()

    binding = load_json(args.binding_contract)
    environment = load_json(args.environment_contract)
    pavilion = load_json(args.pavilion_source)
    panel = load_json(args.panel_source)
    surface = load_json(args.surface_domain)
    chart = load_json(args.geometry_chart)
    materials = load_json(args.materials_contract)
    profile = load_json(args.materials_profile)
    provenance = load_json(args.materials_provenance)
    png = args.materials_png.read_bytes()

    require(binding.get("schema") == SCHEMA, "binding contract schema drift")
    require(environment.get("schema") == "axm.environment-building-utility-panel-clearance-current-world/v0.1", "Environment receiver contract drift")
    require(pavilion.get("schema") == "axm.building-hard-surface/v0.2", "Building source schema drift")
    require(panel.get("schema") == "axm.building-utility-panel/v0.1", "panel source schema drift")
    require(surface.get("schema") == "axm.building-utility-panel-service-surface-domain/v0.1", "service domain schema drift")
    require(chart.get("schema") == "axm.building-utility-panel-service-surface-chart/v0.1", "Geometry chart schema drift")
    require(materials.get("schema") == "axm.building-utility-panel-serialized-review-texture/v0.1", "Materials image contract drift")
    require(provenance.get("schema") == "axm.technical-art-materials-retained-image-provenance/v0.1", "retained image provenance drift")

    owners = binding["owner_bindings"]
    require(owners["environment"]["head"] == args.environment_head, "Environment exact head drift")
    require(owners["hard_surface"]["head"] == args.hard_surface_head, "Hard-Surface exact head drift")
    require(owners["geometry"]["head"] == args.geometry_head, "Geometry exact head drift")
    require(owners["materials"]["head"] == args.materials_head, "Materials continuity head drift")

    authority = environment["current_receiver_authority"]
    rebind = environment["receiver_rebind"]
    expected = binding["current_receiver_identity"]
    require(authority["current_source_variant_id"] == expected["variant_id"], "current receiver variant drift")
    require(authority["placement_translation_source_xyz_m"] == expected["placement_translation_source_xyz_m"], "current receiver placement drift")
    require(rebind["expected_vertex_count"] == expected["vertex_count"] == 184, "current receiver vertex count drift")
    require(rebind["expected_triangle_count"] == expected["triangle_count"] == 276, "current receiver triangle count drift")
    require(rebind["expected_surface_count"] == expected["surface_count"] == 5, "current receiver surface count drift")

    require(panel["orientation_contract"] == "panel local +X maps to receiver outward normal; local +Y maps receiver lateral; local +Z maps receiver up", "panel orientation contract drift")
    require(surface["face_selector"] == "LOCAL_POSITIVE_X_OUTER_FACE", "outer service face selector drift")
    require(surface["reference_frame"]["primary_axis_local"] == [0.0, 1.0, 0.0], "service primary axis drift")
    require(surface["reference_frame"]["secondary_axis_local"] == [0.0, 0.0, 1.0], "service secondary axis drift")
    require(surface["reference_frame"]["outward_axis_local"] == [1.0, 0.0, 0.0], "service outward axis drift")
    require(panel["proof_geometry"]["size_local_xyz_m"] == [0.08, 1.10, 1.50], "panel box extent drift")
    require(abs(float(surface["reference_frame"]["origin_local_m"][0]) - 0.04) <= EPS, "outer service face depth drift")

    interfaces = {row["id"]: row for row in pavilion["interfaces"]}
    current_groups = rebind["current_receiver_vertex_groups"]
    current_centers = rebind["successor_centers_current_receiver_xyz_m"]
    contract_panels = binding["panel_bindings"]
    require(set(contract_panels) == set(current_groups) == {"front-utility-bay", "east-utility-bay"}, "receiver panel identity drift")

    chart_rows = chart["vertices"]
    require([row["source_corner_index"] for row in chart_rows] == [0, 1, 2, 3], "Geometry source corner order drift")
    require([row["chart_uv"] for row in chart_rows] == [[0.0,0.0],[1.0,0.0],[1.0,1.0],[0.0,1.0]], "Geometry chart UV drift")
    require(chart["triangles"] == [[0,1,2],[0,2,3]], "Geometry chart triangle drift")
    require(surface["metric_domain"]["corner_positions_local_m"] == [[0.04,-0.55,-0.75],[0.04,0.55,-0.75],[0.04,0.55,0.75],[0.04,-0.55,0.75]], "Hard-Surface service corners drift")

    rt = materials["review_texture"]
    image_size = [int(v) for v in rt["image_size_px"]]
    active_origin = [int(v) for v in rt["active_region_origin_px"]]
    active_size = [int(v) for v in rt["active_region_px"]]
    require(image_size == [512,512] and active_origin == [80,16] and active_size == [352,480], "Materials atlas identity drift")
    require(provenance["materials_contract_blob_sha"] == owners["materials"]["serialized_contract_blob_sha"], "Materials retained contract provenance drift")
    require(provenance["materials_png_sha256"] == sha256(png), "retained Materials PNG digest drift")
    require(len(png) == int(provenance["materials_png_bytes"]), "retained Materials PNG byte count drift")
    require(materials["geometry_directional_sampling"]["head"] == args.geometry_head, "Materials no longer binds exact Geometry head")

    uv_corners = [map_chart_uv(row["chart_uv"], image_size, active_origin, active_size) for row in chart_rows]
    require(uv_corners == [[0.15625,0.03125],[0.84375,0.03125],[0.84375,0.96875],[0.15625,0.96875]], "exact atlas UV corner drift")

    all_positions: list[list[float]] = []
    all_uvs: list[list[float]] = []
    all_triangles: list[list[int]] = []
    panel_receipts: dict[str, Any] = {}
    placement = [float(v) for v in authority["placement_translation_source_xyz_m"]]
    local_offset_to_chart_corner = {4: 0, 6: 1, 7: 2, 5: 3}
    projection_order = [0, 3, 1, 2, 0, 3, 1, 2]

    for panel_id in ("front-utility-bay", "east-utility-bay"):
        interface = interfaces[panel_id]
        normal = [float(v) for v in interface["normal"]]
        lateral = [float(v) for v in interface["lateral"]]
        up = [float(v) for v in interface["up"]]
        require(frame_ok(normal, lateral, up), f"{panel_id} receiver frame drift")
        group = [int(v) for v in current_groups[panel_id]]
        expected_group = [int(v) for v in contract_panels[panel_id]["current_receiver_vertex_indices"]]
        require(group == expected_group and len(group) == 8, f"{panel_id} current receiver group drift")
        service_indices = [group[offset] for offset in (4,6,7,5)]
        require(service_indices == contract_panels[panel_id]["outer_service_face_receiver_vertex_indices"], f"{panel_id} exact outer service face index mapping drift")

        center_receiver = [float(v) for v in current_centers[panel_id]]
        center_source = [center_receiver[i] - placement[i] for i in range(3)]
        expected_source = [float(v) for v in rebind["successor_centers_source_xyz_m"][panel_id]]
        require(max(abs(a-b) for a,b in zip(center_source, expected_source)) <= EPS, f"{panel_id} receiver/source placement mismatch")

        face_center_receiver = add(center_receiver, mul(normal, 0.04))
        world_corners: list[list[float]] = []
        for row in chart_rows:
            s, t = [float(v) for v in row["metric_st_m"]]
            point = add(add(face_center_receiver, mul(lateral, s)), mul(up, t))
            world_corners.append([round(v, 12) for v in point])

        base_index = len(all_positions)
        all_positions.extend(world_corners)
        all_uvs.extend(uv_corners)
        all_triangles.extend([[base_index + i for i in tri] for tri in chart["triangles"]])

        projected_uv_by_receiver_vertex = {
            str(group[offset]): uv_corners[projection_order[offset]] for offset in range(8)
        }
        service_uv_by_receiver_vertex = {
            str(group[offset]): uv_corners[corner] for offset, corner in local_offset_to_chart_corner.items()
        }
        panel_receipts[panel_id] = {
            "current_receiver_center_xyz_m": center_receiver,
            "source_center_xyz_m": center_source,
            "outward_normal": normal,
            "lateral_axis": lateral,
            "up_axis": up,
            "current_receiver_vertex_indices": group,
            "outer_service_face_receiver_vertex_indices": service_indices,
            "outer_service_face_positions_current_receiver_xyz_m": world_corners,
            "outer_service_face_uv0": uv_corners,
            "full_box_planar_projection_uv0_by_receiver_vertex": projected_uv_by_receiver_vertex,
            "exact_service_face_uv0_by_receiver_vertex": service_uv_by_receiver_vertex,
            "non_service_face_projection_authority": "TECHNICAL_ART_RECEIVER_FILL_ONLY__NOT_SOURCE_OR_GEOMETRY_EQUIVALENCE",
        }

    mat = profile["candidate"][materials["material_role"]]
    helper = load_module(args.glb_helper, "axm_ta_existing_material_bridge")
    glb = helper.build_glb(
        positions=all_positions,
        uvs=all_uvs,
        triangles=all_triangles,
        png=png,
        metallic=float(mat["metallic"]),
        roughness=float(mat["roughness"]),
        asset_label="service-pavilion-current-receiver-utility-panel-service-faces",
    )

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    glb_path = out / "current-receiver-utility-panel-service-faces.glb"
    glb_path.write_bytes(glb)

    receipt = {
        "schema": SCHEMA,
        "result": RESULT,
        "technical_art_head": args.technical_art_head,
        "owner_bindings": {
            "environment": {"head": args.environment_head, "contract_sha256": sha256(args.environment_contract.read_bytes())},
            "hard_surface": {"head": args.hard_surface_head, "surface_domain_sha256": sha256(args.surface_domain.read_bytes())},
            "geometry": {"head": args.geometry_head, "chart_sha256": sha256(args.geometry_chart.read_bytes())},
            "materials": {"head": args.materials_head, "serialized_contract_sha256": sha256(args.materials_contract.read_bytes()), "retained_png_sha256": sha256(png)},
            "universal_creation": {"head": args.uc_head, "material_uv_module_blob": args.uc_module_blob, "modified": False},
        },
        "current_receiver_identity": expected,
        "surface_role": materials["material_role"],
        "atlas_uv_bounds": {"min": [0.15625,0.03125], "max": [0.84375,0.96875]},
        "directional_texels_per_m": [320.0, 320.0],
        "panel_bindings": panel_receipts,
        "proof_carrier": {
            "path": glb_path.name,
            "sha256": sha256(glb),
            "bytes": len(glb),
            "vertices": len(all_positions),
            "triangles": len(all_triangles),
            "positions_current_receiver_xyz_m": all_positions,
            "uv0": all_uvs,
        },
        "checks": {
            "exact_current_receiver_184v_276t_5surface_identity_bound": True,
            "two_exact_current_receiver_panel_groups_bound": True,
            "hard_surface_positive_x_service_face_preserved": True,
            "geometry_chart_corner_bijection_preserved": True,
            "materials_active_region_and_png_preserved": True,
            "front_and_east_service_faces_share_owner_chart_without_frame_guessing": True,
            "non_service_projection_marked_receiver_only": True,
            "uc_product_code_modified": False,
        },
        "promotion": {
            "environment_adoption": False,
            "runtime_acceptance": False,
            "art_direction_acceptance": False,
            "visual_qa_acceptance": False,
            "canon": False,
            "production_ready": False,
        },
        "truth_boundary": "PASS binds the exact owner service-face chart and retained Materials image to the two source-owned utility-panel instances of Environment's current 184-vertex / 276-triangle / 5-surface receiver using the explicit receiver frames and current clearance-successor centers. The four outer service-face corners are owner-equivalent. UV values projected onto the remaining box vertices exist only as a Technical-Art receiver fill so the existing five-surface representation can carry TEXCOORD_0 without a topology split; they are not promoted to source/Geometry authority or visual acceptance. UC is consumed only as a generic observer and is not modified. Environment adoption, final look, runtime/device acceptance, CANON and production readiness remain HOLD.",
    }
    (out / "current-receiver-utility-panel-uv-image-binding-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(RESULT)
    print(json.dumps({"glb_sha256": receipt["proof_carrier"]["sha256"], "front_service_indices": panel_receipts["front-utility-bay"]["outer_service_face_receiver_vertex_indices"], "east_service_indices": panel_receipts["east-utility-bay"]["outer_service_face_receiver_vertex_indices"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
