extends "res://atmosphere_current_world_compact_east_visual_response_observe.gd"

const ANIMATION_CONTRACT := "axm.animation-compact-east-current-world-discrete-playback/v0.1"
const PARENT_VFX_HEAD := "29ef2d4cc4398b3f26290e4e1f1f10398ca9898c"
const DURATION_S := 0.5
const INTERVALS := 16
const STEP_S := DURATION_S / INTERVALS
const UNIQUE_LOOP_PHASES := 16
const OUTPUT_PATH := "res://animation-compact-east-current-world-runtime.json"
const CONTEXT := "elevated_oblique"
const MOTION_TRUTH := "DISCRETE_EXACT_VFX_STATES_NOT_SMOOTH_INTERPOLATION"

func _source_for_phase(states:Array, phase:int)->Dictionary:
    var row := states[phase] as Dictionary
    return _compact(row.get("scene", {}) as Dictionary)

func _max_vertex_delta(a:Array,b:Array)->float:
    if a.size()!=b.size() or a.is_empty():
        return INF
    var out:=0.0
    for index in range(a.size()):
        out=max(out,gvec(a[index] as Array).distance_to(gvec(b[index] as Array)))
    return out

func _phase_mesh(source:Dictionary)->ArrayMesh:
    var proof:=source.get("nature_material_family_receiving",{}) as Dictionary
    var vertices:=source.get("vertices_source_xyz_m",[]) as Array
    var triangles:=source.get("triangles",[]) as Array
    if vertices.size()!=390 or triangles.size()!=570:
        fail("compact-east animation source topology count drift")
        return ArrayMesh.new()
    var mesh:=ArrayMesh.new()
    var total:=_commit_nature_surfaces(mesh,vertices,triangles,proof,false)
    if total!=570 or mesh.get_surface_count()!=2:
        fail("compact-east animation exact two-surface build failed")
        return ArrayMesh.new()
    return mesh

func _find_compact_child(root:Node3D,stats:Array)->MeshInstance3D:
    var stat_index:=-1
    for index in range(stats.size()):
        if String((stats[index] as Dictionary).get("asset_id",""))==COMPACT_EAST_ASSET_ID:
            if stat_index!=-1:
                fail("compact-east runtime stat count exceeded one")
                return null
            stat_index=index
    if stat_index==-1:
        fail("compact-east runtime stat missing")
        return null
    if root.get_child_count()==stats.size() and stat_index<root.get_child_count():
        var aligned:=root.get_child(stat_index)
        if aligned is MeshInstance3D:
            return aligned as MeshInstance3D
    for child in root.get_children():
        if child is MeshInstance3D:
            var name_text:=String(child.name)
            if name_text==COMPACT_EAST_ASSET_ID or name_text.contains("compact-east"):
                return child as MeshInstance3D
    fail("compact-east emitted MeshInstance3D could not be identified")
    return null

func _phase_for_mesh(mesh:Mesh,phase_meshes:Array)->int:
    for index in range(phase_meshes.size()):
        if mesh==phase_meshes[index]:
            return index
    return -1

func _make_player(root3d:Node3D,node:MeshInstance3D,phase_meshes:Array)->AnimationPlayer:
    node.name="compact-east-animation-receiver"
    var player:=AnimationPlayer.new()
    player.name="compact-east-animation-player"
    root3d.add_child(player)
    player.root_node=NodePath("..")
    var animation:=Animation.new()
    animation.length=DURATION_S
    animation.loop_mode=Animation.LOOP_LINEAR
    var track:=animation.add_track(Animation.TYPE_VALUE)
    animation.track_set_path(track,NodePath("compact-east-animation-receiver:mesh"))
    animation.track_set_interpolation_type(track,Animation.INTERPOLATION_NEAREST)
    animation.value_track_set_update_mode(track,Animation.UPDATE_DISCRETE)
    for phase in range(UNIQUE_LOOP_PHASES):
        animation.track_insert_key(track,float(phase)*STEP_S,phase_meshes[phase])
    var library:=AnimationLibrary.new()
    library.add_animation("compact_east_exact_states",animation)
    player.add_animation_library("",library)
    return player

func _capture(viewport:SubViewport,phase:int)->Dictionary:
    var result:=capture_mode(viewport,CONTEXT,phase,"animation")
    if result.get("state")!="PASS":
        fail("compact-east animation capture failed at phase %s" % phase)
        return {}
    return result

