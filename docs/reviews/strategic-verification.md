# Strategic interface verification

## Environment and scope

Observed environment: managed Linux 6.18.55 x86_64, glibc 2.41; three visible logical CPUs (AMD EPYC 9V74 host model); Python 3.12.14; Node 24.19.0; Debian Chromium 154.0.8037.57; PostgreSQL 17.11 on loopback. Browser runs use isolated schemas, standard fictional fixtures and a private loopback API. They do not initialize or alter a real campaign.

Baseline `tests/browser_desktop.py` passed freshly at `65f8321`. It verifies the prior desktop interaction model, not the new workspace acceptance contract. Candidate acceptance uses `tests/browser_strategic.py`.

## Performance method

Measure first report readiness and repeated warm task navigation separately. The first-report timers start after the pointer click returns, so they are residual readiness waits, not cold action-to-ready latency. Report samples, viewport, fixture size and timing definition; timings include whichever browser automation, API and rendering boundaries are actually awaited. Compare retained DOM/canvas and request counts before/after repeated panel changes; listener counts only when directly measured. A bounded fixture cannot establish production-scale throughput, GPU/rendering performance, stable heap usage over long campaigns, or remote-network latency. Do not infer resource stability from one screenshot.

## Browser limits

Chromium covers desktop and actual emulated touch input. A Linux browser engine run does not establish native device/Safari behavior. WebKit distribution downloads were rejected by the environment network policy in the prior milestone; there is no installed usable WebKit runtime here. No bypass or Safari compatibility claim is made. Browser/display zoom and small viewport recovery are distinct checks and should be recorded explicitly.

Backend calculations, schema and geography remain outside this UI change. The user excludes unnecessary expensive simulation stress repeats for cosmetic/interface changes. Existing 10,000-turn evidence is historical baseline evidence, not a new performance result for this release candidate.

## Candidate results

Nine targeted backend/API tests passed freshly in 1.084 seconds: all five `test_v2_acceptance` cases, static asset/API handoff, private campaign access filtering, preview/commit/retry/stale handling, and pre-game/restore behavior. Backend source remains unchanged. JavaScript syntax checks and `git diff --check` also pass. The full `tests/browser_strategic.py` Chromium regression passed against the isolated demo-v2 fixture at 1280×900, 656×518 and 390×844. It checks all 16 management destinations using concrete recorded data (and the explicit empty Budget state), Galaxy/Sector/System/Planet navigation, local/campaign scope, construction, character inspection, Orders draft, preview/commit, historical read-only/live/branch return, campaign A→B→A stale responses, delayed login cancellation after logout and a held-map dialog navigation race. Authentication/campaign entry uses visible pointer controls rather than bypassing a modal with programmatic selection. Actual emulated touch opens Menu, navigates and zooms. Viewport resizing is covered. Browser display zoom and native device zoom remain unverified; map zoom is exercised.

A nondefault pan, zoom and population overlay, selected province, map image pixels and canvas identity remain equal after Economy → Construction → map. Repeated navigation does not remount the canvas. No uncaught page errors occurred.

Latest bounded performance sample:

| Measurement | Result |
| --- | --- |
| First Economy residual local-pane readiness, after click returned | 9.29 ms |
| First Construction residual local-pane readiness, after click returned | 29.25 ms |
| 24 cached programmatic transitions (eight Economy/Construction/map sequences), median / p95 | 3.47 / 8.73 ms |
| Visible DOM nodes before / after | 1,583 / 1,583 |
| Recorded API resource entries before / after | 27 / 27 |
| Post-GC CDP documents / nodes / JS event listeners before and after | 1 / 3,089 / 283, unchanged |

Warm timing starts before `HWDesktop.open()` and ends when the expected workspace title or map visibility is ready. It excludes physical pointer input and does not await a full rendered frame or chart completion. First-report timings exclude app startup and may exclude click processing. These observations support retained UI/resource behavior in this fixture, not production performance, complete heap/GPU stability or remote-network latency. Ignored local evidence: `data/strategic-candidate/metrics.json` and fresh full-frame screenshots in the same directory.
