extends "res://atmosphere_current_world_nature_material_family_observe.gd"

const OBJECT_PAYLOAD_PATH := "res://generated/current_world_object_material_family.json"
const OBJECT_SCHEMA := "axm.environment-current-world-object-material-family-composition/v0.1"
const OBJECT_STATUS := "PASS_CURRENT_WORLD_OBJECT_MATERIAL_FAMILY_STRUCTURE"
const OBJECT_PARENT_HEAD := "72d4128b602e27c886a0731ddd670ec8c14aaa7e"
const OBJECT_PARENT_DIGEST := "5d050b2d628f73d7e1b738e900eaba22f56ac7bcdd5fc46a5bf781e1d9058866"
const OBJECT_ASSET_ID := "source:object:modular-equipment-case-001"
const OBJECT_SOURCE_HEAD := "d3fa10a270faae7925811f44f03381fe5c5d0215"
const OBJECT_SOURCE_SHA256 := "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
const OBJECT_MATERIALS_HEAD := "c85517446a769e0d5f880fc0e9e32f47124f7b5e"
const OBJECT_PROFILE_SHA256 := "dc200229d6c25fa84063aa51f66103abc022efa54b2167e4432a5b47fc40360c"
const OBJECT_RECEIVING_SCHEMA := "axm.environment-object-material-family-receiving/v0.1"
const OBJECT_MATERIAL_IDS := ["shell_coating","service_dark","hardware_steel","rubber_guard","interface_orange"]

func load_payload()->Dictionary:
    if not FileAccess.file_exists(OBJECT_PAYLOAD_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(OBJECT_PAYLOAD_PATH))
    if not (parsed is Dictionary):
        return {}
    var canonical=parsed as Dictionary
    if String(canonical.get("schema",""))!=OBJECT_SCHEMA or String(canonical.get("status",""))!=OBJECT_STATUS:
        return {}
    if String(canonical.get("parent_environment_head",""))!=OBJECT_PARENT_HEAD:
        return {}
    if String(canonical.get("parent_composition_digest",""))!=OBJECT_PARENT_DIGEST:
        return {}
    if String(canonical.get("object_materials_head",""))!=OBJECT_MATERIALS_HEAD:
        return {}
    if String(canonical.get("object_material_profile_sha256",""))!=OBJECT_PROFILE_SHA256:
        return {}
    if String(canonical.get("object_source_head",""))!=OBJECT_SOURCE_HEAD or String(canonical.get("object_source_sha256",""))!=OBJECT_SOURCE_SHA256:
        return {}
    var compat=canonical.duplicate(true)
    compat["schema"]="axm.environment-current-world-weather-width-evidence/v0.1"
    compat["status"]="PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE"
    compat["parent_variant_head"]="e482d003853e52fc835f1797ddfb6506a50083ef"
    return compat

func write_receipt()->void:
    receipt["environment_object_materials_head"]=OBJECT_MATERIALS_HEAD
    receipt["environment_object_material_profile_sha256"]=OBJECT_PROFILE_SHA256
    receipt["environment_object_material_source_head"]=OBJECT_SOURCE_HEAD
    receipt["environment_object_material_source_sha256"]=OBJECT_SOURCE_SHA256
    receipt["environment_object_material_truth_boundary"]="Exact static-host source-role scalar PBR receiving proof only. No utility module, inner-lid experiment, articulation, source transform/scale, collision, gameplay, final Art/QA preference or target-device acceptance is promoted."
    super.write_receipt()

