"""Check the finished PCB (pads read from the .kicad_pcb) against the project
specification tables (info.md: display, ReSpeaker, UART, servos, power)."""

import sys

import pcbnew

from gen_pcb import PCB
from netlist import BP_NAMES

board = pcbnew.LoadBoard(str(PCB))
pads = {}
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetNumber():
            pads[(fp.GetReference(), p.GetNumber())] = p.GetNetname()
by_name = {v: k for k, v in BP_NAMES.items()}
fails = []


def net(ref, pin):
    return pads[(ref, str(pin))]


def same(a, b, why):
    if not net(*a) or net(*a) != net(*b):
        fails.append(f"{why}: {a}={net(*a)!r} vs {b}={net(*b)!r}")


def check(cond, why):
    if not cond:
        fails.append(why)


# 2. Display: display pin == Raspberry pin (tested wiring).
for d, r in [(1, 1), (4, 4), (6, 6), (11, 11), (18, 18), (19, 19), (21, 21), (22, 22), (23, 23), (24, 24), (26, 26)]:
    same(("J13", d), ("J12", r), f"pantalla {d}->Pi {r}")
check(net("J12", 1) == "+3V3" and net("J12", 4) == "+5V" and net("J12", 6) == "GND", "rieles Pi")

# 3. ReSpeaker table (note 1->17 and 6->39 in the spec: same rails).
for s, r in [(1, 17), (2, 2), (6, 39), (3, 3), (5, 5), (7, 7), (12, 12), (35, 35), (37, 37), (38, 38), (40, 40)]:
    same(("J14", s), ("J12", r), f"ReSpeaker {s}->Pi {r}")
for s in (11, 19, 23, 32, 33):
    check(net("J14", s) == "", f"ReSpeaker pin {s} debe quedar desconectado")
check(net("J14", 8) == net("J14", 10) == "", "UART fuera del ReSpeaker")
# 3.3 V and 5 V never share a net.
check(net("J12", 1) != net("J12", 2), "3V3 y 5V separados")

# 4. UART crossover at 3.3 V.
same(("J12", 8), ("U1", by_name["PA3"]), "Pi TX (8) -> PA3 USART2_RX")
same(("J12", 10), ("U1", by_name["PA2"]), "Pi RX (10) <- PA2 USART2_TX")
check(net("U1", by_name["GND"]) == net("J12", 6) == "GND", "tierra comun Pi/STM32")

# 5. Servos: PWM pin -> series resistor -> S; V+ = 6 V; GND = power ground.
for i, pin in enumerate(["PB6", "PB7", "PB8", "PB9", "PA8"]):
    r, j = f"R{i + 1}", f"J{7 + i}"
    same(("U1", by_name[pin]), (r, 1), f"{pin} -> {r}")
    same((r, 2), (j, 1), f"{r} -> {j} S")
    check(net(j, 2) == "+6V_SERVO" and net(j, 3) == "PGND", f"{j} V+/GND")
    check(net(j, 2) not in {net("U1", by_name["5V"]), net("U1", by_name["3V3"]), net("J12", 2)},
          f"{j} no se alimenta de la STM32 ni de la Pi")

# 6. Power chain: battery -> switch -> fuses -> servo switch -> buck / regulator.
check({net("J1", 1), net("J1", 2)} == {"PGND", "VBAT_RAW"}, "XT60")
check({net("J2", 1), net("J2", 2)} == {"VBAT_RAW", "VBAT_SW"}, "interruptor general")
check(net("F1", 1) == net("F2", 1) == "VBAT_SW", "fusibles tras el interruptor")
check({net("J3", 1), net("J3", 2)} == {net("F1", 2), net("J4", 1)}, "F1 -> SW servos -> buck")
check(net("J6", 1) == net("F2", 2), "F2 -> regulador Pi")
check(net("J5", 2) == "+6V_SERVO", "salida buck = 6 V servos")
check(net("NT1", 1) == "GND" and net("NT1", 2) == "PGND", "union unica GND/PGND")

print("spec checks:", "OK" if not fails else "FAIL")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
