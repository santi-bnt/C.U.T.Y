"""Generates docs/assets/freertos-firmware-architecture.svg (run from the repo root).

Hand-placed layout; edit the numbers below and re-run if tasks or queues change."""
from pathlib import Path

W, H = 1280, 910
INK, MUTED = "#2C2C2A", "#5F5E5A"
RAMPS = {  # fill, stroke, title, body
    "pi": ("#EEEDFE", "#534AB7", "#26215C", "#3C3489"),
    "isr": ("#FAECE7", "#993C1D", "#4A1B0C", "#712B13"),
    "task": ("#E1F5EE", "#0F6E56", "#04342C", "#085041"),
    "safety": ("#FCEBEB", "#A32D2D", "#501313", "#791F1F"),
    "queue": ("#F1EFE8", "#888780", "#2C2C2A", "#444441"),
    "hw": ("#FAEEDA", "#854F0B", "#412402", "#633806"),
}
FONT = "font-family=\"-apple-system,Segoe UI,Helvetica,Arial,sans-serif\""
out = []


def text(x, y, s, size=12, weight=400, fill=INK, anchor="start"):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
               f'text-anchor="{anchor}" {FONT}>{s}</text>')


def box(x, y, w, h, ramp, title, lines=(), center=False, rx=8):
    f, s, t, b = RAMPS[ramp]
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{f}" stroke="{s}" stroke-width="1"/>')
    cx, anchor = (x + w / 2, "middle") if center else (x + 12, "start")
    yy = y + 20
    text(cx, yy, title, 13, 600, t, anchor)
    for line in lines:
        yy += 17
        text(cx, yy, line, 12, 400, b, anchor)


def arrow(d, color=MUTED, dashed=False, width=1.4):
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash} marker-end="url(#a)"/>')


# ---- frame
out.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>')
text(20, 40, "C.U.T.Y STM32F401 firmware: FreeRTOS task architecture", 20, 700)
text(20, 64, "Hardware timers make the pulses; tasks only decide them. Arrows are data flow, dashed lines are supervision.", 13, 400, MUTED)
out.append('<rect x="300" y="92" width="960" height="800" rx="16" fill="#FAFAF8" stroke="#B4B2A9" stroke-width="1"/>')
text(320, 118, "STM32F401CC Black Pill: FreeRTOS V11.1 + CMSIS-RTOS2, 84 MHz, 1 kHz tick", 14, 600)

# ---- Raspberry Pi and UART
box(20, 250, 170, 320, "pi", "Raspberry Pi 5", ["stm32_bridge.py", "", "sends", "V2,HB every 100 ms", "V2,ARM  V2,START", "V2,TARGET,joint,milli", "", "reads", "ACK / NAK per frame", "TEL every 200 ms", "BOOT, DIAG every 5 s"])
arrow("M190 330 H316", "#534AB7")
arrow("M320 500 H194", "#534AB7")
text(255, 320, "pin 8 → PA3", 11, 400, MUTED, "middle")
text(255, 490, "PA2 → pin 10", 11, 400, MUTED, "middle")
text(255, 410, "USART2", 12, 600, INK, "middle")
text(255, 426, "115200 8N1", 11, 400, MUTED, "middle")

# ---- ISR
box(320, 250, 130, 320, "isr", "USART2 IRQ", ["NVIC priority 6", "", "RX", "byte + ms stamp", "errors: resync", "marker", "", "", "", "TX", "TXE drains the", "1 KB ring"])

# ---- row A: RX path
box(470, 305, 100, 50, "queue", "rx queue", ["256 x 8 B"], True)
arrow("M450 330 H466")
arrow("M570 330 H586")
box(590, 270, 200, 120, "task", "CommunicationTask", ["AboveNormal (32), on RX", "V2 parser, resync", "50 ms gap rule", "max 64 bytes, then yield"])
box(810, 280, 100, 42, "queue", "commands", ["8 entries"], True)
box(810, 338, 100, 42, "queue", "targets", ["3 x 1, latest"], True)
arrow("M790 301 H806"); arrow("M790 359 H806")
arrow("M910 301 H926"); arrow("M910 359 H926")
box(930, 250, 180, 140, "task", "ServoControlTask", ["High (40), 10 / 20 ms", "only controller owner", "states, HEAD_PAN FIR", "trajectory + limits", "pulses + output gate"])

# ---- SafetyTask and hardware column
box(590, 138, 520, 74, "safety", "SafetyTask: High1 (41), every 10 ms, never touches controller state",
    ["ServoControlTask beat older than 50 ms: kill PWM pins, stop refreshing IWDG", "Battery at 10 Hz: below 9.9 V for 1 s = BATTERY_LOW (latched until 11.0 V)"])
