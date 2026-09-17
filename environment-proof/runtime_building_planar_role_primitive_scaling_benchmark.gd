extends SceneTree

const ACTIVE_PATH := "res://generated/runtime-building-active.json"
const CANDIDATE_PATH := "res://generated/runtime-building-planar.json"
const OUTPUT_PATH := "res://runtime-building-planar-role-primitive-scaling.json"
const SCHEMA := "axm.runtime-building-planar-role-primitive-scaling/v0.1"
const BUILDING_ID := "source:building:service-pavilion-001"
const ROLES := ["frame_galvanized","infill_coating","roof_membrane","slab_mineral","utility_panel_ochre"]
const INSTANCE_COUNTS := [1,16,64,256]
const MAX_INSTANCES := 256
const WARMUP_PAIRS := 5
const TRIALS := 41
const FRAMES_PER_SAMPLE := 3

func fail(message:String)->void:
    push_error(message)
    var f:=FileAccess.open(OUTPUT_PATH,FileAccess.WRITE)
    if f!=null:
        f.store_string(JSON.stringify({"schema":SCHEMA,"state":"FAIL_INFRASTRUCTURE","failure":message,"godot_version":Engine.get_version_info()},"  ")+"\n")
        f.close()
    quit(1)

func load_json(path:String)->Dictionary:
    if not FileAccess.file_exists(path):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(path))
    return parsed as Dictionary if parsed is Dictionary else {}

func gvec(values:Array)->Vector3:
    return Vector3(float(values[0]),float(values[2]),-float(values[1]))

func building_material(row:Dictionary)->StandardMaterial3D:
    var payload=row.get("material",{}) as Dictionary
    var albedo=payload.get("albedo",[]) as Array
    if albedo.size()!=4:
        return StandardMaterial3D.new()
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(float(albedo[0]),float(albedo[1]),float(albedo[2]),float(albedo[3]))
    material.metallic=float(payload.get("metallic",0.0))
    material.roughness=float(payload.get("roughness",1.0))
    material.cull_mode=BaseMaterial3D.CULL_DISABLED
    return material

func building_proof(payload:Dictionary)->Dictionary:
    var states=payload.get("states",[]) as Array
    if states.size()!=17:
        return {}
    var scene=(states[0] as Dictionary).get("scene",{}) as Dictionary
    var proof=scene.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!=BUILDING_ID:
        return {}
    return proof

func mesh_diag(mesh:ArrayMesh)->Dictionary:
    var vertices:=0
    var indices:=0
    var primitives:=0
    var surfaces:Array=[]
    for surface_index in range(mesh.get_surface_count()):
        var vc:=mesh.surface_get_array_len(surface_index)
        var ic:=mesh.surface_get_array_index_len(surface_index)
        var pc:=ic/3 if ic>0 else vc/3
        vertices+=vc
        indices+=ic
        primitives+=pc
        surfaces.append({"surface_index":surface_index,"vertices":vc,"indices":ic,"primitives":pc})
    return {"surface_count":mesh.get_surface_count(),"vertices":vertices,"indices":indices,"primitives":primitives,"surfaces":surfaces}

func build_receiver_mesh(proof:Dictionary,index_after_normals:bool)->ArrayMesh:
    var vertices=proof.get("vertices_source_xyz_m",[]) as Array
    var surfaces=proof.get("surfaces",[]) as Array
    if surfaces.size()!=5:
        return ArrayMesh.new()
    var unindexed:=ArrayMesh.new()
    var roles:Array=[]
    for surface_value in surfaces:
        var surface=surface_value as Dictionary
        var role:=String(surface.get("surface_role",""))
        if role!=String(surface.get("material_id","")):
            return ArrayMesh.new()
        roles.append(role)
        var triangles=surface.get("triangles",[]) as Array
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for tri_value in triangles:
            var tri=tri_value as Array
            if tri.size()!=3:
                return ArrayMesh.new()
            for raw_index in tri:
                var index:=int(raw_index)
                if index<0 or index>=vertices.size():
                    return ArrayMesh.new()
                st.add_vertex(gvec(vertices[index] as Array))
        st.generate_normals()
        st.commit(unindexed)
        unindexed.surface_set_material(unindexed.get_surface_count()-1,building_material(surface))
    if roles!=ROLES:
        return ArrayMesh.new()
    if not index_after_normals:
        return unindexed
    var indexed:=ArrayMesh.new()
    for surface_index in range(unindexed.get_surface_count()):
        var st:=SurfaceTool.new()
        st.create_from(unindexed,surface_index)
        st.index()
        st.commit(indexed)
        indexed.surface_set_material(indexed.get_surface_count()-1,unindexed.surface_get_material(surface_index))
    return indexed

