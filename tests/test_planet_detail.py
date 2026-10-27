"""Native fine geography is authoritative; coarse maps are checked projections."""
import copy
import hashlib
import json
import unittest

from app.planet_detail import (WIDTH, HEIGHT, SCALE, SIZE, MAX_BYTES, VERSION,
    _noise, _mix_latitude, _summaries, _validate_courses, generate_planet_v10,
    validate_planet_detail, project_planet_detail)

CHOICES = {
    'continental': ('none','water','water-ice'),
    'archipelago': ('none','water','none'),
    'oceanic': ('none','none','none'),
    'arid': ('none','none','none'),
    'barren': ('cratered','lava','none'),
    'frozen': ('cratered','hydrocarbon','water-ice'),
}


class PlanetDetailTests(unittest.TestCase):
    fixtures = {}
    namespace = 'fine-test'
    seed = 123

    @classmethod
    def fixture(cls,preset='continental'):
        if preset not in cls.fixtures:
            cls.fixtures[preset]=generate_planet_v10(cls.namespace,cls.seed,preset,*CHOICES[preset],naming='generated')
        return cls.fixtures[preset]

    def test_native_resolution_and_real_subcell_geography(self):
        geo,p=self.fixture()
        self.assertEqual((p['version'],p['width'],p['height']),(VERSION,1024,640))
        self.assertEqual((WIDTH,HEIGHT,SCALE),(1024,640,8))
        self.assertEqual(len(p['elevation']),SIZE)
        self.assertLess(len(json.dumps(p,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()),MAX_BYTES)
        mixed=0;fine_relief=0
        for py in range(80):
            for px in range(128):
                cells=[(py*SCALE+dy)*WIDTH+px*SCALE+dx for dy in range(SCALE) for dx in range(SCALE)]
                mixed+=len({p['terrain_grid'][i]=='o' for i in cells})>1
                fine_relief+=len({p['elevation'][i] for i in cells})>12
        self.assertGreater(mixed,100)
        self.assertGreater(fine_relief,2000)
        self.assertNotIn('elevation',geo['surface'])
        self.assertEqual(len(geo['provinces']),40)

    def test_determinism_and_seed_isolation_without_input_mutation(self):
        geo,p=self.fixture()
        original=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
        repeated=generate_planet_v10(self.namespace,self.seed,'continental',*CHOICES['continental'],naming='generated')
        self.assertEqual((geo,p),repeated)
        alternate_geo,alternate=generate_planet_v10(self.namespace,self.seed+1,'continental',*CHOICES['continental'],naming='generated')
        self.assertNotEqual(alternate['elevation'],p['elevation'])
        self.assertNotEqual(alternate['terrain_grid'],p['terrain_grid'])
        self.assertEqual(original,hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest())
        self.assertEqual(geo['provinces'],alternate_geo['provinces'])

    def test_all_presets_materials_and_fine_craters(self):
        for preset,choices in CHOICES.items():
            with self.subTest(preset=preset):
                geo,p=self.fixture(preset)
                self.assertEqual(geo['surface']['preset'],preset)
                self.assertLess(len(json.dumps(p,separators=(',',':')).encode()),MAX_BYTES)
                if preset in ('barren','arid','frozen'):
                    self.assertLessEqual(set(p['terrain_grid']),set('r' if preset=='barren' else 'pr'))
                    self.assertEqual(p['rivers'],[])
                    self.assertFalse(any(f['kind'] in ('ocean','sea','river') for f in p['hydrography']['features']))
                else:
                    self.assertIn('o',p['terrain_grid'])
                    self.assertTrue(p['rivers'])
                lake=choices[1]
                self.assertEqual(bool(set(p['materials'])&set('whl')),lake!='none')
                self.assertEqual('i' in p['materials'],choices[2]!='none')
                self.assertEqual(bool(p['craters']),choices[0]!='none')
                if p['craters']:
                    self.assertTrue(any(c['radius_q']>256 for c in p['craters']))

    def test_summaries_and_canonical_province_anchors_use_actual_eligible_fine_land(self):
        geo,p=self.fixture()
        provinces,summary,anchors=_summaries(self.namespace,p['terrain_grid'],p['materials'])
        self.assertEqual((geo['provinces'],geo['terrain_grid'],p['province_anchors']),(provinces,summary,anchors))
        self.assertGreaterEqual(sum(a['cell'] is not None for a in anchors),3)
        for province,a in zip(provinces,anchors):
            if a['cell'] is None: continue
            i=a['cell'];x,y=i%WIDTH,i//WIDTH
            self.assertNotEqual(p['terrain_grid'][i],'o')
            self.assertNotIn(p['materials'][i],'whl')
            self.assertTrue(province['x']*SCALE<=x<(province['x']+16)*SCALE)
            self.assertTrue(province['y']*SCALE<=y<(province['y']+16)*SCALE)
        bad=copy.deepcopy(p);bad['province_anchors'][0]['cell']=SIZE
        with self.assertRaisesRegex(ValueError,'summary/anchors'): validate_planet_detail(bad,geo)

    def test_saved_river_receiver_graph_and_corruption(self):
        _,p=self.fixture()
        features=p['hydrography']['features']
        self.assertLessEqual(len(p['rivers']),96)
        _validate_courses(p,features,p['feature_index'],p['elevation'],False)
        river=p['rivers'][0]
        self.assertGreater(len(river['points']),20)
        bad=copy.deepcopy(p)
        bad['rivers'][0]['points'][1]=bad['rivers'][0]['points'][0]
        with self.assertRaises(ValueError): _validate_courses(bad,features,p['feature_index'],p['elevation'],False)
        bad=copy.deepcopy(p)
        bad['rivers'][0]['points']=[river['points'][0],(river['points'][0]+WIDTH*20)%SIZE,river['points'][-1]]
        with self.assertRaises(ValueError): _validate_courses(bad,features,p['feature_index'],p['elevation'],False)
        bad=copy.deepcopy(p)
        bad['rivers'][0]['points']=river['points'][:-1]
        with self.assertRaises(ValueError): _validate_courses(bad,features,p['feature_index'],p['elevation'],False)

    def test_strict_payload_corruption_and_fresh_projection(self):
        geo,p=self.fixture()
        for key,value in (('version','old'),('width',True),('height',640.0),('elevation',[False]*SIZE),
                          ('materials','q'*SIZE),('terrain_grid','x'*SIZE),('feature_index',[True]*SIZE),
                          ('feature_ids',[]),('seed','hidden')):
            bad=dict(p);bad[key]=value
            with self.assertRaises(ValueError,msg=key): validate_planet_detail(bad,geo)
        projected=project_planet_detail(p)
        self.assertEqual(projected,p)
        self.assertIsNot(projected['elevation'],p['elevation'])
        self.assertIsNot(projected['rivers'][0]['points'],p['rivers'][0]['points'])
        self.assertIsNot(projected['hydrography']['features'][0],p['hydrography']['features'][0])
        self.assertIsNot(projected['province_anchors'][0],p['province_anchors'][0])
        extras=copy.deepcopy(p)
        extras['seed']='hidden';extras['hydrography']['seed']='hidden';extras['hydrography']['features'][0]['secret']='hidden'
        self.assertEqual(project_planet_detail(extras),p)

    def test_meridional_air_exchange_preserves_bounds_and_removes_row_jumps(self):
        humidity=[1000 if i//WIDTH<HEIGHT//2 else 0 for i in range(SIZE)]
        humidity=_mix_latitude(_mix_latitude(humidity,16),16)
        self.assertEqual(humidity[0],1000)
        self.assertEqual(humidity[-1],0)
        self.assertGreaterEqual(min(humidity),0)
        self.assertLessEqual(max(humidity),1000)
        self.assertLess(max(abs(humidity[y*WIDTH]-humidity[(y-1)*WIDTH]) for y in range(1,HEIGHT)),40)

    def test_periodic_noise_has_a_smooth_longitude_seam(self):
        for scale in (8,25,83,205):
            self.assertEqual(_noise(123,0,100,scale,'test'),_noise(123,WIDTH,100,scale,'test'))
            self.assertLess(abs(_noise(123,WIDTH-1,100,scale,'test')-_noise(123,0,100,scale,'test')),200)
