extends "res://atmosphere_current_world_nature_leaf_flutter_observe.gd"

# Proof-host continuity: atmosphere_current_world_weather_width_observe.gd is restored
# byte-for-byte from Map commit 15a03b7c3ba3aaa7c0475ca1a3091c15581f559b so the
# already-accepted inherited current-world observer chain is self-contained at this head.

const COMPACT_EAST_VFX_HEAD := "cef2ad78d8e36a55ada5dad07329f1a7125d48de"
const COMPACT_EAST_STRUCTURE_RESULT := "PASS_CURRENT_WORLD_COMPACT_EAST_VISUAL_RESPONSE_STRUCTURE"
const COMPACT_EAST_RECEIVING_SCHEMA := "axm.environment-compact-east-visual-response-receiving/v0.1"
const COMPACT_EAST_ASSET_ID := "source:nature:compact-east-tree-neutral-001"
const COMPACT_EAST_WEATHER_SEMANTICS := "VISUAL_DIRECTION_ONLY_NOT_PHYSICAL_WIND_SPEED"

func _compact_east(scene:Dictionary)->Dictionary:
    var found:Array = []
    for raw in scene.get("additional_source_meshes", []) as Array:
        var source := raw as Dictionary
        if String(source.get("asset_id", "")) == COMPACT_EAST_ASSET_ID:
            found.append(source)
    if found.size() != 1:
        return {}
    return found[0] as Dictionary

func load_payload()->Dictionary:
    # The inherited chain converts the canonical Nature-migration payload into the
    # Weather-width compatibility schema required by the inherited live observer.
    # Keep that compatibility envelope: the states inside it are already a deep
    # duplicate of the same canonical file and therefore contain the exact compact-
    # east phase meshes validated below.
    var compat := super.load_payload()
    if compat.is_empty():
        return {}
    if not FileAccess.file_exists(NATURE_MIGRATION_PAYLOAD_PATH):
        return {}
    var parsed = JSON.parse_string(FileAccess.get_file_as_string(NATURE_MIGRATION_PAYLOAD_PATH))
    if not (parsed is Dictionary):
        return {}
    var canonical := parsed as Dictionary
    if String(canonical.get("compact_east_visual_response_vfx_head", "")) != COMPACT_EAST_VFX_HEAD:
        return {}
    if String(canonical.get("compact_east_visual_response_structure_result", "")) != COMPACT_EAST_STRUCTURE_RESULT:
        return {}
    if String(canonical.get("compact_east_visual_response_weather_semantics", "")) != COMPACT_EAST_WEATHER_SEMANTICS:
        return {}
    var states := canonical.get("states", []) as Array
    if states.size() != 17:
        return {}
    for index in range(states.size()):
        var row := states[index] as Dictionary
        var scene := row.get("scene", {}) as Dictionary
        var source := _compact_east(scene)
        if source.is_empty():
            return {}
        var receiving := source.get("environment_compact_east_visual_response_receiving", {}) as Dictionary
        if String(receiving.get("schema", "")) != COMPACT_EAST_RECEIVING_SCHEMA:
            return {}
        if String(receiving.get("vfx_head", "")) != COMPACT_EAST_VFX_HEAD:
            return {}
        if int(receiving.get("source_phase_index", -1)) != index:
            return {}
        if String(receiving.get("weather_semantics", "")) != COMPACT_EAST_WEATHER_SEMANTICS:
            return {}
    return compat

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var result := super.add_static_source(root3d, source, cull_target_asset_id)
    if result.is_empty():
        return result
    if String(result.get("asset_id", "")) == COMPACT_EAST_ASSET_ID:
        var receiving := source.get("environment_compact_east_visual_response_receiving", {}) as Dictionary
        if String(receiving.get("schema", "")) != COMPACT_EAST_RECEIVING_SCHEMA:
            fail("compact-east visual response receiving schema missing")
            return {}
        result["compact_east_visual_response_vfx_head"] = String(receiving.get("vfx_head", ""))
        result["compact_east_visual_response_phase_index"] = int(receiving.get("source_phase_index", -1))
        result["compact_east_visual_response_maximum_added_vertex_displacement_m"] = float(receiving.get("maximum_added_vertex_displacement_m", -1.0))
        result["compact_east_visual_response_weather_semantics"] = String(receiving.get("weather_semantics", ""))
    return result

