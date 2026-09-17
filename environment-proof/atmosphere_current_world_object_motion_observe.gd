extends "res://atmosphere_current_world_object_rigid_component_observe.gd"

const MOTION_PLAN_PATH := "res://generated/object-motion-receiver-plan.json"
const MOTION_STATE := "PASS_CURRENT_WORLD_OBJECT_ANIMATION_OWNER_SAMPLE_RECEIVER__VFX_RUNTIME_ENV_ADOPTION_HELD"
const MOTION_RULE := "ANIMATION_OWNER_SAMPLES_MAY_ENTER_A_CURRENT_WORLD_RIGID_RECEIVER_ONLY_THROUGH_EXACT_COMPONENT_PIVOT_AND_TARGET_ROTATION_BINDINGS_WITH_NEUTRAL_AND_ENDPOINT_CLOSURE_PROVEN"
const MOTION_SCHEMA := "axm.environment-object-motion-receiver-plan/v0.1"
const EXACT_ANIMATION_HEAD := "c688936a84f80f292e43587c9d3386bd717f8178"
const EXACT_SEQUENCE_DIGEST := "0a3523cf792264f610881552fd2ebd438aabdfd05e30e92af9dbb33ded1fa2d3"
const EPS_DEG := 0.00002
const EPS_M := 0.000001

func _motion_read_json(path:String)->Dictionary:
    if not FileAccess.file_exists(path):
        fail("Technical Art Object motion plan missing: "+path)
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(path))
    if not (parsed is Dictionary):
        fail("Technical Art Object motion plan invalid JSON")
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

func _motion_receiver_local_mesh_center(container:Node3D,node:Node3D)->Vector3:
    if not (node is MeshInstance3D):
        fail("Technical Art Object motion expected MeshInstance3D: "+String(node.name))
        return Vector3.ZERO
    var instance:=node as MeshInstance3D
    if instance.mesh==null:
        fail("Technical Art Object motion mesh missing: "+String(node.name))
        return Vector3.ZERO
    var point:=instance.mesh.get_aabb().get_center()
    var cursor:Node3D=node
    while cursor!=container:
        point=cursor.transform*point
        var parent:=cursor.get_parent()
        if not (parent is Node3D):
            fail("Technical Art Object motion node escaped receiver hierarchy")
            return Vector3.ZERO
        cursor=parent as Node3D
    return point

func _motion_vec3(values:Array)->Vector3:
    if values.size()!=3:
        fail("Technical Art Object motion pivot arity drift")
        return Vector3.ZERO
    return Vector3(float(values[0]),float(values[1]),float(values[2]))

func _motion_add_track(animation:Animation,root:Node3D,node:Node3D,samples:Array,key:String)->int:
    var track:=animation.add_track(Animation.TYPE_VALUE)
    animation.track_set_path(track,NodePath(str(root.get_path_to(node))+":rotation_degrees"))
    animation.track_set_interpolation_type(track,Animation.INTERPOLATION_NEAREST)
    animation.value_track_set_update_mode(track,Animation.UPDATE_DISCRETE)
    for row in samples:
        animation.track_insert_key(track,float(row["time_s"]),Vector3(float(row[key]),0.0,0.0))
    return track

