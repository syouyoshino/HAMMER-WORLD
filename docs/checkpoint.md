V7 verified implementation: **`ed66cb6`** on `map-generation`.

# Continuation checkpoint

Read `AGENTS.md`, `plan.md` and `docs/decisions.md`, then inspect actual source/tests and Git state. The existing repository is accessible and the scheduled continuation resumed the same work. Preserve the existing implementation. Do not duplicate completed acceptance runs without a relevant change.

## Current V8 material continuation

Opt-in V8 saves independently chosen liquid-lake and polar-water-ice masks.
Read `docs/reviews/surface-materials.md` for the strict contract, creation flags,
independent accepted backend/visual reviews, corrections and minor limits.
122 Python tests, Node material/crater checks, corrected protected V8 browser,
legacy V7 navigation and V3 cartography pass. Backend source is frozen and the
10,000-turn V8 gate is currently running in isolated QA PostgreSQL; do not edit
backend or claim final gate acceptance until its source-matching report passes.
Preserve this continuation; do not rerun accepted visual reviews without a change.

## Verified V7 cratered-world milestone

On `map-generation`, opt-in V7 saves separately chosen cratered geology for new
dry rock/ice worlds. All63 V1–V6 private/public baseline pairs remain exact;
no old maps/history/IDs or numeric rules change. Bounded high backend review and
the same fresh medium visual critic accept the corrected idealized scope.
Matching gradients/NW lighting fix crater artifacts; coast/river presentation,
Terrain annotation density, desktop chrome and caption layout are improved.

111 Python tests, canonical/seam/waterless Node checks, final protected V7
navigation/orders/history and legacy navigation/cartography/strategic/movement
browser regressions pass. Mixed10,000-turn V7 gate passed2465.58s; all backend
hashes match. History50 read4095.5ms remains a material full-snapshot cost.
Read `docs/reviews/cratered-worlds.md` and latest branch section for evidence,
creation flags, independent critique, performance/browser limits and delivery.

No photorealism/science claim: circular profiles/overlaps and axial/coarse source
geography remain stylized. Fractured ice, basalt/maria, volcanic and atmospheric
families are later work. No original-cloud recovery, character-relationships
branch edit, old-map conversion, merge or deployment. Interface release candidate.

## Earlier cylindrical-chart continuation — 23 October 2026 (Australia/Melbourne)

On `map-generation`, implementation `d43a4cd` adds opt-in V6 periodic longitude with bounded
latitude at128×80. Existing V1–V5 output/defaults/records remain unchanged;
Sol high independently matched45 legacy private/public baseline pairs. A fresh
Sol medium critic accepted scoped desktop navigation after Forces hover contrast,
legend/overview/counter overlap, wrapping guidance and label leader corrections.
Final V6 and legacy movement browser checks pass;98 Python tests plus existing
V5 navigation/V4 preset/V3 cartography/broad strategic regressions passed.
The mixed V6 10,000-turn gate passed in2722.03s with10,001 source snapshots;
all backend hashes match the frozen source. History50 read3721.7ms remains a
limit. Read `docs/reviews/planet-wrap.md` and the latest branch section for exact
browser/performance evidence and delivery references.

This is navigation acceptance, not planetary-art or commercial-game parity.
Actual barren/frozen captures lack recognizable geology; no new NASA photos
were fetched (403). Geological families/gas giants remain future work independent
of water/vegetation presets. Minor route/header clearance and small metadata,
plus inherited history/storage cost, are documented. No cloud-data recovery,
old-map conversion, character-relationships branch edit, merge or deployment.

## Earlier continuous-map continuation

On `map-generation`, implementation `c488e3f` adds opt-in V5 128×80 saved planetary charts, preserving
existing V1–V4 output and records. Full-canvas cover/clamped panning, pointer
zoom, cover-relative100–500% zoom, separate Recenter, inspector-aware overview
and shared cached recorded land anchors are implemented. Independent scoped
desktop critique accepts navigation; legacy holding-label/zoom regressions were
fixed and rerun.93 distinct Python tests and navigation/preset/V3/broad browser
regressions are verified, including Chromium browser zoom100–200%. The mixed
V5 10,000-turn gate passes in2529.31s; final backend hashes match its report.
History50 reads3980.1ms on the larger full-snapshot fixture, a documented cost.
Read `docs/reviews/continuous-map.md` and the final section of
`docs/branches/map-generation.md` before continuing. Desktop only; no wrapping,
data recovery, merge or deployment is claimed. Delivery references are recorded
in the branch document.

