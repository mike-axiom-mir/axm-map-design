extends "res://atmosphere_current_world_object_footprint_material_review.gd"

const ENV_INDEXED_OBJECT_MODE := "INDEXED_CURRENT_WORLD_OBJECT"

func _mesh_surface_diag(mesh:ArrayMesh)->Dictionary:
    var surfaces:Array=[]
    var total_vertices:=0
    var total_indices:=0
    var total_primitives:=0
    for surface_index in range(mesh.get_surface_count()):
        var vertex_count:=mesh.surface_get_array_len(surface_index)
        var index_count:=mesh.surface_get_array_index_len(surface_index)
        var primitive_count:=index_count/3 if index_count>0 else vertex_count/3
        total_vertices+=vertex_count
        total_indices+=index_count
        total_primitives+=primitive_count
        surfaces.append({
            "surface_index":surface_index,
            "material_id":OBJECT_MATERIAL_IDS[surface_index] if surface_index<OBJECT_MATERIAL_IDS.size() else "UNKNOWN",
            "vertex_count":vertex_count,
            "index_count":index_count,
            "primitive_count":primitive_count
        })
    return {
        "surface_count":mesh.get_surface_count(),
        "total_vertices":total_vertices,
        "total_indices":total_indices,
        "total_primitives":total_primitives,
        "surfaces":surfaces
    }

func _index_existing_object_mesh(node:MeshInstance3D)->Dictionary:
    var source_mesh:=node.mesh as ArrayMesh
    if source_mesh==null or source_mesh.get_surface_count()!=OBJECT_MATERIAL_IDS.size():
        fail("Environment indexed Object expected exact five-surface ArrayMesh")
        return {}
    var indexed_mesh:=ArrayMesh.new()
    for surface_index in range(source_mesh.get_surface_count()):
        var st:=SurfaceTool.new()
        st.create_from(source_mesh,surface_index)
        st.index()
        st.commit(indexed_mesh)
        indexed_mesh.surface_set_material(
            indexed_mesh.get_surface_count()-1,
            source_mesh.surface_get_material(surface_index)
        )
    node.mesh=indexed_mesh
    return _mesh_surface_diag(indexed_mesh)

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_static_source(root3d,source,cull_target_asset_id)
    if String(result.get("asset_id",""))!=OBJECT_ASSET_ID:
        return result
    if _footprint_review_mode()!=FOOTPRINT_CANDIDATE_VISIBLE:
        fail("Environment indexed Object successor requires exact visible footprint cue context")
        return {}
    if root3d.get_child_count()!=child_count_before+1:
        fail("Environment indexed Object expected exactly one emitted Object child")
        return {}
    var emitted:=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is MeshInstance3D):
        fail("Environment indexed Object emitted child is not MeshInstance3D")
        return {}
    var node:=emitted as MeshInstance3D
    if not (node.mesh is ArrayMesh):
        fail("Environment indexed Object mesh is not ArrayMesh")
        return {}

    var before:=_mesh_surface_diag(node.mesh as ArrayMesh)
    var after:=_index_existing_object_mesh(node)
    if after.is_empty():
        return {}
    result["environment_object_surface_indexing"]={
        "schema":"axm.environment-current-world-object-indexed-surface-receiving/v0.1",
        "mode":ENV_INDEXED_OBJECT_MODE,
        "runtime_donor_pr":33,
        "runtime_donor_head":"ddd9e8b783b213c6e44bf5eea482de1d41918766",
        "source_object_head":OBJECT_SOURCE_HEAD,
        "source_object_sha256":OBJECT_SOURCE_SHA256,
        "materials_head":OBJECT_MATERIALS_HEAD,
        "material_profile_sha256":OBJECT_PROFILE_SHA256,
        "material_ids":OBJECT_MATERIAL_IDS.duplicate(),
        "before":before,
        "after":after,
        "truth_boundary":"Environment receiving successor applies the exact Runtime PR #33 post-normal SurfaceTool.index() mechanism to the already-preferred five-surface static Object inside the exact visible footprint-cue world. Source geometry, material roles/scalars, transform, footprint geometry, Building, Nature, Weather, route, cameras and lighting are unchanged."
    }
    return result

func write_receipt()->void:
    receipt["environment_object_indexed_receiver_mode"]=ENV_INDEXED_OBJECT_MODE
    receipt["environment_object_indexed_receiver_runtime_donor_pr"]=33
    receipt["environment_object_indexed_receiver_runtime_donor_head"]="ddd9e8b783b213c6e44bf5eea482de1d41918766"
    receipt["environment_object_indexed_receiver_truth_boundary"]="Exact producer-adoption receiving proof only. It does not transfer Runtime target-device acceptance, change Object source/material authority, grant footprint-cue QA acceptance, or generalize indexing to arbitrary assets."
    super.write_receipt()
