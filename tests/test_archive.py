import hashlib
import json
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from app.archive import ArchiveWorker
from app.engine import SCHEMA_VERSION,RULES_VERSION,canonical_json,initial_state
from app.store import Store
from tests.pg_fixture import PostgresTestCase


class SimulatedProcessCrash(BaseException):
    pass


class FakeDrive:
    def __init__(self):
        self.files = {}
        self.id_count = 0
        self.fail_before_upload = None
        self.crash_after_upload = False
        self.wrong_bytes = False
        self.wrong_parent = False

    def generate_id(self):
        self.id_count += 1
        return f"reserved-id-{self.id_count}"

    def create_file(self, file_id, name, folder_id, payload):
        if self.fail_before_upload:
            raise RuntimeError(self.fail_before_upload)
        if file_id in self.files:
            raise FileExistsError("reserved file ID already exists")
        actual = payload + b" changed" if self.wrong_bytes else payload
        parent = "unexpected-folder" if self.wrong_parent else folder_id
        self.files[file_id] = {"metadata": {"id": file_id, "name": name,
                                             "mimeType": "application/json", "parents": [parent],
                                             "trashed": False}, "payload": actual}
        if self.crash_after_upload:
            self.crash_after_upload = False
            raise SimulatedProcessCrash()

    def get_file(self, file_id):
        record = self.files.get(file_id)
        return None if record is None else dict(record["metadata"])

    def download_file(self, file_id):
        return self.files[file_id]["payload"]


