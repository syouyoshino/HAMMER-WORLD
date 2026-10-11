import json
import sqlite3
import tempfile
import unittest
import uuid
from pathlib import Path

from app.engine import RULES_VERSION, SCHEMA_VERSION, canonical_json, initial_state
from app.sqlite_migration import import_sqlite
from app.store import Store
from tests.pg_fixture import PostgresTestCase


class MigrationTests(PostgresTestCase, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.source = Path(self.tmp.name) / "legacy.sqlite3"
        self.backup = Path(self.tmp.name) / "legacy-backup.sqlite3"
        self._make_source()

    def tearDown(self):
        self.tmp.cleanup()
        super().tearDown()

    def _make_source(self, corrupt=False):
        state = initial_state("legacy-demo", 177)
        state_json = canonical_json(state)
        state_hash = Store.snapshot_hash("legacy-demo", 0, state)
        if corrupt:
            state_hash = "0" * 64
        with sqlite3.connect(self.source) as db:
            db.executescript("""
              CREATE TABLE campaigns(id TEXT PRIMARY KEY,kind TEXT NOT NULL,parent_snapshot_id TEXT,current_snapshot_id TEXT);
              CREATE TABLE snapshots(id TEXT PRIMARY KEY,campaign_id TEXT,turn INTEGER,schema_version TEXT,rules_version TEXT,
                state_json TEXT,state_hash TEXT,command_json TEXT,submission_id TEXT,created_at TEXT);
              CREATE TABLE outbox(snapshot_id TEXT PRIMARY KEY,status TEXT,attempts INTEGER,last_error TEXT,remote_file_id TEXT);
            """)
            db.execute("INSERT INTO campaigns VALUES(?,?,?,?)", ("legacy-demo", "demo", None, None))
            db.execute("INSERT INTO snapshots VALUES(?,?,?,?,?,?,?,?,?,?)",
                       ("snapshot-legacy", "legacy-demo", 0, SCHEMA_VERSION, RULES_VERSION,
                        state_json, state_hash, None, None, "2026-10-01T00:00:00+00:00"))
            db.execute("UPDATE campaigns SET current_snapshot_id='snapshot-legacy'")
            db.execute("INSERT INTO outbox VALUES(?,?,?,?,?)", ("snapshot-legacy", "pending", 0, None, None))

    def test_migration_preserves_ids_json_pointers_and_outbox_and_backs_up_first(self):
        original = self.source.read_bytes()
        result = import_sqlite(self.source, self.backup, self.db)
        self.assertTrue(self.backup.exists())
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(result["snapshots"], 1)
        current = self.db.current("legacy-demo")
        self.assertEqual(current["snapshot"]["id"], "snapshot-legacy")
        self.assertEqual(current["snapshot"]["state"], initial_state("legacy-demo", 177))
        self.assertEqual(self.db.archive_outbox("snapshot-legacy")["status"], "pending")

    def test_bad_hash_and_nonempty_target_are_rejected_atomically(self):
        with sqlite3.connect(self.source) as db:
            db.execute("UPDATE snapshots SET state_hash=?", ("0" * 64,))
        with self.assertRaisesRegex(ValueError, "checksum"):
            import_sqlite(self.source, self.backup, self.db)
        self.assertEqual(self.db.campaigns(), [])
        with sqlite3.connect(self.source) as db:
            db.execute("UPDATE snapshots SET state_hash=?", (Store.snapshot_hash("legacy-demo", 0, initial_state("legacy-demo", 177)),))
        self.db.create_pregame("already-there")
        with self.assertRaisesRegex(ValueError, "empty"):
            import_sqlite(self.source, self.backup, self.db)
        self.assertEqual([c["id"] for c in self.db.campaigns()], ["already-there"])

    def test_cross_campaign_current_pointer_is_rejected_before_import(self):
        with sqlite3.connect(self.source) as db:
            db.execute("UPDATE campaigns SET current_snapshot_id='another-campaign-snapshot'")
        with self.assertRaisesRegex(ValueError, "current snapshot campaign"):
            import_sqlite(self.source,self.backup,self.db)
        self.assertEqual(self.db.campaigns(),[])

    def test_self_consistent_invalid_state_and_malformed_command_are_rejected(self):
        state=initial_state("legacy-demo",177); state["food"]=-1
        with sqlite3.connect(self.source) as db:
            db.execute("UPDATE snapshots SET state_json=?,state_hash=?",
                (canonical_json(state),Store.snapshot_hash("legacy-demo",0,state)))
        with self.assertRaisesRegex(ValueError,"resource invariant"):
            import_sqlite(self.source,self.backup,self.db)
        state=initial_state("legacy-demo",177)
        with sqlite3.connect(self.source) as db:
            db.execute("UPDATE snapshots SET state_json=?,state_hash=?,command_json=?",
                (canonical_json(state),Store.snapshot_hash("legacy-demo",0,state),"{"))
        with self.assertRaises(ValueError): import_sqlite(self.source,self.backup,self.db)
        self.assertEqual(self.db.campaigns(),[])


if __name__ == "__main__":
    unittest.main()
