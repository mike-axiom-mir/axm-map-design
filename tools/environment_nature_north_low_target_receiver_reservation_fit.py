from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
import numpy as np

SCHEMA='axm.environment-nature-north-low-target-receiver-reservation-fit/v0.3'
RESULT='PASS_CURRENT_WORLD_NATURE_NORTH_LOW_CURRENT_OWNER_TARGET_RECEIVER_ENVELOPE_FITS_EXISTING_EAST_REAR_RESERVATION__ART_RUNTIME_FINAL_ADOPTION_HELD'
RULE='TARGET_HOST_MOTION_MAY_BE_SPATIALLY_RECEIVED_ONLY_AFTER_EXACT_TARGET_RECEIVER_GEOMETRY_OWNER_SAMPLES_AND_TRANSPORT_TOLERANCE_ARE_COMPOSED_WITH_CURRENT_MULTI_ASSET_GUARDS__SPATIAL_FIT_DOES_NOT_TRANSFER_VISUAL_RUNTIME_OR_CANON_AUTHORITY'
TARGET_ASSET='source:nature:east-rear-tree-neutral-001'
EXPECTED_MESH='aa9d450a78fef722672ea9af0f9aca98b4c1a0ca3705661784f5f61f3e9b6a31'
EXPECTED_TA_HEAD='02c5223dd9288c12607f0553e2f1103be38ae71f'
EXPECTED_ANIM='5cacd61e22433b0c33f29111827283b81cc0ba0d'
EXPECTED_RIG='69640e558f0c1ac59d4d0e3155676e0967a03d04'
EXPECTED_UC='7ddefca57b153fab02c1f54f38de22148cb52c1b'
EXPECTED_TARGET_STATE='PASS_NATURE_NORTH_LOW_PARENT_EXCLUSION_CURRENT_UC_GODOT_TARGET'
EXPECTED_PREV_ENV='PASS_CURRENT_WORLD_NATURE_SHARED_DRIVER_SIMULTANEOUS_SAMPLED_SWEEP_FITS_EXISTING_EAST_REAR_RESERVATION__TARGET_HOST_VISUAL_WIND_RUNTIME_ADOPTION_HELD'
EXPECTED_CURRENT_WORLD='PASS_CURRENT_WORLD_BUILDING_UTILITY_PANEL_CLEARANCE_SUCCESSOR_ART_DIRECTION_PROVENANCE_CONVERGENCE__NO_WORLD_RERENDER_REQUIRED__RUNTIME_CLOSE_RANGE_FINAL_ADOPTION_HELD'
TOL=1e-6