func _motion_apply_sample(plan:Dictionary,index:int,lid:Node3D,pivots:Dictionary)->Dictionary:
    var samples=plan.get("samples",[]) as Array
    var row=samples[index] as Dictionary
    lid.rotation_degrees=Vector3(float(row["lid_target_rotation_deg_x"]),0.0,0.0)
    for sid in pivots.keys():
        var pivot=pivots[sid] as Node3D
        pivot.rotation_degrees=Vector3(float(row["latch_target_rotation_deg_x"]),0.0,0.0)
    var lid_error:=absf(lid.rotation_degrees.x-float(row["lid_target_rotation_deg_x"]))
    var latch_error:=0.0
    for sid in pivots.keys():
        var pivot=pivots[sid] as Node3D
        latch_error=maxf(latch_error,absf(pivot.rotation_degrees.x-float(row["latch_target_rotation_deg_x"])))
    if lid_error>EPS_DEG or latch_error>EPS_DEG:
        fail("Technical Art Object motion sampled target transform drift")
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
    if samples.size()!=101:
        fail("Technical Art Object motion sample count drift")
        return {}

    var lid:=_motion_find_node(container,"lid_shell")
    var keeper0:=_motion_find_node(container,"latch_0_keeper")
    var keeper1:=_motion_find_node(container,"latch_1_keeper")
    if lid==null or keeper0==null or keeper1==null:
        fail("Technical Art Object motion receiver hierarchy missing")
        return {}

    var stations=plan.get("stations",[]) as Array
    if stations.size()!=2:
        fail("Technical Art Object motion station count drift")
        return {}
    var pivots:Dictionary={}
    var levers:Dictionary={}
    var neutral_lever_centers:Dictionary={}
    for raw in stations:
        var station=raw as Dictionary
        var sid:=String(station.get("station_id",""))
        var lever_name:=String(station.get("lever_component",""))
        var lever:=_motion_find_node(container,lever_name)
        if lever==null:
            fail("Technical Art Object motion lever missing: "+lever_name)
            return {}
        neutral_lever_centers[lever_name]=_motion_receiver_local_mesh_center(container,lever)
        var old_container_transform:=lever.transform
        var pivot:=Node3D.new()
        pivot.name="technical_art_motion_pivot_"+sid
        pivot.position=_motion_vec3(station.get("pivot_receiver_xyz_m",[]) as Array)
        container.add_child(pivot)
        lever.reparent(pivot,false)
        lever.transform=pivot.transform.affine_inverse()*old_container_transform
        pivots[sid]=pivot
        levers[sid]=lever

    var neutral_pivot_drift:=0.0
    for sid in pivots.keys():
        var lever=levers[sid] as Node3D
        neutral_pivot_drift=maxf(neutral_pivot_drift,(neutral_lever_centers[String(lever.name)] as Vector3).distance_to(_motion_receiver_local_mesh_center(container,lever)))
    if neutral_pivot_drift>EPS_M:
        fail("Technical Art Object motion pivot insertion changed neutral geometry")
        return {}

    var animation:=Animation.new()
    animation.length=2.5
    animation.loop_mode=Animation.LOOP_NONE
    var lid_track:=_motion_add_track(animation,container,lid,samples,"lid_target_rotation_deg_x")
    var latch_tracks:Array=[]
    for sid in pivots.keys():
        latch_tracks.append(_motion_add_track(animation,container,pivots[sid] as Node3D,samples,"latch_target_rotation_deg_x"))
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

    var start_keeper0:=_motion_receiver_local_mesh_center(container,keeper0)
    var start_keeper1:=_motion_receiver_local_mesh_center(container,keeper1)
    var start_levers:Dictionary={}
    for sid in levers.keys():
        start_levers[sid]=_motion_receiver_local_mesh_center(container,levers[sid] as Node3D)
    var probes:Array=[]
    probes.append(_motion_apply_sample(plan,0,lid,pivots))
    probes.append(_motion_apply_sample(plan,10,lid,pivots))
    var release_keeper_drift:=maxf(start_keeper0.distance_to(_motion_receiver_local_mesh_center(container,keeper0)),start_keeper1.distance_to(_motion_receiver_local_mesh_center(container,keeper1)))
    var release_min_lever_move:=999.0
    for sid in levers.keys():
        release_min_lever_move=minf(release_min_lever_move,(start_levers[sid] as Vector3).distance_to(_motion_receiver_local_mesh_center(container,levers[sid] as Node3D)))
    if release_keeper_drift>EPS_M or release_min_lever_move<0.001:
        fail("Technical Art Object motion release sample does not preserve closed lid / move levers")
        return {}
    probes.append(_motion_apply_sample(plan,50,lid,pivots))
    var peak_min_keeper_move:=minf(start_keeper0.distance_to(_motion_receiver_local_mesh_center(container,keeper0)),start_keeper1.distance_to(_motion_receiver_local_mesh_center(container,keeper1)))
    if peak_min_keeper_move<0.03:
        fail("Technical Art Object motion peak sample did not move lid-owned keepers")
        return {}
    probes.append(_motion_apply_sample(plan,100,lid,pivots))
    var endpoint_keeper_drift:=maxf(start_keeper0.distance_to(_motion_receiver_local_mesh_center(container,keeper0)),start_keeper1.distance_to(_motion_receiver_local_mesh_center(container,keeper1)))
    var endpoint_lever_drift:=0.0
    for sid in levers.keys():
        endpoint_lever_drift=maxf(endpoint_lever_drift,(start_levers[sid] as Vector3).distance_to(_motion_receiver_local_mesh_center(container,levers[sid] as Node3D)))
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
    var selected_observation:=_motion_apply_sample(plan,selected,lid,pivots)
    result["environment_object_motion_receiver"]={
        "schema":"axm.environment-object-motion-current-world-observation/v0.1",
        "state":MOTION_STATE,
        "reusable_rule":MOTION_RULE,
        "animation_head":EXACT_ANIMATION_HEAD,
        "sequence_digest":EXACT_SEQUENCE_DIGEST,
        "track_count":3,
        "key_counts":[101,101,101],
        "neutral_pivot_wrapper_max_drift_m":neutral_pivot_drift,
        "release_keeper_drift_m":release_keeper_drift,
        "release_min_lever_move_m":release_min_lever_move,
        "peak_min_keeper_move_m":peak_min_keeper_move,
        "endpoint_keeper_drift_m":endpoint_keeper_drift,
        "endpoint_lever_drift_m":endpoint_lever_drift,
        "probe_samples":probes,
        "selected_sample":selected_observation,
        "sample_application_mode":"exact_owner_sample_receiver_local_transform_before_scene_attach",
        "vfx_adoption":false,
        "runtime_acceptance":false,
        "environment_adoption":false,
        "art_qa_acceptance":false,
        "canon":false,
        "truth_boundary":"Exact Object Animation owner samples are adapted onto the already-proven current-world rigid component receiver with the same target coordinate/sign convention as the pinned owner AnimationPlayer proof. The current-world proof applies selected discrete samples before scene attachment and retains a 3x101 AnimationPlayer representation, but does not claim wall-clock playback. Technical Art does not retime motion, infer mechanics, adopt VFX, claim Runtime/device performance, final visual acceptance, CANON or production readiness."
    }
    return result

func write_receipt()->void:
    receipt["technical_art_object_motion_current_world_state"]=MOTION_STATE
    receipt["technical_art_object_motion_current_world_rule"]=MOTION_RULE
    receipt["technical_art_object_motion_animation_head"]=EXACT_ANIMATION_HEAD
    receipt["technical_art_object_motion_sequence_digest"]=EXACT_SEQUENCE_DIGEST
    receipt["technical_art_object_motion_vfx_adoption"]=false
    receipt["technical_art_object_motion_runtime_acceptance"]=false
    receipt["technical_art_object_motion_environment_adoption"]=false
    receipt["technical_art_object_motion_art_qa_acceptance"]=false
    receipt["technical_art_object_motion_truth_boundary"]="Receiver-only discrete sampled-motion transport on the current-world Object rigid boundary. Animation owns timing/easing/order; Object/Rigging own hierarchy/pivots; Environment owns adoption; Runtime owns device/performance; Art/QA own appearance. Wall-clock playback is not claimed here."
    super.write_receipt()
