#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
PASS_STATE="PASS_OBJECT_STATIC_BATCH_ELIGIBILITY_SUCCESSOR_CONTINUITY__HOLD_FRESH_RUNTIME_VISUAL_DEVICE"
PRIOR_RUNTIME_RESULT="PASS_OBJECT_CURRENT_WORLD_STATIC_COMPONENT_BATCHING__HOLD_ART_QA_TARGET_DEVICE_FUTURE_ARTICULATION"
SUCCESSOR_ANIMATION_RESULT="PASS_OBJECT_CURRENT_WORLD_OWNER_ANIMATION_WALLCLOCK_REBOUND_TO_TA_FC567_RECEIVER"
STABLE_PLAN_KEYS=["coordinate_conversion","duration_s","lid_component","object_source_sha256","sample_count","sample_rate_hz","samples","sequence_digest","sequence_id","stations"]
MAP_PROVENANCE_KEYS={"technical_art_head","inspected_current_uc_head"}
def fail(m): raise SystemExit(m)
def load(p):
    v=json.loads(Path(p).read_text())
    if not isinstance(v,dict): fail(f"expected JSON object: {p}")
    return v
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def canonical(v): return sha_bytes(json.dumps(v,sort_keys=True,separators=(",",":")).encode())
def moving_closure(m):
    comps=m.get("components"); req=m.get("required_moving_components")
    if not isinstance(comps,list) or not isinstance(req,list): fail("component map missing components or required_moving_components")
    moving={str(x) for x in req}; changed=True
    while changed:
        changed=False
        for row in comps:
            name=str(row.get("name","")); parent=row.get("parent")
            if parent is not None and str(parent) in moving and name not in moving:
                moving.add(name); changed=True
    return sorted(moving)
