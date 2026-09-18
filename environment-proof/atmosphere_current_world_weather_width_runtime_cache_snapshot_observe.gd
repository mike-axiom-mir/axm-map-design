extends "res://atmosphere_current_world_weather_width_runtime_cache_observe.gd"

# Repair layer for the Runtime cache experiment.
# The first cache attempt used duplicate(true) on the live ImmediateMesh, which
# retained zero Weather surfaces. A later ArrayMesh snapshot preserved geometry
# but introduced a tiny 1-LSB visual difference in the elevated camera. Build
# each finite cache entry with the exact native mesh resource type and the exact
# inherited producer builder before the playback clock starts instead.

func build_context_cache(camera:Camera3D,states:Array,context:String)->Dictionary:
    configure_camera(camera,(states[0] as Dictionary)["scene"] as Dictionary,context)
    await settle(1)
    _attach_mutable_meshes()
    var memory_before:=runtime_stats()
    var original_weather_mesh:ImmediateMesh=weather_mesh
    var original_sapling_mesh:ArrayMesh=sapling_mesh
    var weather_meshes:Array=[]
    var sapling_meshes:Array=[]
    var source_receipts:Array=[]
    var maximum_width_residual:=0.0
    var build_start_us:=Time.get_ticks_usec()

    for row_value in states:
        var row=row_value as Dictionary
        var scene=row["scene"] as Dictionary

        # Deliberately replace only the receiving mesh resources while invoking
        # the inherited exact builders. Weather remains an ImmediateMesh and the
        # sapling remains an ArrayMesh, matching the rebuild control path.
        weather_mesh=ImmediateMesh.new()
        sapling_mesh=ArrayMesh.new()

        var sapling_update=fill_sapling(scene["sapling"] as Dictionary)
        if not sapling_receipt_is_live(sapling_update):
            weather_mesh=original_weather_mesh
            sapling_mesh=original_sapling_mesh
            _attach_mutable_meshes()
            return {"state":"FAIL_CACHE_SAPLING","index":row["index"],"detail":sapling_update}

        var weather_update=fill_weather_width_ribbons(scene["weather_lines"] as Array,camera)
        if String(weather_update.get("state",""))!="PASS_SOURCE_WIDTH_PX_CAMERA_PROJECTED_RIBBONS":
            weather_mesh=original_weather_mesh
            sapling_mesh=original_sapling_mesh
            _attach_mutable_meshes()
            return {"state":"FAIL_CACHE_WEATHER","index":row["index"],"detail":weather_update}

        var residual:=float(weather_update.get("maximum_projected_width_residual_px",999.0))
        if residual>WIDTH_RESIDUAL_TOL_PX:
            weather_mesh=original_weather_mesh
            sapling_mesh=original_sapling_mesh
            _attach_mutable_meshes()
            return {"state":"FAIL_CACHE_WIDTH_RESIDUAL","index":row["index"],"detail":weather_update}
        maximum_width_residual=maxf(maximum_width_residual,residual)

        if weather_mesh.get_surface_count()!=int(weather_update.get("surface_count",0)) or sapling_mesh.get_surface_count()!=int(sapling_update.get("surface_count",0)):
            var mismatch={
                "state":"FAIL_CACHE_SOURCE_SURFACE_MISMATCH",
                "index":row["index"],
                "expected_weather_surfaces":int(weather_update.get("surface_count",0)),
                "cached_weather_surfaces":weather_mesh.get_surface_count(),
                "expected_sapling_surfaces":int(sapling_update.get("surface_count",0)),
                "cached_sapling_surfaces":sapling_mesh.get_surface_count()
            }
            weather_mesh=original_weather_mesh
            sapling_mesh=original_sapling_mesh
            _attach_mutable_meshes()
            return mismatch

        weather_meshes.append(weather_mesh)
        sapling_meshes.append(sapling_mesh)
        source_receipts.append({
            "index":row["index"],
            "weather_field_digest":row["weather_field_digest"],
            "weather_width_profile_digest":row["weather_width_profile_digest"],
            "sapling_mesh_digest":row["sapling_mesh_digest"],
            "weather_update":weather_update,
            "sapling_update":sapling_update,
            "cache_build_policy":"EXACT_INHERITED_BUILDERS_ON_NATIVE_RESOURCE_TYPES",
            "weather_resource_class":"ImmediateMesh",
            "sapling_resource_class":"ArrayMesh",
            "cached_weather_surface_count":weather_mesh.get_surface_count(),
            "cached_sapling_surface_count":sapling_mesh.get_surface_count()
        })

    var build_end_us:=Time.get_ticks_usec()

    # Restore the rebuild-control resources before either timed mode starts.
    weather_mesh=original_weather_mesh
    sapling_mesh=original_sapling_mesh
    _attach_mutable_meshes()
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
        "resource_policy":"17_PREBUILT_WEATHER_IMMEDIATE_MESHES_PLUS_17_PREBUILT_SAPLING_ARRAY_MESHES_PER_FIXED_CAMERA_CONTEXT__EXACT_INHERITED_BUILDERS"
    }
