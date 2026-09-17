extends "res://atmosphere_current_world_building_planar_role_surface_index_observe.gd"

const TECHNICAL_ART_INDEX_BUNDLE_SCHEMA := "axm.technical-art-building-planar-role-index-bundle/v0.1"
const TECHNICAL_ART_INDEX_BUNDLE_PATH := "res://technical-art-building-planar-role-index-bundle.json"
const TECHNICAL_ART_RUNTIME_PARENT_HEAD := "8d5860c308c244d314ede5b79021e46f35c4040d"

var technical_art_index_bundle:Dictionary = {}

func _vec3_rows(values)->Array:
    var out:Array = []
    for value in values:
        var v:Vector3 = value
        out.append([v.x, v.y, v.z])
    return out

func _int_rows(values)->Array:
    var out:Array = []
    for value in values:
        out.append(int(value))
    return out

func _capture_surface_bundle(mesh:ArrayMesh)->Dictionary:
    var surfaces:Array = []
    var total_vertices := 0
    var total_indices := 0
    var total_triangles := 0
    for surface_index in range(mesh.get_surface_count()):
        var arrays := mesh.surface_get_arrays(surface_index)
        var vertices = arrays[Mesh.ARRAY_VERTEX]
        var normals = arrays[Mesh.ARRAY_NORMAL]
        var indices = arrays[Mesh.ARRAY_INDEX]
        if vertices == null or normals == null:
            fail("Technical Art bundle expected POSITION and NORMAL arrays")
            return {}
        if vertices.size() != normals.size():
            fail("Technical Art bundle POSITION/NORMAL cardinality drift")
            return {}
        var storage_indices := _int_rows(indices) if indices != null else []
        var triangle_corner_indices:Array = []
        if storage_indices.is_empty():
            for index in range(vertices.size()):
                triangle_corner_indices.append(index)
        else:
            triangle_corner_indices = storage_indices.duplicate()
        if triangle_corner_indices.size() % 3 != 0:
            fail("Technical Art bundle triangle index arity drift")
            return {}
        total_vertices += vertices.size()
        total_indices += storage_indices.size()
        total_triangles += triangle_corner_indices.size() / 3
        surfaces.append({
            "surface_index": surface_index,
            "partition_identity": BUILDING_PLANAR_ROLES[surface_index] if surface_index < BUILDING_PLANAR_ROLES.size() else "UNKNOWN",
            "vertex_count": vertices.size(),
            "storage_index_count": storage_indices.size(),
            "triangle_count": triangle_corner_indices.size() / 3,
            "positions": _vec3_rows(vertices),
            "normals": _vec3_rows(normals),
            "storage_indices": storage_indices,
            "triangle_corner_indices": triangle_corner_indices,
        })
    return {
        "surface_count": mesh.get_surface_count(),
        "total_vertices": total_vertices,
        "total_storage_indices": total_indices,
        "total_triangles": total_triangles,
        "surfaces": surfaces,
    }

func _index_existing_planar_building(node:MeshInstance3D)->Dictionary:
    var source_mesh := node.mesh as ArrayMesh
    if source_mesh == null:
        fail("Technical Art bundle expected pre-index ArrayMesh")
        return {}
    var before := _capture_surface_bundle(source_mesh)
    if before.is_empty():
        return {}
    var result := super._index_existing_planar_building(node)
    if result.is_empty():
        return {}
    var indexed_mesh := node.mesh as ArrayMesh
    if indexed_mesh == null:
        fail("Technical Art bundle expected indexed ArrayMesh")
        return {}
    var after := _capture_surface_bundle(indexed_mesh)
    if after.is_empty():
        return {}
    technical_art_index_bundle = {
        "schema": TECHNICAL_ART_INDEX_BUNDLE_SCHEMA,
        "runtime_parent_head": TECHNICAL_ART_RUNTIME_PARENT_HEAD,
        "building_hard_surface_head": BUILDING_PLANAR_HARD_SURFACE_HEAD,
        "building_materials_head": BUILDING_PLANAR_MATERIALS_HEAD,
        "representation_id": BUILDING_PLANAR_REPRESENTATION_ID,
        "material_partitions": BUILDING_PLANAR_ROLES.duplicate(),
        "before": before,
        "after": after,
        "truth_boundary": "Exact current-world Godot receiver observation only. The five caller-owned material partitions remain separate. The bundle records pre-index and post-index POSITION/NORMAL/index arrays so Technical Art can compare UC observer output to the real receiver. No Environment adoption, visual acceptance, target-device performance, arbitrary-mesh safety or source-topology rewrite is implied.",
    }
    return result

func write_receipt()->void:
    if technical_art_index_bundle.is_empty():
        fail("Technical Art index bundle was not captured")
        return
    var file := FileAccess.open(TECHNICAL_ART_INDEX_BUNDLE_PATH, FileAccess.WRITE)
    if file == null:
        fail("Technical Art index bundle could not be written")
        return
    file.store_string(JSON.stringify(technical_art_index_bundle, "  "))
    file.store_string("\n")
    file.close()
    receipt["technical_art_building_planar_role_uc_index_bridge"] = "EXACT_GODOT_BEFORE_AFTER_INDEX_BUNDLE_RETAINED"
    receipt["technical_art_building_planar_role_uc_index_bridge_truth_boundary"] = "Technical Art captures exact receiver arrays and compares them to a pinned UC observer only. Product representation, material semantics, visual acceptance, Runtime acceptance and Environment adoption remain separately owned."
    super.write_receipt()
