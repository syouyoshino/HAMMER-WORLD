# Continuation checkpoint

Read `AGENTS.md`, `plan.md` and `docs/decisions.md`, then inspect actual source/tests and Git state. The existing repository is accessible and the scheduled continuation resumed the same work. Preserve the existing implementation. Do not duplicate completed acceptance runs without a relevant change.

## Saved stellar astronomy continuation

Implementation/tests/review: `1887986` on `map-generation`.

Read `docs/reviews/celestial-stars.md` and the latest branch note.
Opt-in new demos now save static-v1 astronomy; existing records/default digests
remain intact. Native Orbit shows the public host star from those records with
exact camera perspective/parallax, directional light and explicit Locate.
Historical sky remains read only; legacy native views show Star unlocated.
Independent backend and visual/interaction reviews accept the scoped feature;
240 legacy hashes and 10,000 connected astronomy-retention turns pass. Preserve
the documented frozen-epoch/night-survey/browser/performance limitations.

## Globe lighting and celestial-data continuation

Implementation/review: `4335f6f` on `map-generation`.

Read `docs/reviews/globe-lighting-and-celestial-data.md` and the latest branch note.
Three shader lines improve spherical shading; independent visual and actual orbital
browser regression accept the scoped result. Recorded barren rock stays grey;
water/lava/frozen fixtures retain distinct materials. Accurate sky markers remain
blocked by absent physical positions/ephemeris/frame/epoch/orientation. Do not
reinterpret topological chart coordinates or decorative stars as real bearings.

## Orbital background depth continuation

Implementation/tests/review: `5ef3d75` on `map-generation`.

Read `docs/reviews/orbital-background-depth.md` and the latest branch note.
The decorative sky now uses continuous world-ray noise in one bounded 128-side
cached bitmap rather than recognizable clouds/strokes. Preserve the documented
rejected candidates, independent findings and performance limits. Globe relief
remains separate; no campaign astronomy or units were invented.

## Adaptive orbital background continuation

Implementation `9a78a62` is verified, committed and pushed to `origin/map-generation`.

Read `docs/reviews/adaptive-space-background.md` and the latest branch note.
The camera-responsive near-black/slate haze and sparse sky are independently
accepted within scope. Browser pixel/idle/transition/resource/fallback checks and
protected auth/history/movement regression pass; no backend or terrain/shader
module changed. Input pacing and GPU/native-rate smoothness limits remain
explicit. Keep generic decoration separate from campaign astronomy. Delivery evidence and limits remain in that review.

## All-environment quality-control continuation

Implementation `2c918fd` is verified, committed and pushed to `origin/map-generation`.

Read `docs/reviews/environment-quality.md` and the latest map-generation branch
section. Current scope covers nine representative profiles, all six presets and
all implemented liquid/ice choices, both desktop themes. New QA fixtures are
isolated, existing records stay unchanged. Shared status contrast and native
feature camera visibility defects are corrected; no renderer/backend changed.
The audit retains rejected early transition captures separately. See the review
for final matrix results, source-hash scope, remaining inherited limits and
continuation evidence. This remains an interface release candidate.

## Desktop quality-control follow-up

Implementation `917fb6a` is verified, committed and pushed to `origin/map-generation`.

The current-run audit and correction are recorded in
`docs/reviews/quality-control.md`. Truthful startup/pregame state, stable report
reading surfaces, active scope semantics, campaign-dialog naming/focus, settlement
context, units and project empty-state hierarchy are corrected. One independent
Sol medium critic accepted the scoped final visual candidate. Protected native
Chromium regression passed, including auth/stale responses, historical read-only
and movement preview/commit. Backend and map/sphere/annotation hashes remain
unchanged; prior simulation gates remain applicable. See the review for final
browser/performance evidence and limitations. No merge or deployment.

## Orbital settlement orientation continuation

Implementation `61f19a8` is committed and pushed to `origin/map-generation`.

Recorded settlement annotations now make rocky globes navigable. Independent
blind A/B review and follow-up interaction review accept the bounded task after
fixing focus loss, visibility-cap ordering, directional cues and label/anchor
clarity. Markers use public settlements and exact saved province anchors;
activation descends to the corresponding province inspector. North-up, building
glyphs/leaders, explicit Hydro names, keyboard/touch input and bounded DOM cache
are verified. Read `docs/reviews/orbital-orientation.md` and the latest branch
section for findings, evidence, delivery references and limits.

Protected campaign/auth/history/movement regression passes; actual Chromium
desktop tab zoom100–200% passes both physical sizes. Twenty warmed cycles retain
one canvas and stable DOM/listeners. Backend and terrain/sphere renderer hashes
match the prior accepted release; no repeat simulation gate was warranted.
Physical polar distortion and sparse natural rock relief remain limitations.

## Native planetary-scale release candidate

Native V10 backend `128a45a` and interface `34a9f25` are verified and pushed
to `origin/map-generation`; native surface review
has accepted the dry/ice corrections. The true navigation globe and strategic Surface workflow have independent
scoped acceptance; final delivery references are in the branch document. Read `docs/reviews/planet-scale.md`. Independent critique twice
rejected additive V9-detail treatments, leading to canonical1024×640 generation
and compact128×80 strategic summaries. Old V1–V9 maps/defaults remain exact.

