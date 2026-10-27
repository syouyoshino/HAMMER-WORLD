# Desktop quality control — 27 October 2026

Scope: current `map-generation` interface release candidate. Audit the actual
campaign → orbital settlement → Economy → Construction → map journey, including
empty/pregame states. No terrain, generation, numerical, persistence or security
architecture change. Fictional local fixtures are not recovered campaign records.

## Current-run evidence and step health

Fresh full-frame Chromium captures at 1440×1024 were taken before implementation
in ignored `data/quality-control/current/`. The coordinator inspected each saved
image. Corrected captures and before/after DOM snapshots are in
`data/quality-control/final/`; intermediate failures remain in `candidate-1`,
`candidate-2-before-label-cleanup` and `candidate-2` rather than being discarded.

1. **Campaign access — healthy.** No selected campaign means no example planet,
   grid or idle loading indicator. The named modal starts on a visible control.
   Evidence: `final/00-campaign-access.png`.
2. **Orbit — healthy within renderer limits.** Recorded settlement targets and
   hierarchy remain available. Survey dimensions are supplementary tooltip data.
   Evidence: `final/01-orbit.png`.
3. **Settlement inspection — healthy.** Stable neutral reading surface, recorded
   identity and explicit housing/unrest/stock units. Evidence: `final/02-settlement.png`.
4. **Economy — healthy for available records; diagnosis unverified.** Settlement
   identity persists in the workspace header. Local/campaign state is visible and
   exposed through correct pressed semantics. No invented economic problem or
   forecast fills missing turn-zero outcome data. Evidence:
   `final/03-economy.png`, `final/08-scope-campaign.png` and corresponding DOM.
5. **Construction — healthy.** Projects have an explicit empty state. Identical
   facilities are grouped only when every non-ID field agrees; all IDs remain in
   disclosures. Evidence: `final/04-construction.png`.
6. **Return to map — healthy.** Selection and camera survive management navigation.
   Evidence: `final/05-return-map.png` plus browser assertions.
7. **Campaign switch — healthy in exercised fixtures.** New geography/legend
   replaces the previous context. Evidence: `final/06-campaign-switch.png`.
8. **Pregame — healthy.** Unknown values stay unknown; unavailable map controls
   are disabled and stale survey dimensions cleared. Final critic caught one
   residual selection prompt; corrected to “This campaign has no recorded
   geography.” Evidence: `final/07-pregame.png` is the pre-copy-fix capture;
   regression capture records the final copy.

## Findings, correction and independent review

A fresh GPT-6.1 Sol medium critic initially examined only this run's anonymous
application captures and DOM, without prior acceptance verdicts or implementation
history. This was a single-product audit, not a blind commercial comparison.

| Finding | Priority | Implemented correction |
| --- | --- | --- |
| Example planet/grid and idle loading before selecting a campaign | Medium | Truthful initial markup, full initial render, unavailable-control guards |
| Broad terrain bands behind small inspector/report text | Medium | Opaque inspector content and nearly opaque report reading surfaces; translucent chrome retained |
| Active related view/scope absent from accessible state | Medium | Pressed semantics, updated on every local/campaign activation |
| Unnamed campaign modal and uncertain initial focus | Medium | Heading association, focusable container and first visible enabled control |
| Workspace loses visible settlement identity | Low–medium | Persistent settlement/province/planet scope; campaign scope explicitly retains selection |
| Unclear local units and weak project empty state | Low | Known rule-backed units, explicit projects section, grouped identical facilities preserving IDs |
| Selected pregame campaign still receives select-campaign prompt | Low | Context-specific no-geography footer |
| Breadcrumb masks Recenter label at200% desktop tab zoom | Medium in that viewport | Place breadcrumb below the fourth narrow-toolbar row; verify center hit target |

Luna implemented the bounded first candidate. Actual rechecking exposed incomplete
inspector coverage and stale pressed state after scope changes; one localized Sol
medium escalation corrected those behaviors. The same independent critic inspected
all nine final full-frame captures and relevant DOM and **accepted the scoped
quality pass**. No alternate critic was sought. The remaining centered-workspace
occlusion is an accepted tradeoff: textual context remains and Return to map
restores the exact camera/selection. No docking rewrite was justified.

This review does not newly compare Victoria 3, CK3 or Stellaris, nor certify parity
with them. Prior reference examination remains recorded in the branch and earlier
review documents. No fresh equivalent late-game/reference footage was available
for this bounded pass. Character relationships remain outside this branch/task.

## Verification

