"""Physical-radius serialization boundaries without Earth-size defaults."""
import unittest
from decimal import Decimal, getcontext, localcontext

from app.planet_scale import canonical_radius, metadata, radius_for_planet


class PlanetScaleTests(unittest.TestCase):
    def test_equivalent_input_and_exact_fractional_sizes(self):
        for value, expected in (("6371000", "6.371e6"), ("6.371e6", "6.371e6"),
                                ("0.000000001", "1e-9"), ("125.000", "1.25e2"),
                                ("1e1000000", "1e1000000")):
            with self.subTest(value=value):
                self.assertEqual(canonical_radius(value), expected)
                self.assertEqual(canonical_radius(expected), expected)
        coefficient = "1234567890123456789012345678901234567890123456789012345678901234"
        result = canonical_radius(coefficient + "e1000000")
        self.assertEqual(Decimal(result), Decimal(coefficient + "e1000000"))

    def test_invalid_formats_and_nonpositive_values_are_rejected(self):
        invalid = [None, True, False, 6371000, 1.2, "", "0", "-1", "-1e1000",
                   "NaN", "sNaN", "Infinity", "-Infinity", "not-a-radius",
                   "1" * 65, "1e2147483648", "1e-2147483649", "1" * 257]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                canonical_radius(value)

    def test_extreme_size_metadata_stays_compact_and_does_not_change_context(self):
        before = getcontext().copy()
        for radius in ("1e-2147483648", "1e-9", "1e5", "1e8", "1e1000000", "9e2147483647"):
            info = metadata(radius)
            self.assertEqual(info["radius_m"], canonical_radius(radius))
            self.assertEqual(info["detail_width_px"], 1024)
            for name in ("equatorial_circumference_m_approx", "equatorial_sample_m_approx"):
                self.assertLess(len(info[name]), 200)
                self.assertTrue(Decimal(info[name]).is_finite())
                self.assertGreater(Decimal(info[name]), 0)
        after = getcontext()
        self.assertEqual((after.prec, after.Emax, after.Emin), (before.prec, before.Emax, before.Emin))
        with localcontext() as context:
            context.prec = 96
            sample = Decimal(metadata("100000")["equatorial_sample_m_approx"])
            self.assertEqual(sample, Decimal("613.59228515625"))
            self.assertEqual(Decimal(metadata("1000000")["equatorial_sample_m_approx"]), sample * 10)

    def test_radius_is_explicit_and_planet_overrides_do_not_become_defaults(self):
        planets = ["small", "large"]
        with self.assertRaises(ValueError):
            radius_for_planet(planet_ids=planets)
        with self.assertRaises(ValueError):
            radius_for_planet(per_planet={"small": "100"}, planet_ids=planets)
        with self.assertRaises(ValueError):
            radius_for_planet("100", {"unknown": "1"}, planets)
        self.assertEqual(radius_for_planet("1e-9", {"large": "1e1000000"}, planets),
                         {"small": "1e-9", "large": "1e1000000"})
        self.assertEqual(radius_for_planet(per_planet={"small": "1", "large": "2000"}, planet_ids=planets),
                         {"small": "1e0", "large": "2e3"})


if __name__ == "__main__":
    unittest.main()
