extends "res://animation_object_current_world_wallclock_observe.gd"

const VFX_RECEIPT_PATH := "res://vfx-object-release-motes-current-world-runtime.json"
const VFX_EFFECT_PATH := "res://generated/object-vfx-lid-release-motes-v2.json"
const EXACT_ANIMATION_PARENT_HEAD := "c2695f654f9dd44312ca5d205eceb27f7c2680ee"
const EXACT_OBJECT_VFX_HEAD := "bc114ee7ec876107892ccedeefc8e5020315488a"
const EXACT_OBJECT_SOURCE_SHA256 := "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
const EXACT_OWNER_SEED := 41027
const EXACT_MOTE_COUNT := 18
const PIXEL_THRESHOLD := 1.0 / 255.0

class VfxFrameDriver:
    extends Node
    var player:AnimationPlayer
    var particles:Array=[]
    var effect:Dictionary={}
    var update_callable:Callable
    var active_count:int=0
    var maximum_active_count:int=0
    var pre_trigger_inactive_seen:bool=false
    var active_window_seen:bool=false
    var post_effect_inactive_seen:bool=false

    func _process(_delta:float)->void:
        if player==null or not update_callable.is_valid():
            active_count=0
            return
        var position_s:=player.current_animation_position
        active_count=int(update_callable.call(particles,effect,position_s,true))
        maximum_active_count=maxi(maximum_active_count,active_count)
        if position_s<0.24 and active_count==0:
            pre_trigger_inactive_seen=true
        if position_s>=0.25 and position_s<=0.79 and active_count>0:
            active_window_seen=true
        if position_s>=0.80 and active_count==0:
            post_effect_inactive_seen=true

var vfx_receipt:Dictionary={}

func _vfx_write_receipt()->void:
    var file:=FileAccess.open(VFX_RECEIPT_PATH,FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(vfx_receipt,"  ")+"\n")
        file.close()

func _vfx_fail(message:String)->void:
    vfx_receipt["state"]="FAIL_CURRENT_WORLD_OBJECT_VFX_V2_RECEIVING_EVIDENCE"
    vfx_receipt["error"]=message
    _vfx_write_receipt()
    push_error(message)
    quit(1)

func _vfx_read_json(path:String)->Dictionary:
    if not FileAccess.file_exists(path):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(path))
    return parsed as Dictionary if parsed is Dictionary else {}

func _vfx_validate_effect(effect:Dictionary)->String:
    if String(effect.get("schema",""))!="axm.object-reactive-vfx/v0.1":
        return "unexpected VFX schema"
    if String(effect.get("effect_id",""))!="lid-open-release-motes-001-irregularity-repair-candidate-v2":
        return "unexpected VFX successor identity"
    if String(effect.get("asset_id",""))!="modular-equipment-case-001":
        return "unexpected VFX asset identity"
    if String(effect.get("source_sha256",""))!=EXACT_OBJECT_SOURCE_SHA256:
        return "Object source identity drift"
    var dep:=effect.get("animation_dependency",{}) as Dictionary
    if String(dep.get("sequence_id",""))!="lid-latch-open-hold-close-001":
        return "Animation sequence identity drift"
    if absf(float(dep.get("trigger_time_s",-1.0))-0.25)>0.000001:
        return "VFX trigger time drift"
    if String(dep.get("trigger_phase_id",""))!="play_exact_lid_clip":
        return "VFX trigger phase drift"
    if String(dep.get("trigger_semantics",""))!="EXACT_ANIMATION_PHASE_BOUNDARY_NOT_GAMEPLAY_EVENT":
        return "VFX trigger semantics promoted beyond visual phase binding"
    var visual:=effect.get("visual_source",{}) as Dictionary
    if int(visual.get("seed",-1))!=EXACT_OWNER_SEED or int(visual.get("particle_count",0))!=EXACT_MOTE_COUNT:
        return "owner seed or mote count drift"
    if String(visual.get("source_label",""))!="STYLIZED_VISUAL_RELEASE_MOTES_NOT_DUST_OR_FLUID_SIMULATION":
        return "VFX source semantics drift"
    if String(visual.get("parameter_sampling",""))!="DECORRELATED_INTEGER_MIX_V2_IRREGULAR_MARKS":
        return "V2 irregularity sampler identity drift"
    var modulation:=visual.get("repair_modulation",{}) as Dictionary
    if modulation.is_empty():
        return "V2 repair modulation missing"
    if float(modulation.get("billboard_aspect_max",2.0))>1.0 or float(modulation.get("alpha_scale_max",2.0))>1.0:
        return "V2 modulation exceeds owner size/alpha ceilings"
    if float(modulation.get("vertical_spawn_jitter_abs_max_m",1.0))>0.012001 or float(modulation.get("curve_abs_max_m",1.0))>0.010001:
        return "V2 irregularity envelope drift"
    return ""

