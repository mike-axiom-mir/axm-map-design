extends "res://animation_compact_east_current_world_playback_observe.gd"

const WALLCLOCK_SCHEMA := "axm.animation-compact-east-current-world-wallclock-sequence/v0.1"
const EXACT_PLAYBACK_PREDECESSOR_HEAD := "48dc93848aa336f9b6079ccfe738acbe539253ac"
const WALLCLOCK_OUTPUT_PATH := "res://animation-compact-east-current-world-wallclock-runtime.json"
const WALLCLOCK_RESULT := "PASS_COMPACT_EAST_CURRENT_WORLD_REVIEWABLE_WALL_CLOCK_FRAME_SEQUENCE_RETAINED"
const WALLCLOCK_CAPTURE_SEMANTICS := "FRAME_POST_DRAW_RENDERED_SEQUENCE_WITH_IMAGE_READBACK_INSTRUMENTATION_NOT_UNINSTRUMENTED_DISPLAY_SCANOUT"
const REQUIRED_WARMUP_WRAPS := 1
const REQUIRED_CAPTURED_LOOPS := 2

func _wallclock_write_receipt()->void:
    var file := FileAccess.open(WALLCLOCK_OUTPUT_PATH, FileAccess.WRITE)
    if file:
        file.store_string(JSON.stringify(receipt, "  ") + "\n")

func _wallclock_fail(message:String)->void:
    receipt["state"] = "FAIL"
    receipt["error"] = message
    _wallclock_write_receipt()
    push_error(message)
    quit(1)

func _capture_rendered_frame(viewport:SubViewport, frame_index:int, active_phase:int, timestamp_s:float, animation_position_s:float, wrapped:bool, cycle_index:int)->Dictionary:
    var image := viewport.get_texture().get_image()
    if image == null or image.is_empty():
        return {}
    return {
        "sequence_index": frame_index,
        "timestamp_s": timestamp_s,
        "animation_position_s": animation_position_s,
        "observed_phase": active_phase,
        "wrapped": wrapped,
        "cycle_index": cycle_index,
        "width": image.get_width(),
        "height": image.get_height(),
        "image": image
    }

