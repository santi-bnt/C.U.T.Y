"""Cable/connector keep-out volumes vs every printed part (mesh booleans)."""
import sys, json
sys.path.insert(0, '.')
import build, refs, head
from meshcheck import to_manifold, bb_hit
kos = refs.carrier_keepouts() + refs.pi_keepouts() + refs.power_keepouts() + [("ko_lcd_header", head.display_keepout())]
P = {n: to_manifold(build.cached(n, fn)) for n, fn, *_ in build.PRINTED}
bad = []
for n, k in kos:
    K = to_manifold(k)
    for pn, M in P.items():
        if n == "ko_pi_sd" and pn.startswith("S2_Body_Back"):      # SD is reached with the back shell off
            continue
        if bb_hit(K, M, 0.0):
            v = (K ^ M).volume()
            if v > 0.5:
                bad.append((n, pn, round(v, 1)))
print("keepouts", len(kos), "hits", json.dumps(bad))