func _hash01(seed:int,index:int,salt:int)->float:
    var value:int=(seed*1664525+(index+1)*1013904223+(salt+1)*374761393)&0x7fffffff
    value=((value^(value>>13))*1274126177)&0x7fffffff
    value=value^(value>>16)
    return float(value&0x7fffffff)/2147483647.0

func _receiver_local_mesh_bounds(container:Node3D,node:Node3D)->Dictionary:
    if not (node is MeshInstance3D):
        return {}
    var instance:=node as MeshInstance3D
    if instance.mesh==null:
        return {}
    var aabb:=instance.mesh.get_aabb()
    var minp:=Vector3(INF,INF,INF)
    var maxp:=Vector3(-INF,-INF,-INF)
    for ix in [0,1]:
        for iy in [0,1]:
            for iz in [0,1]:
                var point:=aabb.position+Vector3(aabb.size.x*ix,aabb.size.y*iy,aabb.size.z*iz)
                var cursor:Node3D=node
                while cursor!=container:
                    point=cursor.transform*point
                    var parent:=cursor.get_parent()
                    if not (parent is Node3D):
                        return {}
                    cursor=parent as Node3D
                minp.x=minf(minp.x,point.x)
                minp.y=minf(minp.y,point.y)
                minp.z=minf(minp.z,point.z)
                maxp.x=maxf(maxp.x,point.x)
                maxp.y=maxf(maxp.y,point.y)
                maxp.z=maxf(maxp.z,point.z)
    return {"min":minp,"max":maxp}

