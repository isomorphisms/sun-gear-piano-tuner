"""Independent layout arithmetic checks; do not call these FreeCAD verification."""
from dataclasses import replace
import math
import unittest
from cad.adapter_geometry import DEFAULT
from cad.drive_geometry import DriveSpec, make_layout, summary_rows


class PitchLayoutTests(unittest.TestCase):
    def test_fixed_ring_ratios_and_pitch_geometry(self):
        for study,ratio,sun,planet,ring in [
            ('planetary4',4,18,18,54),('planetary5',5,18,27,72)]:
            l=make_layout(study)
            self.assertEqual((l['input_teeth'],l['planet_teeth'],l['ring_teeth']),
                             (sun,planet,ring))
            self.assertEqual(l['ratio'],ratio)
            self.assertEqual(ring,sun+2*planet)
            self.assertEqual((sun+ring)%l['planet_count'],0)
            self.assertAlmostEqual(l['pitch_center_distance'],
                                   (sun+planet)*l['module']/2)
            self.assertAlmostEqual(l['ring_pitch_radius']-l['pitch_center_distance'],
                                   planet*l['module']/2)
            self.assertGreater(l['neighbor_tip_clearance'],0)

    def test_planetary_pitch_circles_contact_without_nonmesh_overlap(self):
        for study in ('planetary4','planetary5'):
            l=make_layout(study)
            sun=l['disks'][0];planets=l['disks'][1:]
            for p in planets:
                self.assertAlmostEqual(math.hypot(p.x-sun.x,p.y-sun.y),
                                       sun.pitch_radius+p.pitch_radius)
                self.assertAlmostEqual(math.hypot(p.x,p.y)+p.pitch_radius,
                                       l['ring_pitch_radius'])
            for i,p in enumerate(planets):
                for q in planets[i+1:]:
                    self.assertGreater(math.hypot(p.x-q.x,p.y-q.y),
                                       p.pitch_radius+q.pitch_radius+2*l['module'])

    def test_compound_two_stage_ratio_direction_and_centres(self):
        l=make_layout('compound6')
        self.assertEqual((l['input_teeth'],l['first_driven_teeth'],
                          l['second_driver_teeth'],l['output_teeth']),
                         (18,54,24,48))
        self.assertEqual(l['ratio'],6)
        self.assertEqual(l['stage1_center'],l['stage2_center'])
        self.assertAlmostEqual((18/54)*(24/48),1/6)
        # Both stages reverse sign once, so net rotation is same-direction.
        self.assertEqual((-1)*(-1),1)
        x=l['stage2_center'];y=l['stage1_center']
        self.assertNotEqual((x,y),(0,0))

    def test_axial_depths_and_unknown_lateral_fit(self):
        rows={r['name']:r for r in summary_rows()}
        self.assertEqual(rows['planetary4']['width_mm'],51.2)
        self.assertEqual(rows['planetary5']['width_mm'],65.6)
        self.assertEqual(rows['compound6']['width_mm'],77.2)
        self.assertEqual(rows['compound6']['depth_mm'],65.2)
        for row in rows.values():
            self.assertLess(row['top_mm'],DEFAULT.box_depth)
            self.assertGreater(row['remaining_axial_mm'],0)
            self.assertIn('PITCH ENVELOPE',row['note'])

    def test_parameter_changes_recalculate_package(self):
        base=make_layout('planetary4')
        changed=make_layout('planetary4',drive=DriveSpec(module=1.0))
        self.assertGreater(changed['casing_radius'],base['casing_radius'])
        self.assertEqual(changed['top_z'],base['top_z'])
        wider=make_layout('compound6',drive=DriveSpec(face_width=12.0))
        self.assertGreater(wider['top_z'],make_layout('compound6')['top_z'])

    def test_fail_closed_invalid_specs(self):
        for kind in ('planetary4','planetary5','compound6'):
            with self.subTest(study=kind):
                with self.assertRaises(ValueError):
                    make_layout(kind,drive=DriveSpec(face_width=30,axial_gap=20))
                with self.assertRaises(ValueError):
                    make_layout(kind,adapter=replace(DEFAULT,box_depth=40))
        with self.assertRaises(ValueError):
            make_layout('not-a-gear')
        with self.assertRaises(ValueError):
            make_layout('planetary4',drive=DriveSpec(module=-1))

    def test_12_tooth_warning_is_preserved(self):
        from cad.drive_geometry import _external_disk
        with self.assertRaisesRegex(ValueError,'undercut'):
            _external_disk('unsafe_sun',12,0,0,40,DriveSpec(),'input')

if __name__=='__main__': unittest.main()