func make_multimesh(mesh:ArrayMesh)->MultiMeshInstance3D:
    var multimesh:=MultiMesh.new()
    multimesh.transform_format=MultiMesh.TRANSFORM_3D
    multimesh.mesh=mesh
    multimesh.instance_count=MAX_INSTANCES
    multimesh.visible_instance_count=0
    var side:=16
    for index in range(MAX_INSTANCES):
        var col:=index%side
        var row:=int(index/side)
        var origin:=Vector3((float(col)-7.5)*0.76,(float(row)-7.5)*0.35,0.0)
        var basis:=Basis().scaled(Vector3(0.08,0.08,0.08))
        multimesh.set_instance_transform(index,Transform3D(basis,origin))
    var node:=MultiMeshInstance3D.new()
    node.multimesh=multimesh
    return node

func runtime_stats()->Dictionary:
    return {"objects_in_frame":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),"primitives_in_frame":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),"draw_calls_in_frame":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),"texture_mem_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED),"buffer_mem_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_BUFFER_MEM_USED)}

func present(control:MultiMeshInstance3D,candidate:MultiMeshInstance3D,use_candidate:bool,count:int)->void:
    control.multimesh.visible_instance_count=count
    candidate.multimesh.visible_instance_count=count
    control.visible=not use_candidate
    candidate.visible=use_candidate
    await RenderingServer.frame_post_draw
    await RenderingServer.frame_post_draw

func measure_frame_delivery(control:MultiMeshInstance3D,candidate:MultiMeshInstance3D,use_candidate:bool,count:int)->float:
    await present(control,candidate,use_candidate,count)
    var started:=Time.get_ticks_usec()
    for _frame in range(FRAMES_PER_SAMPLE):
        await RenderingServer.frame_post_draw
    return float(Time.get_ticks_usec()-started)/1000.0/float(FRAMES_PER_SAMPLE)

