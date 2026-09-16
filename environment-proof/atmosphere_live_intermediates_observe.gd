extends SceneTree

const PAYLOAD_PATH := "res://generated/atmosphere_live_intermediates.json"
const CONTEXTS := ["path_eye", "elevated_oblique"]
const SETTLE_FRAMES := 3

var receipt := {
    "schema":"axm.environment-atmosphere-live-intermediates-observation/v0.1",
    "proof_runtime":"Godot 4.7.2 GL Compatibility",
    "promotion_effect":"NONE",
    "truth_boundary":"Same-process visual observation of 17 exact source-evaluated synchronized Weather + Nature states through stable proof-host resources. This is not physical wind, wall-clock frame pacing, renderer interpolation, target-device performance, gameplay, final Art Direction, CANON, or mastery."
}

var weather_node:MeshInstance3D = null
var weather_mesh:ImmediateMesh = null
var weather_material:StandardMaterial3D = null
var sapling_node:MeshInstance3D = null
var sapling_mesh:ArrayMesh = null
var sapling_material:StandardMaterial3D = null

func write_receipt()->void:
    var file:=FileAccess.open("res://atmosphere-live-intermediates-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(receipt,"  ")+"\n")
        file.close()

func fail(message:String)->void:
    receipt["state"]="FAIL_INFRASTRUCTURE"
    receipt["failure"]=message
    receipt["godot_version"]=Engine.get_version_info()
    write_receipt()
    push_error(message)
    quit(1)

func load_payload()->Dictionary:
    if not FileAccess.file_exists(PAYLOAD_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(PAYLOAD_PATH))
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

func make_weather()->void:
    weather_material=StandardMaterial3D.new()
    weather_material.albedo_color=Color(0.55,0.77,1.0,0.62)
    weather_material.emission_enabled=true
    weather_material.emission=Color(0.25,0.48,0.78,1.0)
    weather_material.emission_energy_multiplier=0.85
    weather_material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
    weather_material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
    weather_mesh=ImmediateMesh.new()
    weather_node=MeshInstance3D.new()
    weather_node.name="source-weather-visual-field"
    weather_node.mesh=weather_mesh

func fill_weather(lines:Array)->Dictionary:
    weather_mesh.clear_surfaces()
    weather_mesh.surface_begin(Mesh.PRIMITIVE_LINES,weather_material)
    for line in lines:
        var row=line as Dictionary
        var a=row["tail_xy"] as Array
        var b=row["head_xy"] as Array
        var h=float(row["presentation_height_m"])
        weather_mesh.surface_add_vertex(gvec([float(a[0]),float(a[1]),h]))
        weather_mesh.surface_add_vertex(gvec([float(b[0]),float(b[1]),h]))
    weather_mesh.surface_end()
    return {
        "node_instance_id":weather_node.get_instance_id(),
        "mesh_instance_id":weather_mesh.get_instance_id(),
        "material_instance_id":weather_material.get_instance_id(),
        "surface_count":weather_mesh.get_surface_count(),
        "streak_count":lines.size()
    }

func make_sapling()->void:
    sapling_material=StandardMaterial3D.new()
    sapling_material.albedo_color=Color(0.20,0.43,0.20,1.0)
    sapling_material.roughness=0.82
    sapling_material.cull_mode=BaseMaterial3D.CULL_DISABLED
    sapling_mesh=ArrayMesh.new()
    sapling_node=MeshInstance3D.new()
    sapling_node.name="source-sapling-live-intermediate"
    sapling_node.mesh=sapling_mesh
    sapling_node.material_override=sapling_material

func fill_sapling(sapling:Dictionary)->Dictionary:
    sapling_mesh.clear_surfaces()
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
    st.commit(sapling_mesh)
    return {
        "node_instance_id":sapling_node.get_instance_id(),
        "mesh_instance_id":sapling_mesh.get_instance_id(),
        "material_instance_id":sapling_material.get_instance_id(),
        "surface_count":sapling_mesh.get_surface_count(),
        "source_vertex_count":vertices.size(),
        "source_triangle_count":triangles.size()
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

func capture(viewport:SubViewport,context:String,index:int)->Dictionary:
    var image:=viewport.get_texture().get_image()
    if image==null or image.is_empty():
        return {"state":"FAIL_CAPTURE"}
    var path="res://atmosphere-live-%s-%02d.png" % [context,index]
    if image.save_png(path)!=OK:
        return {"state":"FAIL_CAPTURE"}
    return {
        "state":"PASS",
        "path":path,
        "width":image.get_width(),
        "height":image.get_height(),
        "bytes":FileAccess.get_file_as_bytes(path).size()
    }

func _initialize()->void:
    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!="axm.environment-atmosphere-live-intermediates-evidence/v0.1":
        fail("missing or invalid dense atmosphere payload")
        return
    if String(payload.get("status",""))!="PASS_DENSE_INTERMEDIATE_SOURCE_SEQUENCE":
        fail("dense source sequence must PASS before target-host observation")
        return
    var states=payload["states"] as Array
    if states.size()!=17:
        fail("target-host proof requires exact 17-state dense sequence")
        return
    var first=states[0] as Dictionary
    var data=first["candidate_scene"] as Dictionary

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

    make_weather()
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
        var scene=row["candidate_scene"] as Dictionary
        var weather_update=fill_weather(scene["weather_lines"] as Array)
        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        await settle()
        var contexts={}
        for context in CONTEXTS:
            configure_camera(camera,scene,String(context))
            await settle()
            var stats=runtime_stats()
            var shot=capture(viewport,String(context),int(row["index"]))
            if shot.get("state")!="PASS":
                fail("capture failed for %s sample %s" % [context,row["index"]])
                return
            contexts[String(context)]={"runtime":stats,"capture":shot}
        samples.append({
            "index":row["index"],
            "time_s":row["time_s"],
            "sampling_role":row["sampling_role"],
            "weather_field_digest":row["weather_field_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "contexts":contexts
        })

    receipt["state"]="PASS_DENSE_INTERMEDIATE_LIVE_OBSERVATION"
    receipt["sequence_digest"]=payload["sequence_digest"]
    receipt["sampling_schedule_s"]=payload["sampling_schedule_s"]
    receipt["samples"]=samples
    receipt["godot_version"]=Engine.get_version_info()
    write_receipt()
    quit(0)
