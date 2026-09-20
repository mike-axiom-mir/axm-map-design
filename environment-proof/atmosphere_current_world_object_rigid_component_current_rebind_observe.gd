extends "res://atmosphere_current_world_building_utility_panel_clearance_observe.gd"

const RIGID_COMPONENT_MAP_PATH := "res://generated/object-rigid-component-map.json"
const RIGID_COMPONENT_STATE := "PASS_CURRENT_WORLD_OBJECT_RIGID_COMPONENT_BOUNDARY_NEUTRAL_EQUIVALENCE__ANIMATION_VFX_ADOPTION_HELD"
const RIGID_COMPONENT_RULE := "SOURCE_OWNED_RIGID_COMPONENT_BOUNDARIES_MAY_REPLACE_A_STATIC_RECEIVER_ONLY_WHEN_THE_EXISTING_MATERIAL_NORMAL_UV_AND_NEUTRAL_WORLD_IMAGE_IDENTITIES_REMAIN_EXACT"
const RIGID_COMPONENT_SCHEMA := "axm.environment-object-rigid-component-map/v0.1"
const RIGID_RECEIVER_OBSERVATION_SCHEMA := "axm.environment-object-rigid-component-receiver-observation/v0.1"
const EXACT_OBJECT_SOURCE_SHA256 := "49b1f9ed9865893d6de6f1ec8f069576732df694853fde4e3fcff366de32644a"
const EXACT_OBJECT_TA_HEAD := "b9848c62b2adde84e9e0afc219088113216799d6"
const HISTORICAL_OBJECT_TA_HEAD := "965fb2f24dbd0b0cbb748d9f8b8712d62966315f"
const REQUIRED_MOVING_COMPONENTS := ["lid_shell", "latch_0_lever", "latch_1_lever"]

func _ta_sha256_bytes(data:PackedByteArray)->String:
    var context:=HashingContext.new()
    if context.start(HashingContext.HASH_SHA256)!=OK:
        fail("Technical Art rigid component map SHA-256 initialization failed")
        return ""
    if context.update(data)!=OK:
        fail("Technical Art rigid component map SHA-256 update failed")
        return ""
    return context.finish().hex_encode()

func _load_rigid_component_map()->Dictionary:
    if not FileAccess.file_exists(RIGID_COMPONENT_MAP_PATH):
        fail("Technical Art rigid component map missing")
        return {}
    var bytes:=FileAccess.get_file_as_bytes(RIGID_COMPONENT_MAP_PATH)
    var parsed=JSON.parse_string(bytes.get_string_from_utf8())
    if not (parsed is Dictionary):
        fail("Technical Art rigid component map invalid JSON")
        return {}
    var component_map:=parsed as Dictionary
    if String(component_map.get("schema",""))!=RIGID_COMPONENT_SCHEMA:
        fail("Technical Art rigid component map schema drift")
        return {}
    if String(component_map.get("object_source_sha256",""))!=EXACT_OBJECT_SOURCE_SHA256:
        fail("Technical Art rigid component map source identity drift")
        return {}
    if String(component_map.get("technical_art_head",""))!=EXACT_OBJECT_TA_HEAD:
        fail("Technical Art rigid component map donor head drift")
        return {}
    if int(component_map.get("triangles",-1))!=812:
        fail("Technical Art rigid component map triangle count drift")
        return {}
    var components=component_map.get("components",[]) as Array
    if components.size()!=31:
        fail("Technical Art rigid component map component count drift")
        return {}
    var required=component_map.get("required_moving_components",[]) as Array
    if required!=REQUIRED_MOVING_COMPONENTS:
        fail("Technical Art rigid component map moving-boundary identity drift")
        return {}
    component_map["_file_sha256"]=_ta_sha256_bytes(bytes)
    return component_map

