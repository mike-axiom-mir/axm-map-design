extends SceneTree

const SCENE_PATH := "res://generated/scene_runtime.json"
const SETTLE_FRAMES := 16
const VALID_VARIANTS := ["baseline", "candidate"]

var receipt := {
    "schema":"axm.environment-east-tree-runtime-observation/v0.1",
    "proof_runtime":"Godot 4.7.2 GL Compatibility",
    "promotion_effect":"NONE",
    "truth_boundary":"Comparative proof-host counters for the exact east-foreground proxy/source A/B. These counters do not establish target-device FPS/GPU time, final budgets, visual acceptance, gameplay, CANON, or mastery."
}

func output_path(variant:String)->String:
    return "res://runtime-east-tree-%s.json" % variant

func write_receipt(variant:String)->void:
    var file:=FileAccess.open(output_path(variant),FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(receipt,"  ")+"\n")
        file.close()

func fail(variant:String,message:String)->void:
    receipt["state"]="FAIL_INFRASTRUCTURE"
    receipt["failure"]=message
    receipt["godot_version"]=Engine.get_version_info()
    write_receipt(variant)
    push_error(message)
    quit(1)

func load_scene_data()->Dictionary:
    if not FileAccess.file_exists(SCENE_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(SCENE_PATH))
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

func source_material_for(kind:String)->StandardMaterial3D:
    var material:=StandardMaterial3D.new()
    material.roughness=0.82
    if kind=="nature-source":
        material.albedo_color=Color(0.20,0.43,0.20,1.0)
    else:
        material.albedo_color=Color(0.45,0.45,0.45,1.0)
    material.cull_mode=BaseMaterial3D.CULL_DISABLED
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

func add_source_mesh(root3d:Node3D,source:Dictionary,fallback_name:String)->Dictionary:
    var vertices=source["vertices_source_xyz_m"] as Array
    var triangles=source["triangles"] as Array
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
    node.name=String(source.get("asset_id",fallback_name))
    node.mesh=mesh
    node.material_override=source_material_for(String(source.get("kind","nature-source")))
    root3d.add_child(node)
    return {
        "asset_id":String(source.get("asset_id",fallback_name)),
        "vertices":vertices.size(),
        "triangles":triangles.size(),
        "surfaces":mesh.get_surface_count()
    }

func add_sapling(root3d:Node3D,data:Dictionary)->Dictionary:
    var source=Dictionary((data["sapling"] as Dictionary).duplicate(true))
    source["kind"]="nature-source"
    return add_source_mesh(root3d,source,"source-sapling")

func add_additional_source_meshes(root3d:Node3D,data:Dictionary)->Array:
    var results:Array=[]
    for source in data.get("additional_source_meshes",[]) as Array:
        results.append(add_source_mesh(root3d,source as Dictionary,"source-mesh"))
    return results

func add_weather(root3d:Node3D,data:Dictionary)->Dictionary:
    var lines=data["weather_lines"] as Array
    var mesh:=ImmediateMesh.new()
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(0.55,0.77,1.0,0.62)
    material.emission_enabled=true
    material.emission=Color(0.25,0.48,0.78,1.0)
    material.emission_energy_multiplier=0.85
    material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
    material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
    mesh.surface_begin(Mesh.PRIMITIVE_LINES,material)
    for line in lines:
        var row=line as Dictionary
        var a=row["tail_xy"] as Array
        var b=row["head_xy"] as Array
        var h=float(row["presentation_height_m"])
        mesh.surface_add_vertex(gvec([float(a[0]),float(a[1]),h]))
        mesh.surface_add_vertex(gvec([float(b[0]),float(b[1]),h]))
    mesh.surface_end()
    var node:=MeshInstance3D.new()
    node.name="source-weather-visual-field"
    node.mesh=mesh
    root3d.add_child(node)
    return {"streaks":lines.size(),"surfaces":mesh.get_surface_count()}

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

func runtime_stats()->Dictionary:
    return {
        "objects_in_frame":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
        "primitives_in_frame":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
        "draw_calls_in_frame":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
        "texture_mem_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED),
        "buffer_mem_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_BUFFER_MEM_USED)
    }

func settle()->void:
    for _i in range(SETTLE_FRAMES):
        await process_frame

func configure_camera(camera:Camera3D,data:Dictionary,context:String)->Dictionary:
    var camera_data=(data["cameras"] as Dictionary)[context] as Dictionary
    camera.fov=float(camera_data["fov_deg"])
    camera.look_at_from_position(gvec(camera_data["position_source_xyz_m"] as Array),gvec(camera_data["target_source_xyz_m"] as Array),Vector3.UP)
    return camera_data

func capture(viewport:SubViewport,variant:String,context:String)->Dictionary:
    var image:=viewport.get_texture().get_image()
    if image==null or image.is_empty():
        return {"state":"FAIL_CAPTURE"}
    var path="res://runtime-east-tree-%s-%s.png" % [variant,context]
    if image.save_png(path)!=OK:
        return {"state":"FAIL_CAPTURE"}
    return {
        "state":"PASS",
        "width":image.get_width(),
        "height":image.get_height(),
        "bytes":FileAccess.get_file_as_bytes(path).size()
    }

func _initialize()->void:
    var user_args:=OS.get_cmdline_user_args()
    var variant=String(user_args[0]) if user_args.size()>0 else ""
    if not VALID_VARIANTS.has(variant):
        fail(variant if variant!="" else "invalid","missing or unsupported east-tree runtime variant")
        return
    var data:=load_scene_data()
    if data.is_empty():
        fail(variant,"missing or invalid exact scene payload")
        return

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
    var sapling_stats:=add_sapling(root3d,data)
    var additional_stats:=add_additional_source_meshes(root3d,data)
    var weather_stats:=add_weather(root3d,data)

    var camera:=Camera3D.new()
    camera.near=0.05
    camera.far=120.0
    root3d.add_child(camera)
    camera.make_current()

    var contexts={}
    for context in ["path_eye","elevated_oblique"]:
        var camera_data:=configure_camera(camera,data,context)
        await settle()
        var shot:=capture(viewport,variant,context)
        if shot.get("state")!="PASS":
            fail(variant,"capture failed for %s" % context)
            return
        contexts[context]={
            "state":"PASS",
            "runtime":runtime_stats(),
            "capture":shot,
            "camera":camera_data
        }

    receipt["state"]="PASS_SCOPED_EAST_TREE_RUNTIME_OBSERVATION"
    receipt["variant"]=variant
    receipt["receiving_head"]=String(data.get("receiving_head",""))
    receipt["scene_digest"]=String(data.get("scene_digest",""))
    receipt["godot_version"]=Engine.get_version_info()
    receipt["contexts"]=contexts
    receipt["sapling"]=sapling_stats
    receipt["additional_source_meshes"]=additional_stats
    receipt["weather"]=weather_stats
    receipt["proxy_count"]=(data["items"] as Array).size()
    receipt["performance_acceptance"]="COMPARATIVE_PROOF_HOST_ONLY_NO_TARGET_BUDGET"
    write_receipt(variant)
    print("AXM EAST TREE RUNTIME ",JSON.stringify(receipt))
    quit(0)
