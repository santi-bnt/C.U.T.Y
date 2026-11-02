# C.U.T.Y — Cute Utility That Yaps

Menú táctil ligero para Raspberry Pi 5 y pantalla SPI de 480 × 320.
Utiliza Pillow, evdev, NetworkManager y el framebuffer Linux, sin HDMI.

- **Terminal:** comandos no interactivos ejecutados como el usuario `santi`.
- **Internet:** búsqueda Wi-Fi, teclado, mostrar/ocultar contraseña, IP y diagnóstico.
  Reutiliza perfiles guardados por SSID; las nuevas conexiones usan el SSID como nombre.
- **C.U.T.Y:** cara de prueba. Mantén presionada cualquier zona durante
  **5 segundos continuos** para regresar; soltar antes cancela la pulsación.

## Raspberry actual

Directorio: `/home/santi/C.U.T.Y`. Servicio: `cuty-launcher.service`.
Pantalla: `/dev/fb1`, RGB565, overlay `waveshare35a`.
El táctil ADS7846 se localiza por nombre, no por número de evento.
La calibración validada se conserva en `/home/santi/cuty_touch_calibration.json`
y no se incluye en Git. No es necesario reinstalar drivers ni recalibrar.

Dependencias del sistema: Python 3, Pillow, evdev, NetworkManager (`nmcli`),
`ip`, `ping`, `getent` y fuentes DejaVu. `requirements.txt` enumera las bibliotecas Python.

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
La cara es una demostración: no integra audio, cámara ni servos.

No subir contraseñas, perfiles de NetworkManager, calibración local, grabaciones
ni respaldos. El ZIP se conserva como archivo histórico; el código `.py`
extraído contiene los cambios actuales.
