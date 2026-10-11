import json
import unittest

from app.engine_v2 import ALLOCATIONS, V2_RULES, V2_SCHEMA
from app.store import Store
from app.universe import owned_humans
from tests.pg_fixture import PostgresTestCase


class DemoV2Tests(PostgresTestCase, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.v1=self.db.create_demo("legacy-v1",seed=33)
        self.v2=self.db.create_demo_v2("fixture-v2",seed=44)

    def proposal(self, submission="turn-1", allocations=None, actions=None):
        snap=self.db.current("fixture-v2")["snapshot"]
        return {"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":snap["turn"],
            "base_hash":snap["state_hash"],"submission_id":submission,
            "orders":{"allocations":allocations or [],"actions":actions or []},"narrative":"Fictional report."}

    def allocation(self,sid="fixture-v2-forge",**values):
        return {"settlement_id":sid,**{k:values.get(k,0) for k in ALLOCATIONS}}

    def test_explicit_new_campaign_v2_preserves_v1_and_private_projection(self):
        self.assertEqual(self.db.current("legacy-v1")["snapshot"]["schema_version"],"world-v1")
        current=self.db.current("fixture-v2")["snapshot"]
        self.assertEqual((current["schema_version"],current["rules_version"]),(V2_SCHEMA,V2_RULES))
        projection=self.db.player_state(current)
        serialized=json.dumps(projection)
        for secret in ("_private","seeded_marker","generation_nonce","enemy_allocations","enemy_population"):
            self.assertNotIn(secret,serialized)
        self.assertNotIn("Veil",serialized)
        self.assertIn("Unsurveyed System",serialized)
        self.assertEqual(owned_humans(current["state"]),1200)
        self.assertNotIn("crew",current["state"]["settlements"][0])
        self.assertEqual(current["state"]["fleets"][0]["food_reserve"],100)
        packet=self.db.packet("fixture-v2")
        self.assertEqual(packet["example"]["rules_version"],V2_RULES)

    def test_foreign_projection_uses_frozen_observation_not_live_state(self):
        state=self.db.current("fixture-v2")["snapshot"]["state"]
        before=self.db.player_state(self.db.current("fixture-v2")["snapshot"])
        enemy=next(u for u in state["units"] if u["owner"]=="enemy")
        enemy["strength"]=0; enemy["location_id"]="new-hidden-location"
        settlement=next(s for s in state["settlements"] if not s["owned"])
        settlement["civilians"]=999999; settlement["province_id"]="new-hidden-location"
        after=Store.player_state({"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"state":state})
        before_enemy=next(u for u in before["units"] if u["owner"]=="foreign")
        after_enemy=next(u for u in after["units"] if u["owner"]=="foreign")
        self.assertEqual(before_enemy,after_enemy)
        before_foreign=next(s for s in before["settlements"] if not s["owned"])
        after_foreign=next(s for s in after["settlements"] if not s["owned"])
        self.assertEqual(before_foreign,after_foreign)
        self.assertIsNone(after_foreign["civilians"])

    def test_hidden_nodes_cannot_be_moved_to_or_attacked(self):
        from app.engine_v2 import advance
        base=self.db.current("fixture-v2")["snapshot"]; state=base["state"]
        hidden=next(n["id"] for n in state["nodes"] if n["kind"]=="system" and n["knowledge"]=="hidden")
        move={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":0,"base_hash":base["state_hash"],
            "submission_id":"hidden-move","orders":{"allocations":[],"actions":[{"type":"fleet_move","fleet_id":"fixture-v2-transport-01",
            "destination_system_id":hidden,"source_id":"fixture-v2-forge"}]},"narrative":""}
        with self.assertRaisesRegex(ValueError,"not known"):
            self.db.preview("fixture-v2",move)
        enemy=next(u for u in state["fleets"] if u["owner"]=="enemy")
        enemy["intel"]=None
        attack={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":0,"base_hash":base["state_hash"],
            "submission_id":"hidden-attack","orders":{"allocations":[],"actions":[{"type":"fleet_attack","fleet_id":"fixture-v2-transport-01",
            "target_id":"fixture-v2-enemy-fleet"}]},"narrative":""}
        with self.assertRaisesRegex(ValueError,"recorded intelligence"):
            advance(state,attack)

    def test_turn_production_retry_and_population_conservation(self):
        p=self.proposal(allocations=[self.allocation(farmers=200)])
        preview=self.db.preview("fixture-v2",p)
        self.assertEqual(preview["state"]["settlements"][0]["stocks"]["food"],5600)
        self.assertEqual(self.db.current("fixture-v2")["snapshot"]["turn"],0)
        committed=self.db.commit("fixture-v2",p)
        duplicate=self.db.commit("fixture-v2",p)
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(committed["snapshot_id"],duplicate["snapshot_id"])
        live=self.db.player_state(self.db.current("fixture-v2")["snapshot"])
        self.assertEqual(owned_humans(self.db.current("fixture-v2")["snapshot"]["state"]),1200)

    def test_allocation_conflict_and_action_overspend_roll_back(self):
        duplicate=[self.allocation(),self.allocation()]
        with self.assertRaisesRegex(ValueError,"duplicate settlement"):
            self.db.commit("fixture-v2",self.proposal(allocations=duplicate))
        actions=[{"type":"build","settlement_id":"fixture-v2-forge","facility_kind":"farm"} for _ in range(11)]
        before=self.db.current("fixture-v2")["snapshot"]["id"]
        with self.assertRaisesRegex(ValueError,"insufficient"):
            self.db.commit("fixture-v2",self.proposal(actions=actions))
        self.assertEqual(self.db.current("fixture-v2")["snapshot"]["id"],before)

    def test_strict_actions_reject_unknown_fields_and_wrong_allocations(self):
        with self.assertRaisesRegex(ValueError,"allocation"):
            self.db.preview("fixture-v2",self.proposal(allocations=[{**self.allocation(),"happiness":10}]))
        with self.assertRaisesRegex(ValueError,"fields"):
            self.db.preview("fixture-v2",self.proposal(actions=[{"type":"recruit","settlement_id":"fixture-v2-forge","count":10}]))
        with self.assertRaisesRegex(ValueError,"at most"):
            self.db.preview("fixture-v2",self.proposal(actions=[{"type":"treaty","faction_id":"x","operation":"propose"}]*33))

    def test_recruitment_and_starvation_have_recorded_conservation(self):
        p=self.proposal(actions=[{"type":"recruit","settlement_id":"fixture-v2-forge"}])
        result=self.db.commit("fixture-v2",p)
        s=self.db.current("fixture-v2")["snapshot"]["state"]
        forge=next(x for x in s["settlements"] if x["id"]=="fixture-v2-forge")
        self.assertEqual(forge["civilians"],880)
        self.assertEqual(next(u["strength"] for u in s["units"] if u["owner"]=="player"),10)
        self.assertEqual(result["outcome"]["turn"],1)
        self.assertEqual(owned_humans(s),1200)
        state=s
        state["settlements"][0]["stocks"]["food"]=0
        p2=self.proposal(submission="starve",allocations=[self.allocation(miners=100)])
        p2["base_turn"]=state["turn"]
        p2["base_hash"]=Store.snapshot_hash("fixture-v2",state["turn"],state,V2_SCHEMA,V2_RULES)
        # Resolve directly to exercise starvation while keeping stored history immutable.
        from app.engine_v2 import advance
        new,outcome=advance(state,p2)
        self.assertTrue(outcome["deaths"])
        self.assertLess(owned_humans(new),1200)
        forge=next(s for s in new["settlements"] if s["id"]=="fixture-v2-forge")
        self.assertEqual(forge["civilians"],0)
        self.assertTrue(all(value==0 for value in forge["allocations"].values()))
        self.assertEqual(outcome["allocations"][forge["id"]]["miners"],100)
        Store.validate_state(V2_SCHEMA,V2_RULES,new["turn"],new)

    def test_multiple_research_projects_share_productive_lab_capacity(self):
        from app.engine_v2 import advance
        snap=self.db.current("fixture-v2")["snapshot"]
        state=json.loads(json.dumps(snap["state"]))
        forge=next(s for s in state["settlements"] if s["id"]=="fixture-v2-forge")
        forge["stocks"]["energy"]=1; forge["stocks"]["data"]=0
        proposal=self.proposal("competing-research",allocations=[self.allocation(technicians=1,scientists=1)],actions=[
            {"type":"research","settlement_id":forge["id"],"technology_id":"logistics-I"},
            {"type":"research","settlement_id":forge["id"],"technology_id":"industry-I"}])
        proposal["base_hash"]=Store.snapshot_hash("fixture-v2",state["turn"],state,V2_SCHEMA,V2_RULES)
        result,outcome=advance(state,proposal)
        projects=[p for p in result["projects"] if p["kind"]=="research"]
        self.assertEqual(sum(p["work_done"] for p in projects),1)
        self.assertEqual(outcome["allocations"][forge["id"]]["scientists"],1)
        self.assertEqual(sum(forge["allocations"].values()),0)

    def test_arriving_fleet_cannot_attack_until_following_turn(self):
        from app.engine_v2 import advance
        snap=self.db.current("fixture-v2")["snapshot"]
        state=json.loads(json.dumps(snap["state"])); state["turn"]=1
        fleet=next(f for f in state["fleets"] if f["owner"]=="player")
        enemy=next(f for f in state["fleets"] if f["owner"]=="enemy")
        glimmer=next(n["id"] for n in state["nodes"] if n["kind"]=="system" and n["name"]=="Glimmer")
        fleet.update({"settlement_id":None,"system_id":next(n["parent_id"] for n in state["nodes"] if n["id"]==fleet["location_id"]),
            "destination_system_id":glimmer,"origin_settlement_id":"fixture-v2-forge","departure_turn":0,"moving_until":2})
        enemy["system_id"]=glimmer; enemy["intel"]["system_id"]=glimmer
        proposal={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":1,
            "base_hash":Store.snapshot_hash("fixture-v2",1,state,V2_SCHEMA,V2_RULES),"submission_id":"arrival-attack",
            "orders":{"allocations":[],"actions":[{"type":"fleet_attack","fleet_id":fleet["id"],"target_id":enemy["id"]}]},"narrative":""}
        with self.assertRaisesRegex(ValueError,"cannot act"):
            advance(state,proposal)

    def test_investigation_records_low_confidence_population_bracket_only(self):
        enemy="fixture-v2-adversary-home"
        self.db.commit("fixture-v2",self.proposal("investigate",actions=[{"type":"investigate","source_id":"fixture-v2-forge","entity_id":enemy}]))
        snap=self.db.current("fixture-v2")["snapshot"]
        self.db.commit("fixture-v2",{"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":snap["turn"],
            "base_hash":snap["state_hash"],"submission_id":"investigation-finish","orders":{"allocations":[],"actions":[]},"narrative":""})
        current=self.db.current("fixture-v2")["snapshot"]
        foreign=next(s for s in self.db.player_state(current)["settlements"] if not s["owned"])
        self.assertIsNone(foreign["civilians"])
        self.assertEqual(foreign["civilian_population_range"],{"min":0,"max":99})
        self.assertEqual(foreign["confidence"],"low")
        self.assertEqual(foreign["observed_turn"],2)
        self.assertIsNone(foreign["stocks"])

    def test_treasury_reconciles_with_action_and_maintenance_spending(self):
        self.db.commit("fixture-v2",self.proposal(actions=[{"type":"recruit","settlement_id":"fixture-v2-forge"}]))
        state=self.db.current("fixture-v2")["snapshot"]["state"]
        budget=state["latest_budget"]
        self.assertEqual(budget["opening_credits"],400)
        self.assertEqual(budget["tax_revenue"],11)
        self.assertEqual(budget["action_credit_spending"],10)
        self.assertEqual(budget["closing_credits"],400)
        self.assertEqual(budget["opening_credits"]+budget["tax_revenue"]-budget["action_credit_spending"]-sum(x["upkeep_credits"] for x in budget["spending"].values()),budget["closing_credits"])

    def test_colony_arrival_food_and_population_are_conserved(self):
        self.test_exploration_unlocks_geometry_then_colony_arrives()
        state=self.db.current("fixture-v2")["snapshot"]["state"]
        colony=next(s for s in state["settlements"] if s["name"]=="New Settlement")
        self.assertEqual(colony["stocks"]["food"],180)
        self.assertEqual(owned_humans(state),1200)

    def test_transport_food_reserve_and_ground_deployment_combat(self):
        self.db.commit("fixture-v2",self.proposal("recruit-for-deploy",actions=[{"type":"recruit","settlement_id":"fixture-v2-forge"}]))
        state=self.db.current("fixture-v2")["snapshot"]["state"]
        unit=next(u for u in state["units"] if u["owner"]=="player")
        enemy=next(u for u in state["units"] if u["owner"]=="enemy")
        p=self.proposal("deploy-ground",actions=[{"type":"deploy_unit","unit_id":unit["id"],
            "destination_province_id":enemy["location_id"],"source_id":"fixture-v2-forge"}])
        deployed=self.db.commit("fixture-v2",p)
        transit=self.db.current("fixture-v2")["snapshot"]["state"]
        unit=next(u for u in transit["units"] if u["id"]==unit["id"])
        self.assertIsNone(unit["location_id"])
        self.assertEqual(unit["transit_food"],10)
        self.assertEqual(owned_humans(transit),1200)
        snap=self.db.current("fixture-v2")["snapshot"]
        arrive={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":snap["turn"],"base_hash":snap["state_hash"],
            "submission_id":"ground-arrival","orders":{"allocations":[],"actions":[]},"narrative":""}
        self.db.commit("fixture-v2",arrive)
        arrived=self.db.current("fixture-v2")["snapshot"]["state"]
        unit=next(u for u in arrived["units"] if u["id"]==unit["id"])
        self.assertEqual(unit["location_id"],enemy["location_id"])
        self.assertEqual(unit["food_reserve"],0)
        attack=self.proposal("ground-battle",actions=[{"type":"attack","unit_id":unit["id"],"target_id":enemy["id"]}])
        self.db.commit("fixture-v2",attack)
        final=self.db.current("fixture-v2")["snapshot"]["state"]
        self.assertTrue(final["latest_outcome"]["battles"])
        self.assertEqual(owned_humans(final),1199)

    def test_new_campaign_post_state_validator_rejects_bad_units_and_fleet_stores(self):
        state=self.db.current("fixture-v2")["snapshot"]["state"]
        broken=json.loads(json.dumps(state)); broken["fleets"][0]["food_reserve"]=-1
        with self.assertRaisesRegex(ValueError,"fleet stores"):
            Store.validate_state(V2_SCHEMA,V2_RULES,state["turn"],broken)

    def test_hierarchy_filters_historical_maps_and_management_sections(self):
        live=self.db.current("fixture-v2")["snapshot"]
        rows=live["state"]["nodes"]
        find=lambda kind,name: next(n["id"] for n in rows if n["kind"]==kind and n["name"]==name)
        root_id=find("galaxy","The Reach"); region_id=find("region","Kestrel Reach")
        sector_id=find("sector","Hearth"); system_id=find("system","Cinder"); planet_id=find("planet","Reach")
        galactic=self.db.map_view("fixture-v2","galactic")
        self.assertEqual(len(galactic["nodes"]),2)
        sectors=self.db.map_view("fixture-v2","sector",sector_id)
        self.assertEqual({n["name"] for n in sectors["nodes"]},{"Cinder","Unsurveyed System"})
        hidden_id=find("system","Dusk")
        with self.assertRaises(KeyError): self.db.map_view("fixture-v2","system",hidden_id)
        geo=self.db.map_view("fixture-v2","planet",planet_id,overlay="population")
        self.assertTrue(geo["geometry"]["tiles"])
        self.assertTrue(all(r["confidence"]=="unknown" for r in geo["records"] if r["population"] is None))
        summary=self.db.systems("fixture-v2","budget")
        self.assertEqual(summary["turn"],0)
        with self.assertRaises(KeyError): self.db.systems("fixture-v2","economy",self.v1)

    def test_exploration_unlocks_geometry_then_colony_arrives(self):
        state=self.db.current("fixture-v2")["snapshot"]["state"]
        ash=next(n["id"] for n in state["nodes"] if n["kind"]=="planet" and n["name"]=="Ash")
        first=self.proposal("explore-ash",actions=[{"type":"explore","source_id":"fixture-v2-forge","node_id":ash}])
        self.db.commit("fixture-v2",first)
        for turn in (2,3):
            snap=self.db.current("fixture-v2")["snapshot"]
            empty={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":snap["turn"],"base_hash":snap["state_hash"],
                   "submission_id":f"wait-{turn}","orders":{"allocations":[],"actions":[]},"narrative":""}
            self.db.commit("fixture-v2",empty)
        current=self.db.current("fixture-v2")["snapshot"]
        self.assertIn(ash,current["state"]["geography"])
        colonize={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":current["turn"],"base_hash":current["state_hash"],
            "submission_id":"colonize-ash","orders":{"allocations":[],"actions":[{"type":"colonize","fleet_id":"fixture-v2-transport-01",
            "source_id":"fixture-v2-forge","target_planet_id":ash}]},"narrative":""}
        self.db.commit("fixture-v2",colonize)
        for turn in (5,6):
            snap=self.db.current("fixture-v2")["snapshot"]
            payload={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":snap["turn"],"base_hash":snap["state_hash"],
                "submission_id":f"wait-colony-{turn}","orders":{"allocations":[],"actions":[]},"narrative":""}
            self.db.commit("fixture-v2",payload)
        final=self.db.current("fixture-v2")["snapshot"]["state"]
        colonies=[s for s in final["settlements"] if s["planet_id"]==ash and s["owned"]]
        self.assertEqual(len(colonies),1)
        self.assertEqual(colonies[0]["civilians"],100)
        population=owned_humans(final)
        self.assertEqual(population,1200)


if __name__ == "__main__":
    unittest.main()
