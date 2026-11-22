# Test procedure and acceptance ledger

This project has two *different* testing layers. They must never be conflated.

## 1. Local analytic / independent BREP preflight

From repository root:

```sh
PYTHONPATH=. python3 -m unittest discover -s tests/local -v
PYTHONPATH=. python3 cad/build_preview.py
```

Requires CadQuery/OCP only for the second command. These use the same dimensional
math and generate imported, checked STEP solids, but they do **not** exercise FreeCAD.

Results in this draft environment (2026-11-22): four analytic tests passed;
both STEP files exported, reopened and had valid single-solid B-reps.

## 2. Actual FreeCAD integration tests — the acceptance gate

From repository root with a real `FreeCADCmd`/`freecadcmd` installed:

```sh
bash tests/run_freecad.sh
# Or specify a custom launcher:
FREECAD_CMD='/path/to/FreeCADCmd' bash tests/run_freecad.sh
```

The runner invokes `tests/freecad/run_suite.py` **inside FreeCAD's own Python**.
Tests use actual `PartDesign::Body`, sketch objects, pads and subtractive lofts.
The original adapter suite has eight native cases, covering **both** square and star versions:

- Real feature history and profile edge counts (4 vs. 16)
- Valid, non-null, single-solid resulting shapes
- Open cavity, intact barrel wall and *closed* blind end
- 101.6-mm maximum axial depth and 12.7-mm exposed pin properties
- Distinct removed material for square vs. star geometry
- PartDesign recompute after changing a feature dimension
- Regeneration after changing the mouth dimension
- `.FCStd` save, close and reopen; STEP export and import/volume agreement; invalid parameters rejected before creating a document

The runner **deletes the previous result** before running. It errors if FreeCAD is
missing, if a test failed or was skipped, or if no genuine result was written.
Evidence is `build/freecad-test/result.json` and `unittest.log`. After passing,
the runner also exports both **genuine FreeCAD-generated** `.FCStd` editable
models and STEP files into `build/freecad-test/models/`. Missing or empty
exported models make the runner fail.

Run the same tests using FreeCAD's GUI via `tests/freecad/run_gui.FCMacro`, or
create the two native `.FCStd` models with `cad/generate_models.FCMacro`.

The GitHub Actions file `.github/workflows/freecad-native.yml` runs the native
suite on Ubuntu 22.04 with the repository-provided FreeCAD package, and uploads
the report even after failures. A green build may only be claimed **after** the
workflow actually completes successfully.

## Verified adapter result and drive-v2 gate

- **Adapter v1:** 8/8 native FreeCAD 0.19 tests passed in [run
  45054873747](https://github.com/isomorphisms/sun-gear-piano-tuner/actions/runs/45054873747).
  The CI artifacts contain both genuine `.FCStd` and FreeCAD STEP files.
- **Drive v2:** the runner now requires at least **13 native test cases** (8
  adapters + 5 drive reference tests). Native tests validate all three pitch
  layouts, both socket choices, bounding data, parameter changes, and
  `.FCStd` save/reopen and STEP imports. Successful CI exports **six** drive
  pitch-reference `.FCStd` + STEP pairs to `build/freecad-test/drives/`.
- The local working environment lacks FreeCAD; local pure geometry tests (11)
  are NOT native FreeCAD evidence. The drive-v2 CI result must be checked
  separately before claiming it passed.

## Outstanding gates

- Nominal socket mouth across-flats of 7.05 mm is a fitting assumption, not a
  certified #2 star-tip or square-pin measurement.
- Actual tuning-pin fit, interference with strings/other pins, socket steel,
  torque limit, and drive coupling are **unverified**.
- Actual box width/side clearance remains unmeasured; v2 gearbox footprint
  estimates are provisional. No reducer architecture is chosen.
- No tooth profiles, moving contact analysis, stiffness, backlash, torque
  reaction structure, or bearings have been qualified; pitch reference geometry
  is NOT an operating gearbox.
