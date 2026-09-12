"""CadQuery display models derived from the supplied ENERCON foundation drawings.

All coordinates are millimetres. Run with the locally installed Python/CadQuery.
The display model deliberately simplifies steel. reference.py builds unexaggerated
geometry independently in full-size engineering coordinates.
"""
from pathlib import Path
import json
import math
import time

import cadquery as cq
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
SCALE = 160
K = 1000 / SCALE
R = 13.3 * K
RP = 4.4 * K
BASE_R = 86.0
FLOOR = 3.0
UNDERSIDE = FLOOR + 0.5 * K
TOP = FLOOR + 3.2 * K
COLORS = {"concrete": (0.72, 0.73, 0.70), "base": (0.16, 0.20, 0.23),
          "steel": (0.25, 0.31, 0.36), "tower": (0.91, 0.92, 0.87),
          "duct": (0.95, 0.39, 0.10)}
PARTS = {}
ASSEMBLIES = {}
REBAR_RADII = (33, 40.5, 48, 55.5, 63, 70.5, 78)
REBAR_ANGLES = (5, 25, 45, 65, 85)
MAT_Z = UNDERSIDE + .10
MAT_THICKNESS = 1.2
UPPER_THICKNESS = .9


def upper_rebar_z(r):
    return TOP - .4 * K - (r - RP) * 2.0 * K / (R - RP) - .55


def log(message):
    print(time.strftime("%H:%M:%S"), message, flush=True)


def box(x, y, z, at):
    return cq.Solid.makeBox(x, y, z, cq.Vector(*at))


def cylinder(radius, height, at=(0, 0, 0), direction=(0, 0, 1)):
    return cq.Solid.makeCylinder(radius, height, cq.Vector(*at), cq.Vector(*direction))


def fuse(shapes):
    shapes = list(shapes)
    return shapes[0].fuse(*shapes[1:]).clean() if len(shapes) > 1 else shapes[0]


def revolved(points):
    return cq.Workplane("XZ").polyline(points).close().revolve(360, (0, 0), (0, 1)).val()


def annulus(inner, outer, height, z):
    return cq.Workplane("XY").workplane(offset=z).circle(outer).circle(inner).extrude(height).val()


QUADRANT = box(150, 150, 120, (0, 0, -20))


def retained(shape):
    return shape.cut(QUADRANT).clean()


def sector(inner, outer, height, z, start=0, stop=90):
    a, b, m = [math.radians(v) for v in (start, stop, (start + stop) / 2)]
    xy = lambda r, t: (r * math.cos(t), r * math.sin(t))
    return (cq.Workplane("XY").workplane(offset=z).moveTo(*xy(outer, a))
            .threePointArc(xy(outer, m), xy(outer, b)).lineTo(*xy(inner, b))
            .threePointArc(xy(inner, m), xy(inner, a)).close().extrude(height).val())


def segment(p, q, radius):
    p, q = cq.Vector(*p), cq.Vector(*q)
    return cylinder(radius, (q - p).Length, p.toTuple(), (q - p).normalized().toTuple())


def flat_bar(p, q, width=1.2, depth=1.2):
    """A rectangular bar in the XY plane, flat on the print bed."""
    x, y = p
    dx, dy = q[0] - x, q[1] - y
    length = math.hypot(dx, dy)
    return (box(length + width, width, depth, (-width / 2, -width / 2, 0))
            .rotate((0, 0, 0), (0, 0, 1), math.degrees(math.atan2(dy, dx)))
            .translate((x, y, 0)))


def foundation():
    # Main section A-A: central top 0, pedestal -0.05/-0.40, edge -2.40/-2.70,
    # central underside -3.20; 500 mm / 500 mm underside transition.
    profile = [(0, TOP), (3.615 * K, TOP), (RP, TOP - .05 * K),
               (RP, TOP - .4 * K), (R, TOP - 2.4 * K),
               (R, UNDERSIDE), (4.9 * K, UNDERSIDE), (RP, FLOOR), (0, FLOOR)]
    return revolved(profile)


