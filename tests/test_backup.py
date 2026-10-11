"""Real PostgreSQL custom-format backup recovery into a disposable database."""
import os
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app.store import Store
from tests.pg_fixture import PostgresTestCase


class BackupTests(PostgresTestCase, unittest.TestCase):
    def test_dump_restores_history_branches_and_immutable_records(self):
        self.db.create_demo()
        proposal = self.db.packet('demo')['example']
        proposal['orders'] = {'farmers': 400, 'miners': 200, 'technicians': 100}
        committed = self.db.commit('demo', proposal)
        self.db.restore('demo', committed['snapshot_id'], 'branch')
        original = self.db.current('demo')['snapshot']
        self.db.create_demo_v2('demo-v2')
        v2_proposal = self.db.packet('demo-v2')['example']
        self.db.commit('demo-v2', v2_proposal)
        v2_original = self.db.current('demo-v2')['snapshot']
        database = 'recovery_' + uuid.uuid4().hex
        target_dsn = make_conninfo(self.dsn, dbname=database)
        with tempfile.TemporaryDirectory() as scratch:
            destination = Path(scratch) / 'campaign.dump'
            self.db.backup(str(destination))
            self.assertTrue(destination.read_bytes().startswith(b'PGDMP'))
            with psycopg.connect(self.dsn, autocommit=True) as admin:
                admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
            try:
                environment = os.environ.copy()
                pg_names = {'host': 'PGHOST', 'hostaddr': 'PGHOSTADDR', 'port': 'PGPORT',
                            'user': 'PGUSER', 'password': 'PGPASSWORD', 'sslmode': 'PGSSLMODE',
                            'sslrootcert': 'PGSSLROOTCERT'}
                for key, value in conninfo_to_dict(target_dsn).items():
                    if key in pg_names:
                        environment[pg_names[key]] = value
                result = subprocess.run(
                    ['pg_restore', '--dbname', database, '--exit-on-error', '--no-owner', '--no-privileges', str(destination)],
                    env=environment, capture_output=True, text=True,
                )
                # Keep connection strings out of assertion output.
                self.assertEqual(result.returncode, 0, 'pg_restore failed; inspect local server diagnostics')
                recovered = Store(target_dsn, schema=self.schema, initialize=False)
                self.assertEqual(recovered.current('demo')['snapshot']['state_hash'], original['state_hash'])
                self.assertEqual(recovered.current('demo')['snapshot']['state'], original['state'])
                self.assertEqual(recovered.history('demo')[1], 2)
                self.assertEqual(len(recovered.campaigns()), 3)
                self.assertEqual(recovered.current('demo-v2')['snapshot']['state_hash'], v2_original['state_hash'])
                self.assertEqual(recovered.current('demo-v2')['snapshot']['state'], v2_original['state'])
                self.assertEqual(recovered.archive_outbox(committed['snapshot_id'])['status'], 'pending')
                with recovered.connect() as connection:
                    with self.assertRaises(psycopg.Error):
                        connection.execute('UPDATE snapshots SET turn=999 WHERE id=%s', (original['id'],))
                    connection.rollback()
            finally:
                with psycopg.connect(self.dsn, autocommit=True) as admin:
                    admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(database)))


if __name__ == '__main__':
    unittest.main()
