extends "res://atmosphere_current_world_selected_roughness_compact_east_observe.gd"

const BUILDING_UTILITY_PANEL_CLEARANCE_STATE := "PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_CLEARANCE_REBIND_RECEIVER__VISUAL_OBSERVABILITY_CHARACTERIZED__ADOPTION_HELD"
const BUILDING_UTILITY_PANEL_CLEARANCE_RULE := "SOURCE_OWNED_RECEIVER_PLACEMENT_SUCCESSOR_MUST_BE_REBOUND_EXPLICITLY_IN_THE_REAL_WORLD_WHILE_UNRELATED_ASSET_CANDIDATES_REMAIN_EXACT_AND_ADOPTION_STAYS_HELD"
const BUILDING_CLEARANCE_SOURCE_HEAD := "fbfa3b47048755b45dac91451171d5511c8d4f47"
const BUILDING_CLEARANCE_SOURCE_CONTENT_HEAD := "32bbdd54f00aaac87ba8139bf932d8aff6109a66"
const BUILDING_CLEARANCE_PROCEDURAL_HEAD := "0c458e19cda73e26e90531d24fe7697b5a8d14fc"
const FRONT_PANEL_INDICES := [136,137,138,139,140,141,142,143]
const EAST_PANEL_INDICES := [144,145,146,147,148,149,150,151]
const FRONT_OLD_CENTER := Vector3(-2.45,-1.08,1.65)
const FRONT_NEW_CENTER := Vector3(-2.45,-1.10,1.65)
const EAST_OLD_CENTER := Vector3(3.88,0.10,1.65)
const EAST_NEW_CENTER := Vector3(3.90,0.10,1.65)
const FRONT_TRANSLATION := Vector3(0.0,-0.02,0.0)
const EAST_TRANSLATION := Vector3(0.02,0.0,0.0)
const CENTER_EPS := 0.0000001

func _source_vec(value:Variant)->Vector3:
    if not (value is Array):
        fail("Building clearance source vertex must be an xyz array")
        return Vector3.ZERO
    var row:=value as Array
    if row.size()!=3:
        fail("Building clearance source vertex arity drift")
        return Vector3.ZERO
    return Vector3(float(row[0]),float(row[1]),float(row[2]))

func _source_array(value:Vector3)->Array:
    return [value.x,value.y,value.z]

func _group_center(vertices:Array,indices:Array)->Vector3:
    var total:=Vector3.ZERO
    for raw in indices:
        var index:=int(raw)
        if index<0 or index>=vertices.size():
            fail("Building clearance panel vertex index drift")
            return Vector3.ZERO
        total+=_source_vec(vertices[index])
    return total/float(indices.size())

func _center_matches(actual:Vector3,expected:Vector3)->bool:
    return actual.distance_to(expected)<=CENTER_EPS

func _translate_group(vertices:Array,indices:Array,translation:Vector3)->void:
    for raw in indices:
        var index:=int(raw)
        vertices[index]=_source_array(_source_vec(vertices[index])+translation)

func add_building_material(root3d:Node3D,data:Dictionary)->Dictionary:
    var patched:=data.duplicate(true)
    var proof:=patched.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!=BUILDING_ASSET_ID:
        fail("Building clearance candidate missing exact Building receiving asset")
        return {}
    var vertices:=proof.get("vertices_source_xyz_m",[]) as Array
    if vertices.size()!=152:
        fail("Building clearance candidate requires exact 152-vertex receiving representation")
        return {}

    var front_before:=_group_center(vertices,FRONT_PANEL_INDICES)
    var east_before:=_group_center(vertices,EAST_PANEL_INDICES)
    if not _center_matches(front_before,FRONT_OLD_CENTER):
        fail("Building clearance front predecessor center drift: "+str(front_before))
        return {}
    if not _center_matches(east_before,EAST_OLD_CENTER):
        fail("Building clearance east predecessor center drift: "+str(east_before))
        return {}

    _translate_group(vertices,FRONT_PANEL_INDICES,FRONT_TRANSLATION)
    _translate_group(vertices,EAST_PANEL_INDICES,EAST_TRANSLATION)
    var front_after:=_group_center(vertices,FRONT_PANEL_INDICES)
    var east_after:=_group_center(vertices,EAST_PANEL_INDICES)
    if not _center_matches(front_after,FRONT_NEW_CENTER):
        fail("Building clearance front successor center drift: "+str(front_after))
        return {}
    if not _center_matches(east_after,EAST_NEW_CENTER):
        fail("Building clearance east successor center drift: "+str(east_after))
        return {}

    proof["vertices_source_xyz_m"]=vertices
    patched["environment_building_material_receiving"]=proof
    var result:=super.add_building_material(root3d,patched)
    if result.is_empty():
        return {}
    if int(result.get("vertices",-1))!=152 or int(result.get("triangles",-1))!=228 or int(result.get("surface_count",-1))!=5:
        fail("Building clearance candidate topology/surface identity drift")
        return {}

    result["environment_building_utility_panel_clearance_current_world"]={
        "schema":"axm.environment-building-utility-panel-clearance-current-world-observation/v0.1",
        "state":BUILDING_UTILITY_PANEL_CLEARANCE_STATE,
        "reusable_rule":BUILDING_UTILITY_PANEL_CLEARANCE_RULE,
        "building_source_head":BUILDING_CLEARANCE_SOURCE_HEAD,
        "building_source_content_head":BUILDING_CLEARANCE_SOURCE_CONTENT_HEAD,
        "building_procedural_head":BUILDING_CLEARANCE_PROCEDURAL_HEAD,
        "front_predecessor_center_source_xyz_m":_source_array(front_before),
        "front_successor_center_source_xyz_m":_source_array(front_after),
        "front_translation_source_xyz_m":_source_array(FRONT_TRANSLATION),
        "east_predecessor_center_source_xyz_m":_source_array(east_before),
        "east_successor_center_source_xyz_m":_source_array(east_after),
        "east_translation_source_xyz_m":_source_array(EAST_TRANSLATION),
        "translated_source_vertex_count":16,
        "topology_changed":false,
        "surface_partition_changed":false,
        "material_values_changed":false,
        "environment_adoption":false,
        "truth_boundary":"Real current-world Environment receiving candidate only. The two source-owned utility-panel proof boxes move by the exact owner/procedural +0.02 m receiver-normal successor delta; Building topology/material partition and unrelated Object, Nature, Weather, route, camera and lighting state remain owned by their existing lanes. Environment adoption remains held."
    }
    return result

func write_receipt()->void:
    receipt["environment_building_utility_panel_clearance_current_world_state"]=BUILDING_UTILITY_PANEL_CLEARANCE_STATE
    receipt["environment_building_utility_panel_clearance_current_world_rule"]=BUILDING_UTILITY_PANEL_CLEARANCE_RULE
    receipt["environment_building_utility_panel_clearance_source_head"]=BUILDING_CLEARANCE_SOURCE_HEAD
    receipt["environment_building_utility_panel_clearance_source_content_head"]=BUILDING_CLEARANCE_SOURCE_CONTENT_HEAD
    receipt["environment_building_utility_panel_clearance_procedural_head"]=BUILDING_CLEARANCE_PROCEDURAL_HEAD
    receipt["environment_building_utility_panel_clearance_adoption"]=false
    receipt["environment_building_utility_panel_clearance_truth_boundary"]="Exact two-panel receiver-normal placement successor only; no source rewrite, no automatic Environment adoption and no transfer of Art/QA, Runtime, Object, Nature, Weather or CANON authority."
    super.write_receipt()
