#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

PASS="PASS_CURRENT_WORLD_BUILDING_312_CONSUMER_EXACT_POSITION_QUOTIENT_REBIND"
HOLD="HOLD_DEFAULT_ADOPTION__SOURCE_HARD_NORMAL_IDENTITY_AND_TARGET_DEVICE_RUNTIME_REMAIN_SEPARATE"
QHEAD="7dfb1153dc5f80bcbf1b48803f044236d4ebb030"
PARENT="b9b4ab63e23b9756ab79597e86ecc41ea75ea8b7"
QSHA="7d9e0babf605e31ecb3e4edc92d06bd5460cf52a27f02ccbf32bbae44464688f"
PRIOR="55e10a4fa700fb81020a95bd5143deca6a09f208"
ROLLBACK="7713cbe5863c3bc38dabb6236eb4b393401224b6"
CONSUMER="map-consumer:service-pavilion-001:planar-role-post-normal-indexed-001"
WIDTH_SHA="8d61b2dc11f2508d186a1e469185badda7217803f7c4634fb2d951d8579c0dd5"
ROLE={"frame_galvanized":200,"infill_coating":24,"roof_membrane":36,"slab_mineral":36,"utility_panel_ochre":16}
IDX={"frame_galvanized":696,"infill_coating":96,"roof_membrane":72,"slab_mineral":72,"utility_panel_ochre":72}
PLACEMENT=(0.0,0.0,-7.2)

