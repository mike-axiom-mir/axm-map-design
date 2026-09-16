extends "res://atmosphere_current_world_weather_variant_observe.gd"

const WIDTH_PAYLOAD_PATH := "res://generated/current_world_weather_width.json"
const WIDTH_SCHEMA := "axm.environment-current-world-weather-width-evidence/v0.1"
const WIDTH_STATUS := "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE"
const WIDTH_PARENT_HEAD := "e482d003853e52fc835f1797ddfb6506a50083ef"
const WIDTH_CONTEXTS := ["path_eye", "elevated_oblique"]
const WIDTH_RESIDUAL_TOL_PX := 0.05
const WIDTH_PRESENTATION_MODE := "SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBON"

func write_receipt()->void:
    var file:=FileAccess.open("res://atmosphere-current-world-weather-width-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(receipt,"  ")+"\n")
        file.close()

func load_payload()->Dictionary:
    if not FileAccess.file_exists(WIDTH_PAYLOAD_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(WIDTH_PAYLOAD_PATH))
    return parsed as Dictionary if parsed is Dictionary else {}

func capture_mode(viewport:SubViewport,context:String,index:int,mode:String)->Dictionary:
    var image:=viewport.get_texture().get_image()
    if image==null or image.is_empty():
        return {"state":"FAIL_CAPTURE"}
    var path="res://atmosphere-width-%s-%s-%02d.png" % [mode,context,index]
    if image.save_png(path)!=OK:
        return {"state":"FAIL_CAPTURE"}
    return {
        "state":"PASS",
        "path":path,
        "width":image.get_width(),
        "height":image.get_height(),
        "bytes":FileAccess.get_file_as_bytes(path).size()
    }

func fill_weather_width_ribbons(lines:Array,camera:Camera3D)->Dictionary:
    if lines.is_empty():
        return {"state":"FAIL_EMPTY_WEATHER_FIELD"}
    weather_mesh.clear_surfaces()
    weather_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES,weather_material)
    var width_min:=INF
    var width_max:=0.0
    var width_sum:=0.0
    var opacity_min:=1.0
    var opacity_max:=0.0
    var opacity_sum:=0.0
    var maximum_width_residual:=0.0
    var measured_width_count:=0

    for line_value in lines:
        var row=line_value as Dictionary
        var opacity=float(row.get("opacity",-1.0))
        var width_px=float(row.get("source_width_px",-1.0))
        if opacity<0.0 or opacity>1.0:
            return {"state":"FAIL_INVALID_SOURCE_STREAK_OPACITY","streak_id":row.get("id","UNKNOWN"),"opacity":opacity}
        if width_px<=0.0:
            return {"state":"FAIL_INVALID_SOURCE_STREAK_WIDTH","streak_id":row.get("id","UNKNOWN"),"source_width_px":width_px}

        var tail=row["tail_xy"] as Array
        var head=row["head_xy"] as Array
        var height=float(row["presentation_height_m"])
        var a_world:=gvec([float(tail[0]),float(tail[1]),height])
        var b_world:=gvec([float(head[0]),float(head[1]),height])
        if camera.is_position_behind(a_world) or camera.is_position_behind(b_world):
            return {"state":"FAIL_SOURCE_STREAK_BEHIND_CAMERA","streak_id":row.get("id","UNKNOWN")}

        var a_screen:=camera.unproject_position(a_world)
        var b_screen:=camera.unproject_position(b_world)
        var screen_delta:=b_screen-a_screen
        if screen_delta.length()<=0.000001:
            return {"state":"FAIL_DEGENERATE_PROJECTED_STREAK","streak_id":row.get("id","UNKNOWN")}
        var screen_side:=Vector2(-screen_delta.y,screen_delta.x).normalized()
        var half_screen:=screen_side*(width_px*0.5)
        var a_depth:=-camera.to_local(a_world).z
        var b_depth:=-camera.to_local(b_world).z
        if a_depth<=0.0 or b_depth<=0.0:
            return {"state":"FAIL_INVALID_PROJECTED_DEPTH","streak_id":row.get("id","UNKNOWN")}

        var a_minus:=camera.project_position(a_screen-half_screen,a_depth)
        var a_plus:=camera.project_position(a_screen+half_screen,a_depth)
        var b_minus:=camera.project_position(b_screen-half_screen,b_depth)
        var b_plus:=camera.project_position(b_screen+half_screen,b_depth)

        var measured_a:=camera.unproject_position(a_minus).distance_to(camera.unproject_position(a_plus))
        var measured_b:=camera.unproject_position(b_minus).distance_to(camera.unproject_position(b_plus))
        maximum_width_residual=maxf(maximum_width_residual,maxf(absf(measured_a-width_px),absf(measured_b-width_px)))
        measured_width_count+=1

        var vertex_color:=Color(1.0,1.0,1.0,opacity)
        weather_mesh.surface_set_color(vertex_color)
        weather_mesh.surface_add_vertex(a_minus)
        weather_mesh.surface_set_color(vertex_color)
        weather_mesh.surface_add_vertex(b_minus)
        weather_mesh.surface_set_color(vertex_color)
        weather_mesh.surface_add_vertex(b_plus)
        weather_mesh.surface_set_color(vertex_color)
        weather_mesh.surface_add_vertex(a_minus)
        weather_mesh.surface_set_color(vertex_color)
        weather_mesh.surface_add_vertex(b_plus)
        weather_mesh.surface_set_color(vertex_color)
        weather_mesh.surface_add_vertex(a_plus)

        width_min=minf(width_min,width_px)
        width_max=maxf(width_max,width_px)
        width_sum+=width_px
        opacity_min=minf(opacity_min,opacity)
        opacity_max=maxf(opacity_max,opacity)
        opacity_sum+=opacity

    weather_mesh.surface_end()
    return {
        "state":"PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS",
        "presentation_mode":WIDTH_PRESENTATION_MODE,
        "node_instance_id":weather_node.get_instance_id(),
        "mesh_instance_id":weather_mesh.get_instance_id(),
        "material_instance_id":weather_material.get_instance_id(),
        "surface_count":weather_mesh.get_surface_count(),
        "streak_count":lines.size(),
        "source_width_min_px":width_min,
        "source_width_mean_px":width_sum/float(lines.size()),
        "source_width_max_px":width_max,
        "maximum_projected_width_residual_px":maximum_width_residual,
        "measured_width_count":measured_width_count,
        "source_opacity_min":opacity_min,
        "source_opacity_mean":opacity_sum/float(lines.size()),
        "source_opacity_max":opacity_max,
        "source_opacity_consumed":true
    }

