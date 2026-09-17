extends "res://atmosphere_current_world_nature_leaf_flutter_wall_clock_observe.gd"

const RECON_RECEIPT_PATH := "res://vfx-nature-leaf-flutter-timing-reconstruction-static-runtime.json"
const RECON_SCHEMA := "axm.vfx-current-world-nature-leaf-flutter-timing-reconstruction-static-observation/v0.1"
const RECON_MODE := "STATIC_DIRECT_SOURCE_PHASE_IMAGE_BANK_FIXED_WEATHER_NOT_TIMING_MEASUREMENT"

func write_receipt()->void:
    var file := FileAccess.open(RECON_RECEIPT_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(receipt, "  ") + "\n")
        file.close()

func _capture_state(viewport:SubViewport, context:String, phase_index:int)->Dictionary:
    var image := viewport.get_texture().get_image()
    if image == null or image.is_empty():
        return {"state":"FAIL_CAPTURE"}
    var path := "res://timing-reconstruction-fixed-weather-%s-%02d.png" % [context, phase_index]
    if image.save_png(path) != OK:
        return {"state":"FAIL_CAPTURE"}
    return {
        "state":"PASS",
        "path":path,
        "width":image.get_width(),
        "height":image.get_height(),
        "bytes":FileAccess.get_file_as_bytes(path).size()
    }

