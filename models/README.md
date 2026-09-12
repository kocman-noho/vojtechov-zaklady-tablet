# E-175 foundation showcase

Two printable CadQuery display models for **PLA / Bambu Lab A1 mini / 0.4 mm nozzle**,
plus a separate full-size reference and uniformly scaled reference copies.

Open [the offline interactive preview](output/preview.html) in Chrome or Firefox.
It has Closed, Exposed and True-size details views, orbit/zoom, an exploded-view
slider, and a **Show upper reinforcement** toggle. It is self-contained; no
installation, server or internet connection is needed. Allow time for the detailed
reference geometry to load.
For browser performance, reference interior bar families are displayed only in
the exposed quadrant; STEP files retain the complete circular populations.

Revision 2 corrects the disconnected reinforcement presentation: a shared polar grid
now locates the lower mat, five shear-link carriers and four upper panels. The old
cut-face ladders and first print ZIP are preserved in `archive/revision1/`.

## Models

| Version | Scale | Purpose | Files |
|---|---|---|---|
| Closed display | 1:160 | Complete concrete exterior with short tower stub | `output/closed_display_1-160.step` |
| Exposed display | 1:160 | Quarter cutaway with steel and cable ducts | `output/cutaway_display_1-160.step` |
| Closed reference | 1:1, mm | Full-size dimensioned geometry, actual-sized details | `output/reference/closed_reference_1-1.step` |
| Cutaway reference | 1:1, mm | Full-size cutaway exposing actual-sized details | `output/reference/cutaway_reference_1-1.step` |
| Uniform reference copies | 1:160 | Same reference geometry scaled uniformly, no enlarged details | `output/reference/*_reference_1-160.step` |

The printable foundation is **166.25 mm diameter**; its base is **172 mm diameter**.
The actual 3.2 m maximum concrete depth becomes 20 mm. The display includes a
3 mm base floor and an illustrative short tower stub; assembled height is about 42 mm.
The 172 mm base leaves 4 mm per side on the A1 mini's 180 mm bed. A 3 mm brim fits;
do not let the slicer add a large skirt or brim outside the plate.

“Closed” means a complete concrete foundation exterior, without a soil covering.
“Exposed” means a 90-degree opening through the concrete, showing representative
internal components. Both are foundation showcase models, not complete turbines.

## Printing

Import the **individual STLs in `output/print/`** at 100% scale. They are already
in millimetres, at 1:160, centered, with the intended printing face on Z=0.
The STEP assemblies and GLBs show assembled coordinates; they are for CAD/review,
not a single combined print. No AMS is needed: print colors separately and glue.

Start with the A1 mini 0.4 nozzle / Generic PLA / **0.16 mm Optimal** profile.
Use 0.12 mm layers if you want a smoother cone and flange. For the large concrete
parts, 3 walls and approximately 12–15% infill are reasonable starting settings.
Keep small-feature cooling enabled and inspect the slender cage in layer preview.

| Part | Count | Suggested color | Orientation / support |
|---|---:|---|---|
| `closed_base` | 1 | Graphite | Exported flat face down; optional 3 mm brim |
| `closed_concrete` | 1 | Light gray | Flat split face down; no supports intended |
| `closed_lower_center` | 1 | Light gray | Pins up; 45-degree sides |
| `closed_tower` | 1 | Ivory | Flange down |
| `cutaway_base` | 1 | Graphite | Flat face down; includes duct saddles |
| `cutaway_concrete` | 1 | Light gray | Flat split face down |
| `cutaway_lower_center` | 1 | Light gray | Pins up |
| `cutaway_tower` | 1 | Ivory | Flange down |
| `cutaway_anchor_cage` | 1 | Dark gray | Upright; short top-ring bridges between rods |
| `cutaway_bottom_rebar` | 1 | Dark gray | Flat connected mat |
| `cutaway_shear_frame_1` through `_5` | 1 each | Dark gray | Print flat; glue onto the five lower radial bars |
| `cutaway_upper_rebar_1` through `_4` | 1 each | Dark gray | Print flat; assemble inclined over the rounded links |
| `cutaway_duct_1`, `_2`, `_3` | 1 each | Orange | Flat backs down; three individual tubes |

