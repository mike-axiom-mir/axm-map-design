extends "res://atmosphere_current_world_object_selected_roughness_readiness_observe.gd"

const SELECTED_SEGMENTATION_STATE := "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACES_INDEPENDENTLY_ADDRESSABLE__UV0_AND_SELECTED_ROUGHNESS_ADOPTION_HELD"
const SELECTED_SEGMENTATION_RULE := "EXACT_SOURCE_SURFACE_SEGMENTATION_MAY_PRECEDE_UV_BINDING_ONLY_WHEN_PARENT_MATERIAL_AND_DIRECTION_FIELDS_ARE_PRESERVED_AND_REAL_SCENE_CONTINUITY_IS_RETESTED"
const LID_SURFACE_ID := "lid_inner_service_surface"
const FRONT_SURFACE_ID := "front_service_panel_outer_service_surface"
const LID_SOURCE_TRIANGLES := [12, 13]
const FRONT_SOURCE_TRIANGLES := [28, 29]
const RECEIVER_MATERIAL_ORDER := ["shell_coating", "service_dark", "hardware_steel", "rubber_guard", "interface_orange"]

func _as_int_set(values:Array)->Dictionary:
    var result:Dictionary={}
    for raw in values:
        result[int(raw)]=true
    return result

func _segment_surface(
    destination:ArrayMesh,
    source_arrays:Array,
    source_triangle_indices:Array,
    chosen_triangle_indices:Array,
    material:Material,
    segment_id:String,
    material_id:String,
    selected_surface_id:String
)->Dictionary:
    if source_arrays.size()<=Mesh.ARRAY_INDEX:
        fail("selected surface segmentation source array layout drift")
        return {}
    var vertices=source_arrays[Mesh.ARRAY_VERTEX]
    var normals=source_arrays[Mesh.ARRAY_NORMAL]
    var parent_indices=source_arrays[Mesh.ARRAY_INDEX]
    if typeof(vertices)!=TYPE_PACKED_VECTOR3_ARRAY or typeof(normals)!=TYPE_PACKED_VECTOR3_ARRAY:
        fail("selected surface segmentation expected exact parent vertex/normal arrays")
        return {}
    if typeof(parent_indices)!=TYPE_PACKED_INT32_ARRAY:
        fail("selected surface segmentation requires exact indexed parent triangle stream")
        return {}
    if normals.size()!=vertices.size() or parent_indices.size()!=source_triangle_indices.size()*3:
        fail("selected surface segmentation indexed parent cardinality drift")
        return {}
    var local_slot:Dictionary={}
    for slot in range(source_triangle_indices.size()):
        local_slot[int(source_triangle_indices[slot])]=slot
    var chosen_indices:=PackedInt32Array()
    for raw_tri in chosen_triangle_indices:
        var tri_index:=int(raw_tri)
        if not local_slot.has(tri_index):
            fail("selected surface segmentation requested triangle outside parent material surface")
            return {}
        var slot:=int(local_slot[tri_index])
        for corner in range(3):
            var parent_index_offset:=slot*3+corner
            var parent_vertex_index:=int(parent_indices[parent_index_offset])
            if parent_vertex_index<0 or parent_vertex_index>=vertices.size():
                fail("selected surface segmentation parent index references invalid vertex")
                return {}
            chosen_indices.append(parent_vertex_index)
    var segmented_arrays:=source_arrays.duplicate(true)
    segmented_arrays[Mesh.ARRAY_INDEX]=chosen_indices
    destination.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,segmented_arrays)
    destination.surface_set_material(destination.get_surface_count()-1,material)
    return {
        "segment_id":segment_id,
        "material_id":material_id,
        "selected_surface_id":selected_surface_id,
        "triangle_count":chosen_triangle_indices.size(),
        "source_triangle_indices":chosen_triangle_indices.duplicate(),
        "parent_vertex_and_normal_fields_reused":true,
        "parent_index_stream_subset_reused":true
    }

