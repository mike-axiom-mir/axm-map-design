extends "res://atmosphere_current_world_building_current_policy_observe.gd"

const NATURE_SPLIT_CULLING_POLICY_SCHEMA := "axm.environment-nature-surface-culling-policy/v0.1"
const NATURE_SPLIT_CULLING_POLICY_ID := "source-woody-back__source-foliage-two-sided-001"
const NATURE_SPLIT_CULLING_STRUCTURE_RESULT := "PASS_CURRENT_WORLD_NATURE_SPLIT_SURFACE_CULLING_STRUCTURE"
const NATURE_SPLIT_CULLING_MATERIALS_HEAD := "8b2e0523d7a2b210c6404f15bafb08fbedcad4dd"
const NATURE_SPLIT_CULLING_SIDEDNESS_REVIEW_HEAD := "0b7fdfac3be4d9c25236fa8733108e7d32533657"
const NATURE_SPLIT_CULLING_VFX_HEAD := "4e5211d14286f9c292e769a78971f24d59194141"
const NATURE_SPLIT_CULLING_GEOMETRY_HEAD := "da3adbef4de8cddb8f3ebe841d39bb31a8936f5f"

func load_payload()->Dictionary:
    var compat := super.load_payload()
    if compat.is_empty():
        return {}
    if not FileAccess.file_exists(NATURE_MIGRATION_PAYLOAD_PATH):
        return {}
    var parsed = JSON.parse_string(FileAccess.get_file_as_string(NATURE_MIGRATION_PAYLOAD_PATH))
    if not (parsed is Dictionary):
        return {}
    var canonical := parsed as Dictionary
    var policy := canonical.get("nature_surface_culling_policy", {}) as Dictionary
    if String(canonical.get("nature_surface_culling_structure_result", "")) != NATURE_SPLIT_CULLING_STRUCTURE_RESULT:
        return {}
    if String(policy.get("schema", "")) != NATURE_SPLIT_CULLING_POLICY_SCHEMA:
        return {}
    if String(policy.get("policy_id", "")) != NATURE_SPLIT_CULLING_POLICY_ID:
        return {}
    if String(policy.get("woody_surface_cull", "")) != "CULL_BACK":
        return {}
    if String(policy.get("foliage_surface_cull", "")) != "CULL_DISABLED":
        return {}
    if bool(policy.get("explicit_leaf_backface_geometry_adopted", true)):
        return {}
    if String(policy.get("nature_materials_head", "")) != NATURE_SPLIT_CULLING_MATERIALS_HEAD:
        return {}
    if String(policy.get("sidedness_review_head", "")) != NATURE_SPLIT_CULLING_SIDEDNESS_REVIEW_HEAD:
        return {}
    if String(policy.get("vfx_dynamic_leaf_review_head", "")) != NATURE_SPLIT_CULLING_VFX_HEAD:
        return {}
    if String(policy.get("geometry_leaf_candidate_head", "")) != NATURE_SPLIT_CULLING_GEOMETRY_HEAD:
        return {}
    var states := canonical.get("states", []) as Array
    if states.size() != 17:
        return {}
    for row in states:
        var scene := (row as Dictionary).get("scene", {}) as Dictionary
        var scene_policy := scene.get("environment_nature_surface_culling_policy", {}) as Dictionary
        if String(scene_policy.get("policy_id", "")) != NATURE_SPLIT_CULLING_POLICY_ID:
            return {}
    return compat

func _commit_nature_surfaces(mesh:ArrayMesh,vertices:Array,triangles:Array,proof:Dictionary,_legacy_cull_back:bool)->int:
    var partition=proof.get("surface_triangle_indices",{}) as Dictionary
    var materials=proof.get("materials",{}) as Dictionary
    var total:=0
    for role_value in ["woody","foliage"]:
        var role=String(role_value)
        var indices=partition.get(role,[]) as Array
        var material_payload=materials.get(role,{}) as Dictionary
        if indices.is_empty() or material_payload.is_empty():
            fail("Nature split-culling material-family surface partition missing %s" % role)
            return -1
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for raw_tri_index in indices:
            var tri_index=int(raw_tri_index)
            if tri_index<0 or tri_index>=triangles.size():
                fail("Nature split-culling triangle partition index drift")
                return -1
            var tri=triangles[tri_index] as Array
            if tri.size()!=3:
                fail("Nature split-culling triangle arity drift")
                return -1
            for raw_vertex_index in tri:
                var vertex_index=int(raw_vertex_index)
                if vertex_index<0 or vertex_index>=vertices.size():
                    fail("Nature split-culling vertex index drift")
                    return -1
                st.add_vertex(gvec(vertices[vertex_index] as Array))
        st.generate_normals()
        st.commit(mesh)
        var cull_back := role == "woody"
        mesh.surface_set_material(mesh.get_surface_count()-1,_nature_material(material_payload,cull_back))
        total+=indices.size()
    return total

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var result:=super.add_static_source(root3d,source,cull_target_asset_id)
    if result.is_empty():
        return result
    var asset_id:=String(result.get("asset_id",""))
    if asset_id.begins_with("source:nature:") and String(result.get("material_family_id",""))==NATURE_FAMILY_ID:
        result["proof_culling"]="MIXED_BY_MATERIAL_ROLE"
        result["surface_culling"]={"woody":"CULL_BACK","foliage":"CULL_DISABLED"}
        result["explicit_leaf_backface_geometry_adopted"]=false
    return result

func fill_sapling(sapling:Dictionary)->Dictionary:
    var result:=super.fill_sapling(sapling)
    if result.is_empty():
        return result
    result["proof_culling"]="MIXED_BY_MATERIAL_ROLE"
    result["surface_culling"]={"woody":"CULL_BACK","foliage":"CULL_DISABLED"}
    result["explicit_leaf_backface_geometry_adopted"]=false
    return result

func write_receipt()->void:
    receipt["environment_nature_surface_culling_policy_schema"]=NATURE_SPLIT_CULLING_POLICY_SCHEMA
    receipt["environment_nature_surface_culling_policy_id"]=NATURE_SPLIT_CULLING_POLICY_ID
    receipt["environment_nature_woody_surface_cull"]="CULL_BACK"
    receipt["environment_nature_foliage_surface_cull"]="CULL_DISABLED"
    receipt["environment_nature_materials_head"]=NATURE_SPLIT_CULLING_MATERIALS_HEAD
    receipt["environment_nature_sidedness_review_head"]=NATURE_SPLIT_CULLING_SIDEDNESS_REVIEW_HEAD
    receipt["environment_nature_vfx_dynamic_leaf_review_head"]=NATURE_SPLIT_CULLING_VFX_HEAD
    receipt["environment_nature_geometry_leaf_candidate_head"]=NATURE_SPLIT_CULLING_GEOMETRY_HEAD
    receipt["environment_nature_explicit_leaf_backface_geometry_adopted"]=false
    receipt["environment_nature_surface_culling_truth_boundary"]="Current-world receiving review only: exact 390v/570t Nature source geometry and woody/foliage PBR values remain unchanged. Woody uses CULL_BACK; foliage uses CULL_DISABLED. Explicit 490v/620t leaf-backface geometry is not adopted. Pixel deltas remain Art Direction / Visual QA evidence, not automatic aesthetic acceptance."
    super.write_receipt()
