# C.U.T.Y CAD

SolidWorks native files are the mechanical source of truth.

| Area | Contents |
| --- | --- |
| `solidworks/parts/` | Native `.SLDPRT` parts |
| `solidworks/assemblies/` | Native `.SLDASM` assemblies |
| `step/` | Exported interoperability files |
| `stl/` | 3D-printing exports |
| `glb/` | Visualization exports, including `CUTY_V17_Ensamble_completo.glb` |

STEP/STL/GLB are derived exports, never replacements for native sources. Record units, source revision, and export purpose with future assets.

`glb/CUTY_V17_Ensamble_completo.glb` is the supplied V17 visualization assembly: 110 meshes and 116,741 triangles, with CAD coordinates interpreted as millimeters and Z vertical (source extents 180 × 173.02 × 365). It was moved from the repository root without conversion or geometry changes. The web copy remains at `web/public/models/cuty.glb`; black materials and the animated LCD are runtime effects described in [the web README](../../web/README.md).
