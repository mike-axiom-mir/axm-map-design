extends SceneTree

const SEQUENCE_PATH := "res://generated/weather_sequence.json"
const VALID_MODES := ["rebuild_control", "reuse_single_mesh"]
const CONTEXTS := ["path_eye", "elevated_oblique"]
const SETTLE_FRAMES := 3
const STRESS_CYCLES := 48

var receipt := {
    "schema":"axm.environment-weather-dynamic-runtime-observation/v0.1",
    "proof_runtime":"Godot 4.7.2 GL Compatibility",
    "promotion_effect":"NONE",
    "truth_boundary":"Same-process comparative proof for the exact retained nine-state visual-only Weather sequence. rebuild_control is a synthetic reconstruction control, not an existing product implementation. reuse_single_mesh proves only stable proof-host resource identity/counters and measured CPU-side submission observations; it does not establish target-device FPS, GPU frame time, physical weather, final art direction, gameplay, CANON, or mastery."
}

var weather_node:MeshInstance3D = null
var weather_mesh:ImmediateMesh = null
var weather_material:StandardMaterial3D = null
var created_nodes := 0
var created_meshes := 0
var created_materials := 0

func output_path(mode:String)->String:
    return "res://weather-dynamic-runtime-%s.json" % mode

func write_receipt(mode:String)->void:
    var file:=FileAccess.open(output_path(mode),FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(receipt,"  ")+"\n")
        file.close()

func fail(mode:String,message:String)->void:
    receipt["state"]="FAIL_INFRASTRUCTURE"
    receipt["failure"]=message
    receipt["godot_version"]=Engine.get_version_info()
    write_receipt(mode)
    push_error(message)
    quit(1)

func load_sequence()->Dictionary:
    if not FileAccess.file_exists(SEQUENCE_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(SEQUENCE_PATH))
    return parsed as Dictionary if parsed is Dictionary else {}

func gvec(values:Array)->Vector3:
    return Vector3(float(values[0]),float(values[2]),-float(values[1]))

func material_for(kind:String)->StandardMaterial3D:
    var material:=StandardMaterial3D.new()
    material.roughness=0.88
    if kind=="map-surface":
        material.albedo_color=Color(0.43,0.40,0.34,1.0)
    elif kind=="building-proxy":
        material.albedo_color=Color(0.34,0.38,0.44,1.0)
    elif kind=="nature-proxy":
        material.albedo_color=Color(0.27,0.42,0.25,1.0)
    elif kind=="object-proxy":
        material.albedo_color=Color(0.48,0.31,0.18,1.0)
    else:
        material.albedo_color=Color(0.45,0.45,0.45,1.0)
    return material

func add_proxy(root3d:Node3D,item:Dictionary)->void:
    var node:=MeshInstance3D.new()
    node.name=String(item.get("asset_id","proxy"))
    var mesh:=BoxMesh.new()
    var size=item["size_m"] as Array
    mesh.size=Vector3(float(size[0]),float(size[2]),float(size[1]))
    node.mesh=mesh
    node.position=gvec(item["position_m"] as Array)
    node.rotation.y=deg_to_rad(float(item.get("rotation_deg",0.0)))
    node.material_override=material_for(String(item.get("kind","unknown")))
    root3d.add_child(node)

func add_path(root3d:Node3D,data:Dictionary)->void:
    var path=data["readable_path"] as Dictionary
    var node:=MeshInstance3D.new()
    node.name="readable-path-observation-overlay"
    var mesh:=BoxMesh.new()
    var width=float(path["x_max"])-float(path["x_min"])
    var depth=float(path["y_max"])-float(path["y_min"])
    mesh.size=Vector3(width,0.035,depth)
    node.mesh=mesh
    var sx=(float(path["x_min"])+float(path["x_max"]))*0.5
    var sy=(float(path["y_min"])+float(path["y_max"]))*0.5
    node.position=gvec([sx,sy,0.035])
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(0.20,0.38,0.52,0.42)
    material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
    material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
    node.material_override=material
    root3d.add_child(node)

func add_sapling(root3d:Node3D,data:Dictionary)->void:
    var sapling=data["sapling"] as Dictionary
    var vertices=sapling["vertices_source_xyz_m"] as Array
    var triangles=sapling["triangles"] as Array
    var st:=SurfaceTool.new()
    st.begin(Mesh.PRIMITIVE_TRIANGLES)
    for tri in triangles:
        var row=tri as Array
        st.add_vertex(gvec(vertices[int(row[0])] as Array))
        st.add_vertex(gvec(vertices[int(row[1])] as Array))
        st.add_vertex(gvec(vertices[int(row[2])] as Array))
    st.generate_normals()
    var mesh:=st.commit()
    var node:=MeshInstance3D.new()
    node.name=String(sapling.get("asset_id","source-sapling"))
    node.mesh=mesh
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(0.20,0.43,0.20,1.0)
    material.roughness=0.82
    material.cull_mode=BaseMaterial3D.CULL_DISABLED
    node.material_override=material
    root3d.add_child(node)

