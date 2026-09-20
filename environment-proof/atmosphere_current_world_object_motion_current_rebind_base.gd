extends "res://atmosphere_current_world_object_rigid_component_current_rebind_observe.gd"

const MOTION_PLAN_PATH := "res://generated/object-motion-receiver-plan.json"
const CURRENT_WORLD_PATH := "res://generated/current_world_nature_winding_migration.json"
const MOTION_STATE := "PASS_CURRENT_WORLD_OBJECT_ANIMATION_OWNER_SAMPLE_RECEIVER__VFX_RUNTIME_ENV_ADOPTION_HELD"
const MOTION_RULE := "ANIMATION_OWNER_SAMPLES_MAY_ENTER_A_CURRENT_WORLD_RIGID_RECEIVER_ONLY_THROUGH_EXACT_COMPONENT_PIVOT_AXIS_AND_WORLD_PLACEMENT_BINDINGS_WITH_NEUTRAL_ENDPOINT_AND_OWNER_DISTANCE_INVARIANTS_PROVEN"
const MOTION_SCHEMA := "axm.environment-object-motion-receiver-plan/v0.1"
const EXACT_ANIMATION_HEAD := "86bdbe9771bf9eb1bc92bd4160442941763fab1d"
const EXACT_SEQUENCE_DIGEST := "0a3523cf792264f610881552fd2ebd438aabdfd05e30e92af9dbb33ded1fa2d3"
const EXACT_OBJECT_SOURCE_HEAD := "d3fa10a270faae7925811f44f03381fe5c5d0215"
const PLACEMENT_POLICY := "PRESERVE_TARGET_CENTER_XY__PRESERVE_TARGET_Z_ROTATION__GROUND_SOURCE_MIN_Z__NO_SOURCE_SCALE"
const EPS_DEG := 0.00002
const EPS_M := 0.000001
const OWNER_DISTANCE_EPS_M := 0.00001

func _motion_read_json(path:String)->Dictionary:
    if not FileAccess.file_exists(path):
        fail("Technical Art Object motion JSON missing: "+path)
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(path))
    if not (parsed is Dictionary):
        fail("Technical Art Object motion JSON invalid: "+path)
        return {}
    return parsed as Dictionary

func _motion_find_node(root:Node,wanted:String)->Node3D:
    if String(root.name)==wanted and root is Node3D:
        return root as Node3D
    for child in root.get_children():
        var found:=_motion_find_node(child,wanted)
        if found!=null:
            return found
    return null

func _motion_point_to_container(container:Node3D,node:Node3D,point:Vector3)->Vector3:
    var cursor:Node3D=node
    var result:=point
    while cursor!=container:
        result=cursor.transform*result
        var parent:=cursor.get_parent()
        if not (parent is Node3D):
            fail("Technical Art Object motion node escaped receiver hierarchy")
            return Vector3.ZERO
        cursor=parent as Node3D
    return result

func _motion_receiver_local_component_center(container:Node3D,node:Node3D)->Vector3:
    if not (node is MeshInstance3D):
        fail("Technical Art Object motion expected MeshInstance3D: "+String(node.name))
        return Vector3.ZERO
    var instance:=node as MeshInstance3D
    if instance.mesh==null:
        fail("Technical Art Object motion mesh missing: "+String(node.name))
        return Vector3.ZERO
    var minimum:=Vector3(INF,INF,INF)
    var maximum:=Vector3(-INF,-INF,-INF)
    var referenced:=0
    for surface_index in range(instance.mesh.get_surface_count()):
        var arrays:=instance.mesh.surface_get_arrays(surface_index)
        if arrays.size()<=Mesh.ARRAY_INDEX:
            fail("Technical Art Object motion component array layout drift")
            return Vector3.ZERO
        var raw_positions=arrays[Mesh.ARRAY_VERTEX]
        var raw_indices=arrays[Mesh.ARRAY_INDEX]
        if typeof(raw_positions)!=TYPE_PACKED_VECTOR3_ARRAY or typeof(raw_indices)!=TYPE_PACKED_INT32_ARRAY:
            fail("Technical Art Object motion component requires indexed PackedVector3 geometry")
            return Vector3.ZERO
        var positions:=raw_positions as PackedVector3Array
        var indices:=raw_indices as PackedInt32Array
        for raw_index in indices:
            var index:=int(raw_index)
            if index<0 or index>=positions.size():
                fail("Technical Art Object motion component index out of range")
                return Vector3.ZERO
            var point:=_motion_point_to_container(container,node,positions[index])
            minimum=Vector3(minf(minimum.x,point.x),minf(minimum.y,point.y),minf(minimum.z,point.z))
            maximum=Vector3(maxf(maximum.x,point.x),maxf(maximum.y,point.y),maxf(maximum.z,point.z))
            referenced+=1
    if referenced<=0:
        fail("Technical Art Object motion component has no referenced vertices")
        return Vector3.ZERO
    return (minimum+maximum)*0.5

