#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance

EXPECTED_STATE = "PASS_TELEMETRY_BOUND_CLEAN_PRESENTATION_STATE_RECONSTRUCTION"
EXPECTED_RECEIVER = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
EXPECTED_EFFECT = "ecade64227ba1d3d1faf029ca7188ea63c2560ec"
EXPECTED_TIMING = "795d9e8862e895e506c756b9ea01cd6228fa7ab7"
EXPECTED_SKIPS = {"path_eye": [19], "elevated_oblique": [11, 23, 38]}
EXPECTED_PRESENTED = {"path_eye": 47, "elevated_oblique": 45}
STEP_MS = 31.25


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_and_verify(root: Path):
    manifest = json.loads((root / "reconstruction-manifest.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    assert manifest["state"] == EXPECTED_STATE, manifest["state"]
    assert summary["state"] == EXPECTED_STATE, summary["state"]
    assert manifest["accepted_receiver_head"] == EXPECTED_RECEIVER
    assert manifest["nature_vfx_effect_head"] == EXPECTED_EFFECT
    assert manifest["clean_timing_head"] == EXPECTED_TIMING
    assert manifest["clean_presentation_mode"] == "PHASE_LOCKED_LATEST_DUE_DIRECT_SOURCE_STATE_NO_RETIME"
    assert manifest["scheduled_slots"] == 96
    assert manifest["presented_slots"] == 92
    assert manifest["direct_live_capture_of_clean_stream"] is False
    assert manifest["static_images_real_godot"] is True
    assert manifest["interpolation_added"] is False
    assert manifest["source_retimed"] is False
    return manifest


def build_context_index(root: Path, context: str, c: dict):
    phase = {}
    clean_records = []
    for e in c["events"]:
        p = int(e["source_phase_index"])
        image = root / e["png"]
        assert image.is_file(), image
        got = sha256(image)
        assert got == e["png_sha256"], (image, got, e["png_sha256"])
        if p in phase:
            assert phase[p]["png_sha256"] == got
            assert phase[p]["sapling_mesh_digest"] == e["sapling_mesh_digest"]
        else:
            phase[p] = {
                "source_phase_index": p,
                "png": e["png"],
                "png_sha256": got,
                "sapling_mesh_digest": e["sapling_mesh_digest"],
            }
        if e["event"] == "clean_frame_post_draw":
            clean_records.append(e)
    assert set(phase) == set(range(17)), (context, sorted(phase))
    assert phase[0]["png_sha256"] == phase[16]["png_sha256"], context
    assert len(clean_records) == EXPECTED_PRESENTED[context], (context, len(clean_records))
    skips = sorted(set(range(48)) - {int(e["absolute_slot"]) for e in clean_records})
    assert skips == EXPECTED_SKIPS[context], (context, skips)
    return phase, clean_records


def diff_stats(a: Image.Image, b: Image.Image):
    assert a.size == b.size
    aa = a.convert("RGB")
    bb = b.convert("RGB")
    d = ImageChops.difference(aa, bb)
    bbox = d.getbbox()
    changed = 0
    total_abs = 0
    max_delta = 0
    for px in d.getdata():
        m = max(px)
        if m:
            changed += 1
            total_abs += sum(px)
            if m > max_delta:
                max_delta = m
    total_pixels = aa.width * aa.height
    return d, {
        "changed_pixels": changed,
        "total_pixels": total_pixels,
        "changed_fraction": changed / total_pixels,
        "max_channel_delta": max_delta,
        "sum_absolute_rgb_delta": total_abs,
        "mean_absolute_rgb_delta_per_image_pixel": total_abs / (total_pixels * 3.0),
        "mean_absolute_rgb_delta_per_changed_pixel": (total_abs / (changed * 3.0)) if changed else 0.0,
        "changed_bbox_xyxy": list(bbox) if bbox else None,
    }


def amplified(diff: Image.Image, factor: int = 8):
    return ImageEnhance.Brightness(diff).enhance(factor)


def copy_phase_image(root: Path, out_images: Path, context: str, label: str, e: dict):
    src = root / e["png"]
    dst = out_images / f"{context}-{label}-phase-{int(e['source_phase_index']):02d}.png"
    shutil.copy2(src, dst)
    assert sha256(dst) == e["png_sha256"]
    return dst.name


def reject_wrong_skipped_phase(expected_phase: int, proposed_phase: int):
    if proposed_phase != expected_phase:
        raise AssertionError(f"wrong skipped phase: expected {expected_phase}, got {proposed_phase}")


def html_for(report: dict):
    payload = json.dumps(report, separators=(",", ":")).replace("</", "<\\/")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AXM Nature flutter skipped-state consequence review</title>
<style>:root{{font-family:system-ui,sans-serif;color-scheme:dark;background:#111;color:#eee}}body{{margin:0;padding:18px}}h1{{font-size:20px}}.truth{{border:1px solid #666;border-radius:8px;padding:10px 12px;background:#191919;line-height:1.35}}.controls{{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}}select{{font:inherit}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}.card{{border:1px solid #444;border-radius:8px;padding:8px;background:#181818}}img{{width:100%;display:block;background:#000}}.meta{{font:12px ui-monospace,monospace;white-space:pre-wrap;margin-top:6px}}.metrics{{margin-top:12px;font:12px ui-monospace,monospace;white-space:pre-wrap}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}</style></head><body>
<h1>Nature leaf flutter — skipped authored-state consequence review</h1>
<div class="truth"><strong>Evidence aid only.</strong> These exact real-Godot phase images are joined to the already-measured clean 92/96 presentation telemetry. A skipped image is an authored source state that the clean proof-host scheduler did not present in that slot. Difference images are diagnostics; amplified versions are explicitly 8× brightness aids and are not faithful effect amplitude. This surface does not decide naturalness, source retiming, physics, gameplay, target-device performance, CANON, or production readiness.</div>
<div class="controls"><label>Skip window <select id="pick"></select></label></div>
<div class="grid"><div class="card"><strong>Previous presented source state</strong><img id="prev"><div class="meta" id="prevMeta"></div></div><div class="card"><strong>Skipped authored source state</strong><img id="skip"><div class="meta" id="skipMeta"></div></div><div class="card"><strong>Next presented source state</strong><img id="next"><div class="meta" id="nextMeta"></div></div></div>
<div class="grid" style="margin-top:10px"><div class="card"><strong>|previous − skipped| raw</strong><img id="d1"></div><div class="card"><strong>|skipped − next| raw</strong><img id="d2"></div><div class="card"><strong>|previous − next| raw direct jump</strong><img id="d3"></div></div>
<div class="metrics" id="metrics"></div>
<script>const DATA={payload};const sel=document.getElementById('pick');DATA.windows.forEach((w,i)=>{{const o=document.createElement('option');o.value=i;o.textContent=`${{w.context}} · slot ${{w.absolute_slot}} · phase ${{w.skipped_phase}}`;sel.appendChild(o)}});function render(){{const w=DATA.windows[Number(sel.value||0)];prev.src=w.previous_png;skip.src=w.skipped_png;next.src=w.next_png;d1.src=w.previous_to_skipped.raw_diff_png;d2.src=w.skipped_to_next.raw_diff_png;d3.src=w.previous_to_next.raw_diff_png;prevMeta.textContent=`slot ${{w.previous_presented_slot}} · phase ${{w.previous_phase}}`;skipMeta.textContent=`authored slot ${{w.absolute_slot}} · phase ${{w.skipped_phase}} · due ${{w.authored_due_ms.toFixed(2)}} ms`;nextMeta.textContent=`slot ${{w.next_presented_slot}} · phase ${{w.next_phase}}`;metrics.textContent=JSON.stringify({{previous_to_skipped:w.previous_to_skipped.metrics,skipped_to_next:w.skipped_to_next.metrics,previous_to_next:w.previous_to_next.metrics}},null,2)}}sel.onchange=render;render();</script></body></html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.artifact_root.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    out_images = out / "images"
    out_images.mkdir(exist_ok=True)

    manifest = load_and_verify(root)
    report = {
        "state": "PASS_TELEMETRY_BOUND_SKIPPED_STATE_VISUAL_CONSEQUENCE_REVIEW_SURFACE",
        "accepted_receiver_head": EXPECTED_RECEIVER,
        "nature_vfx_effect_head": EXPECTED_EFFECT,
        "clean_timing_head": EXPECTED_TIMING,
        "clean_scheduled_total": 96,
        "clean_presented_total": 92,
        "review_window_count": 4,
        "static_images_real_godot": True,
        "timing_authority": "RETAINED_CLEAN_FRAME_POST_DRAW_TELEMETRY_ONLY",
        "skipped_image_semantics": "AUTHORED_SOURCE_STATE_NOT_PRESENTED_IN_THAT_CLEAN_SLOT",
        "interpolation_added": False,
        "source_retimed": False,
        "direct_live_capture_of_clean_stream": False,
        "final_perceptual_acceptance_claimed": False,
        "gameplay_or_physics_claimed": False,
        "target_device_performance_claimed": False,
        "diagnostic_diff_amplification_factor": 8,
        "windows": [],
    }

    for context in ("path_eye", "elevated_oblique"):
        c = manifest["contexts"][context]
        phase, records = build_context_index(root, context, c)
        by_slot = {int(e["absolute_slot"]): e for e in records}
        for slot in EXPECTED_SKIPS[context]:
            prev_slot = max(s for s in by_slot if s < slot)
            next_slot = min(s for s in by_slot if s > slot)
            skipped_phase = slot % 16
            reject_wrong_skipped_phase(skipped_phase, skipped_phase)
            negative_ok = False
            try:
                reject_wrong_skipped_phase(skipped_phase, (skipped_phase + 1) % 16)
            except AssertionError:
                negative_ok = True
            assert negative_ok

            prev_e = phase[prev_slot % 16]
            skip_e = phase[skipped_phase]
            next_e = phase[next_slot % 16]
            assert prev_e["png_sha256"] != skip_e["png_sha256"]
            assert skip_e["png_sha256"] != next_e["png_sha256"]
            assert prev_e["png_sha256"] != next_e["png_sha256"]

            prev_png = copy_phase_image(root, out_images, context, f"slot-{slot:02d}-previous", prev_e)
            skip_png = copy_phase_image(root, out_images, context, f"slot-{slot:02d}-skipped", skip_e)
            next_png = copy_phase_image(root, out_images, context, f"slot-{slot:02d}-next", next_e)
            a = Image.open(out_images / prev_png).convert("RGB")
            b = Image.open(out_images / skip_png).convert("RGB")
            d = Image.open(out_images / next_png).convert("RGB")

            comparisons = {}
            for name, left, right in (
                ("previous_to_skipped", a, b),
                ("skipped_to_next", b, d),
                ("previous_to_next", a, d),
            ):
                raw, metrics = diff_stats(left, right)
                assert metrics["changed_pixels"] > 0, (context, slot, name, metrics)
                raw_name = f"{context}-slot-{slot:02d}-{name}-raw-diff.png"
                amp_name = f"{context}-slot-{slot:02d}-{name}-x8-diagnostic.png"
                raw.save(out_images / raw_name)
                amplified(raw, 8).save(out_images / amp_name)
                comparisons[name] = {
                    "metrics": metrics,
                    "raw_diff_png": f"images/{raw_name}",
                    "x8_diagnostic_png": f"images/{amp_name}",
                    "raw_diff_sha256": sha256(out_images / raw_name),
                    "x8_diagnostic_sha256": sha256(out_images / amp_name),
                }

            report["windows"].append({
                "context": context,
                "absolute_slot": slot,
                "authored_due_ms": slot * STEP_MS,
                "skipped_phase": skipped_phase,
                "previous_presented_slot": prev_slot,
                "previous_phase": prev_slot % 16,
                "next_presented_slot": next_slot,
                "next_phase": next_slot % 16,
                "previous_png": f"images/{prev_png}",
                "skipped_png": f"images/{skip_png}",
                "next_png": f"images/{next_png}",
                "previous_png_sha256": prev_e["png_sha256"],
                "skipped_png_sha256": skip_e["png_sha256"],
                "next_png_sha256": next_e["png_sha256"],
                "negative_wrong_phase_binding_rejected": negative_ok,
                **comparisons,
            })

    assert len(report["windows"]) == 4
    (out / "skip-consequence-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "review.html").write_text(html_for(report))
    summary = {
        "state": report["state"],
        "windows": [
            {
                "context": w["context"],
                "absolute_slot": w["absolute_slot"],
                "skipped_phase": w["skipped_phase"],
                "previous_to_skipped_changed_pixels": w["previous_to_skipped"]["metrics"]["changed_pixels"],
                "skipped_to_next_changed_pixels": w["skipped_to_next"]["metrics"]["changed_pixels"],
                "previous_to_next_changed_pixels": w["previous_to_next"]["metrics"]["changed_pixels"],
            }
            for w in report["windows"]
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
