# Hammer World

A Windows 95-inspired command interface for a persistent hidden-planet campaign. PostgreSQL holds immutable, checksum-verified snapshots and transactional turn submissions. The app includes a legacy `world-v1` fixture and an explicitly fictional connected `demo-v2` universe with hierarchical maps, management reports, history, JSON orders and a separate archive outbox.

PostgreSQL is authoritative. Google Drive archiving runs as a separate outbox worker; when server credentials or the matching destination folder are absent, records remain pending. Existing campaign documents are unchanged. Real campaign statistics remain unknown.

## Run locally

Python 3.12 or later and PostgreSQL 15 or later are required. Create an empty database and a local environment file, then install the pinned dependencies:

```sh
createdb hammer_world
cp .env.example .env
# Edit WOLD_DATABASE_URL and set a private random WOLD_GM_TOKEN in .env.
python -m venv .venv
.venv/bin/pip install -r requirements.txt
source .venv/bin/activate
set -a
. ./.env
set +a
python -m app.cli init
python -m app.cli init-v2 --campaign-id demo-v2
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 on the same machine. Local mode is for loopback development. The included private access mode requires player and GM bearer tokens and can be used with the prepared TLS deployment templates; no live public host is part of this project.

The `init` command creates the legacy demo and a pre-game campaign with no baseline; `init-v2` adds the separate connected fictional demo. Both remain isolated and versioned. The app never creates a campaign baseline for real-world play. Set `WOLD_GM_TOKEN` to a private random secret yourself; administrative HTTP access is denied when it is unset. Tokens entered in the dashboard stay in page memory and are cleared on logout. Never reuse production credentials in tests.

`WOLD_DATABASE_URL` selects PostgreSQL and is required. `WOLD_DB_SCHEMA` optionally selects a schema (defaults to `public`). The application reads environment variables directly; the shell commands above load `.env` for the current session. Runtime data is ignored by Git. Legacy SQLite databases are accepted only by the explicit migration command below.

## Strategic command interface

The interface uses a monochrome aerospace-instrument design: off-white surfaces, graphite readouts, fine rules and a bundled technical monospace. Choose a campaign explicitly after signing in. The live strategic map stays mounted behind a compact command interface. **Menu** opens the available management destinations; campaign, turn and historical state remain visible. An optional edge-menu shortcut is separate from the primary button and starts disabled.

Select a recorded province or settlement to inspect its condition. **Economy** and **Construction** open one management workspace with related navigation and explicit local/campaign scope. **Map** returns to strategic navigation without arranging windows. Collapse the inspector without clearing selection. Existing History comparisons and Orders & handoff retain their context when navigating between views. Orders exposes proposal/preview state first, with token and JSON controls under a disclosure; calculated balances and settlement breakdowns remain reviewable before committing.

Local stocks and recorded outcomes are not a ranked economic diagnosis or forecast. Character inspection shows available role/assignment records; relationship data is not supplied by the current model. Missing values remain unknown. No relationship graph or mechanics are fabricated.

This branch is an interface release candidate. It neither recovers the unavailable cloud workspace nor modifies the separate character-relationships branch. See [the continuation note](docs/branches/map-desktop-shell.md) and [workflow comparison record](docs/reviews/strategic-workflow-comparison.md) for evidence and limitations. It is not a deployed or operationally certified release.

## ChatGPT handoff

Export a packet from the dashboard's controlled import panel, or use the authorized Linux CLI:

```sh
python -m app.cli packet demo-v2 > decision-packet.json
```

Give the packet to ChatGPT and request a JSON proposal using its exact versioned schema. The packet describes the selected campaign's versioned rules and permitted orders. For `demo-v2`, worker allocations, construction, research, logistics, fleet and ground operations, intelligence and diplomacy are resolved by the backend. Narrative is plain text and has no mechanical effect. Legacy `world-v1` submissions continue to use their original three-worker economy.

Save the returned proposal locally, preview it, then commit explicitly:

```sh
python -m app.cli preview demo-v2 proposal.json
python -m app.cli import-turn demo-v2 proposal.json
```

HTTP equivalents are authenticated `packet`, `preview` and `commit` endpoints under `/api/admin/campaigns/{id}`. Requests require `Authorization: Bearer <WOLD_GM_TOKEN>`. A normal ChatGPT message cannot reach these endpoints. MCP is a future integration.

Stale proposals are rejected. Reusing a submission ID with identical content returns the original result; different content conflicts. Submission IDs are scoped to their campaign.

## Demo rules

`economy-v1` is an explicitly fictional fixture, not an approved real campaign rulebook. Workforce assignments last one turn and their sum cannot exceed population. In order:

1. Each technician produces two energy.
2. Miners consume one available energy each and produce two ore; insufficient energy limits productive miners.
3. Each farmer produces three food.
4. People consume one food each.
5. Food shortage reduces population by the shortage, capped at population; remaining food is zero.

Province population is unknown in v1. Planet population alone drives the economy. The pre-game campaign cannot resolve turns until an approved baseline is implemented and imported. `demo-v2` uses its separate `demo-v2` rules and recorded ledger; it does not upgrade or rewrite the v1 campaign.

## History and backups

History is read-only. Restoring a snapshot creates a new branch and preserves the source timeline and world IDs.

```sh
python -m app.cli restore demo SNAPSHOT_ID demo-branch
python -m app.cli backup backups/campaign.dump
```

Backups use PostgreSQL's custom dump format. Restore into a stopped, empty target with `pg_restore`; never overwrite a running database with a file copy. To migrate a legacy SQLite database, first create a SQLite backup with its backup API, then verify and import it into an empty PostgreSQL target:

```sh
python -m app.cli import-sqlite data/legacy.sqlite3 --backup backups/legacy-copy.sqlite3
```

The importer preserves campaign and snapshot IDs, exact state/command JSON, timeline pointers and outbox rows. It rejects unsupported versions, bad checksums, broken references and non-empty targets.

Snapshots are immutable and checksum-verified. Turn state, snapshot, current pointer and archive job commit in one PostgreSQL transaction. An archive-pending status is not a claim that Google Drive has saved the turn. Configure `WOLD_DRIVE_ACCESS_TOKEN`, `WOLD_DRIVE_FOLDER_ID` and `WOLD_DRIVE_DEMO_FOLDER_ID`, then run `python -m app.cli sync --limit 10` for one bounded upload pass. Demo archives use their own folder. Frozen public archive bytes and their reserved Drive IDs are reused across retries; remote metadata and exact bytes are verified before the outbox is marked complete.

## Verify

```sh
python -m unittest discover -s tests -v
```

Tests require `WOLD_TEST_DATABASE_URL` and create disposable isolated PostgreSQL schemas. See `docs/testing.md` for setup and coverage, `docs/decisions.md` for architecture decisions, and `plan.md` for the accepted eight-step plan.

The Drive worker keeps archives pending until server credentials and a destination are configured. Chromium desktop/mobile and Linux WebKit workflows are exercised. Windows can be dragged by their title bars, resized from their corner handles, and restored with **Reset windows**.

## Access boundary

The default server bind is loopback. Private mode authenticates read-only player access and GM operations separately; the prepared deployment templates add TLS for a private host. Player APIs return allowlisted fields and do not expose generation seeds, private hashes or GM data. These controls do not conceal secrets from the host administrator.
