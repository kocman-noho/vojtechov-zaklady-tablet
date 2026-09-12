"""Check the delivered turbine's blade tips and calibration, without rendering."""
from pathlib import Path
import numpy as np
import trimesh

root = Path(__file__).resolve().parents[1]
mesh = trimesh.load(root / 'public/models/turbine.glb', force='mesh', process=False)
v = mesh.vertices
rotor = v[(v[:, 2] < -5) & (v[:, 1] > 40)]
radius = np.linalg.norm(rotor[:, :2] - [0, 132], axis=1)
angle = np.arctan2(rotor[:, 1] - 132, rotor[:, 0])
tips = []
for direction in [0, 2 * np.pi / 3, -2 * np.pi / 3]:
    difference = np.arctan2(np.sin(angle - direction), np.cos(angle - direction))
    sector = np.abs(difference) < .8
    points, distances = rotor[sector], radius[sector]
    assert abs(distances.max() - 87.5) < .002, 'Blade shell reaches the 175 m rotor circle'
    tips.append(points[distances.argmax()])
assert np.allclose(np.mean(tips, axis=0)[:2], [0, 132], atol=.002), 'Three blade tips centre on the 132 m hub'
assert abs(v[:, 1].min()) < 1e-5, 'Tower remains at the original foundation connection'
# Base accessories extend past the circular shell; its median radius is stable.
base = v[v[:, 1] < .001]
assert abs(np.median(np.linalg.norm(base[:, [0, 2]], axis=1)) - 3.35) < .01, '6.7 m tower base retained'
mesh.merge_vertices(merge_tex=True, merge_norm=True, digits_vertex=5)
for component in mesh.split(only_watertight=False):
    p = component.vertices
    if np.all(p[:, 2] < -5) and np.all(p[:, 1] > 40):
        assert np.linalg.norm(p[:, :2] - [0, 132], axis=1).min() < 85, 'No detached tip attachments remain'
print('PASS: three tapered tips, 175 m rotor, 132 m hub, 6.7 m tower connection, no detached tip fittings.')
