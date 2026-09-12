"""Create browser derivatives only; source CAD/OBJ are never modified."""
from pathlib import Path
import gzip, json
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'experience/public/models'
OUT.mkdir(parents=True,exist_ok=True)
report={}
scene=trimesh.load(ROOT/'models/output/reference/cutaway_reference_1-160.glb',force='scene')
result=trimesh.Scene()
for node in scene.graph.nodes_geometry:
 transform,key=scene.graph[node]
 m=scene.geometry[key].copy();m.apply_transform(transform)
 if any(k in node for k in ['rings','radial','shear','pedestal_rebar']):
  tri=m.vertices[m.faces]
  keep=np.any((tri[:,:,0]>=-.001)&(tri[:,:,1]>=-.001),axis=1)
  m.update_faces(keep);m.remove_unreferenced_vertices()
 # CAD 1:160 millimetre coordinates -> full-size metres, Y up; pedestal top = 0.
 v=m.vertices.copy();m.vertices=np.column_stack((v[:,0]*.16,v[:,2]*.16-3.68,-v[:,1]*.16))
 # Merge coincident exported vertices at 0.1 mm precision without changing positions.
 m.merge_vertices(digits_vertex=4,merge_norm=True,merge_tex=True)
 original_faces=len(m.faces)
 # Preserve triangulation: generic decimation distorts this CAD export's fine seams.
 m.visual=trimesh.visual.ColorVisuals(mesh=m,face_colors=[170,180,165,255])
 result.add_geometry(m,node_name=node,geom_name=node)
 report[node]={'original_faces':original_faces,'vertices':len(m.vertices),'faces':len(m.faces),'bounds_m':m.bounds.tolist()}
 print(node,len(m.vertices),len(m.faces),flush=True)
blob=result.export(file_type='glb');(OUT/'foundation.glb.gz').write_bytes(gzip.compress(blob,compresslevel=6))
from prepare_turbine import prepare_turbine
report['turbine'] = prepare_turbine()
report['reference_scope']='Actual-size reinforcement in exposed quadrant; remaining steel stays occluded by concrete. Reconstructed geometry has inferred placements and documented omissions. Explosion is explanatory, not construction sequencing.'
(OUT/'provenance.json').write_text(json.dumps(report,indent=2))
(OUT/'accuracy.json').write_bytes((ROOT/'models/output/reference/accuracy.json').read_bytes())
print('Ready',[(p.name,round(p.stat().st_size/1e6,2)) for p in OUT.iterdir()],flush=True)
