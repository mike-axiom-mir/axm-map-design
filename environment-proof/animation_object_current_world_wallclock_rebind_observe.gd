extends "res://atmosphere_current_world_object_motion_current_rebind_observe.gd"

const ANIM_OUTPUT_PATH := "res://animation-object-current-world-wallclock-runtime.json"
const ANIM_CONTRACT_SCHEMA := "axm.animation-object-current-world-wallclock/v0.2"
const ANIM_RECEIPT_SCHEMA := "axm.animation-object-current-world-wallclock-observation/v0.2"
const ANIM_PASS_STATE := "PASS_OBJECT_CURRENT_WORLD_OWNER_ANIMATION_WALLCLOCK_REBOUND_TO_TA_FC567_RECEIVER"
const ANIM_TA_PARENT_HEAD := "fc567fd6dd061ccb5e8232bd17ee0af3d2e064b7"
const ANIM_PREDECESSOR_EVIDENCE_HEAD := "343668b80acd52367e3427f3ef97d1662625c18f"
const ANIM_HISTORICAL_TA_PARENT_HEAD := "e085437f6cc958bbf7c5c6464578923d542962b0"
const ANIM_OWNER_HEAD := "86bdbe9771bf9eb1bc92bd4160442941763fab1d"
const ANIM_SEQUENCE_DIGEST := "0a3523cf792264f610881552fd2ebd438aabdfd05e30e92af9dbb33ded1fa2d3"
const ANIM_DURATION_S := 2.5
const ANIM_RATE_HZ := 40.0
const ANIM_SAMPLE_COUNT := 101
const ANIM_CAMERA_CONTEXT := "path_eye"
const ANIM_ANGLE_EPS_DEG := 0.0002
const ANIM_POSITION_EPS_M := 0.000001
const ANIM_MAX_TIMED_FRAMES := 2000
const ANIM_MAX_REVIEW_FRAMES := 240
const ANIM_FRAME_RULE := "MATCH_ACTUAL_PIVOT_QUATERNIONS_ABOUT_THE_EXACT_TECHNICAL_ART_HOST_AXIS_AGAINST_THE_ALREADY_ADAPTED_RECEIVER_PLAN__DO_NOT_ASSUME_SOURCE_EULER_X_EQUALS_HOST_EULER_X"

var anim_receipt:Dictionary = {}
var anim_host_axis := Vector3.RIGHT

func _anim_write_receipt()->void:
    var file := FileAccess.open(ANIM_OUTPUT_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(anim_receipt, "  ") + "\n")
        file.close()

func _anim_fail(message:String)->void:
    anim_receipt["state"] = "FAIL"
    anim_receipt["error"] = message
    _anim_write_receipt()
    push_error(message)
    quit(1)

func _anim_find_player(root:Node)->AnimationPlayer:
    if root is AnimationPlayer and String(root.name) == "AXM_CURRENT_WORLD_OBJECT_OWNER_SAMPLES":
        return root as AnimationPlayer
    for child in root.get_children():
        var found := _anim_find_player(child)
        if found != null:
            return found
    return null

func _anim_collect_pivots(container:Node3D, plan:Dictionary)->Dictionary:
    var pivots:Dictionary = {}
    for raw in plan.get("stations", []) as Array:
        var station := raw as Dictionary
        var sid := String(station.get("station_id", ""))
        var node := _motion_find_node(container, "technical_art_motion_latch_world_pivot_" + sid)
        if node == null:
            return {}
        pivots[sid] = node
    return pivots

func _anim_adapted_receiver_angle(node:Node3D)->float:
    var q := node.quaternion.normalized()
    if q.w < 0.0:
        q = Quaternion(-q.x, -q.y, -q.z, -q.w)
    var signed_sin_half := Vector3(q.x, q.y, q.z).dot(anim_host_axis)
    return rad_to_deg(2.0 * atan2(signed_sin_half, q.w))

func _anim_latch_angles(pivots:Dictionary)->Array:
    var values:Array = []
    var keys:Array = pivots.keys()
    keys.sort()
    for sid in keys:
        values.append(_anim_adapted_receiver_angle(pivots[sid] as Node3D))
    return values

func _anim_match_owner_sample(plan:Dictionary, position_s:float, lid:Node3D, pivots:Dictionary)->Dictionary:
    var lid_angle := _anim_adapted_receiver_angle(lid)
    var latch_angles := _anim_latch_angles(pivots)
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
    return {
        "index":best_index,
        "max_error_deg":best_error,
        "time_error_s":best_time_error,
        "adapted_receiver_lid_rotation_deg":lid_angle,
        "adapted_receiver_latch_rotation_deg":latch_angles
    }

