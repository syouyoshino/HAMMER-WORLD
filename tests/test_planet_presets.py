"""Opt-in planet-v4 preset contracts, persistence, and player projection."""
import copy
import json
import sys
import unittest
from unittest.mock import patch

from app.engine import digest
from app.planet_generation import PRESETS, generate_planet_v4, validate_surface
from app.store import Store
from app.universe import V2_RULES, V2_SCHEMA, build_universe, public_state_v2
from tests.pg_fixture import PostgresTestCase


def land_components(codes):
    pending={i for i,code in enumerate(codes) if code!="o"}
    sizes=[]
    while pending:
        stack=[pending.pop()]; size=0
        while stack:
            i=stack.pop(); size+=1
            for j in (i-64 if i>=64 else -1, i+64 if i<64*39 else -1,
                      i-1 if i%64 else -1, i+1 if i%64<63 else -1):
                if j in pending:
                    pending.remove(j); stack.append(j)
        sizes.append(size)
    return sizes


class PlanetPresetGenerationTests(unittest.TestCase):
    def test_existing_v3_generator_golden_is_unchanged(self):
        from app.planet_generation import generate_planet_v3
        self.assertEqual(digest(generate_planet_v3("compat",55)),
                         "5fd1cb1be6cbfcb34c5040b5723eb2fe67d0b82ca4665a6dce29b7fed4fa83de")

    def test_all_presets_are_deterministic_distinct_and_semantically_valid(self):
        outputs={}
        for preset in PRESETS:
            first=generate_planet_v4("sample",55,preset)
            self.assertEqual(first,generate_planet_v4("sample",55,preset))
            validate_surface(first)
            self.assertEqual(len(first["terrain_grid"]),64*40)
            outputs[preset]=first
        self.assertEqual(len({g["terrain_grid"] for g in outputs.values()}),len(PRESETS))
        for preset in ("continental","archipelago","oceanic"):
            geo=outputs[preset]; surface=geo["surface"]
            self.assertEqual(surface["hydrology"],"ocean-draining")
            self.assertEqual(surface["sea_level"],400)
            codes=geo["terrain_grid"]
            for cell,code in enumerate(codes):
                if code=="o": continue
                current=cell; seen=set()
                while codes[current]!="o":
                    self.assertNotIn(current,seen)
                    seen.add(current)
                    current=surface["drainage"][current]
                    self.assertGreaterEqual(current,0)
        for preset in ("arid","barren","frozen"):
            geo=outputs[preset]; surface=geo["surface"]
            self.assertEqual(surface["hydrology"],"none")
            self.assertIsNone(surface["sea_level"])
            self.assertFalse(set(geo["terrain_grid"]) & set("ocfm"))
            self.assertEqual(surface["drainage"],[-1]*2560)
            self.assertEqual(surface["accumulation"],[1]*2560)
            self.assertEqual(surface["rivers"],[])
        self.assertEqual(set(outputs["barren"]["terrain_grid"]),{"r"})
        self.assertEqual(set(outputs["arid"]["surface"]["moisture"]),{0})
        self.assertLessEqual(max(outputs["frozen"]["surface"]["temperature"]),220)

    def test_landform_shapes_hold_across_seed_families(self):
        for seed in range(12):
            with self.subTest(seed=seed):
                continental=generate_planet_v4("sample",seed,"continental")["terrain_grid"]
                components=land_components(continental)
                boundary=list(range(64))+list(range(64*39,64*40))+list(range(0,64*40,64))+list(range(63,64*40,64))
                self.assertTrue(any(continental[i]!="o" for i in boundary))
                self.assertGreater(max(components),256)
                archipelago=land_components(generate_planet_v4("sample",seed,"archipelago")["terrain_grid"])
                oceanic=land_components(generate_planet_v4("sample",seed,"oceanic")["terrain_grid"])
                self.assertGreaterEqual(len(archipelago),3)
                self.assertGreaterEqual(len(oceanic),3)
                oceanic_land=sum(size for size in oceanic)
                self.assertGreater(oceanic_land,120)
                self.assertLess(oceanic_land,2560*.20)

    def test_preset_resolution_is_stable_per_full_planet_id(self):
        ids=["sample-planet-reach","sample-planet-ash","sample-planet-haven"]
        a=build_universe("sample",55,planet_generator="planet-v4")
        b=build_universe("sample",55,planet_generator="planet-v4")
        self.assertEqual(a,b)
        self.assertEqual(a["_private"]["generator_config"]["planet_presets"],
                         {pid:a["geography"][pid]["surface"]["preset"] for pid in a["geography"]})
        changed=build_universe("sample",55,planet_generator="planet-v4",planet_presets={ids[1]:"barren"})
        self.assertEqual(changed["_private"]["generator_config"]["planet_presets"][ids[1]],"barren")
        self.assertEqual(a["geography"][ids[0]],changed["geography"][ids[0]])
        self.assertEqual(a["geography"][ids[2]],changed["geography"][ids[2]])
        for node in changed["nodes"]:
            if node["kind"]=="planet":
                self.assertEqual(node["class"],{"continental":"terrestrial","archipelago":"oceanic","oceanic":"oceanic",
                    "arid":"arid","barren":"barren","frozen":"ice"}[changed["_private"]["generator_config"]["planet_presets"][node["id"]]])

    def test_v1_to_v3_reject_new_options(self):
        for version in ("planet-v1","planet-v2","planet-v3"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                build_universe("sample",55,planet_generator=version,preset="arid")
        for overrides in ({"unknown-planet":"barren"},{"sample-planet-reach":"unknown"}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                build_universe("sample",55,planet_generator="planet-v4",planet_presets=overrides)

    def test_cli_duplicate_overrides_fail_before_store_initializes(self):
        from app import cli
        with patch.object(cli,"Store") as store, patch.object(sys,"argv",[
            "hammer-world","init-v2","--planet-generator","planet-v4",
            "--planet-preset","x-planet-reach=arid","--planet-preset","x-planet-reach=barren"]):
            with self.assertRaises(SystemExit): cli.main()
            store.assert_not_called()


class PersistedPlanetPresetTests(PostgresTestCase, unittest.TestCase):
    def test_validation_precedes_writes_and_history_keeps_public_metadata(self):
        before=self.db.campaigns()
        for key,choice in (("invalid-preset-hidden","barren"),
                           ("invalid-preset-system-hearth","barren"),
                           ("invalid-preset-planet-reach","unsupported")):
            with self.subTest(key=key,choice=choice), self.assertRaises(ValueError):
                self.db.create_demo_v2("invalid-preset",planet_generator="planet-v4",
                                       planet_presets={key:choice})
        self.assertEqual(self.db.campaigns(),before)

        overrides={"preset-demo-planet-reach":"arid","preset-demo-planet-ash":"archipelago",
                   "preset-demo-planet-haven":"oceanic","preset-demo-planet-veil":"frozen"}
        sid=self.db.create_demo_v2("preset-demo",seed=55,planet_generator="planet-v4",planet_presets=overrides)
        initial=self.db.current("preset-demo")["snapshot"]
        Store.validate_state(V2_SCHEMA,V2_RULES,0,initial["state"])
        state=initial["state"]
        self.assertEqual(state["_private"]["generator_config"]["planet_presets"],overrides)
        public=public_state_v2(state)
        self.assertEqual(public["geography"]["preset-demo-planet-reach"]["surface"]["preset"],"arid")
        encoded=json.dumps(public)
        for hidden in ("preset-demo-planet-veil","planet_presets","seeded_marker","generation_nonce"):
            self.assertNotIn(hidden,encoded)
        proposal={"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":0,
                  "base_hash":initial["state_hash"],"submission_id":"preset-turn",
                  "orders":{"allocations":[],"actions":[]},"narrative":"Preset fixture."}
        self.db.commit("preset-demo",proposal)
        historical=self.db.map_view("preset-demo","planet","preset-demo-planet-reach",snapshot_id=sid)
        self.assertEqual(historical["geometry"]["surface"]["preset"],"arid")
        self.db.restore("preset-demo",sid,"preset-branch")
        restored=self.db.current("preset-branch")["snapshot"]["state"]
        expected=copy.deepcopy(state); expected["_private"]["campaign_id"]="preset-branch"
        self.assertEqual(restored,expected)

    def test_malformed_v4_surface_and_private_mappings_are_rejected(self):
        state=build_universe("malformed",55,planet_generator="planet-v4",preset="barren")
        Store.validate_state(V2_SCHEMA,V2_RULES,0,state)
        reach="malformed-planet-reach"
        for change in ("float-sea-level","rivers-none","rivers-object","rivers-string","class-mismatch","preset-map-mismatch"):
            malformed=copy.deepcopy(state);geo=malformed["geography"][reach];surface=geo["surface"]
            if change=="float-sea-level": surface["sea_level"]=400.0
            elif change=="rivers-none": surface["rivers"]=None
            elif change=="rivers-object": surface["rivers"]={}
            elif change=="rivers-string": surface["rivers"]=""
            elif change=="class-mismatch": next(n for n in malformed["nodes"] if n["id"]==reach)["class"]="ice"
            else: malformed["_private"]["generator_config"]["planet_presets"][reach]="frozen"
            with self.subTest(change=change),self.assertRaises(ValueError):
                Store.validate_state(V2_SCHEMA,V2_RULES,0,malformed)


if __name__=="__main__":
    unittest.main()
