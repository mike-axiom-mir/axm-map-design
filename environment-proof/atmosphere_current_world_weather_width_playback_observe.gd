extends "res://atmosphere_current_world_weather_width_observe.gd"

const PLAYBACK_SCHEMA := "axm.environment-current-world-weather-width-wall-clock-observation/v0.1"
const PLAYBACK_STATE := "OBSERVED_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_WALL_CLOCK_SEQUENCE"
const PLAYBACK_CONTEXTS := ["path_eye", "elevated_oblique"]
const PLAYBACK_INTERVAL_S := 0.03125
const PLAYBACK_INTERVAL_US := 31250

func write_playback_receipt(data:Dictionary)->void:
    var file:=FileAccess.open("res://atmosphere-current-world-weather-width-playback-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(data,"  ")+"\n")
        file.close()

func wait_until_tick(target_us:int)->void:
    var now_us:=Time.get_ticks_usec()
    if now_us<target_us:
        await get_tree().create_timer(float(target_us-now_us)/1000000.0).timeout

func run_context_playback(camera:Camera3D,states:Array,context:String)->Dictionary:
    var first=states[0] as Dictionary
    var first_scene=first["scene"] as Dictionary
    configure_camera(camera,first_scene,context)
    var warm_sapling=fill_sapling(first_scene["sapling"] as Dictionary)
    var warm_weather=fill_weather_width_ribbons(first_scene["weather_lines"] as Array,camera)
    if warm_sapling.get("state")!="PASS" and not String(warm_sapling.get("state","")).begins_with("PASS_"):
        return {"state":"FAIL_WARMUP_SAPLING","detail":warm_sapling}
    if warm_weather.get("state")!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
        return {"state":"FAIL_WARMUP_WEATHER","detail":warm_weather}
    await settle()

    var clock_start_us:=Time.get_ticks_usec()
    var samples=[]
    for row_value in states:
        var row=row_value as Dictionary
        var scene=row["scene"] as Dictionary
        var scheduled_time_s:=float(row["time_s"])
        var target_tick_us:=clock_start_us+int(round(scheduled_time_s*1000000.0))
        await wait_until_tick(target_tick_us)
        var submit_tick_us:=Time.get_ticks_usec()

        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        if sapling_update.get("state")!="PASS" and not String(sapling_update.get("state","")).begins_with("PASS_"):
            return {"state":"FAIL_SAPLING_UPDATE","index":row["index"],"detail":sapling_update}
        var weather_update=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
        if weather_update.get("state")!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_WEATHER_UPDATE","index":row["index"],"detail":weather_update}
        if float(weather_update.get("maximum_projected_width_residual_px",999.0))>WIDTH_RESIDUAL_TOL_PX:
            return {"state":"FAIL_WIDTH_RESIDUAL","index":row["index"],"detail":weather_update}

        await RenderingServer.frame_post_draw
        var draw_tick_us:=Time.get_ticks_usec()
        var submit_time_s:=float(submit_tick_us-clock_start_us)/1000000.0
        var draw_time_s:=float(draw_tick_us-clock_start_us)/1000000.0
        var submit_lateness_ms:=(submit_time_s-scheduled_time_s)*1000.0
        var draw_lateness_ms:=(draw_time_s-scheduled_time_s)*1000.0

        samples.append({
            "index":row["index"],
            "scheduled_time_s":scheduled_time_s,
            "submit_time_s":submit_time_s,
            "draw_time_s":draw_time_s,
            "submit_lateness_ms":submit_lateness_ms,
            "draw_lateness_ms":draw_lateness_ms,
            "weather_field_digest":row["weather_field_digest"],
            "weather_width_profile_digest":row["weather_width_profile_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update
        })

    return {
        "state":"OBSERVED_EXACT_17_STATE_WALL_CLOCK_SEQUENCE",
        "context":context,
        "clock_start_us":clock_start_us,
        "interval_s":PLAYBACK_INTERVAL_S,
        "interval_us":PLAYBACK_INTERVAL_US,
        "samples":samples
    }

func _initialize()->void:
    var playback_receipt={
        "schema":PLAYBACK_SCHEMA,
        "state":"STARTED",
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "promotion_effect":"NONE",
        "presentation_mode":WIDTH_PRESENTATION_MODE,
        "schedule":"EXACT_SOURCE_EVALUATION_TIMES_0_TO_0P5_SECONDS_17_STATES",
        "truth_boundary":"Wall-clock presentation observation for the exact already-proven source-width Weather + sapling states in the two fixed 1100x720 cameras. The observer schedules the 17 direct source states at their exact 0.03125 s source-evaluation times and waits for a Godot post-draw signal after each update. It does not invent interpolation, claim physical wind, controller/gameplay authority, arbitrary camera or resolution behavior, target-device performance, frame-time budget certification, final Art Direction, CANON, or mastery."
    }
    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!=WIDTH_SCHEMA:
        playback_receipt["state"]="FAIL_INVALID_WIDTH_PAYLOAD"
        write_playback_receipt(playback_receipt)
        quit(1)
        return
    if String(payload.get("status",""))!=WIDTH_STATUS:
        playback_receipt["state"]="FAIL_WIDTH_STRUCTURE_NOT_PASS"
        write_playback_receipt(playback_receipt)
        quit(1)
        return
    if String(payload.get("parent_variant_head",""))!=WIDTH_PARENT_HEAD:
        playback_receipt["state"]="FAIL_PARENT_HEAD_DRIFT"
        write_playback_receipt(playback_receipt)
        quit(1)
        return
    var states=payload["states"] as Array
    if states.size()!=17:
        playback_receipt["state"]="FAIL_REQUIRES_EXACT_17_STATES"
        write_playback_receipt(playback_receipt)
        quit(1)
        return
    for index in range(states.size()):
        var row=states[index] as Dictionary
        var expected_time:=float(index)*PLAYBACK_INTERVAL_S
        if int(row.get("index",-1))!=index or absf(float(row.get("time_s",-1.0))-expected_time)>0.000000001:
            playback_receipt["state"]="FAIL_SOURCE_SCHEDULE_DRIFT"
            playback_receipt["failed_index"]=index
            write_playback_receipt(playback_receipt)
            quit(1)
            return

    var first=states[0] as Dictionary
    var data=first["scene"] as Dictionary
    var viewport:=SubViewport.new()
    viewport.size=Vector2i(1100,720)
    viewport.own_world_3d=true
    viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
    viewport.render_target_clear_mode=SubViewport.CLEAR_MODE_ALWAYS
    get_root().add_child(viewport)
    var root3d:=Node3D.new()
    viewport.add_child(root3d)
    add_environment(root3d)
    for item in data["items"] as Array:
        add_proxy(root3d,item as Dictionary)
    add_path(root3d,data)
    var culling_review=data.get("environment_rear_tree_culling_review",{}) as Dictionary
    var cull_target_asset_id=String(culling_review.get("target_asset_id",""))
    if cull_target_asset_id!=VARIANT_TARGET_REAR_ASSET_ID:
        playback_receipt["state"]="FAIL_REAR_TREE_CULLING_TARGET_DRIFT"
        write_playback_receipt(playback_receipt)
        quit(1)
        return
    var static_source_stats:=add_static_sources(root3d,data,cull_target_asset_id)
    make_weather()
    weather_material.cull_mode=BaseMaterial3D.CULL_DISABLED
    root3d.add_child(weather_node)
    make_sapling()
    root3d.add_child(sapling_node)

    var camera:=Camera3D.new()
    camera.near=0.05
    camera.far=120.0
    root3d.add_child(camera)
    camera.make_current()

    var contexts={}
    for context_value in PLAYBACK_CONTEXTS:
        var context=String(context_value)
        var result=await run_context_playback(camera,states,context)
        contexts[context]=result
        if String(result.get("state",""))!="OBSERVED_EXACT_17_STATE_WALL_CLOCK_SEQUENCE":
            playback_receipt["state"]="FAIL_CONTEXT_PLAYBACK"
            playback_receipt["contexts"]=contexts
            write_playback_receipt(playback_receipt)
            quit(1)
            return

    playback_receipt["state"]=PLAYBACK_STATE
    playback_receipt["receiving_head"]=payload["receiving_head"]
    playback_receipt["parent_variant_head"]=payload["parent_variant_head"]
    playback_receipt["weather_variant_head"]=payload["weather_variant_head"]
    playback_receipt["weather_variant_seed"]=payload["weather_variant_seed"]
    playback_receipt["weather_variant_layout_digest"]=payload["weather_variant_layout_digest"]
    playback_receipt["source_width_profile_digest"]=payload["source_width_profile_digest"]
    playback_receipt["static_source_meshes"]=static_source_stats
    playback_receipt["contexts"]=contexts
    playback_receipt["godot_version"]=Engine.get_version_info()
    write_playback_receipt(playback_receipt)
    quit(0)
