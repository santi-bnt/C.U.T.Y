# C.U.T.Y — Cute Utility That Yaps

Menú táctil ligero para Raspberry Pi 5 y pantalla SPI de 480 × 320.
Utiliza Pillow, evdev, NetworkManager y el framebuffer Linux, sin HDMI.

- **Terminal:** comandos no interactivos ejecutados como el usuario `santi`.
- **Internet:** búsqueda Wi-Fi, teclado, mostrar/ocultar contraseña, IP y diagnóstico.
  Reutiliza perfiles guardados por SSID; las nuevas conexiones usan el SSID como nombre.
- **C.U.T.Y:** cara animada. Los ojos parpadean, miran alrededor y, con
  cámara, **siguen a la persona**. La boca se mueve cuando C.U.T.Y habla.
  Un toque corto la hace parpadear. Mantén presionada cualquier zona durante
  **5 segundos continuos** para regresar; soltar antes cancela la pulsación.

## Raspberry actual

Directorio: `/home/santi/C.U.T.Y`. Servicio: `cuty-launcher.service`.
Pantalla: SPI `fb_ili9486`, 480 × 320, RGB565, overlay `waveshare35a`.
Se detecta por nombre y formato, sin depender de que sea `/dev/fb0` o `/dev/fb1`
ni de que haya HDMI conectado. El servicio espera hasta 60 segundos a que aparezca.
El táctil ADS7846 se localiza por nombre, no por número de evento.
La calibración validada se conserva en `/home/santi/cuty_touch_calibration.json`
y no se incluye en Git. No es necesario reinstalar drivers ni recalibrar.

Dependencias del sistema: Python 3, Pillow, evdev, NumPy, NetworkManager (`nmcli`),
`ip`, `ping`, `getent` y fuentes DejaVu. Para que los ojos sigan a la persona:
OpenCV y, con la cámara de la Raspberry, Picamera2. `requirements.txt` enumera
las bibliotecas Python. En Raspberry Pi OS:

```sh
sudo apt install python3-numpy python3-opencv python3-picamera2
```

Sin cámara u OpenCV la cara funciona igual y los ojos curiosean solos.

## Cara animada

El launcher dibuja la cara con `cuty.face` (en `../src`) a 20 fps y solo
envía por SPI las filas que cambiaron. La cámara corre en un hilo aparte
únicamente mientras la cara está en pantalla.

La voz (`python -m cuty`) envía expresiones y el nivel de la boca al puerto
UDP local 5005; se puede iniciar antes o después del launcher. Prueba rápida
sin voz, con la cara en pantalla:

```sh
python3 -c "import socket,json; socket.socket(2,2).sendto(json.dumps({'v':1,'type':'expression','expression':'happy','intensity':1}).encode(),('127.0.0.1',5005))"
```

| Variable | Valor inicial | Uso |
| --- | --- | --- |
| `CUTY_START_MODE` | `menu` | `face` para arrancar directamente en la cara |
| `CUTY_FACE_FPS` | `20` | cuadros por segundo |
| `CUTY_FACE_SSAA` | `2` | suavizado de bordes (`1` si se necesita más velocidad) |
| `CUTY_FACE_LISTEN` | `127.0.0.1:5005` | `0.0.0.0:5005` para recibir la voz desde una PC |
| `CUTY_CAMERA` | `auto` | `picamera`, `usb` u `off` |
| `CUTY_CAMERA_MIRROR` | `1` | `0` si los ojos se mueven al lado contrario |
| `CUTY_CAMERA_ROTATE` | `0` | `180` si la cámara está montada al revés |

Para fijarlas en el servicio, añade líneas `Environment=` en
`cuty-launcher.service` (por ejemplo `Environment=CUTY_START_MODE=face`).

## Prueba manual

Con acceso SSH o terminal disponible, detén los programas que usan la pantalla:

```sh
sudo systemctl stop cuty-launcher.service cuty-wifi-panel.service
sudo python3 /home/santi/C.U.T.Y/cuty_launcher.py
```

Ctrl+C termina la prueba. Para restaurar el menú instalado:

```sh
sudo systemctl start cuty-launcher.service
```

## Arranque automático

El menú ya está habilitado en la Raspberry actual. Para una instalación en
esta misma ruta, después de probar manualmente:

```sh
bash /home/santi/C.U.T.Y/cuty-install.sh
```

No ejecutes simultáneamente el panel antiguo, el espejo ni el menú.
El servicio actual corre como root para acceder al hardware; la terminal
usa `runuser` para ejecutar comandos como `santi`.

## Estado y límites

Panel Wi-Fi y menú probados en la pantalla por el usuario. Inicio automático
configurado; pendiente confirmar tras reinicio. La red Tec (PEAP/MSCHAPv2,
validación de certificados habilitada) necesita validación en campus.
El diagnóstico distingue Wi-Fi de Internet; ICMP puede estar bloqueado.
Escaneo y conexión todavía pueden bloquear temporalmente la interfaz.
La cara integra cámara y voz, pero falta validarla en la pantalla y la cámara
físicas; no mueve servos.

No subir contraseñas, perfiles de NetworkManager, calibración local, grabaciones
ni respaldos. El ZIP se conserva como archivo histórico; el código `.py`
extraído contiene los cambios actuales.
