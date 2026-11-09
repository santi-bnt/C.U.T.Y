# Verification — cinematic story and current Nido integration

## Current-model replacement — 2026-11-09

- Rebuilt `public/models/cuty.glb` and the PCB mechanical subset from the November 6 CadQuery source in `hardware/cad/carcasa_v17/fuente_cad/v17`, using the matching `parts.json` reference data supplied in the ZIP.
- Geometry checks: 113 named meshes, 192,642 triangles, 1,093,424-byte optimized GLB, bounds 180.00 × 365.00 × 173.41 mm, H3 depth 10.72 mm, H4 span 87.05 mm, and `lcd_touch_panel` retained for the existing facial texture pipeline.
- This replaces the previous 1,637,704-byte GLB that had old H3/H4 dimensions. The intro still delays showing the robot until the second section; the assembly photographs remain an earlier reference.
- The website-model rebuild and metadata/export validation completed. Full web tests, lint, production build, browser visual review, and push are still pending in this update.

## Latest documentation update — 2026-11-09

- Rebuilt the interactive robot GLB from the November 6 printable Nido CadQuery source. The page now identifies the interactive model as the current printable enclosure revision; the 18-step photo sequence remains an earlier assembly reference.
- Carrier status now reflects the documented JLCPCB THT assembly order: 37 supplier-soldered components, with F1/F2 fuse hardware and JP1 shunt to be fitted by hand. Receipt, integration, and electrical validation are not claimed complete. PCBWay files are labeled as an alternative package.
- The page now provides the current Nido STL set, CadQuery source, four CAD renders, dimensions, author-supplied verification report, JLCPCB/PCBWay order documents, and the project BOM/readme downloads.
- `npm.cmd run lint` and `npm.cmd run build` passed on Nov 9. Vite reports the existing ~996 kB minified robot scene chunk (~272 kB gzip). No test suite was run for this documentation/assets update.
- Manual production-preview review covered 1440×1000 desktop and 390×844 mobile: CAD views switched correctly; no page errors, failed requests, or horizontal overflow. The floating 3D explorer button was restricted to the robot story so it does not cover the CAD view controls in technical sections.

Validated locally on Windows, 2026-11-06. No production deployment.

## Checks

- ESLint passed.
- Strict TypeScript and Vite production build passed. The shared lazy Three.js chunk remains approximately 996 kB minified / 272 kB gzip, with Vite's large-chunk advisory. Technical Scene code is split separately; no FPS or Lighthouse score is claimed.
- Vitest: **20 passed across 7 files**. Actual compressed GLB decoding, normalized bounds, triangle count, integrated LCD/source immutability, static batching, named arm/head motion and reset, exploded/interior state, deterministic choreography, source hashes, actual asset presence and builder-confirmed pin assignments are tested.
- Playwright: **12 passed**, covering desktop 1440×1000, touch tablet 820×1180 and mobile 390×844. Covers intro skip/focus, original face controls, presets, zoom/reset/wireframe/autorotation, named-part demos, persistent homepage canvas/model cache, EN/ES/menu/deep links, reduced motion, missing-model fallback, actual PCB front/back/selection/3D loading, 3D/2D wiring, confirmed audio table, search/filter and source downloads.
- Assembly step navigation and imagery, downloadable STL ZIP and original engineering downloads checked. Twenty-two supplied confirmed display/audio rows are separate from proposed UART/PWM. The latest ReSpeaker table includes physical7/37 and fixed power/ground physical1/4/6; unit tests assert all 11 rows exactly and browser tests check their displayed values.
- Source KiCad/netlist parity tests remain intact. The existing Python regression run earlier in this task passed **169 tests with 2 skipped**; subsequent changes were only in web.
- Production preview on port 5180, before the final hookup-table amendment: Spanish 3D wiring loaded with the then-current nine confirmed ReSpeaker rows, the 1,637,704-byte model, no page/console errors and no external network requests. The final 11-row table is covered by the updated unit/browser suite.
- No normal-flow page/console errors in final screenshot review. Checked desktop/tablet/mobile and narrow 320×740 for horizontal overflow: none observed. Headless Chromium/Edge software WebGL is not a physical mobile GPU benchmark or Safari certification.

