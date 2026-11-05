export type Locale = "en" | "es";
export type Copy = { en: string; es: string };
export const bi = (en: string, es: string): Copy => ({ en, es });
export const repo = "https://github.com/santi-bnt/C.U.T.Y";
export const source = (path: string) =>
  `${repo}/${path.split("/").at(-1)?.includes(".") ? "blob" : "tree"}/main/${path}`;
export type Stage = "implemented" | "validation" | "planned";
export const stageNames: Record<Stage, Copy> = {
  implemented: bi("Implemented", "Implementado"),
  validation: bi("In validation", "En validación"),
  planned: bi("Planned", "Planeado"),
};
export const components = [
  {
    id: "pi",
    name: "Raspberry Pi 5",
    tag: bi("COMPUTE", "CÓMPUTO"),
    stage: "implemented",
    detail: bi(
      "The high-level brain: AI sessions, audio, camera processing, face rendering and behavior. Basic voice conversation has been physically tested; sustained runtime remains in validation.",
      "El cerebro de alto nivel: sesiones de IA, audio, cámara, cara y comportamiento. La conversación básica se probó físicamente; la estabilidad sostenida sigue en validación.",
    ),
    interface: "Linux · Python · GPIO",
    path: "raspberry/src/cuty",
    spec: "Raspberry Pi 5",
  },
  {
    id: "display",
    name: "Display-G 3.5″",
    tag: bi("INTERFACE", "INTERFAZ"),
    stage: "validation",
    detail: bi(
      "480 × 320 SPI touchscreen with ADS7846 touch. Renders the face and launches conversations from the menu. Intermittent white-screen behavior is still under investigation.",
      "Pantalla táctil SPI de 480 × 320 con ADS7846. Muestra la cara e inicia conversaciones desde el menú. La pantalla blanca intermitente sigue bajo investigación.",
    ),
    interface: "SPI0 · /dev/fb1 · ADS7846",
    path: "raspberry/touchscreen",
    spec: "480 × 320 · SPI",
  },
  {
    id: "audio",
    name: "ReSpeaker 2-Mics",
    tag: bi("AUDIO", "AUDIO"),
    stage: "validation",
    detail: bi(
      "Pi HAT V2.0 with TLV320AIC3104. Microphone capture and speaker playback have been tested together with Gemini replies. Listening sensitivity and output levels need continued tuning.",
      "Pi HAT V2.0 con TLV320AIC3104. La captura y reproducción se probaron con respuestas de Gemini. La sensibilidad y los niveles de salida requieren más ajuste.",
    ),
    interface: "I²C 0x18 · I²S · ALSA",
    path: "docs/audio.md",
    spec: "2 microphones · I²S",
  },
  {
    id: "camera",
    name: "Arducam OV5647",
    tag: bi("VISION", "VISIÓN"),
    stage: "validation",
    detail: bi(
      "OV5647 camera startup has been observed on the Pi. Picamera2/OpenCV adapters feed YuNet detection and visual gaze tracking. End-to-end physical tracking validation is pending.",
      "Se observó el arranque de la cámara OV5647 en la Pi. Picamera2/OpenCV alimentan YuNet y el seguimiento visual. Falta validar físicamente todo el seguimiento.",
    ),
    interface: "CSI · Picamera2 · OpenCV",
    path: "raspberry/src/cuty/vision",
    spec: "OV5647 · CSI",
  },
  {
    id: "stm",
    name: "STM32F401 Black Pill",
    tag: bi("MOTION", "MOVIMIENTO"),
    stage: "planned",
    detail: bi(
      "Carrier target: STM32F401CCU6 Black Pill. The planned real-time controller will receive high-level UART goals and own PWM, motion and safety. Current firmware files are placeholders.",
      "La carrier está diseñada para STM32F401CCU6 Black Pill. El controlador recibirá objetivos UART y gestionará PWM, movimiento y seguridad. El firmware actual contiene plantillas.",
    ),
    interface: "UART / PWM — planned",
    path: "stm32",
    spec: "STM32F401CCU6",
  },
  {
    id: "servo",
    name: "MG996R servos",
    tag: bi("ACTUATION", "ACTUACIÓN"),
    stage: "planned",
    detail: bi(
      "Five servo connectors are included in the carrier design. Physical motion, calibrated limits and motor safety are future work. This viewer does not control servos.",
      "El diseño de la carrier incluye cinco conectores de servo. El movimiento, los límites y la seguridad están pendientes. Este visor no controla servos.",
    ),
    interface: "PWM — planned",
    path: "hardware/electronics/kicad/cuty_carrier",
    spec: "5 carrier connectors",
  },
  {
    id: "pcb",
    name: "Carrier PCB V1.1",
    tag: bi("ELECTRONICS", "ELECTRÓNICA"),
    stage: "validation",
    detail: bi(
      "100 × 92 mm, two-layer KiCad carrier. Native schematic, layout, BOM and fabrication exports exist. Manufacturing, assembly and electrical validation are pending.",
      "Carrier KiCad de dos capas, 100 × 92 mm. Existen esquema, PCB, BOM y archivos de fabricación. La fabricación, el montaje y la validación eléctrica están pendientes.",
    ),
    interface: "KiCad · 2 layers · THT",
    path: "hardware/electronics/kicad/cuty_carrier",
    spec: "100 × 92 mm · 2 layers",
  },
] as const;
export type ComponentId = (typeof components)[number]["id"];
export const capabilities = [
  {
    id: "voice",
    title: bi(
      "A conversation, not a command line.",
      "Una conversación, no una terminal.",
    ),
    label: bi("Conversational AI", "IA conversacional"),
    detail: bi(
      "Gemini Live and OpenAI Realtime adapters exchange audio, transcripts and tool events. Gemini hands-free conversation starts from the touchscreen.",
      "Los adaptadores Gemini Live y OpenAI Realtime intercambian audio, transcripciones y herramientas. Gemini manos libres inicia desde la pantalla.",
    ),
    evidence: bi(
      "Gemini voice turns observed on Raspberry Pi. OpenAI adapter implemented; Pi validation not documented.",
      "Se observaron turnos de Gemini en Raspberry Pi. Adaptador OpenAI implementado; sin validación documentada en la Pi.",
    ),
    path: "raspberry/src/cuty/llm",
    icon: "voice",
  },
  {
    id: "vision",
    title: bi("A little more eye contact.", "Un poco más de contacto visual."),
    label: bi(
      "Computer vision + facial tracking",
      "Visión + seguimiento facial",
    ),
    detail: bi(
      "OpenCV and YuNet, with a Haar fallback, detect faces. Target selection and smoothing turn camera coordinates into expressive eye movements.",
      "OpenCV y YuNet, con alternativa Haar, detectan caras. La selección y el suavizado convierten coordenadas de cámara en movimientos de ojos.",
    ),
    evidence: bi(
      "Software implemented; camera startup observed. Complete physical gaze validation pending. No identity recognition.",
      "Software implementado; arranque de cámara observado. Validación física del seguimiento pendiente. Sin reconocimiento de identidad.",
    ),
    path: "raspberry/src/cuty/vision",
    icon: "vision",
  },
  {
    id: "face",
    title: bi("Personality, in pixels.", "Personalidad en píxeles."),
    label: bi(
      "Expressions + lip synchronization",
      "Expresiones + sincronización labial",
    ),
    detail: bi(
      "Animated eyes, blinks and a mouth respond to conversation state. Lip sync follows the playback audio envelope through a local UDP link.",
      "Ojos, parpadeos y boca responden al estado de conversación. La boca sigue la envolvente de audio reproducido mediante un enlace UDP local.",
    ),
    evidence: bi(
      "Rendering and audio-linked animation implemented. Sustained display reliability and lip-sync tuning remain in validation.",
      "Renderizado y animación con audio implementados. Estabilidad de pantalla y ajuste de sincronización en validación.",
    ),
    path: "raspberry/src/cuty/face",
    icon: "face",
  },
  {
    id: "tools",
    title: bi("Curiosity, with a toolkit.", "Curiosidad con herramientas."),
    label: bi("Local VAD + web search", "VAD local + búsqueda web"),
    detail: bi(
      "Local energy-based voice activity detection segments speech. A web-search tool can add external context to the robot’s conversation.",
      "La detección local por energía segmenta la voz. Una herramienta de búsqueda web puede añadir contexto externo a la conversación del robot.",
    ),
    evidence: bi(
      "Both paths exist in the Python application. This website runs neither AI inference nor live web searches.",
      "Ambas funciones existen en Python. Esta web no ejecuta inferencia de IA ni búsquedas en vivo.",
    ),
    path: "raspberry/src/cuty/audio/activity.py",
    icon: "tools",
  },
];
export const milestones: { stage: Stage; title: Copy; items: Copy[] }[] = [
  {
    stage: "implemented",
    title: bi("Built in code.", "Desarrollado en código."),
    items: [
      bi(
        "Gemini Live + OpenAI Realtime adapters",
        "Adaptadores Gemini Live + OpenAI Realtime",
      ),
      bi(
        "Voice conversation, local VAD and web search",
        "Conversación, VAD local y búsqueda web",
      ),
      bi(
        "YuNet detection + visual gaze tracking",
        "Detección YuNet + seguimiento visual",
      ),
      bi(
        "Animated face, expressions and lip sync",
        "Cara animada, expresiones y sincronización",
      ),
      bi(
        "Touchscreen menu and carrier PCB design",
        "Menú táctil y diseño de PCB carrier",
      ),
    ],
  },
  {
    stage: "validation",
    title: bi("On the workbench.", "En el banco de pruebas."),
    items: [
      bi(
        "ReSpeaker capture / playback: basic tests passed",
        "Captura / reproducción ReSpeaker: pruebas básicas realizadas",
      ),
      bi(
        "Gemini voice replies observed on Pi 5",
        "Respuestas de voz Gemini observadas en Pi 5",
      ),
      bi(
        "Listening sensitivity and stable long sessions",
        "Sensibilidad y sesiones largas estables",
      ),
      bi(
        "Display reliability and camera-to-gaze pipeline",
        "Estabilidad de pantalla y flujo cámara-mirada",
      ),
      bi(
        "PCB fabrication and electrical checks pending",
        "Fabricación y pruebas eléctricas de PCB pendientes",
      ),
    ],
  },
  {
    stage: "planned",
    title: bi("The next frontier.", "Lo que sigue."),
    items: [
      bi(
        "STM32 firmware + validated UART protocol",
        "Firmware STM32 + protocolo UART validado",
      ),
      bi(
        "PWM, servo limits and motion safety",
        "PWM, límites de servo y seguridad",
      ),
      bi(
        "Physical head tracking, IMU and body PID",
        "Seguimiento físico, IMU y PID de cuerpo",
      ),
      bi(
        "Live telemetry and connected dashboard",
        "Telemetría en vivo y dashboard conectado",
      ),
      bi(
        "Local AI fallback and identity recognition",
        "IA local alternativa y reconocimiento de identidad",
      ),
    ],
  },
];
