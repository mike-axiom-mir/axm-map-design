extends "res://atmosphere_current_world_selected_roughness_compact_east_observe.gd"

const BUILDING_UTILITY_PANEL_CLEARANCE_STATE := "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_CLEARANCE_REBIND_RECEIVER__VISUAL_OBSERVABILITY_CHARACTERIZED__ADOPTION_HELD"
const BUILDING_UTILITY_PANEL_CLEARANCE_RULE := "SOURCE_OWNED_RECEIVER_PLACEMENT_SUCCESSOR_MUST_BE_REBOUND_EXPLICITLY_IN_THE_REAL_WORLD_WHILE_UNRELATED_ASSET_CANDIDATES_REMAIN_EXACT_AND_ADOPTION_STAYS_HELD"
const BUILDING_CLEARANCE_SOURCE_HEAD := "fbfa3b47048755b45dac91451171d5511c8d4f47"
const BUILDING_CLEARANCE_SOURCE_CONTENT_HEAD := "32bbdd54f00aaac87ba8139bf932d8aff6109a66"
const BUILDING_CLEARANCE_PROCEDURAL_HEAD := "0c458e19cda73e26e90531d24fe7697b5a8d14fc"
const CLEARANCE_CURRENT_POLICY_HEAD := "a976af429b0ea90e0f0cc72d4a8bd4eb8fef22d3"
const CLEARANCE_CURRENT_VARIANT := "header-segmented-23"
const BUILDING_SEGMENTATION_SOURCE_HEAD := "34124101e616c423c5a3ed5e122ddf09b98a1650"
const BUILDING_SEGMENTATION_REVISION := "service-pavilion-001/interpenetration-free-header-segmentation-003"
const RECEIVER_PLACEMENT_TRANSLATION := Vector3(0.0,7.2,0.0)
const FRONT_PANEL_INDICES := [168,169,170,171,172,173,174,175]
const EAST_PANEL_INDICES := [176,177,178,179,180,181,182,183]
const FRONT_OLD_SOURCE_CENTER := Vector3(-2.45,-1.08,1.65)
const FRONT_NEW_SOURCE_CENTER := Vector3(-2.45,-1.10,1.65)
const EAST_OLD_SOURCE_CENTER := Vector3(3.88,0.10,1.65)
const EAST_NEW_SOURCE_CENTER := Vector3(3.90,0.10,1.65)
const FRONT_OLD_RECEIVER_CENTER := Vector3(-2.45,6.12,1.65)
const FRONT_NEW_RECEIVER_CENTER := Vector3(-2.45,6.10,1.65)
const EAST_OLD_RECEIVER_CENTER := Vector3(3.88,7.30,1.65)
const EAST_NEW_RECEIVER_CENTER := Vector3(3.90,7.30,1.65)
const FRONT_TRANSLATION := Vector3(0.0,-0.02,0.0)
const EAST_TRANSLATION := Vector3(0.02,0.0,0.0)
const CENTER_EPS := 0.0000001

func _source_vec(value:Variant)->Vector3:
    if not (value is Array):
        fail("Building clearance current receiver vertex must be an xyz array")
        return Vector3.ZERO
    var row:=value as Array
    if row.size()!=3:
        fail("Building clearance current receiver vertex arity drift")
        return Vector3.ZERO
    return Vector3(float(row[0]),float(row[1]),float(row[2]))

func _source_array(value:Vector3)->Array:
    return [value.x,value.y,value.z]

func _group_center(vertices:Array,indices:Array)->Vector3:
    var total:=Vector3.ZERO
    for raw in indices:
        var index:=int(raw)
        if index<0 or index>=vertices.size():
            fail("Building clearance current receiver panel vertex index drift")
            return Vector3.ZERO
        total+=_source_vec(vertices[index])
    return total/float(indices.size())

func _center_matches(actual:Vector3,expected:Vector3)->bool:
    return actual.distance_to(expected)<=CENTER_EPS

