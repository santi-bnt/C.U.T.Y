# Continuous product experience — change map

The current implementation follows [EXPERIENCE_PLAN.md](EXPERIENCE_PLAN.md), written after repository/reference inspection and before implementation. It replaces the earlier intro-only camera transition with a single persistent scene across the homepage. [README.md](README.md) documents execution, deployment, source assets, file responsibilities and electrical limitations.

## Modified

- `src/App.tsx`, `src/cinematic.css`: narrative composition, seven-section navigation, typographic hierarchy, technical disclosures and responsive layouts.
- `src/viewer/RobotViewer.tsx`, `Scene.tsx`, `robot.ts`, `storyMotion.ts`: persistent scene, camera ownership, original LCD, local studio lighting, material normals, rendering limits and animation channel.
- `src/App.test.tsx`, `src/test-setup.ts`, `src/viewer/model-asset.test.ts`: preserved interactions, DOM observers and actual V17 geometry/source integrity checks.
- `e2e/portfolio.spec.ts`, `playwright.config.ts`: desktop/tablet/mobile browser interactions, screenshots and fallback validation.
- `README.md`, `REDESIGN.md`, `VERIFICATION.md`: current documentation.

## Added

- `src/components/Choreography.tsx`: measured GSAP master timeline and editorial reveals.
- `src/viewer/choreography.ts`, `choreography.test.ts`: pure responsive camera resolver and tests.
- `src/viewer/batchAssembly.ts`: owned static presentation batching; original V17 GLB untouched.
- `src/components/PcbDesign.tsx`, `WiringConnections.tsx`, `Engineering.test.tsx`: source-backed PCB and wiring interaction.
- `src/data/carrier.generated.json`, `engineering.ts`, `engineering.test.ts`, `boardFunctions.ts`: native component/pad export, typed bilingual connection data and integrity tests.
- `scripts/export-engineering.py`: deterministic source export and pin/net parity verification.
- `public/engineering/`: actual source downloads and board previews; see generated asset manifest for hashes.
- `EXPERIENCE_PLAN.md`: audit, references, visual specification and validation gates.

## Removed

`src/components/StoryIntro.tsx` and `LivePreview.tsx`: superseded by the master choreography and homepage Live section. Existing face/architecture components and future communication contracts remain intact.

No firmware, Raspberry configuration, GPIO assignment, robot service, authentication, database, dependency manifest or Vercel/domain configuration changed. No copied reference-project code/assets. No production deployment.

## Nido integration additions

The later user-supplied archives enabled the previously missing mechanical PCB view. See NIDO_INTEGRATION.md for source differences and README.md for current execution/asset specifications. Earlier no-PCB-model and anonymous-V17 observations describe the pre-import audit, not the current application.

Added: `IntroSequence.tsx`, `AssemblyStory.tsx`, `EngineeringViewport.tsx`, `EngineeringScene.tsx`, `viewer/assembly.ts`, `data/operationalWiring.ts` and its tests, `nido.generated.json`, `nido.css`, `scripts/import-nido.py`, `scripts/export-nido.mjs`, `public/assembly/`, `public/models/carrier-assembly.glb`, and `public/engineering/hardware-connections.md`.

Updated: `public/models/cuty.glb`, `data/model.ts`, `viewer/robot.ts`, `Scene.tsx`, `RobotViewer.tsx`, PCB/wiring UI, `main.tsx`, App composition and geometry/browser tests. The source GLB in hardware is unchanged. No production deployment.
