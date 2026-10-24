import copy
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.planet_generation import generate_planet_v8, generate_planet_v9, project_surface, validate_surface
from app.planet_hydrography import clean_name
from app.engine_v2 import ALLOCATIONS
from app.store import Store
from app.universe import V2_RULES, V2_SCHEMA, build_universe, public_state_v2
from tests.pg_fixture import PostgresTestCase


ROOT = Path(__file__).resolve().parents[1]


class PlanetV9Tests(unittest.TestCase):
    def test_mixed_world_preserves_all_v8_records(self):
        ids = [f"mixed-v9-planet-{suffix}" for suffix in ("reach", "ash", "haven", "veil")]
        options = dict(planet_presets=dict(zip(ids, ("continental", "arid", "frozen", "oceanic"))),
                       planet_geologies={ids[1]: "cratered", ids[2]: "cratered"},
                       planet_lake_materials={ids[0]: "water"},
                       planet_polar_caps={ids[0]: "water-ice", ids[2]: "water-ice"})
        legacy = build_universe("mixed-v9", 741903, planet_generator="planet-v8", **options)
        named = build_universe("mixed-v9", 741903, planet_generator="planet-v9", feature_names="generated", **options)
        stripped = copy.deepcopy(named)
        for geo in stripped["geography"].values():
            geo["surface"].pop("hydrography")
            geo["surface"]["version"] = "planet-v8"
        stripped["_private"]["generator_config"].pop("feature_names")
        stripped["_private"]["generator_config"]["planet"] = "planet-v8"
        self.assertEqual(legacy, stripped)
        target = named["geography"][ids[0]]["surface"]["hydrography"]["features"][0]
        custom = build_universe("mixed-v9", 741903, planet_generator="planet-v9", feature_names="generated",
                                feature_name_overrides={ids[0]: {target["id"]: "Local Sea"}}, **options)
        target.update(name="Local Sea", name_source="custom")
        self.assertEqual(named, custom)

    def test_v9_wraps_unchanged_v8_and_is_deterministic(self):
        legacy = generate_planet_v8("reach", 987, "continental", lake_material="water")
        v9 = generate_planet_v9("reach", 987, "continental", lake_material="water")
        self.assertEqual({k: v for k, v in legacy["surface"].items() if k != "version"},
                         {k: v for k, v in v9["surface"].items() if k not in ("version", "hydrography")})
        self.assertEqual("planet-v9", v9["surface"]["version"])
        self.assertEqual(v9, generate_planet_v9("reach", 987, "continental", lake_material="water"))
        validate_surface(v9)
        types = {f["kind"] for f in v9["surface"]["hydrography"]["features"]}
        self.assertTrue({"ocean", "river", "lake"}.issubset(types))
        river = next(r for r in v9["surface"]["rivers"] if r["points"])
        feature = next(f for f in v9["surface"]["hydrography"]["features"] if f["kind"] == "river")
        self.assertEqual(river["id"], feature["id"])

    def test_feature_names_custom_validation_and_public_copy(self):
        baseline = build_universe("v9names", 741903, planet_generator="planet-v9", preset="continental")
        geo = baseline["geography"]["v9names-planet-reach"]
        feature = geo["surface"]["hydrography"]["features"][0]
        generated = build_universe("v9names", 741903, planet_generator="planet-v9", preset="continental", feature_names="generated")
        again = build_universe("v9names", 741903, planet_generator="planet-v9", preset="continental", feature_names="generated")
        self.assertEqual(generated, again)
        self.assertEqual(generated["geography"]["v9names-planet-reach"]["surface"]["hydrography"],
                         again["geography"]["v9names-planet-reach"]["surface"]["hydrography"])
        custom = build_universe("v9names", 741903, planet_generator="planet-v9", preset="continental",
                                feature_name_overrides={"v9names-planet-reach": {feature["id"]: "  Tír'Sea  "}})
        named = next(f for f in custom["geography"]["v9names-planet-reach"]["surface"]["hydrography"]["features"] if f["id"] == feature["id"])
        self.assertEqual(("Tír'Sea", "custom"), (named["name"], named["name_source"]))
        expected = copy.deepcopy(baseline)
        expected_feature = expected["geography"]["v9names-planet-reach"]["surface"]["hydrography"]["features"][0]
        expected_feature.update(name="Tír'Sea", name_source="custom")
        self.assertEqual(expected, custom)
        Store.validate_state(V2_SCHEMA, V2_RULES, 0, custom)
        public = public_state_v2(custom)
        self.assertEqual({"v9names-planet-reach"}, set(public["geography"]))
        projected = public["geography"]["v9names-planet-reach"]["surface"]["hydrography"]["features"][0]
        projected["cells"].clear()
        self.assertTrue(custom["geography"]["v9names-planet-reach"]["surface"]["hydrography"]["features"][0]["cells"])

    def test_bad_names_and_contract_mutations_rejected(self):
        for name in ("", " \t ", "line\nbreak", "x\u202ey", "x\u200by", "x" * 81,
                     "\u2028name", "name\u2029", "x\u2028y", "x\u2029y"):
            with self.assertRaises(ValueError):
                clean_name(name)
        self.assertEqual("café", clean_name("cafe\u0301"))
        state = build_universe("v9invalid", 12, planet_generator="planet-v9", preset="continental")
        geo = state["geography"]["v9invalid-planet-reach"]
        feature = geo["surface"]["hydrography"]["features"][0]
        cases = []
        altered = copy.deepcopy(state); altered["geography"]["v9invalid-planet-reach"]["surface"]["hydrography"]["features"][0]["cells"][0] = True; cases.append(altered)
        altered = copy.deepcopy(state); altered["geography"]["v9invalid-planet-reach"]["surface"]["hydrography"]["features"][0]["name"] = "x\n"; altered["geography"]["v9invalid-planet-reach"]["surface"]["hydrography"]["features"][0]["name_source"] = "custom"; cases.append(altered)
        altered = copy.deepcopy(state); altered["_private"]["generator_config"]["feature_names"] = "generated"; cases.append(altered)
        for bad in cases:
            with self.assertRaises(ValueError):
                Store.validate_state(V2_SCHEMA, V2_RULES, 0, bad)
        self.assertNotIn("hydrography", feature)

    def test_feature_contract_rejects_mutations_without_normalizing(self):
        geo = generate_planet_v9("contract", 987, "continental", naming="generated")
        mutations = [
            lambda f: f.update(private={"secret": "canary"}),
            lambda f: f.pop("material"),
            lambda f: f.update(cells=[]),
            lambda f: f.update(cells=[-1]),
            lambda f: f.update(cells=[True]),
            lambda f: f.update(anchor=True),
            lambda f: f.update(anchor=-1),
            lambda f: f.update(name_source="unknown"),
            lambda f: f.update(name="WrongGeneratedName"),
        ]
        for name in (" name ", "cafe\u0301", "\u2028name", "name\u2029", "line\nbreak"):
            mutations.append(lambda f, name=name: f.update(name=name, name_source="custom"))
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(geo)
            mutate(bad["surface"]["hydrography"]["features"][0])
            original = copy.deepcopy(bad)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                validate_surface(bad)
            self.assertEqual(original, bad)

    def test_malformed_rivers_raise_value_error_before_hydrography(self):
        for preset in ("continental", "arid"):
            geo = generate_planet_v9("malformed", 987, preset)
            for rivers in (None, "bad", [{"id": "x"}]):
                bad = copy.deepcopy(geo)
                bad["surface"]["rivers"] = rivers
                with self.subTest(preset=preset, rivers=rivers), self.assertRaises(ValueError):
                    validate_surface(bad)

    def test_river_anchor_uses_saved_land_route_midpoint(self):
        state = build_universe("archreview", 741903, planet_generator="planet-v9", preset="continental", feature_names="generated")
        geo = state["geography"]["archreview-planet-reach"]
        feature = next(f for f in geo["surface"]["hydrography"]["features"] if f["id"] == "archreview-reach-river-9394")
        river = next(r for r in geo["surface"]["rivers"] if r["id"] == feature["id"])
        width = geo["planet"]["width"]
        land = [y * width + x for x, y in river["points"] if geo["terrain_grid"][y * width + x] != "o"]
        materials = geo["surface"]["materials"]
        candidates = [i for i in land if materials["lake_mask"][i] == "0" and materials["ice_mask"][i] == "0"] or land
        self.assertEqual(candidates[len(candidates)//2], feature["anchor"])
        self.assertNotEqual("o", geo["terrain_grid"][feature["anchor"]])
        self.assertIn(feature["anchor"], feature["cells"])

    def test_options_reject_legacy_modes_and_cli_catalog_needs_no_database(self):
        for version in ("planet-v1", "planet-v8"):
            with self.assertRaises(ValueError):
                build_universe("legacy", 1, planet_generator=version, feature_names="none")
            result = subprocess.run([sys.executable, "-m", "app.cli", "init-v2", "--planet-generator", version,
                                     "--feature-names", "none"], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("requires --planet-generator planet-v9", result.stderr)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "names.json"
            path.write_text('{"catalog-planet-reach":{"x":"y","x":"z"}}', encoding="utf8")
            command = [sys.executable, "-m", "app.cli", "init-v2", "--campaign-id", "catalog",
                       "--planet-generator", "planet-v9", "--preset", "continental",
                       "--feature-names-file", str(path), "--catalog"]
            env = {**os.environ, "WOLD_DATABASE_URL": "postgresql://invalid.invalid/no-db"}
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("duplicate JSON key", result.stderr)
            path.write_text("{}", encoding="utf8")
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("uncommitted_creation_preview", json.loads(result.stdout)["status"])
            catalog = json.loads(result.stdout)["catalog"]
            self.assertTrue(catalog)
            self.assertTrue(all(set(row) == {"planet_id", "feature_id", "kind", "material", "cell_count", "anchor", "name"} for row in catalog))
            from app.cli import main
            output = io.StringIO()
            with patch.dict(os.environ, {"WOLD_DATABASE_URL": env["WOLD_DATABASE_URL"]}), \
                    patch.object(sys, "argv", ["hammer-world", *command[3:]]), \
                    patch("app.cli.Store.__init__", side_effect=AssertionError("catalog constructed Store")), \
                    contextlib.redirect_stdout(output):
                main()
            self.assertEqual("uncommitted_creation_preview", json.loads(output.getvalue())["status"])


class PlanetV9PersistenceTests(PostgresTestCase, unittest.TestCase):
    def test_nested_feature_canaries_stay_out_of_public_map_and_archive(self):
        self.db.create_demo_v2("canary-v9", seed=741903, planet_generator="planet-v9", preset="continental", feature_names="generated")
        snapshot = self.db.current("canary-v9")["snapshot"]
        state = snapshot["state"]
        for planet_id, geo in state["geography"].items():
            for feature in geo["surface"]["hydrography"]["features"]:
                feature["_private"] = {"nested": ["FEATURE_PRIVATE_CANARY"]}
                if planet_id != "canary-v9-planet-reach":
                    feature["name"] = "HIDDEN_NAME_CANARY"
        original = copy.deepcopy(state)
        public = public_state_v2(state)
        player = self.db.player_state(snapshot)
        with patch.object(self.db, "current", return_value={"snapshot": snapshot}):
            maps = [self.db.map_view("canary-v9", "planet", f"canary-v9-planet-{suffix}") for suffix in ("reach", "ash")]
            with self.assertRaises(KeyError):
                self.db.map_view("canary-v9", "planet", "canary-v9-planet-haven")
        with patch.object(self.db, "_snapshot", return_value=snapshot):
            claim = self.db.claim_archive("canary-worker", 60, {"demo": "demo-folder"})
        archive = json.loads(claim["payload_bytes"])
        for result in (public, player, *maps, archive):
            encoded = json.dumps(result)
            self.assertNotIn("FEATURE_PRIVATE_CANARY", encoded)
            self.assertNotIn("HIDDEN_NAME_CANARY", encoded)
        features = public["geography"]["canary-v9-planet-reach"]["surface"]["hydrography"]["features"]
        self.assertTrue(all(set(f) == {"id", "kind", "material", "cells", "anchor", "name", "name_source"} for f in features))
        direct = project_surface(state["geography"]["canary-v9-planet-reach"])
        direct["surface"]["hydrography"]["features"][0]["cells"].clear()
        features[0]["cells"].clear()
        self.assertEqual(original, state)

    def test_saved_names_survive_history_and_restore(self):
        sid = self.db.create_demo_v2("saved-v9", seed=321, planet_generator="planet-v9",
                                     preset="continental", feature_names="generated")
        initial = self.db.current("saved-v9")["snapshot"]
        state = initial["state"]
        first_geo = state["geography"]["saved-v9-planet-reach"]
        features = first_geo["surface"]["hydrography"]["features"]
        self.assertTrue(any(f["name_source"] == "generated" for f in features))
        public = self.db.player_state(initial)
        self.assertEqual(set(public["geography"]), {"saved-v9-planet-reach"})
        proposal = {"schema_version":V2_SCHEMA, "rules_version":V2_RULES, "base_turn":0,
            "base_hash":initial["state_hash"], "submission_id":"persist-hydrography", "narrative":"Fixture report.",
            "orders":{"allocations":[
                {"settlement_id":"saved-v9-forge", **{key:0 for key in ALLOCATIONS}, "farmers":300},
                {"settlement_id":"saved-v9-outpost", **{key:0 for key in ALLOCATIONS}, "farmers":100}], "actions":[]}}
        self.db.commit("saved-v9", proposal)
        current = self.db.current("saved-v9")["snapshot"]
        self.assertEqual(current["state"]["geography"], state["geography"])
        self.assertEqual(self.db.snapshot(sid)["state"]["geography"], state["geography"])
        history, total = self.db.history("saved-v9")
        self.assertEqual(total, 2)
        self.assertTrue(all(row["state"]["geography"] == state["geography"] for row in history))
        self.db.restore("saved-v9", sid, "restored-v9")
        restored = self.db.current("restored-v9")["snapshot"]["state"]
        self.assertEqual(state["geography"], restored["geography"])
        self.assertEqual(self.db.current("saved-v9")["snapshot"]["state_hash"], current["state_hash"])
        Store.validate_state(V2_SCHEMA, V2_RULES, 0, restored)


if __name__ == "__main__":
    unittest.main()
