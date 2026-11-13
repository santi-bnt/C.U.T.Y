# Music Mode en C.U.T.Y.

## Comportamiento local

Music Mode solo se crea en `--hands-free`, que es el proceso de voz del robot físico. Lee archivos autorizados de `~/Music/CUTY` (o `CUTY_MUSIC_DIR`), en WAV, MP3, FLAC, OGG y M4A, y los decodifica con el PyAV/FFmpeg ya usado por el proyecto. No descarga canciones ni usa una API de búsqueda web para obtener audio.

La salida de voz y la de música comparten la misma salida física del ReSpeaker. La voz pasa por `VolumeSpeaker`; la música usa `LocalMusicProvider` y su propio volumen PCM, de modo que ambos controles siguen separados. En half-duplex, C.U.T.Y. pausa la música y cierra la salida antes de abrir el micrófono, luego vuelve a abrirla para responder y reanuda la pista cuando corresponde.

Durante una pista, la escucha no está abierta: el test de duplex actual emite silencio y solo comprueba que el dispositivo entrega PCM. No prueba cancelación de eco ni reconocimiento fiable mientras suena música. Para pedir algo, da un toque corto a la pantalla; los ojos parpadean, la reproducción se pausa y se abre el micrófono. Di el comando. La pista se reanuda salvo que pidas pausa o detener. Mantén el toque de cinco segundos para salir al menú como antes.

Los comandos deterministas incluyen:

- «Cuty, pon [título] de [artista]» / «Cuty, reproduce [título]».
- «Cuty, pausa la música» / «Cuty, continúa».
- «Cuty, siguiente canción» / «Cuty, canción anterior».
- «Cuty, ¿qué canción está sonando?».
- «Cuty, sube/baja el volumen de la música» / «Cuty, pon el volumen al 40 %».
- «Cuty, deja de reproducir».

La búsqueda usa metadatos título/artista si PyAV los encuentra; si no, usa el nombre del archivo. Al terminar una pista avanza al siguiente archivo en orden alfabético y se detiene al final de la biblioteca. El control de volumen de música se aplica a los siguientes bloques PCM. La música no usa el wrapper de lip-sync de la voz.

## Validación en Raspberry Pi OS

Comprueba la biblioteca y el decodificador antes de usar voz:

```sh
find "${CUTY_MUSIC_DIR:-/home/santi/Music/CUTY}" -type f \
  \( -iname '*.wav' -o -iname '*.mp3' -o -iname '*.flac' -o -iname '*.ogg' -o -iname '*.m4a' \)
```

Pon al menos dos pistas legales en esa carpeta. Luego:

```sh
sudo systemctl restart cuty-launcher.service
sudo journalctl -fu cuty-launcher.service --no-pager \
  | grep --line-buffered -Ei 'MUSIC:|\[VOLUME\]|Microphone:|Speaker:|overflow|underflow|xrun|error'
```

Di «Cuty, pon [título] de [artista]» y confirma `[MUSIC] playing ...`. Mientras suena, toca la pantalla brevemente y di, uno por uno, «pausa la música», «continúa», «siguiente canción», «¿qué canción está sonando?», «baja el volumen de la música» y «deja de reproducir». Para una orden mientras está pausada, toca brevemente otra vez. Comprueba audiblemente la pausa, reanudación, selección y cambio de volumen por la bocina. Espera al final de una pista para confirmar el avance automático. Verifica que los ojos sigan animados y que un toque sostenido de cinco segundos todavía vuelva al menú.

El diagnóstico de duplex silencioso, solo después de salir a la pantalla de menú y nunca mientras esté reproduciendo:

```sh
cd /home/santi/C.U.T.Y/raspberry
.venv/bin/python -m cuty --test-duplex
```

Ese test no justifica activar escucha concurrente; para eso falta una prueba de voz real con música audible y evaluación de eco/cortes.

## Proveedores en línea: evaluación, sin integración

