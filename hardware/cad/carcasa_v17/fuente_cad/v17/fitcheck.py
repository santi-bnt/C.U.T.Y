"""Point-sampling clearance check of components/keep-outs against the body inner surface."""
import sys, itertools
sys.path.insert(0,'.')
from common import *
import body, refs

def sample_pts(shape, n=6):
    b = shape.BoundingBox()
    xs=[b.xmin+(b.xmax-b.xmin)*i/n for i in range(n+1)]
    ys=[b.ymin+(b.ymax-b.ymin)*i/n for i in range(n+1)]
    zs=[b.zmin+(b.zmax-b.zmin)*i/n for i in range(n+1)]
    pts=[(x,y,z) for x in xs for y in ys for z in zs]
    if len(shape.Solids())==1 and shape.Volume() < 0.9*b.xlen*b.ylen*b.zlen:
        pts=[p for p in pts if shape.isInside(V(*p), 0.3)]
    return pts

def worst(shape, clearance):
    w=None
    for x,y,z in sample_pts(shape):
        if z < body.Z_HOLE or z > body.BODY_TOP: 
            continue
        a,b_,n = body.profile_at(z, BODY_WALL+clearance)
        v=(abs(x)/a)**n+(abs(y)/b_)**n
        if w is None or v>w[0]: w=(v,(round(x,1),round(y,1),round(z,1)))
    return w

items = refs.carrier_pcb()+refs.raspberry_pi5()+refs.power_modules()+refs.speaker()+refs.imu()
for nm in ('servo_arm_R','servo_arm_L'):
    items.append((nm, refs.servo_envelope(nm), None))
kos = refs.carrier_keepouts()+refs.pi_keepouts()+refs.power_keepouts()
bad=[]
for n,s,_ in items:
    w=worst(s,1.0)
    if w and w[0]>1: bad.append((n,)+w)
for n,s in kos:
    w=worst(s,0.0)
    if w and w[0]>1: bad.append((n,)+w)
for b in sorted(bad,key=lambda t:-t[1]): print('OUT', b[0], round(b[1],3), b[2])
print('checked', len(items)+len(kos), 'bad', len(bad))
