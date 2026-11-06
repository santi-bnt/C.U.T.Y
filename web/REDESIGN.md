# Cinematic C.U.T.Y. redesign

## Audit before implementation — 2026-11-05

The repository is divided into Raspberry/Python voice, vision, face and touchscreen code; future STM32 firmware; CAD and KiCad hardware; documentation; and this independent web application. The redesign changes only `web/`.

| Area | Existing implementation | Treatment |
| --- | --- | --- |
| Frontend | React 19, TypeScript, Vite, CSS, R3F/Drei/Three, Lucide | Reused; one GSAP dependency added |
| Navigation | Single page with hash anchors, EN/ES context, mobile menu | Existing destinations preserved |
| Authentication / database | No auth SDK, database client or implemented integration | No new integration |
| API / dashboard | No backend endpoints; dashboard and digital-twin directories contain planning notes | Honest offline Live chapter |
| Deployment | Relative Vite base; static Vercel/Netlify/Pages instructions, no checked-in deployment service configuration | Build/output settings retained |
| Identity | Two-eye mark, black V17 body, original green-eye/pink-mouth display; dark/cyan interface | Mark/model/face retained; surrounding UI moves to purple/lavender |
| Assets | Actual V17 GLB, four original face atlases, favicon; no authored robot rig/clips | Asset bytes unchanged |
| Working interactions | Camera presets, orbit, zoom, wireframe, autorotation, face simulation, hardware/capability/architecture selection | Preserved and extended |

Claims remain grounded in `src/data/project.ts` and its repository evidence links. Gemini/OpenAI adapters, local voice activity detection, web search, OpenCV/YuNet tracking, face rendering and touchscreen behavior exist in Python. Basic Pi voice/audio checks are documented; sustained reliability and full physical tracking need validation. STM32 UART/PWM/safety are future work. Carrier V1.1 is a 100 × 92 mm two-layer KiCad design awaiting fabrication and electrical validation. The website does not turn these plans into completed features.

## Reference study

[Lando Norris’s website](https://landonorris.com/) was inspected in desktop and mobile viewports, including its loaded hero and scrolled content. Observed principles: a dominant interactive subject, oversize editorial type, sparse navigation, strong background/scale changes, and mobile controls that explicitly invite interaction. The reference uses Mona Sans, serif display typography, a lime/olive palette, portrait imagery and racing-specific content.

C.U.T.Y. uses its own robot, local system sans/Georgia typography, two-eye branding and purple palette. No reference assets, fonts, shaders or implementation code were copied. Screenshots used for study remain ignored local QA artifacts.

## Narrative and design system

1. **Meet C.U.T.Y.** — giant wordmark and real, black V17 assembly, original face on the actual LCD mesh.
2. **Meet Your Companion** — desktop sticky transition changes copy and camera angle; voice, vision and planned motion have distinct wording.
3. **Inside C.U.T.Y.** — light hardware browser, interactive architecture and specifications with source links.
4. **Expressions & Personality** — existing capability selectors and shared original face demo.
5. **C.U.T.Y. Live** — explicitly disconnected display link, demo navigation and renderer source link. No fabricated telemetry.
6. **Development Journey** — implemented, in-validation and planned milestones; project motivation and repository links.

Tokens in `src/cinematic.css`: purple `#8B5CF6`, deep `#17141F`, paper `#F5F3FA`, lavender `#C4B5FD`. Green eyes remain part of the original face/mark identity. Serif italics provide a softer counterpoint to large sans headings. Engineering selectors retain their existing reusable markup and behavior, styled through the presentation layer.

## Motion and interaction ownership

`StoryIntro` owns a scoped GSAP matchMedia/timeline with cleanup. ScrollTrigger updates an imperative `StoryMotion` channel; it does not rerender the React tree every scroll frame. The R3F camera reads this channel and interpolates toward its destination. Native scrolling is preserved; there is no smooth-scroll hijack.

Orbit, zoom, presets and autorotation give the user manual camera ownership. A labeled control resumes scroll framing. The LCD preset uses the verified front-facing display location, not invented component hotspots. No individual arms or joints are animated.

Above 900 CSS pixels, the first two chapters share a sticky canvas. On narrower devices the robot comes before the longer copy, with all chapters in document flow. Reduced motion removes the sticky storytelling, idle movement and autorotation; both narrative chapters remain readable. The existing explicit camera controls still work. The page uses one lazy canvas, DPR capped at 1.5, low-power WebGL preference, offscreen/tab visibility pausing and small shadow maps. Mobile idle movement is disabled. The desktop idle invalidation timer is capped at 30 Hz; user-driven camera transitions can render more frequently. This is a rendering policy, not a measured device FPS claim.

## Future face stream boundary

`communication/faceFrames.ts` defines `FaceFrame` (decoded pixels and crop rectangle), `FaceFrameSource` (mode and subscription), atlas cropping and a shared 480 × 320 canvas sink. `state/FaceFrames.tsx` can inject a source around the app. `viewer/useFaceTexture.ts` subscribes to a supplied live source with cleanup, or draws the original offline atlas frames when none is provided.

A later transport adapter must own WebSocket connection/reconnection, decoding, frame pacing and ImageBitmap disposal. It can feed this interface without coupling display pixels to a database or to `RobotTransport` telemetry. No such transport, endpoint, remote control or live connection is implemented here. The face lab remains a local simulation; integrating it with future live frames is a separate UI decision. The current Live panel always describes the actual offline release.

## Scope and verification

File inventory (paths relative to `web/`):

| Change | Files |
| --- | --- |
| Added presentation | `src/components/StoryIntro.tsx`, `src/components/LivePreview.tsx`, `src/cinematic.css` |
| Added boundaries | `src/viewer/storyMotion.ts`, `src/communication/faceFrames.ts`, `src/state/FaceFrames.tsx` |
| Added test/docs | `src/communication/faceFrames.test.ts`, `REDESIGN.md` |
| Updated composition/style entry | `src/App.tsx`, `src/main.tsx`, `index.html` |
| Updated existing viewer | `src/viewer/RobotViewer.tsx`, `src/viewer/Scene.tsx`, `src/viewer/model.ts`, `src/viewer/useFaceTexture.ts` |
| Updated dependencies/checks | `package.json`, `package-lock.json`, `eslint.config.js`, `e2e/portfolio.spec.ts` |
| Updated documentation | `README.md`, `VERIFICATION.md` |

Unchanged: model/face asset bytes, technical evidence data, Python application, firmware, GPIO, touchscreen services and all existing anchor destinations. English remains the initial language. Static deployment still uses root `web`, build `npm run build`, output `dist`, without API keys.

See [VERIFICATION.md](VERIFICATION.md) for executed checks and platform limitations, and [README.md](README.md) for local execution and deployment.
