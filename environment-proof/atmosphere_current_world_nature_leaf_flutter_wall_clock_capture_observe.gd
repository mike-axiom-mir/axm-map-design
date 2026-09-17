extends "res://atmosphere_current_world_nature_leaf_flutter_wall_clock_observe.gd"

const CAPTURE_RECEIPT_PATH := "res://vfx-nature-leaf-flutter-wall-clock-capture-runtime.json"
const CAPTURE_ROOT := "res://vfx-nature-leaf-flutter-wall-clock-capture"
const CAPTURE_SCHEMA := "axm.vfx-current-world-nature-leaf-flutter-direct-timed-capture/v0.1"
const CAPTURE_MODE := "DIRECT_POST_DRAW_VIEWPORT_READBACK__PNG_ENCODING_DEFERRED_UNTIL_TIMED_WINDOW_END"

func _capture_frame(camera:Camera3D, absolute_slot:int, cycle_index:int, source_phase:int)->Dictionary:
    var readback_begin_us := Time.get_ticks_usec()
    var image := camera.get_viewport().get_texture().get_image()
    var readback_end_us := Time.get_ticks_usec()
    if image == null or image.is_empty():
        fail("direct timed viewport capture failed at slot %d" % absolute_slot)
        return {}
    return {
        "absolute_slot": absolute_slot,
        "cycle_index": cycle_index,
        "source_phase_index": source_phase,
        "readback_duration_ms": float(readback_end_us - readback_begin_us) / 1000.0,
        "width": image.get_width(),
        "height": image.get_height(),
        "image": image
    }

func _save_deferred_captures(captures:Array, context:String)->Array:
    var context_res := "%s/%s" % [CAPTURE_ROOT, context]
    var context_abs := ProjectSettings.globalize_path(context_res)
    var mkdir_error := DirAccess.make_dir_recursive_absolute(context_abs)
    if mkdir_error != OK and mkdir_error != ERR_ALREADY_EXISTS:
        fail("could not create direct timed capture directory for %s: %s" % [context, mkdir_error])
        return []
    var manifest:Array=[]
    for capture_value in captures:
        var capture := capture_value as Dictionary
        var image := capture.get("image") as Image
        if image == null or image.is_empty():
            fail("deferred capture image missing for %s" % context)
            return []
        var absolute_slot := int(capture.get("absolute_slot", -1))
        var cycle_index := int(capture.get("cycle_index", -1))
        var source_phase := int(capture.get("source_phase_index", -1))
        var filename := "slot-%03d-cycle-%02d-phase-%02d.png" % [absolute_slot, cycle_index, source_phase]
        var relative_path := "%s/%s/%s" % [CAPTURE_ROOT.trim_prefix("res://"), context, filename]
        var save_error := image.save_png("%s/%s" % [context_res, filename])
        if save_error != OK:
            fail("could not save direct timed capture %s: %s" % [relative_path, save_error])
            return []
        manifest.append({
            "absolute_slot": absolute_slot,
            "cycle_index": cycle_index,
            "source_phase_index": source_phase,
            "readback_duration_ms": float(capture.get("readback_duration_ms", -1.0)),
            "width": int(capture.get("width", -1)),
            "height": int(capture.get("height", -1)),
            "png_path": relative_path
        })
    return manifest

func _save_endpoint_capture(image:Image, context:String)->String:
    if image == null or image.is_empty():
        fail("endpoint capture image missing for %s" % context)
        return ""
    var context_res := "%s/%s" % [CAPTURE_ROOT, context]
    var context_abs := ProjectSettings.globalize_path(context_res)
    var mkdir_error := DirAccess.make_dir_recursive_absolute(context_abs)
    if mkdir_error != OK and mkdir_error != ERR_ALREADY_EXISTS:
        fail("could not create endpoint capture directory for %s" % context)
        return ""
    var relative_path := "%s/%s/endpoint-phase-%02d.png" % [CAPTURE_ROOT.trim_prefix("res://"), context, ENDPOINT_WITNESS_PHASE]
    var save_error := image.save_png("%s/endpoint-phase-%02d.png" % [context_res, ENDPOINT_WITNESS_PHASE])
    if save_error != OK:
        fail("could not save endpoint capture %s: %s" % [relative_path, save_error])
        return ""
    return relative_path

