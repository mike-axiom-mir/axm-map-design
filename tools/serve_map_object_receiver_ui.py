#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, mimetypes, subprocess, sys, tempfile, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
MAX_BODY=64*1024
def main()->int:
    ap=argparse.ArgumentParser(description="Loopback-only human wrapper for axm.map.object.receiver.packet")
    ap.add_argument("--component-map",required=True); ap.add_argument("--motion-plan",required=True); ap.add_argument("--environment-report",required=True); ap.add_argument("--runtime-receipt",required=True)
    ap.add_argument("--port",type=int,default=8787); ap.add_argument("--no-open",action="store_true"); args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]; static=(root/"tooling/human/map-object-receiver").resolve(); runner=(root/"tools/run_map_object_receiver_tool.py").resolve(); manifest_path=(root/"tooling/map-object-receiver-packet.manifest.json").resolve()
    evidence={"--component-map":str(Path(args.component_map).resolve()),"--motion-plan":str(Path(args.motion_plan).resolve()),"--environment-report":str(Path(args.environment_report).resolve()),"--runtime-receipt":str(Path(args.runtime_receipt).resolve())}
    for key,value in evidence.items():
        if not Path(value).is_file(): raise SystemExit(f"missing {key} evidence file: {value}")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    class Handler(BaseHTTPRequestHandler):
        server_version="AXMMapReceiverUI/0.1"
        def log_message(self,fmt,*values): sys.stderr.write("[ui] "+(fmt%values)+"\n")
        def send_json(self,status:int,value:dict):
            body=(json.dumps(value,sort_keys=True)+"\n").encode(); self.send_response(status); self.send_header("content-type","application/json; charset=utf-8"); self.send_header("cache-control","no-store"); self.send_header("content-length",str(len(body))); self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            path=urlparse(self.path).path
            if path=="/api/status":
                try:
                    head=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip(); self.send_json(200,{"tool_id":manifest["tool_id"],"layers":manifest["layers"],"exact_head":head,"listen_address":"127.0.0.1","same_runner":True})
                except Exception as exc: self.send_json(500,{"error":str(exc)})
                return
            rel="index.html" if path=="/" else path.lstrip("/"); target=(static/rel).resolve()
            try: target.relative_to(static)
            except ValueError: self.send_error(403); return
            if not target.is_file(): self.send_error(404); return
            data=target.read_bytes(); mime=mimetypes.guess_type(target.name)[0] or "application/octet-stream"; self.send_response(200); self.send_header("content-type",mime); self.send_header("cache-control","no-store"); self.send_header("content-length",str(len(data))); self.end_headers(); self.wfile.write(data)
        def do_POST(self):
            if urlparse(self.path).path!="/api/run": self.send_error(404); return
            try:
                length=int(self.headers.get("content-length","0"))
                if length<=0 or length>MAX_BODY: raise ValueError("request body size is outside bounded limit")
                request=json.loads(self.rfile.read(length))
                if not isinstance(request,dict): raise ValueError("request must be a JSON object")
            except Exception as exc: self.send_json(400,{"error":str(exc)}); return
            with tempfile.TemporaryDirectory(prefix="axm-map-human-") as tmp:
                td=Path(tmp); request_path=td/"request.json"; out=td/"output"; request_path.write_text(json.dumps(request,indent=2,sort_keys=True)+"\n",encoding="utf-8")
                cmd=[sys.executable,str(runner),"--request",str(request_path)]
                for key,value in evidence.items(): cmd.extend([key,value])
                cmd.extend(["--out",str(out)]); proc=subprocess.run(cmd,cwd=root,text=True,capture_output=True)
                if proc.returncode!=0:
                    message=(proc.stderr or proc.stdout or "tool invocation failed").strip(); self.send_json(422,{"error":message,"returncode":proc.returncode}); return
                packet=json.loads((out/"receiver-packet.json").read_text(encoding="utf-8")); receipt=json.loads((out/"receipt.json").read_text(encoding="utf-8")); self.send_json(200,{"request":request,"packet":packet,"receipt":receipt,"runner_stdout":proc.stdout.strip()})
    httpd=ThreadingHTTPServer(("127.0.0.1",args.port),Handler); url=f"http://127.0.0.1:{args.port}/"; print(f"AXM Map Object Receiver UI: {url}",flush=True)
    if not args.no_open: webbrowser.open(url)
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass
    finally: httpd.server_close()
    return 0
if __name__=="__main__": raise SystemExit(main())
