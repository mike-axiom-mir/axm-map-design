extends "res://atmosphere_current_world_weather_width_temporal_exposure_observe.gd"

const RUNTIME_BUDGET_SCHEMA := "axm.environment-weather-temporal-exposure-runtime-observation/v0.1"
const SOURCE_VFX_HEAD := "92cfe5d0dc7e254c1c3e19c5fc168298dea3493a"
const CONTROL_MODE := "single_tap_control"
const CANDIDATE_MODE := "two_tap_temporal_exposure"

func write_runtime_budget_receipt(data:Dictionary,mode:String)->void:
    var path := "res://temporal-exposure-budget-%s-runtime.json" % mode
    var file:=FileAccess.open(path,FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(data,"  ")+"\n")
        file.close()

func fail_runtime_budget(data:Dictionary,mode:String,state:String,detail:Variant=null)->void:
    data["state"]=state
    if detail!=null:
        data["detail"]=detail
    data["godot_version"]=Engine.get_version_info()
    write_runtime_budget_receipt(data,mode)
    push_error(state)
    quit(1)

func timed_control_fill(lines:Array,camera:Camera3D)->Dictionary:
    var start_us:=Time.get_ticks_usec()
    var update:=fill_weather_width_ribbons(lines,camera)
    var end_us:=Time.get_ticks_usec()
    return {
        "state":update.get("state","FAIL"),
        "prepare_usec":end_us-start_us,
        "build_usec":0,
        "fill_usec":end_us-start_us,
        "presentation_streak_count":int(update.get("streak_count",-1)),
        "weather_update":update
    }

func timed_candidate_fill(current_lines:Array,lagged_lines:Array,camera:Camera3D)->Dictionary:
    var start_us:=Time.get_ticks_usec()
    var build:=build_exposure_lines(current_lines,lagged_lines)
    var build_end_us:=Time.get_ticks_usec()
    if build.get("state")!="PASS_BOUNDED_TEMPORAL_EXPOSURE_LINES":
        return {
            "state":"FAIL_EXPOSURE_BUILD",
            "prepare_usec":build_end_us-start_us,
            "build_usec":build_end_us-start_us,
            "fill_usec":0,
            "presentation_streak_count":int(build.get("presentation_tap_count",-1)),
            "exposure_build":build
        }
    var update:=fill_weather_width_ribbons(build["lines"] as Array,camera)
    var end_us:=Time.get_ticks_usec()
    var compact_build:=build.duplicate(false)
    compact_build.erase("lines")
    return {
        "state":update.get("state","FAIL"),
        "prepare_usec":end_us-start_us,
        "build_usec":build_end_us-start_us,
        "fill_usec":end_us-build_end_us,
        "presentation_streak_count":int(build.get("presentation_tap_count",-1)),
        "exposure_build":compact_build,
        "weather_update":update
    }

