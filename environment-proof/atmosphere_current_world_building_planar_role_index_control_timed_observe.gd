extends "res://atmosphere_current_world_building_planar_role_surface_index_observe.gd"

const RUNTIME_BUILDING_PREP_CONTROL_MODE := "POST_NORMAL_SURFACETOOL_INDEX_CONTROL"

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var started_usec:=Time.get_ticks_usec()
    var result:=super.add_segmented_building(root3d,data)
    if String(result.get("asset_id",""))=="source:building:service-pavilion-001":
        result["runtime_building_prepare_usec"]=int(Time.get_ticks_usec()-started_usec)
        result["runtime_building_prepare_mode"]=RUNTIME_BUILDING_PREP_CONTROL_MODE
    return result

func write_receipt()->void:
    receipt["runtime_building_prepare_control_mode"]=RUNTIME_BUILDING_PREP_CONTROL_MODE
    receipt["runtime_building_prepare_timing_boundary"]="Per-state wall-clock microseconds around the exact current Environment planar-role Building receiver construction plus post-normal SurfaceTool.index() rewrite on the proof host. This is proof-host preparation timing only, not target-device frame time."
    super.write_receipt()
