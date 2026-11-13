# C.U.T.Y CAD

SolidWorks native files are the mechanical source of truth.

| Area | Contents |
| --- | --- |
| `solidworks/parts/` | Native `.SLDPRT` parts |
| `solidworks/assemblies/` | Native `.SLDASM` assemblies |
| `step/` | Exported interoperability files |
| `stl/` | 3D-printing exports |
| `glb/` | Visualization exports, including `CUTY_V17_Ensamble_completo.glb` |
| `carcasa_v17/` | Printable V17 “Nido” enclosure: 30 STL files, renders, verification, and parametric CadQuery source |
| `carcasa_v17_fija/` | Fixed V17 variant on a low pedestal; only head and arms move. Includes 27 STL files, renders, and verification; generated from the same `carcasa_v17/` source with `CUTY_FIJO=1` |

STEP/STL/GLB are derived exports, never replacements for native sources. Record units, source revision, and export purpose with future assets.

`glb/CUTY_V17_Ensamble_completo.glb` is the supplied V17 visualization assembly: 110 meshes and 116,741 triangles, with CAD coordinates interpreted as millimeters and Z vertical (source extents 180 × 173.02 × 365). It was moved from the repository root without conversion or geometry changes. The web copy remains at `web/public/models/cuty.glb`; black materials and the animated LCD are runtime effects described in [the web README](../../web/README.md).

`carcasa_v17/` is generated from its own CadQuery source (`carcasa_v17/fuente_cad/`): millimetres, Z up, front −Y; revision V17, 2026-11-05, prepared for a Bambu A1 mini and Fusion.
