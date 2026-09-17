#!/usr/bin/env python3
"""Verify post-normal surface indexing for the exact current-world planar-role Building receiver."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

SCHEMA = "axm.runtime-building-planar-role-surface-index-budget/v0.1"
ENVIRONMENT_HEAD = "b758f9ca006ec5885ff1c2c52e2fb09e9ccdd464"
ACTIVE_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
HARD_SURFACE_HEAD = "93f22e4eeb9bb32516d4b11f8d8bcf47d9792910"
REPRESENTATION_ID = "boundary-only-planar-role-rectangle-render-001"
INDEX_SCHEMA = "axm.runtime-building-planar-role-surface-indexing-observation/v0.1"
ACTIVE_RUN = 35174899697
ACTIVE_ARTIFACT = 10478103666
UNINDEXED_RUN = 35182784756
UNINDEXED_ARTIFACT = 10481340680


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def runtime_path(root: Path) -> Path:
    for p in (root / "candidate" / "runtime.json", root / "runtime.json", root / "indexed" / "runtime.json"):
        if p.exists():
            return p
    raise FileNotFoundError(root)


def rendered_dir(root: Path) -> Path:
    for p in (root / "candidate" / "rendered", root / "rendered", root / "indexed" / "rendered"):
        if p.is_dir():
            return p
    raise FileNotFoundError(root)


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def runtime_rows(runtime: dict) -> dict[tuple[int,str,str],dict]:
    rows={}
    for sample in runtime.get("samples",[]):
        idx=int(sample["index"])
        for camera,modes in sample.get("contexts",{}).items():
            for mode,payload in modes.items():
                rows[(idx,camera,mode)]=payload["runtime"]
    return rows


def find_building(sample: dict) -> dict:
    rows=[r for r in sample.get("static_source_meshes",[]) if r.get("asset_id")=="source:building:service-pavilion-001"]
    if len(rows)!=1:
        raise ValueError(f"expected one Building row, got {len(rows)}")
    return rows[0]


def delta_sets(candidate: dict, reference: dict) -> dict:
    if set(candidate)!=set(reference):
        raise ValueError("runtime observation key drift")
    fields=("draw_calls_in_frame","objects_in_frame","primitives_in_frame","buffer_mem_bytes","texture_mem_bytes")
    out=[]
    for key in sorted(candidate):
        out.append({f:int(candidate[key][f])-int(reference[key][f]) for f in fields})
    return {f:sorted({r[f] for r in out}) for f in fields}


def image_delta(a_path: Path,b_path: Path)->dict:
    with Image.open(a_path).convert("RGB") as a, Image.open(b_path).convert("RGB") as b:
        if a.size!=b.size:
            raise ValueError("image size drift")
        diff=ImageChops.difference(a,b)
        bbox=diff.getbbox()
        changed=0; over_one=0; max_channel=0
        if bbox is not None:
            for px in diff.getdata():
                m=max(px)
                if m:
                    changed+=1; max_channel=max(max_channel,m)
                if m>1:
                    over_one+=1
        return {
            "byte_identical":bbox is None,
            "changed_pixels":changed,
            "pixels_over_1_lsb":over_one,
            "max_channel_delta_lsb":max_channel,
            "bbox":list(bbox) if bbox is not None else None,
            "sha256_a":sha256_file(a_path),
            "sha256_b":sha256_file(b_path),
        }


def verify(active_root:Path,unindexed_root:Path,indexed_root:Path,exact_head:str,output:Path)->None:
    active=load_json(runtime_path(active_root))
    unindexed=load_json(runtime_path(unindexed_root))
    indexed=load_json(runtime_path(indexed_root))
    if any(len(x.get("samples",[]))!=17 for x in (active,unindexed,indexed)):
        raise ValueError("expected 17 samples")
    if unindexed.get("environment_building_planar_role_representation_id")!=REPRESENTATION_ID:
        raise ValueError("unindexed planar-role identity drift")
    if indexed.get("environment_building_planar_role_representation_id")!=REPRESENTATION_ID:
        raise ValueError("indexed planar-role identity drift")
    if indexed.get("runtime_building_planar_role_surface_indexing_result")!="CANDIDATE_INDEXED_AFTER_FINAL_NORMAL_GENERATION":
        raise ValueError("index receipt marker missing")

    receipts=[]
    for sample in indexed["samples"]:
        row=find_building(sample)
        receipt=row.get("runtime_building_planar_role_surface_indexing",{})
        if receipt.get("schema")!=INDEX_SCHEMA:
            raise ValueError("index receipt schema drift")
        if receipt.get("building_hard_surface_head")!=HARD_SURFACE_HEAD or receipt.get("representation_id")!=REPRESENTATION_ID:
            raise ValueError("indexed donor identity drift")
        before=receipt["before"]; after=receipt["after"]
        if before.get("surface_count")!=5 or before.get("total_vertices")!=1008 or before.get("total_indices")!=0 or before.get("total_primitives")!=336:
            raise ValueError(f"unexpected unindexed storage {before}")
        if after.get("surface_count")!=5 or after.get("total_indices")!=1008 or after.get("total_primitives")!=336:
            raise ValueError(f"indexed identity drift {after}")
        if after.get("total_vertices",99999)>=1008:
            raise ValueError("indexing did not reduce stored vertices")
        receipts.append(receipt)
    first=receipts[0]
    if any(r["before"]!=first["before"] or r["after"]!=first["after"] for r in receipts[1:]):
        raise ValueError("storage changed across states")

    before=first["before"]; after=first["after"]
    modeled_before=int(before["total_vertices"])*24
    modeled_after=int(after["total_vertices"])*24+int(after["total_indices"])*4
    modeled_saved=modeled_before-modeled_after
    if modeled_saved<=0:
        raise ValueError("modeled payload did not reduce")

    active_rows=runtime_rows(active); un_rows=runtime_rows(unindexed); idx_rows=runtime_rows(indexed)
    if len(idx_rows)!=68:
        raise ValueError(f"expected 68 runtime observations, got {len(idx_rows)}")
    before_vs_active=delta_sets(un_rows,active_rows)
    idx_vs_un=delta_sets(idx_rows,un_rows)
    idx_vs_active=delta_sets(idx_rows,active_rows)

    if before_vs_active["buffer_mem_bytes"]!=[3600] or before_vs_active["primitives_in_frame"]!=[180]:
        raise ValueError(f"retained Environment before-measure drift: {before_vs_active}")
    for f in ("draw_calls_in_frame","objects_in_frame","texture_mem_bytes"):
        if before_vs_active[f]!=[0]:
            raise ValueError(f"before non-geometry drift {f}: {before_vs_active[f]}")
        if idx_vs_un[f]!=[0]:
            raise ValueError(f"indexing changed non-geometry counter {f}: {idx_vs_un[f]}")
    if idx_vs_un["primitives_in_frame"]!=[0]:
        raise ValueError(f"indexing changed primitive count: {idx_vs_un['primitives_in_frame']}")
    if max(idx_vs_un["buffer_mem_bytes"])>=0:
        raise ValueError(f"indexing did not reduce observed buffer memory: {idx_vs_un['buffer_mem_bytes']}")

    un_dir=rendered_dir(unindexed_root); idx_dir=rendered_dir(indexed_root)
    names=sorted(p.name for p in un_dir.glob("atmosphere-width-*.png"))
    if names!=sorted(p.name for p in idx_dir.glob("atmosphere-width-*.png")) or len(names)!=68:
        raise ValueError("frame-set drift")
    visuals={name:image_delta(un_dir/name,idx_dir/name) for name in names}
    changed=[name for name,row in visuals.items() if not row["byte_identical"]]
    max_pixels=max(r["changed_pixels"] for r in visuals.values())
    max_over_one=max(r["pixels_over_1_lsb"] for r in visuals.values())
    max_lsb=max(r["max_channel_delta_lsb"] for r in visuals.values())

    buffer_penalty_removed=max(idx_vs_active["buffer_mem_bytes"])<=0
    if buffer_penalty_removed:
        state="PASS_BUILDING_PLANAR_ROLE_POST_NORMAL_INDEX_REMOVES_BUFFER_PENALTY__HOLD_PRIMITIVE_AND_VISUAL_REVIEW"
    else:
        state="PASS_BUILDING_PLANAR_ROLE_POST_NORMAL_INDEX_REDUCES_BUFFER__HOLD_RESIDUAL_BUFFER_PRIMITIVE_AND_VISUAL_REVIEW"
    tradeoff=("NONE_OBSERVED__68_FRAMES_BYTE_IDENTICAL" if not changed else
              f"MEASURED_INDEXING_RENDER_DELTA__CHANGED_FRAMES_{len(changed)}__MAX_PIXELS_{max_pixels}__MAX_OVER_1_LSB_{max_over_one}__MAX_LSB_{max_lsb}__ART_QA_REVIEW_REQUIRED")

    report={
        "schema":SCHEMA,
        "state":state,
        "exact_runtime_head":exact_head,
        "environment_parent_head":ENVIRONMENT_HEAD,
        "active_parent_head":ACTIVE_HEAD,
        "representation_id":REPRESENTATION_ID,
        "comparison_artifacts":{
            "active":{"run":ACTIVE_RUN,"artifact":ACTIVE_ARTIFACT},
            "unindexed_planar_role":{"run":UNINDEXED_RUN,"artifact":UNINDEXED_ARTIFACT},
        },
        "building_representation":{
            "surface_count":5,"triangle_count":336,
            "before":before,"after":after,
            "stored_vertex_reduction":int(before["total_vertices"])-int(after["total_vertices"]),
            "stored_vertex_reduction_percent":round(100*(int(before["total_vertices"])-int(after["total_vertices"]))/int(before["total_vertices"]),9),
            "modeled_payload":"POSITION_FLOAT32x3_PLUS_NORMAL_FLOAT32x3_PLUS_UINT32_INDEX__PER_SURFACE",
            "modeled_before_bytes":modeled_before,"modeled_after_bytes":modeled_after,
            "modeled_saved_bytes":modeled_saved,
            "modeled_reduction_percent":round(100*modeled_saved/modeled_before,9),
        },
        "proof_host":{
            "observation_count":68,
            "unindexed_vs_active_delta_sets":before_vs_active,
            "indexed_vs_unindexed_delta_sets":idx_vs_un,
            "indexed_vs_active_delta_sets":idx_vs_active,
            "buffer_penalty_removed_vs_active":buffer_penalty_removed,
        },
        "visuals":{
            "frame_count":68,"changed_frame_count":len(changed),
            "max_changed_pixels":max_pixels,"max_pixels_over_1_lsb":max_over_one,
            "max_channel_delta_lsb":max_lsb,"tradeoff":tradeoff,
        },
        "decision":"POST_NORMAL_PER_SURFACE_INDEXING_IS_A_REAL_PLANAR_ROLE_STORAGE_WIN__PRIMITIVE_COST_AND_VISUAL_PREFERENCE_REMAIN_SEPARATE_GATES",
        "truth_boundary":"This proves only receiver storage/counter behavior for the exact Environment-reviewed planar-role Building on the pinned Godot proof host. It changes no semantic source, triangles, generated normals or material roles/scalars. No target-device CPU/GPU/FPS/VRAM/heap, Environment adoption, Art preference, collision/transport, CANON or production-readiness claim is made.",
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--active-root",type=Path,required=True)
    p.add_argument("--unindexed-root",type=Path,required=True)
    p.add_argument("--indexed-root",type=Path,required=True)
    p.add_argument("--exact-head",required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    verify(a.active_root,a.unindexed_root,a.indexed_root,a.exact_head,a.output)

if __name__=="__main__": main()
