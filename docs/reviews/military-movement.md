# Military counters and movement — 22 October 2026

This extends the aerospace instrument interface on `feature/map-desktop-shell`. It remains an interface release candidate. All movement demonstrations use isolated, fictional PostgreSQL fixtures created with supported recruitment/deployment/fleet commands. No missing cloud campaign database or cartography was recovered, no private campaign records were edited and no deployment/merge/reset was performed.

## Design and data contract

Forces is an optional, discoverable map layer. Ground forces appear on planetary maps; fleets/transport appear at system anchors in sector maps. Counters show recorded stacks, with a picker for individual records. Owned forces use Apple system blue, observed foreign forces neutral treatment, and mixed stacks remain explicitly mixed. Symbols indicate only the recorded ground/fleet/transport category. They do not imply infantry equipment, armor, unit echelon or hostile intent.

Owned in-transit forces remain anchored at their recorded origin until arrival. Solid arrow connectors show recorded endpoints, departure and arrival turns; they are not roads, physical trajectories or interpolated positions. Dotted draft and dashed validated-preview connectors are separate states. Only actions in the exact backend-previewed JSON qualify as validated; unsigned requests never inherit that state. Backend preview calculates costs, timing, resource feasibility and rule validity.

Move stages an existing `deploy_unit` or `fleet_move` action in page memory. Sources are actual owned settlements/depot records, or supported fleet reserves. An unsigned export works without GM permission. Building a full proposal uses a real protected GM packet or appends to existing valid proposal JSON, preserving allocations, narrative and unrelated actions. Invalid unsent JSON is retained. No base hash, permission, statistic or travel estimate is fabricated. Drafts clear across campaign/login/logout/history contexts; authentication tokens remain memory-only. A changed snapshot invalidates completed previews; pending preview/packet responses check their captured context and text.

The small overlay module uses current canvas transforms and recorded entity IDs. It does not remount or replace the canvas, change terrain generation or persist campaign/UI changes together. Temporary review artwork is unrelated to authoritative coordinates; counters are tested on the recorded cartography, not placed over the artwork as if it described the same geography. Character relationships and the separate character branch remain untouched.

## References actually examined

