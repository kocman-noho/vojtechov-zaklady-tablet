"""Create an offline, self-contained WebGL review page from the generated GLBs."""
from pathlib import Path
import base64
import gzip
import json
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
data = {}
for mode, path in [("closed", "closed_display_1-160.glb"),
                   ("cutaway", "cutaway_display_1-160.glb"),
                   ("reference", "reference/cutaway_reference_1-160.glb")]:
    scene = trimesh.load(OUT / path, force="scene")
    parts = []
    for node in scene.graph.nodes_geometry:
        transform, geometry = scene.graph[node]
        m = scene.geometry[geometry].copy()
        m.apply_transform(transform)
        if mode == "reference" and any(key in node for key in ("rings", "radial", "shear", "pedestal_rebar")):
            # Opaque concrete hides these interior faces. Keep the exposed
            # quadrant in the lightweight browser copy; full CAD/GLB retains
            # the complete circular reinforcement population.
            triangles = m.vertices[m.faces]
            keep = np.any((triangles[:, :, 0] >= -.01) & (triangles[:, :, 1] >= -.01), axis=1)
            m.update_faces(keep)
            m.remove_unreferenced_vertices()
        positions = m.vertices[m.faces].reshape(-1, 3)
        normals = np.repeat(m.face_normals, 3, axis=0)
        arrays = np.column_stack((positions, normals)).astype("<f4")
        colors = m.visual.vertex_colors[0, :3] / 255
        lift = 0 if "base" in node or "duct" in node else 18
        if "concrete" in node:
            lift = 45
        if "tower" in node or "top_flange" in node:
            lift = 70
        if "anchor" in node:
            lift = 28
        if "shear" in node or "pedestal_rebar" in node:
            lift = 32
        if "upper_rebar" in node or "upper_rings" in node or "upper_radial" in node:
            lift = 58
        parts.append({"name": node, "color": colors.tolist(), "lift": lift,
                      "vertices": base64.b64encode(gzip.compress(arrays.tobytes(), compresslevel=6)).decode("ascii")})
    data[mode] = parts
template = (ROOT / "viewer_template.html").read_text()
(OUT / "preview.html").write_text(template.replace("__MODEL_DATA__", json.dumps(data, separators=(",", ":"))))
print("Offline preview written:", OUT / "preview.html")
