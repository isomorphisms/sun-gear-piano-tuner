"""Non-FreeCAD preflight; a pass does NOT mean native FreeCAD tests passed."""
from dataclasses import replace
import math
import unittest
from cad.adapter_geometry import AdapterSpec, DEFAULT, STYLES, outline_points, polygon_area


class AdapterGeometryTests(unittest.TestCase):
    def test_envelope_inputs(self):
        self.assertAlmostEqual(DEFAULT.box_depth, 4 * 25.4)
        self.assertAlmostEqual(DEFAULT.exposed_pin_length, 0.5 * 25.4)
        self.assertAlmostEqual(DEFAULT.seated_bottom, 2.7)
        self.assertAlmostEqual(DEFAULT.seated_top, 32.7)
        self.assertAlmostEqual(DEFAULT.remaining_axial_depth, 68.9)

    def test_square_and_star_are_distinct(self):
        square = outline_points('square', DEFAULT.mouth_across_flats)
        star = outline_points('star', DEFAULT.mouth_across_flats)
        self.assertEqual(len(square), 4)
        self.assertEqual(len(star), 16)
        self.assertAlmostEqual(polygon_area(square), DEFAULT.mouth_across_flats**2)
        self.assertGreater(polygon_area(star), polygon_area(square))

    def test_taper(self):
        self.assertAlmostEqual(DEFAULT.roof_across_flats,
           DEFAULT.mouth_across_flats - 2*DEFAULT.cavity_depth*math.tan(math.radians(4)))
        self.assertGreater(DEFAULT.mouth_across_flats, DEFAULT.roof_across_flats)

    def test_rejects_invalid_inputs(self):
        variants = [
            replace(DEFAULT, box_depth=20),
            replace(DEFAULT, cavity_depth=4),
            replace(DEFAULT, cavity_depth=30),
            replace(DEFAULT, mouth_across_flats=15),
            replace(DEFAULT, exposed_pin_length=6),
            replace(DEFAULT, wall_draft_degrees=45),
            replace(DEFAULT, pilot_diameter=16),
            replace(DEFAULT, barrel_length=float('nan')),
        ]
        for specimen in variants:
            with self.subTest(specimen=specimen), self.assertRaises(ValueError):
                specimen.validate()
        with self.assertRaises(ValueError):
            outline_points('hex', 7.05)

if __name__ == '__main__':
    unittest.main()
