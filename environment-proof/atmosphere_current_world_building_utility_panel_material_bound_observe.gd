extends "res://atmosphere_current_world_object_articulated_service_clearance_successor_observe.gd"

const MATERIAL_BINDING_PATH := "res://generated/current-receiver-utility-panel-uv-image-binding-receipt.json"
const MATERIAL_IMAGE_PATH := "res://generated/utility-panel-review-checker-512.png"
const MATERIAL_CONTRACT_PATH := "res://generated/environment-building-utility-panel-material-current-world-ab.json"
const MATERIAL_STATE := "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_MATERIAL_BOUND_RECEIVER__A_B_REVIEW_ONLY__ADOPTION_HELD"
const MATERIAL_RULE := "OWNER_BOUND_UV_IMAGE_TRANSPORT_MAY_ENTER_THE_REAL_WORLD_ONLY_AS_AN_EXPLICIT_A_B_RECEIVER_SUCCESSOR_WITH_UNRELATED_WORLD_IDENTITIES_AND_ROLLBACK_HELD"
const EXPECTED_TA_HEAD := "1434bc4a64faa04db10f47723c37ab7925aaa163"
const EXPECTED_MATERIALS_HEAD := "0ae911792929eaa38b2c2f32239ebfdce8967251"
const EXPECTED_PNG_SHA := "e932cdd94d370184c7361862d5064149cc193e3a8fd80b269cab6543c0919198"
const EXPECTED_RGBA_SHA := "02f8f464eabc734a3be687a7706edf8b8f62ece834fa981c8c993fbb8227bb4b"
const EXPECTED_TA_RESULT := "PASS_CURRENT_184V_BUILDING_RECEIVER_UTILITY_PANEL_SERVICE_FACE_UV_IMAGE_BINDING__HOLD_ENVIRONMENT_VISUAL_RUNTIME_ADOPTION"
const EXPECTED_FILL_AUTHORITY := "TECHNICAL_ART_RECEIVER_FILL_ONLY__NOT_SOURCE_OR_GEOMETRY_EQUIVALENCE"
const EXPECTED_ROLES := ["frame_galvanized","infill_coating","roof_membrane","slab_mineral","utility_panel_ochre"]

func _material_read_json(path:String)->Dictionary:
    if not FileAccess.file_exists(path):
        fail("Environment Building material binding JSON missing: "+path)
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(path))
    if not (parsed is Dictionary):
        fail("Environment Building material binding JSON invalid: "+path)
        return {}
    return parsed as Dictionary

func _material_sha256(data:PackedByteArray)->String:
    var context:=HashingContext.new()
    if context.start(HashingContext.HASH_SHA256)!=OK:
        fail("Environment Building material SHA-256 initialization failed")
        return ""
    if context.update(data)!=OK:
        fail("Environment Building material SHA-256 update failed")
        return ""
    return context.finish().hex_encode()

func _material_contract()->Dictionary:
    var contract:=_material_read_json(MATERIAL_CONTRACT_PATH)
    if contract.is_empty():
        return {}
    if String(contract.get("schema",""))!="axm.environment-building-utility-panel-material-current-world-ab/v0.1":
        fail("Environment Building material A/B contract schema drift")
        return {}
    if String((contract.get("technical_art",{}) as Dictionary).get("head",""))!=EXPECTED_TA_HEAD:
        fail("Environment Building material A/B Technical Art head drift")
        return {}
    if String((contract.get("materials",{}) as Dictionary).get("head",""))!=EXPECTED_MATERIALS_HEAD:
        fail("Environment Building material A/B Materials head drift")
        return {}
    if bool((contract.get("promotion",{}) as Dictionary).get("environment_adoption",true)):
        fail("Environment Building material A/B inflated Environment adoption")
        return {}
    return contract

func _material_binding()->Dictionary:
    var binding:=_material_read_json(MATERIAL_BINDING_PATH)
    if binding.is_empty():
        return {}
    if String(binding.get("result",""))!=EXPECTED_TA_RESULT or String(binding.get("technical_art_head",""))!=EXPECTED_TA_HEAD:
        fail("Environment Building material exact Technical Art binding drift")
        return {}
    var promotion=binding.get("promotion",{}) as Dictionary
    if bool(promotion.get("environment_adoption",true)):
        fail("Technical Art material binding unexpectedly grants Environment adoption")
        return {}
    for panel_id in ["front-utility-bay","east-utility-bay"]:
        var panel=(binding.get("panel_bindings",{}) as Dictionary).get(panel_id,{}) as Dictionary
        if String(panel.get("non_service_face_projection_authority",""))!=EXPECTED_FILL_AUTHORITY:
            fail("Environment Building material receiver-fill authority drift")
            return {}
    return binding

