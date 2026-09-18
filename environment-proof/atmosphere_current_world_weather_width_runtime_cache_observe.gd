extends "res://atmosphere_current_world_weather_width_playback_observe.gd"

const RUNTIME_SCHEMA := "axm.runtime-weather-width-cadence-cache-observation/v0.1"
const RUNTIME_STATE := "OBSERVED_REBUILD_VS_PREBUILT_MESH_SWAP"
const EXACT_VFX_PARENT_HEAD := "bbc8721a8af60b11e660773786426965c421e4ff"
const REVIEW_INDICES := [0, 8, 16]

func write_runtime_cache_receipt(data:Dictionary)->void:
    var file:=FileAccess.open("res://atmosphere-current-world-weather-width-runtime-cache.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(data,"  ")+"\n")
        file.close()

func capture_runtime_frame(viewport:SubViewport,context:String,index:int,mode:String)->Dictionary:
    var image:=viewport.get_texture().get_image()
    if image==null or image.is_empty():
        return {"state":"FAIL_CAPTURE"}
    var path="res://runtime-cache-%s-%s-%02d.png" % [mode,context,index]
    if image.save_png(path)!=OK:
        return {"state":"FAIL_CAPTURE"}
    return {
        "state":"PASS",
        "path":path,
        "width":image.get_width(),
        "height":image.get_height(),
        "bytes":FileAccess.get_file_as_bytes(path).size()
    }

func _attach_mutable_meshes()->void:
    weather_node.mesh=weather_mesh
    sapling_node.mesh=sapling_mesh

func _attach_cached_meshes(cache:Dictionary,index:int)->void:
    weather_node.mesh=(cache["weather_meshes"] as Array)[index] as Mesh
    sapling_node.mesh=(cache["sapling_meshes"] as Array)[index] as Mesh

func build_context_cache(camera:Camera3D,states:Array,context:String)->Dictionary:
    configure_camera(camera,(states[0] as Dictionary)["scene"] as Dictionary,context)
    await settle(1)
    _attach_mutable_meshes()
    var memory_before:=runtime_stats()
    var weather_meshes:Array=[]
    var sapling_meshes:Array=[]
    var source_receipts:Array=[]
    var maximum_width_residual:=0.0
    var build_start_us:=Time.get_ticks_usec()
    for row_value in states:
        var row=row_value as Dictionary
        var scene=row["scene"] as Dictionary
        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        if not sapling_receipt_is_live(sapling_update):
            return {"state":"FAIL_CACHE_SAPLING","index":row["index"],"detail":sapling_update}
        var weather_update=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
        if String(weather_update.get("state",""))!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_CACHE_WEATHER","index":row["index"],"detail":weather_update}
        var residual:=float(weather_update.get("maximum_projected_width_residual_px",999.0))
        if residual>WIDTH_RESIDUAL_TOL_PX:
            return {"state":"FAIL_CACHE_WIDTH_RESIDUAL","index":row["index"],"detail":weather_update}
        maximum_width_residual=maxf(maximum_width_residual,residual)
        var cached_weather:Mesh=weather_mesh.duplicate(true) as Mesh
        var cached_sapling:Mesh=sapling_mesh.duplicate(true) as Mesh
        if cached_weather==null or cached_sapling==null:
            return {"state":"FAIL_CACHE_DUPLICATE","index":row["index"]}
        weather_meshes.append(cached_weather)
        sapling_meshes.append(cached_sapling)
        source_receipts.append({
            "index":row["index"],
            "weather_field_digest":row["weather_field_digest"],
            "weather_width_profile_digest":row["weather_width_profile_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "cached_weather_surface_count":cached_weather.get_surface_count(),
            "cached_sapling_surface_count":cached_sapling.get_surface_count()
        })
    var build_end_us:=Time.get_ticks_usec()
    await settle(1)
    var memory_after:=runtime_stats()
    return {
        "state":"PASS_EXACT_17_STATE_CONTEXT_CACHE",
        "context":context,
        "weather_meshes":weather_meshes,
        "sapling_meshes":sapling_meshes,
        "source_receipts":source_receipts,
        "maximum_projected_width_residual_px":maximum_width_residual,
        "build_duration_ms":float(build_end_us-build_start_us)/1000.0,
        "memory_before":memory_before,
        "memory_after":memory_after,
        "observed_buffer_delta_bytes":int(memory_after["buffer_mem_bytes"])-int(memory_before["buffer_mem_bytes"]),
        "observed_texture_delta_bytes":int(memory_after["texture_mem_bytes"])-int(memory_before["texture_mem_bytes"]),
        "resource_policy":"17_PREBUILT_WEATHER_MESHES_PLUS_17_PREBUILT_SAPLING_MESHES_PER_FIXED_CAMERA_CONTEXT"
    }

func run_mode(camera:Camera3D,states:Array,context:String,mode:String,cache:Dictionary)->Dictionary:
    configure_camera(camera,(states[0] as Dictionary)["scene"] as Dictionary,context)
    await settle(1)
    if mode=="rebuild":
        _attach_mutable_meshes()
        var warm_scene=(states[0] as Dictionary)["scene"] as Dictionary
        var warm_sapling=fill_sapling(warm_scene["sapling"] as Dictionary)
        var warm_weather=fill_weather_width_ribbons(warm_scene["weather_lines"] as Array,camera)
        if not sapling_receipt_is_live(warm_sapling) or String(warm_weather.get("state",""))!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_REBUILD_WARMUP"}
    elif mode=="cached_swap":
        _attach_cached_meshes(cache,0)
    else:
        return {"state":"FAIL_UNKNOWN_MODE","mode":mode}
    await settle(1)

    var clock_start_us:=Time.get_ticks_usec()
    var samples:Array=[]
    for row_value in states:
        var row=row_value as Dictionary
        var index:=int(row["index"])
        var scene=row["scene"] as Dictionary
        var scheduled_time_s:=float(row["time_s"])
        var target_tick_us:=clock_start_us+int(round(scheduled_time_s*1000000.0))
        await wait_until_tick(target_tick_us)
        var submit_tick_us:=Time.get_ticks_usec()
        var update_start_us:=submit_tick_us
        var sapling_update:Dictionary={}
        var weather_update:Dictionary={}
        if mode=="rebuild":
            _attach_mutable_meshes()
            sapling_update=fill_sapling(scene["sapling"] as Dictionary)
            if not sapling_receipt_is_live(sapling_update):
                return {"state":"FAIL_REBUILD_SAPLING","index":index,"detail":sapling_update}
            weather_update=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
            if String(weather_update.get("state",""))!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
                return {"state":"FAIL_REBUILD_WEATHER","index":index,"detail":weather_update}
            if float(weather_update.get("maximum_projected_width_residual_px",999.0))>WIDTH_RESIDUAL_TOL_PX:
                return {"state":"FAIL_REBUILD_WIDTH_RESIDUAL","index":index,"detail":weather_update}
        else:
            _attach_cached_meshes(cache,index)
            var source_receipt=(cache["source_receipts"] as Array)[index] as Dictionary
            sapling_update=source_receipt["sapling_update"] as Dictionary
            weather_update=source_receipt["weather_update"] as Dictionary
        var update_end_us:=Time.get_ticks_usec()
        await RenderingServer.frame_post_draw
        var draw_tick_us:=Time.get_ticks_usec()
        var submit_time_s:=float(submit_tick_us-clock_start_us)/1000000.0
        var update_end_time_s:=float(update_end_us-clock_start_us)/1000000.0
        var draw_time_s:=float(draw_tick_us-clock_start_us)/1000000.0
        samples.append({
            "index":index,
            "scheduled_time_s":scheduled_time_s,
            "submit_time_s":submit_time_s,
            "update_end_time_s":update_end_time_s,
            "draw_time_s":draw_time_s,
            "submit_lateness_ms":(submit_time_s-scheduled_time_s)*1000.0,
            "update_end_lateness_ms":(update_end_time_s-scheduled_time_s)*1000.0,
            "draw_lateness_ms":(draw_time_s-scheduled_time_s)*1000.0,
            "update_duration_ms":float(update_end_us-update_start_us)/1000.0,
            "post_draw_wait_ms":float(draw_tick_us-update_end_us)/1000.0,
            "weather_field_digest":row["weather_field_digest"],
            "weather_width_profile_digest":row["weather_width_profile_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "runtime_after_draw":runtime_stats()
        })
    return {
        "state":"OBSERVED_EXACT_17_STATE_RUNTIME_MODE",
        "context":context,
        "mode":mode,
        "clock_start_us":clock_start_us,
        "interval_s":PLAYBACK_INTERVAL_S,
        "interval_us":PLAYBACK_INTERVAL_US,
        "samples":samples
    }

func retain_visual_pairs(viewport:SubViewport,camera:Camera3D,states:Array,context:String,cache:Dictionary)->Dictionary:
    var pairs:Array=[]
    configure_camera(camera,(states[0] as Dictionary)["scene"] as Dictionary,context)
    await settle(1)
    for raw_index in REVIEW_INDICES:
        var index:=int(raw_index)
        var row=states[index] as Dictionary
        var scene=row["scene"] as Dictionary
        _attach_mutable_meshes()
        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        var weather_update=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
        if not sapling_receipt_is_live(sapling_update) or String(weather_update.get("state",""))!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_REVIEW_REBUILD","index":index}
        await settle(2)
        var rebuild_capture=capture_runtime_frame(viewport,context,index,"rebuild")
        if String(rebuild_capture.get("state",""))!="PASS":
            return {"state":"FAIL_REVIEW_REBUILD_CAPTURE","index":index}
        _attach_cached_meshes(cache,index)
        await settle(2)
        var cached_capture=capture_runtime_frame(viewport,context,index,"cached")
        if String(cached_capture.get("state",""))!="PASS":
            return {"state":"FAIL_REVIEW_CACHED_CAPTURE","index":index}
        pairs.append({"index":index,"rebuild":rebuild_capture,"cached":cached_capture})
    return {"state":"PASS_RETAINED_RUNTIME_VISUAL_PAIRS","context":context,"pairs":pairs}

func _initialize()->void:
    var runtime_receipt={
        "schema":RUNTIME_SCHEMA,
        "state":"STARTED",
        "exact_vfx_parent_head":EXACT_VFX_PARENT_HEAD,
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "promotion_effect":"NONE",
        "interval_s":PLAYBACK_INTERVAL_S,
        "interval_us":PLAYBACK_INTERVAL_US,
        "optimization_candidate":"PREBUILD_EXACT_FINITE_STATE_MESHES_BEFORE_CLOCK_START_THEN_SWAP_MESH_RESOURCES",
        "truth_boundary":"Runtime A/B on the exact VFX source-width Weather + sapling 17-state sequence. Rebuild mode uses the inherited source-correct mutable mesh builders every state. Cached mode prebuilds the exact same finite-state meshes before timing and swaps those resources on schedule. This is a Runtime representation candidate only: it deliberately trades stable mutable mesh-resource identity and additional memory for lower timed update work. It does not prove VFX adoption, arbitrary state streams, target-device performance, gameplay, physical Weather, final Art Direction, CANON, or production readiness."
    }
    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!=WIDTH_SCHEMA or String(payload.get("status",""))!=WIDTH_STATUS:
        runtime_receipt["state"]="FAIL_INVALID_WIDTH_PAYLOAD"
        write_runtime_cache_receipt(runtime_receipt)
        quit(1)
        return
    if String(payload.get("receiving_head",""))!=EXACT_VFX_PARENT_HEAD:
        runtime_receipt["state"]="FAIL_VFX_PARENT_IDENTITY"
        runtime_receipt["observed_receiving_head"]=payload.get("receiving_head","")
        write_runtime_cache_receipt(runtime_receipt)
        quit(1)
        return
    var states=payload["states"] as Array
    if states.size()!=17:
        runtime_receipt["state"]="FAIL_REQUIRES_EXACT_17_STATES"
        write_runtime_cache_receipt(runtime_receipt)
        quit(1)
        return
    for index in range(states.size()):
        var row=states[index] as Dictionary
        if int(row.get("index",-1))!=index or absf(float(row.get("time_s",-1.0))-float(index)*PLAYBACK_INTERVAL_S)>0.000000001:
            runtime_receipt["state"]="FAIL_SOURCE_SCHEDULE_DRIFT"
            runtime_receipt["failed_index"]=index
            write_runtime_cache_receipt(runtime_receipt)
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
        runtime_receipt["state"]="FAIL_REAR_TREE_CULLING_TARGET_DRIFT"
        write_runtime_cache_receipt(runtime_receipt)
        quit(1)
        return
    runtime_receipt["static_source_meshes"]=add_static_sources(root3d,data,cull_target_asset_id)
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
        var cache=await build_context_cache(camera,states,context)
        if String(cache.get("state",""))!="PASS_EXACT_17_STATE_CONTEXT_CACHE":
            runtime_receipt["state"]="FAIL_CACHE_BUILD"
            runtime_receipt["failed_context"]=context
            runtime_receipt["detail"]=cache
            write_runtime_cache_receipt(runtime_receipt)
            quit(1)
            return
        var rebuild=await run_mode(camera,states,context,"rebuild",cache)
        var cached=await run_mode(camera,states,context,"cached_swap",cache)
        var visuals=await retain_visual_pairs(viewport,camera,states,context,cache)
        if String(rebuild.get("state",""))!="OBSERVED_EXACT_17_STATE_RUNTIME_MODE" or String(cached.get("state",""))!="OBSERVED_EXACT_17_STATE_RUNTIME_MODE" or String(visuals.get("state",""))!="PASS_RETAINED_RUNTIME_VISUAL_PAIRS":
            runtime_receipt["state"]="FAIL_RUNTIME_CONTEXT"
            runtime_receipt["failed_context"]=context
            runtime_receipt["rebuild"]=rebuild
            runtime_receipt["cached"]=cached
            runtime_receipt["visuals"]=visuals
            write_runtime_cache_receipt(runtime_receipt)
            quit(1)
            return
        var cache_summary=cache.duplicate(false)
        cache_summary.erase("weather_meshes")
        cache_summary.erase("sapling_meshes")
        contexts[context]={
            "cache":cache_summary,
            "rebuild":rebuild,
            "cached_swap":cached,
            "visuals":visuals
        }

    runtime_receipt["state"]=RUNTIME_STATE
    runtime_receipt["receiving_head"]=payload["receiving_head"]
    runtime_receipt["weather_variant_head"]=payload["weather_variant_head"]
    runtime_receipt["weather_variant_seed"]=payload["weather_variant_seed"]
    runtime_receipt["source_width_profile_digest"]=payload["source_width_profile_digest"]
    runtime_receipt["contexts"]=contexts
    runtime_receipt["godot_version"]=Engine.get_version_info()
    write_runtime_cache_receipt(runtime_receipt)
    quit(0)
