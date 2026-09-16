extends SceneTree

const SCENE_PATH := "res://generated/scene_runtime.json"
const VALID_MODES := ["per_mesh_material_control", "shared_nature_material"]
const CONTEXTS := ["path_eye", "elevated_oblique"]
const SETTLE_FRAMES := 12

var shared_nature_material:StandardMaterial3D = null
var created_nature_materials := 0

var receipt := {
    "schema":"axm.environment-nature-material-runtime-observation/v0.1",
    "proof_runtime":"Godot 4.7.2 GL Compatibility",
    "promotion_effect":"NONE",
    "truth_boundary":"Same-process comparative proof for the exact accepted Building plus three-source Nature Environment candidate. per_mesh_material_control intentionally creates one visually identical Nature StandardMaterial3D per Nature mesh in each observation context. shared_nature_material reuses one immutable Nature StandardMaterial3D across all Nature meshes and both contexts. This proves only proof-host material-resource sharing and exact retained image/counter equivalence; it does not establish target-device FPS, GPU timing, VRAM, production residency, final materials, LOD, streaming, gameplay, CANON, or mastery."
}

func output_path(mode:String)->String:
    return "res://nature-material-runtime-%s.json" % mode

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

func new_source_material(kind:String)->StandardMaterial3D:
    var material:=StandardMaterial3D.new()
    material.roughness=0.82
    if kind=="nature-source":
        material.albedo_color=Color(0.20,0.43,0.20,1.0)
        material.cull_mode=BaseMaterial3D.CULL_DISABLED
        created_nature_materials+=1
    else:
        material.albedo_color=Color(0.45,0.45,0.45,1.0)
    return material

func source_material_for(kind:String,mode:String)->StandardMaterial3D:
    if kind!="nature-source" or mode=="per_mesh_material_control":
        return new_source_material(kind)
    if shared_nature_material==null:
        shared_nature_material=new_source_material(kind)
    return shared_nature_material

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
    var width:=float(path["x_max"])-float(path["x_min"])
    var depth:=float(path["y_max"])-float(path["y_min"])
    mesh.size=Vector3(width,0.035,depth)
    node.mesh=mesh
    var sx:=(float(path["x_min"])+float(path["x_max"]))*0.5
    var sy:=(float(path["y_min"])+float(path["y_max"]))*0.5
    node.position=gvec([sx,sy,0.035])
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(0.20,0.38,0.52,0.42)
    material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
    material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
    node.material_override=material
    root3d.add_child(node)

func add_source_mesh(root3d:Node3D,source:Dictionary,fallback_name:String,mode:String)->Dictionary:
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
    var kind:=String(source.get("kind","nature-source"))
    var source_material:=source_material_for(kind,mode)
    node.material_override=source_material
    root3d.add_child(node)
    return {
        "asset_id":String(source.get("asset_id",fallback_name)),
        "kind":kind,
        "vertices":vertices.size(),
        "triangles":triangles.size(),
        "proof_culling":String(source.get("proof_render_culling","")),
        "material_instance_id":source_material.get_instance_id()
    }

func add_sapling(root3d:Node3D,data:Dictionary,mode:String)->Dictionary:
    var sapling=data["sapling"] as Dictionary
    var source=Dictionary(sapling.duplicate(true))
    source["kind"]="nature-source"
    return add_source_mesh(root3d,source,"source-sapling",mode)

func add_additional_source_meshes(root3d:Node3D,data:Dictionary,mode:String)->Array:
    var results:Array=[]
    var sources=data.get("additional_source_meshes",[]) as Array
    for source in sources:
        results.append(add_source_mesh(root3d,source as Dictionary,"source-mesh",mode))
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
    return {"streaks":lines.size(),"presentation":data["weather_presentation"]}

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

func settle(frames:int=SETTLE_FRAMES)->void:
    for _i in range(frames):
        await process_frame

