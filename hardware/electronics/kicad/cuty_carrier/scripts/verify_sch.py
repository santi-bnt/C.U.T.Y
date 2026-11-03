"""Compare the netlist KiCad extracts from the schematic with netlist.py."""
import sys
import sexpdata
from sexpdata import Symbol
from netlist import build, nets

def kicad_nets(path):
    tree = sexpdata.loads(open(path).read())
    netsec = next(n for n in tree if isinstance(n, list) and n[0] == Symbol("nets"))
    out = {}
    for net in netsec[1:]:
        name = next(n[1] for n in net if isinstance(n, list) and n[0] == Symbol("name"))
        nodes = [(str(next(x[1] for x in n if isinstance(x, list) and x[0] == Symbol("ref"))),
                  str(next(x[1] for x in n if isinstance(x, list) and x[0] == Symbol("pin"))))
                 for n in net if isinstance(n, list) and n[0] == Symbol("node")]
        out[str(name).lstrip("/")] = set(nodes)
    return out

got = kicad_nets(sys.argv[1])
want = {k: set(v) for k, v in nets(build()).items()}
# KiCad names unconnected pins "unconnected-(...)" nets; those must be single-pin.
extra = {k: v for k, v in got.items() if k not in want}
bad_extra = {k: v for k, v in extra.items() if not k.startswith("unconnected-") or len(v) != 1}
diff = {k: (want[k] ^ got.get(k, set())) for k in want if want[k] != got.get(k, set())}
print("nets wanted:", len(want), "nets in schematic:", len(got), "unconnected singles:", len(extra) - len(bad_extra))
print("mismatches:", diff or "none"); print("unexpected nets:", bad_extra or "none")
sys.exit(1 if diff or bad_extra else 0)