func _translate_group(vertices:Array,indices:Array,translation:Vector3)->void:
    for raw in indices:
        var index:=int(raw)
        vertices[index]=_source_array(_source_vec(vertices[index])+translation)

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var patched:=data.duplicate(true)
    var current_policy:=patched.get("environment_building_current_source_policy_rebind",{}) as Dictionary
    if String(current_policy.get("source_policy_head",""))!=CLEARANCE_CURRENT_POLICY_HEAD:
        fail("Building clearance candidate current-source policy head drift")
        return {}
    if String(current_policy.get("current_source_variant_id",""))!=CLEARANCE_CURRENT_VARIANT:
        fail("Building clearance candidate current-source variant drift")
        return {}
    if bool(current_policy.get("receiver_geometry_changed",true)) or bool(current_policy.get("receiver_materials_changed",true)):
        fail("Building clearance candidate requires exact pre-rebind current receiver")
        return {}

    var proof:=patched.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!=BUILDING_ASSET_ID:
        fail("Building clearance candidate missing exact current Building receiving asset")
        return {}
    var segmentation:=proof.get("source_header_segmentation_rebind",{}) as Dictionary
    if String(segmentation.get("source_head",""))!=BUILDING_SEGMENTATION_SOURCE_HEAD:
        fail("Building clearance candidate segmentation source head drift")
        return {}
    if String(segmentation.get("segmentation_revision",""))!=BUILDING_SEGMENTATION_REVISION:
        fail("Building clearance candidate segmentation revision drift")
        return {}
    var placement:=_source_vec(segmentation.get("placement_translation_source_xyz_m",[]))
    if not _center_matches(placement,RECEIVER_PLACEMENT_TRANSLATION):
        fail("Building clearance candidate placement translation drift: "+str(placement))
        return {}

    var vertices:=proof.get("vertices_source_xyz_m",[]) as Array
    if vertices.size()!=184:
        fail("Building clearance candidate requires exact current 184-vertex segmented receiver")
        return {}

    var front_before:=_group_center(vertices,FRONT_PANEL_INDICES)
    var east_before:=_group_center(vertices,EAST_PANEL_INDICES)
    if not _center_matches(front_before,FRONT_OLD_RECEIVER_CENTER):
        fail("Building clearance front current-receiver predecessor center drift: "+str(front_before))
        return {}
    if not _center_matches(east_before,EAST_OLD_RECEIVER_CENTER):
        fail("Building clearance east current-receiver predecessor center drift: "+str(east_before))
        return {}
    if not _center_matches(front_before-RECEIVER_PLACEMENT_TRANSLATION,FRONT_OLD_SOURCE_CENTER):
        fail("Building clearance front source predecessor projection drift")
        return {}
    if not _center_matches(east_before-RECEIVER_PLACEMENT_TRANSLATION,EAST_OLD_SOURCE_CENTER):
        fail("Building clearance east source predecessor projection drift")
        return {}

    _translate_group(vertices,FRONT_PANEL_INDICES,FRONT_TRANSLATION)
    _translate_group(vertices,EAST_PANEL_INDICES,EAST_TRANSLATION)
    var front_after:=_group_center(vertices,FRONT_PANEL_INDICES)
    var east_after:=_group_center(vertices,EAST_PANEL_INDICES)
    if not _center_matches(front_after,FRONT_NEW_RECEIVER_CENTER):
        fail("Building clearance front current-receiver successor center drift: "+str(front_after))
        return {}
    if not _center_matches(east_after,EAST_NEW_RECEIVER_CENTER):
        fail("Building clearance east current-receiver successor center drift: "+str(east_after))
        return {}
    if not _center_matches(front_after-RECEIVER_PLACEMENT_TRANSLATION,FRONT_NEW_SOURCE_CENTER):
        fail("Building clearance front source successor projection drift")
        return {}
    if not _center_matches(east_after-RECEIVER_PLACEMENT_TRANSLATION,EAST_NEW_SOURCE_CENTER):
        fail("Building clearance east source successor projection drift")
        return {}

    proof["vertices_source_xyz_m"]=vertices
    patched["environment_building_material_receiving"]=proof
    var result:=super.add_segmented_building(root3d,patched)
    if result.is_empty():
        return {}
    if int(result.get("vertices",-1))!=184 or int(result.get("triangles",-1))!=276 or int(result.get("surface_count",-1))!=5:
        fail("Building clearance current segmented receiver topology/surface identity drift")
        return {}

    result["environment_building_utility_panel_clearance_current_world"]={
        "schema":"axm.environment-building-utility-panel-clearance-current-world-observation/v0.2",
        "state":BUILDING_UTILITY_PANEL_CLEARANCE_STATE,
        "reusable_rule":BUILDING_UTILITY_PANEL_CLEARANCE_RULE,
        "building_source_head":BUILDING_CLEARANCE_SOURCE_HEAD,
        "building_source_content_head":BUILDING_CLEARANCE_SOURCE_CONTENT_HEAD,
        "building_procedural_head":BUILDING_CLEARANCE_PROCEDURAL_HEAD,
        "current_receiver_source_policy_head":CLEARANCE_CURRENT_POLICY_HEAD,
        "current_receiver_source_variant_id":CLEARANCE_CURRENT_VARIANT,
        "current_receiver_segmentation_source_head":BUILDING_SEGMENTATION_SOURCE_HEAD,
        "current_receiver_segmentation_revision":BUILDING_SEGMENTATION_REVISION,
        "placement_translation_source_xyz_m":_source_array(RECEIVER_PLACEMENT_TRANSLATION),
        "front_predecessor_center_source_xyz_m":_source_array(front_before-RECEIVER_PLACEMENT_TRANSLATION),
        "front_successor_center_source_xyz_m":_source_array(front_after-RECEIVER_PLACEMENT_TRANSLATION),
        "front_predecessor_center_receiver_xyz_m":_source_array(front_before),
        "front_successor_center_receiver_xyz_m":_source_array(front_after),
        "front_translation_source_xyz_m":_source_array(FRONT_TRANSLATION),
        "east_predecessor_center_source_xyz_m":_source_array(east_before-RECEIVER_PLACEMENT_TRANSLATION),
        "east_successor_center_source_xyz_m":_source_array(east_after-RECEIVER_PLACEMENT_TRANSLATION),
        "east_predecessor_center_receiver_xyz_m":_source_array(east_before),
        "east_successor_center_receiver_xyz_m":_source_array(east_after),
        "east_translation_source_xyz_m":_source_array(EAST_TRANSLATION),
        "translated_source_vertex_count":16,
        "topology_changed":false,
        "surface_partition_changed":false,
        "material_values_changed":false,
        "environment_adoption":false,
        "truth_boundary":"Real current-world Environment receiving candidate on the active header-segmented-23 Building receiver only. The first 152-vertex compatibility-path attempt is not promoted. These two source-owned utility-panel boxes move by the exact owner/procedural +0.02 m receiver-normal successor delta while current Building topology/material partition and unrelated Object, Nature, Weather, route, camera and lighting state remain owned by their existing lanes. Environment adoption remains held."
    }
    return result