## Visual review and fixes

Latest steering at that validation: hero contains no visible model or exploration controls; the robot first appears in Meet C.U.T.Y. Tests assert hidden/visible states for desktop/mobile/reduced motion, and the transition clips the canvas below the second section's boundary. Camera/tracking status now reflects the builder's physical confirmation. PCB status then was Sent to fabrication; the current status is updated above from the newer README and order documents.

Replay/typography follow-up: 20 unit tests, lint and build passed; the three affected desktop/tablet/mobile browser scenarios passed with replay, Escape/focus restoration, intro bounds and a canvas text-metrics check proving the hero Y's ink fits its mask. Additional desktop and 320px captures reviewed the complete Y and static reduced-motion replay with no page errors or horizontal overflow. Replay does not remount the persistent model.

Reviewed the kinetic opening and actual revised black robot on desktop/mobile, plus assembly imagery, original LCD, exploded view, PCB 3D and spatial wiring at desktop/tablet/mobile sizes. Corrected intro/deep-link interaction, Skip accessible name/focus, mobile framing and masking, overlapping wiring labels, an unnecessary nested React root from floating labels, and offscreen lazy-view expectations. Simplified electronics remain visibly mechanical reference geometry. Source render images are explicitly labeled as the earlier Nido reference.

Captures remain ignored under `test-results/` and `node_modules/.cache/cuty-research/`. Useful final views include `desktop-nido-intro-final.png`, `desktop-nido-hero-final.png`, `desktop-nido-wiring-final.png` and their tablet/mobile counterparts.

## Asset evidence

The November 6 web GLB was rebuilt from the current CadQuery source with 0.25 mm linear and 0.17 rad angular tessellation, then optimized with gltfpack 1.3.0. It contains 113 named meshes and 192,642 triangles in 1,093,424 bytes; bounds are approximately 180.00 × 365.00 × 173.41 mm. H3 visor depth is 10.72 mm and H4 display/camera bars span 87.05 mm. The integrated LCD mesh name is preserved for the existing face-texture pipeline. Geometry is presentation data, not manufacturing tolerance evidence.

The 146,700-byte PCB GLB contains 45 actual mechanical CAD solids. The CAD source explicitly models purchased electronics as simplified envelopes. It does not replace native electrical layout/net metadata; four fuse pad coordinates differ by 3.4 mm Y. Holes and NT1 have no separately selectable solid. Source archive hashes, output hash and all 18 rendered image hashes are preserved in `public/assembly/provenance.json` and tested.

## Limits

- Head/arm and exploded views are visual simulations, not motor control or validated safe motion.
- Wiring curves are schematic relationships between named CAD part bounds, not physical harness routes/contact coordinates. Ground topology is shown in tables because no NT1 solid exists.
- Display/ReSpeaker are user-confirmed working together. Backlight/final overlay, STM32 UART pins, five PWM assignments, buck model/current, battery protection/fuse/distribution, independent battery-to-Pi regulator and final PCB remain pending according to the supplied user table.
- The author-supplied CAD collision report was preserved, not rerun or promoted into physical validation. Earlier assembly imagery/fastener instructions are not silently treated as the latest manufacturing specification.
- No live dashboard, authentication, database, robot transport or API existed to migrate. Existing future transport/frame contracts remain modular; Live stays offline by default.
- Vercel/domain configuration is unchanged. cuty.mx was not reliably reachable from the research environment; production behavior is not certified by local checks.

See [README.md](README.md), [NIDO_INTEGRATION.md](NIDO_INTEGRATION.md) and [EXPERIENCE_PLAN.md](EXPERIENCE_PLAN.md) for current setup, source traceability and design research.
