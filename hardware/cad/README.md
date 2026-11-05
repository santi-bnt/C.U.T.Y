# C.U.T.Y CAD

SolidWorks native files are the mechanical source of truth.

| Area | Contents |
| --- | --- |
| `solidworks/parts/` | Native `.SLDPRT` parts |
| `solidworks/assemblies/` | Native `.SLDASM` assemblies |
| `step/` | Exported interoperability files |
| `stl/` | 3D-printing exports |
| `carcasa_v17/` | Carcasa imprimible V17 «Nido»: 30 STL para cama de 180 mm, renders, verificación y su fuente paramétrica en CadQuery |

STEP/STL are derived exports, never replacements for native sources. Record units, source revision, and export purpose with future assets. `carcasa_v17/` is generated from its own CadQuery source (`carcasa_v17/fuente_cad/`): millimetres, Z up, front −Y; exported for printing on a Bambu A1 mini and for import into Fusion. Revision V17, 2026-11-05.
