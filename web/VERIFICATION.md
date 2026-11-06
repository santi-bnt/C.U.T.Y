# Verification - cinematic redesign, 2026-11-05

## Executed checks

- `npm run lint`: passed, no errors or warnings.
- `npm test`: **9 passed** across 3 files. Existing EN/ES, contextual hardware/architecture, face interaction, compact navigation, geometry normalization, offline telemetry and actual-asset tests remain green. New tests verify original atlas cropping and full decoded-frame drawing through the common display sink.
- `npm run build`: passed, including strict TypeScript checking. Output: `web/dist/`.
- `npm run test:e2e`: **6 passed** in Microsoft Edge using desktop 1440 x 1000 and iPhone 13 viewport/touch emulation. Covers real GLB loading, all five presets including LCD, zoom/reset/wireframe/autorotation, EN/ES, hardware/architecture panels, original face atlas and mouth demo, reduced motion, missing-model fallback, manual camera ownership/resume, desktop companion transition, mobile model placement and the explicit offline Live state.
- Normal browser flow: no page or console errors. All internal hash-link targets exist. Mobile checks found no horizontal overflow.
- Production preview served on localhost:4173: page and GLB returned HTTP 200; model response was **2,747,512 bytes**. Language switching and original LCD texture loaded without page errors. No production deployment was performed.
- Additional visual/responsive checks: 320 x 640, 390 x 844, 768 x 1024, 1366 x 768 and 1440 x 1000. Initial mobile composition, desktop companion framing, original LCD close-up, full page sections and Spanish laptop layout were visually inspected. A short-viewport text overlap was corrected before the final build.
- Repository Python suite: **169 passed, 2 skipped** using the existing `raspberry/.venv`, with a separate temporary directory under ignored `web/node_modules/.cache/`. Initial attempts encountered Windows temp-directory permissions and a collision with Playwright's output cleanup; the isolated final run passed without robot-code changes.
- `git diff --check`: passed.
- `npm audit --omit=dev`: zero production dependency vulnerabilities reported at verification time. The full dependency audit reports 7 moderate advisories in development dependencies; no force upgrade was applied as part of this redesign.

## Asset and scope integrity

The GLB still matches `hardware/cad/glb/CUTY_V17_Ensamble_completo.glb` byte for byte:

`7EE1BF783E8AD74E6D7F73FF0F7FAFADF89E9ABD772F9C8852C9117CC4543373`

Actual asset tests verify 110 meshes, 116,741 triangles, upright dimensions, black body materials and the original LCD glass's 54 front triangles. Source geometry and orientation remain untouched. The runtime copy is rotated Z-up to Y-up, then uniformly fitted. The face atlases, source GLB and technical project data were not changed.

All tracked changes are within `web/`. No Python application, firmware, GPIO, Raspberry service, API key, backend or database configuration was changed. Existing anchor destinations and Vite relative-base deployment behavior remain intact.

## Limits

Vite retains a large-chunk advisory for the lazy 3D scene (about 1 MB minified / 273 KB gzip). The scene is separate from the page, uses one capped-DPR canvas, and pauses offscreen. Desktop idle invalidation runs at up to 30 Hz; mobile idle movement is disabled. These are implementation policies, not measured real-device performance metrics.

Browser mobile checks are Chromium-based emulation, not physical-phone or Safari certification. No real Raspberry, camera stream, AI session or actuator was exercised by the website. The Live section is offline. Future decoded-frame injection is implemented as a transport-independent interface/provider; a WebSocket adapter, connection lifecycle, security and any live dashboard remain future work. See [REDESIGN.md](REDESIGN.md) for architecture and [README.md](README.md) for run/deploy instructions.
