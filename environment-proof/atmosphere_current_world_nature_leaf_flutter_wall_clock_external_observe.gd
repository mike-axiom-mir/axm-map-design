extends "res://atmosphere_current_world_nature_leaf_flutter_wall_clock_observe.gd"

const EXTERNAL_RECEIPT_PATH := "res://vfx-nature-leaf-flutter-wall-clock-external-runtime.json"
const EXTERNAL_SCHEMA := "axm.vfx-current-world-nature-leaf-flutter-external-capture/v0.1"
const EXTERNAL_CAPTURE_MODE := "EXTERNAL_X11GRAB_FFV1_NO_IN_PROCESS_VIEWPORT_READBACK"
const DISPLAY_W := 1120
const DISPLAY_H := 720
const SCENE_W := 1100
const SCENE_H := 720
const MARKER_W := 20
const MARKER_CELL_H := 24
const CLEAN_REFERENCE_HEAD := "795d9e8862e895e506c756b9ea01cd6228fa7ab7"
const CLEAN_REFERENCE_WORKFLOW := 35179504496
const CLEAN_REFERENCE_PRESENTED_TOTAL := 92
const CLEAN_REFERENCE_PATH_MEAN_MS := 32.0634565
const CLEAN_REFERENCE_ELEVATED_MEAN_MS := 33.7925909
const LOW_INTRUSION_MIN_PRESENTED_TOTAL := 90
const LOW_INTRUSION_MAX_CADENCE_RATIO := 1.10

var marker_cells:Array = []

func write_receipt()->void:
    var file := FileAccess.open(EXTERNAL_RECEIPT_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(receipt, "  ") + "\n")
        file.close()

func _setup_marker(display_root:Control)->void:
    var panel := ColorRect.new()
    panel.position = Vector2(SCENE_W, 0)
    panel.size = Vector2(MARKER_W, DISPLAY_H)
    panel.color = Color(0.0, 0.0, 0.0, 1.0)
    panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
    display_root.add_child(panel)
    marker_cells.clear()
    for index in range(12):
        var cell := ColorRect.new()
        cell.position = Vector2(0, index * MARKER_CELL_H)
        cell.size = Vector2(MARKER_W, MARKER_CELL_H)
        cell.color = Color(0.0, 0.0, 0.0, 1.0)
        cell.mouse_filter = Control.MOUSE_FILTER_IGNORE
        panel.add_child(cell)
        marker_cells.append(cell)
    _set_marker("path_eye", -1, false)

func _set_marker(context:String, absolute_slot:int, valid:bool)->void:
    if marker_cells.size() != 12:
        return
    var slot := maxi(absolute_slot, 0)
    var bits := [1, 0, 1, 1, 1 if valid else 0, 1 if context == "elevated_oblique" else 0]
    for bit_index in range(6):
        bits.append((slot >> bit_index) & 1)
    for index in range(12):
        var value := int(bits[index])
        var level := 1.0 if value == 1 else 0.0
        var cell := marker_cells[index] as ColorRect
        cell.color = Color(level, level, level, 1.0)

