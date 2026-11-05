# Verification — 2026-11-05

Face correction: the original CSS face illustration was replaced with lossless atlases exported directly from the unchanged robot FaceRenderer (neutral/listening/happy/surprised, original gaze/mouth/blink geometry). Browser tests additionally verify that the selected expression's original atlas loads at its expected resolution. The interactive demo's timing and synthetic mouth playback remain offline simulations.

- `npm run build`: passed (strict TypeScript + Vite production assets).
- `npm run lint`: passed, no warnings or errors.
- `npm test`: 7 tests passed. EN/ES switching, contextual hardware and architecture details, face controls, compact navigation, geometry normalization, offline telemetry semantics and the actual V17 asset. The asset test verifies 110 meshes, 116,741 triangles, upright bounds, black body materials, front-glass texture assignment and its 54 screen triangles, while confirming the source geometry and orientation remain untouched.
- `npm run test:e2e`: 4 tests passed in existing Microsoft Edge, desktop 1440 × 1000 and iPhone 13 viewport/touch emulation. No page or console errors on the normal path. Verified model loading, view presets, zoom controls, reset, wireframe, autorotation, translation, component/architecture selection, synthetic mouth toggle, reduced motion and the missing-GLB fallback. Internal anchors exist and the mobile layout has no horizontal overflow.
- Desktop and mobile screenshots visually inspected. Mobile screenshots use DPR 1 to avoid oversized full-page raster captures; the application caps rendering DPR at 1.5.
- The V17 complete assembly replaces the model at the same public asset path. It matches `CUTY_V17_Ensamble_completo.glb` byte-for-byte (SHA-256 `7EE1BF783E8AD74E6D7F73FF0F7FAFADF89E9ABD772F9C8852C9117CC4543373`). Source Z-up coordinates are presented Y-up through a cloned-instance rotation. Viewer bounds: X 180 × Y 365 × Z 173.02 mm. The requested black finish and live local face texture are runtime presentation effects. All technical source-link paths exist in the local repository.

Vite reports a large-chunk advisory for the lazy 3D scene. The main page is separate; the V17 GLB is served locally (2,747,512 bytes). The scene is split from the initial page, demand-rendered, and paused off-screen. This is not a measured real-device performance benchmark.

Mobile testing is Chromium-based emulation, not a physical phone or Safari certification. No Raspberry configuration, firmware, GPIO, services or live AI behavior were changed or tested by this web implementation. No production deployment was performed. Run/deployment instructions are in README.md.