def concrete_parts(cutaway):
    complete = foundation()
    upper = complete.intersect(box(200, 200, 70, (-100, -100, UNDERSIDE)))
    lower = complete.intersect(box(200, 200, UNDERSIDE, (-100, -100, 0)))
    # Two small registration pins fit blind underside sockets. Both remain in
    # the retained concrete, for either version. Diametral clearance: 0.4 mm.
    for x, y in [(-13, -5), (7, -14)]:
        lower = lower.fuse(cylinder(1.5, 1.0, (x, y, UNDERSIDE - .05)))
        upper = upper.cut(cylinder(1.7, 1.3, (x, y, UNDERSIDE - .05)))
    if cutaway:
        upper, lower = retained(upper), retained(lower)
    return upper.clean(), lower.clean()


def display_base(cutaway):
    # The well follows the deeper centre with 0.25 mm radial clearance.
    base = revolved([(0, 0), (BASE_R - .7, 0), (BASE_R, .7),
                     (BASE_R, UNDERSIDE + .6), (R + .3, UNDERSIDE + .6),
                     (R + .3, UNDERSIDE), (4.9 * K + .25, UNDERSIDE),
                     (RP + .25, FLOOR), (0, FLOOR)])
    if cutaway:
        trench = box(68, 8.6, 8, (15, -4.3, FLOOR)).rotate((0, 0, 0), (0, 0, 1), 45)
        base = base.cut(trench)
        # Open saddles locate the three ducts without snap-fit force.
        for along in (43, 74):
            comb = box(2, 8.6, 1.8, (along - 1, -4.3, FLOOR))
            for lateral in (-2.4, 0, 2.4):
                comb = comb.cut(cylinder(.95, 3, (along - 1.5, lateral, 4.1), (1, 0, 0)))
            base = base.fuse(comb.rotate((0, 0, 0), (0, 0, 1), 45))
        for angle in (15, 75):
            a = math.radians(angle)
            base = base.fuse(cylinder(1.1, 2.30, (21 * math.cos(a), 21 * math.sin(a), FLOOR)))
    return base.clean()


def tower(cutaway):
    flange = annulus(18.55, 23.05, 1.2, TOP)
    shell = annulus(20.3, 21.3, 18, TOP + 1.2)
    heads = []
    for i in range(48):
        a = math.radians((i + .5) * 360 / 48)
        for r in (19.6, 22.0):
            x, y = r * math.cos(a), r * math.sin(a)
            heads.append(cq.Workplane("XY").workplane(offset=TOP + 1.2)
                         .center(x, y).polygon(6, 1.05).extrude(.65).val())
    shape = fuse([flange, shell, *heads])
    return retained(shape) if cutaway else shape


def anchor_cage():
    z = 5.30
    bottom = sector(18.55, 23.05, 1.0, z)
    top = sector(18.55, 23.05, 1.2, TOP)
    rods, heads = [], []
    for i in range(12):
        a = math.radians((i + .5) * 7.5)
        for r in (19.6, 22.0):
            x, y = r * math.cos(a), r * math.sin(a)
            rods.append(cylinder(.5, TOP - z, (x, y, z + .1)))
            heads.append(cq.Workplane("XY").workplane(offset=TOP + 1.2)
                         .center(x, y).polygon(6, 1.05).extrude(.65).val())
    return fuse([bottom, top, *rods, *heads])


def bottom_mat():
    # All mats and shear frames share these exact radii and radial axes.
    bars = [sector(r - .6, r + .6, MAT_THICKNESS, MAT_Z, 4.4, 85.6) for r in REBAR_RADII]
    for deg in REBAR_ANGLES:
        a = math.radians(deg)
        bars.append(flat_bar((33 * math.cos(a), 33 * math.sin(a)),
                             (78 * math.cos(a), 78 * math.sin(a))).translate((0, 0, MAT_Z)))
    return fuse(bars)


def shear_frame(angle):
    # A flat-printable carrier sits directly ON the lower radial bar. Rounded
    # hairpins straddle selected ring intersections and support the upper mat.
    # The carrier is a print aid, not an extra structural bar from the drawing.
    floor = MAT_Z + MAT_THICKNESS
    parts = [flat_bar((REBAR_RADII[0], floor + .45), (REBAR_RADII[-2], floor + .45), depth=1.2, width=.9)]
    for r in (REBAR_RADII[1], REBAR_RADII[3], REBAR_RADII[4]):
        cap_top = upper_rebar_z(r) - UPPER_THICKNESS / 2 - .08
        bend, bar = 1.4, .9
        center_z = cap_top - bend - bar / 2
        curved = (cq.Workplane("XY").center(r, center_z).circle(bend + bar / 2)
                  .circle(bend - bar / 2).extrude(1.2).val()
                  .intersect(box(8, 5, 2, (r - 4, center_z, -.1))))
        parts.append(curved)
        for side in (-1, 1):
            parts.append(box(bar, center_z - floor + .05, 1.2,
                             (r + side * bend - bar / 2, floor, 0)))
    return (fuse(parts).rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((0, .6, 0)).rotate((0, 0, 0), (0, 0, 1), angle))


