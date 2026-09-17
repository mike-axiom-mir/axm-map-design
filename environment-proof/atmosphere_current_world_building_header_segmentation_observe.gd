extends "res://atmosphere_current_world_object_readability_dressing_observe.gd"

const SEGMENTED_PAYLOAD_PATH := "res://generated/current_world_building_header_segmentation.json"
const SEGMENTED_SCHEMA := "axm.environment-current-world-building-header-segmentation-composition/v0.1"
const SEGMENTED_STATUS := "PASS_CURRENT_WORLD_BUILDING_HEADER_SEGMENTATION_STRUCTURE"
const SEGMENTED_PARENT_HEAD := "a29aa1e3d2260e8eb5ab2ac78a95d35ce131214c"
const SEGMENTED_SOURCE_HEAD := "34124101e616c423c5a3ed5e122ddf09b98a1650"
const SEGMENTED_MATERIAL_HEAD := "09a534d9d6d4cdaa1bab70cc2d01345b48d8fcc8"
const SEGMENTED_REVISION := "service-pavilion-001/interpenetration-free-header-segmentation-003"
const SEGMENTED_EXPECTED_ROLES := [
    "frame_galvanized",
    "infill_coating",
    "roof_membrane",
    "slab_mineral",
    "utility_panel_ochre",
]

func load_payload()->Dictionary:
    if not FileAccess.file_exists(SEGMENTED_PAYLOAD_PATH):
        return {}
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(SEGMENTED_PAYLOAD_PATH))
    if not (parsed is Dictionary):
        return {}
    var canonical=parsed as Dictionary
    if String(canonical.get("schema",""))!=SEGMENTED_SCHEMA:
        return {}
    if String(canonical.get("status",""))!=SEGMENTED_STATUS:
        return {}
    if String(canonical.get("parent_environment_head",""))!=SEGMENTED_PARENT_HEAD:
        return {}
    if String(canonical.get("building_source_head",""))!=SEGMENTED_SOURCE_HEAD:
        return {}
    if String(canonical.get("building_material_head",""))!=SEGMENTED_MATERIAL_HEAD:
        return {}
    var segmentation=canonical.get("building_header_segmentation",{}) as Dictionary
    if String(segmentation.get("revision",""))!=SEGMENTED_REVISION:
        return {}
    var compat=canonical.duplicate(true)
    compat["schema"]="axm.environment-current-world-weather-width-evidence/v0.1"
    compat["status"]="PASS_CURRENT_WORLD_WEATHER_SOURCE_WIDTH_STRUCTURE"
    compat["parent_variant_head"]="e482d003853e52fc835f1797ddfb6506a50083ef"
    return compat

func write_receipt()->void:
    receipt["environment_building_header_segmentation_source_head"]=SEGMENTED_SOURCE_HEAD
    receipt["environment_building_header_segmentation_material_head"]=SEGMENTED_MATERIAL_HEAD
    receipt["environment_building_header_segmentation_revision"]=SEGMENTED_REVISION
    receipt["environment_building_header_segmentation_truth_boundary"]="Exact source-owned emitted representation only; occupied union, accepted material scalars, Object dressing, Weather, Nature, path, cameras and lighting remain externally owned. Runtime counters are diagnostic only."
    super.write_receipt()

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var proof=data.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!="source:building:service-pavilion-001":
        fail("missing exact segmented Building receiving payload")
        return {}
    var rebind=proof.get("source_header_segmentation_rebind",{}) as Dictionary
    if String(rebind.get("source_head",""))!=SEGMENTED_SOURCE_HEAD:
        fail("segmented Building source head drift")
        return {}
    if String(rebind.get("segmentation_revision",""))!=SEGMENTED_REVISION:
        fail("segmented Building revision drift")
        return {}
    if int(rebind.get("historical_positive_volume_intersection_count",-1))!=4:
        fail("segmented Building historical overlap count drift")
        return {}
    if int(rebind.get("successor_positive_volume_intersection_count",-1))!=0:
        fail("segmented Building successor overlap count drift")
        return {}
    if not bool(rebind.get("occupied_union_equivalent",false)):
        fail("segmented Building occupied-union equivalence missing")
        return {}

    var vertices=proof.get("vertices_source_xyz_m",[]) as Array
    var surfaces=proof.get("surfaces",[]) as Array
    if vertices.size()!=184 or surfaces.size()!=5:
        fail("segmented Building geometry/surface count drift")
        return {}
    var roles:Array=[]
    var material_ids:Array=[]
    var triangle_count:=0
    var mesh:=ArrayMesh.new()
    for surface_value in surfaces:
        var surface=surface_value as Dictionary
        var role=String(surface.get("surface_role",""))
        var material_id=String(surface.get("material_id",""))
        roles.append(role)
        material_ids.append(material_id)
        if role!=material_id:
            fail("segmented Building material role/id drift")
            return {}
        var triangles=surface.get("triangles",[]) as Array
        triangle_count+=triangles.size()
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for tri_value in triangles:
            var tri=tri_value as Array
            if tri.size()!=3:
                fail("segmented Building triangle arity drift")
                return {}
            for raw_index in tri:
                var index=int(raw_index)
                if index<0 or index>=vertices.size():
                    fail("segmented Building triangle index drift")
                    return {}
                st.add_vertex(gvec(vertices[index] as Array))
        st.generate_normals()
        st.commit(mesh)
        var surface_index=mesh.get_surface_count()-1
        mesh.surface_set_material(surface_index,building_material(surface))
    if roles!=SEGMENTED_EXPECTED_ROLES or triangle_count!=276:
        fail("segmented Building exact five-surface partition drift")
        return {}

    var node:=MeshInstance3D.new()
    node.name="source:building:service-pavilion-001"
    node.mesh=mesh
    root3d.add_child(node)
    return {
        "asset_id":"source:building:service-pavilion-001",
        "vertices":vertices.size(),
        "triangles":triangle_count,
        "surface_count":mesh.get_surface_count(),
        "material_ids":material_ids,
        "material_profile_sha256":String((proof.get("provenance",{}) as Dictionary).get("material_profile_sha256","")),
        "proof_culling":"CULL_DISABLED",
        "receiving_policy":String(proof.get("receiving_policy","")),
        "header_segmentation_revision":SEGMENTED_REVISION,
        "source_positive_volume_intersection_count":4,
        "successor_positive_volume_intersection_count":0,
    }

func add_static_sources(root3d:Node3D,data:Dictionary,cull_target_asset_id:String)->Array:
    var results:Array=[]
    for source_value in data.get("additional_source_meshes",[]) as Array:
        var source=source_value as Dictionary
        if String(source.get("asset_id",""))=="source:building:service-pavilion-001":
            fail("neutral Building source must not coexist with segmented material receiver")
            return []
        results.append(add_static_source(root3d,source,cull_target_asset_id))
    results.append(add_segmented_building(root3d,data))
    results.append(add_object_readability_dressing(root3d,data))
    return results
