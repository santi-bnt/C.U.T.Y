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
│   ├── cad/           SolidWorks y exportaciones STEP/STL/GLB
│   └── electronics/   KiCad, esquemas y datasheets
├── web/               Portafolio EN/ES y visor 3D; dashboard conectado futuro
└── docs/              Arquitectura, planes y protocol/
```

Las entradas de voz, pantalla e instalación están dentro de `raspberry/`. El GLB fuente está en `hardware/cad/glb/` y la copia que usa el visor en `web/public/models/`. La raíz conserva documentación, licencia y configuración del repositorio; ya no contiene lanzadores de compatibilidad. Las carpetas ocultas del entorno no son módulos del robot.

## Estado

- Voz: push-to-talk, Gemini predeterminado, OpenAI opcional, búsqueda web, contexto de sesión, idioma según la pregunta y frases de espera en español.
- Pantalla: menú Terminal/Internet/C.U.T.Y, Wi-Fi y **cara animada**: ojos que parpadean y miran alrededor, toque para parpadear y pulsación continua de cinco segundos para volver al menú.
- Cara conectada: con cámara, los ojos **siguen a la persona**; las expresiones de la conversación aparecen en la cara y la **boca se mueve con la voz** (enlace UDP local entre la voz y la pantalla). Ver [cara](docs/face.md).
- Conversación desde el menú: toca C.U.T.Y para recibir un saludo y hablar sin ENTER; di «quiero salir» para volver al inicio. Usa Gemini, el entorno existente y una clave local en `.env`. Ver [configuración](raspberry/touchscreen/README.md#conversación-desde-el-menú).
- Electrónica: [carrier PCB v1.1](hardware/electronics/kicad/cuty_carrier/README.md) para Raspberry Pi 5 y STM32F401 Black Pill, con KiCad, Gerbers, BOM y esquemático. Fabricación, montaje y validación eléctrica pendientes.
- Firmware STM32F401, control de servos, dashboard y mecánica siguen pendientes de implementación.

Raspberry posee IA, voz, pantalla, visión y comportamiento. STM32 poseerá PWM, movimiento, IMU, PID y seguridad: recibirá objetivos de alto nivel, no PWM continuo. Los ejemplos UART siguen siendo propuestas.

## Voz en Windows

Desde la raíz, entra al proyecto de Raspberry y utiliza su entorno:

```powershell
cd raspberry
.\.venv\Scripts\python.exe -m cuty
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Preparación del entorno desde la raíz del repositorio: `./raspberry/scripts/dev_setup.ps1`.
Consulta [la guía de voz](raspberry/README.md). Configura `raspberry/.env`; el lector aún admite un `.env` en la raíz para instalaciones anteriores. No subir claves.

## Pantalla en Raspberry

Consulta [las instrucciones de pantalla](raspberry/touchscreen/README.md). Requiere Linux, framebuffer RGB565, ADS7846, calibración local y dependencias de sistema. Las dependencias Python de pantalla están separadas en `raspberry/touchscreen/requirements.txt`; no instalar evdev en Windows.

Entrada manual: `sudo python3 raspberry/touchscreen/cuty_launcher.py` desde la raíz. Instalación explícita: `bash raspberry/touchscreen/install.sh`, después de probar la pantalla. El servicio actual ya apunta a `raspberry/touchscreen/cuty_launcher.py`; esta limpieza no cambia sus rutas ni la calibración del hardware.

## Web

Consulta [ejecución y despliegue](web/README.md). Desde `web/`, usa `npm ci` y `npm run dev` para abrir el portafolio con el robot negro y su LCD integrado. La web es frontend y funciona sin una Raspberry encendida.

[Arquitectura](docs/architecture.md) · [Roadmap](docs/roadmap.md) · [Protocolo](docs/protocol/protocol.md) · [Movimientos e integración](docs/reorganization.md)

[Mapa de conexiones por bloques (HTML)](docs/conexiones.html) · [Señales (SVG)](docs/assets/conexiones-senales.svg) · [Alimentación (SVG)](docs/assets/conexiones-alimentacion.svg)

Las pruebas locales no certifican la pantalla física ni el arranque de su servicio tras reiniciar la Raspberry
