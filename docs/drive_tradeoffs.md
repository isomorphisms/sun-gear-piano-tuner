# DRIVE-01: reduction packaging and kinematic study (v2)

This is a **pitch-envelope screening study**. It does not provide finished
involute teeth, tested gear clearances, tolerances, torque ratings, backlash,
bearing seats, shafts, attachment to a piano pin, reaction fixture, or
manufacturable housing. No gear option has been selected.

## Non-negotiable recorded inputs

- Available **axial** depth relative to base of tuning pin: **101.6 mm**.
- Exposed tuning pin available: **12.7 mm**. The 10-mm engagement remains a
  *design assumption*, as does the socket's 7.05-mm mouth opening.
- Square and eight-point star have matching external adapters. Either remains
  a candidate. The Ø8 top pilot is NOT a torque-carrying coupling.
- **Lateral clearance is unknown**, as is the required tuning torque and
  permissible reversal deadband.

## Nominal pitch screening (module 0.8; 8-mm face width)

| Layout | Drive / held / output | Teeth | Signed speed reduction | Approx. XY envelope | Top above pin base | Axial remaining |
|---|---|---|---:|---:|---:|---:|
| Planetary P4 | sun / ring / carrier | 18 / 18 / 54, 3 planets | +4:1 | 51.2 × 51.2 mm | 60.7 mm | 40.9 mm |
| Planetary P5 | sun / ring / carrier | 18 / 27 / 72, 3 planets | +5:1 | 65.6 × 65.6 mm | 60.7 mm | 40.9 mm |
| Folded compound S6 | input / none / output | first 18→54, second 24→48 | +6:1 | 77.2 × 65.2 mm | 71.7 mm | 29.9 mm |

The XY envelopes include assumed 3-mm casing margin and full addendum allowance
for external gears; **not** a true fully engineered casing with mounts or
fasteners. These numbers are **computed from provisional geometry**, not actual
measured piano clearance.

### Why the old planetary 12/18/48 candidate was replaced

The old 5:1 12-tooth sun gear is susceptible to undercut with ordinary 20°
full-depth, unshifted involute teeth. A 5:1 candidate with an 18T sun is
18/27/72; the planetary assembly spacing `(sun + ring)/3 = 30` is integral.
For 4:1, 18/18/54 gives `(sun + ring)/3 = 24` and a smaller ring. Both
satisfy `ring = sun + 2*planet` and neighboring planet tip clearances.
These are **necessary**, not sufficient, conditions for working teeth.

### Compound shaft path

The compound 6:1 model places output at (0,0), intermediate at
(28.8,0), input at (28.8,28.8) in millimeters. Two external meshes yield
same-sign output rotation, with ideal speed `ω_out = ω_in / 6`.
A two-layer arrangement avoids pretending that independent input and output
concentric shafts are trivially supported. It also has the greatest lateral
reach, which may prove impossible on the intended piano.

### What the FreeCAD files actually contain

Six `.FCStd` documents, one per drive/socket combination: adapter's real
PartDesign feature tree and **genuine FreeCAD Part::Feature pitch envelopes**
for sun/planets/ring or two-stage spur disk centers, plus reference plates,
clearance indicators and the 4-in depth parameters. Associated STEP files
export these **reference solids only**, not gear manufacturing drawings.
`cad/drive_geometry.py` provides pure parametric computations and rejects
unsupported tooth counts or an over-height stack. `cad/freecad_drive.py`
constructs the reference CAD. `tests/freecad/test_drive_layouts.py` uses actual
FreeCAD geometry for placement, validity, save/reopen, STEP import, and
parameter-regeneration smoke tests.

## Proceed before machining or applying torque

1. **Measure the piano's transverse/side clearance** around the specific pin,
   nearby strings/pins, and where the tool's reaction arm can safely bear.
2. Establish torque and backlash/reversal limits on a spare **test fixture**,
   not with an unqualified printed tip on a piano.
3. Design a removable **steel** tip-to-output torque joint and bearing/reaction
   load paths. Avoid counting the current Ø8 locating pilot as a coupling.
4. Model real 20° involute teeth with profile shift and root fillets where
   required; calculate contact ratio, strength, planet phases and rotation
   interference. Load test a prototype before accepting a gear choice.

## Reference formulas and sources

- Fixed-ring planetary: `ratio = 1 + Z_ring/Z_sun`.
- Pitch: `D = module * Z`, simple planetary coaxial condition
  `Z_ring = Z_sun + 2 * Z_planet`.
- Three equally spaced planets: `(Z_sun + Z_ring)/3` integer.
- Supplier technical reference: [SDP/SI planetary gear design](https://www.sdp-si.com/planetary-gear-design/index.php).
- NASA planetary design study: [NASA/TM—2022-08843](https://ntrs.nasa.gov/api/citations/20220008843/downloads/TM-20220008843.pdf).

**Acceptance boundary:** CI may certify FreeCAD's pitch-layout geometry and
serialization only. It must not report working teeth, transmission accuracy,
strength or suitability to tune a piano without physical engineering evidence.
