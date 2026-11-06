# Review of user-provided assembly artifact

Inspected 2026-11-06. Source: `C:/Users/santi/Downloads/Ensamble C.U.T.Y (Copy).zip`.

Archive SHA256: `869679b75363f0c711bbb636bca4e31b889fd22324c6fa4cdc42d8bcfeac12df`.

## Recovered content

- One self-contained HTML assembly guide, with inline CSS, JavaScript, embedded fonts and a base64 WebP PCB preview.
- 18 WebP images under `img3d/`, depicting robot assembly stages.
- Native-looking component metadata (`PARTS`) for 43 reference designators, plus 2D image annotation anchors.
- SVG electrical illustrations and a scripted playback timeline. The HTML displays a 25-step label; no claim that these assembly instructions were physically validated follows from this.

Inspection copies were extracted under ignored `web/node_modules/.cache/cuty-artifact/`. The original ZIP was not modified. No application code from the archive was executed, and no guide content was published.

## Not a recoverable 3D assembly

The ZIP contains no GLB, glTF, STEP, STL, mesh vertex data, Three.js scene or 3D camera. The apparent 3D robot stages are pre-rendered WebP images, animated with cross-fades, image scaling and SVG annotations. The HTML has an optional image-sequence playback path, but the frame sequence files are absent from this ZIP. The existing real V17 GLB remains the website's 3D source.

The PCB preview can be recovered as a bitmap; it cannot supply verified depth, component geometry or an orbitable assembly. A real PCB export still requires the source CAD/3D export.

## Comparison with current repository

Compared the artifact PARTS data with `src/data/carrier.generated.json`, which is exported and net-checked from the native carrier PCB.

- All 43 reference designators match.
- All component value strings match.
- All 227 exported pad identifiers are present.
- 223 pad coordinates agree within 0.03 mm.
- Four fuse-pad coordinates differ by 3.40 mm in Y:

| Pad | Artifact XY (mm) | Current PCB XY (mm) |
| --- | --- | --- |
| F1.1 | 44.00, 17.90 | 44.00, 14.50 |
| F1.2 | 53.92, 17.90 | 53.92, 14.50 |
| F2.1 | 24.00, 17.90 | 24.00, 14.50 |
| F2.2 | 33.92, 17.90 | 33.92, 14.50 |

This demonstrates substantial layout agreement, not electrical/assembly validation. Do not replace current native footprint hit regions or pin mappings with artifact coordinates. The image and guide may reflect another export/revision; its exact provenance is not established by the ZIP.

The guide describes delivery from JLCPCB and assembled components as instructional scenarios. These do not establish manufacturing or physical test completion. Its product choices, screw counts, printing estimates and electrical instructions need independent validation before adoption as project specifications.

## Reusable material

The supplied images and playback structure can inform an explicitly illustrative assembly walkthrough. Keep the existing native KiCad metadata as source of truth, label rendered imagery as such, and avoid changing the robot's requested black appearance or claiming the walkthrough provides articulated 3D parts. No website replacement or production deployment was performed during this review.
