# Environment Building infill + Weather source-width composition 001

Status: bounded receiving experiment in existing Map Environment PR #24.

## Question

Can the exact Building Materials successor already preferred by Visual QA and 3D Art Direction (`infill_coating.albedo #59666DFF`, material head `225cf82...`, profile `0c4834bf...`) be composed over the exact Environment current world that already carries the source-owned Building successor and the preferred Weather source-width presentation (`0d8b227...`) without changing any other declared world input?

## Exact parents

- Environment parent: Map PR #24 head `0d8b2279ecbba47b9696a951db9513883fbef6c5`, retained artifact `10452505109`, SHA-256 `4ffc52fc421d38a92829d3bf663ab5a48dfc144d16f31028f742ce19855512f4`, composition digest `132e877c8016d833f43d7a4cfe303ad2595913c757b85dd212192eafafed1973`.
- Building Materials donor: Building PR #3 head `225cf82a61ec1512553fda2785ca101a54a6bd30`, retained artifact `10451955371`, SHA-256 `a45ca2e0359d8b06a4a70ca82616d88fa779fe7df7fe9a56d9ba24f2eb9adda1`, material profile `0c4834bf0fc9c0b7aa1a053f35f307b64596e13f305287ca3018b6182b2f6fe9`.
- Building source authority remains `57f66b1245812f0c3d402232a046b86c0b5c72d8`.
- Weather source-width observer donor remains Map VFX PR #25 head `15a03b7c3ba3aaa7c0475ca1a3091c15581f559b`.

## Allowed change

Only the exact Building `infill_coating` material response may change from the predecessor `#344047FF / metallic 0.16 / roughness 0.68` to the accepted donor `#59666DFF / 0.16 / 0.68`.

Held fixed: Building geometry/source topology, frame/roof/slab/service-panel materials, Weather source/seed/layout/source-width fields, Nature sources and animated sapling schedule, Object source, path, cameras, lighting, and all unrelated scene state.

## Evidence boundary

The structural verifier fails closed on Environment parent identity drift, Weather-width drift, Building Materials donor identity drift, and candidate-material drift. The target-host proof uses pinned Godot 4.7.2 GL Compatibility and retains 17 states × 2 cameras × thin-line/source-width presentations. Acceptance requires the exact Building successor profile to reach the host, all inherited 1,224 Weather projected-width observations to stay within the existing 0.05 px tolerance, Object/Nature identities to remain present, and every source-width successor frame to differ from the exact predecessor source-width frame only after the material successor is composed.

This proof does not grant combined-world Art Direction/Visual QA acceptance, target-device performance acceptance, physical material/weather correctness, arbitrary-camera equivalence, gameplay, CANON, production readiness or Environment mastery.
