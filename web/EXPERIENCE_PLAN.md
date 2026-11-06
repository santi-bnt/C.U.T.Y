# C.U.T.Y. continuous product experience

## Inspection and scope

The current app is React 19/TypeScript/Vite with R3F, Drei, Three and GSAP already installed. The existing canvas lives in StoryIntro and stops participating after two chapters. There are two overlapping CSS presentation layers. Technical data, original face atlases, model preparation, camera tools and architecture selectors are useful and will be retained. Dashboard/digital-twin folders contain planning notes, not an application. No authentication, database SDK, API routes or implemented remote robot connection was found. No domain or Vercel configuration will change. Work remains in `web/`; no push or production deployment is part of validation.

## Reference inspection

Inspected README and implementation files at these revisions:

| Reference                                                                     | Revision | Useful idea                                                                                                                                           | Compatibility / limits                                                                                                                          |
| ----------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| [orbital-portfolio](https://github.com/IsmoiljonVahobjonov/orbital-portfolio) | ffae0e5  | ScrollChoreo measures section offsets; CameraRig reads mutable spherical camera state; Scene owns one persistent context with local studio lighting   | Keep the architecture principle; independently author Vite/robot-specific choreography. Its fictional claims and watch assets are not relevant. |
| [aether-boilerplate](https://github.com/giuucmp/aether-boilerplate)           | 54223c6  | canvas-wrapper quality tiers and visibility pause; split-text-reveal masked typography with reduced-motion cleanup                                    | Use existing React/CSS/GSAP; no Next migration, Framer Motion, Lenis or placeholder product model.                                              |
| [Apple-build](https://github.com/Harshit8bit/Apple-build)                     | 5db7320  | ProductViewer separates product state from controls; StudioLights uses locally generated reflection panels; Showcase changes behavior at tablet width | Use product lighting and controlled composition principles, not Apple branding, footage or model-switching assets.                              |
| [Portfolio-cinematic](https://github.com/Rohithpranov07/Portfolio-cinematic)  | 2c1a0b9  | StaggerTextReveal masks words; scroll-morph-hero derives composition from a shared progression; README describes scoped cleanup                       | Adopt restrained typography reveals; avoid its desktop-only compositions, Spline and multiple animation engines.                                |
| [cinematic-portfolio](https://github.com/guneet-baweja/cinematic-portfolio)   | 83e641b  | SceneCanvas has stable ownership; sceneResolver separates deterministic base pose from temporary input offsets                                        | Author a small typed robot pose resolver; omit particles, tunnel effects and postprocessing.                                                    |

No license file or explicit reuse grant was detected in any of the five repository trees/READMEs. They are research references only: no source code or assets will be imported. Lando Norris remains the visual reference for subject-led composition, editorial hierarchy and deliberate transitions; no racing assets or branding are reused. A read-only request to cuty.mx reset the connection in this environment; the local repository is the implementation source of truth. Existing production dashboard/domain behavior cannot be certified from that failed request.

## Visual specification

- Identity: retain the two-eye mark, C.U.T.Y. name, actual black V17 assembly and original green-eye/pink-mouth LCD frames. Purple #8B5CF6, lavender #C4B5FD, ink #17141F, paper #F5F3FA.
- Hero: full viewport, paper background, oversized geometric wordmark behind the robot. Product fills most of the height; short secondary copy and one primary action. Camera tools appear on explicit exploration, not as permanent hero chrome.
- Meet: dark chapter, robot on the left and camera approaching the head. Right-aligned editorial text introduces documented voice, vision and personality.
- Expressions: paper chapter, close-up of the actual LCD at the right; existing original face controls remain functional at the left. Demo is explicitly offline.
- Technology: three-quarter engineering orbit, concise component selector and evidence, with the original architecture/specifications available in a disclosure.
- PCB: actual Gerber previews, physical front/back inspection, pan/zoom, native-footprint highlights and source-backed pin details. No fictional assembled 3D board.
- Wiring: independently readable technical diagram and tables. Power, ground and communication use stable distinct colors with text labels and status.
- Development: genuine milestones with strong hierarchy, no invented percentages. Robot returns in a smaller full-body composition.
- Live: offline entry and future dashboard boundary, without fabricated remote controls or a dead dashboard URL.

## Scene architecture

One homepage-owned lazy scene remains mounted across all chapters. A GSAP controller measures chapter positions, builds one canonical timeline, and writes progress to an imperative channel. A pure typed resolver interpolates camera orbit, distance, target, screen composition and visibility. R3F reads the channel without React scroll rerenders. Anchor jumps, reverse scrolling, resize and disclosure height changes must resolve to the same pose. DOM heading reveals are scoped and cleaned up separately.

Explicit Explore mode gives OrbitControls exclusive ownership, centralizes framing, and exposes existing presets/zoom/reset/wireframe/autorotation. Escape/Close restores the current chapter. Native scrolling remains authoritative outside exploration. Reduced motion snaps between readable static compositions; mobile uses a dedicated framing track, lower DPR and no idle drift. PCB/wiring keep the canvas mounted but dormant while diagrams own the viewport.

Lighting uses a small local studio environment with broad white reflection panels, soft fill and a restrained purple rim, without external HDRs or postprocessing. Source geometry is retained; shared materials, bounded DPR, on-demand rendering, tab visibility and inactive-chapter pausing control cost. No unmeasured performance score is claimed.

## Engineering sources and missing evidence

- KiCad carrier V1.1: 100 x 92 mm, 1.6 mm, two layers. PCB, schematic, BOM, Gerbers, drill files and front/back previews exist. Fabrication, assembly and electrical validation remain pending.
- No verified standalone PCB GLB/STEP or articulated component assembly is available. The 3D slot must say so; exploded view is unavailable.
- Export the web component inventory/pad coordinates from the actual `.kicad_pcb` and compare pin/net assignments against `scripts/netlist.py`. Previews stay unaltered. Downloads are copies of actual project files.
- Pi/display/ReSpeaker pins use physical numbering, with BCM names shown separately. ReSpeaker J14 pins 11/19/23/32/33 must stay open in this carrier design. Module revisions, shared-pin behavior and current manual wiring require inspection.
- Pi UART physical 8/10 to STM32 PA3/PA2; PWM PB6-PB9/PA8 via 220-ohm resistors; battery divider PA1; all proposed carrier connections, not tested firmware.
- Separate 6 V servo buck and 5.1 V/5 A Pi supply are design targets; actual regulator model/current capability and load budget are unverified. LiPo protection/charging remains external. PGND and logic GND meet at NT1; rails are not interchangeable.
- OV5647 CSI startup is documented, but individual ribbon contacts are not mapped here. Do not invent a connector pinout.

## Validation gates

Unit tests for deterministic choreography, source parity and engineering filters; existing interactions retained. Browser tests and screenshots at desktop, tablet and mobile, including reverse/anchor scroll, one persistent canvas, manual ownership, face controls, front/back PCB selection, search/filter, reduced motion and missing-model fallback. Inspect readable copy and model framing in captures, fix issues, then run lint and production build. Preserve static Vite deployment and keep any authenticated controls outside this marketing app.

## Implementation note

Static V17 presentation geometry is batched into one body mesh plus the original separate LCD, preserving source triangle count and bounds. No triangle decimation or source GLB rewrite is performed. The PCB inspection remains source-derived 2D; a verified PCB 3D export is absent.

External regulator isolation and ground topology remain unresolved: a non-isolated USB-C supply may provide a second PGND–GND path outside the PCB NT1. This is a design integration inference requiring continuity/bench verification, not a confirmed hardware fault.
