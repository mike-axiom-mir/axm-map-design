#!/usr/bin/env python3
import argparse, hashlib, json, math, shutil
from pathlib import Path

EXPECTED_RECON_STATE = 'PASS_TELEMETRY_BOUND_CLEAN_PRESENTATION_STATE_RECONSTRUCTION'
EXPECTED_RECEIVER = '7713cbe5863c3bc38dabb6236eb4b393401224b6'
EXPECTED_EFFECT = 'ecade64227ba1d3d1faf029ca7188ea63c2560ec'
EXPECTED_TIMING = '795d9e8862e895e506c756b9ea01cd6228fa7ab7'
EXPECTED_PRESENTED = {'path_eye': 47, 'elevated_oblique': 45}
EXPECTED_SKIPPED = {'path_eye': [19], 'elevated_oblique': [11, 23, 38]}
STEP_MS = 31.25
SLOT_COUNT = 48
TAIL_HOLD_MS = 250.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_reconstruction(root: Path):
    manifest = json.loads((root / 'reconstruction-manifest.json').read_text())
    summary = json.loads((root / 'summary.json').read_text())
    assert manifest['state'] == EXPECTED_RECON_STATE, manifest['state']
    assert summary['state'] == EXPECTED_RECON_STATE, summary['state']
    assert manifest['accepted_receiver_head'] == EXPECTED_RECEIVER
    assert manifest['nature_vfx_effect_head'] == EXPECTED_EFFECT
    assert manifest['clean_timing_head'] == EXPECTED_TIMING
    assert manifest['clean_presentation_mode'] == 'PHASE_LOCKED_LATEST_DUE_DIRECT_SOURCE_STATE_NO_RETIME'
    assert manifest['scheduled_slots'] == 96 and manifest['presented_slots'] == 92
    assert manifest['direct_live_capture_of_clean_stream'] is False
    assert manifest['static_images_real_godot'] is True
    assert manifest['interpolation_added'] is False
    assert manifest['source_retimed'] is False
    assert manifest['video_encoder_is_timing_authority'] is False
    return manifest, summary


def verify_images(root: Path, manifest: dict):
    hashes = {}
    unique = set()
    for context, c in manifest['contexts'].items():
        hashes[context] = {}
        for event in c['events']:
            phase = int(event['source_phase_index'])
            path = root / event['png']
            assert path.is_file(), path
            got = sha256(path)
            assert got == event['png_sha256'], (path, got, event['png_sha256'])
            if phase in hashes[context]:
                assert hashes[context][phase] == got
            else:
                hashes[context][phase] = got
            unique.add(str(path.resolve()))
        assert hashes[context][0] == hashes[context][16], context
        assert len(hashes[context]) == 17, (context, len(hashes[context]))
    assert len(unique) == 34, len(unique)
    return hashes


def clean_timeline(context: str, c: dict):
    events = c['events']
    assert events[0]['event'] == 'pre_timer_neutral_already_established'
    assert float(events[0]['time_ms']) == 0.0
    assert int(events[0]['source_phase_index']) == 0
    records = [e for e in events if e['event'] == 'clean_frame_post_draw']
    assert len(records) == EXPECTED_PRESENTED[context]
    assert c['skipped_slots'] == EXPECTED_SKIPPED[context]
    slots = [int(e['absolute_slot']) for e in records]
    assert slots == sorted(slots) and len(set(slots)) == len(slots)
    assert sorted(set(range(SLOT_COUNT)) - set(slots)) == EXPECTED_SKIPPED[context]
    for e in records:
        slot = int(e['absolute_slot'])
        assert int(e['source_phase_index']) == slot % 16, (context, slot, e['source_phase_index'])
    assert events[-1]['event'] == 'post_window_endpoint_witness'
    assert int(events[-1]['source_phase_index']) == 16
    assert float(events[-1]['time_ms']) > float(records[-1]['time_ms'])
    times = [float(e['time_ms']) for e in events]
    assert all(b > a for a, b in zip(times, times[1:])), (context, times)
    return [{
        'event': e['event'],
        'time_ms': float(e['time_ms']),
        'source_phase_index': int(e['source_phase_index']),
        'absolute_slot': e.get('absolute_slot'),
        'png': e['png'],
        'png_sha256': e['png_sha256'],
        'sapling_mesh_digest': e['sapling_mesh_digest'],
    } for e in events]


