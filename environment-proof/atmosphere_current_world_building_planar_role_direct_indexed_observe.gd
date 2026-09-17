extends "res://atmosphere_current_world_building_planar_role_observe.gd"

const RUNTIME_DIRECT_INDEX_SCHEMA := "axm.runtime-building-planar-role-direct-indexed-receiver/v0.1"
const RUNTIME_DIRECT_INDEX_MODE := "DIRECT_FINAL_POSITION_NORMAL_INDEX_ARRAYS"

func _cardinal_normal(a:Vector3,b:Vector3,c:Vector3)->Vector3:
    var cross:Vector3=(b-a).cross(c-a)
    if cross.length_squared()<=1e-18:
        return Vector3.ZERO
    var n:=cross.normalized()
    var ax:=absf(n.x)
    var ay:=absf(n.y)
    var az:=absf(n.z)
    if ax>=ay and ax>=az and ay<=1e-6 and az<=1e-6:
        return Vector3(1.0 if n.x>0.0 else -1.0,0.0,0.0)
    if ay>=ax and ay>=az and ax<=1e-6 and az<=1e-6:
        return Vector3(0.0,1.0 if n.y>0.0 else -1.0,0.0)
    if az>=ax and az>=ay and ax<=1e-6 and ay<=1e-6:
        return Vector3(0.0,0.0,1.0 if n.z>0.0 else -1.0)
    return Vector3.ZERO

func _normal_code(n:Vector3)->float:
    if n.x>0.5: return 1.0
    if n.x<-0.5: return -1.0
    if n.y>0.5: return 2.0
    if n.y<-0.5: return -2.0
    if n.z>0.5: return 3.0
    if n.z<-0.5: return -3.0
    return 0.0

func _add_direct_surface(mesh:ArrayMesh,vertices:Array,surface:Dictionary)->Dictionary:
    var triangles:=surface.get("triangles",[]) as Array
    var packed_vertices:=PackedVector3Array()
    var packed_normals:=PackedVector3Array()
    var packed_indices:=PackedInt32Array()
    var lookup:Dictionary={}
    for tri_value in triangles:
        var tri:=tri_value as Array
        if tri.size()!=3:
            fail("Runtime direct-indexed Building triangle arity drift")
            return {}
        var source_indices:Array[int]=[]
        var points:Array[Vector3]=[]
        for raw_index in tri:
            var index:=int(raw_index)
            if index<0 or index>=vertices.size():
                fail("Runtime direct-indexed Building triangle index drift")
                return {}
            source_indices.append(index)
            points.append(gvec(vertices[index] as Array))
        var normal:=_cardinal_normal(points[0],points[1],points[2])
        var normal_code:=_normal_code(normal)
        if normal_code==0.0:
            fail("Runtime direct-indexed Building expected exact cardinal face normal")
            return {}
        for point in points:
            var key:=Vector4(point.x,point.y,point.z,normal_code)
            var final_index:int
            if lookup.has(key):
                final_index=int(lookup[key])
            else:
                final_index=packed_vertices.size()
                lookup[key]=final_index
                packed_vertices.append(point)
                packed_normals.append(normal)
            packed_indices.append(final_index)
    var arrays:Array=[]
    arrays.resize(Mesh.ARRAY_MAX)
    arrays[Mesh.ARRAY_VERTEX]=packed_vertices
    arrays[Mesh.ARRAY_NORMAL]=packed_normals
    arrays[Mesh.ARRAY_INDEX]=packed_indices
    mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
    return {
        "stored_vertices":packed_vertices.size(),
        "indices":packed_indices.size(),
        "triangles":packed_indices.size()/3,
    }

