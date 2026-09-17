extends "res://atmosphere_current_world_building_planar_role_observe.gd"

const RUNTIME_DIRECT_INDEX_SCHEMA := "axm.runtime-building-planar-role-direct-indexed-receiver/v0.2"
const RUNTIME_DIRECT_INDEX_MODE := "DIRECT_INDEXED_POSITION_DOMAIN_THEN_GENERATE_NORMALS"
const RUNTIME_SUPERSEDED_DIRECT_ARRAY_MODE := "DIRECT_FINAL_POSITION_NORMAL_INDEX_ARRAYS" # retained only so the failed v0.1 experiment stays machine-discoverable provenance

func _add_direct_surface(mesh:ArrayMesh,vertices:Array,surface:Dictionary)->Dictionary:
    var triangles:=surface.get("triangles",[]) as Array
    var unique_points:Array[Vector3]=[]
    var indices:Array[int]=[]
    var lookup:Dictionary={}
    for tri_value in triangles:
        var tri:=tri_value as Array
        if tri.size()!=3:
            fail("Runtime direct-indexed Building triangle arity drift")
            return {}
        for raw_index in tri:
            var index:=int(raw_index)
            if index<0 or index>=vertices.size():
                fail("Runtime direct-indexed Building triangle index drift")
                return {}
            var point:Vector3=gvec(vertices[index] as Array)
            var final_index:int
            if lookup.has(point):
                final_index=int(lookup[point])
            else:
                final_index=unique_points.size()
                lookup[point]=final_index
                unique_points.append(point)
            indices.append(final_index)

    var st:=SurfaceTool.new()
    st.begin(Mesh.PRIMITIVE_TRIANGLES)
    for point in unique_points:
        st.add_vertex(point)
    for index in indices:
        st.add_index(index)
    st.generate_normals()
    st.commit(mesh)
    var surface_index:=mesh.get_surface_count()-1
    var arrays:=mesh.surface_get_arrays(surface_index)
    var stored_vertices:int=(arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
    var stored_indices:int=(arrays[Mesh.ARRAY_INDEX] as PackedInt32Array).size()
    return {
        "stored_vertices":stored_vertices,
        "indices":stored_indices,
        "triangles":stored_indices/3,
        "position_domain_vertices":unique_points.size(),
    }

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var started_usec:=Time.get_ticks_usec()
    var proof:=data.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!="source:building:service-pavilion-001":
        fail("Runtime direct-indexed Building missing exact planar-role receiving payload")
        return {}
    var receiving:=proof.get("environment_building_planar_role_receiving",{}) as Dictionary
    if String(receiving.get("schema",""))!=BUILDING_PLANAR_RECEIVING_SCHEMA:
        fail("Runtime direct-indexed Building receiving schema drift")
        return {}
    if String(receiving.get("hard_surface_head",""))!=BUILDING_PLANAR_HARD_SURFACE_HEAD:
        fail("Runtime direct-indexed Building Hard-Surface head drift")
        return {}
    if String(receiving.get("materials_head",""))!=BUILDING_PLANAR_MATERIALS_HEAD:
        fail("Runtime direct-indexed Building Materials head drift")
        return {}
    if String(receiving.get("selected_representation_id",""))!=BUILDING_PLANAR_REPRESENTATION_ID:
        fail("Runtime direct-indexed Building representation drift")
        return {}
    if bool(receiving.get("environment_adoption",true)):
        fail("Runtime direct-indexed Building unexpectedly claims Environment adoption")
        return {}

    var vertices:=proof.get("vertices_source_xyz_m",[]) as Array
    var surfaces:=proof.get("surfaces",[]) as Array
    if vertices.size()!=672 or surfaces.size()!=5:
        fail("Runtime direct-indexed Building payload cardinality drift")
        return {}

    var mesh:=ArrayMesh.new()
    var roles:Array=[]
    var material_ids:Array=[]
    var total_stored_vertices:=0
    var total_indices:=0
    var total_triangles:=0
    var surface_metrics:Array=[]
    for surface_value in surfaces:
        var surface:=surface_value as Dictionary
        var role:=String(surface.get("surface_role",""))
        var material_id:=String(surface.get("material_id",""))
        roles.append(role)
        material_ids.append(material_id)
        if role!=material_id:
            fail("Runtime direct-indexed Building material role/id drift")
            return {}
        var metric:=_add_direct_surface(mesh,vertices,surface)
        if metric.is_empty():
            return {}
        var surface_index:=mesh.get_surface_count()-1
        mesh.surface_set_material(surface_index,building_material(surface))
        total_stored_vertices+=int(metric["stored_vertices"])
        total_indices+=int(metric["indices"])
        total_triangles+=int(metric["triangles"])
        metric["surface_role"]=role
        surface_metrics.append(metric)

    if roles!=BUILDING_PLANAR_ROLES or total_triangles!=336:
        fail("Runtime direct-indexed Building five-role/triangle identity drift")
        return {}
    if total_stored_vertices!=312 or total_indices!=1008:
        fail("Runtime direct-indexed Building final storage identity drift: vertices=%d indices=%d metrics=%s" % [total_stored_vertices,total_indices,JSON.stringify(surface_metrics)])
        return {}

    var node:=MeshInstance3D.new()
    node.name="source:building:service-pavilion-001"
    node.mesh=mesh
    root3d.add_child(node)
    var elapsed_usec:=int(Time.get_ticks_usec()-started_usec)
    return {
        "asset_id":"source:building:service-pavilion-001",
        "vertices":vertices.size(),
        "triangles":total_triangles,
        "surface_count":mesh.get_surface_count(),
        "material_ids":material_ids,
        "proof_culling":"CULL_DISABLED",
        "receiving_policy":String(proof.get("receiving_policy","")),
        "representation_id":BUILDING_PLANAR_REPRESENTATION_ID,
        "planar_role_hard_surface_head":BUILDING_PLANAR_HARD_SURFACE_HEAD,
        "planar_role_materials_head":BUILDING_PLANAR_MATERIALS_HEAD,
        "runtime_building_prepare_usec":elapsed_usec,
        "runtime_building_prepare_mode":RUNTIME_DIRECT_INDEX_MODE,
        "runtime_building_direct_indexed":{
            "schema":RUNTIME_DIRECT_INDEX_SCHEMA,
            "surface_count":mesh.get_surface_count(),
            "stored_vertices":total_stored_vertices,
            "indices":total_indices,
            "triangles":total_triangles,
            "source_payload_vertices":vertices.size(),
            "surface_metrics":surface_metrics,
            "truth_boundary":"Directly constructs the exact per-material unique-position index domain first, then lets the same pinned Godot SurfaceTool.generate_normals() define final normals. This skips the control's 1,008-corner temporary mesh and second create_from/index rewrite while preserving the same five source material roles/scalars, 336 triangles, transform and current-world inputs. No UV/tangent/color/skin/morph/custom-channel inference and no default adoption."
        }
    }

func write_receipt()->void:
    receipt["runtime_building_direct_indexed_schema"]=RUNTIME_DIRECT_INDEX_SCHEMA
    receipt["runtime_building_direct_indexed_mode"]=RUNTIME_DIRECT_INDEX_MODE
    receipt["runtime_building_direct_indexed_result"]="CANDIDATE_INDEX_POSITION_DOMAIN_BEFORE_NORMAL_GENERATION"
    receipt["runtime_building_direct_indexed_truth_boundary"]="This candidate skips the control's temporary unindexed triangle-corner mesh plus create_from/index rewrite. It constructs the already-proven per-material unique-position index domain before the same Godot normal-generation step. It is a receiver/import-preparation experiment, not source or Environment adoption."
    super.write_receipt()