func observe_context(camera:Camera3D,states:Array,context:String,mode:String)->Dictionary:
    var first=states[0] as Dictionary
    configure_camera(camera,first["scene"] as Dictionary,context)
    await settle(2)
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

        var prepared:Dictionary
        if mode==CONTROL_MODE:
            prepared=timed_control_fill(current["weather_lines"] as Array,camera)
        else:
            prepared=timed_candidate_fill(current["weather_lines"] as Array,lagged["weather_lines"] as Array,camera)
        if prepared.get("state")!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_WEATHER_PREPARE","sample_index":sample_index,"detail":prepared}
        var weather_update=prepared["weather_update"] as Dictionary
        if float(weather_update.get("maximum_projected_width_residual_px",999.0))>WIDTH_RESIDUAL_TOL_PX:
            return {"state":"FAIL_WIDTH_RESIDUAL","sample_index":sample_index,"detail":prepared}

        var postdraw_start_us:=Time.get_ticks_usec()
        await RenderingServer.frame_post_draw
        var postdraw_end_us:=Time.get_ticks_usec()
        var stats:=runtime_stats()

        weather_ids.append([
            int(weather_update.get("node_instance_id",-1)),
            int(weather_update.get("mesh_instance_id",-1)),
            int(weather_update.get("material_instance_id",-1))
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
            "prepare_usec":int(prepared.get("prepare_usec",-1)),
            "build_usec":int(prepared.get("build_usec",-1)),
            "fill_usec":int(prepared.get("fill_usec",-1)),
            "postdraw_wait_usec":postdraw_end_us-postdraw_start_us,
            "presentation_streak_count":int(prepared.get("presentation_streak_count",-1)),
            "source_streak_count":36,
            "current_bracket":{
                "lower_index":current["lower_index"],
                "upper_index":current["upper_index"],
                "alpha":current["alpha"],
                "lower_weather_field_digest":current["lower_weather_field_digest"],
                "upper_weather_field_digest":current["upper_weather_field_digest"],
                "lower_weather_width_profile_digest":current["lower_weather_width_profile_digest"],
                "upper_weather_width_profile_digest":current["upper_weather_width_profile_digest"]
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
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "runtime":stats,
            "exposure_build":prepared.get("exposure_build",{})
        })

    return {
        "state":"PASS_TEMPORAL_EXPOSURE_RUNTIME_CONTEXT_OBSERVED",
        "context":context,
        "mode":mode,
        "samples":samples,
        "weather_resource_ids":weather_ids,
        "sapling_resource_ids":sapling_ids
    }

func _initialize()->void:
    var mode:=OS.get_environment("AXM_RUNTIME_MODE")
    if mode!=CONTROL_MODE and mode!=CANDIDATE_MODE:
        mode="invalid"
    var receipt={
        "schema":RUNTIME_BUDGET_SCHEMA,
        "state":"STARTED",
        "mode":mode,
        "source_vfx_head":SOURCE_VFX_HEAD,
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "presentation_policy":EXPOSURE_POLICY,
        "capture_policy":"NO_IMAGE_READBACK_OR_ENCODING_IN_MEASUREMENT_LOOP",
        "promotion_effect":"NONE",
        "truth_boundary":"Runtime-only deterministic review-phase cost observation of the VFX-owned single-tap control versus the exact two-tap temporal-exposure receiving representation. Image readback is excluded from the measured loop. This may characterize proof-host submission, observed memory and Weather preparation cost only; it does not establish authored 32 Hz delivery, target-device CPU/GPU/FPS/VRAM, final visual preference, physical Weather, gameplay, CANON, production readiness or mastery."
    }
    if mode=="invalid":
        fail_runtime_budget(receipt,mode,"FAIL_RUNTIME_MODE")
        return

    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!=WIDTH_SCHEMA:
        fail_runtime_budget(receipt,mode,"FAIL_INVALID_WIDTH_PAYLOAD")
        return
    if String(payload.get("status",""))!=WIDTH_STATUS:
        fail_runtime_budget(receipt,mode,"FAIL_WIDTH_STRUCTURE_NOT_PASS")
        return
    if String(payload.get("receiving_head",""))!=SOURCE_VFX_HEAD:
        fail_runtime_budget(receipt,mode,"FAIL_SOURCE_VFX_HEAD_DRIFT",payload.get("receiving_head"))
        return
    var states=payload["states"] as Array
    if states.size()!=17:
        fail_runtime_budget(receipt,mode,"FAIL_REQUIRES_EXACT_17_STATES")
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
        fail_runtime_budget(receipt,mode,"FAIL_REAR_TREE_CULLING_TARGET_DRIFT")
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

    var contexts:Dictionary={}
    for context_value in WIDTH_CONTEXTS:
        var context:=String(context_value)
        var observed=await observe_context(camera,states,context,mode)
        if observed.get("state")!="PASS_TEMPORAL_EXPOSURE_RUNTIME_CONTEXT_OBSERVED":
            fail_runtime_budget(receipt,mode,"FAIL_CONTEXT_OBSERVATION",observed)
            return
        contexts[context]=observed

    receipt["state"]="PASS_TEMPORAL_EXPOSURE_RUNTIME_OBSERVATION"
    receipt["receiving_head"]=payload["receiving_head"]
    receipt["review_phases_us"]=REVIEW_PHASES_US
    receipt["configured_lag_us"]=EXPOSURE_LAG_US
    receipt["source_streak_count"]=36
    receipt["expected_presentation_streak_count"]=36 if mode==CONTROL_MODE else 72
    receipt["static_source_meshes"]=static_source_stats
    receipt["contexts"]=contexts
    receipt["godot_version"]=Engine.get_version_info()
    write_runtime_budget_receipt(receipt,mode)
    quit(0)
