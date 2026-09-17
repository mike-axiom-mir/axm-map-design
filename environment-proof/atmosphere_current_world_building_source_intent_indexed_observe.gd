extends "res://atmosphere_current_world_building_planar_role_observe.gd"

const SOURCE_INTENT_INDEXED_PATH := "res://generated/building_planar_role_source_intent_indexed.json"
const SOURCE_INTENT_INDEXED_SCHEMA := "axm.building-planar-role-indexed-geometry-candidate/v0.1"
const SOURCE_INTENT_RECEIVING_SCHEMA := "axm.environment-building-source-intent-indexed-receiving/v0.1"
const SOURCE_INTENT_GEOMETRY_HEAD := "b9b4ab63e23b9756ab79597e86ecc41ea75ea8b7"
const SOURCE_INTENT_CANDIDATE_ID := "boundary-only-planar-role-source-intent-indexed-001"
const SOURCE_INTENT_CANDIDATE_SHA256 := "f6a831058de66901fd42704b1d8c1cf187b13a0919ae3719c03c4369f107e6c0"
const EXPECTED_MAP_PLACEMENT_TRANSLATION := Vector3(0.0, 0.0, -7.2)
const EXPECTED_MAP_MIN_BOUNDS := Vector3(-3.8, 0.0, -8.2)
const EXPECTED_MAP_MAX_BOUNDS := Vector3(3.92, 3.4, -6.08)

func _load_source_intent_candidate()->Dictionary:
    if not FileAccess.file_exists(SOURCE_INTENT_INDEXED_PATH):
        fail("missing exact 604-vertex source-intent indexed candidate")
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(SOURCE_INTENT_INDEXED_PATH))
    if not (parsed is Dictionary):
        fail("source-intent indexed candidate is not a JSON object")
        return {}
    var candidate:=parsed as Dictionary
    if String(candidate.get("schema",""))!=SOURCE_INTENT_INDEXED_SCHEMA:
        fail("source-intent indexed candidate schema drift")
        return {}
    if String(candidate.get("candidate_id",""))!=SOURCE_INTENT_CANDIDATE_ID:
        fail("source-intent indexed candidate identity drift")
        return {}
    if String(candidate.get("parent_representation_id",""))!=BUILDING_PLANAR_REPRESENTATION_ID:
        fail("source-intent indexed parent representation drift")
        return {}
    var vertices:=candidate.get("vertices",[]) as Array
    var indices:=candidate.get("indices",[]) as Array
    var triangles:=candidate.get("triangles",[]) as Array
    var triangle_roles:=candidate.get("triangle_roles",[]) as Array
    if vertices.size()!=604 or indices.size()!=1008 or triangles.size()!=336 or triangle_roles.size()!=336:
        fail("source-intent indexed candidate count drift")
        return {}
    return candidate

func _mesh_diag(mesh:ArrayMesh)->Dictionary:
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
            "material_role":BUILDING_PLANAR_ROLES[surface_index] if surface_index<BUILDING_PLANAR_ROLES.size() else "UNKNOWN",
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

func _vec_close(a:Vector3,b:Vector3,eps:float=0.000001)->bool:
    return a.distance_to(b)<=eps

func _candidate_translated_bounds(vertices:Array,translation:Vector3)->Dictionary:
    var minimum:=Vector3(INF,INF,INF)
    var maximum:=Vector3(-INF,-INF,-INF)
    for vertex_value in vertices:
        var vertex:=vertex_value as Dictionary
        var p:=gvec(vertex.get("position",[]) as Array)+translation
        minimum=Vector3(min(minimum.x,p.x),min(minimum.y,p.y),min(minimum.z,p.z))
        maximum=Vector3(max(maximum.x,p.x),max(maximum.y,p.y),max(maximum.z,p.z))
    return {"min":minimum,"max":maximum}

