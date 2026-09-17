extends "res://atmosphere_current_world_object_material_family_observe.gd"

const RUNTIME_INDEX_MODE_ENV := "AXM_RUNTIME_OBJECT_INDEX_MODE"
const RUNTIME_CONTROL_MODE := "UNINDEXED_CONTROL"
const RUNTIME_CANDIDATE_MODE := "INDEXED_CANDIDATE"

func _runtime_index_mode()->String:
    return OS.get_environment(RUNTIME_INDEX_MODE_ENV)

func _mesh_surface_diag(mesh:ArrayMesh)->Dictionary:
    var surfaces:Array=[]
    var total_vertices:=0
    var total_indices:=0
    for surface_index in range(mesh.get_surface_count()):
        var vertex_count:=mesh.surface_get_array_len(surface_index)
        var index_count:=mesh.surface_get_array_index_len(surface_index)
        total_vertices+=vertex_count
        total_indices+=index_count
        surfaces.append({
            "surface_index":surface_index,
            "material_id":OBJECT_MATERIAL_IDS[surface_index] if surface_index<OBJECT_MATERIAL_IDS.size() else "UNKNOWN",
            "vertex_count":vertex_count,
            "index_count":index_count,
            "primitive_count":index_count/3 if index_count>0 else vertex_count/3
        })
    return {
        "surface_count":mesh.get_surface_count(),
        "total_vertices":total_vertices,
        "total_indices":total_indices,
        "total_primitives":total_indices/3 if total_indices>0 else total_vertices/3,
        "surfaces":surfaces
    }

func _index_existing_object_mesh(node:MeshInstance3D)->Dictionary:
    var source_mesh:=node.mesh as ArrayMesh
    if source_mesh==null or source_mesh.get_surface_count()!=OBJECT_MATERIAL_IDS.size():
        fail("Runtime Object indexing expected exact five-surface ArrayMesh")
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

    var mode:=_runtime_index_mode()
    if mode!=RUNTIME_CONTROL_MODE and mode!=RUNTIME_CANDIDATE_MODE:
        fail("Runtime Object indexing mode must be exact control or candidate")
        return {}
    if root3d.get_child_count()!=child_count_before+1:
        fail("Runtime Object indexing expected exactly one emitted Object child")
        return {}
    var emitted:=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is MeshInstance3D):
        fail("Runtime Object indexing emitted child is not MeshInstance3D")
        return {}
    var node:=emitted as MeshInstance3D
    if not (node.mesh is ArrayMesh):
        fail("Runtime Object indexing emitted Object mesh is not ArrayMesh")
        return {}

    var before:=_mesh_surface_diag(node.mesh as ArrayMesh)
    var after:=before.duplicate(true)
    if mode==RUNTIME_CANDIDATE_MODE:
        after=_index_existing_object_mesh(node)
        if after.is_empty():
            return {}

    result["runtime_surface_indexing"]={
        "schema":"axm.runtime-object-material-surface-indexing-observation/v0.1",
        "mode":mode,
        "source_object_head":OBJECT_SOURCE_HEAD,
        "source_object_sha256":OBJECT_SOURCE_SHA256,
        "materials_head":OBJECT_MATERIALS_HEAD,
        "material_profile_sha256":OBJECT_PROFILE_SHA256,
        "material_ids":OBJECT_MATERIAL_IDS.duplicate(),
        "before":before,
        "after":after,
        "truth_boundary":"Receiver-only SurfaceTool.index() experiment over the already-validated exact five-surface static Object mesh. Source geometry, triangle membership, material IDs/scalars, transform, camera, lighting and world composition are unchanged. Counts describe this proof-host ArrayMesh representation only."
    }
    return result