class ArchiveTests(PostgresTestCase, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.store = self.db
        self.snapshot_id = self.store.create_demo("demo", seed=9931)

    def outbox(self):
        return self.store.archive_outbox(self.snapshot_id)

    def create_real_archive_fixture(self):
        self.store.create_pregame("real-campaign")
        state=initial_state("real-campaign",771)
        sid=str(uuid.uuid4()); h=Store.snapshot_hash("real-campaign",0,state)
        with self.store.connect() as c:
            c.execute("""INSERT INTO snapshots(id,campaign_id,turn,schema_version,rules_version,state_json,state_hash,
                command_json,submission_id,created_at) VALUES(%s,'real-campaign',0,%s,%s,%s,%s,NULL,NULL,'fixture')""",
                (sid,SCHEMA_VERSION,RULES_VERSION,canonical_json(state),h))
            c.execute("UPDATE campaigns SET current_snapshot_id=%s WHERE id='real-campaign'",(sid,))
            c.execute("INSERT INTO outbox(snapshot_id,status) VALUES(%s,'pending')",(sid,))
        return sid

    def test_missing_credentials_or_folder_leave_item_pending(self):
        worker = ArchiveWorker(self.store, None, {"demo": "folder-demo"})
        result = worker.sync()
        self.assertEqual(result["status"], "disabled")
        self.assertEqual(self.outbox()["status"], "pending")
        self.assertEqual(self.outbox()["attempts"], 0)
        worker = ArchiveWorker(self.store, FakeDrive(), {"demo": None})
        result = worker.sync()
        self.assertEqual(result["status"], "disabled")
        self.assertEqual(self.outbox()["status"], "pending")
        self.assertEqual(self.outbox()["attempts"], 0)

    def test_demo_and_real_folder_collision_is_rejected_without_freezing(self):
        drive = FakeDrive()
        worker = ArchiveWorker(self.store, drive, {"demo":"shared-folder","pregame":"shared-folder"})
        self.assertEqual(worker.sync()["status"], "disabled")
        self.assertEqual(drive.id_count, 0)
        self.assertIsNone(self.outbox()["payload_bytes"])

    def test_frozen_demo_folder_cannot_become_real_folder_on_retry(self):
        drive=FakeDrive()
        claim=self.store.claim_archive("worker-a",60,{"demo":"demo-folder","pregame":"real-folder"})
        self.assertEqual(claim["folder_id"],"demo-folder")
        with self.store.connect() as c:
            c.execute("UPDATE outbox SET lease_expires_at=0 WHERE snapshot_id=%s",(self.snapshot_id,))
        worker=ArchiveWorker(self.store,drive,{"demo":"changed-demo","pregame":"demo-folder"},owner="worker-b")
        self.assertEqual(worker.sync()["items"][0]["status"],"disabled")
        self.assertEqual(drive.id_count,0)
        self.assertEqual(self.outbox()["archive_folder_id"],"demo-folder")

    def test_frozen_real_folder_cannot_become_demo_folder_on_retry(self):
        real_sid=self.create_real_archive_fixture()
        with self.store.connect() as c: c.execute("UPDATE outbox SET status='verified' WHERE snapshot_id=%s",(self.snapshot_id,))
        claim=self.store.claim_archive("worker-a",60,{"demo":"demo-folder","pregame":"real-folder"})
        self.assertEqual(claim["snapshot_id"],real_sid)
        with self.store.connect() as c: c.execute("UPDATE outbox SET lease_expires_at=0 WHERE snapshot_id=%s",(real_sid,))
        worker=ArchiveWorker(self.store,FakeDrive(),{"demo":"real-folder","pregame":"changed-real"},owner="worker-b")
        result=worker.sync()
        self.assertEqual(result["items"][0]["status"],"disabled")
        self.assertEqual(self.store.archive_outbox(real_sid)["archive_folder_id"],"real-folder")

    def test_historical_opposite_kind_folder_cannot_be_reused(self):
        real_sid=self.create_real_archive_fixture()
        with self.store.connect() as c: c.execute("UPDATE outbox SET status='verified' WHERE snapshot_id=%s",(self.snapshot_id,))
        real_claim=self.store.claim_archive("worker-r",60,{"demo":"demo-folder","pregame":"shared"})
        self.assertEqual(real_claim["snapshot_id"],real_sid)
        with self.store.connect() as c:
            c.execute("UPDATE outbox SET status='verified',lease_owner=NULL,lease_expires_at=NULL WHERE snapshot_id=%s",(real_sid,))
            c.execute("UPDATE outbox SET status='verified' WHERE snapshot_id=%s",(self.snapshot_id,))
        self.store.create_demo("second-demo",seed=992)
        worker=ArchiveWorker(self.store,FakeDrive(),{"demo":"shared","pregame":"other"},owner="worker-d")
        result=worker.sync()
        self.assertEqual(result["items"][0]["status"],"disabled")
        current_id=self.store.current("second-demo")["snapshot"]["id"]
        self.assertIsNone(self.store.archive_outbox(current_id)["payload_bytes"])

    def test_concurrent_cross_kind_folder_binding_allows_only_one_kind(self):
        self.create_real_archive_fixture()
        barrier=Barrier(2)
        configurations=[{"demo":"shared","pregame":"other-real"},{"demo":"other-demo","pregame":"shared"}]
        kinds=["demo","pregame"]
        def claim(index):
            barrier.wait()
            return self.store.claim_archive(f"worker-{index}",60,configurations[index],kind=kinds[index])
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(claim,(0,1)))
        claims=[r for r in results if r]
        self.assertEqual(sum(not r.get("disabled") for r in claims),1)
        self.assertEqual(sum(bool(r.get("disabled")) for r in claims),1)

    def test_success_freezes_public_projection_and_exact_checksum(self):
        drive = FakeDrive()
        result = ArchiveWorker(self.store, drive, {"demo": "demo-folder"}, owner="worker-a").sync()
        self.assertEqual(result["status"], "complete")
        item = result["items"][0]
        row = self.outbox()
        archived = json.loads(row["payload_bytes"])
        serialized = row["payload_bytes"].decode("utf-8")
        self.assertEqual(row["status"], "verified")
        self.assertEqual(row["remote_file_id"], item["remote_file_id"])
        self.assertEqual(hashlib.sha256(row["payload_bytes"]).hexdigest(), row["payload_checksum"])
        self.assertEqual(drive.download_file(item["remote_file_id"]), row["payload_bytes"])
        self.assertEqual(archived["archive_schema_version"], "archive-player-v1")
        self.assertEqual(archived["state"]["turn"], 0)
        for secret in ("_private", "seeded_marker", "state_hash", "command_json", "submission_id"):
            self.assertNotIn(secret, serialized)
        self.assertEqual(row["archive_folder_id"], "demo-folder")
        self.assertEqual(row["projection_version"], "archive-player-v1")

    def test_upload_failure_is_pending_and_error_is_sanitized(self):
        drive = FakeDrive()
        drive.fail_before_upload = "Bearer TOP-SECRET-token"
        result = ArchiveWorker(self.store, drive, {"demo": "demo-folder"}, owner="worker-a").sync()
        self.assertEqual(result["status"], "pending")
        self.assertEqual(self.outbox()["status"], "pending")
        self.assertEqual(self.outbox()["attempts"], 1)
        self.assertNotIn("TOP-SECRET", self.outbox()["last_error"])
        self.assertNotIn("TOP-SECRET", json.dumps(result))
        self.assertTrue(self.outbox()["remote_file_id"])
        self.assertEqual(self.outbox()["archive_folder_id"], "demo-folder")
        self.assertIsNotNone(self.outbox()["payload_bytes"])

    def test_crash_after_remote_upload_reuses_reserved_id_and_frozen_folder(self):
        drive = FakeDrive()
        drive.crash_after_upload = True
        first = ArchiveWorker(self.store, drive, {"demo": "folder-original"}, owner="worker-a")
        with self.assertRaises(SimulatedProcessCrash):
            first.sync()
        reserved = self.outbox()["remote_file_id"]
        self.assertIn(reserved, drive.files)
        self.assertEqual(self.outbox()["status"], "uploading")
        with self.store.connect() as c:
            c.execute("UPDATE outbox SET lease_expires_at=0 WHERE snapshot_id=%s", (self.snapshot_id,))

        retry = ArchiveWorker(self.store, drive, {"demo": "folder-changed"}, owner="worker-b")
        result = retry.sync()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(self.outbox()["remote_file_id"], reserved)
        self.assertEqual(drive.id_count, 1)
        self.assertEqual(drive.files[reserved]["metadata"]["parents"], ["folder-original"])
        self.assertEqual(self.outbox()["status"], "verified")

    def test_wrong_remote_bytes_or_parent_never_verify(self):
        for mode in ("wrong_bytes", "wrong_parent"):
            with self.subTest(mode=mode):
                self.tearDown()
                self.setUp()
                drive = FakeDrive()
                setattr(drive, mode, True)
                result = ArchiveWorker(self.store, drive, {"demo": "demo-folder"}).sync()
                self.assertEqual(result["status"], "pending")
                self.assertEqual(self.outbox()["status"], "pending")
                self.assertEqual(self.outbox()["last_error"], "archive_verification_failed")

    def test_expired_lease_can_be_reclaimed_but_old_owner_cannot_ack(self):
        barrier = Barrier(2)
        def claim(owner):
            barrier.wait()
            return self.store.claim_archive(owner, 60, {"demo": "demo-folder"})
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(claim, ["worker-a", "worker-b"]))
        claims = [result for result in results if result]
        self.assertEqual(len(claims), 1)
        first = claims[0]
        old_owner = first["lease_owner"]
        with self.store.connect() as c:
            c.execute("UPDATE outbox SET lease_expires_at=0 WHERE snapshot_id=%s", (self.snapshot_id,))
        second = self.store.claim_archive("worker-c", 60, {"demo": "new-folder"})
        self.assertEqual(second["folder_id"], "demo-folder")
        self.assertEqual(second["lease_owner"], "worker-c")
        self.assertFalse(self.store.mark_archive_verified(self.snapshot_id, old_owner, "whatever"))
        self.assertTrue(self.store.persist_archive_file_id(self.snapshot_id, "worker-c", "durable-id"))
        self.assertFalse(self.store.mark_archive_verified(self.snapshot_id, "worker-c", "wrong-id"))

    def test_environment_uses_separate_demo_and_real_folders(self):
        env = {"WOLD_DRIVE_ACCESS_TOKEN": "not-used-in-this-test",
               "WOLD_DRIVE_DEMO_FOLDER_ID": "fixture-folder",
               "WOLD_DRIVE_FOLDER_ID": "real-folder"}
        from app.archive import worker_from_environment
        worker = worker_from_environment(self.store, env)
        worker.adapter.close()
        claim = self.store.claim_archive("worker", 30,
                                         {"demo": env["WOLD_DRIVE_DEMO_FOLDER_ID"],
                                          "pregame": env["WOLD_DRIVE_FOLDER_ID"]})
        self.assertEqual(claim["folder_id"], "fixture-folder")
        self.assertNotEqual(claim["folder_id"], env["WOLD_DRIVE_FOLDER_ID"])


if __name__ == "__main__":
    unittest.main()
