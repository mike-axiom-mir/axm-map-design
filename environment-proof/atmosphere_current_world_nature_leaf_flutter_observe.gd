extends "res://atmosphere_current_world_nature_split_surface_culling_observe.gd"

const NATURE_LEAF_FLUTTER_VFX_HEAD := "ecade64227ba1d3d1faf029ca7188ea63c2560ec"
const NATURE_LEAF_FLUTTER_GEOMETRY_HEAD := "da3adbef4de8cddb8f3ebe841d39bb31a8936f5f"
const NATURE_LEAF_FLUTTER_STRUCTURE_RESULT := "PASS_CURRENT_WORLD_NATURE_LEAF_FLUTTER_STRUCTURE"
const NATURE_LEAF_FLUTTER_RECEIVING_SCHEMA := "axm.environment-nature-leaf-flutter-receiving/v0.1"

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
    if String(canonical.get("nature_leaf_flutter_vfx_head", "")) != NATURE_LEAF_FLUTTER_VFX_HEAD:
        return {}
    if String(canonical.get("nature_leaf_flutter_geometry_context_head", "")) != NATURE_LEAF_FLUTTER_GEOMETRY_HEAD:
        return {}
    if String(canonical.get("nature_leaf_flutter_structure_result", "")) != NATURE_LEAF_FLUTTER_STRUCTURE_RESULT:
        return {}
    var counts := canonical.get("nature_leaf_flutter_changed_vertex_counts", []) as Array
    if counts.size() != 17 or int(counts[0]) != 0 or int(counts[16]) != 0:
        return {}
    var states := canonical.get("states", []) as Array
    if states.size() != 17:
        return {}
    for index in range(states.size()):
        var row := states[index] as Dictionary
        var scene := row.get("scene", {}) as Dictionary
        var sapling := scene.get("sapling", {}) as Dictionary
        var receiving := sapling.get("environment_nature_leaf_flutter_receiving", {}) as Dictionary
        if String(receiving.get("schema", "")) != NATURE_LEAF_FLUTTER_RECEIVING_SCHEMA:
            return {}
        if String(receiving.get("vfx_head", "")) != NATURE_LEAF_FLUTTER_VFX_HEAD:
            return {}
        if String(receiving.get("geometry_leaf_context_head", "")) != NATURE_LEAF_FLUTTER_GEOMETRY_HEAD:
            return {}
        if int(receiving.get("source_phase_index", -1)) != index:
            return {}
        if bool(receiving.get("explicit_leaf_backface_geometry_adopted", true)):
            return {}
        if String(receiving.get("woody_surface_cull", "")) != "CULL_BACK":
            return {}
        if String(receiving.get("foliage_surface_cull", "")) != "CULL_DISABLED":
            return {}
    return compat

func fill_sapling(sapling:Dictionary)->Dictionary:
    var result := super.fill_sapling(sapling)
    if result.is_empty():
        return result
    var receiving := sapling.get("environment_nature_leaf_flutter_receiving", {}) as Dictionary
    result["leaf_flutter_vfx_head"] = String(receiving.get("vfx_head", ""))
    result["leaf_flutter_phase_index"] = int(receiving.get("source_phase_index", -1))
    result["leaf_flutter_changed_front_vertex_count"] = int(receiving.get("changed_front_vertex_count", -1))
    result["leaf_flutter_maximum_added_vertex_displacement_m"] = float(receiving.get("maximum_added_vertex_displacement_m", -1.0))
    return result

func write_receipt()->void:
    receipt["environment_nature_leaf_flutter_vfx_head"] = NATURE_LEAF_FLUTTER_VFX_HEAD
    receipt["environment_nature_leaf_flutter_geometry_context_head"] = NATURE_LEAF_FLUTTER_GEOMETRY_HEAD
    receipt["environment_nature_leaf_flutter_structure_result"] = NATURE_LEAF_FLUTTER_STRUCTURE_RESULT
    receipt["environment_nature_leaf_flutter_receiving_schema"] = NATURE_LEAF_FLUTTER_RECEIVING_SCHEMA
    receipt["environment_nature_leaf_flutter_truth_boundary"] = "Current-world receiving evidence only. Nature VFX PR #11's bounded deterministic leaf-local source phases are rendered on the accepted 390v/570t woody-back/foliage-two-sided receiver. Building, indexed Object, visible footprint cue, static Nature, Weather, route, cameras and lighting remain fixed. Motion naturalness, shaded backface look, continuous wall-clock timing, physical wind and target-device performance remain separate gates."
    super.write_receipt()
