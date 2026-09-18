from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "axm.environment-building-utility-panel-material-receiver-readiness/v0.1"
RESULT = "HOLD_CURRENT_WORLD_BUILDING_UTILITY_PANEL_MATERIAL_RECEIVER__CURRENT_184V_RECEIVER_HAS_NO_EXACT_UV0_IMAGE_TRANSPORT_BINDING"
RULE = "EXACT_MATERIAL_ROLE_AND_PANEL_PLACEMENT_DO_NOT_AUTHORIZE_WORLD_TEXTURE_ADOPTION_WITHOUT_AN_EXACT_RECEIVER_UV0_IMAGE_TRANSPORT_BOUNDARY"

EXPECTED_PARENT_REVIEW_HEAD = "07f04aa9b5d1620907240acb12c97759fd7c77f4"
EXPECTED_RENDER_HEAD = "7cceec9f3e55a71f51ec227301a92e1896ea2d74"
EXPECTED_TA_HEAD = "457c086d27f3a9c010b365fe75d54b8f812b01ef"
EXPECTED_HARD_SURFACE_HEAD = "fbfa3b47048755b45dac91451171d5511c8d4f47"
EXPECTED_GEOMETRY_HEAD = "02944a9f10528a051603df3a6fd7b3183730773f"
EXPECTED_MATERIALS_HEAD = "5f096369eee2ef44275ea8f1c7dc1b6e564e71c8"
EXPECTED_GLB_SHA256 = "dc65fec67aa6aba4e4a14895b38122ae89b6eafba7f256b07c1a7c9e344bbd68"
EXPECTED_PNG_SHA256 = "e932cdd94d370184c7361862d5064149cc193e3a8fd80b269cab6543c0919198"
EXPECTED_RGBA_SHA256 = "02f8f464eabc734a3be687a7706edf8b8f62ece834fa981c8c993fbb8227bb4b"
EXPECTED_CURRENT_MATERIAL_PROFILE_SHA256 = "370484f92c2393b3f3147e6ce3df851bc4e51d421acb33c3d8687620c967e7df"
EXPECTED_CURRENT_VARIANT = "header-segmented-23"
EXPECTED_SEGMENTATION_REVISION = "service-pavilion-001/interpenetration-free-header-segmentation-003"
EXPECTED_BUILDING_ASSET = "source:building:service-pavilion-001"
EXPECTED_ROLES = [
    "frame_galvanized",
    "infill_coating",
    "roof_membrane",
    "slab_mineral",
    "utility_panel_ochre",
]
EXPECTED_UVS = [
    [0.15625, 0.03125],
    [0.84375, 0.03125],
    [0.84375, 0.96875],
    [0.15625, 0.96875],
]
EXPECTED_CLEARANCE_STATE = "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_CLEARANCE_REBIND_RECEIVER__VISUAL_OBSERVABILITY_CHARACTERIZED__ADOPTION_HELD"
EXPECTED_ASSETS = {
    "source:nature:compact-east-tree-neutral-001",
    "source:nature:east-rear-tree-neutral-001",
    "source:object:modular-equipment-case-001",
    "source:building:service-pavilion-001",
    "environment:dressing:west-object-service-footprint-frame-001",
}
UV_TRANSPORT_KEYS = (
    "uv",
    "texcoord",
    "texture",
    "image",
    "base_color_texture",
    "albedo_texture",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_files(root: Path) -> Iterable[Path]:
    yield from sorted(root.rglob("*.json"))


def find_world_runtimes(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    out: list[tuple[Path, dict[str, Any]]] = []
    for path in json_files(root):
        try:
            data = load(path)
        except Exception:
            continue
        samples = data.get("samples")
        if not isinstance(samples, list) or len(samples) != 17:
            continue
        good = True
        for sample in samples:
            rows = sample.get("static_source_meshes", []) if isinstance(sample, dict) else []
            if not isinstance(rows, list):
                good = False
                break
            ids = {row.get("asset_id") for row in rows if isinstance(row, dict)}
            if not EXPECTED_ASSETS.issubset(ids):
                good = False
                break
            buildings = [
                row
                for row in rows
                if isinstance(row, dict) and row.get("asset_id") == EXPECTED_BUILDING_ASSET
            ]
            if len(buildings) != 1:
                good = False
                break
            building = buildings[0]
            if (
                int(building.get("vertices", -1)),
                int(building.get("triangles", -1)),
                int(building.get("surface_count", -1)),
            ) != (184, 276, 5):
                good = False
                break
            if building.get("material_ids") != EXPECTED_ROLES:
                good = False
                break
        if good:
            out.append((path, data))
    return out


def verify_world(root: Path) -> dict[str, Any]:
    runtimes = find_world_runtimes(root)
    if len(runtimes) < 4:
        raise AssertionError(
            f"expected at least four exact retained current-world runtime receipts, found {len(runtimes)}"
        )
    state_count = 0
    weather_measurements = 0
    building_transport_keys: set[str] = set()
    material_profiles: set[str] = set()
    observed_names: list[str] = []
    for path, data in runtimes:
        observed_names.append(str(path.relative_to(root)))
        if data.get("environment_building_current_source_variant_id") != EXPECTED_CURRENT_VARIANT:
            raise AssertionError("current Building source variant drift")
        if data.get("environment_building_header_segmentation_revision") != EXPECTED_SEGMENTATION_REVISION:
            raise AssertionError("current Building segmentation revision drift")
        if data.get("environment_building_utility_panel_clearance_current_world_state") != EXPECTED_CLEARANCE_STATE:
            raise AssertionError("current Building clearance receiver state drift")
        if data.get("environment_building_utility_panel_clearance_adoption") is not False:
            raise AssertionError("historical Building Environment adoption unexpectedly true")
        for sample in data["samples"]:
            state_count += 1
            rows = sample["static_source_meshes"]
            building = [row for row in rows if row.get("asset_id") == EXPECTED_BUILDING_ASSET][0]
            material_profiles.add(str(building.get("material_profile_sha256")))
            observation = building.get(
                "environment_building_utility_panel_clearance_current_world", {}
            )
            if (
                observation.get("state") != EXPECTED_CLEARANCE_STATE
                or observation.get("environment_adoption") is not False
            ):
                raise AssertionError("nested Building clearance identity/adoption drift")
            if building.get("header_segmentation_revision") != EXPECTED_SEGMENTATION_REVISION:
                raise AssertionError("Building runtime segmented revision drift")

            def collect(value: Any, prefix: str = "") -> None:
                if isinstance(value, dict):
                    for key, nested in value.items():
                        low = str(key).lower()
                        if any(token in low for token in UV_TRANSPORT_KEYS):
                            building_transport_keys.add(prefix + str(key))
                        collect(nested, prefix + str(key) + ".")
                elif isinstance(value, list):
                    for index, nested in enumerate(value):
                        collect(nested, prefix + f"[{index}].")

            collect(building)
            for context in ("path_eye", "elevated_oblique"):
                candidate = sample.get("contexts", {}).get(context, {}).get("candidate", {})
                weather = candidate.get("weather_update", {})
                weather_measurements += int(weather.get("measured_width_count", 0))

    if material_profiles != {EXPECTED_CURRENT_MATERIAL_PROFILE_SHA256}:
        raise AssertionError(f"current world material profile identity drift: {material_profiles}")
    if building_transport_keys:
        raise AssertionError(
            "current Building runtime receipt unexpectedly exposes UV/image transport keys: "
            + repr(sorted(building_transport_keys))
        )
    if weather_measurements < 1224 * 4:
        raise AssertionError(
            f"expected retained Weather evidence across at least four runtime packets, got {weather_measurements}"
        )
    return {
        "runtime_receipts": observed_names,
        "runtime_receipt_count": len(runtimes),
        "world_state_observations": state_count,
        "weather_width_measurements": weather_measurements,
        "current_building_vertices": 184,
        "current_building_triangles": 276,
        "current_building_surfaces": 5,
        "current_material_roles": EXPECTED_ROLES,
        "current_material_profile_sha256": EXPECTED_CURRENT_MATERIAL_PROFILE_SHA256,
        "current_runtime_uv_or_image_transport_keys": [],
        "assets_present": sorted(EXPECTED_ASSETS),
    }


def verify_receiver_source(header_script: Path, clearance_script: Path) -> dict[str, Any]:
    header = header_script.read_text(encoding="utf-8")
    clearance = clearance_script.read_text(encoding="utf-8")
    required = (
        "st.add_vertex",
        "st.generate_normals()",
        "mesh.surface_set_material",
        "vertices.size()!=184",
        "triangle_count!=276",
    )
    for token in required:
        if token not in header:
            raise AssertionError(f"current segmented Building builder witness missing: {token}")
    forbidden = (
        "st.set_uv",
        "ARRAY_TEX_UV",
        "TEXCOORD_0",
        "albedo_texture",
        "base_color_texture",
    )
    found = [token for token in forbidden if token in header]
    if found:
        raise AssertionError(
            f"current segmented Building builder unexpectedly contains UV/image transport operations: {found}"
        )
    if (
        'proof["vertices_source_xyz_m"]=vertices' not in clearance
        or "super.add_segmented_building(root3d,patched)" not in clearance
    ):
        raise AssertionError(
            "current utility-panel clearance receiver no longer delegates the patched positions into segmented builder"
        )
    if '"material_values_changed":false' not in clearance:
        raise AssertionError("current utility-panel clearance material-value hold witness missing")
    found_clearance = [token for token in forbidden if token in clearance]
    if found_clearance:
        raise AssertionError(
            f"clearance layer unexpectedly authors UV/image transport: {found_clearance}"
        )
    return {
        "segmented_builder": str(header_script),
        "clearance_layer": str(clearance_script),
        "segmented_builder_uv_write_operations": [],
        "clearance_layer_uv_write_operations": [],
        "segmented_builder_material_binding_present": True,
        "clearance_delegates_to_segmented_builder": True,
    }


def verify_ta(root: Path) -> dict[str, Any]:
    final = root / "evidence/technical_art_building_utility_panel_material_glb/final"
    exact = load(final / "exact-path-receipt.json")
    bridge = load(final / "technical-art-material-glb-bridge-receipt.json")
    target = load(final / "godot-target-host-receipt.json")
    glb = final / "utility-panel-material-review-transport.glb"
    if (
        exact.get("result")
        != "PASS_EXACT_OWNER_UV_MATERIAL_IMAGE_TO_CURRENT_UC_AND_REAL_GODOT__HOLD_VISUAL_RUNTIME_ADOPTION"
    ):
        raise AssertionError("TA exact owner->Godot result drift")
    if (
        exact.get("technical_art_head") != EXPECTED_TA_HEAD
        or bridge.get("technical_art_head") != EXPECTED_TA_HEAD
    ):
        raise AssertionError("TA head drift")
    owners = bridge.get("owner_bindings", {})
    if owners.get("hard_surface", {}).get("head") != EXPECTED_HARD_SURFACE_HEAD:
        raise AssertionError("Hard Surface owner drift")
    if owners.get("geometry", {}).get("head") != EXPECTED_GEOMETRY_HEAD:
        raise AssertionError("Geometry owner drift")
    if owners.get("materials", {}).get("head") != EXPECTED_MATERIALS_HEAD:
        raise AssertionError("Materials owner drift")
    if bridge.get("artifact", {}).get("sha256") != EXPECTED_GLB_SHA256 or sha256(glb) != EXPECTED_GLB_SHA256:
        raise AssertionError("material carrier GLB identity drift")
    if (
        exact.get("materials_png_sha256") != EXPECTED_PNG_SHA256
        or exact.get("godot_imported_rgba8_sha256") != EXPECTED_RGBA_SHA256
    ):
        raise AssertionError("Materials image identity drift")
    if target.get("state") != "PASS_TARGET_HOST_IMPORTED_MATERIAL_BEARING_GLB":
        raise AssertionError("real Godot material carrier target state drift")
    mesh = target.get("mesh", {})
    if mesh.get("uv_count") != 4 or mesh.get("uvs") != EXPECTED_UVS:
        raise AssertionError("target-host UV0 identity drift")
    image = target.get("image", {})
    if (
        [image.get("width"), image.get("height")] != [512, 512]
        or image.get("rgba8_sha256") != EXPECTED_RGBA_SHA256
    ):
        raise AssertionError("target-host image identity drift")
    material = target.get("material", {})
    if material.get("has_albedo_texture") is not True:
        raise AssertionError("target-host albedo texture binding missing")
    if bridge.get("promotion", {}).get("environment_adoption") is not False:
        raise AssertionError("TA Environment adoption boundary inflated")
    return {
        "technical_art_head": EXPECTED_TA_HEAD,
        "hard_surface_head": EXPECTED_HARD_SURFACE_HEAD,
        "geometry_head": EXPECTED_GEOMETRY_HEAD,
        "materials_head": EXPECTED_MATERIALS_HEAD,
        "glb_sha256": EXPECTED_GLB_SHA256,
        "material_role": bridge.get("transport", {}).get("material_role"),
        "texture_slot": bridge.get("transport", {}).get("texture_slot"),
        "uvs": mesh.get("uvs"),
        "image_size_px": [image.get("width"), image.get("height")],
        "png_sha256": EXPECTED_PNG_SHA256,
        "rgba8_sha256": EXPECTED_RGBA_SHA256,
        "godot_target_state": target.get("state"),
        "environment_adoption": False,
    }


def verify_contract(contract: dict[str, Any]) -> None:
    if (
        contract.get("schema") != SCHEMA
        or contract.get("expected_result") != RESULT
        or contract.get("reusable_rule") != RULE
    ):
        raise AssertionError("Environment readiness contract identity drift")
    if contract.get("parent", {}).get("review_head") != EXPECTED_PARENT_REVIEW_HEAD:
        raise AssertionError("parent review head drift")
    if contract.get("parent", {}).get("render_head") != EXPECTED_RENDER_HEAD:
        raise AssertionError("parent render head drift")
    if contract.get("technical_art", {}).get("head") != EXPECTED_TA_HEAD:
        raise AssertionError("TA contract head drift")
    if contract.get("decision", {}).get("environment_adoption") is not False:
        raise AssertionError("automatic Environment adoption forbidden")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--world-root", required=True)
    parser.add_argument("--ta-root", required=True)
    parser.add_argument("--header-script", required=True)
    parser.add_argument("--clearance-script", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--force-claimed-binding",
        action="store_true",
        help="negative control: pretend Environment already has exact UV/image binding",
    )
    args = parser.parse_args()

    contract = load(Path(args.contract))
    verify_contract(contract)
    world = verify_world(Path(args.world_root))
    receiver = verify_receiver_source(Path(args.header_script), Path(args.clearance_script))
    ta = verify_ta(Path(args.ta_root))
    if args.force_claimed_binding:
        raise AssertionError(
            "Environment cannot self-declare an exact UV0/image binding absent from both the current receiver builder and retained runtime receipt"
        )
    if ta["material_role"] != "utility_panel_ochre":
        raise AssertionError("TA material role drift")

    report = {
        "schema": SCHEMA,
        "state": RESULT,
        "reusable_rule": RULE,
        "parent": contract["parent"],
        "world": world,
        "current_receiver_implementation": receiver,
        "technical_art_carrier": ta,
        "gap": {
            "material_role_matches_current_world": "utility_panel_ochre"
            in world["current_material_roles"],
            "exact_owner_uv0_available_upstream": True,
            "exact_owner_image_available_upstream": True,
            "current_receiver_uv0_binding_proven": False,
            "current_receiver_image_binding_proven": False,
            "current_receiver_material_role_alone_sufficient": False,
            "missing_handoff": "TECHNICAL_ART_OR_GEOMETRY_OWNED_EXACT_UV0_IMAGE_BINDING_FOR_CURRENT_184V_HEADER_SEGMENTED_23_UTILITY_PANEL_SURFACE",
        },
        "decision": {
            "environment_adoption": False,
            "scene_mutated": False,
            "building_geometry_changed": False,
            "building_panel_clearance_changed": False,
            "object_changed": False,
            "nature_changed": False,
            "weather_changed": False,
            "camera_or_light_changed": False,
            "requested_handoff": "Expose an exact current-receiver UV0 + image binding for the two utility-panel surface instances, preserving current 184v/276t/5-surface identity and the corrected panel placement; then Environment can run a real-world A/B without inventing planar UVs.",
        },
        "truth_boundary": (
            "HOLD proves a precise receiving gap, not a visual defect: the exact TA material carrier reaches real Godot with four UVs, TEXCOORD_0/base-color image identity and owner provenance, while the exact current Environment 184v/276t/5-surface Building receiver is constructed from positions + generated normals + scalar material binding and its retained real-world receipt exposes no UV/image transport identity. Environment therefore does not guess planar UVs, transplant the proof-carrier mesh, or relabel matching material-role text as adoption. Art/QA, Runtime/device, Building owners, Technical Art, CANON and production remain separate gates."
        ),
        "four_roots": {
            "truth": "Upstream transport PASS and current-world receiver limitation are both pinned; role-name equality is not treated as UV/image evidence.",
            "agency_non_domination": "Environment does not author Geometry/Materials/Technical-Art UV policy or auto-adopt their carrier.",
            "continuity": "PR49 and its reviewed +20 mm dressing remain unchanged; the current Building clearance receiver and exact TA artifact remain separately addressable.",
            "wisdom_before_speed": "Stop at the missing exact receiver boundary instead of inventing a fast planar mapping that could look plausible but break source authority.",
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(RESULT)
    print(
        json.dumps(
            {
                "runtime_receipts": world["runtime_receipt_count"],
                "world_state_observations": world["world_state_observations"],
                "weather_width_measurements": world["weather_width_measurements"],
                "ta_glb": ta["glb_sha256"],
                "current_receiver_uv0_binding_proven": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
