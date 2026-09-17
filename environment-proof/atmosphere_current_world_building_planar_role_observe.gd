extends "res://atmosphere_current_world_nature_leaf_flutter_observe.gd"

const BUILDING_PLANAR_HARD_SURFACE_HEAD := "93f22e4eeb9bb32516d4b11f8d8bcf47d9792910"
const BUILDING_PLANAR_MATERIALS_HEAD := "4179aa1401f5a9114399e2f998c96809d4b8ed2e"
const BUILDING_PLANAR_REPRESENTATION_ID := "boundary-only-planar-role-rectangle-render-001"
const BUILDING_PLANAR_STRUCTURE_RESULT := "PASS_CURRENT_WORLD_BUILDING_PLANAR_ROLE_RENDER_RECEIVER_STRUCTURE"
const BUILDING_PLANAR_RECEIVING_SCHEMA := "axm.environment-building-planar-role-receiving/v0.1"
const BUILDING_PLANAR_ROLES := [
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
    if String(canonical.get("building_planar_role_structure_result", "")) != BUILDING_PLANAR_STRUCTURE_RESULT:
        return {}
    if String(canonical.get("building_planar_role_hard_surface_head", "")) != BUILDING_PLANAR_HARD_SURFACE_HEAD:
        return {}
    if String(canonical.get("building_planar_role_materials_head", "")) != BUILDING_PLANAR_MATERIALS_HEAD:
        return {}
    if String(canonical.get("building_planar_role_selected_representation_id", "")) != BUILDING_PLANAR_REPRESENTATION_ID:
        return {}
    var states := canonical.get("states", []) as Array
    if states.size() != 17:
        return {}
    for row_value in states:
        var row := row_value as Dictionary
        var scene := row.get("scene", {}) as Dictionary
        var proof := scene.get("environment_building_material_receiving", {}) as Dictionary
        var receiving := proof.get("environment_building_planar_role_receiving", {}) as Dictionary
        if String(receiving.get("schema", "")) != BUILDING_PLANAR_RECEIVING_SCHEMA:
            return {}
        if String(receiving.get("hard_surface_head", "")) != BUILDING_PLANAR_HARD_SURFACE_HEAD:
            return {}
        if String(receiving.get("materials_head", "")) != BUILDING_PLANAR_MATERIALS_HEAD:
            return {}
        if String(receiving.get("selected_representation_id", "")) != BUILDING_PLANAR_REPRESENTATION_ID:
            return {}
        if int(receiving.get("vertex_count", -1)) != 672 or int(receiving.get("triangle_count", -1)) != 336:
            return {}
        if int(receiving.get("rectangle_count", -1)) != 168:
            return {}
        if bool(receiving.get("environment_adoption", true)):
            return {}
    return compat

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var proof := data.get("environment_building_material_receiving", {}) as Dictionary
    if String(proof.get("asset_id", "")) != "source:building:service-pavilion-001":
        fail("missing exact planar-role Building receiving payload")
        return {}
    var receiving := proof.get("environment_building_planar_role_receiving", {}) as Dictionary
    if String(receiving.get("schema", "")) != BUILDING_PLANAR_RECEIVING_SCHEMA:
        fail("planar-role receiving schema drift")
        return {}
    if String(receiving.get("hard_surface_head", "")) != BUILDING_PLANAR_HARD_SURFACE_HEAD:
        fail("planar-role Hard-Surface head drift")
        return {}
    if String(receiving.get("materials_head", "")) != BUILDING_PLANAR_MATERIALS_HEAD:
        fail("planar-role Materials head drift")
        return {}
    if String(receiving.get("selected_representation_id", "")) != BUILDING_PLANAR_REPRESENTATION_ID:
        fail("planar-role representation identity drift")
        return {}
    if bool(receiving.get("environment_adoption", true)):
        fail("planar-role review payload incorrectly claims Environment adoption")
        return {}

    var vertices := proof.get("vertices_source_xyz_m", []) as Array
    var surfaces := proof.get("surfaces", []) as Array
    if vertices.size() != 672 or surfaces.size() != 5:
        fail("planar-role Building geometry/surface count drift")
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
            fail("planar-role Building material role/id drift")
            return {}
        var triangles := surface.get("triangles", []) as Array
        triangle_count += triangles.size()
        var st := SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for tri_value in triangles:
            var tri := tri_value as Array
            if tri.size() != 3:
                fail("planar-role Building triangle arity drift")
                return {}
            for raw_index in tri:
                var index := int(raw_index)
                if index < 0 or index >= vertices.size():
                    fail("planar-role Building triangle index drift")
                    return {}
                st.add_vertex(gvec(vertices[index] as Array))
        st.generate_normals()
        st.commit(mesh)
        var surface_index := mesh.get_surface_count() - 1
        mesh.surface_set_material(surface_index, building_material(surface))

    if roles != BUILDING_PLANAR_ROLES or triangle_count != 336:
        fail("planar-role Building exact five-surface partition drift")
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
        "representation_id": BUILDING_PLANAR_REPRESENTATION_ID,
        "planar_role_hard_surface_head": BUILDING_PLANAR_HARD_SURFACE_HEAD,
        "planar_role_materials_head": BUILDING_PLANAR_MATERIALS_HEAD,
    }

func write_receipt()->void:
    receipt["environment_building_planar_role_representation_id"] = BUILDING_PLANAR_REPRESENTATION_ID
    receipt["environment_building_planar_role_hard_surface_head"] = BUILDING_PLANAR_HARD_SURFACE_HEAD
    receipt["environment_building_planar_role_materials_head"] = BUILDING_PLANAR_MATERIALS_HEAD
    receipt["environment_building_planar_role_structure_result"] = BUILDING_PLANAR_STRUCTURE_RESULT
    receipt["environment_building_planar_role_truth_boundary"] = "Current-world receiving review only. Environment explicitly selects the source-owned planar-role Building render receiver for this evidence run while preserving header-segmented-23 as semantic source, the exact five current material scalars, Nature flutter, indexed Object, visible footprint cue, Weather, route, cameras and lighting. No default adoption, Art/QA preference, Technical-Art transport acceptance or target-device performance acceptance is implied."
    super.write_receipt()
