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
There are eight native test cases, covering **both** square and star versions:

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

## Outstanding gates

- In current local execution **FreeCAD is not installed**: native integration
  tests could not be run locally. This is an unverified gate, not a pass.
- Nominal socket mouth across-flats of 7.05 mm is a fitting assumption, not a
  certified #2 star-tip or square-pin measurement.
- Actual tuning-pin fit, interference with strings/other pins, socket steel,
  torque limit, and drive coupling are **unverified**.
- The box width, gearbox dimensions, gear ratio and coupling have not been selected.
