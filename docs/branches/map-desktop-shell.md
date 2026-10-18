# Aerospace instrument interface release candidate

Branch: `feature/map-desktop-shell`. Verified implementation milestone: `bb716f9` (Rebuild strategic interface as monochrome aerospace instrumentation). This continuation/QA documentation follows it. Earlier `85971b0`/`b6836be` established the strategic workspace; `c488aa1`/`65f8321` implemented/documented the preceding floating desktop shell. The visible Windows-era design is superseded by the user's four supplied monochrome instrument references and complete design authorization.

This is an **interface release candidate**. No unavailable cloud source, cartography or campaign database was recovered. No real campaign records, backend rules, schema, saved coordinates or terrain generation were changed. No merge, deployment or data reset was performed. Operational security, backups and recovery were not independently certified by this interface work.

## Final design

Off-white surfaces, graphite Noto Sans Mono regular/bold, fine rules, open information groups and sparse inverse selected controls replace bevels, navy title bars and nested frames. Fonts are self-hosted with attribution/OFL terms. No new framework, copied reference assets, fake telemetry or decorative gauges were added.

The permanent full-frame canvas, compact command access, retained management workspace and contextual inspector remain. Menu is grouped, campaign/turn/state stay visible and optional edge reveal remains a secondary preference. Inspector collapse retains selection. Reports use saved names and compact factual summaries; technical fields remain in disclosures. Local population/civilians/crew/soldiers are distinguished; unknown totals remain unknown. Economy prioritizes local condition, then stocks. Construction retains actual facilities/projects and work/status. Character relationships remain explicitly unavailable.

Orders leads with proposal/preview state and clear next actions. Token/import/raw JSON controls are secondary; a validated preview exposes balances and readable production/consumption by saved settlement, with complete response details available. Drafts stay in the retained textarea DOM, not storage. Source collapse does not invalidate a valid preview; editing does. Late file reads check the exact current textarea/context. History explains a single baseline instead of displaying an empty plot; real multi-turn charts carry value/turn labels.

Planetary colours/selection/labels adopt the survey presentation without changing geography or camera transforms. Labels anchor to actual provincial land, identify saved holdings without claiming precise settlement coordinates, and prioritize holdings on compact maps. Hierarchy maps use measured persistent-chrome safe bounds within the same canvas, so known markers do not sit behind the header. Drawing and hit testing share clipping; source coordinates and camera state remain authoritative. A single scheduled ResizeObserver handles responsive chrome.

## Functional correctness

The final `tests/browser_strategic.py` Chromium run passes all16 primary management destinations with actual API values/empty states, related History/Orders workflows, local/campaign scope and identifier disclosures. Direct Hearth → Cinder → Reach map-marker clicks, breadcrumb ascent/repeat descent, phone taps and actual100–200% browser zoom pass. This extends the selector/render checks at Galactic/Sector/System/Planet levels.

Nondefault hierarchy camera/image/path and planetary camera/overlay/selection/image remain equal through management navigation, with the same canvas. Orders drafts, preview/commit, historical read-only/live/branch behavior, stale A→B→A responses, pending-login cancellation and delayed-map dialog navigation pass. A cold eight-open Economy burst produces one in-flight history request; guards reject stale completions and allow failed reads to retry. No uncaught page errors occurred.

Nine focused backend/API tests passed freshly in1.149s, covering v2 acceptance, private filtering, static/API handoff, preview/retry/stale and pre-game/restore behavior. JavaScript/Python syntax and diff checks pass. The existing backend10,000-turn milestone is historical; no unnecessary simulation stress repeat was performed for this UI-only change.

## Independent quality loop

One fresh-context Sol medium critic inspected original source photographs and actual full app frames before source/implementation discussion, then followed the same correction loop. Findings corrected: obscured commandbar, repeated headings, small core readouts, raw overcompressed military tables, technical Orders dominance, empty History chart, clipped phone navigation and unclear empty collections. The real validated Orders state revealed a further nested-JSON defect, corrected with structured settlement breakdowns. Apparent200% clipping was diagnosed and corrected as a screenshot-method artifact.

