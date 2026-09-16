extends "res://atmosphere_current_world_building_infill_weather_width_observe.gd"

const DRESSING_PAYLOAD_PATH := "res://generated/current_world_object_readability_dressing.json"
const DRESSING_SCHEMA := "axm.environment-current-world-object-readability-dressing-composition/v0.1"
const DRESSING_STATUS := "PASS_CURRENT_WORLD_OBJECT_READABILITY_DRESSING_STRUCTURE"
const DRESSING_PARENT_HEAD := "5b9b55ec67e31655f51d1acc67284816067e5be6"
const DRESSING_ASSET_ID := "environment:dressing:west-object-service-footprint-frame-001"
const DRESSING_OBJECT_ASSET_ID := "source:object:modular-equipment-case-001"
const DRESSING_ROLE := "ENVIRONMENT_OWNED_RECEIVER_FOOTPRINT_READABILITY_CUE"
const WIDTH_COMPAT_SCHEMA := "axm.environment-current-world-weather-width-evidence/v0.1"
const WIDTH_COMPAT_STATUS := "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE"
const WIDTH_COMPAT_PARENT_HEAD := "e482d003853e52fc835f1797ddfb6506a50083ef"

var dressing_world_corners:Array=[]

func write_receipt()->void:
    receipt["environment_object_readability_dressing_asset_id"]=DRESSING_ASSET_ID
    receipt["environment_object_readability_role"]=DRESSING_ROLE
    receipt["environment_object_readability_truth_boundary"]="Map Environment receiver-footprint dressing only. Exact Object source transform/scale and all Building, Nature and Weather source state remain source-owned; final Art Direction/Visual QA preference and gameplay/runtime certification remain separate."
    var file:=FileAccess.open("res://atmosphere-current-world-weather-width-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(receipt,"  ")+"\n")
        file.close()

func load_payload()->Dictionary:
    if not FileAccess.file_exists(DRESSING_PAYLOAD_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(DRESSING_PAYLOAD_PATH))
    if not (parsed is Dictionary):
        return {}
    var canonical=parsed as Dictionary
    if String(canonical.get("schema",""))!=DRESSING_SCHEMA:
        return {}
    if String(canonical.get("status",""))!=DRESSING_STATUS:
        return {}
    if String(canonical.get("environment_parent_head",""))!=DRESSING_PARENT_HEAD:
        return {}
    if String((canonical.get("dressing",{}) as Dictionary).get("asset_id",""))!=DRESSING_ASSET_ID:
        return {}
    var compat=canonical.duplicate(true)
    compat["schema"]=WIDTH_COMPAT_SCHEMA
    compat["status"]=WIDTH_COMPAT_STATUS
    compat["parent_variant_head"]=WIDTH_COMPAT_PARENT_HEAD
    return compat

func _emit_box(st:SurfaceTool,x0:float,x1:float,y0:float,y1:float,z0:float,z1:float)->void:
    var v=[
        gvec([x0,y0,z0]),gvec([x1,y0,z0]),gvec([x1,y1,z0]),gvec([x0,y1,z0]),
        gvec([x0,y0,z1]),gvec([x1,y0,z1]),gvec([x1,y1,z1]),gvec([x0,y1,z1]),
    ]
    var tris=[
        [0,2,1],[0,3,2], [4,5,6],[4,6,7],
        [0,1,5],[0,5,4], [1,2,6],[1,6,5],
        [2,3,7],[2,7,6], [3,0,4],[3,4,7],
    ]
    for tri in tris:
        for idx in tri:
            st.add_vertex(v[int(idx)])

func _same4(values:Array,expected:Array)->bool:
    if values.size()!=4 or expected.size()!=4:
        return false
    for i in range(4):
        if absf(float(values[i])-float(expected[i]))>0.000001:
            return false
    return true

func add_object_readability_dressing(root3d:Node3D,data:Dictionary)->Dictionary:
    var proof=data.get("environment_object_readability_dressing",{}) as Dictionary
    if String(proof.get("schema",""))!="axm.environment-object-service-footprint-frame/v0.1":
        fail("Object readability dressing schema drift")
        return {}
    if String(proof.get("asset_id",""))!=DRESSING_ASSET_ID or String(proof.get("source_object_asset_id",""))!=DRESSING_OBJECT_ASSET_ID:
        fail("Object readability dressing identity drift")
        return {}
    if String(proof.get("role",""))!=DRESSING_ROLE:
        fail("Object readability dressing role drift")
        return {}
    var footprint=proof.get("outer_footprint_source_xy_m",[]) as Array
    var expected=[-4.025387,-2.890757,3.736077,4.8707069999999995]
    if not _same4(footprint,expected):
        fail("Object readability dressing footprint drift")
        return {}
    var strip_width=float(proof.get("strip_width_m",-1.0))
    var height=float(proof.get("frame_height_m",-1.0))
    if absf(strip_width-0.045)>0.000001 or absf(height-0.02)>0.000001:
        fail("Object readability dressing geometry scalar drift")
        return {}
    var material_data=proof.get("material",{}) as Dictionary
    var albedo=material_data.get("albedo",[]) as Array
    if albedo.size()!=4:
        fail("Object readability dressing material drift")
        return {}

    var xmin=float(footprint[0])
    var xmax=float(footprint[1])
    var ymin=float(footprint[2])
    var ymax=float(footprint[3])
    var st:=SurfaceTool.new()
    st.begin(Mesh.PRIMITIVE_TRIANGLES)
    _emit_box(st,xmin,xmin+strip_width,ymin,ymax,0.0,height)
    _emit_box(st,xmax-strip_width,xmax,ymin,ymax,0.0,height)
    _emit_box(st,xmin+strip_width,xmax-strip_width,ymin,ymin+strip_width,0.0,height)
    _emit_box(st,xmin+strip_width,xmax-strip_width,ymax-strip_width,ymax,0.0,height)
    st.generate_normals()
    var mesh:=st.commit()
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(float(albedo[0]),float(albedo[1]),float(albedo[2]),float(albedo[3]))
    material.metallic=float(material_data.get("metallic",0.0))
    material.roughness=float(material_data.get("roughness",0.9))
    material.cull_mode=BaseMaterial3D.CULL_DISABLED
    var node:=MeshInstance3D.new()
    node.name=DRESSING_ASSET_ID
    node.mesh=mesh
    node.material_override=material
    node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    root3d.add_child(node)

    dressing_world_corners=[]
    for x in [xmin,xmax]:
        for y in [ymin,ymax]:
            for z in [0.0,height]:
                dressing_world_corners.append(gvec([x,y,z]))
    return {
        "asset_id":DRESSING_ASSET_ID,
        "triangles":48,
        "surface_count":mesh.get_surface_count(),
        "proof_role":DRESSING_ROLE,
        "outer_footprint_source_xy_m":footprint,
        "strip_width_m":strip_width,
        "frame_height_m":height,
        "source_object_transform_policy":String(proof.get("source_object_transform_policy","")),
    }

func add_static_sources(root3d:Node3D,data:Dictionary,cull_target_asset_id:String)->Array:
    var results=super.add_static_sources(root3d,data,cull_target_asset_id)
    results.append(add_object_readability_dressing(root3d,data))
    return results

func _projected_dressing_bbox(viewport:SubViewport,width:int,height:int)->Array:
    var camera:=viewport.get_camera_3d()
    if camera==null or dressing_world_corners.size()!=8:
        return []
    var xmin:=INF
    var ymin:=INF
    var xmax:=-INF
    var ymax:=-INF
    for world_value in dressing_world_corners:
        var world:Vector3=world_value
        var p:Vector2=camera.unproject_position(world)
        xmin=minf(xmin,p.x)
        ymin=minf(ymin,p.y)
        xmax=maxf(xmax,p.x)
        ymax=maxf(ymax,p.y)
    return [
        clampi(int(floor(xmin)),0,width-1),
        clampi(int(floor(ymin)),0,height-1),
        clampi(int(ceil(xmax)),0,width-1),
        clampi(int(ceil(ymax)),0,height-1),
    ]

func capture_mode(viewport:SubViewport,context:String,index:int,mode:String)->Dictionary:
    var image:=viewport.get_texture().get_image()
    if image==null or image.is_empty():
        return {"state":"FAIL_CAPTURE"}
    var path="res://atmosphere-width-%s-%s-%02d.png" % [mode,context,index]
    if image.save_png(path)!=OK:
        return {"state":"FAIL_CAPTURE"}
    var bbox=_projected_dressing_bbox(viewport,image.get_width(),image.get_height())
    if bbox.size()!=4:
        return {"state":"FAIL_DRESSING_PROJECTION"}
    return {
        "state":"PASS",
        "path":path,
        "width":image.get_width(),
        "height":image.get_height(),
        "bytes":FileAccess.get_file_as_bytes(path).size(),
        "dressing_projected_bbox_px":bbox,
        "dressing_asset_id":DRESSING_ASSET_ID,
    }
