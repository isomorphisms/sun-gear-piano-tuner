"""Actual FreeCAD PartDesign builder: square and star socket alternatives.

This module MUST run inside FreeCAD. There are no mocks or proxy CAD objects.
Build each socket in a separate native document; gear coupling remains unspecified.
"""
from pathlib import Path
import math
import FreeCAD as App
import Part
import Sketcher

from cad.adapter_geometry import AdapterSpec, DEFAULT, STYLES, outline_points


def _profile(body, name, label, points, height):
    sketch = body.newObject('Sketcher::SketchObject', name)
    sketch.Label = label
    sketch.Placement.Base = App.Vector(0, 0, height)
    for index, a in enumerate(points):
        b = points[(index+1) % len(points)]
        sketch.addGeometry(Part.LineSegment(
            App.Vector(a[0], a[1], 0), App.Vector(b[0], b[1], 0)), False)
    return sketch


def _circle(body, name, label, diameter, height):
    sketch = body.newObject('Sketcher::SketchObject', name)
    sketch.Label = label
    sketch.Placement.Base = App.Vector(0, 0, height)
    sketch.addGeometry(Part.Circle(App.Vector(0,0,0), App.Vector(0,0,1), diameter/2), False)
    sketch.addConstraint(Sketcher.Constraint('Diameter', 0, diameter))
    return sketch


def build_adapter(style, spec=DEFAULT, document_name=None):
    """Return (doc, body, final PartDesign subtractive loft).

    The cavity runs from just below the stock bottom to its blind roof.
    Millimetre z=0 denotes base plane below the exposed tuning pin.
    """
    if style not in STYLES:
        raise ValueError('Unsupported socket style')
    spec.validate()
    name = document_name or ('SunGear_' + style)
    if name in App.listDocuments():
        raise ValueError('Document exists; choose a new document_name')
    doc = App.newDocument(name)
    try:
        body = doc.addObject('PartDesign::Body', 'SocketAdapter')
        body.Label = style.capitalize() + ' tapered socket — unverified fit'
        barrel_profile = _circle(body, 'BarrelProfile', 'Outside barrel', spec.barrel_diameter, spec.seated_bottom)
        doc.recompute()
        barrel = body.newObject('PartDesign::Pad', 'Barrel')
        barrel.Profile = barrel_profile
        barrel.Length = spec.barrel_length
        doc.recompute()

        pilot_profile = _circle(body, 'PilotProfile', 'Provisional coupling pilot',
                                spec.pilot_diameter, spec.seated_bottom + spec.barrel_length)
        doc.recompute()
        pilot = body.newObject('PartDesign::Pad', 'Pilot')
        pilot.Profile = pilot_profile
        pilot.Length = spec.pilot_length
        doc.recompute()

        # The loft starts exactly on the stock's bottom plane. FreeCAD 0.19
        # includes a 0.02-mm lead-in beyond this plane in the body's BBox,
        # so the former overrun failed the axial positioning acceptance test.
        lead = 0.0
        mouth_af = spec.mouth_across_flats
        mouth = _profile(body, 'SocketMouth', style + ' socket mouth',
                         outline_points(style, mouth_af), spec.seated_bottom - lead)
        roof = _profile(body, 'SocketRoof', style + ' blind socket roof',
                        outline_points(style, spec.roof_across_flats),
                        spec.seated_bottom + spec.cavity_depth)
        doc.recompute()
        cut = body.newObject('PartDesign::SubtractiveLoft', 'TaperedSocket')
        cut.Label = 'Tapered ' + style + ' cavity'
        cut.Profile = mouth
        cut.Sections = [roof]
        cut.Ruled = True
        body.Tip = cut
        doc.recompute()

        if cut.Shape.isNull() or not cut.Shape.isValid() or len(cut.Shape.Solids) != 1:
            raise RuntimeError('FreeCAD failed to generate one valid subtractive-loft solid')
        if body.Shape.isNull() or len(body.Shape.Solids) != 1 or not body.Shape.isValid():
            raise RuntimeError('FreeCAD produced an invalid PartDesign body')

        references = doc.addObject('App::DocumentObjectGroup', 'ReferenceEnvelope')
        references.Label = 'Dimensions: 4-in depth / 0.5-in available pin (reference)'
        for prop, val in [
            ('BoxDepth', spec.box_depth),
            ('ExposedPinLength', spec.exposed_pin_length),
            ('TargetEngagement', spec.target_engagement),
            ('AdapterBottom', spec.seated_bottom),
            ('AdapterTop', spec.seated_top),
            ('RemainingDepthAboveAdapter', spec.remaining_axial_depth),
            ('MouthAcrossFlatsUnverified', spec.mouth_across_flats),
            ('RoofAcrossFlatsUnverified', spec.roof_across_flats),
        ]:
            references.addProperty('App::PropertyLength', prop, 'Dimensions')
            setattr(references, prop, val)
        references.addProperty('App::PropertyAngle', 'WallDraft', 'Dimensions')
        references.WallDraft = spec.wall_draft_degrees
        references.addProperty('App::PropertyString', 'FitStatus', 'Notes')
        references.FitStatus = 'PROVISIONAL. Square/star cavity fit and tolerances await real tuning-pin measurements.'
        references.addProperty('App::PropertyString', 'GearCoupling', 'Notes')
        references.GearCoupling = 'NOT CHOSEN; upper pilot is not a torque coupling.'
        references.addProperty('App::PropertyString', 'EnvelopeXY', 'Notes')
        references.EnvelopeXY = 'UNKNOWN: only axial 101.6 mm bounding dimension specified.'
        for guide_name, label, offset, length in [
            ('AxialEnvelopeGuide', 'Available axial depth: 101.6 mm', 19.0, spec.box_depth),
            ('PinLengthGuide', 'Exposed pin: 12.7 mm', 15.0, spec.exposed_pin_length),
        ]:
            obj = doc.addObject('Part::Feature', guide_name)
            obj.Label = label
            obj.Shape = Part.makeLine(App.Vector(offset,0,0), App.Vector(offset,0,length))
            references.addObject(obj)

        doc.recompute()
        if App.GuiUp:
            for obj in [barrel_profile, barrel, pilot_profile, pilot, mouth, roof]:
                obj.ViewObject.Visibility = False
            cut.ViewObject.Visibility = True
            body.ViewObject.Visibility = True
            cut.ViewObject.ShapeColor = (0.73,0.78,0.84)
        return doc, body, cut
    except Exception:
        App.closeDocument(doc.Name)
        raise


def export_adapter(style, directory, spec=DEFAULT):
    """Write a native FreeCAD project and STEP, return file paths."""
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    doc, body, _ = build_adapter(style, spec)
    try:
        native = directory / ('sun_gear_adapter_' + style + '_v1.FCStd')
        step = directory / ('sun_gear_adapter_' + style + '_v1.step')
        doc.recompute()
        doc.saveAs(str(native))
        # Only the adapter body, not reference guide-lines, belongs in STEP.
        Part.export([body], str(step))
        return str(native), str(step)
    finally:
        App.closeDocument(doc.Name)
