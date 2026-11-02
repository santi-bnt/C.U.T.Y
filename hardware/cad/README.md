# C.U.T.Y CAD

SolidWorks native files are the mechanical source of truth.

| Area | Contents |
| --- | --- |
| `solidworks/parts/` | Native `.SLDPRT` parts |
| `solidworks/assemblies/` | Native `.SLDASM` assemblies |
| `step/` | Exported interoperability files |
| `stl/` | 3D-printing exports |

STEP/STL are derived exports, never replacements for native sources. Record units, source revision, and export purpose with future assets. No model creation or conversion is performed in this task.
