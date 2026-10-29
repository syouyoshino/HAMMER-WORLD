"""Saved astronomy compatibility, privacy and transactional retention checks."""
import copy
import importlib
import json
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import astronomy
from app.engine import digest
from app.store import Store
from app.universe import V2_RULES, V2_SCHEMA, build_universe, public_state_v2
from tests.pg_fixture import PostgresTestCase


class AstronomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = build_universe("astro", 55, astronomy="static-v1")

    def test_defaults_preserve_prior_private_and_public_digests(self):
        # Goldens captured from the committed pre-astronomy implementation.
        state = build_universe("compat", 55)
        self.assertEqual(digest(state), "9e3c144d1145d607b52f3806c840d955c76157db003a00764370a023c0aff5df")
        self.assertEqual(digest(public_state_v2(state)), "21d4269240bde41c3589cdebcbfdf26b72d293c614dd64ba97aa49bdaadec8b0")
        self.assertNotIn("astronomy", state)
        self.assertNotIn("astronomy", public_state_v2(state))

    def test_generation_is_deterministic_order_independent_and_isolated(self):
        first = self.state["astronomy"]
        self.assertEqual(first, build_universe("astro", 55, astronomy="static-v1")["astronomy"])
        self.assertEqual(first, astronomy.generate(list(reversed(self.state["nodes"])), 55))
        self.assertNotEqual(first, astronomy.generate(self.state["nodes"], 56))
        legacy = build_universe("astro", 55)
        new = copy.deepcopy(self.state)
        del new["astronomy"]
        del new["_private"]["generator_config"]["astronomy"]
        self.assertEqual(new, legacy, "Astronomy must not perturb terrain or simulation initialization")
        Store.validate_state(V2_SCHEMA, V2_RULES, 0, self.state)

    def test_malformed_or_intersecting_records_are_rejected(self):
        system = "astro-system-hearth"
        star, planet, neighbour = (f"astro-{suffix}" for suffix in
                                   ("system-hearth-star", "planet-reach", "planet-ash"))
        bad = []
        def mutate(change):
            state = copy.deepcopy(self.state)
            change(state)
            bad.append(state)
        mutate(lambda s: s.__setitem__("astronomy", None))
        mutate(lambda s: s["astronomy"].__setitem__("epoch_turn", False))
        for field, value in (("version", "future"), ("motion", "moving"),
                             ("position_unit", "pixels"), ("frame", "unknown"),
                             ("planet_frame", "unknown")):
            mutate(lambda s, k=field, v=value: s["astronomy"].__setitem__(k, v))
        mutate(lambda s: s["_private"]["generator_config"].pop("astronomy"))
        mutate(lambda s: s.pop("astronomy"))
        mutate(lambda s: s["astronomy"]["systems"][system]["bodies"].__setitem__(star, None))
        mutate(lambda s: s["astronomy"]["systems"][system]["bodies"][star].pop("radius_km"))
        for position in ([True, 0, 0], [float("nan"), 0, 0], [100_000_001, 0, 0], [1, 0, 0]):
            mutate(lambda s, p=position: s["astronomy"]["systems"][system]["bodies"][planet].__setitem__("position", p))
        mutate(lambda s: s["astronomy"]["systems"][system]["bodies"][star].__setitem__("position", [1, 0, 0]))
        mutate(lambda s: s["astronomy"]["systems"][system]["bodies"][planet].__setitem__("radius_km", True))
        mutate(lambda s: s["astronomy"]["systems"][system]["bodies"].__setitem__("foreign", {"position": [2, 0, 0], "radius_km": 1000}))
        def overlap(s):
            bodies = s["astronomy"]["systems"][system]["bodies"]
            bodies[neighbour]["position"] = list(bodies[planet]["position"])
            bodies[neighbour]["position"][0] += 1
        mutate(overlap)
        for index, state in enumerate(bad):
            with self.subTest(case=index), self.assertRaises(ValueError):
                Store.validate_state(V2_SCHEMA, V2_RULES, 0, state)
        with self.assertRaises(ValueError):
            build_universe("astro", 55, astronomy="unknown")

    def test_public_projection_does_not_leak_unknown_bodies_or_extra_fields(self):
        state = copy.deepcopy(self.state)
        marker = "ASTRONOMY_PRIVATE_SENTINEL"
        state["astronomy"]["private"] = marker
        for system in state["astronomy"]["systems"].values():
            system["private"] = marker
            for body in system["bodies"].values():
                body["private"] = marker
        projected = public_state_v2(state)
        records = projected["astronomy"]["systems"]
        self.assertEqual(set(records), {"astro-system-hearth"})
        self.assertEqual(set(records["astro-system-hearth"]["bodies"]),
                         {"astro-planet-reach", "astro-system-hearth-star"})
        serialized = json.dumps(projected)
        self.assertNotIn(marker, serialized)
        for node in state["nodes"]:
            if node["knowledge"] != "surveyed":
                self.assertNotIn(node["id"], json.dumps(projected["astronomy"]))
            if node["kind"] == "star" and node["knowledge"] == "surveyed":
                node["knowledge"] = "detected"
        rows = public_state_v2(state)["astronomy"]["systems"]["astro-system-hearth"]["bodies"]
        self.assertEqual(set(rows), {"astro-planet-reach"})


