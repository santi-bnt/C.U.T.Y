# Integración de Raspberry y estructura simplificada

## Origen y alcance

Se ejecutaron `git fetch origin` y `git merge --ff-only origin/main`: la rama local pasó de `39effb9` a `7bfb392`, incorporando también `d7790b5`. No se hizo force push ni se crearon commits adicionales para la reorganización. Los cambios locales previos se conservaron. Esta reorganización aún debe revisarse, añadirse y publicarse mediante Git para llegar a la Raspberry.

El menú táctil y el panel Wi-Fi proceden de GitHub. Sus dos archivos Python y el ZIP se conservaron idénticos al contenido remoto. El ZIP es histórico; los `.py` extraídos contienen las correcciones más recientes. La voz existente permanece en `raspberry/src/cuty`.

Se integraron los archivos en el repositorio, no la ejecución de voz y pantalla: el demo de cara todavía no recibe eventos de conversación ni amplitud de audio. No se añadieron motores, visión, firmware ni dependencias nuevas. Pillow y evdev ya eran dependencias del código remoto y se mantienen separadas de Windows.

## Árbol principal

```text
C.U.T.Y/
├── raspberry/
│   ├── src/cuty/
│   │   ├── brain/       Conversación, personalidad, estados
│   │   ├── llm/         Gemini/OpenAI y búsqueda; fallback local pendiente
│   │   ├── audio/       Micrófono, altavoz y frases de espera
│   │   ├── face/        Eventos de expresión y renderer reutilizable futuro
│   │   ├── vision/      Reservado
│   │   ├── hardware/    Bridge STM32 futuro
│   │   ├── telemetry/   Reservado
│   │   └── utils/
│   ├── touchscreen/    Menú/cara/Wi-Fi existentes y servicio
│   ├── scripts/        Preparación de entornos
│   ├── systemd/        Plantilla de voz, no habilitada
│   └── tests/
├── stm32/              Firmware futuro, sin implementaciones nuevas
├── hardware/
│   ├── cad/            Fuentes SolidWorks y STEP/STL exportados
│   └── electronics/    KiCad, esquemas y datasheets
├── web/                Dashboard/gemelo digital futuros
└── docs/
    └── protocol/       Ejemplos UART, no contrato binario definitivo
```

Se conserva la división interna de Python para no introducir cambios de imports innecesarios en código de voz que ya funciona. Las áreas futuras se mantienen agrupadas, sin desplegarlas como servicios reales.

## Movimientos de esta integración

| Antes | Ahora |
| --- | --- |
| `cad/` | `hardware/cad/` |
| `electronics/` | `hardware/electronics/` |
| `shared/` | `docs/protocol/` |
| `scripts/` | `raspberry/scripts/` |
| `.github/workflows/README.md` | `docs/automation.md` |
| `cuty/__init__.py` | `cuty.py` (compatibilidad de `python -m cuty`) |
| README de GitHub | `raspberry/touchscreen/README.md` |
| `README-CUTY-menu.txt` | `raspberry/touchscreen/README-CUTY-menu.txt` |
| `cuty_launcher.py` original | `raspberry/touchscreen/cuty_launcher.py` |
| `cuty_wifi_panel.py` original | `raspberry/touchscreen/cuty_wifi_panel.py` |
| `cuty_menu.zip` | `raspberry/touchscreen/cuty_menu.zip` |
| `cuty-launcher.service` | `raspberry/touchscreen/cuty-launcher.service` |
| `cuty-install.sh` original | `raspberry/touchscreen/install.sh` |
| requirements de pantalla de GitHub | `raspberry/touchscreen/requirements.txt` |

La reorganización anterior ya había trasladado `voz/` y `src/cuty/robot/` a los módulos de `raspberry/src/cuty/`, y los tests a `raspberry/tests/`. No se repitieron esos movimientos.

## Archivos creados o ajustados

- README raíz: estructura compacta y estado real de voz/pantalla.
- `hardware/README.md`: índice de mecánica y electrónica.
- `cuty.py`: acceso raíz a la aplicación de voz, sin duplicarla.
- Wrappers raíz `cuty_launcher.py`, `cuty_wifi_panel.py`, `cuty-install.sh`: conservan los comandos anteriores y el acceso desde el servicio ya instalado en la Raspberry.
- `requirements.txt` raíz: vuelve a instalar el proyecto de voz; las dependencias Linux de pantalla quedan aparte.
- `.gitignore`: unión de las exclusiones locales/remotas, incluyendo secretos, calibración y archivos generados.
- `.gitattributes`: scripts Bash y unidades systemd con LF para evitar problemas entre Windows y Raspberry.
- Scripts de preparación: rutas adaptadas a `raspberry/scripts/`.
- Instalador de pantalla: encuentra sus archivos desde su propia carpeta.
- Servicio de pantalla: apunta al archivo canónico nuevo. Conserva el usuario root, hardware y ruta de instalación existentes; no se habilitó ni ejecutó aquí.
- Documentos de arquitectura, cara, voz, firmware, electrónica y protocolos: enlaces/rutas ajustados y distinción entre demo existente e integración futura.
- `raspberry/tests/test_touchscreen_integration.py`: tres pruebas portables de RGB565, calibración/límites y rutas de arranque.

## Conservación y respaldo

No se eliminaron fuentes de código. Los directorios antiguos `src`, `voz`, `tests`, `cuty`, `systemd` y `.github` se comprobaron antes de apartarlos: solo contenían cachés Python, metadatos `.egg-info` o estaban vacíos. Se guardaron con prefijo `legacy-` en:

```text
C:\Users\santi\AppData\Local\Temp\cuty-integration-db8ebb73aa9949cfbe0dce300b6214b3
```

Ese respaldo también conserva los tres archivos raíz locales apartados antes del fast-forward. Es un respaldo temporal fuera de Git; no debe considerarse almacenamiento permanente. Los archivos generados pueden regenerarse preparando el entorno. La instalación editable antigua debe actualizarse con `raspberry/scripts/dev_setup.ps1` si se necesita lanzar la aplicación desde fuera de la raíz.

`.env`, `.venv`, `LICENSE` y cualquier configuración privada del editor no se trasladaron. La calibración de la Raspberry sigue fuera de Git en `/home/santi/cuty_touch_calibration.json`. No se adivinó una nueva placa, pinout ni ubicación para esa calibración.

## Validación y límites

Antes: 46 tests de voz pasaban. Después: 49 tests pasan, incluidos los tres nuevos tests de pantalla que no necesitan hardware Linux. El comando de ayuda de voz funciona desde la raíz. Se verifica que los archivos canónicos de pantalla y su ZIP coinciden con los blobs remotos.

No se probó físicamente framebuffer, touch, audio real, red Wi-Fi, reinicio de Raspberry ni activación de systemd. No se ejecutó ningún instalador, no se modificaron las redes y no se instalaron paquetes de pantalla en Windows.

Siguiente tarea recomendada: revisar/publicar los movimientos y probar el menú manualmente en la Raspberry antes de actualizar su servicio. Conectar cara y voz debe ser una tarea posterior explícita.
