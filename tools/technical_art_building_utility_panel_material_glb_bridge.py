#!/usr/bin/env python3
"""Package exact owner-authored Building panel chart + review PNG into a bounded GLB carrier.

Technical Art owns only the transport/package boundary here. Source geometry, chart,
review image/style, material target, visual acceptance, runtime adoption and production
policy remain with their existing owners. The tool does not modify Universal Creation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any

SCHEMA = "axm.technical-art-building-utility-panel-material-glb-bridge/v0.1"
RESULT = "PASS_BUILDING_UTILITY_PANEL_EXACT_OWNER_UV_MATERIAL_IMAGE_PACKAGED_FOR_UC_OBSERVATION__HOLD_TARGET_IMPORT_VISUAL_RUNTIME"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def aligned(blob: bytearray, multiple: int = 4) -> None:
    while len(blob) % multiple:
        blob.append(0)


def glb_json_bytes(doc: dict[str, Any]) -> bytes:
    raw = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    while len(raw) % 4:
        raw += b" "
    return raw


def build_glb(
    *,
    positions: list[list[float]],
    uvs: list[list[float]],
    triangles: list[list[int]],
    png: bytes,
    metallic: float,
    roughness: float,
    asset_label: str,
) -> bytes:
    require(len(positions) == len(uvs) >= 3, "POSITION/TEXCOORD_0 vertex counts must match")
    flat_indices = [int(i) for tri in triangles for i in tri]
    require(len(flat_indices) % 3 == 0, "triangle index count must be divisible by three")
    require(max(flat_indices) < len(positions) and min(flat_indices) >= 0, "triangle index out of range")
    require(len(positions) < 65536, "bounded bridge uses UNSIGNED_SHORT indices")

    binary = bytearray()
    pos_offset = len(binary)
    for row in positions:
        require(len(row) == 3 and all(math.isfinite(float(v)) for v in row), "non-finite POSITION")
        binary += struct.pack("<3f", *map(float, row))
    pos_length = len(binary) - pos_offset
    aligned(binary)

    uv_offset = len(binary)
    for row in uvs:
        require(len(row) == 2 and all(math.isfinite(float(v)) for v in row), "non-finite TEXCOORD_0")
        binary += struct.pack("<2f", *map(float, row))
    uv_length = len(binary) - uv_offset
    aligned(binary)

    idx_offset = len(binary)
    for i in flat_indices:
        binary += struct.pack("<H", i)
    idx_length = len(binary) - idx_offset
    aligned(binary)

    image_offset = len(binary)
    binary += png
    image_length = len(png)
    logical_buffer_length = len(binary)
    aligned(binary)

    pmin = [min(row[axis] for row in positions) for axis in range(3)]
    pmax = [max(row[axis] for row in positions) for axis in range(3)]
    uvmin = [min(row[axis] for row in uvs) for axis in range(2)]
    uvmax = [max(row[axis] for row in uvs) for axis in range(2)]
    doc: dict[str, Any] = {
        "asset": {"version": "2.0", "generator": "AXM Technical Art bounded owner-transport bridge"},
        "scene": 0,
        "scenes": [{"name": "technical-art-proof-carrier", "nodes": [0]}],
        "nodes": [{"name": asset_label, "mesh": 0}],
        "meshes": [{
            "name": f"{asset_label}-surface",
            "primitives": [{
                "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
                "indices": 2,
                "material": 0,
                "mode": 4,
            }],
        }],
        "materials": [{
            "name": "utility_panel_ochre_review_transport_carrier",
            "pbrMetallicRoughness": {
                "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                "baseColorTexture": {"index": 0, "texCoord": 0},
                "metallicFactor": float(metallic),
                "roughnessFactor": float(roughness),
            },
            "doubleSided": True,
            "extras": {
                "axm_scope": "review-transport-carrier-only",
                "production_material": False,
            },
        }],
        "textures": [{"source": 0}],
        "images": [{"name": "materials-owned-serialized-review-checker", "mimeType": "image/png", "bufferView": 3}],
        "buffers": [{"byteLength": logical_buffer_length}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": pos_offset, "byteLength": pos_length, "target": 34962},
            {"buffer": 0, "byteOffset": uv_offset, "byteLength": uv_length, "target": 34962},
            {"buffer": 0, "byteOffset": idx_offset, "byteLength": idx_length, "target": 34963},
            {"buffer": 0, "byteOffset": image_offset, "byteLength": image_length},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(positions), "type": "VEC3", "min": pmin, "max": pmax},
            {"bufferView": 1, "componentType": 5126, "count": len(uvs), "type": "VEC2", "min": uvmin, "max": uvmax},
            {"bufferView": 2, "componentType": 5123, "count": len(flat_indices), "type": "SCALAR", "min": [min(flat_indices)], "max": [max(flat_indices)]},
        ],
    }
    j = glb_json_bytes(doc)
    total = 12 + 8 + len(j) + 8 + len(binary)
    return (
        struct.pack("<4sII", b"glTF", 2, total)
        + struct.pack("<I4s", len(j), b"JSON") + j
        + struct.pack("<I4s", len(binary), b"BIN\x00") + bytes(binary)
    )


def mapped_uvs(chart_vertices: list[dict[str, Any]], image_size: list[int], origin: list[int], active: list[int]) -> list[list[float]]:
    width, height = map(float, image_size)
    ox, oy = map(float, origin)
    sx, sy = map(float, active)
    out: list[list[float]] = []
    for row in chart_vertices:
        uv = row["chart_uv"]
        out.append([(ox + float(uv[0]) * sx) / width, (oy + float(uv[1]) * sy) / height])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface-domain", required=True, type=Path)
    ap.add_argument("--geometry-chart", required=True, type=Path)
    ap.add_argument("--geometry-sampling", required=True, type=Path)
    ap.add_argument("--materials-contract", required=True, type=Path)
    ap.add_argument("--materials-profile", required=True, type=Path)
    ap.add_argument("--materials-provenance", required=True, type=Path)
    ap.add_argument("--materials-png", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--technical-art-head", required=True)
    ap.add_argument("--hard-surface-head", required=True)
    ap.add_argument("--geometry-head", required=True)
    ap.add_argument("--materials-head", required=True)
    ap.add_argument("--uc-head", required=True)
    ap.add_argument("--uc-module-blob", required=True)
    args = ap.parse_args()

    surface = load_json(args.surface_domain)
    chart = load_json(args.geometry_chart)
    sampling = load_json(args.geometry_sampling)
    materials = load_json(args.materials_contract)
    profile = load_json(args.materials_profile)
    provenance = load_json(args.materials_provenance)
    png = args.materials_png.read_bytes()

    require(surface.get("schema") == "axm.building-utility-panel-service-surface-domain/v0.1", "surface-domain schema drift")
    require(chart.get("schema") == "axm.building-utility-panel-service-surface-chart/v0.1", "geometry chart schema drift")
    require(sampling.get("schema") == "axm.building-utility-panel-review-atlas-directional-sampling-rebind/v0.1", "geometry sampling schema drift")
    require(materials.get("schema") == "axm.building-utility-panel-serialized-review-texture/v0.1", "materials contract schema drift")
    require(provenance.get("schema") == "axm.technical-art-materials-retained-image-provenance/v0.1", "materials provenance schema drift")

    asset_id = "utility-access-panel-001"
    surface_id = "utility_panel_outer_service_surface"
    for owner, label in ((surface, "surface"), (chart, "chart"), (sampling, "sampling"), (materials, "materials")):
        require(owner.get("asset_id") == asset_id, f"{label} asset identity drift")
        require(owner.get("surface_id") == surface_id, f"{label} surface identity drift")

    require(materials["geometry_directional_sampling"]["head"] == args.geometry_head, "Materials does not bind exact Geometry head")
    require(sampling["geometry_chart"]["git_blob_sha"] == provenance["geometry_chart_blob_sha"], "Geometry chart blob provenance drift")
    require(materials["geometry_directional_sampling"]["contract_blob_sha"] == provenance["geometry_sampling_blob_sha"], "Geometry sampling blob provenance drift")
    require(provenance["materials_head"] == args.materials_head, "Materials head provenance drift")
    require(provenance["materials_png_sha256"] == sha256(png), "Materials serialized PNG byte identity drift")
    require(provenance["materials_png_bytes"] == len(png), "Materials serialized PNG size drift")

    rt = materials["review_texture"]
    require(rt["image_size_px"] == provenance["image_size_px"], "image dimensions drift")
    require(rt["directional_texels_per_m_by_chart_axis"] == [320.0, 320.0], "review density owner value drift")
    require(sampling["review_sampling_claim"]["directional_texels_per_m_by_chart_axis"] == [320.0, 320.0], "Geometry/Materials sampling handoff drift")
    require(sampling["evidence_transfer_boundary"]["material_bearing_glb_bound"] is False, "predecessor boundary already claims a GLB")
    require(sampling["evidence_transfer_boundary"]["uc_glb_observer_consumed"] is False, "predecessor boundary already claims UC consumption")

    positions = [[float(v) for v in row] for row in surface["metric_domain"]["corner_positions_local_m"]]
    chart_vertices = chart["vertices"]
    require(len(positions) == len(chart_vertices) == 4, "bounded panel bridge expects exact 4-corner owner surface")
    for index, row in enumerate(chart_vertices):
        require(row["source_corner_index"] == index, "source corner identity/order drift")
        require([positions[index][1], positions[index][2]] == [float(x) for x in row["metric_st_m"]], "Geometry metric chart no longer matches Hard Surface local frame")
    require(chart["triangles"] == [[0, 1, 2], [0, 2, 3]], "bounded source triangle connectivity drift")

    image_size = [int(x) for x in rt["image_size_px"]]
    active_origin = [int(x) for x in rt["active_region_origin_px"]]
    active_size = [int(x) for x in rt["active_region_px"]]
    uvs = mapped_uvs(chart_vertices, image_size, active_origin, active_size)
    expected_bounds = [
        active_origin[0] / image_size[0],
        active_origin[1] / image_size[1],
        (active_origin[0] + active_size[0]) / image_size[0],
        (active_origin[1] + active_size[1]) / image_size[1],
    ]
    require([min(x[0] for x in uvs), min(x[1] for x in uvs), max(x[0] for x in uvs), max(x[1] for x in uvs)] == expected_bounds, "active-region UV mapping drift")

    mat = profile["candidate"][materials["material_role"]]
    metallic, roughness = float(mat["metallic"]), float(mat["roughness"])
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    glb_path = out / "utility-panel-material-review-transport.glb"
    negative_path = out / "utility-panel-material-review-transport-aspect-blind-negative.glb"
    glb = build_glb(positions=positions, uvs=uvs, triangles=chart["triangles"], png=png,
                    metallic=metallic, roughness=roughness, asset_label=asset_id)
    negative_uvs = [[float(row["chart_uv"][0]), float(row["chart_uv"][1])] for row in chart_vertices]
    negative_glb = build_glb(positions=positions, uvs=negative_uvs, triangles=chart["triangles"], png=png,
                             metallic=metallic, roughness=roughness, asset_label=f"{asset_id}-aspect-blind-negative")
    glb_path.write_bytes(glb)
    negative_path.write_bytes(negative_glb)

    owner_density = [active_size[0] / float(surface["metric_domain"]["primary_extent_m"]),
                     active_size[1] / float(surface["metric_domain"]["secondary_extent_m"])]
    negative_density = [image_size[0] / float(surface["metric_domain"]["primary_extent_m"]),
                        image_size[1] / float(surface["metric_domain"]["secondary_extent_m"])]
    require(all(abs(v - 320.0) <= 1e-12 for v in owner_density), "owner active-region density arithmetic drift")

    receipt = {
        "schema": SCHEMA,
        "result": RESULT,
        "technical_art_head": args.technical_art_head,
        "owner_bindings": {
            "hard_surface": {"head": args.hard_surface_head, "surface_domain_schema": surface["schema"]},
            "geometry": {"head": args.geometry_head, "chart_blob_sha": provenance["geometry_chart_blob_sha"], "sampling_blob_sha": provenance["geometry_sampling_blob_sha"]},
            "materials": {
                "head": args.materials_head,
                "artifact_id": provenance["materials_artifact_id"],
                "workflow_run": provenance["materials_workflow_run"],
                "artifact_sha256": provenance["materials_artifact_sha256"],
                "serialized_png_sha256": provenance["materials_png_sha256"],
                "serialized_png_bytes": provenance["materials_png_bytes"],
                "base_rgba8_sha256": provenance["base_rgba8_sha256"],
            },
            "universal_creation": {"head": args.uc_head, "module_path": "src/axm_uc/material_uv_evidence.py", "module_blob_sha": args.uc_module_blob, "api": "inspect_material_uv_density"},
        },
        "transport": {
            "position_source": "Hard-Surface exact local service-surface corner_positions_local_m",
            "triangle_source": "Geometry exact chart triangles",
            "chart_uv_source": "Geometry exact normalized chart_uv",
            "atlas_mapping_source": "Materials exact active_region_origin_px/active_region_px/image_size_px",
            "material_role": materials["material_role"],
            "texture_slot": "baseColorTexture/TEXCOORD_0",
            "texture_transform": None,
            "embedded_image_mime_type": "image/png",
            "proof_carrier_double_sided": True,
            "source_or_production_material_policy_changed": False,
        },
        "artifact": {"path": glb_path.name, "bytes": len(glb), "sha256": sha256(glb), "uv_bounds": expected_bounds, "triangles": 2, "vertices": 4},
        "negative_artifact": {"path": negative_path.name, "bytes": len(negative_glb), "sha256": sha256(negative_glb), "purpose": "FULL_SQUARE_NORMALIZED_CHART_IGNORES_MATERIALS_ACTIVE_REGION"},
        "owner_sampling_expectation": {
            "physical_extent_m_by_chart_axis": [surface["metric_domain"]["primary_extent_m"], surface["metric_domain"]["secondary_extent_m"]],
            "embedded_image_size_px": image_size,
            "active_region_px": active_size,
            "active_uv_span": [active_size[0] / image_size[0], active_size[1] / image_size[1]],
            "directional_texels_per_m_by_chart_axis": owner_density,
            "anisotropy_ratio": max(owner_density) / min(owner_density),
            "negative_full_square_texels_per_m_by_chart_axis": negative_density,
            "negative_full_square_anisotropy_ratio": max(negative_density) / min(negative_density),
        },
        "promotion": {
            "uc_observer_consumed_in_this_builder": False,
            "target_host_import_proven_in_this_builder": False,
            "materials_review_target_changed": False,
            "production_uv_adopted": False,
            "production_texture_adopted": False,
            "runtime_adoption": False,
            "environment_adoption": False,
            "art_direction_acceptance": False,
            "visual_qa_acceptance": False,
            "canon": False,
            "production_ready": False,
        },
        "truth_boundary": "Technical Art packages the exact Hard-Surface metric face, current Geometry chart, and exact retained Materials serialized-review PNG into one bounded material-bearing GLB carrier so the generic UC observer and a real target host can inspect transport. The carrier does not become source truth, choose any density/style/atlas policy, change UC, authorize source or runtime adoption, or establish visual/CANON/production readiness.",
    }
    (out / "technical-art-material-glb-bridge-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(RESULT)
    print(json.dumps({"glb_sha256": receipt["artifact"]["sha256"], "glb_bytes": receipt["artifact"]["bytes"], "owner_density": owner_density}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
