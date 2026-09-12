"""Blender worker for prepare_comparisons.py; all output uses metres, Y up, floor origin."""
import json
import math
import os
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

source, output = map(Path, sys.argv[sys.argv.index('--') + 1:])
report = {'assets': {}, 'processing': 'Original proportions and UVs retained. Car scene stripped to vehicle, excluding separate light-glow proxy meshes; car paint, glazing and lamps retain source topology; tyres, trim and metal simplified with material/UV boundaries protected. People and house retain source triangles. Draco geometry; 2K colour and 1K normal maps. Materials reconstructed where exports omitted them.'}


def material(name, color, roughness=.7, metallic=0, texture=None, normal=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    # Inputs are linear; artist-selected colours below are sRGB.
    shader.inputs['Base Color'].default_value = (*[(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4) for c in color], 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    if texture:
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(source / texture), check_existing=True)
        mat.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    if normal:
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(source / normal), check_existing=True)
        tex.image.colorspace_settings.name = 'Non-Color'
        bump = mat.node_tree.nodes.new('ShaderNodeNormalMap')
        bump.inputs['Strength'].default_value = .65
        mat.node_tree.links.new(tex.outputs['Color'], bump.inputs['Color'])
        mat.node_tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return mat


def bounds(objects):
    points = [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]
    return Vector([min(p[i] for p in points) for i in range(3)]), Vector([max(p[i] for p in points) for i in range(3)])


def triangles(objects):
    return sum(sum(len(p.vertices) - 2 for p in obj.data.polygons) for obj in objects)


