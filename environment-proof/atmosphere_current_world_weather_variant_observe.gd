extends "res://atmosphere_current_world_rebind_observe.gd"

const VARIANT_PAYLOAD_PATH := "res://generated/current_world_weather_variant.json"
const VARIANT_SCHEMA := "axm.environment-current-world-weather-variant-evidence/v0.1"
const VARIANT_STATUS := "PASS_CURRENT_WORLD_WEATHER_VARIANT_REBIND_STRUCTURE"
const VARIANT_CONTEXTS := ["path_eye", "elevated_oblique"]
const VARIANT_SEED := 44021
const VARIANT_LAYOUT_DIGEST := "7ed55e93ea9445345016685320716006bc52960b33784cb620ca5670a74cc26f"
const VARIANT_TARGET_REAR_ASSET_ID := "source:nature:east-rear-tree-neutral-001"

func write_receipt()->void:
    var file:=FileAccess.open("res://atmosphere-current-world-weather-variant-runtime.json",FileAccess.WRITE)
    if file!=null:
        file.store_string(JSON.stringify(receipt,"  ")+"\n")
        file.close()

func load_payload()->Dictionary:
    if not FileAccess.file_exists(VARIANT_PAYLOAD_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(VARIANT_PAYLOAD_PATH))
    return parsed as Dictionary if parsed is Dictionary else {}

func capture(viewport:SubViewport,context:String,index:int)->Dictionary:
    var image:=viewport.get_texture().get_image()
    if image==null or image.is_empty():
        return {"state":"FAIL_CAPTURE"}
    var path="res://atmosphere-variant-%s-%02d.png" % [context,index]
    if image.save_png(path)!=OK:
        return {"state":"FAIL_CAPTURE"}
    return {"state":"PASS","path":path,"width":image.get_width(),"height":image.get_height(),"bytes":FileAccess.get_file_as_bytes(path).size()}

func _initialize()->void:
    receipt={
        "schema":"axm.environment-current-world-weather-variant-observation/v0.1",
        "proof_runtime":"Godot 4.7.2 GL Compatibility",
        "promotion_effect":"NONE",
        "weather_variant_seed":VARIANT_SEED,
        "weather_variant_layout_digest":VARIANT_LAYOUT_DIGEST,
        "truth_boundary":"Same-process visual observation of one exact source-owned Weather seeded layout substituted across the already-proven current-world 17-state Weather + sapling sequence. This does not prove arbitrary-seed quality, physical weather, wall-clock pacing, renderer interpolation, source line-width fidelity, target-device performance, gameplay, final Art Direction, CANON, or mastery."
    }
    var payload:=load_payload()
    if payload.is_empty() or String(payload.get("schema",""))!=VARIANT_SCHEMA:
        fail("missing or invalid current-world Weather variant payload")
        return
    if String(payload.get("status",""))!=VARIANT_STATUS:
        fail("current-world Weather variant structure must PASS before target-host observation")
        return
    if int(payload.get("weather_variant_seed",-1))!=VARIANT_SEED:
        fail("Weather variant seed drift")
        return
    if String(payload.get("weather_variant_layout_digest",""))!=VARIANT_LAYOUT_DIGEST:
        fail("Weather variant layout digest drift")
        return
    var states=payload["states"] as Array
    if states.size()!=17:
        fail("target-host proof requires exact 17-state sequence")
        return
    var first=states[0] as Dictionary
    var data=first["scene"] as Dictionary

    var viewport:=SubViewport.new()
    viewport.size=Vector2i(1100,720)
    viewport.own_world_3d=true
    viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
    viewport.render_target_clear_mode=SubViewport.CLEAR_MODE_ALWAYS
    get_root().add_child(viewport)
    var root3d:=Node3D.new()
    viewport.add_child(root3d)
    add_environment(root3d)
    for item in data["items"] as Array:
        add_proxy(root3d,item as Dictionary)
    add_path(root3d,data)
    var culling_review=data.get("environment_rear_tree_culling_review",{}) as Dictionary
    var cull_target_asset_id=String(culling_review.get("target_asset_id",""))
    if cull_target_asset_id!=VARIANT_TARGET_REAR_ASSET_ID:
        fail("current world rear-tree culling target drift")
        return
    var static_source_stats:=add_static_sources(root3d,data,cull_target_asset_id)
    make_weather()
    root3d.add_child(weather_node)
    make_sapling()
    root3d.add_child(sapling_node)

    var camera:=Camera3D.new()
    camera.near=0.05
    camera.far=120.0
    root3d.add_child(camera)
    camera.make_current()

    var samples=[]
    for row_value in states:
        var row=row_value as Dictionary
        var scene=row["scene"] as Dictionary
        var weather_update=fill_weather(scene["weather_lines"] as Array)
        if weather_update.get("state")!="PASS_SOURCE_STREAK_OPACITY_CONSUMED":
            fail("Weather source-opacity update failed at sample %s" % row["index"])
            return
        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        await settle()
        var contexts={}
        for context in VARIANT_CONTEXTS:
            configure_camera(camera,scene,String(context))
            await settle()
            var stats=runtime_stats()
            var shot=capture(viewport,String(context),int(row["index"]))
            if shot.get("state")!="PASS":
                fail("capture failed for %s sample %s" % [context,row["index"]])
                return
            contexts[String(context)]={"runtime":stats,"capture":shot}
        samples.append({
            "index":row["index"],
            "time_s":row["time_s"],
            "sampling_role":row["sampling_role"],
            "weather_field_digest":row["weather_field_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "static_source_meshes":static_source_stats,
            "contexts":contexts
        })

    receipt["state"]="PASS_CURRENT_WORLD_WEATHER_VARIANT_LIVE_OBSERVATION"
    receipt["receiving_head"]=payload["receiving_head"]
    receipt["parent_vfx_head"]=payload["parent_vfx_head"]
    receipt["environment_donor_head"]=payload["environment_donor_head"]
    receipt["dense_vfx_sequence_digest"]=payload["dense_vfx_sequence_digest"]
    receipt["weather_variant_head"]=payload["weather_variant_head"]
    receipt["weather_variant_seed"]=payload["weather_variant_seed"]
    receipt["weather_variant_layout_digest"]=payload["weather_variant_layout_digest"]
    receipt["rear_migrated_mesh_digest"]=payload["rear_migrated_mesh_digest"]
    receipt["weather_opacity_mode"]=WEATHER_OPACITY_MODE
    receipt["static_source_meshes"]=static_source_stats
    receipt["samples"]=samples
    receipt["godot_version"]=Engine.get_version_info()
    write_receipt()
    quit(0)