func add_segmented_building(root3d:Node3D,data:Dictionary)->Dictionary:
    var started_usec:=Time.get_ticks_usec()
    var proof:=data.get("environment_building_material_receiving",{}) as Dictionary
    if String(proof.get("asset_id",""))!="source:building:service-pavilion-001":
        fail("Runtime direct-indexed Building missing exact planar-role receiving payload")
        return {}
    var receiving:=proof.get("environment_building_planar_role_receiving",{}) as Dictionary
    if String(receiving.get("schema",""))!=BUILDING_PLANAR_RECEIVING_SCHEMA:
        fail("Runtime direct-indexed Building receiving schema drift")
        return {}
    if String(receiving.get("hard_surface_head",""))!=BUILDING_PLANAR_HARD_SURFACE_HEAD:
        fail("Runtime direct-indexed Building Hard-Surface head drift")
        return {}
    if String(receiving.get("materials_head",""))!=BUILDING_PLANAR_MATERIALS_HEAD:
        fail("Runtime direct-indexed Building Materials head drift")
        return {}
    if String(receiving.get("selected_representation_id",""))!=BUILDING_PLANAR_REPRESENTATION_ID:
        fail("Runtime direct-indexed Building representation drift")
        return {}
    if bool(receiving.get("environment_adoption",true)):
        fail("Runtime direct-indexed Building unexpectedly claims Environment adoption")
        return {}

    var vertices:=proof.get("vertices_source_xyz_m",[]) as Array
    var surfaces:=proof.get("surfaces",[]) as Array
    if vertices.size()!=672 or surfaces.size()!=5:
        fail("Runtime direct-indexed Building payload cardinality drift")
        return {}

    var mesh:=ArrayMesh.new()
    var roles:Array=[]
    var material_ids:Array=[]
    var total_stored_vertices:=0
    var total_indices:=0
    var total_triangles:=0
    var surface_metrics:Array=[]
    for surface_value in surfaces:
        var surface:=surface_value as Dictionary
        var role:=String(surface.get("surface_role",""))
        var material_id:=String(surface.get("material_id",""))
        roles.append(role)
        material_ids.append(material_id)
        if role!=material_id:
            fail("Runtime direct-indexed Building material role/id drift")
            return {}
        var metric:=_add_direct_surface(mesh,vertices,surface)
        if metric.is_empty():
            return {}
        var surface_index:=mesh.get_surface_count()-1
        mesh.surface_set_material(surface_index,building_material(surface))
        total_stored_vertices+=int(metric["stored_vertices"])
        total_indices+=int(metric["indices"])
        total_triangles+=int(metric["triangles"])
        metric["surface_role"]=role
        surface_metrics.append(metric)

    if roles!=BUILDING_PLANAR_ROLES or total_triangles!=336:
        fail("Runtime direct-indexed Building five-role/triangle identity drift")
        return {}
    if total_stored_vertices!=312 or total_indices!=1008:
        fail("Runtime direct-indexed Building final storage identity drift")
        return {}

    var node:=MeshInstance3D.new()
    node.name="source:building:service-pavilion-001"
    node.mesh=mesh
    root3d.add_child(node)
    var elapsed_usec:=int(Time.get_ticks_usec()-started_usec)
    return {
        "asset_id":"source:building:service-pavilion-001",
        "vertices":vertices.size(),
        "triangles":total_triangles,
        "surface_count":mesh.get_surface_count(),
        "material_ids":material_ids,
        "proof_culling":"CULL_DISABLED",
        "receiving_policy":String(proof.get("receiving_policy","")),
        "representation_id":BUILDING_PLANAR_REPRESENTATION_ID,
        "planar_role_hard_surface_head":BUILDING_PLANAR_HARD_SURFACE_HEAD,
        "planar_role_materials_head":BUILDING_PLANAR_MATERIALS_HEAD,
        "runtime_building_prepare_usec":elapsed_usec,
        "runtime_building_prepare_mode":RUNTIME_DIRECT_INDEX_MODE,
        "runtime_building_direct_indexed":{
            "schema":RUNTIME_DIRECT_INDEX_SCHEMA,
            "surface_count":mesh.get_surface_count(),
            "stored_vertices":total_stored_vertices,
            "indices":total_indices,
            "triangles":total_triangles,
            "source_payload_vertices":vertices.size(),
            "surface_metrics":surface_metrics,
            "truth_boundary":"Direct final position+cardinal-normal+index ArrayMesh construction for the exact Environment-reviewed planar-role Building only. Same five source material roles/scalars, 336 triangles, transform and current-world inputs; no UV/tangent/color/skin/morph/custom-channel inference and no default adoption."
        }
    }

func write_receipt()->void:
    receipt["runtime_building_direct_indexed_schema"]=RUNTIME_DIRECT_INDEX_SCHEMA
    receipt["runtime_building_direct_indexed_mode"]=RUNTIME_DIRECT_INDEX_MODE
    receipt["runtime_building_direct_indexed_result"]="CANDIDATE_DIRECT_FINAL_ARRAY_RECEIVER"
    receipt["runtime_building_direct_indexed_truth_boundary"]="This candidate skips the control's temporary unindexed triangle-corner mesh plus generate_normals/create_from/index rewrite and instead emits the exact final seam/material-domain position+cardinal-normal+index arrays directly. It is a receiver/import-preparation experiment, not source or Environment adoption."
    super.write_receipt()