func _initialize()->void:
    receipt = {
        "schema": WALLCLOCK_SCHEMA,
        "state": "STARTED",
        "exact_playback_predecessor_head": EXACT_PLAYBACK_PREDECESSOR_HEAD,
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
        "capture_semantics": WALLCLOCK_CAPTURE_SEMANTICS,
        "proof_runtime": "Godot 4.7.2 GL Compatibility",
        "promotion_effect": "NONE",
        "full_source_state_delivery_accepted": false,
        "visual_motion_naturalness_accepted": false,
        "display_scanout_accepted": false,
        "runtime_controller_accepted": false,
        "gameplay_accepted": false
    }

    var payload := load_payload()
    if payload.is_empty():
        _wallclock_fail("wall-clock sequence could not load exact VFX receiving payload")
        return
    var states := payload.get("states", []) as Array
    if states.size() != 17:
        _wallclock_fail("wall-clock sequence requires exact 17-state source sequence")
        return
    if String(payload.get("environment_head", "")) != PARENT_VFX_HEAD:
        _wallclock_fail("wall-clock sequence current-world VFX receiving head drift")
        return
    if String(payload.get("compact_east_visual_response_vfx_head", "")) != COMPACT_EAST_VFX_HEAD:
        _wallclock_fail("wall-clock sequence source VFX identity drift")
        return

    var source0 := _source_for_phase(states, 0)
    var source16 := _source_for_phase(states, 16)
    var endpoint_delta := _max_vertex_delta(
        source0.get("vertices_source_xyz_m", []) as Array,
        source16.get("vertices_source_xyz_m", []) as Array
    )
    if endpoint_delta > 1e-12:
        _wallclock_fail("wall-clock sequence source endpoint seam is not exact")
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
        _wallclock_fail("wall-clock sequence rear-tree culling identity drift")
        return

    var static_root := Node3D.new()
    static_root.name = "animation-wallclock-static-source-root"
    root3d.add_child(static_root)
    var static_stats := add_static_sources(static_root, data, cull_target_asset_id)
    var dynamic_node := _find_compact_child(static_root, static_stats)
    if dynamic_node == null:
        _wallclock_fail("wall-clock sequence compact-east receiver missing")
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
        _wallclock_fail("wall-clock sequence could not freeze west-sapling phase 00")
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
        _wallclock_fail("wall-clock sequence could not freeze exact Weather source-width phase 00")
        return
    await settle()

    var player := _make_player(root3d, dynamic_node, phase_meshes)
    var player_id := player.get_instance_id()
    var receiver_id := dynamic_node.get_instance_id()
    player.seek(0.0, true)
    player.play("compact_east_exact_states")

    var previous_phase := _phase_for_mesh(dynamic_node.mesh, phase_meshes)
    if previous_phase < 0:
        _wallclock_fail("wall-clock sequence initial phase is not an exact source mesh")
        return

    var warmup_wraps := 0
    var captured_wraps := 0
    var capture_started := false
    var capture_start_usec := 0
    var previous_capture_usec := 0
    var frame_intervals_ms:Array = []
    var frame_records:Array = []
    var frame_images:Array = []
    var completed_cycles:Array = []
    var current_cycle:Array = []
    var safety_frames := 0

    while captured_wraps < REQUIRED_CAPTURED_LOOPS and safety_frames < 12000:
        await process_frame
        await RenderingServer.frame_post_draw
        safety_frames += 1
        if player.get_instance_id() != player_id or dynamic_node.get_instance_id() != receiver_id:
            _wallclock_fail("wall-clock sequence receiver or AnimationPlayer identity changed")
            return
        var active_phase := _phase_for_mesh(dynamic_node.mesh, phase_meshes)
        if active_phase < 0:
            _wallclock_fail("wall-clock sequence rendered an unknown mesh resource")
            return
        var wrapped := active_phase < previous_phase
        var now_usec := Time.get_ticks_usec()

        if not capture_started:
            if wrapped:
                warmup_wraps += 1
                if warmup_wraps >= REQUIRED_WARMUP_WRAPS:
                    capture_started = true
                    capture_start_usec = now_usec
                    previous_capture_usec = now_usec
                    current_cycle = [active_phase]
                    var first_frame := _capture_rendered_frame(viewport, 0, active_phase, 0.0, player.current_animation_position, true, 0)
                    if first_frame.is_empty():
                        _wallclock_fail("wall-clock sequence could not read first rendered frame")
                        return
                    frame_images.append(first_frame.pop("image"))
                    frame_records.append(first_frame)
            previous_phase = active_phase
            continue

        if wrapped:
            completed_cycles.append(current_cycle.duplicate())
            captured_wraps += 1
            current_cycle = [active_phase]
        elif not current_cycle.has(active_phase):
            current_cycle.append(active_phase)

        var timestamp_s := float(now_usec - capture_start_usec) / 1000000.0
        frame_intervals_ms.append(float(now_usec - previous_capture_usec) / 1000.0)
        previous_capture_usec = now_usec
        var frame_record := _capture_rendered_frame(
            viewport,
            frame_records.size(),
            active_phase,
            timestamp_s,
            player.current_animation_position,
            wrapped,
            captured_wraps
        )
        if frame_record.is_empty():
            _wallclock_fail("wall-clock sequence could not read rendered frame %s" % frame_records.size())
            return
        frame_images.append(frame_record.pop("image"))
        frame_records.append(frame_record)
        previous_phase = active_phase

    player.stop()
    if warmup_wraps < REQUIRED_WARMUP_WRAPS:
        _wallclock_fail("wall-clock sequence did not complete required warmup loop")
        return
    if captured_wraps != REQUIRED_CAPTURED_LOOPS or completed_cycles.size() != REQUIRED_CAPTURED_LOOPS:
        _wallclock_fail("wall-clock sequence did not retain two complete post-warmup loops")
        return
    if frame_records.size() < 8:
        _wallclock_fail("wall-clock sequence retained too few rendered frames for review")
        return

    var output_records:Array = []
    for index in range(frame_records.size()):
        var row := (frame_records[index] as Dictionary).duplicate(true)
        var phase := int(row.get("observed_phase", -1))
        var path := "res://animation-wallclock-frame-%04d-phase-%02d.png" % [index, phase]
        var image := frame_images[index] as Image
        var error := image.save_png(path)
        if error != OK:
            _wallclock_fail("wall-clock sequence PNG write failed at frame %s" % index)
            return
        row["path"] = path
        row["bytes"] = FileAccess.get_file_as_bytes(path).size()
        output_records.append(row)

    var missing_phases_by_cycle:Array = []
    for cycle in completed_cycles:
        var missing:Array = []
        for phase in range(UNIQUE_LOOP_PHASES):
            if not (cycle as Array).has(phase):
                missing.append(phase)
        missing_phases_by_cycle.append(missing)

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

    receipt["state"] = WALLCLOCK_RESULT
    receipt["receiver_context"] = CONTEXT
    receipt["source_endpoint_geometry_delta_m"] = endpoint_delta
    receipt["warmup_wraps"] = warmup_wraps
    receipt["captured_complete_loops"] = captured_wraps
    receipt["rendered_frame_count"] = output_records.size()
    receipt["rendered_frames"] = output_records
    receipt["captured_cycles_observed_phases"] = completed_cycles
    receipt["captured_cycles_missing_phases"] = missing_phases_by_cycle
    receipt["capture_frame_interval_min_ms"] = min_interval_ms
    receipt["capture_frame_interval_mean_ms"] = mean_interval_ms
    receipt["capture_frame_interval_max_ms"] = max_interval_ms
    receipt["persistent_receiver_instance_id"] = receiver_id
    receipt["persistent_animation_player_instance_id"] = player_id
    receipt["frozen_weather_phase"] = 0
    receipt["frozen_west_sapling_phase"] = 0
    receipt["truth_boundary"] = "Post-warmup frame-post-draw rendered evidence from the exact frozen compact-east current-world AnimationPlayer receiver. Two complete consecutive loops plus the closing seam frame are retained with monotonic timestamps and observed exact phase identity. Image readback is itself instrumentation, so these timings do not certify uninstrumented frame cadence, display scanout, full 31.25 ms source-slot delivery, target-device performance, smooth interpolation, physical wind, final motion naturalness, Runtime controller/state-machine policy, gameplay/collision, Art/QA acceptance, CANON or production readiness."
    _wallclock_write_receipt()
    quit(0)