def ideal_timeline(context: str, clean_events: list):
    phase_event = {}
    for e in clean_events:
        phase_event.setdefault(int(e['source_phase_index']), e)
    assert set(phase_event) == set(range(17))
    ideal = []
    p0 = phase_event[0]
    ideal.append({
        'event': 'ideal_authored_slot', 'time_ms': 0.0, 'source_phase_index': 0,
        'absolute_slot': 0, 'png': p0['png'], 'png_sha256': p0['png_sha256'],
        'sapling_mesh_digest': p0['sapling_mesh_digest'],
    })
    for slot in range(1, SLOT_COUNT):
        phase = slot % 16
        e = phase_event[phase]
        ideal.append({
            'event': 'ideal_authored_slot', 'time_ms': slot * STEP_MS,
            'source_phase_index': phase, 'absolute_slot': slot,
            'png': e['png'], 'png_sha256': e['png_sha256'],
            'sapling_mesh_digest': e['sapling_mesh_digest'],
        })
    endpoint = phase_event[16]
    ideal.append({
        'event': 'ideal_authored_endpoint', 'time_ms': SLOT_COUNT * STEP_MS,
        'source_phase_index': 16, 'absolute_slot': None,
        'png': endpoint['png'], 'png_sha256': endpoint['png_sha256'],
        'sapling_mesh_digest': endpoint['sapling_mesh_digest'],
    })
    times = [e['time_ms'] for e in ideal]
    assert all(b > a for a, b in zip(times, times[1:])), (context, times)
    assert abs(ideal[-1]['time_ms'] - 1500.0) < 1e-9
    return ideal


def state_at(events, t_ms):
    out = events[0]
    for e in events[1:]:
        if e['time_ms'] <= t_ms + 1e-9:
            out = e
        else:
            break
    return out


def cadence_aligned_timeline(clean):
    """Inspection-only alignment: make the first presented frame t=0 while preserving every later interval and skip."""
    records = [dict(e) for e in clean if e['event'] == 'clean_frame_post_draw']
    endpoint = dict(clean[-1])
    assert records, 'missing clean frame_post_draw records'
    t0 = float(records[0]['time_ms'])
    out = []
    for e in records:
        e['time_ms'] = float(e['time_ms']) - t0
        e['review_alignment'] = 'FIRST_PRESENTED_FRAME_TO_ZERO_ONLY'
        out.append(e)
    endpoint['time_ms'] = float(endpoint['time_ms']) - t0
    endpoint['review_alignment'] = 'FIRST_PRESENTED_FRAME_TO_ZERO_ONLY'
    out.append(endpoint)
    times = [float(e['time_ms']) for e in out]
    assert abs(times[0]) <= 1e-9
    assert all(b > a for a, b in zip(times, times[1:])), times
    return out, t0


def interval_stats(clean):
    records = [e for e in clean if e['event'] == 'clean_frame_post_draw']
    times = [float(e['time_ms']) for e in records]
    intervals = [b-a for a,b in zip(times,times[1:])]
    assert intervals
    return {
        'count': len(intervals),
        'minimum_ms': min(intervals),
        'mean_ms': sum(intervals)/len(intervals),
        'maximum_ms': max(intervals),
        'minimum_vs_authored_step': min(intervals)/STEP_MS,
        'mean_vs_authored_step': (sum(intervals)/len(intervals))/STEP_MS,
        'maximum_vs_authored_step': max(intervals)/STEP_MS,
    }


