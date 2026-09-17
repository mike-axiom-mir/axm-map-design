extends "res://animation_compact_east_current_world_playback_observe.gd"

const PRESENTATION_SCHEMA := "axm.animation-compact-east-current-world-presentation-observation/v0.1"
const EXACT_WALLCLOCK_PREDECESSOR_HEAD := "84a186f087d8d7353cbfb98750f765d21bcc52be"
const PRESENTATION_OUTPUT_PATH := "res://animation-compact-east-current-world-presentation-runtime.json"
const PRESENTATION_PASS := "PASS_COMPACT_EAST_CURRENT_WORLD_LOW_INTRUSION_PRESENTATION_CREST_RETAINED"
const PRESENTATION_HOLD := "HOLD_COMPACT_EAST_CURRENT_WORLD_LOW_INTRUSION_PRESENTATION_CREST_NOT_RETAINED_EVERY_LOOP"
const PRESENTATION_OBSERVATION_SEMANTICS := "FRAME_POST_DRAW_METADATA_ONLY_DURING_TIMED_PLAYBACK__NO_IMAGE_READBACK_OR_DISK_IO_IN_TIMED_LOOP"
const REVIEW_RASTER_SEMANTICS := "POST_PLAYBACK_EXACT_PHASE_RASTER_RECONSTRUCTION_FOR_REVIEW__NOT_CAPTURED_DISPLAY_SCANOUT"
const REQUIRED_WARMUP_WRAPS := 1
const REQUIRED_OBSERVED_LOOPS := 3
const CREST_PHASE := 8

func _presentation_write_receipt()->void:
    var file := FileAccess.open(PRESENTATION_OUTPUT_PATH, FileAccess.WRITE)
    if file:
        file.store_string(JSON.stringify(receipt, "  ") + "\n")

func _presentation_fail(message:String)->void:
    receipt["state"] = "FAIL"
    receipt["error"] = message
    _presentation_write_receipt()
    push_error(message)
    quit(1)

func _reconstruct_exact_phase_raster(viewport:SubViewport, player:AnimationPlayer, phase:int)->Dictionary:
    player.seek(float(phase) * STEP_S, true)
    await process_frame
    await RenderingServer.frame_post_draw
    var image := viewport.get_texture().get_image()
    if image == null or image.is_empty():
        return {}
    var path := "res://animation-presentation-phase-%02d.png" % phase
    var error := image.save_png(path)
    if error != OK:
        return {}
    return {
        "phase": phase,
        "path": path,
        "width": image.get_width(),
        "height": image.get_height(),
        "bytes": FileAccess.get_file_as_bytes(path).size()
    }