| Reference | Relevant strength / observed issue | Response and limits |
| --- | --- | --- |
| [OpenRA 2019 waypoint-overlay change](https://www.openra.net/news/playtest-20190825/) | Route visibility can be explicit rather than permanently cluttering the map. | Optional Forces layer; connectors explain existing orders. Historical implementation example, not a current-game quality comparison. |
| [OpenRA target-line discussion #16616](https://github.com/OpenRA/OpenRA/issues/16616) | Thin lines and different order meanings need readable treatment at different resolutions. | Arrowheads, separate line patterns and text summaries; phone review revealed and corrected collisions. Discussion evidence, not a reproduced OpenRA defect. |
| [OpenRA fog tracking report #22544](https://github.com/OpenRA/OpenRA/issues/22544) | Order graphics must not reveal live hidden movement. | Explicit owned-only movement fields; foreign counters use frozen observed locations. Regression mutates live hidden orders and proves projection unchanged. Report is not independently reproduced. |
| [milsymbol](https://github.com/spatialillusions/milsymbol) | Consistent symbolic grammar, scalable rendering and explicit affiliation. | A few small generic symbols suit current recorded kinds; no new dependency or claim of APP-6/MIL-STD compliance. |

No equivalent fresh Victoria 3/CK3/Stellaris image set was available for this movement milestone. Earlier reference purposes remain documented separately. This review does not establish commercial-game parity, character-relationship quality or tactical pathfinding.

## Independent critique and correction record

One fresh-context GPT-6.1 Sol medium critic used actual Chromium desktop/mobile interactions and full screenshots, keeping screenshot-only judgments separate from observed behavior. The bounded Sol high contract review checked the movement projection and later reopened only for new preview-state integration evidence.

Concrete findings retained for final verification:

- Counters covered system navigation markers: offset with leader stems so base map markers remain reachable.
- Unnamed stacked records were indistinguishable and confirmation exposed raw IDs: stable ID suffixes distinguish unnamed forces; actual record/destination/source names lead summaries, full IDs remain secondary.
- Dark Forces control contrast and short phone connector-label collisions: explicit readable control surfaces and a separate movement summary.
- Pre-game campaign switch retained previous map headings/counts: clear map identity when recorded geography is unavailable.
- Unsigned requests inherited unrelated validated preview styling: pending requests remain drafts.
- Snapshot refresh retained an old validated preview: new snapshot invalidates preview while retaining unsent JSON.
- Proposal assembly left the staged list stale: refresh staged controls; unsigned requests can be removed before assembly.

The same critic accepts the bounded movement slice with no remaining P2 findings after fresh desktop and 390×844 touch rechecks. A final phone collision between neighboring owned/observed counters required localized Sol medium escalation and a bounded Sol high placement diagnosis: deterministic screen-space rectangles now avoid other counters, visible chrome and actual canvas labels. Leaders retain authoritative anchors. Default center taps independently open the two 50×44 targets with an 8px gap; the picker is foreground and opaque. Grouping uses semantic anchor IDs, never nearby projected coordinates. A bounded scrollable picker fallback retains access if the viewport has no free counter slot; dense late-game quality is not established.

The critic observed desktop/touch movement selection, source/destination lists, staging/removal, return to map, targeting cancellation, transit wording, dark mode and pre-game replacement. It inspected supplied authenticated preview screenshots but did not independently authenticate or commit. Root's separate regression exercises those protected operations. No anonymous commercial-image comparison was performed; no parity conclusion follows. Remaining minor friction: canceling map targeting discards that composer, so restarting requires reopening Move. Small metadata and long displaced leaders on compact maps remain candidates for future refinement, with meaning carried by explicit readouts.

## Verification environment and limits

Debian 13, Python 3.12.14, PostgreSQL 17 in a local Docker QA container, Chromium 154.0.8037.57, three logical CPUs. Browser evidence uses installed Playwright and fresh disposable schemas. Screenshots/runtime JSON remain ignored under `data/`; no fixtures/databases/tokens are committed.

The 73-test Python discovery run passed 72 tests and initially failed the backup test because the host lacked `pg_dump`. Supplying PostgreSQL 17 client binaries from the QA container made the isolated backup/recovery test pass. Three new pure tests verify ground/fleet endpoint projection, arrival cleanup and foreign-order exclusion.

The required 10,000-turn persisted connected fixture passed in 273.12 seconds: 10,001 snapshots, 382,083,362 state bytes, largest state 41,896 bytes, current read 7.0 ms, history-50 read 134.2 ms. This is a bounded synthetic fixture, not production-scale map/fleet or GPU performance. No simulation rules changed.

`tests/browser_movement.py` passes real owned/observed stacks, phone separation and center taps, retained unsent/invalid/malformed JSON, player unsigned export/GM rejection, proposal field preservation, unrelated previews leaving unsigned requests DRAFT, edits during pending preview, exact GM preview/commit, ground transit, fleet map targeting by touch/cancel/reserve-source commit, historical no-Move controls, new-snapshot invalidation and selected fleet inspection through actual arrival. Example loading now assigns fresh submission IDs, correcting the inherited repeated-turn example collision. Campaign switching clears drafts/counters, and exercised workflows have no uncaught page errors.

The final `tests/browser_strategic.py` regression also passes all existing destinations, hierarchy pointer/touch navigation, settlement Economy/Construction/Map, camera/overlay/selection retention, private campaign/login/logout staleness, historical/restore, preview/commit, errors/retry, appearance preferences and actual Chromium 100/125/150/200% tab zoom. The canvas retains identity; 24 management cycles retain DOM2647, post-GC nodes5283/listeners189 and API entries47. Recorded UI action-ready times were first Economy101.3ms/Construction180.3ms, cached median8.97ms/p9513.53ms. The movement test's 24 zoom-button redraw actions averaged72.4ms including Playwright/input overhead; listeners121→121, DOM counters1531→1537, with two force buttons/one control bar retained. These final browser suites ran concurrently, so timings include contention and do not isolate render/paint/GPU cost.

Evidence is ignored under `data/movement-candidate/` (movement results and fresh full screenshots), `data/movement-release-regression/` (complete retained-interface checks) and `data/movement-collision/` (independent localized browser checks). Critic notes were retained under `data/movement-candidate/independent-critic-notes.md`; additional critic captures were produced at `/tmp/movement-critic/`. Chromium154 was tested; WebKit executable is absent, native macOS Safari and physical mobile devices remain unverified. No screen-reader/accessibility certification or production-scale force-density claim is made.

## Integration and continuation

Keep `public/military-map.js` as a presentation layer over authoritative map positions and player projections. When unrecovered cartography is integrated, replace its position inputs rather than regenerating persistent entities or changing the movement contract. Routes remain endpoints until the backend records actual paths. Large fleets, overlapping counters at dense late-game scales, operational hosting, real campaign migration and native Safari/physical-device coverage require separate evidence. Queues, multi-stop routes, automated fronts, cancel-committed movement, equipment-specific symbols and live character relationships remain outside supported mechanics.

Backend projection, guards and plan milestone: `3e97811`. Frontend delivery is documented with its commit reference in `docs/branches/map-desktop-shell.md`.
