"""Opt-in V5 surface shape, identity, preset and compatibility contracts."""
import copy
import unittest

from app.engine import digest, generate_planet
from app.engine_v2 import advance, digest as state_digest
from app.planet_generation import (PRESETS, _neighbors, generate_planet_v2, generate_planet_v3,
                                   generate_planet_v4, generate_planet_v5, validate_surface)
from app.store import Store
from app.universe import V2_RULES, V2_SCHEMA, build_universe, public_state_v2
from tests.pg_fixture import PostgresTestCase


LEGACY_GOLDENS = {'v1:0': 'b431b66b2e1e925437088ab8efdbb2d26a801749c555fa47f5d4f1a3715f61f4', 'v2:0': '13aa27f25215ea85d373ef2ca529f00e411fd043452d0293b73383aede73fbca', 'v3:0': '8347dda4efc6ec4897563683b9bfc8735bbfc6147d819d743d54a9f48b8880b7', 'v1:55': '7030a32b69bf58aaed8a233d92478fa294d2af74f63ff4d861c8192753e7414f', 'v2:55': '58ee0a26d13a49f29406e60cdbe6b807f454084f1c61c32463e8847cf4cf233d', 'v3:55': '5fd1cb1be6cbfcb34c5040b5723eb2fe67d0b82ca4665a6dce29b7fed4fa83de', 'v1:741903': '4392ac9a421fa6db43ad08609bcbe9f65e0ebf0ebbbf462668b13133d857ee33', 'v2:741903': '0c9d3bee0a5988d5abf2f7d0b6fb2866c6b90c250880818b37feb0be457ee25d', 'v3:741903': '8a8452b936c86171b19f1fe42d2b7ae2dd23cc84f6d180d06fa8f343f11ea201', 'v4:continental:0': '153d99d7b1cc2c3c3ed3f67203417a618298a2574702ec453f77f8601d0629ad', 'v4:archipelago:0': '5ae5caf7532db504a83cec159999da68023a7c7abcbd60c8dc0b0ca40feb03ad', 'v4:oceanic:0': '56ec361acb5b53a1f6ff7ebee39be114183421979ba82629467ca94a55eafee8', 'v4:arid:0': '392853730d800e1a8cb638d16b10adf5b70eb88c3d370b02fcd99d78a2e03095', 'v4:barren:0': '1eb6db396f77352b181a4e46b007cb7db805142418a837e9d8e873daa4f76f52', 'v4:frozen:0': 'cf68343e1ebfba5abf53db690972905baf8dbe0f4308623927c0b1049aa5ec0f', 'v4:continental:55': '8277ed6b19fa7f4e0350356fc6adc2905f1b42ffb7440aecd7eec984d9a32219', 'v4:archipelago:55': '3dc173f4e0cec2a2e70f11b2580bf6da2bf32517656d34d26ccc1002748cdd3a', 'v4:oceanic:55': '1b7901c36d0f96fa85675718fa4aecd3bae913e4fba825a782fad53ed77b5bd9', 'v4:arid:55': 'e6ec21253d5aac626bec9b3376b8186589ba64f37f30f568f214980d56cf5a21', 'v4:barren:55': 'b69702dad89ffa766200e626076f781c479a6a6dace66c3a4b171999c9d9d167', 'v4:frozen:55': '2258aa5573ce3223243a76302b8998165baf48f05418dae4bfe4245c302bc0c3', 'v4:continental:741903': 'edf1a29616dd4135cda96728d7971794d40c5946ec0fd425b2c4ac8540a50256', 'v4:archipelago:741903': 'e0059389a09bee7048e0becd6d3d70651c1ddcf6e16217e41dd819fc6c3f3348', 'v4:oceanic:741903': '12d4c2974d712a0fc820e14e7677f472bd25be838c0ea5cc48e6dd6ea258316e', 'v4:arid:741903': 'ff5f21127bedf94968f8ef5089a04e8707e7a6216272ca0df037f36e1ea4b8e5', 'v4:barren:741903': 'c361d914daaa9be94f6201a1b1df718931d8e68950f23b740111a5edc5bfa7dc', 'v4:frozen:741903': '6421260f772a6c26343e1e22e83dbe4596641e77ec6bd652164ca2bbc2736fe8'}


def component_sizes(codes, width, height):
    unseen={i for i,code in enumerate(codes) if code!="o"}
    result=[]
    while unseen:
        stack=[unseen.pop()]; size=0
        while stack:
            i=stack.pop(); size+=1
            for neighbor in _neighbors(i,width,height):
                if neighbor in unseen: unseen.remove(neighbor); stack.append(neighbor)
        result.append(size)
    return sorted(result,reverse=True)


