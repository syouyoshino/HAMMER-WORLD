"""Independent checks of public boundaries and recoverable v2 transactions."""
import copy
import importlib
import json
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.engine_v2 import ALLOCATIONS, V2_RULES, V2_SCHEMA
from app.store import Store
from app.universe import build_universe
from tests.pg_fixture import PostgresTestCase


class V2AcceptanceTests(PostgresTestCase, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.initial = self.db.create_demo_v2("acceptance", seed=9234)
        self.db.create_pregame("campaign")

    def proposal(self, submission, actions=None):
        snapshot = self.db.current("acceptance")["snapshot"]
        allocations = [{"settlement_id": "acceptance-forge", **{key: 0 for key in ALLOCATIONS}, "farmers": 300},
                       {"settlement_id": "acceptance-outpost", **{key: 0 for key in ALLOCATIONS}, "farmers": 100}]
        return {"schema_version": V2_SCHEMA, "rules_version": V2_RULES, "base_turn": snapshot["turn"],
                "base_hash": snapshot["state_hash"], "submission_id": submission, "narrative": "Public fixture report.",
                "orders": {"allocations": allocations, "actions": actions or []}}

    def test_generated_hierarchy_persists_all_planets_and_separate_domain_seeds(self):
        first = build_universe("acceptance", 9234)
        second = build_universe("acceptance", 9234)
        changed = build_universe("acceptance", 9235)
        self.assertEqual(first, second)
        planets = {n["id"] for n in first["nodes"] if n["kind"] == "planet"}
        self.assertEqual(set(first["geography"]), planets)
        self.assertNotEqual(first["geography"], changed["geography"])
        hidden = next(n for n in first["nodes"] if n["kind"] == "planet" and n["knowledge"] == "hidden")
        projected = Store.player_state(self.db.snapshot(self.initial))
        self.assertNotIn(hidden["id"], json.dumps(projected))
        self.assertEqual(set(projected["geography"]), {"acceptance-planet-reach"})
        before = self.db.snapshot(self.initial)["state"]["geography"]
        self.db.commit("acceptance", self.proposal("no-regeneration"))
        self.assertEqual(before, self.db.current("acceptance")["snapshot"]["state"]["geography"])

    def test_calculated_invalid_state_cannot_commit_partial_revision(self):
        current = self.db.current("acceptance")["snapshot"]
        malformed = copy.deepcopy(current["state"])
        malformed["turn"] += 1
        malformed["settlements"][0]["stocks"]["food"] = -1
        with patch("app.store.engine_v2.advance", return_value=(malformed, {})):
            with self.assertRaises(ValueError):
                self.db.commit("acceptance", self.proposal("invalid-calculator"))
        self.assertEqual(self.db.current("acceptance")["snapshot"]["id"], self.initial)
        history, total = self.db.history("acceptance")
        self.assertEqual(total, 1)
        self.assertEqual(len(history), 1)

    def test_nested_outcome_and_intelligence_fields_never_bypass_projection(self):
        self.db.commit("acceptance", self.proposal("nested-projection", [{"type": "recruit", "settlement_id": "acceptance-forge"}]))
        snapshot = copy.deepcopy(self.db.current("acceptance")["snapshot"])
        marker = "CONFIDENTIAL_GM_SENTINEL"
        state = snapshot["state"]
        state["latest_outcome"]["actions"][0]["_private"] = marker
        state["latest_outcome"]["production"]["acceptance-forge"]["gm_report"] = marker
        state["latest_budget"]["spending"]["acceptance-forge"]["_private"] = marker
        state["discoveries"] = [{"turn": 1, "entity_id": "acceptance-adversary-home", "kind": "investigated",
                                 "observed": {"confidence": "low", "civilian_population_range": {"min": 0, "max": 99, "_private": marker}, "_private": marker}}]
        projected = Store.player_state(snapshot)
        self.assertNotIn(marker, json.dumps(projected))
        main = importlib.import_module("app.main")
        history_row = {**snapshot, "archive_status": "pending"}
        with patch.object(main, "store", self.db), patch.object(self.db, "history", return_value=([history_row], 1)):
            result = TestClient(main.app).get("/api/player/campaigns/acceptance/history")
            self.assertEqual(result.status_code, 200)
            self.assertNotIn(marker, result.text)

    def test_player_private_api_filters_all_views_and_unauthorized_history(self):
        main = importlib.import_module("app.main")
        env = {"WOLD_ACCESS_MODE": "private", "WOLD_GM_TOKEN": "acceptance-gm-token",
               "WOLD_PLAYER_TOKEN": "acceptance-player-token", "WOLD_PLAYER_CAMPAIGNS": "acceptance"}
        with patch.object(main, "store", self.db), patch.dict(os.environ, env):
            client = TestClient(main.app)
            headers = {"Authorization": "Bearer acceptance-player-token"}
            self.assertEqual(client.get("/api/player/campaigns").status_code, 401)
            campaigns = client.get("/api/player/campaigns", headers=headers).json()
            self.assertEqual([c["id"] for c in campaigns], ["acceptance"])
            self.assertEqual(client.get("/api/player/campaigns/campaign/history", headers=headers).status_code, 404)
            self.assertEqual(client.get("/api/admin/campaigns/acceptance/packet", headers=headers).status_code, 401)
            routes = ["/api/player/campaigns/acceptance", "/api/player/campaigns/acceptance/history",
                      f"/api/player/snapshots/{self.initial}",
                      "/api/player/campaigns/acceptance/map?level=galactic",
                      "/api/player/campaigns/acceptance/map?level=sector&node_id=acceptance-sector-hearth",
                      "/api/player/campaigns/acceptance/map?level=system&node_id=acceptance-system-hearth",
                      "/api/player/campaigns/acceptance/map?level=planet&node_id=acceptance-planet-reach"]
            sections = ("overview", "economy", "budget", "logistics", "construction", "research", "military",
                        "diplomacy", "intelligence", "exploration", "colonies", "characters", "orders")
            routes += [f"/api/player/campaigns/acceptance/systems?section={section}" for section in sections]
            for route in routes:
                result = client.get(route, headers=headers)
                self.assertEqual(result.status_code, 200, route)
                for secret in ("_private", "seeded_marker", "enemy_allocations", "generation_nonce", "acceptance-system-dusk", "acceptance-planet-veil"):
                    self.assertNotIn(secret, result.text, route)
            for level, node in (("sector", "acceptance-sector-frontier"), ("system", "acceptance-system-dusk"), ("planet", "acceptance-planet-veil")):
                result = client.get(f"/api/player/campaigns/acceptance/map?level={level}&node_id={node}", headers=headers)
                # Detected Frontier may have an empty map. Hidden nodes never do.
                self.assertEqual(result.status_code, 200 if node.endswith("frontier") else 404)

    def test_historical_fog_restores_without_mutating_original_and_new_ids_use_branch(self):
        first = self.proposal("survey-start", [{"type": "explore", "source_id": "acceptance-forge", "node_id": "acceptance-planet-ash"}])
        self.db.commit("acceptance", first)
        for number in (2, 3):
            self.db.commit("acceptance", self.proposal(f"survey-wait-{number}"))
        live = self.db.map_view("acceptance", "planet", "acceptance-planet-ash")
        old = self.db.map_view("acceptance", "planet", "acceptance-planet-ash", self.initial)
        self.assertIsNotNone(live["geometry"])
        self.assertIsNone(old["geometry"])
        branch_id = self.db.restore("acceptance", self.initial, "acceptance-branch")
        branch = self.db.snapshot(branch_id)
        original = self.db.snapshot(self.initial)
        self.assertEqual(branch["state"]["geography"], original["state"]["geography"])
        self.assertEqual(branch["state"]["nodes"], original["state"]["nodes"])
        self.assertEqual(branch["state"]["_private"]["campaign_id"], "acceptance-branch")
        payload = self.proposal("same-key", [{"type": "recruit", "settlement_id": "acceptance-forge"}])
        payload["base_turn"] = branch["turn"]
        payload["base_hash"] = branch["state_hash"]
        self.db.commit("acceptance-branch", payload)
        self.db.commit("acceptance", self.proposal("same-key", [{"type": "recruit", "settlement_id": "acceptance-forge"}]))
        branch_unit = next(u["id"] for u in self.db.current("acceptance-branch")["snapshot"]["state"]["units"] if u["owner"] == "player")
        original_unit = next(u["id"] for u in self.db.current("acceptance")["snapshot"]["state"]["units"] if u["owner"] == "player")
        self.assertNotEqual(branch_unit, original_unit)
        self.assertEqual(self.db.snapshot(self.initial)["state_hash"], original["state_hash"])
        with self.assertRaises(KeyError):
            self.db.map_view("acceptance", "planet", "acceptance-planet-reach", branch_id)


if __name__ == "__main__":
    unittest.main()