func _motion_vec3(values:Array)->Vector3:
    if values.size()!=3:
        fail("Technical Art Object motion vec3 arity drift")
        return Vector3.ZERO
    return Vector3(float(values[0]),float(values[1]),float(values[2]))

func _motion_same_vec3(a:Vector3,b:Vector3,epsilon:float=0.000000001)->bool:
    return a.distance_to(b)<=epsilon

func _motion_current_world_placement()->Dictionary:
    var world:=_motion_read_json(CURRENT_WORLD_PATH)
    if world.is_empty():
        return {}
    if String(world.get("object_source_sha256",""))!=EXACT_OBJECT_SOURCE_SHA256 or String(world.get("object_source_head",""))!=EXACT_OBJECT_SOURCE_HEAD:
        fail("Technical Art Object motion current-world source identity drift")
        return {}
    var source=world.get("object_source",{}) as Dictionary
    if String(source.get("source_sha256",""))!=EXACT_OBJECT_SOURCE_SHA256 or String(source.get("source_head",""))!=EXACT_OBJECT_SOURCE_HEAD:
        fail("Technical Art Object motion embedded current-world source identity drift")
        return {}
    var states=world.get("states",[]) as Array
    if states.size()!=17:
        fail("Technical Art Object motion exact current-world state count drift")
        return {}
    var first:Dictionary={}
    for state_index in range(states.size()):
        var state=states[state_index] as Dictionary
        var scene=state.get("scene",{}) as Dictionary
        var replacement=scene.get("environment_object_replacement",{}) as Dictionary
        if replacement.is_empty():
            fail("Technical Art Object motion current-world placement missing at state "+str(state_index))
            return {}
        if String(replacement.get("source_sha256",""))!=EXACT_OBJECT_SOURCE_SHA256 or String(replacement.get("source_head",""))!=EXACT_OBJECT_SOURCE_HEAD:
            fail("Technical Art Object motion current-world replacement source drift")
            return {}
        if String(replacement.get("placement_policy",""))!=PLACEMENT_POLICY:
            fail("Technical Art Object motion current-world placement policy drift")
            return {}
        var reserved=replacement.get("reserved_proxy_position_m",[]) as Array
        var bounds=replacement.get("source_world_bounds_m",{}) as Dictionary
        var world_min=bounds.get("min",[]) as Array
        if reserved.size()!=3 or world_min.size()!=3:
            fail("Technical Art Object motion current-world placement coordinate arity drift")
            return {}
        var translation_source:=Vector3(float(reserved[0]),float(reserved[1]),float(world_min[2]))
        var yaw_deg:=float(replacement.get("reserved_proxy_rotation_deg",INF))
        if not is_finite(yaw_deg):
            fail("Technical Art Object motion current-world yaw missing")
            return {}
        if state_index==0:
            first={"translation_source":translation_source,"yaw_deg":yaw_deg}
        else:
            if not _motion_same_vec3(first["translation_source"] as Vector3,translation_source) or absf(float(first["yaw_deg"])-yaw_deg)>0.000000001:
                fail("Technical Art Object motion placement differs across exact current-world states")
                return {}
    var theta:=deg_to_rad(float(first["yaw_deg"]))
    var c:=cos(theta)
    var s:=sin(theta)
    var axis_receiver:=Vector3(c,0.0,s).normalized()
    return {
        "state_count":states.size(),
        "translation_source":first["translation_source"],
        "yaw_deg":first["yaw_deg"],
        "axis_receiver":axis_receiver,
        "placement_policy":PLACEMENT_POLICY
    }