def load(p): return json.loads(Path(p).read_text())
def canon(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def qpos(v): return tuple(round(float(x),6) for x in v)
def gvec(v):
    x,y,z=(float(x) for x in v); return qpos((x,z,-y))
def placed(v):
    p=gvec(v); return qpos((p[0]+PLACEMENT[0],p[1]+PLACEMENT[1],p[2]+PLACEMENT[2]))
def building(sample):
    rows=[x for x in sample.get("static_source_meshes",[]) if x.get("asset_id")=="source:building:service-pavilion-001"]
    if len(rows)!=1: raise ValueError(f"expected one Building row, got {len(rows)}")
    return rows[0]

def verify(contract,evidence,quotient,prior,runtime,runtime_report,head):
    if contract.get("schema")!="axm.environment-building-planar-role-quotient-receiving/v0.1" or contract.get("owner")!="Map Environment / World Art": raise ValueError("contract identity drift")
    pins={"consumer_representation_id":CONSUMER,"geometry_quotient_head":QHEAD,"geometry_parent_head":PARENT,"geometry_quotient_sha256":QSHA,"prior_environment_head":PRIOR,"active_segmented_rollback_head":ROLLBACK}
    for k,v in pins.items():
        if contract.get(k)!=v: raise ValueError(f"contract pin drift: {k}")
    if contract.get("placement_translation_source_xyz_m")!=[0.0,7.2,0.0] or tuple(contract.get("placement_translation_godot_xyz_m",[]))!=PLACEMENT: raise ValueError("placement drift")
    for k in ("source_hard_normal_identity_preserved_by_consumer","consumer_generated_normals_are_source_normals","quotient_authorizes_source_collapse","environment_adoption"):
        if contract.get(k) is not False: raise ValueError(f"authority inflation: {k}")
    if contract.get("exact_position_partition_rebind") is not True or contract.get("review_target_only") is not True or contract.get("expected_role_vertex_counts")!=ROLE: raise ValueError("contract receiving scope drift")

    if evidence.get("schema")!="axm.building-planar-role-normal-boundary-quotient-evidence/v0.1" or evidence.get("result")!="PASS_HARD_NORMAL_IDENTITY_REMOVAL_YIELDS_EXACT_312_GROUP_STRUCTURAL_QUOTIENT" or evidence.get("exact_head")!=QHEAD or evidence.get("parent_geometry_head")!=PARENT or evidence.get("quotient_sha256")!=QSHA: raise ValueError("Geometry quotient evidence drift")
    if quotient.get("schema")!="axm.building-planar-role-normal-boundary-quotient/v0.1" or canon(quotient)!=QSHA: raise ValueError("Geometry quotient bytes/digest drift")
    m=evidence.get("metrics",{})
    expected={"parent_render_vertex_count":604,"diagnostic_quotient_group_count":312,"corner_index_count":1008,"triangle_count":336,"removed_source_vertex_identities":292,"hard_normal_crossing_group_count":188}
    for k,v in expected.items():
        if int(m.get(k,-1))!=v: raise ValueError(f"quotient metric drift: {k}")
    if m.get("per_role_quotient_group_count")!=ROLE or m.get("group_size_distribution")!={"1":124,"2":84,"3":104}: raise ValueError("quotient partition metric drift")
    exp={k:set() for k in ROLE}
    for g in quotient.get("groups",[]):
        role=g.get("material_role")
        if role not in exp or g.get("protected_split_id") is not None: raise ValueError("quotient role/split drift")
        p=placed(g.get("position",[]))
        if p in exp[role]: raise ValueError("duplicate quotient role+position")
        exp[role].add(p)
    if {k:len(v) for k,v in exp.items()}!=ROLE: raise ValueError("transformed quotient counts drift")

    if prior.get("state")!="PASS_CURRENT_WORLD_BUILDING_CONSUMER_IDENTITY_REBOUND_TO_SOURCE_SPLIT_POLICY" or prior.get("exact_environment_head")!=PRIOR or prior.get("consumer_representation_id")!=CONSUMER or prior.get("environment_adoption") is not False: raise ValueError("prior Environment identity drift")

    if runtime.get("runtime_building_planar_role_surface_indexing_result")!="CANDIDATE_INDEXED_AFTER_FINAL_NORMAL_GENERATION" or runtime.get("environment_building_planar_role_quotient_receiving_result")!="CANDIDATE_EXACT_POSITION_QUOTIENT_REBOUND" or runtime.get("environment_building_planar_role_quotient_geometry_head")!=QHEAD or runtime.get("environment_building_planar_role_consumer_id")!=CONSUMER or runtime.get("source_width_profile_digest")!=WIDTH_SHA: raise ValueError("current runtime provenance drift")
    samples=runtime.get("samples",[])
    if len(samples)!=17: raise ValueError("expected 17 current-world states")
    snapshot_sha=None; contexts=0; widths=0; max_weather=0.0
    for sample in samples:
        if sample.get("weather_width_profile_digest")!=WIDTH_SHA: raise ValueError("per-state Weather digest drift")
        b=building(sample)
        idx=b.get("runtime_building_planar_role_surface_indexing",{}).get("after",{})
        if (idx.get("surface_count"),idx.get("total_vertices"),idx.get("total_indices"),idx.get("total_primitives"))!=(5,312,1008,336): raise ValueError("consumer storage drift")
        rec=b.get("environment_building_planar_role_quotient_receiving",{})
        if rec.get("schema")!="axm.environment-building-planar-role-quotient-receiving-observation/v0.1" or rec.get("geometry_quotient_head")!=QHEAD or rec.get("consumer_representation_id")!=CONSUMER or rec.get("source_hard_normal_identity_preserved") is not False or rec.get("consumer_generated_normals_are_source_normals") is not False or rec.get("environment_adoption") is not False: raise ValueError("per-state quotient receipt drift")
        snap=rec.get("indexed_snapshot",{}); d=canon(snap)
        if snapshot_sha is None: snapshot_sha=d
        elif snapshot_sha!=d: raise ValueError("static indexed snapshot changed across dynamic states")
        seen={k:set() for k in ROLE}
        for s in snap.get("surfaces",[]):
            role=s.get("material_id")
            if role not in seen or len(s.get("vertices",[]))!=ROLE[role] or len(s.get("indices",[]))!=IDX[role]: raise ValueError(f"surface storage drift: {role}")
            for v in s.get("vertices",[]):
                p=qpos(v.get("position",[]))
                if p in seen[role] or len(v.get("normal",[]))!=3: raise ValueError(f"consumer position/normal drift: {role}")
                seen[role].add(p)
        for role in ROLE:
            if seen[role]!=exp[role]:
                raise ValueError(f"exact quotient/current-world partition mismatch: {role}; missing={sorted(exp[role]-seen[role])[:3]} extra={sorted(seen[role]-exp[role])[:3]}")
        for modes in sample.get("contexts",{}).values():
            contexts+=len(modes)
            w=modes.get("candidate",{}).get("weather_update",{})
            c=int(w.get("measured_width_count",-1)); r=float(w.get("maximum_projected_width_residual_px",999999))
            if c!=36 or r>0.05: raise ValueError("Weather width contract drift")
            widths+=c; max_weather=max(max_weather,r)
    if contexts!=68 or widths!=1224: raise ValueError("current-world observation cardinality drift")

    if runtime_report.get("state")!="PASS_BUILDING_PLANAR_ROLE_POST_NORMAL_INDEX_REMOVES_BUFFER_PENALTY__HOLD_PRIMITIVE_AND_VISUAL_REVIEW": raise ValueError("Runtime comparison state drift")
    after=runtime_report.get("building_representation",{}).get("after",{})
    if (after.get("total_vertices"),after.get("total_indices"),after.get("total_primitives"))!=(312,1008,336): raise ValueError("Runtime storage drift")
    delta=runtime_report.get("proof_host",{}).get("indexed_vs_active_delta_sets",{})
    if delta.get("buffer_mem_bytes")!=[-8304] or delta.get("primitives_in_frame")!=[180] or any(delta.get(k)!=[0] for k in ("draw_calls_in_frame","objects_in_frame","texture_mem_bytes")): raise ValueError("active-relative Runtime trade drift")
    vis=runtime_report.get("visuals",{})
    if vis.get("frame_count")!=68 or vis.get("changed_frame_count")!=68 or int(vis.get("max_changed_pixels",999999))>55 or int(vis.get("max_pixels_over_1_lsb",999999))!=0 or int(vis.get("max_channel_delta_lsb",999999))>1: raise ValueError("indexing raster boundary drift")

    return {
      "schema":"axm.environment-building-planar-role-quotient-receiving-rebind/v0.1","state":PASS,"hold":HOLD,"exact_environment_head":head,"consumer_representation_id":CONSUMER,
      "geometry_quotient":{"head":QHEAD,"parent_geometry_head":PARENT,"quotient_sha256":QSHA,"parent_source_intent_vertices":604,"quotient_groups":312,"removed_source_vertex_identities":292,"hard_normal_crossing_groups":188,"group_size_distribution":{"1":124,"2":84,"3":104},"per_role_group_counts":ROLE},
      "current_world_consumer":{"stored_vertices":312,"indices":1008,"triangles":336,"material_surfaces":5,"exact_role_position_partition_matches_geometry_quotient":True,"source_hard_normal_identity_preserved":False,"consumer_generated_normals_are_source_normals":False},
      "placement":{"source_xyz_m":[0.0,7.2,0.0],"godot_xyz_m":[0.0,0.0,-7.2]},"prior_environment_head":PRIOR,"active_segmented_rollback_head":ROLLBACK,"environment_adoption":False,
      "world_observations":{"state_count":17,"context_count":contexts,"weather_width_observation_count":widths,"maximum_weather_width_residual_px":max_weather,"static_indexed_snapshot_sha256":snapshot_sha,"role_vertex_counts":ROLE},
      "runtime_trade_space":{"indexed_vs_active_buffer_bytes":-8304,"indexed_vs_active_primitives":180,"max_indexing_changed_pixels_per_frame":int(vis["max_changed_pixels"]),"max_indexing_pixels_over_1_lsb":int(vis["max_pixels_over_1_lsb"]),"max_indexing_channel_delta_lsb":int(vis["max_channel_delta_lsb"])},
      "authority":contract.get("authority",{}),"truth_boundary":"The reviewed 312-vertex Godot Building receiver occupies exactly the same material-role + retained-placement position partition as the Geometry-owned 312-group quotient obtained by dropping only source hard-normal identity from the 604-vertex source-intent domain. This explains consumer storage; it does not preserve/recreate source hard normals, authorize source collapse, or adopt this receiver as default.",
      "four_root_gate":{"truth":"Exact quotient and current-world partition are separately pinned; lost source hard-normal identity remains explicit.","agency_non_domination":"Hard Surface owns source normals; Geometry owns quotient diagnosis; Environment owns receiving composition; Technical Art, Runtime and Art/QA keep their gates.","continuity":"The reviewed 312 consumer and active segmented rollback remain pinned; no scene art is rewritten.","wisdom_before_speed":"Explain the existing receiver partition before proposing another mesh or smoothing rewrite."}
    }

def main():
    ap=argparse.ArgumentParser()
    for n in ("contract","quotient-evidence","quotient-groups","prior-environment-report","runtime","runtime-report"): ap.add_argument("--"+n,type=Path,required=True)
    ap.add_argument("--exact-head",required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    out=verify(load(a.contract),load(a.quotient_evidence),load(a.quotient_groups),load(a.prior_environment_report),load(a.runtime),load(a.runtime_report),a.exact_head)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__": main()