## Earlier planet-preset continuation

On `map-generation`, `af28097`/`01c4271`/`b629ccb` add opt-in V4 creation-time presets with independent per-planet overrides and stable auto selection. Arid/Barren/Frozen contain no open water or vegetation. Existing maps and V1–V3 generation are preserved. User now requires desktop-only acceptance.88 distinct Python tests, final desktop preset/legacy regressions, independent scoped critique and a mixed-world10,000-turn gate pass. Read `docs/reviews/planet-presets.md` for commands, exact evidence/limits and continuation; no deployment or recovery of original cloud data occurred.

## Latest interface continuation — 22 October 2026

On separate `map-generation`, implementation `c5e9516` adds opt-in V3 saved terrain, Orbital/Survey planetary styles and semantic charts across the existing four map levels; Light/Dark/System remains toggleable. Existing V1/V2 generation/history/IDs/rules stay intact. Same-critic scoped acceptance,79 Python tests, three Chromium browser regressions and the final10,000-turn V3 gate pass. Read `docs/branches/map-generation.md` for current decisions, exact evidence, minor limits and integration notes; the older results below are historical, not fresh coverage. No production deployment, original cloud recovery or character-relationships merge occurred.

## Accepted scope and completed local delivery

- PostgreSQL is primary; Google Drive is a retryable player-visible archive. SQLite is only an explicit read-only legacy migration source.
- Controlled JSON decision packet/import/preview/commit works. The backend calculates versioned numerical rules; narrative has no implicit mechanical effect. Ordinary ChatGPT messages cannot update the server. Authenticated MCP remains later integration work.
- Luna built bounded implementation tasks, Sol 6.1 medium handled localized numerical-ledger and browser failures, and Sol 6.1 high reviewed architecture/security/numerical/persistence/integration decisions. Keep that hierarchy and lean direct modules.
- The isolated fictional vertical slice and subsequent authorized connected-demo expansion are locally complete. The real campaign remains **pre-game unknown** with no approved baseline or geography. Fictional fixtures never establish campaign canon.
- Four interactive map levels, saved deterministic geography, visibility filtering, zoom/pan/selection, data-backed planetary overlays, 15 management reports/entity inspection, projects, historical metrics/comparisons and movable/resizable retro windows work in the local demo.
- Connected fixture rules cover production, taxation, welfare/growth, construction, research, recruitment, supply/deployment, fleet travel/combat, trade/treaties, exploration, investigations, colonization and character assignments. See ADR-008 for their explicit limits. Legacy world-v1 saves retain their original rules and saved maps.
- Immutable checksum/version-validated PostgreSQL snapshots, campaign row locking, scoped idempotency, atomic snapshot/pointer/outbox writes, rollback, historical branches and explicit legacy migration are implemented. Initial generation and later simulation are separate; every planet's geography and private generator configuration are persisted, never regenerated on reads.
- Private player/GM bearer authorization, campaign allowlists and explicit nested projections exclude seeds, hidden positions, confidential markers and unobserved foreign balances. Frontend tokens stay only in memory; logout invalidates pending requests and clears state.
- Configurable private HTTPS/systemd/Compose, backups and optional bounded archive timer are prepared. Drive retries freeze public bytes/destination/checksum and durable file IDs, verify remote bytes/metadata, enforce leases and keep demo/real folders isolated. Pending jobs are not synchronized jobs.

## Observed acceptance