func _anim_mesh_center(container:Node3D, name:String)->Vector3:
    var node := _motion_find_node(container, name)
    if node == null:
        _anim_fail("Animation current-world node missing: " + name)
        return Vector3.ZERO
    return _motion_receiver_local_component_center(container, node)

func _anim_build_world()->Dictionary:
    var payload := load_payload()
    if payload.is_empty():
        _anim_fail("Animation current-world payload missing")
        return {}
    var states := payload.get("states", []) as Array
    if states.size() != 17:
        _anim_fail("Animation current-world proof requires exact 17-state world payload")
        return {}
    var first_row := states[0] as Dictionary
    var data := first_row.get("scene", {}) as Dictionary
    if data.is_empty():
        _anim_fail("Animation current-world state 00 scene missing")
        return {}

    var placement := _motion_current_world_placement()
    if placement.is_empty():
        _anim_fail("Animation current-world exact Technical-Art placement missing")
        return {}
    anim_host_axis = placement["axis_receiver"] as Vector3
    if absf(anim_host_axis.length() - 1.0) > 0.000001:
        _anim_fail("Animation current-world Technical-Art host axis is not unit length")
        return {}

    var viewport := SubViewport.new()
    viewport.size = Vector2i(1100, 720)
    viewport.own_world_3d = true
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
    get_root().add_child(viewport)

    var root3d := Node3D.new()
    root3d.name = "animation-object-current-world-successor-root"
    viewport.add_child(root3d)
    add_environment(root3d)
    for item in data.get("items", []) as Array:
        add_proxy(root3d, item as Dictionary)
    add_path(root3d, data)

    var culling_review := data.get("environment_rear_tree_culling_review", {}) as Dictionary
    var cull_target_asset_id := String(culling_review.get("target_asset_id", ""))
    if cull_target_asset_id != VARIANT_TARGET_REAR_ASSET_ID:
        _anim_fail("Animation current-world rear-tree identity drift")
        return {}

    var static_root := Node3D.new()
    static_root.name = "animation-object-current-world-static-root"
    root3d.add_child(static_root)
    var static_stats := add_static_sources(static_root, data, cull_target_asset_id)
    if static_stats.is_empty():
        _anim_fail("Animation current-world static receiver construction failed")
        return {}

    make_weather()
    weather_material.cull_mode = BaseMaterial3D.CULL_DISABLED
    root3d.add_child(weather_node)
    make_sapling()
    root3d.add_child(sapling_node)
    var sapling_update := fill_sapling(data.get("sapling", {}) as Dictionary)
    if sapling_update.is_empty():
        _anim_fail("Animation current-world west sapling phase 00 failed")
        return {}

    var camera := Camera3D.new()
    camera.near = 0.05
    camera.far = 120.0
    root3d.add_child(camera)
    camera.make_current()
    configure_camera(camera, data, ANIM_CAMERA_CONTEXT)
    await settle()
    var weather_update := fill_weather_width_ribbons(data.get("weather_lines", []) as Array, camera)
    if String(weather_update.get("state", "")) != "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
        _anim_fail("Animation current-world Weather phase 00 failed")
        return {}
    await settle()

    var player := _anim_find_player(static_root)
    if player == null:
        _anim_fail("Animation current-world owner AnimationPlayer missing")
        return {}
    var player_parent := player.get_parent()
    if not (player_parent is Node3D):
        _anim_fail("Animation current-world owner AnimationPlayer parent is not the rigid receiver")
        return {}
    var container := player_parent as Node3D

    var plan := _motion_read_json(MOTION_PLAN_PATH)
    if plan.is_empty():
        _anim_fail("Animation current-world exact motion plan missing")
        return {}
    if String(plan.get("animation_head", "")) != ANIM_OWNER_HEAD or String(plan.get("sequence_digest", "")) != ANIM_SEQUENCE_DIGEST:
        _anim_fail("Animation current-world owner identity drift")
        return {}
    if int(plan.get("sample_count", -1)) != ANIM_SAMPLE_COUNT or absf(float(plan.get("duration_s", -1.0)) - ANIM_DURATION_S) > 0.000001:
        _anim_fail("Animation current-world owner timing identity drift")
        return {}

    var lid := _motion_find_node(container, "technical_art_motion_hinge_world_pivot")
    var keeper0 := _motion_find_node(container, "latch_0_keeper")
    var keeper1 := _motion_find_node(container, "latch_1_keeper")
    if lid == null or keeper0 == null or keeper1 == null:
        _anim_fail("Animation current-world hinge/keeper hierarchy missing")
        return {}
    var pivots := _anim_collect_pivots(container, plan)
    if pivots.size() != 2:
        _anim_fail("Animation current-world latch pivot count drift")
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

