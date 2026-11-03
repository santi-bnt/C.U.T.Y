"""Autoroute with Freerouting, then pour GND / PGND zones and run DRC.

    /usr/bin/python3 route.py /path/to/freerouting.jar [passes]
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pcbnew
import sexpdata
from sexpdata import Symbol

from gen_pcb import GND_POLY, NT_KEEPOUT, OX, OY, PGND_POLY, PCB, mm, write_project
from netlist import POWER_NETS

# Same classes as the .kicad_pro (KiCad 7 scripting does not resolve its patterns).
CLASSES = {  # name: (clearance, width, via, drill)
    "Default": (0.25, 0.3, 0.8, 0.4),
    "Supply": (0.25, 0.8, 1.0, 0.5),
    "Power": (0.4, 2.5, 1.2, 0.6),
    "PowerGnd": (0.4, 1.5, 1.2, 0.6),
}
SUPPLY = {"+5V", "+3V3", "+5V_BP", "5V_JP", "+3V3_BP", "GND"}


def apply_netclasses(board) -> None:
    ns = board.GetDesignSettings().m_NetSettings
    made = {}
    for name, (clr, w, via, drill) in CLASSES.items():
        nc = ns.m_DefaultNetClass if name == "Default" else pcbnew.NETCLASS(name)
        nc.SetClearance(mm(clr)); nc.SetTrackWidth(mm(w))
        nc.SetViaDiameter(mm(via)); nc.SetViaDrill(mm(drill))
        if name != "Default":
            ns.m_NetClasses[name] = nc
        made[name] = nc
    for netname, item in board.GetNetsByName().items():
        netname = str(netname)
        cls = ("PowerGnd" if netname == "PGND" else "Power" if netname in POWER_NETS
               else "Supply" if netname in SUPPLY else "Default")
        if netname:
            item.SetNetClass(made[cls])


def import_ses(board, ses: Path) -> tuple[int, int]:
    """Minimal Specctra session importer (KiCad 7's needs the GUI)."""
    tree = sexpdata.loads(ses.read_text())

    def find(node, key):
        return [n for n in node if isinstance(n, list) and n and n[0] == Symbol(key)]

    routes = find(tree, "routes")[0]
    res = find(routes, "resolution")[0]
    scale = {"um": 1e-3, "mm": 1.0, "mil": 0.0254, "inch": 25.4}[str(res[1])] / float(res[2])

    def P(x, y):
        return pcbnew.VECTOR2I(mm(float(x) * scale), mm(-float(y) * scale))

    tracks = vias = 0
    for net in find(find(routes, "network_out")[0], "net"):
        item = board.FindNet(str(net[1]))
        for wire in find(net, "wire"):
            path = find(wire, "path")[0]
            layer, width, coords = str(path[1]), float(path[2]), path[3:]
            pts = [P(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
            for a, b in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(a); t.SetEnd(b); t.SetWidth(mm(width * scale))
                t.SetLayer(board.GetLayerID(layer)); t.SetNet(item)
                board.Add(t); tracks += 1
        for v in find(net, "via"):
            m = re.search(r"_(\d+):(\d+)_um", str(v[1]))
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(P(v[2], v[3]))
            via.SetWidth(mm(int(m.group(1)) / 1000)); via.SetDrill(mm(int(m.group(2)) / 1000))
            via.SetNet(item)
            board.Add(via); vias += 1
    return tracks, vias

ROOT = PCB.parent
WORK = ROOT / "scripts" / "_route"


def add_zone(board, net_name, layer, poly, priority, clearance=0.4):
    zone = pcbnew.ZONE(board)
    zone.SetLayer(board.GetLayerID(layer))
    zone.SetNet(board.FindNet(net_name))
    outline = zone.Outline()
    outline.NewOutline()
    inset = 0.0
    for x, y in poly:
        outline.Append(mm(OX + x), mm(OY + y))
    zone.SetAssignedPriority(priority)
    zone.SetLocalClearance(mm(clearance))
    zone.SetMinThickness(mm(0.3))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetThermalReliefGap(mm(0.4))
    zone.SetThermalReliefSpokeWidth(mm(0.6))
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(zone)
    return zone


def main() -> None:
    jar = sys.argv[1]
    passes = sys.argv[2] if len(sys.argv) > 2 else "40"
    WORK.mkdir(exist_ok=True)
    # Always start from a freshly generated board (placement + hand-routed power only).
    __import__("gen_pcb").main()
    board = pcbnew.LoadBoard(str(PCB))
    apply_netclasses(board)
    dsn, ses = WORK / "board.dsn", WORK / "board.ses"
    assert pcbnew.ExportSpecctraDSN(board, str(dsn))
    if passes != "reuse":
        subprocess.run(["java", "-jar", jar, "-de", str(dsn), "-do", str(ses), "-mp", passes,
                        "--gui.enabled=false"], check=True, cwd=WORK, timeout=1500)
    print("imported tracks/vias:", import_ses(board, ses))

    # Pours: logic GND and power PGND share the boundary drawn in gen_pcb.py.
    for layer in ("B.Cu", "F.Cu"):
        add_zone(board, "GND", layer, GND_POLY, 1)
        add_zone(board, "PGND", layer, PGND_POLY, 1)
    x0, y0, x1, y1 = NT_KEEPOUT
    keep = pcbnew.ZONE(board)
    keep.SetIsRuleArea(True)
    keep.SetDoNotAllowCopperPour(True)
    keep.SetDoNotAllowTracks(False); keep.SetDoNotAllowVias(False)
    keep.SetDoNotAllowPads(False); keep.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu)
    keep.SetLayerSet(ls)
    o = keep.Outline(); o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(mm(OX + x), mm(OY + y))
    board.Add(keep)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    # Remove short autorouter stubs that end nowhere.
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    removed = 0
    while True:
        stubs = [t for t in board.GetTracks()
                 if t.GetClass() == "PCB_TRACK" and not t.IsLocked() and conn.TestTrackEndpointDangling(t, False)]
        if not stubs:
            break
        for t in stubs:
            board.Remove(t); removed += 1
        board.BuildConnectivity()
        conn = board.GetConnectivity()
    print("dangling stubs removed:", removed)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    print("unconnected:", board.GetConnectivity().GetUnconnectedCount(True))
    board.Save(str(PCB))
    write_project()   # pcbnew rewrites the .kicad_pro on save; restore classes and rules
    report = ROOT / "drc_report.txt"
    pcbnew.WriteDRCReport(board, str(report), pcbnew.EDA_UNITS_MILLIMETRES, True)
    print(report.read_text()[-1500:])


if __name__ == "__main__":
    main()
