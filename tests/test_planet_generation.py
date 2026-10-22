"""New fixture geography, legacy compatibility and player-boundary regressions."""
import copy
import json
import unittest

from app.engine import digest, generate_planet, initial_state, public_state
from app.planet_generation import generate_planet_v2, generate_planet_v3, validate_surface
from app.store import Store
from app.universe import V2_RULES, V2_SCHEMA, build_universe, public_state_v2
from tests.pg_fixture import PostgresTestCase


class PlanetGenerationTests(unittest.TestCase):
    def test_legacy_default_output_is_unchanged(self):
        self.assertEqual(digest(generate_planet("compat",55)),
                         "7030a32b69bf58aaed8a233d92478fa294d2af74f63ff4d861c8192753e7414f")
        self.assertEqual(digest(build_universe("compat",55)),
                         "9e3c144d1145d607b52f3806c840d955c76157db003a00764370a023c0aff5df")
        self.assertNotIn("surface", public_state(initial_state("compat",55)))
        self.assertEqual(digest(generate_planet_v2("compat",55)),
                         "58ee0a26d13a49f29406e60cdbe6b807f454084f1c61c32463e8847cf4cf233d")

    def test_v3_removes_clipped_plateau_and_rectangular_coast_artifacts(self):
        from collections import Counter
        def longest_coast_run(codes):
            longest=0
            for vertical in (False,True):
                for row in range(64 if vertical else 40):
                    for sign in (-1,1):
                        run=0
                        for col in range(40 if vertical else 64):
                            x,y=(row,col) if vertical else (col,row)
                            nx,ny=(x+sign,y) if vertical else (x,y+sign)
                            coast=(0<=nx<64 and 0<=ny<40 and codes[y*64+x]!="o" and codes[ny*64+nx]=="o")
                            run=run+1 if coast else 0
                            longest=max(longest,run)
            return longest
        for seed in (0,1,55,1234,4242,741903):
            fractions={}
            for cls in ("terrestrial","oceanic"):
                with self.subTest(seed=seed,planet_class=cls):
                    geo=generate_planet_v3("sample",seed,cls)
                    validate_surface(geo)
                    codes=geo["terrain_grid"]
                    heights=[h for h,c in zip(geo["surface"]["elevation"],codes) if c!="o"]
                    fractions[cls]=len(heights)
                    # A coast spanning half the map and a single clipped level
                    # covering 5% of land reproduce the diagnosed v2 artifacts.
                    self.assertLess(longest_coast_run(codes),32)
                    self.assertLess(Counter(heights).most_common(1)[0][1],len(heights)//20)
            self.assertLess(fractions["oceanic"],fractions["terrestrial"])
            state=build_universe("sample",seed,planet_generator="planet-v3")
            Store.validate_state(V2_SCHEMA,V2_RULES,0,state)
            geo=state["geography"]["sample-planet-reach"]
            for settlement in state["settlements"]:
                p=next(p for p in geo["provinces"] if p["id"]==settlement["province_id"])
                self.assertTrue(any(geo["terrain_grid"][y*64+x]!="o" for y in range(p["y"],p["y"]+8) for x in range(p["x"],p["x"]+8)))
        self.assertEqual(generate_planet_v3("sample",55),generate_planet_v3("sample",55))
        self.assertNotEqual(generate_planet_v3("sample",55)["terrain_grid"],generate_planet_v3("sample",56)["terrain_grid"])

    def test_determinism_coherence_classes_and_valid_land_locations(self):
        a = generate_planet_v2("sample",55)
        self.assertEqual(a, generate_planet_v2("sample",55))
        self.assertNotEqual(a["terrain_grid"],generate_planet_v2("sample",56)["terrain_grid"])
        self.assertGreater(len(a["surface"]["rivers"]),0)
        elevations = a["surface"]["elevation"]
        nearby = sum(abs(elevations[i]-elevations[i+1]) for i in range(2559) if i%64 != 63)
        distant = sum(abs(elevations[i]-elevations[(i+640)%2560]) for i in range(2559) if i%64 != 63)
        self.assertLess(nearby,distant)
        for seed in (0,1,55,9234,741903):
            for cls in ("terrestrial","oceanic","arid","ice"):
                with self.subTest(seed=seed,planet_class=cls):
                    geo = generate_planet_v2("sample",seed,cls)
                    validate_surface(geo)
                    self.assertEqual(len(geo["provinces"]),40)
                    self.assertEqual(set(geo["terrain_grid"])-set("ocprfm"),set())
                    for river in geo["surface"]["rivers"]:
                        self.assertEqual(len(river["points"]),len({tuple(p) for p in river["points"]}))
            state = build_universe("sample",seed,planet_generator="planet-v2")
            Store.validate_state(V2_SCHEMA,V2_RULES,0,state)
            geo = state["geography"]["sample-planet-reach"]
            for settlement in state["settlements"]:
                p = next(p for p in geo["provinces"] if p["id"] == settlement["province_id"])
                self.assertTrue(any(geo["terrain_grid"][y*64+x] != "o"
                                    for y in range(p["y"],p["y"]+8) for x in range(p["x"],p["x"]+8)))
        ice = generate_planet_v2("sample",55,"ice")["surface"]["temperature"]
        self.assertLess(sum(ice),sum(a["surface"]["temperature"]))

    def test_surface_corruption_rejected_in_both_snapshot_versions(self):
        base = generate_planet_v2("sample",55)
        mutations = []
        bad=copy.deepcopy(base); bad["surface"]["version"]="future"; mutations.append(bad)
        bad=copy.deepcopy(base); bad["surface"]["seed"]=55; mutations.append(bad)
        bad=copy.deepcopy(base); bad["surface"]["elevation"][0]=True; mutations.append(bad)
        bad=copy.deepcopy(base); bad["surface"]["moisture"].pop(); mutations.append(bad)
        bad=copy.deepcopy(base); bad["surface"]["accumulation"][0]=2561; mutations.append(bad)
        land=next(i for i,c in enumerate(base["terrain_grid"]) if c != "o")
        bad=copy.deepcopy(base); bad["surface"]["drainage"][land]=land; mutations.append(bad)
        bad=copy.deepcopy(base); bad["surface"]["drainage"][land]=-1; mutations.append(bad)
        bad=copy.deepcopy(base); bad["surface"]["rivers"][0]["points"][-1]=[32,20]; mutations.append(bad)
        bad=copy.deepcopy(base); bad["surface"]["rivers"][0]["seed"]=55; mutations.append(bad)
        state = build_universe("sample",55,planet_generator="planet-v2")
        for index, geo in enumerate(mutations):
            with self.subTest(index=index):
                legacy=initial_state("sample",55); legacy.update(geo)
                with self.assertRaises(ValueError):
                    Store.validate_state("world-v1","economy-v1",0,legacy)
                new=copy.deepcopy(state); new["geography"]["sample-planet-reach"]=geo
                with self.assertRaises(ValueError):
                    Store.validate_state(V2_SCHEMA,V2_RULES,0,new)

    def test_public_allowlists_keep_hidden_geography_and_seeds_private(self):
        marker="CONFIDENTIAL_SURFACE_MARKER"
        state=build_universe("sample",55,planet_generator="planet-v3")
        for geo in state["geography"].values():
            geo["surface"]["_private"]=marker
            for river in geo["surface"]["rivers"]:
                river["private_seed"]=marker
        projected=public_state_v2(state)
        self.assertEqual(set(projected["geography"]),{"sample-planet-reach"})
        encoded=json.dumps(projected)
        for secret in (marker,"_private","seeded_marker","generation_nonce","enemy_allocations","sample-planet-veil"):
            self.assertNotIn(secret,encoded)
        geo=state["geography"]["sample-planet-reach"]
        legacy=initial_state("sample",55); legacy.update(geo)
        self.assertNotIn(marker,json.dumps(public_state(legacy)))
        self.assertEqual(projected["geography"]["sample-planet-reach"]["surface"]["elevation"],geo["surface"]["elevation"])


class PersistedPlanetGenerationTests(PostgresTestCase, unittest.TestCase):
    def test_new_fixture_commit_historical_reads_and_exact_branch_restore(self):
        legacy=self.db.create_demo_v2("unchanged",seed=55)
        old=copy.deepcopy(self.db.current("unchanged")["snapshot"])
        self.db.create_demo_v2("previous-v2",seed=55,planet_generator="planet-v2")
        previous=copy.deepcopy(self.db.current("previous-v2")["snapshot"])
        first=self.db.create_demo_v2("orbital",seed=55,planet_generator="planet-v3")
        initial=self.db.current("orbital")["snapshot"]
        self.assertEqual(self.db.current("unchanged")["snapshot"],old)
        self.assertEqual(self.db.current("previous-v2")["snapshot"],previous)
        with self.assertRaisesRegex(ValueError,"already exists"):
            self.db.create_demo_v2("unchanged",planet_generator="planet-v2")
        self.assertEqual(self.db.current("unchanged")["snapshot"]["id"],legacy)
        proposal={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":0,
                  "base_hash":initial["state_hash"],"submission_id":"surface-turn",
                  "orders":{"allocations":[],"actions":[]},"narrative":"Fictional fixture."}
        self.db.commit("orbital",proposal)
        current=self.db.current("orbital")["snapshot"]
        self.assertEqual(current["state"]["geography"],initial["state"]["geography"])
        self.assertEqual(self.db.snapshot(first),initial)
        historical=self.db.map_view("orbital","planet","orbital-planet-reach",snapshot_id=first)
        self.assertEqual(historical["geometry"]["surface"],initial["state"]["geography"]["orbital-planet-reach"]["surface"])
        self.db.restore("orbital",first,"orbital-branch")
        restored=self.db.current("orbital-branch")["snapshot"]["state"]
        expected=copy.deepcopy(initial["state"]); expected["_private"]["campaign_id"]="orbital-branch"
        self.assertEqual(restored,expected)
        self.assertEqual(self.db.current("orbital")["snapshot"]["id"],current["id"])
        packet=json.dumps(self.db.packet("orbital"))
        for secret in ("_private","seeded_marker","generation_nonce","orbital-planet-veil"):
            self.assertNotIn(secret,packet)


if __name__ == "__main__":
    unittest.main()