def upper_panel(start, stop):
    # One planar facet between shared radial axes. Four facets approximate the
    # cone, enabling every upper panel to print flat without disposable supports.
    mid = math.radians((start + stop) / 2)
    half = math.radians((stop - start) / 2)
    slope = -2.0 * K / (R - RP)
    stretch = math.hypot(math.cos(half), slope)
    xdir = cq.Vector(math.cos(half) * math.cos(mid), math.cos(half) * math.sin(mid), slope).normalized()
    tangent = cq.Vector(-math.sin(mid), math.cos(mid), 0)
    normal = xdir.cross(tangent)
    plane = cq.Plane(origin=(0, 0, upper_rebar_z(0)), xDir=xdir, normal=normal)
    rails = []
    for r in REBAR_RADII:
        rails.append(flat_bar((r * stretch, -r * math.sin(half)),
                              (r * stretch, r * math.sin(half)), depth=UPPER_THICKNESS))
    for sign in (-1, 1):
        rails.append(flat_bar((33 * stretch, sign * 33 * math.sin(half)),
                              (78 * stretch, sign * 78 * math.sin(half)), depth=UPPER_THICKNESS))
    shape = fuse(rails).translate((0, 0, -UPPER_THICKNESS / 2)).transformShape(plane.rG)
    # Miter the shared radial seams. Each mating edge retains a printable half
    # width of the 1.2 mm rail; assembled adjacent panels do not overlap.
    a, b = math.radians(start), math.radians(stop)
    wedge = (cq.Workplane("XY").workplane(offset=-10).polyline(
             [(0, 0), (130 * math.cos(a), 130 * math.sin(a)),
              (130 * math.cos(b), 130 * math.sin(b))]).close().extrude(70).val())
    shape = shape.intersect(wedge).clean()
    axis = normal.cross(cq.Vector(0, 0, 1)).normalized().toTuple()
    angle = math.degrees(math.acos(normal.z))
    return shape, [(axis, angle)]


def duct(lateral):
    # Schematic route matching the drawing's vertical drop, bend and outward
    # run. Three visible conduits represent the bundle; d=1.6 mm for PLA.
    radius = 7
    path = (cq.Workplane("XZ").moveTo(7, 21.5).lineTo(7, 11.1)
            .threePointArc((14 - radius / math.sqrt(2), 11.1 - radius / math.sqrt(2)), (14, 4.1))
            .lineTo(81, 4.1).wire())
    tube = cq.Workplane("XY", origin=(7, 0, 21.5)).circle(.8).sweep(path).val()
    # Flat back face improves bed adhesion when the tube is printed on its side.
    tube = tube.intersect(box(100, 1.5, 40, (0, -.7, 0)))
    return tube.translate((0, lateral, 0)).rotate((0, 0, 0), (0, 0, 1), 45)


def mesh(shape):
    verts, faces = shape.tessellate(.04, .12)
    return trimesh.Trimesh(np.asarray([v.toTuple() for v in verts]), np.asarray(faces), process=True)


def register(name, shape, color, note, flat_rotation=None):
    log("Export " + name)
    if not shape.isValid():
        raise ValueError("Invalid CAD shape: " + name)
    solids = len(shape.Solids())
    if solids != 1:
        raise ValueError(f"{name}: expected one connected solid, found {solids}")
    oriented = shape
    if flat_rotation:
        for axis, angle in flat_rotation:
            oriented = oriented.rotate((0, 0, 0), axis, angle)
    bb = oriented.BoundingBox()
    oriented = oriented.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))
    path = OUT / "print" / (name + ".stl")
    cq.exporters.export(oriented, str(path), tolerance=.025, angularTolerance=.10)
    check = trimesh.load_mesh(path)
    dims = check.extents
    if not check.is_watertight or not check.is_winding_consistent or check.volume <= 0:
        raise ValueError("Invalid print mesh: " + name)
    if max(dims) > 174:
        raise ValueError("Part exceeds reserved A1 mini footprint: " + name)
    PARTS[name] = {"shape": shape, "color": color, "note": note,
                   "dimensions_mm": [round(float(x), 3) for x in dims],
                   "volume_mm3": round(float(check.volume), 3),
                   "watertight": bool(check.is_watertight), "cad_solids": solids}


