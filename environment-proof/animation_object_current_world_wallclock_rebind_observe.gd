extends "res://animation_object_current_world_wallclock_observe.gd"

const REBIND_CONTRACT_SCHEMA := "axm.animation-object-current-world-wallclock/v0.2"
const REBIND_RECEIPT_SCHEMA := "axm.animation-object-current-world-wallclock-observation/v0.2"
const REBIND_PASS_STATE := "PASS_OBJECT_CURRENT_WORLD_OWNER_ANIMATION_WALLCLOCK_REBOUND_TO_TA_E085_RECEIVER"
const REBIND_TA_PARENT_HEAD := "e085437f6cc958bbf7c5c6464578923d542962b0"
const REBIND_PREDECESSOR_EVIDENCE_HEAD := "c2695f654f9dd44312ca5d205eceb27f7c2680ee"
const REBIND_FRAME_RULE := "MATCH_ACTUAL_PIVOT_QUATERNIONS_ABOUT_THE_EXACT_TECHNICAL_ART_HOST_AXIS_THEN_MAP_HOST_ANGLE_BACK_TO_OWNER_CONVENTION__DO_NOT_ASSUME_SOURCE_EULER_X_EQUALS_HOST_EULER_X"

var _rebind_axis := Vector3.RIGHT
var _rebind_lid:Node3D = null
var _rebind_pivots:Dictionary = {}

func _build_current_world()->Dictionary:
    var world := await super._build_current_world()
    if world.is_empty():
        return {}
    var placement := _motion_current_world_placement()
    if placement.is_empty():
        _animation_fail("Animation successor rebind could not recover exact Technical-Art host placement")
        return {}
    _rebind_axis = placement["axis_receiver"] as Vector3
    if absf(_rebind_axis.length() - 1.0) > 0.000001:
        _animation_fail("Animation successor rebind host axis is not unit length")
        return {}
    _rebind_lid = world["lid"] as Node3D
    _rebind_pivots = world["pivots"] as Dictionary
    if _rebind_lid == null or _rebind_pivots.size() != 2:
        _animation_fail("Animation successor rebind lost lid or bilateral latch pivots")
        return {}
    return world

func _owner_angle_from_host_pivot(node:Node3D)->float:
    var q := node.quaternion.normalized()
    # q and -q are the same orientation. Keep the shortest representation so
    # atan2 remains stable for this <=100 degree owner sequence.
    if q.w < 0.0:
        q = Quaternion(-q.x, -q.y, -q.z, -q.w)
    var signed_sin_half := Vector3(q.x, q.y, q.z).dot(_rebind_axis)
    var host_angle_rad := 2.0 * atan2(signed_sin_half, q.w)
    # Technical Art's verified e085 adapter reconstructs the owner motion in
    # Godot's proper-rotation host frame by negating the owner angle once.
    return -rad_to_deg(host_angle_rad)

func _latch_angles(pivots:Dictionary)->Array:
    var values:Array = []
    var keys:Array = pivots.keys()
    keys.sort()
    for sid in keys:
        values.append(_owner_angle_from_host_pivot(pivots[sid] as Node3D))
    return values

func _match_owner_sample(plan:Dictionary, position_s:float, _legacy_lid_euler_x:float, _legacy_latch_angles:Array)->Dictionary:
    if _rebind_lid == null or _rebind_pivots.size() != 2:
        return {"index":-1, "max_error_deg":INF, "time_error_s":INF}
    var observed_lid := _owner_angle_from_host_pivot(_rebind_lid)
    var observed_latches := _latch_angles(_rebind_pivots)
    var best_error := INF
    var best_time_error := INF
    var best_index := -1
    for raw in plan.get("samples", []) as Array:
        var row := raw as Dictionary
        var error := absf(observed_lid - float(row["lid_target_rotation_deg_x"]))
        for raw_latch in observed_latches:
            error = maxf(error, absf(float(raw_latch) - float(row["latch_target_rotation_deg_x"])))
        var time_error := absf(position_s - float(row["time_s"]))
        if error < best_error - 0.0000001 or (absf(error - best_error) <= 0.0000001 and time_error < best_time_error):
            best_error = error
            best_time_error = time_error
            best_index = int(row["index"])
    return {
        "index":best_index,
        "max_error_deg":best_error,
        "time_error_s":best_time_error,
        "owner_lid_rotation_deg":observed_lid,
        "owner_latch_rotation_deg":observed_latches
    }

func _write_animation_receipt()->void:
    animation_receipt["schema"] = REBIND_RECEIPT_SCHEMA
    animation_receipt["contract_schema"] = REBIND_CONTRACT_SCHEMA
    animation_receipt["technical_art_parent_head"] = REBIND_TA_PARENT_HEAD
    animation_receipt["predecessor_animation_evidence_head"] = REBIND_PREDECESSOR_EVIDENCE_HEAD
    animation_receipt["receiver_frame_matching_rule"] = REBIND_FRAME_RULE
    animation_receipt["acceptance_pose_match_uses_host_quaternion_projected_to_exact_receiver_axis"] = true
    animation_receipt["legacy_lid_rotation_deg_x_fields_are_host_euler_diagnostics_only"] = true
    if String(animation_receipt.get("state", "")) == "PASS_OBJECT_CURRENT_WORLD_OWNER_ANIMATION_WALLCLOCK_AND_SHADED_REVIEW_SEQUENCE":
        animation_receipt["state"] = REBIND_PASS_STATE
    if String(animation_receipt.get("state", "")) == REBIND_PASS_STATE:
        animation_receipt["truth_boundary"] = "The frozen 2.5 s / 40 Hz / 101-key owner sequence is replayed on exact Technical-Art successor e085 after its verified owner-glTF to Godot-host frame adapter. Acceptance pose membership is measured from actual pivot quaternions about the exact receiver axis and mapped back to owner angle convention; source Euler X is not assumed to equal host Euler X. The low-intrusion pass and separate shaded review remain observation only. No source retime, receiver construction authority, Runtime/controller, target-device/display performance, VFX, Environment adoption, gameplay, physics, Art/QA, CANON or production acceptance transfers."
    super._write_animation_receipt()
