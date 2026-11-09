import { bi } from "./project";
import {
  bcm,
  wiringNodes as cadNodes,
  type ConnectionRow,
  type WireFilter,
  type WiringStatus,
} from "./engineering";
export const wiringEvidence = `${import.meta.env.BASE_URL}engineering/wiring-evidence.html`;
export const connectionRows: ConnectionRow[] = [];
function add(
  id: string,
  from: string,
  to: string,
  net: string,
  pin: string,
  destination: string,
  kind: WireFilter,
  status: WiringStatus,
  voltage = "3.3 V logic / lógica",
  physical?: number,
) {
  connectionRows.push({
    id,
    from,
    to,
    net,
    pin,
    destination,
    voltage,
    gpio:
      physical && bcm[String(physical)] !== undefined
        ? `BCM ${bcm[String(physical)]}`
        : "—",
    tags: [
      kind,
      ...(!["power", "ground"].includes(kind) ? ["signals" as const] : []),
      ...(physical && !["power", "ground"].includes(kind)
        ? ["GPIO" as const]
        : []),
    ],
    status,
    source: wiringEvidence,
  });
}
for (const [name, pin, kind] of [
  ["3.3 V", 1, "power"],
  ["5 V", 4, "power"],
  ["GND", 6, "ground"],
  ["Touch IRQ", 11, "GPIO"],
  ["LCD DC / RS", 18, "GPIO"],
  ["SPI MOSI", 19, "SPI"],
  ["SPI MISO", 21, "SPI"],
  ["LCD RESET", 22, "GPIO"],
  ["SPI SCLK", 23, "SPI"],
  ["LCD CS", 24, "SPI"],
  ["Touch CS", 26, "SPI"],
] as const)
  add(
    "display-" + pin,
    "pi",
    "display",
    name,
    `Pi ${pin}`,
    `Waveshare / ${name}`,
    kind,
    "confirmed",
    kind === "power"
      ? name
      : kind === "ground"
        ? "0 V"
        : "3.3 V logic / lógica",
    pin,
  );
for (const [name, pin, kind, label] of [
  ["3.3 V", 1, "power", "1"],
  ["I2C SDA", 3, "I2C", "3"],
  ["5 V", 4, "power", "4"],
  ["I2C SCL", 5, "I2C", "5"],
  ["GND", 6, "ground", "6"],
  ["MCLK", 7, "I2S", "7"],
  ["I2S BCLK", 12, "I2S", "12"],
  ["I2S LRCLK", 35, "I2S", "35"],
  ["AUD_RST", 37, "GPIO", "37"],
  ["I2S DIN", 38, "I2S", "38"],
  ["I2S DOUT", 40, "I2S", "40"],
] as const)
  add(
    "audio-" + name,
    "pi",
    "audio",
    name,
    `Pi ${label}`,
    `ReSpeaker / ${name}`,
    kind,
    "confirmed",
    kind === "power"
      ? name
      : kind === "ground"
        ? "0 V"
        : "3.3 V logic / lógica",
    pin,
  );
add(
  "camera",
  "pi",
  "camera",
  "CSI",
  "Pi CAM/DISP 22-pin",
  "OV5647 15-pin / adapter",
  "signals",
  "confirmed",
  "Power + image via CSI / alimentación e imagen",
);
add(
  "uart-tx",
  "pi",
  "stm",
  "UART TXD",
  "Pi 8 / TXD",
  "STM32 RX — TBD / por confirmar",
  "UART",
  "proposed",
  "3.3 V",
  8,
);
add(
  "uart-rx",
  "stm",
  "pi",
  "UART RXD",
  "STM32 TX — TBD / por confirmar",
  "Pi 10 / RXD",
  "UART",
  "proposed",
  "3.3 V",
  10,
);
for (let i = 1; i <= 5; i++)
  add(
    "pwm" + i,
    "stm",
    "servos",
    `PWM ${i} — TBD / por asignar`,
    "STM32 PWM — TBD",
    `Servo ${i} orange/yellow / naranja/amarillo`,
    "servo",
    "proposed",
    "3.3 V signal; 6 V supply / señal; alimentación",
  );