def skipped_windows(context, clean, skipped):
    records = [e for e in clean if e['event'] == 'clean_frame_post_draw']
    out = []
    for slot in skipped:
        prev = max((e for e in records if int(e['absolute_slot']) < slot), key=lambda e: int(e['absolute_slot']), default=clean[0])
        nxt = min((e for e in records if int(e['absolute_slot']) > slot), key=lambda e: int(e['absolute_slot']))
        out.append({
            'absolute_slot': slot,
            'skipped_phase': slot % 16,
            'authored_due_ms': slot * STEP_MS,
            'previous_presented_slot': prev.get('absolute_slot'),
            'previous_presented_phase': int(prev['source_phase_index']),
            'previous_presented_time_ms': float(prev['time_ms']),
            'next_presented_slot': int(nxt['absolute_slot']),
            'next_presented_phase': int(nxt['source_phase_index']),
            'next_presented_time_ms': float(nxt['time_ms']),
            'direct_presented_phase_jump': f"{int(prev['source_phase_index'])}->{int(nxt['source_phase_index'])}",
        })
    return out


def write_ffconcat(path: Path, events: list, artifact_root: Path, tail_ms=TAIL_HOLD_MS):
    lines = ['ffconcat version 1.0']
    for i, e in enumerate(events):
        img = (artifact_root / e['png']).resolve()
        assert img.is_file(), img
        if i + 1 < len(events):
            dur = (float(events[i+1]['time_ms']) - float(e['time_ms'])) / 1000.0
        else:
            dur = tail_ms / 1000.0
        assert dur > 0
        s = str(img).replace("'", "'\\''")
        lines.append(f"file '{s}'")
        lines.append('option framerate 1000')
        lines.append(f"duration {dur:.9f}")
    s = str((artifact_root / events[-1]['png']).resolve()).replace("'", "'\\''")
    lines.append(f"file '{s}'")
    lines.append('option framerate 1000')
    path.write_text('\n'.join(lines) + '\n')


def html_for(report):
    payload = json.dumps(report, separators=(',', ':')).replace('</', '<\\/')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AXM Nature flutter — clean vs ideal review</title>