func add_environment(root3d:Node3D)->void:
    var env:=Environment.new()
    env.background_mode=Environment.BG_COLOR
    env.background_color=Color(0.055,0.07,0.09,1.0)
    env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color=Color(0.56,0.60,0.67,1.0)
    env.ambient_light_energy=0.62
    var world:=WorldEnvironment.new()
    world.environment=env
    root3d.add_child(world)
    var sun:=DirectionalLight3D.new()
    sun.shadow_enabled=true
    sun.light_energy=1.55
    sun.rotation_degrees=Vector3(-52,-35,0)
    root3d.add_child(sun)

func make_weather_material()->StandardMaterial3D:
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(0.55,0.77,1.0,0.62)
    material.emission_enabled=true
    material.emission=Color(0.25,0.48,0.78,1.0)
    material.emission_energy_multiplier=0.85
    material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
    material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
    created_materials+=1
    return material

func fill_weather_mesh(mesh:ImmediateMesh,material:StandardMaterial3D,lines:Array)->void:
    mesh.clear_surfaces()
    mesh.surface_begin(Mesh.PRIMITIVE_LINES,material)
    for line in lines:
        var row=line as Dictionary
        var a=row["tail_xy"] as Array
        var b=row["head_xy"] as Array
        var h=float(row["presentation_height_m"])
        mesh.surface_add_vertex(gvec([float(a[0]),float(a[1]),h]))
        mesh.surface_add_vertex(gvec([float(b[0]),float(b[1]),h]))
    mesh.surface_end()

func apply_weather(root3d:Node3D,mode:String,lines:Array)->Dictionary:
    var start_usec:=Time.get_ticks_usec()
    if mode=="rebuild_control":
        if weather_node!=null:
            weather_node.free()
        weather_material=make_weather_material()
        weather_mesh=ImmediateMesh.new()
        created_meshes+=1
        fill_weather_mesh(weather_mesh,weather_material,lines)
        weather_node=MeshInstance3D.new()
        created_nodes+=1
        weather_node.name="source-weather-visual-field"
        weather_node.mesh=weather_mesh
        root3d.add_child(weather_node)
    else:
        if weather_node==null:
            weather_material=make_weather_material()
            weather_mesh=ImmediateMesh.new()
            created_meshes+=1
            weather_node=MeshInstance3D.new()
            created_nodes+=1
            weather_node.name="source-weather-visual-field"
            weather_node.mesh=weather_mesh
            root3d.add_child(weather_node)
        fill_weather_mesh(weather_mesh,weather_material,lines)
    var elapsed:=Time.get_ticks_usec()-start_usec
    return {
        "submission_usec":elapsed,
        "node_instance_id":weather_node.get_instance_id(),
        "mesh_instance_id":weather_mesh.get_instance_id(),
        "material_instance_id":weather_material.get_instance_id(),
        "surface_count":weather_mesh.get_surface_count(),
        "streak_count":lines.size()
    }

func runtime_stats()->Dictionary:
    return {
        "objects_in_frame":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
        "primitives_in_frame":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
        "draw_calls_in_frame":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
        "texture_mem_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED),
        "buffer_mem_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_BUFFER_MEM_USED)
    }

func settle(frames:int=SETTLE_FRAMES)->void:
    for _i in range(frames):
        await process_frame

func configure_camera(camera:Camera3D,data:Dictionary,context:String)->void:
    var camera_data=(data["cameras"] as Dictionary)[context] as Dictionary
    camera.fov=float(camera_data["fov_deg"])
    camera.look_at_from_position(gvec(camera_data["position_source_xyz_m"] as Array),gvec(camera_data["target_source_xyz_m"] as Array),Vector3.UP)

func capture(viewport:SubViewport,mode:String,context:String,index:int)->Dictionary:
    var image:=viewport.get_texture().get_image()
    if image==null or image.is_empty():
        return {"state":"FAIL_CAPTURE"}
    var path="res://weather-dynamic-%s-%s-%02d.png" % [mode,context,index]
    if image.save_png(path)!=OK:
        return {"state":"FAIL_CAPTURE"}
    return {
        "state":"PASS",
        "path":path,
        "width":image.get_width(),
        "height":image.get_height(),
        "bytes":FileAccess.get_file_as_bytes(path).size()
    }

func summarize(values:Array)->Dictionary:
    if values.is_empty():
        return {"count":0,"min_usec":0,"median_usec":0,"p95_usec":0,"max_usec":0,"total_usec":0}
    var ordered=values.duplicate()
    ordered.sort()
    var count=ordered.size()
    var median_index=int(floor(float(count-1)*0.5))
    var p95_index=int(ceil(float(count)*0.95))-1
    p95_index=clamp(p95_index,0,count-1)
    var total:=0
    for value in ordered:
        total+=int(value)
    return {
        "count":count,
        "min_usec":int(ordered[0]),
        "median_usec":int(ordered[median_index]),
        "p95_usec":int(ordered[p95_index]),
        "max_usec":int(ordered[count-1]),
        "total_usec":total
    }

