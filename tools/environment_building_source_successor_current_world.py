from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json
from pathlib import Path

SCHEMA='axm.environment-current-world-building-source-successor-evidence/v0.1'
STATUS='PASS_CURRENT_WORLD_BUILDING_SOURCE_SUCCESSOR_STRUCTURE'
BASE_SCHEMA='axm.environment-current-world-building-material-convergence-evidence/v0.1'
BASE_STATUS='PASS_CURRENT_WORLD_BUILDING_MATERIAL_CONVERGENCE_STRUCTURE'
OBS_SCHEMA='axm.environment-current-world-weather-variant-evidence/v0.1'
OBS_STATUS='PASS_CURRENT_WORLD_WEATHER_VARIANT_REBIND_STRUCTURE'
BUILDING='source:building:service-pavilion-001'
SOURCE_SCHEMA='axm.building-hard-surface/v0.2'
SOURCE_REV='service-pavilion-001/closed-outward-box-shells-002'
TOPOLOGY='closed-outward-12-triangle-v1'
ROLES=['frame_galvanized','infill_coating','roof_membrane','slab_mineral','utility_panel_ochre']
EPS=1e-9

def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def file_sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def scene_digest(s):
    v=copy.deepcopy(s); v.pop('scene_digest',None); return digest(v)
