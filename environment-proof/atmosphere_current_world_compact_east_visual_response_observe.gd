extends "res://atmosphere_current_world_nature_leaf_flutter_observe.gd"

const COMPACT_EAST_VFX_HEAD := "cef2ad78d8e36a55ada5dad07329f1a7125d48de"
const COMPACT_EAST_STRUCTURE_RESULT := "PASS_CURRENT_WORLD_COMPACT_EAST_VISUAL_RESPONSE_STRUCTURE"
const COMPACT_EAST_RECEIVING_SCHEMA := "axm.environment-compact-east-visual-response-receiving/v0.1"
const COMPACT_EAST_ASSET_ID := "source:nature:compact-east-tree-neutral-001"
const COMPACT_EAST_WEATHER_SEMANTICS := "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED"

func _compact_east(scene:Dictionary)->Dictionary:
    var found:Array = []
    for raw in scene.get("additional_source_meshes", []) as Array:
        var source := raw as Dictionary
        if String(source.get("asset_id", "")) == COMPACT_EAST_ASSET_ID:
            found.append(source)
    if found.size() != 1:
        return {}
    return found[0] as Dictionary

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
    if String(canonical.get("compact_east_visual_response_vfx_head", "")) != COMPACT_EAST_VFX_HEAD:
        return {}
    if String(canonical.get("compact_east_visual_response_structure_result", "")) != COMPACT_EAST_STRUCTURE_RESULT:
        return {}
    if String(canonical.get("compact_east_visual_response_weather_semantics", "")) != COMPACT_EAST_WEATHER_SEMANTICS:
        return {}
    var states := canonical.get("states", []) as Array
    if states.size() != 17:
        return {}
    for index in range(states.size()):
        var row := states[index] as Dictionary
        var scene := row.get("scene", {}) as Dictionary
        var source := _compact_east(scene)
        if source.is_empty():
            return {}
        var receiving := source.get("environment_compact_east_visual_response_receiving", {}) as Dictionary
        if String(receiving.get("schema", "")) != COMPACT_EAST_RECEIVING_SCHEMA:
            return {}
        if String(receiving.get("vfx_head", "")) != COMPACT_EAST_VFX_HEAD:
            return {}
        if int(receiving.get("source_phase_index", -1)) != index:
            return {}
        if String(receiving.get("weather_semantics", "")) != COMPACT_EAST_WEATHER_SEMANTICS:
            return {}
    return compat

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var result := super.add_static_source(root3d, source, cull_target_asset_id)
    if result.is_empty():
        return result
    if String(result.get("asset_id", "")) == COMPACT_EAST_ASSET_ID:
        var receiving := source.get("environment_compact_east_visual_response_receiving", {}) as Dictionary
        if String(receiving.get("schema", "")) != COMPACT_EAST_RECEIVING_SCHEMA:
            fail("compact-east visual response receiving schema missing")
            return {}
        result["compact_east_visual_response_vfx_head"] = String(receiving.get("vfx_head", ""))
        result["compact_east_visual_response_phase_index"] = int(receiving.get("source_phase_index", -1))
        result["compact_east_visual_response_maximum_added_vertex_displacement_m"] = float(receiving.get("maximum_added_vertex_displacement_m", -1.0))
        result["compact_east_visual_response_weather_semantics"] = String(receiving.get("weather_semantics", ""))
    return result

func write_receipt()->void:
    receipt["environment_compact_east_visual_response_vfx_head"] = COMPACT_EAST_VFX_HEAD
    receipt["environment_compact_east_visual_response_structure_result"] = COMPACT_EAST_STRUCTURE_RESULT
    receipt["environment_compact_east_visual_response_receiving_schema"] = COMPACT_EAST_RECEIVING_SCHEMA
    receipt["environment_compact_east_visual_response_weather_semantics"] = COMPACT_EAST_WEATHER_SEMANTICS
    receipt["environment_compact_east_visual_response_phase_count"] = 17
    receipt["environment_compact_east_visual_response_truth_boundary"] = "Current-world receiving evidence only. The exact compact-east Nature VFX source-local 17-state bounded visual response is rendered inside the accepted Nature leaf-flutter current-world receiver. Existing Weather, west-sapling leaf flutter, Building, Object, rear Nature, route, cameras and lighting remain separate preserved identities. Visible shape change is not physical wind, biomechanics, gameplay/physics, wall-clock timing, target-device performance or final Art/Visual-QA acceptance."
    super.write_receipt()
