"""Native FreeCAD tests; this module must import actual FreeCAD, Part, Sketcher.

No mocks, CadQuery substitutes, or tests based solely on exported STEP files.
"""
from dataclasses import replace
import os
from pathlib import Path
import tempfile
import unittest
import FreeCAD as App
import Part
from cad.adapter_geometry import DEFAULT
from cad.freecad_adapter import build_adapter, export_adapter


class FreeCADAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sun-gear-freecad-')

    def tearDown(self):
        for name in list(App.listDocuments()):
            if name.startswith(('SunGear_', 'StepRoundTrip_')):
                App.closeDocument(name)
        self.temp.cleanup()

    def build(self, style, spec=DEFAULT):
        name = 'SunGear_' + style + '_' + self._testMethodName
        return build_adapter(style, spec=spec, document_name=name)

    def test_native_square_and_star_part_design_feature_trees(self):
        for style, num_edges in [('square',4), ('star',16)]:
            with self.subTest(style=style):
                doc, body, cut = self.build(style)
                self.assertEqual(body.TypeId, 'PartDesign::Body')
                self.assertEqual(cut.TypeId, 'PartDesign::SubtractiveLoft')
                self.assertEqual(body.Tip.Name, cut.Name)
                self.assertEqual(len(doc.getObject('SocketMouth').Geometry), num_edges)
                self.assertEqual(len(doc.getObject('SocketRoof').Geometry), num_edges)
                self.assertEqual(doc.getObject('Barrel').TypeId, 'PartDesign::Pad')
                self.assertEqual(doc.getObject('Pilot').TypeId, 'PartDesign::Pad')
                self.assertTrue(cut.Ruled)
                self.assertFalse(cut.Shape.isNull())
                self.assertTrue(cut.Shape.isValid())
                self.assertEqual(len(cut.Shape.Solids), 1)
                self.assertTrue(body.Shape.isValid())
                self.assertEqual(len(body.Shape.Solids), 1)
                self.assertGreater(body.Shape.Volume, 0)

    def test_actual_cavity_is_open_and_blind(self):
        for style in ('square', 'star'):
            with self.subTest(style=style):
                _, body, _ = self.build(style)
                low = DEFAULT.seated_bottom
                roof = low + DEFAULT.cavity_depth
                # A probe entirely within the socket's central void must not
                # intersect material; after the blind roof, it MUST hit metal.
                open_probe = Part.makeCylinder(0.8, DEFAULT.cavity_depth-0.4,
                                                App.Vector(0,0,low+0.2))
                closed_probe = Part.makeCylinder(0.8, 1.0, App.Vector(0,0,roof+0.4))
                self.assertLess(body.Shape.common(open_probe).Volume, 1e-5)
                self.assertGreater(body.Shape.common(closed_probe).Volume, 1.0)
                # The outer wall should remain intact.
                wall_probe = Part.makeCylinder(0.2, 1.0,
                                App.Vector(DEFAULT.barrel_diameter/2-0.5,0,low+1.0))
                self.assertGreater(body.Shape.common(wall_probe).Volume, 0.05)

    def test_axial_envelope_and_reference_properties(self):
        for style in ('square', 'star'):
            with self.subTest(style=style):
                doc, body, _ = self.build(style)
                self.assertAlmostEqual(body.Shape.BoundBox.ZMin, DEFAULT.seated_bottom, places=4)
                self.assertAlmostEqual(body.Shape.BoundBox.ZMax, DEFAULT.seated_top, places=4)
                self.assertLessEqual(body.Shape.BoundBox.ZMax, DEFAULT.box_depth)
                refs = doc.getObject('ReferenceEnvelope')
                self.assertAlmostEqual(refs.BoxDepth.Value, 101.6)
                self.assertAlmostEqual(refs.ExposedPinLength.Value, 12.7)
                self.assertAlmostEqual(refs.RemainingDepthAboveAdapter.Value, 68.9)
                self.assertIn('UNKNOWN', refs.EnvelopeXY)

    def test_square_has_more_stock_than_star_at_identical_size(self):
        _, square, _ = self.build('square')
        _, star, _ = self.build('star')
        self.assertGreater(square.Shape.Volume, star.Shape.Volume)
        # Both are cavities in same 15-mm/8-mm coaxial stock.
        expected_stock = (3.141592653589793/4)*(
            DEFAULT.barrel_diameter**2*DEFAULT.barrel_length
            + DEFAULT.pilot_diameter**2*DEFAULT.pilot_length)
        self.assertLess(square.Shape.Volume, expected_stock)
        self.assertLess(star.Shape.Volume, expected_stock)

    def test_native_recompute_after_pilot_length_change(self):
        for style in ('square', 'star'):
            with self.subTest(style=style):
                doc, body, _ = self.build(style)
                pilot = doc.getObject('Pilot')
                original = body.Shape.BoundBox.ZMax
                pilot.Length = DEFAULT.pilot_length + 1.0
                doc.recompute()
                self.assertTrue(body.Shape.isValid())
                self.assertEqual(len(body.Shape.Solids), 1)
                self.assertAlmostEqual(body.Shape.BoundBox.ZMax, original + 1.0, places=4)
                pilot.Length = DEFAULT.pilot_length
                doc.recompute()
                self.assertAlmostEqual(body.Shape.BoundBox.ZMax, original, places=4)

    def test_parameters_regenerate_native_geometry(self):
        wider = replace(DEFAULT, mouth_across_flats=7.25)
        for style in ('square', 'star'):
            with self.subTest(style=style):
                _, nominal, _ = self.build(style)
                _, larger_cavity, _ = build_adapter(style, wider,
                    document_name='SunGear_' + style + '_wider')
                self.assertTrue(larger_cavity.Shape.isValid())
                self.assertLess(larger_cavity.Shape.Volume, nominal.Shape.Volume)

    def test_native_fcstd_save_close_reopen_and_step_roundtrip(self):
        for style in ('square', 'star'):
            with self.subTest(style=style):
                doc, body, _ = self.build(style)
                original_volume = body.Shape.Volume
                native_path = Path(self.temp.name) / ('adapter_' + style + '.FCStd')
                step_path = Path(self.temp.name) / ('adapter_' + style + '.step')
                doc.recompute()
                doc.saveAs(str(native_path))
                Part.export([body], str(step_path))
                self.assertTrue(native_path.exists() and native_path.stat().st_size > 1000)
                self.assertTrue(step_path.exists() and step_path.stat().st_size > 1000)
                App.closeDocument(doc.Name)
                reopened = App.openDocument(str(native_path))
                reopened.recompute()
                restored = reopened.getObject('SocketAdapter')
                self.assertEqual(reopened.getObject('TaperedSocket').TypeId,
                                 'PartDesign::SubtractiveLoft')
                self.assertTrue(restored.Shape.isValid())
                self.assertEqual(len(restored.Shape.Solids), 1)
                self.assertAlmostEqual(restored.Shape.Volume, original_volume, places=3)
                imported_doc = App.newDocument('StepRoundTrip_' + style)
                Part.insert(str(step_path), imported_doc.Name)
                imported_doc.recompute()
                solid_shapes = [obj.Shape for obj in imported_doc.Objects
                                if hasattr(obj, 'Shape') and not obj.Shape.isNull()
                                and len(obj.Shape.Solids)]
                self.assertTrue(solid_shapes, 'STEP import yielded no solid')
                self.assertTrue(all(shape.isValid() for shape in solid_shapes))
                imported_volume = sum(shape.Volume for shape in solid_shapes)
                self.assertAlmostEqual(imported_volume, original_volume, places=2)
                App.closeDocument(imported_doc.Name)
                App.closeDocument(reopened.Name)

    def test_invalid_dimensions_rejected_before_freecad_document_creation(self):
        number_before = len(App.listDocuments())
        with self.assertRaises(ValueError):
            build_adapter('square', replace(DEFAULT, box_depth=20),
                          document_name='SunGear_invalid')
        self.assertEqual(number_before, len(App.listDocuments()))

if __name__ == '__main__':
    unittest.main()
