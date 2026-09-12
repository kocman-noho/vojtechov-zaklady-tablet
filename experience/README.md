# Beneath — E-175 foundation explorer

An interactive Three.js experience built around the supplied detailed foundation and turbine. Source CAD, printable models and the original OBJ remain unchanged.

## Run

Requires Node.js 22.12+.

```sh
cd experience
npm ci
npm run dev
```

Open http://localhost:5173. The app bundles its dependencies and assets locally; no CDN, online fonts, model service or API key is needed at runtime.

The interface follows the NOHO brand (noho.cz/brand-centrum): dark blue `#003366`, cream `#efeae2`, green `#249e6b` and lime `#cedc00`, set in Styrene A. The licensed Styrene A woff2 files live in `public/fonts/`; the source OTFs are not part of this repository. The 3D canvas fills the whole stage and the intro, comparison panel and controls float over it.

```sh
npm run build
npm run preview
```

`dist/` is a standalone static-site build. Serve it over HTTP(S), rather than opening `index.html` directly from disk. The loader accepts either ordinary binary delivery of `.glb.gz` or a server-provided `Content-Encoding: gzip` header, detecting whether the browser has already decompressed the data. Modern browsers with WebGL 2 and DecompressionStream are required.

## Explore

- **Základ:** actual-size reference geometry in a quarter cutaway.
- **Rozložení:** animated separation, a manual slider and component visibility. The explosion is explanatory, not a construction sequence.
- **Celá elektrárna:** supplied turbine with its simplified foundation removed and fitted to the foundation's 132 m hub-height configuration.

- Toggle the supplied **Ivan**, **Marina**, **2016 Škoda Kodiaq** and **family house** independently. All stand at the ground level outside the soil opening and the separated concrete's position. People retain their source proportions (approximately 1.88 m and 1.75 m); the car is uniformly scaled to 4.697 m long. The replacement `model_dom_2.3DS` house is approximately 9.08 m tall and 13.70 × 13.66 m across, including roof and steps. Source units are interpreted as inches from architectural proportions, so its scale is illustrative. Its corrupted site terrain is excluded, and below-grade footings are clipped at source z=0.
- Drag to orbit, scroll/pinch to zoom, right-drag to pan. Camera controls include reset, top view, zoom and automatic rotation. With the canvas focused: arrow keys orbit, `+`/`-` zoom, `R` resets. Escape dismisses the notes dialog.

The bigger picture hides all comparison objects and the comparison/layer panels. Returning to either foundation chapter restores the previous comparison selections, including a house still downloading when the chapter changed. A direct `#scale` link skips comparison downloads until they are needed.

The comparison assets are local Draco-compressed GLBs in `public/models/comparisons/`. The house downloads on first selection; toggling a loaded object reuses its meshes and textures. A failed comparison download leaves the foundation usable and its toggle offers a retry. The Draco WASM decoder is bundled locally and limited to two workers. Colour atlases are capped at 2K, other maps at 1K, with mipmaps and capped anisotropic filtering. Rendering remains on demand when the camera and scene are still.

The Czech interface uses a full-screen 3D canvas with two floating bars. Camera controls and model notes sit in the top bar; chapters, comparisons and layers sit in the bottom bar. The separation slider appears in Rozložení. Sidebar headlines, explanatory panels and the extra footer are removed; model tags and dimensions remain visible, using Czech text and decimal commas. Longer explanations and gesture instructions are available in O modelu. Controls have at least 44 px touch targets; one finger orbits, two fingers pan, and pinching zooms. Resizing preserves the user's orbit and adapts framing. The page follows dynamic viewport height and safe-area insets; touch rendering is capped at 1.5× pixel density.

Car and house material definitions were missing or blank in the supplied exports. Their finishes were reconstructed, using the supplied car badge, timber and paving textures. The people retain their diffuse and normal maps and all source triangles. Car paint, glazing and lamps retain their original topology and normals for smooth reflections; tyres, trim and metal are simplified, with normals rebuilt after reduction. A small generated lighting environment provides reflections on paint, glazing and metal without an external HDR download.

`public/models/comparisons/provenance.json` records source hashes, triangle counts, byte sizes, dimensions and scale assumptions. Originals stay in Downloads and are never modified or copied into the public build. The exports did not include original license documents; the generated derivatives retain the source assets' reuse terms.

## Geometry and provenance

`public/models/provenance.json` records source files, conversion, bounds and mesh counts. `accuracy.json` preserves the original reference-model limitations. The in-app Sources & model notes panel explains these to viewers.

The foundation derives from `../models/output/reference/cutaway_reference_1-160.glb`, not the enlarged printable model. The CAD 1:160 millimetres are converted to full-size metres, with Y up and the pedestal top at zero. Foundation dimensions are 26.6 m diameter and 3.2 m maximum concrete depth. Interior reinforcement is retained in the exposed quadrant, as in the existing model preview, while anchor components retain their source geometry. The browser copy preserves the reference triangulation. Generic decimation was unsuitable for the CAD seams, so download size is reduced with quadrant filtering and gzip instead.