func _initialize()->void:
    receipt={
        "schema":"axm.environment-current-world-weather-width-observation/v0.1",
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "promotion_effect":"NONE",
        "parent_variant_head":WIDTH_PARENT_HEAD,
        "presentation_mode":WIDTH_PRESENTATION_MODE,
        "truth_boundary":"Same-process fixed-view A/B of the inherited renderer-default Weather line presentation versus camera-projected ribbon geometry carrying the exact source-authored screen-pixel widths. This proves only the two declared 1100x720 cameras and all 17 retained source states. It does not prove physical weather dimensions, arbitrary camera/resolution behavior, wall-clock playback, target-device performance, gameplay visibility, final Art Direction, CANON, or mastery."
    }
    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!=WIDTH_SCHEMA:
        fail("missing or invalid current-world Weather width payload")
        return
    if String(payload.get("status",""))!=WIDTH_STATUS:
        fail("Weather width structure must PASS before target-host observation")
        return
    if String(payload.get("parent_variant_head",""))!=WIDTH_PARENT_HEAD:
        fail("Weather width parent variant head drift")
        return
    var states=payload["states"] as Array
    if states.size()!=17:
        fail("Weather width target-host proof requires exact 17-state sequence")
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
        fail("current-world rear-tree culling target drift")
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

    var samples=[]
    for row_value in states:
        var row=row_value as Dictionary
        var scene=row["scene"] as Dictionary
        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        var contexts={}
        for context_value in WIDTH_CONTEXTS:
            var context=String(context_value)
            configure_camera(camera,scene,context)
            await settle()

            var control_weather=fill_weather(scene["weather_lines"] as Array)
            if control_weather.get("state")!="PASS_SOURCE_STREAK_OPACITY_CONSUMED":
                fail("control Weather update failed at sample %s / %s" % [row["index"],context])
                return
            await settle()
            var control_stats=runtime_stats()
            var control_shot=capture_mode(viewport,context,int(row["index"]),"control")
            if control_shot.get("state")!="PASS":
                fail("control capture failed at sample %s / %s" % [row["index"],context])
                return

            var candidate_weather=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
            if candidate_weather.get("state")!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
                fail("candidate Weather width update failed at sample %s / %s: %s" % [row["index"],context,candidate_weather])
                return
            if float(candidate_weather.get("maximum_projected_width_residual_px",999.0))>WIDTH_RESIDUAL_TOL_PX:
                fail("candidate projected source-width residual exceeded tolerance at sample %s / %s" % [row["index"],context])
                return
            await settle()
            var candidate_stats=runtime_stats()
            var candidate_shot=capture_mode(viewport,context,int(row["index"]),"candidate")
            if candidate_shot.get("state")!="PASS":
                fail("candidate capture failed at sample %s / %s" % [row["index"],context])
                return

            contexts[context]={
                "control":{"weather_update":control_weather,"runtime":control_stats,"capture":control_shot},
                "candidate":{"weather_update":candidate_weather,"runtime":candidate_stats,"capture":candidate_shot}
            }

        samples.append({
            "index":row["index"],
            "time_s":row["time_s"],
            "weather_field_digest":row["weather_field_digest"],
            "weather_width_profile_digest":row["weather_width_profile_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "sapling_update":sapling_update,
            "static_source_meshes":static_source_stats,
            "contexts":contexts
        })

    receipt["state"]="PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION"
    receipt["receiving_head"]=payload["receiving_head"]
    receipt["parent_variant_head"]=payload["parent_variant_head"]
    receipt["weather_variant_head"]=payload["weather_variant_head"]
    receipt["weather_variant_seed"]=payload["weather_variant_seed"]
    receipt["weather_variant_layout_digest"]=payload["weather_variant_layout_digest"]
    receipt["source_width_profile_digest"]=payload["source_width_profile_digest"]
    receipt["source_width_summary"]=payload["source_width_summary"]
    receipt["static_source_meshes"]=static_source_stats
    receipt["samples"]=samples
    receipt["godot_version"]=Engine.get_version_info()
    write_receipt()
    quit(0)
