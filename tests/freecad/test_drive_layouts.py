"""Native FreeCAD tests of the real geometry tree, not CadQuery stand-ins.

These assertions cover pitch envelopes and serialization. They CANNOT certify
load-bearing meshing, tooth stresses, torsional backlash, or physical fit.
"""
from dataclasses import replace
import math
from pathlib import Path
import tempfile
import unittest
import FreeCAD as App
import Part
from cad.adapter_geometry import DEFAULT
from cad.drive_geometry import DriveSpec, STUDIES, make_layout
from cad.freecad_drive import build_drive, export_drive


class NativeDrivePitchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='sun-drive-native-')

    def tearDown(self):
        for name in list(App.listDocuments()):
            if name.startswith(('SunGearDrive_','DriveReload_','DriveStep_')):
                App.closeDocument(name)
        self.tmp.cleanup()

    def test_both_socket_styles_with_three_native_drive_layouts(self):
        for study in STUDIES:
            for style in ('square','star'):
                with self.subTest(study=study,style=style):
                    doc,body,layout,features=build_drive(study,style,
                        document_name='SunGearDrive_'+study+'_'+style+'_valid')
                    self.assertTrue(body.Shape.isValid())
                    self.assertEqual(len(body.Shape.Solids),1)
                    refs=doc.getObject('DrivePitchReferences')
                    self.assertEqual(refs.StudyType,study)
                    self.assertIn('NOT MEASURED',refs.EnvelopeWidthStatus)
                    self.assertIn('PITCH ENVELOPES',refs.DesignStatus)
                    self.assertAlmostEqual(refs.IdealInputToOutputRatio,layout['ratio'])
                    self.assertAlmostEqual(refs.AxialTop.Value,layout['top_z'])
                    self.assertLessEqual(refs.AxialTop.Value,doc.getObject('ReferenceEnvelope').BoxDepth.Value)
                    for name,obj in features.items():
                        self.assertFalse(obj.Shape.isNull(),name)
                        self.assertTrue(obj.Shape.isValid(),name)
                    self.assertEqual(len([n for n in features if n.startswith('Planet')]),
                                     3 if study.startswith('planetary') else 0)
                    self.assertEqual(doc.getObject('TaperedSocket').TypeId,
                                     'PartDesign::SubtractiveLoft')

    def test_native_pitch_disks_at_expected_centres_and_heights(self):
        for study in STUDIES:
            with self.subTest(study=study):
                doc,_,layout,features=build_drive(study,'square')
                for disk in layout['disks']:
                    shape=features[disk.name].Shape
                    self.assertAlmostEqual(shape.BoundBox.ZMin,disk.z,places=5)
                    self.assertAlmostEqual(shape.BoundBox.ZLength,disk.face_width,places=5)
                    center=shape.CenterOfMass
                    self.assertAlmostEqual(center.x,disk.x,places=5)
                    self.assertAlmostEqual(center.y,disk.y,places=5)
                    self.assertAlmostEqual(features[disk.name].PitchRadius.Value,
                                           disk.pitch_radius,places=5)
                self.assertLessEqual(layout['top_z'],DEFAULT.box_depth)

    def test_native_save_reopen_and_step_import(self):
        for study in STUDIES:
            with self.subTest(study=study):
                native,step=export_drive(study,'star',self.tmp.name)
                self.assertGreater(Path(native).stat().st_size,1000)
                self.assertGreater(Path(step).stat().st_size,1000)
                reopened=App.openDocument(native)
                try:
                    reopened.recompute()
                    self.assertEqual(reopened.getObject('DrivePitchReferences').StudyType,study)
                    self.assertTrue(reopened.getObject('SocketAdapter').Shape.isValid())
                    self.assertTrue(reopened.getObject('InputStub').Shape.isValid())
                finally:
                    App.closeDocument(reopened.Name)
                imported=App.newDocument('DriveStep_'+study)
                try:
                    Part.insert(step,imported.Name)
                    imported.recompute()
                    solids=[o.Shape for o in imported.Objects if hasattr(o,'Shape')
                            and not o.Shape.isNull() and len(o.Shape.Solids)]
                    self.assertGreaterEqual(len(solids),5)
                    self.assertTrue(all(s.isValid() for s in solids))
                finally:
                    App.closeDocument(imported.Name)

    def test_native_rebuild_after_module_change(self):
        for study in STUDIES:
            with self.subTest(study=study):
                _,_,nominal,_=build_drive(study,'square',
                    document_name='SunGearDrive_'+study+'_nominal')
                doc,_,changed,features=build_drive(study,'square',drive=DriveSpec(module=1.0),
                    document_name='SunGearDrive_'+study+'_mod1')
                self.assertGreater(changed['xy_bounds'][1]-changed['xy_bounds'][0],
                                   nominal['xy_bounds'][1]-nominal['xy_bounds'][0])
                self.assertTrue(all(o.Shape.isValid() for o in features.values()))

    def test_invalid_axial_stack_never_creates_freecad_document(self):
        old=set(App.listDocuments())
        with self.assertRaises(ValueError):
            build_drive('compound6','square',drive=DriveSpec(face_width=30,axial_gap=20),
                        document_name='SunGearDrive_bad_envelope')
        self.assertEqual(old,set(App.listDocuments()))

if __name__=='__main__':unittest.main()