func _clear_static_root(static_root:Node3D)->void:
    for child in static_root.get_children():
        static_root.remove_child(child)
        child.free()

func _initialize()->void:
    receipt = {
        "schema":"axm.environment-current-world-weather-width-observation/v0.1",
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "promotion_effect":"NONE",
        "parent_variant_head":WIDTH_PARENT_HEAD,
        "presentation_mode":WIDTH_PRESENTATION_MODE,
        "truth_boundary":"Same-process fixed-view current-world observation of the exact compact-east 17-state visual-only Nature response while retaining the inherited Weather-width A/B surface. Static source meshes are rebuilt from each exact state before both fixed-view captures so compact-east phase identity is observed rather than frozen at the initial neutral state. This proves only the declared 1100x720 sampled states. It does not prove physical wind, biomechanics, wall-clock playback, target-device performance, gameplay/physics, final Art Direction, CANON, or mastery."
    }
    var payload := load_payload()
    if payload.is_empty() or String(payload.get("schema", "")) != WIDTH_SCHEMA:
        fail("missing or invalid current-world Weather width compatibility payload")
        return
    if String(payload.get("status", "")) != WIDTH_STATUS:
        fail("Weather width structure must PASS before compact-east target-host observation")
        return
    if String(payload.get("parent_variant_head", "")) != WIDTH_PARENT_HEAD:
        fail("Weather width parent variant head drift")
        return
    var states := payload.get("states", []) as Array
    if states.size() != 17:
        fail("compact-east target-host proof requires exact 17-state sequence")
        return

    var first := states[0] as Dictionary
    var data := first.get("scene", {}) as Dictionary
    var viewport := SubViewport.new()
    viewport.size = Vector2i(1100, 720)
    viewport.own_world_3d = true
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
    get_root().add_child(viewport)
    var root3d := Node3D.new()
    viewport.add_child(root3d)
    add_environment(root3d)
    for item in data.get("items", []) as Array:
        add_proxy(root3d, item as Dictionary)
    add_path(root3d, data)

    var culling_review := data.get("environment_rear_tree_culling_review", {}) as Dictionary
    var cull_target_asset_id := String(culling_review.get("target_asset_id", ""))
    if cull_target_asset_id != VARIANT_TARGET_REAR_ASSET_ID:
        fail("current-world rear-tree culling target drift")
        return

    # In this inherited chain add_static_sources deliberately expands beyond the
    # three additional_source_meshes rows to include accepted Building and dressing
    # receivers as well. Rebuild that full inherited set every phase and let the
    # downstream verifier compare every non-compact runtime row byte-for-byte with
    # the accepted parent rather than imposing a false source-count equality here.
    var static_root := Node3D.new()
    static_root.name = "dynamic-static-source-phase-root"
    root3d.add_child(static_root)

    make_weather()
    weather_material.cull_mode = BaseMaterial3D.CULL_DISABLED
    root3d.add_child(weather_node)
    make_sapling()
    root3d.add_child(sapling_node)

    var camera := Camera3D.new()
    camera.near = 0.05
    camera.far = 120.0
    root3d.add_child(camera)
    camera.make_current()

    var samples:Array = []
    var first_static_source_stats:Array = []
    for row_value in states:
        var row := row_value as Dictionary
        var scene := row.get("scene", {}) as Dictionary
        var index := int(row.get("index", -1))
        if index < 0 or index >= 17:
            fail("compact-east source phase index drift")
            return
        var row_culling_review := scene.get("environment_rear_tree_culling_review", {}) as Dictionary
        if String(row_culling_review.get("target_asset_id", "")) != cull_target_asset_id:
            fail("current-world rear-tree culling target changed across compact-east phases")
            return

        _clear_static_root(static_root)
        var static_source_stats := add_static_sources(static_root, scene, cull_target_asset_id)
        var compact_rows:Array = []
        for stat_value in static_source_stats:
            var stat := stat_value as Dictionary
            if String(stat.get("asset_id", "")) == COMPACT_EAST_ASSET_ID:
                compact_rows.append(stat)
        if compact_rows.size() != 1:
            fail("compact-east runtime source count drift at sample %s" % index)
            return
        var compact_stat := compact_rows[0] as Dictionary
        if int(compact_stat.get("compact_east_visual_response_phase_index", -1)) != index:
            fail("compact-east runtime phase identity drift at sample %s" % index)
            return
        if String(compact_stat.get("compact_east_visual_response_vfx_head", "")) != COMPACT_EAST_VFX_HEAD:
            fail("compact-east runtime VFX identity drift at sample %s" % index)
            return
        if index == 0:
            first_static_source_stats = static_source_stats.duplicate(true)

        var sapling_update := fill_sapling(scene.get("sapling", {}) as Dictionary)
        var contexts := {}
        for context_value in WIDTH_CONTEXTS:
            var context := String(context_value)
            configure_camera(camera, scene, context)
            await settle()

            var control_weather := fill_weather(scene.get("weather_lines", []) as Array)
            if control_weather.get("state") != "PASS_SOURCE_STREAK_OPACITY_CONSUMED":
                fail("control Weather update failed at sample %s / %s" % [index, context])
                return
            await settle()
            var control_stats := runtime_stats()
            var control_shot := capture_mode(viewport, context, index, "control")
            if control_shot.get("state") != "PASS":
                fail("control capture failed at sample %s / %s" % [index, context])
                return

            var candidate_weather := fill_weather_width_ribbons(scene.get("weather_lines", []) as Array, camera)
            if candidate_weather.get("state") != "PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
                fail("candidate Weather width update failed at sample %s / %s: %s" % [index, context, candidate_weather])
                return
            if float(candidate_weather.get("maximum_projected_width_residual_px", 999.0)) > WIDTH_RESIDUAL_TOL_PX:
                fail("candidate projected source-width residual exceeded tolerance at sample %s / %s" % [index, context])
                return
            await settle()
            var candidate_stats := runtime_stats()
            var candidate_shot := capture_mode(viewport, context, index, "candidate")
            if candidate_shot.get("state") != "PASS":
                fail("candidate capture failed at sample %s / %s" % [index, context])
                return

            contexts[context] = {
                "control":{"weather_update":control_weather,"runtime":control_stats,"capture":control_shot},
                "candidate":{"weather_update":candidate_weather,"runtime":candidate_stats,"capture":candidate_shot}
            }

        samples.append({
            "index":index,
            "time_s":row.get("time_s"),
            "weather_field_digest":row.get("weather_field_digest"),
            "weather_width_profile_digest":row.get("weather_width_profile_digest"),
            "sapling_mesh_digest":row.get("sapling_mesh_digest"),
            "sapling_update":sapling_update,
            "static_source_meshes":static_source_stats.duplicate(true),
            "contexts":contexts
        })

    receipt["state"] = "PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_LIVE_OBSERVATION"
    receipt["receiving_head"] = payload.get("receiving_head")
    receipt["parent_variant_head"] = payload.get("parent_variant_head")
    receipt["weather_variant_head"] = payload.get("weather_variant_head")
    receipt["weather_variant_seed"] = payload.get("weather_variant_seed")
    receipt["weather_variant_layout_digest"] = payload.get("weather_variant_layout_digest")
    receipt["source_width_profile_digest"] = payload.get("source_width_profile_digest")
    receipt["source_width_summary"] = payload.get("source_width_summary")
    receipt["static_source_meshes"] = first_static_source_stats
    receipt["samples"] = samples
    receipt["godot_version"] = Engine.get_version_info()
    write_receipt()
    quit(0)

func write_receipt()->void:
    receipt["environment_compact_east_visual_response_vfx_head"] = COMPACT_EAST_VFX_HEAD
    receipt["environment_compact_east_visual_response_structure_result"] = COMPACT_EAST_STRUCTURE_RESULT
    receipt["environment_compact_east_visual_response_receiving_schema"] = COMPACT_EAST_RECEIVING_SCHEMA
    receipt["environment_compact_east_visual_response_weather_semantics"] = COMPACT_EAST_WEATHER_SEMANTICS
    receipt["environment_compact_east_visual_response_phase_count"] = 17
    receipt["environment_compact_east_visual_response_truth_boundary"] = "Current-world receiving evidence only. The exact compact-east Nature VFX source-local 17-state bounded visual response is rendered inside the accepted Nature leaf-flutter current-world receiver. Existing Weather, west-sapling leaf flutter, Building, Object, rear Nature, route, cameras and lighting remain separate preserved identities. Visible shape change is not physical wind, biomechanics, gameplay/physics, wall-clock timing, target-device performance or final Art/Visual-QA acceptance."
    super.write_receipt()
