"""Recorded owned movement is public; foreign orders remain private."""
import copy
import unittest

from app.engine_v2 import advance
from app.universe import V2_RULES, V2_SCHEMA, build_universe, public_state_v2


class MovementProjectionTests(unittest.TestCase):
    def setUp(self):
        self.state = build_universe("movement", 44)

    def step(self, actions=()):
        self.state, _ = advance(self.state, {
            "schema_version": V2_SCHEMA, "rules_version": V2_RULES,
            "base_turn": self.state["turn"], "base_hash": "0" * 64,
            "submission_id": f"movement-{self.state['turn'] + 1}",
            "orders": {"allocations": [], "actions": list(actions)}, "narrative": "",
        })
        return public_state_v2(self.state)

    def test_ground_connector_uses_recorded_endpoints_and_disappears_on_arrival(self):
        self.step([{"type": "recruit", "settlement_id": "movement-forge"}])
        unit = next(u for u in self.state["units"] if u["owner"] == "player")
        origin = unit["location_id"]
        target = next(u["location_id"] for u in self.state["units"] if u["owner"] == "enemy")
        projected = self.step([{"type": "deploy_unit", "unit_id": unit["id"],
                                "destination_province_id": target, "source_id": "movement-forge"}])
        moving = next(u for u in projected["units"] if u["id"] == unit["id"])
        self.assertIsNone(moving["location_id"])
        self.assertEqual({k: moving[k] for k in ("origin_province_id", "destination_province_id",
                                                "departure_turn", "moving_until", "supply_source_id")},
                         {"origin_province_id": origin, "destination_province_id": target,
                          "departure_turn": 2, "moving_until": 3, "supply_source_id": "movement-forge"})
        arrived = next(u for u in self.step()["units"] if u["id"] == unit["id"])
        self.assertEqual(arrived["location_id"], target)
        self.assertIsNone(arrived["moving_until"])
        for key in ("origin_province_id", "destination_province_id", "departure_turn"):
            self.assertNotIn(key, arrived)

    def test_fleet_system_remains_origin_until_recorded_arrival(self):
        fleet = next(f for f in self.state["fleets"] if f["owner"] == "player")
        origin = fleet["system_id"]
        destination = "movement-system-glimmer"
        projected = self.step([{"type": "fleet_move", "fleet_id": fleet["id"],
                                "destination_system_id": destination, "source_id": "movement-forge"}])
        moving = next(f for f in projected["fleets"] if f["id"] == fleet["id"])
        self.assertEqual({k: moving[k] for k in ("system_id", "destination_system_id", "origin_settlement_id",
                                                "departure_turn", "moving_until")},
                         {"system_id": origin, "destination_system_id": destination,
                          "origin_settlement_id": "movement-forge", "departure_turn": 1, "moving_until": 3})
        waiting = next(f for f in self.step()["fleets"] if f["id"] == fleet["id"])
        self.assertEqual(waiting["system_id"], origin)
        arrived = next(f for f in self.step()["fleets"] if f["id"] == fleet["id"])
        self.assertEqual(arrived["system_id"], destination)
        self.assertIsNone(arrived["moving_until"])
        for key in ("destination_system_id", "origin_settlement_id", "departure_turn"):
            self.assertNotIn(key, arrived)

    def test_foreign_live_movement_never_changes_frozen_projection(self):
        before = public_state_v2(self.state)
        foreign_unit = next(u for u in self.state["units"] if u["owner"] != "player")
        foreign_fleet = next(f for f in self.state["fleets"] if f["owner"] != "player")
        foreign_unit.update({"location_id": None, "origin_province_id": "secret-origin",
                             "destination_province_id": "secret-destination", "departure_turn": 99,
                             "moving_until": 100, "supply_source_id": "secret-source"})
        foreign_fleet.update({"system_id": "secret-system", "location_id": "secret-location",
                              "destination_system_id": "secret-destination", "origin_settlement_id": "secret-origin",
                              "departure_turn": 99, "moving_until": 100})
        # Even copied observation metadata must not open a new foreign-order field.
        for entity in (foreign_unit, foreign_fleet):
            entity["intel"].update(copy.deepcopy({k: v for k, v in entity.items()
                                                 if k not in ("intel", "location_id", "system_id")}))
        after = public_state_v2(self.state)
        for collection in ("units", "fleets"):
            self.assertEqual([x for x in before[collection] if x["owner"] == "foreign"],
                             [x for x in after[collection] if x["owner"] == "foreign"])


if __name__ == "__main__":
    unittest.main()
