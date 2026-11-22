# Adapter design and fit record (v0)

## Inputs that came from the project

- Maximum available **axial** depth: **4.000 in = 101.6 mm**.
- Usable pin available for gripping: **0.500 in = 12.7 mm**.
- Tuning-pin tool interface: nominal **#2 eight-point star** socket, tapered to fit a four-flat tapered piano tuning pin.
- Gear train: **not selected**. Keep the adapter detachable from subsequent reducer variants.
- CAD system: **FreeCAD**. Use an editable, feature-based model; supply STEP for interchange.

## Parameters — provisional fit-study values, not production dimensions

| Parameter | v0 value | Status |
|---|---:|---|
| Socket external barrel | Ø15.0 × 20.0 mm | Provisional; check neighboring pins/string clearance |
| Upper locating pilot | Ø8.0 × 10.0 mm | Placeholder; **not** a usable torque-transmitting joint |
| Total adapter height | 30.0 mm | Geometric v0 |
| Star mouth nominal across flats (component square) | 7.05 mm | **Unverified**, not a published #2 tolerance |
| Star blind depth | 11.5 mm | Chosen to permit nominal 10 mm engagement with clearance |
| Star taper | 4° per wall, ~8° included | Approximate; actual pins and tips vary |
| Star blind end nominal across flats | ~5.44 mm | Derived from 7.05 - 2 × 11.5 × tan(4°) |
| Target grip depth | 10.0 mm | **Design assumption**; needs a real seating test |
| Bottom end of adapter above pin base | 2.7 mm | Derived from 12.7 - 10.0 |
| Adapter top above pin base | 32.7 mm | Derived from 2.7 + 30.0 |
| Remaining axial depth above top | 68.9 mm | Derived from 101.6 - 32.7; **not** all available for gears after bearings/housing |

The profile is the outer union-boundary of two concentric squares rotated 45°: a 16-vertex outline with eight outer points and eight concave valleys. The mouth and roof sketches are connected by ruled loft surfaces, giving a draft into the blind socket. The actual fitting contact needs proof; this is not a certified #2 geometry.

**Critical distinction:** a tuning pin marked **2/0** uses a nominal shank diameter (often .282 in), which does *not* specify either the square head across-flats size or the commercial **#2 tip**'s socket geometry. Do not substitute .282 in for the square opening dimension.

## Fit, materials, and verification

1. Measure one of the intended tuning pins at several axial positions across the four flats, plus its taper, exposed height, pin spacing, and clearance from wire coils. If a pin cannot be removed, compare with a separately purchased reference pin or a verified commercial #2 star tip.
2. Compare the socket model directly with a **hardened, commercially made #2 star tuning tip**. Different #2 tips have different actual geometry/fit; report tool maker and part number with measurements.
3. Run the macro in FreeCAD and confirm the resultant `PartDesign::SubtractiveLoft` is a single valid solid; confirm the native `.FCStd` opens and parameters regenerate. The supplied STEP was checked independently; actual FreeCAD execution remains unverified.
4. Check that the pin enters without bottoming on the socket roof, makes useful contact on all four sides, does not rock, and clears adjacent tuning pins and strings.
5. Do not transmit real tuning torque through an FDM, SLA, or other unqualified printed socket. Use a purchased hardened tip or a properly engineered steel part, with verified torque coupling, bearings, and a proof-test on a test fixture first.

## Reduction mechanisms to compare, not commit to

- **5:1 coaxial planetary** (previous concept): 12-tooth sun, 18-tooth planets, fixed 48-tooth ring, three planets, 0.8 module, 20° pressure angle, about 8 mm face width. For fixed ring ratio, `1 + ring/sun = 5`. Validate carrier torque and backlash; this is a candidate, not a validated design.
- Alternative planetary ratios or compound stages: increased control, potentially increased backlash/compliance and manufacturing complexity.
- **Worm** gear reduction: compact high ratio in some layouts, but friction, stiction, reversibility and backlash may impair fine tuning; test before selecting.
- **Spur** compound train: geometrically easier to fabricate and measure but may add off-axis package width and load paths.
- Other transmission routes (strain-wave, differential, direct manual fine adjust) should be compared to a baseline; no assumption of benefit without a torque/backlash model.

Decision criteria: output torque, controlled incremental rotation, deadband after reversing, torsional stiffness, pin-side reaction/handle support, ratio, manufacturability, noise, cost, and hard **101.6 mm axial height**. **Maximum transverse envelope is still unknown.**

## Background technical references

- Renner USA, *Technical Manual: Tuning Lever Design*: https://rennerusa.com/wp-content/uploads/2017/06/techmanual_lever_design.pdf (approx. 8-degree included pin taper, eight-point tips, variability in socket fit and rocking)
- Howard Piano Industries, standard #2 star tip: https://www.howardpianoindustries.com/piano-tuning-lever-tip/
- Piano Technicians Guild discussion of star-tip sizing vs tuning-pin shank: https://music.stackexchange.com/questions/49614/how-can-i-determine-the-diameter-of-my-pianos-tuning-pins
- Generic commercial socket tip: Schaff No. 14B, #2 star (1 inch overall); an alternative is to purchase such a tip and build a removable gear coupling around it rather than manufacture its mating socket from scratch.