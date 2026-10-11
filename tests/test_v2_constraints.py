"""Economic and logistical scarcity scenarios using the approved fixture rules."""
import unittest

from app.engine_v2 import ALLOCATIONS, V2_RULES, V2_SCHEMA, advance
from app.store import Store
from app.universe import build_universe, owned_humans


class ScarcityTests(unittest.TestCase):
    def setUp(self):
        self.state = build_universe("scarcity", 612)

    def resolve(self, actions=None, forge=None):
        rows = [{"settlement_id": "scarcity-forge", **{key: 0 for key in ALLOCATIONS}, **(forge or {"farmers": 300})},
                {"settlement_id": "scarcity-outpost", **{key: 0 for key in ALLOCATIONS}, "farmers": 100}]
        payload = {"schema_version": V2_SCHEMA, "rules_version": V2_RULES,
                   "base_turn": self.state["turn"], "base_hash": "0" * 64,
                   "submission_id": f"turn-{self.state['turn'] + 1}", "narrative": "",
                   "orders": {"allocations": rows, "actions": actions or []}}
        result, outcome = advance(self.state, payload)
        Store.validate_state(V2_SCHEMA, V2_RULES, result["turn"], result)
        self.state = result
        return outcome

    def test_energy_and_inputs_limit_industry_and_research(self):
        forge = self.state["settlements"][0]
        forge["stocks"].update(energy=0, ore=0, metals=0, data=20)
        outcome = self.resolve([{"type": "research", "settlement_id": forge["id"], "technology_id": "logistics-I"}],
                               {"farmers": 300, "miners": 10, "refiners": 10, "machinists": 10, "scientists": 5})
        output = outcome["production"][forge["id"]]
        self.assertEqual((output["ore"], output["metals"], output["materiel"], output["data"]), (0, 0, 0, 0))
        self.assertEqual(self.state["projects"][0]["work_done"], 0)
        self.assertEqual(self.state["settlements"][0]["stocks"]["data"], 20)

    def test_housing_caps_births_and_new_people_consume_food(self):
        self.state["settlements"][0]["housing"] = 902
        before = owned_humans(self.state)
        outcome = self.resolve([{"type": "set_policy", "settlement_id": "scarcity-forge", "tax_rate": 1,
                                 "welfare": False, "growth_enabled": True}])
        self.assertEqual(sum(item["count"] for item in outcome["births"]), 2)
        self.assertEqual(owned_humans(self.state), before + 2)
        self.assertEqual(self.state["settlements"][0]["stocks"]["food"], 5896)
        second = self.resolve()
        self.assertEqual(second["births"], [])

    def test_completed_ship_project_waits_for_real_crew(self):
        self.state["settlements"][0]["civilians"] = 5
        before = owned_humans(self.state)
        self.resolve([{"type": "build_transport", "settlement_id": "scarcity-forge"}], {"builders": 5})
        for _ in range(3):
            self.resolve(forge={"builders": 5})
        project = next(p for p in self.state["projects"] if p["kind"] == "transport")
        self.assertEqual(project["work_done"], project["work_required"])
        self.assertEqual(len([f for f in self.state["fleets"] if f["owner"] == "player"]), 1)
        self.assertEqual(owned_humans(self.state), before)

    def test_deployed_rations_share_capacity_and_missing_depot_causes_losses(self):
        self.resolve([{"type": "recruit", "settlement_id": "scarcity-forge"}])
        unit = next(u for u in self.state["units"] if u["owner"] == "player")
        enemy = next(u for u in self.state["units"] if u["owner"] == "enemy")
        self.resolve([{"type": "deploy_unit", "unit_id": unit["id"], "destination_province_id": enemy["location_id"], "source_id": "scarcity-forge"}])
        self.resolve()  # Arrives after eating its paid travel ration.
        with self.assertRaisesRegex(ValueError, "depot route capacity"):
            self.resolve([{"type": "dispatch", "source_id": "scarcity-forge", "destination_id": "scarcity-outpost", "resource": "ore", "quantity": 11}])
        self.state["facilities"] = [f for f in self.state["facilities"] if not (f["settlement_id"] == "scarcity-forge" and f["kind"] == "depot")]
        before = owned_humans(self.state)
        outcome = self.resolve()
        self.assertEqual(sum(d["count"] for d in outcome["deaths"]), 10)
        self.assertEqual(owned_humans(self.state), before - 10)
        self.assertEqual(next(u["strength"] for u in self.state["units"] if u["owner"] == "player"), 0)


if __name__ == "__main__":
    unittest.main()
