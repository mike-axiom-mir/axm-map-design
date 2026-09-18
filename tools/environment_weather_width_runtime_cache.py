from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "axm.runtime-weather-width-cadence-cache-observation/v0.1"
REPORT_SCHEMA = "axm.runtime-weather-width-cadence-cache-evidence/v0.1"
EXACT_VFX_PARENT_HEAD = "bbc8721a8af60b11e660773786426965c421e4ff"
INTERVAL_MS = 31.25
CONTEXTS = ("path_eye", "elevated_oblique")
REVIEW_INDICES = (0, 8, 16)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary(mode: dict[str, Any]) -> dict[str, Any]:
    samples = mode["samples"]
    submit = [float(row["submit_lateness_ms"]) for row in samples]
    update_end = [float(row["update_end_lateness_ms"]) for row in samples]
    draw = [float(row["draw_lateness_ms"]) for row in samples]
    update_duration = [float(row["update_duration_ms"]) for row in samples]
    post_draw_wait = [float(row["post_draw_wait_ms"]) for row in samples]
    return {
        "sample_count": len(samples),
        "maximum_submit_lateness_ms": max(submit),
        "submit_deadline_miss_count": sum(value > INTERVAL_MS for value in submit),
        "maximum_update_end_lateness_ms": max(update_end),
        "update_end_deadline_miss_count": sum(value > INTERVAL_MS for value in update_end),
        "maximum_post_draw_lateness_ms": max(draw),
        "post_draw_deadline_miss_count": sum(value > INTERVAL_MS for value in draw),
        "mean_update_duration_ms": sum(update_duration) / len(update_duration),
        "maximum_update_duration_ms": max(update_duration),
        "mean_post_draw_wait_ms": sum(post_draw_wait) / len(post_draw_wait),
        "maximum_post_draw_wait_ms": max(post_draw_wait),
    }


