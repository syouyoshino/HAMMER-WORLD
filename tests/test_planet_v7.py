"""V7 cratered dry-world generation and persistence contract."""
import copy
import unittest

from app.planet_generation import (crater_profile_q, generate_planet_v7,
                                   project_surface, validate_surface)
from app.universe import build_universe, public_state_v2
from app.store import Store
from tests.pg_fixture import PostgresTestCase


class PlanetV7PureTests(unittest.TestCase):
    def test_integer_profile_is_bounded_and_supports_periodic_distance(self):
        self.assertEqual(crater_profile_q(0, 80, 40, 20), -40)
        self.assertEqual(crater_profile_q(80, 80, 40, 20), 20)
        self.assertEqual(crater_profile_q(100, 80, 40, 20), 0)
        self.assertEqual(crater_profile_q(101, 80, 40, 20), 0)

    def test_generation_is_deterministic_and_v7_craters_are_saved_and_projected(self):
        first = generate_planet_v7("reach", 987, "arid", "cratered")
        second = generate_planet_v7("reach", 987, "arid", "cratered")
        self.assertEqual(first, second)
        surface = first["surface"]
        self.assertEqual(surface["version"], "planet-v7")
        self.assertEqual(surface["topology"], "cylinder-x")
        self.assertEqual(surface["geology"], "cratered")
        self.assertGreaterEqual(len(surface["craters"]), 1)
        self.assertTrue(all(401 <= value <= 1000 for value in surface["elevation"]))
        validate_surface(first)
        projected = project_surface(first)["surface"]
        self.assertEqual(projected["craters"], surface["craters"])
        projected["craters"][0]["id"] = "mutated"
        projected["elevation"][0] = -1
        self.assertNotEqual(surface["craters"][0]["id"], "mutated")
        self.assertGreaterEqual(surface["elevation"][0], 401)

    def test_no_geology_has_no_craters_and_wet_cratered_choice_is_rejected(self):
        none = generate_planet_v7("reach", 123, "oceanic", "none")
        self.assertEqual(none["surface"]["craters"], [])
        with self.assertRaises(ValueError):
            generate_planet_v7("reach", 123, "oceanic", "cratered")

    def test_public_crater_projection_allowlists_nested_fields_and_copies_descriptors(self):
        geo = generate_planet_v7("reach", 123, "arid", "cratered")
        crater = geo["surface"]["craters"][0]
        crater["private_marker"] = {"secret": "hidden"}
        projected = project_surface(geo)["surface"]
        self.assertEqual(set(projected["craters"][0]),
                         {"id", "x_q", "y_q", "radius_q", "depth", "rim_height"})
        self.assertNotIn("private_marker", repr(projected))
        projected["craters"][0]["depth"] = -1
        projected["craters"].clear()
        self.assertGreater(crater["depth"], 0)
        self.assertTrue(geo["surface"]["craters"])

    def test_v7_requires_exact_province_coverage(self):
        geo = generate_planet_v7("reach", 123, "arid", "cratered")
        validate_surface(geo)
        for mutation in ("narrow", "overlap", "missing", "unaligned"):
            with self.subTest(mutation=mutation):
                malformed = copy.deepcopy(geo)
                provinces = malformed["provinces"]
                if mutation == "narrow": provinces[0]["width"] = 15
                elif mutation == "overlap":
                    provinces[1].update({key:provinces[0][key] for key in ("x", "y")})
                elif mutation == "missing": provinces.pop()
                else: provinces[0]["x"] = 1
                with self.assertRaisesRegex(ValueError, "province coverage"):
                    validate_surface(malformed)

    def test_legacy_build_rejects_geology_arguments(self):
        for version in range(1, 7):
            for arguments in ({"geology": "cratered"}, {"geology": "unknown"},
                              {"planet_geologies": {}},
                              {"planet_geologies": {"unknown-planet": "none"}}):
                with self.subTest(version=version, arguments=arguments):
                    with self.assertRaisesRegex(ValueError, "geology requires planet-v7"):
                        build_universe("slice", 321, planet_generator=f"planet-v{version}", **arguments)

    def test_legacy_state_rejects_v7_geology_configuration(self):
        for version in range(1, 7):
            with self.subTest(version=version):
                state = build_universe("slice", 321, planet_generator=f"planet-v{version}")
                Store.validate_state("world-v2", "demo-v2", 0, state)
                state["_private"]["generator_config"]["planet_geologies"] = {}
                with self.assertRaisesRegex(ValueError, "V7 geology requires"):
                    Store.validate_state("world-v2", "demo-v2", 0, state)

    def test_default_v1_and_explicit_legacy_geology_defaults_match(self):
        default = build_universe("slice", 321)
        explicit = build_universe("slice", 321, planet_generator="planet-v1",
                                  geology="none", planet_geologies=None)
        self.assertEqual(default, explicit)
        self.assertEqual(default["_private"]["generator_config"]["planet"], "planet-v1")

    def test_v7_state_accepts_none_and_dry_cratered_geology(self):
        for preset, geology in (("oceanic", "none"), ("arid", "cratered"),
                                ("barren", "cratered"), ("frozen", "cratered")):
            with self.subTest(preset=preset, geology=geology):
                state = build_universe("slice", 321, planet_generator="planet-v7",
                                       preset=preset, geology=geology)
                Store.validate_state("world-v2", "demo-v2", 0, state)

    def test_descriptor_validation_rejects_bool_duplicate_and_bad_extent(self):
        geo = generate_planet_v7("reach", 123, "barren", "cratered")
        for change in (
            lambda crater: crater.update(x_q=True),
            lambda crater: crater.update(y_q=1280),
            lambda crater: crater.update(radius_q=23),
        ):
            malformed = copy.deepcopy(geo)
            change(malformed["surface"]["craters"][0])
            with self.assertRaises(ValueError): validate_surface(malformed)
        malformed = copy.deepcopy(geo)
        malformed["surface"]["craters"].append(dict(malformed["surface"]["craters"][0]))
        with self.assertRaises(ValueError): validate_surface(malformed)

    def test_geology_change_is_per_planet_and_private_config_matches_all_planets(self):
        ids = {f"slice-planet-{name}" for name in ("reach", "ash", "haven", "veil")}
        base = build_universe("slice", 321, planet_generator="planet-v7", preset="arid")
        altered = build_universe("slice", 321, planet_generator="planet-v7", preset="arid",
                                 planet_geologies={"slice-planet-reach": "cratered"})
        self.assertEqual(set(base["_private"]["generator_config"]["planet_geologies"]), ids)
        self.assertEqual(base["_private"]["generator_config"]["planet_geologies"]["slice-planet-ash"], "none")
        self.assertNotEqual(base["geography"]["slice-planet-reach"]["surface"]["craters"],
                            altered["geography"]["slice-planet-reach"]["surface"]["craters"])
        for planet_id in ids - {"slice-planet-reach"}:
            self.assertEqual(base["geography"][planet_id], altered["geography"][planet_id])
        self.assertNotIn("generator_config", public_state_v2(altered))


class PlanetV7PersistenceTests(PostgresTestCase, unittest.TestCase):
    def test_saved_v7_projects_only_surveyed_planet_and_restore_keeps_descriptors(self):
        self.db.create_demo_v2("saved-v7", seed=321, planet_generator="planet-v7", preset="barren",
                               geology="cratered")
        saved = self.db.current("saved-v7")["snapshot"]["state"]
        self.db.validate_state("world-v2", "demo-v2", 0, saved)
        public = self.db.player_state(self.db.current("saved-v7")["snapshot"])
        self.assertEqual(set(public["geography"]), {"saved-v7-planet-reach"})
        self.assertIn("craters", public["geography"]["saved-v7-planet-reach"]["surface"])
        projected = public["geography"]["saved-v7-planet-reach"]["surface"]["craters"]
        projected.clear()
        self.assertTrue(saved["geography"]["saved-v7-planet-reach"]["surface"]["craters"])
        snapshot_id = self.db.current("saved-v7")["snapshot"]["id"]
        self.db.restore("saved-v7", snapshot_id, "restored-v7")
        restored = self.db.current("restored-v7")["snapshot"]["state"]
        self.assertEqual(restored["geography"], saved["geography"])


if __name__ == "__main__": unittest.main()
