extends "res://atmosphere_current_world_object_motion_observe.gd"

const OUTPUT_PATH := "res://animation-object-current-world-wallclock-runtime.json"
const CONTRACT_SCHEMA := "axm.animation-object-current-world-wallclock/v0.1"
const RECEIPT_SCHEMA := "axm.animation-object-current-world-wallclock-observation/v0.1"
const PASS_STATE := "PASS_OBJECT_CURRENT_WORLD_OWNER_ANIMATION_WALLCLOCK_AND_SHADED_REVIEW_SEQUENCE"
const EXACT_TA_PARENT_HEAD := "d2974dec5043ed9afad346574b23ef8bd4438a76"
const OWNER_ANIMATION_HEAD := "c688936a84f80f292e43587c9d3386bd717f8178"
const OWNER_SEQUENCE_DIGEST := "0a3523cf792264f610881552fd2ebd438aabdfd05e30e92af9dbb33ded1fa2d3"
const OWNER_DURATION_S := 2.5
const OWNER_RATE_HZ := 40.0
const OWNER_SAMPLE_COUNT := 101
const CAMERA_CONTEXT := "path_eye"
const ANGLE_EPS_DEG := 0.0002
const POSITION_EPS_M := 0.000001
const MAX_TIMED_FRAMES := 2000
const MAX_REVIEW_FRAMES := 240

var animation_receipt:Dictionary = {}

func _write_animation_receipt()->void:
    var file := FileAccess.open(OUTPUT_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(animation_receipt, "  ") + "\n")
        file.close()

func _animation_fail(message:String)->void:
    animation_receipt["state"] = "FAIL"
    animation_receipt["error"] = message
    _write_animation_receipt()
    push_error(message)
    quit(1)

func _find_animation_player(root:Node)->AnimationPlayer:
    if root is AnimationPlayer and String(root.name) == "AXM_CURRENT_WORLD_OBJECT_OWNER_SAMPLES":
        return root as AnimationPlayer
    for child in root.get_children():
        var found := _find_animation_player(child)
        if found != null:
            return found
    return null

func _collect_pivots(container:Node3D, plan:Dictionary)->Dictionary:
    var pivots:Dictionary = {}
    for raw in plan.get("stations", []) as Array:
        var station := raw as Dictionary
        var sid := String(station.get("station_id", ""))
        var node := _motion_find_node(container, "technical_art_motion_pivot_" + sid)
        if node == null:
            return {}
        pivots[sid] = node
    return pivots

func _latch_angles(pivots:Dictionary)->Array:
    var values:Array = []
    var keys:Array = pivots.keys()
    keys.sort()
    for sid in keys:
        values.append((pivots[sid] as Node3D).rotation_degrees.x)
    return values

func _match_owner_sample(plan:Dictionary, position_s:float, lid_angle:float, latch_angles:Array)->Dictionary:
    var best_error := INF
    var best_time_error := INF
    var best_index := -1
    for raw in plan.get("samples", []) as Array:
        var row := raw as Dictionary
        var error := absf(lid_angle - float(row["lid_target_rotation_deg_x"]))
        for raw_latch in latch_angles:
            error = maxf(error, absf(float(raw_latch) - float(row["latch_target_rotation_deg_x"])))
        var time_error := absf(position_s - float(row["time_s"]))
        if error < best_error - 0.0000001 or (absf(error - best_error) <= 0.0000001 and time_error < best_time_error):
            best_error = error
            best_time_error = time_error
            best_index = int(row["index"])
    return {"index":best_index, "max_error_deg":best_error, "time_error_s":best_time_error}

func _mesh_center(container:Node3D, name:String)->Vector3:
    var node := _motion_find_node(container, name)
    if node == null:
        _animation_fail("Animation current-world node missing: " + name)
        return Vector3.ZERO
    return _motion_receiver_local_mesh_center(container, node)