Final frozen backend:147 Python tests PASS1144.544s under concurrent QA load;
264 exact V1–V9 private/public baseline hashes; 10,000-turn isolated PostgreSQL
fixture PASS459.36s with10,001 snapshots, exact history/restore, unchanged fine
geography and4assets. Snapshot JSON sum713,976,548B plus20,906,145B separate detail;
largest state75,232B; current read12.0ms; history50 290.1ms. All14 app source hashes
match ignored `data/planet-scale/{backend-freeze,stress-v10}.json` and current code.
These are local fixture measurements, not production throughput/disk usage.

Protected Chromium native workflow passes: defaultForge; settlement economy/
construction/map return; fine feature search/picking; stable canvas/input handlers;
canonical map-target movement preview/commit; read-only history; late actual
asset rejection after campaign switch/logout; no stored tokens or page errors.
Replay used previously generated fictional fixtures with exact backend hashes and
creation-option checks, then actual SQL/auth/turn operations. See ignored
`data/planet-scale/browser-orbit-final/workflow.json`. Water's scoped visual review is
accepted; continuation review accepted dry/caps filtering and frozen/ice contrast.
Final orbital acceptance follows a lighting separation: unlit saved surface
composition on the sphere, detailed relief on Surface. Prior HIGH polar spokes
are resolved. The same critic accepts the bounded navigation globe, not optical
accuracy or Google Earth fidelity. Sparse rock landmarks and polar distortion
remain limitations. Final read-only orbit controls/fallback and actual Chrome
Settings zoom100–200% pass both desktop sizes; no exercised page errors. WebKit
is unavailable; native Safari is unverified. Cached Surface warm-draw means
2.19–15.90ms on a shared2-CPU Linux fixture;20warm workspace cycles keep the same
canvas/DOM/listeners. See the source-hashed final performance supplement.

QA exposed an inherited concurrent startup-DDL/writer deadlock; rollback left no
orphan assets/jobs or failed campaign head. Serialize setup after readiness;
operational startup/migration concurrency is not certified. Do not rerun gates
for frontend-only fixes. No merge/deploy; runtime data stays ignored.

## Current V9 hydrographic-identity continuation

On `map-generation`, the optional V9 names/catalog/feature inspector and rendering
corrections are implemented and independently accepted within the documented
scope. Read `docs/reviews/hydrography-names.md` and the latest branch section.
132 Python tests, 240 exact legacy hashes, focused renderer checks, complete
protected V9 and legacy cartography/strategic browsers pass. Chromium 154 actual
native zoom100–200% passes both physical desktop window sizes; WebKit absent,
native Safari unverified. Existing maps/defaults/history/rules remain unchanged.

Implementation **`feaf766`** is committed and pushed. The final V9 10,000-turn
isolated PostgreSQL gate passed in **5450.49 seconds**, with 10,001 snapshots,
unchanged geography and exact history/independent restore. All twelve report
source hashes match the frozen backend and committed implementation. Largest
state: 1,183,300 bytes; summed snapshot JSON: 9,538,588,921 bytes (not disk usage).
Current read: 161.4 ms; 50-record history: 10,021.3 ms on the shared 2-CPU Linux
fixture. Full-snapshot storage/history cost is a measured limitation, especially
for the newly requested larger planetary scale. Report:
`data/hydrography-pass/stress-v9.json` (ignored runtime evidence).

Next: investigate genuinely larger geographic scale/detail and meaningful zoom,
preserving existing maps and immutable history; obtain the bounded architecture
review before increasing grids or changing persistence. No merge or deploy.

## Current V8 material continuation

Opt-in V8 saves independently chosen liquid-lake and polar-water-ice masks.
Read `docs/reviews/surface-materials.md` for the strict contract, creation flags,
independent accepted backend/visual reviews, corrections and minor limits.
Implementation **`50a4afa`** is pushed to `map-generation`. 122 Python tests, Node
material/crater checks, corrected protected V8 browser, legacy V7 navigation,
V3 cartography and actual desktop browser zoom 100–200% pass. The isolated V8
10,000-turn gate passed 3291.49 s with 10,001 snapshots and exact history/restore;
all 11 backend hashes match freeze/report/pushed source. Reading 50 history records took 5558.8 ms
remains a full-snapshot performance limit. Preserve the accepted scoped release
candidate; do not repeat gates/reviews without a relevant change. No merge/deploy.

## Verified V7 cratered-world milestone

Implementation: **`ed66cb6`**.

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

## 29 October 2026 — map-generation interface candidate

Explicit-radius V11 generation and context-preserving star/planet/moon destinations
are implemented on `map-generation`; old versions/campaigns remain unchanged.
There is no Earth-size default. The finite overview reports unresolved detail.
Read `docs/reviews/physical-scale-and-body-focus.md` and the branch notes for numeric
contracts, independent critique corrections, browser/resource evidence, final
stress results and remaining minor limits. No merge/deployment or unrecovered
cartography/real-campaign recovery is implied. Light/dark and desktop scope remain.
