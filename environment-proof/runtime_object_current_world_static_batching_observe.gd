extends "res://animation_object_current_world_wallclock_observe.gd"

const RUNTIME_OUTPUT_PATH := "res://runtime-object-current-world-static-batching.json"
const RUNTIME_SCHEMA := "axm.runtime-object-current-world-static-batching-observation/v0.1"
const RUNTIME_PASS_STATE := "PASS_OBJECT_CURRENT_WORLD_STATIC_COMPONENT_BATCHING__HOLD_ART_QA_TARGET_DEVICE_FUTURE_ARTICULATION"
const EXACT_ANIMATION_PARENT_HEAD := "c2695f654f9dd44312ca5d205eceb27f7c2680ee"
const EXACT_TECHNICAL_ART_PARENT_HEAD := "d2974dec5043ed9afad346574b23ef8bd4438a76"
const RETAINED_SAMPLE_INDICES := [0, 10, 50, 100]
const BATCH_NODE_NAME := "AXM_RUNTIME_STATIC_COMPONENT_BATCH"

var runtime_receipt:Dictionary = {}

func _runtime_write()->void:
    var file := FileAccess.open(RUNTIME_OUTPUT_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(runtime_receipt, "  ") + "\n")
        file.close()

func _runtime_fail(message:String)->void:
    runtime_receipt["state"] = "FAIL"
    runtime_receipt["error"] = message
    _runtime_write()
    push_error(message)
    quit(1)

func _runtime_stats()->Dictionary:
    return {
        "objects_in_frame": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
        "primitives_in_frame": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
        "draw_calls_in_frame": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
        "texture_mem_bytes": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED),
        "buffer_mem_bytes": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_BUFFER_MEM_USED)
    }

func _moving_component_names(component_map:Dictionary)->Dictionary:
    var moving:Dictionary = {}
    for name in REQUIRED_MOVING_COMPONENTS:
        moving[String(name)] = true
    var changed := true
    while changed:
        changed = false
        for raw in component_map.get("components", []) as Array:
            var row := raw as Dictionary
            var name := String(row.get("name", ""))
            var parent_value = row.get("parent")
            if parent_value != null and moving.has(String(parent_value)) and not moving.has(name):
                moving[name] = true
                changed = true
    return moving

func _component_mesh_nodes(container:Node3D, component_map:Dictionary)->Dictionary:
    var nodes:Dictionary = {}
    for raw in component_map.get("components", []) as Array:
        var row := raw as Dictionary
        var name := String(row.get("name", ""))
        var found := _motion_find_node(container, name)
        if found == null or not (found is MeshInstance3D):
            _runtime_fail("Runtime component MeshInstance3D missing: " + name)
            return {}
        nodes[name] = found as MeshInstance3D
    return nodes

func _mesh_surface_triangle_count(mesh:Mesh)->int:
    var total := 0
    for surface_index in range(mesh.get_surface_count()):
        var index_count:int = mesh.surface_get_array_index_len(surface_index)
        var vertex_count:int = mesh.surface_get_array_len(surface_index)
        total += int(index_count / 3) if index_count > 0 else int(vertex_count / 3)
    return total

func _component_diag(nodes:Dictionary, moving:Dictionary)->Dictionary:
    var surfaces := 0
    var triangles := 0
    var moving_surfaces := 0
    var moving_triangles := 0
    var static_surfaces := 0
    var static_triangles := 0
    var names:Array = nodes.keys()
    names.sort()
    for raw_name in names:
        var name := String(raw_name)
        var node := nodes[name] as MeshInstance3D
        if node.mesh == null:
            _runtime_fail("Runtime control component mesh missing before batching: " + name)
            return {}
        var surface_count := node.mesh.get_surface_count()
        var triangle_count := _mesh_surface_triangle_count(node.mesh)
        surfaces += surface_count
        triangles += triangle_count
        if moving.has(name):
            moving_surfaces += surface_count
            moving_triangles += triangle_count
        else:
            static_surfaces += surface_count
            static_triangles += triangle_count
    return {
        "surface_instances": surfaces,
        "triangles": triangles,
        "moving_surface_instances": moving_surfaces,
        "moving_triangles": moving_triangles,
        "static_surface_instances": static_surfaces,
        "static_triangles": static_triangles
    }

func _arrays_equal_except_index(a:Array, b:Array)->bool:
    if a.size() != b.size():
        return false
    for slot in range(a.size()):
        if slot == Mesh.ARRAY_INDEX:
            continue
        if typeof(a[slot]) != typeof(b[slot]):
            return false
        if a[slot] != b[slot]:
            return false
    return true

