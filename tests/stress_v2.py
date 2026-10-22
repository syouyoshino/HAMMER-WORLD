"""Connected, nonzero 10,000-turn PostgreSQL acceptance run.

Run separately from routine unit tests: python tests/stress_v2.py [turns].
Every record lives in a disposable schema; no campaign database is selected.
"""
import json
import hashlib
import math
import os
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg import sql
from app.engine_v2 import ALLOCATIONS, V2_RULES, V2_SCHEMA
from app.store import Store
from app.universe import owned_humans, owned_resources


def actions_for(turn, state):
    find = lambda rows, predicate: next(row for row in rows if predicate(row))
    forge = "long-run-forge"
    faction = "long-run-faction-ash"
    actions = []
    if turn == 1:
        actions = [
            {"type": "assign", "character_id": "long-run-character-engineer", "target_id": forge},
            {"type": "build", "settlement_id": forge, "facility_kind": "habitation"},
            {"type": "research", "settlement_id": forge, "technology_id": "logistics-I"},
            {"type": "treaty", "faction_id": faction, "operation": "propose"},
            {"type": "recruit", "settlement_id": forge},
        ]
    elif turn == 2:
        actions = [
            {"type": "treaty", "faction_id": faction, "operation": "accept"},
            {"type": "dispatch", "source_id": forge, "destination_id": "long-run-outpost", "resource": "ore", "quantity": 10},
            {"type": "investigate", "source_id": forge, "entity_id": "long-run-adversary-home"},
            {"type": "explore", "source_id": forge, "node_id": "long-run-planet-ash"},
            {"type": "build_transport", "settlement_id": forge},
        ]
    elif turn == 3:
        unit = find(state["units"], lambda u: u["owner"] == "player")
        enemy = find(state["units"], lambda u: u["owner"] == "enemy")
        actions = [{"type": "deploy_unit", "unit_id": unit["id"], "destination_province_id": enemy["location_id"], "source_id": forge}]
    elif turn == 5:
        unit = find(state["units"], lambda u: u["owner"] == "player")
        actions = [
            {"type": "attack", "unit_id": unit["id"], "target_id": "long-run-enemy-ground"},
            {"type": "colonize", "fleet_id": "long-run-transport-01", "source_id": forge, "target_planet_id": "long-run-planet-ash"},
        ]
    elif turn == 6:
        actions = [{"type": "research", "settlement_id": forge, "technology_id": "industry-I"}]
    elif turn == 10:
        actions = [{"type": "set_policy", "settlement_id": forge, "tax_rate": 2, "welfare": True, "growth_enabled": False}]
    elif turn == 20:
        actions = [{"type": "set_policy", "settlement_id": forge, "tax_rate": 1, "welfare": False, "growth_enabled": False}]
    if turn >= 3 and turn % 2:
        actions.append({"type": "trade", "source_id": forge, "faction_id": faction, "resource": "ore", "quantity": 5, "direction": "sell"})
    elif turn >= 4:
        actions.append({"type": "trade", "source_id": forge, "faction_id": faction, "resource": "ore", "quantity": 5, "direction": "buy"})
    return actions


def allocations_for(state):
    rows = []
    for settlement in state["settlements"]:
        if not settlement["owned"]:
            continue
        # Cover a full local meal, including the crew and troops. Departing
        # groups already have reserves; this slight surplus is intentional.
        people = settlement["civilians"]
        people += sum(u["strength"] for u in state["units"] if u["owner"] == "player" and u.get("settlement_id") == settlement["id"])
        people += sum(f["crew"] for f in state["fleets"] if f["owner"] == "player" and f.get("settlement_id") == settlement["id"])
        row = {"settlement_id": settlement["id"], **{key: 0 for key in ALLOCATIONS}}
        row["farmers"] = math.ceil(people / 3)
        if settlement["id"].endswith("-forge"):
            row.update(miners=20, technicians=32, refiners=10, drillers=10, machinists=5, scientists=5, builders=10)
        elif settlement["id"].endswith("-outpost"):
            row.update(miners=10, technicians=10)
        rows.append(row)
    return rows


