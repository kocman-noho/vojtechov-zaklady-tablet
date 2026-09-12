"""Rebuild only the browser turbine; original source files remain untouched."""
from pathlib import Path
import json
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'experience/public/models'


def prepare_turbine():
    source = next(ROOT.glob('Wind*/*.obj'))
    turbine = trimesh.load(source, force='mesh', process=False)
    turbine.visual.uv[:, 1] *= -1
    hub_z, cut_z = -.2723405, -.00144

    # The source contains five detached fittings on each blade tip, including
    # a conspicuous box/frame. Identify connected geometry using welded positions
    # ONLY for classification; retain the original mesh's UVs and topology.
    v = turbine.vertices
    rotor_mask = (v[:, 1] > .008) & (v[:, 2] < -.14)
    radial = np.linalg.norm(v[:, [0, 2]] - [0, hub_z], axis=1)
    source_radius = radial[rotor_mask].max()
    welded, inverse = np.unique(np.round(v, 10), axis=0, return_inverse=True)
    topology = trimesh.Trimesh(welded, inverse[turbine.faces], process=False)
    components = trimesh.graph.connected_components(topology.face_adjacency, nodes=np.arange(len(turbine.faces)))
    keep = np.ones(len(turbine.faces), dtype=bool)
    removed = []
    for component in components:
        indices = np.unique(turbine.faces[component])
        if np.all(rotor_mask[indices]) and radial[indices].min() > source_radius * .98:
            keep[component] = False
            removed.append(len(component))
    # Guard the source-specific cleanup against accidentally targeting a new model.
    if len(removed) != 15 or sum(removed) != 2184:
        raise ValueError(f'Unexpected tip geometry: {len(removed)} components, {sum(removed)} faces')
    turbine.update_faces(keep)
    turbine.remove_unreferenced_vertices()
    turbine = trimesh.intersections.slice_mesh_plane(turbine, [0, 0, -1], [0, 0, cut_z], cap=False)
    v = turbine.vertices.copy()
    rotor_mask = (v[:, 1] > .008) & (v[:, 2] < -.14)
    # Calibrate to the blade shell, not to the removed attachment extremities.
    rotor_radius = np.linalg.norm(v[rotor_mask][:, [0, 2]] - [0, hub_z], axis=1).max()
    scale = 87.5 / rotor_radius
    height = (cut_z - v[:, 2]) * scale
    base_shell_radius = .008954 * scale
    radial_fit = 1 - (1 - 3.35 / base_shell_radius) * (1 - np.clip(height / 95, 0, 1))
    source_hub = (cut_z - hub_z) * scale
    shorten = source_hub - 132
    height -= np.clip((height - 15) / 80, 0, 1) * shorten
    turbine.vertices = np.column_stack((v[:, 0] * scale * radial_fit, height, -v[:, 1] * scale * radial_fit))
    pbr = turbine.visual.material.to_pbr()
    pbr.metallicFactor, pbr.roughnessFactor = 0.0, .78
    turbine.visual.material = pbr
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'turbine.glb').write_bytes(trimesh.Scene(turbine).export(file_type='glb'))
    return {
        'source_file': str(source.relative_to(ROOT)), 'source_uv_v_sign_corrected': True,
        'source_label_rotor_m': 172, 'display_rotor_m': 175, 'display_hub_m': 132,
        'source_uniformly_scaled_hub_m': float(source_hub), 'tower_shortening_m': float(shorten),
        'tower_base_shell_diameter_m': 6.7, 'cut_plane_source_z': cut_z,
        'bounds_m': turbine.bounds.tolist(), 'faces': len(turbine.faces),
        'tip_cleanup': {'removed_components': len(removed), 'removed_faces': sum(removed),
                        'description': 'Removed detached source tip fittings; original tapered blade shells and UVs retained. Rotor calibration now uses the blade-shell radius.'},
    }


if __name__ == '__main__':
    path = OUT / 'provenance.json'
    report = json.loads(path.read_text()) if path.exists() else {}
    report['turbine'] = prepare_turbine()
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['turbine'], indent=2))
