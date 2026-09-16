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
    var result:=super.add_object_readability_dressing(root3d,data)
    var mode:=_footprint_review_mode()
    if result.is_empty() or mode=="INVALID":
        return result
    var found:=false
    for child in root3d.get_children():
        if String(child.name)==FOOTPRINT_REVIEW_ASSET_ID:
            found=true
            if child is GeometryInstance3D:
                (child as GeometryInstance3D).visible=(mode==FOOTPRINT_CANDIDATE_VISIBLE)
            else:
                fail("Object footprint review node is not GeometryInstance3D")
    if not found:
        fail("Object footprint review dressing node missing")
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
