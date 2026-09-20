extends "res://animation_object_current_world_wallclock_rebind_observe.gd"

# Acceptance shim for the current Technical-Art fc567 successor.
# The receiver plan already contains the adapted host-frame target angles.
# Compare the actual pivot quaternions directly with quaternions generated
# from those targets about the exact Technical-Art host axis. Scalar angles
# below are diagnostics only; they are not the acceptance primitive.
func _anim_match_owner_sample(plan:Dictionary, position_s:float, lid:Node3D, pivots:Dictionary)->Dictionary:
    var actual_lid_q := lid.quaternion.normalized()
    var actual_latch_qs:Array = []
    var pivot_keys:Array = pivots.keys()
    pivot_keys.sort()
    for sid in pivot_keys:
        actual_latch_qs.append((pivots[sid] as Node3D).quaternion.normalized())

    var best_error := INF
    var best_time_error := INF
    var best_index := -1
    var best_lid_target := 0.0
    var best_latch_target := 0.0
    for raw in plan.get("samples", []) as Array:
        var row := raw as Dictionary
        var lid_target := float(row["lid_target_rotation_deg_x"])
        var latch_target := float(row["latch_target_rotation_deg_x"])
        var expected_lid_q := _motion_quaternion(anim_host_axis, lid_target)
        var expected_latch_q := _motion_quaternion(anim_host_axis, latch_target)
        var error := rad_to_deg(actual_lid_q.angle_to(expected_lid_q))
        for raw_q in actual_latch_qs:
            error = maxf(error, rad_to_deg((raw_q as Quaternion).angle_to(expected_latch_q)))
        var time_error := absf(position_s - float(row["time_s"]))
        if error < best_error - 0.0000001 or (absf(error - best_error) <= 0.0000001 and time_error < best_time_error):
            best_error = error
            best_time_error = time_error
            best_index = int(row["index"])
            best_lid_target = lid_target
            best_latch_target = latch_target

    var latch_diagnostics:Array = []
    for _sid in pivot_keys:
        latch_diagnostics.append(best_latch_target)
    return {
        "index":best_index,
        "max_error_deg":best_error,
        "time_error_s":best_time_error,
        "adapted_receiver_lid_rotation_deg":best_lid_target,
        "adapted_receiver_latch_rotation_deg":latch_diagnostics
    }
