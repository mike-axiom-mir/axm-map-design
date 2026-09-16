extends "res://atmosphere_current_world_object_material_family_observe.gd"

const FOOTPRINT_REVIEW_MODE_ENV := "AXM_OBJECT_FOOTPRINT_REVIEW_MODE"
const FOOTPRINT_CONTROL_HIDDEN := "CONTROL_HIDDEN"
const FOOTPRINT_CANDIDATE_VISIBLE := "CANDIDATE_VISIBLE"
const FOOTPRINT_REVIEW_ASSET_ID := "environment:dressing:west-object-service-footprint-frame-001"
const FOOTPRINT_REVIEW_WORLD_HEAD := "6575cc38db9f0f62b14a82b352d8582edf89856d"
const FOOTPRINT_REVIEW_WORLD_DIGEST := "677dfe17afe49bf3f6edc28359c40a8add3dc357cb918529f0015a99f71baf70"

func _footprint_review_mode()->String:
    var mode:=OS.get_environment(FOOTPRINT_REVIEW_MODE_ENV)
    if mode!=FOOTPRINT_CONTROL_HIDDEN and mode!=FOOTPRINT_CANDIDATE_VISIBLE:
        fail("Object footprint review mode must be explicit")
        return "INVALID"
    return mode

func add_object_readability_dressing(root3d:Node3D,data:Dictionary)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_object_readability_dressing(root3d,data)
    var mode:=_footprint_review_mode()
    if result.is_empty() or mode=="INVALID":
        return result
    if String(result.get("asset_id",""))!=FOOTPRINT_REVIEW_ASSET_ID:
        fail("Object footprint review returned dressing identity drift")
        return result
    if root3d.get_child_count()!=child_count_before+1:
        fail("Object footprint review expected exactly one emitted dressing child")
        return result
    var emitted:=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is GeometryInstance3D):
        fail("Object footprint review emitted child is not GeometryInstance3D")
        return result
    (emitted as GeometryInstance3D).visible=(mode==FOOTPRINT_CANDIDATE_VISIBLE)
    result["review_visibility_mode"]=mode
    result["review_visibility_only"]=true
    return result

func write_receipt()->void:
    receipt["environment_object_footprint_review_mode"]=_footprint_review_mode()
    receipt["environment_object_footprint_review_world_head"]=FOOTPRINT_REVIEW_WORLD_HEAD
    receipt["environment_object_footprint_review_world_digest"]=FOOTPRINT_REVIEW_WORLD_DIGEST
    receipt["environment_object_footprint_review_policy"]="REVIEW_ONLY_VISIBILITY_TOGGLE__SAME_DRESSING_MESH_RESIDENCY__NO_SOURCE_OR_COMPOSITION_REWRITE"
    receipt["environment_object_footprint_review_truth_boundary"]="Exact current-world Object-material footprint-cue visibility A/B only. The cue mesh exists in both review modes so geometry/resource residency is held fixed while visibility is isolated; prior creation-cost evidence remains historical. Final Art Direction/Visual QA preference and target-device Runtime acceptance remain separate."
    super.write_receipt()
