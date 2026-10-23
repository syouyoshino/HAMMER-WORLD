"""Creation-time preset choices through the actual operator command."""
import json
import os
import subprocess
import sys
import unittest

from tests.pg_fixture import PostgresTestCase


class PlanetPresetCommandTests(PostgresTestCase, unittest.TestCase):
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


if __name__ == '__main__': unittest.main()