func _material_texture()->ImageTexture:
    var png_bytes:=FileAccess.get_file_as_bytes(MATERIAL_IMAGE_PATH)
    if _material_sha256(png_bytes)!=EXPECTED_PNG_SHA:
        fail("Environment Building material serialized PNG identity drift")
        return null
    var image:=Image.new()
    if image.load(MATERIAL_IMAGE_PATH)!=OK or image.is_empty():
        fail("Environment Building material image load failed")
        return null
    image.convert(Image.FORMAT_RGBA8)
    if image.get_width()!=512 or image.get_height()!=512 or _material_sha256(image.get_data())!=EXPECTED_RGBA_SHA:
        fail("Environment Building material decoded RGBA8 identity drift")
        return null
    image.generate_mipmaps()
    return ImageTexture.create_from_image(image)

func _material_uv_map(binding:Dictionary)->Dictionary:
    var merged:Dictionary={}
    var panels=binding.get("panel_bindings",{}) as Dictionary
    for panel_id in ["front-utility-bay","east-utility-bay"]:
        var panel=panels.get(panel_id,{}) as Dictionary
        var values=panel.get("full_box_planar_projection_uv0_by_receiver_vertex",{}) as Dictionary
        for key in values.keys():
            if merged.has(String(key)):
                fail("Environment Building material duplicate Technical Art receiver UV index")
                return {}
            merged[String(key)]=values[key]
    if merged.size()!=16:
        fail("Environment Building material Technical Art receiver UV map count drift")
        return {}
    return merged

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var contract:=_material_contract()
    var binding:=_material_binding()
    if contract.is_empty() or binding.is_empty():
        return {}
    var texture:=_material_texture()
    if texture==null:
        return {}
    var uv_map:=_material_uv_map(binding)
    if uv_map.is_empty():
        return {}

    var patched:=data.duplicate(true)
    var current_policy:=patched.get("environment_building_current_source_policy_rebind",{}) as Dictionary
    if String(current_policy.get("source_policy_head",""))!=CLEARANCE_CURRENT_POLICY_HEAD or String(current_policy.get("current_source_variant_id",""))!=CLEARANCE_CURRENT_VARIANT:
        fail("Environment Building material candidate current-source policy drift")
        return {}
    if bool(current_policy.get("receiver_geometry_changed",true)) or bool(current_policy.get("receiver_materials_changed",true)):
        fail("Environment Building material candidate requires exact pre-binding current receiver")
        return {}

    var proof:=patched.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!="source:building:service-pavilion-001":
        fail("Environment Building material candidate missing exact Building receiver")
        return {}
    var segmentation:=proof.get("source_header_segmentation_rebind",{}) as Dictionary
    if String(segmentation.get("source_head",""))!=BUILDING_SEGMENTATION_SOURCE_HEAD or String(segmentation.get("segmentation_revision",""))!=BUILDING_SEGMENTATION_REVISION:
        fail("Environment Building material candidate segmentation identity drift")
        return {}
    var placement:=_source_vec(segmentation.get("placement_translation_source_xyz_m",[]))
    if not _center_matches(placement,RECEIVER_PLACEMENT_TRANSLATION):
        fail("Environment Building material candidate placement translation drift")
        return {}

    var vertices:=proof.get("vertices_source_xyz_m",[]) as Array
    if vertices.size()!=184:
        fail("Environment Building material candidate requires exact 184-vertex receiver")
        return {}
    var front_before:=_group_center(vertices,FRONT_PANEL_INDICES)
    var east_before:=_group_center(vertices,EAST_PANEL_INDICES)
    if not _center_matches(front_before,FRONT_OLD_RECEIVER_CENTER) or not _center_matches(east_before,EAST_OLD_RECEIVER_CENTER):
        fail("Environment Building material candidate predecessor panel center drift")
        return {}
    _translate_group(vertices,FRONT_PANEL_INDICES,FRONT_TRANSLATION)
    _translate_group(vertices,EAST_PANEL_INDICES,EAST_TRANSLATION)
    if not _center_matches(_group_center(vertices,FRONT_PANEL_INDICES),FRONT_NEW_RECEIVER_CENTER) or not _center_matches(_group_center(vertices,EAST_PANEL_INDICES),EAST_NEW_RECEIVER_CENTER):
        fail("Environment Building material candidate successor panel center drift")
        return {}

    var surfaces=proof.get("surfaces",[]) as Array
    if surfaces.size()!=5:
        fail("Environment Building material candidate exact surface count drift")
        return {}
    var mesh:=ArrayMesh.new()
    var roles:Array=[]
    var material_ids:Array=[]
    var triangle_count:=0
    var utility_emitted_vertices:=0
    for surface_value in surfaces:
        var surface=surface_value as Dictionary
        var role:=String(surface.get("surface_role",""))
        var material_id:=String(surface.get("material_id",""))
        roles.append(role)
        material_ids.append(material_id)
        if role!=material_id:
            fail("Environment Building material candidate role/material drift")
            return {}
        var triangles=surface.get("triangles",[]) as Array
        triangle_count+=triangles.size()
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for tri_value in triangles:
            var tri=tri_value as Array
            if tri.size()!=3:
                fail("Environment Building material candidate triangle arity drift")
                return {}
            for raw_index in tri:
                var index:=int(raw_index)
                if index<0 or index>=vertices.size():
                    fail("Environment Building material candidate triangle index drift")
                    return {}
                if role=="utility_panel_ochre":
                    var key:=str(index)
                    if not uv_map.has(key):
                        fail("Environment Building material utility surface references vertex outside exact Technical Art binding: "+key)
                        return {}
                    var uv=uv_map[key] as Array
                    if uv.size()!=2:
                        fail("Environment Building material UV arity drift")
                        return {}
                    st.set_uv(Vector2(float(uv[0]),float(uv[1])))
                    utility_emitted_vertices+=1
                st.add_vertex(gvec(vertices[index] as Array))
        st.generate_normals()
        st.commit(mesh)
        var surface_index:=mesh.get_surface_count()-1
        var material:=building_material(surface)
        if role=="utility_panel_ochre":
            material.albedo_color=Color.WHITE
            material.albedo_texture=texture
            material.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
        mesh.surface_set_material(surface_index,material)
    if roles!=EXPECTED_ROLES or triangle_count!=276 or mesh.get_surface_count()!=5 or utility_emitted_vertices<=0:
        fail("Environment Building material candidate current receiver partition drift")
        return {}

    var node:=MeshInstance3D.new()
    node.name="source:building:service-pavilion-001"
    node.mesh=mesh
    root3d.add_child(node)
    return {
        "asset_id":"source:building:service-pavilion-001",
        "vertices":vertices.size(),
        "triangles":triangle_count,
        "surface_count":mesh.get_surface_count(),
        "material_ids":material_ids,
        "material_profile_sha256":String((proof.get("provenance",{}) as Dictionary).get("material_profile_sha256","")),
        "proof_culling":"CULL_DISABLED",
        "receiving_policy":String(proof.get("receiving_policy","")),
        "header_segmentation_revision":BUILDING_SEGMENTATION_REVISION,
        "source_positive_volume_intersection_count":4,
        "successor_positive_volume_intersection_count":0,
        "environment_building_utility_panel_clearance_current_world":{
            "schema":"axm.environment-building-utility-panel-clearance-current-world-observation/v0.2",
            "state":BUILDING_UTILITY_PANEL_CLEARANCE_STATE,
            "reusable_rule":BUILDING_UTILITY_PANEL_CLEARANCE_RULE,
            "building_source_head":BUILDING_CLEARANCE_SOURCE_HEAD,
            "building_source_content_head":BUILDING_CLEARANCE_SOURCE_CONTENT_HEAD,
            "building_procedural_head":BUILDING_CLEARANCE_PROCEDURAL_HEAD,
            "current_receiver_source_policy_head":CLEARANCE_CURRENT_POLICY_HEAD,
            "current_receiver_source_variant_id":CLEARANCE_CURRENT_VARIANT,
            "current_receiver_segmentation_source_head":BUILDING_SEGMENTATION_SOURCE_HEAD,
            "current_receiver_segmentation_revision":BUILDING_SEGMENTATION_REVISION,
            "placement_translation_source_xyz_m":_source_array(RECEIVER_PLACEMENT_TRANSLATION),
            "front_predecessor_center_source_xyz_m":_source_array(front_before-RECEIVER_PLACEMENT_TRANSLATION),
            "front_successor_center_source_xyz_m":_source_array(_group_center(vertices,FRONT_PANEL_INDICES)-RECEIVER_PLACEMENT_TRANSLATION),
            "front_predecessor_center_receiver_xyz_m":_source_array(front_before),
            "front_successor_center_receiver_xyz_m":_source_array(_group_center(vertices,FRONT_PANEL_INDICES)),
            "front_translation_source_xyz_m":_source_array(FRONT_TRANSLATION),
            "east_predecessor_center_source_xyz_m":_source_array(east_before-RECEIVER_PLACEMENT_TRANSLATION),
            "east_successor_center_source_xyz_m":_source_array(_group_center(vertices,EAST_PANEL_INDICES)-RECEIVER_PLACEMENT_TRANSLATION),
            "east_predecessor_center_receiver_xyz_m":_source_array(east_before),
            "east_successor_center_receiver_xyz_m":_source_array(_group_center(vertices,EAST_PANEL_INDICES)),
            "east_translation_source_xyz_m":_source_array(EAST_TRANSLATION),
            "translated_source_vertex_count":16,
            "topology_changed":false,
            "surface_partition_changed":false,
            "material_values_changed":false,
            "environment_adoption":false,
            "truth_boundary":"Real current-world Environment receiving candidate on the active header-segmented-23 Building receiver only. The first 152-vertex compatibility-path attempt is not promoted. These two source-owned utility-panel boxes move by the exact owner/procedural +0.02 m receiver-normal successor delta while current Building topology/material partition and unrelated Object, Nature, Weather, route, camera and lighting state remain owned by their existing lanes. Environment adoption remains held."
        },
        "environment_building_utility_panel_material_current_world":{
            "schema":"axm.environment-building-utility-panel-material-current-world-observation/v0.1",
            "state":MATERIAL_STATE,
            "reusable_rule":MATERIAL_RULE,
            "technical_art_head":EXPECTED_TA_HEAD,
            "materials_head":EXPECTED_MATERIALS_HEAD,
            "serialized_png_sha256":EXPECTED_PNG_SHA,
            "decoded_rgba8_sha256":EXPECTED_RGBA_SHA,
            "uv_bound_receiver_vertex_count":uv_map.size(),
            "receiver_fill_authority":EXPECTED_FILL_AUTHORITY,
            "material_albedo_source":"EXACT_MATERIALS_SERIALIZED_REVIEW_TEXTURE",
            "material_metallic":0.18,
            "material_roughness":0.62,
            "environment_adoption":false,
            "art_qa_acceptance":false,
            "runtime_acceptance":false
        }
    }