class AstronomyPersistenceTests(PostgresTestCase, unittest.TestCase):
    def test_creation_commit_history_restore_and_private_api(self):
        initial_id = self.db.create_demo_v2("astro", 55, astronomy="static-v1")
        self.db.create_demo_v2("old", 55)
        initial = self.db.snapshot(initial_id)
        saved = copy.deepcopy(initial["state"]["astronomy"])
        proposal = {"schema_version": V2_SCHEMA, "rules_version": V2_RULES,
                    "base_turn": 0, "base_hash": initial["state_hash"],
                    "submission_id": "astronomy-retention", "narrative": "Fictional fixture.",
                    "orders": {"allocations": [], "actions": []}}
        self.db.preview("astro", proposal)
        self.db.commit("astro", proposal)
        self.assertEqual(self.db.current("astro")["snapshot"]["state"]["astronomy"], saved)
        self.assertEqual(self.db.snapshot(initial_id), initial)
        self.db.restore("astro", initial_id, "restored")
        self.assertEqual(self.db.current("restored")["snapshot"]["state"]["astronomy"], saved)
        with self.assertRaises(ValueError):
            self.db.create_demo_v2("astro", 99, astronomy="static-v1")
        self.assertNotIn("astronomy", self.db.current("old")["snapshot"]["state"])
        main = importlib.import_module("app.main")
        env = {"WOLD_ACCESS_MODE": "private", "WOLD_GM_TOKEN": "astro-test-gm",
               "WOLD_PLAYER_TOKEN": "astro-test-player", "WOLD_PLAYER_CAMPAIGNS": "astro"}
        with patch.object(main, "store", self.db), patch.dict(os.environ, env):
            client = TestClient(main.app)
            headers = {"Authorization": "Bearer astro-test-player"}
            self.assertEqual(client.get("/api/player/campaigns").status_code, 401)
            self.assertEqual(client.get("/api/player/campaigns/astro").status_code, 404)
            for path in ("/api/player/campaigns/astro", "/api/player/campaigns/astro/history",
                         f"/api/player/snapshots/{initial_id}",
                         "/api/player/campaigns/astro/map?level=system&node_id=astro-system-hearth",
                         "/api/player/campaigns/astro/map?level=planet&node_id=astro-planet-reach"):
                response = client.get(path, headers=headers)
                self.assertEqual(response.status_code, 200, path)
                for secret in ("astro-system-dusk", "astro-planet-ash", "astro-planet-haven",
                               "astro-planet-veil", "_private", "seeded_marker"):
                    # Ash remains a detected chart node, but may never appear in astronomy.
                    target = response.json().get("astronomy", {}) if secret == "astro-planet-ash" else response.text
                    self.assertNotIn(secret, json.dumps(target) if isinstance(target, dict) else target)
            self.assertEqual(client.get("/api/player/campaigns/old", headers=headers).status_code, 404)
            self.assertEqual(client.get(f"/api/player/campaigns/old/map?level=planet&snapshot_id={initial_id}", headers=headers).status_code, 404)


if __name__ == "__main__":
    unittest.main()