func _make_particles(effect:Dictionary,seam_min:Vector3,seam_max:Vector3,root:Node3D)->Array:
    var visual:=effect["visual_source"] as Dictionary
    var modulation:=visual["repair_modulation"] as Dictionary
    var seed:=int(visual["seed"])
    var count:=int(visual["particle_count"])
    var rgb:=visual["color_srgb"] as Array
    var base_color:=Color(float(rgb[0]),float(rgb[1]),float(rgb[2]),float(visual["alpha_peak"]))
    var particles:Array=[]
    for i in range(count):
        var start_x:=lerpf(seam_min.x,seam_max.x,_hash01(seed,i,1))
        var start_z:=lerpf(seam_min.z,seam_max.z,_hash01(seed,i,2))
        var spawn:=float(effect["animation_dependency"]["trigger_time_s"])+float(visual["emission_span_s"])*_hash01(seed,i,3)
        var lifetime:=lerpf(float(visual["lifetime_min_s"]),float(visual["lifetime_max_s"]),_hash01(seed,i,4))
        var size:=lerpf(float(visual["size_min_m"]),float(visual["size_max_m"]),_hash01(seed,i,5))
        var vx:=lerpf(-float(visual["lateral_speed_abs_max_mps"]),float(visual["lateral_speed_abs_max_mps"]),_hash01(seed,i,6))
        var vy:=lerpf(float(visual["vertical_speed_min_mps"]),float(visual["vertical_speed_max_mps"]),_hash01(seed,i,7))
        var vz:=-lerpf(float(visual["camera_forward_speed_min_mps"]),float(visual["camera_forward_speed_max_mps"]),_hash01(seed,i,8))
        var aspect:=lerpf(float(modulation["billboard_aspect_min"]),float(modulation["billboard_aspect_max"]),_hash01(seed,i,9))
        var alpha_scale:=lerpf(float(modulation["alpha_scale_min"]),float(modulation["alpha_scale_max"]),_hash01(seed,i,10))
        var y_jitter:=lerpf(-float(modulation["vertical_spawn_jitter_abs_max_m"]),float(modulation["vertical_spawn_jitter_abs_max_m"]),_hash01(seed,i,11))
        var curve_amp:=lerpf(-float(modulation["curve_abs_max_m"]),float(modulation["curve_abs_max_m"]),_hash01(seed,i,12))
        var curve_phase:=TAU*_hash01(seed,i,13)
        var quad:=QuadMesh.new()
        quad.size=Vector2(size,size*aspect)
        var material:=StandardMaterial3D.new()
        material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
        material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
        material.billboard_mode=BaseMaterial3D.BILLBOARD_ENABLED
        material.albedo_color=Color(base_color.r,base_color.g,base_color.b,0.0)
        quad.material=material
        var mote:=MeshInstance3D.new()
        mote.name="current_world_release_mote_%02d"%i
        mote.mesh=quad
        mote.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
        mote.visible=false
        root.add_child(mote)
        particles.append({
            "node":mote,
            "material":material,
            "start":Vector3(start_x,seam_min.y+y_jitter,start_z),
            "spawn":spawn,
            "lifetime":lifetime,
            "velocity":Vector3(vx,vy,vz),
            "base_color":base_color,
            "alpha_scale":alpha_scale,
            "curve_amp":curve_amp,
            "curve_phase":curve_phase
        })
    return particles

func _set_particle_state(particles:Array,effect:Dictionary,time_s:float,enabled:bool)->int:
    var visual:=effect["visual_source"] as Dictionary
    var modulation:=visual["repair_modulation"] as Dictionary
    var gravity:=float(visual["gravity_visual_mps2"])
    var active:=0
    for particle in particles:
        var mote:=particle["node"] as MeshInstance3D
        var material:=particle["material"] as StandardMaterial3D
        var age:=time_s-float(particle["spawn"])
        var lifetime:=float(particle["lifetime"])
        if not enabled or age<0.0 or age>lifetime:
            mote.visible=false
            material.albedo_color.a=0.0
            continue
        active+=1
        var u:=clampf(age/lifetime,0.0,1.0)
        var start:=particle["start"] as Vector3
        var velocity:=particle["velocity"] as Vector3
        mote.position=start+velocity*age+Vector3(0.0,0.5*gravity*age*age,0.0)
        var curve_window:=sin(PI*u)
        var curve_phase:=float(particle["curve_phase"])
        var curve_amp:=float(particle["curve_amp"])*curve_window
        mote.position+=Vector3(sin(PI*u+curve_phase)*curve_amp,cos(PI*u+curve_phase)*curve_amp*float(modulation["curve_vertical_ratio"]),0.0)
        var c:=particle["base_color"] as Color
        var alpha:=c.a*float(particle["alpha_scale"])*pow(maxf(0.0,sin(PI*u)),0.75)
        material.albedo_color=Color(c.r,c.g,c.b,alpha)
        mote.visible=alpha>0.005
    return active