class PlanetV5Tests(unittest.TestCase):
    def test_v1_to_v4_generators_match_captured_goldens(self):
        goldens=LEGACY_GOLDENS
        for seed in (0,55,741903):
            self.assertEqual(digest(generate_planet("compat",seed)),goldens[f"v1:{seed}"])
            self.assertEqual(digest(generate_planet_v2("compat",seed)),goldens[f"v2:{seed}"])
            self.assertEqual(digest(generate_planet_v3("compat",seed)),goldens[f"v3:{seed}"])
            for preset in PRESETS:
                self.assertEqual(digest(generate_planet_v4("compat",seed,preset)),goldens[f"v4:{preset}:{seed}"])

    def test_all_presets_are_real_v5_fields_with_full_legacy_province_membership(self):
        generated={}
        for preset in PRESETS:
            with self.subTest(preset=preset):
                geo=generate_planet_v5("sample",55,preset)
                validate_surface(geo)
                self.assertEqual((geo["planet"]["width"],geo["planet"]["height"]),(128,80))
                self.assertEqual(len(geo["terrain_grid"]),128*80)
                self.assertTrue(all(len(geo["surface"][key])==128*80 for key in
                                    ("elevation","temperature","moisture","drainage","accumulation")))
                provinces=geo["provinces"]
                self.assertEqual(len(provinces),40)
                self.assertEqual([p["id"] for p in provinces],
                                 [f"sample-p-{y:02d}-{x:02d}" for y in range(5) for x in range(8)])
                self.assertEqual([(p["x"],p["y"],p["width"],p["height"]) for p in provinces],
                                 [(x*16,y*16,16,16) for y in range(5) for x in range(8)])
                self.assertEqual(geo,generate_planet_v5("sample",55,preset))
                generated[preset]=geo
        continental=component_sizes(generated["continental"]["terrain_grid"],128,80)
        archipelago=component_sizes(generated["archipelago"]["terrain_grid"],128,80)
        oceanic=component_sizes(generated["oceanic"]["terrain_grid"],128,80)
        self.assertGreater(continental[0],sum(continental)//2)
        self.assertGreaterEqual(len(archipelago),5)
        self.assertGreater(sum(c!="o" for c in generated["archipelago"]["terrain_grid"]),
                           sum(c!="o" for c in generated["oceanic"]["terrain_grid"]))
        for preset in ("arid","barren","frozen"):
            self.assertTrue(all(v>400 for v in generated[preset]["surface"]["elevation"]))

    def test_universe_v5_contract_and_distant_land_actions(self):
        state=build_universe("sample",741903,planet_generator="planet-v5",preset="continental")
        Store.validate_state(V2_SCHEMA,V2_RULES,0,state)
        self.assertEqual(state["_private"]["generator_config"]["grid"],"grid128x80")
        geo=state["geography"]["sample-planet-reach"]
        public=public_state_v2(state)
        projected=public["geography"]["sample-planet-reach"]
        self.assertNotIn("sample-planet-veil",public["geography"])
        far=next(p for p in geo["provinces"] if (p["x"]>=64 or p["y"]>=40) and
                 any(geo["terrain_grid"][y*128+x]!="o" for y in range(p["y"],p["y"]+16) for x in range(p["x"],p["x"]+16)))
        self.assertTrue(any(tile["province_id"]==far["id"] for tile in projected["tiles"]))
        for settlement in state["settlements"]:
            province=next(p for p in geo["provinces"] if p["id"]==settlement["province_id"])
            self.assertTrue(any(geo["terrain_grid"][y*128+x]!="o"
                                for y in range(province["y"],province["y"]+16)
                                for x in range(province["x"],province["x"]+16)))
        malformed=copy.deepcopy(state);malformed["geography"]["sample-planet-reach"]["provinces"][0]["width"]=15
        with self.assertRaises(ValueError): Store.validate_state(V2_SCHEMA,V2_RULES,0,malformed)
        source=next(s for s in state["settlements"] if s["owned"])
        state["units"].append({"id":"sample-player-unit","kind":"ground","owner":"player",
            "planet_id":source["planet_id"],"settlement_id":source["id"],"location_id":source["province_id"],
            "strength":10,"readiness":100,"created_turn":-1,"acted_turn":-1,"food_reserve":0})
        proposal={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":0,
            "base_hash":state_digest(state),"submission_id":"v5-far-deploy",
            "orders":{"allocations":[],"actions":[{"type":"deploy_unit","unit_id":"sample-player-unit",
                "destination_province_id":far["id"],"source_id":source["id"]}]},"narrative":""}
        changed,_=advance(state,proposal)
        deployed=next(u for u in changed["units"] if u["id"]=="sample-player-unit")
        self.assertEqual(deployed["destination_province_id"],far["id"])
        Store.validate_state(V2_SCHEMA,V2_RULES,1,changed)


class PersistedPlanetV5Tests(PostgresTestCase,unittest.TestCase):
    def test_history_and_restore_preserve_full_v5_geometry(self):
        sid=self.db.create_demo_v2("v5-restore",seed=55,planet_generator="planet-v5",preset="archipelago")
        initial=self.db.current("v5-restore")["snapshot"]
        expected=copy.deepcopy(initial["state"]["geography"])
        proposal={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":0,
            "base_hash":initial["state_hash"],"submission_id":"v5-history-turn",
            "orders":{"allocations":[],"actions":[]},"narrative":""}
        self.db.commit("v5-restore",proposal)
        historical=self.db.map_view("v5-restore","planet","v5-restore-planet-reach",snapshot_id=sid)
        self.assertEqual((historical["geometry"]["planet"]["width"],historical["geometry"]["planet"]["height"]),(128,80))
        self.db.restore("v5-restore",sid,"v5-restore-branch")
        restored=self.db.current("v5-restore-branch")["snapshot"]["state"]
        self.assertEqual(restored["geography"],expected)


if __name__=="__main__":
    unittest.main()
