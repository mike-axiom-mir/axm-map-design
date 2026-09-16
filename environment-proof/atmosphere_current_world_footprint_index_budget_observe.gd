extends "res://atmosphere_current_world_object_indexed_footprint_observe.gd"

const RUNTIME_FOOTPRINT_INDEX_MODE_ENV := "AXM_RUNTIME_FOOTPRINT_INDEX_MODE"
const RUNTIME_FOOTPRINT_INDEX_CONTROL := "UNINDEXED_FOOTPRINT_CONTROL"
const RUNTIME_FOOTPRINT_INDEX_CANDIDATE := "INDEXED_FOOTPRINT_CANDIDATE"
const RUNTIME_FOOTPRINT_INDEX_PARENT_HEAD := "b9d9ed28e9a826c4698014db5f91c59aba9dddfc"
const RUNTIME_FOOTPRINT_INDEX_SCHEMA := "axm.runtime-footprint-index-budget/v0.1"

func _runtime_footprint_index_mode()->String:
    var mode:=OS.get_environment(RUNTIME_FOOTPRINT_INDEX_MODE_ENV)
    if mode!=RUNTIME_FOOTPRINT_INDEX_CONTROL and mode!=RUNTIME_FOOTPRINT_INDEX_CANDIDATE:
        fail("Runtime footprint index mode must be explicit")
        return "INVALID"
    return mode

func _runtime_footprint_mesh_diag(mesh:ArrayMesh)->Dictionary:
    var total_vertices:=0
    var total_indices:=0
    var total_primitives:=0
    var surfaces:Array=[]
    for surface_index in range(mesh.get_surface_count()):
        var vertex_count:=mesh.surface_get_array_len(surface_index)
        var index_count:=mesh.surface_get_array_index_len(surface_index)
        var primitive_count:=index_count/3 if index_count>0 else vertex_count/3
        total_vertices+=vertex_count
        total_indices+=index_count
        total_primitives+=primitive_count
        surfaces.append({
            "surface_index":surface_index,
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

func _index_exact_footprint_surface(node:MeshInstance3D)->Dictionary:
    var source_mesh:=node.mesh as ArrayMesh
    if source_mesh==null or source_mesh.get_surface_count()!=1:
        fail("Runtime footprint indexing expected exact single-surface ArrayMesh")
        return {}
    var st:=SurfaceTool.new()
    st.create_from(source_mesh,0)
    st.index()
    var indexed_mesh:=st.commit()
    if indexed_mesh==null:
        fail("Runtime footprint indexing failed to commit candidate mesh")
        return {}
    node.mesh=indexed_mesh
    return _runtime_footprint_mesh_diag(indexed_mesh)

func add_object_readability_dressing(root3d:Node3D,data:Dictionary)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_object_readability_dressing(root3d,data)
    var mode:=_runtime_footprint_index_mode()
    if result.is_empty() or mode=="INVALID":
        return result
    if String(result.get("asset_id",""))!=DRESSING_ASSET_ID:
        fail("Runtime footprint indexing received dressing identity drift")
        return {}
    if _footprint_review_mode()!=FOOTPRINT_CANDIDATE_VISIBLE:
        fail("Runtime footprint indexing requires exact Art-preferred visible cue context")
        return {}
    if root3d.get_child_count()!=child_count_before+1:
        fail("Runtime footprint indexing expected exactly one emitted dressing child")
        return {}
    var emitted:=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is MeshInstance3D):
        fail("Runtime footprint indexing emitted dressing child is not MeshInstance3D")
        return {}
    var node:=emitted as MeshInstance3D
    if not (node.mesh is ArrayMesh):
        fail("Runtime footprint indexing dressing mesh is not ArrayMesh")
        return {}

    var before:=_runtime_footprint_mesh_diag(node.mesh as ArrayMesh)
    var after:=before.duplicate(true)
    if mode==RUNTIME_FOOTPRINT_INDEX_CANDIDATE:
        after=_index_exact_footprint_surface(node)
        if after.is_empty():
            return {}

    result["runtime_footprint_surface_indexing"]={
        "schema":RUNTIME_FOOTPRINT_INDEX_SCHEMA,
        "mode":mode,
        "environment_parent_head":RUNTIME_FOOTPRINT_INDEX_PARENT_HEAD,
        "asset_id":DRESSING_ASSET_ID,
        "proof_role":DRESSING_ROLE,
        "before":before,
        "after":after,
        "truth_boundary":"Runtime changes only the in-memory index representation of the already-generated Map-owned visible footprint cue after normals exist. Cue dimensions, material override, visibility, placement, Object representation, Building, Nature, Weather, route, cameras and lighting are unchanged.",
    }
    return result

func write_receipt()->void:
    receipt["runtime_footprint_index_mode"]=_runtime_footprint_index_mode()
    receipt["runtime_footprint_index_parent_head"]=RUNTIME_FOOTPRINT_INDEX_PARENT_HEAD
    receipt["runtime_footprint_index_policy"]="POST_NORMAL_SINGLE_SURFACE_INDEXING__NO_VISUAL_ROLE_OR_MATERIAL_COLLAPSE"
    receipt["runtime_footprint_index_truth_boundary"]="Exact proof-host representation A/B only. It does not establish target-device FPS/CPU/GPU/VRAM/heap improvement, final visual preference, arbitrary procedural-mesh safety, UC extraction, CANON or production readiness."
    super.write_receipt()