func _diff_metrics(a:Image,b:Image)->Dictionary:
    if a.get_width()!=b.get_width() or a.get_height()!=b.get_height():
        return {"changed_pixels":-1}
    var changed:=0
    var minx:=a.get_width()
    var miny:=a.get_height()
    var maxx:=-1
    var maxy:=-1
    var max_delta:=0.0
    for y in range(a.get_height()):
        for x in range(a.get_width()):
            var p:=a.get_pixel(x,y)
            var q:=b.get_pixel(x,y)
            var delta:=maxf(absf(p.r-q.r),maxf(absf(p.g-q.g),absf(p.b-q.b)))
            max_delta=maxf(max_delta,delta)
            if delta>PIXEL_THRESHOLD:
                changed+=1
                minx=mini(minx,x)
                miny=mini(miny,y)
                maxx=maxi(maxx,x)
                maxy=maxi(maxy,y)
    var bbox:Array=[]
    if changed>0:
        bbox=[minx,miny,maxx+1,maxy+1]
    return {"changed_pixels":changed,"changed_fraction":float(changed)/float(a.get_width()*a.get_height()),"max_rgb_delta":max_delta,"bbox_half_open":bbox}

func _static_ab(world:Dictionary,effect:Dictionary,particles:Array,data:Dictionary,context_id:String,time_s:float)->Dictionary:
    var viewport:=world["viewport"] as SubViewport
    var camera:=world["camera"] as Camera3D
    var player:=world["player"] as AnimationPlayer
    var lid:=world["lid"] as Node3D
    configure_camera(camera,data,context_id)
    var weather_update:=fill_weather_width_ribbons(data.get("weather_lines",[]) as Array,camera)
    if String(weather_update.get("state",""))!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
        _vfx_fail("Weather width re-projection failed for VFX review context "+context_id)
        return {}
    await settle()
    player.stop()
    player.play("owner_samples")
    player.pause()
    player.seek(time_s,true)
    player.advance(0.0)
    _set_particle_state(particles,effect,time_s,false)
    for _i in range(3):
        await process_frame
        await RenderingServer.frame_post_draw
    var lid_control:=lid.rotation_degrees
    var control:=viewport.get_texture().get_image()
    if control==null or control.is_empty():
        _vfx_fail("Current-world VFX control raster unavailable")
        return {}
    var tag:="%s-%04dms"%[context_id,int(round(time_s*1000.0))]
    var control_path:="res://vfx-current-world-%s-control.png"%tag
    if control.save_png(control_path)!=OK:
        _vfx_fail("Could not save current-world VFX control raster")
        return {}
    var active_count:=_set_particle_state(particles,effect,time_s,true)
    for _j in range(3):
        await process_frame
        await RenderingServer.frame_post_draw
    if lid_control.distance_to(lid.rotation_degrees)>0.00001:
        _vfx_fail("VFX changed Object Animation state during current-world A/B")
        return {}
    var candidate:=viewport.get_texture().get_image()
    if candidate==null or candidate.is_empty():
        _vfx_fail("Current-world VFX candidate raster unavailable")
        return {}
    var candidate_path:="res://vfx-current-world-%s-candidate.png"%tag
    if candidate.save_png(candidate_path)!=OK:
        _vfx_fail("Could not save current-world VFX candidate raster")
        return {}
    return {
        "context_id":context_id,
        "time_s":time_s,
        "active_particle_count":active_count,
        "control_path":control_path.trim_prefix("res://"),
        "candidate_path":candidate_path.trim_prefix("res://"),
        "diff":_diff_metrics(control,candidate)
    }