func _run_context(states:Array, camera:Camera3D, context:String)->Dictionary:
    var first_row := states[0] as Dictionary
    var first_scene := first_row["scene"] as Dictionary
    configure_camera(camera, first_scene, context)
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
    await settle(4)

    var records:Array=[]
    var deferred_captures:Array=[]
    var frame_intervals_ms:Array=[]
    var selection_lateness_ms:Array=[]
    var submit_lateness_ms:Array=[]
    var post_draw_lateness_ms:Array=[]
    var apply_duration_ms:Array=[]
    var capture_readback_ms:Array=[]
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

            var apply_begin_us := Time.get_ticks_usec()
            var sapling_update := fill_sapling(scene["sapling"] as Dictionary)
            if sapling_update.is_empty():
                fail("sapling update failed at timed capture slot %d / %s" % [due_slot, context])
                return {}
            var submit_us := Time.get_ticks_usec()
            await RenderingServer.frame_post_draw
            var post_draw_us := Time.get_ticks_usec()

            # Capture exactly the post-draw viewport produced by this presented
            # direct source state. PNG encoding is deferred until after the timed
            # window; only viewport readback can perturb later scheduling, and its
            # duration is retained explicitly instead of hidden.
            var capture := _capture_frame(camera, due_slot, source_cycle, source_phase)
            if capture.is_empty():
                return {}
            deferred_captures.append(capture)
            capture_readback_ms.append(float(capture.get("readback_duration_ms", 0.0)))

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
                "capture_readback_duration_ms": float(capture.get("readback_duration_ms", 0.0)),
                "sapling_update": sapling_update
            })
            last_observed_slot = due_slot
        else:
            await process_frame

    var endpoint_row := states[ENDPOINT_WITNESS_PHASE] as Dictionary
    var endpoint_scene := endpoint_row["scene"] as Dictionary
    var endpoint_update := fill_sapling(endpoint_scene["sapling"] as Dictionary)
    if endpoint_update.is_empty():
        fail("endpoint witness update failed in %s" % context)
        return {}
    await RenderingServer.frame_post_draw
    var endpoint_post_draw_us := Time.get_ticks_usec()
    var endpoint_image := camera.get_viewport().get_texture().get_image()
    if endpoint_image == null or endpoint_image.is_empty():
        fail("endpoint witness direct capture failed in %s" % context)
        return {}

    # Encoding occurs only after the timed scheduling window has finished.
    var capture_manifest := _save_deferred_captures(deferred_captures, context)
    if capture_manifest.size() != records.size():
        fail("direct timed capture manifest count mismatch in %s" % context)
        return {}
    var endpoint_png := _save_endpoint_capture(endpoint_image, context)
    if endpoint_png.is_empty():
        return {}

    var missing_slots := _slots_missing(records)
    var state := "PASS_WALL_CLOCK_DIRECT_TIMED_CAPTURE_FULL_SOURCE_COVERAGE"
    if not missing_slots.is_empty():
        state = "PASS_WALL_CLOCK_DIRECT_TIMED_CAPTURE_SOURCE_DROPS_OBSERVED"

    return {
        "state": state,
        "context": context,
        "presentation_mode": PRESENTATION_MODE,
        "weather_policy": WEATHER_POLICY,
        "capture_schema": CAPTURE_SCHEMA,
        "capture_mode": CAPTURE_MODE,
        "capture_manifest": capture_manifest,
        "captured_frame_count": capture_manifest.size(),
        "capture_readback_duration_ms": {
            "mean": _mean(capture_readback_ms),
            "p50": _percentile(capture_readback_ms, 0.50),
            "p95": _percentile(capture_readback_ms, 0.95),
            "max": capture_readback_ms.max() if not capture_readback_ms.is_empty() else 0.0
        },
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
        "endpoint_png_path": endpoint_png,
        "endpoint_post_draw_offset_ms": float(endpoint_post_draw_us - start_us) / 1000.0,
        "runtime_stats_after_endpoint": runtime_stats()
    }

func write_receipt()->void:
    receipt["direct_timed_visual_capture_schema"] = CAPTURE_SCHEMA
    receipt["direct_timed_visual_capture_mode"] = CAPTURE_MODE
    receipt["direct_timed_visual_capture_truth_boundary"] = "Direct post-draw proof-host viewport captures of the actually presented phase-locked direct Nature source states. PNG encoding is deferred until each timed window ends; viewport readback remains instrumentation overhead and its duration is retained per frame. These images are direct rendered-frame evidence but not display scanout, perceptual naturalness, target-device performance, physical wind/biomechanics, gameplay/collision, final Art/QA acceptance, CANON or production readiness."
    var file := FileAccess.open(CAPTURE_RECEIPT_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(receipt, "  ") + "\n")
        file.close()
