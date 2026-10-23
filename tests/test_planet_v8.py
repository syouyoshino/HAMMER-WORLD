"""Saved composition contracts, independent options and persisted V8 history."""
import copy
import unittest

from app.planet_generation import PRESETS, generate_planet_v7, generate_planet_v8, project_surface, validate_surface
from app.planet_materials import MATERIAL_KEYS, cap_edges, reserved_anchors
from app.universe import build_universe, public_state_v2
from app.store import Store
from app.engine_v2 import ALLOCATIONS
from tests.pg_fixture import PostgresTestCase


class PlanetV8PureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geo = generate_planet_v8('reach', 987, 'barren', 'cratered', 'water', 'water-ice')
        cls.state = build_universe('slice', 321, planet_generator='planet-v8', preset='barren',
                                   geology='cratered', lake_material='water', polar_caps='water-ice')

    def test_deterministic_saved_layer_leaves_v7_base_exact(self):
        self.assertEqual(self.geo, generate_planet_v8('reach', 987, 'barren', 'cratered', 'water', 'water-ice'))
        base = copy.deepcopy(self.geo)
        materials = base['surface'].pop('materials')
        base['surface']['version'] = 'planet-v7'
        self.assertEqual(base, generate_planet_v7('reach', 987, 'barren', 'cratered'))
        self.assertEqual(set(materials), MATERIAL_KEYS)
        validate_surface(self.geo)

    def test_supported_presets_have_nonempty_disjoint_masks_and_preserved_anchors(self):
        for seed in (0, 15, 741903):
            for preset in PRESETS:
                with self.subTest(seed=seed, preset=preset):
                    geo = generate_planet_v8('reach', seed, preset, lake_material='hydrocarbon' if preset=='frozen' else 'water', polar_caps='water-ice')
                    m = geo['surface']['materials']
                    lakes = {i for i,c in enumerate(m['lake_mask']) if c=='1'}
                    ice = {i for i,c in enumerate(m['ice_mask']) if c=='1'}
                    self.assertTrue(lakes)
                    self.assertTrue(ice)
                    self.assertFalse(lakes & ice)
                    self.assertFalse(lakes & reserved_anchors(geo))
                    self.assertTrue(all(geo['terrain_grid'][i] not in 'oc' for i in lakes))
                    # All pole cells are solid, even on ocean and holdings.
                    self.assertEqual(m['ice_mask'][:128], '1'*128)
                    self.assertEqual(m['ice_mask'][-128:], '1'*128)

    def test_periodic_cap_boundaries_and_connected_lakes(self):
        m = self.geo['surface']['materials']
        for pole in ('north','south'):
            edges = cap_edges(987,128,pole)
            self.assertLessEqual(max(abs(a-b) for a,b in zip(edges, edges[1:]+edges[:1])),1)
            self.assertGreater(len(set(edges)),1)
        remaining = {i for i,c in enumerate(m['lake_mask']) if c=='1'}
        components = []
        while remaining:
            stack=[remaining.pop()]; size=0
            while stack:
                i=stack.pop();size+=1;x,y=i%128,i//128
                for j in (y*128+(x-1)%128,y*128+(x+1)%128,i-128,i+128):
                    if j in remaining:
                        remaining.remove(j);stack.append(j)
            components.append(size)
        self.assertLessEqual(len(components),7)
        self.assertTrue(all(size>=1 for size in components))

    def test_options_are_independent_and_per_planet(self):
        water=generate_planet_v8('reach',987,'barren',lake_material='water')
        lava=generate_planet_v8('reach',987,'barren',lake_material='lava')
        self.assertEqual(water['surface']['materials']['lake_mask'],lava['surface']['materials']['lake_mask'])
        none=generate_planet_v8('reach',987,'barren')
        caps=generate_planet_v8('reach',987,'barren',polar_caps='water-ice')
        self.assertEqual(none['surface']['materials']['lake_mask'],'0'*10240)
        self.assertEqual(caps['surface']['materials']['lake_mask'],'0'*10240)
        combined=generate_planet_v8('reach',987,'barren',lake_material='water',polar_caps='water-ice')
        self.assertEqual(combined['surface']['materials']['ice_mask'],caps['surface']['materials']['ice_mask'])
        base=build_universe('slice',321,planet_generator='planet-v8',preset='barren')
        changed=build_universe('slice',321,planet_generator='planet-v8',preset='barren',planet_lake_materials={'slice-planet-reach':'lava'})
        for pid in base['geography']:
            if not pid.endswith('reach'): self.assertEqual(base['geography'][pid],changed['geography'][pid])
        config=changed['_private']['generator_config']
        for key in ('planet_lake_materials','planet_polar_caps'):
            self.assertEqual(set(config[key]),set(base['geography']))

    def test_invalid_choices_and_overrides_rejected(self):
        for preset,lake,caps in (('frozen','water','none'),('frozen','lava','none'),
                                ('arid','hydrocarbon','none'),('arid','lava','water-ice'),
                                ('arid',True,'none'),('arid','none',True)):
            with self.subTest(preset=preset,lake=lake,caps=caps):
                with self.assertRaises(ValueError): generate_planet_v8('reach',1,preset,lake_material=lake,polar_caps=caps)
        for field in ('planet_lake_materials','planet_polar_caps'):
            for value in (True,[],{'unknown':'none'},{True:'none'},{'slice-planet-reach':True}):
                with self.assertRaises(ValueError): build_universe('slice',1,planet_generator='planet-v8',**{field:value})

    def test_strict_mask_and_nested_key_validation(self):
        for change in (
            lambda m:m.update(lake_mask=True),
            lambda m:m.update(ice_mask=['0']*10240),
            lambda m:m.update(lake_mask='0'*10239),
            lambda m:m.update(lake_mask='x'*10240),
            lambda m:m.update(lake_mask='0'*10240),
            lambda m:m.update(lake_material='none'),
            lambda m:m.update(private_marker='hidden'),
            lambda m:m.pop('polar_caps'),
            lambda m:m.update(ice_mask='1'*10240),
        ):
            malformed=copy.deepcopy(self.geo);change(malformed['surface']['materials'])
            with self.assertRaises(ValueError):validate_surface(malformed)
        for index in (0,next(iter(reserved_anchors(self.geo)))):
            malformed=copy.deepcopy(self.geo);m=malformed['surface']['materials']
            m['lake_mask']=m['lake_mask'][:index]+'1'+m['lake_mask'][index+1:]
            with self.assertRaises(ValueError):validate_surface(malformed)

    def test_private_config_matches_surface_and_legacy_rejects_new_keys_and_args(self):
        Store.validate_state('world-v2','demo-v2',0,self.state)
        for key in ('planet_lake_materials','planet_polar_caps'):
            for change in ('missing','extra','mismatch','bool'):
                state=copy.deepcopy(self.state);config=state['_private']['generator_config']
                if change=='missing':config.pop(key)
                elif change=='extra':config[key]['unknown']='none'
                elif change=='mismatch':config[key]['slice-planet-reach']='none'
                else:config[key]=True
                with self.assertRaises(ValueError):Store.validate_state('world-v2','demo-v2',0,state)
        for version in range(1,8):
            for args in ({'lake_material':'none'},{'polar_caps':'none'},{'planet_lake_materials':{}},{'planet_polar_caps':{}}):
                with self.assertRaises(ValueError):build_universe('slice',1,planet_generator=f'planet-v{version}',**args)
            state=build_universe('slice',1,planet_generator=f'planet-v{version}')
            for key in ('planet_lake_materials','planet_polar_caps'):
                malformed=copy.deepcopy(state);malformed['_private']['generator_config'][key]={}
                with self.assertRaises(ValueError):Store.validate_state('world-v2','demo-v2',0,malformed)
        self.assertEqual(build_universe('slice',1),build_universe('slice',1,planet_generator='planet-v1'))

    def test_projection_is_explicit_copied_and_surveyed_only(self):
        geo=copy.deepcopy(self.geo);geo['surface']['materials']['private_marker']='hidden'
        projected=project_surface(geo)['surface']
        self.assertEqual(set(projected['materials']),MATERIAL_KEYS)
        projected['materials']['lake_material']='changed'
        self.assertEqual(geo['surface']['materials']['lake_material'],'water')
        public=public_state_v2(self.state)
        self.assertEqual(set(public['geography']),{'slice-planet-reach'})
        self.assertNotIn('generator_config',repr(public))
        public['geography']['slice-planet-reach']['surface']['materials']['lake_mask']='changed'
        self.assertNotEqual(self.state['geography']['slice-planet-reach']['surface']['materials']['lake_mask'],'changed')