func _surface_group_key(material:Material, arrays:Array)->String:
    return "%s:%s:%s:%s" % [
        str(material.get_instance_id()),
        str(hash(arrays[Mesh.ARRAY_VERTEX])),
        str(hash(arrays[Mesh.ARRAY_NORMAL])),
        str(hash(arrays[Mesh.ARRAY_TEX_UV]))
    ]

func _build_static_batch(container:Node3D, nodes:Dictionary, moving:Dictionary)->Dictionary:
    var groups:Dictionary = {}
    var static_names:Array = []
    var static_triangles := 0

    var names:Array = nodes.keys()
    names.sort()
    for raw_name in names:
        var name := String(raw_name)
        if moving.has(name):
            continue
        static_names.append(name)
        var node := nodes[name] as MeshInstance3D
        if node.transform != Transform3D.IDENTITY:
            _runtime_fail("Runtime static component has a non-identity local transform and cannot be safely batched: " + name)
            return {}
        if node.mesh == null:
            _runtime_fail("Runtime static component mesh missing: " + name)
            return {}
        for surface_index in range(node.mesh.get_surface_count()):
            var arrays := node.mesh.surface_get_arrays(surface_index)
            if arrays.size() <= Mesh.ARRAY_INDEX:
                _runtime_fail("Runtime static component array layout drift: " + name)
                return {}
            if typeof(arrays[Mesh.ARRAY_INDEX]) != TYPE_PACKED_INT32_ARRAY:
                _runtime_fail("Runtime static component requires indexed geometry: " + name)
                return {}
            var material := node.mesh.surface_get_material(surface_index)
            if material == null:
                _runtime_fail("Runtime static component material missing: " + name)
                return {}
            var indices := arrays[Mesh.ARRAY_INDEX] as PackedInt32Array
            if indices.size() == 0 or indices.size() % 3 != 0:
                _runtime_fail("Runtime static component index stream drift: " + name)
                return {}
            static_triangles += int(indices.size() / 3)
            var key := _surface_group_key(material, arrays)
            if not groups.has(key):
                groups[key] = {
                    "arrays": arrays.duplicate(true),
                    "material": material,
                    "indices": PackedInt32Array(),
                    "source_surface_instances": 0
                }
            var group := groups[key] as Dictionary
            var canonical := group["arrays"] as Array
            if not _arrays_equal_except_index(canonical, arrays):
                _runtime_fail("Runtime static batching surface-group hash collision or attribute-domain drift")
                return {}
            var merged := group["indices"] as PackedInt32Array
            merged.append_array(indices)
            group["indices"] = merged
            group["source_surface_instances"] = int(group["source_surface_instances"]) + 1
            groups[key] = group

    var keys:Array = groups.keys()
    keys.sort()
    var batch_mesh := ArrayMesh.new()
    var source_surface_instances := 0
    for raw_key in keys:
        var group := groups[String(raw_key)] as Dictionary
        var arrays := (group["arrays"] as Array).duplicate(true)
        arrays[Mesh.ARRAY_INDEX] = group["indices"] as PackedInt32Array
        batch_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
        batch_mesh.surface_set_material(batch_mesh.get_surface_count() - 1, group["material"] as Material)
        source_surface_instances += int(group["source_surface_instances"])

    if batch_mesh.get_surface_count() <= 0:
        _runtime_fail("Runtime static batch produced no surfaces")
        return {}
    if _mesh_surface_triangle_count(batch_mesh) != static_triangles:
        _runtime_fail("Runtime static batch triangle count drift")
        return {}

    var batch_node := MeshInstance3D.new()
    batch_node.name = BATCH_NODE_NAME
    batch_node.mesh = batch_mesh
    container.add_child(batch_node)

    var detached := 0
    for raw_name in static_names:
        var node := nodes[String(raw_name)] as MeshInstance3D
        node.mesh = null
        node.set_meta("axm_runtime_static_batched", true)
        detached += 1

    return {
        "node": batch_node,
        "static_component_names": static_names,
        "static_component_count": static_names.size(),
        "source_surface_instances": source_surface_instances,
        "batch_surface_count": batch_mesh.get_surface_count(),
        "static_triangles": static_triangles,
        "detached_static_mesh_count": detached
    }

func _seek_sample(world:Dictionary, sample_index:int)->void:
    var player := world["player"] as AnimationPlayer
    player.stop()
    player.play("owner_samples")
    player.seek(float(sample_index) / OWNER_RATE_HZ, true)
    player.pause()
    await process_frame
    await RenderingServer.frame_post_draw
    await RenderingServer.frame_post_draw

