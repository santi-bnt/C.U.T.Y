"""PCB parity: every pad's net must match netlist.py, and all nets must be fully routed."""
import sys
import pcbnew
from netlist import build
from gen_pcb import PCB

board = pcbnew.LoadBoard(str(PCB))
parts = {p.ref: p for p in build()}
errors = []
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
if set(fps) != set(parts):
    errors.append(f"footprint set differs: {set(fps) ^ set(parts)}")
for ref, fp in fps.items():
    for pad in fp.Pads():
        want = parts[ref].pins.get(pad.GetNumber(), "") if pad.GetNumber() else ""
        got = pad.GetNetname()
        if want != got:
            errors.append(f"{ref}.{pad.GetNumber()}: board={got!r} design={want!r}")
board.BuildConnectivity()
unrouted = board.GetConnectivity().GetUnconnectedCount(True)
bb = board.GetBoardEdgesBoundingBox()
print(f"footprints {len(fps)}, pads checked {sum(len(list(f.Pads())) for f in fps.values())}, "
      f"unrouted {unrouted}, board {pcbnew.ToMM(bb.GetWidth()):.1f} x {pcbnew.ToMM(bb.GetHeight()):.1f} mm, "
      f"tracks {len(board.GetTracks())}")
print("errors:", errors or "none")
sys.exit(1 if errors or unrouted else 0)
