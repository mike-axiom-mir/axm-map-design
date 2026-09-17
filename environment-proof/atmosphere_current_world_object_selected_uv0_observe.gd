extends "res://atmosphere_current_world_object_selected_surface_segmentation_observe.gd"

const SELECTED_UV0_STATE := "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACE_UV0_BOUND__ROUGHNESS_ADOPTION_HELD"
const SELECTED_UV0_RULE := "EXACT_RECEIVER_UV_BINDING_MUST_MATCH_PINNED_SOURCE_VERTEX_IDENTITY_TO_TEXCOORD_IDENTITY_BEFORE_SPATIAL_MATERIAL_FIELD_REVIEW"
const PARENT_ENVIRONMENT_HEAD := "8856745aa0f3de626599afa35fe16a92ae68fa50"
const OBJECT_SOURCE_HEAD := "d3fa10a270faae7925811f44f03381fe5c5d0215"
const OBJECT_HOST_SOURCE_SHA256 := "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
const TECHNICAL_ART_HEAD := "1bcdbae786e02f3ca46a89e4e0ff608d74f364b4"
const MATERIALS_AUTHORITY_HEAD := "0515a2d5ad2c7a1eb545f2b7b327b7367530dfca"
const TECHNICAL_ART_SURFACE_SPEC_SHA256 := "1f87a7b287c7caa138deee64b687d0aba67a3485ddeae6f80a38ebd906a86aec"
const TA_SURFACE_SPEC_PATH := "res://generated/object-selected-roughness-ta-surface.json"
const LID_UV_SURFACE_INDEX := 1
const FRONT_UV_SURFACE_INDEX := 3
const LID_SOURCE_VERTEX_TO_TA_CORNER := {8:0,9:3,10:2,11:1}
const FRONT_SOURCE_VERTEX_TO_TA_CORNER := {16:0,17:1,20:3,21:2}

func _load_ta_surface_spec()->Dictionary:
    if not FileAccess.file_exists(TA_SURFACE_SPEC_PATH):
        fail("selected UV0 exact Technical Art surface spec missing")
        return {}
    var file:=FileAccess.open(TA_SURFACE_SPEC_PATH,FileAccess.READ)
    if file==null:
        fail("selected UV0 exact Technical Art surface spec unreadable")
        return {}
    var parsed=JSON.parse_string(file.get_as_text())
    if typeof(parsed)!=TYPE_DICTIONARY:
        fail("selected UV0 exact Technical Art surface spec invalid JSON")
        return {}
    var spec:=parsed as Dictionary
    if String(spec.get("schema",""))!="axm.surface-3d/v0.1":
        fail("selected UV0 exact Technical Art surface spec schema drift")
        return {}
    var primitives=spec.get("primitives",[]) as Array
    if primitives.size()!=2:
        fail("selected UV0 requires exact two Technical Art source surfaces")
        return {}
    return spec

func _primitive(spec:Dictionary,surface_id:String)->Dictionary:
    var rows:Array=[]
    for raw in spec.get("primitives",[]) as Array:
        var row=raw as Dictionary
        if String(row.get("id",""))==surface_id:
            rows.append(row)
    if rows.size()!=1:
        fail("selected UV0 Technical Art primitive identity drift: "+surface_id)
        return {}
    return rows[0] as Dictionary

func _vector2_from_array(values:Array)->Vector2:
    if values.size()!=2:
        fail("selected UV0 Technical Art texcoord cardinality drift")
        return Vector2.ZERO
    return Vector2(float(values[0]),float(values[1]))

func _exact_ta_index_topology(indices:Array)->bool:
    var expected:=[0,2,1,0,3,2]
    if indices.size()!=expected.size():
        return false
    for i in range(expected.size()):
        if int(indices[i])!=expected[i] or float(indices[i])!=float(expected[i]):
            return false
    return true

func _selected_source_vertex_ids(source:Dictionary,source_triangle_indices:Array)->Dictionary:
    if String(source.get("source_head",""))!=OBJECT_SOURCE_HEAD or String(source.get("source_sha256",""))!=OBJECT_HOST_SOURCE_SHA256:
        fail("selected UV0 Object source identity drift")
        return {}
    var triangles=source.get("triangles",[]) as Array
    var vertices=source.get("vertices_source_xyz_m",[]) as Array
    if triangles.size()!=812 or vertices.size()!=468:
        fail("selected UV0 exact Object source topology cardinality drift")
        return {}
    var ids:Dictionary={}
    for raw_triangle_index in source_triangle_indices:
        var triangle_index:=int(raw_triangle_index)
        if triangle_index<0 or triangle_index>=triangles.size():
            fail("selected UV0 source triangle index out of range")
            return {}
        var tri=triangles[triangle_index] as Array
        if tri.size()!=3:
            fail("selected UV0 source triangle arity drift")
            return {}
        for raw_vertex_index in tri:
            var source_vertex_index:=int(raw_vertex_index)
            if source_vertex_index<0 or source_vertex_index>=vertices.size():
                fail("selected UV0 source vertex index out of range")
                return {}
            ids[source_vertex_index]=true
    if ids.size()!=4:
        fail("selected UV0 source-owned selected face must resolve to exact four source vertices")
        return {}
    return ids

