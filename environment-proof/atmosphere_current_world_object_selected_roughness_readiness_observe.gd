extends "res://atmosphere_current_world_nature_leaf_flutter_observe.gd"

const SELECTED_ROUGHNESS_MATERIALS_HEAD := "0515a2d5ad2c7a1eb545f2b7b327b7367530dfca"
const SELECTED_ROUGHNESS_SCALAR_SHA256 := "b8d13c07f9b71278042b0d42d44b84579a3f327c6adf6723cae4c8c8f06dd38e"
const SELECTED_ROUGHNESS_TECHNICAL_ART_HEAD := "1bcdbae786e02f3ca46a89e4e0ff608d74f364b4"
const SELECTED_ROUGHNESS_TECHNICAL_ART_RESULT := "PASS_OBJECT_SERVICE_DARK_SELECTED_ROUGHNESS_SCALAR_TO_CURRENT_UC_TEXTURED_GLB_TO_GODOT_FRONT_VIEWS"
const SELECTED_ROUGHNESS_READINESS_STATE := "HOLD_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_RECEIVER__EXACT_UV0_BINDING_NOT_PRESENT"
const SELECTED_ROUGHNESS_RULE := "SPATIAL_MATERIAL_FIELD_REQUIRES_EXACT_RECEIVER_UV_IDENTITY_BEFORE_CURRENT_WORLD_ADOPTION"

func _selected_roughness_uv_diag(mesh:ArrayMesh)->Dictionary:
    if mesh.get_surface_count()!=OBJECT_MATERIAL_IDS.size():
        fail("selected roughness readiness expected exact five-surface Object receiver")
        return {}
    var surfaces:Array=[]
    var total_uv0:=0
    for surface_index in range(mesh.get_surface_count()):
        var arrays:=mesh.surface_get_arrays(surface_index)
        if arrays.size()<=Mesh.ARRAY_TEX_UV:
            fail("selected roughness readiness mesh array layout drift")
            return {}
        var uv_value=arrays[Mesh.ARRAY_TEX_UV]
        var uv_count:=0
        if uv_value!=null:
            if typeof(uv_value)!=TYPE_PACKED_VECTOR2_ARRAY:
                fail("selected roughness readiness UV0 array type drift")
                return {}
            uv_count=uv_value.size()
        total_uv0+=uv_count
        surfaces.append({
            "surface_index":surface_index,
            "material_id":OBJECT_MATERIAL_IDS[surface_index],
            "vertex_count":mesh.surface_get_array_len(surface_index),
            "index_count":mesh.surface_get_array_index_len(surface_index),
            "uv0_count":uv_count,
            "uv0_present":uv_count>0
        })
    return {
        "surface_count":mesh.get_surface_count(),
        "total_uv0_count":total_uv0,
        "all_surfaces_uv0_absent":total_uv0==0,
        "surfaces":surfaces
    }

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_static_source(root3d,source,cull_target_asset_id)
    if String(result.get("asset_id",""))!=OBJECT_ASSET_ID:
        return result
    if root3d.get_child_count()!=child_count_before+1:
        fail("selected roughness readiness expected exactly one emitted Object child")
        return {}
    var emitted:=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is MeshInstance3D):
        fail("selected roughness readiness Object child is not MeshInstance3D")
        return {}
    var node:=emitted as MeshInstance3D
    if not (node.mesh is ArrayMesh):
        fail("selected roughness readiness Object mesh is not ArrayMesh")
        return {}
    var uv_diag:=_selected_roughness_uv_diag(node.mesh as ArrayMesh)
    if uv_diag.is_empty():
        return {}
    if int(uv_diag.get("total_uv0_count",-1))!=0:
        fail("current Environment Object receiver unexpectedly gained UV0; re-evaluate selected roughness adoption instead of preserving HOLD")
        return {}
    result["environment_object_selected_roughness_receiver_readiness"]={
        "schema":"axm.environment-object-selected-roughness-receiver-readiness-observation/v0.1",
        "state":SELECTED_ROUGHNESS_READINESS_STATE,
        "reusable_rule":SELECTED_ROUGHNESS_RULE,
        "current_receiver_materials_head":OBJECT_MATERIALS_HEAD,
        "current_receiver_material_profile_sha256":OBJECT_PROFILE_SHA256,
        "selected_materials_head":SELECTED_ROUGHNESS_MATERIALS_HEAD,
        "selected_scalar_r8_sha256":SELECTED_ROUGHNESS_SCALAR_SHA256,
        "technical_art_head":SELECTED_ROUGHNESS_TECHNICAL_ART_HEAD,
        "technical_art_result":SELECTED_ROUGHNESS_TECHNICAL_ART_RESULT,
        "uv0":uv_diag,
        "selected_roughness_adopted":false,
        "environment_adoption":false,
        "truth_boundary":"Real current-world receiver inspection only. The selected roughness scalar and Technical Art transport remain upstream-owned evidence. Environment does not invent UVs, infer texture placement from material name, retime Nature/Weather, alter Object source geometry, or promote adoption."
    }
    return result

func write_receipt()->void:
    receipt["environment_object_selected_roughness_readiness_state"]=SELECTED_ROUGHNESS_READINESS_STATE
    receipt["environment_object_selected_roughness_reusable_rule"]=SELECTED_ROUGHNESS_RULE
    receipt["environment_object_selected_roughness_materials_head"]=SELECTED_ROUGHNESS_MATERIALS_HEAD
    receipt["environment_object_selected_roughness_scalar_sha256"]=SELECTED_ROUGHNESS_SCALAR_SHA256
    receipt["environment_object_selected_roughness_technical_art_head"]=SELECTED_ROUGHNESS_TECHNICAL_ART_HEAD
    receipt["environment_object_selected_roughness_truth_boundary"]="No scene mutation or roughness-field adoption. Current receiver UV0 is observed in the same real Building + Nature + Object + footprint + Weather scene before any downstream handoff."
    super.write_receipt()
