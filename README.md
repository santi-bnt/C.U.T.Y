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
- Pantalla: menú Terminal/Internet/C.U.T.Y, Wi-Fi, cara demo, toque para parpadear y pulsación continua de cinco segundos para volver al menú.
- Ambas partes están integradas en el repositorio. La cara todavía **no está conectada** a las expresiones ni al audio de la conversación.
- Servos, cámara, firmware, dashboard, PCB y mecánica siguen sin implementarse.

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