func _motion_owner_receiver_point_to_world_receiver(local_receiver:Vector3,placement:Dictionary)->Vector3:
    # Owner receiver convention is [source X, source Z, source Y]. Convert back to source,
    # apply Environment's exact source-space Z-yaw + translation, then return to receiver convention.
    var source_local:=Vector3(local_receiver.x,local_receiver.z,local_receiver.y)
    var theta:=deg_to_rad(float(placement["yaw_deg"]))
    var c:=cos(theta)
    var s:=sin(theta)
    var translation=placement["translation_source"] as Vector3
    var source_world:=Vector3(
        c*source_local.x-s*source_local.y+translation.x,
        s*source_local.x+c*source_local.y+translation.y,
        source_local.z+translation.z
    )
    return Vector3(source_world.x,source_world.z,source_world.y)

func _motion_wrap_at_world_pivot(container:Node3D,node:Node3D,pivot_world:Vector3,name:String)->Node3D:
    var old_container_transform:=node.transform
    var wrapper:=Node3D.new()
    wrapper.name=name
    wrapper.position=pivot_world
    container.add_child(wrapper)
    node.reparent(wrapper,false)
    node.transform=wrapper.transform.affine_inverse()*old_container_transform
    return wrapper

func _motion_quaternion(axis:Vector3,degrees:float)->Quaternion:
    return Quaternion(axis,deg_to_rad(degrees)).normalized()

func _motion_add_track(animation:Animation,root:Node3D,node:Node3D,samples:Array,key:String,axis:Vector3)->int:
    var track:=animation.add_track(Animation.TYPE_VALUE)
    animation.track_set_path(track,NodePath(str(root.get_path_to(node))+":quaternion"))
    animation.track_set_interpolation_type(track,Animation.INTERPOLATION_NEAREST)
    animation.value_track_set_update_mode(track,Animation.UPDATE_DISCRETE)
    for row in samples:
        animation.track_insert_key(track,float(row["time_s"]),_motion_quaternion(axis,float(row[key])))
    return track

