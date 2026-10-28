# Planetary environment quality control — 28 October 2026

Scope: the map-generation interface release candidate, using fresh desktop
Chromium captures and actual UI/API interactions. Cover all six implemented
terrain presets and all implemented liquid materials, with polar ice and craters
both represented. This is nine representative profiles, not exhaustive coverage
of every seed, option combination or map scale. No commercial-game, planetary
physics, Google Earth, deployment or native Safari parity is claimed.

## Profiles and data boundaries

| Profile | Preset | Liquid | Polar ice | Geology | Fixture source |
| --- | --- | --- | --- | --- | --- |
| Water | Continental | Water | Water ice | None | Existing isolated demo |
| Lava | Barren | Lava | None | Cratered | Existing isolated demo |
| Hydrocarbon | Frozen | Hydrocarbon | Water ice | Cratered | Existing isolated demo |
| Rock with ice caps | Barren | None | Water ice | Cratered | Existing isolated demo |
| Archipelago | Archipelago | Water | Water ice | None | New isolated QA fixture |
| Oceanic | Oceanic | Water | Water ice | None | New isolated QA fixture |
| Arid | Arid | None | None | None | New isolated QA fixture |
| Dry rock | Barren | None | None | Cratered | New isolated QA fixture |
| Frozen | Frozen | None | Water ice | Cratered | New isolated QA fixture |

New fixtures live in a separate disposable PostgreSQL QA schema and loopback
preview. Existing demo/pregame records were not regenerated, overwritten or
promoted to canon. No real campaign data was recovered or invented. The browser
checks compare public state/snapshot before and after each read-only workflow.

## Flow and evidence

Evidence is current-run only, under ignored `data/environment-quality/final/PROFILE/`.
Each primary stage has full-frame1440×1024 light and dark PNGs and an accessibility
tree. Before-action DOM snapshots and `workflow.json` accompany each profile.
The first four candidates are retained in `baseline/` before the shared contrast
correction. No crops, altered terrain or generated mockups are audit evidence.

1. **Orbit and campaign identity:** recorded settlement targets, north-up cue,
   hierarchy, material legend and campaign state.
2. **Select settlement:** actual orbital landmark opens the correct province and
   recorded settlement inspector; hidden identifiers match saved records.
3. **Economy:** local identity/units remain readable; local/campaign controls expose
   correct pressed state in both directions. Unrecorded economic diagnosis and
   forecasts remain explicitly unavailable.
4. **Construction:** local/campaign navigation, all nine recorded facility IDs,
   grouped identical records and explicit zero-project state.
5. **Return to map:** exact surface camera and selected province preserved;
   backdrop remains mounted.
6. **Material/polar inspection:** actual feature selection or truthful empty
   catalogue, material identity and panel input containment; fresh polar orbit
   evidence where exercised.
7. **Pregame:** unknown resources, unavailable map controls, cleared prior context
   and truthful no-geography footer; named modal keyboard containment/Escape.

The first complete nine-profile primary matrix passed functional assertions.
Independent visual review then rejected early light captures: an unfinished globe
fade or deferred labels made them inaccurate evidence despite correct saved
selection. Those files remain in `candidate-early-captures/`. Captures now wait
beyond the known420ms transition, then fonts and two paint frames, before either
theme image. Only settled replacement screenshots are final evidence.

Per-profile health, final screenshots and interaction results follow after the
complete matrix and independent review.

## Findings and implementation

A single fresh Sol medium critic reviews the current-run evidence, without prior
acceptance verdicts or implementation discussion. Luna owns bounded changes;
localized test issues use Sol medium. No architectural rewrite is in scope.

- **Shared moderate contrast defect:** small green Construction “Complete” labels
  were faint on the light off-white reading surface. The existing green foreground
  token `#008932` against `#f8f8f4` gives4.265:1 by sRGB calculation; this is a
  sampled token comparison, not a full compliance audit. Labels now use normal
  text color with a4×4 Apple system-green square. Meaning stays explicit and the
  official accent palette is retained. Dark mode receives the same clear label.
- **Moderate selected-feature visibility defect:** the recorded lava lake anchor
  projected to(720,110.4), under the top toolbar, despite an open named inspector.
  A fresh screenshot plus `elementFromPoint` proved the obstruction. A bounded Sol
  high diagnosis traced it to the app's vertical pan clamp, which clipped a
  correct reveal movement at the physical canvas edge. Native V10 Y bounds now
  account for the existing safe HUD rectangle. The terrain edge can reach the
  reserved HUD boundary; it never leaves blank space inside the safe map area.
  Legacy camera bounds, horizontal wrapping, map renderer and geography remain
  unchanged. Existing feature/composition selection uses the corrected bounds.
  Testing the saved southern lake at minimum scale then exposed a second
  obstruction: the minimap heading covered its anchor at(952,823.3). Reveal
  candidates now avoid live DOM rectangles for inspector, minimap, force controls
  and expanded force panels. Painted canvas label reservations are deliberately
  excluded from this UI-obstacle list. The old eight-pixel selection margin is
  retained; only the pan clamp gains HUD padding.
- **Minor empty-catalog confusion:** a zero-feature surface also showed an unused
  search field and a second “no matches” sentence. Empty catalogues now show only
  the count and truthful no-bodies explanation.
- **Inherited minor visual limits:** fine muted terrain classes and tiny legend
  swatches are harder to distinguish than broad water/rock/ice classes. The
  navigation globe has smoother albedo than the cratered strategic surface.
  Pale blue selection contours have weaker contrast over bright ice, although
  they remain traceable with settlement labels and recorded inspector context.
  Those are presentation/renderer limits, not invented terrain or missing records.

## Checks and limits

