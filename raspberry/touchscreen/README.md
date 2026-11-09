# C.U.T.Y — Companion Unit That Yaps

Menú táctil ligero para Raspberry Pi 5 y pantalla SPI de 480 × 320.
Utiliza Pillow, evdev, NetworkManager y el framebuffer Linux, sin HDMI.

- **Terminal:** comandos no interactivos ejecutados como el usuario `santi`.
- **Internet:** búsqueda Wi-Fi, teclado, mostrar/ocultar contraseña, IP y diagnóstico.
  Reutiliza perfiles guardados por SSID; las nuevas conexiones usan el SSID como nombre.
- **C.U.T.Y:** cara animada. Los ojos parpadean, miran alrededor y, con
  cámara, **siguen a la persona**. La boca se mueve cuando C.U.T.Y habla.
  Un toque corto la hace parpadear. Mantén presionada cualquier zona durante
  **5 segundos continuos** para regresar; soltar antes cancela la pulsación.

## Apagar y reiniciar desde la pantalla

En el menú principal, toca **Apagar / Reiniciar**, elige la acción y confirma
con **Sí, apagar** o **Sí, reiniciar**. **Cancelar** vuelve a las opciones y
**Menú** regresa al inicio. Seleccionar una acción no la ejecuta todavía.

Al confirmar se cierran la voz y la cámara y se solicita a systemd un apagado
o reinicio normal, sin forzarlo. La pantalla muestra el estado y bloquea toques
repetidos; si la solicitud falla, conserva un menú utilizable y registra el error.
El launcher utiliza los permisos root de su servicio existente; no instala
paquetes ni necesita cambios de sudoers, GPIO o del servicio.

Para apagar desde la cara, mantén la pulsación de cinco segundos para volver
al menú y utiliza el botón. Estas acciones pertenecen a la pantalla física;
el portafolio web sigue funcionando como demostración local del robot.

## Conversación desde el menú

Al tocar **C.U.T.Y**, el menú abre la cara e inicia la voz con
`raspberry/.venv/bin/python -m cuty --hands-free`, como el usuario `santi`.
Gemini saluda primero; después escucha automáticamente y responde cuando
terminas de hablar y haces una pausa. No hay que pulsar ENTER.

Di **«salir»**, **«quiero salir»** o **«regresa al menú principal»** cuando
esté escuchando para cerrar la conversación y regresar al inicio. También
se conserva la pulsación de cinco segundos para salir. Salir cierra la voz,
libera el micrófono y detiene la cámara. Al volver a entrar empieza una
conversación nueva. Si la voz falla, vuelve al menú y muestra un aviso.

También admite **«Cuty, quiero salir»**, «Oye Cuty, quiero salir» y el nombre
transcrito como «C.U.T.Y.» o «Cuti». Una llamada del modelo para cerrar sin
una orden explícita en la transcripción se rechaza; palabras ajenas como
«curiosarte» no deben cerrar la conversación. Las frases de espera salen
solo después de cinco segundos, como máximo una por turno; si ya empezó
una frase corta, termina antes de reproducir la respuesta.

Usa las dependencias ya preparadas en `raspberry/.venv`; esta función no
instala paquetes ni modifica el arranque, los overlays, ALSA o GPIO.
Selecciona automáticamente `seeed2micvoicec` si no hay dispositivos
explícitos en la configuración. No ejecutes otra sesión de voz a la vez.

La clave debe estar en `/home/santi/C.U.T.Y/raspberry/.env`:

```dotenv
GEMINI_API_KEY=TU_CLAVE_REAL
```

Ese archivo está excluido de Git. Una clave exportada en una terminal SSH
no llega al servicio del menú. Puedes editarlo con `nano` y limitar su
lectura con `chmod 600 /home/santi/C.U.T.Y/raspberry/.env`.
No pegues claves en GitHub, comandos compartidos o registros.

Después de actualizar el código, reinicia únicamente el launcher:

```sh
sudo systemctl restart cuty-launcher.service
```

Para revisar fallos sin mostrar el archivo de la clave:

```sh
journalctl -u cuty-launcher.service -n 60 --no-pager
```

El modo automático usa Gemini y detección local de energía, sin dependencias
nuevas. El micrófono se abre al escuchar y se cierra durante la respuesta:
espera a que termine de hablar para responder o pedir salir. No hay
interrupción de voz mientras habla. En sitios ruidosos puede requerir ajustar
`CUTY_VAD_THRESHOLD` (inicial `350`, RMS PCM16) o `CUTY_VAD_SILENCE`
(inicial `0.9`, segundos) en `.env`. Cada intervención tiene un límite
aproximado de veinte segundos. La sensibilidad requiere validación física.

La salida física se cierra antes de abrir la captura y vuelve a abrirse
después de cerrar el micrófono, para evitar mantener dos streams ALSA
simultáneos en el HAT. La detección inicial acumula voz dentro de una ventana
de 300 ms y permite interrupciones cortas entre sonidos. El registro indica
si llegan bloques PCM, su nivel RMS, el inicio de voz y el final por pausa;
estos mensajes no guardan grabaciones ni requieren paquetes adicionales.

Para conservar solo la cara, define `CUTY_MENU_VOICE=off` en el entorno
del launcher. Puedes probar la conversación por SSH, sin el menú, con
`python -m cuty --hands-free` dentro del entorno virtual.

### Diagnóstico previo a la interrupción por voz

El modo actual cierra el micrófono mientras habla. No implementa todavía
la interrupción al decir «Cuty» durante la respuesta. Para comprobar si el
HAT puede capturar y reproducir de forma simultánea usando un único stream,
vuelve al menú principal y ejecuta desde `raspberry`:

```sh
./.venv/bin/python -m cuty --test-duplex
```

Habla durante tres segundos. La salida transmite únicamente silencio; no
se guardan grabaciones, no se llama a Gemini y no se cambian controles.
El resultado `Duplex OK` y los niveles permiten evaluar el siguiente paso.
Esta prueba por sí sola no implementa reconocimiento del nombre ni
cancelación de eco, y no activa otro modo de conversación.

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
UDP local 5005. El menú inicia su propia voz al entrar en C.U.T.Y; no abras
una segunda instancia. Prueba rápida
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
sudo python3 /home/santi/C.U.T.Y/raspberry/touchscreen/cuty_launcher.py
```

Ctrl+C termina la prueba. Para restaurar el menú instalado:

```sh
sudo systemctl start cuty-launcher.service
```

## Arranque automático

El menú ya está habilitado en la Raspberry actual. Para una instalación en
esta misma ruta, después de probar manualmente:

```sh
bash /home/santi/C.U.T.Y/raspberry/touchscreen/install.sh
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