<style>
:root{{font-family:system-ui,sans-serif;color-scheme:dark;background:#111;color:#eee}}body{{margin:0;padding:18px}}h1{{font-size:20px;margin:0 0 8px}}.truth{{padding:10px 12px;border:1px solid #666;border-radius:8px;background:#191919;margin-bottom:14px;line-height:1.35}}.controls{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:12px 0}}button,select,input{{font:inherit}}button{{padding:6px 10px}}input[type=range]{{width:min(760px,90vw)}}.panels{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.panel{{border:1px solid #444;border-radius:8px;padding:8px;background:#181818}}.panel img{{width:100%;height:auto;display:block;background:#000}}.meta{{font-family:ui-monospace,monospace;font-size:12px;white-space:pre-wrap;margin-top:7px}}.different{{outline:3px solid #ddd}}.skips{{margin-top:12px;display:flex;flex-wrap:wrap;gap:6px}}.status{{font-family:ui-monospace,monospace;font-size:13px}}.note{{font-size:13px;color:#ccc;margin-top:8px}}@media(max-width:900px){{.panels{{grid-template-columns:1fr}}}}
</style></head><body>
<h1>Nature leaf flutter — measured clean presentation vs ideal authored schedule</h1>
<div class="truth"><strong>Review surface only.</strong> Left = telemetry-bound reconstruction of the clean no-capture proof-host stream. Right = unobserved ideal authored 31.25 ms direct-source schedule using the same exact real-Godot source-state images. This browser is <strong>not timing authority</strong>; it does not turn reconstruction into direct framebuffer capture, target-device evidence, source retiming, or Art/QA acceptance.</div>
<div class="controls"><label>Camera <select id="ctx"><option>path_eye</option><option>elevated_oblique</option></select></label><label>Clock <select id="mode"><option value="raw">Raw telemetry clock</option><option value="aligned">Cadence-aligned review</option></select></label><button id="play">Play</button><button id="reset">Reset</button><label>Speed <select id="speed"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label><span class="status" id="clock"></span></div>
<div><input id="scrub" type="range" min="0" max="1805" step="0.1" value="0"></div>
<div class="note" id="modeNote"></div>
<div class="panels"><div class="panel" id="cleanPanel"><strong>Clean measured presentation</strong><img id="cleanImg"><div class="meta" id="cleanMeta"></div></div><div class="panel" id="idealPanel"><strong>Ideal authored source schedule</strong><img id="idealImg"><div class="meta" id="idealMeta"></div></div></div>
<div class="skips" id="skips"></div>
<script>const DATA={payload};let t=0,playing=false,last=null;const $=id=>document.getElementById(id);function stateAt(events,x){{let s=events[0];for(const e of events){{if(e.time_ms<=x+1e-7)s=e;else break}}return s}}function activeClean(c){{return $('mode').value==='aligned'?c.cadence_aligned_clean_events:c.raw_clean_events}}function reviewEnd(c){{return $('mode').value==='aligned'?c.aligned_review_end_ms:c.raw_review_end_ms}}function render(){{const c=DATA.contexts[$('ctx').value],cleanEvents=activeClean(c),cl=stateAt(cleanEvents,t),id=stateAt(c.ideal_events,t);$('cleanImg').src=cl.png;$('idealImg').src=id.png;$('cleanMeta').textContent=`t=${{t.toFixed(1)}} ms\nphase=${{cl.source_phase_index}} slot=${{cl.absolute_slot}}\nevent=${{cl.event}}`;$('idealMeta').textContent=`t=${{t.toFixed(1)}} ms\nphase=${{id.source_phase_index}} slot=${{id.absolute_slot}}\nevent=${{id.event}}`;$('clock').textContent=`${{t.toFixed(1)}} ms / ${{reviewEnd(c).toFixed(1)}} ms · ${{cl.source_phase_index===id.source_phase_index?'same source state':'DIFFERENT source state'}}`;$('cleanPanel').classList.toggle('different',cl.source_phase_index!==id.source_phase_index);$('scrub').max=reviewEnd(c);$('scrub').value=t;$('modeNote').textContent=$('mode').value==='aligned'?`Cadence-aligned review subtracts only the first clean frame_post_draw offset (${{c.first_presented_offset_ms.toFixed(3)}} ms) so the first presented clean frame starts at t=0. It preserves all later measured intervals and skipped source slots. This is inspection alignment only, not timing authority or source retiming.`:'Raw telemetry clock preserves the exact clean frame_post_draw offsets against the authored due-time reference, including the initial proof-host presentation latency.';$('skips').innerHTML='';for(const s of c.skipped_windows){{const b=document.createElement('button');b.textContent=`skip slot ${{s.absolute_slot}} / phase ${{s.skipped_phase}}`;b.onclick=()=>{{t=s.authored_due_ms;playing=false;render()}};$('skips').appendChild(b)}}}}function tick(now){{if(!playing)return;if(last===null)last=now;const dt=(now-last)*parseFloat($('speed').value);last=now;t+=dt;const end=reviewEnd(DATA.contexts[$('ctx').value]);if(t>=end){{t=end;playing=false;$('play').textContent='Play'}}render();if(playing)requestAnimationFrame(tick)}}$('play').onclick=()=>{{playing=!playing;$('play').textContent=playing?'Pause':'Play';last=null;if(playing)requestAnimationFrame(tick)}};$('reset').onclick=()=>{{playing=false;$('play').textContent='Play';t=0;render()}};$('scrub').oninput=e=>{{playing=false;$('play').textContent='Play';t=parseFloat(e.target.value);render()}};for(const id of ['ctx','mode'])$(id).onchange=()=>{{playing=false;$('play').textContent='Play';t=0;render()}};render();</script></body></html>'''


def build(artifact_root: Path, out: Path):
    manifest, summary = load_reconstruction(artifact_root)
    verify_images(artifact_root, manifest)
    out.mkdir(parents=True, exist_ok=True)
    dst = out / 'static-rendered'
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(artifact_root / 'static-rendered', dst)
    report = {
        'schema':'axm.vfx-nature-leaf-flutter-clean-vs-ideal-review/v0.1',
        'state':'PASS_TELEMETRY_BOUND_CLEAN_VS_IDEAL_REVIEW_SURFACE',
        'retained_reconstruction_state':manifest['state'],
        'accepted_receiver_head':EXPECTED_RECEIVER,
        'nature_vfx_effect_head':EXPECTED_EFFECT,
        'clean_timing_head':EXPECTED_TIMING,
        'authored_source_step_ms':STEP_MS,
        'authored_unique_phase_count':16,
        'scheduled_slots_per_context':SLOT_COUNT,
        'clean_presented_total':92,
        'clean_scheduled_total':96,
        'direct_live_capture_of_clean_stream':False,
        'interpolation_added':False,
        'source_retimed':False,
        'ideal_schedule_is_counterfactual_reference_not_observed_runtime':True,
        'browser_is_timing_authority':False,
        'final_perceptual_acceptance_claimed':False,
        'contexts':{}
    }
    for context in ('path_eye','elevated_oblique'):
        c = manifest['contexts'][context]
        clean = clean_timeline(context, c)
        ideal = ideal_timeline(context, clean)
        aligned, first_offset = cadence_aligned_timeline(clean)
        skips = skipped_windows(context, clean, EXPECTED_SKIPPED[context])
        stats = interval_stats(clean)
        raw_review_end = max(float(clean[-1]['time_ms']), float(ideal[-1]['time_ms'])) + TAIL_HOLD_MS
        aligned_review_end = max(float(aligned[-1]['time_ms']), float(ideal[-1]['time_ms'])) + TAIL_HOLD_MS
        ctx = {
            'clean_presented_slots':EXPECTED_PRESENTED[context],
            'clean_skipped_slots':EXPECTED_SKIPPED[context],
            'clean_endpoint_ms':float(clean[-1]['time_ms']),
            'first_presented_offset_ms':first_offset,
            'ideal_endpoint_ms':1500.0,
            'raw_review_end_ms':raw_review_end,
            'aligned_review_end_ms':aligned_review_end,
            'clean_frame_post_draw_interval_stats':stats,
            'skipped_windows':skips,
            'raw_clean_events':clean,
            'cadence_aligned_clean_events':aligned,
            'ideal_events':ideal,
        }
        report['contexts'][context] = ctx
        write_ffconcat(out / f'raw-clean-{context}.ffconcat', clean, out, TAIL_HOLD_MS)
        write_ffconcat(out / f'ideal-{context}.ffconcat', ideal, out, TAIL_HOLD_MS)
        write_ffconcat(out / f'cadence-aligned-clean-{context}.ffconcat', aligned, out, TAIL_HOLD_MS)
    for ctx in report['contexts'].values():
        for collection in ('raw_clean_events','cadence_aligned_clean_events','ideal_events'):
            for e in ctx[collection]:
                e['png'] = e['png'].replace('static-rendered/', 'static-rendered/')
    (out/'comparison-manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (out/'review.html').write_text(html_for(report))
    summary_out = {
        'state': report['state'],
        'clean_presented_total':'92/96',
        'path_eye_skipped_slots':EXPECTED_SKIPPED['path_eye'],
        'elevated_oblique_skipped_slots':EXPECTED_SKIPPED['elevated_oblique'],
        'ideal_schedule':'48 slots/context at 31.25 ms plus exact neutral endpoint at 1500 ms',
        'cadence_aligned_review':'subtracts first clean frame_post_draw offset only; preserves all later intervals and skips; review alignment only',
        'direct_live_capture_of_clean_stream':False,
        'final_perceptual_acceptance_claimed':False,
    }
    (out/'summary.json').write_text(json.dumps(summary_out,indent=2,sort_keys=True)+'\n')
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--artifact-root',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    report=build(args.artifact_root,args.output)
    print(json.dumps({
        'state':report['state'],
        'path_eye_interval_stats':report['contexts']['path_eye']['clean_frame_post_draw_interval_stats'],
        'elevated_oblique_interval_stats':report['contexts']['elevated_oblique']['clean_frame_post_draw_interval_stats'],
        'skipped_slots_total':sum(len(c['clean_skipped_slots']) for c in report['contexts'].values()),
    },indent=2))
if __name__=='__main__': main()
