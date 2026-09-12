"""Full-size, unexaggerated reference geometry (mm), plus uniform 1:160 copies.

This is a dimensioned visualization, not a fabrication-complete rebar model.
Every inference/omission is recorded in reference/accuracy.json.
"""
from pathlib import Path
import json
import math
import re
import subprocess

import cadquery as cq
import numpy as np
import trimesh

from build_models import annulus, box, cylinder, revolved, log

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "reference"
SCALE = 160
SOURCE = next(ROOT.parent.glob("D02888981*.pdf"))


def compound(shapes):
    return cq.Compound.makeCompound(list(shapes))


def schedule():
    raw = subprocess.check_output(["pdftotext", "-raw", str(SOURCE), "-"], text=True)
    rows = []
    for line in raw.splitlines():
        m = re.fullmatch(r"(1\d\d) (20|25) (\d+) (\d+) (\d+) ([\d.]+) ([\d.]+) ([\d.]+)", line.strip())
        if m and 100 <= int(m[1]) <= 166:
            rows.append({"position": int(m[1]), "diameter_mm": int(m[2]),
                         "rings": int(m[3]), "segments_per_ring": int(m[4]),
                         "segments_total": int(m[5]), "arc_length_mm": float(m[6]) * 1000,
                         "radius_mm": float(m[7]) * 1000, "lap_mm": float(m[8]) * 1000})
    assert len(rows) == 67 and len({r["position"] for r in rows}) == 67
    return rows


def underside(r):
    return -3200 if r <= 4400 else (-2700 if r >= 4900 else -3200 + r - 4400)


def concrete():
    # Section A-A; top at r=4400 is -50, whereas backfill level is -150.
    return revolved([(0, 0), (3615, 0), (4400, -50), (4400, -400),
                     (13300, -2400), (13300, -2700), (4900, -2700),
                     (4400, -3200), (0, -3200)])


def rings(rows):
    shapes = []
    for row in rows:
        radius, dia = row["radius_mm"], row["diameter_mm"]
        for layer in range(row["rings"]):
            # 50 mm cover, then alternating 25 mm radial / ring layers.
            # Exact placement needs the complete coordinated reinforcement set.
            z = underside(radius) + 50 + 25 + dia / 2 + layer * (25 + dia)
            shapes.append(cq.Solid.makeTorus(radius, dia / 2, cq.Vector(0, 0, z)))
    return compound(shapes)


def radial_subset():
    shapes = []
    # Straight-bar groups whose quantities, diameters and lengths are explicit
    # in the supplied bending diagrams. Start radii/phase are inferred.
    for pos, count, dia, length, layer in [(5, 120, 25, 9550, 1), (6, 240, 10, 2100, 1),
                                          (7, 120, 25, 8500, 3), (8, 120, 25, 6200, 3),
                                          (9, 120, 25, 8500, 5)]:
        end = 13200 if pos != 8 else 10900
        z = -2700 + 50 + dia / 2 + (layer - 1) * 25
        for i in range(count):
            a = 2 * math.pi * (i + (.5 if pos in (6, 8) else 0)) / count
            shapes.append(cylinder(dia / 2, length,
                          ((end - length) * math.cos(a), (end - length) * math.sin(a), z),
                          (math.cos(a), math.sin(a), 0)))
    return compound(shapes)


def top_surface(r):
    if r <= 3615:
        return 0
    if r <= 4400:
        return -50 * (r - 3615) / (4400 - 3615)
    return -400 - (r - 4400) * 2000 / 8900


def upper_reinforcement():
    """Section-derived upper mats; dimensions are not minimum-print-size clamped.

    Section gives diameters, group counts and spacings. Starting radius, phase,
    layer elevations and radial bar bends remain inferred without D02888982.
    """
    rings_list, radial_list = [], []
    # Section groups 300–348: 31 rings d16 @200, 12 d20 @170, 6 d25 @170.
    # Spacing interpreted along the sloping section, starting 100 mm inboard.
    projected = 1 / math.sqrt(1 + (2000 / 8900) ** 2)
    r = 13200.0
    for i in range(49):
        dia = 16 if i < 31 else (20 if i < 43 else 25)
        step = 200 if i < 31 else 170
        rings_list.append(cq.Solid.makeTorus(r, dia / 2, cq.Vector(0, 0, top_surface(r) - 50 - dia / 2)))
        # Secondary top layer. Sparse outer section / dense inner section in
        # the supplied section; exact correspondence to 400–433 is inferred.
        if i >= 20 or i % 3 == 0:
            rings_list.append(cq.Solid.makeTorus(r, dia / 2, cq.Vector(0, 0, top_surface(r) - 100 - dia / 2)))
        r -= step * projected
    # Pedestal top mats on both sides of the basket, with actual d25 bars.
    for center_r in [2280 + 170 * i for i in range(6)] + [3520 + 170 * i for i in range(6)]:
        for depth in (62.5, 112.5):
            rings_list.append(cq.Solid.makeTorus(center_r, 12.5, cq.Vector(0, 0, top_surface(center_r) - depth)))
    # Radial top bars d25: two 120-bar families, representative centerlines.
    # They follow the pedestal, drop and sloping upper face. Bends/lengths are
    # inferred, NOT asserted to reproduce complete bending schedules 10–12.
    for depth in (87.5, 137.5):
        path = (cq.Workplane("XZ").moveTo(2300, -depth)
                .lineTo(4300, top_surface(4300) - depth)
                .lineTo(4500, top_surface(4500) - depth)
                .lineTo(13200, top_surface(13200) - depth).wire())
        start_direction = cq.Vector(2000, 0, top_surface(4300)).normalized()
        profile = cq.Workplane(cq.Plane(origin=(2300, 0, -depth), normal=start_direction)).circle(12.5)
        bar = profile.sweep(path, transition="round").val()
        for i in range(120):
            radial_list.append(bar.rotate((0, 0, 0), (0, 0, 1), 3 * i + 1.5))
    return compound(rings_list), compound(radial_list), len(rings_list)