def load_module(path):
    spec=importlib.util.spec_from_file_location('axm_env_building_successor',path)
    if spec is None or spec.loader is None: raise ValueError(f'cannot load source module {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def parse_obj(lines):
    verts=[]; tris=[]; objects=[]
    for line in lines:
        if line.startswith('o '): objects.append(line[2:].strip())
        elif line.startswith('v '):
            _,x,y,z=line.split(); verts.append([float(x),float(y),float(z)])
        elif line.startswith('f '): tris.append([int(x.split('/')[0])-1 for x in line.split()[1:]])
    if (len(verts),len(tris),len(objects))!=(152,228,19): raise ValueError('successor geometry count drift')
    return verts,tris,objects
def material_map(receiving):
    rows=receiving.get('surfaces',[])
    if [r.get('surface_role') for r in rows]!=ROLES: raise ValueError('surface role drift')
    if any(r.get('material_id')!=r.get('surface_role') for r in rows): raise ValueError('material role/id drift')
    return {r['surface_role']:copy.deepcopy(r['material']) for r in rows}
def strip_building(scene):
    v=copy.deepcopy(scene); v.pop('scene_digest',None); v.pop('environment_building_material_receiving',None); return v
def translation_error(local,world):
    if len(local)!=len(world): raise ValueError('vertex count drift')
    t=[world[0][i]-local[0][i] for i in range(3)]; err=0.0
    for a,b in zip(local,world):
        for i in range(3): err=max(err,abs(a[i]+t[i]-b[i]))
    return t,err

def build(base,source_root,mp,mr,source_head,material_head,receiving_head):
    if base.get('schema')!=BASE_SCHEMA or base.get('status')!=BASE_STATUS or len(base.get('states',[]))!=17: raise ValueError('exact PR24 material parent must PASS first')
    if mp.get('schema')!='axm.building-material-lookdev-payload/v0.1': raise ValueError('material payload schema drift')
    if mr.get('schema')!='axm.building-material-lookdev-build-receipt/v0.1' or mr.get('result')!='PASS_SOURCE_BOUND_BUILDING_SURFACE_PAYLOAD': raise ValueError('material/source receipt not PASS')
    ident=mp.get('source_identity',{})
    if mr.get('hard_surface_source_head')!=source_head or ident.get('hard_surface_head')!=source_head: raise ValueError('source head drift')
    if (mr.get('source_schema'),mr.get('source_revision'),mr.get('box_topology_revision'))!=(SOURCE_SCHEMA,SOURCE_REV,TOPOLOGY): raise ValueError('source successor identity drift')
    topo=mr.get('topology_summary') or {}
    required={'object_count':19,'vertex_count':152,'triangle_count':228,'boundary_edge_count':0,'nonmanifold_edge_count':0,'orientation_conflict_edge_count':0,'degenerate_triangle_count':0,'outward_triangle_count':228,'inward_triangle_count':0}
    if any(topo.get(k)!=v for k,v in required.items()): raise ValueError('source topology metrics drift')
    root=Path(source_root); sm=load_module(root/'tools/build_service_pavilion.py'); built=sm.build()
    if len(built)<9 or getattr(sm,'BOX_TOPOLOGY_REVISION',None)!=TOPOLOGY or built[8]!=topo: raise ValueError('exact source builder topology does not match receipt')
    local,tris,objects=parse_obj(built[3])
    if file_sha(root/'assets/service_pavilion_001.json')!=mr.get('pavilion_source_sha256') or file_sha(root/'assets/utility_access_panel_001.json')!=mr.get('panel_source_sha256'): raise ValueError('source file digest drift')
    if base.get('building_material_profile_sha256')!=mr.get('material_profile_sha256'): raise ValueError('topology-only rebind forbids material profile change')
    first=base['states'][0]['scene']['environment_building_material_receiving']; mats=material_map(first)
    cand=mp.get('materials',{}).get('candidate',{})
    if set(cand)!=set(ROLES) or any(cand[r]!=mats[r] for r in ROLES): raise ValueError('topology-only rebind forbids material-value change')
    world=first['vertices_source_xyz_m']; translation,err=translation_error(local,world)
    if err>EPS: raise ValueError(f'successor vertex placement drift {err}')
    comps=mp.get('components',[])
    if len(comps)!=19: raise ValueError('component count drift')
    grouped={r:[] for r in ROLES}; object_rows=[]
    for i,c in enumerate(comps):
        role=c.get('candidate_material')
        if role not in grouped: raise ValueError('unexpected component material role')
        block=copy.deepcopy(tris[i*12:(i+1)*12]); grouped[role]+=block; object_rows.append({'index':i,'component_id':c.get('id'),'surface_role':role,'triangle_count':len(block)})
    surfaces=[{'surface_role':r,'material_id':r,'material':copy.deepcopy(mats[r]),'triangles':grouped[r]} for r in ROLES]
    partition_sha=digest(grouped); states=[]; old_parts=[]; new_parts=[]
    for br in base['states']:
        row=copy.deepcopy(br); scene=row['scene']; old=scene.get('environment_building_material_receiving',{})
        if old.get('asset_id')!=BUILDING or old.get('vertices_source_xyz_m')!=world or material_map(old)!=mats: raise ValueError('parent Building receiving drift')
        before=strip_building(scene); old_parts.append(digest({r['surface_role']:r['triangles'] for r in old['surfaces']}))
        recv=copy.deepcopy(old); recv['surfaces']=copy.deepcopy(surfaces); recv['source_geometry_digest']=digest({'vertices':world,'triangles':tris}); recv['receiving_policy']='EXACT_SOURCE_OWNED_CLOSED_OUTWARD_TOPOLOGY_REBIND_NO_MATERIAL_RETUNE'
        recv['source_successor_rebind']={'source_head':source_head,'source_schema':SOURCE_SCHEMA,'source_revision':SOURCE_REV,'box_topology_revision':TOPOLOGY,'material_head':material_head,'material_profile_sha256':mr['material_profile_sha256'],'pavilion_source_sha256':mr['pavilion_source_sha256'],'panel_source_sha256':mr['panel_source_sha256'],'placement_translation_source_xyz_m':translation,'topology_summary':copy.deepcopy(topo)}
        prov=recv.setdefault('provenance',{}); prov.update({'building_source_head':source_head,'building_material_head':material_head,'pavilion_source_sha256':mr['pavilion_source_sha256'],'panel_source_sha256':mr['panel_source_sha256'],'material_profile_sha256':mr['material_profile_sha256'],'placement_translation_source_xyz_m':translation})
        recv['truth_boundary']='Environment rebinds only the integrated current-world Building receiving geometry to the exact source-owned closed/outward successor topology while preserving current material values and all Weather, Nature, Object, path, camera, lighting and placement state. This is not a visual-hierarchy repair or final look acceptance.'
        scene['environment_building_material_receiving']=recv; scene['scene_digest']=scene_digest(scene)
        if strip_building(scene)!=before: raise ValueError('unrelated current-world state drift')
        new_parts.append(digest({r['surface_role']:r['triangles'] for r in recv['surfaces']})); states.append(row)
    checks={
      'exact_parent_passes_first':base['status']==BASE_STATUS,
      'exact_17_state_schedule_preserved':[r.get('time_s') for r in states]==[r.get('time_s') for r in base['states']],
      'weather_field_sequence_preserved':[r.get('weather_field_digest') for r in states]==[r.get('weather_field_digest') for r in base['states']],
      'sapling_mesh_sequence_preserved':[r.get('sapling_mesh_digest') for r in states]==[r.get('sapling_mesh_digest') for r in base['states']],
      'object_source_identity_preserved':all(any(s.get('asset_id')=='source:object:modular-equipment-case-001' for s in r['scene'].get('additional_source_meshes',[])) for r in states),
      'rear_tree_identity_preserved':all(any(s.get('asset_id')=='source:nature:east-rear-tree-neutral-001' for s in r['scene'].get('additional_source_meshes',[])) for r in states),
      'building_world_vertices_preserved':all(r['scene']['environment_building_material_receiving']['vertices_source_xyz_m']==world for r in states),
      'building_material_values_preserved':all(material_map(r['scene']['environment_building_material_receiving'])==mats for r in states),
      'source_successor_topology_exact':built[8]==topo,
      'successor_partition_changes_historical_partition':len(set(old_parts))==1 and len(set(new_parts))==1 and old_parts[0]!=new_parts[0],
      'successor_partition_is_228_triangles':sum(len(v) for v in grouped.values())==228,
      'source_successor_vertex_alignment_exact':err<=EPS,
      'material_payload_bound_to_successor':ident.get('hard_surface_head')==source_head,
      'material_profile_unchanged':base['building_material_profile_sha256']==mr['material_profile_sha256'],
      'cameras_preserved':all(a['scene'].get('cameras')==b['scene'].get('cameras') for a,b in zip(states,base['states'])),
      'path_preserved':all(a['scene'].get('readable_path')==b['scene'].get('readable_path') for a,b in zip(states,base['states']))}
    if not all(checks.values()): raise ValueError(f'source-successor checks failed {checks}')
    out={'schema':SCHEMA,'study_id':'environment-current-world-building-source-successor-001','status':STATUS,'receiving_head':receiving_head,'parent_environment_head':base['receiving_head'],'parent_composition_digest':base['composition_digest'],'weather_variant_head':base['weather_variant_head'],'weather_variant_seed':base['weather_variant_seed'],'weather_variant_layout_digest':base['weather_variant_layout_digest'],'object_source_head':base['object_source_head'],'object_source_sha256':base['object_source_sha256'],'rear_migrated_mesh_digest':base['rear_migrated_mesh_digest'],'historical_building_source_head':base['building_source_head'],'building_source_head':source_head,'building_source_schema':SOURCE_SCHEMA,'building_source_revision':SOURCE_REV,'building_box_topology_revision':TOPOLOGY,'building_material_head':material_head,'building_material_profile_sha256':mr['material_profile_sha256'],'pavilion_source_sha256':mr['pavilion_source_sha256'],'panel_source_sha256':mr['panel_source_sha256'],'placement_translation_source_xyz_m':translation,'source_topology_summary':topo,'surface_partition_sha256':partition_sha,'component_surface_rows':object_rows,'checks':checks,'states':states,'truth_boundary':'PASS proves only that the exact source-owned Building closed/outward successor replaces the historical malformed face table inside the already-proven current world while world vertices, current five material values, Weather, Nature, Object, path, cameras, lighting and placements remain fixed. It does not repair or accept the known current-world infill hierarchy FAIL, establish final normals/tangents/UVs, target-device performance, gameplay, CANON, production readiness or Environment mastery.','non_claims':['CURRENT_WORLD_INFILL_HIERARCHY_REPAIRED_OR_ACCEPTED','FINAL_ART_DIRECTION_OR_VISUAL_QA_ACCEPTANCE','FINAL_NORMALS_TANGENTS_UVS_TEXTURES_OR_WEATHERING','TARGET_DEVICE_RUNTIME_BUDGET','COLLISION_NAVIGATION_OR_GAMEPLAY','CANON_PRODUCTION_READY_GAME_READY_OR_MASTERY']}
    out['composition_digest']=digest({'parent':out['parent_composition_digest'],'source_head':source_head,'source_revision':SOURCE_REV,'topology_revision':TOPOLOGY,'material_profile':out['building_material_profile_sha256'],'surface_partition':partition_sha,'scenes':[r['scene']['scene_digest'] for r in states]})
    return out

def observer(payload):
    return {'schema':OBS_SCHEMA,'status':OBS_STATUS,'receiving_head':payload['receiving_head'],'parent_vfx_head':payload['parent_environment_head'],'environment_donor_head':payload['parent_environment_head'],'dense_vfx_sequence_digest':payload['parent_composition_digest'],'weather_variant_head':payload['weather_variant_head'],'weather_variant_seed':payload['weather_variant_seed'],'weather_variant_layout_digest':payload['weather_variant_layout_digest'],'rear_migrated_mesh_digest':payload['rear_migrated_mesh_digest'],'states':copy.deepcopy(payload['states']),'compatibility_projection_truth':'OBSERVER_COMPATIBILITY_ONLY_CANONICAL_ACCEPTANCE_USES_ENVIRONMENT_BUILDING_SOURCE_SUCCESSOR_SCHEMA'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--base',required=True); p.add_argument('--building-source-root',required=True); p.add_argument('--material-payload',required=True); p.add_argument('--material-receipt',required=True); p.add_argument('--source-head',required=True); p.add_argument('--material-head',required=True); p.add_argument('--receiving-head',required=True); p.add_argument('--output',required=True); p.add_argument('--observer-output',required=True); a=p.parse_args()
    out=build(json.load(open(a.base)),a.building_source_root,json.load(open(a.material_payload)),json.load(open(a.material_receipt)),a.source_head,a.material_head,a.receiving_head)
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); Path(a.observer_output).write_text(json.dumps(observer(out),indent=2,sort_keys=True)+'\n'); print(json.dumps({'status':out['status'],'composition_digest':out['composition_digest'],'checks':out['checks']},indent=2,sort_keys=True))
if __name__=='__main__': main()