func _build_current_world()->Dictionary:
    var payload := load_payload()
    if payload.is_empty():
        _animation_fail("Animation current-world payload missing")
        return {}
    var states := payload.get("states", []) as Array
    if states.size() != 17:
        _animation_fail("Animation current-world proof requires exact 17-state world payload")
        return {}
    var first_row := states[0] as Dictionary
    var data := first_row.get("scene", {}) as Dictionary
    if data.is_empty():
        _animation_fail("Animation current-world state 00 scene missing")
        return {}

    var viewport := SubViewport.new()
    viewport.size = Vector2i(1100, 720)
    viewport.own_world_3d = true
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
    get_root().add_child(viewport)

    var root3d := Node3D.new()
    root3d.name = "animation-object-current-world-root"
    viewport.add_child(root3d)
    add_environment(root3d)
    for item in data.get("items", []) as Array:
        add_proxy(root3d, item as Dictionary)
    add_path(root3d, data)

    var culling_review := data.get("environment_rear_tree_culling_review", {}) as Dictionary
    var cull_target_asset_id := String(culling_review.get("target_asset_id", ""))
    if cull_target_asset_id != VARIANT_TARGET_REAR_ASSET_ID:
        _animation_fail("Animation current-world rear-tree identity drift")
        return {}

    var static_root := Node3D.new()
    static_root.name = "animation-object-current-world-static-root"
    root3d.add_child(static_root)
    var static_stats := add_static_sources(static_root, data, cull_target_asset_id)
    if static_stats.is_empty():
        _animation_fail("Animation current-world static receiver construction failed")
        return {}

    make_weather()
    weather_material.cull_mode = BaseMaterial3D.CULL_DISABLED
    root3d.add_child(weather_node)
    make_sapling()
    root3d.add_child(sapling_node)
    var sapling_update := fill_sapling(data.get("sapling", {}) as Dictionary)
    if sapling_update.is_empty():
        _animation_fail("Animation current-world west sapling phase 00 failed")
        return {}

    var camera := Camera3D.new()
    camera.near = 0.05
    camera.far = 120.0
    root3d.add_child(camera)
    camera.make_current()
    configure_camera(camera, data, CAMERA_CONTEXT)
    await settle()
    var weather_update := fill_weather_width_ribbons(data.get("weather_lines", []) as Array, camera)
    if String(weather_update.get("state", "")) != "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
        _animation_fail("Animation current-world Weather phase 00 failed")
        return {}
    await settle()

    var container := _motion_find_node(static_root, OBJECT_ASSET_ID)
    if container == null:
        _animation_fail("Animation current-world Object rigid receiver missing")
        return {}
    var player := _find_animation_player(container)
    if player == null:
        _animation_fail("Animation current-world owner AnimationPlayer missing")
        return {}
    var plan := _motion_read_json(MOTION_PLAN_PATH)
    if plan.is_empty():
        _animation_fail("Animation current-world exact motion plan missing")
        return {}
    if String(plan.get("animation_head", "")) != OWNER_ANIMATION_HEAD or String(plan.get("sequence_digest", "")) != OWNER_SEQUENCE_DIGEST:
        _animation_fail("Animation current-world owner identity drift")
        return {}
    if int(plan.get("sample_count", -1)) != OWNER_SAMPLE_COUNT or absf(float(plan.get("duration_s", -1.0)) - OWNER_DURATION_S) > 0.000001:
        _animation_fail("Animation current-world owner timing identity drift")
        return {}

    var lid := _motion_find_node(container, "lid_shell")
    var keeper0 := _motion_find_node(container, "latch_0_keeper")
    var keeper1 := _motion_find_node(container, "latch_1_keeper")
    if lid == null or keeper0 == null or keeper1 == null:
        _animation_fail("Animation current-world lid/keeper hierarchy missing")
        return {}
    var pivots := _collect_pivots(container, plan)
    if pivots.size() != 2:
        _animation_fail("Animation current-world latch pivot count drift")
        return {}

    return {
        "viewport":viewport,
        "root3d":root3d,
        "static_root":static_root,
        "container":container,
        "player":player,
        "plan":plan,
        "lid":lid,
        "keeper0":keeper0,
        "keeper1":keeper1,
        "pivots":pivots,
        "camera":camera
    }