func _component_lookup(component_map:Dictionary)->Dictionary:
    var triangle_to_component:Dictionary={}
    var rows:Dictionary={}
    for raw in component_map.get("components",[]) as Array:
        var row=raw as Dictionary
        var name:=String(row.get("name",""))
        var first:=int(row.get("first_triangle",-1))
        var count:=int(row.get("triangle_count",-1))
        if name.is_empty() or rows.has(name) or first<0 or count<=0 or first+count>812:
            fail("Technical Art rigid component row drift")
            return {}
        rows[name]=row
        for tri in range(first,first+count):
            if triangle_to_component.has(tri):
                fail("Technical Art rigid component triangle overlap")
                return {}
            triangle_to_component[tri]=name
    if triangle_to_component.size()!=812:
        fail("Technical Art rigid component map does not cover exact 812 source triangles")
        return {}
    for tri in range(812):
        if not triangle_to_component.has(tri):
            fail("Technical Art rigid component map has a source triangle gap")
            return {}
    return {"triangle_to_component":triangle_to_component,"rows":rows}

func _localized_arrays(source_arrays:Array,subset:PackedInt32Array,localize:bool,pivot:Vector3)->Array:
    var arrays:=source_arrays.duplicate(true) as Array
    arrays[Mesh.ARRAY_INDEX]=subset
    if localize:
        var raw_positions=source_arrays[Mesh.ARRAY_VERTEX]
        if typeof(raw_positions)!=TYPE_PACKED_VECTOR3_ARRAY:
            fail("Technical Art rigid receiver requires PackedVector3Array positions")
            return []
        var source_positions:=raw_positions as PackedVector3Array
        var positions:=PackedVector3Array()
        positions.resize(source_positions.size())
        for index in range(source_positions.size()):
            positions[index]=source_positions[index]-pivot
        arrays[Mesh.ARRAY_VERTEX]=positions
    return arrays