func _object_material(payload:Dictionary)->StandardMaterial3D:
    var albedo=payload.get("albedo",[]) as Array
    if albedo.size()!=4:
        fail("Object material albedo drift")
        return StandardMaterial3D.new()
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(float(albedo[0]),float(albedo[1]),float(albedo[2]),float(albedo[3]))
    material.metallic=float(payload.get("metallic",-1.0))
    material.roughness=float(payload.get("roughness",-1.0))
    if material.metallic<0.0 or material.metallic>1.0 or material.roughness<0.0 or material.roughness>1.0:
        fail("Object material scalar drift")
    material.cull_mode=BaseMaterial3D.CULL_DISABLED
    return material

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var proof=source.get("object_material_family_receiving",{}) as Dictionary
    if proof.is_empty():
        return super.add_static_source(root3d,source,cull_target_asset_id)
    if String(source.get("asset_id",""))!=OBJECT_ASSET_ID:
        fail("Object material receiver attached to unexpected asset")
        return {}
    if String(proof.get("schema",""))!=OBJECT_RECEIVING_SCHEMA:
        fail("Object material receiving schema drift")
        return {}
    if String(proof.get("materials_head",""))!=OBJECT_MATERIALS_HEAD or String(proof.get("material_profile_sha256",""))!=OBJECT_PROFILE_SHA256:
        fail("Object material receiving identity drift")
        return {}
    if String(proof.get("source_head",""))!=OBJECT_SOURCE_HEAD or String(proof.get("source_sha256",""))!=OBJECT_SOURCE_SHA256:
        fail("Object material source provenance drift")
        return {}
    if String(proof.get("source_scope",""))!="EXACT_STATIC_HOST_ONLY__NO_UTILITY_MODULE__NO_INNER_LID_REVIEW_SLOT":
        fail("Object material receiving scope widened")
        return {}
    if not cull_target_asset_id.is_empty() and String(source.get("asset_id",""))==cull_target_asset_id:
        fail("Object material host unexpectedly became rear-tree culling target")
        return {}

    var vertices=source.get("vertices_source_xyz_m",[]) as Array
    var triangles=source.get("triangles",[]) as Array
    if vertices.size()!=468 or triangles.size()!=812:
        fail("Object material exact geometry count drift")
        return {}
    var partition=proof.get("surface_triangle_indices",{}) as Dictionary
    var materials=proof.get("materials",{}) as Dictionary
    var mesh:=ArrayMesh.new()
    var total:=0
    var seen:Dictionary={}
    for material_id_value in OBJECT_MATERIAL_IDS:
        var material_id=String(material_id_value)
        var indices=partition.get(material_id,[]) as Array
        var material_payload=materials.get(material_id,{}) as Dictionary
        if indices.is_empty() or material_payload.is_empty():
            fail("Object material surface partition missing %s" % material_id)
            return {}
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for raw_tri_index in indices:
            var tri_index=int(raw_tri_index)
            if tri_index<0 or tri_index>=triangles.size() or seen.has(tri_index):
                fail("Object material surface partition index drift")
                return {}
            seen[tri_index]=true
            var tri=triangles[tri_index] as Array
            if tri.size()!=3:
                fail("Object material triangle arity drift")
                return {}
            for raw_vertex_index in tri:
                var vertex_index=int(raw_vertex_index)
                if vertex_index<0 or vertex_index>=vertices.size():
                    fail("Object material vertex index drift")
                    return {}
                st.add_vertex(gvec(vertices[vertex_index] as Array))
        st.generate_normals()
        st.commit(mesh)
        mesh.surface_set_material(mesh.get_surface_count()-1,_object_material(material_payload))
        total+=indices.size()
    if total!=812 or seen.size()!=812 or mesh.get_surface_count()!=5:
        fail("Object material exact five-surface partition drift")
        return {}

    var node:=MeshInstance3D.new()
    node.name=OBJECT_ASSET_ID
    node.mesh=mesh
    root3d.add_child(node)
    return {
        "asset_id":OBJECT_ASSET_ID,
        "vertices":vertices.size(),
        "triangles":triangles.size(),
        "surface_count":mesh.get_surface_count(),
        "material_ids":OBJECT_MATERIAL_IDS.duplicate(),
        "material_profile_sha256":OBJECT_PROFILE_SHA256,
        "materials_head":OBJECT_MATERIALS_HEAD,
        "source_head":OBJECT_SOURCE_HEAD,
        "source_sha256":OBJECT_SOURCE_SHA256,
        "proof_culling":"CULL_DISABLED",
        "source_scope":"EXACT_STATIC_HOST_ONLY__NO_UTILITY_MODULE__NO_INNER_LID_REVIEW_SLOT"
    }
