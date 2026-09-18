extends "res://atmosphere_current_world_weather_width_coalesced_observe.gd"

const RUNTIME_CACHE_SCHEMA := "axm.runtime-weather-width-latest-due-cache-observation/v0.1"
const RUNTIME_CACHE_STATE := "OBSERVED_LATEST_DUE_REBUILD_VS_PREBUILT_CACHE"
const EXACT_VFX_LATEST_DUE_HEAD := "e95910c8c5c45cd8d51be3b259825cf85064efc2"
const RUNTIME_REVIEW_INDICES := [0, 8, 16]

func write_runtime_cache_receipt(data:Dictionary)->void:
    var file:=FileAccess.open("res://atmosphere-current-world-weather-width-latest-due-cache-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(data,"  ")+"\n")
        file.close()

func capture_runtime_frame(viewport:SubViewport,context:String,index:int,mode:String)->Dictionary:
    var image:=viewport.get_texture().get_image()
    if image==null or image.is_empty():
        return {"state":"FAIL_CAPTURE"}
    var relative_path="latest-due-cache-frames/%s-%s-state-%02d.png" % [mode,context,index]
    var resource_path="res://"+relative_path
    var error:=image.save_png(resource_path)
    if error!=OK:
        return {"state":"FAIL_CAPTURE","error":error,"path":relative_path}
    return {
        "state":"PASS_CAPTURED_FRAME",
        "path":relative_path,
        "sha256":FileAccess.get_sha256(resource_path),
        "width":image.get_width(),
        "height":image.get_height()
    }

func attach_fresh_mutable_meshes()->void:
    weather_mesh=ImmediateMesh.new()
    weather_node.mesh=weather_mesh
    sapling_mesh=ArrayMesh.new()
    sapling_node.mesh=sapling_mesh

func attach_cached_meshes(cache:Dictionary,index:int)->void:
    weather_mesh=(cache["weather_meshes"] as Array)[index] as ImmediateMesh
    sapling_mesh=(cache["sapling_meshes"] as Array)[index] as ArrayMesh
    weather_node.mesh=weather_mesh
    sapling_node.mesh=sapling_mesh

func build_context_cache(camera:Camera3D,states:Array,context:String)->Dictionary:
    configure_camera(camera,(states[0] as Dictionary)["scene"] as Dictionary,context)
    await settle(1)
    var memory_before:=runtime_stats()
    var weather_meshes:Array=[]
    var sapling_meshes:Array=[]
    var source_receipts:Array=[]
    var maximum_width_residual:=0.0
    var build_start_us:=Time.get_ticks_usec()
    for row_value in states:
        var row=row_value as Dictionary
        var scene=row["scene"] as Dictionary
        # Rebuild each cached state into the producer's native resource types.
        # Do not duplicate ImmediateMesh: earlier Runtime evidence proved that
        # deep duplication can retain zero Weather surfaces on this host.
        attach_fresh_mutable_meshes()
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
        weather_meshes.append(weather_mesh)
        sapling_meshes.append(sapling_mesh)
        source_receipts.append({
            "index":row["index"],
            "weather_field_digest":row["weather_field_digest"],
            "weather_width_profile_digest":row["weather_width_profile_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "weather_surface_count":weather_mesh.get_surface_count(),
            "sapling_surface_count":sapling_mesh.get_surface_count()
        })
    var build_end_us:=Time.get_ticks_usec()
    await settle(1)
    var memory_after:=runtime_stats()
    return {
        "state":"PASS_EXACT_17_STATE_NATIVE_TYPE_CACHE",
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
        "resource_policy":"17_NATIVE_IMMEDIATEMESH_WEATHER_PLUS_17_NATIVE_ARRAYMESH_SAPLING_PER_FIXED_CAMERA_CONTEXT"
    }

func warm_mode(camera:Camera3D,states:Array,context:String,mode:String,cache:Dictionary)->Dictionary:
    configure_camera(camera,(states[0] as Dictionary)["scene"] as Dictionary,context)
    await settle(1)
    if mode=="rebuild":
        attach_fresh_mutable_meshes()
        var scene=(states[0] as Dictionary)["scene"] as Dictionary
        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        var weather_update=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
        if not sapling_receipt_is_live(sapling_update):
            return {"state":"FAIL_WARM_SAPLING","detail":sapling_update}
        if String(weather_update.get("state",""))!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_WARM_WEATHER","detail":weather_update}
    elif mode=="cached_swap":
        attach_cached_meshes(cache,0)
    else:
        return {"state":"FAIL_UNKNOWN_MODE","mode":mode}
    await RenderingServer.frame_post_draw
    return {"state":"PASS_MODE_WARM"}

func run_latest_due_mode(viewport:SubViewport,camera:Camera3D,states:Array,context:String,mode:String,cache:Dictionary)->Dictionary:
    var warm=await warm_mode(camera,states,context,mode,cache)
    if String(warm.get("state",""))!="PASS_MODE_WARM":
        return warm

    var clock_start_us:int=Time.get_ticks_usec()
    var samples:Array=[]
    var dropped:Array=[]
    var previous_index:int=-1

    while previous_index<states.size()-1:
        var elapsed_us:int=Time.get_ticks_usec()-clock_start_us
        var selected_index:int=latest_due_index(elapsed_us,states.size())
        if selected_index<=previous_index:
            var next_index:int=previous_index+1
            var next_tick_us:int=clock_start_us+next_index*SOURCE_INTERVAL_US
            var remaining_us:int=next_tick_us-Time.get_ticks_usec()
            if remaining_us>0:
                await create_timer(float(remaining_us)/1000000.0).timeout
            continue

        var row=states[selected_index] as Dictionary
        var scene=row["scene"] as Dictionary
        var selection_tick_us:int=Time.get_ticks_usec()
        var selection_elapsed_us:int=selection_tick_us-clock_start_us
        var due_at_selection:int=latest_due_index(selection_elapsed_us,states.size())
        if due_at_selection!=selected_index:
            continue

        var skipped_now:=exact_skipped_indices(previous_index,selected_index)
        for skipped_index in skipped_now:
            dropped.append(skipped_index)

        var update_start_us:int=Time.get_ticks_usec()
        var sapling_update:Dictionary={}
        var weather_update:Dictionary={}
        if mode=="rebuild":
            sapling_update=fill_sapling(scene["sapling"] as Dictionary)
            if not sapling_receipt_is_live(sapling_update):
                return {"state":"FAIL_REBUILD_SAPLING","index":selected_index,"detail":sapling_update}
            weather_update=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
            if String(weather_update.get("state",""))!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
                return {"state":"FAIL_REBUILD_WEATHER","index":selected_index,"detail":weather_update}
        else:
            attach_cached_meshes(cache,selected_index)
            var source_receipt=(cache["source_receipts"] as Array)[selected_index] as Dictionary
            sapling_update=source_receipt["sapling_update"] as Dictionary
            weather_update=source_receipt["weather_update"] as Dictionary
        if float(weather_update.get("maximum_projected_width_residual_px",999.0))>WIDTH_RESIDUAL_TOL_PX:
            return {"state":"FAIL_WIDTH_RESIDUAL","index":selected_index,"detail":weather_update}
        var update_end_us:int=Time.get_ticks_usec()
        var submit_tick_us:int=update_end_us
        await RenderingServer.frame_post_draw
        var draw_tick_us:int=Time.get_ticks_usec()
        var frame=capture_runtime_frame(viewport,context,selected_index,mode)
        if String(frame.get("state",""))!="PASS_CAPTURED_FRAME":
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
            "update_duration_ms":float(update_end_us-update_start_us)/1000.0,
            "post_draw_wait_ms":float(draw_tick_us-update_end_us)/1000.0,
            "skipped_before":skipped_now,
            "weather_field_digest":row["weather_field_digest"],
            "weather_width_profile_digest":row["weather_width_profile_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "frame":frame,
            "runtime_after_draw":runtime_stats()
        })
        previous_index=selected_index

    return {
        "state":"OBSERVED_LATEST_DUE_RUNTIME_MODE",
        "context":context,
        "mode":mode,
        "clock_start_us":clock_start_us,
        "source_interval_s":SOURCE_INTERVAL_S,
        "source_interval_us":SOURCE_INTERVAL_US,
        "presentation_policy":PRESENTATION_POLICY,
        "selection_semantics":SELECTION_SEMANTICS,
        "samples":samples,
        "dropped_indices":dropped
    }

func retain_visual_pairs(viewport:SubViewport,camera:Camera3D,states:Array,context:String,cache:Dictionary)->Dictionary:
    configure_camera(camera,(states[0] as Dictionary)["scene"] as Dictionary,context)
    await settle(1)
    var pairs:Array=[]
    for raw_index in RUNTIME_REVIEW_INDICES:
        var index:=int(raw_index)
        var row=states[index] as Dictionary
        var scene=row["scene"] as Dictionary
        attach_fresh_mutable_meshes()
        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        var weather_update=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
        if not sapling_receipt_is_live(sapling_update) or String(weather_update.get("state",""))!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_REVIEW_REBUILD","index":index}
        await settle(2)
        var rebuild_capture=capture_runtime_frame(viewport,context,index,"review-rebuild")
        attach_cached_meshes(cache,index)
        await settle(2)
        var cached_capture=capture_runtime_frame(viewport,context,index,"review-cached")
        if String(rebuild_capture.get("state",""))!="PASS_CAPTURED_FRAME" or String(cached_capture.get("state",""))!="PASS_CAPTURED_FRAME":
            return {"state":"FAIL_REVIEW_CAPTURE","index":index}
        pairs.append({"index":index,"rebuild":rebuild_capture,"cached":cached_capture})
    return {"state":"PASS_RETAINED_RUNTIME_VISUAL_PAIRS","context":context,"pairs":pairs}

func _initialize()->void:
    var runtime_receipt={
        "schema":RUNTIME_CACHE_SCHEMA,
        "state":"STARTED",
        "exact_vfx_latest_due_head":EXACT_VFX_LATEST_DUE_HEAD,
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "promotion_effect":"NONE",
        "source_interval_s":SOURCE_INTERVAL_S,
        "source_interval_us":SOURCE_INTERVAL_US,
        "presentation_policy":PRESENTATION_POLICY,
        "selection_semantics":SELECTION_SEMANTICS,
        "optimization_candidate":"PREBUILD_EXACT_FINITE_STATE_NATIVE_MESHES_THEN_SWAP_UNDER_LATEST_DUE_POLICY",
        "truth_boundary":"Runtime A/B only. The control preserves VFX's exact latest-due selection semantics and rebuilds exact Weather + sapling source geometry after selection. The candidate prebuilds the same 17 exact native-type meshes per fixed-camera context before the clock starts and swaps them after the same selection decision. This tests whether the known mesh-update speedup improves source freshness or stale-state skipping under the current proof-host fallback. It deliberately trades stable mesh-resource identity and memory for lower timed update work. It does not change VFX source semantics or prove target-device performance, authored 32 Hz presentation, gameplay, physical Weather, arbitrary cameras, final Art Direction, CANON, or production readiness."
    }
    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!=WIDTH_SCHEMA or String(payload.get("status",""))!=WIDTH_STATUS:
        runtime_receipt["state"]="FAIL_INVALID_WIDTH_PAYLOAD"
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
        if int(row.get("index",-1))!=index or absf(float(row.get("time_s",-1.0))-float(index)*SOURCE_INTERVAL_S)>0.000000001:
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
    for context_value in COALESCED_CONTEXTS:
        var context=String(context_value)
        var cache=await build_context_cache(camera,states,context)
        if String(cache.get("state",""))!="PASS_EXACT_17_STATE_NATIVE_TYPE_CACHE":
            runtime_receipt["state"]="FAIL_CACHE_BUILD"
            runtime_receipt["failed_context"]=context
            runtime_receipt["detail"]=cache
            write_runtime_cache_receipt(runtime_receipt)
            quit(1)
            return
        var rebuild=await run_latest_due_mode(viewport,camera,states,context,"rebuild",cache)
        var cached=await run_latest_due_mode(viewport,camera,states,context,"cached_swap",cache)
        var visuals=await retain_visual_pairs(viewport,camera,states,context,cache)
        if String(rebuild.get("state",""))!="OBSERVED_LATEST_DUE_RUNTIME_MODE" or String(cached.get("state",""))!="OBSERVED_LATEST_DUE_RUNTIME_MODE" or String(visuals.get("state",""))!="PASS_RETAINED_RUNTIME_VISUAL_PAIRS":
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

    runtime_receipt["state"]=RUNTIME_CACHE_STATE
    runtime_receipt["receiving_head"]=payload["receiving_head"]
    runtime_receipt["parent_variant_head"]=payload["parent_variant_head"]
    runtime_receipt["weather_variant_head"]=payload["weather_variant_head"]
    runtime_receipt["weather_variant_seed"]=payload["weather_variant_seed"]
    runtime_receipt["weather_variant_layout_digest"]=payload["weather_variant_layout_digest"]
    runtime_receipt["source_width_profile_digest"]=payload["source_width_profile_digest"]
    runtime_receipt["contexts"]=contexts
    runtime_receipt["godot_version"]=Engine.get_version_info()
    write_runtime_cache_receipt(runtime_receipt)
    quit(0)
