"""Fast motion-sweep interference checks with manifold3d meshes."""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import manifold3d as mf
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ARM_AXIS_Y, ARM_AXIS_Z   # noqa
import base, build, verify


def to_manifold(shape, tol=0.25):
    M = _to_manifold(shape, tol)
    if M.status() != mf.Error.NoError:            # coarse tessellation can leave seams open: retry finer
        M = _to_manifold(shape, 0.05, 0.15)
    return M


def _to_manifold(shape, tol=0.25, ang=0.3):
    vs, tr = shape.tessellate(tol, ang)
    v = np.array([[p.x, p.y, p.z] for p in vs], dtype=np.float64)
    f = np.array(tr, dtype=np.int64)
    m = trimesh.Trimesh(v, f, process=True)
    m.merge_vertices()
    mesh = mf.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32), tri_verts=np.asarray(m.faces, dtype=np.uint32))
    return mf.Manifold(mesh)


def rot_matrix(axis_pt, axis_dir, deg):
    a = np.radians(deg)
    d = np.array(axis_dir, float) / np.linalg.norm(axis_dir)
    K = np.array([[0, -d[2], d[1]], [d[2], 0, -d[0]], [-d[1], d[0], 0]])
    R = np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K
    p = np.array(axis_pt, float)
    t = p - R @ p
    return np.hstack([R, t[:, None]])


def compose(A, B):
    """A after B (3x4 matrices)."""
    A4 = np.vstack([A, [0, 0, 0, 1]])
    B4 = np.vstack([B, [0, 0, 0, 1]])
    return (A4 @ B4)[:3]


def vol(a, b):
    i = a ^ b
    return i.volume()


def bb_hit(a, b, m=0.5):
    A = a.bounding_box()
    B = b.bounding_box()
    return not (A[3] + m < B[0] or B[3] + m < A[0] or A[4] + m < B[1] or B[4] + m < A[1] or A[5] + m < B[2] or B[5] + m < A[2])


def main():
    t0 = time.time()
    parts = verify.load_parts()
    M = {}
    bad = []
    for p in parts:
        try:
            M[p["name"]] = to_manifold(p["shape"])
            if M[p["name"]].status() != mf.Error.NoError or M[p["name"]].volume() <= 0:
                bad.append(p["name"])
        except Exception as e:
            bad.append(p["name"])
    print("manifolds", len(M), "bad", bad, round(time.time() - t0, 1), flush=True)
    grp = {p["name"]: p["group"] for p in parts}
    rep = {"non_manifold": bad}
    moving = [n for n in M if grp[n] in verify.MOVING_GROUPS]
    static = [n for n in M if grp[n] == "base"]
    if not build.FIJO:   # the fixed variant has no gimbal
        res = {}
        for pitch, roll in ((18, 0), (-18, 0), (0, 12), (0, -12), (0, 15), (0, -15), (0, 18), (0, -18), (14, 10), (-14, -10), (14, -10), (-14, 10)):
            T = compose(rot_matrix((0, 0, base.ROLL_BOLT_Z), (0, 1, 0), roll), rot_matrix((0, 0, base.PITCH_BOLT_Z), (1, 0, 0), pitch))
            hits = []
            for n in moving:
                mm = M[n].transform(T)
                for s in static:
                    if bb_hit(mm, M[s]):
                        v = vol(mm, M[s])
                        if v > 0.5:
                            hits.append((n, s, round(v, 2)))
            res[f"pitch{pitch:+d}_roll{roll:+d}"] = hits
        rep["gimbal"] = res
        print("gimbal", json.dumps(res), round(time.time() - t0, 1), flush=True)
    # head pan
    head = [n for n in M if grp[n] == "head" and not n.endswith("_spline")]
    others = [n for n in M if grp[n] in ("shell", "arms", "core") and n != "K4_Neck_Hub"]
    res = {}
    for ang in (-90, -60, -30, 30, 60, 90):
        T = rot_matrix((0, 0, 0), (0, 0, 1), ang)
        hits = []
        for n in head:
            mm = M[n].transform(T)
            for o in others:
                if bb_hit(mm, M[o]):
                    v = vol(mm, M[o])
                    if v > 0.5:
                        hits.append((n, o, round(v, 2)))
        res[f"pan{ang:+d}"] = hits
    rep["head_pan"] = res
    print("head", json.dumps(res), round(time.time() - t0, 1), flush=True)
    # arms
    res = {}
    names = {"L": ("A1_Arm_L", "A3_Hand_L", "A5_Arm_Cap_L"), "R": ("A2_Arm_R", "A4_Hand_R", "A6_Arm_Cap_R")}
    others = [n for n in M if grp[n] in ("shell", "head", "base")]
    for side, nms in names.items():
        for ang in (-120, -90, -60, -30, 30, 60, 90, 120):
            T = rot_matrix((0, ARM_AXIS_Y, ARM_AXIS_Z), (1, 0, 0), ang)
            hits = []
            for n in nms:
                mm = M[n].transform(T)
                for o in others:
                    if bb_hit(mm, M[o]):
                        v = vol(mm, M[o])
                        if v > 0.5:
                            hits.append((n, o, round(v, 2)))
            res[f"arm{side}{ang:+d}"] = hits
    rep["arms"] = res
    print("arms", json.dumps(res), round(time.time() - t0, 1), flush=True)
    # static pairwise (all) with meshes
    names = list(M)
    res = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if not (grp[a] and (a[:1] in "BGKSAH" and a[1:2].isdigit() or b[:1] in "BGKSAH" and b[1:2].isdigit())):
                continue
            if verify.ignored(a, b) or not bb_hit(M[a], M[b], 0.0):
                continue
            v = vol(M[a], M[b])
            if v > 0.5:
                res.append((a, b, round(v, 2)))
    rep["static_mesh"] = res
    print("static", json.dumps(res), round(time.time() - t0, 1), flush=True)
    (build.OUT / "sweep_report.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
