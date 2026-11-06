import { bi, type Copy } from "./project";
import type { BoardPart } from "./engineering";
/** Descriptions of design intent, traced to carrier netlist.py and README. */
const functions: Record<string, Copy> = {
  J1: bi(
    "LiPo 3S battery entry. Pin 2 is VBAT_RAW; pin 1 is power ground. Verify actual polarity and connector orientation.",
    "Entrada LiPo 3S. Pin 2 VBAT_RAW; pin 1 tierra de potencia. Verifica polaridad y orientación reales.",
  ),
  J2: bi(
    "Connection for the external main power switch, between raw and switched battery nets.",
    "Conexión al interruptor principal externo, entre batería directa y conmutada.",
  ),
  J3: bi(
    "External servo-branch switch, downstream of the F1 fuse.",
    "Interruptor externo de servos después del fusible F1.",
  ),
  J4: bi(
    "Battery-side input to the external servo buck converter. This is not a regulated output.",
    "Entrada de batería al buck externo de servos. No es una salida regulada.",
  ),
  J5: bi(
    "Regulated return from the external servo buck. Design target is 6.0 V; measure it before connection. Pin 2 is positive, pin 1 PGND.",
    "Retorno regulado del buck externo. Objetivo: 6.0 V; mídelo antes de conectar. Pin 2 positivo, pin 1 PGND.",
  ),
  J6: bi(
    "Battery-side feed to a separate external Pi regulator. The proposed 5.1 V / 5 A output goes to Pi USB-C, not back through this connector.",
    "Alimentación de batería al regulador Pi externo. La salida propuesta de 5.1 V / 5 A va al USB-C Pi, no regresa por este conector.",
  ),
  J12: bi(
    "40-pin Raspberry Pi ribbon header. Physical pin numbering is preserved; only the listed nets are routed.",
    "Header de cable Pi de 40 pines. Conserva numeración física; solo se enrutan las redes indicadas.",
  ),
  J13: bi(
    "26-pin SPI display ribbon header for the documented Display-G / waveshare35a configuration. Verify the actual display revision.",
    "Header de pantalla SPI de 26 pines para Display-G / waveshare35a documentado. Verifica la revisión real.",
  ),
  J14: bi(
    "ReSpeaker V2.0 header with a deliberately restricted pin subset. Pins 11, 19, 23, 32 and 33 remain unconnected in this carrier design.",
    "Header ReSpeaker V2.0 con pines limitados. Los pines 11, 19, 23, 32 y 33 quedan sin conectar en el diseño.",
  ),
  J15: bi(
    "Future IMU connector on Black Pill I2C2, with an independent +3V3_BP rail. No sensor model or firmware is validated.",
    "Conector IMU futuro en I2C2 Black Pill, con +3V3_BP independiente. Sensor y firmware sin validar.",
  ),
  U1: bi(
    "Socket for the WeAct STM32F401CCU6 Black Pill. Routes UART, five PWM targets and battery sensing; firmware and physical motion are pending.",
    "Zócalo WeAct STM32F401CCU6 Black Pill. Distribuye UART, cinco PWM y medición de batería; firmware y movimiento pendientes.",
  ),
  NT1: bi(
    "The sole designed tie between logic GND and power PGND. This separates return paths; continuity still requires physical validation.",
    "Única unión diseñada entre GND lógica y PGND de potencia. Separa retornos; falta validar continuidad físicamente.",
  ),
  JP1: bi(
    "Removable Pi-to-Black-Pill 5 V supply jumper, upstream of the D1 Schottky diode.",
    "Jumper extraíble de 5 V Pi a Black Pill, antes del diodo Schottky D1.",
  ),
  D1: bi(
    "1N5819 Schottky in the Black Pill supply path, intended to prevent USB backfeed into the Pi. Electrical validation is pending.",
    "Schottky 1N5819 en la alimentación Black Pill, diseñado para evitar retorno USB a la Pi. Validación eléctrica pendiente.",
  ),
  F1: bi(
    "10 A design fuse for the battery-side servo branch. Its rating does not certify converter or track continuous-current capability.",
    "Fusible de diseño de 10 A en la rama de batería para servos. No certifica corriente continua del convertidor ni de pistas.",
  ),
  F2: bi(
    "5 A design fuse on the battery-side Pi regulator feed. It is not a measurement of the regulator output rating.",
    "Fusible de diseño de 5 A en batería hacia regulador Pi. No mide la capacidad de salida del regulador.",
  ),
  C3: bi(
    "100 nF battery-sense filter between VBAT_SENSE and logic ground.",
    "Filtro de medición de batería de 100 nF entre VBAT_SENSE y GND lógica.",
  ),
  R6: bi(
    "100 kΩ upper battery-divider resistor, from switched battery to VBAT_SENSE.",
    "Resistencia superior de 100 kΩ del divisor, desde batería conmutada a VBAT_SENSE.",
  ),
  R7: bi(
    "22 kΩ lower battery-divider resistor, from VBAT_SENSE to logic ground. The design maps 12.6 V to approximately 2.27 V; ADC calibration is pending.",
    "Resistencia inferior de 22 kΩ, desde VBAT_SENSE a GND. El diseño reduce 12.6 V a unos 2.27 V; calibración ADC pendiente.",
  ),
};
export function boardFunction(part: BoardPart): Copy {
  if (functions[part.ref]) return functions[part.ref];
  if (/^J(7|8|9|10|11)$/.test(part.ref))
    return bi(
      "Servo connector: pin 1 signal, pin 2 +6V_SERVO, pin 3 PGND. Check physical orientation; control firmware and load budget are pending.",
      "Conector servo: pin 1 señal, pin 2 +6V_SERVO, pin 3 PGND. Verifica orientación; firmware y presupuesto de carga pendientes.",
    );
  if (/^R[1-5]$/.test(part.ref))
    return bi(
      "220 Ω series resistor between the STM32 PWM target and the corresponding servo signal.",
      "Resistencia de 220 Ω en serie entre PWM STM32 y la señal del servo correspondiente.",
    );
  if (["C1", "C2"].includes(part.ref))
    return bi(
      "1000 µF / 16 V bulk capacitor on the designed 6 V servo rail, referenced to PGND. Check polarity.",
      "Capacitor de reserva de 1000 µF / 16 V en el riel servo de 6 V, referido a PGND. Revisa polaridad.",
    );
  if (["R11", "R12"].includes(part.ref))
    return bi(
      "4.7 kΩ I2C2 pull-up to the independent Black Pill +3V3_BP rail.",
      "Pull-up I2C2 de 4.7 kΩ al riel independiente +3V3_BP Black Pill.",
    );
  if (part.ref.startsWith("R"))
    return bi(
      "Indicator LED current-limiting resistor. Value and connected rail are defined by the native BOM and netlist.",
      "Resistencia limitadora del LED. Valor y riel definidos por BOM y netlist nativos.",
    );
  if (part.ref.startsWith("D"))
    return bi(
      "Rail indicator LED; assigned voltage label and nets are part of the design, not live measurements.",
      "LED indicador de riel; etiqueta y redes son del diseño, no medidas en vivo.",
    );
  return bi(
    "M3 mechanical mounting hole. The design keeps copper away from the mounting area.",
    "Orificio mecánico M3. El diseño mantiene cobre alejado del montaje.",
  );
}