def export_assembly(name, names):
    assembly = cq.Assembly(name=name)
    scene = trimesh.Scene()
    for part in names:
        p = PARTS[part]
        color = COLORS[p["color"]]
        assembly.add(p["shape"], name=part, color=cq.Color(*color))
        m = mesh(p["shape"])
        m.visual.vertex_colors = [int(c * 255) for c in color] + [255]
        scene.add_geometry(m, node_name=part, geom_name=part)
    assembly.export(str(OUT / (name + ".step")))
    scene.export(str(OUT / (name + ".glb")))
    ASSEMBLIES[name] = names


def main():
    (OUT / "print").mkdir(parents=True, exist_ok=True)
    for cut in (False, True):
        prefix = "cutaway" if cut else "closed"
        upper, lower = concrete_parts(cut)
        register(prefix + "_base", display_base(cut), "base", "Print flat; 3 mm brim optional.")
        register(prefix + "_concrete", upper, "concrete", "Flat underside down, as exported.")
        register(prefix + "_lower_center", lower, "concrete", "Pins up. The 45-degree sides need no supports.")
        register(prefix + "_tower", tower(cut), "tower", "Flange down; print separately and glue to pedestal.")
    register("cutaway_anchor_cage", anchor_cage(), "steel",
             "Upright. Small bridges between rods support the top ring; inspect in slicer.")
    register("cutaway_bottom_rebar", bottom_mat(), "steel", "Flat connected mat; glue above base.")
    reinforcement = []
    for i, angle in enumerate(REBAR_ANGLES, 1):
        name = f"cutaway_shear_frame_{i}"
        register(name, shear_frame(angle), "steel", "Print flat. Carrier glues directly onto the matching lower radial bar.",
                 [((0, 0, 1), -angle), ((1, 0, 0), -90)])
        reinforcement.append(name)
    for i, (start, stop) in enumerate(zip(REBAR_ANGLES, REBAR_ANGLES[1:]), 1):
        name = f"cutaway_upper_rebar_{i}"
        panel, orientation = upper_panel(start, stop)
        register(name, panel, "steel", "Print flat. Glue onto hairpin crowns; seams follow the shared radial axes.", orientation)
        reinforcement.append(name)
    for i, offset in enumerate((-2.4, 0, 2.4), 1):
        register(f"cutaway_duct_{i}", duct(offset), "duct", "Flat back down; glue in base saddles.",
                 [((0, 0, 1), -45), ((1, 0, 0), 90)])
    closed = ["closed_" + p for p in ("base", "lower_center", "concrete", "tower")]
    cutaway = ["cutaway_" + p for p in ("base", "lower_center", "concrete", "tower",
               "anchor_cage", "bottom_rebar", "duct_1", "duct_2", "duct_3")] + reinforcement
    export_assembly("closed_display_1-160", closed)
    export_assembly("cutaway_display_1-160", cutaway)
    report = {"scale": SCALE, "foundation_diameter_mm": R * 2,
              "base_diameter_mm": BASE_R * 2, "printer": "Bambu Lab A1 mini",
              "reinforcement_grid": {"radii_mm": REBAR_RADII, "angles_deg": REBAR_ANGLES,
                                      "lower_mat_top_z": MAT_Z + MAT_THICKNESS,
                                      "shear_frame_bottom_z": MAT_Z + MAT_THICKNESS,
                                      "upper_mat": "four flat-printable facets; seams on shared radial axes"},
              "parts": {n: {k: v for k, v in p.items() if k != "shape"} for n, p in PARTS.items()},
              "assemblies": ASSEMBLIES}
    (OUT / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    log("Display exports complete")


if __name__ == "__main__":
    main()
