# C.U.T.Y. — cinematic engineering portfolio

Frontend-only React / TypeScript / Vite app using React Three Fiber, Drei, Three.js and GSAP. No backend, authentication, database, AI requests or live robot connection is added. Robot source, GPIO, overlays, services and domain configuration are untouched.

## Run

Requires Node.js 22.12+ or a compatible newer version:

```powershell
cd web
npm.cmd ci
npm.cmd run dev
```

Open Vite's printed URL. On other shells use `npm` normally. Dependencies stay under `web/node_modules`.

```sh
npm run lint
npm test
npm run test:e2e
npm run build
npm run preview
```

Build performs strict TypeScript checking and outputs `dist/`. Browser tests use Edge on Windows or Playwright Chromium elsewhere; install Chromium in a project-local browser cache if needed. Do not open index.html with file://.

## The experience

A kinetic C.U.T.Y. typographic opening precedes a text-only hero, with Skip and reduced-motion bypass. The robot and exploration controls appear only in the second section, Meet C.U.T.Y.; the transition is clipped to that section so it cannot cover the first. Deep section links bypass the opening. One lazy homepage canvas persists throughout the story. A measured GSAP master timeline drives deterministic desktop/mobile camera poses without page-wide React scroll updates. Explicit exploration takes camera ownership; Escape restores the story.

Replay intro buttons in the hero and footer reopen the opening without reloading the page or remounting the model. Escape/Skip closes it and restores keyboard focus. With reduced motion, an explicitly requested replay shows static branding until closed. Letter masks include space for glyph overhang so the Y is not clipped; mobile animation tracking stays inside the viewport.

The updated **V17 Nido November 5 revision** has named parts, smooth CAD normals and authored internal materials. The exterior remains black and the original animated Python face remains mapped onto the actual LCD glass. Explore supports orbit/pinch, presets, zoom/reset, wireframe, autorotation, inside/exploded views and clearly labeled head/arm motion demos. These are visual rigid-part simulations, not motor commands or proof of safe joint limits.

The assembly section now leads with the **November 6, 2026 printable Nido revision**, using the current author-provided front, back, side and X-ray renders. Its fit updates include the camera cradle and retaining bar, measured 5.8 mm display bars, a speaker pocket sized 35.4 × 25 × 5.5 mm and a battery drawer designed around the team's HM2202 pack envelope. Exact battery dimensions and camera lens-center position remain to be measured. The section downloads the matching 30 oriented STL parts, CadQuery source, dimensions and author report. Reported 0 static interferences and 34 poses are clearly attributed to the author and are not physical validation.

The interactive robot GLB and 18-step assembly images remain from earlier revisions: the GLB is dated November 5 and the image sequence is an earlier assembly reference. The page labels these separately from the November 6 print CAD instead of implying they are the same revision.

PCB inspection retains native KiCad front/back pad selection, zoom/pan and electrical details. Its additional 3D mode uses **45 actual solids extracted from revised Nido CAD**. Purchased electronics are simplified mechanical envelopes, not a validated KiCad 3D component library. Orbit, front/back/isometric views, camera focus, hover and selection work. Holes/NT1 have no separately selectable solid, and four F1/F2 pad coordinates differ between the artifact and current KiCad by 3.4 mm in Y. Native electrical data is not replaced by this model.

Wiring defaults to an interactive 3D interior with selected components and colored functional curves; a 2D overview and searchable tables remain available. Curve endpoints derive from named CAD bounds and represent relationships, not physical harness routes or contact coordinates. Ground topology stays in the table because NT1 has no CAD solid. Technical viewers load near the viewport and pause while hidden; the dormant homepage canvas is retained.

## Which connections are confirmed

Latest builder update: camera operation and facial tracking are confirmed on the robot, alongside display/audio. Their component states are Implemented. The hardware README records an assembled THT order with JLCPCB: 37 components soldered by the supplier; F1/F2 holders and fuses, plus the JP1 shunt, are fitted by hand. The page links the order's BOM, placement file and instructions, and separately labels the PCBWay PCBA package as an alternative. Receipt, integration and electrical checks are not presented as validated. Visual gaze tracking is separate from future servo-driven head tracking.

`src/data/operationalWiring.ts` and `public/engineering/hardware-connections.md` record the builder's supplied table. Display and ReSpeaker operation together is confirmed. Display DC is BCM24 / physical18; RESET is BCM25 / physical22; touch IRQ is BCM17 / physical11. The latest explicit ReSpeaker table uses 5 V physical4, 3.3 V physical1, GND physical6, I2C physical3/5, MCLK physical7 / BCM4, I2S physical12/35/38/40 and AUD_RST physical37 / BCM26. These 11 rows supersede the earlier audio hookup list.

UART is proposed at Pi physical8/10; final STM32 RX/TX and all five PWM pins remain unassigned. Backlight/overlay, exact buck current rating, protection/fuses/distribution, battery-to-Pi regulator and final PCB connectors remain pending. These are independent of the confirmed audio/display test. Preserve the working GPIO configuration.