func _timed_playback(world:Dictionary)->Dictionary:
    var container := world["container"] as Node3D
    var player := world["player"] as AnimationPlayer
    var plan := world["plan"] as Dictionary
    var lid := world["lid"] as Node3D
    var pivots := world["pivots"] as Dictionary

    player.stop()
    player.seek(0.0, true)
    player.speed_scale = 1.0
    await process_frame
    await RenderingServer.frame_post_draw

    var start_keeper0 := _mesh_center(container, "latch_0_keeper")
    var start_keeper1 := _mesh_center(container, "latch_1_keeper")
    var start_levers:Dictionary = {}
    for raw in plan.get("stations", []) as Array:
        var station := raw as Dictionary
        var lever_name := String(station["lever_component"])
        start_levers[lever_name] = _mesh_center(container, lever_name)

    var player_id := player.get_instance_id()
    var receiver_id := container.get_instance_id()
    var start_usec := Time.get_ticks_usec()
    var previous_usec := start_usec
    var intervals_ms:Array = []
    var observations:Array = []
    var seen_indices:Dictionary = {}
    var phase_order_violations := 0
    var max_sample_error_deg := 0.0
    var max_lid_angle_deg := 0.0
    var min_latch_angle_deg := 0.0
    var frame_count := 0
    var natural_stop := false

    player.play("owner_samples")
    while frame_count < MAX_TIMED_FRAMES:
        await process_frame
        await RenderingServer.frame_post_draw
        frame_count += 1
        var now_usec := Time.get_ticks_usec()
        intervals_ms.append(float(now_usec - previous_usec) / 1000.0)
        previous_usec = now_usec
        if player.get_instance_id() != player_id or container.get_instance_id() != receiver_id:
            _animation_fail("Animation current-world receiver or AnimationPlayer identity changed")
            return {}
        var position_s := player.current_animation_position
        var lid_angle := lid.rotation_degrees.x
        var latch_angles := _latch_angles(pivots)
        if latch_angles.size() != 2:
            _animation_fail("Animation current-world lost bilateral latch pivots")
            return {}
        var matched := _match_owner_sample(plan, position_s, lid_angle, latch_angles)
        var sample_error := float(matched["max_error_deg"])
        max_sample_error_deg = maxf(max_sample_error_deg, sample_error)
        if sample_error > ANGLE_EPS_DEG:
            _animation_fail("Animation current-world wall-clock pose escaped exact owner samples")
            return {}
        var matched_index := int(matched["index"])
        seen_indices[matched_index] = true
        max_lid_angle_deg = maxf(max_lid_angle_deg, absf(lid_angle))
        for raw_angle in latch_angles:
            min_latch_angle_deg = minf(min_latch_angle_deg, float(raw_angle))
            if absf(lid_angle) > ANGLE_EPS_DEG and absf(float(raw_angle) + 50.0) > ANGLE_EPS_DEG:
                phase_order_violations += 1
        if observations.is_empty() or int((observations[observations.size()-1] as Dictionary)["matched_owner_sample_index"]) != matched_index:
            observations.append({
                "frame":frame_count,
                "elapsed_s":float(now_usec - start_usec) / 1000000.0,
                "animation_position_s":position_s,
                "matched_owner_sample_index":matched_index,
                "max_owner_sample_error_deg":sample_error,
                "lid_rotation_deg_x":lid_angle,
                "latch_rotation_deg_x":latch_angles
            })
        if not player.is_playing():
            natural_stop = true
            break

    var elapsed_s := float(Time.get_ticks_usec() - start_usec) / 1000000.0
    if not natural_stop:
        _animation_fail("Animation current-world timed playback did not stop naturally")
        return {}
    if phase_order_violations != 0:
        _animation_fail("Animation current-world wall-clock phase ordering violated")
        return {}
    if max_lid_angle_deg < 99.0 or min_latch_angle_deg > -49.9:
        _animation_fail("Animation current-world wall-clock playback did not traverse owner peak poses")
        return {}

    var endpoint_keeper_drift := maxf(start_keeper0.distance_to(_mesh_center(container, "latch_0_keeper")), start_keeper1.distance_to(_mesh_center(container, "latch_1_keeper")))
    var endpoint_lever_drift := 0.0
    for lever_name in start_levers.keys():
        var start_center:Vector3 = start_levers[lever_name]
        endpoint_lever_drift = maxf(endpoint_lever_drift, start_center.distance_to(_mesh_center(container, String(lever_name))))
    if endpoint_keeper_drift > POSITION_EPS_M or endpoint_lever_drift > POSITION_EPS_M:
        _animation_fail("Animation current-world wall-clock endpoint closure drift")
        return {}

    var min_interval_ms := 0.0
    var mean_interval_ms := 0.0
    var max_interval_ms := 0.0
    if not intervals_ms.is_empty():
        min_interval_ms = float(intervals_ms[0])
        max_interval_ms = float(intervals_ms[0])
        var total := 0.0
        for raw_interval in intervals_ms:
            var value := float(raw_interval)
            min_interval_ms = minf(min_interval_ms, value)
            max_interval_ms = maxf(max_interval_ms, value)
            total += value
        mean_interval_ms = total / float(intervals_ms.size())

    var seen:Array = seen_indices.keys()
    seen.sort()
    return {
        "observation_semantics":"FRAME_POST_DRAW_METADATA_ONLY_NO_VIEWPORT_READBACK_NO_DISK_WRITE",
        "natural_stop":natural_stop,
        "elapsed_s":elapsed_s,
        "process_frame_count":frame_count,
        "observed_owner_sample_indices":seen,
        "observed_owner_sample_count":seen.size(),
        "pose_transition_records":observations,
        "max_owner_sample_error_deg":max_sample_error_deg,
        "phase_order_violations":phase_order_violations,
        "max_abs_lid_angle_deg":max_lid_angle_deg,
        "min_latch_angle_deg":min_latch_angle_deg,
        "endpoint_keeper_drift_m":endpoint_keeper_drift,
        "endpoint_lever_drift_m":endpoint_lever_drift,
        "frame_post_draw_interval_min_ms":min_interval_ms,
        "frame_post_draw_interval_mean_ms":mean_interval_ms,
        "frame_post_draw_interval_max_ms":max_interval_ms,
        "performance_authority":false
    }