func make_viewport(context:String,data:Dictionary,mode:String)->Dictionary:
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
    var sapling_stats:=add_sapling(root3d,data,mode)
    var additional_source_stats:=add_additional_source_meshes(root3d,data,mode)
    var weather_stats:=add_weather(root3d,data)
    var camera:=Camera3D.new()
    camera.near=0.05
    camera.far=120.0
    root3d.add_child(camera)
    camera.make_current()
    var camera_data=(data["cameras"] as Dictionary)[context] as Dictionary
    camera.fov=float(camera_data["fov_deg"])
    camera.look_at_from_position(gvec(camera_data["position_source_xyz_m"] as Array),gvec(camera_data["target_source_xyz_m"] as Array),Vector3.UP)
    return {"viewport":viewport,"sapling":sapling_stats,"additional_source_meshes":additional_source_stats,"weather":weather_stats,"camera":camera_data}

func capture_context(context:String,data:Dictionary,mode:String)->Dictionary:
    var setup:=make_viewport(context,data,mode)
    var viewport:=setup["viewport"] as SubViewport
    await settle()
    var stats:=runtime_stats()
    var image:=viewport.get_texture().get_image()
    if image==null or image.is_empty():
        return {"state":"FAIL_CAPTURE"}
    var path="res://nature-material-%s-%s.png" % [mode,context]
    if image.save_png(path)!=OK:
        return {"state":"FAIL_CAPTURE"}
    var source_rows:Array=[setup["sapling"]]
    source_rows.append_array(setup["additional_source_meshes"] as Array)
    var nature_rows:Array=[]
    var nature_material_ids:Array=[]
    for row_value in source_rows:
        var row=row_value as Dictionary
        if String(row.get("kind",""))=="nature-source":
            nature_rows.append(row)
            nature_material_ids.append(int(row["material_instance_id"]))
    var unique_material_ids:Array=[]
    for material_id in nature_material_ids:
        if not unique_material_ids.has(material_id):
            unique_material_ids.append(material_id)
    var result={
        "state":"PASS",
        "capture":{"width":image.get_width(),"height":image.get_height(),"bytes":FileAccess.get_file_as_bytes(path).size(),"path":path},
        "camera":setup["camera"],
        "runtime":stats,
        "sapling":setup["sapling"],
        "additional_source_meshes":setup["additional_source_meshes"],
        "weather":setup["weather"],
        "proxy_count":(data["items"] as Array).size(),
        "nature_source_mesh_count":nature_rows.size(),
        "nature_material_instance_ids":nature_material_ids,
        "unique_nature_material_instance_ids":unique_material_ids
    }
    viewport.queue_free()
    await settle(2)
    return result

func _initialize()->void:
    var args:=OS.get_cmdline_user_args()
    var mode:=String(args[0]) if args.size()>0 else ""
    if not VALID_MODES.has(mode):
        fail(mode if mode!="" else "invalid","missing or unsupported Nature material sharing mode")
        return
    var data:=load_scene_data()
    if data.is_empty():
        fail(mode,"missing or invalid exact scene payload")
        return
    var contexts={}
    for context in CONTEXTS:
        var row:=await capture_context(String(context),data,mode)
        if row.get("state")!="PASS":
            fail(mode,"Nature material runtime capture failed for %s" % context)
            return
        contexts[String(context)]=row
    receipt["state"]="PASS_TARGET_HOST_NATURE_MATERIAL_SHARING_OBSERVATION_READY"
    receipt["mode"]=mode
    receipt["godot_version"]=Engine.get_version_info()
    receipt["scene_digest"]=String(data.get("scene_digest",""))
    receipt["receiving_head"]=String(data.get("receiving_head",""))
    receipt["contexts"]=contexts
    receipt["created_nature_materials"]=created_nature_materials
    receipt["source_integration"]=data["source_integration"]
    receipt["weather_presentation"]=data["weather_presentation"]
    if data.has("environment_replacement"):
        receipt["environment_replacement"]=data["environment_replacement"]
    write_receipt(mode)
    print("AXM NATURE MATERIAL RUNTIME ",JSON.stringify(receipt))
    quit(0)
