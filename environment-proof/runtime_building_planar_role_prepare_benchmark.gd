extends SceneTree

const PAYLOAD_PATH := "res://generated/current_world_nature_winding_migration.json"
const OUTPUT_PATH := "res://runtime-building-planar-role-prepare-benchmark.json"
const BUILDING_ID := "source:building:service-pavilion-001"
const REPRESENTATION_ID := "boundary-only-planar-role-rectangle-render-001"
const TRIALS := 41
const WARMUPS := 5

func fail(message:String)->void:
    push_error(message)
    quit(1)

func gvec(row:Array)->Vector3:
    return Vector3(float(row[0]),float(row[1]),float(row[2]))

func load_proof()->Dictionary:
    if not FileAccess.file_exists(PAYLOAD_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(PAYLOAD_PATH))
    if not (parsed is Dictionary):
        return {}
    var payload:=parsed as Dictionary
    if String(payload.get("building_planar_role_selected_representation_id",""))!=REPRESENTATION_ID:
        return {}
    var states:=payload.get("states",[]) as Array
    if states.size()!=17:
        return {}
    var scene:Dictionary=(states[0] as Dictionary).get("scene",{}) as Dictionary
    var proof:=scene.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!=BUILDING_ID:
        return {}
    if (proof.get("vertices_source_xyz_m",[]) as Array).size()!=672:
        return {}
    if (proof.get("surfaces",[]) as Array).size()!=5:
        return {}
    return proof

func mesh_diag(mesh:ArrayMesh)->Dictionary:
    var total_vertices:=0
    var total_indices:=0
    var total_primitives:=0
    var surfaces:Array=[]
    for surface_index in range(mesh.get_surface_count()):
        var vertex_count:=mesh.surface_get_array_len(surface_index)
        var index_count:=mesh.surface_get_array_index_len(surface_index)
        total_vertices+=vertex_count
        total_indices+=index_count
        total_primitives+=index_count/3 if index_count>0 else vertex_count/3
        surfaces.append({"surface_index":surface_index,"vertex_count":vertex_count,"index_count":index_count})
    return {
        "surface_count":mesh.get_surface_count(),
        "total_vertices":total_vertices,
        "total_indices":total_indices,
        "total_primitives":total_primitives,
        "surfaces":surfaces,
    }

func build_control(proof:Dictionary)->ArrayMesh:
    var vertices:=proof.get("vertices_source_xyz_m",[]) as Array
    var surfaces:=proof.get("surfaces",[]) as Array
    var unindexed:=ArrayMesh.new()
    for surface_value in surfaces:
        var surface:=surface_value as Dictionary
        var triangles:=surface.get("triangles",[]) as Array
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for tri_value in triangles:
            var tri:=tri_value as Array
            for raw_index in tri:
                st.add_vertex(gvec(vertices[int(raw_index)] as Array))
        st.generate_normals()
        st.commit(unindexed)
    var before:=mesh_diag(unindexed)
    if int(before.get("surface_count",0))!=5 or int(before.get("total_vertices",0))!=1008 or int(before.get("total_indices",-1))!=0 or int(before.get("total_primitives",0))!=336:
        return ArrayMesh.new()
    var indexed:=ArrayMesh.new()
    for surface_index in range(unindexed.get_surface_count()):
        var st:=SurfaceTool.new()
        st.create_from(unindexed,surface_index)
        st.index()
        st.commit(indexed)
    return indexed

func build_candidate(proof:Dictionary)->ArrayMesh:
    var vertices:=proof.get("vertices_source_xyz_m",[]) as Array
    var surfaces:=proof.get("surfaces",[]) as Array
    var mesh:=ArrayMesh.new()
    for surface_value in surfaces:
        var surface:=surface_value as Dictionary
        var triangles:=surface.get("triangles",[]) as Array
        var unique_points:Array[Vector3]=[]
        var indices:Array[int]=[]
        var lookup:Dictionary={}
        for tri_value in triangles:
            var tri:=tri_value as Array
            for raw_index in tri:
                var point:Vector3=gvec(vertices[int(raw_index)] as Array)
                var final_index:int
                if lookup.has(point):
                    final_index=int(lookup[point])
                else:
                    final_index=unique_points.size()
                    lookup[point]=final_index
                    unique_points.append(point)
                indices.append(final_index)
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for point in unique_points:
            st.add_vertex(point)
        for index in indices:
            st.add_index(index)
        st.generate_normals()
        st.commit(mesh)
    return mesh

func valid_final(mesh:ArrayMesh)->bool:
    var diag:=mesh_diag(mesh)
    return int(diag.get("surface_count",0))==5 and int(diag.get("total_vertices",0))==312 and int(diag.get("total_indices",0))==1008 and int(diag.get("total_primitives",0))==336

