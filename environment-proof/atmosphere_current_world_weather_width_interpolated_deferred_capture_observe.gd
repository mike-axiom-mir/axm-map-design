extends "res://atmosphere_current_world_weather_width_interpolated_observe.gd"

const RUNTIME_CAPTURE_POLICY := "DEFER_PNG_READBACK_UNTIL_AFTER_TIMED_SEQUENCE"
const TIMED_FRAME_STATE := "DEFERRED_FROM_TIMED_LOOP"

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
    var timed_sequence_end_us:int=clock_start_us

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

        var materialize_start_us:int=Time.get_ticks_usec()
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
        timed_sequence_end_us=draw_tick_us

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
            "materialize_duration_ms":float(submit_tick_us-materialize_start_us)/1000.0,
            "post_draw_wait_ms":float(draw_tick_us-submit_tick_us)/1000.0,
            "lower_weather_field_digest":lower["weather_field_digest"],
            "upper_weather_field_digest":upper["weather_field_digest"],
            "lower_weather_width_profile_digest":lower["weather_width_profile_digest"],
            "upper_weather_width_profile_digest":upper["weather_width_profile_digest"],
            "lower_sapling_mesh_digest":lower["sapling_mesh_digest"],
            "upper_sapling_mesh_digest":upper["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "frame":{"state":TIMED_FRAME_STATE}
        })
        previous_source_time_s=source_time_s
        frame_index+=1
        if source_time_s>=LAST_SOURCE_TIME_S-0.000001:
            break

    var deferred_capture_start_us:int=Time.get_ticks_usec()
    var deferred_capture=capture_interpolated_frame(camera,context,frame_index)
    var deferred_capture_end_us:int=Time.get_ticks_usec()
    if deferred_capture.get("state")!="PASS_CAPTURED_FRAME":
        return {"state":"FAIL_DEFERRED_FRAME_CAPTURE","detail":deferred_capture}

    return {
        "state":INTERP_CONTEXT_STATE,
        "context":context,
        "clock_start_us":clock_start_us,
        "source_interval_s":SOURCE_INTERVAL_S,
        "source_interval_us":SOURCE_INTERVAL_US,
        "presentation_policy":PRESENTATION_POLICY,
        "interpolation_semantics":INTERPOLATION_SEMANTICS,
        "runtime_capture_policy":RUNTIME_CAPTURE_POLICY,
        "timed_sequence_duration_ms":float(timed_sequence_end_us-clock_start_us)/1000.0,
        "deferred_capture_duration_ms":float(deferred_capture_end_us-deferred_capture_start_us)/1000.0,
        "deferred_capture":deferred_capture,
        "samples":samples
    }