func write_receipt()->void:
    receipt["environment_building_utility_panel_clearance_current_world_state"]=BUILDING_UTILITY_PANEL_CLEARANCE_STATE
    receipt["environment_building_utility_panel_clearance_current_world_rule"]=BUILDING_UTILITY_PANEL_CLEARANCE_RULE
    receipt["environment_building_utility_panel_clearance_source_head"]=BUILDING_CLEARANCE_SOURCE_HEAD
    receipt["environment_building_utility_panel_clearance_source_content_head"]=BUILDING_CLEARANCE_SOURCE_CONTENT_HEAD
    receipt["environment_building_utility_panel_clearance_procedural_head"]=BUILDING_CLEARANCE_PROCEDURAL_HEAD
    receipt["environment_building_utility_panel_clearance_current_receiver_source_policy_head"]=CLEARANCE_CURRENT_POLICY_HEAD
    receipt["environment_building_utility_panel_clearance_current_receiver_variant_id"]=CLEARANCE_CURRENT_VARIANT
    receipt["environment_building_utility_panel_clearance_current_receiver_segmentation_source_head"]=BUILDING_SEGMENTATION_SOURCE_HEAD
    receipt["environment_building_utility_panel_clearance_current_receiver_segmentation_revision"]=BUILDING_SEGMENTATION_REVISION
    receipt["environment_building_utility_panel_clearance_adoption"]=false
    receipt["environment_building_utility_panel_clearance_truth_boundary"]="Exact two-panel receiver-normal placement successor on the active 184-vertex header-segmented-23 current receiver only; no legacy compatibility-path promotion, no source rewrite, no automatic Environment adoption and no transfer of Art/QA, Runtime, Object, Nature, Weather or CANON authority."
    super.write_receipt()