The turbine OBJ has no reliable real-world unit metadata and is labelled “172 m rotor”. The browser derivative is calibrated to the [manufacturer's 175 m rotor specification](https://www.enercon.de/en/turbines/e-175-ep5). The tower's middle span is adapted to 132 m hub height and its base shell to the foundation's 6.7 m connection diameter; the nacelle and rotor translate rigidly. This visual fit is not a supplier-approved HST-132 tower reconstruction. The supplied simplified footing and 15 detached blade-tip fittings (2,184 triangles) are removed from the derivative, never the source file. The original tapered blade shells remain intact; rotor calibration uses their radius, excluding those fittings. The tip boxes were present in the original OBJ, not introduced by browser optimization.

The app labels the project “Vojtěchov, CZ” from the workspace context; the ground uses the drawing’s −0.15 m backfill level, and every comparison object stands on it. An illustrative soil opening reveals the foundation; the exposed quadrant extends to −4.05 m to clear the ducts, while the other quadrants meet the concrete’s −3.20/−2.70 m underside. Its opening dimensions, bank slopes and soil appearance are presentation choices, not an excavation design or surveyed terrain. The concrete lifts above the ground before translating sideways during deconstruction. The 759 m³ concrete volume is the supplied drawing's figure, not a new calculation. The Kodiaq length comes from [Škoda's 2016 press kit](https://www.skoda-storyboard.com/en/press-kits/skoda-kodiaq-paris-press-kit-2016/); width includes the source model's mirrors.

The concrete surface uses the supplied `Modern House_01_TEXTURE (4).jpg`, reduced to a 1K JPEG in `public/textures/`. Object-space triplanar sampling blends across the curved body and cut faces at 3 m per tile. Subtle colour, roughness and 3 mm-scaled bump variation add detail without changing the CAD mesh. The texture stays attached during deconstruction, uses mipmaps, and falls back to plain concrete if unavailable.

The new house has no image maps in its 3DS file. Its named material regions are rebuilt as plaster, clay tiles, linen, glazing and metal, with timber and stone textures from the supplied house ZIP. Dense curtains are simplified while roof tile geometry is preserved to avoid damaged edges. The house remains an optional, cached download.

## Rebuild browser assets

The generated assets are committed with the app; Python is only needed to regenerate them.

```sh
python -m venv /tmp/foundation-venv
/tmp/foundation-venv/bin/pip install numpy scipy trimesh pillow
/tmp/foundation-venv/bin/python scripts/prepare_models.py
```

To regenerate only the turbine after tip cleanup, run `python scripts/prepare_turbine.py`. Its source-specific checks verify exactly 15 detached tip components before removing them.

Paths are resolved relative to this script and the existing source-model folders. Expect the original reference GLB to require appreciable memory while processing.

To rebuild the comparison models, install Pillow and libarchive and use Blender 4.3+ with its glTF exporter:

```sh
python scripts/prepare_comparisons.py --downloads ~/Downloads --blender /path/to/blender
```

The script uses the Kodiaq OBJ and `textures.rar`, Ivan/Marina OBJs and their texture RARs, the original house Blender and scanline ZIPs, then replaces that house with `model_dom_2.3DS`. It stages archives in a temporary directory, converts geometry and textures, records provenance, and copies the matching Draco decoder from the installed Three.js package. Committed GLBs and decoders are sufficient for ordinary builds; Blender is not a runtime dependency.

To rebuild just the replacement house, run `python scripts/prepare_house_3ds.py --blender /path/to/blender`. The script leaves Downloads originals untouched.

## Verification

With the dev server running and Google Chrome installed:

```sh
npm test
```

Set `CHROME_PATH` to another Chromium executable or `PREVIEW_URL` to a different server address. The Playwright check verifies model loading, dimensions, all three chapters, explosion, play/pause, component toggles, comparison toggles, reset, dialog keyboard behavior and mobile overflow. It saves screenshots to `artifacts/` and reports browser errors. Tests use software WebGL for portability; hardware GPU performance varies by device.

Comparison loading checks: `node scripts/check-comparisons.mjs` verifies independent toggles, lazy loading, caching, failed-download recovery, toggling during a pending request, all four ground contacts, mobile controls and the 5 MB asset budget. Set `PREVIEW_URL` to run it against a production or nested-path build.

Tablet checks: `PREVIEW_URL=http://127.0.0.1:4175 node scripts/check-ipad.mjs` exercises direct full-picture loading, comparison isolation/restoration, touch controls, orientation changes, eight iPad viewport sizes, touch targets, Czech labels and the two floating bars. It uses Chromium touch emulation and saves screenshots in `artifacts/`; real iPad Safari and hardware frame rates still require device testing.

Blade-tip geometry checks: `python scripts/check-turbine.py` verifies three intact blade tips on the 175 m rotor circle, the 132 m hub, tower contact and absence of detached tip fittings.

Ground-cutaway checks: `node scripts/check-terrain.mjs` verifies the soil surface, duct clearance and support profile without a browser. With the production build served at port 4173, `node scripts/check-ground.mjs` checks comparison-object elevations, exploded concrete clearance, desktop/mobile rendering and browser errors.