- Current protected `tests/browser_planet_detail.py` passes against disposable
  PostgreSQL fixtures using a source-verified native fixture cache: real private
  authentication, native selections, Economy/Construction return, pointer zoom,
  canonical feature selection, delayed asset rejection on campaign switch/logout,
  supported movement preview/commit and historical read-only. No page errors;
  no browser-storage tokens. Fixture records remain unchanged before supported
  commit; this does not write the local preview campaign.
- `node --check` passes for both changed JavaScript modules. Orbital projection,
  inverse picking, seam/pole/resource and settlement-label contract checks pass.
- All 14 backend hashes match the native-scale freeze; native map, sphere and
  annotation module hashes match the accepted predecessor. No numeric/persistence
  source changed, so the retained 10,000-turn simulation gate was not repeated.
- Chromium154.0.8037.57 actual tab zoom100/125/150/200% passes existing control,
  hierarchy, feature selection and Economy-return checks at physical1280×960 and
  1920×1280. Inspecting the1280/200% screenshot nevertheless exposed breadcrumb
  overlap over Recenter. Narrow short-height offsets are corrected and a targeted
  label-center hit test is added to the final recheck. The earlier geometry-only
  gate is not presented as sufficient visual evidence.
- Twenty warmed Economy/map cycles on a fictional rocky fixture retain one map
  canvas, two landmark nodes, one document,1302 DOM nodes and130 event listeners.
  Measured annotation-layout mean0.045ms/max0.200ms over44 calls. Linux6.18.55,
  two-CPU cgroup quota,1440×1024 Chromium154; these measure annotation work only,
  not frame time, terrain throughput or production-scale performance. Evidence:
  ignored `data/quality-control/resources/metrics.json`. An earlier overly strict
  exact-node-equality assertion rejected a1303→1302 decrease; correcting the
  harness to reject growth produced the stable recheck above. These measurements
  precede the isolated narrow-short-height CSS offset correction.
- Current WebKit and native macOS Safari remain unverified. All current checks
  use real Chromium; historical WebKit results are not reused as current coverage.

- The corrected1280/200% capture passes the additional Recenter-center hit test
  and geometric breadcrumb separation. The same independent critic accepts this
  corrected zoom state. It retains a low-severity extreme-viewport limitation:
  Forces overlaps the minimap heading and the minimap covers part of the footer
  instructions. Normal1440×1024 captures do not show this collision. Evidence:
  `data/quality-control/zoom-fixed-1280/browser-zoom-200.png` and `metrics.json`.

- Final `tests/browser_quality_control.py` passes on the final frozen product
  source: named modal/visible focus, Tab/Shift+Tab containment and Escape return;
  truthful startup/pregame map state; actual orbital settlement selection; both
  scope directions in Economy/Construction with pressed state matching visible
  content; all nine recorded facility IDs preserved by grouping; explicit empty
  projects; exact camera/selection return; unchanged demo and pregame public
  records. No page errors. Light and dark Economy screenshots and the corrected
  pregame footer were inspected by the coordinator. Evidence:
  `data/quality-control/regression/workflow.json`, `economy-light.png`,
  `economy-dark.png`, `16-pregame-empty-map.png`.

Reproduce the read-only focused test against explicitly prepared local V10
fixtures (the defaults refer to this session's fictional preview):

```sh
WOLD_QC_BASE=http://127.0.0.1:4203 \
WOLD_QC_CAMPAIGN=material-water WOLD_QC_PREGAME=campaign \
.venv/bin/python tests/browser_quality_control.py
```

The harness initially confused synthetic geometry and canonical planet IDs, then
queried labels before native detail loaded and read hidden disclosure IDs using
`innerText`. Matching persisted province IDs, awaiting actual visible landmarks
and reading disclosure `textContent` resolved the test issues without product or
record changes. The final test intentionally requires the configured fixture's
visible settlement landmark instead of creating a second picking algorithm.

## Limits and continuation

- This is an interface release candidate, not a verified deployment or operations
  release. No merge, deployment, data reset or recovery claim follows.
- The turn-zero fixture lacks budget/outcome data needed to verify identifying a
  main economic problem. Missing information is stated honestly.
- The centered management workspace obscures terrain while open. Persistent
  settlement identity and exact return are verified; comparison pinning is not
  newly assessed.
- Natural rocky terrain remains sparse and the globe uses reconstructed albedo,
  not physical spherical height/LOD. Polar/chart distortion is inherited. Map
  rendering and immutable detail assets are untouched in this pass.
- Current Chromium coverage does not establish native macOS Safari or WebKit
  coverage. No accessibility compliance certification or measured contrast-ratio
  audit was conducted.
- Preserve the frozen backend and terrain modules when integrating unrecovered
  cartography. All changes here are UI presentation/state semantics and a focused
  browser regression; no new campaign schema or data dependency.
