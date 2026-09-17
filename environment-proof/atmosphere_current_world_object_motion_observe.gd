extends "res://atmosphere_current_world_object_motion_observe_base.gd"

# The owner Animation/UC proof intentionally uses the glTF receiver frame
# source [x,y,z] -> [x,z,y], which is a handedness-changing reflection.
# The current Map proof host builds source geometry through gvec(),
# source [x,y,z] -> Godot [x,z,-y], which is a proper rotation.
# Keep those two boundaries explicit instead of silently treating them as
# the same receiver frame.
const OWNER_FRAME_CONVERSION := "source [x,y,z] -> UC/glTF [x,z,y]; handedness flip requires target +X rotation = negative source mathematical +X rotation"
const CURRENT_WORLD_HOST_FRAME_CONVERSION := "source [x,y,z] -> Godot current-world [x,z,-y]"
const OWNER_TO_HOST_FRAME_RULE := "UC_GLTF_TO_GODOT_CURRENT_WORLD_REFLECTION_Z__NEGATE_OWNER_ROTATION_ANGLE_AFTER_WORLD_AXIS_PLACEMENT"

func _motion_read_json(path:String)->Dictionary:
    var parsed:=super._motion_read_json(path)
    if parsed.is_empty():
        return parsed
    if path==MOTION_PLAN_PATH and String(parsed.get("coordinate_conversion",""))!=OWNER_FRAME_CONVERSION:
        fail("Technical Art Object motion owner receiver frame identity drift")
        return {}
    return parsed

func _motion_current_world_placement()->Dictionary:
    var placement:=super._motion_current_world_placement()
    if placement.is_empty():
        return {}
    # Parent value is the exact Environment yaw expressed in the owner
    # UC/glTF receiver convention [x,z,y].  The real current-world host uses
    # gvec() == [x,z,-y], so reflect only receiver Z before using it as the
    # Godot-space world hinge axis.
    var owner_axis=placement["axis_receiver"] as Vector3
    var host_axis:=Vector3(owner_axis.x,owner_axis.y,-owner_axis.z).normalized()
    if absf(host_axis.length()-1.0)>0.000001:
        fail("Technical Art Object motion Godot host hinge axis is not unit length")
        return {}
    placement["owner_receiver_axis"]=owner_axis
    placement["axis_receiver"]=host_axis
    placement["owner_frame_conversion"]=OWNER_FRAME_CONVERSION
    placement["current_world_host_frame_conversion"]=CURRENT_WORLD_HOST_FRAME_CONVERSION
    placement["owner_to_host_frame_rule"]=OWNER_TO_HOST_FRAME_RULE
    return placement

func _motion_owner_receiver_point_to_world_receiver(local_receiver:Vector3,placement:Dictionary)->Vector3:
    # Parent performs owner [x,z,y] -> source, Environment source-space yaw +
    # translation, then returns the world point in owner [x,z,y].  Convert
    # that point to the actual Godot current-world host [x,z,-y].
    var owner_world:=super._motion_owner_receiver_point_to_world_receiver(local_receiver,placement)
    return Vector3(owner_world.x,owner_world.y,-owner_world.z)

func _motion_quaternion(axis:Vector3,degrees:float)->Quaternion:
    # The owner target angle already contains the glTF handedness flip.
    # Reconstructing the same source rotation in Godot's proper-rotation
    # [x,z,-y] frame therefore negates that owner angle exactly once.
    return Quaternion(axis,deg_to_rad(-degrees)).normalized()

func _motion_apply_sample(plan:Dictionary,index:int,lid_pivot:Node3D,latch_pivots:Dictionary,axis:Vector3)->Dictionary:
    var observed:=super._motion_apply_sample(plan,index,lid_pivot,latch_pivots,axis)
    if observed.is_empty():
        return {}
    observed["godot_host_lid_rotation_deg_about_world_axis"]=-float(observed["lid_target_rotation_deg_x"])
    observed["godot_host_latch_rotation_deg_about_world_axis"]=-float(observed["latch_target_rotation_deg_x"])
    observed["owner_to_host_frame_rule"]=OWNER_TO_HOST_FRAME_RULE
    return observed

func write_receipt()->void:
    receipt["technical_art_object_motion_owner_frame_conversion"]=OWNER_FRAME_CONVERSION
    receipt["technical_art_object_motion_current_world_host_frame_conversion"]=CURRENT_WORLD_HOST_FRAME_CONVERSION
    receipt["technical_art_object_motion_owner_to_host_frame_rule"]=OWNER_TO_HOST_FRAME_RULE
    receipt["technical_art_object_motion_uc_modified"]=false
    receipt["technical_art_object_motion_host_frame_truth_boundary"]="The exact owner Animation/UC transform contract is preserved in its [x,z,y] receiver frame, then adapted only at the real Map/Godot receiving boundary to the host's existing [x,z,-y] gvec convention. No source motion, Environment placement, Object/Rigging semantics, UC implementation, VFX, Runtime acceptance, Art/QA acceptance or CANON state is changed."
    super.write_receipt()
