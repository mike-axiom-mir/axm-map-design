from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_ENVIRONMENT_OBSERVER_BLOB_SHA = "05b9d7e84cadc065b21d5a7ea8009b9850bfcd25"

INSERT = r'''
func receiving_material_from_spec(spec:Dictionary)->StandardMaterial3D:
    var rgba:=spec["albedo"] as Array
    var material:=StandardMaterial3D.new()
    material.albedo_color=Color(float(rgba[0]),float(rgba[1]),float(rgba[2]),float(rgba[3]))
    material.metallic=float(spec["metallic"])
    material.roughness=float(spec["roughness"])
    material.cull_mode=BaseMaterial3D.CULL_DISABLED
    return material

func add_building_material_receiving(root3d:Node3D,data:Dictionary)->Dictionary:
    var proof=data["building_material_receiving"] as Dictionary
    var vertices=proof["vertices_source_xyz_m"] as Array
    var surfaces=proof["surfaces"] as Array
    var triangle_total:=0
    var material_ids:Array=[]
    var surface_roles:Array=[]
    for raw_surface in surfaces:
        var surface=raw_surface as Dictionary
        var triangles=surface["triangles"] as Array
        var st:=SurfaceTool.new()
        st.begin(Mesh.PRIMITIVE_TRIANGLES)
        for tri in triangles:
            var row=tri as Array
            st.add_vertex(gvec(vertices[int(row[0])] as Array))
            st.add_vertex(gvec(vertices[int(row[1])] as Array))
            st.add_vertex(gvec(vertices[int(row[2])] as Array))
        st.generate_normals()
        var mesh:=st.commit()
        var node:=MeshInstance3D.new()
        node.name="building-surface-%s" % String(surface["surface_role"])
        node.mesh=mesh
        node.material_override=receiving_material_from_spec(surface["material"] as Dictionary)
        root3d.add_child(node)
        triangle_total+=triangles.size()
        material_ids.append(String(surface["material_id"]))
        surface_roles.append(String(surface["surface_role"]))
    return {
        "asset_id":String(proof["asset_id"]),
        "mode":String(proof["mode"]),
        "vertices":vertices.size(),
        "triangles":triangle_total,
        "surface_count":surfaces.size(),
        "surface_roles":surface_roles,
        "material_ids":material_ids,
        "provenance":proof["provenance"],
        "proof_culling":String(proof.get("proof_render_culling",""))
    }
'''


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def patch(source: Path, output: Path) -> None:
    text = source.read_text(encoding="utf-8")
    observed = git_blob_sha(source)
    if observed != EXPECTED_ENVIRONMENT_OBSERVER_BLOB_SHA:
        raise SystemExit(f"Environment observer identity drift: {observed}")

    receipt_anchor = 'const RECEIPT := "res://environment-runtime-receipt.json"\n'
    receipt_replacement = 'const RECEIPT := "res://material-environment-runtime-receipt.json"\n'
    if text.count(receipt_anchor) != 1:
        raise SystemExit("receipt path anchor drift")
    text = text.replace(receipt_anchor, receipt_replacement)

    weather_anchor = "func add_weather(root3d:Node3D,data:Dictionary)->Dictionary:\n"
    if text.count(weather_anchor) != 1:
        raise SystemExit("weather anchor drift")
    text = text.replace(weather_anchor, INSERT + "\n" + weather_anchor)

    make_anchor = "    var additional_source_stats:=add_additional_source_meshes(root3d,data)\n    var weather_stats:=add_weather(root3d,data)\n"
    make_replacement = "    var additional_source_stats:=add_additional_source_meshes(root3d,data)\n    var building_material_stats:=add_building_material_receiving(root3d,data)\n    var weather_stats:=add_weather(root3d,data)\n"
    if text.count(make_anchor) != 1:
        raise SystemExit("viewport construction anchor drift")
    text = text.replace(make_anchor, make_replacement)

    return_anchor = '    return {"viewport":viewport,"sapling":sapling_stats,"additional_source_meshes":additional_source_stats,"weather":weather_stats,"camera":camera_data}\n'
    return_replacement = '    return {"viewport":viewport,"sapling":sapling_stats,"additional_source_meshes":additional_source_stats,"building_material_receiving":building_material_stats,"weather":weather_stats,"camera":camera_data}\n'
    if text.count(return_anchor) != 1:
        raise SystemExit("viewport result anchor drift")
    text = text.replace(return_anchor, return_replacement)

    result_anchor = '        "additional_source_meshes":setup["additional_source_meshes"],\n        "weather":setup["weather"],\n'
    result_replacement = '        "additional_source_meshes":setup["additional_source_meshes"],\n        "building_material_receiving":setup["building_material_receiving"],\n        "weather":setup["weather"],\n'
    if text.count(result_anchor) != 1:
        raise SystemExit("capture result anchor drift")
    text = text.replace(result_anchor, result_replacement)

    state_anchor = '    receipt["state"]="PASS_TARGET_HOST_ENVIRONMENT_OBSERVATION_READY"\n'
    if text.count(state_anchor) != 1:
        raise SystemExit("receipt state anchor drift")
    text = text.replace(state_anchor, '    receipt["state"]="PASS_TARGET_HOST_BUILDING_MATERIAL_RECEIVING_READY"\n')

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="environment-proof/observe.gd")
    parser.add_argument("--output", default="material-environment-proof/observe.gd")
    args = parser.parse_args()
    patch(Path(args.source), Path(args.output))
    print(f"patched {args.source} -> {args.output}")
