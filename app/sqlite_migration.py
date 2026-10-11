"""Explicit, read-only migration of a legacy SQLite database into PostgreSQL."""
import os
import json
import sqlite3
from pathlib import Path

from .engine import RULES_VERSION, SCHEMA_VERSION


def backup_sqlite_source(source, backup):
    """Copy a quiescent source using SQLite's backup API before inspecting it."""
    source = Path(source).resolve()
    backup = Path(backup).resolve()
    if source == backup:
        raise ValueError("SQLite backup path must differ from source")
    backup.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as src:
        with sqlite3.connect(backup) as dst:
            src.backup(dst)
    with sqlite3.connect(f"file:{backup}?mode=ro", uri=True) as check:
        result = check.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise ValueError("SQLite backup integrity check failed")
    return str(backup)


def import_sqlite(source, backup, store):
    """Import all immutable records and pointers without regeneration or coercion."""
    from .store import Store

    backup_sqlite_source(source, backup)
    with sqlite3.connect(f"file:{Path(backup).resolve()}?mode=ro", uri=True) as src:
        src.row_factory = sqlite3.Row
        tables = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"campaigns", "snapshots", "outbox"}.issubset(tables):
            raise ValueError("SQLite source does not contain the expected campaign tables")
        fk_errors = src.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise ValueError("SQLite source has broken foreign key references")
        campaigns = src.execute("SELECT * FROM campaigns ORDER BY id").fetchall()
        snapshots = src.execute("SELECT rowid AS _migration_rowid,* FROM snapshots ORDER BY rowid").fetchall()
        outbox = src.execute("SELECT * FROM outbox").fetchall()
        campaign_columns = {r[1] for r in src.execute("PRAGMA table_info(campaigns)")}
        snapshot_columns = {r[1] for r in src.execute("PRAGMA table_info(snapshots)")}
        outbox_columns = {r[1] for r in src.execute("PRAGMA table_info(outbox)")}

    for row in snapshots:
        record = dict(row)
        if record["schema_version"] != SCHEMA_VERSION or record["rules_version"] != RULES_VERSION:
            raise ValueError("SQLite source contains an unsupported snapshot version")
        state = json.loads(record["state_json"])
        if record["state_hash"] != Store.snapshot_hash(record["campaign_id"], record["turn"], state,
                record["schema_version"],record["rules_version"]):
            raise ValueError("SQLite source snapshot checksum verification failed")
        Store.validate_state(record["schema_version"],record["rules_version"],record["turn"],state)
        if record.get("command_json"):
            command=json.loads(record["command_json"])
            if (record["schema_version"],record["rules_version"])==(SCHEMA_VERSION,RULES_VERSION):
                from .engine import validate_submission
                validate_submission(command)
            else:
                from .engine_v2 import validate_submission
                validate_submission(command)
    snapshot_owners = {dict(row)["id"]: dict(row)["campaign_id"] for row in snapshots}
    for campaign in campaigns:
        item = dict(campaign)
        current = item.get("current_snapshot_id") if "current_snapshot_id" in campaign_columns else None
        if current and snapshot_owners.get(current) != item["id"]:
            raise ValueError("SQLite source current snapshot campaign invariant failed")

    with store.connect() as c:
        c.execute("BEGIN")
        c.execute("LOCK TABLE campaigns,snapshots,outbox IN ACCESS EXCLUSIVE MODE")
        counts = [c.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]
                  for table in ("campaigns", "snapshots", "outbox")]
        if any(counts):
            raise ValueError("PostgreSQL target must be empty before SQLite import")
        for campaign in campaigns:
            item = dict(campaign)
            c.execute("INSERT INTO campaigns(id,kind,parent_snapshot_id,current_snapshot_id) VALUES(%s,%s,NULL,NULL)",
                      (item["id"], item["kind"]))
        for row in snapshots:
            item = dict(row)
            values = (item["id"], item["campaign_id"], item["turn"], item["schema_version"],
                      item["rules_version"], item["state_json"], item["state_hash"],
                      item.get("command_json"), item.get("submission_id"), item["created_at"])
            c.execute("""INSERT INTO snapshots(id,campaign_id,turn,schema_version,rules_version,state_json,
                state_hash,command_json,submission_id,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", values)
        for campaign in campaigns:
            item = dict(campaign)
            parent = item.get("parent_snapshot_id") if "parent_snapshot_id" in campaign_columns else None
            current = item.get("current_snapshot_id") if "current_snapshot_id" in campaign_columns else None
            c.execute("UPDATE campaigns SET parent_snapshot_id=%s,current_snapshot_id=%s WHERE id=%s",
                      (parent, current, item["id"]))
        for row in outbox:
            item = dict(row)
            # Older SQLite outboxes predate archive freezing and leases.
            fields = ("snapshot_id", "status", "attempts", "last_error", "remote_file_id")
            vals = [item.get(k) for k in fields]
            if "archive_folder_id" in outbox_columns:
                vals += [item.get("archive_folder_id"), item.get("projection_version"),
                         item.get("payload_bytes"), item.get("payload_checksum")]
            c.execute("""INSERT INTO outbox(snapshot_id,status,attempts,last_error,remote_file_id,
                archive_folder_id,projection_version,payload_bytes,payload_checksum)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                tuple(vals + [None] * (9 - len(vals))))
    return {"campaigns": len(campaigns), "snapshots": len(snapshots), "outbox": len(outbox),
            "backup": str(Path(backup).resolve())}
