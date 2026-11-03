"""Build cuty_carrier.kicad_pcb: placement, outline, silkscreen and hand-routed
high-current tracks. Signals are routed afterwards by route.py (Freerouting).

Run with the system Python that ships KiCad's pcbnew module (/usr/bin/python3).
All coordinates below are board-relative millimetres (origin = top-left corner).
"""

from __future__ import annotations

import json
from pathlib import Path

import pcbnew

from netlist import FP, POWER_NETS, SERVO_NAMES, build, check

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "cuty_carrier.kicad_pcb"
OX, OY = 100.0, 50.0          # board origin on the page
W, H = 100.0, 92.0            # board size (PCBWay <=100x100 price tier)

# ref: (x, y, rotation)  - x/y of the footprint origin (pad 1 for most parts)
SERVO_Y = [51.5, 59.0, 66.5, 74.0, 81.5]
PLACE = {
    # power entry (top band) -------------------------------------------
    "J1": (18.0, 19.0, 90),      # XT60, mouth to the left edge, + pad on top
    "J2": (32.0, 5.6, 180),      # main switch terminal, wires exit top edge
    "J4": (44.5, 5.6, 180),      # servo buck input
    "J3": (57.0, 5.6, 180),      # servo switch terminal
    "F2": (24.0, 14.5, 0),       # Raspberry Pi fuse 5 A
    "F1": (44.0, 14.5, 0),       # servo fuse 10 A
    "J6": (5.5, 27.5, 270),      # Pi regulator input, wires exit left edge
    "J5": (5.5, 39.0, 270),      # servo buck output (pin 2 = +6 V)
    "C1": (15.0, 40.0, 0),
    "C2": (27.0, 40.0, 0),
    "R10": (14.0, 27.0, 0), "D4": (26.5, 27.0, 180),
    "R9": (14.0, 31.8, 0), "D3": (26.5, 31.8, 180),
    "NT1": (38.8, 24.0, 180),    # GND (pin 1) on the logic side, PGND on the power side
    # logic --------------------------------------------------------------
    "J13": (93.0, 4.0, 270),     # display header: odd row at the top edge, pin 1 on the right
    "J14": (93.0, 50.0, 270),    # ReSpeaker header, same orientation as the Pi
    "J12": (93.0, 59.5, 270),    # Raspberry Pi box header (ribbon cable)
    "U1": (96.5, 88.5, 180),     # Black Pill, USB-C at the right edge
    "D1": (54.16, 68.1, 180),
    "JP1": (36.5, 68.1, 90),
    "J15": (42.5, 74.0, 0),
    "R11": (38.5, 84.0, 90), "R12": (35.5, 84.0, 90),
    "R6": (42.0, 24.0, 270), "R7": (45.0, 31.62, 90), "C3": (48.0, 31.62, 90),
    "R8": (22.0, 89.5, 0), "D2": (34.5, 89.5, 180),
    # mounting
    "H1": (3.5, 3.5, 0), "H2": (96.5, 12.0, 0), "H3": (3.5, 88.5, 0), "H4": (42.0, 88.5, 0),
}
for i, y in enumerate(SERVO_Y):
    PLACE[f"J{7 + i}"] = (7.6, y, 270)          # S, +, - from right to left
    PLACE[f"R{i + 1}"] = (19.5, y, 180)         # PWM pad on the right, servo pad on the left

# Reference designator positions where the library default collides (board coords).
REF_POS = {
    "F2": (29.0, 16.2, 0), "F1": (49.0, 16.2, 0),
    "J2": (29.5, 3.0, 0), "J4": (42.0, 3.0, 0), "J3": (54.5, 3.0, 0),
    "J6": (9.4, 30.0, 90), "J5": (9.4, 41.5, 90), "J1": (9.0, 12.0, 0),
    "R10": (17.8, 25.2, 0), "R9": (17.8, 30.0, 0), "D4": (22.0, 29.6, 0), "D3": (22.0, 34.4, 0),
    "JP1": (37.8, 70.6, 0), "D1": (49.1, 70.0, 0), "R8": (25.8, 87.6, 0), "D2": (33.2, 91.2, 0),
    "R6": (40.2, 27.8, 90), "R7": (46.4, 27.8, 90), "C3": (49.8, 29.1, 90),
    "J15": (40.4, 77.8, 90), "R11": (38.5, 86.4, 0), "R12": (35.5, 86.4, 0),
    "NT1": (37.5, 26.0, 0), "C1": (17.5, 46.4, 0), "C2": (29.5, 46.4, 0),
}
for i, y in enumerate(SERVO_Y):
    REF_POS[f"J{7 + i}"] = (5.0, y - 2.2, 0)
    REF_POS[f"R{i + 1}"] = (15.7, y - 2.2, 0)

