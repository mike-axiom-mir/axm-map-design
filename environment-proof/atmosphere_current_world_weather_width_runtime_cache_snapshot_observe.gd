extends "res://atmosphere_current_world_weather_width_runtime_cache_observe.gd"

# Repair layer for the Runtime cache experiment.
# ImmediateMesh.duplicate(true) does not preserve the generated surfaces in the
# Godot 4.7.2 proof host used by this lane. Snapshot every live generated
# surface into a standalone ArrayMesh instead, preserving primitive type and
# material, and fail closed if any expected surface disappears.

func snapshot_live_mesh(source:Mesh,label:String)->Dictionary:
    if source==null:
        return {"state":"FAIL_SNAPSHOT_NULL_MESH","label":label}
    var source_surface_count:int=source.get_surface_count()
    if source_surface_count<=0:
        return {"state":"FAIL_SNAPSHOT_EMPTY_SOURCE","label":label,"source_surface_count":source_surface_count}
    var snapshot:ArrayMesh=ArrayMesh.new()
    for surface_index in range(source_surface_count):
        var arrays:Array=source.surface_get_arrays(surface_index)
        if arrays.is_empty():
            return {"state":"FAIL_SNAPSHOT_EMPTY_ARRAYS","label":label,"surface_index":surface_index}
        snapshot.add_surface_from_arrays(source.surface_get_primitive_type(surface_index),arrays)
        var material:Material=source.surface_get_material(surface_index)
        if material!=null:
            snapshot.surface_set_material(surface_index,material)
    if snapshot.get_surface_count()!=source_surface_count:
        return {
            "state":"FAIL_SNAPSHOT_SURFACE_COUNT_DRIFT",
            "label":label,
            "source_surface_count":source_surface_count,
            "snapshot_surface_count":snapshot.get_surface_count()
        }
    return {
        "state":"PASS_LIVE_MESH_SNAPSHOT",
        "label":label,
        "source_surface_count":source_surface_count,
        "snapshot_surface_count":snapshot.get_surface_count(),
        "mesh":snapshot
    }

func build_context_cache(camera:Camera3D,states:Array,context:String)->Dictionary:
    configure_camera(camera,(states[0] as Dictionary)["scene"] as Dictionary,context)
    await settle(1)
    _attach_mutable_meshes()
    var memory_before:=runtime_stats()
    var weather_meshes:Array=[]
    var sapling_meshes:Array=[]
    var source_receipts:Array=[]
    var maximum_width_residual:=0.0
    var build_start_us:=Time.get_ticks_usec()
    for row_value in states:
        var row=row_value as Dictionary
        var scene=row["scene"] as Dictionary
        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        if not sapling_receipt_is_live(sapling_update):
            return {"state":"FAIL_CACHE_SAPLING","index":row["index"],"detail":sapling_update}
        var weather_update=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
        if String(weather_update.get("state",""))!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            return {"state":"FAIL_CACHE_WEATHER","index":row["index"],"detail":weather_update}
        var residual:=float(weather_update.get("maximum_projected_width_residual_px",999.0))
        if residual>WIDTH_RESIDUAL_TOL_PX:
            return {"state":"FAIL_CACHE_WIDTH_RESIDUAL","index":row["index"],"detail":weather_update}
        maximum_width_residual=maxf(maximum_width_residual,residual)

        var weather_snapshot:=snapshot_live_mesh(weather_mesh,"weather")
        if String(weather_snapshot.get("state",""))!="PASS_LIVE_MESH_SNAPSHOT":
            return {"state":"FAIL_CACHE_WEATHER_SNAPSHOT","index":row["index"],"detail":weather_snapshot}
        var sapling_snapshot:=snapshot_live_mesh(sapling_mesh,"sapling")
        if String(sapling_snapshot.get("state",""))!="PASS_LIVE_MESH_SNAPSHOT":
            return {"state":"FAIL_CACHE_SAPLING_SNAPSHOT","index":row["index"],"detail":sapling_snapshot}

        var cached_weather:Mesh=weather_snapshot["mesh"] as Mesh
        var cached_sapling:Mesh=sapling_snapshot["mesh"] as Mesh
        var expected_weather_surfaces:=int(weather_update.get("surface_count",0))
        var expected_sapling_surfaces:=int(sapling_update.get("surface_count",0))
        if cached_weather.get_surface_count()!=expected_weather_surfaces or cached_sapling.get_surface_count()!=expected_sapling_surfaces:
            return {
                "state":"FAIL_CACHE_SOURCE_SURFACE_MISMATCH",
                "index":row["index"],
                "expected_weather_surfaces":expected_weather_surfaces,
                "cached_weather_surfaces":cached_weather.get_surface_count(),
                "expected_sapling_surfaces":expected_sapling_surfaces,
                "cached_sapling_surfaces":cached_sapling.get_surface_count()
            }
        weather_meshes.append(cached_weather)
        sapling_meshes.append(cached_sapling)
        source_receipts.append({
            "index":row["index"],
            "weather_field_digest":row["weather_field_digest"],
            "weather_width_profile_digest":row["weather_width_profile_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "snapshot_policy":"ARRAY_MESH_COPY_OF_LIVE_GENERATED_SURFACES",
            "cached_weather_surface_count":cached_weather.get_surface_count(),
            "cached_sapling_surface_count":cached_sapling.get_surface_count()
        })
    var build_end_us:=Time.get_ticks_usec()
    await settle(1)
    var memory_after:=runtime_stats()
    return {
        "state":"PASS_EXACT_17_STATE_CONTEXT_CACHE",
        "context":context,
        "weather_meshes":weather_meshes,
        "sapling_meshes":sapling_meshes,
        "source_receipts":source_receipts,
        "maximum_projected_width_residual_px":maximum_width_residual,
        "build_duration_ms":float(build_end_us-build_start_us)/1000.0,
        "memory_before":memory_before,
        "memory_after":memory_after,
        "observed_buffer_delta_bytes":int(memory_after["buffer_mem_bytes"])-int(memory_before["buffer_mem_bytes"]),
        "observed_texture_delta_bytes":int(memory_after["texture_mem_bytes"])-int(memory_before["texture_mem_bytes"]),
        "resource_policy":"17_PREBUILT_WEATHER_ARRAY_MESH_SNAPSHOTS_PLUS_17_PREBUILT_SAPLING_ARRAY_MESH_SNAPSHOTS_PER_FIXED_CAMERA_CONTEXT"
    }
