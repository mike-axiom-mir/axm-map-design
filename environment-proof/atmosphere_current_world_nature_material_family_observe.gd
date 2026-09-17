extends "res://atmosphere_current_world_building_header_segmentation_observe.gd"

const NATURE_PAYLOAD_PATH := "res://generated/current_world_nature_material_family.json"
const NATURE_SCHEMA := "axm.environment-current-world-nature-material-family-composition/v0.1"
const NATURE_STATUS := "PASS_CURRENT_WORLD_NATURE_MATERIAL_FAMILY_STRUCTURE"
const NATURE_MATERIALS_HEAD := "8b2e0523d7a2b210c6404f15bafb08fbedcad4dd"
const NATURE_GEOMETRY_REFERENCE_HEAD := "da3adbef4de8cddb8f3ebe841d39bb31a8936f5f"
const NATURE_FAMILY_ID := "nature-woody-foliage-family-001"

func load_payload()->Dictionary:
    if not FileAccess.file_exists(NATURE_PAYLOAD_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(NATURE_PAYLOAD_PATH))
    if not (parsed is Dictionary):
        return {}
    var canonical=parsed as Dictionary
    if String(canonical.get("schema",""))!=NATURE_SCHEMA or String(canonical.get("status",""))!=NATURE_STATUS:
        return {}
    if String(canonical.get("nature_materials_head",""))!=NATURE_MATERIALS_HEAD:
        return {}
    if String(canonical.get("nature_geometry_reference_head",""))!=NATURE_GEOMETRY_REFERENCE_HEAD:
        return {}
    if String((canonical.get("nature_material_family",{}) as Dictionary).get("family_id",""))!=NATURE_FAMILY_ID:
        return {}
    var compat=canonical.duplicate(true)
    compat["schema"]="axm.environment-current-world-weather-width-evidence/v0.1"
    compat["status"]="PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE"
    compat["parent_variant_head"]="e482d003853e52fc835f1797ddfb6506a50083ef"
    return compat

func write_receipt()->void:
    receipt["environment_nature_material_family_id"]=NATURE_FAMILY_ID
    receipt["environment_nature_materials_head"]=NATURE_MATERIALS_HEAD
    receipt["environment_nature_geometry_reference_head"]=NATURE_GEOMETRY_REFERENCE_HEAD
    receipt["environment_nature_material_truth_boundary"]="Exact three-source scalar/color material-family receiving proof only. Existing source geometry, motion, placement and proof culling are preserved; final sidedness, Art Direction/QA and target-device cost remain separate."
    super.write_receipt()

func _nature_material(payload:Dictionary,cull_back:bool)->StandardMaterial3D:
    var albedo=payload.get("albedo",[]) as Array
    if albedo.size()!=4:
        fail("Nature material albedo drift")
        return StandardMaterial3D.new()
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(float(albedo[0]),float(albedo[1]),float(albedo[2]),float(albedo[3]))
    material.metallic=float(payload.get("metallic",-1.0))
    material.roughness=float(payload.get("roughness",-1.0))
    if material.metallic<0.0 or material.metallic>1.0 or material.roughness<0.0 or material.roughness>1.0:
        fail("Nature material scalar drift")
    material.cull_mode=BaseMaterial3D.CULL_BACK if cull_back else BaseMaterial3D.CULL_DISABLED
    return material