func _uv0_count(mesh:ArrayMesh)->int:
    var total:=0
    for surface_index in range(mesh.get_surface_count()):
        var arrays:=mesh.surface_get_arrays(surface_index)
        if arrays.size()<=Mesh.ARRAY_TEX_UV:
            fail("selected surface segmentation mesh array layout drift")
            return -1
        var uv_value=arrays[Mesh.ARRAY_TEX_UV]
        if uv_value!=null:
            if typeof(uv_value)!=TYPE_PACKED_VECTOR2_ARRAY:
                fail("selected surface segmentation UV0 type drift")
                return -1
            total+=uv_value.size()
    return total

func _build_segmented_receiver(source:Dictionary,parent_mesh:ArrayMesh)->Dictionary:
    if parent_mesh.get_surface_count()!=5:
        fail("selected surface segmentation requires exact five-surface parent receiver")
        return {}
    var proof=source.get("object_material_family_receiving",{}) as Dictionary
    var partition=proof.get("surface_triangle_indices",{}) as Dictionary
    if partition.is_empty():
        fail("selected surface segmentation missing exact parent material partition")
        return {}
    var shell_indices=partition.get("shell_coating",[]) as Array
    var service_indices=partition.get("service_dark",[]) as Array
    if shell_indices.size()!=24 or service_indices.size()!=12:
        fail("selected surface segmentation parent shell/service partition cardinality drift")
        return {}
    var shell_set:=_as_int_set(shell_indices)
    var service_set:=_as_int_set(service_indices)
    for tri in LID_SOURCE_TRIANGLES:
        if not shell_set.has(int(tri)):
            fail("lid selected face no longer resides in parent shell_coating receiver")
            return {}
    for tri in FRONT_SOURCE_TRIANGLES:
        if not service_set.has(int(tri)):
            fail("front selected face no longer resides in parent service_dark receiver")
            return {}

    var lid_set:=_as_int_set(LID_SOURCE_TRIANGLES)
    var front_set:=_as_int_set(FRONT_SOURCE_TRIANGLES)
    var shell_remainder:Array=[]
    var service_remainder:Array=[]
    for raw in shell_indices:
        if not lid_set.has(int(raw)):
            shell_remainder.append(int(raw))
    for raw in service_indices:
        if not front_set.has(int(raw)):
            service_remainder.append(int(raw))
    if shell_remainder.size()!=22 or service_remainder.size()!=10:
        fail("selected surface segmentation remainder cardinality drift")
        return {}

    var segmented:=ArrayMesh.new()
    var segments:Array=[]
    for material_index in range(RECEIVER_MATERIAL_ORDER.size()):
        var material_id:=String(RECEIVER_MATERIAL_ORDER[material_index])
        var source_arrays:=parent_mesh.surface_get_arrays(material_index)
        var parent_material:=parent_mesh.surface_get_material(material_index)
        if parent_material==null:
            fail("selected surface segmentation parent material missing")
            return {}
        var source_indices=partition.get(material_id,[]) as Array
        var appended:Array=[]
        if material_id=="shell_coating":
            appended.append(_segment_surface(segmented,source_arrays,source_indices,shell_remainder,parent_material,"shell_coating_remainder",material_id,""))
            appended.append(_segment_surface(segmented,source_arrays,source_indices,LID_SOURCE_TRIANGLES,parent_material,LID_SURFACE_ID,material_id,LID_SURFACE_ID))
        elif material_id=="service_dark":
            appended.append(_segment_surface(segmented,source_arrays,source_indices,service_remainder,parent_material,"service_dark_remainder",material_id,""))
            appended.append(_segment_surface(segmented,source_arrays,source_indices,FRONT_SOURCE_TRIANGLES,parent_material,FRONT_SURFACE_ID,material_id,FRONT_SURFACE_ID))
        else:
            appended.append(_segment_surface(segmented,source_arrays,source_indices,source_indices,parent_material,material_id,material_id,""))
        for row in appended:
            if (row as Dictionary).is_empty():
                return {}
            segments.append(row)

    if segmented.get_surface_count()!=7 or segments.size()!=7:
        fail("selected surface segmentation did not produce exact seven-surface receiver")
        return {}
    var expected_counts:=[22,2,10,2,656,96,24]
    var total_triangles:=0
    for index in range(segments.size()):
        var row=segments[index] as Dictionary
        if row.is_empty() or int(row.get("triangle_count",-1))!=int(expected_counts[index]):
            fail("selected surface segmentation exact segment cardinality drift")
            return {}
        total_triangles+=int(row["triangle_count"])
    if total_triangles!=812:
        fail("selected surface segmentation host triangle coverage drift")
        return {}
    var uv0_total:=_uv0_count(segmented)
    if uv0_total!=0:
        fail("selected surface segmentation unexpectedly introduced UV0")
        return {}
    return {
        "mesh":segmented,
        "observation":{
            "schema":"axm.environment-object-selected-surface-segmentation-observation/v0.1",
            "state":SELECTED_SEGMENTATION_STATE,
            "reusable_rule":SELECTED_SEGMENTATION_RULE,
            "source_surface_correspondence_head":"be4e0dbf245c4658c48b902024cf397cc6557b5f",
            "current_receiver_materials_head":OBJECT_MATERIALS_HEAD,
            "current_receiver_material_profile_sha256":OBJECT_PROFILE_SHA256,
            "pre_split_surface_count":5,
            "post_split_surface_count":7,
            "unique_material_count":5,
            "total_triangles":total_triangles,
            "segments":segments,
            "selected_surface_segments":{
                LID_SURFACE_ID:{"surface_index":1,"material_id":"shell_coating","source_triangle_indices":LID_SOURCE_TRIANGLES.duplicate()},
                FRONT_SURFACE_ID:{"surface_index":3,"material_id":"service_dark","source_triangle_indices":FRONT_SOURCE_TRIANGLES.duplicate()}
            },
            "uv0_total_count":uv0_total,
            "selected_roughness_adopted":false,
            "environment_adoption":false,
            "parent_material_objects_reused":true,
            "parent_vertex_and_normal_fields_reused":true,
            "parent_index_stream_subsets_reused":true,
            "truth_boundary":"The Map receiver only splits the exact two source-owned faces into independently addressable draw surfaces while reusing parent vertex positions, parent generated normals, parent index references and the exact parent material objects. No UV0 or selected roughness is added."
        }
    }

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_static_source(root3d,source,cull_target_asset_id)
    if String(result.get("asset_id",""))!=OBJECT_ASSET_ID:
        return result
    if root3d.get_child_count()!=child_count_before+1:
        fail("selected surface segmentation expected exactly one emitted Object child")
        return {}
    var emitted:=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is MeshInstance3D):
        fail("selected surface segmentation Object child is not MeshInstance3D")
        return {}
    var node:=emitted as MeshInstance3D
    if not (node.mesh is ArrayMesh):
        fail("selected surface segmentation parent mesh is not ArrayMesh")
        return {}
    var built:=_build_segmented_receiver(source,node.mesh as ArrayMesh)
    if built.is_empty():
        return {}
    node.mesh=built["mesh"] as ArrayMesh
    result["surface_count"]=7
    result["environment_object_selected_surface_segmentation"]=built["observation"]
    return result

func write_receipt()->void:
    receipt["environment_object_selected_surface_segmentation_state"]=SELECTED_SEGMENTATION_STATE
    receipt["environment_object_selected_surface_segmentation_rule"]=SELECTED_SEGMENTATION_RULE
    receipt["environment_object_selected_surface_segmentation_truth_boundary"]="Exact receiving partition only. The real Building + Nature + Object + footprint + Weather scene is rerendered after splitting the two source-owned faces; UV0 and selected roughness adoption remain held."
    super.write_receipt()
