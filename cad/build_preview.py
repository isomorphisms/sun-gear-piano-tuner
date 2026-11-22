"""Independent CadQuery STEP/STL build for nominal FreeCAD-macro parameters.
Not a substitute for executing the FreeCAD Part Design feature tree.
"""
import math
from pathlib import Path
import cadquery as cq
from OCP.BRepCheck import BRepCheck_Analyzer

OUT = Path(__file__).resolve().parent
box_depth, pin_exposed, engagement = 101.6, 12.7, 10.0
barrel_diameter, barrel_length = 15.0, 20.0
pilot_diameter, pilot_length = 8.0, 10.0
star_mouth_af, star_depth, taper_degrees = 7.05, 11.5, 4.0
z0 = pin_exposed-engagement
star_roof_af = star_mouth_af - 2*star_depth*math.tan(math.radians(taper_degrees))

def wire(across_flats, z):
    half = across_flats/2
    outer_r = math.sqrt(2)*half
    inner_r = math.sqrt(1 + (math.sqrt(2)-1)**2)*half
    vertices = []
    for i in range(16):
        r = outer_r if i%2==0 else inner_r
        a = math.radians(i*22.5)
        vertices.append(cq.Vector(r*math.cos(a), r*math.sin(a), z))
    return cq.Wire.makePolygon(vertices + vertices[:1], close=True)

barrel = cq.Solid.makeCylinder(barrel_diameter/2, barrel_length, cq.Vector(0,0,z0))
pilot = cq.Solid.makeCylinder(pilot_diameter/2, pilot_length, cq.Vector(0,0,z0+barrel_length))
stock = barrel.fuse(pilot)
# Mouth protrudes fractionally beyond end to guarantee a clean open recess.
star = cq.Solid.makeLoft([wire(star_mouth_af+0.01, z0-0.01), wire(star_roof_af, z0+star_depth)], ruled=True)
result = stock.cut(star)
assert result.isValid() and BRepCheck_Analyzer(result.wrapped).IsValid()
assert len(result.Solids()) == 1
expected = z0 + barrel_length + pilot_length
assert expected <= box_depth
bb = result.BoundingBox()
assert abs(bb.zmin-z0) < 1e-5 and abs(bb.zmax-expected)<1e-5
assert result.Volume() > 0
cq.exporters.export(result, str(OUT/'sun_gear_adapter_v0.step'), exportType='STEP')
cq.exporters.export(result, str(OUT/'sun_gear_adapter_v0.stl'), exportType='STL', tolerance=0.08, angularTolerance=0.08)
print(f'valid={result.isValid()}, solids={len(result.Solids())}, volume_mm3={result.Volume():.3f}, ') 
print(f'mouth_af={star_mouth_af}, roof_af={star_roof_af:.3f}, seated_bottom_z={z0:.3f}, top_z={expected:.3f}, remaining_height={box_depth-expected:.3f}')
