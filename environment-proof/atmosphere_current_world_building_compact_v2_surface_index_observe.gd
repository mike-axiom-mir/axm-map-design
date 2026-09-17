extends "res://atmosphere_current_world_building_compact_v2_observe.gd"

const RUNTIME_BUILDING_INDEX_SCHEMA := "axm.runtime-building-compact-v2-surface-indexing-observation/v0.1"

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
            "material_id":BUILDING_COMPACT_ROLES[surface_index] if surface_index<BUILDING_COMPACT_ROLES.size() else "UNKNOWN",
            "vertex_count":vertex_count,
            "index_count":index_count,
            "primitive_count":primitive_count,
        })
    return {
        "surface_count":mesh.get_surface_count(),
        "total_vertices":total_vertices,
        "total_indices":total_indices,
        "total_primitives":total_primitives,
        "surfaces":surfaces,
    }

func _index_existing_building_mesh(node:MeshInstance3D)->Dictionary:
    var source_mesh:=node.mesh as ArrayMesh
    if source_mesh==null or source_mesh.get_surface_count()!=BUILDING_COMPACT_ROLES.size():
        fail("Runtime Building indexing expected exact five-surface ArrayMesh")
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

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_segmented_building(root3d,data)
    if String(result.get("asset_id",""))!="source:building:service-pavilion-001":
        return result
    if root3d.get_child_count()!=child_count_before+1:
        fail("Runtime Building indexing expected exactly one emitted Building child")
        return {}
    var emitted:=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is MeshInstance3D):
        fail("Runtime Building indexing emitted child is not MeshInstance3D")
        return {}
    var node:=emitted as MeshInstance3D
    if not (node.mesh is ArrayMesh):
        fail("Runtime Building indexing emitted Building mesh is not ArrayMesh")
        return {}

    var before:=_mesh_surface_diag(node.mesh as ArrayMesh)
    if before.get("surface_count",0)!=5 or before.get("total_primitives",0)!=2052:
        fail("Runtime Building indexing control representation drift")
        return {}
    if before.get("total_indices",-1)!=0 or before.get("total_vertices",0)!=6156:
        fail("Runtime Building indexing expected unindexed triangle-corner control")
        return {}

    var after:=_index_existing_building_mesh(node)
    if after.is_empty():
        return {}
    if after.get("surface_count",0)!=5 or after.get("total_primitives",0)!=2052:
        fail("Runtime Building indexing changed surface/primitive identity")
        return {}
    if after.get("total_indices",0)!=6156:
        fail("Runtime Building indexing index-stream count drift")
        return {}
    if after.get("total_vertices",0)>=before.get("total_vertices",0):
        fail("Runtime Building indexing did not reduce stored vertices")
        return {}

    result["runtime_building_compact_v2_surface_indexing"]={
        "schema":RUNTIME_BUILDING_INDEX_SCHEMA,
        "environment_parent_head":"ef2cb9cc84edc10ab66c2230daca625623e0b00d",
        "building_geometry_head":BUILDING_COMPACT_GEOMETRY_HEAD,
        "building_hard_surface_head":BUILDING_COMPACT_HARD_SURFACE_HEAD,
        "building_materials_head":BUILDING_COMPACT_MATERIALS_HEAD,
        "representation_id":BUILDING_COMPACT_REPRESENTATION_ID,
        "material_roles":BUILDING_COMPACT_ROLES.duplicate(),
        "before":before,
        "after":after,
        "truth_boundary":"Receiver-only post-normal SurfaceTool.index() experiment over the exact five-surface compact-v2 Building already reviewed by Environment and Art Direction. Source topology, triangle membership, final generated normals, material roles/scalars, transform, cameras, lighting, Weather, Nature, Object and footprint cue are unchanged. Counts describe this proof-host ArrayMesh representation only; no target-device frame-time or production adoption is implied.",
    }
    return result

func write_receipt()->void:
    receipt["runtime_building_compact_v2_surface_indexing_result"]="CANDIDATE_INDEXED_AFTER_FINAL_NORMAL_GENERATION"
    receipt["runtime_building_compact_v2_surface_indexing_truth_boundary"]="Post-normal indexing is applied only to the exact compact-v2 current-world receiver after its existing five surfaces and generated normals are built. Visual/runtime acceptance remains independently verified outside this observer."
    super.write_receipt()
