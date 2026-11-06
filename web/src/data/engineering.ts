import carrier from "./carrier.generated.json";
import { bi, type Copy } from "./project";
export { carrier };
export type BoardPart = (typeof carrier.components)[number];
export const engineeringAsset = (name: string) =>
  `${import.meta.env.BASE_URL}engineering/${name}`;
export const netlistPath = `${carrier.source}/scripts/netlist.py`;
export const pcbPath = `${carrier.source}/cuty_carrier.kicad_pcb`;
export const wiringStates = {
  confirmed: bi("Builder-confirmed", "Confirmado por el usuario"),
  proposed: bi("Proposed carrier wiring", "Cableado propuesto"),
  unverified: bi("Unverified", "Sin verificar"),
};
export type WiringStatus = keyof typeof wiringStates;
export const filters = [
  "all",
  "power",
  "ground",
  "signals",
  "GPIO",
  "SPI",
  "I2C",
  "I2S",
  "UART",
  "servo",
] as const;
export type WireFilter = (typeof filters)[number];
export const filterNames: Record<WireFilter, Copy> = {
  all: bi("All", "Todo"),
  power: bi("Power", "Potencia"),
  ground: bi("Ground", "Tierra"),
  signals: bi("Signals", "Señales"),
  GPIO: bi("GPIO", "GPIO"),
  SPI: bi("SPI", "SPI"),
  I2C: bi("I²C", "I²C"),
  I2S: bi("I²S", "I²S"),
  UART: bi("UART", "UART"),
  servo: bi("Servo control", "Control de servos"),
};
export const bcm: Record<string, number> = {
  "3": 2,
  "5": 3,
  "7": 4,
  "8": 14,
  "10": 15,
  "11": 17,
  "12": 18,
  "18": 24,
  "19": 10,
  "21": 9,
  "22": 25,
  "23": 11,
  "24": 8,
  "26": 7,
  "35": 19,
  "37": 26,
  "38": 20,
  "40": 21,
};
export function netKind(net: string): WireFilter {
  if (net === "GND" || net === "PGND") return "ground";
  if (/^\+|^VBAT_(RAW|SW|SERVO|PI)|^5V_JP/.test(net)) return "power";
  if (["AUD_RST", "LCD_DC", "LCD_RST", "TP_IRQ"].includes(net)) return "GPIO";
  if (net.startsWith("I2C")) return "I2C";
  if (net.startsWith("I2S") || net.startsWith("AUD")) return "I2S";
  if (net.startsWith("SPI") || net.startsWith("LCD") || net.startsWith("TP_"))
    return "SPI";
  if (net === "PI_TXD" || net === "PI_RXD") return "UART";
  if (net.startsWith("PWM") || net.startsWith("SERVO")) return "servo";
  return "signals";
}
export interface ConnectionRow {
  id: string;
  from: string;
  to: string;
  net: string;
  pin: string;
  destination: string;
  gpio: string;
  voltage: string;
  tags: WireFilter[];
  status: WiringStatus;
  source: string;
}
const piHeader: Record<string, string> = carrier.piHeader;
const headerRows = (ref: string, subsystem: string): ConnectionRow[] =>
  carrier.components
    .find((part) => part.ref === ref)!
    .pins.filter((pin) => pin.net)
    .map((pin) => {
      const kind = netKind(pin.net);
      return {
        id: `${ref}.${pin.pin}`,
        from: "pi",
        to: subsystem,
        net: pin.net,
        pin: `Pi ${pin.pin}`,
        destination: `${ref}.${pin.pin}`,
        gpio: bcm[pin.pin] === undefined ? "—" : `BCM ${bcm[pin.pin]}`,
        voltage:
          pin.net === "+5V"
            ? "5 V rail / riel"
            : pin.net === "+3V3"
              ? "3.3 V rail / riel"
              : kind === "ground"
                ? "0 V reference / referencia"
                : "3.3 V Pi logic; verify peripheral / verificar periférico",
        tags: [
          kind,
          ...(kind !== "power" && kind !== "ground"
            ? (["signals", "GPIO"] as WireFilter[])
            : []),
        ],
        status: "proposed",
        source: netlistPath,
      };
    });