func _mapping_keys(mapping:Dictionary)->Dictionary:
    var result:Dictionary={}
    for raw_key in mapping.keys():
        result[int(raw_key)]=true
    return result

func _same_int_keyset(a:Dictionary,b:Dictionary)->bool:
    if a.size()!=b.size():
        return false
    for raw_key in a.keys():
        if not b.has(int(raw_key)):
            return false
    return true

func _source_world_position_godot(source:Dictionary,source_vertex_index:int)->Vector3:
    var vertices=source.get("vertices_source_xyz_m",[]) as Array
    if source_vertex_index<0 or source_vertex_index>=vertices.size():
        fail("selected UV0 source world vertex index out of range")
        return Vector3.ZERO
    return gvec(vertices[source_vertex_index] as Array)

func _bind_selected_surface_uv(
    source_arrays:Array,
    primitive:Dictionary,
    source:Dictionary,
    source_triangle_indices:Array,
    source_vertex_to_ta_corner:Dictionary,
    surface_id:String,
    surface_index:int
)->Dictionary:
    if source_arrays.size()<=Mesh.ARRAY_TEX_UV:
        fail("selected UV0 receiver array layout drift")
        return {}
    var vertices=source_arrays[Mesh.ARRAY_VERTEX]
    var normals=source_arrays[Mesh.ARRAY_NORMAL]
    var indices=source_arrays[Mesh.ARRAY_INDEX]
    if typeof(vertices)!=TYPE_PACKED_VECTOR3_ARRAY or typeof(normals)!=TYPE_PACKED_VECTOR3_ARRAY:
        fail("selected UV0 requires exact segmented parent position/normal arrays")
        return {}
    if typeof(indices)!=TYPE_PACKED_INT32_ARRAY or indices.size()!=6:
        fail("selected UV0 requires exact two-triangle selected receiver segment")
        return {}
    var old_uv=source_arrays[Mesh.ARRAY_TEX_UV]
    if old_uv!=null:
        if typeof(old_uv)!=TYPE_PACKED_VECTOR2_ARRAY or old_uv.size()!=0:
            fail("selected UV0 parent selected segment unexpectedly already carries UV0")
            return {}

    var ta_positions=primitive.get("positions",[]) as Array
    var ta_texcoords=primitive.get("texcoords",[]) as Array
    var ta_indices=primitive.get("indices",[]) as Array
    if ta_positions.size()!=4 or ta_texcoords.size()!=4 or not _exact_ta_index_topology(ta_indices):
        fail("selected UV0 Technical Art primitive exact four-corner identity drift")
        return {}

    var selected_source_ids:=_selected_source_vertex_ids(source,source_triangle_indices)
    if selected_source_ids.is_empty() or not _same_int_keyset(selected_source_ids,_mapping_keys(source_vertex_to_ta_corner)):
        fail("selected UV0 source vertex-to-Technical-Art corner adapter no longer matches exact selected source face")
        return {}
    var used_ta_corners:Dictionary={}
    for raw_source_vertex in source_vertex_to_ta_corner.keys():
        var ta_corner:=int(source_vertex_to_ta_corner[raw_source_vertex])
        if ta_corner<0 or ta_corner>=4 or used_ta_corners.has(ta_corner):
            fail("selected UV0 source vertex-to-Technical-Art corner adapter is not a bijection")
            return {}
        used_ta_corners[ta_corner]=true
    if used_ta_corners.size()!=4:
        fail("selected UV0 source vertex-to-Technical-Art corner adapter does not cover all four TA corners")
        return {}

    var referenced:Dictionary={}
    for raw_index in indices:
        var vertex_index:=int(raw_index)
        if vertex_index<0 or vertex_index>=vertices.size():
            fail("selected UV0 selected segment references invalid parent vertex")
            return {}
        referenced[vertex_index]=true
    if referenced.size()!=4:
        fail("selected UV0 selected segment must reference exactly four receiver vertices")
        return {}

    var uv:=PackedVector2Array()
    uv.resize(vertices.size())
    var matched_source:Dictionary={}
    var maximum_delta:=0.0
    var pairs:Array=[]
    var receiver_vertex_indices:Array=referenced.keys()
    receiver_vertex_indices.sort()
    for raw_receiver_vertex in receiver_vertex_indices:
        var receiver_vertex:=int(raw_receiver_vertex)
        var position:Vector3=vertices[receiver_vertex]
        var best_source_vertex:=-1
        var best_delta:=INF
        for raw_source_vertex in selected_source_ids.keys():
            var source_vertex:=int(raw_source_vertex)
            if matched_source.has(source_vertex):
                continue
            var source_position:=_source_world_position_godot(source,source_vertex)
            var delta:=position.distance_to(source_position)
            if delta<best_delta:
                best_delta=delta
                best_source_vertex=source_vertex
        if best_source_vertex<0 or best_delta>0.000001:
            fail("selected UV0 receiver vertex cannot bind exact current-world source vertex identity")
            return {}
        matched_source[best_source_vertex]=true
        maximum_delta=max(maximum_delta,best_delta)
        var ta_corner:=int(source_vertex_to_ta_corner[best_source_vertex])
        var texcoord:=_vector2_from_array(ta_texcoords[ta_corner] as Array)
        uv[receiver_vertex]=texcoord
        var source_position:=_source_world_position_godot(source,best_source_vertex)
        pairs.append({
            "receiver_vertex_index":receiver_vertex,
            "source_vertex_index":best_source_vertex,
            "technical_art_corner_index":ta_corner,
            "receiver_position_godot":[position.x,position.y,position.z],
            "source_world_position_godot":[source_position.x,source_position.y,source_position.z],
            "texcoord":[texcoord.x,texcoord.y],
            "position_delta_m":best_delta
        })
    if matched_source.size()!=4:
        fail("selected UV0 did not consume all four exact source vertices exactly once")
        return {}

    var unused_zero:=true
    for vertex_index in range(uv.size()):
        if not referenced.has(vertex_index) and uv[vertex_index]!=Vector2.ZERO:
            unused_zero=false
            break
    if not unused_zero:
        fail("selected UV0 unused receiver UV slots must remain deterministic zero")
        return {}

    var candidate_arrays:=source_arrays.duplicate(true)
    candidate_arrays[Mesh.ARRAY_TEX_UV]=uv
    return {
        "arrays":candidate_arrays,
        "observation":{
            "surface_id":surface_id,
            "surface_index":surface_index,
            "source_triangle_indices":source_triangle_indices.duplicate(),
            "source_vertex_indices":selected_source_ids.keys(),
            "referenced_vertex_count":referenced.size(),
            "matched_source_vertex_count":matched_source.size(),
            "matched_ta_corner_count":used_ta_corners.size(),
            "maximum_source_world_position_delta_m":maximum_delta,
            "exact_source_vertex_to_texcoord_identity_bound":true,
            "source_vertex_to_technical_art_corner":source_vertex_to_ta_corner.duplicate(),
            "ta_transport_positions_used_as_source_positions":false,
            "uv0_array_count":uv.size(),
            "unused_uv_values_zero":unused_zero,
            "source_vertex_to_texcoord_pairs":pairs
        }
    }

