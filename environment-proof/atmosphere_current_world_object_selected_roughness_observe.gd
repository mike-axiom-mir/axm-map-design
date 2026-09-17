extends "res://atmosphere_current_world_object_selected_uv0_observe.gd"

const SELECTED_ROUGHNESS_STATE := "PASS_CURRENT_WORLD_OBJECT_SELECTED_ROUGHNESS_APPEARANCE_CANDIDATE_BOUND__ENVIRONMENT_ADOPTION_HELD"
const SELECTED_APPEARANCE_RULE := "SPATIAL_MATERIAL_FIELD_MAY_ENTER_CURRENT_WORLD_REVIEW_ONLY_AFTER_EXACT_SURFACE_AND_UV_IDENTITY__APPEARANCE_AND_RUNTIME_ACCEPTANCE_REMAIN_SEPARATE"
const SELECTED_ROUGHNESS_PARENT_HEAD := "4eed6da68f746ca2849c89fa88533f82bc836b26"
const SELECTED_ROUGHNESS_PNG_PATH := "res://generated/object-selected-roughness.png"
const SELECTED_ROUGHNESS_PNG_SHA256 := "57cf746a9a7e0615884fe3c45c6c4df677c2bd0631def61b3ccb1684daa26949"
const SELECTED_FIELD_SCALAR_SHA256 := "b8d13c07f9b71278042b0d42d44b84579a3f327c6adf6723cae4c8c8f06dd38e"
const SELECTED_ROUGHNESS_WIDTH := 512
const SELECTED_ROUGHNESS_HEIGHT := 512
const SELECTED_ROUGHNESS_MIN_R8 := 153
const SELECTED_ROUGHNESS_MAX_R8 := 183
const SELECTED_ROUGHNESS_UNIQUE_R8 := 31

func _sha256_bytes(data:PackedByteArray)->String:
    var context:=HashingContext.new()
    if context.start(HashingContext.HASH_SHA256)!=OK:
        return ""
    if context.update(data)!=OK:
        return ""
    return context.finish().hex_encode()

func _selected_scalar_summary(image:Image)->Dictionary:
    if image.get_width()!=SELECTED_ROUGHNESS_WIDTH or image.get_height()!=SELECTED_ROUGHNESS_HEIGHT:
        fail("selected roughness image dimensions drift")
        return {}
    var bytes:=PackedByteArray()
    bytes.resize(SELECTED_ROUGHNESS_WIDTH*SELECTED_ROUGHNESS_HEIGHT)
    var min_value:=255
    var max_value:=0
    var seen:Dictionary={}
    var index:=0
    for y in range(SELECTED_ROUGHNESS_HEIGHT):
        for x in range(SELECTED_ROUGHNESS_WIDTH):
            var value:=clampi(int(round(image.get_pixel(x,y).r*255.0)),0,255)
            bytes[index]=value
            index+=1
            min_value=mini(min_value,value)
            max_value=maxi(max_value,value)
            seen[value]=true
    return {
        "sha256":_sha256_bytes(bytes),
        "bytes":bytes.size(),
        "min":min_value,
        "max":max_value,
        "unique":seen.size()
    }

func _load_selected_roughness_texture()->Dictionary:
    if not FileAccess.file_exists(SELECTED_ROUGHNESS_PNG_PATH):
        fail("selected roughness PNG missing")
        return {}
    var png_bytes:=FileAccess.get_file_as_bytes(SELECTED_ROUGHNESS_PNG_PATH)
    var png_sha:=_sha256_bytes(png_bytes)
    if png_sha!=SELECTED_ROUGHNESS_PNG_SHA256:
        fail("selected roughness PNG identity drift")
        return {}
    var image:=Image.new()
    if image.load(SELECTED_ROUGHNESS_PNG_PATH)!=OK:
        fail("selected roughness PNG unreadable")
        return {}
    var summary:=_selected_scalar_summary(image)
    if summary.is_empty():
        return {}
    if String(summary.get("sha256",""))!=SELECTED_FIELD_SCALAR_SHA256:
        fail("selected roughness scalar R8 identity drift")
        return {}
    if int(summary.get("min",-1))!=SELECTED_ROUGHNESS_MIN_R8 or int(summary.get("max",-1))!=SELECTED_ROUGHNESS_MAX_R8 or int(summary.get("unique",-1))!=SELECTED_ROUGHNESS_UNIQUE_R8:
        fail("selected roughness scalar observation drift")
        return {}
    if image.generate_mipmaps()!=OK:
        fail("selected roughness mipmap generation failed")
        return {}
    return {
        "texture":ImageTexture.create_from_image(image),
        "png_sha256":png_sha,
        "scalar_summary":summary
    }

