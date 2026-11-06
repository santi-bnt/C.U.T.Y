# Verification — cinematic story and revised Nido integration

Validated locally on Windows, 2026-11-06. No production deployment.

## Checks

- ESLint passed.
- Strict TypeScript and Vite production build passed. The shared lazy Three.js chunk remains approximately 996 kB minified / 272 kB gzip, with Vite's large-chunk advisory. Technical Scene code is split separately; no FPS or Lighthouse score is claimed.
- Vitest: **20 passed across 7 files**. Actual compressed GLB decoding, normalized bounds, triangle count, integrated LCD/source immutability, static batching, named arm/head motion and reset, exploded/interior state, deterministic choreography, source hashes, actual asset presence and builder-confirmed pin assignments are tested.
- Playwright: **12 passed**, covering desktop 1440×1000, touch tablet 820×1180 and mobile 390×844. Covers intro skip/focus, original face controls, presets, zoom/reset/wireframe/autorotation, named-part demos, persistent homepage canvas/model cache, EN/ES/menu/deep links, reduced motion, missing-model fallback, actual PCB front/back/selection/3D loading, 3D/2D wiring, confirmed audio table, search/filter and source downloads.
- Assembly step navigation and imagery, downloadable STL ZIP and original engineering downloads checked. Twenty-two supplied confirmed display/audio rows are separate from proposed UART/PWM. The latest ReSpeaker table includes physical7/37 and fixed power/ground physical2/17/39; unit tests assert all 11 rows exactly and browser tests check their displayed values.
- Source KiCad/netlist parity tests remain intact. The existing Python regression run earlier in this task passed **169 tests with 2 skipped**; subsequent changes were only in web.
- Production preview on port 5180, before the final hookup-table amendment: Spanish 3D wiring loaded with the then-current nine confirmed ReSpeaker rows, the 1,637,704-byte model, no page/console errors and no external network requests. The final 11-row table is covered by the updated unit/browser suite.
- No normal-flow page/console errors in final screenshot review. Checked desktop/tablet/mobile and narrow 320×740 for horizontal overflow: none observed. Headless Chromium/Edge software WebGL is not a physical mobile GPU benchmark or Safari certification.

## Visual review and fixes

Reviewed the kinetic opening and actual revised black robot on desktop/mobile, plus assembly imagery, original LCD, exploded view, PCB 3D and spatial wiring at desktop/tablet/mobile sizes. Corrected intro/deep-link interaction, Skip accessible name/focus, mobile framing and masking, overlapping wiring labels, an unnecessary nested React root from floating labels, and offscreen lazy-view expectations. Simplified electronics remain visibly mechanical reference geometry. Source render images are explicitly labeled as the earlier Nido reference.

Captures remain ignored under `test-results/` and `node_modules/.cache/cuty-research/`. Useful final views include `desktop-nido-intro-final.png`, `desktop-nido-hero-final.png`, `desktop-nido-wiring-final.png` and their tablet/mobile counterparts.

## Asset evidence

The revised native GLB has 109 named meshes, 318,023 triangles and 11,407,376 bytes. gltfpack 1.3.0 retained names/materials, quantized/compressed without requesting simplification, and removed five degenerate triangles. Web GLB: 1,637,704 bytes / 318,018 triangles, with local bundled meshopt decoding. Bounds approximately 180.00 × 365.00 × 173.27 mm. Geometry is presentation data, not manufacturing tolerance evidence.

The 146,700-byte PCB GLB contains 45 actual mechanical CAD solids. The CAD source explicitly models purchased electronics as simplified envelopes. It does not replace native electrical layout/net metadata; four fuse pad coordinates differ by 3.4 mm Y. Holes and NT1 have no separately selectable solid. Source archive hashes, output hash and all 18 rendered image hashes are preserved in `public/assembly/provenance.json` and tested.

## Limits

- Head/arm and exploded views are visual simulations, not motor control or validated safe motion.
- Wiring curves are schematic relationships between named CAD part bounds, not physical harness routes/contact coordinates. Ground topology is shown in tables because no NT1 solid exists.
- Display/ReSpeaker are user-confirmed working together. Backlight/final overlay, STM32 UART pins, five PWM assignments, buck model/current, battery protection/fuse/distribution, independent battery-to-Pi regulator and final PCB remain pending according to the supplied user table.
- The author-supplied CAD collision report was preserved, not rerun or promoted into physical validation. Earlier assembly imagery/fastener instructions are not silently treated as the latest manufacturing specification.
- No live dashboard, authentication, database, robot transport or API existed to migrate. Existing future transport/frame contracts remain modular; Live stays offline by default.
- Vercel/domain configuration is unchanged. cuty.mx was not reliably reachable from the research environment; production behavior is not certified by local checks.

See [README.md](README.md), [NIDO_INTEGRATION.md](NIDO_INTEGRATION.md) and [EXPERIENCE_PLAN.md](EXPERIENCE_PLAN.md) for current setup, source traceability and design research.
