# Environment Composition Baseline 001

This is the first environment-scale integration proof for the design constellation. It lives in `axm-map-design` because map-design owns composition; it does **not** give map-design ownership of building, nature, object, or weather source assets.

The study deliberately uses explicit `PROXY_ONLY` geometry for four asset classes: map surface, building, nature, and object. Weather is represented only as directional context. The aim is to make scale, spacing, readable-path clearance, asset identity, and retained scene evidence falsifiable before the building/nature/object/weather departments have mature source assets.

Run:

```bash
python tools/environment_composition.py
python -m unittest discover -s tests -v
```

Generated evidence under `evidence/environment_baseline_001/`:

- `scene.obj` — deterministic text 3D scene containing all proxy asset classes;
- `top.svg` — deterministic top-view composition evidence from the same source manifest;
- `evidence.json` — exact bounded evidence result and source digest.

A PASS means only that the exact proxy composition contains the required asset classes, keeps the declared central path clear, respects the declared minimum proxy spacing, retains an explicit nonzero weather-context direction, and keeps every composed asset labelled `PROXY_ONLY`.

It does **not** prove visual quality, believable architecture or botany, traversal/gameplay, final department assets, weather simulation, lighting/materials, collision, target-engine import, runtime performance, or Art Director acceptance.

## Replacement-by-contract handoff

As `axm-building-design`, `axm-nature-design`, `axm-object-design`, and `axm-weather-design` produce source-owned candidates, replace one proxy at a time while preserving exact provenance and the same composition questions. A real department asset must never inherit a PASS merely because the proxy it replaces passed.