func _run_external_context(states:Array, camera:Camera3D, context:String)->Dictionary:
    var first_row := states[0] as Dictionary
    var first_scene := first_row["scene"] as Dictionary
    configure_camera(camera, first_scene, context)
    _set_marker(context, -1, false)
    await settle(4)

    var fixed_weather := fill_weather_width_ribbons(first_scene["weather_lines"] as Array, camera)
    if fixed_weather.get("state") != "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
        fail("fixed source-width Weather setup failed in %s: %s" % [context, fixed_weather])
        return {}
    if float(fixed_weather.get("maximum_projected_width_residual_px", 999.0)) > WIDTH_RESIDUAL_TOL_PX:
        fail("fixed source-width Weather residual exceeded tolerance in %s" % context)
        return {}

    var initial_sapling := fill_sapling(first_scene["sapling"] as Dictionary)
    if initial_sapling.is_empty():
        fail("initial sapling setup failed in %s" % context)
        return {}
    if int(initial_sapling.get("leaf_flutter_phase_index", -1)) != 0:
        fail("initial sapling source phase identity drifted in %s" % context)
        return {}
    await settle(4)

    var records:Array = []
    var frame_intervals_ms:Array = []
    var selection_lateness_ms:Array = []
    var submit_lateness_ms:Array = []
    var post_draw_lateness_ms:Array = []
    var apply_duration_ms:Array = []
    var last_post_draw_us := -1
    var last_observed_slot := -1
    var start_us := Time.get_ticks_usec()
    var stop_us := start_us + EXPECTED_SLOTS_PER_CONTEXT * PHASE_STEP_US

    while Time.get_ticks_usec() < stop_us:
        var observed_us := Time.get_ticks_usec()
        var elapsed_us := observed_us - start_us
        var due_slot := mini(int(elapsed_us / PHASE_STEP_US), EXPECTED_SLOTS_PER_CONTEXT - 1)
        if due_slot != last_observed_slot:
            var source_phase := due_slot % UNIQUE_PHASE_COUNT
            var source_cycle := int(due_slot / UNIQUE_PHASE_COUNT)
            var row := states[source_phase] as Dictionary
            var scene := row["scene"] as Dictionary
            var ideal_due_us := start_us + due_slot * PHASE_STEP_US
            var selection_late := float(observed_us - ideal_due_us) / 1000.0

            # The marker and source state change in the same main-loop turn,
            # before one shared frame_post_draw. The external recorder never invokes
            # an in-process viewport image-readback API or PNG encoding path.
            _set_marker(context, due_slot, true)
            var apply_begin_us := Time.get_ticks_usec()
            var sapling_update := fill_sapling(scene["sapling"] as Dictionary)
            if sapling_update.is_empty():
                fail("sapling update failed at external-capture slot %d / %s" % [due_slot, context])
                return {}
            if int(sapling_update.get("leaf_flutter_phase_index", -1)) != source_phase:
                fail("sapling source phase identity mismatch at slot %d / %s" % [due_slot, context])
                return {}
            var submit_us := Time.get_ticks_usec()
            await RenderingServer.frame_post_draw
            var post_draw_us := Time.get_ticks_usec()

            var apply_ms := float(submit_us - apply_begin_us) / 1000.0
            var submit_late := float(submit_us - ideal_due_us) / 1000.0
            var draw_late := float(post_draw_us - ideal_due_us) / 1000.0
            if last_post_draw_us >= 0:
                frame_intervals_ms.append(float(post_draw_us - last_post_draw_us) / 1000.0)
            last_post_draw_us = post_draw_us
            selection_lateness_ms.append(selection_late)
            submit_lateness_ms.append(submit_late)
            post_draw_lateness_ms.append(draw_late)
            apply_duration_ms.append(apply_ms)

            records.append({
                "absolute_slot": due_slot,
                "cycle_index": source_cycle,
                "source_phase_index": source_phase,
                "source_time_s": float(row.get("time_s", -1.0)),
                "sapling_mesh_digest": String(row.get("sapling_mesh_digest", "")),
                "ideal_due_offset_ms": float(due_slot * PHASE_STEP_US) / 1000.0,
                "selection_offset_ms": float(observed_us - start_us) / 1000.0,
                "submit_offset_ms": float(submit_us - start_us) / 1000.0,
                "post_draw_offset_ms": float(post_draw_us - start_us) / 1000.0,
                "selection_lateness_ms": selection_late,
                "submit_lateness_ms": submit_late,
                "post_draw_lateness_ms": draw_late,
                "apply_duration_ms": apply_ms,
                "sapling_update": sapling_update,
                "external_marker_slot": due_slot,
                "external_marker_context_bit": 1 if context == "elevated_oblique" else 0
            })
            last_observed_slot = due_slot
        else:
            await process_frame

    _set_marker(context, -1, false)
    await RenderingServer.frame_post_draw

    var endpoint_row := states[ENDPOINT_WITNESS_PHASE] as Dictionary
    var endpoint_scene := endpoint_row["scene"] as Dictionary
    var endpoint_update := fill_sapling(endpoint_scene["sapling"] as Dictionary)
    if endpoint_update.is_empty():
        fail("endpoint witness update failed in %s" % context)
        return {}
    if int(endpoint_update.get("leaf_flutter_phase_index", -1)) != ENDPOINT_WITNESS_PHASE:
        fail("endpoint phase identity drifted in %s" % context)
        return {}
    await RenderingServer.frame_post_draw
    var endpoint_post_draw_us := Time.get_ticks_usec()

    var missing_slots := _slots_missing(records)
    var state := "PASS_EXTERNAL_CAPTURE_WALL_CLOCK_CHARACTERIZATION_FULL_SOURCE_COVERAGE"
    if not missing_slots.is_empty():
        state = "PASS_EXTERNAL_CAPTURE_WALL_CLOCK_CHARACTERIZATION_SOURCE_DROPS_OBSERVED"

    return {
        "state": state,
        "context": context,
        "presentation_mode": PRESENTATION_MODE,
        "weather_policy": WEATHER_POLICY,
        "external_capture_mode": EXTERNAL_CAPTURE_MODE,
        "external_marker_schema": "sync=1011;valid;context;slot_lsb0..5",
        "fixed_weather_update": fixed_weather,
        "scheduled_slot_count": EXPECTED_SLOTS_PER_CONTEXT,
        "presented_slot_count": records.size(),
        "skipped_slot_count": missing_slots.size(),
        "skipped_slots": missing_slots,
        "phase_coverage": _phase_coverage(records),
        "records": records,
        "selection_lateness_ms": {
            "mean": _mean(selection_lateness_ms),
            "p50": _percentile(selection_lateness_ms, 0.50),
            "p95": _percentile(selection_lateness_ms, 0.95),
            "max": selection_lateness_ms.max() if not selection_lateness_ms.is_empty() else 0.0
        },
        "submit_lateness_ms": {
            "mean": _mean(submit_lateness_ms),
            "p50": _percentile(submit_lateness_ms, 0.50),
            "p95": _percentile(submit_lateness_ms, 0.95),
            "max": submit_lateness_ms.max() if not submit_lateness_ms.is_empty() else 0.0
        },
        "post_draw_lateness_ms": {
            "mean": _mean(post_draw_lateness_ms),
            "p50": _percentile(post_draw_lateness_ms, 0.50),
            "p95": _percentile(post_draw_lateness_ms, 0.95),
            "max": post_draw_lateness_ms.max() if not post_draw_lateness_ms.is_empty() else 0.0
        },
        "apply_duration_ms": {
            "mean": _mean(apply_duration_ms),
            "p50": _percentile(apply_duration_ms, 0.50),
            "p95": _percentile(apply_duration_ms, 0.95),
            "max": apply_duration_ms.max() if not apply_duration_ms.is_empty() else 0.0
        },
        "post_draw_interval_ms": {
            "mean": _mean(frame_intervals_ms),
            "p50": _percentile(frame_intervals_ms, 0.50),
            "p95": _percentile(frame_intervals_ms, 0.95),
            "max": frame_intervals_ms.max() if not frame_intervals_ms.is_empty() else 0.0
        },
        "endpoint_witness_phase": ENDPOINT_WITNESS_PHASE,
        "endpoint_sapling_mesh_digest": String(endpoint_row.get("sapling_mesh_digest", "")),
        "endpoint_update": endpoint_update,
        "endpoint_post_draw_offset_ms": float(endpoint_post_draw_us - start_us) / 1000.0,
        "runtime_stats_after_endpoint": runtime_stats()
    }

