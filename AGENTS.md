# Guía para cambios en C.U.T.Y

- Prioriza la legibilidad: usa nombres descriptivos y conserva las convenciones técnicas existentes.
- Escribe comentarios en español claro; mantén identificadores, protocolos, APIs y términos técnicos en inglés cuando corresponda.
- Explica dentro del código las decisiones no obvias, los límites de seguridad, las unidades y las condiciones de error.
- No repitas en comentarios lo que ya expresa claramente la instrucción ni agregues texto artificial o tutoriales extensos.
- Describe solo el comportamiento implementado; identifica explícitamente lo simulado, no conectado o pendiente.
- Conserva compatibilidad, seguridad, determinismo y rendimiento. No cambies comportamiento como parte de una mejora de comentarios.
- Evita modificar archivos generados por STM32CubeMX/HAL; conserva sus secciones de usuario y no edites dependencias vendorizadas sin necesidad.