func _build_component_receiver(parent_mesh:ArrayMesh,segmentation:Dictionary,component_map:Dictionary)->Dictionary:
    if parent_mesh.get_surface_count()!=7:
        fail("Technical Art rigid receiver requires exact seven-surface selected-roughness parent")
        return {}
    var segments=segmentation.get("segments",[]) as Array
    if segments.size()!=7:
        fail("Technical Art rigid receiver requires exact seven source-triangle segments")
        return {}
    var lookup:=_component_lookup(component_map)
    if lookup.is_empty():
        return {}
    var triangle_to_component=lookup["triangle_to_component"] as Dictionary
    var rows=lookup["rows"] as Dictionary
    var subsets:Dictionary={}
    var covered:=0
    for surface_index in range(parent_mesh.get_surface_count()):
        var arrays:=parent_mesh.surface_get_arrays(surface_index)
        if arrays.size()<=Mesh.ARRAY_INDEX:
            fail("Technical Art rigid receiver parent array layout drift")
            return {}
        var raw_indices=arrays[Mesh.ARRAY_INDEX]
        if typeof(raw_indices)!=TYPE_PACKED_INT32_ARRAY:
            fail("Technical Art rigid receiver requires exact indexed parent surfaces")
            return {}
        var indices:=raw_indices as PackedInt32Array
        var segment=segments[surface_index] as Dictionary
        var source_triangles=segment.get("source_triangle_indices",[]) as Array
        if source_triangles.size()*3!=indices.size():
            fail("Technical Art rigid receiver source-triangle/index correspondence drift")
            return {}
        for slot in range(source_triangles.size()):
            var source_triangle:=int(source_triangles[slot])
            if not triangle_to_component.has(source_triangle):
                fail("Technical Art rigid receiver source triangle has no component owner")
                return {}
            var component:=String(triangle_to_component[source_triangle])
            if not subsets.has(component):
                subsets[component]={}
            var by_surface=subsets[component] as Dictionary
            if not by_surface.has(surface_index):
                by_surface[surface_index]=PackedInt32Array()
            var subset=by_surface[surface_index] as PackedInt32Array
            subset.append(int(indices[slot*3+0]))
            subset.append(int(indices[slot*3+1]))
            subset.append(int(indices[slot*3+2]))
            by_surface[surface_index]=subset
            subsets[component]=by_surface
            covered+=1
    if covered!=812 or subsets.size()!=31:
        fail("Technical Art rigid receiver component partition cardinality drift")
        return {}

    var pivot_values=component_map.get("hinge_pivot_receiver_xyz_m",[]) as Array
    if pivot_values.size()!=3:
        fail("Technical Art rigid receiver hinge pivot arity drift")
        return {}
    var pivot:=Vector3(float(pivot_values[0]),float(pivot_values[1]),float(pivot_values[2]))
    var nodes:Dictionary={}
    var component_surface_instances:=0
    var emitted_triangles:=0
    for raw in component_map.get("components",[]) as Array:
        var row=raw as Dictionary
        var name:=String(row.get("name",""))
        if not subsets.has(name):
            fail("Technical Art rigid receiver component has no retained surface triangles: "+name)
            return {}
        var mesh:=ArrayMesh.new()
        var by_surface=subsets[name] as Dictionary
        var surface_indices:Array=by_surface.keys()
        surface_indices.sort()
        for raw_surface_index in surface_indices:
            var surface_index:=int(raw_surface_index)
            var subset=by_surface[surface_index] as PackedInt32Array
            if subset.size()==0 or subset.size()%3!=0:
                fail("Technical Art rigid receiver component surface index stream drift: "+name)
                return {}
            var parent_arrays:=parent_mesh.surface_get_arrays(surface_index)
            var localized:=bool(row.get("localized_to_hinge_pivot",false))
            var arrays:=_localized_arrays(parent_arrays,subset,localized,pivot)
            if arrays.is_empty():
                return {}
            mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
            var material:=parent_mesh.surface_get_material(surface_index)
            if material==null:
                fail("Technical Art rigid receiver lost parent material: "+name)
                return {}
            mesh.surface_set_material(mesh.get_surface_count()-1,material)
            component_surface_instances+=1
            emitted_triangles+=subset.size()/3
        var node:=MeshInstance3D.new()
        node.name=name
        node.mesh=mesh
        nodes[name]=node
    if emitted_triangles!=812 or nodes.size()!=31:
        fail("Technical Art rigid receiver emitted geometry count drift")
        return {}

    var lid=nodes.get("lid_shell") as MeshInstance3D
    if lid==null:
        fail("Technical Art rigid receiver lid_shell node missing")
        return {}
    lid.position=pivot
    var lid_edges:Array=[]
    for raw in component_map.get("components",[]) as Array:
        var row=raw as Dictionary
        var name:=String(row.get("name",""))
        var parent_value=row.get("parent")
        if parent_value!=null:
            var parent_name:=String(parent_value)
            if not nodes.has(parent_name):
                fail("Technical Art rigid receiver parent node missing: "+parent_name)
                return {}
            var parent_node=nodes[parent_name] as MeshInstance3D
            var child_node=nodes[name] as MeshInstance3D
            parent_node.add_child(child_node)
            lid_edges.append([parent_name,name])
    var container:=Node3D.new()
    container.name=OBJECT_ASSET_ID
    for raw in component_map.get("components",[]) as Array:
        var row=raw as Dictionary
        var name:=String(row.get("name",""))
        if row.get("parent")==null:
            container.add_child(nodes[name] as MeshInstance3D)
    if container.get_child_count()!=27:
        fail("Technical Art rigid receiver root component count drift")
        return {}
    for required in REQUIRED_MOVING_COMPONENTS:
        if not nodes.has(String(required)):
            fail("Technical Art rigid receiver required moving boundary missing")
            return {}
    return {
        "container":container,
        "observation":{
            "schema":RIGID_RECEIVER_OBSERVATION_SCHEMA,
            "state":RIGID_COMPONENT_STATE,
            "reusable_rule":RIGID_COMPONENT_RULE,
            "object_source_sha256":EXACT_OBJECT_SOURCE_SHA256,
            "technical_art_head":EXACT_OBJECT_TA_HEAD,
            "component_map_sha256":String(component_map.get("_file_sha256","")),
            "component_count":nodes.size(),
            "component_surface_instances":component_surface_instances,
            "triangles":emitted_triangles,
            "parent_selected_surface_count":parent_mesh.get_surface_count(),
            "hinge_pivot_receiver_xyz_m":[pivot.x,pivot.y,pivot.z],
            "lid_hierarchy_edges":lid_edges,
            "required_moving_components":REQUIRED_MOVING_COMPONENTS.duplicate(),
            "source_positions_reconstructed_at_neutral":true,
            "index_stream_partition_only":true,
            "materials_reused":true,
            "normals_reused":true,
            "uv0_reused":true,
            "selected_roughness_material_resources_reused":true,
            "animation_adoption":false,
            "vfx_adoption":false,
            "runtime_acceptance":false,
            "environment_adoption":false,
            "truth_boundary":"Technical Art receiving structure only. Exact Object-owned component ranges and lid ownership are consumed from the pinned Object Technical Art donor, while the current Map receiver's already-proven material objects, normals, UV0 and selected roughness are reused. Neutral geometry is reconstructed exactly. No animation sample, VFX particle, Runtime/device acceptance, Art/QA acceptance, gameplay, CANON or production promotion is made."
        }
    }

