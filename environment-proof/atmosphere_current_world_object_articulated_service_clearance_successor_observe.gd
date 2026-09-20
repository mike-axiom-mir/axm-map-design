extends "res://atmosphere_current_world_object_motion_current_rebind_observe.gd"

const SERVICE_CLEARANCE_CONTRACT_PATH := "res://generated/environment-object-articulated-service-clearance.json"
const SERVICE_CLEARANCE_SCHEMA := "axm.environment-object-articulated-service-clearance/v0.1"
const SERVICE_CLEARANCE_RENDER_STATE := "PASS_CURRENT_WORLD_OBJECT_ARTICULATED_SERVICE_CLEARANCE_SUCCESSOR_RENDERED__ART_QA_RUNTIME_ADOPTION_HELD"
const SERVICE_CLEARANCE_RENDER_RULE := "SPATIALLY_PROVEN_ENVIRONMENT_DRESSING_SUCCESSOR_MUST_BE_RENDERED_AGAINST_THE_EXACT_PREDECESSOR_WORLD_WITH_OWNER_MOTION_CAMERAS_LIGHTS_AND_UNRELATED_ASSETS_HELD"
const SERVICE_CLEARANCE_FRAME_ASSET_ID := "environment:dressing:west-object-service-footprint-frame-001"
const SERVICE_CLEARANCE_FRAME_ROLE := "ENVIRONMENT_OWNED_RECEIVER_FOOTPRINT_READABILITY_CUE"
const SERVICE_CLEARANCE_OBJECT_ASSET_ID := "source:object:modular-equipment-case-001"
const SERVICE_CLEARANCE_EXPECTED_EXPANSION_M := 0.02
const SERVICE_CLEARANCE_EXPECTED_PREDECESSOR := [-4.025387,-2.890757,3.736077,4.8707069999999995]

func _service_read_contract()->Dictionary:
    if not FileAccess.file_exists(SERVICE_CLEARANCE_CONTRACT_PATH):
        fail("Environment articulated service-clearance render contract missing")
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(SERVICE_CLEARANCE_CONTRACT_PATH))
    if not (parsed is Dictionary):
        fail("Environment articulated service-clearance render contract invalid")
        return {}
    var contract=parsed as Dictionary
    if String(contract.get("schema",""))!=SERVICE_CLEARANCE_SCHEMA:
        fail("Environment articulated service-clearance render contract schema drift")
        return {}
    var candidate=contract.get("candidate",{}) as Dictionary
    if absf(float(candidate.get("rear_outer_edge_expansion_m",-1.0))-SERVICE_CLEARANCE_EXPECTED_EXPANSION_M)>0.000001:
        fail("Environment articulated service-clearance render expansion drift")
        return {}
    if bool(candidate.get("environment_adoption",true)):
        fail("Environment articulated service-clearance render contract inflated adoption authority")
        return {}
    var frame=contract.get("service_frame",{}) as Dictionary
    if String(frame.get("asset_id",""))!=SERVICE_CLEARANCE_FRAME_ASSET_ID:
        fail("Environment articulated service-clearance render frame identity drift")
        return {}
    if not _same4(frame.get("predecessor_outer_footprint_world_xy_m",[]) as Array,SERVICE_CLEARANCE_EXPECTED_PREDECESSOR):
        fail("Environment articulated service-clearance predecessor footprint drift")
        return {}
    return contract

