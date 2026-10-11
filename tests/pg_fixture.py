"""Disposable isolated PostgreSQL schemas for tests; never falls back to SQLite."""
import os
import uuid
from unittest.mock import patch

import psycopg
from psycopg import sql

from app.store import Store


class PostgresTestCase:
    def setUp(self):
        self.dsn = os.environ.get("WOLD_TEST_DATABASE_URL")
        if not self.dsn:
            raise RuntimeError("WOLD_TEST_DATABASE_URL is required for tests")
        self.schema = "test_" + uuid.uuid4().hex
        with psycopg.connect(self.dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
        self.env_patcher=patch.dict(os.environ,{"WOLD_DATABASE_URL":self.dsn,"WOLD_DB_SCHEMA":self.schema,"WOLD_ACCESS_MODE":"local"})
        self.env_patcher.start()
        self.db = Store(self.dsn, schema=self.schema)

    def tearDown(self):
        with psycopg.connect(self.dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))
        self.env_patcher.stop()