func write_receipt()->void:
    receipt["environment_building_utility_panel_material_current_world_state"]=MATERIAL_STATE
    receipt["environment_building_utility_panel_material_current_world_rule"]=MATERIAL_RULE
    receipt["environment_building_utility_panel_material_technical_art_head"]=EXPECTED_TA_HEAD
    receipt["environment_building_utility_panel_material_materials_head"]=EXPECTED_MATERIALS_HEAD
    receipt["environment_building_utility_panel_material_png_sha256"]=EXPECTED_PNG_SHA
    receipt["environment_building_utility_panel_material_rgba8_sha256"]=EXPECTED_RGBA_SHA
    receipt["environment_building_utility_panel_material_environment_adoption"]=false
    receipt["environment_building_utility_panel_material_art_qa_acceptance"]=false
    receipt["environment_building_utility_panel_material_runtime_acceptance"]=false
    receipt["environment_building_utility_panel_material_truth_boundary"]="Exact Technical Art current-receiver UV/image binding consumed into the existing 184v/276t/5-surface Building receiver for real-world A/B review only. Only the utility-panel material surface receives the exact Materials review PNG and TA UV0 mapping; receiver-local fill remains explicitly non-source. Building geometry/placement, Object articulation, Nature, Weather, Environment dressing, cameras and lights remain inherited. No automatic Environment, Art/QA, Runtime/device, CANON or production adoption."
    super.write_receipt()