func _initialize()->void:
    Engine.max_fps=0
    DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
    var active_payload:=load_json(ACTIVE_PATH)
    var candidate_payload:=load_json(CANDIDATE_PATH)
    if active_payload.is_empty() or candidate_payload.is_empty():
        fail("missing exact active or planar-role payload")
        return
    var active_proof:=building_proof(active_payload)
    var candidate_proof:=building_proof(candidate_payload)
    if active_proof.is_empty() or candidate_proof.is_empty():
        fail("missing exact Building receiving proof in donor payload")
        return
    if (active_proof.get("vertices_source_xyz_m",[]) as Array).size()!=184:
        fail("active segmented source vertex identity drift")
        return
    if (candidate_proof.get("vertices_source_xyz_m",[]) as Array).size()!=672:
        fail("planar-role source vertex identity drift")
        return
    var active_mesh:=build_receiver_mesh(active_proof,false)
    var candidate_mesh:=build_receiver_mesh(candidate_proof,true)
    var active_diag:=mesh_diag(active_mesh)
    var candidate_diag:=mesh_diag(candidate_mesh)
    if active_diag.get("surface_count",0)!=5 or active_diag.get("vertices",0)!=828 or active_diag.get("indices",-1)!=0 or active_diag.get("primitives",0)!=276:
        fail("active segmented final mesh identity drift: %s" % JSON.stringify(active_diag))
        return
    if candidate_diag.get("surface_count",0)!=5 or candidate_diag.get("vertices",0)!=312 or candidate_diag.get("indices",0)!=1008 or candidate_diag.get("primitives",0)!=336:
        fail("indexed planar-role final mesh identity drift: %s" % JSON.stringify(candidate_diag))
        return

    var viewport:=SubViewport.new()
    viewport.size=Vector2i(1280,720)
    viewport.own_world_3d=true
    viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
    viewport.render_target_clear_mode=SubViewport.CLEAR_MODE_ALWAYS
    get_root().add_child(viewport)
    var root3d:=Node3D.new()
    viewport.add_child(root3d)
    var env:=Environment.new()
    env.background_mode=Environment.BG_COLOR
    env.background_color=Color(0.055,0.07,0.09,1.0)
    env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color=Color(0.56,0.60,0.67,1.0)
    env.ambient_light_energy=0.62
    var world:=WorldEnvironment.new()
    world.environment=env
    root3d.add_child(world)
    var sun:=DirectionalLight3D.new()
    sun.shadow_enabled=false
    sun.light_energy=1.55
    sun.rotation_degrees=Vector3(-52,-35,0)
    root3d.add_child(sun)
    var active_node:=make_multimesh(active_mesh)
    active_node.name="active-segmented-stress"
    root3d.add_child(active_node)
    var candidate_node:=make_multimesh(candidate_mesh)
    candidate_node.name="indexed-planar-role-stress"
    root3d.add_child(candidate_node)
    var camera:=Camera3D.new()
    camera.projection=Camera3D.PROJECTION_ORTHOGONAL
    camera.size=7.3
    camera.near=0.05
    camera.far=80.0
    root3d.add_child(camera)
    camera.look_at_from_position(Vector3(0.0,0.0,25.0),Vector3.ZERO,Vector3.UP)
    camera.make_current()
    for _warm in range(8):
        await RenderingServer.frame_post_draw

    var results:Array=[]
    for count_value in INSTANCE_COUNTS:
        var count:=int(count_value)
        for warmup in range(WARMUP_PAIRS):
            var candidate_first:bool=(warmup%2)==1
            await measure_frame_delivery(active_node,candidate_node,candidate_first,count)
            await measure_frame_delivery(active_node,candidate_node,not candidate_first,count)
        var control_ms:Array=[]
        var candidate_ms:Array=[]
        var paired_delta_ms:Array=[]
        for trial in range(TRIALS):
            var candidate_first:bool=(trial%2)==1
            var first:float=await measure_frame_delivery(active_node,candidate_node,candidate_first,count)
            var second:float=await measure_frame_delivery(active_node,candidate_node,not candidate_first,count)
            var control_value:float
            var candidate_value:float
            if candidate_first:
                candidate_value=first
                control_value=second
            else:
                control_value=first
                candidate_value=second
            control_ms.append(control_value)
            candidate_ms.append(candidate_value)
            paired_delta_ms.append(candidate_value-control_value)
        await present(active_node,candidate_node,false,count)
        var control_stats:=runtime_stats()
        await present(active_node,candidate_node,true,count)
        var candidate_stats:=runtime_stats()
        results.append({"instance_count":count,"control_frame_ms":control_ms,"candidate_frame_ms":candidate_ms,"paired_delta_candidate_minus_control_ms":paired_delta_ms,"control_runtime":control_stats,"candidate_runtime":candidate_stats})

    var receipt:={"schema":SCHEMA,"state":"PASS_RAW_PRIMITIVE_SCALING_MEASUREMENT","proof_runtime":"Godot 4.7.2 GL Compatibility / X11","measurement_mode":"SAME_PROCESS_ALTERNATING_EXACT_RECEIVER_MULTIMESH_STRESS__NO_IMAGE_READBACK_IN_TIMED_WINDOW","instance_counts":INSTANCE_COUNTS,"warmup_pairs":WARMUP_PAIRS,"paired_trials_per_count":TRIALS,"frames_per_sample":FRAMES_PER_SAMPLE,"active_identity":active_diag,"candidate_identity":candidate_diag,"results":results,"visual_tradeoff":"NO_NEW_VISUAL_MUTATION__BENCHMARK_REUSES_EXACT_ACTIVE_SEGMENTED_AND_ALREADY_ART_REVIEWED_INDEXED_PLANAR_ROLE_RECEIVERS","truth_boundary":"Same-process proof-host primitive-scaling microbenchmark. It amplifies the exact active segmented and indexed planar-role Building receivers through identical MultiMesh instance transforms so small steady render-cost differences can become measurable while draw submission shape remains comparable. It excludes viewport readback from the timed window and does not represent current-world density, gameplay, target-device CPU/GPU/FPS/VRAM/thermal acceptance, Art preference, Environment adoption, CANON or production readiness.","godot_version":Engine.get_version_info()}
    var file:=FileAccess.open(OUTPUT_PATH,FileAccess.WRITE)
    if file==null:
        fail("could not open primitive scaling output")
        return
    file.store_string(JSON.stringify(receipt,"  ")+"\n")
    file.close()
    print("PASS_RAW_PRIMITIVE_SCALING_MEASUREMENT")
    quit(0)
