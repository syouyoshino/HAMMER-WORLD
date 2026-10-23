"""Creation-time preset choices through the actual operator command."""
import json
import os
import subprocess
import sys
import unittest

from tests.pg_fixture import PostgresTestCase


class PlanetPresetCommandTests(PostgresTestCase, unittest.TestCase):
    def test_v6_cli_selects_cylindrical_generator_for_new_worlds(self):
        command = [sys.executable, '-m', 'app.cli', 'init-v2', '--campaign-id', 'cli-v6',
                   '--planet-generator', 'planet-v6', '--preset', 'archipelago']
        result = subprocess.run(command, env=dict(os.environ), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        state = self.db.current('cli-v6')['snapshot']['state']
        config = state['_private']['generator_config']
        self.assertEqual(config['planet'], 'planet-v6')
        self.assertEqual(config['grid'], 'grid128x80')
        self.assertEqual(len(config['planet_presets']), 4)
        self.assertTrue(all(geo['surface']['topology'] == 'cylinder-x'
                            for geo in state['geography'].values()))

    def test_v5_cli_creates_larger_independent_presets_without_replacing_existing_maps(self):
        self.db.create_demo_v2('cli-old', seed=55, planet_generator='planet-v4', preset='arid')
        before = self.db.current('cli-old')['snapshot']['state_hash']
        command = [sys.executable, '-m', 'app.cli', 'init-v2', '--campaign-id', 'cli-v5',
                   '--planet-generator', 'planet-v5', '--preset', 'oceanic',
                   '--planet-preset', 'cli-v5-planet-reach=barren']
        result = subprocess.run(command, env=dict(os.environ), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        state = self.db.current('cli-v5')['snapshot']['state']
        for planet_id, geo in state['geography'].items():
            self.assertEqual((geo['planet']['width'], geo['planet']['height']), (128, 80))
            self.assertEqual(geo['surface']['preset'], 'barren' if planet_id.endswith('-reach') else 'oceanic')
        self.assertEqual(self.db.current('cli-old')['snapshot']['state_hash'], before)

    def test_choices_persist_and_bad_or_repeated_creation_cannot_replace_them(self):
        command = [sys.executable, '-m', 'app.cli', 'init-v2', '--campaign-id', 'cli-presets',
                   '--planet-generator', 'planet-v4', '--preset', 'auto',
                   '--planet-preset', 'cli-presets-planet-reach=barren',
                   '--planet-preset', 'cli-presets-planet-ash=archipelago']
        result = subprocess.run(command, env=dict(os.environ), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['campaign_id'], 'cli-presets')
        initial = self.db.current('cli-presets')['snapshot']
        choices = initial['state']['_private']['generator_config']['planet_presets']
        self.assertEqual(choices['cli-presets-planet-reach'], 'barren')
        self.assertEqual(choices['cli-presets-planet-ash'], 'archipelago')
        self.assertEqual(initial['state']['geography']['cli-presets-planet-reach']['surface']['rivers'], [])
        repeated = subprocess.run(command, env=dict(os.environ), capture_output=True, text=True)
        self.assertNotEqual(repeated.returncode, 0)
        self.assertIn('campaign already exists', repeated.stderr)
        self.assertEqual(self.db.current('cli-presets')['snapshot']['state_hash'], initial['state_hash'])
        rejected = subprocess.run([sys.executable, '-m', 'app.cli', 'init-v2', '--campaign-id',
                                   'bad-cli-preset', '--planet-generator', 'planet-v4',
                                   '--planet-preset', 'bad-cli-preset-system-hearth=barren'],
                                  env=dict(os.environ), capture_output=True, text=True)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertNotIn('bad-cli-preset', [item['id'] for item in self.db.campaigns()])
        self.assertEqual(self.db.current('cli-presets')['snapshot']['state_hash'], initial['state_hash'])

    def test_v7_cli_persists_per_planet_geology_and_rejects_bad_overrides(self):
        command = [sys.executable, '-m', 'app.cli', 'init-v2', '--campaign-id', 'cli-v7',
                   '--planet-generator', 'planet-v7', '--preset', 'barren',
                   '--planet-geology', 'cli-v7-planet-reach=cratered']
        result = subprocess.run(command, env=dict(os.environ), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        state = self.db.current('cli-v7')['snapshot']['state']
        config = state['_private']['generator_config']
        self.assertEqual(config['planet'], 'planet-v7')
        self.assertEqual(config['planet_geologies']['cli-v7-planet-reach'], 'cratered')
        self.assertEqual(config['planet_geologies']['cli-v7-planet-ash'], 'none')
        self.assertEqual(state['geography']['cli-v7-planet-ash']['surface']['craters'], [])
        for args in (
            ['--planet-geology', 'cli-v7-planet-reach=none', '--planet-geology', 'cli-v7-planet-reach=cratered'],
            ['--planet-geology', 'unknown-planet=cratered'],
            ['--planet-geology', 'bad-v7-planet-reach=cratered', '--preset', 'continental'],
        ):
            rejected = subprocess.run([sys.executable, '-m', 'app.cli', 'init-v2', '--campaign-id', 'bad-v7',
                                       '--planet-generator', 'planet-v7', '--preset', 'barren', *args],
                                      env=dict(os.environ), capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            if '--preset' in args:
                self.assertIn('cratered geology requires an arid, barren, or frozen preset', rejected.stderr)
            self.assertNotIn('bad-v7', [item['id'] for item in self.db.campaigns()])
        legacy_geology = subprocess.run([sys.executable, '-m', 'app.cli', 'init-v2', '--campaign-id',
                                        'bad-legacy-geology', '--geology', 'none'],
                                       env=dict(os.environ), capture_output=True, text=True)
        self.assertNotEqual(legacy_geology.returncode, 0)
        self.assertNotIn('bad-legacy-geology', [item['id'] for item in self.db.campaigns()])




class PlanetMaterialCommandTests(PostgresTestCase, unittest.TestCase):
    def run_cli(self, cid, options):
        return subprocess.run([sys.executable, '-m', 'app.cli', 'init-v2', '--campaign-id', cid, *options],
                              env=dict(os.environ), capture_output=True, text=True)

    def test_v8_global_and_per_planet_options_persist(self):
        result=self.run_cli('cli-v8',['--planet-generator','planet-v8','--preset','barren',
                                    '--geology','cratered','--lake-material','water','--polar-caps','water-ice',
                                    '--planet-lake-material','cli-v8-planet-reach=none',
                                    '--planet-polar-caps','cli-v8-planet-ash=none'])
        self.assertEqual(result.returncode,0,result.stderr)
        state=self.db.current('cli-v8')['snapshot']['state']
        config=state['_private']['generator_config']
        self.assertEqual(config['planet_lake_materials']['cli-v8-planet-reach'],'none')
        self.assertEqual(config['planet_lake_materials']['cli-v8-planet-ash'],'water')
        self.assertEqual(config['planet_polar_caps']['cli-v8-planet-ash'],'none')
        self.assertEqual(config['planet_polar_caps']['cli-v8-planet-reach'],'water-ice')
        self.db.validate_state('world-v2','demo-v2',0,state)

    def test_cli_rejects_legacy_even_explicit_none_duplicates_unknown_and_bad_combinations(self):
        for version in range(1,8):
            for flag in ('--lake-material','--polar-caps'):
                result=self.run_cli('bad-legacy-material',['--planet-generator',f'planet-v{version}',flag,'none'])
                self.assertNotEqual(result.returncode,0)
                self.assertIn('require --planet-generator planet-v8',result.stderr)
        for options in (
            ['--planet-lake-material','bad-v8-planet-reach=water','--planet-lake-material','bad-v8-planet-reach=lava'],
            ['--planet-polar-caps','bad-v8-planet-reach=none','--planet-polar-caps','bad-v8-planet-reach=water-ice'],
            ['--planet-lake-material','unknown=water'],
            ['--planet-polar-caps','unknown=water-ice'],
            ['--planet-lake-material','bad-v8-planet-reach=unknown'],
            ['--planet-polar-caps','missing-equals'],
            ['--lake-material','lava','--polar-caps','water-ice'],
            ['--preset','frozen','--lake-material','water'],
            ['--preset','frozen','--lake-material','lava'],
            ['--lake-material','hydrocarbon'],
        ):
            result=self.run_cli('bad-v8',['--planet-generator','planet-v8','--preset','barren',*options])
            self.assertNotEqual(result.returncode,0,result.stdout)
        self.assertNotIn('bad-v8',[c['id'] for c in self.db.campaigns()])
        self.assertNotIn('bad-legacy-material',[c['id'] for c in self.db.campaigns()])


if __name__ == '__main__': unittest.main()