func _pose_signature(world:Dictionary, moving:Dictionary)->Dictionary:
    var container := world["container"] as Node3D
    var lid := world["lid"] as Node3D
    var pivots := world["pivots"] as Dictionary
    var centers:Dictionary = {}
    var names:Array = moving.keys()
    names.sort()
    for raw_name in names:
        var name := String(raw_name)
        var node := _motion_find_node(container, name)
        if node == null:
            _runtime_fail("Runtime moving component missing during pose capture: " + name)
            return {}
        var center := _motion_receiver_local_mesh_center(container, node)
        centers[name] = [center.x, center.y, center.z]
    return {
        "lid_rotation_deg_x": lid.rotation_degrees.x,
        "latch_rotation_deg_x": _latch_angles(pivots),
        "centers_receiver_xyz_m": centers
    }

func _vec3_from_array(values:Array)->Vector3:
    return Vector3(float(values[0]), float(values[1]), float(values[2]))

func _pose_delta(control:Dictionary, candidate:Dictionary)->Dictionary:
    var max_angle := absf(float(control["lid_rotation_deg_x"]) - float(candidate["lid_rotation_deg_x"]))
    var a_latches := control["latch_rotation_deg_x"] as Array
    var b_latches := candidate["latch_rotation_deg_x"] as Array
    if a_latches.size() != b_latches.size():
        _runtime_fail("Runtime latch pose arity drift")
        return {}
    for i in range(a_latches.size()):
        max_angle = maxf(max_angle, absf(float(a_latches[i]) - float(b_latches[i])))
    var a_centers := control["centers_receiver_xyz_m"] as Dictionary
    var b_centers := candidate["centers_receiver_xyz_m"] as Dictionary
    if a_centers.keys().size() != b_centers.keys().size():
        _runtime_fail("Runtime moving center key drift")
        return {}
    var max_position := 0.0
    for raw_name in a_centers.keys():
        var name := String(raw_name)
        if not b_centers.has(name):
            _runtime_fail("Runtime moving center missing in candidate: " + name)
            return {}
        var a := _vec3_from_array(a_centers[name] as Array)
        var b := _vec3_from_array(b_centers[name] as Array)
        max_position = maxf(max_position, a.distance_to(b))
    return {"max_angle_deg": max_angle, "max_position_m": max_position}

func _save_image(image:Image, path:String)->void:
    if image == null or image.is_empty():
        _runtime_fail("Runtime shaded image unavailable: " + path)
        return
    if image.get_format() != Image.FORMAT_RGBA8:
        image.convert(Image.FORMAT_RGBA8)
    var err := image.save_png(path)
    if err != OK:
        _runtime_fail("Runtime failed to save shaded image: " + path)

func _visual_delta(a:PackedByteArray, b:PackedByteArray)->Dictionary:
    if a.size() != b.size() or a.size() % 4 != 0:
        _runtime_fail("Runtime visual byte-domain drift")
        return {}
    var changed_pixels := 0
    var pixels_over_1 := 0
    var max_delta := 0
    for offset in range(0, a.size(), 4):
        var pixel_max := 0
        for channel in range(4):
            pixel_max = maxi(pixel_max, absi(int(a[offset + channel]) - int(b[offset + channel])))
        if pixel_max > 0:
            changed_pixels += 1
        if pixel_max > 1:
            pixels_over_1 += 1
        max_delta = maxi(max_delta, pixel_max)
    return {
        "pixel_count": int(a.size() / 4),
        "changed_pixels": changed_pixels,
        "pixels_over_1_lsb": pixels_over_1,
        "max_channel_delta_lsb": max_delta,
        "byte_identical_pixels": changed_pixels == 0
    }

func _capture_control(world:Dictionary, sample_index:int, moving:Dictionary)->Dictionary:
    await _seek_sample(world, sample_index)
    var runtime := _runtime_stats()
    var pose := _pose_signature(world, moving)
    var viewport := world["viewport"] as SubViewport
    var image := viewport.get_texture().get_image()
    var path := "res://runtime-object-static-batching-control-key%03d.png" % sample_index
    _save_image(image, path)
    return {
        "runtime": runtime,
        "pose": pose,
        "pixels": image.get_data(),
        "path": path
    }

