extends "res://atmosphere_current_world_weather_width_interpolated_observe.gd"

const EXPOSURE_SCHEMA := "axm.environment-current-world-weather-width-temporal-exposure-observation/v0.1"
const EXPOSURE_STATE := "OBSERVED_BOUNDED_TEMPORAL_EXPOSURE_CANDIDATE"
const EXPOSURE_CONTEXT_STATE := "OBSERVED_BOUNDED_TEMPORAL_EXPOSURE_CONTEXT"
const EXPOSURE_POLICY := "TWO_TAP_HALF_OPACITY_RECEIVING_ONLY_TEMPORAL_EXPOSURE"
const EXPOSURE_LAG_US := 15625
const EXPOSURE_CURRENT_WEIGHT := 0.5
const EXPOSURE_LAGGED_WEIGHT := 0.5
const REVIEW_PHASES_US := [0, 62500, 125000, 187500, 250000, 312500, 375000, 437500, 500000]

func write_exposure_receipt(data:Dictionary)->void:
    var file:=FileAccess.open("res://atmosphere-current-world-weather-width-temporal-exposure-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(data,"  ")+"\n")
        file.close()

func capture_exposure_frame(camera:Camera3D,context:String,sample_index:int,mode:String)->Dictionary:
    var image:=camera.get_viewport().get_texture().get_image()
    if image==null or image.is_empty():
        return {"state":"FAIL_CAPTURE_EMPTY","mode":mode,"sample_index":sample_index}
    image.convert(Image.FORMAT_RGBA8)
    var png_relative="temporal-exposure-frames/%s-%s-%02d.png" % [mode,context,sample_index]
    var raw_relative="temporal-exposure-raw/%s-%s-%02d.rgba" % [mode,context,sample_index]
    var png_resource="res://"+png_relative
    var raw_resource="res://"+raw_relative
    var png_error:=image.save_png(png_resource)
    if png_error!=OK:
        return {"state":"FAIL_CAPTURE_PNG","mode":mode,"sample_index":sample_index,"error":png_error}
    var raw_file:=FileAccess.open(raw_resource,FileAccess.WRITE)
    if raw_file==null:
        return {"state":"FAIL_CAPTURE_RAW","mode":mode,"sample_index":sample_index}
    raw_file.store_buffer(image.get_data())
    raw_file.close()
    return {
        "state":"PASS_CAPTURED_EXPOSURE_FRAME",
        "mode":mode,
        "png_path":png_relative,
        "raw_path":raw_relative,
        "png_sha256":FileAccess.get_sha256(png_resource),
        "raw_sha256":FileAccess.get_sha256(raw_resource),
        "width":image.get_width(),
        "height":image.get_height(),
        "format":"RGBA8"
    }

func phase_sample(states:Array,phase_us:int)->Dictionary:
    var bracket:=bracket_for_elapsed(phase_us,states.size())
    if bracket.get("state")!="PASS_CONTINUOUS_PHASE_BRACKET":
        return {"state":"FAIL_PHASE_BRACKET","detail":bracket}
    var lower_index:=int(bracket["lower_index"])
    var upper_index:=int(bracket["upper_index"])
    var alpha:=float(bracket["alpha"])
    var lower=states[lower_index] as Dictionary
    var upper=states[upper_index] as Dictionary
    var lower_scene=lower["scene"] as Dictionary
    var upper_scene=upper["scene"] as Dictionary
    var weather_blend:=blend_weather_lines(lower_scene["weather_lines"] as Array,upper_scene["weather_lines"] as Array,alpha)
    if weather_blend.get("state")!="PASS_INTERPOLATED_WEATHER_BRACKET":
        return {"state":"FAIL_PHASE_WEATHER_BLEND","detail":weather_blend}
    var sapling_blend:=blend_sapling(lower_scene["sapling"] as Dictionary,upper_scene["sapling"] as Dictionary,alpha)
    if sapling_blend.get("state")!="PASS_INTERPOLATED_SAPLING_BRACKET":
        return {"state":"FAIL_PHASE_SAPLING_BLEND","detail":sapling_blend}
    return {
        "state":"PASS_PHASE_SAMPLE",
        "phase_us":phase_us,
        "source_time_s":float(phase_us)/1000000.0,
        "lower_index":lower_index,
        "upper_index":upper_index,
        "alpha":alpha,
        "lower_weather_field_digest":lower["weather_field_digest"],
        "upper_weather_field_digest":upper["weather_field_digest"],
        "lower_weather_width_profile_digest":lower["weather_width_profile_digest"],
        "upper_weather_width_profile_digest":upper["weather_width_profile_digest"],
        "lower_sapling_mesh_digest":lower["sapling_mesh_digest"],
        "upper_sapling_mesh_digest":upper["sapling_mesh_digest"],
        "weather_lines":weather_blend["lines"],
        "sapling":sapling_blend["sapling"]
    }

func build_exposure_lines(current_lines:Array,lagged_lines:Array)->Dictionary:
    if current_lines.size()!=36 or lagged_lines.size()!=36:
        return {"state":"FAIL_EXPOSURE_SOURCE_COUNT"}
    if absf(EXPOSURE_CURRENT_WEIGHT+EXPOSURE_LAGGED_WEIGHT-1.0)>0.000000001:
        return {"state":"FAIL_EXPOSURE_WEIGHT_SUM"}
    var lines:Array=[]
    var maximum_source_alpha:=0.0
    var maximum_theoretical_combined_alpha:=0.0
    var maximum_combined_alpha_over_source:=0.0
    for index in range(36):
        var current=current_lines[index] as Dictionary
        var lagged=lagged_lines[index] as Dictionary
        var current_id:=String(current.get("id",""))
        if current_id.is_empty() or current_id!=String(lagged.get("id","")):
            return {"state":"FAIL_EXPOSURE_STREAK_IDENTITY","index":index}
        var current_width:=float(current.get("source_width_px",-1.0))
        var lagged_width:=float(lagged.get("source_width_px",-2.0))
        if current_width<=0.0 or absf(current_width-lagged_width)>0.000000001:
            return {"state":"FAIL_EXPOSURE_WIDTH_IDENTITY","streak_id":current_id}
        var source_alpha:=float(current.get("opacity",-1.0))
        var lagged_alpha:=float(lagged.get("opacity",-1.0))
        if source_alpha<0.0 or source_alpha>1.0 or lagged_alpha<0.0 or lagged_alpha>1.0:
            return {"state":"FAIL_EXPOSURE_OPACITY_RANGE","streak_id":current_id}

        var current_tap:=current.duplicate(true) as Dictionary
        current_tap["opacity"]=source_alpha*EXPOSURE_CURRENT_WEIGHT
        current_tap["exposure_tap"]="current"
        current_tap["exposure_source_id"]=current_id
        lines.append(current_tap)

        var lagged_tap:=lagged.duplicate(true) as Dictionary
        lagged_tap["opacity"]=lagged_alpha*EXPOSURE_LAGGED_WEIGHT
        lagged_tap["exposure_tap"]="lagged"
        lagged_tap["exposure_source_id"]=current_id
        lines.append(lagged_tap)

        var effective_alpha:=1.0-(1.0-source_alpha*EXPOSURE_CURRENT_WEIGHT)*(1.0-lagged_alpha*EXPOSURE_LAGGED_WEIGHT)
        maximum_source_alpha=maxf(maximum_source_alpha,maxf(source_alpha,lagged_alpha))
        maximum_theoretical_combined_alpha=maxf(maximum_theoretical_combined_alpha,effective_alpha)
        maximum_combined_alpha_over_source=maxf(maximum_combined_alpha_over_source,effective_alpha-maxf(source_alpha,lagged_alpha))

    return {
        "state":"PASS_BOUNDED_TEMPORAL_EXPOSURE_LINES",
        "lines":lines,
        "source_streak_count":36,
        "presentation_tap_count":72,
        "current_weight":EXPOSURE_CURRENT_WEIGHT,
        "lagged_weight":EXPOSURE_LAGGED_WEIGHT,
        "weight_sum":EXPOSURE_CURRENT_WEIGHT+EXPOSURE_LAGGED_WEIGHT,
        "maximum_source_alpha":maximum_source_alpha,
        "maximum_theoretical_combined_alpha":maximum_theoretical_combined_alpha,
        "maximum_combined_alpha_over_source":maximum_combined_alpha_over_source
    }

func run_exposure_context(camera:Camera3D,states:Array,context:String)->Dictionary:
    var first=states[0] as Dictionary
    var first_scene=first["scene"] as Dictionary
    configure_camera(camera,first_scene,context)
    await settle(1)
    var samples:Array=[]
    var weather_ids:Array=[]
    var sapling_ids:Array=[]

    for sample_index in range(REVIEW_PHASES_US.size()):
        var phase_us:=int(REVIEW_PHASES_US[sample_index])
        var lagged_phase_us:=maxi(0,phase_us-EXPOSURE_LAG_US)
        var current:=phase_sample(states,phase_us)
        var lagged:=phase_sample(states,lagged_phase_us)
        if current.get("state")!="PASS_PHASE_SAMPLE" or lagged.get("state")!="PASS_PHASE_SAMPLE":
            return {"state":"FAIL_PHASE_SAMPLE","sample_index":sample_index,"current":current,"lagged":lagged}

        var sapling_update=fill_sapling(current["sapling"] as Dictionary)
        if not sapling_receipt_is_live(sapling_update):
            return {"state":"FAIL_SAPLING_UPDATE","sample_index":sample_index,"detail":sapling_update}

        var control_weather=fill_weather_width_ribbons(current["weather_lines"] as Array,camera)
        if control_weather.get("state")!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_CONTROL_WEATHER","sample_index":sample_index,"detail":control_weather}
        if float(control_weather.get("maximum_projected_width_residual_px",999.0))>WIDTH_RESIDUAL_TOL_PX:
            return {"state":"FAIL_CONTROL_WIDTH_RESIDUAL","sample_index":sample_index,"detail":control_weather}
        await RenderingServer.frame_post_draw
        var control_frame:=capture_exposure_frame(camera,context,sample_index,"control")
        if control_frame.get("state")!="PASS_CAPTURED_EXPOSURE_FRAME":
            return {"state":"FAIL_CONTROL_CAPTURE","sample_index":sample_index,"detail":control_frame}

        var exposure_build:=build_exposure_lines(current["weather_lines"] as Array,lagged["weather_lines"] as Array)
        if exposure_build.get("state")!="PASS_BOUNDED_TEMPORAL_EXPOSURE_LINES":
            return {"state":"FAIL_EXPOSURE_BUILD","sample_index":sample_index,"detail":exposure_build}
        var exposure_weather=fill_weather_width_ribbons(exposure_build["lines"] as Array,camera)
        if exposure_weather.get("state")!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_EXPOSURE_WEATHER","sample_index":sample_index,"detail":exposure_weather}
        if float(exposure_weather.get("maximum_projected_width_residual_px",999.0))>WIDTH_RESIDUAL_TOL_PX:
            return {"state":"FAIL_EXPOSURE_WIDTH_RESIDUAL","sample_index":sample_index,"detail":exposure_weather}
        await RenderingServer.frame_post_draw
        var exposure_frame:=capture_exposure_frame(camera,context,sample_index,"candidate")
        if exposure_frame.get("state")!="PASS_CAPTURED_EXPOSURE_FRAME":
            return {"state":"FAIL_EXPOSURE_CAPTURE","sample_index":sample_index,"detail":exposure_frame}

        weather_ids.append([
            int(exposure_weather.get("node_instance_id",-1)),
            int(exposure_weather.get("mesh_instance_id",-1)),
            int(exposure_weather.get("material_instance_id",-1))
        ])
        sapling_ids.append([
            int(sapling_update.get("node_instance_id",-1)),
            int(sapling_update.get("mesh_instance_id",-1)),
            int(sapling_update.get("material_instance_id",-1))
        ])
        samples.append({
            "sample_index":sample_index,
            "phase_us":phase_us,
            "lagged_phase_us":lagged_phase_us,
            "lag_us":phase_us-lagged_phase_us,
            "current_bracket":{
                "lower_index":current["lower_index"],
                "upper_index":current["upper_index"],
                "alpha":current["alpha"],
                "lower_weather_field_digest":current["lower_weather_field_digest"],
                "upper_weather_field_digest":current["upper_weather_field_digest"],
                "lower_weather_width_profile_digest":current["lower_weather_width_profile_digest"],
                "upper_weather_width_profile_digest":current["upper_weather_width_profile_digest"],
                "lower_sapling_mesh_digest":current["lower_sapling_mesh_digest"],
                "upper_sapling_mesh_digest":current["upper_sapling_mesh_digest"]
            },
            "lagged_bracket":{
                "lower_index":lagged["lower_index"],
                "upper_index":lagged["upper_index"],
                "alpha":lagged["alpha"],
                "lower_weather_field_digest":lagged["lower_weather_field_digest"],
                "upper_weather_field_digest":lagged["upper_weather_field_digest"],
                "lower_weather_width_profile_digest":lagged["lower_weather_width_profile_digest"],
                "upper_weather_width_profile_digest":lagged["upper_weather_width_profile_digest"]
            },
            "exposure_build":exposure_build.duplicate(false),
            "sapling_update":sapling_update,
            "control_weather_update":control_weather,
            "exposure_weather_update":exposure_weather,
            "control_frame":control_frame,
            "candidate_frame":exposure_frame
        })
        samples[-1]["exposure_build"].erase("lines")

    return {
        "state":EXPOSURE_CONTEXT_STATE,
        "context":context,
        "presentation_policy":EXPOSURE_POLICY,
        "review_phases_us":REVIEW_PHASES_US,
        "configured_lag_us":EXPOSURE_LAG_US,
        "samples":samples,
        "weather_resource_ids":weather_ids,
        "sapling_resource_ids":sapling_ids
    }

func _initialize()->void:
    var receipt={
        "schema":EXPOSURE_SCHEMA,
        "state":"STARTED",
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "promotion_effect":"NONE",
        "presentation_mode":WIDTH_PRESENTATION_MODE,
        "presentation_policy":EXPOSURE_POLICY,
        "configured_lag_us":EXPOSURE_LAG_US,
        "current_weight":EXPOSURE_CURRENT_WEIGHT,
        "lagged_weight":EXPOSURE_LAGGED_WEIGHT,
        "truth_boundary":"Bounded receiving-only VFX presentation candidate. Each authored Weather streak is rendered as two camera-projected source-width taps: current continuous-phase state plus a 15.625 ms lagged continuous-phase state, each at half of its interpolated source opacity. The exact Weather source states remain authority; sapling motion remains single current-phase interpolation. This proof uses deterministic review phases, not wall-clock scheduling. It does not establish authored 32 Hz delivery, final temporal aesthetics, physical weather, gameplay or physics authority, target-device performance, arbitrary cameras, CANON, production readiness, or mastery."
    }
    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!=WIDTH_SCHEMA:
        receipt["state"]="FAIL_INVALID_WIDTH_PAYLOAD"
        write_exposure_receipt(receipt)
        quit(1)
        return
    if String(payload.get("status",""))!=WIDTH_STATUS:
        receipt["state"]="FAIL_WIDTH_STRUCTURE_NOT_PASS"
        write_exposure_receipt(receipt)
        quit(1)
        return
    if String(payload.get("parent_variant_head",""))!=WIDTH_PARENT_HEAD:
        receipt["state"]="FAIL_PARENT_HEAD_DRIFT"
        write_exposure_receipt(receipt)
        quit(1)
        return

    var states=payload["states"] as Array
    if states.size()!=17:
        receipt["state"]="FAIL_REQUIRES_EXACT_17_STATES"
        write_exposure_receipt(receipt)
        quit(1)
        return
    for index in range(states.size()):
        var row=states[index] as Dictionary
        if int(row.get("index",-1))!=index or absf(float(row.get("time_s",-1.0))-float(index)*SOURCE_INTERVAL_S)>0.000000001:
            receipt["state"]="FAIL_SOURCE_SCHEDULE_DRIFT"
            receipt["failed_index"]=index
            write_exposure_receipt(receipt)
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
        write_exposure_receipt(receipt)
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
        var context:=String(context_value)
        var result=await run_exposure_context(camera,states,context)
        contexts[context]=result
        if String(result.get("state",""))!=EXPOSURE_CONTEXT_STATE:
            receipt["state"]="FAIL_EXPOSURE_CONTEXT"
            receipt["failed_context"]=context
            receipt["contexts"]=contexts
            receipt["static_source_meshes"]=static_source_stats
            write_exposure_receipt(receipt)
            quit(1)
            return

    receipt["state"]=EXPOSURE_STATE
    receipt["receiving_head"]=payload["receiving_head"]
    receipt["parent_variant_head"]=payload["parent_variant_head"]
    receipt["weather_variant_head"]=payload["weather_variant_head"]
    receipt["weather_variant_seed"]=payload["weather_variant_seed"]
    receipt["weather_variant_layout_digest"]=payload["weather_variant_layout_digest"]
    receipt["source_width_profile_digest"]=payload["source_width_profile_digest"]
    receipt["static_source_meshes"]=static_source_stats
    receipt["contexts"]=contexts
    receipt["godot_version"]=Engine.get_version_info()
    write_exposure_receipt(receipt)
    quit(0)
