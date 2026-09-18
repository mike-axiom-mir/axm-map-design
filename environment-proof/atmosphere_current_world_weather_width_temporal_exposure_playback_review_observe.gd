extends "res://atmosphere_current_world_weather_width_temporal_exposure_normalized_observe.gd"

const SOURCE_CADENCE_REVIEW_SCHEMA := "axm.environment-current-world-weather-width-temporal-exposure-source-cadence-observation/v0.1"
const SOURCE_CADENCE_REVIEW_STATE := "OBSERVED_OPACITY_NORMALIZED_TEMPORAL_EXPOSURE_SOURCE_CADENCE_REVIEW"
const SOURCE_CADENCE_REVIEW_PHASES_US := [
    0,31250,62500,93750,125000,156250,187500,218750,250000,
    281250,312500,343750,375000,406250,437500,468750,500000
]
const SOURCE_CADENCE_INTERVAL_US := 31250

func write_exposure_receipt(data:Dictionary)->void:
    data["schema"]=SOURCE_CADENCE_REVIEW_SCHEMA
    var prior_state:=String(data.get("state",""))
    if prior_state=="OBSERVED_BOUNDED_TEMPORAL_EXPOSURE_CANDIDATE" or prior_state==NORMALIZED_EXPOSURE_STATE:
        data["state"]=SOURCE_CADENCE_REVIEW_STATE
    data["presentation_policy"]=NORMALIZED_EXPOSURE_POLICY
    data["opacity_mapping"]=NORMALIZED_MAPPING
    data["review_phases_us"]=SOURCE_CADENCE_REVIEW_PHASES_US
    data["source_cadence_interval_us"]=SOURCE_CADENCE_INTERVAL_US
    data["review_delivery_semantics"]="EXACT_REAL_GODOT_SOURCE_CADENCE_FRAME_PAIRS__OFFLINE_ONE_SHOT_NOMINAL_32HZ_REVIEW_ONLY"
    data["truth_boundary"]="Review-only receiving evidence. The exact unchanged single-tap source-width control and exact unchanged opacity-normalized two-tap candidate are captured at all 17 authored 31.25 ms source-evaluation phases. The retained frames may be advanced by an offline page against a nominal 32 Hz clock, but browser/display cadence is not measured and no end-to-start loop seam is claimed. This does not establish human-perceived smoothness, final aesthetics, authored display delivery, physical Weather, gameplay or physics authority, target-device performance, arbitrary cameras, Runtime adoption, CANON, production readiness, or mastery."
    var contexts=data.get("contexts",{}) as Dictionary
    for context_key in contexts.keys():
        var context=contexts[context_key] as Dictionary
        context["presentation_policy"]=NORMALIZED_EXPOSURE_POLICY
        context["review_phases_us"]=SOURCE_CADENCE_REVIEW_PHASES_US
        context["source_cadence_interval_us"]=SOURCE_CADENCE_INTERVAL_US
    var file:=FileAccess.open("res://atmosphere-current-world-weather-width-temporal-exposure-source-cadence-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(data,"  ")+"\n")
        file.close()

func run_exposure_context(camera:Camera3D,states:Array,context:String)->Dictionary:
    var first=states[0] as Dictionary
    var first_scene=first["scene"] as Dictionary
    configure_camera(camera,first_scene,context)
    await settle(1)
    var samples:Array=[]
    var weather_ids:Array=[]
    var sapling_ids:Array=[]

    for sample_index in range(SOURCE_CADENCE_REVIEW_PHASES_US.size()):
        var phase_us:=int(SOURCE_CADENCE_REVIEW_PHASES_US[sample_index])
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
        "presentation_policy":NORMALIZED_EXPOSURE_POLICY,
        "review_phases_us":SOURCE_CADENCE_REVIEW_PHASES_US,
        "source_cadence_interval_us":SOURCE_CADENCE_INTERVAL_US,
        "configured_lag_us":EXPOSURE_LAG_US,
        "samples":samples,
        "weather_resource_ids":weather_ids,
        "sapling_resource_ids":sapling_ids
    }