# Hand-routed power: (net, layer, width, [points])
TRACKS = [
    ("VBAT_RAW", "F.Cu", 3.0, [(18.0, 11.8), (18.0, 5.6), (26.92, 5.6)]),
    ("VBAT_SW", "F.Cu", 3.0, [(32.0, 5.6), (32.0, 10.8)]),
    ("VBAT_SW", "F.Cu", 3.0, [(24.0, 14.5), (24.0, 10.8), (44.0, 10.8), (44.0, 14.5)]),
    ("VBAT_SERVO", "F.Cu", 3.0, [(53.92, 14.5), (57.0, 11.42), (57.0, 5.6)]),
    ("VBAT_SERVO_SW", "F.Cu", 3.0, [(51.92, 5.6), (44.5, 5.6)]),
    ("VBAT_PI", "F.Cu", 2.0, [(33.92, 17.9), (33.92, 24.0), (9.0, 24.0), (5.5, 27.5)]),
    ("+6V_SERVO", "F.Cu", 2.5, [(5.5, 44.08), (5.06, 46.5), (5.06, SERVO_Y[-1])]),
    ("+6V_SERVO", "B.Cu", 2.5, [(5.5, 44.08), (5.06, 46.5), (5.06, SERVO_Y[-1])]),
    ("+6V_SERVO", "F.Cu", 2.5, [(5.5, 44.08), (15.0, 44.08), (27.0, 44.08), (27.0, 40.0)]),
    ("+6V_SERVO", "F.Cu", 2.5, [(15.0, 44.08), (15.0, 40.0)]),
    # Net tie: each side leaves the zone keep-out on its own short track.
    ("PGND", "F.Cu", 1.0, [(36.2, 24.0), (36.2, 20.8)]),
    ("PGND", "B.Cu", 1.0, [(36.2, 24.0), (36.2, 20.8)]),
    ("GND", "F.Cu", 1.0, [(38.8, 24.0), (38.8, 27.2)]),
    ("GND", "B.Cu", 1.0, [(38.8, 24.0), (38.8, 27.2)]),
] + [(f"SERVO{i + 1}", "F.Cu", 0.5, [(7.6, y), (11.88, y)]) for i, y in enumerate(SERVO_Y)]
NT_KEEPOUT = (35.0, 22.6, 40.0, 25.4)     # no zone fill around the net-tie bridge

# Zone polygons (board-relative). PGND = power area, GND = logic area.
PGND_POLY = [(0, 0), (61, 0), (61, 21.5), (37.3, 21.5), (37.3, 47.5), (10.3, 47.5), (10.3, 92), (0, 92)]
GND_POLY = [(61, 0), (100, 0), (100, 92), (10.3, 92), (10.3, 47.5), (37.3, 47.5), (37.3, 21.5), (61, 21.5)]

