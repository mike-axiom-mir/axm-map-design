extends "res://atmosphere_current_world_object_selected_surface_segmentation_observe.gd"

const SELECTED_UV0_STATE := "PASS_CURRENT_WORLD_OBJECT_SELECTED_SERVICE_SURFACE_UV0_BOUND__ROUGHNESS_ADOPTION_HELD"
const SELECTED_UV0_RULE := "EXACT_RECEIVER_UV_BINDING_MUST_MATCH_PINNED_SOURCE_SURFACE_POSITION_TO_TEXCOORD_IDENTITY_BEFORE_SPATIAL_MATERIAL_FIELD_REVIEW"
const PARENT_ENVIRONMENT_HEAD := "8856745aa0f3de626599afa35fe16a92ae68fa50"
const TECHNICAL_ART_HEAD := "1bcdbae786e02f3ca46a89e4e0ff608d74f364b4"
const MATERIALS_AUTHORITY_HEAD := "0515a2d5ad2c7a1eb545f2b7b327b7367530dfca"
const TECHNICAL_ART_SURFACE_SPEC_SHA256 := "1f87a7b287c7caa138deee64b687d0aba67a3485ddeae6f80a38ebd906a86aec"
const TA_SURFACE_SPEC_PATH := "res://generated/object-selected-roughness-ta-surface.json"
const LID_UV_SURFACE_INDEX := 1
const FRONT_UV_SURFACE_INDEX := 3

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

func _vector3_from_array(values:Array)->Vector3:
    if values.size()!=3:
        fail("selected UV0 Technical Art position cardinality drift")
        return Vector3.ZERO
    return Vector3(float(values[0]),float(values[1]),float(values[2]))

func _ta_uc_position_to_current_world_godot(values:Array)->Vector3:
    # Technical Art's pinned donor explicitly records source +X right/+Y forward/+Z up
    # -> UC/glTF +X right/+Y up/+Z forward. The current Map receiver uses gvec(),
    # source -> Godot [x,z,-y]. Therefore exact TA UC positions map to [x,y,-z]
    # before a receiver-space position/UV identity comparison is meaningful.
    var uc:=_vector3_from_array(values)
    return Vector3(uc.x,uc.y,-uc.z)

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

func _bind_selected_surface_uv(
    source_arrays:Array,
    primitive:Dictionary,
    surface_id:String,
    source_triangles:Array,
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
    var matched_ta:Dictionary={}
    var maximum_delta:=0.0
    var pairs:Array=[]
    var vertex_indices:Array=referenced.keys()
    vertex_indices.sort()
    for raw_vertex_index in vertex_indices:
        var vertex_index:=int(raw_vertex_index)
        var position:Vector3=vertices[vertex_index]
        var best_corner:=-1
        var best_delta:=INF
        for corner in range(ta_positions.size()):
            if matched_ta.has(corner):
                continue
            var ta_position:=_ta_uc_position_to_current_world_godot(ta_positions[corner] as Array)
            var delta:=position.distance_to(ta_position)
            if delta<best_delta:
                best_delta=delta
                best_corner=corner
        if best_corner<0 or best_delta>0.000001:
            fail("selected UV0 receiver position cannot bind exact Technical Art texcoord identity after pinned UC-to-Godot coordinate conversion")
            return {}
        matched_ta[best_corner]=true
        maximum_delta=max(maximum_delta,best_delta)
        var texcoord:=_vector2_from_array(ta_texcoords[best_corner] as Array)
        uv[vertex_index]=texcoord
        pairs.append({
            "receiver_vertex_index":vertex_index,
            "technical_art_corner_index":best_corner,
            "position_godot":[position.x,position.y,position.z],
            "technical_art_position_uc":ta_positions[best_corner],
            "texcoord":[texcoord.x,texcoord.y],
            "position_delta_m":best_delta
        })
    if matched_ta.size()!=4:
        fail("selected UV0 did not consume all four Technical Art corners exactly once")
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
            "source_triangle_indices":source_triangles.duplicate(),
            "referenced_vertex_count":referenced.size(),
            "matched_ta_corner_count":matched_ta.size(),
            "maximum_position_match_delta_m":maximum_delta,
            "exact_position_to_texcoord_pairs_bound":true,
            "technical_art_position_space":"UC_GLTF__X_RIGHT_Y_UP_Z_FORWARD",
            "receiver_position_space":"GODOT_CURRENT_WORLD__X_RIGHT_Y_UP_Z_BACK_FROM_SOURCE_FORWARD",
            "coordinate_conversion":"TA_UC_XYZ_TO_GODOT_X_Y_NEG_Z",
            "uv0_array_count":uv.size(),
            "unused_uv_values_zero":unused_zero,
            "position_to_texcoord_pairs":pairs
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

func _build_uv0_receiver(parent_mesh:ArrayMesh,spec:Dictionary)->Dictionary:
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
            var lid:=_bind_selected_surface_uv(source_arrays,_primitive(spec,LID_SURFACE_ID),LID_SURFACE_ID,LID_SOURCE_TRIANGLES,surface_index)
            if lid.is_empty():
                return {}
            arrays_to_add=lid["arrays"] as Array
            selected_observations[LID_SURFACE_ID]=lid["observation"]
        elif surface_index==FRONT_UV_SURFACE_INDEX:
            var front:=_bind_selected_surface_uv(source_arrays,_primitive(spec,FRONT_SURFACE_ID),FRONT_SURFACE_ID,FRONT_SOURCE_TRIANGLES,surface_index)
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
            "schema":"axm.environment-object-selected-uv0-current-world-observation/v0.1",
            "state":SELECTED_UV0_STATE,
            "reusable_rule":SELECTED_UV0_RULE,
            "parent_environment_head":PARENT_ENVIRONMENT_HEAD,
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
            "truth_boundary":"Exact UV0 receiving identity only. The two already-segmented source-owned faces receive the exact Technical Art position-to-texcoord pairs after explicit pinned UC/glTF-to-current-world Godot coordinate conversion, while all material objects, scalar values, textures, positions, normals and triangle/index membership remain unchanged. Selected roughness is intentionally not adopted in this pass."
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
    var built:=_build_uv0_receiver(node.mesh as ArrayMesh,spec)
    if built.is_empty():
        return {}
    node.mesh=built["mesh"] as ArrayMesh
    result["surface_count"]=7
    result["environment_object_selected_uv0_current_world"]=built["observation"]
    return result

func write_receipt()->void:
    receipt["environment_object_selected_uv0_current_world_state"]=SELECTED_UV0_STATE
    receipt["environment_object_selected_uv0_current_world_rule"]=SELECTED_UV0_RULE
    receipt["environment_object_selected_uv0_technical_art_head"]=TECHNICAL_ART_HEAD
    receipt["environment_object_selected_uv0_materials_authority_head"]=MATERIALS_AUTHORITY_HEAD
    receipt["environment_object_selected_uv0_truth_boundary"]="Exact receiving UV0 only. TA positions are explicitly converted from pinned UC/glTF coordinates into the current-world Godot receiver frame; the real Building + Nature + Object + footprint + Weather scene is rerendered before any selected roughness texture/material adoption."
    super.write_receipt()