def through_depth_links():
    """Representative rounded U centerlines using d25/d10 and source ring counts.

    Heights/radial stations follow section groups 31–41. Hook tails and exact
    bends are omitted; the tangential orientation and phase are inferred.
    """
    parts = []
    stations = [(4650, 120, 25, 2000), (5880, 60, 25, 1710),
                (6860, 120, 25, 1510), (7840, 60, 25, 1280),
                (8820, 120, 25, 1060), (9800, 120, 25, 840),
                (10800, 120, 25, 610), (11800, 120, 10, 390),
                (12300, 120, 10, 370), (12800, 120, 10, 260)]
    for r, count, dia, height in stations:
        bottom, bend = -2600, 150
        apex = bottom + height
        path = (cq.Workplane("YZ", origin=(r, 0, 0)).moveTo(-bend, bottom)
                .lineTo(-bend, apex - bend)
                .threePointArc((0, apex), (bend, apex - bend)).lineTo(bend, bottom).wire())
        bar = cq.Workplane("XY", origin=(r, -bend, bottom)).circle(dia / 2).sweep(path).val()
        for i in range(count):
            parts.append(bar.rotate((0, 0, 0), (0, 0, 1), i * 360 / count))
    return compound(parts), len(parts)


def pedestal_reinforcement():
    parts = []
    # Explicit erection-ring table rows 803/804: R4040/R2410, d10, three each.
    for r in (2410, 4040):
        for z in (-700, -1100, -2150):
            parts.append(cq.Solid.makeTorus(r, 5, cq.Vector(0, 0, z)))
    # Section group 700: nine d10 internal rings at R2250, nominal 300 spacing.
    for i in range(9):
        parts.append(cq.Solid.makeTorus(2250, 5, cq.Vector(0, 0, -3050 + i * 300)))
    # d16 upright legs on either side of the basket, linked visually by hoops.
    # Locations, phase and straight simplification of bent legs are inferred.
    for r in (2410, 4040):
        for i in range(120):
            a = math.radians(3 * i + 1.5)
            parts.append(cylinder(8, 2930, (r * math.cos(a), r * math.sin(a), -3080)))
    return compound(parts)


def ducts():
    # DN100 corrugated conduits: drawing specifies OD160 / ID150, min R1500.
    # Routing/phase and termination levels are illustrative, not surveyed.
    path = (cq.Workplane("XZ").moveTo(900, 0).lineTo(900, -2050)
            .threePointArc((2400 - 1500 / math.sqrt(2), -2050 - 1500 / math.sqrt(2)), (2400, -3550))
            .lineTo(13300, -3550).wire())
    tube = cq.Workplane("XY", origin=(900, 0, 0)).circle(80).circle(75).sweep(path).val()
    return compound([tube.translate((0, (i - 3.5) * 220, 0)).rotate((0, 0, 0), (0, 0, 1), 45)
                     for i in range(8)])


