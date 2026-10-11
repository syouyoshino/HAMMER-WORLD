"""Exact owned-resource accounting across meals, transfers and paid fixture rules."""
import unittest
from unittest.mock import patch

from app.engine_v2 import ALLOCATIONS, V2_RULES, V2_SCHEMA, advance
from app.universe import RESOURCES, build_universe, owned_resources
from tests.pg_fixture import PostgresTestCase


def proposal(state, actions=None, workers=None, state_hash="0" * 64):
    campaign=state["_private"]["campaign_id"]
    allocations=[{"settlement_id":s["id"], **{k:0 for k in ALLOCATIONS},
                  **({"farmers":300 if s["id"]==campaign+"-forge" else 100} if workers is None else workers)}
                 for s in state["settlements"] if s["owned"] and s["planet_id"]==campaign+"-planet-reach"]
    return {"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":state["turn"],
            "base_hash":state_hash,"submission_id":f"ledger-{state['turn']+1}","narrative":"",
            "orders":{"actions":actions or [],"allocations":allocations}}


class LedgerAssertions:
    def assert_balanced(self, before, after, outcome):
        ledger=outcome["resources"]
        self.assertEqual(ledger["opening"],owned_resources(before))
        self.assertEqual(ledger["closing"],owned_resources(after))
        for resource in RESOURCES:
            inflow=sum(row.get(resource,0) for row in ledger["inflows"].values())
            outflow=sum(row.get(resource,0) for row in ledger["outflows"].values())
            self.assertEqual(ledger["opening"][resource]+inflow-outflow,ledger["closing"][resource],resource)
            self.assertEqual(outcome["total_consumption"][resource],sum(row.get(resource,0)
                for category,row in ledger["outflows"].items() if category not in ("trade","destruction")))


