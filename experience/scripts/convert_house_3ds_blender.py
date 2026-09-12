"""Blender worker for the static 3DS house conversion."""
import json
import math
import os
import re
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

source, destination = map(Path, sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source / 'house.glb'))


def make_material(name, color, roughness, metallic=0, texture=None):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.use_backface_culling = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*[c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in color], 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    if texture:
        node = material.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(source / texture))
        material.node_tree.links.new(node.outputs['Color'], shader.inputs['Base Color'])
    return material


plaster = make_material('Warm plaster', (.84, .82, .77), .93)
palette = {
    'wall_light': plaster,
    'wall_dark': make_material('Sandstone accent plaster', (.65, .59, .49), .93),
    'roof': make_material('Clay roof tiles', (.48, .25, .16), .8),
    'roof_2': make_material('Roof soffits', (.48, .38, .28), .85),
    'wood': make_material('Timber frames and doors', (1, 1, 1), .7, texture='wood.jpg'),
    'glass': make_material('Window glazing', (.28, .37, .4), .16, .12),
    'stone': make_material('Stone masonry', (1, 1, 1), .93, texture='stone.jpg'),
    'dark sreel': make_material('Dark metalwork', (.22, .24, .25), .42, .6),
    'curtains': make_material('Linen curtains', (.88, .85, .79), .98),
}
glass_shader = palette['glass'].node_tree.nodes.get('Principled BSDF')
glass_shader.inputs['Alpha'].default_value = .38
objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
triangles_before = sum(len(obj.data.polygons) for obj in objects)
for obj in objects:
    bpy.context.view_layer.objects.active = obj
    original = re.sub(r'\.\d+$', '', obj.data.materials[0].name)
    if original not in palette:
        raise ValueError(f'Unrecognised source material: {original}')
    obj.data.materials.clear()
    obj.data.materials.append(palette[original])
    # Source window/door proportions are consistent with inch units. Use a
    # uniform 0.0254 m scale; the assumed units are recorded in provenance.
    obj.data.transform(Matrix.Scale(.0254, 4) @ obj.matrix_world)
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    # The supplied building extends below its z=0 finished-ground plane.
    # Retain that plane as the ground contact instead of exposing its footings.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                          dist=.000001, plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_inner=True)
    bm.to_mesh(obj.data)
    bm.free()
    if original == 'curtains' and len(obj.data.polygons) > 1000:
        modifier = obj.modifiers.new('Browser detail', 'DECIMATE')
        modifier.ratio = .08
        modifier.delimit = {'MATERIAL', 'SHARP', 'NORMAL'}
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    # Recompute normals at architectural creases after reducing dense tiles.
    obj.data.normals_split_custom_set([(0, 0, 0)] * len(obj.data.loops))
    for face in obj.data.polygons:
        face.use_smooth = True
    obj.data.set_sharp_from_angle(angle=math.radians(35))

points = [vertex.co for obj in objects for vertex in obj.data.vertices]
low = Vector([min(p[i] for p in points) for i in range(3)])
high = Vector([max(p[i] for p in points) for i in range(3)])
center = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
for obj in objects:
    obj.data.transform(Matrix.Translation(-center))
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.object.join()
house = bpy.context.object
house.name = 'house'
bpy.ops.export_scene.gltf(filepath=str(destination), export_format='GLB', use_selection=True,
                          export_animations=False, export_cameras=False, export_lights=False,
                          export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
                          export_draco_position_quantization=14, export_draco_normal_quantization=10,
                          export_draco_texcoord_quantization=12)
size = high - low
info = {'file': 'house.glb', 'bytes': destination.stat().st_size,
        'triangles': sum(len(face.vertices) - 2 for face in house.data.polygons),
        'dimensions_m': [round(size.x, 5), round(size.z, 5), round(size.y, 5)],
        'scale_note': 'Source units interpreted as inches from architectural proportions (0.0254 m per unit). Uniform scaling; below-ground geometry clipped at source z=0. Overall bounds include attached steps, roof and chimney, excluding site terrain/paving.',
        'material_note': 'Named 3DS material assignments retained. No source image texture references. Added project-supplied timber and stone textures; clay roof, plaster, curtains and glazing use PBR finishes. Curtain density reduced; original roof tile geometry preserved to avoid distorted edges.'}
(source / 'output.json').write_text(json.dumps(info, indent=2) + '\n')
print(json.dumps(info), flush=True)
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
