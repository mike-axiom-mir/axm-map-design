extends "res://atmosphere_current_world_nature_leaf_flutter_observe.gd"

const BUILDING_COMPACT_GEOMETRY_HEAD := "16253e7dd2f8cd590667f9631e4b50fdfcc7280d"
const BUILDING_COMPACT_HARD_SURFACE_HEAD := "35d0ba62d7e534b3cd00ac69e99386843ffa3f2e"
const BUILDING_COMPACT_MATERIALS_HEAD := "4179aa1401f5a9114399e2f998c96809d4b8ed2e"
const BUILDING_COMPACT_REPRESENTATION_ID := "boundary-only-union-shell-conforming-compact-v2-001"
const BUILDING_COMPACT_STRUCTURE_RESULT := "PASS_CURRENT_WORLD_BUILDING_COMPACT_V2_STRUCTURE"
const BUILDING_COMPACT_RECEIVING_SCHEMA := "axm.environment-building-compact-v2-receiving/v0.1"
const BUILDING_COMPACT_ROLES := [
    "frame_galvanized",
    "infill_coating",
    "roof_membrane",
    "slab_mineral",
    "utility_panel_ochre",
]

func load_payload()->Dictionary:
    var compat := super.load_payload()
    if compat.is_empty():
        return {}
    if not FileAccess.file_exists(NATURE_MIGRATION_PAYLOAD_PATH):
        return {}
    var parsed = JSON.parse_string(FileAccess.get_file_as_string(NATURE_MIGRATION_PAYLOAD_PATH))
    if not (parsed is Dictionary):
        return {}
    var canonical := parsed as Dictionary
    if String(canonical.get("building_compact_v2_structure_result", "")) != BUILDING_COMPACT_STRUCTURE_RESULT:
        return {}
    if String(canonical.get("building_compact_v2_geometry_head", "")) != BUILDING_COMPACT_GEOMETRY_HEAD:
        return {}
    if String(canonical.get("building_compact_v2_hard_surface_head", "")) != BUILDING_COMPACT_HARD_SURFACE_HEAD:
        return {}
    if String(canonical.get("building_compact_v2_materials_head", "")) != BUILDING_COMPACT_MATERIALS_HEAD:
        return {}
    if String(canonical.get("building_compact_v2_selected_representation_id", "")) != BUILDING_COMPACT_REPRESENTATION_ID:
        return {}
    var states := canonical.get("states", []) as Array
    if states.size() != 17:
        return {}
    for row_value in states:
        var row := row_value as Dictionary
        var scene := row.get("scene", {}) as Dictionary
        var proof := scene.get("environment_building_material_receiving", {}) as Dictionary
        var receiving := proof.get("environment_building_compact_v2_receiving", {}) as Dictionary
        if String(receiving.get("schema", "")) != BUILDING_COMPACT_RECEIVING_SCHEMA:
            return {}
        if String(receiving.get("geometry_head", "")) != BUILDING_COMPACT_GEOMETRY_HEAD:
            return {}
        if String(receiving.get("hard_surface_head", "")) != BUILDING_COMPACT_HARD_SURFACE_HEAD:
            return {}
        if String(receiving.get("materials_head", "")) != BUILDING_COMPACT_MATERIALS_HEAD:
            return {}
        if String(receiving.get("selected_representation_id", "")) != BUILDING_COMPACT_REPRESENTATION_ID:
            return {}
        if int(receiving.get("vertex_count", -1)) != 1004 or int(receiving.get("triangle_count", -1)) != 2052:
            return {}
        if bool(receiving.get("environment_adoption", true)):
            return {}
    return compat

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var proof := data.get("environment_building_material_receiving", {}) as Dictionary
    if String(proof.get("asset_id", "")) != "source:building:service-pavilion-001":
        fail("missing exact compact-v2 Building receiving payload")
        return {}
    var receiving := proof.get("environment_building_compact_v2_receiving", {}) as Dictionary
    if String(receiving.get("schema", "")) != BUILDING_COMPACT_RECEIVING_SCHEMA:
        fail("compact-v2 receiving schema drift")
        return {}
    if String(receiving.get("geometry_head", "")) != BUILDING_COMPACT_GEOMETRY_HEAD:
        fail("compact-v2 Geometry head drift")
        return {}
    if String(receiving.get("hard_surface_head", "")) != BUILDING_COMPACT_HARD_SURFACE_HEAD:
        fail("compact-v2 Hard-Surface head drift")
        return {}
    if String(receiving.get("materials_head", "")) != BUILDING_COMPACT_MATERIALS_HEAD:
        fail("compact-v2 Materials head drift")
        return {}
    if String(receiving.get("selected_representation_id", "")) != BUILDING_COMPACT_REPRESENTATION_ID:
        fail("compact-v2 representation identity drift")
        return {}
    if bool(receiving.get("environment_adoption", true)):
        fail("compact-v2 review payload incorrectly claims Environment adoption")
        return {}

    var vertices := proof.get("vertices_source_xyz_m", []) as Array
    var surfaces := proof.get("surfaces", []) as Array
    if vertices.size() != 1004 or surfaces.size() != 5:
        fail("compact-v2 Building geometry/surface count drift")
        return {}

    var roles:Array = []
    var material_ids:Array = []
    var triangle_count := 0
    var mesh := ArrayMesh.new()
    for surface_value in surfaces:
        var surface := surface_value as Dictionary
        var role := String(surface.get("surface_role", ""))
        var material_id := String(surface.get("material_id", ""))
        roles.append(role)
        material_ids.append(material_id)
        if role != material_id:
            fail("compact-v2 Building material role/id drift")
            return {}
        var triangles := surface.get("triangles", []) as Array
        triangle_count += triangles.size()
        var st := SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for tri_value in triangles:
            var tri := tri_value as Array
            if tri.size() != 3:
                fail("compact-v2 Building triangle arity drift")
                return {}
            for raw_index in tri:
                var index := int(raw_index)
                if index < 0 or index >= vertices.size():
                    fail("compact-v2 Building triangle index drift")
                    return {}
                st.add_vertex(gvec(vertices[index] as Array))
        st.generate_normals()
        st.commit(mesh)
        var surface_index := mesh.get_surface_count() - 1
        mesh.surface_set_material(surface_index, building_material(surface))

    if roles != BUILDING_COMPACT_ROLES or triangle_count != 2052:
        fail("compact-v2 Building exact five-surface partition drift")
        return {}

    var node := MeshInstance3D.new()
    node.name = "source:building:service-pavilion-001"
    node.mesh = mesh
    root3d.add_child(node)
    return {
        "asset_id": "source:building:service-pavilion-001",
        "vertices": vertices.size(),
        "triangles": triangle_count,
        "surface_count": mesh.get_surface_count(),
        "material_ids": material_ids,
        "proof_culling": "CULL_DISABLED",
        "receiving_policy": String(proof.get("receiving_policy", "")),
        "representation_id": BUILDING_COMPACT_REPRESENTATION_ID,
        "compact_v2_geometry_head": BUILDING_COMPACT_GEOMETRY_HEAD,
        "compact_v2_hard_surface_head": BUILDING_COMPACT_HARD_SURFACE_HEAD,
        "compact_v2_materials_head": BUILDING_COMPACT_MATERIALS_HEAD,
    }

func write_receipt()->void:
    receipt["environment_building_compact_v2_representation_id"] = BUILDING_COMPACT_REPRESENTATION_ID
    receipt["environment_building_compact_v2_geometry_head"] = BUILDING_COMPACT_GEOMETRY_HEAD
    receipt["environment_building_compact_v2_hard_surface_head"] = BUILDING_COMPACT_HARD_SURFACE_HEAD
    receipt["environment_building_compact_v2_materials_head"] = BUILDING_COMPACT_MATERIALS_HEAD
    receipt["environment_building_compact_v2_structure_result"] = BUILDING_COMPACT_STRUCTURE_RESULT
    receipt["environment_building_compact_v2_truth_boundary"] = "Current-world receiving review only. Environment explicitly selects the source-owned compact-v2 Building representation for this evidence run while preserving header-segmented-23 as semantic source, the exact five material scalars, Nature flutter, indexed Object, visible footprint cue, Weather, route, cameras and lighting. No default adoption, Art/QA preference, Technical-Art transport acceptance or target-device performance acceptance is implied."
    super.write_receipt()
