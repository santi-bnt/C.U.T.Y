# Verification — 2026-11-05

Face correction: the original CSS face illustration was replaced with lossless atlases exported directly from the unchanged robot FaceRenderer (neutral/listening/happy/surprised, original gaze/mouth/blink geometry). Browser tests additionally verify that the selected expression's original atlas loads at its expected resolution. The interactive demo's timing and synthetic mouth playback remain offline simulations.

- `npm run build`: passed (strict TypeScript + Vite production assets).
- `npm run lint`: passed, no warnings or errors.
- `npm test`: 6 tests passed. EN/ES switching, contextual hardware and architecture details, face controls, compact navigation, translated geometry normalization, offline telemetry semantics. Unit tests replace the WebGL boundary; browser tests below use the real GLB.
- `npm run test:e2e`: 4 tests passed in existing Microsoft Edge, desktop 1440 × 1000 and iPhone 13 viewport/touch emulation. No page or console errors on the normal path. Verified model loading, view presets, zoom controls, reset, wireframe, autorotation, translation, component/architecture selection, synthetic mouth toggle, reduced motion and the missing-GLB fallback. Internal anchors exist and the mobile layout has no horizontal overflow.
- Desktop and mobile screenshots visually inspected. Mobile screenshots use DPR 1 to avoid oversized full-page raster captures; the application caps rendering DPR at 1.5.
- GLB matches the supplied root file byte-for-byte (SHA-256 `A2397D78B038BEBF39F173041E1ED4D66C4B3DC843D247CE6C7359CFA8E969EF`). Bounds and triangle count read directly from the asset. All technical source-link paths exist in the local repository.

Vite reports the expected large-chunk advisory for the lazy 3D scene: approximately 999 kB minified / 272 kB gzip. The main page is separate (approximately 258 kB / 82 kB gzip); the 922 kB GLB is served locally. The scene is split from the initial page, demand-rendered, and paused off-screen. This is not a measured real-device performance benchmark.

Mobile testing is Chromium-based emulation, not a physical phone or Safari certification. No Raspberry configuration, firmware, GPIO, services or live AI behavior were changed or tested by this web implementation. No production deployment was performed. Run/deployment instructions are in README.md.
