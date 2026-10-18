# Instrument interface verification

Environment: managed Linux6.18.55, Debian13 Chromium154.0.8037.57, Python3.12.14, Node24.19.0 and loopback PostgreSQL17.11. Three visible logical CPUs on an AMD EPYC9V74 host were reported in this workspace. Standard fictional fixtures run in isolated PostgreSQL schemas with private API servers and random memory-only test tokens. No real campaign was initialized, recovered, modified or reset.

## Browser and workflow method

`tests/browser_strategic.py` runs the actual application. It checks all16 management destinations against actual API fixture values (including explicit null Budget/empty collections), local Economy/Construction scope, public identifiers under disclosures, retained Orders drafts, supported preview/commit, historical read-only/live/branch behavior and context races. API-level verification separately covers private filtering, immutable histories and retry/stale rules.

Planetary management return compares actual canvas image pixels, retained canvas identity, nondefault pan/zoom, population overlay and selected province. Optional edge reveal, map gesture suppression and emulated touch use real input. Phone/tablet/desktop viewport checks use390×844,656×518 and1280×900; independent presentation captures additionally use1440×960. No uncaught page errors occurred in the passing runs. A fresh independent critic also exercised ordinary desktop navigation, mobile menu scrolling/Orders entry and access-dialog keyboard containment, separately from screenshots.

Actual Chromium browser zoom uses a disposable persistent profile, a fixed1280×960 browser window and Chrome Settings’ own default-zoom API. It verifies factors100%,125%,150%,200%, effective CSS viewport/DPR and `visualViewport.scale===1`, then uses ordinary Menu/campaign/zoom/Return interactions. No extension policy bypass is used. Direct CDP screenshot capture without an implicit clip is necessary: Playwright’s no-viewport screenshot clipping otherwise cropped browser-zoomed frames. Full physical captures remain1280×873 at all factors; CSS viewports are1280×873,1024×698,853×582 and640×436 respectively.

A final four-level selector/render check exposed hierarchy markers behind fixed controls. This is a real navigation defect rather than a missing fixture. A bounded Sol high review approved hierarchy-only safe drawing bounds; direct painted-marker descent and breadcrumb/camera regression results are recorded below after correction. The same independent critic also verified direct desktop, phone and actual200% zoom descent and accepted the expanded hierarchy scope. The test reads actual painted marker pixels and normal hover labels, then uses actual pointer/touch input, rather than exporting private app state or reproducing projection math.

## Timing and resource method

First Economy/Construction timers start **before** the actual pointer click and end when the relevant local pane/actual facility text is ready. They include automation/input overhead, exclude app startup, and do not await a complete rendered chart or paint. This differs from the preceding strategic milestone’s residual-after-click timers; do not treat the new values as a directly comparable speed regression/improvement.

Warm timing starts before programmatic `HWDesktop.open()` and ends at title/visibility readiness for24 cached transitions (eight Economy/Construction/map sequences). It does not represent24 complete journeys, physical pointer-to-paint latency, remote networking, startup or late-game content. DOM/API resource entry counts and explicit-GC CDP node/listener counts are compared around those transitions. A bounded plateau does not certify leak freedom, total heap/GPU stability or production performance.

## Results

Final hierarchy-corrected Chromium suite: **PASS**, with no uncaught page errors. The actual Hearth → Cinder → Reach marker path passes using pointer input, breadcrumb ascent and repeat descent, phone taps, and each actual browser zoom factor100–200%. A nondefault hierarchy pan/zoom and exact image/canvas/path remain equal across management navigation. Planetary camera/overlay/selection regression also passes.

The cold-context test holds the first Economy history request, opens Economy eight times, and observes exactly one request. It then resolves and truly warms Economy/Construction before measuring cached transitions. A separate narrow localized probe verifies stale-selection completion rejection, failure/retry and the equivalent management loading guard. This avoids calling a newly changed context “warm” and prevents duplicate in-flight work.

| Latest bounded sample | Result |
| --- | --- |
| First local Economy action to pane readiness |29.62ms |
| First local Construction action to facility readiness |52.27ms |
|24 cached transitions median / p95 |4.64 /13.15ms |
| Visible DOM nodes before / after |2,382 /2,382 |
| Post-GC CDP documents / nodes / JS event listeners before and after |1 /4,723 /176, unchanged |
| API resource entries before / after cached transitions |47 /47 |
| Held history requests for eight rapid cold opens |1 |

These counts include the expanded four-map/direct-descent and cold-warmup test setup, so do not compare raw request totals with earlier shorter scripts as an application regression. Captures and exact metrics are ignored local artifacts under `data/instrument-candidate/`; final full visual screens are under `data/instrument-final/`. The bundled two-weight font is about1MiB uncompressed; startup transfer/paint was not measured.

Nine focused backend/API tests passed freshly in1.149s: the five v2 acceptance cases plus static/API handoff, private campaign filtering, preview/commit/retry/stale and pre-game/restore behavior. Backend source and simulation rules are unchanged. No expensive simulation stress repeat was performed for these presentation changes; existing10,000-turn evidence belongs to the earlier backend milestone.

Chromium desktop and emulated touch are covered. WebKit remains unavailable: its distribution hosts rejected downloads under the workspace policy in the earlier milestone. Native macOS Safari remains unverified. No deployed/operational-security/backups/recovery certification is claimed.


## Subsequent command-station polish

See `docs/branches/map-desktop-shell.md`, Military command-station polish, for fresh `1ce20be` evidence. The complete Chromium regression passed, including a new `?map=placeholder` input/canvas-retention check. Updated runtime measurements are in ignored `data/instrument-polish-regression/metrics.json`; the final CSS disclosure-width fix was then checked by fresh desktop/phone captures. Original environment/method boundaries still apply.