func _surface_has_uv0(mesh:ArrayMesh,surface_index:int)->bool:
    var arrays:=mesh.surface_get_arrays(surface_index)
    if arrays.size()<=Mesh.ARRAY_TEX_UV:
        fail("selected UV0 candidate array layout drift")
        return true
    var uv_value=arrays[Mesh.ARRAY_TEX_UV]
    if uv_value==null:
        return false
    if typeof(uv_value)!=TYPE_PACKED_VECTOR2_ARRAY:
        fail("selected UV0 candidate UV0 type drift")
        return true
    return uv_value.size()>0

func _build_uv0_receiver(source:Dictionary,parent_mesh:ArrayMesh,spec:Dictionary)->Dictionary:
    if parent_mesh.get_surface_count()!=7:
        fail("selected UV0 requires exact seven-surface segmented parent")
        return {}
    var candidate:=ArrayMesh.new()
    var selected_observations:Dictionary={}
    var total_triangles:=0
    for surface_index in range(parent_mesh.get_surface_count()):
        var source_arrays:=parent_mesh.surface_get_arrays(surface_index)
        var material:=parent_mesh.surface_get_material(surface_index)
        if material==null:
            fail("selected UV0 segmented parent material missing")
            return {}
        var arrays_to_add:=source_arrays
        if surface_index==LID_UV_SURFACE_INDEX:
            var lid:=_bind_selected_surface_uv(source_arrays,_primitive(spec,LID_SURFACE_ID),source,LID_SOURCE_TRIANGLES,LID_SOURCE_VERTEX_TO_TA_CORNER,LID_SURFACE_ID,surface_index)
            if lid.is_empty():
                return {}
            arrays_to_add=lid["arrays"] as Array
            selected_observations[LID_SURFACE_ID]=lid["observation"]
        elif surface_index==FRONT_UV_SURFACE_INDEX:
            var front:=_bind_selected_surface_uv(source_arrays,_primitive(spec,FRONT_SURFACE_ID),source,FRONT_SOURCE_TRIANGLES,FRONT_SOURCE_VERTEX_TO_TA_CORNER,FRONT_SURFACE_ID,surface_index)
            if front.is_empty():
                return {}
            arrays_to_add=front["arrays"] as Array
            selected_observations[FRONT_SURFACE_ID]=front["observation"]
        candidate.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays_to_add)
        candidate.surface_set_material(candidate.get_surface_count()-1,material)
        total_triangles+=candidate.surface_get_array_index_len(candidate.get_surface_count()-1)/3

    if candidate.get_surface_count()!=7 or total_triangles!=812:
        fail("selected UV0 candidate receiver structure drift")
        return {}
    if selected_observations.size()!=2:
        fail("selected UV0 candidate did not bind exact two selected surfaces")
        return {}
    for surface_index in range(candidate.get_surface_count()):
        var should_have_uv:=surface_index==LID_UV_SURFACE_INDEX or surface_index==FRONT_UV_SURFACE_INDEX
        if _surface_has_uv0(candidate,surface_index)!=should_have_uv:
            fail("selected UV0 presence leaked or disappeared across receiver surfaces")
            return {}
    return {
        "mesh":candidate,
        "observation":{
            "schema":"axm.environment-object-selected-uv0-current-world-observation/v0.2",
            "state":SELECTED_UV0_STATE,
            "reusable_rule":SELECTED_UV0_RULE,
            "parent_environment_head":PARENT_ENVIRONMENT_HEAD,
            "object_source_head":OBJECT_SOURCE_HEAD,
            "object_host_source_sha256":OBJECT_HOST_SOURCE_SHA256,
            "technical_art_head":TECHNICAL_ART_HEAD,
            "materials_authority_head":MATERIALS_AUTHORITY_HEAD,
            "technical_art_surface_spec_sha256":TECHNICAL_ART_SURFACE_SPEC_SHA256,
            "receiver_surface_count":candidate.get_surface_count(),
            "total_triangles":total_triangles,
            "selected_surfaces":selected_observations,
            "non_selected_surfaces_uv0_absent":true,
            "selected_roughness_adopted":false,
            "environment_adoption":false,
            "parent_material_objects_reused":true,
            "position_normal_index_fields_reused":true,
            "truth_boundary":"Exact UV0 receiving identity only. The two already-segmented source-owned faces reuse the current-world Object source vertex identity to select the exact Technical Art TEXCOORD_0 corner values. Downstream TA proof positions are not promoted to source/world positions. Material objects, scalar values, textures, positions, normals and triangle/index membership remain unchanged. Selected roughness is intentionally not adopted in this pass."
        }
    }

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_static_source(root3d,source,cull_target_asset_id)
    if String(result.get("asset_id",""))!=OBJECT_ASSET_ID:
        return result
    if root3d.get_child_count()!=child_count_before+1:
        fail("selected UV0 expected exactly one emitted Object child")
        return {}
    var emitted:=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is MeshInstance3D):
        fail("selected UV0 Object child is not MeshInstance3D")
        return {}
    var node:=emitted as MeshInstance3D
    if not (node.mesh is ArrayMesh):
        fail("selected UV0 segmented parent mesh is not ArrayMesh")
        return {}
    var spec:=_load_ta_surface_spec()
    if spec.is_empty():
        return {}
    var built:=_build_uv0_receiver(source,node.mesh as ArrayMesh,spec)
    if built.is_empty():
        return {}
    node.mesh=built["mesh"] as ArrayMesh
    result["surface_count"]=7
    result["environment_object_selected_uv0_current_world"]=built["observation"]
    return result

func write_receipt()->void:
    receipt["environment_object_selected_uv0_current_world_state"]=SELECTED_UV0_STATE
    receipt["environment_object_selected_uv0_current_world_rule"]=SELECTED_UV0_RULE
    receipt["environment_object_selected_uv0_object_source_head"]=OBJECT_SOURCE_HEAD
    receipt["environment_object_selected_uv0_object_host_source_sha256"]=OBJECT_HOST_SOURCE_SHA256
    receipt["environment_object_selected_uv0_technical_art_head"]=TECHNICAL_ART_HEAD
    receipt["environment_object_selected_uv0_materials_authority_head"]=MATERIALS_AUTHORITY_HEAD
    receipt["environment_object_selected_uv0_truth_boundary"]="Exact receiving UV0 only. Current-world receiver positions are rebound to exact pinned Object source vertex indices before TA TEXCOORD_0 corner values are consumed; downstream transport positions are not treated as source positions. The real Building + Nature + Object + footprint + Weather scene is rerendered before any selected roughness texture/material adoption."
    super.write_receipt()
