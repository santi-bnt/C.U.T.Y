# C.U.T.Y — Cute Utility That Yaps

Compañero de escritorio expresivo. La voz desarrollada en Windows y el menú/cara subidos desde la Raspberry conviven en este repositorio.

## Cinco áreas principales

```text
C.U.T.Y/
├── raspberry/
│   ├── src/cuty/      Voz, conversación y proveedores
│   ├── touchscreen/   Menú táctil, cara demo, Wi-Fi y servicio
│   ├── tests/
│   ├── scripts/       Preparación de Windows/Raspberry
│   └── systemd/       Plantilla futura del servicio de voz
├── stm32/             Firmware futuro: servos, IMU, PID, UART y seguridad
├── hardware/
│   ├── cad/           SolidWorks y exportaciones STEP/STL
│   └── electronics/   KiCad, esquemas y datasheets
├── web/               Dashboard y gemelo digital futuros
└── docs/              Arquitectura, planes y protocol/
```

Los archivos de arranque de la raíz son wrappers de compatibilidad, no otras copias de la aplicación. Las carpetas ocultas del entorno no son módulos del robot.

## Estado

- Voz: push-to-talk, Gemini predeterminado, OpenAI opcional, búsqueda web, contexto de sesión, idioma según la pregunta y frases de espera en español.
- Pantalla: menú Terminal/Internet/C.U.T.Y, Wi-Fi y **cara animada**: ojos que parpadean y miran alrededor, toque para parpadear y pulsación continua de cinco segundos para volver al menú.
- Cara conectada: con cámara, los ojos **siguen a la persona**; las expresiones de la conversación aparecen en la cara y la **boca se mueve con la voz** (enlace UDP local entre la voz y la pantalla). Ver [cara](docs/face.md).
- Conversación desde el menú: toca C.U.T.Y para recibir un saludo y hablar sin ENTER; di «quiero salir» para volver al inicio. Usa Gemini, el entorno existente y una clave local en `.env`. Ver [configuración](raspberry/touchscreen/README.md#conversación-desde-el-menú).
- Electrónica: [carrier PCB v1.1](hardware/electronics/kicad/cuty_carrier/README.md) para Raspberry Pi 5 y STM32F401 Black Pill, con KiCad, Gerbers, BOM y esquemático. Fabricación, montaje y validación eléctrica pendientes.
- Firmware STM32F401, control de servos, dashboard y mecánica siguen pendientes de implementación.

Raspberry posee IA, voz, pantalla, visión y comportamiento. STM32 poseerá PWM, movimiento, IMU, PID y seguridad: recibirá objetivos de alto nivel, no PWM continuo. Los ejemplos UART siguen siendo propuestas.

## Voz en Windows

Desde la raíz, con el entorno existente:

```powershell
.\.venv\Scripts\python.exe -m cuty
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Preparación del entorno: `./raspberry/scripts/dev_setup.ps1`.
Consulta [la guía de voz](raspberry/README.md). Se conserva el `.env` privado de la raíz; también se admite `raspberry/.env`. No subir claves.

## Pantalla en Raspberry

Consulta [las instrucciones de pantalla](raspberry/touchscreen/README.md). Requiere Linux, framebuffer RGB565, ADS7846, calibración local y dependencias de sistema. Las dependencias Python de pantalla están separadas en `raspberry/touchscreen/requirements.txt`; no instalar evdev en Windows.

Los comandos anteriores `sudo python3 cuty_launcher.py` y `bash cuty-install.sh` siguen funcionando mediante wrappers. El instalador cambia servicios: solo se ejecuta manualmente en la Raspberry, después de probar la pantalla. No se ejecutó durante esta integración.

[Arquitectura](docs/architecture.md) · [Roadmap](docs/roadmap.md) · [Protocolo](docs/protocol/protocol.md) · [Movimientos e integración](docs/reorganization.md)

Las pruebas locales no certifican la pantalla física ni el arranque de su servicio tras reiniciar la Raspberry.
