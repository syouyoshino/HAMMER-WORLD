import json
import os
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient
from app.engine import RULES_VERSION, SCHEMA_VERSION, advance, generate_planet, initial_state
from app.engine_v2 import initial_state as initial_state_v2
from app.universe import V2_RULES, V2_SCHEMA, public_state_v2
from app.store import Store
from tests.pg_fixture import PostgresTestCase


class BackendTests(PostgresTestCase, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.sid=self.db.create_demo("demo",seed=1234)
        self.db.create_pregame("campaign")

    def proposal(self, **changes):
        snap=self.db.current("demo")["snapshot"]
        p={"schema_version":SCHEMA_VERSION,"rules_version":RULES_VERSION,"base_turn":snap["turn"],
           "base_hash":snap["state_hash"],"submission_id":"sub-1","orders":{"farmers":400,"miners":200,"technicians":100},"narrative":"A fictional season."}
        p.update(changes); return p

    def test_domain_seed_order_is_deterministic(self):
        a=generate_planet("demo",15); b=generate_planet("demo",15)
        self.assertEqual(a,b)
        self.assertEqual(a["provinces"][0]["id"],"demo-p-00-00")

    def test_v2_readiness_capacity_and_movement_destinations_are_typed(self):
        state=initial_state_v2("typed",seed=55)
        self.assertEqual(state["_private"]["generator_version"],"hierarchical-v1")
        self.assertEqual(state["_private"]["generator_config"]["grid"],"grid64x40")
        Store.validate_state(V2_SCHEMA,V2_RULES,0,state)
        self.assertNotIn("generator_config",public_state_v2(state))
        cases=[]
        bad=__import__("copy").deepcopy(state);bad["units"][0]["readiness"]=True;cases.append(bad)
        bad=__import__("copy").deepcopy(state);bad["fleets"][0]["capacity"]=True;cases.append(bad)
        bad=__import__("copy").deepcopy(state);bad["fleets"][0]["location_id"]=next(n["id"] for n in bad["nodes"] if n["kind"]=="belt");cases.append(bad)
        bad=__import__("copy").deepcopy(state);bad["fleets"][0]["moving_until"]=2;bad["fleets"][0]["destination_system_id"]=next(n["id"] for n in bad["nodes"] if n["kind"]=="planet");cases.append(bad)
        bad=__import__("copy").deepcopy(state);bad["units"][0].update({"moving_until":1,"destination_province_id":bad["geography"]["typed-planet-haven"]["provinces"][0]["id"],"supply_source_id":bad["settlements"][0]["id"],"transit_food":bad["units"][0]["strength"]});cases.append(bad)
        for index,candidate in enumerate(cases):
            with self.subTest(index=index):
                with self.assertRaises(ValueError): Store.validate_state(V2_SCHEMA,V2_RULES,0,candidate)

    def test_fleet_docking_projection_is_player_only_and_tracks_travel(self):
        self.db.create_demo_v2("projection-map",seed=56)
        geometry=self.db.map_view("projection-map","planet","projection-map-planet-reach",overlay="population")
        forge=self.db.player_state(self.db.current("projection-map")["snapshot"])["settlements"][0]
        population=next(r["population"] for r in geometry["records"] if r["province_id"]==forge["province_id"])
        self.assertEqual(population,900)
        state=initial_state_v2("projection",seed=56)
        projected=public_state_v2(state)
        forge=next(s for s in projected["settlements"] if s["id"]=="projection-forge")
        self.assertEqual(forge["local_population"],900)
        owned=next(f for f in projected["fleets"] if f["id"]=="projection-transport-01")
        self.assertEqual(owned["settlement_id"],"projection-forge")
        foreign=next(f for f in projected["fleets"] if f["owner"]=="foreign")
        self.assertNotIn("settlement_id",foreign)
        traveling=__import__("copy").deepcopy(state)
        ship=next(f for f in traveling["fleets"] if f["owner"]=="player")
        ship["settlement_id"]=None;ship["location_id"]=ship["system_id"];ship["moving_until"]=2
        traveled=public_state_v2(traveling)
        forge=next(s for s in traveled["settlements"] if s["id"]=="projection-forge")
        self.assertEqual(forge["local_population"],890)
        owned=next(f for f in traveled["fleets"] if f["id"]==ship["id"])
        self.assertIsNone(owned["settlement_id"])

    def test_preview_commit_retry_and_stale(self):
        p=self.proposal(); before=self.db.current("demo")["snapshot"]["id"]
        result=self.db.preview("demo",p)
        self.assertEqual(self.db.current("demo")["snapshot"]["id"],before)
        committed=self.db.commit("demo",p)
        duplicate=self.db.commit("demo",p)
        self.assertEqual(committed["snapshot_id"],duplicate["snapshot_id"])
        self.assertTrue(duplicate["duplicate"])
        stale=dict(p,submission_id="sub-2")
        with self.assertRaises(RuntimeError): self.db.commit("demo",stale)
        conflict=dict(p,narrative="different")
        with self.assertRaises(ValueError): self.db.commit("demo",conflict)

    def test_strict_validation_and_rollback(self):
        p=self.proposal(orders={"farmers":1201,"miners":0,"technicians":0})
        with self.assertRaises(ValueError): self.db.commit("demo",p)
        p=self.proposal(orders={"farmers":True,"miners":0,"technicians":0})
        with self.assertRaises(ValueError): self.db.commit("demo",p)
        self.assertEqual(self.db.current("demo")["snapshot"]["turn"],0)
        c=self.db.connect()
        with self.assertRaises(Exception): c.execute("UPDATE snapshots SET turn=3 WHERE id=%s",(self.sid,))
        c.close()

    def test_economy_starvation_and_energy_limited_mining(self):
        s=initial_state("x",2)
        s["food"]=0
        s["energy"]=3
        p={"schema_version":SCHEMA_VERSION,"rules_version":RULES_VERSION,"base_turn":0,"base_hash":"0"*64,
           "submission_id":"x","orders":{"farmers":0,"miners":9,"technicians":0},"narrative":""}
        n,out=advance(s,p)
        self.assertEqual(n["ore"],s["ore"]+6)
        self.assertEqual(n["energy"],0)
        self.assertEqual(n["population"],0)
        self.assertEqual(n["food"],0)
        self.assertEqual(out["population_lost"],1200)

    def test_pregame_has_no_numeric_state_and_restore_branches(self):
        self.assertIsNone(self.db.current("campaign")["snapshot"])
        self.db.commit("demo",self.proposal())
        history,_=self.db.history("demo")
        original_ids=[p["id"] for p in history[0]["state"]["provinces"]]
        branch=self.db.restore("demo",history[0]["id"],"branch")
        b=self.db.current("branch")
        self.assertEqual(original_ids,[p["id"] for p in b["snapshot"]["state"]["provinces"]])
        self.assertEqual(self.db.current("demo")["snapshot"]["turn"],1)
        self.assertEqual(b["campaign"]["parent_snapshot_id"],history[0]["id"])
        self.assertEqual(b["snapshot"]["turn"],0)
        self.assertEqual(b["snapshot"]["state"],history[0]["state"])

    def test_concurrent_turn_commits_only_advance_once(self):
        base=self.db.current("demo")["snapshot"]
        gate=Barrier(2)
        proposals=[]
        for sid in ("race-a","race-b"):
            proposals.append({"schema_version":SCHEMA_VERSION,"rules_version":RULES_VERSION,
                "base_turn":base["turn"],"base_hash":base["state_hash"],"submission_id":sid,
                "orders":{"farmers":300,"miners":0,"technicians":0},"narrative":""})
        def try_commit(proposal):
            gate.wait()
            try: return self.db.commit("demo",proposal)
            except RuntimeError: return "stale"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(try_commit,proposals))
        self.assertEqual(sum(result != "stale" for result in results),1)
        self.assertEqual(self.db.current("demo")["snapshot"]["turn"],1)
        self.assertEqual(len(self.db.history("demo")[0]),2)

    def test_failed_outbox_insert_rolls_back_snapshot_and_pointer(self):
        before=self.db.current("demo")["campaign"]["current_snapshot_id"]
        with self.db.connect() as c:
            c.execute("CREATE FUNCTION fail_outbox() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'injected outbox failure'; END $$")
            c.execute("CREATE TRIGGER fail_outbox BEFORE INSERT ON outbox FOR EACH ROW EXECUTE FUNCTION fail_outbox()")
        with self.assertRaises(Exception): self.db.commit("demo",self.proposal())
        self.assertEqual(self.db.current("demo")["campaign"]["current_snapshot_id"],before)
        with self.db.connect() as c:
            self.assertEqual(c.execute("SELECT count(*) AS n FROM snapshots WHERE campaign_id='demo'").fetchone()["n"],1)
            self.assertEqual(c.execute("SELECT count(*) AS n FROM outbox").fetchone()["n"],1)

    def test_submission_id_scoped_to_campaign(self):
        self.db.create_demo("other",seed=99)
        p1=self.proposal()
        p2=self.proposal()
        other=self.db.current("other")["snapshot"]
        p2.update(base_turn=other["turn"],base_hash=other["state_hash"])
        first=self.db.commit("demo",p1); second=self.db.commit("other",p2)
        self.assertNotEqual(first["snapshot_id"],second["snapshot_id"])
        self.assertTrue(self.db.commit("other",p2)["duplicate"])

    def test_current_pointer_must_reference_same_campaign_snapshot(self):
        other_sid=self.db.create_demo("other",seed=88)
        with self.assertRaises(Exception):
            with self.db.connect() as c:
                c.execute("UPDATE campaigns SET current_snapshot_id=%s WHERE id='demo'",(other_sid,))
        with self.db.connect() as c:
            c.execute("ALTER TABLE campaigns DROP CONSTRAINT campaign_current_snapshot_fk")
            c.execute("UPDATE campaigns SET current_snapshot_id=%s WHERE id='demo'",(other_sid,))
        with self.assertRaisesRegex(ValueError,"current snapshot campaign"):
            self.db.current("demo")

    def test_player_api_filters_private_state_and_gm_denied_without_token(self):
        import app.main as api
        api.store=self.db
        old=os.environ.pop("WOLD_GM_TOKEN",None)
        try:
            client=TestClient(api.app)
            result=client.get("/api/player/campaigns/demo").json()
            serialized=json.dumps(result)
            self.assertNotIn("_private",serialized); self.assertNotIn("seeded_marker",serialized)
            self.assertEqual(client.get("/api/admin/campaigns/demo/packet").status_code,401)
        finally:
            if old is not None: os.environ["WOLD_GM_TOKEN"]=old

    def test_corrupt_snapshot_fails_closed(self):
        with self.db.connect() as c:
            c.execute("DROP TRIGGER snapshots_no_update ON snapshots")
            c.execute("UPDATE snapshots SET state_hash=%s WHERE id=%s",("0"*64,self.sid))
        with self.assertRaisesRegex(ValueError,"checksum"):
            self.db.current("demo")

    def test_dashboard_static_assets_and_authenticated_api_flow(self):
        import app.main as api
        api.store=self.db
        old=os.environ.get("WOLD_GM_TOKEN")
        os.environ["WOLD_GM_TOKEN"]="test-secret"
        try:
            client=TestClient(api.app)
            self.assertIn("HAMMER WORLD",client.get("/").text)
            self.assertIn("planet-map",client.get("/").text)
            self.assertEqual(client.get("/static/app.js").status_code,200)
            headers={"Authorization":"Bearer test-secret"}
            packet=client.get("/api/admin/campaigns/demo/packet",headers=headers).json()
            proposal=packet["example"]
            proposal["submission_id"]="http-flow"
            preview=client.post("/api/admin/campaigns/demo/preview",headers=headers,json=proposal)
            self.assertEqual(preview.status_code,200)
            committed=client.post("/api/admin/campaigns/demo/commit",headers=headers,json=proposal)
            self.assertEqual(committed.status_code,200)
            self.assertEqual(committed.json()["turn"],1)
            self.assertEqual(client.get("/api/player/campaigns/demo/history").json()["total"],2)
        finally:
            if old is None: os.environ.pop("WOLD_GM_TOKEN",None)
            else: os.environ["WOLD_GM_TOKEN"]=old

    def test_private_access_filters_campaigns_and_snapshot_ownership(self):
        import app.main as api
        api.store=self.db
        other=self.db.create_demo("other",seed=77)
        env={"WOLD_ACCESS_MODE":"private","WOLD_GM_TOKEN":"gm-test","WOLD_PLAYER_TOKEN":"player-test",
             "WOLD_PLAYER_CAMPAIGNS":"demo"}
        with patch.dict(os.environ,env,clear=False):
            client=TestClient(api.app)
            self.assertEqual(client.get("/api/access").json(),{"mode":"private","login_required":True})
            self.assertEqual(client.get("/api/player/campaigns").status_code,401)
            player={"Authorization":"Bearer player-test"}
            listing=client.get("/api/player/campaigns",headers=player)
            self.assertEqual([row["id"] for row in listing.json()],["demo"])
            self.assertEqual(client.get("/api/player/campaigns/demo",headers=player).status_code,200)
            self.assertEqual(client.get("/api/player/campaigns/other",headers=player).status_code,404)
            self.assertEqual(client.get(f"/api/player/snapshots/{other}",headers=player).status_code,404)
            self.assertEqual(client.get("/api/player/campaigns/other/map",headers=player).status_code,404)
            self.assertEqual(client.get("/api/player/campaigns/other/systems?section=economy",headers=player).status_code,404)
            gm={"Authorization":"Bearer gm-test"}
            self.assertEqual({row["id"] for row in client.get("/api/player/campaigns",headers=gm).json()},{"demo","campaign","other"})

    def test_private_access_configuration_requires_distinct_tokens(self):
        from app.main import validate_access_configuration
        with self.assertRaisesRegex(RuntimeError,"requires WOLD_GM_TOKEN"):
            validate_access_configuration({"WOLD_ACCESS_MODE":"private"})
        with self.assertRaisesRegex(RuntimeError,"must differ"):
            validate_access_configuration({"WOLD_ACCESS_MODE":"private","WOLD_GM_TOKEN":"same","WOLD_PLAYER_TOKEN":"same"})
        with self.assertRaisesRegex(RuntimeError,"wildcards"):
            validate_access_configuration({"WOLD_ACCESS_MODE":"private","WOLD_GM_TOKEN":"gm","WOLD_PLAYER_CAMPAIGNS":"*"})

    def test_admin_body_size_limit(self):
        import app.main as api
        api.store=self.db
        response=TestClient(api.app).post("/api/admin/campaigns/demo/commit",content=b" "*33000)
        self.assertEqual(response.status_code,413)

    def test_ten_thousand_persisted_fixture_turns(self):
        self.db.create_demo("stress",seed=42)
        current=self.db.current("stress")["snapshot"]
        for turn in range(10000):
            payload={"schema_version":SCHEMA_VERSION,"rules_version":RULES_VERSION,"base_turn":turn,
                     "base_hash":current["state_hash"],"submission_id":f"stress-{turn}",
                     "orders":{"farmers":600,"miners":100,"technicians":50},"narrative":""}
            result=self.db.commit("stress",payload)
            current=self.db.current("stress")["snapshot"]
            self.assertEqual(current["turn"],turn+1)
            self.assertEqual(result["turn"],turn+1)
        rows,total=self.db.history("stress",limit=2,offset=9999)
        self.assertEqual(total,10001)
        self.assertEqual([row["turn"] for row in rows],[9999,10000])
        with self.db.connect() as c:
            size=c.execute("SELECT pg_total_relation_size('snapshots') AS n").fetchone()["n"]
        self.assertLess(size,200_000_000)


if __name__=="__main__": unittest.main()