func _initialize()->void:
    var args:=OS.get_cmdline_user_args()
    var mode=String(args[0]) if args.size()>0 else ""
    if not VALID_MODES.has(mode):
        fail(mode if mode!="" else "invalid","missing or unsupported Weather update mode")
        return
    var sequence:=load_sequence()
    if sequence.is_empty() or String(sequence.get("schema",""))!="axm.environment-weather-sequence-proof-evidence/v0.1":
        fail(mode,"missing or invalid exact Weather sequence payload")
        return
    if String(sequence.get("status",""))!="PASS":
        fail(mode,"Weather sequence must PASS before Runtime observation")
        return
    var states=sequence["states"] as Array
    if states.size()!=9:
        fail(mode,"Runtime proof requires exact nine-state Weather sequence")
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
    add_sapling(root3d,data)
    var camera:=Camera3D.new()
    camera.near=0.05
    camera.far=120.0
    root3d.add_child(camera)
    camera.make_current()

    var evidence_samples=[]
    var evidence_submit=[]
    for row_value in states:
        var row=row_value as Dictionary
        var scene=row["scene"] as Dictionary
        var update=apply_weather(root3d,mode,scene["weather_lines"] as Array)
        evidence_submit.append(update["submission_usec"])
        await settle()
        var contexts={}
        for context in CONTEXTS:
            configure_camera(camera,scene,String(context))
            await settle()
            var stats=runtime_stats()
            var shot=capture(viewport,mode,String(context),int(row["index"]))
            if shot.get("state")!="PASS":
                fail(mode,"capture failed for %s sample %s" % [context,row["index"]])
                return
            contexts[String(context)]={"runtime":stats,"capture":shot}
        evidence_samples.append({
            "index":row["index"],
            "time_s":row["time_s"],
            "field_digest":row["field_digest"],
            "update":update,
            "contexts":contexts
        })

    var stress_submit=[]
    var cycle_memory=[]
    for cycle in range(STRESS_CYCLES):
        for row_value in states:
            var row=row_value as Dictionary
            var scene=row["scene"] as Dictionary
            var update=apply_weather(root3d,mode,scene["weather_lines"] as Array)
            stress_submit.append(update["submission_usec"])
        await settle()
        var stats=runtime_stats()
        cycle_memory.append({
            "cycle":cycle,
            "buffer_mem_bytes":stats["buffer_mem_bytes"],
            "texture_mem_bytes":stats["texture_mem_bytes"],
            "draw_calls_in_frame":stats["draw_calls_in_frame"],
            "primitives_in_frame":stats["primitives_in_frame"],
            "objects_in_frame":stats["objects_in_frame"]
        })

    receipt["state"]="PASS_SCOPED_SAME_PROCESS_WEATHER_UPDATE_OBSERVATION"
    receipt["mode"]=mode
    receipt["receiving_head"]=String(sequence.get("receiving_head",""))
    receipt["environment_base_head"]=String(sequence.get("environment_base_head",""))
    receipt["sequence_digest"]=String(sequence.get("sequence_digest",""))
    receipt["weather_source"]=sequence["weather_source"]
    receipt["sampling_schedule_s"]=sequence["sampling_schedule_s"]
    receipt["static_receiving_state_digest"]=String(sequence.get("static_receiving_state_digest",""))
    receipt["godot_version"]=Engine.get_version_info()
    receipt["evidence_samples"]=evidence_samples
    receipt["stress"]={
        "cycles":STRESS_CYCLES,
        "updates":stress_submit.size(),
        "submission":summarize(stress_submit),
        "cycle_memory":cycle_memory
    }
    receipt["evidence_submission"]=summarize(evidence_submit)
    receipt["resource_creations"]={
        "weather_nodes":created_nodes,
        "weather_meshes":created_meshes,
        "weather_materials":created_materials
    }
    receipt["update_semantics"]=(
        "SYNTHETIC_REBUILD_CONTROL_FREES_AND_RECREATES_NODE_MESH_MATERIAL_PER_STATE" if mode=="rebuild_control" else
        "CANDIDATE_REUSES_ONE_NODE_ONE_IMMEDIATEMESH_ONE_MATERIAL_AND_REBUILDS_ONLY_ITS_SINGLE_LINE_SURFACE"
    )
    receipt["performance_acceptance"]="PROOF_HOST_COMPARATIVE_ONLY_NO_TARGET_BUDGET"
    write_receipt(mode)
    print("AXM WEATHER DYNAMIC RUNTIME ",JSON.stringify(receipt))
    quit(0)
