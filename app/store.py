"""PostgreSQL persistence: immutable snapshots and transactional campaign turns."""
import json
import os
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from psycopg import sql

from .engine import (RULES_VERSION, SCHEMA_VERSION, advance, canonical_json, digest,
                     initial_state, public_state, validate_submission)
from . import engine_v2
from .universe import V2_RULES, V2_SCHEMA, RESOURCES, owned_humans, public_state_v2
from .universe import build_universe
from .planet_generation import GEOLOGIES, PLANET_CLASSES, PRESETS, resolve_planet_presets, validate_surface


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, dsn=None, schema=None, initialize=True):
        self.dsn = dsn or os.environ.get("WOLD_DATABASE_URL")
        if not self.dsn:
            raise RuntimeError("WOLD_DATABASE_URL is required; PostgreSQL is the authoritative database")
        self.schema = schema or os.environ.get("WOLD_DB_SCHEMA") or os.environ.get("WOLD_DATABASE_SCHEMA")
        if self.schema and not self.schema.replace("_", "").isalnum():
            raise ValueError("invalid database schema name")
        if initialize:
            self.initialize()

    def connect(self):
        conn = psycopg.connect(self.dsn, row_factory=dict_row)
        if self.schema:
            conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
        return conn

    def initialize(self):
        with self.connect() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS campaigns(
              id TEXT PRIMARY KEY,
              kind TEXT NOT NULL CHECK(kind IN ('demo','pregame')),
              parent_snapshot_id TEXT,
              current_snapshot_id TEXT
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS snapshots(
              sequence BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
              id TEXT PRIMARY KEY,
              campaign_id TEXT NOT NULL REFERENCES campaigns(id),
              turn INTEGER NOT NULL,
              schema_version TEXT NOT NULL,
              rules_version TEXT NOT NULL,
              state_json TEXT NOT NULL,
              state_hash TEXT NOT NULL,
              command_json TEXT,
              submission_id TEXT,
              created_at TEXT NOT NULL,
              UNIQUE(campaign_id,id)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS outbox(
              snapshot_id TEXT PRIMARY KEY REFERENCES snapshots(id),
              status TEXT NOT NULL,
              attempts INTEGER NOT NULL DEFAULT 0,
              last_error TEXT,
              remote_file_id TEXT,
              archive_folder_id TEXT,
              projection_version TEXT,
              payload_bytes BYTEA,
              payload_checksum TEXT,
              lease_owner TEXT,
              lease_expires_at DOUBLE PRECISION
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS schema_migrations(
              version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL
            )""")
            c.execute("""DO $$ BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='campaign_parent_snapshot_fk' AND connamespace=current_schema()::regnamespace) THEN
                ALTER TABLE campaigns ADD CONSTRAINT campaign_parent_snapshot_fk
                  FOREIGN KEY(parent_snapshot_id) REFERENCES snapshots(id);
              END IF;
            END $$""")
            c.execute("CREATE UNIQUE INDEX IF NOT EXISTS snapshots_campaign_id_id ON snapshots(campaign_id,id)")
            c.execute("ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaign_current_snapshot_fk")
            c.execute("ALTER TABLE campaigns ADD CONSTRAINT campaign_current_snapshot_fk FOREIGN KEY(id,current_snapshot_id) REFERENCES snapshots(campaign_id,id)")
            c.execute("CREATE UNIQUE INDEX IF NOT EXISTS snapshots_submission ON snapshots(campaign_id,submission_id) WHERE submission_id IS NOT NULL")
            c.execute("CREATE INDEX IF NOT EXISTS snapshots_campaign_sequence ON snapshots(campaign_id,sequence)")
            c.execute("CREATE INDEX IF NOT EXISTS outbox_claim ON outbox(status,lease_expires_at)")
            c.execute("""CREATE OR REPLACE FUNCTION reject_snapshot_mutation() RETURNS trigger AS $$
              BEGIN RAISE EXCEPTION 'snapshots are immutable'; END;
            $$ LANGUAGE plpgsql""")
            c.execute("DROP TRIGGER IF EXISTS snapshots_no_update ON snapshots")
            c.execute("DROP TRIGGER IF EXISTS snapshots_no_delete ON snapshots")
            c.execute("CREATE TRIGGER snapshots_no_update BEFORE UPDATE ON snapshots FOR EACH ROW EXECUTE FUNCTION reject_snapshot_mutation()")
            c.execute("CREATE TRIGGER snapshots_no_delete BEFORE DELETE ON snapshots FOR EACH ROW EXECUTE FUNCTION reject_snapshot_mutation()")
            c.execute("INSERT INTO schema_migrations(version,name,applied_at) VALUES(1,'postgresql_archive_leases',%s) ON CONFLICT(version) DO NOTHING", (now(),))
            c.execute("INSERT INTO schema_migrations(version,name,applied_at) VALUES(2,'campaign_scoped_current_pointer',%s) ON CONFLICT(version) DO NOTHING", (now(),))

    @staticmethod
    def snapshot_hash(campaign_id, turn, state, schema_version=SCHEMA_VERSION, rules_version=RULES_VERSION):
        return digest({"schema_version": schema_version, "rules_version": rules_version,
                       "campaign_id": campaign_id, "turn": turn, "state": state})

    @staticmethod
    def validate_state(schema_version, rules_version, turn, state):
        if not isinstance(state,dict) or type(turn) is not int or type(state.get("turn")) is not int or state.get("turn")!=turn:
            raise ValueError("snapshot turn invariant failed")
        if (schema_version,rules_version)==(SCHEMA_VERSION,RULES_VERSION):
            validate_surface(state)
            if any(type(state.get(key)) is not int or state[key]<0 for key in ("population","food","ore","energy")):
                raise ValueError("snapshot resource invariant failed")
        elif (schema_version,rules_version)==(V2_SCHEMA,V2_RULES):
            if not isinstance(state.get("_private"),dict) or not isinstance(state.get("settlements"),list) or not isinstance(state.get("nodes"),list):
                raise ValueError("snapshot v2 state invariant failed")
            groups=("nodes","settlements","facilities","projects","units","fleets","shipments","factions","expeditions","characters")
            for group in groups:
                rows=state.get(group,[])
                if not isinstance(rows,list) or any(not isinstance(row,dict) or not isinstance(row.get("id"),str) for row in rows) or len({row["id"] for row in rows})!=len(rows):
                    raise ValueError("snapshot v2 entity identity invariant failed")
            all_ids=[row["id"] for group in groups for row in state.get(group,[])]
            if len(set(all_ids))!=len(all_ids): raise ValueError("snapshot v2 global entity identity invariant failed")
            nodes={n["id"]:n for n in state["nodes"]}
            node_kinds={"galaxy","region","sector","system","planet","star","belt","moon"}
            parent_kind={"galaxy":None,"region":"galaxy","sector":"region","system":"sector","planet":"system","star":"system","belt":"system","moon":"planet"}
            if any(n.get("kind") not in node_kinds or n.get("knowledge") not in ("hidden","detected","surveyed") or (n.get("parent_id") is not None and n["parent_id"] not in nodes) or
                   (n.get("kind") in parent_kind and ((parent_kind[n["kind"]] is None and n.get("parent_id") is not None) or (parent_kind[n["kind"]] is not None and (n.get("parent_id") is None or nodes[n["parent_id"]].get("kind")!=parent_kind[n["kind"]])))) or
                   (n.get("knowledge")!="hidden" and n.get("parent_id") is not None and nodes[n["parent_id"]].get("knowledge")=="hidden") for n in state["nodes"]):
                raise ValueError("snapshot v2 hierarchy invariant failed")
            planet_ids={nid for nid,node in nodes.items() if node.get("kind")=="planet"}
            geography=state.get("geography")
            if not isinstance(geography,dict) or set(geography)!=planet_ids:
                raise ValueError("snapshot v2 persisted geography invariant failed")
            province_planet={}
            for planet_id,geo in geography.items():
                planet=geo.get("planet",{})
                width,height=planet.get("width"),planet.get("height")
                if not isinstance(planet.get("id"),str) or not planet["id"] or type(width)is not int or type(height)is not int or width<1 or height<1 or not isinstance(geo.get("terrain_grid"),str) or len(geo["terrain_grid"])!=width*height or any(code not in "ocprfm" for code in geo["terrain_grid"]):
                    raise ValueError("snapshot v2 geography shape invariant failed")
                validate_surface(geo)
                surface=geo.get("surface",{})
                if surface.get("version") in ("planet-v4","planet-v5","planet-v6","planet-v7"):
                    node=nodes.get(planet_id,{})
                    if surface.get("preset") not in PRESETS or node.get("class")!=PLANET_CLASSES.get(surface.get("preset")):
                        raise ValueError("planet-v4 preset and body class invariant failed")
                for province in geo.get("provinces",[]):
                    if any(type(province.get(k)) is not int for k in ("x","y","width","height")) or province["x"]<0 or province["y"]<0 or province["width"]<1 or province["height"]<1 or province["x"]+province["width"]>width or province["y"]+province["height"]>height or province.get("id") in province_planet:
                        raise ValueError("snapshot v2 province geometry invariant failed")
                    province_planet[province["id"]]=planet_id
            for geo in geography.values():
                if len(geo.get("provinces",[]))==0: raise ValueError("snapshot v2 province geometry invariant failed")
            config=state.get("_private",{}).get("generator_config",{})
            if config.get("planet")!="planet-v7" and "planet_geologies" in config:
                raise ValueError("V7 geology requires its matching generator configuration")
            preset_planets={pid:geo["surface"]["preset"] for pid,geo in geography.items()
                        if geo.get("surface",{}).get("version") in ("planet-v4","planet-v5","planet-v6","planet-v7")}
            if config.get("planet") in ("planet-v4","planet-v5","planet-v6","planet-v7"):
                recorded=config.get("planet_presets")
                if not isinstance(recorded,dict) or set(recorded)!=planet_ids or recorded!=preset_planets:
                    raise ValueError("private planet preset configuration invariant failed")
                expected_version=config["planet"]
                if any(geo.get("surface",{}).get("version")!=expected_version for geo in geography.values()):
                    raise ValueError("planet preset version and generator configuration differ")
                expected_grid="grid128x80" if expected_version in ("planet-v5","planet-v6","planet-v7") else "grid64x40"
                if config.get("grid")!=expected_grid:
                    raise ValueError("planet generator grid configuration invariant failed")
                if expected_version=="planet-v7":
                    geologies=config.get("planet_geologies")
                    recorded_geologies={pid:geo["surface"].get("geology") for pid,geo in geography.items()}
                    if not isinstance(geologies,dict) or set(geologies)!=planet_ids or geologies!=recorded_geologies or any(g not in GEOLOGIES for g in geologies.values()):
                        raise ValueError("private planet geology configuration invariant failed")
                elif "planet_geologies" in config or any(geo.get("surface",{}).get("version")=="planet-v7" for geo in geography.values()):
                    raise ValueError("V7 geology requires its matching generator configuration")
            elif preset_planets or "planet_presets" in config:
                raise ValueError("preset geography requires its matching generator configuration")
            settlements={s["id"]:s for s in state["settlements"]}
            for settlement in state["settlements"]:
                if any(type(settlement.get(k)) is not int or settlement[k]<0 for k in ("civilians",)) or any(k in settlement for k in ("soldiers","crew","settlers")):
                    raise ValueError("snapshot v2 population invariant failed")
                if type(settlement.get("housing")) is not int or settlement["housing"]<0 or type(settlement.get("unrest")) is not int or not 0<=settlement["unrest"]<=100 or type(settlement.get("owned")) is not bool:
                    raise ValueError("snapshot v2 settlement scalar invariant failed")
                policy=settlement.get("policy")
                if not isinstance(policy,dict) or type(policy.get("tax_rate")) is not int or not 0<=policy["tax_rate"]<=2 or any(type(policy.get(k)) is not bool for k in ("welfare","growth_enabled")):
                    raise ValueError("snapshot v2 settlement policy invariant failed")
                if not isinstance(settlement.get("stocks"),dict) or set(settlement["stocks"])!=set(RESOURCES) or any(type(v)is not int or v<0 for v in settlement["stocks"].values()):
                    raise ValueError("snapshot v2 resource invariant failed")
                allocations=settlement.get("allocations")
                if not isinstance(allocations,dict) or set(allocations)!=set(engine_v2.ALLOCATIONS) or any(type(v)is not int or v<0 for v in allocations.values()) or sum(allocations.values())>settlement["civilians"]:
                    raise ValueError("snapshot v2 worker allocation invariant failed")
                if settlement.get("planet_id") not in planet_ids or province_planet.get(settlement.get("province_id"))!=settlement.get("planet_id"):
                    raise ValueError("snapshot v2 settlement location invariant failed")
            if any(type(u.get("strength")) is not int or u["strength"]<0 for u in state.get("units",[])):
                raise ValueError("snapshot v2 unit population invariant failed")
            province_ids=set(province_planet)
            if any(u.get("owner") not in ("player","enemy") or (u.get("location_id") not in province_ids and not (u.get("location_id") is None and u.get("moving_until"))) or u.get("settlement_id") not in settlements or u.get("planet_id") not in planet_ids or (u.get("location_id") is not None and province_planet.get(u.get("location_id"))!=u.get("planet_id")) or (u.get("settlement_id") in settlements and settlements[u["settlement_id"]].get("planet_id")!=u.get("planet_id")) or (u.get("supply_source_id") is not None and (u.get("supply_source_id") not in settlements or settlements[u["supply_source_id"]].get("planet_id")!=u.get("planet_id"))) or any(type(u.get(k,0)) is not int or u.get(k,0)<0 for k in ("food_reserve","transit_food")) for u in state.get("units",[])):
                raise ValueError("snapshot v2 unit reference invariant failed")
            for unit in state.get("units",[]):
                if type(unit.get("readiness")) is not int or not 0<=unit["readiness"]<=100:
                    raise ValueError("snapshot v2 unit readiness invariant failed")
                if unit["strength"]==0 and unit.get("moving_until"): raise ValueError("snapshot v2 defeated unit activity invariant failed")
                if unit.get("moving_until") is not None and (type(unit["moving_until"]) is not int or unit["moving_until"]!=turn+1 or unit.get("destination_province_id") not in province_ids or province_planet.get(unit.get("destination_province_id"))!=unit.get("planet_id") or unit.get("supply_source_id") not in settlements or unit.get("transit_food",0)<unit["strength"]):
                    raise ValueError("snapshot v2 unit movement invariant failed")
            for fleet in state.get("fleets",[]):
                if type(fleet.get("crew")) is not int or fleet["crew"]<0 or type(fleet.get("strength")) is not int or fleet.get("strength")!=fleet["crew"]:
                    raise ValueError("snapshot v2 fleet population invariant failed")
                if type(fleet.get("capacity")) is not int or fleet["capacity"]<0:
                    raise ValueError("snapshot v2 fleet capacity invariant failed")
                if any(type(fleet.get(k,0)) is not int or fleet.get(k,0)<0 for k in ("food_reserve","promethium_reserve")):
                    raise ValueError("snapshot v2 fleet stores invariant failed")
                if fleet.get("owner") not in ("player","enemy") or fleet.get("system_id") not in nodes or nodes[fleet["system_id"]].get("kind")!="system" or (fleet.get("settlement_id") is not None and (fleet["settlement_id"] not in settlements or settlements[fleet["settlement_id"]].get("planet_id")!=fleet.get("location_id"))):
                    raise ValueError("snapshot v2 fleet reference invariant failed")
                location=fleet.get("location_id")
                if location not in nodes or nodes[location].get("kind") not in ("planet","system") or (nodes[location].get("kind")=="planet" and nodes[location].get("parent_id")!=fleet["system_id"]) or (nodes[location].get("kind")=="system" and location!=fleet["system_id"]):
                    raise ValueError("snapshot v2 fleet location invariant failed")
                if fleet.get("moving_until") is not None and (type(fleet["moving_until"]) is not int or fleet["moving_until"]<=turn or fleet.get("destination_system_id") not in nodes or nodes[fleet["destination_system_id"]].get("kind")!="system"):
                    raise ValueError("snapshot v2 fleet movement invariant failed")
                if fleet["crew"]==0 and fleet.get("moving_until"): raise ValueError("snapshot v2 defeated fleet activity invariant failed")
            for shipment in state.get("shipments",[]):
                if type(shipment.get("quantity")) is not int or shipment["quantity"]<=0 or shipment.get("resource") not in RESOURCES or shipment.get("source_id") not in settlements or shipment.get("destination_id") not in settlements:
                    raise ValueError("snapshot v2 shipment invariant failed")
            for mission in state.get("expeditions",[]):
                if mission.get("kind") not in ("explore","investigate","colonize") or mission.get("source_id") not in settlements or type(mission.get("owned")) is not bool:
                    raise ValueError("snapshot v2 expedition reference invariant failed")
                for key in ("settlers","food_cargo"):
                    if key in mission and (type(mission[key]) is not int or mission[key]<0): raise ValueError("snapshot v2 mission resource invariant failed")
                if mission.get("kind")=="colonize" and (mission.get("fleet_id") not in {f["id"] for f in state.get("fleets",[])} or mission.get("source_id") not in settlements):
                    raise ValueError("snapshot v2 colony reference invariant failed")
                if mission.get("kind")=="colonize":
                    fleet=next(f for f in state["fleets"] if f["id"]==mission["fleet_id"])
                    if fleet.get("crew",0)<=0 or fleet.get("capacity",0)<mission.get("settlers",0) or fleet.get("moving_until")!=mission.get("arrive_turn") or type(mission.get("arrive_turn")) is not int or mission["arrive_turn"]<=turn or mission.get("target_planet_id") not in planet_ids:
                        raise ValueError("snapshot v2 colony mission invariant failed")
                if mission.get("kind")=="explore" and (mission.get("node_id") not in nodes or type(mission.get("arrive_turn")) is not int or mission["arrive_turn"]<=turn):
                    raise ValueError("snapshot v2 exploration mission invariant failed")
                if mission.get("kind")=="investigate" and (mission.get("entity_id") not in settlements or settlements[mission["entity_id"]].get("owned") or type(mission.get("finish_turn")) is not int or mission["finish_turn"]<=turn):
                    raise ValueError("snapshot v2 investigation mission invariant failed")
            for facility in state.get("facilities",[]):
                if facility.get("settlement_id") not in settlements or facility.get("kind") not in engine_v2.FACILITIES or type(facility.get("active_turn")) is not int or facility["active_turn"]<0 or type(facility.get("completed")) is not bool:
                    raise ValueError("snapshot v2 facility invariant failed")
            for project in state.get("projects",[]):
                if any(type(project.get(k)) is not int or project[k]<0 for k in ("work_required","work_done","created_turn")) or project["work_done"]>project["work_required"] or project.get("settlement_id") not in settlements:
                    raise ValueError("snapshot v2 project invariant failed")
                if project.get("kind") not in ("facility","transport","research") or (project.get("kind")=="facility" and project.get("facility_kind") not in engine_v2.FACILITIES) or (project.get("kind")=="research" and project.get("technology_id") not in ("logistics-I","industry-I")):
                    raise ValueError("snapshot v2 project type invariant failed")
            for shipment in state.get("shipments",[]):
                if any(type(shipment.get(k)) is not int or shipment[k]<0 for k in ("arrive_turn","created_turn")) or shipment["arrive_turn"]<=turn:
                    raise ValueError("snapshot v2 shipment timing invariant failed")
            for character in state.get("characters",[]):
                if character.get("role") not in ("engineer","steward","general","scout") or type(character.get("owned")) is not bool or type(character.get("experience")) is not int or character["experience"]<0:
                    raise ValueError("snapshot v2 character invariant failed")
                if character.get("assignment") is not None and character["assignment"] not in {s["id"] for s in state["settlements"] if s["owned"]}|{u["id"] for u in state["units"] if u.get("owner")=="player"}|{f["id"] for f in state["fleets"] if f.get("owner")=="player"}:
                    raise ValueError("snapshot v2 assignment invariant failed")
            if type(owned_humans(state)) is not int or owned_humans(state)<0:
                raise ValueError("snapshot v2 total population invariant failed")
        else:
            raise ValueError("snapshot schema or rules version is unsupported")

    def create_demo(self, campaign_id="demo", seed=741903):
        with self.connect() as c:
            c.execute("BEGIN")
            if c.execute("SELECT 1 FROM campaigns WHERE id=%s", (campaign_id,)).fetchone():
                raise ValueError("campaign already exists")
            state = initial_state(campaign_id, seed)
            sid = str(uuid.uuid4())
            h = self.snapshot_hash(campaign_id, 0, state)
            c.execute("INSERT INTO campaigns(id,kind) VALUES(%s,'demo')", (campaign_id,))
            c.execute("""INSERT INTO snapshots(id,campaign_id,turn,schema_version,rules_version,state_json,
                state_hash,command_json,submission_id,created_at) VALUES(%s,%s,0,%s,%s,%s,%s,NULL,NULL,%s)""",
                (sid,campaign_id,SCHEMA_VERSION,RULES_VERSION,canonical_json(state),h,now()))
            c.execute("UPDATE campaigns SET current_snapshot_id=%s WHERE id=%s", (sid,campaign_id))
            c.execute("INSERT INTO outbox(snapshot_id,status) VALUES(%s,'pending')", (sid,))
            return sid

    def create_demo_v2(self, campaign_id="demo-v2", seed=741903, *, planet_generator="planet-v1", preset=None, planet_presets=None, geology="none", planet_geologies=None):
        if planet_generator not in ("planet-v4","planet-v5","planet-v6","planet-v7") and (preset is not None or planet_presets is not None or planet_geologies is not None):
            raise ValueError("planet presets require planet-v4, planet-v5, or planet-v6")
        if planet_generator in ("planet-v4","planet-v5","planet-v6","planet-v7"):
            ids={f"{campaign_id}-planet-{suffix}" for suffix in ("reach","ash","haven","veil")}
            resolve_planet_presets(seed, ids, "auto" if preset is None else preset, planet_presets)
        if planet_generator!="planet-v7" and (planet_geologies is not None or geology!="none"):
            raise ValueError("planet geology requires planet-v7")
        with self.connect() as c:
            c.execute("BEGIN")
            if c.execute("SELECT 1 FROM campaigns WHERE id=%s", (campaign_id,)).fetchone():
                raise ValueError("campaign already exists")
            state=build_universe(campaign_id,seed,planet_generator=planet_generator,preset=preset,planet_presets=planet_presets,geology=geology,planet_geologies=planet_geologies)
            self.validate_state(V2_SCHEMA,V2_RULES,0,state)
            sid=str(uuid.uuid4()); h=self.snapshot_hash(campaign_id,0,state,V2_SCHEMA,V2_RULES)
            c.execute("INSERT INTO campaigns(id,kind) VALUES(%s,'demo')",(campaign_id,))
            c.execute("""INSERT INTO snapshots(id,campaign_id,turn,schema_version,rules_version,state_json,state_hash,
                command_json,submission_id,created_at) VALUES(%s,%s,0,%s,%s,%s,%s,NULL,NULL,%s)""",
                (sid,campaign_id,V2_SCHEMA,V2_RULES,canonical_json(state),h,now()))
            c.execute("UPDATE campaigns SET current_snapshot_id=%s WHERE id=%s",(sid,campaign_id))
            c.execute("INSERT INTO outbox(snapshot_id,status) VALUES(%s,'pending')",(sid,))
            return sid

    def create_pregame(self, campaign_id="campaign"):
        with self.connect() as c:
            c.execute("INSERT INTO campaigns(id,kind) VALUES(%s,'pregame')", (campaign_id,))

    def campaigns(self):
        with self.connect() as c:
            return [dict(r) for r in c.execute("SELECT id,kind,parent_snapshot_id,current_snapshot_id FROM campaigns ORDER BY id").fetchall()]

    def _snapshot(self, c, sid):
        row = c.execute("SELECT * FROM snapshots WHERE id=%s", (sid,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["state"] = json.loads(result.pop("state_json"))
        versions=(result["schema_version"],result["rules_version"])
        self.validate_state(*versions,result["turn"],result["state"])
        if versions==(V2_SCHEMA,V2_RULES) and result["state"].get("_private",{}).get("campaign_id")!=result["campaign_id"]:
            raise ValueError("snapshot v2 private campaign identity invariant failed")
        if result["state_hash"] != self.snapshot_hash(result["campaign_id"], result["turn"], result["state"],*versions):
            raise ValueError("snapshot checksum verification failed")
        result["command"] = json.loads(result.pop("command_json")) if result["command_json"] else None
        return result

    def current(self, campaign_id):
        with self.connect() as c:
            campaign = c.execute("SELECT * FROM campaigns WHERE id=%s", (campaign_id,)).fetchone()
            if not campaign:
                return None
            if not campaign["current_snapshot_id"]:
                return {"campaign": dict(campaign), "snapshot": None}
            owner = c.execute("SELECT campaign_id FROM snapshots WHERE id=%s", (campaign["current_snapshot_id"],)).fetchone()
            if not owner or owner["campaign_id"] != campaign_id:
                raise ValueError("current snapshot campaign invariant failed")
            snap = self._snapshot(c, campaign["current_snapshot_id"])
            return {"campaign": dict(campaign), "snapshot": snap}

    @staticmethod
    def player_state(snapshot):
        if not snapshot: return None
        if (snapshot["schema_version"],snapshot["rules_version"])==(V2_SCHEMA,V2_RULES):
            return public_state_v2(snapshot["state"])
        return public_state(snapshot["state"])

    def map_view(self,campaign_id,level,node_id=None,snapshot_id=None,overlay="terrain"):
        if level not in ("galactic","sector","system","planet"): raise ValueError("invalid map level")
        if overlay not in ("terrain","provinces","population","infrastructure","military","politics"): raise ValueError("invalid map overlay")
        cur=self.current(campaign_id)
        if not cur: raise KeyError("campaign not found")
        snap=self._snapshot_for_campaign(campaign_id,snapshot_id) if snapshot_id else cur["snapshot"]
        if not snap: raise ValueError("pre-game campaign has no map")
        if (snap["schema_version"],snap["rules_version"])!=(V2_SCHEMA,V2_RULES): raise ValueError("hierarchy maps are available in demo-v2")
        projected=public_state_v2(snap["state"]); visible={n["id"]:n for n in projected["nodes"]}
        regions=[n for n in projected["nodes"] if n["kind"]=="region"]
        if level=="galactic":
            groups=[]; sectors=[]
            for region in regions:
                children=[n for n in projected["nodes"] if n["kind"]=="sector" and n["parent_id"]==region["id"]]
                groups.append({"region":region,"sectors":children}); sectors.extend(children)
            return {"campaign_id":campaign_id,"snapshot_id":snap["id"],"turn":snap["turn"],"level":level,
                "groups":groups,"nodes":sectors,"links":[],"overlay":overlay,"records":[]}
        if not node_id or node_id not in visible: raise KeyError("map node not found")
        parent=visible[node_id]
        expected={"sector":"sector","system":"system","planet":"planet"}[level]
        if parent["kind"]!=expected: raise KeyError("map node not found")
        if level=="sector":
            nodes=[n for n in projected["nodes"] if n["kind"]=="system" and n["parent_id"]==parent["id"]]
            return {"campaign_id":campaign_id,"snapshot_id":snap["id"],"turn":snap["turn"],"level":level,
                "parent":parent,"nodes":nodes,"links":[e for e in projected["links"] if e["a"] in {n["id"] for n in nodes} and e["b"] in {n["id"] for n in nodes}],"overlay":overlay,"records":[]}
        if level=="system":
            planets=[n for n in projected["nodes"] if n["kind"]=="planet" and n["parent_id"]==parent["id"]]
            bodies=[n for n in projected["nodes"] if n["kind"] in ("star","belt") and n["parent_id"]==parent["id"]]
            for planet in planets:
                planet["moons"]=[n for n in projected["nodes"] if n["kind"]=="moon" and n["parent_id"]==planet["id"]]
            return {"campaign_id":campaign_id,"snapshot_id":snap["id"],"turn":snap["turn"],"level":level,
                "parent":parent,"nodes":planets,"bodies":bodies,"links":[],"overlay":overlay,"records":[]}
        selected=parent
        geometry=projected["geography"].get(selected["id"])
        moons=[n for n in projected["nodes"] if n["kind"]=="moon" and n["parent_id"]==selected["id"]]
        records=[]
        if geometry:
            for province in geometry["provinces"]:
                owners=[s for s in projected["settlements"] if s.get("planet_id")==selected["id"] and s.get("province_id")==province["id"]]
                if overlay=="population":
                    province_units=[u for u in projected["units"] if u.get("owner")=="player" and u.get("location_id")==province["id"]]
                    docked_crew=sum(f.get("crew",0) for f in projected["fleets"] if f.get("owner")=="player" and
                        any(s.get("id")==f.get("settlement_id") and s.get("province_id")==province["id"] for s in projected["settlements"]))
                    if owners and all(x.get("owned") for x in owners):
                        population=sum(x.get("civilians",0) for x in owners)+sum(u.get("strength",0) for u in province_units)+docked_crew
                        confidence="verified"
                    elif province_units:
                        population=sum(u.get("strength",0) for u in province_units); confidence="verified"
                    else:
                        population=None; confidence="unknown"
                    record={"province_id":province["id"],"population":population,"confidence":confidence}
                elif overlay=="infrastructure":
                    record={"province_id":province["id"],"facilities":[{"id":f["id"],"kind":f["kind"],"completed":f["completed"]} for f in projected["facilities"] if any(s["id"]==f["settlement_id"] and s["province_id"]==province["id"] for s in owners)]}
                elif overlay=="politics":
                    record={"province_id":province["id"],"unrest":max((s["unrest"] for s in owners if s.get("owned")),default=None),"confidence":"verified" if owners and all(s.get("owned") for s in owners) else "unknown"}
                elif overlay=="military":
                    record={"province_id":province["id"],"units":[{k:u.get(k) for k in ("id","kind","strength","readiness","owner","confidence","observed_turn")} for u in projected["units"] if u.get("location_id")==province["id"]],"confidence":"verified"}
                else:
                    record={"province_id":province["id"],"ownership":"owned" if any(s.get("owned") for s in owners) else ("foreign" if owners else "unknown")}
                records.append(record)
        return {"campaign_id":campaign_id,"snapshot_id":snap["id"],"turn":snap["turn"],"level":"planet",
                "parent":selected,"selected_planet":selected,"moons":moons,"geometry":geometry,"overlay":overlay,"records":records,"links":[]}

    def _snapshot_for_campaign(self,campaign_id,snapshot_id):
        with self.connect() as c:
            row=c.execute("SELECT campaign_id FROM snapshots WHERE id=%s",(snapshot_id,)).fetchone()
            if not row or row["campaign_id"]!=campaign_id: raise KeyError("snapshot not found in campaign")
            return self._snapshot(c,snapshot_id)

    def systems(self,campaign_id,section,snapshot_id=None):
        allowed={"overview","economy","budget","logistics","construction","research","military","diplomacy","intelligence","exploration","colonies","characters","orders"}
        if section not in allowed: raise ValueError("unknown management section")
        cur=self.current(campaign_id)
        if not cur: raise KeyError("campaign not found")
        snap=self._snapshot_for_campaign(campaign_id,snapshot_id) if snapshot_id else cur["snapshot"]
        if not snap: return {"campaign_id":campaign_id,"section":section,"turn":None,"confidence":"unknown","records":[]}
        if (snap["schema_version"],snap["rules_version"])!=(V2_SCHEMA,V2_RULES):
            raise ValueError("management sections are available in demo-v2")
        p=public_state_v2(snap["state"])
        records={"overview":{"economy":p["settlements"],"outcome":p["latest_outcome"]},
            "economy":{"settlements":p["settlements"],"production":p["latest_production"],"outcome":p["latest_outcome"]},
            "budget":p["latest_budget"],"logistics":{"shipments":p["shipments"],"depots":[f for f in p["facilities"] if f["kind"]=="depot"]},
            "construction":{"facilities":p["facilities"],"projects":p["projects"]},
            "research":{"technologies":p["technologies"],"projects":[x for x in p["projects"] if x.get("technology_id")]},
            "military":{"units":p["units"],"fleets":p["fleets"]},"diplomacy":{"factions":p["factions"]},
            "intelligence":{"discoveries":p["discoveries"]},"exploration":{"missions":p["expeditions"],"discoveries":p["discoveries"]},
            "colonies":{"settlements":p["settlements"],"missions":[x for x in p["expeditions"] if x.get("kind")=="colonize"]},
            "characters":{"characters":p["characters"]},"orders":{"allowed_actions":sorted(engine_v2.ACTION_TYPES),"action_limit":engine_v2.ACTION_LIMIT}}
        return {"campaign_id":campaign_id,"snapshot_id":snap["id"],"turn":snap["turn"],"section":section,"records":records[section]}

    def snapshot(self, sid):
        with self.connect() as c:
            return self._snapshot(c, sid)

    def history(self, campaign_id, limit=50, offset=0):
        with self.connect() as c:
            total = c.execute("SELECT count(*) AS total FROM snapshots WHERE campaign_id=%s", (campaign_id,)).fetchone()["total"]
            rows = c.execute("""SELECT s.id,s.turn,s.schema_version,s.rules_version,s.state_json,s.created_at,o.status AS archive_status
                FROM snapshots s LEFT JOIN outbox o ON o.snapshot_id=s.id
                WHERE s.campaign_id=%s ORDER BY s.sequence LIMIT %s OFFSET %s""",
                (campaign_id,limit,offset)).fetchall()
            result = []
            for row in rows:
                snap = self._snapshot(c, row["id"])
                result.append(dict(row) | {"state":snap["state"]})
            return result,total

    def packet(self, campaign_id):
        cur = self.current(campaign_id)
        if not cur:
            raise KeyError("campaign not found")
        if cur["campaign"]["kind"] != "demo":
            raise ValueError("pre-game campaign has no numeric baseline")
        s = cur["snapshot"]
        if (s["schema_version"],s["rules_version"])==(V2_SCHEMA,V2_RULES):
            return {"campaign_id":campaign_id,"turn":s["turn"],"base_hash":s["state_hash"],
                "schema_version":V2_SCHEMA,"rules_version":V2_RULES,"context":public_state_v2(s["state"]),
                "allowed_orders":{"allocations":sorted(engine_v2.ALLOCATIONS),"actions":sorted(engine_v2.ACTION_TYPES),"action_limit":engine_v2.ACTION_LIMIT},
                "example":{"schema_version":V2_SCHEMA,"rules_version":V2_RULES,"base_turn":s["turn"],"base_hash":s["state_hash"],
                    "submission_id":"demo-v2-turn-1","orders":{"allocations":[],"actions":[]},"narrative":""}}
        if (s["schema_version"],s["rules_version"])!=(SCHEMA_VERSION,RULES_VERSION): raise ValueError("unsupported campaign version")
        return {"campaign_id":campaign_id,"turn":s["turn"],"base_hash":s["state_hash"],
                "schema_version":SCHEMA_VERSION,"rules_version":RULES_VERSION,
                "context":public_state(s["state"]),"allowed_orders":{"farmers":"integer >= 0","miners":"integer >= 0","technicians":"integer >= 0","sum":"at most population"},
                "example":{"schema_version":SCHEMA_VERSION,"rules_version":RULES_VERSION,"base_turn":s["turn"],"base_hash":s["state_hash"],"submission_id":"demo-turn-1","orders":{"farmers":0,"miners":0,"technicians":0},"narrative":""}}

    def _existing_submission(self, c, campaign_id, payload):
        row = c.execute("SELECT * FROM snapshots WHERE campaign_id=%s AND submission_id=%s",
                        (campaign_id,payload["submission_id"])).fetchone()
        if not row:
            return None
        snap = self._snapshot(c, row["id"])
        if snap["command"] != payload:
            raise ValueError("submission_id already used with different content")
        return snap

    @staticmethod
    def _validate_any_submission(payload):
        versions=(payload.get("schema_version"),payload.get("rules_version")) if isinstance(payload,dict) else None
        if versions==(V2_SCHEMA,V2_RULES): engine_v2.validate_submission(payload)
        elif versions==(SCHEMA_VERSION,RULES_VERSION): validate_submission(payload)
        else: raise ValueError("unsupported schema_version or rules_version")

    def preview(self, campaign_id, payload):
        self._validate_any_submission(payload)
        with self.connect() as c:
            camp = c.execute("SELECT * FROM campaigns WHERE id=%s", (campaign_id,)).fetchone()
            if not camp:
                raise KeyError("campaign not found")
            old = self._existing_submission(c, campaign_id, payload)
            if old:
                prior=old["state"].get("latest_outcome") or (old["state"].get("outcomes") or [None])[-1]
                return {"duplicate":True,"snapshot_id":old["id"],"turn":old["turn"],"state_hash":old["state_hash"],"outcome":prior}
            if camp["kind"] != "demo" or not camp["current_snapshot_id"]:
                raise ValueError("campaign has no numeric baseline")
            base = self._snapshot(c, camp["current_snapshot_id"])
            if (base["schema_version"],base["rules_version"])==(V2_SCHEMA,V2_RULES):
                if (payload["schema_version"],payload["rules_version"])!=(V2_SCHEMA,V2_RULES): raise ValueError("proposal version does not match campaign snapshot")
                if payload["base_turn"] != base["turn"] or payload["base_hash"] != base["state_hash"]: raise RuntimeError("stale base")
                new,outcome=engine_v2.advance(base["state"],payload)
                self.validate_state(V2_SCHEMA,V2_RULES,new["turn"],new)
                if new.get("_private",{}).get("campaign_id")!=campaign_id: raise ValueError("snapshot v2 private campaign identity invariant failed")
                return {"duplicate":False,"state":public_state_v2(new),"outcome":outcome,
                    "state_hash":self.snapshot_hash(campaign_id,new["turn"],new,V2_SCHEMA,V2_RULES)}
            if (payload["schema_version"],payload["rules_version"])!=(SCHEMA_VERSION,RULES_VERSION): raise ValueError("proposal version does not match campaign snapshot")
            validate_submission(payload)
            if payload["base_turn"] != base["turn"] or payload["base_hash"] != base["state_hash"]:
                raise RuntimeError("stale base")
            new,outcome = advance(base["state"], payload)
            return {"duplicate":False,"state":public_state(new),"outcome":outcome,
                    "state_hash":self.snapshot_hash(campaign_id,new["turn"],new)}

    def commit(self, campaign_id, payload):
        self._validate_any_submission(payload)
        with self.connect() as c:
            c.execute("BEGIN")
            camp = c.execute("SELECT * FROM campaigns WHERE id=%s FOR UPDATE", (campaign_id,)).fetchone()
            if not camp:
                raise KeyError("campaign not found")
            old = self._existing_submission(c, campaign_id, payload)
            if old:
                prior=old["state"].get("latest_outcome") or (old["state"].get("outcomes") or [None])[-1]
                return {"duplicate":True,"snapshot_id":old["id"],"turn":old["turn"],"state_hash":old["state_hash"],"outcome":prior}
            if camp["kind"] != "demo" or not camp["current_snapshot_id"]:
                raise ValueError("campaign has no numeric baseline")
            base = self._snapshot(c, camp["current_snapshot_id"])
            is_v2=(base["schema_version"],base["rules_version"])==(V2_SCHEMA,V2_RULES)
            if (payload["schema_version"],payload["rules_version"])!=(base["schema_version"],base["rules_version"]):
                raise ValueError("proposal version does not match campaign snapshot")
            if payload["base_turn"] != base["turn"] or payload["base_hash"] != base["state_hash"]:
                raise RuntimeError("stale base")
            new,outcome = (engine_v2.advance if is_v2 else advance)(base["state"], payload)
            sid = str(uuid.uuid4())
            schema,rules=(V2_SCHEMA,V2_RULES) if is_v2 else (SCHEMA_VERSION,RULES_VERSION)
            self.validate_state(schema,rules,new["turn"],new)
            if is_v2 and new.get("_private",{}).get("campaign_id")!=campaign_id: raise ValueError("snapshot v2 private campaign identity invariant failed")
            h = self.snapshot_hash(campaign_id,new["turn"],new,schema,rules)
            c.execute("""INSERT INTO snapshots(id,campaign_id,turn,schema_version,rules_version,state_json,
                state_hash,command_json,submission_id,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (sid,campaign_id,new["turn"],schema,rules,canonical_json(new),h,canonical_json(payload),payload["submission_id"],now()))
            c.execute("UPDATE campaigns SET current_snapshot_id=%s WHERE id=%s", (sid,campaign_id))
            c.execute("INSERT INTO outbox(snapshot_id,status) VALUES(%s,'pending')", (sid,))
            return {"duplicate":False,"snapshot_id":sid,"turn":new["turn"],"state_hash":h,"outcome":outcome,"archive_status":"pending"}

    def restore(self, campaign_id, snapshot_id, new_campaign_id):
        with self.connect() as c:
            c.execute("BEGIN")
            if not c.execute("SELECT 1 FROM campaigns WHERE id=%s FOR SHARE", (campaign_id,)).fetchone():
                raise KeyError("campaign not found")
            row = c.execute("SELECT campaign_id FROM snapshots WHERE id=%s AND campaign_id=%s",
                            (snapshot_id,campaign_id)).fetchone()
            if not row:
                raise KeyError("snapshot not found in campaign")
            checked = self._snapshot(c, snapshot_id)
            original = checked["state"]
            new = dict(original)
            new["_private"] = dict(original["_private"])
            if "campaign_id" in new["_private"]: new["_private"]["campaign_id"]=new_campaign_id
            sid = str(uuid.uuid4())
            schema,rules=checked["schema_version"],checked["rules_version"]
            self.validate_state(schema,rules,new["turn"],new)
            if schema==V2_SCHEMA and new.get("_private",{}).get("campaign_id")!=new_campaign_id: raise ValueError("snapshot v2 private campaign identity invariant failed")
            h = self.snapshot_hash(new_campaign_id,new["turn"],new,schema,rules)
            c.execute("INSERT INTO campaigns(id,kind,parent_snapshot_id) VALUES(%s,'demo',%s)",
                      (new_campaign_id,snapshot_id))
            c.execute("""INSERT INTO snapshots(id,campaign_id,turn,schema_version,rules_version,state_json,
                state_hash,command_json,submission_id,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,NULL,NULL,%s)""",
                (sid,new_campaign_id,new["turn"],schema,rules,canonical_json(new),h,now()))
            c.execute("UPDATE campaigns SET current_snapshot_id=%s WHERE id=%s", (sid,new_campaign_id))
            c.execute("INSERT INTO outbox(snapshot_id,status) VALUES(%s,'pending')", (sid,))
            return sid

    def claim_archive(self, owner, lease_seconds, folder_ids, timestamp=None, kind=None):
        import hashlib
        timestamp = time.time() if timestamp is None else timestamp
        demo_folder, real_folder = folder_ids.get("demo"), folder_ids.get("pregame")
        if demo_folder and real_folder and demo_folder == real_folder:
            return {"disabled": True, "reason": "demo and real archive destinations must differ"}
        if kind not in (None,"demo","pregame"): raise ValueError("invalid campaign kind filter")
        with self.connect() as c:
            c.execute("BEGIN")
            query="""SELECT o.*,s.campaign_id,c.kind,s.turn
              FROM outbox o JOIN snapshots s ON s.id=o.snapshot_id
              JOIN campaigns c ON c.id=s.campaign_id
              WHERE o.status!='verified' AND
                (o.lease_owner IS NULL OR o.lease_expires_at IS NULL OR o.lease_expires_at<=%s)
              """
            params=[timestamp]
            if kind: query+="AND c.kind=%s " ; params.append(kind)
            query+="ORDER BY s.sequence LIMIT 1 FOR UPDATE OF o SKIP LOCKED"
            row = c.execute(query, tuple(params)).fetchone()
            if not row:
                return None
            folder_id = row["archive_folder_id"]
            payload_bytes = row["payload_bytes"]
            projection_version = row["projection_version"]
            payload_checksum = row["payload_checksum"]
            if payload_bytes is None:
                folder_id = folder_ids.get(row["kind"])
                if not folder_id:
                    return {"disabled": True, "snapshot_id": row["snapshot_id"]}
            elif not folder_id:
                return {"disabled": True, "snapshot_id": row["snapshot_id"]}
            # Serialize folder binding and reject reuse by the opposite campaign kind,
            # including historical/verified records and retries frozen under old config.
            c.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",(folder_id,))
            opposite = c.execute("""SELECT 1 FROM outbox o JOIN snapshots s ON s.id=o.snapshot_id
                JOIN campaigns c ON c.id=s.campaign_id WHERE c.kind<>%s AND o.archive_folder_id=%s LIMIT 1""",
                (row["kind"],folder_id)).fetchone()
            configured_opposite=folder_ids.get("pregame" if row["kind"]=="demo" else "demo")
            if opposite or (configured_opposite and folder_id==configured_opposite):
                return {"disabled": True, "snapshot_id": row["snapshot_id"],
                        "reason": "archive folder is reserved for the other campaign kind"}
            if payload_bytes is None:
                snapshot = self._snapshot(c, row["snapshot_id"])
                if (snapshot["schema_version"],snapshot["rules_version"])==(V2_SCHEMA,V2_RULES):
                    archive_version="archive-player-v2"
                    projection=public_state_v2(snapshot["state"])
                elif (snapshot["schema_version"],snapshot["rules_version"])==(SCHEMA_VERSION,RULES_VERSION):
                    archive_version="archive-player-v1"
                    projection=public_state(snapshot["state"])
                else:
                    raise ValueError("snapshot version has no archive projection")
                envelope = {
                    "archive_schema_version": archive_version,
                    "campaign_id": row["campaign_id"], "snapshot_id": row["snapshot_id"],
                    "turn": row["turn"], "schema_version": snapshot["schema_version"],
                    "rules_version": snapshot["rules_version"], "created_at": snapshot["created_at"],
                    "state": projection,
                }
                payload_bytes = canonical_json(envelope).encode("utf-8")
                payload_checksum = hashlib.sha256(payload_bytes).hexdigest()
                projection_version = archive_version
            elif hashlib.sha256(bytes(payload_bytes)).hexdigest() != payload_checksum:
                raise ValueError("frozen archive payload checksum verification failed")
            expires = timestamp + lease_seconds
            c.execute("""UPDATE outbox SET status='uploading',attempts=attempts+1,
                archive_folder_id=%s,projection_version=%s,payload_bytes=%s,payload_checksum=%s,
                lease_owner=%s,lease_expires_at=%s WHERE snapshot_id=%s""",
                (folder_id,projection_version,payload_bytes,payload_checksum,owner,expires,row["snapshot_id"]))
            return {"snapshot_id":row["snapshot_id"],"campaign_id":row["campaign_id"],
                    "turn":row["turn"],"folder_id":folder_id,"projection_version":projection_version,
                    "payload_bytes":bytes(payload_bytes),"payload_checksum":payload_checksum,
                    "remote_file_id":row["remote_file_id"],"lease_owner":owner,"lease_expires_at":expires}

    def persist_archive_file_id(self, snapshot_id, owner, file_id, timestamp=None):
        timestamp = time.time() if timestamp is None else timestamp
        with self.connect() as c:
            c.execute("BEGIN")
            row = c.execute("SELECT remote_file_id FROM outbox WHERE snapshot_id=%s AND lease_owner=%s AND status='uploading' AND lease_expires_at>%s FOR UPDATE",
                            (snapshot_id,owner,timestamp)).fetchone()
            if not row or (row["remote_file_id"] and row["remote_file_id"] != file_id):
                return False
            c.execute("UPDATE outbox SET remote_file_id=%s WHERE snapshot_id=%s AND lease_owner=%s",
                      (file_id,snapshot_id,owner))
            return True

    def mark_archive_verified(self, snapshot_id, owner, file_id, timestamp=None):
        timestamp = time.time() if timestamp is None else timestamp
        with self.connect() as c:
            c.execute("BEGIN")
            cursor = c.execute("""UPDATE outbox SET status='verified',last_error=NULL,
                lease_owner=NULL,lease_expires_at=NULL WHERE snapshot_id=%s AND lease_owner=%s
                AND remote_file_id=%s AND status='uploading' AND lease_expires_at>%s""",
                (snapshot_id,owner,file_id,timestamp))
            return cursor.rowcount == 1

    def release_archive(self, snapshot_id, owner, safe_error):
        with self.connect() as c:
            c.execute("BEGIN")
            cursor = c.execute("""UPDATE outbox SET status='pending',last_error=%s,
                lease_owner=NULL,lease_expires_at=NULL WHERE snapshot_id=%s AND lease_owner=%s""",
                (safe_error,snapshot_id,owner))
            return cursor.rowcount == 1

    def archive_outbox(self, snapshot_id):
        with self.connect() as c:
            row = c.execute("SELECT * FROM outbox WHERE snapshot_id=%s", (snapshot_id,)).fetchone()
            return dict(row) if row else None

    def backup(self, destination):
        """Write a consistent custom-format PostgreSQL dump for this Store schema."""
        env = dict(os.environ)
        connection = conninfo_to_dict(self.dsn)
        pg_names = {"host": "PGHOST", "hostaddr": "PGHOSTADDR", "port": "PGPORT",
                    "dbname": "PGDATABASE", "user": "PGUSER", "password": "PGPASSWORD",
                    "sslmode": "PGSSLMODE", "sslrootcert": "PGSSLROOTCERT"}
        for key, env_name in pg_names.items():
            if key in connection:
                env[env_name] = connection[key]
        command = ["pg_dump", "--format=custom", "--no-owner", "--no-privileges",
                   "--file", str(destination)]
        if self.schema:
            command.extend(["--schema", self.schema])
        subprocess.run(command, env=env, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE)
        return str(destination)