Broader map coverage exposed a genuine hierarchy occlusion defect after earlier reviewed states had passed. A bounded Sol high diagnosis approved the safe projection described above; Luna implemented it. The same independent critic then separately performed actual desktop clicks,390×844 touch taps and actual200% browser-zoom direct hierarchy descent, alongside its earlier ordinary report navigation and15 Tab/15 Shift+Tab dialog-containment checks. It accepts the complete presentation in the adapted reference family, including the extended hierarchy path, with no remaining evidenced P0/P1/P2. It did not use numerical averages to hide defects.

Remaining P3 notes: small tertiary metadata, subtle scroll continuation, generous report spacing and reduced readout separation where terrain lies behind the header at200% zoom. Sparse fixture worlds, schematic higher-map grouping and pixel/tile geography remain renderer/content limits. The visual verdict is separate from parent-run functional tests.

## Comparative and browser limits

All four user photographs were actually opened: monochrome avionics/instrument controls, approximately1179×780 pixels, photographed at an angle with blur. They establish a design family, not equivalent game content or a1:1 screen layout. Blur/faintness is intentionally not reproduced. No proprietary assets were copied.

Earlier commercial/open-source research remains documented in `docs/reviews/strategic-interface-baseline.md` and `strategic-workflow-comparison.md`. The user-requested task comparisons remain: Victoria3 main economic diagnosis **partial** because authoritative diagnosis/trends are absent; CK3 relationship comprehension **unavailable** because relationship records are absent; Stellaris-style strategic return **passes within tested paths**. This release does not claim whole-game parity. The specific A World Divided reference remains unidentified.

Chromium154 on managed Linux covers desktop, emulated touch,1280×900/656×518/390×844 layouts and actual browser zoom100/125/150/200%. Independent design captures also use1440×960. At200%, effective CSS640×436/DPR2 is confirmed with visualViewport scale1. Full CDP captures are1280×873 physical pixels. WebKit remains unavailable after earlier policy403 download failures; native macOS Safari and physical mobile devices remain unverified.

## Performance evidence

On an isolated fictional demo-v2 PostgreSQL fixture: first local Economy/Construction pointer-action-to-ready measurements29.62/52.27ms;24 genuinely cached transitions median4.64ms/p9513.15ms. DOM2,382, post-GC CDP nodes4,723/listeners176 and API resource entries47 remained unchanged around cached transitions. Eight rapid cold Economy opens produced one held request.

Timings exclude startup and do not await full paint/chart completion; warm timings are programmatic transitions rather than physical pointer input. These are fixture observations, not production throughput, long-session leak freedom or heap/GPU guarantees. The two font files are about1MiB uncompressed. See `docs/reviews/instrument-verification.md` for exact method, environment and boundaries.

## Integration and continuation

Implementation is scoped to public presentation/lifecycle files and the browser regression. Backend schemas, rules, migrations and terrain generation are unchanged. Integrate independently recovered cartography at `public/app.js` render/navigation boundaries; retain canvas identity, public projection authority and safe persistent-chrome bounds. Do not derive map projection from transient workspace/inspector geometry. Preserve per-context loading/request guards and memory-only tokens.

`HWDesktop.createWindow`/registry/open/close remain the screen integration boundary. This branch does not modify or depend on `feature/character-relationships`. Add real relationship or diagnostic views only when authorized recorded data supplies them; do not fabricate records to complete a design demonstration.

Run `tests/browser_strategic.py` with an isolated `WOLD_TEST_DATABASE_URL`; see `docs/testing.md`. Root `design-qa.md` records source truth, comparison history and final passed gate. Screenshots/metrics under ignored `data/instrument-*` are local runtime evidence, excluded from commits and reproducible from tests. The optional loopback preview uses an isolated fictional schema, not a deployment or recovered database.

Continuation: review the branch diff before manual integration; reconcile any independently recovered cartography; address P3 polish as useful; verify WebKit/Safari/physical devices when available; evaluate larger real authorized datasets separately. No automatic merge or deployment is authorized or performed.
