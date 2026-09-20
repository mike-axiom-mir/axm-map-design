# AXM Map Object Receiver — human wrapper

This is a local browser surface over the exact `axm.map.object.receiver.packet` request contract.

It does not implement packet construction. `tools/serve_map_object_receiver_ui.py` accepts the five request fields, writes the request JSON, and invokes `tools/run_map_object_receiver_tool.py` with the exact evidence files supplied when the server starts.

## Local launch

From a clean checkout of the verified tool head, run the loopback server with the four exact evidence files:

    python tools/serve_map_object_receiver_ui.py --component-map /path/to/object-rigid-component-map.json --motion-plan /path/to/object-motion-receiver-plan.json --environment-report /path/to/environment-report.json --runtime-receipt /path/to/runtime.json

The server binds only to `127.0.0.1`. Invocation does not require network access. The browser UI owns no new creation semantics: sample index, service-frame choice and static-batching choice are the same fields in `tooling/schemas/map-object-receiver-tool-request.schema.json`.

The UI does not grant Environment adoption, Art/QA acceptance, target-device performance, future arbitrary-articulation safety, gameplay/physics, CANON or production readiness.
