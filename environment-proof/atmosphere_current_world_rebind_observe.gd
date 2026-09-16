extends SceneTree

const PAYLOAD_PATH := "res://generated/current_world_atmosphere_rebind.json"
const CONTEXTS := ["path_eye", "elevated_oblique"]
const SETTLE_FRAMES := 3
const WEATHER_OPACITY_MODE := "SOURCE_STREAK_OPACITY_VERTEX_ALPHA"
const DENSE_VFX_DONOR_HEAD := "6e386d513c0b2e821a89fb066b2e3ab58a0d6868"
const DENSE_VFX_SEQUENCE_DIGEST := "f7f2cad01184e8651bcc722b755a2f3c2292ca13e81c7399579d7f42e0c19b30"
const TARGET_REAR_ASSET_ID := "source:nature:east-rear-tree-neutral-001"

var receipt := {
    "schema":"axm.environment-current-world-atmosphere-rebind-observation/v0.1",
    "proof_runtime":"Godot 4.7.2 GL Compatibility",
    "promotion_effect":"NONE",
    "dense_vfx_donor_head":DENSE_VFX_DONOR_HEAD,
    "dense_vfx_sequence_digest":DENSE_VFX_SEQUENCE_DIGEST,
    "truth_boundary":"Same-process visual observation of the exact 17-state visual-only Weather + sapling sequence rebound into the current migrated-rear-tree Map world. This does not prove physical weather, wall-clock pacing, renderer interpolation, source line-width fidelity, deformation for other vegetation, target-device performance, gameplay, final Art Direction, CANON, or mastery."
}

var weather_node:MeshInstance3D = null
var weather_mesh:ImmediateMesh = null
var weather_material:StandardMaterial3D = null
var sapling_node:MeshInstance3D = null
var sapling_mesh:ArrayMesh = null
var sapling_material:StandardMaterial3D = null

func write_receipt()->void:
    var file:=FileAccess.open("res://atmosphere-current-world-rebind-runtime.json",FileAccess.WRITE)
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

func source_material_for(kind:String,cull_back:bool=false)->StandardMaterial3D:
    var material:=StandardMaterial3D.new()
    material.roughness=0.82
    if kind=="nature-source":
        material.albedo_color=Color(0.20,0.43,0.20,1.0)
    elif kind=="building-source":
        material.albedo_color=Color(0.34,0.38,0.44,1.0)
    else:
        material.albedo_color=Color(0.45,0.45,0.45,1.0)
    material.cull_mode=BaseMaterial3D.CULL_BACK if cull_back else BaseMaterial3D.CULL_DISABLED
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
    mesh.size=Vector3(float(path["x_max"])-float(path["x_min"]),0.035,float(path["y_max"])-float(path["y_min"]))
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

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var vertices=source["vertices_source_xyz_m"] as Array
    var triangles=source["triangles"] as Array
    var asset_id=String(source.get("asset_id","source-mesh"))
    var cull_back=asset_id==cull_target_asset_id and not cull_target_asset_id.is_empty()
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
    node.name=asset_id
    node.mesh=mesh
    node.material_override=source_material_for(String(source.get("kind","nature-source")),cull_back)
    root3d.add_child(node)
    return {
        "asset_id":asset_id,
        "vertices":vertices.size(),
        "triangles":triangles.size(),
        "proof_culling":"CULL_BACK" if cull_back else "CULL_DISABLED",
        "mesh_digest":String(source.get("mesh_digest",""))
    }

func add_static_sources(root3d:Node3D,data:Dictionary,cull_target_asset_id:String)->Array:
    var results:Array=[]
    for source in data.get("additional_source_meshes",[]) as Array:
        results.append(add_static_source(root3d,source as Dictionary,cull_target_asset_id))
    return results

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
    weather_material.albedo_color=Color(0.55,0.77,1.0,1.0)
    weather_material.emission_enabled=true
    weather_material.emission=Color(0.25,0.48,0.78,1.0)
    weather_material.emission_energy_multiplier=0.85
    weather_material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
    weather_material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
    weather_material.vertex_color_use_as_albedo=true
    weather_mesh=ImmediateMesh.new()
    weather_node=MeshInstance3D.new()
    weather_node.name="source-weather-visual-field-live"
    weather_node.mesh=weather_mesh