func _review_playback(world:Dictionary)->Dictionary:
    var viewport := world["viewport"] as SubViewport
    var player := world["player"] as AnimationPlayer
    var plan := world["plan"] as Dictionary
    var lid := world["lid"] as Node3D
    var pivots := world["pivots"] as Dictionary

    player.stop()
    player.seek(0.0, true)
    await process_frame
    await RenderingServer.frame_post_draw

    var frames:Array = []
    var frame_index := 0
    var first_image := viewport.get_texture().get_image()
    if first_image == null or first_image.is_empty():
        _animation_fail("Animation current-world neutral review raster unavailable")
        return {}
    var first_path := "res://animation-object-current-world-wallclock-frame-%03d.png" % frame_index
    if first_image.save_png(first_path) != OK:
        _animation_fail("Animation current-world neutral review raster save failed")
        return {}
    frames.append({"frame":frame_index,"animation_position_s":0.0,"matched_owner_sample_index":0,"path":first_path,"bytes":FileAccess.get_file_as_bytes(first_path).size()})
    frame_index += 1

    player.play("owner_samples")
    var safety := 0
    while safety < MAX_REVIEW_FRAMES:
        await process_frame
        await RenderingServer.frame_post_draw
        safety += 1
        var position_s := player.current_animation_position
        var lid_angle := lid.rotation_degrees.x
        var latch_angles := _latch_angles(pivots)
        var matched := _match_owner_sample(plan, position_s, lid_angle, latch_angles)
        if float(matched["max_error_deg"]) > ANGLE_EPS_DEG:
            _animation_fail("Animation current-world captured playback escaped exact owner sample")
            return {}
        var image := viewport.get_texture().get_image()
        if image == null or image.is_empty():
            _animation_fail("Animation current-world wall-clock review raster unavailable")
            return {}
        var path := "res://animation-object-current-world-wallclock-frame-%03d.png" % frame_index
        if image.save_png(path) != OK:
            _animation_fail("Animation current-world wall-clock review raster save failed")
            return {}
        frames.append({
            "frame":frame_index,
            "animation_position_s":position_s,
            "matched_owner_sample_index":int(matched["index"]),
            "max_owner_sample_error_deg":float(matched["max_error_deg"]),
            "lid_rotation_deg_x":lid_angle,
            "latch_rotation_deg_x":latch_angles,
            "path":path,
            "bytes":FileAccess.get_file_as_bytes(path).size()
        })
        frame_index += 1
        if not player.is_playing():
            break
    if player.is_playing():
        _animation_fail("Animation current-world captured review playback exceeded safety frame budget")
        return {}
    if frames.size() < 12:
        _animation_fail("Animation current-world captured review sequence too short")
        return {}

    return {
        "observation_semantics":"SECOND_REAL_ANIMATIONPLAYER_PLAYBACK_WITH_VIEWPORT_READBACK_AND_PNG_IO__TIMING_NOT_PERFORMANCE_EVIDENCE",
        "camera_context":CAMERA_CONTEXT,
        "frame_count":frames.size(),
        "frames":frames,
        "capture_timing_accepted":false,
        "display_scanout_accepted":false
    }