class PlanetV8PersistenceTests(PostgresTestCase, unittest.TestCase):
    def test_history_and_restore_preserve_saved_masks(self):
        sid=self.db.create_demo_v2('saved-v8',seed=321,planet_generator='planet-v8',preset='barren',geology='cratered',lake_material='lava')
        initial=self.db.current('saved-v8')['snapshot']
        state=initial['state']
        public=self.db.player_state(initial)
        self.assertEqual(set(public['geography']),{'saved-v8-planet-reach'})
        proposal = {"schema_version":"world-v2", "rules_version":"demo-v2", "base_turn":0,
                    "base_hash":initial["state_hash"], "submission_id":"persist-materials", "narrative":"Fixture report.",
                    "orders":{"allocations":[{"settlement_id":"saved-v8-forge", **{key:0 for key in ALLOCATIONS}, "farmers":300},
                                              {"settlement_id":"saved-v8-outpost", **{key:0 for key in ALLOCATIONS}, "farmers":100}], "actions":[]}}
        self.db.commit('saved-v8', proposal)
        current=self.db.current('saved-v8')['snapshot']
        self.assertEqual(current['state']['geography'], state['geography'])
        self.assertEqual(self.db.snapshot(sid)['state']['geography'],state['geography'])
        history,total=self.db.history('saved-v8')
        self.assertEqual(total,2)
        self.assertTrue(all(row['state']['geography']==state['geography'] for row in history))
        self.db.restore('saved-v8',sid,'restored-v8')
        restored=self.db.current('restored-v8')['snapshot']['state']
        self.assertEqual(state['geography'],restored['geography'])
        self.assertEqual(self.db.current('saved-v8')['snapshot']['state_hash'],current['state_hash'])
        Store.validate_state('world-v2','demo-v2',0,restored)


if __name__=='__main__':unittest.main()