func fill_weather(lines:Array)->Dictionary:
    if lines.is_empty():
        return {"state":"FAIL_EMPTY_WEATHER_FIELD"}
    weather_mesh.clear_surfaces()
    weather_mesh.surface_begin(Mesh.PRIMITIVE_LINES,weather_material)
    var opacity_min:=1.0
    var opacity_max:=0.0
    var opacity_sum:=0.0
    for line in lines:
        var row=line as Dictionary
        var opacity=float(row.get("opacity",-1.0))
        if opacity<0.0 or opacity>1.0:
            return {"state":"FAIL_INVALID_SOURCE_STREAK_OPACITY","opacity":opacity,"streak_id":row.get("id","UNKNOWN")}
        opacity_min=minf(opacity_min,opacity)
        opacity_max=maxf(opacity_max,opacity)
        opacity_sum+=opacity
        var a=row["tail_xy"] as Array
        var b=row["head_xy"] as Array
        var h=float(row["presentation_height_m"])
        var vertex_color:=Color(1.0,1.0,1.0,opacity)
        weather_mesh.surface_set_color(vertex_color)
        weather_mesh.surface_add_vertex(gvec([float(a[0]),float(a[1]),h]))
        weather_mesh.surface_set_color(vertex_color)
        weather_mesh.surface_add_vertex(gvec([float(b[0]),float(b[1]),h]))
    weather_mesh.surface_end()
    return {
        "state":"PASS_SOURCE_STREAK_OPACITY_CONSUMED",
        "node_instance_id":weather_node.get_instance_id(),
        "mesh_instance_id":weather_mesh.get_instance_id(),
        "material_instance_id":weather_material.get_instance_id(),
        "surface_count":weather_mesh.get_surface_count(),
        "streak_count":lines.size(),
        "opacity_mode":WEATHER_OPACITY_MODE,
        "source_opacity_consumed":true,
        "source_opacity_min":opacity_min,
        "source_opacity_max":opacity_max,
        "source_opacity_mean":opacity_sum/float(lines.size()),
        "width_policy":"SOURCE_WIDTH_PX_NOT_MAPPED_TO_3D_LINE_WIDTH_IN_THIS_PROOF"
    }

func make_sapling()->void:
    sapling_material=StandardMaterial3D.new()
    sapling_material.albedo_color=Color(0.20,0.43,0.20,1.0)
    sapling_material.roughness=0.82
    sapling_material.cull_mode=BaseMaterial3D.CULL_DISABLED
    sapling_mesh=ArrayMesh.new()
    sapling_node=MeshInstance3D.new()
    sapling_node.name="source-sapling-live-rebound"
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
    var path="res://atmosphere-current-%s-%02d.png" % [context,index]
    if image.save_png(path)!=OK:
        return {"state":"FAIL_CAPTURE"}
    return {"state":"PASS","path":path,"width":image.get_width(),"height":image.get_height(),"bytes":FileAccess.get_file_as_bytes(path).size()}

func _initialize()->void:
    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!="axm.environment-current-world-atmosphere-rebind-evidence/v0.1":
        fail("missing or invalid current-world atmosphere payload")
        return
    if String(payload.get("status",""))!="PASS_CURRENT_WORLD_DENSE_ATMOSPHERE_REBIND_STRUCTURE":
        fail("current-world atmosphere structure must PASS before target-host observation")
        return
    if String(payload.get("dense_vfx_sequence_digest",""))!=DENSE_VFX_SEQUENCE_DIGEST:
        fail("dense VFX sequence digest drift")
        return
    var states=payload["states"] as Array
    if states.size()!=17:
        fail("target-host proof requires exact 17-state sequence")
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
    if cull_target_asset_id!=TARGET_REAR_ASSET_ID:
        fail("current world rear-tree culling target drift")
        return
    var static_source_stats:=add_static_sources(root3d,data,cull_target_asset_id)
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
        var scene=row["scene"] as Dictionary
        var weather_update=fill_weather(scene["weather_lines"] as Array)
        if weather_update.get("state")!="PASS_SOURCE_STREAK_OPACITY_CONSUMED":
            fail("Weather source-opacity update failed at sample %s" % row["index"])
            return
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
            "static_source_meshes":static_source_stats,
            "contexts":contexts
        })

    receipt["state"]="PASS_CURRENT_WORLD_DENSE_ATMOSPHERE_LIVE_OBSERVATION"
    receipt["receiving_head"]=payload["receiving_head"]
    receipt["environment_donor_head"]=payload["environment_donor_head"]
    receipt["dense_vfx_sequence_digest"]=payload["dense_vfx_sequence_digest"]
    receipt["rear_migrated_mesh_digest"]=payload["rear_migrated_mesh_digest"]
    receipt["weather_opacity_mode"]=WEATHER_OPACITY_MODE
    receipt["static_source_meshes"]=static_source_stats
    receipt["samples"]=samples
    receipt["godot_version"]=Engine.get_version_info()
    write_receipt()
    quit(0)
