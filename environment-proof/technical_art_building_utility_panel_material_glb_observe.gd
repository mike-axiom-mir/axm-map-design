extends SceneTree

const SCHEMA := "axm.technical-art-building-utility-panel-material-glb-target-host/v0.1"
const GLB_PATH := "res://generated/utility-panel-material-review-transport.glb"
const OUTPUT_PATH := "res://generated/technical-art-material-glb-target-host-receipt.json"

func sha256_bytes(data: PackedByteArray) -> String:
    var context := HashingContext.new()
    if context.start(HashingContext.HASH_SHA256) != OK:
        return ""
    if context.update(data) != OK:
        return ""
    return context.finish().hex_encode()

func vector3_rows(values: PackedVector3Array) -> Array:
    var rows: Array = []
    for v in values:
        rows.append([v.x, v.y, v.z])
    return rows

func vector2_rows(values: PackedVector2Array) -> Array:
    var rows: Array = []
    for v in values:
        rows.append([v.x, v.y])
    return rows

func int_rows(values: PackedInt32Array) -> Array:
    var rows: Array = []
    for v in values:
        rows.append(int(v))
    return rows

func find_mesh_instance(node: Node) -> MeshInstance3D:
    if node is MeshInstance3D:
        return node as MeshInstance3D
    for child in node.get_children():
        var found := find_mesh_instance(child)
        if found != null:
            return found
    return null

func write_receipt(data: Dictionary) -> void:
    var file := FileAccess.open(OUTPUT_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(data, "  ") + "\n")
        file.close()

func fail(message: String, extra := {}) -> void:
    var receipt := {
        "schema": SCHEMA,
        "state": "FAIL_TARGET_HOST_IMPORT",
        "failure": message,
        "promotion_effect": "NONE"
    }
    for key in extra:
        receipt[key] = extra[key]
    write_receipt(receipt)
    push_error(message)
    quit(1)

func _initialize() -> void:
    var document := GLTFDocument.new()
    var state := GLTFState.new()
    var error := document.append_from_file(GLB_PATH, state)
    if error != OK:
        fail("Godot GLTFDocument could not parse exact Technical Art carrier", {"error": error})
        return
    var root := document.generate_scene(state)
    if root == null:
        fail("Godot GLTFDocument could not generate a scene")
        return
    var mesh_instance := find_mesh_instance(root)
    if mesh_instance == null or mesh_instance.mesh == null:
        fail("generated scene lacks MeshInstance3D")
        return
    var mesh := mesh_instance.mesh
    if mesh.get_surface_count() != 1:
        fail("bounded carrier must import as exactly one mesh surface", {"surface_count": mesh.get_surface_count()})
        return
    var arrays := mesh.surface_get_arrays(0)
    if arrays.size() <= Mesh.ARRAY_INDEX:
        fail("imported surface arrays are incomplete")
        return
    var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
    var uvs: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
    var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
    if vertices.size() != 4 or uvs.size() != 4 or indices.size() != 6:
        fail("imported bounded carrier topology count drift", {
            "vertices": vertices.size(), "uvs": uvs.size(), "indices": indices.size()
        })
        return

    var material := mesh.surface_get_material(0)
    if material == null or not (material is BaseMaterial3D):
        fail("imported surface lacks BaseMaterial3D")
        return
    var base_material := material as BaseMaterial3D
    var texture := base_material.albedo_texture
    if texture == null:
        fail("imported material lacks albedo texture")
        return
    var image := texture.get_image()
    if image == null or image.is_empty():
        fail("imported albedo texture cannot be read back")
        return
    image.convert(Image.FORMAT_RGBA8)
    var rgba := image.get_data()
    var rgba_sha := sha256_bytes(rgba)
    if rgba_sha == "":
        fail("failed to hash imported RGBA8 image")
        return

    var receipt := {
        "schema": SCHEMA,
        "state": "PASS_TARGET_HOST_IMPORTED_MATERIAL_BEARING_GLB",
        "renderer": "Godot 4.7.2 GL Compatibility / Linux proof host",
        "source_glb": GLB_PATH,
        "mesh": {
            "surface_count": mesh.get_surface_count(),
            "vertex_count": vertices.size(),
            "uv_count": uvs.size(),
            "index_count": indices.size(),
            "positions": vector3_rows(vertices),
            "uvs": vector2_rows(uvs),
            "indices": int_rows(indices)
        },
        "material": {
            "class": base_material.get_class(),
            "metallic": base_material.metallic,
            "roughness": base_material.roughness,
            "cull_mode": base_material.cull_mode,
            "has_albedo_texture": true
        },
        "image": {
            "width": image.get_width(),
            "height": image.get_height(),
            "format": int(image.get_format()),
            "rgba8_bytes": rgba.size(),
            "rgba8_sha256": rgba_sha
        },
        "truth_boundary": "This receipt proves the exact bounded Technical Art GLB reaches Godot with a mesh, TEXCOORD_0, material binding and readable embedded image. It does not infer production material/culling policy, visual acceptance, runtime cost, Environment adoption, CANON or production readiness.",
        "promotion_effect": "NONE"
    }
    write_receipt(receipt)
    print(JSON.stringify(receipt, "  "))
    root.free()
    quit(0)