func _initialize()->void:
    receipt = {
        "schema": PRESENTATION_SCHEMA,
        "state": "STARTED",
        "exact_wallclock_predecessor_head": EXACT_WALLCLOCK_PREDECESSOR_HEAD,
        "parent_vfx_receiving_head": PARENT_VFX_HEAD,
        "nature_vfx_head": COMPACT_EAST_VFX_HEAD,
        "source_motion_truth": MOTION_TRUTH,
        "duration_s": DURATION_S,
        "intervals": INTERVALS,
        "authored_endpoint_inclusive_states": 17,
        "loop_track_unique_states": UNIQUE_LOOP_PHASES,
        "source_step_s": STEP_S,
        "animation_track_interpolation": "NEAREST",
        "animation_update_mode": "DISCRETE",
        "animation_loop_mode": "LOOP_LINEAR",
        "presentation_observation_semantics": PRESENTATION_OBSERVATION_SEMANTICS,
        "review_raster_semantics": REVIEW_RASTER_SEMANTICS,
        "proof_runtime": "Godot 4.7.2 GL Compatibility",
        "timed_loop_viewport_image_readbacks": 0,
        "timed_loop_disk_writes": 0,
        "promotion_effect": "NONE",
        "full_source_state_delivery_accepted": false,
        "display_scanout_accepted": false,
        "target_device_delivery_accepted": false,
        "visual_motion_naturalness_accepted": false,
        "runtime_controller_accepted": false,
        "gameplay_accepted": false
    }

    var payload := load_payload()
    if payload.is_empty():
        _presentation_fail("presentation observer could not load exact VFX receiving payload")
        return
    var states := payload.get("states", []) as Array
    if states.size() != 17:
        _presentation_fail("presentation observer requires exact 17-state source sequence")
        return
    if String(payload.get("environment_head", "")) != PARENT_VFX_HEAD:
        _presentation_fail("presentation observer current-world VFX receiving head drift")
        return
    if String(payload.get("compact_east_visual_response_vfx_head", "")) != COMPACT_EAST_VFX_HEAD:
        _presentation_fail("presentation observer source VFX identity drift")
        return

    var source0 := _source_for_phase(states, 0)
    var source16 := _source_for_phase(states, 16)
    var endpoint_delta := _max_vertex_delta(
        source0.get("vertices_source_xyz_m", []) as Array,
        source16.get("vertices_source_xyz_m", []) as Array
    )
    if endpoint_delta > 1e-12:
        _presentation_fail("presentation observer source endpoint seam is not exact")
        return

    var source15 := _source_for_phase(states, 15)
    var authored_final_step := _max_vertex_delta(
        source15.get("vertices_source_xyz_m", []) as Array,
        source16.get("vertices_source_xyz_m", []) as Array
    )
    var loop_step := _max_vertex_delta(
        source15.get("vertices_source_xyz_m", []) as Array,
        source0.get("vertices_source_xyz_m", []) as Array
    )
    if abs(authored_final_step - loop_step) > 1e-12:
        _presentation_fail("presentation observer loop seam adds motion beyond authored final step")
        return

    var first_row := states[0] as Dictionary
    var data := first_row.get("scene", {}) as Dictionary
    var viewport := SubViewport.new()
    viewport.size = Vector2i(1100, 720)
    viewport.own_world_3d = true
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
    get_root().add_child(viewport)

    var root3d := Node3D.new()
    viewport.add_child(root3d)
    add_environment(root3d)
    for item in data.get("items", []) as Array:
        add_proxy(root3d, item as Dictionary)
    add_path(root3d, data)

    var culling_review := data.get("environment_rear_tree_culling_review", {}) as Dictionary
    var cull_target_asset_id := String(culling_review.get("target_asset_id", ""))
    if cull_target_asset_id != VARIANT_TARGET_REAR_ASSET_ID:
        _presentation_fail("presentation observer rear-tree culling identity drift")
        return

    var static_root := Node3D.new()
    static_root.name = "animation-presentation-static-source-root"
    root3d.add_child(static_root)
    var static_stats := add_static_sources(static_root, data, cull_target_asset_id)
    var dynamic_node := _find_compact_child(static_root, static_stats)
    if dynamic_node == null:
        _presentation_fail("presentation observer compact-east receiver missing")
        return

    var phase_meshes:Array = []
    for phase in range(UNIQUE_LOOP_PHASES):
        phase_meshes.append(_phase_mesh(_source_for_phase(states, phase)))
    dynamic_node.mesh = phase_meshes[0]

    make_weather()
    weather_material.cull_mode = BaseMaterial3D.CULL_DISABLED
    root3d.add_child(weather_node)
    make_sapling()
    root3d.add_child(sapling_node)
    var sapling_update := fill_sapling(data.get("sapling", {}) as Dictionary)
    if sapling_update.is_empty():
        _presentation_fail("presentation observer could not freeze west-sapling phase 00")
        return

    var camera := Camera3D.new()
    camera.near = 0.05
    camera.far = 120.0
    root3d.add_child(camera)
    camera.make_current()
    configure_camera(camera, data, CONTEXT)
    await settle()
    var weather_update := fill_weather_width_ribbons(data.get("weather_lines", []) as Array, camera)
    if weather_update.get("state") != "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
        _presentation_fail("presentation observer could not freeze exact Weather source-width phase 00")
        return
    await settle()

    var player := _make_player(root3d, dynamic_node, phase_meshes)
    var player_id := player.get_instance_id()
    var receiver_id := dynamic_node.get_instance_id()
    player.seek(0.0, true)
    player.play("compact_east_exact_states")

    var previous_phase := _phase_for_mesh(dynamic_node.mesh, phase_meshes)
    if previous_phase < 0:
        _presentation_fail("presentation observer initial phase is not an exact source mesh")
        return

    var warmup_wraps := 0
    var observed_wraps := 0
    var observation_started := false
    var observation_start_usec := 0
    var previous_frame_usec := Time.get_ticks_usec()
    var frame_intervals_ms:Array = []
    var frame_observations := 0
    var transition_records:Array = []
    var completed_cycles:Array = []
    var current_cycle:Array = []
    var wrap_times_s:Array = []
    var safety_frames := 0

    while observed_wraps < REQUIRED_OBSERVED_LOOPS and safety_frames < 12000:
        await process_frame
        await RenderingServer.frame_post_draw
        safety_frames += 1
        frame_observations += 1
        if player.get_instance_id() != player_id or dynamic_node.get_instance_id() != receiver_id:
            _presentation_fail("presentation observer receiver or AnimationPlayer identity changed")
            return
        var active_phase := _phase_for_mesh(dynamic_node.mesh, phase_meshes)
        if active_phase < 0:
            _presentation_fail("presentation observer rendered an unknown mesh resource")
            return
        var wrapped := active_phase < previous_phase
        var now_usec := Time.get_ticks_usec()

        if not observation_started:
            if wrapped:
                warmup_wraps += 1
                if warmup_wraps >= REQUIRED_WARMUP_WRAPS:
                    observation_started = true
                    observation_start_usec = now_usec
                    previous_frame_usec = now_usec
                    current_cycle = [active_phase]
                    transition_records.append({
                        "transition_index": 0,
                        "timestamp_s": 0.0,
                        "animation_position_s": player.current_animation_position,
                        "observed_phase": active_phase,
                        "wrapped": true,
                        "cycle_index": 0
                    })
            previous_phase = active_phase
            continue

        frame_intervals_ms.append(float(now_usec - previous_frame_usec) / 1000.0)
        previous_frame_usec = now_usec

        if wrapped:
            completed_cycles.append(current_cycle.duplicate())
            observed_wraps += 1
            wrap_times_s.append(float(now_usec - observation_start_usec) / 1000000.0)
            current_cycle = [active_phase]
        elif active_phase != previous_phase:
            current_cycle.append(active_phase)

        if active_phase != previous_phase or wrapped:
            transition_records.append({
                "transition_index": transition_records.size(),
                "timestamp_s": float(now_usec - observation_start_usec) / 1000000.0,
                "animation_position_s": player.current_animation_position,
                "observed_phase": active_phase,
                "wrapped": wrapped,
                "cycle_index": observed_wraps
            })
        previous_phase = active_phase

    player.stop()
    if warmup_wraps < REQUIRED_WARMUP_WRAPS:
        _presentation_fail("presentation observer did not complete required warmup loop")
        return
    if observed_wraps != REQUIRED_OBSERVED_LOOPS or completed_cycles.size() != REQUIRED_OBSERVED_LOOPS:
        _presentation_fail("presentation observer did not complete three post-warmup loops")
        return
    if transition_records.size() < 8:
        _presentation_fail("presentation observer retained too few phase transitions")
        return

    var missing_phases_by_cycle:Array = []
    var crest_observed_by_cycle:Array = []
    var crest_observed_all_cycles := true
    for cycle in completed_cycles:
        var missing:Array = []
        for phase in range(UNIQUE_LOOP_PHASES):
            if not (cycle as Array).has(phase):
                missing.append(phase)
        missing_phases_by_cycle.append(missing)
        var has_crest := (cycle as Array).has(CREST_PHASE)
        crest_observed_by_cycle.append(has_crest)
        if not has_crest:
            crest_observed_all_cycles = false

    var cycle_durations:Array = []
    var prior_wrap := 0.0
    for raw_wrap in wrap_times_s:
        var wrap_time := float(raw_wrap)
        cycle_durations.append(wrap_time - prior_wrap)
        prior_wrap = wrap_time

    var min_interval_ms := 0.0
    var mean_interval_ms := 0.0
    var max_interval_ms := 0.0
    if not frame_intervals_ms.is_empty():
        min_interval_ms = float(frame_intervals_ms[0])
        max_interval_ms = float(frame_intervals_ms[0])
        var interval_sum := 0.0
        for raw in frame_intervals_ms:
            var value := float(raw)
            min_interval_ms = min(min_interval_ms, value)
            max_interval_ms = max(max_interval_ms, value)
            interval_sum += value
        mean_interval_ms = interval_sum / float(frame_intervals_ms.size())

    # Review rasters are reconstructed only after timed playback has stopped.
    # They make the actually observed phase sequence inspectable without inserting
    # viewport image readback or disk encoding into the timed playback loop itself.
    player.play("compact_east_exact_states")
    player.pause()
    var reconstructed_phase_rasters:Array = []
    for phase in range(UNIQUE_LOOP_PHASES):
        var raster := await _reconstruct_exact_phase_raster(viewport, player, phase)
        if raster.is_empty():
            _presentation_fail("presentation observer could not reconstruct exact phase raster %s" % phase)
            return
        reconstructed_phase_rasters.append(raster)
    player.stop()

    receipt["state"] = PRESENTATION_PASS if crest_observed_all_cycles else PRESENTATION_HOLD
    receipt["receiver_context"] = CONTEXT
    receipt["source_endpoint_geometry_delta_m"] = endpoint_delta
    receipt["authored_final_step_m"] = authored_final_step
    receipt["loop_step_m"] = loop_step
    receipt["loop_step_residual_m"] = abs(authored_final_step - loop_step)
    receipt["warmup_wraps"] = warmup_wraps
    receipt["observed_complete_loops"] = observed_wraps
    receipt["frame_post_draw_observation_count"] = frame_observations
    receipt["phase_transition_count"] = transition_records.size()
    receipt["phase_transitions"] = transition_records
    receipt["observed_cycles_phases"] = completed_cycles
    receipt["observed_cycles_missing_phases"] = missing_phases_by_cycle
    receipt["crest_phase"] = CREST_PHASE
    receipt["crest_observed_by_cycle"] = crest_observed_by_cycle
    receipt["crest_observed_all_cycles"] = crest_observed_all_cycles
    receipt["wrap_times_s"] = wrap_times_s
    receipt["cycle_durations_s"] = cycle_durations
    receipt["frame_post_draw_interval_min_ms"] = min_interval_ms
    receipt["frame_post_draw_interval_mean_ms"] = mean_interval_ms
    receipt["frame_post_draw_interval_max_ms"] = max_interval_ms
    receipt["persistent_receiver_instance_id"] = receiver_id
    receipt["persistent_animation_player_instance_id"] = player_id
    receipt["frozen_weather_phase"] = 0
    receipt["frozen_west_sapling_phase"] = 0
    receipt["reconstructed_phase_rasters"] = reconstructed_phase_rasters
    receipt["reconstructed_phase_raster_count"] = reconstructed_phase_rasters.size()
    receipt["truth_boundary"] = "Real AnimationPlayer playback is observed for three post-warmup loops at frame_post_draw with metadata only: no viewport image readback and no disk write occur inside the timed loop. Exact phase rasters are reconstructed only after playback stops, keyed to the same frozen receiver, camera and source states, so they are review aids rather than captured display scanout. This evidence does not establish target-device delivery, scanout, complete source-slot presentation, physical wind, final motion naturalness, Runtime controller/state-machine policy, gameplay/collision, Art/QA acceptance, CANON or production readiness."
    _presentation_write_receipt()
    quit(0)