func _anim_timed_playback(world:Dictionary)->Dictionary:
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

    var start_keeper0 := _anim_mesh_center(container, "latch_0_keeper")
    var start_keeper1 := _anim_mesh_center(container, "latch_1_keeper")
    var start_levers:Dictionary = {}
    for raw in plan.get("stations", []) as Array:
        var station := raw as Dictionary
        var lever_name := String(station["lever_component"])
        start_levers[lever_name] = _anim_mesh_center(container, lever_name)

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
    while frame_count < ANIM_MAX_TIMED_FRAMES:
        await process_frame
        await RenderingServer.frame_post_draw
        frame_count += 1
        var now_usec := Time.get_ticks_usec()
        intervals_ms.append(float(now_usec - previous_usec) / 1000.0)
        previous_usec = now_usec
        if player.get_instance_id() != player_id or container.get_instance_id() != receiver_id:
            _anim_fail("Animation current-world receiver or AnimationPlayer identity changed")
            return {}
        var position_s := player.current_animation_position
        var matched := _anim_match_owner_sample(plan, position_s, lid, pivots)
        var sample_error := float(matched["max_error_deg"])
        max_sample_error_deg = maxf(max_sample_error_deg, sample_error)
        if sample_error > ANIM_ANGLE_EPS_DEG:
            _anim_fail("Animation current-world wall-clock pose escaped exact adapted receiver samples")
            return {}
        var matched_index := int(matched["index"])
        var lid_angle := float(matched["adapted_receiver_lid_rotation_deg"])
        var latch_angles := matched["adapted_receiver_latch_rotation_deg"] as Array
        seen_indices[matched_index] = true
        max_lid_angle_deg = maxf(max_lid_angle_deg, absf(lid_angle))
        for raw_angle in latch_angles:
            min_latch_angle_deg = minf(min_latch_angle_deg, float(raw_angle))
            if absf(lid_angle) > ANIM_ANGLE_EPS_DEG and absf(float(raw_angle) + 50.0) > ANIM_ANGLE_EPS_DEG:
                phase_order_violations += 1
        if observations.is_empty() or int((observations[observations.size()-1] as Dictionary)["matched_owner_sample_index"]) != matched_index:
            observations.append({
                "frame":frame_count,
                "elapsed_s":float(now_usec - start_usec) / 1000000.0,
                "animation_position_s":position_s,
                "matched_owner_sample_index":matched_index,
                "max_owner_sample_error_deg":sample_error,
                "adapted_receiver_lid_rotation_deg":lid_angle,
                "adapted_receiver_latch_rotation_deg":latch_angles
            })
        if not player.is_playing():
            natural_stop = true
            break

    var elapsed_s := float(Time.get_ticks_usec() - start_usec) / 1000000.0
    if not natural_stop:
        _anim_fail("Animation current-world timed playback did not stop naturally")
        return {}
    if phase_order_violations != 0:
        _anim_fail("Animation current-world wall-clock phase ordering violated")
        return {}
    if max_lid_angle_deg < 99.0 or min_latch_angle_deg > -49.9:
        _anim_fail("Animation current-world wall-clock playback did not traverse owner peak poses")
        return {}

    var endpoint_keeper_drift := maxf(start_keeper0.distance_to(_anim_mesh_center(container, "latch_0_keeper")), start_keeper1.distance_to(_anim_mesh_center(container, "latch_1_keeper")))
    var endpoint_lever_drift := 0.0
    for lever_name in start_levers.keys():
        var start_center:Vector3 = start_levers[lever_name]
        endpoint_lever_drift = maxf(endpoint_lever_drift, start_center.distance_to(_anim_mesh_center(container, String(lever_name))))
    if endpoint_keeper_drift > ANIM_POSITION_EPS_M or endpoint_lever_drift > ANIM_POSITION_EPS_M:
        _anim_fail("Animation current-world wall-clock endpoint closure drift")
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