arrow("M990 250 V216", "#A32D2D", True)
arrow("M1060 212 V246", "#A32D2D", True)
text(996, 236, "beat", 11, 400, "#A32D2D")
text(1066, 236, "flags", 11, 400, "#A32D2D")
box(1130, 128, 115, 42, "hw", "IWDG", ["about 250 ms"], True)
box(1130, 178, 115, 42, "hw", "ADC1 PA1", ["122/22 divider"], True)
arrow("M1110 150 H1126", "#A32D2D", True)
arrow("M1130 199 H1114", "#854F0B")
arrow("M1098 212 V228 H1187 V246", "#A32D2D", True)
text(1120, 244, "kill", 11, 400, "#A32D2D", "middle")
box(1130, 250, 115, 140, "hw", "TIM4 PWM", ["50 Hz, 1 us steps", "PB6  J7 head", "PB7  J8 left arm", "PB8  J9 right arm", "J10, J11 held low"])
arrow("M1110 320 H1126", "#854F0B")
box(1130, 404, 115, 42, "hw", "LED PC13", ["state blink"], True)
arrow("M1110 540 H1187 V450", "#854F0B")

# ---- row B: TX path
box(930, 430, 85, 42, "queue", "replies", ["8 entries"], True)
box(1025, 430, 85, 42, "queue", "snapshot", ["1, latest"], True)
arrow("M972 390 V426"); arrow("M1067 390 V426")
box(830, 520, 280, 80, "task", "DiagnosticsTask", ["Low (8), every 200 ms", "snapshot to telemetry, LED, DIAG 5 s"])
arrow("M1067 472 V516")
box(700, 540, 100, 40, "queue", "telemetry", ["1 entry"], True)
box(700, 590, 100, 40, "queue", "diag", ["1 entry"], True)
arrow("M830 560 H804"); arrow("M830 600 V610 H804")
box(470, 430, 210, 90, "task", "TxTask", ["Normal (24), every 5 ms", "the only UART writer", "BOOT, ACK/NAK, TEL, DIAG"])
arrow("M930 451 H684")
arrow("M700 560 H630 V524"); arrow("M700 610 H600 V524")
arrow("M470 500 H454")

# ---- bottom panels
out.append('<rect x="320" y="660" width="440" height="215" rx="10" fill="#FFFFFF" stroke="#D3D1C7"/>')
text(336, 684, "Controller states (faults latch, first reason is kept)", 13, 600)
box(340, 704, 110, 40, "queue", "DISARMED", [], True)
box(500, 704, 100, 40, "queue", "READY", [], True)
box(640, 704, 100, 40, "task", "ACTIVE", [], True)
box(500, 810, 100, 40, "safety", "FAULT", [], True)
arrow("M450 724 H496"); text(473, 700, "HB+ARM", 11, 400, MUTED, "middle")
arrow("M600 724 H636"); text(618, 700, "START", 11, 400, MUTED, "middle")
arrow("M690 744 V830 H604", "#A32D2D")
text(698, 790, "heartbeat, RX,", 11, 400, "#A32D2D"); text(698, 804, "stale, overrun,", 11, 400, "#A32D2D"); text(698, 818, "limit, battery", 11, 400, "#A32D2D")
arrow("M500 830 H395 V748")
text(448, 822, "RESET", 11, 400, MUTED, "middle")
text(336, 866, "PWM only in ACTIVE. FAULT releases the servos; RESET clears it; DISARM always works.", 11, 400, MUTED)

out.append('<rect x="780" y="660" width="465" height="215" rx="10" fill="#FFFFFF" stroke="#D3D1C7"/>')
text(796, 684, "Four independent safety layers", 13, 600)
layers = [
    ("1", "Controller FAULT", "500 ms without HB, bad frame, limit, low battery: released"),
    ("2", "SafetyTask kill", "control task stuck > 50 ms: PWM pins forced low, latched"),
    ("3", "IWDG reset", "safety task or scheduler stuck: MCU resets, outputs off"),
    ("4", "J3 servo switch", "hardware cut of the 6 V servo rail, always available"),
]
for i, (n, title, desc) in enumerate(layers):
    y = 712 + i * 40
    out.append(f'<circle cx="806" cy="{y + 4}" r="11" fill="#FCEBEB" stroke="#A32D2D"/>')
    text(806, y + 8, n, 12, 600, "#501313", "middle")
    text(826, y + 2, title, 12, 600, INK)
    text(826, y + 18, desc, 11, 400, MUTED)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">'
       '<title>C.U.T.Y STM32F401 FreeRTOS firmware architecture</title>'
       '<desc>USART2 interrupt feeds CommunicationTask, which feeds ServoControlTask through queues; '
       'ServoControlTask drives TIM4 PWM; SafetyTask supervises it with the IWDG and battery ADC; '
       'DiagnosticsTask and TxTask send telemetry back to the Raspberry Pi.</desc>'
       '<defs><marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
       'orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" '
       'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>'
       + "".join(out) + "</svg>\n")
target = Path("docs/assets/freertos-firmware-architecture.svg")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(svg, encoding="utf-8")
print("wrote", target, len(svg), "bytes")
