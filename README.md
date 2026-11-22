# Sun-gear piano tuner

A mechanical, fine-adjustment piano tuning tool. Initial work is the **tuning-pin adapter**; the reduction mechanism is **not yet chosen**. The mechanism must deliver controlled micro-rotation under high torque, with sufficiently low backlash and torsional compliance to make small adjustments reliable.

## First-pass CAD

- [`cad/sun_gear_adapter_v0.FCMacro`](cad/sun_gear_adapter_v0.FCMacro) creates an **editable Part Design model in FreeCAD** (Barrel pad, Pilot pad, tapered eight-point Subtractive Loft, and Z reference geometry). Run it from FreeCAD's Macro menu; it writes `~/sun_gear_adapter_v0.FCStd`.
- [`cad/sun_gear_adapter_v0.step`](cad/sun_gear_adapter_v0.step) is a geometrically checked B-rep preview of the same **nominal** design. Import into FreeCAD for inspection. STEP is not a substitute for the native feature history.
- [`cad/sun_gear_adapter_v0.stl`](cad/sun_gear_adapter_v0.stl) is an inspection-only tessellation. A printed part must **not** be used for high-torque piano tuning.
- [`docs/adapter_design_notes.md`](docs/adapter_design_notes.md) contains dimensions, caveats, verification jobs, and next mechanical options.

**Important:** this is an approximate **#2 star-style** tapered socket, *not* a commercially proven #2 socket dimension. The #2 label is not a standardized across-flats measurement, and tuning-pin shank diameters are not the head dimensions. Fit must be established against a real pin and an existing hardened #2 tip before torque is applied.

## Known envelope

| Requirement | Imperial | Metric |
|---|---:|---:|
| Available axial depth | **4.000 in** | **101.6 mm** |
| Usable protruding piano tuning-pin length | **0.500 in** | **12.7 mm** |

Only axial depth is known. There is **no measured width/diameter envelope** for the gearbox. A 5:1 planetary with sun 12T / planets 18T / fixed ring 48T was discussed previously, but it is only one option. We will compare mechanisms before committing to it.

## Status

First-pass geometry exists, and an independent geometric preview is validated. FreeCAD macro execution on an actual FreeCAD installation, piano fit, allowable torque, backlash, bearing support, and housing packaging are **not yet verified**.