The cage is the most delicate component. Print it first to check the 1 mm rods
and short bridges on your PLA/profile. It has passed a slicer check, but has not
been physically printed. Temperature, adhesion and fit still depend on your setup.
The rods are joined at both ends; handle the cage by its rings.

## Assembly

1. Glue the lower center to the main concrete piece using its two locating pins.
   Sockets have 0.4 mm diametral clearance and 0.3 mm extra depth.
2. Dry-fit the concrete on its matching base. The sloping well locates the deeper
   center; the rim locates the foundation perimeter with 0.3 mm radial clearance.
3. For the exposed version, fit the three orange ducts in the base saddles before
   installing the reinforcement. Their upright ends emerge inside the anchor cage.
4. Glue the cage's lower ring onto the two small base posts. Its open ends align
   with the concrete cut faces. Glue the bottom reinforcement mat onto the base.
5. Glue the five shear-frame carrier strips **onto the lower radial bars**, in
   increasing angular order (5°, 25°, 45°, 65°, 85°). All five frames have the same
   profile. Their lower faces sit on the mat's top face, at Z=7.425 mm. Their rounded
   hairpins straddle shared ring positions at radii 40.5, 55.5 and 63 mm.
6. Fit the four upper panels between adjacent frames, following the cone's slope.
   The panel joints follow the same radial axes. Use small glue dots on the hairpin
   crowns; a nominal 0.08 mm allowance helps seating. The outermost thin bay has
   no carrier below it. The upper panels can be glued together as a removable cap
   instead of fixed to the frames, to demonstrate the reinforcement beneath.
7. Glue the tower flange onto the pedestal. In the exposed version, its opening
   aligns with the cutaway cage. Fix the concrete to the base after checking fit.

Small dots of adhesive are sufficient. The parts are locating/glue fits, not
force-fit connectors. The exploded preview shows component separation for inspection;
it is not a literal sequence of vertical assembly motions.

## What is exact, and what is simplified?

Main geometry comes from section A-A in **D02888980**, including the 26.6 m outside
diameter, 8.8 m pedestal, -0.05 m pedestal edge, -0.40 m start of the main slope,
-2.40/-2.70 m outer edge and -3.20 m central underside. The -0.15 m line is the
backfill level. The reconstructed gross concrete volume is 758.119 m³ versus the
drawing's listed 759 m³; this is a close geometric reconstruction, not an exact
volume match to the original CAD.

The **display** enlarges/simplifies the steel: 1 mm anchor shafts, 1.2 mm lower mat,
0.9 mm upper panel thickness and hairpin bar width, two rows of 48 illustrative bolt positions around the full flange, a
slightly widened flange/bolt pattern, 1 mm tower wall, and three 1.6 mm ducts.
The mats share radii 33, 40.5, 48, 55.5, 63, 70.5 and 78 mm, and radial axes
5°, 25°, 45°, 65° and 85°. The lower rings are curved; upper rings are approximated
by four 20° chord segments so their panels print flat. Their endpoints match the
same grid. The five carrier strips keep the U-shaped shear-link representations
printable as connected pieces; these strips are print aids, not extra documented
structural bars. This remains a sparse illustrative cage, not literal bar scheduling.
The base is a presentation cradle,
not a representation of soil, blinding or EPS. Ducts are raised into a visible
base trench. These adjustments make the display manufacturable and readable.

The **reference has no feature enlargement**. It is built independently in actual
millimetres and then uniformly scaled for the 1:160 copies. It includes:

- All **240 M36 nominal shafts**, at the two dimensioned radii 3213 and 3440 mm.
- Dimensioned top flange and lower anchor ring, including their radii and thicknesses.
- **107 lower reinforcing rings**, from all 67 schedule rows 100–166, using the
  specified diameters, radii and ring counts.
- **720 straight radial bars**, the documented subset of groups 5–9, with their
  actual quantities, diameters and lengths.
- **Upper circumferential and radial reinforcement**, following the sloping face
  and pedestal, using section-derived d16/d20/d25 bar sizes. The added upper radial
  families contain 240 d25 bars. Starting radii, layer mapping and bends are inferred.
- **Through-depth shear links** at ten radial stations, using d25/d10 sizes and
  the section's nominal height/count families. Rounded U centerlines omit detailed
  hooks; exact orientation and bends are inferred.
- **Pedestal reinforcement**: d16 upright legs, d10 internal rings and erection
  hoops. These are distinct from the M36 tower anchor basket. Heights/phase and
  straight simplification of bent legs are inferred.
- Eight conduits with the duct plan's **160 mm outside / 150 mm inside diameter**
  and **1500 mm bend radius**.

It is **not a fabrication-complete reinforcement model**. Exact layer elevations,
radial-bar start radii/phase and duct routing are inferred and explicitly recorded.
Rings are continuous circles; lap splices/tangents/staggering are omitted. Remaining bent
bars, exact hook tails, nuts, threads and unestablished rod protrusions are omitted.
The separate upper reinforcement plan D02888982 and the supplier's detailed basket
drawing are not in this workspace. The supplied lower sheet nevertheless **does show
upper reinforcement and through-depth links in its section**, which is the basis
for this revision's reconstruction. It should never have been presented as bottom
reinforcement only. A tower shell is omitted from the reference
because its wall thickness was not established. See the full machine-readable
[accuracy record](output/reference/accuracy.json).

At 1:160, real 20 mm bars are **0.125 mm**, M36 shafts are **0.225 mm**, and the
conduit wall is **0.03125 mm**. The reference exports deliberately retain those
sizes. They belong in CAD or the viewer, not in the 0.4 mm PLA printing workflow.
Reference STL files are kept out of the printable folder. Their full interiors
contain embedded/touching components and are not a single fused printable solid.

## Validation and reproduction

`output/validation.json` records per-part CAD validity, one-solid connectivity,
watertight mesh checks, dimensions and volume. `output/assembly_checks.json` records
pairwise interference checks on reimported STEP assemblies. `output/slicing_validation.json`
records actual OrcaSlicer checks with the A1 mini / 0.16 mm / Generic PLA profiles.
`output/reinforcement_seating.json` checks that each shear carrier actually touches
the lower mat and comes within 0.15 mm of the upper panels for gluing.
These are digital checks, not a physical print or structural verification.

Source files:

- `build_models.py`: printable display geometry and exports.
- `build_reference.py`: actual-size reference and its source/assumption records.
- `make_viewer.py` + `viewer_template.html`: self-contained offline WebGL viewer.
- `render_preview.py`: local Blender renders of the generated geometry.
- `validate_exports.py`: assembly and optional slicer checks.

The local environment used CadQuery 2.8.0, trimesh 4.12.2 and Blender 5.2.1.

```bash
python3 models/build_models.py
python3 models/build_reference.py
python3 models/make_viewer.py
python3 models/validate_exports.py
# Optional: point to an extracted/local OrcaSlicer AppRun and its resources:
python3 models/validate_exports.py --slicer /path/to/OrcaSlicer/AppRun
```

Do not change only `SCALE` in the display script for a new printer: the deliberately
fixed printing details and base must be reviewed along with the scale. The reference
script has an independent full-size model and a uniform export scale.

Printer build volume/nozzle were checked against [Bambu Lab's A1 mini specifications](https://us.store.bambulab.com/products/a1-mini).
The local implementation uses [CadQuery's assembly/export capabilities](https://cadquery.readthedocs.io/en/latest/classreference.html).
