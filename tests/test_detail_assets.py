"""Immutable detail publication, scoped reads, archive and recovery contracts."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import uuid
from unittest.mock import patch

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app.detail_assets import detail_reference, validate_detail_reference
from app.engine import canonical_json
from app.store import Store, now
from app.universe import build_universe, public_state_v2
from app.planet_generation import validate_surface, project_surface, _province_rectangles
from tests.pg_fixture import PostgresTestCase


class DetailReferenceTests(unittest.TestCase):
    def test_reference_is_canonical_bounded_and_strict(self):
        payload = {"version":"planet-detail-v2", "width":1024, "height":640, "label":"é"}
        ref = detail_reference(payload)
        self.assertEqual(hashlib.sha256(canonical_json(payload).encode()).hexdigest(), ref["sha256"])
        for key, value in (("width",True), ("height",639), ("sha256","A"*64),
                           ("byte_length",0), ("byte_length",8388609), ("private","canary")):
            bad = dict(ref); bad[key] = value
            with self.assertRaises(ValueError):
                validate_detail_reference(bad)
        with self.assertRaises(ValueError):
            detail_reference(payload | {"oversized":"x"*8388608})

    def test_v10_summary_contract_is_small_and_rejects_fine_snapshot_arrays(self):
        geo = {"planet":{"id":"summary-planet-001","name":"Summary","width":128,"height":80},
               "provinces":_province_rectangles("summary",128,80,16), "terrain_grid":"p"*(128*80),
               "surface":{"version":"planet-v10","preset":"continental","topology":"cylinder-x",
                          "hydrology":"ocean-draining","sea_level":400,"geology":"none",
                          "lake_material":"none","polar_caps":"none"}}
        validate_surface(geo)
        self.assertEqual(geo["surface"], project_surface(geo)["surface"])
        self.assertLess(len(canonical_json(geo)),20000)
        for key in ("elevation","drainage","hydrography","materials","_private"):
            bad = copy.deepcopy(geo); bad["surface"][key] = []
            with self.assertRaises(ValueError): validate_surface(bad)
        bad = copy.deepcopy(geo); bad["provinces"][1]["x"] = 0
        with self.assertRaises(ValueError): validate_surface(bad)


class DetailAssetPersistenceTests(PostgresTestCase, unittest.TestCase):
    # Natural generation has separate deterministic tests. Reuse its actual
    # result while each persistence case still writes a fresh isolated schema.
    fixture = None

    def create(self, campaign_id="detail"):
        if type(self).fixture is None:
            assets = {}
            state = build_universe("detail",741903,planet_generator="planet-v10",preset="continental",
                                   feature_names="generated",detail_assets=assets)
            type(self).fixture = state, assets
        self.assertEqual("detail",campaign_id)
        def fixture_universe(requested_campaign, seed, **options):
            self.assertEqual("detail",requested_campaign)
            state, assets = type(self).fixture
            options["detail_assets"].update(copy.deepcopy(assets))
            return copy.deepcopy(state)
        with patch("app.store.build_universe",side_effect=fixture_universe):
            self.db.create_demo_v2(campaign_id, planet_generator="planet-v10", preset="continental", feature_names="generated")
        return self.db.current(campaign_id)["snapshot"]

    def test_assets_stay_out_of_snapshots_and_survive_turn_branch_and_archive(self):
        original = self.create()
        planet = "detail-planet-reach"
        loaded = self.db.planet_detail("detail", planet)
        ref = loaded["detail_ref"]
        self.assertEqual(ref, detail_reference(loaded["detail"]))
        with patch("app.planet_detail.generate_planet_v10", side_effect=AssertionError("map read regenerated detail")):
            self.assertEqual(loaded, self.db.planet_detail("detail", planet, original["id"]))
            self.db.history("detail")
        serialized = canonical_json(original["state"])
        self.assertNotIn('"feature_index"', serialized)
        self.assertNotIn('"elevation"', serialized)
        self.assertNotIn('"hydrography"', serialized)
        self.assertLess(len(serialized),100000)
        self.assertEqual({planet}, set(public_state_v2(original["state"])["geography"]))
        with self.db.connect() as c:
            self.assertEqual(4, c.execute("SELECT count(*) AS n FROM planet_detail_assets").fetchone()["n"])
            with self.assertRaises(psycopg.Error):
                c.execute("UPDATE planet_detail_assets SET version=version WHERE sha256=%s", (ref["sha256"],))
            c.rollback()
            with self.assertRaises(psycopg.Error):
                c.execute("DELETE FROM planet_detail_assets WHERE sha256=%s", (ref["sha256"],))
            c.rollback()
        proposal = self.db.packet("detail")["example"]
        committed = self.db.commit("detail", proposal)
        self.assertEqual(loaded["detail"], self.db.planet_detail("detail", planet, original["id"])["detail"])
        self.assertEqual(original["id"], self.db.planet_detail("detail", planet, original["id"])["snapshot_id"])
        self.db.restore("detail", original["id"], "detail-branch")
        self.assertEqual(loaded["detail"], self.db.planet_detail("detail-branch", planet)["detail"])
        self.db.commit("detail-branch", self.db.packet("detail-branch")["example"])
        self.assertEqual(committed["snapshot_id"], self.db.current("detail")["snapshot"]["id"])
        with self.db.connect() as c:
            self.assertEqual(4, c.execute("SELECT count(*) AS n FROM planet_detail_assets").fetchone()["n"])
        claim = self.db.claim_archive("detail-worker", 60, {"demo":"demo-folder"})
        archive = json.loads(claim["payload_bytes"])
        self.assertEqual("archive-player-v3", archive["archive_schema_version"])
        self.assertEqual({ref["sha256"]}, set(archive["detail_assets"]))
        self.assertEqual(loaded["detail"], archive["detail_assets"][ref["sha256"]])
        for pid, geo in original["state"]["geography"].items():
            if pid != planet:
                self.assertNotIn(geo["detail_ref"]["sha256"], claim["payload_bytes"].decode())

    def test_interrupted_creation_rolls_back_assets_and_snapshot_together(self):
        with patch.object(self.db, "snapshot_hash", side_effect=RuntimeError("fixture interruption")):
            with self.assertRaisesRegex(RuntimeError, "fixture interruption"):
                self.create()
        with self.db.connect() as c:
            for table in ("planet_detail_assets", "snapshots", "campaigns", "outbox"):
                count = c.execute(sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(table))).fetchone()["n"]
                self.assertEqual(0, count, table)

    def test_detail_api_checks_login_campaign_snapshot_and_survey(self):
        snap = self.create()
        self.db.create_demo_v2("other")
        other = self.db.current("other")["snapshot"]
        import app.main as main
        from fastapi.testclient import TestClient
        env = {"WOLD_ACCESS_MODE":"private", "WOLD_GM_TOKEN":"fixture-gm", "WOLD_PLAYER_TOKEN":"fixture-player",
               "WOLD_PLAYER_CAMPAIGNS":"detail"}
        with patch.dict(os.environ, env), patch.object(main, "store", self.db), TestClient(main.app) as client:
            url = "/api/player/campaigns/detail/detail"
            params = {"planet_id":"detail-planet-reach", "snapshot_id":snap["id"]}
            auth = {"Authorization":"Bearer fixture-player"}
            self.assertEqual(404, client.get(url, params=params).status_code)
            self.assertEqual(404, client.get(url.replace("campaigns/detail/", "campaigns/other/"), params=params, headers=auth).status_code)
            for invalid in (other["id"], "false-snapshot"):
                self.assertEqual(404, client.get(url, params=params | {"snapshot_id":invalid}, headers=auth).status_code)
            for suffix in ("ash", "haven", "veil", "missing"):
                self.assertEqual(404, client.get(url, params=params | {"planet_id":f"detail-planet-{suffix}"}, headers=auth).status_code)
            response = client.get(url, params=params, headers=auth)
            self.assertEqual(200, response.status_code)
            self.assertEqual("no-store", response.headers["cache-control"])
            self.assertEqual(snap["id"], response.json()["snapshot_id"])
            self.assertNotIn("_private", response.text)
            self.assertNotIn("seed", response.text)

    def test_missing_and_corrupt_detail_fail_closed_without_regeneration(self):
        snap = self.create()
        planet = "detail-planet-reach"
        geo = snap["state"]["geography"][planet]
        # An independently persisted malformed snapshot cannot hide a missing dependency.
        missing = copy.deepcopy(snap["state"])
        missing["_private"]["campaign_id"] = "missing"
        missing["geography"][planet]["detail_ref"]["sha256"] = "0"*64
        sid = str(uuid.uuid4())
        with self.db.connect() as c:
            c.execute("INSERT INTO campaigns(id,kind) VALUES('missing','demo')")
            c.execute("""INSERT INTO snapshots(id,campaign_id,turn,schema_version,rules_version,state_json,state_hash,created_at)
                VALUES(%s,'missing',0,%s,%s,%s,%s,%s)""", (sid, snap["schema_version"], snap["rules_version"], canonical_json(missing),
                    self.db.snapshot_hash("missing",0,missing,snap["schema_version"],snap["rules_version"]),now()))
            c.execute("UPDATE campaigns SET current_snapshot_id=%s WHERE id='missing'", (sid,))
        with self.assertRaisesRegex(ValueError,"missing or mismatched"):
            self.db.current("missing")
        with self.assertRaises(ValueError):
            self.db.restore("missing", sid, "missing-branch")
        # Privileged damage is detected from actual bytes on map load and restore.
        with self.db.connect() as c:
            c.execute("ALTER TABLE planet_detail_assets DISABLE TRIGGER planet_detail_no_mutation")
            c.execute("UPDATE planet_detail_assets SET payload_json=replace(payload_json,'planet-detail-v2','planet-detail-v0') WHERE sha256=%s", (geo["detail_ref"]["sha256"],))
            c.execute("ALTER TABLE planet_detail_assets ENABLE TRIGGER planet_detail_no_mutation")
        with self.assertRaisesRegex(ValueError,"checksum"):
            self.db.planet_detail("detail",planet)
        with self.assertRaisesRegex(ValueError,"checksum"):
            self.db.restore("detail",snap["id"],"corrupt-branch")
        self.assertNotIn("corrupt-branch", {c["id"] for c in self.db.campaigns()})

    def test_backup_recovers_assets_and_their_immutable_history_references(self):
        snap = self.create()
        original = self.db.planet_detail("detail", "detail-planet-reach")
        database = "detail_recovery_" + uuid.uuid4().hex
        target = make_conninfo(self.dsn, dbname=database)
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "detail.dump"
            self.db.backup(destination)
            with psycopg.connect(self.dsn, autocommit=True) as admin:
                admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
            try:
                env = dict(os.environ)
                for key, name in {"host":"PGHOST", "hostaddr":"PGHOSTADDR", "port":"PGPORT", "user":"PGUSER", "password":"PGPASSWORD"}.items():
                    if key in conninfo_to_dict(target): env[name] = conninfo_to_dict(target)[key]
                result = subprocess.run(["pg_restore","--dbname",database,"--exit-on-error","--no-owner","--no-privileges",str(destination)],
                                        env=env,capture_output=True)
                self.assertEqual(0,result.returncode,"detail pg_restore failed")
                recovered = Store(target,schema=self.schema,initialize=False)
                self.assertEqual(snap["state_hash"],recovered.current("detail")["snapshot"]["state_hash"])
                self.assertEqual(original,recovered.planet_detail("detail","detail-planet-reach"))
                recovered.restore("detail",snap["id"],"recovered-branch")
                self.assertEqual(original["detail"],recovered.planet_detail("recovered-branch","detail-planet-reach")["detail"])
            finally:
                with psycopg.connect(self.dsn,autocommit=True) as admin:
                    admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(database)))


if __name__ == "__main__":
    unittest.main()