def verify(receipt: dict[str, Any], frames_root: Path) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    checks["schema"] = receipt.get("schema") == SCHEMA
    checks["observer_completed"] = receipt.get("state") == "OBSERVED_REBUILD_VS_PREBUILT_MESH_SWAP"
    checks["exact_vfx_parent_head"] = receipt.get("exact_vfx_parent_head") == EXACT_VFX_PARENT_HEAD
    checks["receiving_head"] = receipt.get("receiving_head") == EXACT_VFX_PARENT_HEAD
    checks["exact_interval"] = abs(float(receipt.get("interval_s", -1.0)) - 0.03125) <= 1e-12
    contexts = receipt.get("contexts")
    checks["contexts"] = isinstance(contexts, dict) and set(contexts) == set(CONTEXTS)

    context_metrics: dict[str, Any] = {}
    visual_pairs: list[dict[str, Any]] = []
    if checks["contexts"]:
        for context in CONTEXTS:
            payload = contexts[context]
            cache = payload.get("cache", {})
            rebuild = payload.get("rebuild", {})
            cached = payload.get("cached_swap", {})
            visuals = payload.get("visuals", {})
            context_ok = (
                cache.get("state") == "PASS_EXACT_17_STATE_CONTEXT_CACHE"
                and rebuild.get("state") == "OBSERVED_EXACT_17_STATE_RUNTIME_MODE"
                and cached.get("state") == "OBSERVED_EXACT_17_STATE_RUNTIME_MODE"
                and visuals.get("state") == "PASS_RETAINED_RUNTIME_VISUAL_PAIRS"
                and len(rebuild.get("samples", [])) == 17
                and len(cached.get("samples", [])) == 17
                and float(cache.get("maximum_projected_width_residual_px", 999.0)) <= 0.05
            )
            checks[f"{context}_structure"] = context_ok
            if not context_ok:
                continue
            source_identity_ok = True
            for index, (before, after) in enumerate(zip(rebuild["samples"], cached["samples"])):
                source_identity_ok &= (
                    int(before.get("index", -1)) == index
                    and int(after.get("index", -1)) == index
                    and abs(float(before.get("scheduled_time_s", -1.0)) - index * 0.03125) <= 1e-12
                    and abs(float(after.get("scheduled_time_s", -1.0)) - index * 0.03125) <= 1e-12
                    and before.get("weather_field_digest") == after.get("weather_field_digest")
                    and before.get("weather_width_profile_digest") == after.get("weather_width_profile_digest")
                    and before.get("sapling_mesh_digest") == after.get("sapling_mesh_digest")
                )
            checks[f"{context}_source_identity"] = source_identity_ok
            before_metrics = _summary(rebuild)
            after_metrics = _summary(cached)
            context_metrics[context] = {
                "rebuild": before_metrics,
                "cached_swap": after_metrics,
                "cache_build_duration_ms": float(cache["build_duration_ms"]),
                "observed_buffer_delta_bytes": int(cache["observed_buffer_delta_bytes"]),
                "observed_texture_delta_bytes": int(cache["observed_texture_delta_bytes"]),
                "maximum_projected_width_residual_px": float(cache["maximum_projected_width_residual_px"]),
                "mean_update_duration_reduction_ms": before_metrics["mean_update_duration_ms"] - after_metrics["mean_update_duration_ms"],
                "maximum_update_duration_reduction_ms": before_metrics["maximum_update_duration_ms"] - after_metrics["maximum_update_duration_ms"],
                "submit_deadline_miss_reduction": before_metrics["submit_deadline_miss_count"] - after_metrics["submit_deadline_miss_count"],
                "post_draw_deadline_miss_reduction": before_metrics["post_draw_deadline_miss_count"] - after_metrics["post_draw_deadline_miss_count"],
            }

            pairs = visuals.get("pairs", [])
            checks[f"{context}_review_pair_count"] = [int(row.get("index", -1)) for row in pairs] == list(REVIEW_INDICES)
            for row in pairs:
                index = int(row["index"])
                before_path = frames_root / f"runtime-cache-rebuild-{context}-{index:02d}.png"
                after_path = frames_root / f"runtime-cache-cached-{context}-{index:02d}.png"
                exists = before_path.is_file() and after_path.is_file()
                same = exists and before_path.read_bytes() == after_path.read_bytes()
                visual_pairs.append(
                    {
                        "context": context,
                        "index": index,
                        "rebuild_path": str(before_path),
                        "cached_path": str(after_path),
                        "rebuild_sha256": _sha256(before_path) if exists else None,
                        "cached_sha256": _sha256(after_path) if exists else None,
                        "byte_identical": same,
                    }
                )

    checks["all_visual_review_pairs_byte_identical"] = len(visual_pairs) == 6 and all(row["byte_identical"] for row in visual_pairs)
    structural = all(checks.values())
    cached_submit_clear = structural and all(
        context_metrics[context]["cached_swap"]["submit_deadline_miss_count"] == 0 for context in CONTEXTS
    )
    cached_post_draw_clear = structural and all(
        context_metrics[context]["cached_swap"]["post_draw_deadline_miss_count"] == 0 for context in CONTEXTS
    )
    update_reduced = structural and all(
        context_metrics[context]["mean_update_duration_reduction_ms"] > 0.0 for context in CONTEXTS
    )

    if not structural:
        state = "FAIL_RUNTIME_CACHE_EVIDENCE_INTEGRITY"
    elif cached_submit_clear and cached_post_draw_clear and update_reduced:
        state = "PASS_PREBUILT_MESH_SWAP_FULL_PROOF_HOST_CADENCE_CANDIDATE"
    elif cached_submit_clear and update_reduced:
        state = "PASS_PREBUILT_MESH_SWAP_SUBMIT_CADENCE__HOLD_POST_DRAW"
    elif update_reduced:
        state = "PASS_PREBUILT_MESH_SWAP_UPDATE_COST_REDUCTION__HOLD_CADENCE"
    else:
        state = "HOLD_PREBUILT_MESH_SWAP_NO_MEASURED_UPDATE_WIN"

    return {
        "schema": REPORT_SCHEMA,
        "state": state,
        "exact_vfx_parent_head": EXACT_VFX_PARENT_HEAD,
        "source_interval_ms": INTERVAL_MS,
        "checks": checks,
        "context_metrics": context_metrics,
        "visual_pairs": visual_pairs,
        "cached_submit_deadline_clear": cached_submit_clear,
        "cached_post_draw_deadline_clear": cached_post_draw_clear,
        "mean_update_duration_reduced_in_both_contexts": update_reduced,
        "representation_tradeoff": "PREBUILT_MESH_RESOURCE_SET_REPLACES_ONE_MUTABLE_WEATHER_AND_SAPLING_MESH_DURING_CACHED_MODE",
        "truth_boundary": "This report compares exact inherited per-state mesh rebuilds against a prebuilt finite-state mesh-resource swap candidate in the same Godot proof process. Byte-identical retained review frames establish no observed visual change only for six exact review pairs. Timing and RenderingServer memory counters belong only to this proof host. VFX source authority, stable mutable mesh-resource identity, arbitrary streams/cameras, target devices, gameplay, final Art Direction, CANON and production readiness remain outside this report.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--frames-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    report = verify(receipt, args.frames_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "state": report["state"],
        "cached_submit_deadline_clear": report["cached_submit_deadline_clear"],
        "cached_post_draw_deadline_clear": report["cached_post_draw_deadline_clear"],
        "context_metrics": report["context_metrics"],
    }, indent=2, sort_keys=True))
    if report["state"] == "FAIL_RUNTIME_CACHE_EVIDENCE_INTEGRITY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
