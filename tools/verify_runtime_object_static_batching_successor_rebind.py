#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

SCHEMA = "axm.runtime-object-static-batching-successor-rebind-observation/v0.1"
PASS_STATE = "PASS_OBJECT_STATIC_BATCHING_SUCCESSOR_REBIND__HOLD_ART_QA_TARGET_DEVICE_FUTURE_ARTICULATION"
EXPECTED_SAMPLES = [0, 10, 50, 100]
ANIMATION_PARENT = "51f1c0002f58f138911cce7d95a30add9a1e03af"
TA_PARENT = "fc567fd6dd061ccb5e8232bd17ee0af3d2e064b7"


def fail(msg: str) -> None:
    raise SystemExit(msg)


def load(path: str) -> dict:
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        fail("receipt must be a JSON object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    d = load(args.receipt)

    if d.get("schema") != SCHEMA:
        fail("schema drift")
    if d.get("state") != PASS_STATE:
        fail("state is not bounded successor PASS")
    if d.get("animation_parent_head") != ANIMATION_PARENT:
        fail("successor Animation head drift")
    if d.get("technical_art_parent_head") != TA_PARENT:
        fail("successor Technical Art head drift")
    if d.get("component_count") != 31:
        fail("component count drift")
    if d.get("control_component_surface_instances") != 33:
        fail("control component-surface count drift")

    moving = int(d.get("moving_component_count", -1))
    static = int(d.get("static_component_count", -1))
    if moving != 7 or static != 24 or moving + static != 31:
        fail("pass-48 moving/static classification drift")
    if int(d.get("static_batch_surface_count", -1)) <= 0:
        fail("static batch surface count missing")
    if int(d.get("candidate_render_surface_count", 999)) >= 33:
        fail("candidate did not reduce rendered surface count")
    if int(d.get("detached_static_mesh_count", -1)) != static:
        fail("static semantic-node detach count drift")
    if not d.get("component_nodes_preserved", False):
        fail("source-owned component nodes not preserved")
    if d.get("future_arbitrary_articulation_accepted", True):
        fail("future arbitrary articulation authority inflated")
    if d.get("target_device_performance_accepted", True):
        fail("target-device authority inflated")
    if d.get("art_qa_accepted", True):
        fail("Art/QA authority inflated")

    rows = d.get("measurements")
    if not isinstance(rows, list) or [r.get("sample_index") for r in rows] != EXPECTED_SAMPLES:
        fail("retained sample set drift")

    draw_wins = []
    object_wins = []
    buffer_deltas = []
    changed_pixels = []
    max_visual_delta = 0
    for row in rows:
        c = row.get("control_runtime", {})
        x = row.get("candidate_runtime", {})
        for key in ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame",
                    "texture_mem_bytes", "buffer_mem_bytes"):
            if key not in c or key not in x:
                fail(f"missing runtime counter {key}")
        if int(x["draw_calls_in_frame"]) >= int(c["draw_calls_in_frame"]):
            fail("candidate did not reduce draw calls at every retained sample")
        if int(x["objects_in_frame"]) >= int(c["objects_in_frame"]):
            fail("candidate did not reduce visible objects at every retained sample")
        if int(x["primitives_in_frame"]) != int(c["primitives_in_frame"]):
            fail("primitive count changed")
        if int(x["texture_mem_bytes"]) != int(c["texture_mem_bytes"]):
            fail("texture memory changed")
        draw_wins.append(int(c["draw_calls_in_frame"]) - int(x["draw_calls_in_frame"]))
        object_wins.append(int(c["objects_in_frame"]) - int(x["objects_in_frame"]))
        buffer_deltas.append(int(x["buffer_mem_bytes"]) - int(c["buffer_mem_bytes"]))

        visual = row.get("visual", {})
        over = int(visual.get("pixels_over_1_lsb", -1))
        delta = int(visual.get("max_channel_delta_lsb", 999))
        changed = int(visual.get("changed_pixels", -1))
        if over != 0 or delta > 1 or changed < 0:
            fail("successor shaded visual drift exceeded one LSB gate")
        changed_pixels.append(changed)
        max_visual_delta = max(max_visual_delta, delta)
        if float(row.get("max_owner_pose_delta_deg", 999.0)) > 0.0002:
            fail("successor owner pose changed")
        if float(row.get("max_owner_position_delta_m", 999.0)) > 0.000001:
            fail("successor moving-component position changed")

    if min(draw_wins) <= 0 or min(object_wins) <= 0:
        fail("missing consistent submission/object win")

    summary = d.get("summary", {})
    if int(summary.get("min_draw_calls_saved", -1)) != min(draw_wins):
        fail("draw-call summary drift")
    if int(summary.get("min_objects_saved", -1)) != min(object_wins):
        fail("object summary drift")
    if int(summary.get("buffer_delta_min_bytes", 0)) != min(buffer_deltas):
        fail("buffer minimum summary drift")
    if int(summary.get("buffer_delta_max_bytes", 0)) != max(buffer_deltas):
        fail("buffer maximum summary drift")

    print(PASS_STATE)
    print(json.dumps({
        "samples": EXPECTED_SAMPLES,
        "moving_components": moving,
        "static_components": static,
        "static_batch_surfaces": d["static_batch_surface_count"],
        "candidate_render_surfaces": d["candidate_render_surface_count"],
        "min_draw_calls_saved": min(draw_wins),
        "max_draw_calls_saved": max(draw_wins),
        "min_objects_saved": min(object_wins),
        "buffer_delta_min_bytes": min(buffer_deltas),
        "buffer_delta_max_bytes": max(buffer_deltas),
        "changed_pixels_by_sample": changed_pixels,
        "max_visual_delta_lsb": max_visual_delta,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