`src/data/engineering.ts` and `carrier.generated.json` remain the separate native KiCad source, including proposed PA2/PA3 and PWM design assignments. The 3D/source preview does not promote those proposals into tested wiring. No firmware or electrical configuration is changed.

## Assets and performance

`public/models/cuty.glb` is now generated from the revised user-provided native GLB, replacing the older anonymous V17. Native: 11,407,376 bytes, 109 named meshes, 318,023 triangles. Web: **1,637,704 bytes, 318,018 triangles**, with meshopt compression and quantization. No simplification ratio was requested; gltfpack removed five degenerate triangles. Measured web bounds are approximately 180.00 × 365.00 × 173.27 mm. Position/normal quantization is presentation optimization, not manufacturing geometry. Names and materials are retained. There are no authored animation clips or skin.

`public/models/carrier-assembly.glb` is the 146,700-byte mechanical subset. Geometry, asset hashes and provenance are tested. The original robot GLB remains in `hardware/cad/` unchanged. Recovered face PNGs/poster remain in `public/assembly/` as references; runtime face animation continues using the original four WebP atlases under `public/face/`.

The existing Three/Drei meshopt decoder is bundled locally; no CDN decoder, remote font, HDR or AI service is required. DPR is capped, technical canvases are lazy, hidden views pause, static homepage geometry is batched, and no postprocessing is added. There are no FPS/Lighthouse claims. Vite retains a large shared 3D-chunk advisory.

## Regenerate assets

No new runtime dependency was installed. gltfpack is an isolated build tool cached within `web/node_modules/.cache`.

From repository root, using an existing Python environment:

```powershell
raspberry/.venv/Scripts/python.exe web/scripts/import-nido.py --prepare
cd web
npm.cmd exec --yes --cache ./node_modules/.cache/npm-tools --package=gltfpack@1.3.0 -- gltfpack -i node_modules/.cache/cuty-nido-revision/CUTY_V17_Nido/CUTY_V17.glb -o node_modules/.cache/cuty-nido-revision/nido-web.glb -kn -km -vp 16 -vn 12 -cc
../raspberry/.venv/Scripts/python.exe scripts/import-nido.py
node scripts/export-nido.mjs
```

The importer accepts `--downloads PATH`, defaulting to the current user's Downloads, and expects the three supplied ZIP names documented in `public/assembly/provenance.json`. It reads ZIP contents without executing artifact JavaScript or CAD Python. Only web assets are written. The source CAD generation/check scripts are reference material, not automatically executed.

Native KiCad export: from repository root, `raspberry/.venv/Scripts/python.exe web/scripts/export-engineering.py`. This compares native pad nets to `scripts/netlist.py` before generating source downloads and includes the current JLCPCB order files and PCBWay alternative; it does not define the confirmed operational wiring. Current printable Nido export: `raspberry/.venv/Scripts/python.exe web/scripts/export-current-nido.py`. Original face export: `raspberry/.venv/Scripts/python.exe web/scripts/export-face.py`.

## Main files and future integration

- `App.tsx`, `cinematic.css`, `nido.css`: bilingual narrative and responsive presentation.
- `components/IntroSequence.tsx`, `Choreography.tsx`, `AssemblyStory.tsx`: opening, measured story and supplied assembly images.
- `viewer/Scene.tsx`, `RobotViewer.tsx`, `robot.ts`, `assembly.ts`: original face integration, named geometry, exclusive exploration and visual demos.
- `components/PcbDesign.tsx`, `WiringConnections.tsx`, `EngineeringViewport.tsx`, `viewer/EngineeringScene.tsx`: native layout and spatial inspection.
- `data/operationalWiring.ts`, `engineering.ts`, `nido.generated.json`: confirmed hookup table, separate native electrical design and measured geometry.
- `scripts/import-nido.py`, `export-nido.mjs`, `export-current-nido.py`: source model import, CAD subset extraction and current November 6 print package export.
- Existing `communication/robot.ts`, `faceFrames.ts` and `state/FaceFrames.tsx`: future transport/decoded-frame boundaries, independent of database state. No socket or credentials.

Live is offline by default. Optional public HTTPS `VITE_CUTY_DASHBOARD_URL` links to a separately deployed dashboard; its authentication stays there. No dashboard/auth/database existed to migrate.

## Static deployment

Vercel: Root Directory `web`, Vite preset, build `npm run build`, output `dist`. Netlify: base `web`, build `npm run build`, publish `dist`. GitHub Pages: publish complete `web/dist`; relative base supports subdirectories, or set `BASE_PATH=/C.U.T.Y/`. No domain/deployment configuration changed and no production deployment was performed.

Research/file map: [EXPERIENCE_PLAN.md](EXPERIENCE_PLAN.md), [REDESIGN.md](REDESIGN.md), [NIDO_INTEGRATION.md](NIDO_INTEGRATION.md). Validation: [VERIFICATION.md](VERIFICATION.md).