func _anim_review_playback(world:Dictionary)->Dictionary:
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
        _anim_fail("Animation current-world neutral review raster unavailable")
        return {}
    var first_path := "res://animation-object-current-world-wallclock-frame-%03d.png" % frame_index
    if first_image.save_png(first_path) != OK:
        _anim_fail("Animation current-world neutral review raster save failed")
        return {}
    frames.append({"frame":frame_index,"animation_position_s":0.0,"matched_owner_sample_index":0,"max_owner_sample_error_deg":0.0,"path":first_path,"bytes":FileAccess.get_file_as_bytes(first_path).size()})
    frame_index += 1

    player.play("owner_samples")
    var safety := 0
    while safety < ANIM_MAX_REVIEW_FRAMES:
        await process_frame
        await RenderingServer.frame_post_draw
        safety += 1
        var position_s := player.current_animation_position
        var matched := _anim_match_owner_sample(plan, position_s, lid, pivots)
        if float(matched["max_error_deg"]) > ANIM_ANGLE_EPS_DEG:
            _anim_fail("Animation current-world captured playback escaped exact adapted receiver sample")
            return {}
        var image := viewport.get_texture().get_image()
        if image == null or image.is_empty():
            _anim_fail("Animation current-world wall-clock review raster unavailable")
            return {}
        var path := "res://animation-object-current-world-wallclock-frame-%03d.png" % frame_index
        if image.save_png(path) != OK:
            _anim_fail("Animation current-world wall-clock review raster save failed")
            return {}
        frames.append({
            "frame":frame_index,
            "animation_position_s":position_s,
            "matched_owner_sample_index":int(matched["index"]),
            "max_owner_sample_error_deg":float(matched["max_error_deg"]),
            "adapted_receiver_lid_rotation_deg":float(matched["adapted_receiver_lid_rotation_deg"]),
            "adapted_receiver_latch_rotation_deg":matched["adapted_receiver_latch_rotation_deg"],
            "path":path,
            "bytes":FileAccess.get_file_as_bytes(path).size()
        })
        frame_index += 1
        if not player.is_playing():
            break
    if player.is_playing():
        _anim_fail("Animation current-world captured review playback exceeded safety frame budget")
        return {}
    if frames.size() < 12:
        _anim_fail("Animation current-world captured review sequence too short")
        return {}

    return {
        "observation_semantics":"SECOND_REAL_ANIMATIONPLAYER_PLAYBACK_WITH_VIEWPORT_READBACK_AND_PNG_IO__TIMING_NOT_PERFORMANCE_EVIDENCE",
        "camera_context":ANIM_CAMERA_CONTEXT,
        "frame_count":frames.size(),
        "frames":frames,
        "capture_timing_accepted":false,
        "display_scanout_accepted":false
    }

func _initialize()->void:
    anim_receipt = {
        "schema":ANIM_RECEIPT_SCHEMA,
        "state":"STARTED",
        "contract_schema":ANIM_CONTRACT_SCHEMA,
        "technical_art_parent_head":ANIM_TA_PARENT_HEAD,
        "historical_technical_art_parent_head":ANIM_HISTORICAL_TA_PARENT_HEAD,
        "historical_receipts_reused_as_current_evidence":false,
        "predecessor_animation_evidence_head":ANIM_PREDECESSOR_EVIDENCE_HEAD,
        "animation_head":ANIM_OWNER_HEAD,
        "sequence_digest":ANIM_SEQUENCE_DIGEST,
        "duration_s":ANIM_DURATION_S,
        "sample_rate_hz":ANIM_RATE_HZ,
        "sample_count":ANIM_SAMPLE_COUNT,
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "receiver_construction_owned_by_technical_art":true,
        "receiver_frame_matching_rule":ANIM_FRAME_RULE,
        "acceptance_pose_match_uses_host_quaternion_projected_to_exact_receiver_axis":true,
        "receiver_plan_already_encodes_owner_to_host_angle_adaptation":true,
        "source_euler_x_not_used_for_acceptance":true,
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

    var world := await _anim_build_world()
    if world.is_empty():
        return
    var timed := await _anim_timed_playback(world)
    if timed.is_empty():
        return
    var review := await _anim_review_playback(world)
    if review.is_empty():
        return

    anim_receipt["state"] = ANIM_PASS_STATE
    anim_receipt["timed_playback"] = timed
    anim_receipt["shaded_review_playback"] = review
    anim_receipt["truth_boundary"] = "The frozen 2.5 s / 40 Hz / 101-key owner sequence is replayed on exact current Technical-Art successor fc567fd6dd061ccb5e8232bd17ee0af3d2e064b7. The prior e085437f6cc958bbf7c5c6464578923d542962b0 receiver proof remains historical and is not reused as current evidence. Acceptance pose membership is measured from actual pivot quaternions about the exact receiver axis against Technical Art's already-adapted receiver plan; source Euler X is not assumed to equal host Euler X. No source retime, receiver-construction authority, Runtime/controller, target-device/display performance, VFX, Environment adoption, gameplay, physics, Art/QA, CANON or production acceptance transfers."
    _anim_write_receipt()
    quit(0)