func add_static_source(root3d:Node3D,source:Dictionary,cull_target_asset_id:String)->Dictionary:
    var child_count_before:=root3d.get_child_count()
    var result:=super.add_static_source(root3d,source,cull_target_asset_id)
    if String(result.get("asset_id",""))!=OBJECT_ASSET_ID:
        return result
    if root3d.get_child_count()!=child_count_before+1:
        fail("Technical Art rigid receiver expected exactly one inherited Object child")
        return {}
    var emitted=root3d.get_child(root3d.get_child_count()-1)
    if not (emitted is MeshInstance3D):
        fail("Technical Art rigid receiver inherited Object child is not MeshInstance3D")
        return {}
    var inherited:=emitted as MeshInstance3D
    if not (inherited.mesh is ArrayMesh):
        fail("Technical Art rigid receiver inherited Object mesh is not ArrayMesh")
        return {}
    var segmentation=result.get("environment_object_selected_surface_segmentation",{}) as Dictionary
    if String(result.get("source_sha256",""))!=EXACT_OBJECT_SOURCE_SHA256:
        fail("Technical Art rigid receiver inherited Object source drift")
        return {}
    var component_map:=_load_rigid_component_map()
    if component_map.is_empty():
        return {}
    var built:=_build_component_receiver(inherited.mesh as ArrayMesh,segmentation,component_map)
    if built.is_empty():
        return {}
    root3d.remove_child(inherited)
    inherited.free()
    root3d.add_child(built["container"] as Node3D)
    result["environment_object_rigid_component_receiver"]=built["observation"]
    return result

func write_receipt()->void:
    receipt["technical_art_object_rigid_component_state"]=RIGID_COMPONENT_STATE
    receipt["technical_art_object_rigid_component_rule"]=RIGID_COMPONENT_RULE
    receipt["technical_art_object_rigid_component_source_sha256"]=EXACT_OBJECT_SOURCE_SHA256
    receipt["technical_art_object_rigid_component_donor_head"]=EXACT_OBJECT_TA_HEAD
    receipt["technical_art_object_rigid_component_historical_donor_head"]=HISTORICAL_OBJECT_TA_HEAD
    receipt["technical_art_object_rigid_component_historical_receipt_reused_as_current_evidence"]=false
    receipt["technical_art_object_rigid_component_animation_adoption"]=false
    receipt["technical_art_object_rigid_component_vfx_adoption"]=false
    receipt["technical_art_object_rigid_component_runtime_acceptance"]=false
    receipt["technical_art_object_rigid_component_truth_boundary"]="Fresh current-Object provenance rebind over the exact neutral receiver articulation boundary. Historical 965fb2 evidence remains historical only; fresh b9848c62 component identity is required. Source-owned rigid groups are exposed as transformable nodes while current Map materials/normals/UV/roughness remain receiver-owned. Animation/VFX application and Runtime/Art/QA/CANON acceptance remain held."
    super.write_receipt()