- Final focused discovery: **68 tests passed in 29.584 seconds**, excluding the already-verified legacy v1 10,000-turn case. After the owned-fleet projection correction, its additional docking regression, five independent v2 acceptance checks and 12 archive checks passed. The docking regression exercises the actual planetary population map, including its ten docked crew.
- Sol high independently rejected **43 invalid scalar/location/destination cases**, accepted valid boundaries, and verified PostgreSQL persistence/restore of private generator metadata with no public exposure. It also verified that an unrecorded resource mutation fails closed rather than being balanced by a fabricated residual.
- Final connected **10,000-turn PostgreSQL run PASSED in 580.74 seconds**. It retained a source-hashed report at ignored `data/verification/stress-v2.json`. Every turn reconciled people, every categorized resource and treasury. It checked 10,001 immutable source snapshots and restored the exact initial world into an independent branch while preserving the original timeline. Final owned population 1,199 reflects a recorded combat casualty; the fixture did not collapse to a zero-state simulation.
- Local synthetic measurements: largest state **41,896 JSON bytes**; total source-state JSON **382,083,362 bytes**; current read **14.1 ms** and 50-row historical read **154.6 ms**. These are measured fixture results, not production benchmarks. All three retained backend source hashes match current files.
- The earlier legacy economy-v1 10,000-turn PostgreSQL gate passed in approximately 297 seconds. No relevant v1 calculation/persistence change justified rerunning it.
- Real PostgreSQL custom-format `pg_dump`/`pg_restore` recovery into a separate database passed, including v1/v2 state, history, branches, queued archives and immutable-record enforcement.
- Trusted localhost HTTPS/private API verification passed using Caddy and a temporary CA, including unauthenticated denial, player campaign isolation, GM authorization and safe fields. Compose and Caddy template validation plus backup shell syntax passed.
- Final **Chromium and Linux WebKit** runs passed both legacy and private v2 workflows: all four maps, distinct rendered overlays, 15 management reports, eight original history metrics/comparison, preview without writes, calculated commit, read-only inspection, branch restoration, pre-game unknown values, login/logout/reload clearing, window interaction and mobile layout/accessibility. No JavaScript page errors or mobile horizontal overflow. A deliberately held history response verifies busy controls and subsequent live navigation. The source-hashed four-run result is at ignored `data/verification/browsers.json`.
- Desktop/mobile screenshots were inspected; captures remain under ignored `data/previews/`. Linux WebKit is engine coverage, **not native macOS Safari verification**.

## Failures found and resolved

- High review found starvation/workforce, shared research inputs, arrival action/timing, destroyed traveler, population location, nested projection and incomplete consumption/ledger defects. Luna and Sol medium corrected them before final acceptance. Resource ledgers now record actual mutations, never inferred balancing adjustments.
- Screenshot review found clipped phone navigation/login, raw inspector timestamps, indistinguishable overlays and a docked-crew projection omission (Forge showed 890 instead of 900). Corrected mobile icon navigation/access, readable timestamps, recorded shading/markers with unknown areas, and owned-only fleet docking projection. Foreign docking fields remain excluded.
- Intermittent WebKit history/live/restore timeouts were reproduced: an asynchronous history refresh detached a button between pointerdown and pointerup. Sol medium added busy/disabled controls and stale-render guards, a deterministic delayed-response regression, and restored legacy production reports from recorded fields. All final browser workflows passed afterward.
- Older connected runs stopped at 5,000 before fixes or lost their final tool output during environment continuation. Neither is claimed as final acceptance. The retained completed 10,000-turn report supersedes them.
- One delegated WebKit diagnostic lacked extracted Linux libraries and could not launch. Final runs supplied the temporary dependency paths correctly. Caddy validation initially tried a read-only home directory; temporary XDG directories resolved that environment issue without changing deployment templates.

## Next steps requiring configuration or new scope

1. Follow `README.md` to create a protected local environment, initialize the separate demos/pre-game campaign and start the loopback server. `docs/playing.md` explains the controlled handoff and history; `docs/testing.md` records verification commands.
2. For actual Drive operation, configure server-side credentials and distinct folder IDs, renew the access token on the server, then test an authenticated upload/retry. Proposed real folder name: **Wold — Campaign Archives**. Existing Campaign Memory, State Ledger and Chronicle were not modified; no live Drive synchronization is claimed.
3. Choose a Linux host/domain for private HTTPS when ready, configure protected database/access settings and backups, then verify the actual external endpoint and recovery. No public deployment was performed.
4. Test on native macOS Safari before claiming that browser. Implement authenticated MCP against the existing pipeline only when explicitly taken up. Import a real campaign baseline only after its rules/data are approved; never use demo values as canon.

## Temporary local QA environment

PostgreSQL 17 QA runs in Docker on loopback port 55432. Protected connection values are in `/tmp/hammer-app.env`; never print or commit them. Psycopg dependencies are under `/tmp/hammer-python-deps`; PostgreSQL client tools and WebKit Linux dependencies are under `/tmp/hammer-webkit-deps/root`; Caddy is `/tmp/hammer-caddy`; Playwright browsers are `/tmp/hammer-world-browsers`. These temporary tools are not deployment configuration. Tests use disposable schemas and recovery databases. Credentials, databases, dumps and generated captures/reports are ignored by Git.
