extends "res://atmosphere_current_world_object_indexed_footprint_observe.gd"

const NATURE_MIGRATION_PAYLOAD_PATH := "res://generated/current_world_nature_winding_migration.json"
const NATURE_MIGRATION_SCHEMA := "axm.environment-current-world-nature-source-winding-migration/v0.1"
const NATURE_MIGRATION_STATUS := "PASS_CURRENT_WORLD_NATURE_SOURCE_WINDING_MIGRATION_STRUCTURE"
const NATURE_VFX_HEAD := "0b9167ac6d7b6d94d9fef92720f8c60e3ef45700"
const NATURE_SOURCE_MIGRATION_HEAD := "4ddbe66e5c02d22407ef773d5346a2fe6f349a2d"
const NATURE_GEOMETRY_ORACLE := "e2224d4bf88f7e68503072c884e5a726b8d0c53d"
const NATURE_MATERIALS_HEAD_MIGRATION := "8b2e0523d7a2b210c6404f15bafb08fbedcad4dd"
const NATURE_FAMILY_ID_MIGRATION := "nature-woody-foliage-family-001"

func load_payload()->Dictionary:
    if not FileAccess.file_exists(NATURE_MIGRATION_PAYLOAD_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(NATURE_MIGRATION_PAYLOAD_PATH))
    if not (parsed is Dictionary):
        return {}
    var canonical=parsed as Dictionary
    if String(canonical.get("schema",""))!=NATURE_MIGRATION_SCHEMA:
        return {}
    if String(canonical.get("status",""))!=NATURE_MIGRATION_STATUS:
        return {}
    if String(canonical.get("nature_vfx_head",""))!=NATURE_VFX_HEAD:
        return {}
    if String(canonical.get("nature_source_migration_head",""))!=NATURE_SOURCE_MIGRATION_HEAD:
        return {}
    if String(canonical.get("nature_geometry_oracle",""))!=NATURE_GEOMETRY_ORACLE:
        return {}
    if String(canonical.get("nature_materials_head",""))!=NATURE_MATERIALS_HEAD_MIGRATION:
        return {}
    if String((canonical.get("nature_material_family",{}) as Dictionary).get("family_id",""))!=NATURE_FAMILY_ID_MIGRATION:
        return {}
    var checks=canonical.get("checks",{}) as Dictionary
    for key in checks:
        if not bool(checks[key]):
            return {}
    var compat=canonical.duplicate(true)
    compat["schema"]="axm.environment-current-world-weather-width-evidence/v0.1"
    compat["status"]="PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE"
    compat["parent_variant_head"]="e482d003853e52fc835f1797ddfb6506a50083ef"
    return compat

func write_receipt()->void:
    receipt["environment_nature_vfx_head"]=NATURE_VFX_HEAD
    receipt["environment_nature_source_migration_head"]=NATURE_SOURCE_MIGRATION_HEAD
    receipt["environment_nature_geometry_oracle"]=NATURE_GEOMETRY_ORACLE
    receipt["environment_nature_source_migration_mode"]="SOURCE_GENERATOR_WINDING_MIGRATION_WITH_REBOUND_VISUAL_WIND_RESPONSE"
    receipt["environment_nature_source_migration_truth_boundary"]="Exact current-world receiving proof for Nature PR #9 source-generator cap winding plus Nature VFX PR #11 rebound sapling response. Building, indexed Object, visible Object footprint cue, Nature woody/foliage material family, Weather source-width presentation, route, cameras and lighting remain owned by their existing lanes. Rendered differences are evidence for Art/QA review, not an automatic visual-neutrality claim."
    super.write_receipt()