func _initialize()->void:
    vfx_receipt={
        "schema":"axm.vfx-object-current-world-receiving-evidence/v0.1",
        "state":"STARTED",
        "animation_parent_head":EXACT_ANIMATION_PARENT_HEAD,
        "object_vfx_head":EXACT_OBJECT_VFX_HEAD,
        "owner_seed":EXACT_OWNER_SEED,
        "promotion_effect":"NONE",
        "vfx_owner_replaced":false,
        "animation_timing_or_easing_modified":false,
        "weather_semantics_modified":false,
        "world_composition_modified":false,
        "gameplay_event_semantics_claimed":false,
        "physics_accepted":false,
        "gameplay_accepted":false,
        "runtime_performance_accepted":false,
        "art_direction_accepted":false,
        "visual_qa_accepted":false,
        "canon":false,
        "production_ready":false
    }
    var effect:=_vfx_read_json(VFX_EFFECT_PATH)
    if effect.is_empty():
        _vfx_fail("Exact Object VFX v2 source missing")
        return
    var contract_error:=_vfx_validate_effect(effect)
    if not contract_error.is_empty():
        _vfx_fail(contract_error)
        return

    animation_receipt={"schema":"axm.animation-object-current-world-wallclock-observation/v0.1","state":"VFX_CHILD_BUILDING_PARENT_RECEIVER"}
    var world:=await _build_current_world()
    if world.is_empty():
        return
    var container:=world["container"] as Node3D
    var lid:=world["lid"] as Node3D
    var bounds:=_receiver_local_mesh_bounds(container,lid)
    if bounds.is_empty():
        _vfx_fail("Could not derive receiver-local lid bounds")
        return
    var bmin:=bounds["min"] as Vector3
    var bmax:=bounds["max"] as Vector3
    var seam_min:=Vector3(bmin.x+0.07,bmin.y+0.012,bmin.z-0.008)
    var seam_max:=Vector3(bmax.x-0.07,bmin.y+0.012,bmin.z+0.018)
    var effect_root:=Node3D.new()
    effect_root.name="AXM_CURRENT_WORLD_OBJECT_RELEASE_MOTES_V2"
    container.add_child(effect_root)
    var particles:=_make_particles(effect,seam_min,seam_max,effect_root)
    if particles.size()!=EXACT_MOTE_COUNT:
        _vfx_fail("Current-world VFX particle construction count drift")
        return

    var driver:=VfxFrameDriver.new()
    driver.name="AXM_CURRENT_WORLD_OBJECT_VFX_DRIVER"
    driver.player=world["player"] as AnimationPlayer
    driver.particles=particles
    driver.effect=effect
    driver.update_callable=Callable(self,"_set_particle_state")
    driver.process_priority=100
    container.add_child(driver)

    var timed:=await _timed_playback(world)
    if timed.is_empty():
        return
    if not driver.pre_trigger_inactive_seen or not driver.active_window_seen or not driver.post_effect_inactive_seen:
        _vfx_fail("Current-world real playback did not observe pre/active/post VFX states")
        return
    if driver.maximum_active_count!=EXACT_MOTE_COUNT:
        _vfx_fail("Current-world real playback did not reach all owner motes")
        return
    driver.set_process(false)
    _set_particle_state(particles,effect,0.0,false)

    var payload:=load_payload()
    if payload.is_empty():
        _vfx_fail("Current-world payload unavailable for VFX A/B")
        return
    var states:=payload.get("states",[]) as Array
    if states.is_empty():
        _vfx_fail("Current-world VFX A/B has no source state")
        return
    var data:=((states[0] as Dictionary).get("scene",{}) as Dictionary)
    var checks:Array=[]
    var observed_contexts:Dictionary={}
    for context_id in ["path_eye","elevated_oblique"]:
        for time_s in [0.20,0.30,0.40,0.52,0.80]:
            var check:=await _static_ab(world,effect,particles,data,context_id,time_s)
            if check.is_empty():
                return
            var changed:=int((check["diff"] as Dictionary)["changed_pixels"])
            var fraction:=float((check["diff"] as Dictionary)["changed_fraction"])
            var active:=int(check["active_particle_count"])
            if time_s==0.20 or time_s==0.80:
                if active!=0 or changed!=0:
                    _vfx_fail("Current-world VFX inactive closure failed for "+context_id)
                    return
            else:
                if fraction>0.08:
                    _vfx_fail("Current-world VFX active raster escaped bounded 8% review envelope")
                    return
                if time_s==0.40 and active!=EXACT_MOTE_COUNT:
                    _vfx_fail("Current-world VFX 0.40 s owner-count drift")
                    return
                if changed>0:
                    observed_contexts[context_id]=true
            checks.append(check)

    var observed:Array=observed_contexts.keys()
    observed.sort()
    var decision:="HOLD_V2_NOT_OBSERVABLE_IN_EXISTING_CURRENT_WORLD_CAMERAS__DO_NOT_AMPLIFY_AUTOMATICALLY"
    if not observed.is_empty():
        decision="PASS_V2_VISUALLY_OBSERVABLE_IN_EXISTING_CURRENT_WORLD_CONTEXT__HOLD_ART_QA_RUNTIME_AND_ADOPTION"

    vfx_receipt["state"]="PASS_CURRENT_WORLD_OBJECT_VFX_V2_RECEIVING_EVIDENCE"
    vfx_receipt["decision"]=decision
    vfx_receipt["effect_id"]=effect.get("effect_id")
    vfx_receipt["effect_source_sha256"]=effect.get("source_sha256")
    vfx_receipt["trigger_time_s"]=(effect["animation_dependency"] as Dictionary).get("trigger_time_s")
    vfx_receipt["trigger_semantics"]=(effect["animation_dependency"] as Dictionary).get("trigger_semantics")
    vfx_receipt["effect_source_label"]=(effect["visual_source"] as Dictionary).get("source_label")
    vfx_receipt["parameter_sampling"]=(effect["visual_source"] as Dictionary).get("parameter_sampling")
    vfx_receipt["repair_modulation"]=(effect["visual_source"] as Dictionary).get("repair_modulation")
    vfx_receipt["derived_receiver_local_emitter_seam"]={"min":[seam_min.x,seam_min.y,seam_min.z],"max":[seam_max.x,seam_max.y,seam_max.z]}
    vfx_receipt["timed_playback"]={
        "natural_stop":timed.get("natural_stop"),
        "elapsed_s":timed.get("elapsed_s"),
        "process_frame_count":timed.get("process_frame_count"),
        "observed_owner_sample_count":timed.get("observed_owner_sample_count"),
        "max_owner_sample_error_deg":timed.get("max_owner_sample_error_deg"),
        "endpoint_keeper_drift_m":timed.get("endpoint_keeper_drift_m"),
        "endpoint_lever_drift_m":timed.get("endpoint_lever_drift_m"),
        "vfx_pre_trigger_inactive_seen":driver.pre_trigger_inactive_seen,
        "vfx_active_window_seen":driver.active_window_seen,
        "vfx_post_effect_inactive_seen":driver.post_effect_inactive_seen,
        "vfx_maximum_active_count":driver.maximum_active_count,
        "timing_is_target_device_performance_evidence":false
    }
    vfx_receipt["static_ab_checks"]=checks
    vfx_receipt["visually_observing_existing_camera_contexts"]=observed
    vfx_receipt["visual_truth_boundary"]="Existing current-world cameras may prove observability/non-observability of the unchanged V2 cue. A visible delta is review evidence only; a zero delta is a HOLD and must not trigger automatic brightening, enlargement, densification, camera movement or Animation retiming."
    vfx_receipt["truth_boundary"]="The exact Object VFX irregularity-v2 candidate is transported unchanged into the exact Map PR46 current-world Object Animation receiver and driven from the same real AnimationPlayer phase. This evidence may establish phase-bound renderability, inactive closure and existing-camera observability only. It does not adopt V2, replace owner seed 41027, prove physical dust/airflow/pressure, gameplay/collision/damage, Runtime or target-device performance, Art Direction/Visual QA acceptance, CANON or production readiness."
    _vfx_write_receipt()
    print("AXM CURRENT WORLD OBJECT VFX V2 ",JSON.stringify(vfx_receipt))
    quit(0)
