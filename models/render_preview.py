"""Run with Blender's bundled Python; renders generated CAD meshes locally."""
from pathlib import Path
import math
import sys
import bpy
from mathutils import Vector, Matrix

OUT = Path(__file__).resolve().parent / "output"
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 40
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.world.color = (.5, .5, .5)
scene.view_settings.view_transform = "AgX"


def material(name, color, metallic=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = .62
    bsdf.inputs["Metallic"].default_value = metallic
    return m


materials = {"concrete": material("Warm concrete", (.62, .64, .61)),
             "base": material("Graphite plinth", (.065, .095, .12)),
             "tower": material("Ivory tower", (.85, .87, .83)),
             "steel": material("Exposed steel", (.12, .18, .22), .3),
             "duct": material("Orange conduit", (.95, .25, .035))}


def load(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(OUT / (name + ".glb")))
    added = set(bpy.data.objects) - before
    # The trimesh GLB stores engineering Z-up coordinates. glTF import assumes
    # Y-up, so restore the engineering frame before setting up the camera.
    correction = Matrix.Rotation(-math.pi / 2, 4, "X")
    for obj in added:
        if obj.parent is None:
            obj.matrix_world = correction @ obj.matrix_world
    for obj in added:
        if obj.type != "MESH":
            continue
        key = "steel"
        for candidate in ("base", "tower", "duct", "concrete", "lower_center"):
            if candidate in obj.name:
                key = "concrete" if candidate == "lower_center" else candidate
                break
        obj.data.materials.clear()
        obj.data.materials.append(materials[key])
        if "reference" not in name:
            bevel = obj.modifiers.new("Render-only edge highlights", "BEVEL")
            bevel.width = .065
            bevel.segments = 2
    return added


floor = material("Backdrop", (.77, .80, .79))
bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, -.12))
bpy.context.object.data.materials.append(floor)

for location, energy, size in [((70, 20, 260), 2100000, 180),
                                ((-170, 70, 120), 1000000, 160),
                                ((20, -200, 170), 1300000, 130)]:
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.rotation_euler = (Vector((0, 0, 5)) - light.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(210, 245, 185))
camera = bpy.context.object
camera.rotation_euler = (Vector((0, 0, 10)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = 205
scene.camera = camera

targets = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else (
    "closed_display_1-160", "cutaway_display_1-160", "reference/cutaway_reference_1-160")
for name in targets:
    objects = load(name)
    scene.render.filepath = str(OUT / (name + ".png"))
    bpy.ops.render.render(write_still=True)
    for obj in objects:
        bpy.data.objects.remove(obj, do_unlink=True)