func _initialize()->void:
    receipt = {
        "schema": EXTERNAL_SCHEMA,
        "state": "NOT_RUN",
        "promotion_effect": "NONE",
        "proof_runtime": "Godot 4.7.2 GL Compatibility / X11",
        "environment_parent_head": EXACT_ENVIRONMENT_PARENT_HEAD,
        "vfx_effect_head": EXACT_VFX_EFFECT_HEAD,
        "presentation_mode": PRESENTATION_MODE,
        "weather_policy": WEATHER_POLICY,
        "source_phase_step_s": PHASE_STEP_S,
        "source_unique_phase_count": UNIQUE_PHASE_COUNT,
        "source_endpoint_witness_phase": ENDPOINT_WITNESS_PHASE,
        "source_cycle_duration_s": CYCLE_DURATION_S,
        "test_cycles_per_context": TEST_CYCLES,
        "external_capture_mode": EXTERNAL_CAPTURE_MODE,
        "external_display_size": [DISPLAY_W, DISPLAY_H],
        "embedded_scene_size": [SCENE_W, SCENE_H],
        "marker_width_px": MARKER_W,
        "clean_reference": {
            "head": CLEAN_REFERENCE_HEAD,
            "workflow": CLEAN_REFERENCE_WORKFLOW,
            "presented_total": CLEAN_REFERENCE_PRESENTED_TOTAL,
            "path_eye_mean_post_draw_ms": CLEAN_REFERENCE_PATH_MEAN_MS,
            "elevated_oblique_mean_post_draw_ms": CLEAN_REFERENCE_ELEVATED_MEAN_MS
        },
        "low_intrusion_comparability_gate": {
            "minimum_presented_total": LOW_INTRUSION_MIN_PRESENTED_TOTAL,
            "maximum_mean_cadence_ratio_per_context": LOW_INTRUSION_MAX_CADENCE_RATIO
        },
        "truth_boundary": "External X11 capture characterization only. The exact accepted Nature source states, phase-locked latest-due no-retime scheduler, current-world receiver and fixed Weather phase remain unchanged. The in-process proof performs no viewport image readback or PNG encoding during the timed windows. A narrow telemetry strip outside the 1100x720 scene crop binds externally recorded frames to context/absolute source slot. Any extra display-composition or external-recording cost is measured by comparison with the exact clean no-capture reference, not hidden. This is not display-scanout proof, perceptual naturalness acceptance, physical wind, gameplay, target-device performance, CANON or production readiness."
    }

    var payload := load_payload()
    if payload.is_empty():
        fail("missing exact current-world Nature leaf-flutter payload")
        return
    if String(payload.get("nature_leaf_flutter_vfx_head", "")) != EXACT_VFX_EFFECT_HEAD:
        fail("Nature leaf-flutter effect identity drifted")
        return
    if String(payload.get("environment_head", "")) != EXACT_ENVIRONMENT_PARENT_HEAD:
        fail("current-world Environment parent identity drifted")
        return
    if String(payload.get("nature_leaf_flutter_structure_result", "")) != "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_STRUCTURE":
        fail("current-world leaf-flutter structure is not green")
        return
    var states := payload.get("states", []) as Array
    if states.size() != 17:
        fail("external capture requires exact 17-state source sequence")
        return
    if absf(float((states[1] as Dictionary).get("time_s", -1.0)) - PHASE_STEP_S) > 1e-12:
        fail("leaf-flutter source phase spacing drifted")
        return
    if absf(float((states[ENDPOINT_WITNESS_PHASE] as Dictionary).get("time_s", -1.0)) - CYCLE_DURATION_S) > 1e-12:
        fail("leaf-flutter endpoint time drifted")
        return

    var root_window := get_root()
    root_window.size = Vector2i(DISPLAY_W, DISPLAY_H)
    root_window.position = Vector2i(0, 0)

    var display_root := Control.new()
    display_root.position = Vector2.ZERO
    display_root.size = Vector2(DISPLAY_W, DISPLAY_H)
    display_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
    root_window.add_child(display_root)

    var container := SubViewportContainer.new()
    container.position = Vector2.ZERO
    container.size = Vector2(SCENE_W, SCENE_H)
    container.stretch = false
    container.mouse_filter = Control.MOUSE_FILTER_IGNORE
    display_root.add_child(container)

    var viewport := SubViewport.new()
    viewport.size = Vector2i(SCENE_W, SCENE_H)
    viewport.own_world_3d = true
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
    container.add_child(viewport)
    _setup_marker(display_root)

    var first := states[0] as Dictionary
    var data := first["scene"] as Dictionary
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

    await settle(8)
    var contexts := {}
    for context_value in PLAYBACK_CONTEXTS:
        var context := String(context_value)
        var result := await _run_external_context(states, camera, context)
        if result.is_empty():
            return
        contexts[context] = result
        _set_marker(context, -1, false)
        await settle(4)

    var total_presented := 0
    for context_value in PLAYBACK_CONTEXTS:
        total_presented += int((contexts[String(context_value)] as Dictionary).get("presented_slot_count", 0))
    var path_interval := (contexts["path_eye"] as Dictionary).get("post_draw_interval_ms", {}) as Dictionary
    var elevated_interval := (contexts["elevated_oblique"] as Dictionary).get("post_draw_interval_ms", {}) as Dictionary
    var path_mean := float(path_interval.get("mean", 999.0))
    var elevated_mean := float(elevated_interval.get("mean", 999.0))
    var path_ratio := path_mean / CLEAN_REFERENCE_PATH_MEAN_MS
    var elevated_ratio := elevated_mean / CLEAN_REFERENCE_ELEVATED_MEAN_MS
    var coverage_ok := total_presented >= LOW_INTRUSION_MIN_PRESENTED_TOTAL
    var cadence_ok := path_ratio <= LOW_INTRUSION_MAX_CADENCE_RATIO and elevated_ratio <= LOW_INTRUSION_MAX_CADENCE_RATIO

    receipt["receiving_head"] = payload.get("receiving_head", "")
    receipt["environment_head"] = payload.get("environment_head", "")
    receipt["nature_leaf_flutter_vfx_head"] = payload.get("nature_leaf_flutter_vfx_head", "")
    receipt["nature_leaf_flutter_geometry_context_head"] = payload.get("nature_leaf_flutter_geometry_context_head", "")
    receipt["static_source_meshes"] = static_source_stats
    receipt["contexts"] = contexts
    receipt["godot_version"] = Engine.get_version_info()
    receipt["comparison_to_clean_reference"] = {
        "presented_total": total_presented,
        "clean_presented_total": CLEAN_REFERENCE_PRESENTED_TOTAL,
        "presented_delta": total_presented - CLEAN_REFERENCE_PRESENTED_TOTAL,
        "path_eye_mean_post_draw_ms": path_mean,
        "path_eye_cadence_ratio_vs_clean": path_ratio,
        "elevated_oblique_mean_post_draw_ms": elevated_mean,
        "elevated_oblique_cadence_ratio_vs_clean": elevated_ratio,
        "coverage_gate_pass": coverage_ok,
        "cadence_gate_pass": cadence_ok
    }
    receipt["truth_flags"] = {
        "exact_art_preferred_spatial_response_preserved": true,
        "geometry_materials_environment_and_cameras_reauthored": false,
        "weather_semantics_reauthored": false,
        "weather_held_fixed_during_timing_run": true,
        "direct_source_states_only": true,
        "interpolation_used": false,
        "retiming_used": false,
        "in_process_viewport_readback_used": false,
        "in_process_png_encoding_used": false,
        "external_display_composition_added": true,
        "external_capture_perceptual_acceptance_proven": false,
        "physical_wind_proven": false,
        "gameplay_or_collision_proven": false,
        "target_device_performance_proven": false
    }
    if coverage_ok and cadence_ok:
        receipt["state"] = "PASS_EXTERNAL_X11_CAPTURE_LOW_INTRUSION_TIMING_COMPARABLE"
    else:
        receipt["state"] = "HOLD_EXTERNAL_X11_CAPTURE_PERTURBS_CLEAN_REFERENCE"
    write_receipt()
    print(receipt["state"])
    await settle(6)
    _set_marker("path_eye", -1, false)
    quit(0)
