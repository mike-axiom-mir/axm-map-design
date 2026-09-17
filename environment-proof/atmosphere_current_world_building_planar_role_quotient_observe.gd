extends "res://atmosphere_current_world_building_planar_role_surface_index_observe.gd"

const BUILDING_QUOTIENT_RECEIVING_SCHEMA := "axm.environment-building-planar-role-quotient-receiving-observation/v0.1"
const BUILDING_QUOTIENT_GEOMETRY_HEAD := "7dfb1153dc5f80bcbf1b48803f044236d4ebb030"
const BUILDING_QUOTIENT_CONSUMER_ID := "map-consumer:service-pavilion-001:planar-role-post-normal-indexed-001"

func _vec3_list(value:Vector3)->Array:
    return [float(value.x), float(value.y), float(value.z)]

func _indexed_snapshot(mesh:ArrayMesh)->Dictionary:
    var surfaces:Array=[]
    var total_vertices:=0
    var total_indices:=0
    var total_primitives:=0
    for surface_index in range(mesh.get_surface_count()):
        var arrays:=mesh.surface_get_arrays(surface_index)
        var positions:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
        var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
        var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
        if positions.size()!=normals.size():
            fail("quotient receiver position/normal cardinality drift")
            return {}
        var vertices:Array=[]
        for i in range(positions.size()):
            vertices.append({"position":_vec3_list(positions[i]),"normal":_vec3_list(normals[i])})
        var index_rows:Array=[]
        for value in indices:
            index_rows.append(int(value))
        total_vertices+=positions.size()
        total_indices+=indices.size()
        total_primitives+=indices.size()/3
        surfaces.append({
            "surface_index":surface_index,
            "material_id":BUILDING_PLANAR_ROLES[surface_index] if surface_index<BUILDING_PLANAR_ROLES.size() else "UNKNOWN",
            "vertices":vertices,
            "indices":index_rows,
        })
    return {"surface_count":mesh.get_surface_count(),"total_vertices":total_vertices,"total_indices":total_indices,"total_primitives":total_primitives,"surfaces":surfaces}

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_segmented_building(root3d,data)
    if String(result.get("asset_id",""))!="source:building:service-pavilion-001":
        return result
    if root3d.get_child_count()!=child_count_before+1:
        fail("quotient receiver expected exactly one emitted Building child")
        return {}
    var emitted:=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is MeshInstance3D):
        fail("quotient receiver emitted child is not MeshInstance3D")
        return {}
    var node:=emitted as MeshInstance3D
    if not (node.mesh is ArrayMesh):
        fail("quotient receiver emitted Building mesh is not ArrayMesh")
        return {}
    var snapshot:=_indexed_snapshot(node.mesh as ArrayMesh)
    if snapshot.is_empty():
        return {}
    if int(snapshot.get("surface_count",0))!=5 or int(snapshot.get("total_vertices",0))!=312 or int(snapshot.get("total_indices",0))!=1008 or int(snapshot.get("total_primitives",0))!=336:
        fail("quotient receiver indexed storage identity drift")
        return {}
    result["environment_building_planar_role_quotient_receiving"]={
        "schema":BUILDING_QUOTIENT_RECEIVING_SCHEMA,
        "geometry_quotient_head":BUILDING_QUOTIENT_GEOMETRY_HEAD,
        "consumer_representation_id":BUILDING_QUOTIENT_CONSUMER_ID,
        "exact_position_partition_rebind":true,
        "source_hard_normal_identity_preserved":false,
        "consumer_generated_normals_are_source_normals":false,
        "environment_adoption":false,
        "indexed_snapshot":snapshot,
        "truth_boundary":"Environment records the exact post-normal indexed Godot receiver arrays so Geometry's hard-normal quotient can be rebound by material role + transformed position. This observation does not claim source hard-normal preservation, source-normal equivalence, Technical-Art transport acceptance, Runtime/device acceptance or default Environment adoption."
    }
    return result

func write_receipt()->void:
    receipt["environment_building_planar_role_quotient_receiving_result"]="CANDIDATE_EXACT_POSITION_QUOTIENT_REBOUND"
    receipt["environment_building_planar_role_quotient_geometry_head"]=BUILDING_QUOTIENT_GEOMETRY_HEAD
    receipt["environment_building_planar_role_consumer_id"]=BUILDING_QUOTIENT_CONSUMER_ID
    receipt["environment_building_planar_role_quotient_receiving_truth_boundary"]="The current-world receiver is observed for exact role+position quotient comparison only. Source hard-normal identity, generated-normal equivalence, default adoption, Technical-Art transport, target-device Runtime and Art/QA remain separate gates."
    super.write_receipt()
