"""Native radius-aware geography and its public metadata boundary."""
import copy
import hashlib
import json
import unittest

from app.detail_assets import asset_bytes
from app.planet_detail import validate_planet_detail
from app.planet_generation import project_surface, validate_surface
from app.planet_scale import physical_octave_periods
from app.planet_v11 import generate_planet_v11
from app.universe import build_universe


class PlanetV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maps = {}
        for radius in ("6.371e6", "1e8"):
            cls.maps[radius] = generate_planet_v11("scale-unit", 55, "continental",
                lake_material="water", polar_caps="water-ice", radius_m=radius)

    def test_size_changes_recorded_geography_not_only_labels(self):
        digests = []
        for radius, (geometry, payload) in self.maps.items():
            self.assertEqual(geometry["surface"]["radius_m"], radius)
            self.assertEqual((payload["width"], payload["height"]), (1024, 640))
            self.assertLessEqual(len(asset_bytes(payload)), 8 * 1024 * 1024)
            validate_surface(geometry)
            validate_planet_detail(payload, geometry)
            digests.append(hashlib.sha256(payload["terrain_grid"].encode()).hexdigest())
            self.assertLess(sum(v in (0, 1000) for v in payload["elevation"]), len(payload["elevation"]) // 2,
                            "Unnormalised noise must not flatten most terrain at the clamps")
        self.assertNotEqual(*digests)
        self.assertNotEqual(self.maps["6.371e6"][1]["elevation"], self.maps["1e8"][1]["elevation"])

    def test_accepted_extreme_sizes_do_not_alias_unresolved_bands(self):
        for radius in ("1e1000000", "9e2147483647"):
            periods = physical_octave_periods(radius)
            self.assertTrue(all(v["status"] == "attenuated" and v["sample_period_px"] == "0" for v in periods.values()))
        tiny = physical_octave_periods("1e-2147483648")
        self.assertTrue(all(v["status"] == "generalized" for v in tiny.values()))
        self.assertTrue(all(4 <= int(v["sample_period_px"]) <= 512 for v in tiny.values()))
        normal, large = physical_octave_periods("6.371e6"), physical_octave_periods("1e8")
        self.assertLess(int(large["continental"]["sample_period_px"]), int(normal["continental"]["sample_period_px"]))

    def test_forged_resolution_or_omission_flags_are_rejected(self):
        geometry, payload = self.maps["6.371e6"]
        corruptions = []
        for key, value in (("radius_m", "Infinity"), ("radius_m", "6371000"),
                           ("equatorial_sample_m_approx", "0"), ("detail_width_px", 4096),
                           ("scale_model", "unversioned")):
            bad = copy.deepcopy(geometry)
            bad["surface"][key] = value
            corruptions.append(bad)
        bad = copy.deepcopy(geometry)
        bad["surface"]["physical_bands"]["lake"] = "attenuated"
        bad["surface"]["physical_octaves"]["lake"]["status"] = "attenuated"
        corruptions.append(bad)
        for bad in corruptions:
            with self.subTest(surface=bad["surface"]), self.assertRaises(ValueError):
                validate_planet_detail(payload, bad)

    def test_nested_scale_projection_is_fresh_and_allowlisted(self):
        geometry = copy.deepcopy(self.maps["6.371e6"][0])
        marker = "PRIVATE_SCALE_SENTINEL"
        geometry["surface"]["private"] = marker
        geometry["surface"]["physical_bands"]["private"] = marker
        geometry["surface"]["physical_octaves"]["private"] = {"private": marker}
        geometry["surface"]["physical_octaves"]["lake"]["private"] = marker
        projected = project_surface(geometry)
        self.assertNotIn(marker, json.dumps(projected))
        projected["surface"]["physical_bands"]["lake"] = "edited"
        projected["surface"]["physical_octaves"]["lake"]["status"] = "edited"
        self.assertNotEqual(geometry["surface"]["physical_bands"]["lake"], "edited")
        self.assertNotEqual(geometry["surface"]["physical_octaves"]["lake"]["status"], "edited")

    def test_creation_never_assumes_earth_radius(self):
        with self.assertRaises(ValueError):
            build_universe("needs-radius", 55, planet_generator="planet-v11")
        with self.assertRaises(ValueError):
            build_universe("old-generator", 55, planet_generator="planet-v10", radius_m="1e8")


if __name__ == "__main__":
    unittest.main()