func _capture_candidate(world:Dictionary, sample_index:int, moving:Dictionary, control:Dictionary)->Dictionary:
    await _seek_sample(world, sample_index)
    var runtime := _runtime_stats()
    var pose := _pose_signature(world, moving)
    var viewport := world["viewport"] as SubViewport
    var image := viewport.get_texture().get_image()
    var path := "res://runtime-object-static-batching-candidate-key%03d.png" % sample_index
    _save_image(image, path)
    var delta := _visual_delta(control["pixels"] as PackedByteArray, image.get_data())
    var pose_delta := _pose_delta(control["pose"] as Dictionary, pose)
    return {
        "runtime": runtime,
        "pose": pose,
        "path": path,
        "visual": delta,
        "max_owner_pose_delta_deg": float(pose_delta["max_angle_deg"]),
        "max_owner_position_delta_m": float(pose_delta["max_position_m"])
    }

func _component_nodes_preserved(container:Node3D, component_map:Dictionary)->bool:
    for raw in component_map.get("components", []) as Array:
        var name := String((raw as Dictionary).get("name", ""))
        if _motion_find_node(container, name) == null:
            return false
    return true

func _initialize()->void:
    runtime_receipt = {
        "schema": RUNTIME_SCHEMA,
        "state": "STARTED",
        "animation_parent_head": EXACT_ANIMATION_PARENT_HEAD,
        "technical_art_parent_head": EXACT_TECHNICAL_ART_PARENT_HEAD
    }

    Engine.max_fps = 0
    DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)

    var world := await _build_current_world()
    if world.is_empty():
        _runtime_fail("Runtime could not build exact Animation/Technical-Art current world")
        return
    var container := world["container"] as Node3D
    var component_map := _load_rigid_component_map()
    if component_map.is_empty():
        _runtime_fail("Runtime exact rigid component map missing")
        return
    var moving := _moving_component_names(component_map)
    var nodes := _component_mesh_nodes(container, component_map)
    if nodes.size() != 31:
        _runtime_fail("Runtime exact component node count drift")
        return
    var control_diag := _component_diag(nodes, moving)
    if control_diag.is_empty():
        return
    if int(control_diag["surface_instances"]) != 33 or int(control_diag["triangles"]) != 812:
        _runtime_fail("Runtime exact Technical-Art receiver identity drift")
        return

    var control_by_sample:Dictionary = {}
    for raw_index in RETAINED_SAMPLE_INDICES:
        var sample_index := int(raw_index)
        control_by_sample[sample_index] = await _capture_control(world, sample_index, moving)

    await _seek_sample(world, 0)
    var build_started := Time.get_ticks_usec()
    var batch := _build_static_batch(container, nodes, moving)
    var batch_build_usec := Time.get_ticks_usec() - build_started
    if batch.is_empty():
        return
    await process_frame
    await RenderingServer.frame_post_draw
    await RenderingServer.frame_post_draw

    if not _component_nodes_preserved(container, component_map):
        _runtime_fail("Runtime batching removed source-owned component nodes")
        return
    for raw_name in moving.keys():
        var moving_node := nodes[String(raw_name)] as MeshInstance3D
        if moving_node.mesh == null:
            _runtime_fail("Runtime batching detached a moving component mesh: " + String(raw_name))
            return

    var candidate_render_surface_count := int(control_diag["moving_surface_instances"]) + int(batch["batch_surface_count"])
    var candidate_triangles := int(control_diag["moving_triangles"]) + int(batch["static_triangles"])
    if candidate_triangles != 812:
        _runtime_fail("Runtime candidate triangle count drift")
        return

    var measurements:Array = []
    var min_draw_saved := 2147483647
    var min_objects_saved := 2147483647
    var min_buffer_delta := 2147483647
    var max_buffer_delta := -2147483648
    var total_changed_pixels := 0
    var total_pixels_over_1 := 0
    var max_visual_delta := 0

    for raw_index in RETAINED_SAMPLE_INDICES:
        var sample_index := int(raw_index)
        var control := control_by_sample[sample_index] as Dictionary
        var candidate := await _capture_candidate(world, sample_index, moving, control)
        var control_runtime := control["runtime"] as Dictionary
        var candidate_runtime := candidate["runtime"] as Dictionary
        var draw_saved := int(control_runtime["draw_calls_in_frame"]) - int(candidate_runtime["draw_calls_in_frame"])
        var objects_saved := int(control_runtime["objects_in_frame"]) - int(candidate_runtime["objects_in_frame"])
        var buffer_delta := int(candidate_runtime["buffer_mem_bytes"]) - int(control_runtime["buffer_mem_bytes"])
        min_draw_saved = mini(min_draw_saved, draw_saved)
        min_objects_saved = mini(min_objects_saved, objects_saved)
        min_buffer_delta = mini(min_buffer_delta, buffer_delta)
        max_buffer_delta = maxi(max_buffer_delta, buffer_delta)
        var visual := candidate["visual"] as Dictionary
        total_changed_pixels += int(visual["changed_pixels"])
        total_pixels_over_1 += int(visual["pixels_over_1_lsb"])
        max_visual_delta = maxi(max_visual_delta, int(visual["max_channel_delta_lsb"]))
        measurements.append({
            "sample_index": sample_index,
            "time_s": float(sample_index) / OWNER_RATE_HZ,
            "control_runtime": control_runtime,
            "candidate_runtime": candidate_runtime,
            "visual": visual,
            "max_owner_pose_delta_deg": candidate["max_owner_pose_delta_deg"],
            "max_owner_position_delta_m": candidate["max_owner_position_delta_m"]
        })

    if min_draw_saved <= 0:
        _runtime_fail("Runtime static batching did not reduce draw calls at every retained owner sample")
        return
    if min_objects_saved <= 0:
        _runtime_fail("Runtime static batching did not reduce visible objects at every retained owner sample")
        return
    if total_pixels_over_1 != 0 or max_visual_delta > 1:
        _runtime_fail("Runtime static batching exceeded the one-LSB fixed-view visual boundary")
        return

    var visual_tradeoff := "NONE_OBSERVED_ALL_RETAINED_SHADED_PAIRS_PIXEL_IDENTICAL"
    if total_changed_pixels > 0:
        visual_tradeoff = "BOUNDED_FIXED_VIEW_RASTER_DELTA__ZERO_PIXELS_OVER_1_LSB__ART_QA_REVIEW_REQUIRED"

    runtime_receipt = {
        "schema": RUNTIME_SCHEMA,
        "state": RUNTIME_PASS_STATE,
        "proof_runtime": "Godot 4.7.2 GL Compatibility / X11",
        "animation_parent_head": EXACT_ANIMATION_PARENT_HEAD,
        "technical_art_parent_head": EXACT_TECHNICAL_ART_PARENT_HEAD,
        "component_count": nodes.size(),
        "moving_component_count": moving.size(),
        "static_component_count": int(batch["static_component_count"]),
        "control_component_surface_instances": int(control_diag["surface_instances"]),
        "control_moving_surface_instances": int(control_diag["moving_surface_instances"]),
        "control_static_surface_instances": int(control_diag["static_surface_instances"]),
        "static_batch_surface_count": int(batch["batch_surface_count"]),
        "candidate_render_surface_count": candidate_render_surface_count,
        "control_triangles": int(control_diag["triangles"]),
        "candidate_triangles": candidate_triangles,
        "detached_static_mesh_count": int(batch["detached_static_mesh_count"]),
        "component_nodes_preserved": true,
        "batch_build_usec_single_observation": batch_build_usec,
        "measurements": measurements,
        "summary": {
            "min_draw_calls_saved": min_draw_saved,
            "min_objects_saved": min_objects_saved,
            "buffer_delta_min_bytes": min_buffer_delta,
            "buffer_delta_max_bytes": max_buffer_delta,
            "total_changed_pixels_across_pairs": total_changed_pixels,
            "total_pixels_over_1_lsb": total_pixels_over_1,
            "max_channel_delta_lsb": max_visual_delta
        },
        "visual_tradeoff": visual_tradeoff,
        "representation_tradeoff": "STATIC_SOURCE_OWNED_COMPONENT_NODES_REMAIN_ADDRESSABLE_BUT_THEIR_RENDER_MESHES_ARE_DETACHED_AND_UNIONED_INTO_ONE_SHARED_STATIC_BATCH; A FUTURE_SEQUENCE_THAT_ANIMATES_ANY_CURRENTLY_STATIC_COMPONENT_REQUIRES_DEBATCH_OR_REBIND",
        "future_arbitrary_articulation_accepted": false,
        "target_device_performance_accepted": false,
        "art_qa_accepted": false,
        "environment_adoption": false,
        "vfx_adoption": false,
        "canon": false,
        "truth_boundary": "Exact current-owner-sequence receiver optimization only. The Technical-Art 31-component semantic hierarchy remains present, while only components proven static under the pinned 101-key Object owner sequence surrender individual render meshes to one material/attribute-compatible ArrayMesh batch. Runtime measures proof-host submission/object/buffer counters and fixed-view shaded raster deltas. This does not authorize batching a component that moves in another sequence, target-device performance, Environment/VFX adoption, Art/QA acceptance, CANON or production readiness."
    }
    _runtime_write()
    print(RUNTIME_PASS_STATE)
    quit(0)
