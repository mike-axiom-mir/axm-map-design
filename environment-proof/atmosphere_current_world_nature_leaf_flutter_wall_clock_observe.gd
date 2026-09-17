extends "res://atmosphere_current_world_nature_leaf_flutter_observe.gd"

const WALL_CLOCK_RECEIPT_PATH := "res://vfx-nature-leaf-flutter-wall-clock-runtime.json"
const WALL_CLOCK_SCHEMA := "axm.vfx-current-world-nature-leaf-flutter-wall-clock-observation/v0.1"
const EXACT_ENVIRONMENT_PARENT_HEAD := "7713cbe5863c3bc38dabb6236eb4b393401224b6"
const EXACT_VFX_EFFECT_HEAD := "ecade64227ba1d3d1faf029ca7188ea63c2560ec"
const PLAYBACK_CONTEXTS := ["path_eye", "elevated_oblique"]
const UNIQUE_PHASE_COUNT := 16
const ENDPOINT_WITNESS_PHASE := 16
const PHASE_STEP_S := 0.03125
const CYCLE_DURATION_S := 0.5
const TEST_CYCLES := 3
const PHASE_STEP_US := 31250
const EXPECTED_SLOTS_PER_CONTEXT := UNIQUE_PHASE_COUNT * TEST_CYCLES
const PRESENTATION_MODE := "PHASE_LOCKED_LATEST_DUE_DIRECT_SOURCE_STATE_NO_RETIME"
const WEATHER_POLICY := "FIXED_AT_SOURCE_PHASE_00_SOURCE_WIDTH_PRESENTATION"

func write_receipt()->void:
    var file := FileAccess.open(WALL_CLOCK_RECEIPT_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(receipt, "  ") + "\n")
        file.close()

func _percentile(values:Array, fraction:float)->float:
    if values.is_empty():
        return 0.0
    var ordered := values.duplicate()
    ordered.sort()
    var index := clampi(int(ceil(float(ordered.size() - 1) * fraction)), 0, ordered.size() - 1)
    return float(ordered[index])

func _mean(values:Array)->float:
    if values.is_empty():
        return 0.0
    var total := 0.0
    for value in values:
        total += float(value)
    return total / float(values.size())

func _slots_missing(records:Array)->Array:
    var seen := {}
    for record_value in records:
        var record := record_value as Dictionary
        seen[int(record.get("absolute_slot", -1))] = true
    var missing:Array=[]
    for slot in range(EXPECTED_SLOTS_PER_CONTEXT):
        if not seen.has(slot):
            missing.append(slot)
    return missing

func _phase_coverage(records:Array)->Dictionary:
    var counts := {}
    for phase in range(UNIQUE_PHASE_COUNT):
        counts[str(phase)] = 0
    for record_value in records:
        var record := record_value as Dictionary
        var phase := int(record.get("source_phase_index", -1))
        if phase >= 0 and phase < UNIQUE_PHASE_COUNT:
            counts[str(phase)] = int(counts[str(phase)]) + 1
    return counts

