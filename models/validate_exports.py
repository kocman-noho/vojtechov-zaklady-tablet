"""Check assembly interference and optionally slice every display STL locally."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import itertools
import json
import subprocess

import cadquery as cq

OUT = Path(__file__).resolve().parent / "output"


def interference():
    results = {}
    for name in ("closed_display_1-160", "cutaway_display_1-160"):
        solids = cq.importers.importStep(str(OUT / (name + ".step"))).val().Solids()
        hits = []
        for i, j in itertools.combinations(range(len(solids)), 2):
            volume = solids[i].intersect(solids[j]).Volume()
            if volume > .02:
                hits.append({"solid_indices": [i, j], "overlap_mm3": round(volume, 5)})
        results[name] = {"solid_count": len(solids), "interferences": hits}
    (OUT / "assembly_checks.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2), flush=True)
    if any(v["interferences"] for v in results.values()):
        raise ValueError("Assembly interference found")


def reinforcement_seating():
    # Regression check for the reported disconnected/misaligned display cage:
    # every carrier must physically seat on the lower mat and meet the upper
    # panels within the intended small adhesive allowance.
    from build_models import bottom_mat, shear_frame, upper_panel, REBAR_ANGLES
    lower = bottom_mat()
    upper = cq.Compound.makeCompound([upper_panel(a, b)[0] for a, b in zip(REBAR_ANGLES, REBAR_ANGLES[1:])])
    checks = []
    for angle in REBAR_ANGLES:
        frame = shear_frame(angle)
        lower_gap, upper_gap = frame.distance(lower), frame.distance(upper)
        checks.append({"angle_deg": angle, "lower_seating_gap_mm": round(lower_gap, 6),
                       "upper_seating_gap_mm": round(upper_gap, 6)})
        assert lower_gap < .00001, f"Floating lower carrier at {angle} degrees"
        assert upper_gap < .15, f"Disconnected upper mat at {angle} degrees"
    (OUT / "reinforcement_seating.json").write_text(json.dumps(checks, indent=2) + "\n")
    print("Reinforcement seating: PASS", flush=True)


def slicing(slicer):
    resources = slicer.parent / "resources" / "profiles" / "BBL"
    check_root = OUT / "slicer_checks"
    check_root.mkdir(exist_ok=True)
    def run(path):
        folder = check_root / path.stem
        folder.mkdir(exist_ok=True)
        args = [str(slicer), "--datadir", str(folder / "settings"),
                "--load-settings", str(resources / "machine/Bambu Lab A1 mini 0.4 nozzle.json") + ";" +
                str(resources / "process/0.16mm Optimal @BBL A1M.json"),
                "--load-filaments", str(resources / "filament/Generic PLA @BBL A1M.json"),
                "--slice", "0", "--outputdir", str(folder), str(path)]
        result = subprocess.run(args, capture_output=True, text=True, timeout=180)
        (folder / "log.txt").write_text(result.stdout + result.stderr)
        report_path = folder / "result.json"
        report = json.loads(report_path.read_text()) if report_path.exists() else {}
        passed = result.returncode == 0 and report.get("return_code") == 0
        print(path.name, "PASS" if passed else "FAIL", flush=True)
        return path.name, {"passed": passed, "process_exit": result.returncode, "result": report}
    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = dict(pool.map(run, sorted((OUT / "print").glob("*.stl"))))
    summary = {"slicer": "OrcaSlicer 2.3.2", "machine": "Bambu Lab A1 mini 0.4 nozzle",
               "process": "0.16mm Optimal @BBL A1M", "filament": "Generic PLA @BBL A1M",
               "physical_print_tested": False, "parts": reports}
    (OUT / "slicing_validation.json").write_text(json.dumps(summary, indent=2) + "\n")
    if not all(r["passed"] for r in reports.values()):
        raise ValueError("Some slicing checks failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slicer", type=Path)
    args = parser.parse_args()
    interference()
    reinforcement_seating()
    if args.slicer:
        slicing(args.slicer)