func _initialize()->void:
    receipt = {
        "schema": RECON_SCHEMA,
        "state": "NOT_RUN",
        "promotion_effect": "NONE",
        "proof_runtime": "Godot 4.7.2 GL Compatibility",
        "environment_parent_head": EXACT_ENVIRONMENT_PARENT_HEAD,
        "vfx_effect_head": EXACT_VFX_EFFECT_HEAD,
        "observation_mode": RECON_MODE,
        "weather_policy": WEATHER_POLICY,
        "source_unique_phase_count": UNIQUE_PHASE_COUNT,
        "source_endpoint_witness_phase": ENDPOINT_WITNESS_PHASE,
        "source_phase_step_s": PHASE_STEP_S,
        "source_cycle_duration_s": CYCLE_DURATION_S,
        "truth_boundary": "Static real-Godot source-state image bank for offline reconstruction of the separately measured clean wall-clock presentation stream. Weather is held at exact source phase 00 while each exact Nature sapling source phase is rendered independently in the two accepted current-world cameras. Framebuffer readback and PNG encoding occur only in this untimed static observer and therefore make no cadence/performance claim. This does not directly capture the clean timed run, prove display scanout, perceptual naturalness, physical wind, gameplay, target-device performance, final Art/QA acceptance, CANON or production readiness."
    }

    var payload := load_payload()
    if payload.is_empty():
        fail("missing exact current-world Nature leaf-flutter payload")
        return
    if String(payload.get("environment_head", "")) != EXACT_ENVIRONMENT_PARENT_HEAD:
        fail("accepted Environment receiver identity drifted")
        return
    if String(payload.get("nature_leaf_flutter_vfx_head", "")) != EXACT_VFX_EFFECT_HEAD:
        fail("Nature leaf-flutter effect identity drifted")
        return
    if String(payload.get("nature_leaf_flutter_structure_result", "")) != "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_STRUCTURE":
        fail("current-world leaf-flutter structure is not green")
        return

    var states := payload.get("states", []) as Array
    if states.size() != 17:
        fail("timing reconstruction image bank requires exact 17-state source sequence")
        return
    if absf(float((states[1] as Dictionary).get("time_s", -1.0)) - PHASE_STEP_S) > 1e-12:
        fail("leaf-flutter source phase spacing drifted")
        return
    if absf(float((states[ENDPOINT_WITNESS_PHASE] as Dictionary).get("time_s", -1.0)) - CYCLE_DURATION_S) > 1e-12:
        fail("leaf-flutter endpoint time drifted")
        return
    if String((states[0] as Dictionary).get("sapling_mesh_digest", "")) != String((states[ENDPOINT_WITNESS_PHASE] as Dictionary).get("sapling_mesh_digest", "")):
        fail("neutral endpoint sapling identity drifted")
        return

    var first := states[0] as Dictionary
    var data := first["scene"] as Dictionary
    var viewport := SubViewport.new()
    viewport.size = Vector2i(1100, 720)
    viewport.own_world_3d = true
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
    get_root().add_child(viewport)

    var root3d := Node3D.new()
    viewport.add_child(root3d)
    add_environment(root3d)
    for item in data["items"] as Array:
        add_proxy(root3d, item as Dictionary)
    add_path(root3d, data)
    var culling_review := data.get("environment_rear_tree_culling_review", {}) as Dictionary
    var cull_target_asset_id := String(culling_review.get("target_asset_id", ""))
    if cull_target_asset_id != VARIANT_TARGET_REAR_ASSET_ID:
        fail("current-world rear-tree culling target drift")
        return
    var static_source_stats := add_static_sources(root3d, data, cull_target_asset_id)

    make_weather()
    weather_material.cull_mode = BaseMaterial3D.CULL_DISABLED
    root3d.add_child(weather_node)
    make_sapling()
    root3d.add_child(sapling_node)

    var camera := Camera3D.new()
    camera.near = 0.05
    camera.far = 120.0
    root3d.add_child(camera)
    camera.make_current()

    var contexts := {}
    for context_value in PLAYBACK_CONTEXTS:
        var context := String(context_value)
        configure_camera(camera, data, context)
        await settle(4)

        var fixed_weather := fill_weather_width_ribbons(data["weather_lines"] as Array, camera)
        if fixed_weather.get("state") != "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            fail("fixed source-width Weather setup failed in %s: %s" % [context, fixed_weather])
            return
        if float(fixed_weather.get("maximum_projected_width_residual_px", 999.0)) > WIDTH_RESIDUAL_TOL_PX:
            fail("fixed source-width Weather residual exceeded tolerance in %s" % context)
            return
        await settle(2)

        var captures:Array=[]
        for phase_index in range(states.size()):
            var row := states[phase_index] as Dictionary
            var scene := row["scene"] as Dictionary
            var sapling_update := fill_sapling(scene["sapling"] as Dictionary)
            if sapling_update.is_empty():
                fail("sapling static phase update failed at phase %d / %s" % [phase_index, context])
                return
            await settle(2)
            var capture := _capture_state(viewport, context, phase_index)
            if capture.get("state") != "PASS":
                fail("static phase capture failed at phase %d / %s" % [phase_index, context])
                return
            captures.append({
                "phase_index": phase_index,
                "source_time_s": float(row.get("time_s", -1.0)),
                "sapling_mesh_digest": String(row.get("sapling_mesh_digest", "")),
                "sapling_update": sapling_update,
                "capture": capture
            })

        contexts[context] = {
            "fixed_weather_update": fixed_weather,
            "captures": captures,
            "runtime_stats_after_static_bank": runtime_stats()
        }

    receipt["state"] = "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_FIXED_WEATHER_STATIC_PHASE_IMAGE_BANK"
    receipt["receiving_head"] = payload.get("receiving_head", "")
    receipt["environment_head"] = payload.get("environment_head", "")
    receipt["nature_leaf_flutter_vfx_head"] = payload.get("nature_leaf_flutter_vfx_head", "")
    receipt["nature_leaf_flutter_geometry_context_head"] = payload.get("nature_leaf_flutter_geometry_context_head", "")
    receipt["static_source_meshes"] = static_source_stats
    receipt["contexts"] = contexts
    receipt["godot_version"] = Engine.get_version_info()
    receipt["truth_flags"] = {
        "real_godot_static_source_states_rendered": true,
        "weather_held_fixed_at_source_phase_00": true,
        "direct_source_states_only": true,
        "interpolation_added": false,
        "source_retimed": false,
        "timed_capture_performed": false,
        "framebuffer_readback_used_only_for_static_bank": true,
        "clean_wall_clock_timing_measured_here": false,
        "clean_timed_run_directly_captured_here": false,
        "display_scanout_timing_proven": false,
        "perceptual_naturalness_or_final_art_acceptance": false,
        "physical_wind_or_biomechanics": false,
        "gameplay_or_collision": false,
        "target_device_performance": false
    }
    write_receipt()
    quit(0)