def run(turns=10000):
    dsn = os.environ["WOLD_TEST_DATABASE_URL"]
    schema = "stress_v2_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    started = time.monotonic()
    try:
        db = Store(dsn, schema=schema)
        planet_generator = os.environ.get("WOLD_TEST_PLANET_GENERATOR", "planet-v1")
        initial_id = db.create_demo_v2("long-run", seed=4242, planet_generator=planet_generator)
        current = db.current("long-run")["snapshot"]
        checkpoints = {0: (initial_id, current["state_hash"])}
        largest = len(json.dumps(current["state"]))
        for turn in range(1, turns + 1):
            state = current["state"]
            before_people = owned_humans(state)
            proposal = {"schema_version": V2_SCHEMA, "rules_version": V2_RULES,
                        "base_turn": current["turn"], "base_hash": current["state_hash"],
                        "submission_id": f"stress-{turn}", "narrative": "Fictional connected acceptance fixture.",
                        "orders": {"allocations": allocations_for(state), "actions": actions_for(turn, state)}}
            committed = db.commit("long-run", proposal)
            current = db.current("long-run")["snapshot"]
            state = current["state"]
            assert current["turn"] == turn
            losses = sum(item["count"] for item in committed["outcome"]["deaths"])
            assert owned_humans(state) == before_people - losses, (turn, "population conservation")
            assert owned_humans(state) > 1000, (turn, "fixture collapsed")
            resources = owned_resources(state)
            assert all(value >= 0 for value in resources.values())
            ledger = committed["outcome"]["resources"]
            assert ledger["closing"] == resources
            for resource, value in resources.items():
                expected_resource = ledger["opening"][resource] + sum(row.get(resource, 0) for row in ledger["inflows"].values()) - sum(row.get(resource, 0) for row in ledger["outflows"].values())
                assert value == expected_resource, (turn, resource, "resource conservation")
            if turn > 50:
                assert ledger["outflows"]["meals"]["food"] == owned_humans(state), (turn, "one meal per person")
            budget = state["latest_budget"]
            spending = sum(item["upkeep_credits"] + item["welfare"] for item in budget["spending"].values())
            # Trade spending is a breakdown within total action spending.
            assert budget["trade_spending"] <= budget["action_credit_spending"]
            expected = budget["opening_credits"] + budget["tax_revenue"] + budget["trade_revenue"] - budget["action_credit_spending"] - spending
            assert budget["closing_credits"] == expected, (turn, "budget reconciliation")
            largest = max(largest, len(json.dumps(state)))
            if turn % 1000 == 0 or turn == turns:
                checkpoints[turn] = (current["id"], current["state_hash"])
                print(json.dumps({"progress_turn": turn, "elapsed_seconds": round(time.monotonic() - started, 1), "population": owned_humans(state)}), flush=True)
        assert {"logistics-I", "industry-I"} <= set(state["technologies"])
        assert any(s["owned"] and s["planet_id"] == "long-run-planet-ash" for s in state["settlements"])
        for turn, (snapshot_id, checksum) in checkpoints.items():
            snapshot = db.snapshot(snapshot_id)
            assert snapshot["turn"] == turn and snapshot["state_hash"] == checksum
        restored = db.restore("long-run", initial_id, "restored-initial")
        branch = db.snapshot(restored)
        original = db.snapshot(initial_id)
        # Only branch identity metadata changes during restoration.
        branch_state = json.loads(json.dumps(branch["state"]))
        branch_state["_private"]["campaign_id"] = "long-run"
        assert branch_state == original["state"]
        assert db.current("long-run")["snapshot"]["turn"] == turns
        with db.connect() as connection:
            metrics = connection.execute("SELECT count(*) AS snapshots, sum(octet_length(state_json)) AS state_bytes FROM snapshots WHERE campaign_id='long-run'").fetchone()
        query_start = time.monotonic()
        db.current("long-run")
        current_ms = (time.monotonic() - query_start) * 1000
        query_start = time.monotonic()
        page, total = db.history("long-run", limit=50, offset=max(0, turns - 49))
        history_ms = (time.monotonic() - query_start) * 1000
        assert total == turns + 1 and page[-1]["turn"] == turns
        return {"connected_stress": "PASS", "planet_generator": planet_generator, "turns": turns, "seconds": round(time.monotonic() - started, 2),
                "population": owned_humans(state), "largest_state_bytes": largest,
                "current_read_ms": round(current_ms, 1), "history_50_ms": round(history_ms, 1), **metrics}
    finally:
        with psycopg.connect(dsn, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


if __name__ == "__main__":
    report = run(int(sys.argv[1]) if len(sys.argv) > 1 else 10000)
    repo = Path(__file__).resolve().parents[1]
    report["source_hashes"] = {name: hashlib.sha256((repo / name).read_bytes()).hexdigest()
                               for name in ("app/engine_v2.py", "app/universe.py", "app/store.py", "app/planet_generation.py")}
    destination = repo / "data/verification/stress-v2.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