func _run_context(states:Array, camera:Camera3D, context:String)->Dictionary:
    var first_row := states[0] as Dictionary
    var first_scene := first_row["scene"] as Dictionary
    configure_camera(camera, first_scene, context)
    await settle(4)

    # Hold Weather literally fixed while the exact accepted sapling response is
    # driven in real wall clock. This isolates the VFX timing question from a
    # simultaneous Weather animation without changing Weather source semantics.
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
    var frame_intervals_ms:Array=[]
    var selection_lateness_ms:Array=[]
    var submit_lateness_ms:Array=[]
    var post_draw_lateness_ms:Array=[]
    var apply_duration_ms:Array=[]
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
                fail("sapling update failed at wall-clock slot %d / %s" % [due_slot, context])
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
                "sapling_update": sapling_update
            })
            last_observed_slot = due_slot
        else:
            await process_frame

    # Phase 16 is the exact endpoint witness, not an extra dwell in the 16-state
    # repeating cycle. Present it only after the timed window to prove exact
    # neutral return remains consumable on the same live receiver.
    var endpoint_row := states[ENDPOINT_WITNESS_PHASE] as Dictionary
    var endpoint_scene := endpoint_row["scene"] as Dictionary
    var endpoint_update := fill_sapling(endpoint_scene["sapling"] as Dictionary)
    if endpoint_update.is_empty():
        fail("endpoint witness update failed in %s" % context)
        return {}
    await RenderingServer.frame_post_draw
    var endpoint_post_draw_us := Time.get_ticks_usec()

    var missing_slots := _slots_missing(records)
    var state := "PASS_WALL_CLOCK_REFERENCE_CHARACTERIZATION_FULL_SOURCE_COVERAGE"
    if not missing_slots.is_empty():
        state = "PASS_WALL_CLOCK_REFERENCE_CHARACTERIZATION_SOURCE_DROPS_OBSERVED"

    return {
        "state": state,
        "context": context,
        "presentation_mode": PRESENTATION_MODE,
        "weather_policy": WEATHER_POLICY,
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
        "schema": WALL_CLOCK_SCHEMA,
        "state": "NOT_RUN",
        "promotion_effect": "NONE",
        "proof_runtime": "Godot 4.7.2 GL Compatibility",
        "environment_parent_head": EXACT_ENVIRONMENT_PARENT_HEAD,
        "vfx_effect_head": EXACT_VFX_EFFECT_HEAD,
        "presentation_mode": PRESENTATION_MODE,
        "weather_policy": WEATHER_POLICY,
        "source_phase_step_s": PHASE_STEP_S,
        "source_unique_phase_count": UNIQUE_PHASE_COUNT,
        "source_endpoint_witness_phase": ENDPOINT_WITNESS_PHASE,
        "source_cycle_duration_s": CYCLE_DURATION_S,
        "test_cycles_per_context": TEST_CYCLES,
        "truth_boundary": "Real proof-host wall-clock presentation characterization of the exact Art-preferred Nature leaf micro-flutter source states inside the exact current-world receiver. Weather is held at exact source phase 00 using the existing source-width presentation while only the sapling source state advances. The scheduler is phase-locked to monotonic wall clock and presents the latest due direct source state without interpolation or retiming; missed slots are retained as evidence rather than slowing the effect. This is not display-scanout timing, perceptual naturalness, physical wind, gameplay, target-device performance, final Art/QA acceptance, CANON or production readiness."
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
        fail("wall-clock reference requires exact 17-state source sequence")
        return
    if absf(float((states[1] as Dictionary).get("time_s", -1.0)) - PHASE_STEP_S) > 1e-12:
        fail("leaf-flutter source phase spacing drifted")
        return
    if absf(float((states[ENDPOINT_WITNESS_PHASE] as Dictionary).get("time_s", -1.0)) - CYCLE_DURATION_S) > 1e-12:
        fail("leaf-flutter endpoint time drifted")
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
    var any_source_drops := false
    for context_value in PLAYBACK_CONTEXTS:
        var context := String(context_value)
        var result := await _run_context(states, camera, context)
        if result.is_empty():
            return
        if int(result.get("skipped_slot_count", 0)) > 0:
            any_source_drops = true
        contexts[context] = result

    receipt["state"] = "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_WALL_CLOCK_REFERENCE_FULL_SOURCE_COVERAGE"
    if any_source_drops:
        receipt["state"] = "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_WALL_CLOCK_REFERENCE_SOURCE_DROPS_OBSERVED"
    receipt["receiving_head"] = payload.get("receiving_head", "")
    receipt["environment_head"] = payload.get("environment_head", "")
    receipt["nature_leaf_flutter_vfx_head"] = payload.get("nature_leaf_flutter_vfx_head", "")
    receipt["nature_leaf_flutter_geometry_context_head"] = payload.get("nature_leaf_flutter_geometry_context_head", "")
    receipt["static_source_meshes"] = static_source_stats
    receipt["contexts"] = contexts
    receipt["godot_version"] = Engine.get_version_info()
    receipt["truth_flags"] = {
        "exact_art_preferred_spatial_response_preserved": true,
        "geometry_materials_environment_and_cameras_reauthored": false,
        "weather_semantics_reauthored": false,
        "weather_held_fixed_during_timing_run": true,
        "direct_source_states_only": true,
        "interpolation_added": false,
        "retiming_added": false,
        "monotonic_wall_clock_scheduler_tested": true,
        "render_frame_post_draw_observed": true,
        "display_scanout_timing_proven": false,
        "perceptual_naturalness_or_final_art_acceptance": false,
        "physical_wind_or_biomechanics": false,
        "gameplay_or_collision": false,
        "target_device_performance": false,
        "canon_or_production_readiness": false
    }
    write_receipt()
    print(receipt["state"])
    quit(0)