add(
  "battery-in",
  "battery",
  "buck",
  "Battery + / batería +",
  "LiPo +",
  "Buck IN+",
  "power",
  "proposed",
  "11.1 V nominal / 12.6 V max",
);
add(
  "battery-ground",
  "battery",
  "buck",
  "Battery − / batería −",
  "LiPo −",
  "Buck IN−",
  "ground",
  "proposed",
  "GND",
);
add(
  "servo-supply",
  "buck",
  "servos",
  "Regulated + / regulada +",
  "Buck OUT+",
  "Servo red / rojo",
  "power",
  "proposed",
  "Measure ~6.0 V / medir",
);
add(
  "servo-ground",
  "buck",
  "servos",
  "Servo GND",
  "Buck OUT−",
  "Servo brown/black / marrón/negro",
  "ground",
  "proposed",
  "Common ground / tierra común",
);
for (const from of ["pi", "stm", "servos"])
  add(
    "common-" + from,
    from,
    "ground",
    "Common GND / tierra común",
    from + " GND",
    "Common ground / tierra común",
    "ground",
    "proposed",
    "0 V reference / referencia",
  );
add(
  "pi-power",
  "regulator",
  "pi",
  "Independent Pi supply / fuente independiente",
  "Compatible USB-C supply",
  "Pi USB-C",
  "power",
  "unverified",
  "5.1 V; current to validate / corriente por validar",
);
add(
  "pi-battery",
  "battery",
  "regulator",
  "Independent regulator TBD",
  "LiPo battery branch / rama batería",
  "Pi regulator — not finalized / pendiente",
  "power",
  "unverified",
  "Do not connect battery directly / no conectar directa",
);
const detail: Record<string, ReturnType<typeof bi>> = {
  pi: bi(
    "Display and ReSpeaker connections confirmed working together by the builder. Power through a compatible USB-C supply; the battery regulator is not finalized.",
    "Pantalla y ReSpeaker confirmados funcionando juntos por el constructor. Alimentación USB-C compatible; regulador desde batería pendiente.",
  ),
  display: bi(
    "Waveshare 3.5-inch (G): confirmed pin table, including modified DC on BCM24 and RESET on BCM25. Backlight and final overlay remain to check; preserve working GPIO configuration.",
    "Waveshare 3.5 pulgadas (G): tabla confirmada, con DC modificado en BCM24 y RESET en BCM25. Retroiluminación y overlay final pendientes; conservar configuración GPIO actual.",
  ),
  audio: bi(
    "Confirmed I2C/I2S and power connections. Do not use the RGB LEDs (BCM10/11) or HAT button (BCM17); those pins belong to the display. BCM18 remains I2S BCLK.",
    "I2C/I2S y alimentación confirmados. No usar LED RGB (BCM10/11) ni botón HAT (BCM17): son de la pantalla. BCM18 se reserva para I2S BCLK.",
  ),
  stm: bi(
    "Proposed 3.3 V UART, crossed TX/RX with shared ground. STM32 UART pins and all five PWM pins still await final assignment.",
    "UART de 3.3 V propuesto, TX/RX cruzados y tierra común. Pines UART STM32 y los cinco PWM aún por asignar.",
  ),
  servos: bi(
    "Five MG996R: red to regulated 6 V, brown/black to servo ground, orange/yellow to assigned STM32 PWM. Final PWM assignments are pending.",
    "Cinco MG996R: rojo a 6 V regulados, marrón/negro a GND y naranja/amarillo a PWM STM32. Asignaciones PWM pendientes.",
  ),
  camera: bi(
    "The builder confirmed camera operation and facial tracking. OV5647 15-pin CSI connects to Pi 5 CAM/DISP 22-pin through a compatible adapter. Power and image travel through CSI; individual contacts are not enumerated.",
    "El constructor confirmó cámara y seguimiento facial. OV5647 CSI de 15 pines a CAM/DISP Pi 5 de 22 pines con adaptador compatible. Alimentación e imagen por CSI; no se enumeran contactos internos.",
  ),
  battery: bi(
    "LiPo 3S: 11.1 V nominal, 12.6 V full, 2200 mAh, 24.42 Wh and labeled 50C. Protection, fuse and final distribution remain to verify.",
    "LiPo 3S: 11.1 V nominal, 12.6 V cargada, 2200 mAh, 24.42 Wh e indicación 50C. Protección, fusible y distribución final pendientes.",
  ),
  buck: bi(
    "Measure approximately 6.0 V before connecting servos. Exact buck model and admissible simultaneous current remain unverified.",
    "Medir aproximadamente 6.0 V antes de conectar servos. Modelo exacto y corriente simultánea admisible pendientes.",
  ),
  regulator: bi(
    "An independent battery-to-Pi regulator still needs definition and validation. The 6 V servo rail must not power the Pi.",
    "El regulador independiente batería–Pi requiere definición y validación. El riel servo de 6 V no alimenta la Pi.",
  ),
  ground: bi(
    "Share electrical ground references among Pi, STM32 and servo supply. Do not connect positive outputs of different-voltage regulators. Final PCB grounding remains separate from this confirmed hookup table.",
    "Compartir referencias GND entre Pi, STM32 y alimentación de servos. No unir salidas positivas de reguladores de distintos voltajes. Tierra final de PCB se documenta aparte.",
  ),
};
export const wiringNodes = cadNodes.map((n) => ({
  ...n,
  label: n.id === "ground" ? "Common GND / Tierra común" : n.label,
  detail: detail[n.id] ?? n.detail,
  voltage:
    n.id === "stm"
      ? bi("3.3 V UART / PWM pins pending", "UART 3.3 V / PWM pendientes")
      : n.id === "battery"
        ? bi(
            "11.1 V / 12.6 V · 2200 mAh · 24.42 Wh",
            "11.1 V / 12.6 V · 2200 mAh · 24.42 Wh",
          )
        : n.id === "regulator"
          ? bi(
              "5.1 V USB-C; battery regulator pending",
              "USB-C 5.1 V; regulador batería pendiente",
            )
          : ["audio", "display"].includes(n.id)
            ? bi(
                "3.3 V / 5 V · confirmed power hookup",
                "3.3 V / 5 V · alimentación confirmada",
              )
            : n.voltage,
}));
export const wiringEdges = [
  {
    from: "pi",
    to: "audio",
    kind: "I2C",
    label: "SDA 3 / SCL 5",
    status: "confirmed",
  },
  {
    from: "pi",
    to: "audio",
    kind: "I2S",
    label: "MCLK 7 / I2S 12, 35, 38, 40",
    status: "confirmed",
  },
  {
    from: "pi",
    to: "audio",
    kind: "GPIO",
    label: "AUD_RST 37 / BCM26",
    status: "confirmed",
  },
  {
    from: "pi",
    to: "display",
    kind: "SPI",
    label: "SPI + DC24 / RESET25 BCM",
    status: "confirmed",
  },
  {
    from: "pi",
    to: "display",
    kind: "GPIO",
    label: "Touch IRQ BCM17",
    status: "confirmed",
  },
  {
    from: "pi",
    to: "audio",
    kind: "power",
    label: "3.3 V / 5 V",
    status: "confirmed",
  },
  {
    from: "pi",
    to: "display",
    kind: "power",
    label: "3.3 V / 5 V",
    status: "confirmed",
  },
  {
    from: "pi",
    to: "camera",
    kind: "signals",
    label: "CSI 22 ↔ 15",
    status: "confirmed",
  },
  {
    from: "pi",
    to: "stm",
    kind: "UART",
    label: "3.3 V / STM pins TBD",
    status: "proposed",
  },
  {
    from: "stm",
    to: "servos",
    kind: "servo",
    label: "PWM pins TBD",
    status: "proposed",
  },
  {
    from: "battery",
    to: "buck",
    kind: "power",
    label: "11.1 V nominal",
    status: "proposed",
  },
  {
    from: "buck",
    to: "servos",
    kind: "power",
    label: "~6.0 V regulated",
    status: "proposed",
  },
  {
    from: "battery",
    to: "regulator",
    kind: "power",
    label: "Independent supply TBD",
    status: "unverified",
  },
  {
    from: "regulator",
    to: "pi",
    kind: "power",
    label: "5.1 V USB-C",
    status: "unverified",
  },
  ...["pi", "stm", "servos"].map((from) => ({
    from,
    to: "ground",
    kind: "ground",
    label: "Common GND",
    status: "proposed",
  })),
] as {
  from: string;
  to: string;
  kind: WireFilter;
  label: string;
  status: WiringStatus;
}[];