func _initialize()->void:
    receipt={
        "schema":ANIMATION_CONTRACT,
        "state":"STARTED",
        "parent_vfx_receiving_head":PARENT_VFX_HEAD,
        "nature_vfx_head":COMPACT_EAST_VFX_HEAD,
        "source_motion_truth":MOTION_TRUTH,
        "duration_s":DURATION_S,
        "intervals":INTERVALS,
        "authored_endpoint_inclusive_states":17,
        "loop_track_unique_states":UNIQUE_LOOP_PHASES,
        "source_step_s":STEP_S,
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "promotion_effect":"NONE"
    }
    var payload:=load_payload()
    if payload.is_empty():
        fail("compact-east Animation could not load exact VFX receiving payload")
        return
    var states:=payload.get("states",[]) as Array
    if states.size()!=17:
        fail("compact-east Animation requires exact 17-state source sequence")
        return
    if String(payload.get("environment_head",""))!=PARENT_VFX_HEAD:
        fail("compact-east current-world VFX receiving head drift")
        return
    if String(payload.get("compact_east_visual_response_vfx_head",""))!=COMPACT_EAST_VFX_HEAD:
        fail("compact-east source VFX identity drift")
        return

    var source0:=_source_for_phase(states,0)
    var source16:=_source_for_phase(states,16)
    var endpoint_delta:=_max_vertex_delta(
        source0.get("vertices_source_xyz_m",[]) as Array,
        source16.get("vertices_source_xyz_m",[]) as Array
    )
    if endpoint_delta>1e-12:
        fail("compact-east source endpoint seam is not exact")
        return
    var source15:=_source_for_phase(states,15)
    var authored_final_step:=_max_vertex_delta(
        source15.get("vertices_source_xyz_m",[]) as Array,
        source16.get("vertices_source_xyz_m",[]) as Array
    )
    var loop_step:=_max_vertex_delta(
        source15.get("vertices_source_xyz_m",[]) as Array,
        source0.get("vertices_source_xyz_m",[]) as Array
    )
    if abs(authored_final_step-loop_step)>1e-12:
        fail("compact-east loop seam adds motion beyond authored final step")
        return

    var mutated:=(source16.get("vertices_source_xyz_m",[]) as Array).duplicate(true)
    var first:=(mutated[0] as Array).duplicate()
    first[0]=float(first[0])+0.001
    mutated[0]=first
    var negative_delta:=_max_vertex_delta(source0.get("vertices_source_xyz_m",[]) as Array,mutated)
    if negative_delta<0.000999:
        fail("compact-east verifier-only endpoint mutation was not detected")
        return

    var first_row:=states[0] as Dictionary
    var data:=first_row.get("scene",{}) as Dictionary
    var viewport:=SubViewport.new()
    viewport.size=Vector2i(1100,720)
    viewport.own_world_3d=true
    viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
    viewport.render_target_clear_mode=SubViewport.CLEAR_MODE_ALWAYS
    get_root().add_child(viewport)
    var root3d:=Node3D.new()
    viewport.add_child(root3d)
    add_environment(root3d)
    for item in data.get("items",[]) as Array:
        add_proxy(root3d,item as Dictionary)
    add_path(root3d,data)

    var culling_review:=data.get("environment_rear_tree_culling_review",{}) as Dictionary
    var cull_target_asset_id:=String(culling_review.get("target_asset_id",""))
    if cull_target_asset_id!=VARIANT_TARGET_REAR_ASSET_ID:
        fail("compact-east Animation rear-tree culling identity drift")
        return
    var static_root:=Node3D.new()
    static_root.name="animation-static-source-root"
    root3d.add_child(static_root)
    var static_stats:=add_static_sources(static_root,data,cull_target_asset_id)
    var dynamic_node:=_find_compact_child(static_root,static_stats)
    if dynamic_node==null:
        return

    var phase_meshes:Array=[]
    var phase_mesh_digests:Array=[]
    for phase in range(UNIQUE_LOOP_PHASES):
        var source:=_source_for_phase(states,phase)
        phase_meshes.append(_phase_mesh(source))
        phase_mesh_digests.append(String(source.get("mesh_digest","")))
        if receipt.get("state")=="FAIL":
            return
    dynamic_node.mesh=phase_meshes[0]

    make_weather()
    weather_material.cull_mode=BaseMaterial3D.CULL_DISABLED
    root3d.add_child(weather_node)
    make_sapling()
    root3d.add_child(sapling_node)
    var sapling_update:=fill_sapling(data.get("sapling",{}) as Dictionary)
    if sapling_update.is_empty():
        fail("compact-east Animation could not freeze west-sapling source phase 00")
        return

    var camera:=Camera3D.new()
    camera.near=0.05
    camera.far=120.0
    root3d.add_child(camera)
    camera.make_current()
    configure_camera(camera,data,CONTEXT)
    var weather_update:=fill_weather_width_ribbons(data.get("weather_lines",[]) as Array,camera)
    if weather_update.get("state")!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
        fail("compact-east Animation could not freeze exact Weather source-width state 00")
        return
    await settle()

    var player:=_make_player(root3d,dynamic_node,phase_meshes)
    var player_id:=player.get_instance_id()
    var node_id:=dynamic_node.get_instance_id()
    var deterministic:Array=[]
    for phase in range(UNIQUE_LOOP_PHASES):
        player.seek(float(phase)*STEP_S,true)
        var observed:=_phase_for_mesh(dynamic_node.mesh,phase_meshes)
        if observed!=phase:
            fail("compact-east AnimationPlayer exact-key resource mismatch at phase %s -> %s" % [phase,observed])
            return
        deterministic.append({"phase":phase,"time_s":float(phase)*STEP_S,"mesh_instance_id":dynamic_node.mesh.get_instance_id(),"source_mesh_digest":phase_mesh_digests[phase]})

    player.seek(0.0,true)
    await settle()
    var captures:Array=[]
    captures.append(_capture(viewport,0))
    player.seek(8.0*STEP_S,true)
    await settle()
    captures.append(_capture(viewport,8))
    player.seek(15.0*STEP_S,true)
    await settle()
    captures.append(_capture(viewport,15))
    if captures.any(func(v): return (v as Dictionary).is_empty()):
        return

    player.seek(0.0,true)
    player.play("compact_east_exact_states")
    var completed_cycles:Array=[]
    var current_cycle:Array=[0]
    var previous_phase:=0
    var process_frames:=0
    var playback_start_usec:=Time.get_ticks_usec()
    var wrap_times_s:Array=[]
    var safety_frames:=0
    while completed_cycles.size()<3 and safety_frames<12000:
        await process_frame
        safety_frames+=1
        process_frames+=1
        if player.get_instance_id()!=player_id or dynamic_node.get_instance_id()!=node_id:
            fail("compact-east Animation playback receiver identity changed")
            return
        var active_phase:=_phase_for_mesh(dynamic_node.mesh,phase_meshes)
        if active_phase<0:
            fail("compact-east Animation playback produced an unknown mesh resource")
            return
        if active_phase<previous_phase:
            completed_cycles.append(current_cycle.duplicate())
            wrap_times_s.append(float(Time.get_ticks_usec()-playback_start_usec)/1000000.0)
            current_cycle=[active_phase]
        elif not current_cycle.has(active_phase):
            current_cycle.append(active_phase)
        previous_phase=active_phase
    player.stop()
    if completed_cycles.size()!=3:
        fail("compact-east Animation real playback did not cross three loop seams")
        return
    for cycle_index in range(completed_cycles.size()):
        var phases:=completed_cycles[cycle_index] as Array
        if phases.size()!=16:
            fail("compact-east Animation real playback missed exact states in cycle %s: %s" % [cycle_index,phases])
            return
        for phase in range(16):
            if not phases.has(phase):
                fail("compact-east Animation real playback missing phase %s in cycle %s" % [phase,cycle_index])
                return

    var cycle_durations:Array=[]
    var prior:=0.0
    for wrap_time in wrap_times_s:
        cycle_durations.append(float(wrap_time)-prior)
        prior=float(wrap_time)

    receipt.update({
        "state":"PASS_COMPACT_EAST_CURRENT_WORLD_EXACT_STATE_ANIMATIONPLAYER_PLAYBACK_AND_LOOP",
        "receiver_context":CONTEXT,
        "animation_track_interpolation":"NEAREST",
        "animation_update_mode":"DISCRETE",
        "animation_loop_mode":"LOOP_LINEAR",
        "deterministic_exact_key_checks":deterministic,
        "deterministic_exact_key_count":deterministic.size(),
        "source_endpoint_geometry_delta_m":endpoint_delta,
        "authored_final_step_m":authored_final_step,
        "loop_step_m":loop_step,
        "loop_step_residual_m":abs(authored_final_step-loop_step),
        "negative_control_endpoint_mutation_m":negative_delta,
        "negative_control_result":"REJECTED_AS_REQUIRED",
        "real_playback_wraps":completed_cycles.size(),
        "real_playback_process_frames":process_frames,
        "real_playback_cycles_observed_phases":completed_cycles,
        "real_playback_wrap_times_s":wrap_times_s,
        "real_playback_cycle_durations_s":cycle_durations,
        "persistent_receiver_instance_id":node_id,
        "persistent_animation_player_instance_id":player_id,
        "frozen_weather_phase":0,
        "frozen_west_sapling_phase":0,
        "captures":captures,
        "truth_boundary":"Exact current-world AnimationPlayer playback witness for the already-authored compact-east 17-state VFX response. The looping track uses the 16 unique source states at the exact 31.25 ms source cadence and omits only the duplicate phase-16 neutral endpoint, whose geometry equality and seam step are checked separately. This proves discrete exact-state playback and repeated loop continuity in the accepted current-world proof receiver; it does not establish smooth interpolation, physical wind, final motion naturalness, Runtime controller/state-machine policy, target-device delivery, collision/gameplay, Art/QA acceptance, CANON or production readiness."
    })
    write_receipt()
    quit(0)

func write_receipt()->void:
    var file:=FileAccess.open(OUTPUT_PATH,FileAccess.WRITE)
    if file:
        file.store_string(JSON.stringify(receipt,"  ")+"\n")
