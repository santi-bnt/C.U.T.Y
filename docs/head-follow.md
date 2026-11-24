# Seguimiento facial PAN

## Flujo y modos

El `FaceTracker` existente abre una sola cámara, detecta con YuNet o Haar y produce un `FaceTarget` normalizado. El mismo objetivo alimenta los ojos de pantalla y, si se habilita, el PID PAN.

- `CUTY_FOLLOW_DRY_RUN=1`: conserva una simulación en memoria; no abre UART ni activa servos.
- Seguimiento físico: está implementado con `IpcHeadAdapter`. La cámara envía velocidades recientes por socket Unix local; el proceso de conversación es el único dueño del UART y el STM32 genera PWM y limita la trayectoria.
- El seguimiento físico está deshabilitado por defecto. Requiere `CUTY_ROBOT_MODE=robot`, un perfil completo y confirmado, enlace UART válido en DISARMED, `CUTY_FOLLOW_PHYSICAL_ENABLE=1` en el proceso de voz y en el launcher de pantalla, y una pulsación manual de 0.7 a menos de 5 segundos para armar.
- Al perder la detección por 0.5 s, ante una detección inválida, una desconexión o un error de tiempo, el adaptador se detiene y desarma. Para reanudar hace falta otra pulsación explícita. No devuelve la cabeza a un extremo ni reanuda automáticamente.
- Ojos y cabeza usan el mismo detector, pero los ojos siguen funcionando independientemente del actuador.

El eje vertical solo se conserva como diagnóstico; no hay un eje TILT conectado. El controlador Raspberry mide error de imagen normalizado, no grados. El estado disponible es una consigna/velocidad comandada, no una medición de posición.

## Habilitación física

No actives seguimiento hasta que cada articulación tenga calibración física revisada y el firmware corresponda al mismo perfil. Añade al entorno privado cargado por los servicios (no al repositorio ni a la web):

```dotenv
CUTY_ROBOT_MODE=robot
CUTY_SERVO_CALIBRATION_PROFILE=/ruta/al/perfil-confirmado.json
CUTY_STM32_PORT=/dev/ttyAMA0
CUTY_FOLLOW_PHYSICAL_ENABLE=1
CUTY_FOLLOW_DRY_RUN=0
```

La variable `CUTY_FOLLOW_PHYSICAL_ENABLE=1` debe estar disponible también para `cuty-launcher.service`, que crea el adaptador en el proceso de cámara. El proceso de voz debe registrar UART válido y estado DISARMED; el launcher y la conversación deben ejecutarse con el mismo usuario IPC configurado. Reinicia ambos procesos después de cambiar el entorno:

```sh
sudo systemctl edit cuty-launcher.service
```

Añade al override:

```ini
[Service]
Environment=CUTY_FOLLOW_PHYSICAL_ENABLE=1
```

Guarda y aplica el cambio:

```sh
sudo systemctl daemon-reload
sudo systemctl restart cuty-launcher.service
```

Configura `CUTY_ROBOT_MODE`, el perfil, el puerto y `CUTY_FOLLOW_DRY_RUN=0` en el `raspberry/.env` privado; `app.py` lo carga para el proceso de voz. El launcher es root y no carga ese `.env`, por eso el opt-in físico también debe ir en el override del servicio. Al reiniciarlo se recrean el launcher y su proceso de voz. Comprueba el estado sin exponer `.env` ni claves:

```sh
sudo journalctl -u cuty-launcher.service -n 60 --no-pager
```

En la cara, mantén pulsado entre 0.7 y 5 segundos para armar o detener. La orden de armado reclama el control exclusivo, ejecuta ARM/START explícitos y solo entonces admite consignas. La pérdida de cara desarma; otra pulsación es necesaria.

## Límites implementados

| Parámetro | Predeterminado | Uso |
| --- | ---: | --- |
| `CUTY_FOLLOW_KP` | `1.2` | Ganancia proporcional sobre error normalizado |
| `CUTY_FOLLOW_KI` | `0` | Ganancia integral; comienza desactivada |
| `CUTY_FOLLOW_KD` | `0.08` | Ganancia derivativa filtrada |
| `CUTY_FOLLOW_DETECTION_ALPHA` | `0.35` | Suavizado exponencial de detección, `(0, 1]` |
| `CUTY_FOLLOW_DERIVATIVE_ALPHA` | `0.25` | Suavizado de derivada, `(0, 1]` |
| `CUTY_FOLLOW_DEADBAND` | `0.035` | Zona muerta de error normalizado |
| `CUTY_FOLLOW_LOST_TIMEOUT` | `0.5 s` | Antigüedad máxima del objetivo para mantener seguimiento |
| `CUTY_FOLLOW_MAX_DT` | `0.25 s` | Tope de intervalo usado en la aceleración calculada en Raspberry |
| Socket físico | `±0.15` posición normalizada | El servidor IPC limita el recorrido acumulado del objetivo facial |
| IPC | `0.35 s` | Rechaza consignas vencidas |

Además, el STM32 aplica los límites de pulso, velocidad y aceleración del perfil activo. El controlador de Raspberry limita velocidad/aceleración antes de enviar. Estos valores no son ángulos ni límites mecánicos medidos. No se afinen ganancias hasta completar la prueba supervisada de [validación física](robot-validation.md).

## Pruebas de software

Desde `raspberry/`:

```sh
python -m pytest tests/test_head_follow.py tests/test_face_tracker.py tests/test_motion_ipc.py
```

Las pruebas usan detecciones y adaptadores falsos; no validan la cámara real ni el movimiento físico.

## Referencias

- `raspberry/src/cuty/vision/face_tracker.py`: cámara única, detección y objetivo.
- `raspberry/src/cuty/vision/head_follow.py`: PID y política de pérdida de rostro.
- `raspberry/src/cuty/hardware/motion_ipc.py`: socket local y adaptador de cabeza.
- `raspberry/src/cuty/hardware/robot_motion.py`: propietario UART y trayectoria STM32.
- `raspberry/touchscreen/cuty_launcher.py`: habilitación por entorno y pulsación manual.
