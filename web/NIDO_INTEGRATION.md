# Nido asset integration plan — 2026-11-06

User authorized use of all three provided ZIP archives, followed by requests for a pre-reveal C.U.T.Y. typographic intro and 3D wiring simulation.

## Sources

- Assembly artifact: HTML, 18 pre-rendered assembly WebPs, embedded PCB bitmap and metadata; no mesh. Prior audit in ARTIFACT_REVIEW.md. Four fuse pad coordinates differ from current KiCad.
- Nido browser artifact: actual Base64-wrapped, quantized GLB; 111 named parts, materials, illustrative pivot/explosion code and original face PNGs. An earlier revision: not the preferred geometry source now.
- CUTY_V17_Nido_rev.zip: revised native GLB (109 meshes, 318,023 triangles), 30 printable STL and STEP parts, full assembly STEP, CadQuery source, part dimensions and an author-supplied CAD verification report. The README mentions renders/textures that are absent from this ZIP; recover those from the two artifacts instead. Bought electronics are explicitly simplified solids in refs.py.

## Implementation

Use the revised geometry as the authoritative new web model, optimized with gltfpack 1.3.0, named nodes/materials retained, no triangle simplification requested, meshopt compression with the existing local Three/Drei decoder. Keep original robot face atlas integration and black exterior. Add named-part inspection, exploded view and a limited, explicitly visual head/arm demo, not motor control or mechanical validation.

Recover supplied assembly images for an editorial, bilingual walkthrough and offer actual source STL/doc/verification downloads on demand. Avoid importing unverified screw counts, purchased ratings or collision results as measured physical capabilities.

Replace the PCB missing-model state with a viewer of the actual revised CAD electronics subset. Label it a mechanical reference with simplified components, not a validated KiCad 3D export. Preserve native 2D pad/net data and show known revision differences.

Add 3D functional wiring on the actual interior geometry, with selected components, class-colored schematic paths and filters synchronized to existing source-backed tables. Endpoints derive from actual named mesh bounds. Curves are illustrative relationships, not harness routing; cable contacts remain unverified. Keep a 2D overview option.

Add an accessible typographic intro before robot reveal: skip, reduced-motion bypass, local DOM animation only. Preserve one homepage canvas and lazy independent technical viewers, paused when hidden. No firmware, GPIO, service, auth or domain changes; no production deployment.

## Validation

Measure original/repacked GLB bounds, names and triangles; verify PCB reference mapping and preserve KiCad tests. Exercise intro skip, model display, explosion, pose demo, PCB front/back/selection, 3D wiring filters, assembly walkthrough and all existing camera/language/fallback controls. Review desktop/mobile screenshots, run lint/unit/browser suites and production build. Record actual optimization and unresolved limitations after implementation.

## Implemented outcome

### Current print CAD update · 2026-11-06

The repository includes `hardware/cad/carcasa_v17/`, the November 6 printable enclosure revision based on team-measured component envelopes. The website's interactive model has now been rebuilt from that CadQuery source and its `parts.json` reference data. The static export includes four supplied CAD renders, 30 oriented STL files, matching CadQuery source, part dimensions and the author's `verificacion.json`.

The November 6 source README reports measurements for the Pi 5, Display-G, ReSpeaker, OV5647 camera and speaker. It also notes the battery's exact size and the camera lens-center measurement remain pending. The accompanying model report lists 30 watertight parts, 0 exact static interferences, 18 cable-clearance zones and 34 poses. These remain author-supplied CAD results; no physical print or assembly validation is inferred.

### Carrier assembly order documentation

The merged hardware README records a THT assembly order at JLCPCB, with 37 supplier-soldered components. F1/F2 fuse holders and fuses, and the JP1 shunt, are hand-fitted. JLCPCB BOM/CPL/notes are linked from the PCB section. PCBWay's PCBA package remains available but is labeled as an alternative to the documented order. Receipt and electrical validation are not asserted by this website update.

The current web GLB is generated from the November 6 CadQuery source; the native geometry build remains in the ignored web cache and no robot source code is changed. gltfpack 1.3.0 produced a 1,093,424-byte asset with 113 named meshes and 192,642 triangles, retaining names/materials with quantization/compression and no requested simplification. Measured web bounds are about 180.00 × 365.00 × 173.41 mm. The rebuilt model measures the H3 visor at 10.72 mm and the H4 display/camera bars at 87.05 mm.

The recovered earlier GLB/HTML provided naming and interaction references, while the latest revised native GLB supplies rendered geometry. The old assembly artifact supplies 18 images; the earlier model artifact supplies poster/static face references. Thirty revised STL files and original source documents are downloadable. The source archives themselves remain in Downloads.

A 45-solid PCB mechanical subset is exported from the revised CAD. Its components are simplified source solids, not an electrically validated KiCad 3D export. Four fuse pad coordinates differ from current native PCB coordinates by 3.4 mm Y. Native PCB tables remain authoritative for the CAD view.

The user later supplied an explicit operational hookup table. It supersedes inference about which connections are tested: Waveshare and ReSpeaker are builder-confirmed, while STM32 UART/PWM pin assignments, power distribution and final PCB remain pending. `operationalWiring.ts` drives the wiring simulation/tables; `engineering.ts` retains distinct native CAD proposals. A subsequent explicit ReSpeaker table adds MCLK physical7 / BCM4 and AUD_RST physical37 / BCM26, and fixes power/ground to physical1/4/6. The current operational data follows that latest 11-row table.

Intro uses a roughly three-second DOM typographic sequence with Skip, reduced-motion bypass and deep-link bypass. Manual exploration adds inside/exploded views and rigid-part motion simulations. 3D wiring uses actual CAD interior solids and schematic curves; no physical cable routes or pin coordinates are asserted. Separate technical viewers are lazy and demand-rendered. No backend, motor commands or production deployment.
