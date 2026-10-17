# Map desktop shell continuation

Branch: `feature/map-desktop-shell`, based on committed `work` at `e8198b200ec92db3c33d4d797ca8034f1de96529`. Implementation milestone: `c488aa1` (Add map-first Win95 desktop shell with retained floating windows).

This is an independent implementation from the committed baseline. No files or campaign records from the unavailable original cloud task were recovered. Do not merge automatically. No deployment is authorized by this task.

## Integration approach

A bounded GPT-6.1 Sol high review approved a thin desktop shell around existing DOM screens and the existing live map. The canvas must remain mounted while windows open, close, move, minimize or clear. Map controls belong in a floating Cartography window. The shell replaces the baseline's transform-only pane dragging, without changing terrain generation, saved coordinates or simulation rules.

Each management screen needs its own retained container and request generation. Campaign/login context invalidation must reject stale successes and failures, including A → B → A. Window operations must not rerender the Orders form or discard proposal text. Browser preferences contain only clamped window geometry and launcher pin preference; tokens and campaign data remain outside persistent browser storage.

## Cartography and related-branch integration

The shared integration points are `public/index.html`, the render/navigation/authentication boundaries in `public/app.js`, and scoped desktop styles. The map renderer and backend geography are retained. Future unrecovered cartography changes should preserve the canvas node and direct map state, integrating controls with the Cartography window rather than remounting the map. Screen registration is the intended extension point for a future character-relationships screen; this branch does not modify or depend on `feature/character-relationships`.

## Validation and review

The Chromium shell workflow passed with no JavaScript page errors. Coverage includes explicit selection followed by automatic chooser dismissal, edge reveal/dismissal, four API-backed map levels, map-gesture suppression, drag/resize/maximize, minimize/restore, retained Orders draft, distinct Industry/Fleet windows, all 15 management destinations and entity inspection, Clear desktop preservation, stale A → B → A response rejection, pending-login cancellation, turn preview/commit, historical inspect/live/branch restoration, retained History comparison, independent Economy/History charts, and 390×844 viewport recovery. Actual touchscreen input opened HW while unpinned, waited 700 ms and opened a labelled command. Additional regressions verified Escape/Clear cancellation of a pending reveal, real titlebar dragging and resize-grip holds at the left edge without launcher activation, and actual UI pin preference writes. UI storage was limited to geometry/pin keys and reload required fresh authentication/selection.

Nine focused backend/API tests passed in 1.121 seconds: all five v2 acceptance cases plus static/API handoff, private campaign access, preview/commit/retry/stale and pre-game/restore cases. JavaScript syntax checks and `git diff --check` passed.

An independent fresh GPT-6.1 Sol medium review inspected the five actual screenshots and bounded source. It found mobile launcher labels suppressed by legacy CSS, missing utility-window commands, comparison-range loss on History reopen, and no active-window visual indication. The builder also identified a blank retained History window after historical selection. These were corrected, and chart source selection was decoupled from window focus. A localized Sol medium escalation completed touch/timing diagnostics and corrected a test that expected “Economy ledger” where the actual launcher label is “Economy”.

The same independent reviewer inspected materially updated screenshots/source and confirmed the prior concrete findings corrected, with no residual material defect in that bounded review. It assessed the Win95 presentation, compact launcher, window hierarchy and map dominance as coherent. Generic inherited pictograms remain a minor visual-polish limitation. This is an explicit visual assessment, separate from functional test success.

Earlier results in `docs/checkpoint.md` describe the committed baseline, not this branch.

WebKit installation was attempted in this environment but its distribution hosts returned HTTP 403 `Domain forbidden`. Chromium is installed. Linux WebKit, if later available, still does not establish native macOS Safari compatibility.

The user explicitly excludes repeated expensive simulation stress tests for UI-only work without a demonstrated risk. Backend simulation, migrations and saved geography are outside this branch's scope; the baseline's existing 10,000-turn results are not claimed as a fresh run.

## Source and continuation

Implementation lives in `public/desktop-shell.js` and `public/desktop-shell.css`, with two asset includes in `public/index.html` and focused integration changes in `public/app.js`. Existing backend, map drawing/generation, simulation and migration files are unchanged. `HWDesktop.createWindow` / the singleton registry permit later screen integration. The legacy pane drag handlers were replaced by shell lifecycle handling.

Run `python tests/browser_desktop.py` with `WOLD_TEST_DATABASE_URL` configured to an isolated PostgreSQL test database. See `docs/testing.md`. The old dashboard browser scripts retain their old always-visible navigation and automatic-demo assumptions and are superseded for shell acceptance on this branch. The final clean-map artifact was inspected and shows only the live map and HW button. Fresh actual browser screenshots are ignored artifacts at `data/previews/chromium-desktop-{map,launcher,multiple-windows,inspector,mobile}.png`.

Next steps: review the branch diff before any manual integration; reconcile independently recovered cartography changes at the boundaries above; verify WebKit/native Safari when available. No automatic merge or deployment was performed. No live Drive sync, real campaign initialization or recovery of unavailable workspace files is claimed.

Final browser output:

```json
{"browser":"chromium","desktop_shell":"PASS","map_levels":4,"turn_history":"PASS","auth_context":"PASS","page_errors":[]}
```
