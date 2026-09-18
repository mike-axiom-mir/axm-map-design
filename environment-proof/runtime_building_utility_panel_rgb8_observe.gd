extends "res://atmosphere_current_world_building_utility_panel_material_bound_observe.gd"

const RUNTIME_RGB8_STATE := "PASS_BUILDING_UTILITY_PANEL_OPAQUE_ALPHA_ELISION_RGB8__HOLD_ART_QA_TARGET_DEVICE_GENERIC_POLICY"
const RUNTIME_RGB8_RULE := "ELIDE_TEXTURE_ALPHA_ONLY_AFTER_EXACT_OWNER_BYTES_PROVE_ALPHA_IS_UNIFORMLY_OPAQUE_AND_RETAIN_REAL_WORLD_RASTER_EQUIVALENCE"
const EXPECTED_ENVIRONMENT_PARENT_HEAD := "595df99daf866b5e3dcaa4be87eeb650af637919"
const EXPECTED_RGB8_SHA := "f515fe2a52a5356e1e8e1dfe560e20b53c3dff184047a05059d189ae6cd60192"
const EXPECTED_RGBA8_BASE_BYTES := 1048576
const EXPECTED_RGB8_BASE_BYTES := 786432
const EXPECTED_RGBA8_MIP_BYTES := 1398100
const EXPECTED_RGB8_MIP_BYTES := 1048575

var runtime_rgb8_texture_receipt:Dictionary = {}

func _material_texture()->ImageTexture:
    var png_bytes:=FileAccess.get_file_as_bytes(MATERIAL_IMAGE_PATH)
    if _material_sha256(png_bytes)!=EXPECTED_PNG_SHA:
        fail("Runtime Building RGB8 serialized PNG identity drift")
        return null
    var image:=Image.new()
    if image.load(MATERIAL_IMAGE_PATH)!=OK or image.is_empty():
        fail("Runtime Building RGB8 material image load failed")
        return null
    image.convert(Image.FORMAT_RGBA8)
    var rgba:=image.get_data()
    if image.get_width()!=512 or image.get_height()!=512 or rgba.size()!=EXPECTED_RGBA8_BASE_BYTES or _material_sha256(rgba)!=EXPECTED_RGBA_SHA:
        fail("Runtime Building RGB8 decoded RGBA8 identity drift")
        return null
    var opaque_samples:=0
    for offset in range(3,rgba.size(),4):
        if int(rgba[offset])!=255:
            fail("Runtime Building RGB8 alpha-elision precondition failed: non-opaque alpha sample")
            return null
        opaque_samples+=1
    if opaque_samples!=512*512:
        fail("Runtime Building RGB8 alpha sample count drift")
        return null

    image.convert(Image.FORMAT_RGB8)
    var rgb:=image.get_data()
    if rgb.size()!=EXPECTED_RGB8_BASE_BYTES or _material_sha256(rgb)!=EXPECTED_RGB8_SHA:
        fail("Runtime Building RGB8 exact RGB payload drift")
        return null
    image.generate_mipmaps()
    var mip_bytes:=image.get_data().size()
    if mip_bytes!=EXPECTED_RGB8_MIP_BYTES:
        fail("Runtime Building RGB8 mip-chain byte count drift")
        return null

    runtime_rgb8_texture_receipt={
        "schema":"axm.runtime-building-utility-panel-rgb8-texture-observation/v0.1",
        "state":RUNTIME_RGB8_STATE,
        "rule":RUNTIME_RGB8_RULE,
        "environment_parent_head":EXPECTED_ENVIRONMENT_PARENT_HEAD,
        "serialized_png_sha256":EXPECTED_PNG_SHA,
        "decoded_rgba8_sha256":EXPECTED_RGBA_SHA,
        "decoded_rgb8_sha256":EXPECTED_RGB8_SHA,
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
        "environment_adoption":false,
        "materials_adoption":false,
        "technical_art_adoption":false,
        "target_device_acceptance":false,
        "art_qa_acceptance":false,
        "generic_rgb8_policy":false,
        "canon":false
    }
    return ImageTexture.create_from_image(image)

func write_receipt()->void:
    receipt["runtime_building_utility_panel_rgb8_state"]=RUNTIME_RGB8_STATE
    receipt["runtime_building_utility_panel_rgb8_rule"]=RUNTIME_RGB8_RULE
    receipt["runtime_building_utility_panel_rgb8_environment_parent_head"]=EXPECTED_ENVIRONMENT_PARENT_HEAD
    receipt["runtime_building_utility_panel_rgb8_texture_receipt"]=runtime_rgb8_texture_receipt
    receipt["runtime_building_utility_panel_rgb8_target_device_acceptance"]=false
    receipt["runtime_building_utility_panel_rgb8_art_qa_acceptance"]=false
    receipt["runtime_building_utility_panel_rgb8_generic_policy"]=false
    receipt["runtime_building_utility_panel_rgb8_truth_boundary"]="Exact current-world Building utility-panel material receiver only. Runtime drops an alpha channel only after the exact owner RGBA8 payload proves every alpha sample is 255, preserves RGB bytes exactly, retains the full mip chain, and measures real Godot raster/runtime deltas against the exact Environment parent candidate. This does not authorize alpha elision for arbitrary textures or establish target-device performance, Art/QA acceptance, CANON or production readiness."
    super.write_receipt()