class ResourceLedgerTests(LedgerAssertions, unittest.TestCase):
    def setUp(self):
        self.state=build_universe("ledger",612)

    def step(self, actions=None, workers=None):
        before=self.state
        self.state,outcome=advance(before,proposal(before,actions,workers))
        self.assert_balanced(before,self.state,outcome)
        return outcome

    def recruit(self):
        self.step([{"type":"recruit","settlement_id":"ledger-forge"}])
        return next(u for u in self.state["units"] if u["owner"]=="player")

    def deploy(self, unit, destination):
        return self.step([{"type":"deploy_unit","unit_id":unit["id"],"source_id":"ledger-forge",
                           "destination_province_id":destination}])

    def test_return_home_arrival_has_one_paid_meal(self):
        unit=self.recruit()
        enemy=next(u for u in self.state["units"] if u["owner"]=="enemy")
        self.deploy(unit,enemy["location_id"])
        self.step()
        home=self.state["settlements"][0]
        unit=next(u for u in self.state["units"] if u["owner"]=="player")
        self.deploy(unit,home["province_id"])
        arrival=self.step()
        self.assertEqual(arrival["resources"]["outflows"]["meals"]["food"],1200)
        self.assertEqual(arrival["consumption"][home["id"]]["food"],890)
        self.assertEqual(next(u for u in self.state["units"] if u["owner"]=="player")["location_id"],home["province_id"])

    def test_defeated_departure_cancels_march_and_returns_unused_food(self):
        unit=self.recruit(); forge=self.state["settlements"][0]
        forge["stocks"]["food"]=10  # All paid into cargo, leaving no departure meal.
        enemy=next(u for u in self.state["units"] if u["owner"]=="enemy")
        outcome=self.step([{"type":"deploy_unit","unit_id":unit["id"],"source_id":forge["id"],
            "destination_province_id":enemy["location_id"]}],workers={})
        dead=next(u for u in self.state["units"] if u["owner"]=="player")
        self.assertEqual(dead["strength"],0)
        self.assertIsNone(dead["moving_until"])
        self.assertNotIn("destination_province_id",dead)
        self.assertEqual(dead["transit_food"],0)
        self.assertEqual(self.state["settlements"][0]["stocks"]["food"],10)
        self.assertFalse(any(row["entity_id"]==dead["id"] for row in outcome.get("resource_losses",[])))

    def test_recipes_research_growth_welfare_and_trade_record_actual_flows(self):
        faction=self.state["factions"][0]
        faction["treaties"]=[{"kind":"trade","status":"active","accepted_by_gm":True}]
        actions=[{"type":"research","settlement_id":"ledger-forge","technology_id":"industry-I"},
                 {"type":"set_policy","settlement_id":"ledger-forge","tax_rate":1,"welfare":True,"growth_enabled":True},
                 {"type":"trade","source_id":"ledger-forge","faction_id":faction["id"],"resource":"ore","quantity":3,"direction":"buy"},
                 {"type":"trade","source_id":"ledger-forge","faction_id":faction["id"],"resource":"food","quantity":2,"direction":"sell"}]
        outcome=self.step(actions,{"farmers":200,"miners":10,"technicians":20,"refiners":5,"machinists":4,"scientists":5})
        flows=outcome["resources"]
        self.assertEqual(flows["inflows"]["trade"],{"ore":3,"credits":2})
        self.assertEqual(flows["outflows"]["trade"],{"credits":6,"food":2})
        self.assertEqual(flows["outflows"]["recipes"]["metals"],4)
        self.assertEqual(flows["outflows"]["research"],{"data":5})
        self.assertEqual(flows["outflows"]["growth"],{"food":16})
        self.assertEqual(flows["outflows"]["welfare"],{"credits":5})

    def test_colony_food_transfers_and_travel_meals_balance(self):
        ash=next(n for n in self.state["nodes"] if n["name"]=="Ash")
        ash["knowledge"]="surveyed"
        self.step([{"type":"colonize","fleet_id":"ledger-transport-01","source_id":"ledger-forge","target_planet_id":ash["id"]}])
        travel=self.step(); arrival=self.step()
        self.assertEqual(travel["resources"]["outflows"]["meals"]["food"],1200)
        self.assertEqual(arrival["resources"]["outflows"]["meals"]["food"],1200)
        colony=next(s for s in self.state["settlements"] if s["planet_id"]==ash["id"])
        self.assertEqual(colony["stocks"]["food"],180)
        self.assertEqual(len(self.state["expeditions"]),0)

    def test_orbital_and_remote_rations_included_in_total_consumption(self):
        unit=self.recruit()
        enemy=next(u for u in self.state["units"] if u["owner"]=="enemy")
        self.deploy(unit,enemy["location_id"]); self.step()
        fleet=self.state["fleets"][0]; fleet["settlement_id"]=None
        outcome=self.step()
        local=sum(row["food"] for row in outcome["consumption"].values())
        self.assertEqual(outcome["total_consumption"]["food"],local+20)

    def test_dispatch_resupply_and_fleet_travel_are_internal_except_meals_and_burn(self):
        destination=self.state["links"][0]["b"]
        outcome=self.step([
            {"type":"dispatch","source_id":"ledger-forge","destination_id":"ledger-outpost","resource":"ore","quantity":20},
            {"type":"resupply_fleet","source_id":"ledger-forge","fleet_id":"ledger-transport-01","food_quantity":30,"promethium_quantity":5},
            {"type":"fleet_move","fleet_id":"ledger-transport-01","destination_system_id":destination,"source_id":"ledger-forge"}])
        self.assertEqual(outcome["resources"]["outflows"]["action_costs"],{"promethium":5})
        second=self.step(); third=self.step()
        self.assertEqual(second["resources"]["outflows"]["meals"]["food"],1200)
        self.assertEqual(third["resources"]["outflows"]["meals"]["food"],1200)
        fleet=self.state["fleets"][0]
        self.assertIsNone(fleet["moving_until"])
        self.assertEqual(fleet["food_reserve"],130)

    def test_destroyed_colonizer_loses_cargo_once(self):
        ash=next(n for n in self.state["nodes"] if n["name"]=="Ash")
        ash["knowledge"]="surveyed"
        forge=self.state["settlements"][0]; forge["stocks"]["food"]=400
        outcome=self.step([{"type":"colonize","fleet_id":"ledger-transport-01","source_id":"ledger-forge","target_planet_id":ash["id"]}],workers={})
        self.assertEqual(outcome["resources"]["outflows"]["destruction"],{"food":500,"promethium":20})
        self.assertFalse(self.state["expeditions"])
        self.assertEqual(self.state["fleets"][0]["crew"],0)
        next_turn=self.step(workers={})
        self.assertNotIn("destruction",next_turn["resources"]["outflows"])

    def test_unrecorded_resource_mutation_fails_closed(self):
        def corrupt(state, *args): state["settlements"][0]["stocks"]["ore"]-=1
        with patch("app.engine_v2._resolve_battles",side_effect=corrupt):
            with self.assertRaisesRegex(ValueError,"resource reconciliation invariant failed: ore"):
                self.step()

    def test_missing_exploration_baseline_is_not_regenerated(self):
        ash=next(n for n in self.state["nodes"] if n["name"]=="Ash")
        self.step([{"type":"explore","source_id":"ledger-forge","node_id":ash["id"]}])
        self.step()
        del self.state["geography"][ash["id"]]
        with self.assertRaisesRegex(ValueError,"no persisted geography"):
            self.step()


class PersistentLedgerTests(LedgerAssertions, PostgresTestCase, unittest.TestCase):
    def test_committed_ledger_and_reconciliation_failure_are_atomic(self):
        self.db.create_demo_v2("ledger",seed=612)
        first=self.db.current("ledger")["snapshot"]
        self.db.commit("ledger",proposal(first["state"],[{"type":"recruit","settlement_id":"ledger-forge"}],state_hash=first["state_hash"]))
        committed=self.db.current("ledger")["snapshot"]
        self.assert_balanced(first["state"],committed["state"],committed["state"]["latest_outcome"])
        history_before=self.db.history("ledger")[1]
        def corrupt(state,*args): state["settlements"][0]["stocks"]["ore"]-=1
        with patch("app.engine_v2._resolve_battles",side_effect=corrupt):
            with self.assertRaisesRegex(ValueError,"resource reconciliation"):
                self.db.commit("ledger",proposal(committed["state"],state_hash=committed["state_hash"]))
        self.assertEqual(self.db.current("ledger")["snapshot"]["id"],committed["id"])
        self.assertEqual(self.db.history("ledger")[1],history_before)
        self.assertEqual(self.db.archive_outbox(committed["id"])["status"],"pending")


if __name__=="__main__": unittest.main()