func _material_with_selected_roughness(parent:Material,texture:Texture2D,surface_id:String)->StandardMaterial3D:
    if not (parent is StandardMaterial3D):
        fail("selected roughness requires current StandardMaterial3D receiver: "+surface_id)
        return StandardMaterial3D.new()
    var material:=parent.duplicate(true) as StandardMaterial3D
    if material==null:
        fail("selected roughness material duplication failed: "+surface_id)
        return StandardMaterial3D.new()
    material.roughness=1.0
    material.roughness_texture=texture
    material.roughness_texture_channel=BaseMaterial3D.TEXTURE_CHANNEL_RED
    material.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
    material.texture_repeat=false
    return material

func _bind_selected_roughness(parent_mesh:ArrayMesh)->Dictionary:
    if parent_mesh.get_surface_count()!=7:
        fail("selected roughness requires exact seven-surface UV-bound receiver")
        return {}
    var loaded:=_load_selected_roughness_texture()
    if loaded.is_empty():
        return {}
    var texture:=loaded["texture"] as Texture2D
    var candidate:=ArrayMesh.new()
    var selected:Dictionary={}
    for surface_index in range(parent_mesh.get_surface_count()):
        var arrays:=parent_mesh.surface_get_arrays(surface_index)
        var material:=parent_mesh.surface_get_material(surface_index)
        if material==null:
            fail("selected roughness parent material missing")
            return {}
        var chosen:Material=material
        var selected_id:=""
        if surface_index==LID_UV_SURFACE_INDEX:
            selected_id=LID_SURFACE_ID
            chosen=_material_with_selected_roughness(material,texture,selected_id)
        elif surface_index==FRONT_UV_SURFACE_INDEX:
            selected_id=FRONT_SURFACE_ID
            chosen=_material_with_selected_roughness(material,texture,selected_id)
        candidate.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
        candidate.surface_set_material(candidate.get_surface_count()-1,chosen)
        if not selected_id.is_empty():
            var uv_value=arrays[Mesh.ARRAY_TEX_UV]
            if typeof(uv_value)!=TYPE_PACKED_VECTOR2_ARRAY or (uv_value as PackedVector2Array).size()==0:
                fail("selected roughness target surface lost UV0: "+selected_id)
                return {}
            var parent_std:=material as StandardMaterial3D
            var candidate_std:=chosen as StandardMaterial3D
            selected[selected_id]={
                "surface_index":surface_index,
                "uv0_count":(uv_value as PackedVector2Array).size(),
                "parent_albedo":[parent_std.albedo_color.r,parent_std.albedo_color.g,parent_std.albedo_color.b,parent_std.albedo_color.a],
                "parent_metallic":parent_std.metallic,
                "parent_scalar_roughness":parent_std.roughness,
                "candidate_roughness_scalar_multiplier":candidate_std.roughness,
                "selected_roughness_texture_bound":candidate_std.roughness_texture!=null,
                "selected_roughness_texture_channel":"RED",
                "base_color_and_metallic_preserved":parent_std.albedo_color==candidate_std.albedo_color and absf(parent_std.metallic-candidate_std.metallic)<=0.0000001
            }
    if selected.size()!=2:
        fail("selected roughness did not bind exact two selected surfaces")
        return {}
    for surface_index in range(candidate.get_surface_count()):
        var mat:=candidate.surface_get_material(surface_index)
        if not (mat is StandardMaterial3D):
            fail("selected roughness candidate material type drift")
            return {}
        var std:=mat as StandardMaterial3D
        var should_have_texture:=surface_index==LID_UV_SURFACE_INDEX or surface_index==FRONT_UV_SURFACE_INDEX
        if (std.roughness_texture!=null)!=should_have_texture:
            fail("selected roughness texture leaked or disappeared across receiver surfaces")
            return {}
    return {
        "mesh":candidate,
        "observation":{
            "schema":"axm.environment-object-selected-roughness-current-world-observation/v0.1",
            "state":SELECTED_ROUGHNESS_STATE,
            "reusable_rule":SELECTED_APPEARANCE_RULE,
            "parent_environment_head":SELECTED_ROUGHNESS_PARENT_HEAD,
            "materials_authority_head":MATERIALS_AUTHORITY_HEAD,
            "technical_art_head":TECHNICAL_ART_HEAD,
            "selected_png_sha256":SELECTED_ROUGHNESS_PNG_SHA256,
            "selected_scalar_r8_sha256":SELECTED_FIELD_SCALAR_SHA256,
            "selected_scalar_r8_min":SELECTED_ROUGHNESS_MIN_R8,
            "selected_scalar_r8_max":SELECTED_ROUGHNESS_MAX_R8,
            "selected_scalar_r8_unique":SELECTED_ROUGHNESS_UNIQUE_R8,
            "selected_surfaces":selected,
            "selected_surface_count":selected.size(),
            "non_selected_surfaces_roughness_texture_absent":true,
            "geometry_positions_normals_indices_uv0_reused":true,
            "selected_roughness_bound":true,
            "environment_adoption":false,
            "truth_boundary":"Exact Materials-selected roughness field is bound only to the two already source-segmented and exact-UV0-bound Object faces. Current receiver albedo and metallic are preserved per face; geometry, normals, indices, UV0, Weather, Building, Nature, dressing, route, cameras and lights are unchanged. This is an Environment appearance candidate only; Runtime and Art/QA acceptance remain separate."
        }
    }

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_static_source(root3d,source,cull_target_asset_id)
    if String(result.get("asset_id",""))!=OBJECT_ASSET_ID:
        return result
    if root3d.get_child_count()!=child_count_before+1:
        fail("selected roughness expected exactly one emitted Object child")
        return {}
    var emitted:=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is MeshInstance3D):
        fail("selected roughness Object child is not MeshInstance3D")
        return {}
    var node:=emitted as MeshInstance3D
    if not (node.mesh is ArrayMesh):
        fail("selected roughness UV-bound parent mesh is not ArrayMesh")
        return {}
    var built:=_bind_selected_roughness(node.mesh as ArrayMesh)
    if built.is_empty():
        return {}
    node.mesh=built["mesh"] as ArrayMesh
    result["surface_count"]=7
    result["environment_object_selected_roughness_current_world"]=built["observation"]
    return result

func write_receipt()->void:
    receipt["environment_object_selected_roughness_current_world_state"]=SELECTED_ROUGHNESS_STATE
    receipt["environment_object_selected_roughness_current_world_rule"]=SELECTED_APPEARANCE_RULE
    receipt["environment_object_selected_roughness_png_sha256"]=SELECTED_ROUGHNESS_PNG_SHA256
    receipt["environment_object_selected_roughness_scalar_sha256"]=SELECTED_FIELD_SCALAR_SHA256
    receipt["environment_object_selected_roughness_truth_boundary"]="Real current-world appearance candidate only. Exact selected roughness is bound through the proven selected-face + exact-UV0 receiver while source geometry and unrelated world state remain fixed. Environment does not self-approve appearance or runtime cost."
    super.write_receipt()