func measure_once(proof:Dictionary,candidate:bool)->Dictionary:
    RenderingServer.sync()
    var started:=Time.get_ticks_usec()
    var mesh:ArrayMesh=build_candidate(proof) if candidate else build_control(proof)
    var elapsed:=int(Time.get_ticks_usec()-started)
    if not valid_final(mesh):
        return {"ok":false,"elapsed_usec":elapsed,"diag":mesh_diag(mesh)}
    mesh=null
    RenderingServer.sync()
    return {"ok":true,"elapsed_usec":elapsed}

func median(values:Array[int])->float:
    var ordered:=values.duplicate()
    ordered.sort()
    return float(ordered[int(ordered.size()/2)])

func percentile_nearest(values:Array[int],fraction:float)->int:
    var ordered:=values.duplicate()
    ordered.sort()
    var index:=int(round(float(ordered.size()-1)*fraction))
    return int(ordered[clampi(index,0,ordered.size()-1)])

func _initialize()->void:
    var proof:=load_proof()
    if proof.is_empty():
        fail("Runtime Building preparation benchmark could not load exact proof payload")
        return

    for warmup in range(WARMUPS):
        var first_candidate:bool=(warmup%2)==1
        var a:=measure_once(proof,first_candidate)
        var b:=measure_once(proof,not first_candidate)
        if not bool(a.get("ok",false)) or not bool(b.get("ok",false)):
            fail("Runtime Building preparation benchmark warmup storage drift")
            return

    var control_usec:Array[int]=[]
    var candidate_usec:Array[int]=[]
    var paired_delta_candidate_minus_control:Array[int]=[]
    for trial in range(TRIALS):
        var candidate_first:bool=(trial%2)==1
        var first:=measure_once(proof,candidate_first)
        var second:=measure_once(proof,not candidate_first)
        if not bool(first.get("ok",false)) or not bool(second.get("ok",false)):
            fail("Runtime Building preparation benchmark measured storage drift")
            return
        var control_value:int
        var candidate_value:int
        if candidate_first:
            candidate_value=int(first["elapsed_usec"])
            control_value=int(second["elapsed_usec"])
        else:
            control_value=int(first["elapsed_usec"])
            candidate_value=int(second["elapsed_usec"])
        control_usec.append(control_value)
        candidate_usec.append(candidate_value)
        paired_delta_candidate_minus_control.append(candidate_value-control_value)

    var control_median:=median(control_usec)
    var candidate_median:=median(candidate_usec)
    var paired_median:=median(paired_delta_candidate_minus_control)
    var faster_pairs:=0
    for delta in paired_delta_candidate_minus_control:
        if delta<0:
            faster_pairs+=1
    var report:={
        "schema":"axm.runtime-building-planar-role-prepare-benchmark/v0.1",
        "representation_id":REPRESENTATION_ID,
        "trials":TRIALS,
        "warmups":WARMUPS,
        "ordering":"alternating control-first/candidate-first pairs with RenderingServer.sync outside timed boundary",
        "control_path":"1008 unindexed triangle-corner vertices -> generate normals -> create_from/index -> 312 stored vertices / 1008 indices",
        "candidate_path":"deduplicate position domain in receiver -> 312 vertices / 1008 indices -> generate normals",
        "timing_boundary":"Godot proof-host microseconds around geometry receiver construction only; no material creation, node insertion, PNG readback, whole-scene render, target-device frame time or GPU timing",
        "control_usec":control_usec,
        "candidate_usec":candidate_usec,
        "paired_delta_candidate_minus_control_usec":paired_delta_candidate_minus_control,
        "control_median_usec":control_median,
        "candidate_median_usec":candidate_median,
        "paired_delta_median_usec":paired_median,
        "control_p90_usec":percentile_nearest(control_usec,0.90),
        "candidate_p90_usec":percentile_nearest(candidate_usec,0.90),
        "candidate_faster_pairs":faster_pairs,
        "candidate_slower_or_equal_pairs":TRIALS-faster_pairs,
        "final_identity":{"surface_count":5,"stored_vertices":312,"indices":1008,"primitives":336},
        "truth_boundary":"This is a repeated proof-host geometry-construction benchmark of the exact current planar-role Building receiver paths. It intentionally excludes identical material creation and scene setup. It cannot establish target-device frame/FPS/GPU/VRAM acceptance, arbitrary attribute-domain safety, Art/QA acceptance or Environment adoption."
    }
    var f:=FileAccess.open(OUTPUT_PATH,FileAccess.WRITE)
    if f==null:
        fail("Runtime Building preparation benchmark could not open output")
        return
    f.store_string(JSON.stringify(report,"  ")+"\n")
    f.close()
    print(JSON.stringify(report))
    quit(0)
