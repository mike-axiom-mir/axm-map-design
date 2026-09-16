extends "res://atmosphere_current_world_weather_width_observe.gd"

const COMBINED_PAYLOAD_PATH := "res://generated/current_world_building_successor_weather_width.json"
const COMBINED_SCHEMA := "axm.environment-current-world-building-successor-weather-width-composition/v0.1"
const COMBINED_STATUS := "PASS_CURRENT_WORLD_BUILDING_SUCCESSOR_WEATHER_WIDTH_STRUCTURE"
const BUILDING_ASSET_ID := "source:building:service-pavilion-001"
const BUILDING_SOURCE_HEAD := "57f66b1245812f0c3d402232a046b86c0b5c72d8"
const BUILDING_POLICY := "EXACT_SOURCE_OWNED_CLOSED_OUTWARD_TOPOLOGY_REBIND_NO_MATERIAL_RETUNE"
const BUILDING_MATERIAL_PROFILE := "e8dd0c33b9b2aea108194af57a8fe8de39c7e67bb86109af6dbf3895f22c010b"
const EXPECTED_SURFACE_ROLES := [
    "frame_galvanized",
    "infill_coating",
    "roof_membrane",
    "slab_mineral",
    "utility_panel_ochre",
]

func load_payload()->Dictionary:
    if not FileAccess.file_exists(COMBINED_PAYLOAD_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(COMBINED_PAYLOAD_PATH))
    if not (parsed is Dictionary):
        return {}
    var canonical=parsed as Dictionary
    if String(canonical.get("schema",""))!=COMBINED_SCHEMA:
        return {}
    if String(canonical.get("status",""))!=COMBINED_STATUS:
        return {}
    if String(canonical.get("building_source_head",""))!=BUILDING_SOURCE_HEAD:
        return {}
    if String(canonical.get("building_material_profile_sha256",""))!=BUILDING_MATERIAL_PROFILE:
        return {}
    var compat=canonical.duplicate(true)
    compat["schema"]="axm.environment-current-world-weather-width-evidence/v0.1"
    compat["status"]="PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE"
    compat["parent_variant_head"]="e482d003853e52fc835f1797ddfb6506a50083ef"
    return compat

func building_material(row:Dictionary)->StandardMaterial3D:
    var payload=row.get("material",{}) as Dictionary
    var albedo=payload.get("albedo",[]) as Array
    if albedo.size()!=4:
        fail("Building material albedo must contain exact RGBA values")
        return StandardMaterial3D.new()
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(float(albedo[0]),float(albedo[1]),float(albedo[2]),float(albedo[3]))
    material.metallic=float(payload.get("metallic",-1.0))
    material.roughness=float(payload.get("roughness",-1.0))
    if material.metallic<0.0 or material.metallic>1.0 or material.roughness<0.0 or material.roughness>1.0:
        fail("Building material scalar PBR value out of range")
    material.cull_mode=BaseMaterial3D.CULL_DISABLED
    return material

func add_building_material(root3d:Node3D,data:Dictionary)->Dictionary:
    var proof=data.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!=BUILDING_ASSET_ID:
        fail("missing exact Building material receiving payload")
        return {}
    if String(proof.get("receiving_policy",""))!=BUILDING_POLICY:
        fail("Building source-successor receiving policy drift")
        return {}
    var rebind=proof.get("source_successor_rebind",{}) as Dictionary
    if String(rebind.get("source_head",""))!=BUILDING_SOURCE_HEAD:
        fail("Building source-successor head drift")
        return {}
    var provenance=proof.get("provenance",{}) as Dictionary
    if String(provenance.get("material_profile_sha256",""))!=BUILDING_MATERIAL_PROFILE:
        fail("Building material profile drift")
        return {}

    var vertices=proof.get("vertices_source_xyz_m",[]) as Array
    var surfaces=proof.get("surfaces",[]) as Array
    if vertices.size()!=152 or surfaces.size()!=5:
        fail("Building material receiving geometry/surface count drift")
        return {}
    var roles:Array=[]
    var material_ids:Array=[]
    var triangle_count:=0
    var mesh:=ArrayMesh.new()
    for surface_value in surfaces:
        var surface=surface_value as Dictionary
        var role=String(surface.get("surface_role",""))
        var material_id=String(surface.get("material_id",""))
        roles.append(role)
        material_ids.append(material_id)
        if role!=material_id:
            fail("Building material role/id drift")
            return {}
        var triangles=surface.get("triangles",[]) as Array
        triangle_count+=triangles.size()
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for tri_value in triangles:
            var tri=tri_value as Array
            if tri.size()!=3:
                fail("Building material triangle arity drift")
                return {}
            for raw_index in tri:
                var index=int(raw_index)
                if index<0 or index>=vertices.size():
                    fail("Building material triangle index drift")
                    return {}
                st.add_vertex(gvec(vertices[index] as Array))
        st.generate_normals()
        st.commit(mesh)
        var surface_index=mesh.get_surface_count()-1
        mesh.surface_set_material(surface_index,building_material(surface))
    if roles!=EXPECTED_SURFACE_ROLES or triangle_count!=228:
        fail("Building exact five-surface partition drift")
        return {}
    var node:=MeshInstance3D.new()
    node.name=BUILDING_ASSET_ID
    node.mesh=mesh
    root3d.add_child(node)
    return {
        "asset_id":BUILDING_ASSET_ID,
        "vertices":vertices.size(),
        "triangles":triangle_count,
        "surface_count":mesh.get_surface_count(),
        "material_ids":material_ids,
        "material_profile_sha256":BUILDING_MATERIAL_PROFILE,
        "proof_culling":"CULL_DISABLED",
        "receiving_policy":BUILDING_POLICY,
        "building_source_head":BUILDING_SOURCE_HEAD,
    }

func add_static_sources(root3d:Node3D,data:Dictionary,cull_target_asset_id:String)->Array:
    var results:Array=[]
    for source_value in data.get("additional_source_meshes",[]) as Array:
        var source=source_value as Dictionary
        if String(source.get("asset_id",""))==BUILDING_ASSET_ID:
            fail("neutral Building source must remain absent in source-successor composition")
            return []
        results.append(add_static_source(root3d,source,cull_target_asset_id))
    results.append(add_building_material(root3d,data))
    return results
