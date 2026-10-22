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

## Map desktop shell branch

`feature/map-desktop-shell` changes the dashboard interaction model. It requires explicit campaign selection after login, launches reports from the HW command launcher, and retains multiple floating screens. The original `browser_smoke.py` and `browser_v2.py` scripts describe the previous always-visible dashboard and automatic demo selection; their selectors and assumptions require adaptation before use on this branch. The branch-specific desktop browser workflow is the acceptance entry point for the new shell:

```sh
WOLD_TEST_DATABASE_URL=postgresql://USER@HOST/ISOLATED_TEST_DATABASE \
WOLD_CHROMIUM_EXECUTABLE=/usr/bin/chromium \
python tests/browser_desktop.py
```

The script uses disposable schemas, starts a private loopback server and generates only explicitly fictional demo fixtures. It removes its schema/server at completion and writes fresh captures under `data/previews/chromium-desktop-*.png`.

Use an isolated PostgreSQL test database and the installed Chromium executable. Captures and runtime verification output belong under ignored `data/`; never commit private campaign records or tokens. See `docs/branches/map-desktop-shell.md` for the actual observed branch results and unavailable browser coverage. Do not interpret baseline stress results as new runs on this branch.


## Simplified strategic-interface candidate

Use the new interaction contract rather than the prior floating-window selectors:

```sh
WOLD_TEST_DATABASE_URL=postgresql://USER@HOST/ISOLATED_TEST_DATABASE \
WOLD_CHROMIUM_EXECUTABLE=/usr/bin/chromium \
python tests/browser_strategic.py
```

The script runs the real private application with isolated fictional fixtures and retains evidence under ignored `data/instrument-candidate/` (override with `WOLD_BROWSER_ARTIFACT_DIR`). See `docs/reviews/strategic-verification.md` for actual coverage, environment, timing definitions and limits. The older `browser_desktop.py` is useful to reproduce the `65f8321` baseline; it does not define the current workspace UX. Keep historical evidence distinct from fresh candidate results.


The instrument release candidate adds actual Chromium browser zoom100–200% in a disposable profile, full physical viewport captures, retained hierarchy/planet camera checks and direct painted-marker navigation. See `docs/reviews/instrument-verification.md` and root `design-qa.md`. Current captures/metrics are ignored runtime evidence; no private data or screenshot assets belong in commits.


The tactical overlay extension of `tests/browser_strategic.py` also commits supported build/recruit commands in its disposable fixture to check actual work and readiness graphics. Its response-only fixtures verify literal record-title rendering and unknown progress for invalid work without changing stored records. The optional generated map is loaded and toggled while underlying canvas pixels/context remain equal. Temporary artwork's first transfer and compositor cost are not included in cached transition metrics.


The Apple-colour graph extension verifies local food flow against authorized recorded outcomes, no fabricated baseline graph, cached food/energy/ore switching, consecutive history failures plus recovery, and fixed12px HTML axes after phone/desktop resize. Palette values are centralized in CSS; browser capture evidence checks actual panel alpha and chart-label dimensions.

## Versioned cartography candidate

`map-generation` preserves default V1 generation and stored geography. Create a **new fictional demo ID** with `python -m app.cli init-v2 --campaign-id NEW_ID --planet-generator planet-v3`; this explicitly uses the configured database and refuses existing IDs. Do not use it to replace a campaign. No new generation is enabled on startup or ordinary reads.

Run the candidate checks against an explicitly isolated PostgreSQL QA database:

```sh
WOLD_TEST_DATABASE_URL=postgresql://USER@HOST/ISOLATED_TEST_DATABASE \
python -m unittest tests.test_planet_generation -q
WOLD_TEST_DATABASE_URL=postgresql://USER@HOST/ISOLATED_TEST_DATABASE \
python tests/browser_cartography.py
WOLD_TEST_DATABASE_URL=postgresql://USER@HOST/ISOLATED_TEST_DATABASE \
python tests/browser_movement.py
WOLD_TEST_DATABASE_URL=postgresql://USER@HOST/ISOLATED_TEST_DATABASE \
WOLD_TEST_PLANET_GENERATOR=planet-v3 python tests/stress_v2.py 10000
```

The cartography browser script creates generated and legacy fictional fixtures in its own disposable schema. It tests real four-level marker navigation, Orbital/Survey, Light/Dark/System with no terrain-pixel/data change, bounded handler counts, retained canvas, touch controls/force stacks, unknown campaign clearing and unchanged snapshot hashes. It uses installed system Chromium and writes captures/metrics beneath ignored `data/map-release/`; it does not claim WebKit or native Safari coverage. Use `browser_strategic.py` for broad management/auth/history/browser-zoom checks and `browser_movement.py` for protected GM preview/commit and movement authority checks. Keep generated runtime evidence out of Git. See `docs/branches/map-generation.md` for the actual results and remaining resolution limits.

## Independent V4 planet presets (desktop scope)

`python -m app.cli init-v2 --campaign-id NEW_ID --planet-generator planet-v4 --preset auto` selects a stable preset per new fictional planet. Add repeatable `--planet-preset FULL_PLANET_NODE_ID=PRESET` overrides. See `docs/reviews/planet-presets.md`; existing IDs cannot be overwritten.

With an explicitly isolated `WOLD_TEST_DATABASE_URL`, run `python -m unittest tests.test_planet_presets tests.test_planet_preset_cli tests.test_planet_generation -q` and `python tests/browser_planet_presets.py`. The preset browser script now targets desktop only, per user direction; it captures six fixtures in both styles/themes and exercises actual mouse hierarchy navigation and selection without mutating snapshots. For the connected gate, set `WOLD_TEST_PLANET_GENERATOR=planet-v4`, `WOLD_TEST_PLANET_PRESET=auto` and `WOLD_TEST_PLANET_PRESETS` to a JSON map of full planet IDs to presets. Set `WOLD_STRESS_REPORT=data/verification/stress-v4-presets.json` to retain the earlier V3 report separately, then run `python tests/stress_v2.py 10000`. All fixtures use disposable schemas; runtime reports/captures remain ignored.