| Opción | Audio en la Raspberry | Cuenta y autenticación | ARM64 / recursos | Restricciones y evaluación |
|---|---|---|---|---|
| Biblioteca local | Sí: PyAV decodifica PCM y `SoundDeviceSpeaker` lo envía al ReSpeaker. Funciona sin red. | Sin suscripción ni tokens; el usuario aporta archivos que tiene derecho a reproducir. | Es la ruta ya instalada; uso de CPU/RAM depende del códec y la pista. No se ha medido en el robot en esta sesión. | Control pleno de pausa, siguiente, búsqueda local y volumen PCM independiente. Menor riesgo y mejor opción actual. |
| Spotify Web Playback SDK | Sí, técnicamente: crea un dispositivo Spotify Connect en un navegador compatible y el navegador emite audio por su salida configurada. El Web API por sí solo solo controla un dispositivo activo; no descarga ni entrega el PCM a `LocalMusicProvider`. | Spotify Premium requerido. OAuth Authorization Code with PKCE; access token de una hora y refresh token con vencimiento de seis meses, por lo que requiere renovación y reautorización periódica. El modo de desarrollo actual también exige Premium al propietario y limita nuevas apps a cinco usuarios. | Spotify documenta navegadores Linux de escritorio, incluido Chrome, pero no una garantía específica para Raspberry Pi 5/ARM64, DRM/codec ni coexistencia con el stream PortAudio `hw:2,0`. Se debe comprobar salida, decodificación protegida, memoria y conflicto de dispositivo. | Es la opción técnica más cercana si se acepta Premium y mantener Chromium con un reproductor visible/integrado. No la integro hasta probar audio real, control del reproductor y términos aplicables al rostro animado. |
| Apple MusicKit on the Web | Sí, a través de MusicKit JS en navegador; no es un endpoint de búsqueda que entregue audio PCM para el reproductor Python. | Cuenta con Apple Music para reproducción completa; developer token firmado y autorización/user token de la persona. Requiere credenciales de desarrollador y flujo de autorización/renovación. | Apple ofrece soporte web, pero no confirma específicamente Raspberry Pi OS/ARM64 ni reproducción DRM en Chromium de Pi. También comparte la posible colisión del audio del navegador con ALSA/PortAudio. | Viable solo como reproductor web visible con autorización; no como sustituto directo del proveedor local. Complejidad mayor que biblioteca local y compatibilidad física pendiente. |
| YouTube / YouTube Music | El IFrame Player API puede reproducir/controlar un video embebido; no está autorizado separar su audio para la bocina como flujo musical. | API key/OAuth según datos y funciones; API de datos no implica permiso de reproducción. YouTube Music normalmente requiere cuenta y plan para funciones premium, pero eso no da un API Pi de audio separado. | Chromium puede alojar el reproductor; debe permanecer como reproductor YouTube conforme a sus requisitos, y no se debe ocultar/minimizar para background playback. | No encaja con C.U.T.Y. mostrando solo los ojos: no descargar, extraer ni reproducir audio separado; las políticas también prohíben background playback del reproductor API. No recomendado para este Music Mode. |

**Recomendación:** conservar la biblioteca local ahora. Si después quieres Internet, hagamos primero una prueba de concepto web separada en Chromium con una cuenta Premium de Spotify. Debe demostrar playback ARM64 hacia la bocina física, pausa mediante el toque, recuperación OAuth y convivencia con la animación antes de elegir integración. No hay resultados de hardware asumidos aquí. La búsqueda de catálogo nunca debe confundirse con permiso o capacidad de reproducir audio.

## Prueba opcional de Spotify Soloist (robot físico)

El repositorio ahora incluye un adaptador opcional: `CUTY_MUSIC_PROVIDER=spotify_soloist`. Soloist reproduce el audio como su propio dispositivo Spotify Connect; C.U.T.Y. solo busca títulos con Spotify Web API y envía la URI/controles al daemon local. La búsqueda requiere un Client ID/Secret de una aplicación de Spotify Developer. Soloist requiere aparte su propia API key; no compartas ninguna de esas credenciales.

En este modo puedes decir "Cuty, modo música" y luego usar Spotify en el celular: abre el selector de dispositivos, elige "CUTY Spotify" y controla las canciones desde la app. La Raspberry debe estar encendida y Soloist activo. El comando de voz confirma cómo entrar al flujo; no inicia una canción por sí mismo.

Spotify publica un binario Linux AArch64, aunque su documentación dice que el build AArch64 se prueba principalmente en Raspberry Pi 3 con Raspberry Pi OS basado en Trixie. Soloist requiere PipeWire o PulseAudio para su salida Linux; la app actual de C.U.T.Y. usa PortAudio directamente para el micrófono y bocina Seeed. Por eso la reproducción correcta, la ruta al ReSpeaker y que ambos procesos puedan abrir el audio durante half-duplex necesitan comprobación en esta Raspberry Pi 5 antes de dejar el proveedor activado. No cambies el proveedor hasta que Soloist se oiga por la bocina física.