func add_object_readability_dressing(root3d:Node3D,data:Dictionary)->Dictionary:
    var contract:=_service_read_contract()
    if contract.is_empty():
        return {}
    var proof=data.get("environment_object_readability_dressing",{}) as Dictionary
    if String(proof.get("schema",""))!="axm.environment-object-service-footprint-frame/v0.1":
        fail("Environment articulated service-clearance source dressing schema drift")
        return {}
    if String(proof.get("asset_id",""))!=SERVICE_CLEARANCE_FRAME_ASSET_ID or String(proof.get("source_object_asset_id",""))!=SERVICE_CLEARANCE_OBJECT_ASSET_ID:
        fail("Environment articulated service-clearance source dressing identity drift")
        return {}
    if String(proof.get("role",""))!=SERVICE_CLEARANCE_FRAME_ROLE:
        fail("Environment articulated service-clearance source dressing role drift")
        return {}

    var predecessor=proof.get("outer_footprint_source_xy_m",[]) as Array
    if not _same4(predecessor,SERVICE_CLEARANCE_EXPECTED_PREDECESSOR):
        fail("Environment articulated service-clearance source dressing predecessor drift")
        return {}
    var frame=contract.get("service_frame",{}) as Dictionary
    var strip_width:=float(proof.get("strip_width_m",-1.0))
    var height:=float(proof.get("frame_height_m",-1.0))
    if absf(strip_width-float(frame.get("strip_width_m",-1.0)))>0.000001 or absf(height-float(frame.get("frame_height_m",-1.0)))>0.000001:
        fail("Environment articulated service-clearance source dressing scalar drift")
        return {}

    var candidate=predecessor.duplicate()
    candidate[3]=float(candidate[3])+SERVICE_CLEARANCE_EXPECTED_EXPANSION_M
    var xmin:=float(candidate[0])
    var xmax:=float(candidate[1])
    var ymin:=float(candidate[2])
    var ymax:=float(candidate[3])

    var material_data=proof.get("material",{}) as Dictionary
    var albedo=material_data.get("albedo",[]) as Array
    if albedo.size()!=4:
        fail("Environment articulated service-clearance dressing material drift")
        return {}

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
    node.name=SERVICE_CLEARANCE_FRAME_ASSET_ID
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
        "asset_id":SERVICE_CLEARANCE_FRAME_ASSET_ID,
        "triangles":48,
        "surface_count":mesh.get_surface_count(),
        "proof_role":SERVICE_CLEARANCE_FRAME_ROLE,
        "outer_footprint_source_xy_m":candidate,
        "predecessor_outer_footprint_source_xy_m":predecessor,
        "rear_outer_edge_expansion_m":SERVICE_CLEARANCE_EXPECTED_EXPANSION_M,
        "strip_width_m":strip_width,
        "frame_height_m":height,
        "source_object_transform_policy":String(proof.get("source_object_transform_policy","")),
        "environment_adoption":false,
    }

func write_receipt()->void:
    receipt["environment_object_articulated_service_clearance_render_state"]=SERVICE_CLEARANCE_RENDER_STATE
    receipt["environment_object_articulated_service_clearance_render_rule"]=SERVICE_CLEARANCE_RENDER_RULE
    receipt["environment_object_articulated_service_clearance_predecessor_outer_footprint_world_xy_m"]=SERVICE_CLEARANCE_EXPECTED_PREDECESSOR
    receipt["environment_object_articulated_service_clearance_successor_outer_footprint_world_xy_m"]=[-4.025387,-2.890757,3.736077,4.890707]
    receipt["environment_object_articulated_service_clearance_rear_outer_edge_expansion_m"]=SERVICE_CLEARANCE_EXPECTED_EXPANSION_M
    receipt["environment_object_articulated_service_clearance_environment_adoption"]=false
    receipt["environment_object_articulated_service_clearance_art_qa_acceptance"]=false
    receipt["environment_object_articulated_service_clearance_runtime_acceptance"]=false
    receipt["environment_object_articulated_service_clearance_truth_boundary"]="Rendered current-world review candidate only. The spatial +20 mm rear-edge successor is shown through the exact articulated Object receiver with inherited Building, Nature, Weather, selected Object roughness, cameras and lighting held. Rendering does not grant Environment adoption, Art/QA acceptance, Runtime/device acceptance, gameplay/collision authority, CANON or production readiness."
    super.write_receipt()
