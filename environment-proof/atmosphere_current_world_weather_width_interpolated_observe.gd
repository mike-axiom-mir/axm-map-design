extends "res://atmosphere_current_world_weather_width_observe.gd"

const INTERP_SCHEMA := "axm.environment-current-world-weather-width-continuous-phase-observation/v0.1"
const INTERP_STATE := "OBSERVED_CONTINUOUS_PHASE_VISUAL_INTERPOLATION"
const INTERP_CONTEXT_STATE := "OBSERVED_CONTINUOUS_PHASE_CONTEXT"
const INTERP_CONTEXTS := ["path_eye", "elevated_oblique"]
const SOURCE_INTERVAL_S := 0.03125
const SOURCE_INTERVAL_US := 31250
const LAST_SOURCE_INDEX := 16
const LAST_SOURCE_TIME_S := 0.5
const LAST_SOURCE_TIME_US := 500000
const PRESENTATION_POLICY := "CONTINUOUS_PHASE_LINEAR_VISUAL_INTERPOLATION_PRESENTATION_ONLY"
const INTERPOLATION_SEMANTICS := "INTERPOLATE_ONLY_RECEIVING_WEATHER_GEOMETRY_OPACITY_AND_SAPLING_VERTICES_BETWEEN_EXACT_AUTHORED_BRACKETS"