for key in ['car', 'man', 'woman', 'house']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if key == 'house':
        bpy.ops.wm.open_mainfile(filepath=str(source / 'Modern House_05_blend.blend'))
    else:
        name = {'car': 'Car+Skoda+Kodiaq+2016.obj', 'man': 'Ivan_1304.obj', 'woman': 'Marina_1276.obj'}[key]
        bpy.ops.wm.obj_import(filepath=str(source / name))
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH' or (key == 'car' and ('Kodiaq' not in obj.name or obj.name.endswith('_Lights'))):
            bpy.data.objects.remove(obj, do_unlink=True)
    objects = list(bpy.context.scene.objects)
    original_triangles = triangles(objects)
    if key in ('man', 'woman'):
        prefix = 'Ivan_1304' if key == 'man' else 'Marina_1276'
        mat = material(key.title(), (1, 1, 1), .82, texture=prefix + '_DIFF-web.jpg', normal=prefix + '_NORM-web.jpg')
        for obj in objects:
            obj.data.materials.clear()
            obj.data.materials.append(mat)
        scale = .001
        note = 'Source interpreted as millimetres; scan pose and proportions preserved.'
    elif key == 'car':
        paint = material('Deep blue metallic paint', (.035, .23, .38), .27, .45)
        shader = paint.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Coat Weight'].default_value = .5
        shader.inputs['Coat Roughness'].default_value = .18
        glass = material('Tinted glazing', (.14, .21, .25), .16, .25)
        rubber = material('Tyres and rubber', (.085, .09, .095), .86)
        dark = material('Dark trim', (.12, .14, .16), .4, .12)
        chrome = material('Brushed alloy', (.7, .73, .76), .26, .82)
        red = material('Rear lamp lenses', (.55, .025, .035), .22, .12)
        white = material('Headlights and plates', (.88, .89, .86), .25, .15)
        icons = material('Original badges', (1, 1, 1), .4, .15, texture='tq_Kodiaq_Icons_Diffuse-web.jpg')
        for obj in objects:
            for i, mat in enumerate(obj.data.materials):
                name = mat.name if mat else ''
                replacement = paint if name == 'tq_Car_Paint' else icons if 'Icons' in name else rubber if 'Tire' in name or 'Rubber' in name else chrome if 'Chrome' in name or 'Mirror' in name else red if 'Red' in name else white if 'Light_Emission' in name or 'Plate_Europe' in name or name == 'Material' else glass if 'Glass' in name else dark
                obj.data.materials[i] = replacement
        # Preserve exterior paint and glazing exactly: decimation can spoil their
        # continuous reflections even when the silhouette is unchanged.
        bpy.ops.object.select_all(action='SELECT')
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.separate(type='MATERIAL')
        bpy.ops.object.mode_set(mode='OBJECT')
        objects = list(bpy.context.scene.objects)
        for obj in objects:
            if obj.active_material in (paint, glass, red, white, icons):
                continue
            bpy.context.view_layer.objects.active = obj
            decimate = obj.modifiers.new('Browser detail', 'DECIMATE')
            decimate.ratio = .24
            decimate.delimit = {'UV', 'MATERIAL', 'SHARP', 'NORMAL'}
            bpy.ops.object.modifier_apply(modifier=decimate.name)
            obj.data.normals_split_custom_set([(0, 0, 0)] * len(obj.data.loops))
            for polygon in obj.data.polygons:
                polygon.use_smooth = True
            obj.data.set_sharp_from_angle(angle=math.radians(45))
        low, high = bounds(objects)
        scale = 4.697 / (high.y - low.y)
        note = 'Uniformly calibrated to 4.697 m length; mirrors retained. Source materials missing, finishes reconstructed with supplied badge atlas. Dimensions: https://www.skoda-storyboard.com/en/press-kits/skoda-kodiaq-paris-press-kit-2016/'
    else:
        plaster = material('Warm mineral plaster', (.84, .82, .76), .94)
        frame = material('Graphite window frames', (.2, .24, .26), .42, .25)
        glass = material('Blue grey glazing', (.24, .35, .40), .19, .28)
        roof = material('Standing seam roof', (.28, .32, .33), .46, .5)
        timber = material('Timber screens', (1, 1, 1), .78, texture='Modern House_01_TEXTURE (7)-web.jpg')
        paving = material('Stone terrace', (1, 1, 1), .95, texture='Modern House_01_TEXTURE (3)-web.jpg')
        concrete = material('Concrete sills and steps', (.62, .64, .62), .9)
        palette = {1: timber, 2: frame, 3: concrete, 4: plaster, 5: roof, 6: glass, 7: concrete, 8: paving, 9: plaster, 10: plaster, 11: timber}
        for obj in objects:
            mat = palette[int(obj.name[-2:])]
            obj.data.materials.clear()
            obj.data.materials.append(mat)
        scale = .02
        note = 'Illustrative two-storey house scale: 6.36 m overall height. Site bounds include terraces and fences. Original single blank material replaced by finishes assigned to architectural mesh groups; supplied timber and paving UV textures retained.'
    # Bake world transforms and uniformly scale, then centre on the floor.
    rotation = Matrix.Rotation(math.pi / 2, 4, 'Z') if key == 'car' else Matrix.Identity(4)
    for obj in objects:
        obj.data.transform(Matrix.Scale(scale, 4) @ rotation @ obj.matrix_world)
        obj.matrix_world = Matrix.Identity(4)
    low, high = bounds(objects)
    offset = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    for obj in objects:
        obj.data.transform(Matrix.Translation(-offset))
    # Join meshes sharing materials to reduce draw calls (glTF splits by material).
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = key
    final_triangles = triangles([obj])
    size = high - low
    path = output / (key + '.glb')
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                              export_animations=False, export_cameras=False, export_lights=False,
                              export_image_format='AUTO', export_draco_mesh_compression_enable=True,
                              export_draco_mesh_compression_level=6,
                              export_draco_position_quantization=14, export_draco_normal_quantization=10,
                              export_draco_texcoord_quantization=12)
    report['assets'][key] = {'file': path.name, 'bytes': path.stat().st_size,
                             'original_triangles': original_triangles, 'triangles': final_triangles,
                             'dimensions_m': [round(size.x, 5), round(size.z, 5), round(size.y, 5)],
                             'scale_note': note}
    print(key, report['assets'][key], flush=True)
(output / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n')
# Some headless Blender builds hang in PulseAudio teardown, even with -noaudio.
# All exports are synchronous and files are closed before bypassing that teardown.
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