export const connectionRows: ConnectionRow[] = [
  ...headerRows("J13", "display"),
  ...headerRows("J14", "audio"),
];
const add = (
  id: string,
  from: string,
  to: string,
  net: string,
  pin: string,
  destination: string,
  voltage: string,
  kind: WireFilter,
  status: WiringStatus = "proposed",
  source = netlistPath,
) =>
  connectionRows.push({
    id,
    from,
    to,
    net,
    pin,
    destination,
    voltage,
    gpio: "—",
    tags: [
      kind,
      ...(kind === "UART" ? (["GPIO"] as WireFilter[]) : []),
      ...(kind !== "power" && kind !== "ground"
        ? (["signals"] as WireFilter[])
        : []),
    ],
    status,
    source,
  });
add(
  "uart-tx",
  "pi",
  "stm",
  "PI_TXD",
  "Pi physical 8 / BCM 14",
  "U1.29 / PA3 RX",
  "3.3 V logic target / lógica prevista",
  "UART",
);
add(
  "uart-rx",
  "stm",
  "pi",
  "PI_RXD",
  "U1.28 / PA2 TX",
  "Pi physical 10 / BCM 15",
  "3.3 V logic target / lógica prevista",
  "UART",
);
["PB6", "PB7", "PB8", "PB9", "PA8"].forEach((pin, i) =>
  add(
    `servo-${i + 1}`,
    "stm",
    "servos",
    `PWM${i + 1} → R${i + 1} 220 Ω → SERVO${i + 1}`,
    pin,
    `J${i + 7}.1 signal`,
    "PWM level acceptance unverified / nivel sin validar",
    "servo",
  ),
);
for (let i = 7; i <= 11; i++) {
  add(
    `servo-power-${i}`,
    "buck",
    "servos",
    "+6V_SERVO",
    "J5.2 / external buck +",
    `J${i}.2`,
    "6.0 V design target / objetivo",
    "power",
  );
  add(
    `servo-ground-${i}`,
    "servos",
    "ground",
    "PGND",
    `J${i}.3`,
    "NT1.2 / PGND",
    "Power ground / tierra de potencia",
    "ground",
  );
}
add(
  "battery-servo",
  "battery",
  "buck",
  "VBAT_RAW → SW → F1 10 A → SW → J4",
  "J1.2 via J2/F1/J3",
  "J4.1 buck input",
  "3S: 11.1 V nominal; 12.6 V full / cargada",
  "power",
);
add(
  "battery-pi",
  "battery",
  "regulator",
  "VBAT_RAW → SW → F2 5 A → J6",
  "J1.2 via J2/F2",
  "J6.1 regulator input",
  "3S: 11.1 V nominal; 12.6 V full / cargada",
  "power",
);
add(
  "pi-supply",
  "regulator",
  "pi",
  "USB-C supply / alimentación",
  "External 5.1 V regulator",
  "Pi USB-C (not GPIO)",
  "5.1 V / 5 A target; module & PD unverified",
  "power",
  "unverified",
  "docs/wiring.md",
);
add(
  "stm-supply",
  "pi",
  "stm",
  "+5V → JP1 → D1 → +5V_BP",
  "J12 +5V",
  "U1 5V via JP1 / D1",
  "5 V input via 1N5819; independent +3V3_BP",
  "power",
);
add(
  "battery-ground",
  "battery",
  "ground",
  "PGND",
  "J1.1",
  "NT1.2",
  "Power ground / tierra de potencia",
  "ground",
);
add(
  "logic-ground",
  "pi",
  "ground",
  "GND",
  "J12 GND",
  "NT1.1",
  "Logic ground / tierra lógica",
  "ground",
);
add(
  "buck-ground",
  "buck",
  "ground",
  "PGND",
  "J4.2 / J5.1",
  "NT1.2",
  "Carrier power-ground design / tierra de potencia",
  "ground",
);
add(
  "regulator-ground",
  "regulator",
  "ground",
  "PGND",
  "J6.2 input return",
  "NT1.2",
  "External regulator isolation / USB-C return unverified",
  "ground",
  "unverified",
);
add(
  "stm-ground",
  "stm",
  "ground",
  "GND",
  "U1.19 / U1.39",
  "NT1.1",
  "Logic ground / tierra lógica",
  "ground",
);
add(
  "battery-adc",
  "battery",
  "stm",
  "VBAT_SENSE",
  "R6 100 kΩ / R7 22 kΩ + C3 100 nF",
  "U1.27 / PA1",
  "12.6 V → 2.27 V design; ADC calibration pending",
  "signals",
);
add(
  "camera-csi",
  "camera",
  "pi",
  "CSI",
  "OV5647 camera ribbon",
  "Pi CSI connector; contacts not mapped",
  "Exact cable/orientation unverified / sin verificar",
  "signals",
  "unverified",
  "docs/bom.md",
);
export const wiringNodes = [
  {
    id: "pi",
    label: "Raspberry Pi 5",
    refs: ["J12"],
    x: 480,
    y: 265,
    voltage: bi("5.1 V USB-C supply target", "Objetivo: 5.1 V por USB-C"),
    detail: bi(
      "High-level compute. Audio and screen operation reported; carrier routing remains proposed.",
      "Cómputo principal. Audio y pantalla reportados; la carrier sigue propuesta.",
    ),
  },
  {
    id: "audio",
    label: "ReSpeaker 2-Mics V2.0",
    refs: ["J14"],
    x: 180,
    y: 90,
    voltage: bi(
      "Pi 5 V and 3.3 V rails in design",
      "Rieles Pi de 5 V y 3.3 V en diseño",
    ),
    detail: bi(
      "Capture/playback confirmed at interface level. Exact manual pin wiring is not certified here. Carrier J14 routing is proposed.",
      "Captura/reproducción confirmadas como interfaz. No se certifica el cableado manual. J14 es propuesto.",
    ),
  },
  {
    id: "display",
    label: "3.5″ SPI display",
    refs: ["J13"],
    x: 785,
    y: 90,
    voltage: bi(
      "Pi 5 V and 3.3 V rails in design",
      "Rieles Pi de 5 V y 3.3 V en diseño",
    ),
    detail: bi(
      "Repository: Display-G 480 × 320 / ADS7846, waveshare35a. Verify the actual Waveshare-compatible revision before wiring.",
      "Repositorio: Display-G 480 × 320 / ADS7846, waveshare35a. Verifica la revisión compatible con Waveshare antes de cablear.",
    ),
  },
  {
    id: "camera",
    label: "Arducam OV5647",
    refs: [],
    x: 480,
    y: 45,
    voltage: bi(
      "CSI cable supply; contacts unverified",
      "Alimentación por CSI; contactos sin verificar",
    ),
    detail: bi(
      "Camera startup observed. This carrier has no CSI connector; the camera connects directly to the Pi. No invented ribbon pinout.",
      "Arranque observado. La carrier no tiene CSI: la cámara va a la Pi. No se inventan contactos del cable.",
    ),
  },
  {
    id: "stm",
    label: "STM32F401 Black Pill",
    refs: ["U1", "JP1", "D1", "J15"],
    x: 480,
    y: 475,
    voltage: bi(
      "5 V input via JP1/D1; own 3.3 V rail",
      "5 V por JP1/D1; riel de 3.3 V propio",
    ),
    detail: bi(
      "UART, PWM, ADC and future IMU are carrier design mappings. Firmware, electrical levels and motion are not physically validated.",
      "UART, PWM, ADC e IMU futura son asignaciones del diseño. Firmware, niveles y movimiento sin validar físicamente.",
    ),
  },
  {
    id: "servos",
    label: "MG996R × 5",
    refs: ["J7", "J8", "J9", "J10", "J11"],
    x: 180,
    y: 475,
    voltage: bi(
      "6.0 V target, external servo buck",
      "Objetivo 6.0 V, buck externo",
    ),
    detail: bi(
      "Five connectors: pin 1 signal, pin 2 +6 V, pin 3 PGND. The physical − + S order must be checked against orientation; stall-current budget is unverified.",
      "Cinco conectores: pin 1 señal, pin 2 +6 V, pin 3 PGND. Comprueba la orientación − + S; falta presupuesto de corriente de bloqueo.",
    ),
  },
  {
    id: "battery",
    label: "LiPo 3S / 11.1 V",
    refs: ["J1", "J2", "F1", "F2"],
    x: 90,
    y: 265,
    voltage: bi(
      "11.1 V nominal / 12.6 V fully charged",
      "11.1 V nominal / 12.6 V cargada",
    ),
    detail: bi(
      "Carrier design input. Fuses are not over-discharge protection. An appropriate external BMS/alarm and balanced 3S charger are still required.",
      "Entrada del diseño. Los fusibles no protegen sobredescarga. Se requieren BMS/alarma y cargador balanceador 3S externos.",
    ),
  },
  {
    id: "buck",
    label: "Adjustable servo buck",
    refs: ["J4", "J5", "C1", "C2"],
    x: 235,
    y: 355,
    voltage: bi(
      "Adjust to 6.0 V before connection",
      "Ajustar a 6.0 V antes de conectar",
    ),
    detail: bi(
      "External module, exact part and current rating unverified. J4 is input; J5 is regulated return. A 10 A fuse does not certify the buck or traces for 10 A continuous.",
      "Módulo externo; modelo y corriente sin verificar. J4 es entrada; J5 retorno regulado. El fusible de 10 A no certifica 10 A continuos.",
    ),
  },
  {
    id: "regulator",
    label: "Pi DC-DC regulator",
    refs: ["J6"],
    x: 785,
    y: 340,
    voltage: bi(
      "5.1 V / 5 A design target",
      "Objetivo del diseño: 5.1 V / 5 A",
    ),
    detail: bi(
      "Separate Pi supply, not the 6 V servo rail. Actual converter, USB-C negotiation, cable loss and current capability remain unverified.",
      "Fuente Pi separada del riel servo de 6 V. Convertidor, negociación USB-C, caída y capacidad sin verificar.",
    ),
  },
  {
    id: "ground",
    label: "NT1 / GND ↔ PGND",
    refs: ["NT1"],
    x: 785,
    y: 490,
    voltage: bi("One designed ground tie", "Un punto de unión diseñado"),
    detail: bi(
      "Logic GND and power PGND meet only at NT1 in the carrier. Keep high-current servo returns out of audio/logic paths. Verify continuity before power.",
      "En la PCB, GND lógica y PGND de potencia se unen en NT1. Falta verificar retornos adicionales del regulador externo. Evita retorno de servos por audio/lógica; verifica continuidad sin energía.",
    ),
  },
] as const;
export interface WireEdge {
  from: string;
  to: string;
  label: string;
  kind: WireFilter;
  status: WiringStatus;
}
export const wiringEdges: WireEdge[] = [
  {
    from: "pi",
    to: "audio",
    label: "I²C / J14",
    kind: "I2C",
    status: "proposed",
  },
  {
    from: "pi",
    to: "audio",
    label: "I²S / J14",
    kind: "I2S",
    status: "proposed",
  },
  {
    from: "pi",
    to: "display",
    label: "SPI0 / J13",
    kind: "SPI",
    status: "proposed",
  },
  {
    from: "camera",
    to: "pi",
    label: "CSI · contacts TBD",
    kind: "signals",
    status: "unverified",
  },
  {
    from: "pi",
    to: "stm",
    label: "UART / PA2 + PA3",
    kind: "UART",
    status: "proposed",
  },
  {
    from: "stm",
    to: "servos",
    label: "PWM / 220 Ω",
    kind: "servo",
    status: "proposed",
  },
  {
    from: "battery",
    to: "buck",
    label: "F1 10 A / J4",
    kind: "power",
    status: "proposed",
  },
  {
    from: "battery",
    to: "regulator",
    label: "F2 5 A / J6",
    kind: "power",
    status: "proposed",
  },
  {
    from: "buck",
    to: "servos",
    label: "J5 / 6 V target",
    kind: "power",
    status: "proposed",
  },
  {
    from: "regulator",
    to: "pi",
    label: "USB-C / 5.1 V target",
    kind: "power",
    status: "unverified",
  },
  {
    from: "pi",
    to: "stm",
    label: "JP1 + D1 / 5 V",
    kind: "power",
    status: "proposed",
  },
  {
    from: "pi",
    to: "audio",
    label: "5 V / 3.3 V",
    kind: "power",
    status: "proposed",
  },
  {
    from: "pi",
    to: "display",
    label: "5 V / 3.3 V",
    kind: "power",
    status: "proposed",
  },
  {
    from: "battery",
    to: "ground",
    label: "PGND",
    kind: "ground",
    status: "proposed",
  },
  {
    from: "pi",
    to: "ground",
    label: "GND",
    kind: "ground",
    status: "proposed",
  },
  {
    from: "servos",
    to: "ground",
    label: "PGND",
    kind: "ground",
    status: "proposed",
  },
  {
    from: "buck",
    to: "ground",
    label: "PGND / J4 + J5",
    kind: "ground",
    status: "proposed",
  },
  {
    from: "stm",
    to: "ground",
    label: "GND",
    kind: "ground",
    status: "proposed",
  },
];
export function matchesFilter(row: { tags: WireFilter[] }, filter: WireFilter) {
  return filter === "all" || row.tags.includes(filter);
}
export function physicalPiNet(pin: string) {
  return piHeader[pin] ?? "NC";
}
