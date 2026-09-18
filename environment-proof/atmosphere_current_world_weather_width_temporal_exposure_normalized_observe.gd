extends "res://atmosphere_current_world_weather_width_temporal_exposure_observe.gd"

const NORMALIZED_EXPOSURE_SCHEMA := "axm.environment-current-world-weather-width-temporal-exposure-normalized-observation/v0.1"
const NORMALIZED_EXPOSURE_STATE := "OBSERVED_OPACITY_NORMALIZED_TEMPORAL_EXPOSURE_CANDIDATE"
const NORMALIZED_EXPOSURE_POLICY := "TWO_TAP_TRANSMITTANCE_NORMALIZED_RECEIVING_ONLY_TEMPORAL_EXPOSURE"
const NORMALIZED_MAPPING := "SOURCE_ALPHA_TO_TRANSMITTANCE_EXPONENT"

func normalized_tap_alpha(source_alpha:float,weight:float)->float:
    var bounded_alpha:=clampf(source_alpha,0.0,1.0)
    return 1.0-pow(1.0-bounded_alpha,weight)

func build_exposure_lines(current_lines:Array,lagged_lines:Array)->Dictionary:
    if current_lines.size()!=36 or lagged_lines.size()!=36:
        return {"state":"FAIL_EXPOSURE_SOURCE_COUNT"}
    if absf(EXPOSURE_CURRENT_WEIGHT+EXPOSURE_LAGGED_WEIGHT-1.0)>0.000000001:
        return {"state":"FAIL_EXPOSURE_WEIGHT_SUM"}
    var lines:Array=[]
    var opacity_rows:Array=[]
    var maximum_source_alpha:=0.0
    var maximum_theoretical_combined_alpha:=0.0
    var maximum_combined_alpha_over_source:=0.0
    var maximum_equal_source_combined_alpha_error:=0.0
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

        var current_tap_alpha:=normalized_tap_alpha(source_alpha,EXPOSURE_CURRENT_WEIGHT)
        var lagged_tap_alpha:=normalized_tap_alpha(lagged_alpha,EXPOSURE_LAGGED_WEIGHT)

        var current_tap:=current.duplicate(true) as Dictionary
        current_tap["opacity"]=current_tap_alpha
        current_tap["exposure_tap"]="current"
        current_tap["exposure_source_id"]=current_id
        current_tap["opacity_mapping"]=NORMALIZED_MAPPING
        lines.append(current_tap)

        var lagged_tap:=lagged.duplicate(true) as Dictionary
        lagged_tap["opacity"]=lagged_tap_alpha
        lagged_tap["exposure_tap"]="lagged"
        lagged_tap["exposure_source_id"]=current_id
        lagged_tap["opacity_mapping"]=NORMALIZED_MAPPING
        lines.append(lagged_tap)

        var effective_alpha:=1.0-(1.0-current_tap_alpha)*(1.0-lagged_tap_alpha)
        var alpha_ceiling:=maxf(source_alpha,lagged_alpha)
        var equal_source:=absf(source_alpha-lagged_alpha)<=0.000000001
        var equal_source_error:=absf(effective_alpha-source_alpha) if equal_source else 0.0
        maximum_source_alpha=maxf(maximum_source_alpha,alpha_ceiling)
        maximum_theoretical_combined_alpha=maxf(maximum_theoretical_combined_alpha,effective_alpha)
        maximum_combined_alpha_over_source=maxf(maximum_combined_alpha_over_source,effective_alpha-alpha_ceiling)
        maximum_equal_source_combined_alpha_error=maxf(maximum_equal_source_combined_alpha_error,equal_source_error)
        opacity_rows.append({
            "streak_id":current_id,
            "current_source_alpha":source_alpha,
            "lagged_source_alpha":lagged_alpha,
            "current_tap_alpha":current_tap_alpha,
            "lagged_tap_alpha":lagged_tap_alpha,
            "effective_alpha":effective_alpha,
            "alpha_ceiling":alpha_ceiling,
            "equal_source":equal_source,
            "equal_source_combined_alpha_error":equal_source_error
        })

    return {
        "state":"PASS_BOUNDED_TEMPORAL_EXPOSURE_LINES",
        "lines":lines,
        "opacity_rows":opacity_rows,
        "source_streak_count":36,
        "presentation_tap_count":72,
        "current_weight":EXPOSURE_CURRENT_WEIGHT,
        "lagged_weight":EXPOSURE_LAGGED_WEIGHT,
        "weight_sum":EXPOSURE_CURRENT_WEIGHT+EXPOSURE_LAGGED_WEIGHT,
        "opacity_mapping":NORMALIZED_MAPPING,
        "maximum_source_alpha":maximum_source_alpha,
        "maximum_theoretical_combined_alpha":maximum_theoretical_combined_alpha,
        "maximum_combined_alpha_over_source":maximum_combined_alpha_over_source,
        "maximum_equal_source_combined_alpha_error":maximum_equal_source_combined_alpha_error
    }

func write_exposure_receipt(data:Dictionary)->void:
    data["schema"]=NORMALIZED_EXPOSURE_SCHEMA
    if String(data.get("state",""))=="OBSERVED_BOUNDED_TEMPORAL_EXPOSURE_CANDIDATE":
        data["state"]=NORMALIZED_EXPOSURE_STATE
    data["presentation_policy"]=NORMALIZED_EXPOSURE_POLICY
    data["opacity_mapping"]=NORMALIZED_MAPPING
    data["truth_boundary"]="Bounded receiving-only VFX presentation candidate. Each authored Weather streak is rendered as current plus 15.625 ms lagged source-bound taps. Each tap maps source alpha into a weighted transmittance exponent, so coincident equal-source taps reproduce the original source alpha instead of dimming it. Exact Weather source states remain authority; sapling motion remains single current-phase interpolation. This deterministic review proof isolates the prior zero-lag opacity attenuation confound but does not establish authored 32 Hz delivery, perceptual smoothness, final aesthetics, physical weather, gameplay or physics authority, target-device performance, arbitrary cameras, CANON, production readiness, or mastery."
    var contexts=data.get("contexts",{}) as Dictionary
    for context_key in contexts.keys():
        var context=contexts[context_key] as Dictionary
        context["presentation_policy"]=NORMALIZED_EXPOSURE_POLICY
    var file:=FileAccess.open("res://atmosphere-current-world-weather-width-temporal-exposure-normalized-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(data,"  ")+"\n")
        file.close()
