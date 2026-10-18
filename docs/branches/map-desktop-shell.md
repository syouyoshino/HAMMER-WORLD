# Strategic command interface release candidate

Branch: `feature/map-desktop-shell`, based on `work` at `e8198b200ec92db3c33d4d797ca8034f1de96529`. Earlier milestones `c488aa1` and `65f8321` implemented/documented the retained floating desktop shell; this candidate supersedes its visible window-management model. Verified implementation milestone: `85971b0` (Simplify map shell into a strategic command workspace). This continuation/review documentation is the following delivery milestone.

No unavailable cloud source, cartography or campaign database was recovered. No real campaign records, database contents, terrain engine, backend rules or schema were changed. No merge, deployment or data reset was performed. This is an **interface release candidate**, not operational/security/backup certification or commercial-game parity.

## Final decisions

A bounded GPT-6.1 Sol high review approved a permanent unchanged-size map frame, retained connected report containers, one primary management workspace, one collapsible contextual inspector and a bounded Campaign & Access dialog. Luna implemented the main change; Sol medium handled localized asynchronous navigation races. See ADR-011 in `docs/decisions.md`.

The persistent compact command bar exposes labelled Menu, campaign choice, turn and recorded pending/history state. Map hierarchy and overlay controls are directly available. Optional edge reveal is off by default and suppressed during map gestures. Ordinary navigation requires no dragging, resizing, minimizing or window arrangement. Related tabs retain reports and Orders drafts. Explicit Map/close/Escape return controls preserve strategic context; inspector collapse does not clear selection. Inspector placement uses the opposite side of a selected point where possible. Large management views overlay rather than resize the canvas.

Selected Economy/Construction default to actual matching planet-and-province holdings, with explicit campaign scope tabs. Facility names/status and local stock/condition records precede secondary identifiers. Missing rates, diagnosis and character relationships are explicitly unavailable. Campaign-wide screens identify their scope separately from retained map selection. Authentication tokens remain memory-only; the new persisted setting is only `hw.command.edge.v1`. Old geometry/pin settings are ignored.

## Verification and independent review

Fresh baseline screenshots/browser interactions established the initial gaps before edits. Nine focused backend/API tests passed; JavaScript syntax and diff checks passed. The new Chromium browser suite passes all 16 management destinations, four map levels, recorded local/campaign contents, construction, character inspection, retained Orders draft, supported turn preview/commit, historical read-only/live/branch behavior, stale A→B→A requests, delayed login/logout and a delayed-map dialog race. Normal visible controls were exercised for initial authentication/campaign entry. Actual emulated touch exercises command access, management return and map zoom.

Across Economy → Construction → map, the same canvas, nondefault camera, population overlay, selection and image pixels are retained. Viewports 1280×900, 656×518 and 390×844 were exercised without document overflow or stranded return controls. No uncaught page errors occurred. Browser display zoom remains unverified.

One fresh-context Sol medium critic received anonymous full-frame baseline/candidate/reference material before implementation context, then reviewed concrete fixes in the same loop. Local-first information, scope mistakes and clipped/colliding mobile controls were corrected. The final ten screenshots support scoped acceptance of the implemented local journey with no critical/major UI blocker. Interaction evidence came from the browser suite, separately from screenshot critique.

User-requested comparisons remain distinct: Victoria 3 main economic diagnosis is **partial** because authoritative ranked diagnosis/trends are absent; CK3 relationship understanding is **unavailable** because character relationship records are absent; Stellaris-style strategic return **passes within the tested path**. Passing the interface path does not complete the two unavailable data/mechanics tasks.

See `docs/reviews/strategic-interface-baseline.md`, `strategic-workflow-comparison.md`, `strategic-quality-loop.md` and `strategic-verification.md` for research provenance, findings/resolutions, task evidence and exact methods.

## References and performance

Actual Open-IG full screenshots and source at `9891378f2f00ba83d51ad92773f8cb2dd9744b12` were inspected. Official Victoria 3 UX/data-visualization and CK3 controls/relationship descriptions, Stellaris interface documentation, and indexed HOI4/Shadow Empire/Starsector examples informed bounded comparisons. Direct commercial image downloads were blocked; no equivalent live-play or full commercial pixel review is claimed. The user's A World Divided reference remains unidentified. No reference assets/code were copied into the product.

On managed Linux, Chromium154, Python3.12, Node24 and PostgreSQL17 with an isolated fictional demo-v2 fixture: 24 cached programmatic transitions measured median3.47ms/p95 8.73ms to title/visibility readiness. DOM1,583, post-GC CDP nodes3,089/listeners283, and API resource entries27 were unchanged. First local-pane residual waits after click completion were9.29/29.25ms; these are not startup or complete input-to-paint timings. No production-scale, heap/GPU or long-session guarantee follows. No unnecessary simulation stress repeat was performed for this UI-only change.

Chromium desktop and emulated touch are covered. WebKit is unavailable: its distribution hosts returned policy403. Native macOS Safari is unverified.

## Remaining limitations and integration

Nonblocking polish findings remain: raw military tables can wrap/clip columns, inspector IDs/province-total Unknown have excessive prominence, mobile scope headings wrap, some small labels/dropdown truncation and duplicate breadcrumb naming remain. The inherited map has sparse fixture geography, square-tile/outline limitations and phone letterboxing. These are recorded rather than masked with fabricated content.

Integration points are `public/desktop-shell.js`, scoped CSS and focused render/navigation/auth lifecycle boundaries in `public/app.js`; existing map drawing/generation and backend files are retained. Keep the canvas mounted and frame size stable when integrating independently recovered cartography. `HWDesktop.createWindow`/registry/open/close remain compatible screen-registration hooks for a future character-relationships screen. This branch neither modifies nor depends on `feature/character-relationships`. Preserve request epochs/sequences and avoid late navigation/chooser closing after awaited requests.

Run `tests/browser_strategic.py` with an isolated `WOLD_TEST_DATABASE_URL`; see `docs/testing.md`. `browser_desktop.py` is historical baseline evidence, not the new interaction contract. Screenshots/metrics under ignored `data/strategic-{baseline,candidate}` and anonymous review packets are local runtime evidence and excluded from commits. Continue with readable Military summaries, province/settlement population labeling, browser-zoom/WebKit coverage and authorized relationship/diagnosis data when available. Review the diff before any manual integration; do not assume missing cloud work was recovered.