func _motion_apply_sample(plan:Dictionary,index:int,lid_pivot:Node3D,latch_pivots:Dictionary,axis:Vector3)->Dictionary:
    var samples=plan.get("samples",[]) as Array
    var row=samples[index] as Dictionary
    var lid_expected:=_motion_quaternion(axis,float(row["lid_target_rotation_deg_x"]))
    var latch_expected:=_motion_quaternion(axis,float(row["latch_target_rotation_deg_x"]))
    lid_pivot.quaternion=lid_expected
    for sid in latch_pivots.keys():
        var pivot=latch_pivots[sid] as Node3D
        pivot.quaternion=latch_expected
    var lid_error:=rad_to_deg(lid_pivot.quaternion.angle_to(lid_expected))
    var latch_error:=0.0
    for sid in latch_pivots.keys():
        var pivot=latch_pivots[sid] as Node3D
        latch_error=maxf(latch_error,rad_to_deg(pivot.quaternion.angle_to(latch_expected)))
    if lid_error>EPS_DEG or latch_error>EPS_DEG:
        fail("Technical Art Object motion sampled target quaternion drift")
        return {}
    return {"index":index,"time_s":row["time_s"],"lid_error_deg":lid_error,"max_latch_error_deg":latch_error,"lid_target_rotation_deg_x":row["lid_target_rotation_deg_x"],"latch_target_rotation_deg_x":row["latch_target_rotation_deg_x"]}

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_static_source(root3d,source,cull_target_asset_id)
    if String(result.get("asset_id",""))!=OBJECT_ASSET_ID:
        return result
    if root3d.get_child_count()!=child_count_before+1:
        fail("Technical Art Object motion expected one emitted rigid receiver child")
        return {}
    var emitted=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is Node3D):
        fail("Technical Art Object motion emitted rigid receiver is not Node3D")
        return {}
    var container:=emitted as Node3D
    var plan:=_motion_read_json(MOTION_PLAN_PATH)
    if plan.is_empty():
        return {}
    if String(plan.get("schema",""))!=MOTION_SCHEMA or String(plan.get("result",""))!="PASS_OBJECT_ANIMATION_OWNER_SAMPLES_ADAPTED_TO_CURRENT_WORLD_RIGID_RECEIVER":
        fail("Technical Art Object motion plan state drift")
        return {}
    if String(plan.get("object_source_sha256",""))!=EXACT_OBJECT_SOURCE_SHA256 or String(plan.get("object_technical_art_head",""))!=EXACT_OBJECT_TA_HEAD:
        fail("Technical Art Object motion source/TA identity drift")
        return {}
    if String(plan.get("animation_head",""))!=EXACT_ANIMATION_HEAD or String(plan.get("sequence_digest",""))!=EXACT_SEQUENCE_DIGEST:
        fail("Technical Art Object motion Animation identity drift")
        return {}
    var samples=plan.get("samples",[]) as Array
    var owner_invariants=plan.get("owner_target_motion_invariants",{}) as Dictionary
    if samples.size()!=101 or owner_invariants.is_empty():
        fail("Technical Art Object motion sample/invariant contract drift")
        return {}

    var placement:=_motion_current_world_placement()
    if placement.is_empty():
        return {}
    var axis=placement["axis_receiver"] as Vector3
    if absf(axis.length()-1.0)>0.000001:
        fail("Technical Art Object motion transformed hinge axis is not unit length")
        return {}

    var lid:=_motion_find_node(container,"lid_shell")
    var keeper0:=_motion_find_node(container,"latch_0_keeper")
    var keeper1:=_motion_find_node(container,"latch_1_keeper")
    if lid==null or keeper0==null or keeper1==null:
        fail("Technical Art Object motion receiver hierarchy missing")
        return {}

    var rigid_map:=_motion_read_json(RIGID_COMPONENT_MAP_PATH)
    var hinge_local_values=rigid_map.get("hinge_pivot_receiver_xyz_m",[]) as Array
    if hinge_local_values.size()!=3:
        fail("Technical Art Object motion hinge pivot receiver identity missing")
        return {}
    var hinge_local:=_motion_vec3(hinge_local_values)
    var hinge_world:=_motion_owner_receiver_point_to_world_receiver(hinge_local,placement)
    var neutral_lid_center:=_motion_receiver_local_component_center(container,lid)
    var lid_pivot:=_motion_wrap_at_world_pivot(container,lid,hinge_world,"technical_art_motion_hinge_world_pivot")
    var neutral_lid_wrapper_drift:=neutral_lid_center.distance_to(_motion_receiver_local_component_center(container,lid))
    if neutral_lid_wrapper_drift>EPS_M:
        fail("Technical Art Object motion world hinge pivot insertion changed neutral lid geometry")
        return {}

    var stations=plan.get("stations",[]) as Array
    if stations.size()!=2:
        fail("Technical Art Object motion station count drift")
        return {}
    var latch_pivots:Dictionary={}
    var levers:Dictionary={}
    var station_world_pivots:Dictionary={}
    var neutral_lever_centers:Dictionary={}
    for raw in stations:
        var station=raw as Dictionary
        var sid:=String(station.get("station_id",""))
        var lever_name:=String(station.get("lever_component",""))
        var lever:=_motion_find_node(container,lever_name)
        if lever==null:
            fail("Technical Art Object motion lever missing: "+lever_name)
            return {}
        neutral_lever_centers[lever_name]=_motion_receiver_local_component_center(container,lever)
        var local_pivot:=_motion_vec3(station.get("pivot_receiver_xyz_m",[]) as Array)
        var world_pivot:=_motion_owner_receiver_point_to_world_receiver(local_pivot,placement)
        var pivot:=_motion_wrap_at_world_pivot(container,lever,world_pivot,"technical_art_motion_latch_world_pivot_"+sid)
        latch_pivots[sid]=pivot
        levers[sid]=lever
        station_world_pivots[sid]=[world_pivot.x,world_pivot.y,world_pivot.z]

    var neutral_pivot_drift:=neutral_lid_wrapper_drift
    for sid in latch_pivots.keys():
        var lever=levers[sid] as Node3D
        neutral_pivot_drift=maxf(neutral_pivot_drift,(neutral_lever_centers[String(lever.name)] as Vector3).distance_to(_motion_receiver_local_component_center(container,lever)))
    if neutral_pivot_drift>EPS_M:
        fail("Technical Art Object motion world-placement pivot insertion changed neutral geometry")
        return {}

    var animation:=Animation.new()
    animation.length=2.5
    animation.loop_mode=Animation.LOOP_NONE
    var lid_track:=_motion_add_track(animation,container,lid_pivot,samples,"lid_target_rotation_deg_x",axis)
    var latch_tracks:Array=[]
    for sid in latch_pivots.keys():
        latch_tracks.append(_motion_add_track(animation,container,latch_pivots[sid] as Node3D,samples,"latch_target_rotation_deg_x",axis))
    if animation.track_get_key_count(lid_track)!=101:
        fail("Technical Art Object motion lid track key count drift")
        return {}
    for track in latch_tracks:
        if animation.track_get_key_count(int(track))!=101:
            fail("Technical Art Object motion latch track key count drift")
            return {}

    var player:=AnimationPlayer.new()
    player.name="AXM_CURRENT_WORLD_OBJECT_OWNER_SAMPLES"
    container.add_child(player)
    player.root_node=NodePath("..")
    var library:=AnimationLibrary.new()
    library.add_animation("owner_samples",animation)
    player.add_animation_library("",library)

    var start_keeper0:=_motion_receiver_local_component_center(container,keeper0)
    var start_keeper1:=_motion_receiver_local_component_center(container,keeper1)
    var start_levers:Dictionary={}
    for sid in levers.keys():
        start_levers[sid]=_motion_receiver_local_component_center(container,levers[sid] as Node3D)
    var probes:Array=[]
    probes.append(_motion_apply_sample(plan,0,lid_pivot,latch_pivots,axis))
    probes.append(_motion_apply_sample(plan,10,lid_pivot,latch_pivots,axis))
    var release_keeper_drift:=maxf(start_keeper0.distance_to(_motion_receiver_local_component_center(container,keeper0)),start_keeper1.distance_to(_motion_receiver_local_component_center(container,keeper1)))
    var release_min_lever_move:=999.0
    for sid in levers.keys():
        release_min_lever_move=minf(release_min_lever_move,(start_levers[sid] as Vector3).distance_to(_motion_receiver_local_component_center(container,levers[sid] as Node3D)))
    var owner_release:=float(owner_invariants.get("release_min_lever_move_m",-1.0))
    var release_owner_residual:=absf(release_min_lever_move-owner_release)
    if release_keeper_drift>EPS_M or release_owner_residual>OWNER_DISTANCE_EPS_M:
        fail("Technical Art Object motion release sample diverged from rigid-placement-invariant owner target")
        return {}
    probes.append(_motion_apply_sample(plan,50,lid_pivot,latch_pivots,axis))
    var peak_min_keeper_move:=minf(start_keeper0.distance_to(_motion_receiver_local_component_center(container,keeper0)),start_keeper1.distance_to(_motion_receiver_local_component_center(container,keeper1)))
    var owner_peak:=float(owner_invariants.get("peak_min_keeper_move_m",-1.0))
    var peak_owner_residual:=absf(peak_min_keeper_move-owner_peak)
    if peak_owner_residual>OWNER_DISTANCE_EPS_M:
        fail("Technical Art Object motion peak sample diverged from rigid-placement-invariant owner target")
        return {}
    probes.append(_motion_apply_sample(plan,100,lid_pivot,latch_pivots,axis))
    var endpoint_keeper_drift:=maxf(start_keeper0.distance_to(_motion_receiver_local_component_center(container,keeper0)),start_keeper1.distance_to(_motion_receiver_local_component_center(container,keeper1)))
    var endpoint_lever_drift:=0.0
    for sid in levers.keys():
        endpoint_lever_drift=maxf(endpoint_lever_drift,(start_levers[sid] as Vector3).distance_to(_motion_receiver_local_component_center(container,levers[sid] as Node3D)))
    if endpoint_keeper_drift>EPS_M or endpoint_lever_drift>EPS_M:
        fail("Technical Art Object motion endpoint closure drift")
        return {}

    var selected_text:=OS.get_environment("AXM_OBJECT_MOTION_SAMPLE_INDEX")
    if selected_text.is_empty():
        selected_text="0"
    var selected:=int(selected_text)
    if selected<0 or selected>=101:
        fail("Technical Art Object motion selected sample out of range")
        return {}
    var selected_observation:=_motion_apply_sample(plan,selected,lid_pivot,latch_pivots,axis)
    var translation=placement["translation_source"] as Vector3
    receipt["technical_art_object_motion_historical_ta_head"]="965fb2f24dbd0b0cbb748d9f8b8712d62966315f"
    receipt["technical_art_object_motion_historical_receipt_reused_as_current_evidence"]=false
    result["environment_object_motion_receiver"]={
        "schema":"axm.environment-object-motion-current-world-observation/v0.2",
        "state":MOTION_STATE,
        "reusable_rule":MOTION_RULE,
        "animation_head":EXACT_ANIMATION_HEAD,
        "sequence_digest":EXACT_SEQUENCE_DIGEST,
        "track_count":3,
        "key_counts":[101,101,101],
        "component_center_observer":"referenced_indexed_vertices_only",
        "current_world_state_count":placement["state_count"],
        "current_world_placement_policy":placement["placement_policy"],
        "current_world_source_translation_xyz_m":[translation.x,translation.y,translation.z],
        "current_world_source_yaw_deg":placement["yaw_deg"],
        "current_world_receiver_hinge_axis_xyz":[axis.x,axis.y,axis.z],
        "current_world_receiver_hinge_pivot_xyz_m":[hinge_world.x,hinge_world.y,hinge_world.z],
        "current_world_receiver_latch_pivots_xyz_m":station_world_pivots,
        "neutral_pivot_wrapper_max_drift_m":neutral_pivot_drift,
        "release_keeper_drift_m":release_keeper_drift,
        "release_min_lever_move_m":release_min_lever_move,
        "owner_release_min_lever_move_m":owner_release,
        "release_owner_distance_residual_m":release_owner_residual,
        "peak_min_keeper_move_m":peak_min_keeper_move,
        "owner_peak_min_keeper_move_m":owner_peak,
        "peak_owner_distance_residual_m":peak_owner_residual,
        "endpoint_keeper_drift_m":endpoint_keeper_drift,
        "endpoint_lever_drift_m":endpoint_lever_drift,
        "probe_samples":probes,
        "selected_sample":selected_observation,
        "sample_application_mode":"exact_owner_sample_world_placement_adapted_receiver_transform_before_scene_attach",
        "vfx_adoption":false,
        "runtime_acceptance":false,
        "environment_adoption":false,
        "art_qa_acceptance":false,
        "canon":false,
        "truth_boundary":"Current target-Rigging-bound Object Animation owner samples are adapted onto the freshly rebound current-world rigid component receiver; historical Object TA provenance is retained separately and not reused as current evidence. after applying Environment's exact rigid placement to owner pivots and hinge axis. Component-center evidence observes only referenced indexed vertices, because each receiver component intentionally reuses a parent-sized vertex array with a component-only index subset. Owner-target center-displacement distances are checked as rigid-placement invariants. The proof applies selected discrete samples before scene attachment and retains a 3x101 AnimationPlayer representation, but does not claim wall-clock playback. Technical Art does not retime motion, infer mechanics, adopt VFX, claim Runtime/device performance, Environment adoption, final visual acceptance, CANON or production readiness."
    }
    return result