SILK = [
    # (text, x, y, size, rotation)
    ("BAT 3S", 8.0, 15.5, 1.2, 0), ("-", 21.2, 19.0, 1.5, 0), ("+", 21.2, 11.8, 1.5, 0),
    ("SW PRINCIPAL", 29.5, 1.2, 0.9, 0),
    ("BUCK IN", 42.0, 1.2, 0.9, 0), ("+", 44.5, 9.0, 1.0, 0), ("-", 39.42, 9.0, 1.0, 0),
    ("SW SERVOS", 54.5, 1.2, 0.9, 0),
    ("FUSIBLE Pi 5A", 29.0, 20.6, 0.9, 0), ("FUSIBLE SERVOS 10A", 49.0, 20.6, 0.9, 0),
    ("REG Pi", 12.6, 25.5, 0.9, 0), ("+", 1.2, 27.5, 1.0, 0), ("-", 1.2, 32.58, 1.0, 0),
    ("BUCK OUT", 13.6, 36.6, 0.8, 0), ("-", 1.2, 39.0, 1.0, 0), ("+6V", 1.5, 44.08, 0.8, 0),
    ("BAT", 29.6, 27.0, 0.9, 0), ("6V", 29.4, 31.8, 0.9, 0),
    ("- + S", 5.0, 48.6, 0.9, 0),
    ("5V Pi", 37.6, 89.5, 0.9, 0), ("5V STM32", 37.8, 65.6, 0.8, 0),
    ("I2C IMU", 42.5, 71.4, 0.8, 0), ("3V3 GND SCL SDA", 44.8, 77.8, 0.8, 270),
    ("PANTALLA 3.5in (pin 1 >)", 78.0, 10.4, 1.0, 0),
    ("RESPEAKER 2-MIC (pin 1 >)", 76.0, 46.4, 1.0, 0),
    ("RPI 5 GPIO - cable plano 40 vias", 76.0, 66.9, 1.0, 0),
    ("C.U.T.Y carrier v1.0", 74.0, 25.0, 1.6, 0),
    ("Tec de Monterrey GDL - 2026", 74.0, 28.0, 1.0, 0),
    ("Divisor VBAT -> PA0", 48.0, 35.6, 0.8, 0),
]
for i, (y, name) in enumerate(zip(SERVO_Y, SERVO_NAMES)):
    SILK.append((f"J{7 + i} S{i + 1} {name}", 27.5, y, 0.9, 0))


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def write_project() -> None:
    """Design rules and net classes live in the .kicad_pro file."""
    pro_path = ROOT / "cuty_carrier.kicad_pro"
    pro = json.loads(pro_path.read_text()) if pro_path.exists() else {}
    pro["meta"] = {"filename": "cuty_carrier.kicad_pro", "version": 1}
    pro["board"] = {
        "design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2,
                         "silk_line_width": 0.12, "silk_text_size_h": 1.0, "silk_text_size_v": 1.0,
                         "silk_text_thickness": 0.15},
            "rules": {"min_clearance": 0.2, "min_track_width": 0.2, "min_via_annular_width": 0.15,
                      "min_via_diameter": 0.6, "min_through_hole_diameter": 0.3,
                      "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
                      "min_copper_edge_clearance": 0.5, "min_silk_clearance": 0.0,
                      "allow_blind_buried_vias": False, "allow_microvias": False},
            "rule_severities": {"silk_overlap": "ignore", "silk_over_copper": "ignore",
                                "silk_edge_clearance": "ignore", "text_height": "ignore",
                                "text_thickness": "ignore", "lib_footprint_issues": "ignore",
                                "lib_footprint_mismatch": "ignore", "courtyards_overlap": "warning"},
            "track_widths": [0.0, 0.3, 0.5, 0.8, 1.5, 2.0, 2.5, 3.0],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.8, "drill": 0.4},
                               {"diameter": 1.2, "drill": 0.6}],
        },
        "layer_presets": [], "viewports": [],
    }
    def cls(name, clearance, width, via, drill):
        return {"name": name, "clearance": clearance, "track_width": width, "via_diameter": via,
                "via_drill": drill, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
                "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
                "pcb_color": "rgba(0, 0, 0, 0.000)"}
    pro["net_settings"] = {
        "classes": [cls("Default", 0.25, 0.3, 0.8, 0.4),
                    cls("Supply", 0.25, 0.8, 1.0, 0.5),
                    cls("Power", 0.4, 2.5, 1.2, 0.6),
                    cls("PowerGnd", 0.4, 1.5, 1.2, 0.6)],
        "meta": {"version": 3},
        "net_colors": None, "netclass_assignments": None,
        "netclass_patterns": ([{"netclass": "Power", "pattern": n} for n in sorted(POWER_NETS - {"PGND"})]
                              + [{"netclass": "PowerGnd", "pattern": "PGND"}]
                              + [{"netclass": "Supply", "pattern": n}
                                 for n in ("+5V", "+3V3", "+5V_BP", "5V_JP", "+3V3_BP", "GND")]),
    }
    pro.setdefault("schematic", {"legacy_lib_dir": "", "legacy_lib_list": []})
    pro.setdefault("libraries", {"pinned_footprint_libs": [], "pinned_symbol_libs": []})
    pro.setdefault("sheets", [["00000000-0000-0000-0000-000000000000", ""]])
    pro.setdefault("text_variables", {})
    pro["boards"] = []
    pro_path.write_text(json.dumps(pro, indent=2))


