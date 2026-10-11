# Verification

Use a separate PostgreSQL test database. `WOLD_TEST_DATABASE_URL` is required; the tests never fall back to SQLite. Each test uses a disposable schema. The backup recovery test also creates a temporary database, so the test role needs `CREATEDB`. Do not use a live campaign database as the test database.

Install the runtime requirements and PostgreSQL 17 client tools (`pg_dump`, `pg_restore`). Set the test connection in a protected environment, then run:

```sh
python -m unittest discover -s tests -v
```

The persistence stress test runs 10,000 committed turns and can take several minutes. It exercises real PostgreSQL transactions and snapshot history, rather than only calling a pure calculator. Tests also cover rollback, stale/concurrent submissions, retry identity, legacy migration, checksum corruption, historical branching, archive verification, privacy and resource constraints. Observed results are recorded in `docs/checkpoint.md`.

## Browser checks

Install Playwright as a development-only dependency and install its browsers/system dependencies for your host. Chromium can also use `WOLD_CHROMIUM_EXECUTABLE`; WebKit requires a working Playwright WebKit installation. Browser scripts create a disposable database schema and start a loopback server.

```sh
python tests/browser_smoke.py chromium
python tests/browser_smoke.py webkit
python tests/browser_v2.py chromium
python tests/browser_v2.py webkit
```

The legacy smoke workflow checks map interaction, recorded production reports, resource values, windows, preview/commit, historical inspection, branch restoration, pre-game unknown values and a mobile viewport. The private v2 workflow additionally checks in-memory login/logout, campaign allowlisting, all four map levels, distinct recorded overlays, 15 management reports and entity inspection, history metrics/comparison and reload clearing credentials. A deliberately delayed history response verifies controls remain disabled during refresh and live navigation works afterward. Captures are written to ignored `data/previews/`.

WebKit coverage helps catch Safari engine differences. A native macOS Safari run is still distinct and should be performed before claiming macOS verification.

## Connected long-term acceptance

```sh
python tests/stress_v2.py 10000
```

This separate PostgreSQL run uses nonzero production and connected construction, research, deployment, combat, trade, exploration and colonization. Every turn checks human conservation, explicit categorized resource flows, treasury reconciliation and immutable historical reads. It restores the original snapshot into a branch without changing the source timeline. It measures storage and query times and retains a source-hashed report in ignored `data/verification/stress-v2.json`. The fixture has growth disabled; targeted scarcity tests separately exercise growth, housing limits, shortages, shared research inputs and supply capacity. A successful fixture does not establish balanced rules for a real campaign.

## Local HTTPS

Install Caddy or set `WOLD_CADDY_EXECUTABLE` to its binary, then run:

```sh
python tests/https_smoke.py
```

This check starts Caddy and the application on loopback, uses a temporary local CA with certificate verification enabled, and tests player denial, campaign allowlisting, GM access and public-field filtering. It neither installs a trust certificate globally nor publishes a site.

## Live integration

Fake Drive tests verify retries, content verification and archive isolation. They do not establish a live Google connection. After configuring credentials and separate archive destinations, verify an authenticated upload and retry against Drive before claiming synchronization. Likewise, validate the chosen external HTTPS host before claiming deployment.