The settled primary matrix passes all nine profiles: actual orbital selection,
local/campaign round trips in both reports, all facility IDs, exact map return,
truthful unknowns, keyboard dialog behavior and unchanged public fixture records.
No JavaScript page errors occurred. Ninety primary screenshots plus per-profile
pregame captures were saved; rejected early images are not final evidence.

The protected native browser suite passes after correcting the test's hard-coded
picking window to actual safe canvas bounds and explicitly choosing open water,
rather than ice covering the same recorded ocean. Diagnostics confirm expected
and selected saved feature IDs match. Actual private auth, preview/commit,
historical read-only, stale-response/logout exclusion, persistent canvas/handlers,
pointer zoom and legacy switching passed with no page errors. This run precedes
the final feature-only minimap-obstacle correction; the all-profile materials
matrix exercises that correction directly.

The same independent critic accepts all nine settled primary placements and the
corrected lava feature pair, including the previously minimap-obscured southern
anchor at minimum scale. No alternative critic was sought. Final material-matrix results follow below.

The primary screenshots and protected run precede only the final feature-reveal
obstacle-list correction. Their exercised primary navigation/auth/history paths
are unchanged by that localized callback. The final materials matrix loads the
latest source and directly tests its saved-feature placement and input behavior.
All reports record product hashes so this distinction remains inspectable.
Orbital drag captures prove a changed view, not a verified pole endpoint.
Browser timings include capture/setup and are not player latency or performance
benchmarks. No changed calculation/persistence source warrants repeating the
retained10,000-turn simulation gate. WebKit and native macOS Safari are unverified
in this pass. Keyboard/focus checks and visible label review do not establish
accessibility certification. Missing turn-zero outcomes still prevent verifying
an actual economic-problem diagnosis. Comparison with commercial reference games
was not repeated.


## Final outcome and replay

All nine primary workflows and all nine material checks pass. Latest-source
material checks verify45 canonical anchor placements across the five profiles
that record hydrographic features: northern/southern/representative chosen
anchors at regional, minimum and maximum supported detail scales. Every sampled
anchor is in the safe map rectangle and exposed through a native canvas hit;
terrain covers the entire safe rectangle. Four zero-feature profiles show a
truthful clean empty state, without invented features. Names, collapse/reopen
and inspector wheel input preserve camera/selection. No clear-selection control
exists for these selected water-body records; tests record that absence rather
than pretend to exercise one.

| Profile | Primary, both themes | Materials, both themes | Recorded features | Anchor-scale checks |
| --- | --- | --- | --- | --- |
| water | Pass | Pass | 110 | 9 |
| lava | Pass | Pass | 7 | 9 |
| hydrocarbon | Pass | Pass | 7 | 9 |
| caps | Pass | Pass | 0 | 0 |
| archipelago | Pass | Pass | 89 | 9 |
| oceanic | Pass | Pass | 45 | 9 |
| arid | Pass | Pass | 0 | 0 |
| dry-rock | Pass | Pass | 0 | 0 |
| frozen | Pass | Pass | 0 | 0 |

No exercised flow produced a page error or changed public campaign records.
The single independent Sol medium critic accepts the tested scope with no
unresolved blocking or moderate finding, after reviewing initial/corrected primary
and material pairs and relevant accessibility trees. Remaining inherited minor
limits are fine-color/legend density, weaker blue province contours on bright ice
and smoother globe relief. Acceptance does not cover every seed/geometry/option
combination, full pole endpoints, physical realism or untested responsive sizes.

Final local evidence: `data/environment-quality/final/matrix-summary.json`,
`primary-matrix.json`, `materials-matrix.json`, per-profile workflow/ARIA/PNG files,
and `gallery.html` (126 linked primary/material frames, aspect ratios preserved).
The gallery was opened in Chromium through a loopback-only HTTP preview; all126
paths and nine sections were checked, and its visible layout inspected in
`gallery-preview.png`. Direct local-file navigation was unavailable in the browser.
Screenshots remain ignored runtime artifacts, so the gallery lives in this
workspace rather than in the Git source backup.

Read-only replay against a prepared fictional profile:

```sh
WOLD_QC_BASE=http://127.0.0.1:4203 WOLD_QC_CAMPAIGN=material-lava \
WOLD_QC_OUT=data/environment-quality/replay-lava \
.venv/bin/python tests/browser_quality_control.py
WOLD_QC_BASE=http://127.0.0.1:4203 WOLD_QC_CAMPAIGN=material-lava \
WOLD_QC_OUT=data/environment-quality/replay-lava \
.venv/bin/python tests/browser_environment_materials.py
```

Added profiles use separate loopback4205 and `environment-PROFILE` IDs; existing
profiles use4203 and `material-PROFILE`. Session-only QA connection/schema context
is under ignored `/workspace/scratch/environment-qa-context.json`. Do not treat
these fixtures as deployment or overwrite missing real campaign state with them.

Performance observations: Linux6.18.55, two-CPU quota, Chromium154.0.8037.57,
1440×1024. Settled primary whole-test wall times15.87–29.58s and material times
24.58–32.86s include browser startup, settling, assertions and many screenshots.
They are automation costs, not game action latency or rendering benchmarks.
Protected switching retained one canvas and stable input handlers. No production
performance claim follows. Orbital projection/seam/pole/resource and landmark
Node checks, JavaScript/Python syntax and whitespace checks pass. All14 frozen
backend files and map/sphere/landmark modules remain unchanged. Retained10,000-turn
simulation results apply; no UI-only simulation rerun was warranted. WebKit and
native macOS Safari remain unverified in this pass.

Delivery references follow the implementation commit. This is an interface
release candidate; no merge, deployment or operational backup/recovery
certification was performed.