func write_receipt()->void:
    receipt["technical_art_object_motion_current_world_state"]=MOTION_STATE
    receipt["technical_art_object_motion_current_world_rule"]=MOTION_RULE
    receipt["technical_art_object_motion_animation_head"]=EXACT_ANIMATION_HEAD
    receipt["technical_art_object_motion_sequence_digest"]=EXACT_SEQUENCE_DIGEST
    receipt["technical_art_object_motion_world_placement_adapted"]=true
    receipt["technical_art_object_motion_component_center_observer"]="referenced_indexed_vertices_only"
    receipt["technical_art_object_motion_vfx_adoption"]=false
    receipt["technical_art_object_motion_runtime_acceptance"]=false
    receipt["technical_art_object_motion_environment_adoption"]=false
    receipt["technical_art_object_motion_art_qa_acceptance"]=false
    receipt["technical_art_object_motion_truth_boundary"]="Receiver-only discrete sampled-motion transport on the current-world Object rigid boundary. Animation owns timing/easing/order; Object/Rigging own hierarchy/pivots; Environment owns placement/adoption; Runtime owns device/performance; Art/QA own appearance. Technical Art only adapts the exact owner frame through the exact Environment rigid placement and proves retained invariants; wall-clock playback is not claimed here."
    super.write_receipt()