def read_json(p: Path)->dict[str,Any]: return json.loads(p.read_text(encoding='utf-8'))
def sha256(p: Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def bounds(v):
    a=np.asarray(v,float); return a.min(axis=0),a.max(axis=0)

def build_report(contract, env, world, prior, art, *, left_contraction_m=0.0, claim_visual=False):
    if contract.get('schema')!=SCHEMA: raise AssertionError('Environment target-receiver contract schema drift')
    if claim_visual: raise AssertionError('spatial target-receiver fit cannot claim visual acceptance')
    if left_contraction_m<0: raise AssertionError('negative reservation contraction is invalid')
    if env.get('schema')!='axm.environment-derived-nature-target-envelope/v0.1': raise AssertionError('target-envelope fixture schema drift')
    src=env.get('source_artifact',{})
    if src.get('technical_art_head')!=EXPECTED_TA_HEAD or src.get('artifact_id')!=10542513318 or src.get('artifact_sha256')!='7b991dfd749ac758ece3c2c6ea320d10cfed5ff38c822c7ed88342461226a932':
        raise AssertionError('exact Technical Art artifact identity drift')
    chain=env.get('exact_owner_chain',{})
    if chain.get('animation_head')!=EXPECTED_ANIM or chain.get('rigging_head')!=EXPECTED_RIG or chain.get('uc_head')!=EXPECTED_UC:
        raise AssertionError('current Nature owner chain drift')
    tr=env.get('target_receipt',{})
    if tr.get('state')!=EXPECTED_TARGET_STATE or tr.get('godot_version')!='4.7.2-stable (official)': raise AssertionError('exact Godot target receipt drift')
    if tr.get('receiver_nodes_verified')!=12 or tr.get('receiver_triangles')!=620 or tr.get('samples_verified')!=41 or tr.get('visible_repeat_samples')!=40:
        raise AssertionError('target receiver structural/sample identity drift')
    if not env.get('uc_receiver',{}).get('binary_geometry_payload_identical_through_uc_graph_rebind'):
        raise AssertionError('UC target receiver no longer proves binary geometry continuity')
    if env.get('uc_receiver',{}).get('rigid_glb_sha256')!=tr.get('receiver_glb_sha256'):
        raise AssertionError('target receipt GLB identity no longer matches UC receiver')
    target_tol=float(tr.get('position_tolerance_m',-1))
    if not (0 < target_tol <= 5e-6+1e-12): raise AssertionError('target transport tolerance widened')
    if float(tr.get('maximum_target_sample_position_residual_m',1))>target_tol: raise AssertionError('target transport receipt is outside tolerance')
    if prior.get('result')!=EXPECTED_PREV_ENV: raise AssertionError('previous Environment source-motion reservation proof missing')
    if prior.get('decision',{}).get('target_host_acceptance') is not False: raise AssertionError('previous source pass history was silently promoted')
    if art.get('result')!=EXPECTED_CURRENT_WORLD or art.get('current_world_reused_without_rerender') is not True:
        raise AssertionError('latest current-world semantic convergence receipt missing')
    if art.get('multi_asset_world_scope_retained')!=['Building','Object','Nature','Weather','Environment dressing']:
        raise AssertionError('current multi-asset world scope drift')

    states=world.get('states',[])
    if len(states)!=17: raise AssertionError('current world must retain exact 17 Weather states')
    scene0=states[0]['scene']
    rows=[r for r in scene0.get('additional_source_meshes',[]) if r.get('asset_id')==TARGET_ASSET]
    if len(rows)!=1: raise AssertionError('current world must contain exactly one east-rear Nature receiver')
    row=rows[0]
    if row.get('mesh_digest')!=EXPECTED_MESH or len(row.get('vertices_source_xyz_m',[]))!=390 or len(row.get('triangles',[]))!=570:
        raise AssertionError('current world east-rear Nature receiver identity drift')
    world_min,world_max=bounds(row['vertices_source_xyz_m'])
    samples=env.get('samples',[])
    if len(samples)!=41 or [int(x['index']) for x in samples]!=list(range(41)): raise AssertionError('exact target sample envelope sequence drift')
    neutral=samples[0]
    nmin=np.asarray(neutral['source_xyz_bounds_min_m'],float); nmax=np.asarray(neutral['source_xyz_bounds_max_m'],float)
    if np.max(np.abs((world_max-world_min)-(nmax-nmin)))>TOL:
        raise AssertionError('current world receiver size drift from exact target receiver neutral geometry')
    tmin=world_min-nmin; tmax=world_max-nmax
    if np.max(np.abs(tmin-tmax))>TOL: raise AssertionError('current world target receiver is not a pure translation of exact target neutral geometry')
    translation=(tmin+tmax)*0.5

    repl=scene0.get('environment_rear_tree_replacement',{})
    if repl.get('target_asset_id')!='proxy:nature-tree-east-a' or repl.get('placement_policy')!='PRESERVE_TARGET_CENTER_XY__GROUND_SOURCE_MIN_Z__NO_FORM_SCALE__NO_EXTRA_ROTATION':
        raise AssertionError('east-rear Environment reservation/placement identity drift')
    reserved=[float(v) for v in repl.get('reserved_proxy_footprint_m',[])]
    if len(reserved)!=4: raise AssertionError('east-rear reservation footprint missing')
    reserved[0]+=left_contraction_m
    height=float(repl.get('reserved_proxy_size_m',[0,0,-1])[2])
    for state in states[1:]:
        sc=state['scene']; rr=[r for r in sc.get('additional_source_meshes',[]) if r.get('asset_id')==TARGET_ASSET]
        if len(rr)!=1 or rr[0]!=row: raise AssertionError('east-rear Nature receiver drift across Weather states')
        if sc.get('environment_rear_tree_replacement',{})!=scene0.get('environment_rear_tree_replacement',{}): raise AssertionError('east-rear reservation drift across Weather states')

    union_min=np.array([np.inf]*3); union_max=np.array([-np.inf]*3)
    min_margin=np.inf; min_nong=np.inf; min_ground=np.inf; witness=None; rowsout=[]
    for s in samples:
        raw_min=np.asarray(s['source_xyz_bounds_min_m'],float)+translation
        raw_max=np.asarray(s['source_xyz_bounds_max_m'],float)+translation
        pmin=raw_min-target_tol; pmax=raw_max+target_tol
        union_min=np.minimum(union_min,pmin); union_max=np.maximum(union_max,pmax)
        margins=[float(pmin[0]-reserved[0]),float(reserved[1]-pmax[0]),float(pmin[1]-reserved[2]),float(reserved[3]-pmax[1]),float(pmin[2]),float(height-pmax[2])]
        local=min(margins); nong=min(margins[0],margins[1],margins[2],margins[3],margins[5]); ground=margins[4]
        rr={'sample_index':int(s['index']),'time_s':float(s['time_s']),'north_low_child_angle_deg':float(s['north_low_child_angle_deg']),'target_receiver_angle_deg':float(s['target_receiver_angle_deg']),'transport_tolerance_expanded_world_bounds_min_m':pmin.tolist(),'transport_tolerance_expanded_world_bounds_max_m':pmax.tolist(),'reservation_margins_left_right_front_rear_ground_top_m':margins}
        rowsout.append(rr)
        min_margin=min(min_margin,local); min_ground=min(min_ground,ground)
        if nong<min_nong: min_nong=nong; witness=rr
    if min_nong < -TOL: raise AssertionError(f'exact current target receiver escapes existing non-ground Environment reservation: {min_nong:.9f} m')
    if min_ground < -(target_tol+TOL): raise AssertionError(f'target receiver ground residual exceeds bounded transport tolerance: {min_ground:.9f} m')

    path_gap=float(union_min[0]-float(scene0['readable_path']['x_max']))
    building_gap=float(scene0['environment_building_replacement']['source_world_footprint_m'][2]-union_max[1])
    compact_gap=float(union_min[1]-scene0['environment_replacement']['source_world_footprint_m'][3])
    object_gap=float(union_min[0]-scene0['environment_object_replacement']['source_world_footprint_m'][1])
    if min(path_gap,building_gap,compact_gap,object_gap)<=0: raise AssertionError('target receiver envelope crosses current-world multi-asset composition guard')

    return {
      'schema':SCHEMA,'result':RESULT,'reusable_rule':RULE,
      'exact_inputs':{'environment_predecessor_head':contract['environment']['predecessor_head'],'current_world_pr51_head':contract['environment']['current_world_pr51_head'],'technical_art_head':EXPECTED_TA_HEAD,'animation_head':EXPECTED_ANIM,'rigging_head':EXPECTED_RIG,'uc_head':EXPECTED_UC,'target_artifact_id':10542513318,'target_artifact_sha256':src['artifact_sha256'],'target_receiver_glb_sha256':tr['receiver_glb_sha256']},
      'current_world':{'weather_states_retained':17,'multi_asset_scope':art['multi_asset_world_scope_retained'],'east_rear_translation_xyz_m':translation.tolist(),'environment_reservation_xy_m':reserved,'environment_reserved_height_m':height},
      'target_receiver_sweep':{'samples_evaluated':41,'receiver_nodes':12,'receiver_triangles':620,'godot_version':tr['godot_version'],'transport_position_tolerance_m':target_tol,'maximum_observed_target_sample_residual_m':tr['maximum_target_sample_position_residual_m'],'minimum_transport_adjusted_reservation_margin_m':float(min_margin),'minimum_transport_adjusted_non_ground_margin_m':float(min_nong),'minimum_non_ground_witness':witness,'minimum_transport_adjusted_ground_margin_m':float(min_ground),'union_transport_adjusted_world_bounds_min_m':union_min.tolist(),'union_transport_adjusted_world_bounds_max_m':union_max.tolist()},
      'current_world_separation_guards':{'readable_path_x_separation_m':path_gap,'building_y_separation_m':building_gap,'compact_east_nature_y_separation_m':compact_gap,'articulated_object_x_separation_m':object_gap},
      'decision':{'spatial_receive_ready_for_exact_current_target_receiver':True,'world_scene_changed':False,'tree_placement_changed':False,'reservation_changed':left_contraction_m!=0.0,'visual_acceptance':False,'runtime_target_device_acceptance':False,'environment_adoption':False,'canon':False},
      'truth_boundary':'PASS combines the exact current Technical Art target receiver geometry/sample envelope and bounded Godot transport tolerance with the unchanged current multi-asset world reservation. It establishes spatial receiving readiness only. No new shaded world render was made, and Art/QA visual acceptance, natural wind, Runtime/device performance, connected skinning, collision/navigation, CANON and production readiness do not transfer.'
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--contract',type=Path,required=True); ap.add_argument('--target-envelope',type=Path,required=True); ap.add_argument('--combined-world',type=Path,required=True); ap.add_argument('--prior-environment-report',type=Path,required=True); ap.add_argument('--current-world-report',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--reservation-left-contraction-m',type=float,default=0.0); ap.add_argument('--claim-visual-acceptance',action='store_true'); args=ap.parse_args()
    c=read_json(args.contract)
    if sha256(args.target_envelope)!=c.get('target_envelope_fixture',{}).get('sha256'): raise AssertionError('target-envelope fixture digest drift')
    r=build_report(c,read_json(args.target_envelope),read_json(args.combined_world),read_json(args.prior_environment_report),read_json(args.current_world_report),left_contraction_m=args.reservation_left_contraction_m,claim_visual=args.claim_visual_acceptance)
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps({'result':r['result'],'minimum_non_ground_margin_m':r['target_receiver_sweep']['minimum_transport_adjusted_non_ground_margin_m'],'guards':r['current_world_separation_guards']},indent=2))
if __name__=='__main__': main()
