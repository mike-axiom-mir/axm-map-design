extends "res://materials_current_world_building_utility_panel_production_surface_observe.gd"

const RUNTIME_PRODUCTION_RGB8_STATE := "PASS_BUILDING_UTILITY_PANEL_PRODUCTION_SURFACE_OPAQUE_ALPHA_ELISION_RGB8__HOLD_ART_QA_TARGET_DEVICE_GENERIC_POLICY"
const RUNTIME_PRODUCTION_RGB8_RULE := "REBIND_OPAQUE_ALPHA_ELISION_ONLY_TO_EXACT_MATERIALS_PRODUCTION_SURFACE_AFTER_OWNER_BYTES_PROVE_ALPHA_IS_UNIFORMLY_255_AND_FRESH_CURRENT_WORLD_RASTER_EQUIVALENCE_IS_REMEASURED"
const EXPECTED_RUNTIME_PARENT_HEAD := "1afa51cb89b536db0d2434328722a1521febe0ad"
const EXPECTED_MATERIALS_OWNER_HEAD := "75bf511be8a89778ab40868707a68e80a210608a"
const PRODUCTION_IMAGE_PATH := "res://generated/utility-panel-production-surface-001.png"
const EXPECTED_PRODUCTION_PNG_SHA := "fdf56d0c0b2e65a181a23cb5db4067555f188cce28ef2479fd5a71c8e11d220c"
const EXPECTED_PRODUCTION_RGBA8_SHA := "408a6eaecf99fa328487785f85d089c93da2b84c3ae9ead0bf6e1f8d2a0bdcad"
const EXPECTED_PRODUCTION_RGB8_SHA := "222f72229db1f79e8222f536d4124655c14f9fe96fc316cddfe13c8decc294ae"
const EXPECTED_RGBA8_BASE_BYTES := 1048576
const EXPECTED_RGB8_BASE_BYTES := 786432
const EXPECTED_RGBA8_MIP_BYTES := 1398100
const EXPECTED_RGB8_MIP_BYTES := 1048575

var runtime_production_rgb8_texture_receipt:Dictionary = {}

func _material_texture()->ImageTexture:
    var png_bytes:=FileAccess.get_file_as_bytes(PRODUCTION_IMAGE_PATH)
    if _material_sha256(png_bytes)!=EXPECTED_PRODUCTION_PNG_SHA:
        fail("Runtime Building production-surface RGB8 serialized PNG identity drift")
        return null
    var image:=Image.new()
    if image.load(PRODUCTION_IMAGE_PATH)!=OK or image.is_empty():
        fail("Runtime Building production-surface RGB8 material image load failed")
        return null
    image.convert(Image.FORMAT_RGBA8)
    var rgba:=image.get_data()
    if image.get_width()!=512 or image.get_height()!=512 or rgba.size()!=EXPECTED_RGBA8_BASE_BYTES or _material_sha256(rgba)!=EXPECTED_PRODUCTION_RGBA8_SHA:
        fail("Runtime Building production-surface RGB8 decoded RGBA8 identity drift")
        return null
    var opaque_samples:=0
    for offset in range(3,rgba.size(),4):
        if int(rgba[offset])!=255:
            fail("Runtime Building production-surface RGB8 alpha-elision precondition failed: non-opaque alpha sample")
            return null
        opaque_samples+=1
    if opaque_samples!=512*512:
        fail("Runtime Building production-surface RGB8 alpha sample count drift")
        return null

    image.convert(Image.FORMAT_RGB8)
    var rgb:=image.get_data()
    if rgb.size()!=EXPECTED_RGB8_BASE_BYTES or _material_sha256(rgb)!=EXPECTED_PRODUCTION_RGB8_SHA:
        fail("Runtime Building production-surface RGB8 exact RGB payload drift")
        return null
    image.generate_mipmaps()
    var mip_bytes:=image.get_data().size()
    if mip_bytes!=EXPECTED_RGB8_MIP_BYTES:
        fail("Runtime Building production-surface RGB8 mip-chain byte count drift")
        return null

    runtime_production_rgb8_texture_receipt={
        "schema":"axm.runtime-building-utility-panel-production-surface-rgb8-texture-observation/v0.1",
        "state":RUNTIME_PRODUCTION_RGB8_STATE,
        "rule":RUNTIME_PRODUCTION_RGB8_RULE,
        "runtime_parent_head":EXPECTED_RUNTIME_PARENT_HEAD,
        "materials_owner_head":EXPECTED_MATERIALS_OWNER_HEAD,
        "serialized_png_sha256":EXPECTED_PRODUCTION_PNG_SHA,
        "decoded_rgba8_sha256":EXPECTED_PRODUCTION_RGBA8_SHA,
        "decoded_rgb8_sha256":EXPECTED_PRODUCTION_RGB8_SHA,
        "alpha_sample_count":opaque_samples,
        "alpha_min":255,
        "alpha_max":255,
        "rgba8_base_level_bytes":EXPECTED_RGBA8_BASE_BYTES,
        "rgb8_base_level_bytes":EXPECTED_RGB8_BASE_BYTES,
        "rgba8_full_mip_chain_bytes":EXPECTED_RGBA8_MIP_BYTES,
        "rgb8_full_mip_chain_bytes":mip_bytes,
        "theoretical_payload_bytes_saved":EXPECTED_RGBA8_MIP_BYTES-mip_bytes,
        "source_image_reauthored":false,
        "uv_changed":false,
        "material_scalars_changed":false,
        "surface_recipe_changed":false,
        "environment_adoption":false,
        "materials_adoption":false,
        "technical_art_adoption":false,
        "target_device_acceptance":false,
        "art_qa_acceptance":false,
        "generic_rgb8_policy":false,
        "fleet_import_rule":false,
        "canon":false
    }
    return ImageTexture.create_from_image(image)

func write_receipt()->void:
    receipt["runtime_building_utility_panel_production_surface_rgb8_state"]=RUNTIME_PRODUCTION_RGB8_STATE
    receipt["runtime_building_utility_panel_production_surface_rgb8_rule"]=RUNTIME_PRODUCTION_RGB8_RULE
    receipt["runtime_building_utility_panel_production_surface_rgb8_runtime_parent_head"]=EXPECTED_RUNTIME_PARENT_HEAD
    receipt["runtime_building_utility_panel_production_surface_rgb8_materials_owner_head"]=EXPECTED_MATERIALS_OWNER_HEAD
    receipt["runtime_building_utility_panel_production_surface_rgb8_texture_receipt"]=runtime_production_rgb8_texture_receipt
    receipt["runtime_building_utility_panel_production_surface_rgb8_target_device_acceptance"]=false
    receipt["runtime_building_utility_panel_production_surface_rgb8_art_qa_acceptance"]=false
    receipt["runtime_building_utility_panel_production_surface_rgb8_generic_policy"]=false
    receipt["runtime_building_utility_panel_production_surface_rgb8_truth_boundary"]="Exact Materials production-surface successor 001 on the existing current-world Building receiver only. Runtime removes only the unused alpha channel after proving the exact owner PNG/RGBA/RGB identities and every alpha sample equals 255, while preserving the same UV transport, material scalars, world state and full mip chain. This is a fresh receiver rebind of the prior checker optimization, not permission to generalize RGB8 conversion across arbitrary textures or assets. Target-device, Art/QA, Environment adoption, CANON and production readiness remain held."
    super.write_receipt()