func _parent_bounds(vertices:Array)->Dictionary:
    var minimum:=Vector3(INF,INF,INF)
    var maximum:=Vector3(-INF,-INF,-INF)
    for vertex_value in vertices:
        var p:=gvec(vertex_value as Array)
        minimum=Vector3(min(minimum.x,p.x),min(minimum.y,p.y),min(minimum.z,p.z))
        maximum=Vector3(max(maximum.x,p.x),max(maximum.y,p.y),max(maximum.z,p.z))
    return {"min":minimum,"max":maximum}

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var proof:=data.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!="source:building:service-pavilion-001":
        fail("missing exact planar-role Building receiving payload")
        return {}
    var receiving:=proof.get("environment_building_planar_role_receiving",{}) as Dictionary
    if String(receiving.get("schema",""))!=BUILDING_PLANAR_RECEIVING_SCHEMA:
        fail("planar-role receiving schema drift")
        return {}
    if String(receiving.get("hard_surface_head",""))!=BUILDING_PLANAR_HARD_SURFACE_HEAD:
        fail("planar-role Hard-Surface head drift")
        return {}
    if String(receiving.get("materials_head",""))!=BUILDING_PLANAR_MATERIALS_HEAD:
        fail("planar-role Materials head drift")
        return {}
    if String(receiving.get("selected_representation_id",""))!=BUILDING_PLANAR_REPRESENTATION_ID:
        fail("planar-role parent representation drift")
        return {}
    if bool(receiving.get("environment_adoption",true)):
        fail("planar-role review payload incorrectly claims Environment adoption")
        return {}

    var placement_raw:=receiving.get("placement_translation_source_xyz_m",[]) as Array
    if placement_raw.size()!=3:
        fail("planar-role current-world placement translation missing")
        return {}
    var placement:=gvec(placement_raw)
    if not _vec_close(placement,EXPECTED_MAP_PLACEMENT_TRANSLATION):
        fail("planar-role current-world placement translation drift: %s" % placement)
        return {}

    var candidate:=_load_source_intent_candidate()
    if candidate.is_empty():
        return {}
    var vertices:=candidate.get("vertices",[]) as Array
    var triangles:=candidate.get("triangles",[]) as Array
    var triangle_roles:=candidate.get("triangle_roles",[]) as Array
    var parent_vertices:=proof.get("vertices_source_xyz_m",[]) as Array
    var parent_surfaces:=proof.get("surfaces",[]) as Array
    if parent_vertices.size()!=672 or parent_surfaces.size()!=BUILDING_PLANAR_ROLES.size():
        fail("expected exact parent planar-role Building geometry/material payload")
        return {}

    var translated_bounds:=_candidate_translated_bounds(vertices,placement)
    var parent_bounds:=_parent_bounds(parent_vertices)
    if not _vec_close(translated_bounds["min"] as Vector3,parent_bounds["min"] as Vector3) or not _vec_close(translated_bounds["max"] as Vector3,parent_bounds["max"] as Vector3):
        fail("source-intent candidate translated bounds do not match retained Map receiver bounds")
        return {}
    if not _vec_close(translated_bounds["min"] as Vector3,EXPECTED_MAP_MIN_BOUNDS) or not _vec_close(translated_bounds["max"] as Vector3,EXPECTED_MAP_MAX_BOUNDS):
        fail("source-intent candidate translated bounds drift from exact current-world Building envelope")
        return {}

    var surface_by_role:Dictionary={}
    for surface_value in parent_surfaces:
        var surface:=surface_value as Dictionary
        var role:=String(surface.get("surface_role",""))
        if role.is_empty() or role!=String(surface.get("material_id","")):
            fail("parent Building material role/id drift")
            return {}
        surface_by_role[role]=surface
    if surface_by_role.size()!=BUILDING_PLANAR_ROLES.size():
        fail("parent Building material-role map drift")
        return {}

    var mesh:=ArrayMesh.new()
    for role_value in BUILDING_PLANAR_ROLES:
        var role:=String(role_value)
        var role_triangle_indices:Array=[]
        for triangle_index in range(triangles.size()):
            if String(triangle_roles[triangle_index])==role:
                role_triangle_indices.append(triangle_index)
        if role_triangle_indices.is_empty():
            fail("source-intent candidate omitted one required material role")
            return {}

        var role_vertex_indices:Array=[]
        var seen:Dictionary={}
        for triangle_index_value in role_triangle_indices:
            var tri:=triangles[int(triangle_index_value)] as Array
            if tri.size()!=3:
                fail("source-intent indexed triangle arity drift")
                return {}
            for raw_index in tri:
                var global_index:=int(raw_index)
                if global_index<0 or global_index>=vertices.size():
                    fail("source-intent indexed triangle index out of range")
                    return {}
                if not seen.has(global_index):
                    seen[global_index]=true
                    role_vertex_indices.append(global_index)

        var local_index:Dictionary={}
        var arrays:Array=[]
        arrays.resize(Mesh.ARRAY_MAX)
        var positions:=PackedVector3Array()
        var normals:=PackedVector3Array()
        for global_index_value in role_vertex_indices:
            var global_index:=int(global_index_value)
            var vertex:=vertices[global_index] as Dictionary
            if String(vertex.get("material_role",""))!=role:
                fail("source-intent indexed vertex crosses material-role boundary")
                return {}
            local_index[global_index]=local_index.size()
            positions.append(gvec(vertex.get("position",[]) as Array)+placement)
            normals.append(gvec(vertex.get("normal",[]) as Array))
        var local_indices:=PackedInt32Array()
        for triangle_index_value in role_triangle_indices:
            var tri:=triangles[int(triangle_index_value)] as Array
            local_indices.append(int(local_index[int(tri[0])]))
            local_indices.append(int(local_index[int(tri[1])]))
            local_indices.append(int(local_index[int(tri[2])]))
        arrays[Mesh.ARRAY_VERTEX]=positions
        arrays[Mesh.ARRAY_NORMAL]=normals
        arrays[Mesh.ARRAY_INDEX]=local_indices
        mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
        mesh.surface_set_material(mesh.get_surface_count()-1,building_material(surface_by_role[role] as Dictionary))

    var storage:=_mesh_diag(mesh)
    if storage.get("surface_count",0)!=5 or storage.get("total_vertices",0)!=604 or storage.get("total_indices",0)!=1008 or storage.get("total_primitives",0)!=336:
        fail("source-intent indexed Godot storage identity drift: %s" % JSON.stringify(storage))
        return {}

    var node:=MeshInstance3D.new()
    node.name="source:building:service-pavilion-001"
    node.mesh=mesh
    root3d.add_child(node)
    return {
        "asset_id":"source:building:service-pavilion-001",
        "vertices":604,
        "triangles":336,
        "surface_count":5,
        "material_ids":BUILDING_PLANAR_ROLES.duplicate(),
        "proof_culling":"CULL_DISABLED",
        "receiving_policy":String(proof.get("receiving_policy","")),
        "representation_id":SOURCE_INTENT_CANDIDATE_ID,
        "environment_building_source_intent_indexed":{
            "schema":SOURCE_INTENT_RECEIVING_SCHEMA,
            "geometry_head":SOURCE_INTENT_GEOMETRY_HEAD,
            "candidate_id":SOURCE_INTENT_CANDIDATE_ID,
            "candidate_sha256":SOURCE_INTENT_CANDIDATE_SHA256,
            "parent_representation_id":BUILDING_PLANAR_REPRESENTATION_ID,
            "source_owner_equivalence_identity_claimed":true,
            "environment_adoption":false,
            "placement_translation_source_xyz_m":placement_raw.duplicate(),
            "placement_translation_godot_xyz_m":[placement.x,placement.y,placement.z],
            "translated_bounds_godot_xyz_m":{
                "min":[(translated_bounds["min"] as Vector3).x,(translated_bounds["min"] as Vector3).y,(translated_bounds["min"] as Vector3).z],
                "max":[(translated_bounds["max"] as Vector3).x,(translated_bounds["max"] as Vector3).y,(translated_bounds["max"] as Vector3).z],
            },
            "storage":storage,
            "truth_boundary":"Exact 604-vertex Geometry source-intent indexed candidate rendered at the exact retained Map placement as a current-world Environment review target only. Hard-Surface source semantics, five material roles/scalars, Nature, Object, footprint, Weather, route, cameras and lighting remain outside this receiver construction. Art/QA, Technical-Art transport and Runtime/device acceptance remain separate gates."
        }
    }

func write_receipt()->void:
    receipt["environment_building_source_intent_indexed_result"]="CANDIDATE_SOURCE_INTENT_INDEXED_RECEIVER"
    receipt["environment_building_source_intent_indexed_geometry_head"]=SOURCE_INTENT_GEOMETRY_HEAD
    receipt["environment_building_source_intent_indexed_candidate_id"]=SOURCE_INTENT_CANDIDATE_ID
    receipt["environment_building_source_intent_indexed_candidate_sha256"]=SOURCE_INTENT_CANDIDATE_SHA256
    receipt["environment_building_source_intent_indexed_truth_boundary"]="Exact source-intent indexed Building receiver at the retained Map placement; current-world observation only. No default Environment adoption, visual preference, transport acceptance, target-device performance, CANON or production-readiness implication."
    super.write_receipt()
