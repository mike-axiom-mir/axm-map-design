extends "res://atmosphere_current_world_weather_width_observe.gd"

const COALESCED_SCHEMA := "axm.environment-current-world-weather-width-latest-due-observation/v0.1"
const COALESCED_STATE := "OBSERVED_LATEST_DUE_SOURCE_STATE_PRESENTATION"
const COALESCED_CONTEXTS := ["path_eye", "elevated_oblique"]
const SOURCE_INTERVAL_S := 0.03125
const SOURCE_INTERVAL_US := 31250
const PRESENTATION_POLICY := "LATEST_DUE_EXACT_SOURCE_STATE_NO_INTERPOLATION"
const SELECTION_SEMANTICS := "SELECT_FRESHEST_DUE_SOURCE_STATE_WHEN_RENDERER_RETURNS_CONTROL"

func write_coalesced_receipt(data:Dictionary)->void:
    var file:=FileAccess.open("res://atmosphere-current-world-weather-width-coalesced-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(data,"  ")+"\n")
        file.close()

func sapling_receipt_is_live(receipt:Dictionary)->bool:
    return int(receipt.get("surface_count",0))>0 and int(receipt.get("source_vertex_count",0))>0 and int(receipt.get("source_triangle_count",0))>0

func latest_due_index(elapsed_us:int,state_count:int)->int:
    if state_count<=0:
        return -1
    return clampi(int(floor(float(maxi(elapsed_us,0))/float(SOURCE_INTERVAL_US))),0,state_count-1)

func exact_skipped_indices(previous_index:int,current_index:int)->Array:
    var skipped=[]
    for index in range(previous_index+1,current_index):
        skipped.append(index)
    return skipped

func capture_frame(camera:Camera3D,context:String,index:int)->Dictionary:
    var image:=camera.get_viewport().get_texture().get_image()
    var relative_path="coalesced-frames/%s-state-%02d.png" % [context,index]
    var resource_path="res://"+relative_path
    var error:=image.save_png(resource_path)
    if error!=OK:
        return {"state":"FAIL_SAVE_FRAME","error":error,"path":relative_path}
    return {
        "state":"PASS_CAPTURED_FRAME",
        "path":relative_path,
        "sha256":FileAccess.get_sha256(resource_path),
        "width":image.get_width(),
        "height":image.get_height()
    }

func run_context_coalesced(camera:Camera3D,states:Array,context:String)->Dictionary:
    var first=states[0] as Dictionary
    var first_scene=first["scene"] as Dictionary
    configure_camera(camera,first_scene,context)
    await settle(1)

    var warm_sapling=fill_sapling(first_scene["sapling"] as Dictionary)
    if not sapling_receipt_is_live(warm_sapling):
        return {"state":"FAIL_WARMUP_SAPLING","detail":warm_sapling}
    var warm_weather=fill_weather_width_ribbons(first_scene["weather_lines"] as Array,camera)
    if warm_weather.get("state")!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
        return {"state":"FAIL_WARMUP_WEATHER","detail":warm_weather}
    await RenderingServer.frame_post_draw

    var clock_start_us:=Time.get_ticks_usec()
    var samples=[]
    var dropped=[]
    var previous_index=-1

    while previous_index<states.size()-1:
        var elapsed_us:=Time.get_ticks_usec()-clock_start_us
        var selected_index:=latest_due_index(elapsed_us,states.size())
        if selected_index<=previous_index:
            var next_index:=previous_index+1
            var next_tick_us:=clock_start_us+next_index*SOURCE_INTERVAL_US
            var remaining_us:=next_tick_us-Time.get_ticks_usec()
            if remaining_us>0:
                await create_timer(float(remaining_us)/1000000.0).timeout
            continue

        var row=states[selected_index] as Dictionary
        var scene=row["scene"] as Dictionary
        var selection_tick_us:=Time.get_ticks_usec()
        var selection_elapsed_us:=selection_tick_us-clock_start_us
        var due_at_selection:=latest_due_index(selection_elapsed_us,states.size())
        if due_at_selection!=selected_index:
            # Scheduler movement can only advance the newest due state. Re-enter
            # the loop instead of presenting a knowingly stale source state.
            continue

        var skipped_now:=exact_skipped_indices(previous_index,selected_index)
        for skipped_index in skipped_now:
            dropped.append(skipped_index)

        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        if not sapling_receipt_is_live(sapling_update):
            return {"state":"FAIL_SAPLING_UPDATE","index":selected_index,"detail":sapling_update}
        var weather_update=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
        if weather_update.get("state")!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_WEATHER_UPDATE","index":selected_index,"detail":weather_update}
        if float(weather_update.get("maximum_projected_width_residual_px",999.0))>WIDTH_RESIDUAL_TOL_PX:
            return {"state":"FAIL_WIDTH_RESIDUAL","index":selected_index,"detail":weather_update}

        var submit_tick_us:=Time.get_ticks_usec()
        await RenderingServer.frame_post_draw
        var draw_tick_us:=Time.get_ticks_usec()
        var frame=capture_frame(camera,context,selected_index)
        if frame.get("state")!="PASS_CAPTURED_FRAME":
            return {"state":"FAIL_FRAME_CAPTURE","index":selected_index,"detail":frame}

        var scheduled_time_s:=float(row["time_s"])
        var selection_time_s:=float(selection_tick_us-clock_start_us)/1000000.0
        var submit_time_s:=float(submit_tick_us-clock_start_us)/1000000.0
        var draw_time_s:=float(draw_tick_us-clock_start_us)/1000000.0
        samples.append({
            "index":selected_index,
            "scheduled_time_s":scheduled_time_s,
            "latest_due_index_at_selection":due_at_selection,
            "selection_time_s":selection_time_s,
            "submit_time_s":submit_time_s,
            "draw_time_s":draw_time_s,
            "source_age_at_selection_ms":(selection_time_s-scheduled_time_s)*1000.0,
            "source_age_at_submit_ms":(submit_time_s-scheduled_time_s)*1000.0,
            "source_age_at_draw_ms":(draw_time_s-scheduled_time_s)*1000.0,
            "skipped_before":skipped_now,
            "weather_field_digest":row["weather_field_digest"],
            "weather_width_profile_digest":row["weather_width_profile_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "frame":frame
        })
        previous_index=selected_index

    return {
        "state":"OBSERVED_LATEST_DUE_SOURCE_STATE_SEQUENCE",
        "context":context,
        "clock_start_us":clock_start_us,
        "source_interval_s":SOURCE_INTERVAL_S,
        "source_interval_us":SOURCE_INTERVAL_US,
        "presentation_policy":PRESENTATION_POLICY,
        "selection_semantics":SELECTION_SEMANTICS,
        "samples":samples,
        "dropped_indices":dropped
    }

func _initialize()->void:
    var receipt={
        "schema":COALESCED_SCHEMA,
        "state":"STARTED",
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "promotion_effect":"NONE",
        "presentation_mode":WIDTH_PRESENTATION_MODE,
        "presentation_policy":PRESENTATION_POLICY,
        "selection_semantics":SELECTION_SEMANTICS,
        "truth_boundary":"Optional VFX presentation fallback evidence only. When the proof renderer cannot present every authored 31.25 ms state on time, this observer never invents interpolation and never rewrites Weather source semantics. It selects the freshest exact source state already due whenever the renderer returns control, may skip stale intermediate visual states, retains each actually presented frame, and still uses the established source-width receiving path. This does not establish authored 32 Hz presentation, target-device performance, physical weather, gameplay or physics authority, final Art Direction, CANON, production readiness, or mastery."
    }
    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!=WIDTH_SCHEMA:
        receipt["state"]="FAIL_INVALID_WIDTH_PAYLOAD"
        write_coalesced_receipt(receipt)
        quit(1)
        return
    if String(payload.get("status",""))!=WIDTH_STATUS:
        receipt["state"]="FAIL_WIDTH_STRUCTURE_NOT_PASS"
        write_coalesced_receipt(receipt)
        quit(1)
        return
    if String(payload.get("parent_variant_head",""))!=WIDTH_PARENT_HEAD:
        receipt["state"]="FAIL_PARENT_HEAD_DRIFT"
        write_coalesced_receipt(receipt)
        quit(1)
        return

    var states=payload["states"] as Array
    if states.size()!=17:
        receipt["state"]="FAIL_REQUIRES_EXACT_17_STATES"
        write_coalesced_receipt(receipt)
        quit(1)
        return
    for index in range(states.size()):
        var row=states[index] as Dictionary
        var expected_time:=float(index)*SOURCE_INTERVAL_S
        if int(row.get("index",-1))!=index or absf(float(row.get("time_s",-1.0))-expected_time)>0.000000001:
            receipt["state"]="FAIL_SOURCE_SCHEDULE_DRIFT"
            receipt["failed_index"]=index
            write_coalesced_receipt(receipt)
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
        receipt["state"]="FAIL_REAR_TREE_CULLING_TARGET_DRIFT"
        write_coalesced_receipt(receipt)
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
    for context_value in COALESCED_CONTEXTS:
        var context=String(context_value)
        var result=await run_context_coalesced(camera,states,context)
        contexts[context]=result
        if String(result.get("state",""))!="OBSERVED_LATEST_DUE_SOURCE_STATE_SEQUENCE":
            receipt["state"]="FAIL_CONTEXT_PRESENTATION"
            receipt["contexts"]=contexts
            write_coalesced_receipt(receipt)
            quit(1)
            return

    receipt["state"]=COALESCED_STATE
    receipt["receiving_head"]=payload["receiving_head"]
    receipt["parent_variant_head"]=payload["parent_variant_head"]
    receipt["weather_variant_head"]=payload["weather_variant_head"]
    receipt["weather_variant_seed"]=payload["weather_variant_seed"]
    receipt["weather_variant_layout_digest"]=payload["weather_variant_layout_digest"]
    receipt["source_width_profile_digest"]=payload["source_width_profile_digest"]
    receipt["static_source_meshes"]=static_source_stats
    receipt["contexts"]=contexts
    receipt["godot_version"]=Engine.get_version_info()
    write_coalesced_receipt(receipt)
    quit(0)
