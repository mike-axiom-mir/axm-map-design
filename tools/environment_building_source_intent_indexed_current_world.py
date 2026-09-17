#!/usr/bin/env python3
"""Environment gate for the exact 604-vertex source-intent indexed Building receiver.

Consumes the Building Geometry source-intent indexed candidate as a donor, renders it in
Map's existing multi-asset current world, and compares it with the active segmented
rollback and the already-reviewed 312-vertex consumer. This is a review-target proof,
not default adoption, Runtime/device certification, or Technical-Art transport approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

SCHEMA = "axm.environment-building-source-intent-indexed-current-world/v0.1"
GEOMETRY_EVIDENCE_SCHEMA = "axm.building-planar-role-indexed-geometry-evidence/v0.1"
GEOMETRY_CANDIDATE_SCHEMA = "axm.building-planar-role-indexed-geometry-candidate/v0.1"
GEOMETRY_HEAD = "b9b4ab63e23b9756ab79597e86ecc41ea75ea8b7"
GEOMETRY_RESULT = "PASS_SOURCE_INTENT_INDEXED_RENDER_DOMAIN_EXACT_CORNER_RECONSTRUCTION"
CANDIDATE_ID = "boundary-only-planar-role-source-intent-indexed-001"
CANDIDATE_SHA256 = "f6a831058de66901fd42704b1d8c1cf187b13a0919ae3719c03c4369f107e6c0"
PARENT_REPRESENTATION_ID = "boundary-only-planar-role-rectangle-render-001"
SOURCE_INTENT_HEAD = "0caa9ac9644f027350935240476bd0bf3bb66e18"
ACTIVE_ROLLBACK_HEAD = "7713cbe5863c3bc38dabb6236eb4b393401224b6"
REVIEWED_312_HEAD = "55e10a4fa700fb81020a95bd5143deca6a09f208"
EXPECTED_WIDTH_PROFILE_DIGEST = "8d61b2dc11f2508d186a1e469185badda7217803f7c4634fb2d951d8579c0dd5"
EXPECTED_WEATHER_WIDTH_OBSERVATIONS = 1224
WEATHER_WIDTH_RESIDUAL_LIMIT_PX = 0.05
ENVIRONMENT_PASS = "PASS_CURRENT_WORLD_SOURCE_INTENT_INDEXED_BUILDING_RECEIVER_REVIEW_READY"
ENVIRONMENT_HOLD = "HOLD_DEFAULT_ADOPTION_PENDING_ART_QA_TECHNICAL_ART_AND_TARGET_DEVICE_RUNTIME_REVIEW"
BUILDING_ASSET_ID = "source:building:service-pavilion-001"
RECEIPT_SCHEMA = "axm.environment-building-source-intent-indexed-receiving/v0.1"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def runtime_path(root: Path) -> Path:
    for path in (root / "candidate" / "runtime.json", root / "indexed" / "runtime.json", root / "runtime.json"):
        if path.exists():
            return path
    raise FileNotFoundError(root)


def rendered_dir(root: Path) -> Path:
    for path in (root / "candidate" / "rendered", root / "indexed" / "rendered", root / "rendered"):
        if path.is_dir():
            return path
    raise FileNotFoundError(root)


def runtime_rows(runtime: dict) -> dict[tuple[int, str, str], dict]:
    rows: dict[tuple[int, str, str], dict] = {}
    for sample in runtime.get("samples", []):
        idx = int(sample["index"])
        for camera, modes in sample.get("contexts", {}).items():
            for mode, payload in modes.items():
                rows[(idx, camera, mode)] = payload["runtime"]
    return rows


def delta_sets(candidate: dict, reference: dict) -> dict:
    if set(candidate) != set(reference):
        raise ValueError("runtime observation key drift")
    fields = ("draw_calls_in_frame", "objects_in_frame", "primitives_in_frame", "buffer_mem_bytes", "texture_mem_bytes")
    deltas = []
    for key in sorted(candidate):
        deltas.append({field: int(candidate[key][field]) - int(reference[key][field]) for field in fields})
    return {field: sorted({row[field] for row in deltas}) for field in fields}


def image_delta(a_path: Path, b_path: Path) -> dict:
    with Image.open(a_path).convert("RGB") as a, Image.open(b_path).convert("RGB") as b:
        if a.size != b.size:
            raise ValueError("image size drift")
        diff = ImageChops.difference(a, b)
        bbox = diff.getbbox()
        changed = 0
        over_one = 0
        max_channel = 0
        if bbox is not None:
            for px in diff.getdata():
                maximum = max(px)
                if maximum:
                    changed += 1
                    max_channel = max(max_channel, maximum)
                if maximum > 1:
                    over_one += 1
        return {
            "byte_identical": bbox is None,
            "changed_pixels": changed,
            "pixels_over_1_lsb": over_one,
            "max_channel_delta_lsb": max_channel,
            "bbox": list(bbox) if bbox is not None else None,
            "sha256_a": sha256_file(a_path),
            "sha256_b": sha256_file(b_path),
        }


def summarize_visuals(reference_root: Path, candidate_root: Path) -> dict:
    ref_dir = rendered_dir(reference_root)
    cand_dir = rendered_dir(candidate_root)
    names = sorted(path.name for path in ref_dir.glob("atmosphere-width-*.png"))
    if len(names) != 68 or names != sorted(path.name for path in cand_dir.glob("atmosphere-width-*.png")):
        raise ValueError("68-frame retained image set drift")
    rows = {name: image_delta(ref_dir / name, cand_dir / name) for name in names}
    changed = [name for name, row in rows.items() if not row["byte_identical"]]
    return {
        "frame_count": 68,
        "changed_frame_count": len(changed),
        "byte_identical_frame_count": 68 - len(changed),
        "max_changed_pixels": max(row["changed_pixels"] for row in rows.values()),
        "max_pixels_over_1_lsb": max(row["pixels_over_1_lsb"] for row in rows.values()),
        "max_channel_delta_lsb": max(row["max_channel_delta_lsb"] for row in rows.values()),
        "max_changed_fraction": max(row["changed_pixels"] / (1100 * 720) for row in rows.values()),
        "rows": rows,
    }


def find_building(sample: dict) -> dict:
    rows = [row for row in sample.get("static_source_meshes", []) if row.get("asset_id") == BUILDING_ASSET_ID]
    if len(rows) != 1:
        raise ValueError(f"expected one Building row, got {len(rows)}")
    return rows[0]


def canonical_sha256(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_geometry(geometry_evidence: dict, candidate: dict) -> None:
    if geometry_evidence.get("schema") != GEOMETRY_EVIDENCE_SCHEMA:
        raise ValueError("Geometry evidence schema drift")
    if geometry_evidence.get("result") != GEOMETRY_RESULT:
        raise ValueError("Geometry donor is not at expected scoped PASS")
    if geometry_evidence.get("exact_head") != GEOMETRY_HEAD:
        raise ValueError("Geometry exact-head drift")
    if geometry_evidence.get("candidate_id") != CANDIDATE_ID:
        raise ValueError("Geometry candidate identity drift")
    if geometry_evidence.get("candidate_sha256") != CANDIDATE_SHA256:
        raise ValueError("Geometry candidate digest drift")
    metrics = geometry_evidence.get("metrics", {})
    expected = {
        "source_triangle_corner_count": 1008,
        "render_vertex_count": 604,
        "index_count": 1008,
        "triangle_count": 336,
        "material_role_count": 5,
    }
    for key, value in expected.items():
        if int(metrics.get(key, -1)) != value:
            raise ValueError(f"Geometry metric drift for {key}: {metrics.get(key)}")
    if metrics.get("exact_corner_stream_reconstruction") is not True:
        raise ValueError("Geometry exact corner reconstruction no longer true")
    if canonical_sha256(candidate) != CANDIDATE_SHA256:
        raise ValueError("Geometry candidate canonical digest does not reproduce pinned identity")
    if candidate.get("schema") != GEOMETRY_CANDIDATE_SCHEMA or candidate.get("candidate_id") != CANDIDATE_ID:
        raise ValueError("Geometry candidate schema/id drift")
    if candidate.get("parent_representation_id") != PARENT_REPRESENTATION_ID:
        raise ValueError("Geometry parent representation drift")
    if len(candidate.get("vertices", [])) != 604 or len(candidate.get("indices", [])) != 1008 or len(candidate.get("triangles", [])) != 336:
        raise ValueError("Geometry candidate storage/count drift")


def verify_runtime(candidate_runtime: dict) -> dict:
    if candidate_runtime.get("environment_building_source_intent_indexed_result") != "CANDIDATE_SOURCE_INTENT_INDEXED_RECEIVER":
        raise ValueError("candidate current-world result marker missing")
    if candidate_runtime.get("environment_building_source_intent_indexed_geometry_head") != GEOMETRY_HEAD:
        raise ValueError("candidate Geometry head drift")
    if candidate_runtime.get("environment_building_source_intent_indexed_candidate_id") != CANDIDATE_ID:
        raise ValueError("candidate identity drift in runtime receipt")
    if candidate_runtime.get("source_width_profile_digest") != EXPECTED_WIDTH_PROFILE_DIGEST:
        raise ValueError("Weather width-profile digest drift")

    samples = candidate_runtime.get("samples", [])
    if len(samples) != 17:
        raise ValueError(f"expected 17 current-world states, got {len(samples)}")
    context_count = 0
    weather_width_count = 0
    max_weather_residual = 0.0
    storage = None
    for sample in samples:
        if sample.get("weather_width_profile_digest") != EXPECTED_WIDTH_PROFILE_DIGEST:
            raise ValueError("per-state Weather profile digest drift")
        building = find_building(sample)
        receipt = building.get("environment_building_source_intent_indexed", {})
        if receipt.get("schema") != RECEIPT_SCHEMA:
            raise ValueError("per-state source-intent receiver receipt schema drift")
        if receipt.get("geometry_head") != GEOMETRY_HEAD or receipt.get("candidate_id") != CANDIDATE_ID:
            raise ValueError("per-state Geometry provenance drift")
        this_storage = receipt.get("storage", {})
        if this_storage.get("surface_count") != 5 or this_storage.get("total_vertices") != 604 or this_storage.get("total_indices") != 1008 or this_storage.get("total_primitives") != 336:
            raise ValueError(f"per-state source-intent receiver storage drift: {this_storage}")
        if storage is None:
            storage = this_storage
        elif this_storage != storage:
            raise ValueError("source-intent receiver storage changed across states")
        for camera_context in sample.get("contexts", {}).values():
            context_count += len(camera_context)
            update = camera_context.get("candidate", {}).get("weather_update", {})
            count = int(update.get("measured_width_count", -1))
            if count != 36:
                raise ValueError(f"Weather projected-width count drift: {count}")
            residual = float(update.get("maximum_projected_width_residual_px", 999999.0))
            if residual > WEATHER_WIDTH_RESIDUAL_LIMIT_PX:
                raise ValueError(f"Weather projected-width residual exceeds gate: {residual}")
            weather_width_count += count
            max_weather_residual = max(max_weather_residual, residual)
    if context_count != 68:
        raise ValueError(f"expected 68 state/camera/presentation observations, got {context_count}")
    if weather_width_count != EXPECTED_WEATHER_WIDTH_OBSERVATIONS:
        raise ValueError(f"expected {EXPECTED_WEATHER_WIDTH_OBSERVATIONS} Weather width observations, got {weather_width_count}")
    return {
        "state_count": 17,
        "context_count": context_count,
        "weather_width_observation_count": weather_width_count,
        "maximum_weather_width_residual_px": max_weather_residual,
        "storage": storage,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry-evidence", type=Path, required=True)
    parser.add_argument("--geometry-candidate", type=Path, required=True)
    parser.add_argument("--active-root", type=Path, required=True)
    parser.add_argument("--reviewed-312-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--exact-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    geometry_evidence = load(args.geometry_evidence)
    geometry_candidate = load(args.geometry_candidate)
    verify_geometry(geometry_evidence, geometry_candidate)

    active_runtime = load(runtime_path(args.active_root))
    reviewed_runtime = load(runtime_path(args.reviewed_312_root))
    candidate_runtime = load(runtime_path(args.candidate_root))
    world = verify_runtime(candidate_runtime)

    candidate_rows = runtime_rows(candidate_runtime)
    reviewed_rows = runtime_rows(reviewed_runtime)
    active_rows = runtime_rows(active_runtime)
    if len(candidate_rows) != 68 or len(reviewed_rows) != 68 or len(active_rows) != 68:
        raise ValueError("runtime row count drift")

    candidate_vs_reviewed = delta_sets(candidate_rows, reviewed_rows)
    candidate_vs_active = delta_sets(candidate_rows, active_rows)
    for field in ("draw_calls_in_frame", "objects_in_frame", "texture_mem_bytes"):
        if candidate_vs_reviewed[field] != [0]:
            raise ValueError(f"source-intent candidate changed unexpected {field} vs reviewed 312: {candidate_vs_reviewed[field]}")
        if candidate_vs_active[field] != [0]:
            raise ValueError(f"source-intent candidate changed unexpected {field} vs active: {candidate_vs_active[field]}")
    if candidate_vs_reviewed["primitives_in_frame"] != [0]:
        raise ValueError(f"source-intent candidate changed primitives vs reviewed 312: {candidate_vs_reviewed['primitives_in_frame']}")
    if candidate_vs_active["primitives_in_frame"] != [180]:
        raise ValueError(f"source-intent candidate primitive residual vs active drift: {candidate_vs_active['primitives_in_frame']}")

    visuals_vs_reviewed = summarize_visuals(args.reviewed_312_root, args.candidate_root)
    visuals_vs_active = summarize_visuals(args.active_root, args.candidate_root)

    report = {
        "schema": SCHEMA,
        "state": ENVIRONMENT_PASS,
        "hold": ENVIRONMENT_HOLD,
        "exact_environment_head": args.exact_head,
        "geometry": {
            "head": GEOMETRY_HEAD,
            "result": GEOMETRY_RESULT,
            "candidate_id": CANDIDATE_ID,
            "candidate_sha256": CANDIDATE_SHA256,
            "source_intent_head": SOURCE_INTENT_HEAD,
            "vertices": 604,
            "indices": 1008,
            "triangles": 336,
            "material_roles": 5,
        },
        "comparison_heads": {
            "active_segmented_rollback": ACTIVE_ROLLBACK_HEAD,
            "reviewed_312_consumer": REVIEWED_312_HEAD,
        },
        "environment_adoption": False,
        "world_observations": world,
        "proof_host": {
            "candidate_vs_reviewed_312_delta_sets": candidate_vs_reviewed,
            "candidate_vs_active_delta_sets": candidate_vs_active,
        },
        "visuals": {
            "candidate_vs_reviewed_312": {key: value for key, value in visuals_vs_reviewed.items() if key != "rows"},
            "candidate_vs_active": {key: value for key, value in visuals_vs_active.items() if key != "rows"},
        },
        "decision": (
            "SOURCE_INTENT_INDEXED_RECEIVER_IS_CURRENT_WORLD_REVIEW_READY__DEFAULT_ADOPTION_HELD. "
            "The exact 604-vertex Geometry identity now has direct multi-asset Map evidence and can be compared truthfully with the existing 312 consumer and active segmented rollback without collapsing source, consumer, visual, transport or Runtime authority."
        ),
        "authority": {
            "hard_surface": "source render-equivalence intent",
            "geometry_topology": "604-vertex exact indexed realization",
            "environment": "current-world receiving comparison / rollback / handoff",
            "art_direction": "visual preference",
            "visual_qa": "independent visual acceptance",
            "technical_art": "transport/import exactness",
            "runtime": "target-host/device cost and adoption",
        },
        "handoff": [
            "Art Direction + Visual QA: inspect exact 604-vs-312 and 604-vs-active retained current-world differences before any default receiver choice.",
            "Technical Art: if the 604 identity is transported beyond this procedural Godot proof, bind the exact Geometry digest and prove attribute/index transport independently.",
            "Runtime: compare the exact 604 receiver against the 312 and active baselines on representative target hardware; proof-host counter deltas are not device acceptance.",
        ],
        "truth_boundary": (
            "This PASS establishes only that the exact Building Geometry 604-vertex source-intent indexed candidate can be reconstructed and rendered inside the retained Building + Nature + Object + Weather current world while the declared non-Building scene state and Weather width contract remain stable. "
            "Nonzero visual differences, any proof-host buffer delta, the +180 primitive residual versus active segmented, transport exactness and target-device performance remain separate facts. No default adoption, CANON or production readiness is implied."
        ),
        "four_root_gate": {
            "truth": "The 604 source-intent Geometry identity and the 312 consumer-generated identity remain separately measured instead of being relabelled equivalent.",
            "agency_non_domination": "Environment provides receiving evidence only; source, visual, transport and Runtime owners keep their decisions.",
            "continuity": "Active segmented rollback and reviewed 312 consumer remain pinned and directly comparable to the new exact 604 candidate.",
            "wisdom_before_speed": "Render the exact new source-intent candidate in the real multi-asset world before considering replacement or generic promotion.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
