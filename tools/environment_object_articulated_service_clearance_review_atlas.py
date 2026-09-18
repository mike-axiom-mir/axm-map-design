from __future__ import annotations
import argparse, base64, hashlib, html, json, struct, zipfile
from pathlib import Path

SCHEMA="axm.environment-object-articulated-service-clearance-review-atlas/v0.1"
REPORT_SCHEMA="axm.environment-object-articulated-service-clearance-render-review/v0.2"
REPORT_RESULT="PASS_CURRENT_WORLD_OBJECT_ARTICULATED_SERVICE_CLEARANCE_SUCCESSOR_RENDERED__LOCALIZED_VISUAL_DELTA__ADOPTION_HELD"
RESULT="PASS_CURRENT_WORLD_OBJECT_ARTICULATED_SERVICE_CLEARANCE_REVIEW_ATLAS__EXACT_RETAINED_A_B__ADOPTION_HELD"

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def uri(b:bytes)->str: return "data:image/png;base64,"+base64.b64encode(b).decode()
def dims(b:bytes)->tuple[int,int]:
    if b[:8]!=b"\x89PNG\r\n\x1a\n" or b[12:16]!=b"IHDR": raise ValueError("invalid PNG")
    return struct.unpack(">II",b[16:24])

def image_panel(data:str,w:int,h:int,x:int,y:int,pw:int,ph:int,view=None)->str:
    if view is None: view=(0,0,w,h)
    vx,vy,vw,vh=view
    return (f'<svg x="{x}" y="{y}" width="{pw}" height="{ph}" viewBox="{vx} {vy} {vw} {vh}" '
            f'preserveAspectRatio="xMidYMid meet"><image x="0" y="0" width="{w}" height="{h}" href="{data}"/></svg>')

def diff_panel(a:str,b:str,w:int,h:int,x:int,y:int,pw:int,ph:int,idx:int,amp:int,view=None)->tuple[str,str]:
    if view is None: view=(0,0,w,h)
    vx,vy,vw,vh=view
    fid=f"d{idx}"
    defs=(f'<filter id="{fid}" filterUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">'
          f'<feImage href="{a}" x="0" y="0" width="{w}" height="{h}" preserveAspectRatio="none" result="a"/>'
          f'<feImage href="{b}" x="0" y="0" width="{w}" height="{h}" preserveAspectRatio="none" result="b"/>'
          f'<feBlend in="a" in2="b" mode="difference" result="d"/>'
          f'<feComponentTransfer in="d"><feFuncR type="linear" slope="{amp}"/><feFuncG type="linear" slope="{amp}"/>'
          f'<feFuncB type="linear" slope="{amp}"/><feFuncA type="identity"/></feComponentTransfer></filter>')
    panel=(f'<svg x="{x}" y="{y}" width="{pw}" height="{ph}" viewBox="{vx} {vy} {vw} {vh}" preserveAspectRatio="xMidYMid meet">'
           f'<rect x="0" y="0" width="{w}" height="{h}" fill="black" filter="url(#{fid})"/></svg>')
    return defs,panel

