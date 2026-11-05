# Verification — 2026-11-05

Face correction: the original CSS face illustration was replaced with lossless atlases exported directly from the unchanged robot FaceRenderer (neutral/listening/happy/surprised, original gaze/mouth/blink geometry). Browser tests additionally verify that the selected expression's original atlas loads at its expected resolution. The interactive demo's timing and synthetic mouth playback remain offline simulations.

- `npm run build`: passed (strict TypeScript + Vite production assets).
- `npm run lint`: passed, no warnings or errors.
- `npm test`: 7 tests passed. EN/ES switching, contextual hardware and architecture details, face controls, compact navigation, translated geometry normalization, offline telemetry semantics and the real V23 asset. UI unit tests replace the WebGL boundary; the asset test parses the real file and browser tests below render it.
- `npm run test:e2e`: 4 tests passed in existing Microsoft Edge, desktop 1440 × 1000 and iPhone 13 viewport/touch emulation. No page or console errors on the normal path. Verified model loading, view presets, zoom controls, reset, wireframe, autorotation, translation, component/architecture selection, synthetic mouth toggle, reduced motion and the missing-GLB fallback. Internal anchors exist and the mobile layout has no horizontal overflow.
- Desktop and mobile screenshots visually inspected. Mobile screenshots use DPR 1 to avoid oversized full-page raster captures; the application caps rendering DPR at 1.5.
- V23 replaces the previous model at the same public asset path. It matches `CUTY_V23_Assembly_web.glb` byte-for-byte (SHA-256 `FEA02D0E4677BEFA6C3B33E95F365CCEBE1EB833C926DEE9B243801AF8B28C23`). Nine meshes, original materials and node transforms are preserved. Measured world bounds are X 182.70 × Y 333.75 × Z 131.67 mm; triangle count is 103,446. A real-asset test parses the GLB and verifies these properties. All technical source-link paths exist in the local repository.

Vite reports a large-chunk advisory for the lazy 3D scene. The main page is separate; the V23 GLB is served locally (4,958,296 bytes). The scene is split from the initial page, demand-rendered, and paused off-screen. This is not a measured real-device performance benchmark.

Mobile testing is Chromium-based emulation, not a physical phone or Safari certification. No Raspberry configuration, firmware, GPIO, services or live AI behavior were changed or tested by this web implementation. No production deployment was performed. Run/deployment instructions are in README.md.