def main() -> None:
    parts = build()
    check(parts)
    write_project()
    sym_uuid = json.loads((ROOT / "scripts" / "symbol_uuids.json").read_text())
    root_uuid = __import__("gen_sch").ROOT_UUID

    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.SetBoardThickness(mm(1.6))

    nets: dict[str, pcbnew.NETINFO_ITEM] = {}

    def net(name: str) -> pcbnew.NETINFO_ITEM:
        if name not in nets:
            item = pcbnew.NETINFO_ITEM(board, name)
            board.Add(item)
            nets[name] = item
        return nets[name]

    for p in parts:
        lib, name = p.footprint
        libpath = str(ROOT / "CUTY.pretty") if lib == "CUTY" else FP + lib + ".pretty"
        fp = pcbnew.FootprintLoad(libpath, name)
        assert fp is not None, (lib, name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(p.ref)
        fp.SetValue(p.value)
        x, y, rot = PLACE[p.ref]
        board.Add(fp)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pt(x, y))
        if p.ref in sym_uuid:
            fp.SetPath(pcbnew.KIID_PATH(f"/{sym_uuid[p.ref]}"))
        fp.SetField("Descripcion", p.note) if hasattr(fp, "SetField") else None
        for pad in fp.Pads():
            n = p.pins.get(pad.GetNumber(), "")
            if n:
                pad.SetNet(net(n))
                # Dense headers: solid zone joints instead of starved thermal spokes.
                if n == "GND" and p.ref in ("J12", "J13", "J14", "J15", "U1"):
                    pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        # Keep reference text small and readable.
        ref = fp.Reference()
        ref.SetTextSize(pcbnew.VECTOR2I(mm(0.9), mm(0.9)))
        ref.SetTextThickness(mm(0.14))
        fp.Value().SetVisible(False)
        if p.group == "mech" or p.ref in {f"J{n}" for n in range(7, 12)}:
            ref.SetVisible(False)          # labelled by board text instead
        if p.ref in REF_POS:
            rx, ry, rr = REF_POS[p.ref]
            ref.SetPosition(pt(rx, ry))
            ref.SetTextAngleDegrees(rr)

    # Outline with rounded corners.
    r = 2.0
    corners = [(r, 0, W - r, 0), (W, r, W, H - r), (W - r, H, r, H), (0, H - r, 0, r)]
    for x0, y0, x1, y1 in corners:
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pt(x0, y0)); seg.SetEnd(pt(x1, y1))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.1))
        board.Add(seg)
    for cx, cy, sx, sy in ((r, r, 0, r), (W - r, r, W - r, 0), (W - r, H - r, W, H - r), (r, H - r, r, H)):
        arc = pcbnew.PCB_SHAPE(board)
        arc.SetShape(pcbnew.SHAPE_T_ARC)
        arc.SetCenter(pt(cx, cy)); arc.SetStart(pt(sx, sy))
        arc.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T), True)
        arc.SetLayer(pcbnew.Edge_Cuts); arc.SetWidth(mm(0.1))
        board.Add(arc)

    for net_name, layer, width, pts in TRACKS:
        lid = board.GetLayerID(layer)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pt(x0, y0)); t.SetEnd(pt(x1, y1))
            t.SetWidth(mm(width)); t.SetLayer(lid); t.SetNet(net(net_name)); t.SetLocked(True)
            board.Add(t)

    for text, x, y, size, rot in SILK:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(pt(x, y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(max(0.12, size * 0.15)))
        t.SetTextAngleDegrees(rot)
        board.Add(t)

    board.Save(str(PCB))
    print("pcb written:", PCB.name, len(parts), "footprints,", len(nets), "nets")


if __name__ == "__main__":
    main()