func _initialize()->void:
    animation_receipt = {
        "schema":RECEIPT_SCHEMA,
        "state":"STARTED",
        "contract_schema":CONTRACT_SCHEMA,
        "technical_art_parent_head":EXACT_TA_PARENT_HEAD,
        "animation_head":OWNER_ANIMATION_HEAD,
        "sequence_digest":OWNER_SEQUENCE_DIGEST,
        "duration_s":OWNER_DURATION_S,
        "sample_rate_hz":OWNER_RATE_HZ,
        "sample_count":OWNER_SAMPLE_COUNT,
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "receiver_construction_owned_by_technical_art":true,
        "source_motion_retimed":false,
        "source_keys_changed":false,
        "source_easing_changed":false,
        "source_amplitude_changed":false,
        "vfx_adoption":false,
        "environment_adoption":false,
        "runtime_controller_accepted":false,
        "target_device_performance_accepted":false,
        "gameplay_accepted":false,
        "physics_accepted":false,
        "art_qa_accepted":false,
        "canon":false,
        "production_ready":false
    }

    var world := await _build_current_world()
    if world.is_empty():
        return
    var timed := await _timed_playback(world)
    if timed.is_empty():
        return
    var review := await _review_playback(world)
    if review.is_empty():
        return

    animation_receipt["state"] = PASS_STATE
    animation_receipt["timed_playback"] = timed
    animation_receipt["shaded_review_playback"] = review
    animation_receipt["truth_boundary"] = "The exact owner-authored 2.5 s / 40 Hz / 101-key Object sequence is played by the real Godot AnimationPlayer on the exact Technical-Art current-world rigid receiver. A first metadata-only frame_post_draw pass proves natural completion, exact-owner-sample pose membership, release-before-lid/lid-neutral-before-reengage ordering and neutral endpoint closure without viewport readback or disk IO. A second real playback retains shaded frames for visual review; that capture pass is instrumentation and is not performance evidence. No Runtime/controller, device-performance, VFX, Environment-adoption, gameplay, physics, Art/QA, CANON or production acceptance is transferred."
    _write_animation_receipt()
    quit(0)