def board(title:str,rows:list[dict],amp:int,zoom_bbox=None)->str:
    pw,ph,gap,left,labelw=420,275,18,22,225
    top,rowh=92,350
    width=left+labelw+3*pw+2*gap+30
    height=top+len(rows)*rowh+55
    defs=[]; body=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#111418"/>',
        '<style>text{font-family:system-ui,sans-serif;fill:#f1f4f7}.muted{fill:#aab4bf}.warn{fill:#f5d38a}</style>',
        f'<text x="{left}" y="34" font-size="24" font-weight="700">{html.escape(title)}</text>',
        f'<text x="{left}" y="62" font-size="14" class="muted">Exact retained A/B. Difference is diagnostic ×{amp}; source PNG bytes remain unchanged.</text>']
    for ci,hdr in enumerate(("PREDECESSOR","SUCCESSOR +20mm",f"ABS DIFF ×{amp}")):
        x=left+labelw+ci*(pw+gap); body.append(f'<text x="{x}" y="84" font-size="13" font-weight="700" class="muted">{hdr}</text>')
    for i,row in enumerate(rows):
        y=top+i*rowh
        body += [f'<text x="{left}" y="{y+28}" font-size="18" font-weight="700">{html.escape(row["label"])}</text>',
                 f'<text x="{left}" y="{y+51}" font-size="12" class="muted">pre {row["pred_sha"][:12]}…</text>',
                 f'<text x="{left}" y="{y+70}" font-size="12" class="muted">succ {row["succ_sha"][:12]}…</text>']
        view=None if zoom_bbox is None else (zoom_bbox[0],zoom_bbox[1],zoom_bbox[2]-zoom_bbox[0]+1,zoom_bbox[3]-zoom_bbox[1]+1)
        for ci,key in enumerate(("pred","succ")):
            x=left+labelw+ci*(pw+gap)
            body.append(f'<rect x="{x-2}" y="{y-2}" width="{pw+4}" height="{ph+4}" fill="#2a3038" rx="4"/>')
            body.append(image_panel(row[key],row["w"],row["h"],x,y,pw,ph,view))
        x=left+labelw+2*(pw+gap)
        body.append(f'<rect x="{x-2}" y="{y-2}" width="{pw+4}" height="{ph+4}" fill="#2a3038" rx="4"/>')
        d,p=diff_panel(row["pred"],row["succ"],row["w"],row["h"],x,y,pw,ph,i,amp,view); defs.append(d); body.append(p)
    body.insert(1,"<defs>"+"".join(defs)+"</defs>")
    body.append(f'<text x="{left}" y="{height-22}" font-size="12" class="warn">Review aid only — full 272-frame artifact remains authority; environment_adoption=false.</text>')
    body.append("</svg>")
    return "\n".join(body)+"\n"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--artifact-zip",required=True); ap.add_argument("--contract",required=True); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args(); artifact=Path(a.artifact_zip).read_bytes(); contract=json.loads(Path(a.contract).read_text())
    if contract.get("schema")!=SCHEMA: raise SystemExit("contract schema drift")
    if sha(artifact)!=contract["source_artifact"]["sha256"]: raise SystemExit("source artifact SHA-256 mismatch")
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(Path(a.artifact_zip)) as z:
        head=z.read("exact-head.txt").decode().strip()
        if head!=contract["source_artifact"]["exact_head"]: raise SystemExit("exact head drift")
        base="evidence/environment_object_articulated_service_clearance_render_review"
        report=json.loads(z.read(f"{base}/report.json"))
        if report.get("schema")!=REPORT_SCHEMA or report.get("result")!=REPORT_RESULT: raise SystemExit("render report drift")
        if report.get("authority",{}).get("environment_adoption") is not False: raise SystemExit("unexpected adoption")
        if report.get("rendered_owner_samples")!=contract["selection"]["owner_samples"]: raise SystemExit("owner-sample drift")
        bbox=report["samples"]["0"]["visual"]["global_changed_bbox_px"]
        if report["samples"]["40"]["visual"]["global_changed_bbox_px"]!=bbox: raise SystemExit("review locality drift")
        amp=int(contract["selection"]["diff_amplification"]); state=int(contract["selection"]["weather_state_index"])
        manifest_rows=[]; outputs=[]
        for mode in contract["selection"]["presentation_modes"]:
            rows=[]
            for sample in contract["selection"]["owner_samples"]:
                for context in contract["selection"]["camera_contexts"]:
                    fn=f"atmosphere-width-{mode}-{context}-{state:02d}.png"
                    pn=f"{base}/predecessor-{sample}/rendered/{fn}"; sn=f"{base}/successor-{sample}/rendered/{fn}"
                    pb,sb=z.read(pn),z.read(sn); pd,sd=dims(pb),dims(sb)
                    if pd!=sd: raise SystemExit("A/B dimension drift")
                    rows.append({"label":f"sample {sample} · {context} · state {state:02d}","pred":uri(pb),"succ":uri(sb),"pred_sha":sha(pb),"succ_sha":sha(sb),"w":pd[0],"h":pd[1]})
                    manifest_rows.append({"owner_sample":sample,"owner_time_s":report["samples"][str(sample)]["owner_time_s"],"presentation_mode":mode,"camera_context":context,"weather_state_index":state,"predecessor_member":pn,"successor_member":sn,"predecessor_sha256":sha(pb),"successor_sha256":sha(sb),"dimensions_px":list(pd)})
            for suffix,zoom in (("",None),("-zoom",bbox)):
                name=f"service-clearance-review-atlas-{mode}{suffix}.svg"
                (out/name).write_text(board(f"AXM Environment · articulated service-clearance review · {mode}{' · zoom' if zoom else ''}",rows,amp,zoom),encoding="utf-8")
                outputs.append(name)
    manifest={"schema":SCHEMA,"result":RESULT,"source_artifact":contract["source_artifact"],"source_artifact_sha256_reproduced":sha(artifact),
              "selection":contract["selection"],"selected_pair_count":len(manifest_rows),"rows":manifest_rows,"outputs":outputs,
              "reusable_rule":"LARGE_REAL_SCENE_A_B_EVIDENCE_SHOULD_SHIP_WITH_A_DETERMINISTIC_COMPACT_ATLAS_THAT_PRESERVES_EXACT_SOURCE_FRAMES_AND_LABELS_ANY_DIAGNOSTIC_AMPLIFICATION",
              "authority":{"environment_adoption":False,"art_direction_acceptance":False,"independent_visual_qa_acceptance":False,"runtime_acceptance":False,"canon":False},
              "truth_boundary":"Atlas derives only from the exact retained PR #49 render artifact. Midpoint Weather state 08, both existing cameras, both owner samples and both existing presentation modes are selected by contract. Original A/B PNG bytes are embedded unchanged; difference is diagnostic-only x16. Full 272-frame artifact remains authority."}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(RESULT); print(json.dumps({"selected_pair_count":len(manifest_rows),"outputs":outputs,"artifact_sha256":sha(artifact)},sort_keys=True))
if __name__=="__main__": main()