func _commit_nature_surfaces(mesh:ArrayMesh,vertices:Array,triangles:Array,proof:Dictionary,cull_back:bool)->int:
    var partition=proof.get("surface_triangle_indices",{}) as Dictionary
    var materials=proof.get("materials",{}) as Dictionary
    var total:=0
    for role_value in ["woody","foliage"]:
        var role=String(role_value)
        var indices=partition.get(role,[]) as Array
        var material_payload=materials.get(role,{}) as Dictionary
        if indices.is_empty() or material_payload.is_empty():
            fail("Nature material-family surface partition missing %s" % role)
            return -1
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for raw_tri_index in indices:
            var tri_index=int(raw_tri_index)
            if tri_index<0 or tri_index>=triangles.size():
                fail("Nature material-family triangle partition index drift")
                return -1
            var tri=triangles[tri_index] as Array
            if tri.size()!=3:
                fail("Nature material-family triangle arity drift")
                return -1
            for raw_vertex_index in tri:
                var vertex_index=int(raw_vertex_index)
                if vertex_index<0 or vertex_index>=vertices.size():
                    fail("Nature material-family vertex index drift")
                    return -1
                st.add_vertex(gvec(vertices[vertex_index] as Array))
        st.generate_normals()
        st.commit(mesh)
        mesh.surface_set_material(mesh.get_surface_count()-1,_nature_material(material_payload,cull_back))
        total+=indices.size()
    return total

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var proof=source.get("nature_material_family_receiving",{}) as Dictionary
    if proof.is_empty():
        return super.add_static_source(root3d,source,cull_target_asset_id)
    if String(proof.get("family_id",""))!=NATURE_FAMILY_ID or String(proof.get("materials_head",""))!=NATURE_MATERIALS_HEAD:
        fail("static Nature material-family identity drift")
        return {}
    var asset_id=String(source.get("asset_id",""))
    var cull_back=asset_id==cull_target_asset_id and not cull_target_asset_id.is_empty()
    var expected_cull="CULL_BACK" if cull_back else String(source.get("proof_render_culling",""))
    if String(proof.get("preserved_proof_culling",""))!=String(source.get("proof_render_culling","")):
        fail("static Nature proof culling provenance drift")
        return {}
    var vertices=source.get("vertices_source_xyz_m",[]) as Array
    var triangles=source.get("triangles",[]) as Array
    if vertices.size()!=390 or triangles.size()!=570:
        fail("static Nature exact geometry count drift")
        return {}
    var mesh:=ArrayMesh.new()
    var total=_commit_nature_surfaces(mesh,vertices,triangles,proof,cull_back)
    if total!=570 or mesh.get_surface_count()!=2:
        fail("static Nature exact two-surface material-family partition drift")
        return {}
    var node:=MeshInstance3D.new()
    node.name=asset_id
    node.mesh=mesh
    root3d.add_child(node)
    return {
        "asset_id":asset_id,
        "vertices":vertices.size(),
        "triangles":triangles.size(),
        "surface_count":mesh.get_surface_count(),
        "material_family_id":NATURE_FAMILY_ID,
        "material_ids":["woody","foliage"],
        "proof_culling":"CULL_BACK" if cull_back else "CULL_DISABLED",
        "preserved_source_proof_culling":expected_cull,
        "mesh_digest":String(source.get("mesh_digest",""))
    }

func make_sapling()->void:
    sapling_mesh=ArrayMesh.new()
    sapling_node=MeshInstance3D.new()
    sapling_node.name="source-sapling-live-rebound"
    sapling_node.mesh=sapling_mesh

func fill_sapling(sapling:Dictionary)->Dictionary:
    sapling_mesh.clear_surfaces()
    var proof=sapling.get("nature_material_family_receiving",{}) as Dictionary
    if String(proof.get("family_id",""))!=NATURE_FAMILY_ID or String(proof.get("materials_head",""))!=NATURE_MATERIALS_HEAD:
        fail("dynamic sapling material-family identity drift")
        return {}
    if String(proof.get("preserved_proof_culling",""))!=String(sapling.get("proof_render_culling","")):
        fail("dynamic sapling proof culling provenance drift")
        return {}
    var vertices=sapling.get("vertices_source_xyz_m",[]) as Array
    var triangles=sapling.get("triangles",[]) as Array
    if vertices.size()!=390 or triangles.size()!=570:
        fail("dynamic sapling exact geometry count drift")
        return {}
    var total=_commit_nature_surfaces(sapling_mesh,vertices,triangles,proof,false)
    if total!=570 or sapling_mesh.get_surface_count()!=2:
        fail("dynamic sapling exact two-surface material-family partition drift")
        return {}
    return {
        "node_instance_id":sapling_node.get_instance_id(),
        "mesh_instance_id":sapling_mesh.get_instance_id(),
        "surface_count":sapling_mesh.get_surface_count(),
        "source_vertex_count":vertices.size(),
        "source_triangle_count":triangles.size(),
        "material_family_id":NATURE_FAMILY_ID,
        "material_ids":["woody","foliage"],
        "proof_culling":"CULL_DISABLED"
    }