func write_interpolated_receipt(data:Dictionary)->void:
    var file:=FileAccess.open("res://atmosphere-current-world-weather-width-interpolated-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(data,"  ")+"\n")
        file.close()

func capture_interpolated_frame(camera:Camera3D,context:String,frame_index:int)->Dictionary:
    var image:=camera.get_viewport().get_texture().get_image()
    var relative_path="interpolated-frames/%s-frame-%02d.png" % [context,frame_index]
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

func _lerp_number(a:float,b:float,alpha:float)->float:
    return a+(b-a)*alpha

func _blend_vector(values_a:Array,values_b:Array,alpha:float)->Array:
    if values_a.size()!=values_b.size():
        return []
    var result:Array=[]
    for index in range(values_a.size()):
        result.append(_lerp_number(float(values_a[index]),float(values_b[index]),alpha))
    return result

func blend_weather_lines(lower_lines:Array,upper_lines:Array,alpha:float)->Dictionary:
    if lower_lines.size()!=36 or upper_lines.size()!=36:
        return {"state":"FAIL_WEATHER_BRACKET_COUNT"}
    var blended:Array=[]
    for index in range(lower_lines.size()):
        var lower=lower_lines[index] as Dictionary
        var upper=upper_lines[index] as Dictionary
        var streak_id:=String(lower.get("id",""))
        if streak_id.is_empty() or streak_id!=String(upper.get("id","")):
            return {"state":"FAIL_WEATHER_STREAK_IDENTITY","index":index}
        var lower_width:=float(lower.get("source_width_px",-1.0))
        var upper_width:=float(upper.get("source_width_px",-2.0))
        if lower_width<=0.0 or absf(lower_width-upper_width)>0.000000001:
            return {"state":"FAIL_WEATHER_WIDTH_BRACKET_DRIFT","streak_id":streak_id}
        var row:=lower.duplicate(true) as Dictionary
        row["tail_xy"]=_blend_vector(lower["tail_xy"] as Array,upper["tail_xy"] as Array,alpha)
        row["head_xy"]=_blend_vector(lower["head_xy"] as Array,upper["head_xy"] as Array,alpha)
        row["presentation_height_m"]=_lerp_number(float(lower["presentation_height_m"]),float(upper["presentation_height_m"]),alpha)
        row["opacity"]=_lerp_number(float(lower["opacity"]),float(upper["opacity"]),alpha)
        row["source_width_px"]=lower_width
        blended.append(row)
    return {"state":"PASS_INTERPOLATED_WEATHER_BRACKET","lines":blended}

func blend_sapling(lower:Dictionary,upper:Dictionary,alpha:float)->Dictionary:
    var lower_vertices=lower.get("vertices_source_xyz_m",[]) as Array
    var upper_vertices=upper.get("vertices_source_xyz_m",[]) as Array
    var lower_triangles=lower.get("triangles",[]) as Array
    var upper_triangles=upper.get("triangles",[]) as Array
    if lower_vertices.is_empty() or lower_vertices.size()!=upper_vertices.size():
        return {"state":"FAIL_SAPLING_VERTEX_BRACKET"}
    if lower_triangles!=upper_triangles:
        return {"state":"FAIL_SAPLING_TOPOLOGY_BRACKET"}
    var vertices:Array=[]
    for index in range(lower_vertices.size()):
        var blended_vertex:=_blend_vector(lower_vertices[index] as Array,upper_vertices[index] as Array,alpha)
        if blended_vertex.size()!=3:
            return {"state":"FAIL_SAPLING_VERTEX_COMPONENTS","index":index}
        vertices.append(blended_vertex)
    var result:=lower.duplicate(true) as Dictionary
    result["vertices_source_xyz_m"]=vertices
    result["triangles"]=lower_triangles.duplicate(true)
    return {"state":"PASS_INTERPOLATED_SAPLING_BRACKET","sapling":result}

func bracket_for_elapsed(elapsed_us:int,state_count:int)->Dictionary:
    if state_count!=17:
        return {"state":"FAIL_REQUIRES_EXACT_17_STATES"}
    var clamped_us:int=clampi(elapsed_us,0,LAST_SOURCE_TIME_US)
    if clamped_us>=LAST_SOURCE_TIME_US:
        return {
            "state":"PASS_CONTINUOUS_PHASE_BRACKET",
            "lower_index":LAST_SOURCE_INDEX,
            "upper_index":LAST_SOURCE_INDEX,
            "alpha":0.0,
            "source_time_s":LAST_SOURCE_TIME_S,
            "clamped_elapsed_us":clamped_us
        }
    var lower_index:int=clampi(int(floor(float(clamped_us)/float(SOURCE_INTERVAL_US))),0,LAST_SOURCE_INDEX-1)
    var upper_index:int=lower_index+1
    var lower_us:int=lower_index*SOURCE_INTERVAL_US
    var alpha:float=clampf(float(clamped_us-lower_us)/float(SOURCE_INTERVAL_US),0.0,1.0)
    return {
        "state":"PASS_CONTINUOUS_PHASE_BRACKET",
        "lower_index":lower_index,
        "upper_index":upper_index,
        "alpha":alpha,
        "source_time_s":float(clamped_us)/1000000.0,
        "clamped_elapsed_us":clamped_us
    }

func sapling_receipt_is_live(receipt:Dictionary)->bool:
    return int(receipt.get("surface_count",0))>0 and int(receipt.get("source_vertex_count",0))>0 and int(receipt.get("source_triangle_count",0))>0

func run_context_interpolated(camera:Camera3D,states:Array,context:String)->Dictionary:
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

    var clock_start_us:int=Time.get_ticks_usec()
    var samples:Array=[]
    var frame_index:int=0
    var previous_source_time_s:float=-1.0

    while true:
        var selection_tick_us:int=Time.get_ticks_usec()
        var selection_elapsed_us:int=selection_tick_us-clock_start_us
        var bracket:=bracket_for_elapsed(selection_elapsed_us,states.size())
        if bracket.get("state")!="PASS_CONTINUOUS_PHASE_BRACKET":
            return {"state":"FAIL_BRACKET_SELECTION","detail":bracket}

        var source_time_s:=float(bracket["source_time_s"])
        if source_time_s<=previous_source_time_s+0.000001 and source_time_s<LAST_SOURCE_TIME_S:
            await process_frame
            continue

        var lower_index:=int(bracket["lower_index"])
        var upper_index:=int(bracket["upper_index"])
        var alpha:=float(bracket["alpha"])
        var lower=states[lower_index] as Dictionary
        var upper=states[upper_index] as Dictionary
        var lower_scene=lower["scene"] as Dictionary
        var upper_scene=upper["scene"] as Dictionary

        var weather_blend:=blend_weather_lines(lower_scene["weather_lines"] as Array,upper_scene["weather_lines"] as Array,alpha)
        if weather_blend.get("state")!="PASS_INTERPOLATED_WEATHER_BRACKET":
            return {"state":"FAIL_WEATHER_INTERPOLATION","frame_index":frame_index,"detail":weather_blend}
        var sapling_blend:=blend_sapling(lower_scene["sapling"] as Dictionary,upper_scene["sapling"] as Dictionary,alpha)
        if sapling_blend.get("state")!="PASS_INTERPOLATED_SAPLING_BRACKET":
            return {"state":"FAIL_SAPLING_INTERPOLATION","frame_index":frame_index,"detail":sapling_blend}

        var sapling_update=fill_sapling(sapling_blend["sapling"] as Dictionary)
        if not sapling_receipt_is_live(sapling_update):
            return {"state":"FAIL_SAPLING_UPDATE","frame_index":frame_index,"detail":sapling_update}
        var weather_update=fill_weather_width_ribbons(weather_blend["lines"] as Array,camera)
        if weather_update.get("state")!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_WEATHER_UPDATE","frame_index":frame_index,"detail":weather_update}
        if float(weather_update.get("maximum_projected_width_residual_px",999.0))>WIDTH_RESIDUAL_TOL_PX:
            return {"state":"FAIL_WIDTH_RESIDUAL","frame_index":frame_index,"detail":weather_update}

        var submit_tick_us:int=Time.get_ticks_usec()
        await RenderingServer.frame_post_draw
        var draw_tick_us:int=Time.get_ticks_usec()
        var frame=capture_interpolated_frame(camera,context,frame_index)
        if frame.get("state")!="PASS_CAPTURED_FRAME":
            return {"state":"FAIL_FRAME_CAPTURE","frame_index":frame_index,"detail":frame}

        var selection_time_s:=float(selection_tick_us-clock_start_us)/1000000.0
        var submit_time_s:=float(submit_tick_us-clock_start_us)/1000000.0
        var draw_time_s:=float(draw_tick_us-clock_start_us)/1000000.0
        samples.append({
            "frame_index":frame_index,
            "lower_index":lower_index,
            "upper_index":upper_index,
            "alpha":alpha,
            "source_time_s":source_time_s,
            "selection_time_s":selection_time_s,
            "submit_time_s":submit_time_s,
            "draw_time_s":draw_time_s,
            "source_age_at_selection_ms":(selection_time_s-source_time_s)*1000.0,
            "source_age_at_submit_ms":(submit_time_s-source_time_s)*1000.0,
            "source_age_at_draw_ms":(draw_time_s-source_time_s)*1000.0,
            "lower_weather_field_digest":lower["weather_field_digest"],
            "upper_weather_field_digest":upper["weather_field_digest"],
            "lower_weather_width_profile_digest":lower["weather_width_profile_digest"],
            "upper_weather_width_profile_digest":upper["weather_width_profile_digest"],
            "lower_sapling_mesh_digest":lower["sapling_mesh_digest"],
            "upper_sapling_mesh_digest":upper["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "frame":frame
        })
        previous_source_time_s=source_time_s
        frame_index+=1
        if source_time_s>=LAST_SOURCE_TIME_S-0.000001:
            break

    return {
        "state":INTERP_CONTEXT_STATE,
        "context":context,
        "clock_start_us":clock_start_us,
        "source_interval_s":SOURCE_INTERVAL_S,
        "source_interval_us":SOURCE_INTERVAL_US,
        "presentation_policy":PRESENTATION_POLICY,
        "interpolation_semantics":INTERPOLATION_SEMANTICS,
        "samples":samples
    }

func _initialize()->void:
    var receipt={
        "schema":INTERP_SCHEMA,
        "state":"STARTED",
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "promotion_effect":"NONE",
        "presentation_mode":WIDTH_PRESENTATION_MODE,
        "presentation_policy":PRESENTATION_POLICY,
        "interpolation_semantics":INTERPOLATION_SEMANTICS,
        "truth_boundary":"Bounded VFX presentation candidate only. The exact Weather + sapling source states remain authored authority. This observer synthesizes receiving-only linear visual states between adjacent exact brackets at the wall-clock phase available when the renderer returns control. It interpolates Weather tail/head positions, presentation height and opacity plus sapling vertex positions, while source-authored streak width remains unchanged. It does not rewrite Weather source semantics, claim authored 32 Hz delivery, physical weather, gameplay or physics authority, target-device performance, final Art Direction, CANON, production readiness, or mastery."
    }
    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!=WIDTH_SCHEMA:
        receipt["state"]="FAIL_INVALID_WIDTH_PAYLOAD"
        write_interpolated_receipt(receipt)
        quit(1)
        return
    if String(payload.get("status",""))!=WIDTH_STATUS:
        receipt["state"]="FAIL_WIDTH_STRUCTURE_NOT_PASS"
        write_interpolated_receipt(receipt)
        quit(1)
        return
    if String(payload.get("parent_variant_head",""))!=WIDTH_PARENT_HEAD:
        receipt["state"]="FAIL_PARENT_HEAD_DRIFT"
        write_interpolated_receipt(receipt)
        quit(1)
        return

    var states=payload["states"] as Array
    if states.size()!=17:
        receipt["state"]="FAIL_REQUIRES_EXACT_17_STATES"
        write_interpolated_receipt(receipt)
        quit(1)
        return
    for index in range(states.size()):
        var row=states[index] as Dictionary
        var expected_time:=float(index)*SOURCE_INTERVAL_S
        if int(row.get("index",-1))!=index or absf(float(row.get("time_s",-1.0))-expected_time)>0.000000001:
            receipt["state"]="FAIL_SOURCE_SCHEDULE_DRIFT"
            receipt["failed_index"]=index
            write_interpolated_receipt(receipt)
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
        write_interpolated_receipt(receipt)
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
    for context_value in INTERP_CONTEXTS:
        var context=String(context_value)
        var result=await run_context_interpolated(camera,states,context)
        contexts[context]=result
        if String(result.get("state",""))!=INTERP_CONTEXT_STATE:
            receipt["state"]="FAIL_CONTEXT_PRESENTATION"
            receipt["contexts"]=contexts
            write_interpolated_receipt(receipt)
            quit(1)
            return

    receipt["state"]=INTERP_STATE
    receipt["receiving_head"]=payload["receiving_head"]
    receipt["parent_variant_head"]=payload["parent_variant_head"]
    receipt["weather_variant_head"]=payload["weather_variant_head"]
    receipt["weather_variant_seed"]=payload["weather_variant_seed"]
    receipt["weather_variant_layout_digest"]=payload["weather_variant_layout_digest"]
    receipt["source_width_profile_digest"]=payload["source_width_profile_digest"]
    receipt["static_source_meshes"]=static_source_stats
    receipt["contexts"]=contexts
    receipt["godot_version"]=Engine.get_version_info()
    write_interpolated_receipt(receipt)
    quit(0)