def export_scene(groups, name, scale, preview=False):
    assembly = cq.Assembly(name=name)
    scene = trimesh.Scene()
    for label, shape, color in groups:
        s = shape if scale == 1 else shape.scale(1 / scale)
        assert s.isValid(), label
        assembly.add(s, name=label, color=cq.Color(*color))
        if preview:
            verts, faces = s.tessellate(.025, .16)
            m = trimesh.Trimesh(np.asarray([v.toTuple() for v in verts]), np.asarray(faces), process=True)
            # Translate only the visual copy to the same display datum.
            m.apply_translation([0, 0, 23])
            m.visual.vertex_colors = [int(c * 255) for c in color] + [255]
            scene.add_geometry(m, node_name=label, geom_name=label)
    log("Export " + name)
    assembly.export(str(OUT / (name + ".step")))
    if preview:
        scene.export(str(OUT / (name + ".glb")))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = schedule()
    body = concrete()
    rod_list = []
    # 2 x 120 M36 at the two explicitly dimensioned radii.
    for radius in (3213, 3440):
        for i in range(120):
            a = 2 * math.pi * i / 120
            rod_list.append(cylinder(18, 2896, (radius * math.cos(a), radius * math.sin(a), -2836)))
    rods = compound(rod_list)
    upper = annulus(3038, 3615, 100, -40)
    lower = annulus(3128, 3525, 50, -2836)
    # Holes follow nominal shafts; engineering clearances are not specified.
    upper = upper.cut(rods)
    lower = lower.cut(rods)
    service = ducts()
    log("Building upper mats, shear links and pedestal reinforcement")
    upper_rings, upper_radials, upper_ring_count = upper_reinforcement()
    links, link_count = through_depth_links()
    body = body.cut(upper).cut(lower).cut(service)
    # Uncut concrete for a closed exterior; rods/rebar are embedded components.
    cut = box(18000, 18000, 6000, (0, 0, -4500))
    common = [("anchor_rods_240_M36", rods, (.23, .29, .34)),
              ("top_flange_actual_dimensions", upper, (.47, .50, .52)),
              ("lower_anchor_ring_actual_dimensions", lower, (.35, .4, .43)),
              ("scheduled_lower_rings_inferred_layer_elevations", rings(rows), (.25, .31, .35)),
              ("partial_radial_groups_5_to_9_inferred_placement", radial_subset(), (.31, .36, .39)),
              ("upper_rings_section_derived_inferred_placement", upper_rings, (.25, .31, .35)),
              ("upper_radial_bars_d25_inferred_bends", upper_radials, (.31, .36, .39)),
              ("through_depth_shear_links_inferred_bends", links, (.29, .35, .39)),
              ("pedestal_rebar_and_hoops_inferred_placement", pedestal_reinforcement(), (.25, .31, .35)),
              ("ducts_OD160_ID150_R1500_inferred_route", service, (.91, .36, .08))]
    for version, concrete_shape in [("closed", body), ("cutaway", body.cut(cut))]:
        groups = [("concrete", concrete_shape, (.72, .73, .70)), *common]
        export_scene(groups, f"{version}_reference_1-1", 1)
        export_scene(groups, f"{version}_reference_1-160", SCALE, preview=True)
        cq.exporters.export(concrete_shape.scale(1 / SCALE),
                            str(OUT / f"{version}_concrete_unexaggerated_1-160.stl"),
                            tolerance=.025, angularTolerance=.1)
    # A full-detail scaled inspection STL, kept out of the printable-part folder.
    cq.exporters.export(compound([s for _, s, _ in common]).scale(1 / SCALE),
                        str(OUT / "internal_details_unexaggerated_1-160_VIEW_ONLY.stl"),
                        tolerance=.025, angularTolerance=.16)
    report = {"units": "mm", "full_size_scale": "1:1", "uniform_copy_scale": "1:160",
              "feature_enlargement": "none", "foundation_diameter_mm": 26600,
              "concrete_max_depth_mm": 3200,
              "gross_concrete_volume_m3": round(concrete().Volume() / 1e9, 3),
              "drawing_concrete_volume_m3": 759,
              "anchor_rod_count": len(rod_list), "anchor_rod_diameter_mm": 36,
              "anchor_rod_radii_mm": [3213, 3440], "scheduled_lower_ring_rows": rows,
              "included_lower_ring_count": sum(row["rings"] for row in rows),
              "partial_radial_groups": [5, 6, 7, 8, 9], "partial_radial_bar_count": 720,
              "upper_ring_count": upper_ring_count, "upper_radial_bar_count": 240,
              "through_depth_shear_link_count": link_count,
              "revision": "Added section-derived upper mats, shear links and pedestal reinforcement; no enlargement.",
              "source_verified": ["main concrete section dimensions", "240 M36 rods and their pitch radii",
                                  "top and lower anchor-ring radii and thicknesses", "67 lower ring schedule rows",
                                  "straight lower radial group quantities, diameters and lengths", "duct OD/ID and minimum bend radius",
                                  "upper/shear/pedestal bar diameters and arrangement categories visible in section"],
              "inferred": ["rebar layer elevations and exact start/phase of straight radial bars",
                           "duct route, bundle spacing and termination levels", "anchor rod angular phase",
                           "upper radial centerlines, upper ring starting radii/secondary-layer mapping",
                           "shear-link orientation and bend geometry; the two inner 60-count groups represented by one 120-count family",
                           "pedestal upright centerlines, hoop elevations and angular phase"],
              "omitted": ["fabrication-level reconciliation with unprovided upper plan D02888982", "remaining bent radial bars, hook tails and detailed shear-link bends",
                          "ring laps, tangents, staggering and bar ribs (rings modeled continuous)",
                          "rod protrusions beyond ring faces, nuts and threads; detailed supplier basket drawing absent",
                          "tower shell: wall thickness not established", "lightning clamps and backfill"],
              "scope": "Dimensioned visualization with actual-size details; not a complete fabrication or as-built model.",
              "print_warning": "Reference 1:160 has 0.125 mm diameter 20 mm rebar and 0.225 mm M36 shafts; not intended for a 0.4 mm nozzle."}
    (OUT / "accuracy.json").write_text(json.dumps(report, indent=2) + "\n")
    log("Unexaggerated reference exports complete")


if __name__ == "__main__":
    main()
