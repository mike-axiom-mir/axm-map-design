extends "res://atmosphere_current_world_nature_winding_migration_observe.gd"

const BUILDING_CURRENT_POLICY_HEAD := "a976af429b0ea90e0f0cc72d4a8bd4eb8fef22d3"
const BUILDING_CURRENT_POLICY_SCHEMA := "axm.building-current-emission-policy/v0.1"
const BUILDING_CURRENT_VARIANT := "header-segmented-23"
const BUILDING_LEGACY_VARIANT := "base-closed-outward-19"
const BUILDING_POLICY_REBIND_RESULT := "PASS_CURRENT_WORLD_BUILDING_CURRENT_SOURCE_POLICY_REBIND_STRUCTURE"

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
    if String(canonical.get("building_current_source_policy_head", "")) != BUILDING_CURRENT_POLICY_HEAD:
        return {}
    if String(canonical.get("building_current_source_policy_schema", "")) != BUILDING_CURRENT_POLICY_SCHEMA:
        return {}
    if String(canonical.get("building_current_source_variant_id", "")) != BUILDING_CURRENT_VARIANT:
        return {}
    if String(canonical.get("building_legacy_compatibility_variant_id", "")) != BUILDING_LEGACY_VARIANT:
        return {}
    if String(canonical.get("building_current_source_policy_rebind_result", "")) != BUILDING_POLICY_REBIND_RESULT:
        return {}
    var states := canonical.get("states", []) as Array
    if states.size() != 17:
        return {}
    for row in states:
        var scene := (row as Dictionary).get("scene", {}) as Dictionary
        var rebind := scene.get("environment_building_current_source_policy_rebind", {}) as Dictionary
        if String(rebind.get("source_policy_head", "")) != BUILDING_CURRENT_POLICY_HEAD:
            return {}
        if String(rebind.get("current_source_variant_id", "")) != BUILDING_CURRENT_VARIANT:
            return {}
        if bool(rebind.get("receiver_geometry_changed", true)):
            return {}
        if bool(rebind.get("receiver_materials_changed", true)):
            return {}
    return compat

func write_receipt()->void:
    receipt["environment_building_current_source_policy_head"] = BUILDING_CURRENT_POLICY_HEAD
    receipt["environment_building_current_source_policy_schema"] = BUILDING_CURRENT_POLICY_SCHEMA
    receipt["environment_building_current_source_variant_id"] = BUILDING_CURRENT_VARIANT
    receipt["environment_building_legacy_compatibility_variant_id"] = BUILDING_LEGACY_VARIANT
    receipt["environment_building_current_source_policy_rebind_result"] = BUILDING_POLICY_REBIND_RESULT
    receipt["environment_building_current_source_policy_truth_boundary"] = "Exact current-world receiving/provenance rebind only. The already-rendered 23-box segmented Building receiver is bound to Building Hard Surface's current-source policy without changing receiver geometry/materials or any Nature, Object, Weather, path, camera or lighting input. Historical producer identities remain preserved."
    super.write_receipt()
