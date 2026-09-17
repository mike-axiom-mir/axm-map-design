extends "res://atmosphere_current_world_nature_leaf_flutter_observe.gd"

const PLANAR_PAYLOAD_PATH := "res://generated/building_planar_role_render_receiver.json"
const RUNTIME_PLANAR_SCHEMA := "axm.runtime-building-planar-role-render-receiver-observation/v0.1"
const BUILDING_PLANAR_HARD_SURFACE_HEAD := "93f22e4eeb9bb32516d4b11f8d8bcf47d9792910"
const BUILDING_PLANAR_REPRESENTATION_ID := "boundary-only-planar-role-rectangle-render-001"
const BUILDING_PLANAR_PAYLOAD_SHA256 := "cf086f2446b8f915378007b4402a5e4f83da09ecd05818b890a3e918563f8b12"
const BUILDING_PLANAR_ROLES := [
    "frame_galvanized",
    "infill_coating",
    "roof_membrane",
    "slab_mineral",
    "utility_panel_ochre",
]

func _load_planar_payload()->Dictionary:
    if not FileAccess.file_exists(PLANAR_PAYLOAD_PATH):
        fail("Runtime planar-role Building payload missing")
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(PLANAR_PAYLOAD_PATH))
    if not (parsed is Dictionary):
        fail("Runtime planar-role Building payload parse failure")
        return {}
    var candidate=parsed as Dictionary
    if String(candidate.get("schema",""))!="axm.building-planar-role-render-receiver-policy/v0.1":
        fail("Runtime planar-role Building schema drift")
        return {}
    if String(candidate.get("representation_id",""))!=BUILDING_PLANAR_REPRESENTATION_ID:
        fail("Runtime planar-role Building representation drift")
        return {}
    var vertices=candidate.get("vertices",[]) as Array
    var triangles=candidate.get("triangles",[]) as Array
    var triangle_roles=candidate.get("triangle_roles",[]) as Array
    var rectangles=candidate.get("rectangles",[]) as Array
    if vertices.size()!=672 or triangles.size()!=336 or triangle_roles.size()!=336 or rectangles.size()!=168:
        fail("Runtime planar-role Building exact candidate count drift")
        return {}
    return candidate

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
            "material_id":BUILDING_PLANAR_ROLES[surface_index] if surface_index<BUILDING_PLANAR_ROLES.size() else "UNKNOWN",
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

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var proof=data.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!="source:building:service-pavilion-001":
        fail("Runtime planar-role Building missing exact current-world material receiver")
        return {}
    var rebind=proof.get("source_header_segmentation_rebind",{}) as Dictionary
    if String(rebind.get("source_head",""))!="34124101e616c423c5a3ed5e122ddf09b98a1650":
        fail("Runtime planar-role Building semantic source drift")
        return {}
    if int((rebind.get("topology_summary",{}) as Dictionary).get("triangle_count",-1))!=276:
        fail("Runtime planar-role Building active source triangle-count drift")
        return {}

    var provenance=proof.get("provenance",{}) as Dictionary
    var placement=provenance.get("placement_translation_source_xyz_m",[]) as Array
    if placement.size()!=3:
        fail("Runtime planar-role Building placement missing")
        return {}
    if abs(float(placement[0]))>1e-9 or abs(float(placement[1])-7.2)>1e-9 or abs(float(placement[2]))>1e-9:
        fail("Runtime planar-role Building placement drift")
        return {}

    var material_by_role:Dictionary={}
    for surface_value in proof.get("surfaces",[]) as Array:
        var surface=surface_value as Dictionary
        var role=String(surface.get("surface_role",""))
        if role!=String(surface.get("material_id","")):
            fail("Runtime planar-role Building material role/id drift")
            return {}
        material_by_role[role]=surface
    if material_by_role.size()!=5:
        fail("Runtime planar-role Building material role count drift")
        return {}
    for role in BUILDING_PLANAR_ROLES:
        if not material_by_role.has(role):
            fail("Runtime planar-role Building missing material role "+role)
            return {}

    var candidate:=_load_planar_payload()
    if candidate.is_empty():
        return {}
    var local_vertices=candidate.get("vertices",[]) as Array
    var triangles=candidate.get("triangles",[]) as Array
    var triangle_roles=candidate.get("triangle_roles",[]) as Array

    var mesh:=ArrayMesh.new()
    var material_ids:Array=[]
    var emitted_triangles:=0
    for role in BUILDING_PLANAR_ROLES:
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        var role_triangles:=0
        for triangle_index in range(triangles.size()):
            if String(triangle_roles[triangle_index])!=role:
                continue
            var tri=triangles[triangle_index] as Array
            if tri.size()!=3:
                fail("Runtime planar-role Building triangle arity drift")
                return {}
            for raw_index in tri:
                var index=int(raw_index)
                if index<0 or index>=local_vertices.size():
                    fail("Runtime planar-role Building triangle index drift")
                    return {}
                var local=local_vertices[index] as Array
                if local.size()!=3:
                    fail("Runtime planar-role Building vertex arity drift")
                    return {}
                var world_source=[
                    float(local[0])+float(placement[0]),
                    float(local[1])+float(placement[1]),
                    float(local[2])+float(placement[2]),
                ]
                st.add_vertex(gvec(world_source))
            role_triangles+=1
        if role_triangles<=0:
            fail("Runtime planar-role Building role has no triangles: "+role)
            return {}
        st.generate_normals()
        st.commit(mesh)
        var surface_index=mesh.get_surface_count()-1
        mesh.surface_set_material(surface_index,building_material(material_by_role[role] as Dictionary))
        material_ids.append(role)
        emitted_triangles+=role_triangles

    if emitted_triangles!=336 or mesh.get_surface_count()!=5:
        fail("Runtime planar-role Building final surface/triangle identity drift")
        return {}
    var storage:=_mesh_surface_diag(mesh)
    if int(storage.get("total_vertices",-1))!=1008 or int(storage.get("total_indices",-1))!=0 or int(storage.get("total_primitives",-1))!=336:
        fail("Runtime planar-role Building Map render-domain storage drift")
        return {}

    var node:=MeshInstance3D.new()
    node.name="source:building:service-pavilion-001"
    node.mesh=mesh
    root3d.add_child(node)
    return {
        "asset_id":"source:building:service-pavilion-001",
        "vertices":local_vertices.size(),
        "triangles":emitted_triangles,
        "surface_count":mesh.get_surface_count(),
        "material_ids":material_ids,
        "material_profile_sha256":String(provenance.get("material_profile_sha256","")),
        "proof_culling":"CULL_DISABLED",
        "receiving_policy":"EXPLICIT_SOURCE_OWNED_PLANAR_ROLE_RENDER_RECEIVER__RUNTIME_REVIEW_ONLY",
        "representation_id":BUILDING_PLANAR_REPRESENTATION_ID,
        "runtime_building_planar_role_receiver":{
            "schema":RUNTIME_PLANAR_SCHEMA,
            "environment_parent_head":"ef2cb9cc84edc10ab66c2230daca625623e0b00d",
            "building_hard_surface_head":BUILDING_PLANAR_HARD_SURFACE_HEAD,
            "representation_id":BUILDING_PLANAR_REPRESENTATION_ID,
            "source_payload_sha256":BUILDING_PLANAR_PAYLOAD_SHA256,
            "semantic_source_variant":"header-segmented-23",
            "material_roles":BUILDING_PLANAR_ROLES.duplicate(),
            "rectangle_count":168,
            "candidate_vertex_count":672,
            "candidate_triangle_count":336,
            "map_render_storage":storage,
            "truth_boundary":"Runtime-only current-world receiving experiment for the exact Hard-Surface planar-role render receiver. Semantic Building source, exact five material scalars, world transform, Nature, Object, Weather, footprint cue, route, cameras and lighting remain unchanged. The render-only receiver makes no collision, transport, manufacturing or automatic Environment-adoption claim.",
        },
    }

func write_receipt()->void:
    receipt["runtime_building_planar_role_receiver_result"]="CANDIDATE_EXACT_HARD_SURFACE_PLANAR_ROLE_RENDER_RECEIVER"
    receipt["runtime_building_planar_role_receiver_hard_surface_head"]=BUILDING_PLANAR_HARD_SURFACE_HEAD
    receipt["runtime_building_planar_role_receiver_representation_id"]=BUILDING_PLANAR_REPRESENTATION_ID
    receipt["runtime_building_planar_role_receiver_truth_boundary"]="The exact Building-local render-only rectangle cover is substituted only for current-world runtime/visual characterization. Runtime does not adopt it, alter material values, or claim target-device performance."
    super.write_receipt()