En la Raspberry, descarga el archivo oficial para `aarch64` desde [Downloads and updates de Spotify Soloist](https://developer.spotify.com/documentation/soloist/reference/downloads-and-updates), extráelo e instálalo siguiendo su [guía oficial](https://developer.spotify.com/documentation/soloist/tutorials/getting-started). Crea la API key de Soloist y una app Web API en Spotify for Developers. No pegues aquí ni subas al repositorio los secretos. Ejecuta el daemon como el usuario `santi` con una carpeta de datos estable:

```sh
install -d -m 700 /home/santi/.local/share/soloist /home/santi/.cache/soloist
read -rsp 'Spotify Soloist API key: ' SOLOIST_API_KEY; echo
export SOLOIST_API_KEY
soloist --device-name 'CUTY Spotify' \
  --api-key "$SOLOIST_API_KEY" \
  --data-dir /home/santi/.local/share/soloist \
  --cache-dir /home/santi/.cache/soloist \
  --ws 127.0.0.1:9090
```

Con el daemon activo, selecciona `CUTY Spotify` en el selector de dispositivos de la app oficial de Spotify del teléfono conectado a la misma red y reproduce algo para completar el emparejamiento. Después revisa `soloist ctl status` y `soloist ctl now`. Soloist conserva la sesión en su carpeta de datos; cada build oficial caduca a los 90 días y hay que actualizarlo desde Spotify.

El ejemplo de servicio es una unidad de usuario para que Soloist vea la sesión PipeWire/PulseAudio. Crea `/home/santi/.config/cuty/spotify.env` con `SOLOIST_API_KEY=...` y permisos `600`, copia [`cuty-spotify-soloist.service.example`](../raspberry/systemd/cuty-spotify-soloist.service.example) a `/home/santi/.config/systemd/user/cuty-spotify-soloist.service`, y luego habilita el gestor de servicios de usuario en el arranque:

```sh
sudo loginctl enable-linger santi
sudo -u santi XDG_RUNTIME_DIR=/run/user/1000 systemctl --user daemon-reload
sudo -u santi XDG_RUNTIME_DIR=/run/user/1000 systemctl --user enable --now cuty-spotify-soloist.service
sudo -u santi XDG_RUNTIME_DIR=/run/user/1000 systemctl --user status cuty-spotify-soloist.service --no-pager -l
```

Guarda en `/home/santi/C.U.T.Y/raspberry/.env` los valores locales (archivo modo `600`):

```dotenv
CUTY_MUSIC_PROVIDER=spotify_soloist
CUTY_SPOTIFY_SOLOIST_WS=ws://127.0.0.1:9090
CUTY_SPOTIFY_CLIENT_ID=...
CUTY_SPOTIFY_CLIENT_SECRET=...
CUTY_SPOTIFY_MARKET=MX
```

Instala el editable package actualizado y reinicia el launcher:

```sh
cd /home/santi/C.U.T.Y/raspberry
.venv/bin/pip install -e .
sudo systemctl restart cuty-launcher.service
sudo journalctl -fu cuty-launcher.service --no-pager \
  | grep --line-buffered -Ei 'Spotify Soloist|MUSIC:|reproductor|VOLUME|error'
```

Prueba `Cuty, pon 505 de Arctic Monkeys`, pregunta `qué canción está sonando`, y prueba pausa, continúa, siguiente, bajar volumen y detener. Durante música, el toque corto mantiene el diseño half-duplex actual. Revisa también que Gemini vuelva a abrir el micro y hable por el mismo ReSpeaker después de pausar Soloist.

Si la bocina física queda ocupada por Soloist o la salida de Soloist aparece en otro dispositivo, vuelve a `CUTY_MUSIC_PROVIDER=local` y reinicia el servicio. No actives escucha simultánea ni cambies drivers/ALSA para resolverlo sin medir primero la Pi. La app maneja Soloist offline como “sin música” para mantener Gemini activo, y devuelve una respuesta hablada de error si falla una orden remota.

Notas: Soloist no expone un comando `stop` dedicado; C.U.T.Y. lo implementa como pausa + desactivar el dispositivo Connect. La WebSocket API se liga solo a loopback porque no tiene autenticación ni TLS. Los resultados de búsqueda son catálogo/URIs, no archivos descargados; todo audio se reproduce dentro de Soloist.

Fuentes oficiales consultadas el 12 de noviembre de 2026:

- [Spotify Web Playback SDK](https://developer.spotify.com/documentation/web-playback-sdk) y [requisito Premium](https://developer.spotify.com/documentation/web-playback-sdk/howtos/web-app-player).
- [Spotify Web API: iniciar reproducción en dispositivo activo](https://developer.spotify.com/documentation/web-api/reference/start-a-users-playback), [PKCE](https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow), [renovación de token](https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens) y [cambios de modo de desarrollo 2026](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide).
- [Apple MusicKit](https://developer.apple.com/musickit/) y [autorización de usuario](https://developer.apple.com/documentation/applemusicapi/user-authentication-for-musickit).
- [YouTube IFrame Player API](https://developers.google.com/youtube/iframe_api_reference) y [políticas de desarrollador](https://developers.google.com/youtube/terms/developer-policies-guide).