def semantic_map(m): return {k:v for k,v in m.items() if k not in MAP_PROVENANCE_KEYS}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--contract",required=True); ap.add_argument("--prior-runtime-root",required=True); ap.add_argument("--successor-animation-root",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args(); c=load(a.contract); prior=Path(a.prior_runtime_root); succ=Path(a.successor_animation_root)
    if c.get("schema")!="axm.runtime-object-static-batching-successor-continuity/v0.1": fail("contract schema drift")
    ps=load(prior/"SUMMARY.json"); ss=load(succ/"SUMMARY.json")
    pm_p=prior/"ta-parent"/"object-rigid-component-map.json"; sm_p=succ/"ta-parent"/"object-rigid-component-map.json"
    pp_p=prior/"ta-parent"/"object-motion-receiver-plan.json"; sp_p=succ/"ta-parent"/"object-motion-receiver-plan.json"
    pm,sm,pp,sp=map(load,[pm_p,sm_p,pp_p,sp_p])
    if ps.get("exact_head")!=c["prior_runtime_head"] or ps.get("result")!=PRIOR_RUNTIME_RESULT: fail("prior Runtime identity/result drift")
    if ss.get("exact_head")!=c["successor_animation_head"] or ss.get("result")!=SUCCESSOR_ANIMATION_RESULT: fail("successor Animation identity/result drift")
    if ss.get("technical_art_parent_head")!=c["successor_technical_art_head"] or ss.get("animation_head")!=c["owner_animation_head"]: fail("current Animation/TA provenance drift")
    if ss.get("predecessor_animation_evidence_head")!=c["successor_predecessor_animation_head"]: fail("successor predecessor Animation provenance drift")
    if ss.get("runtime_controller_accepted",True) or ss.get("target_device_performance_accepted",True): fail("Animation successor inflated Runtime/device authority")
    p_raw=pm_p.read_bytes(); s_raw=sm_p.read_bytes(); p_file=sha_bytes(p_raw); s_file=sha_bytes(s_raw)
    if p_file!=c["prior_component_map_file_sha256"] or s_file!=c["successor_component_map_file_sha256"]: fail("component-map file identity drift")
    if p_raw==s_raw: fail("provenance unexpectedly collapsed to historical component-map bytes")
    if pm.get("technical_art_head")!=c["prior_object_technical_art_head"] or sm.get("technical_art_head")!=c["successor_object_technical_art_head"]: fail("Object TA provenance drift")
    if pm.get("inspected_current_uc_head")!=c["prior_inspected_uc_head"] or sm.get("inspected_current_uc_head")!=c["successor_inspected_uc_head"]: fail("UC provenance drift")
    p_sem=semantic_map(pm); s_sem=semantic_map(sm); p_sem_sha=canonical(p_sem); s_sem_sha=canonical(s_sem)
    if p_sem!=s_sem or p_sem_sha!=c["expected_component_map_semantic_sha256"] or s_sem_sha!=c["expected_component_map_semantic_sha256"]: fail("component semantic payload drift")
    p_subset={k:pp.get(k) for k in STABLE_PLAN_KEYS}; s_subset={k:sp.get(k) for k in STABLE_PLAN_KEYS}
    p_subset_sha=canonical(p_subset); s_subset_sha=canonical(s_subset)
    if p_subset!=s_subset or p_subset_sha!=c["expected_stable_motion_subset_sha256"] or s_subset_sha!=c["expected_stable_motion_subset_sha256"]: fail("stable motion semantic subset drift")
    if pp.get("animation_head")!="c688936a84f80f292e43587c9d3386bd717f8178" or sp.get("animation_head")!=c["owner_animation_head"]: fail("motion-plan Animation provenance drift")
    if pp.get("object_technical_art_head")!=c["prior_object_technical_art_head"] or sp.get("object_technical_art_head")!=c["successor_object_technical_art_head"]: fail("motion-plan Object TA provenance drift")
    inv=sp.get("owner_target_motion_invariants")
    if not isinstance(inv,dict) or any(float(inv.get(k,-1.0))<0 for k in ("neutral_pivot_wrapper_max_drift_m","release_keeper_drift_m","release_min_lever_move_m","peak_min_keeper_move_m","endpoint_keeper_drift_m","endpoint_lever_drift_m")): fail("current owner invariants missing")
    comps=sm.get("components",[]); moving=moving_closure(sm); static=len(comps)-len(moving)
    if len(comps)!=c["expected_component_count"] or len(moving)!=c["expected_moving_component_count"] or static!=c["expected_static_component_count"]: fail("classification drift")
    if ps.get("moving_component_count")!=len(moving) or ps.get("static_component_count")!=static: fail("prior Runtime classification disagreement")
    if ps.get("candidate_render_surface_count")!=c["prior_measured_candidate_render_surface_count"]: fail("prior surface result drift")
    if ps.get("summary",{}).get("min_draw_calls_saved")!=c["prior_measured_min_draw_calls_saved"]: fail("prior draw result drift")
    if -int(ps.get("summary",{}).get("buffer_delta_min_bytes",0))!=c["prior_measured_buffer_bytes_saved"]: fail("prior buffer result drift")
    receipt={"schema":"axm.runtime-object-static-batching-successor-continuity-observation/v0.2","state":PASS_STATE,
      "prior_runtime_head":c["prior_runtime_head"],"prior_runtime_artifact_id":c["prior_runtime_artifact_id"],"successor_animation_head":c["successor_animation_head"],
      "successor_animation_artifact_id":c["successor_animation_artifact_id"],"successor_technical_art_head":c["successor_technical_art_head"],"owner_animation_head":c["owner_animation_head"],
      "owner_sequence_digest":c["owner_sequence_digest"],"component_map_semantic_sha256":s_sem_sha,"prior_component_map_file_sha256":p_file,"successor_component_map_file_sha256":s_file,
      "stable_motion_subset_sha256":s_subset_sha,"component_count":len(comps),"moving_component_count":len(moving),"moving_components":moving,"static_component_count":static,
      "classification_reuse_authorized":True,"provenance_changed_and_retained":True,"component_map_byte_identity_claimed":False,
      "prior_runtime_counter_transfer_authorized":False,"prior_visual_acceptance_transfer_authorized":False,"target_device_performance_accepted":False,
      "future_arbitrary_articulation_accepted":False,"art_qa_accepted":False,"canon":False,
      "prior_measured_candidate_render_surface_count":ps["candidate_render_surface_count"],"prior_measured_min_draw_calls_saved":ps["summary"]["min_draw_calls_saved"],
      "prior_measured_buffer_bytes_saved":-int(ps["summary"]["buffer_delta_min_bytes"]),"prior_visual_tradeoff":ps["visual_tradeoff"],
      "truth_boundary":"Semantic component geometry/parentage/material topology and exact owner motion semantics remain identical while producer identities changed. Only classification transfers; historical bytes/counters/visuals do not."}
    Path(a.output).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); print(PASS_STATE); print(json.dumps(receipt,sort_keys=True))
if __name__=="__main__": main()
