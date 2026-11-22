"""Independent OpenCascade preview for square and star prototypes.

THIS IS NOT THE NATIVE FREECAD TEST. It verifies portable BREP/STEP geometry only.
Run: PYTHONPATH=. python cad/build_preview.py
"""
import math
from pathlib import Path
import cadquery as cq
from OCP.BRepCheck import BRepCheck_Analyzer
from cad.adapter_geometry import DEFAULT, outline_points, polygon_area

OUT = Path(__file__).resolve().parent


def wire(style, across_flats, z):
    pts = [cq.Vector(x,y,z) for x,y in outline_points(style, across_flats)]
    return cq.Wire.makePolygon(pts + pts[:1], close=True)


def build(style):
    spec = DEFAULT
    z0 = spec.seated_bottom
    barrel = cq.Solid.makeCylinder(spec.barrel_diameter/2, spec.barrel_length, cq.Vector(0,0,z0))
    pilot = cq.Solid.makeCylinder(spec.pilot_diameter/2, spec.pilot_length,
                                  cq.Vector(0,0,z0+spec.barrel_length))
    stock = barrel.fuse(pilot)
    lead = 0.0
    mouth = spec.mouth_across_flats
    cutter = cq.Solid.makeLoft([
        wire(style,mouth,z0-lead),
        wire(style,spec.roof_across_flats,z0+spec.cavity_depth)],ruled=True)
    solid = stock.cut(cutter)
    assert solid.isValid() and BRepCheck_Analyzer(solid.wrapped).IsValid()
    assert len(solid.Solids()) == 1 and solid.Volume()>0
    bbox = solid.BoundingBox()
    assert abs(bbox.zmin-spec.seated_bottom) < 1e-5
    assert abs(bbox.zmax-spec.seated_top) < 1e-5
    assert spec.seated_top <= spec.box_depth
    # Verify central cavity is open and closes after roof (material above roof).
    void_probe = cq.Solid.makeCylinder(0.8, spec.cavity_depth-0.4, cq.Vector(0,0,z0+0.2))
    roof_probe = cq.Solid.makeCylinder(0.8,1.0,cq.Vector(0,0,z0+spec.cavity_depth+0.4))
    assert solid.intersect(void_probe).Volume() < 1e-5
    assert solid.intersect(roof_probe).Volume() > 1
    path = OUT / ('sun_gear_adapter_' + style + '_v1.step')
    cq.exporters.export(solid,str(path),exportType='STEP')
    # Re-read the actual artifact; don't trust only the pre-export shape.
    imported = cq.importers.importStep(str(path))
    assert imported.val().isValid()
    assert len(imported.solids().vals()) == 1
    assert abs(imported.val().Volume()-solid.Volume()) < 1e-2
    print('%s valid STEP: %d bytes, volume %.3f mm3, height %.3f mm'
        % (style,path.stat().st_size,solid.Volume(),bbox.zmax))
    return solid


if __name__ == '__main__':
    square = build('square')
    star = build('star')
    assert square.Volume()>star.Volume(), 'Square must have smaller cutout than star'
    print('Independent STEP previews: PASS. Native FreeCAD: NOT TESTED.')
