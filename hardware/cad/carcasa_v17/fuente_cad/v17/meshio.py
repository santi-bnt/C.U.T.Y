"""Tessellate CadQuery shapes into a coloured GLB (for renders and the web viewer)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh


def tess(shape, tol=0.12, ang=0.25):
    from OCP.BRepTools import BRepTools
    BRepTools.Clean_s(shape.wrapped)          # drop any finer triangulation cached on the shape
    vs, tris = shape.tessellate(tol, ang)
    v = np.array([[p.x, p.y, p.z] for p in vs], dtype=np.float32)
    f = np.array(tris, dtype=np.int64)
    return v, f


def to_mesh(shape, tol=0.12, ang=0.25, smooth_deg=32.0):
    v, f = tess(shape, tol, ang)
    m = trimesh.Trimesh(vertices=v, faces=f, process=True)
    if len(m.faces) and smooth_deg:
        try:
            m = trimesh.graph.smooth_shade(m, angle=np.radians(smooth_deg))
        except Exception:
            pass
    return m


def export_glb(items, path, tol=0.15, ang=0.3, meta=None):
    """items: list of dict(name, shape, color(rgb 0-1), group, extra...)"""
    scene = trimesh.Scene()
    info = []
    for it in items:
        m = to_mesh(it["shape"], tol, ang)
        if len(m.faces) == 0:
            continue
        # glTF is Y-up: rotate world (Z-up) -> (Y-up): (x, y, z) -> (x, z, -y)
        R = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)
        m.apply_transform(R)
        _ = m.vertex_normals
        # build colours are sRGB (as Fusion/STEP shows them); glTF base colours are linear
        r, g, b = [((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92 for c in it["color"]]
        mat = trimesh.visual.material.PBRMaterial(
            name=it["name"], baseColorFactor=[r, g, b, it.get("alpha", 1.0)],
            metallicFactor=it.get("metal", 0.0), roughnessFactor=it.get("rough", 0.55),
            alphaMode="BLEND" if it.get("alpha", 1.0) < 1 else "OPAQUE", doubleSided=True)
        m.visual = trimesh.visual.TextureVisuals(material=mat)
        scene.add_geometry(m, node_name=it["name"], geom_name=it["name"])
        info.append({k: v for k, v in it.items() if k not in ("shape",)})
    from trimesh.exchange.gltf import export_glb as _eg
    Path(path).write_bytes(_eg(scene, include_normals=True))
    if meta is not None:
        Path(meta).write_text(json.dumps(info, indent=1))
    return info
