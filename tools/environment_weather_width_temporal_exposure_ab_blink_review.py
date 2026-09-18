from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import shutil
from pathlib import Path
from typing import Any

try:
    from . import environment_weather_width_temporal_exposure_readability as readability
except ImportError:
    import environment_weather_width_temporal_exposure_readability as readability

legacy = readability.legacy

SCHEMA = "axm.environment-current-world-weather-width-temporal-exposure-ab-blink-review/v0.1"
STATUS = "PASS_OPACITY_NORMALIZED_TEMPORAL_EXPOSURE_AB_BLINK_REVIEW_SURFACE"
DECISION = "REVIEW_SURFACE_ONLY_NO_ART_OR_QA_PREFERENCE"
SELECTED_PHASES_US = (0, 125000, 312500, 500000)


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_html(report: dict[str, Any], path: str | Path) -> None:
    cards: list[str] = []
    for context in legacy.CONTEXTS:
        rows = report.get("contexts", {}).get(context, {}).get("samples", [])
        for row in rows:
            phase_ms = float(row["phase_us"]) / 1000.0
            changed = int(row["changed_pixels"])
            fraction = float(row["changed_fraction"]) * 100.0
            max_delta = int(row["maximum_rgb_channel_delta_lsb"])
            control = html.escape(str(row["control_copy"]))
            candidate = html.escape(str(row["candidate_copy"]))
            cards.append(
                f"""
                <article class="card" data-context="{html.escape(context)}" data-phase="{phase_ms:g}">
                  <header><strong>{html.escape(context)}</strong> · {phase_ms:g} ms</header>
                  <div class="stack">
                    <img src="{control}" alt="control {html.escape(context)} {phase_ms:g} ms">
                    <img class="candidate" src="{candidate}" alt="candidate {html.escape(context)} {phase_ms:g} ms">
                  </div>
                  <p>{changed:,} changed px · {fraction:.5f}% frame · max {max_delta} RGB LSB</p>
                </article>
                """
            )

    candidate_head = html.escape(str(report.get("candidate_head", "")))
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AXM Weather normalized temporal exposure A/B blink review</title>
<style>
:root {{ color-scheme: dark; font-family: system-ui, sans-serif; background:#111; color:#eee; }}
body {{ margin:0; padding:24px; }}
main {{ max-width:1400px; margin:auto; }}
.controls {{ position:sticky; top:0; z-index:3; background:#111e; padding:12px 0; backdrop-filter:blur(6px); }}
button {{ font:inherit; padding:8px 12px; margin-right:8px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:18px; }}
.card {{ border:1px solid #444; border-radius:10px; overflow:hidden; background:#181818; }}
.card header,.card p {{ padding:10px 12px; margin:0; }}
.stack {{ position:relative; aspect-ratio:55/36; overflow:hidden; background:#000; }}
.stack img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:contain; image-rendering:auto; }}
.stack img.candidate {{ animation:blink 1s steps(1,end) infinite; }}
body.paused .stack img.candidate {{ animation-play-state:paused; opacity:.5; }}
body.candidate-only .stack img:first-child {{ opacity:0; }}
body.candidate-only .stack img.candidate {{ animation:none; opacity:1; }}
body.control-only .stack img.candidate {{ animation:none; opacity:0; }}
@keyframes blink {{ 0%,49% {{opacity:0}} 50%,100% {{opacity:1}} }}
small {{ color:#bbb; }}
code {{ overflow-wrap:anywhere; }}
</style>
</head>
<body>
<main>
<h1>Weather normalized temporal exposure · exact retained A/B blink review</h1>
<p>Candidate head <code>{candidate_head}</code>. This page alternates exact retained control/candidate PNGs only; it does not modify source pixels or effect parameters.</p>
<div class="controls">
<button onclick="document.body.className=''">Blink</button>
<button onclick="document.body.className='paused'">50/50 overlay</button>
<button onclick="document.body.className='control-only'">Control</button>
<button onclick="document.body.className='candidate-only'">Candidate</button>
</div>
<div class="grid">{''.join(cards)}</div>
<p><small>Review aid only. A visual difference is not an aesthetic preference, smoothing proof, physical-weather claim, gameplay/physics claim, target-device performance claim, CANON decision or production-readiness claim.</small></p>
</main>
</body>
</html>
"""
    Path(path).write_text(document, encoding="utf-8")


def build_review(
    payload: dict[str, Any],
    receipt: dict[str, Any],
    normalized_report: dict[str, Any],
    image_root: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    root = Path(image_root)
    out = Path(output_dir)
    images_out = out / "images"
    images_out.mkdir(parents=True, exist_ok=True)

    base = readability.verify_readability_review(payload, receipt, normalized_report, root)
    base_green = base.get("state") == readability.STATUS and all(base.get("checks", {}).values())

    selected_complete = True
    selected_hash_bound = True
    nonzero_visible = True
    phase0_equivalent = True
    context_reports: dict[str, Any] = {}

    for context in legacy.CONTEXTS:
        samples = receipt.get("contexts", {}).get(context, {}).get("samples", [])
        by_phase = {int(row.get("phase_us", -1)): row for row in samples}
        rows: list[dict[str, Any]] = []
        for phase_us in SELECTED_PHASES_US:
            sample = by_phase.get(phase_us)
            if sample is None:
                selected_complete = False
                continue
            control = sample.get("control_frame", {})
            candidate = sample.get("candidate_frame", {})
            if not legacy._verify_frame(control, root) or not legacy._verify_frame(candidate, root):
                selected_hash_bound = False
                continue

            control_src = root / str(control["png_path"])
            candidate_src = root / str(candidate["png_path"])
            control_name = f"control-{context}-{phase_us:06d}us.png"
            candidate_name = f"candidate-{context}-{phase_us:06d}us.png"
            shutil.copyfile(control_src, images_out / control_name)
            shutil.copyfile(candidate_src, images_out / candidate_name)

            if _sha256(images_out / control_name) != str(control.get("png_sha256")):
                selected_hash_bound = False
            if _sha256(images_out / candidate_name) != str(candidate.get("png_sha256")):
                selected_hash_bound = False

            metrics = readability._pair_metrics(
                root / str(control["raw_path"]),
                root / str(candidate["raw_path"]),
            )
            changed = int(metrics["changed_pixels"])
            max_delta = int(metrics["maximum_rgb_channel_delta_lsb"])
            if phase_us == 0:
                phase0_equivalent = phase0_equivalent and max_delta <= 1
            elif changed <= 0:
                nonzero_visible = False

            rows.append(
                {
                    "phase_us": phase_us,
                    "control_copy": f"images/{control_name}",
                    "candidate_copy": f"images/{candidate_name}",
                    "control_sha256": str(control.get("png_sha256")),
                    "candidate_sha256": str(candidate.get("png_sha256")),
                    **metrics,
                }
            )
        if len(rows) != len(SELECTED_PHASES_US):
            selected_complete = False
        context_reports[context] = {"samples": rows}

    checks = {
        "underlying_readability_review_recomputes_green": base_green,
        "all_selected_context_phase_pairs_are_present": selected_complete,
        "all_selected_pngs_reverify_exact_retained_hashes_after_copy": selected_hash_bound,
        "selected_nonzero_phases_have_direct_visual_delta": nonzero_visible,
        "selected_zero_lag_pairs_remain_within_one_rgb_lsb": phase0_equivalent,
    }

    report = {
        "schema": SCHEMA,
        "state": STATUS if all(checks.values()) else "FAIL",
        "decision": DECISION,
        "candidate_head": payload.get("receiving_head"),
        "presentation_policy": normalized_report.get("presentation_policy"),
        "selected_phases_us": list(SELECTED_PHASES_US),
        "contexts": context_reports,
        "checks": checks,
        "truth_boundary": (
            "PASS proves only that an offline A/B blink/overlay review page was built from exact hash-bound retained "
            "real-Godot control/candidate PNGs for selected review phases of the unchanged opacity-normalized Weather "
            "candidate. It does not establish aesthetic preference, human-perceived smoothness, physical weather, "
            "gameplay or physics behavior, arbitrary-camera equivalence, target-device performance, Art/Visual-QA "
            "acceptance, CANON or production readiness."
        ),
    }
    return report


def exercise_selected_frame_negative_control(
    payload: dict[str, Any],
    receipt: dict[str, Any],
    normalized_report: dict[str, Any],
    image_root: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    mutated = copy.deepcopy(receipt)
    first_context = legacy.CONTEXTS[0]
    for sample in mutated["contexts"][first_context]["samples"]:
        if int(sample.get("phase_us", -1)) == SELECTED_PHASES_US[0]:
            sample["candidate_frame"]["png_sha256"] = "0" * 64
            break
    return build_review(payload, mutated, normalized_report, image_root, output_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--normalized-report", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    report = build_review(
        _load(args.payload),
        _load(args.receipt),
        _load(args.normalized_report),
        args.image_root,
        out,
    )
    (out / "ab_blink_review.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_html(report, out / "ab_blink_review.html")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
