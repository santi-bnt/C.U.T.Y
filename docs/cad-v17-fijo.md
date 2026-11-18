# V17 fijo: STL y modelo web

La configuración prevista usa tres MG996R: cabeza PAN, brazo izquierdo y brazo derecho. La PCB conserva cinco salidas: J7–J9 son asignaciones propuestas y J10/J11 están reservados. Las conexiones físicas aún no se han validado.

La selección de los 27 STL, sus hashes y la comparación con los archivos anteriores está en [stl-selection.json](../hardware/cad/carcasa_v17_fija/stl-selection.json). Los diez STL prioritarios del ZIP de piezas nuevas coinciden byte por byte con los originales de la carpeta fija. Los sufijos (2) son copias. La comprobación anterior y posterior no detectó cambios en los STL ni en los archivos de la carrier PCB.

El GLB contiene las 27 mallas originales y conserva sus vértices y orden de triángulos; las piezas se colocan con rotaciones y traslaciones rígidas. [El manifiesto](../web/public/assembly/fixed-stl-manifest.json) registra hashes, dimensiones, matrices y referencias. Los planos de ubicación provienen del código CAD y las posiciones compartidas del GLB Nido histórico. Los componentes comprados son envolventes simplificadas; se omitieron ocho tornillos nuevos, el cable de batería y la unión XT60.

Los pivotes se basan en los ejes del CAD; las amplitudes son ilustrativas y no están calibradas. Las colisiones exactas del GLB no se han repetido: CadQuery no pudo cargar una dependencia bloqueada por la política de aplicaciones del sistema. Hay que verificar transformaciones y holguras en CAD, y el ajuste físico antes de fabricar o mover el mecanismo.

Para reproducir el GLB, ejecutar desde web/ los comandos `npm ci` y `node scripts/build-fixed-model.mjs`. El script verifica los hashes y vértices; no repara ni vuelve a triangular los STL. El modelo sin cuantización ocupa aproximadamente 22 MB. El GLB histórico se conserva en hardware/cad/glb/archive/ como fuente de referencias compradas.
