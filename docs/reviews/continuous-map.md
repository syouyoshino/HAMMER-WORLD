# Continuous map navigation

Branch: `map-generation`. This milestone addresses the exposed rectangular
terrain image and the difference between dragging a small image and navigating
a larger saved map. Desktop is the accepted viewport scope.

## Baseline and architectural decision

Actual Chromium interaction on the six-preset build confirmed that mouse drag
already moved the map, but exposed a flat backing around a finite 64×40 image.
Fresh full-frame baseline captures are in ignored `data/continuous-map/`.

A bounded GPT-6.1 Sol high review approved an opt-in `planet-v5` surface with
128×80 saved cells and forty 16×16 provinces. Existing generator versions and
persisted snapshots are not converted. Province IDs retain their format/order
within newly created worlds; this does not imply geographical identity between
versions. No schema migration or numerical/resource/movement rule change is
part of this work.

Terrain must be generated and persisted by the backend. The client must not
invent terrain beyond a saved extent, copy edge cells, tile a regional map or
infer hidden geography. Whole-planet survey filtering remains authoritative;
the application has no partial planetary reconnaissance model.

The main camera covers the map canvas and is bounded by the real saved extent.
Pointer zoom uses the inverse world point under the cursor. A full-extent
overview provides orientation; Recenter is separate from changing zoom.
Labels, selection, military anchors and drawing use the same projection.

East–west wrapping is deferred until generation, climate and drainage support
the seam. This is a larger finite planetary chart, not a spherical simulation.
No new wave animation, terrain engine or simulated reconnaissance was added.

## Independent backend review

GPT-6.1 Sol high found no critical or major backend defect in its final bounded
review. It independently compared full private states and player projections
against `be19367` for V1–V4 across three seeds per version, with exact equality.
All six V5 presets across six seeds passed state validation and rectangle-based
tile projection checks. Hidden/detected planetary geography remained excluded,
and private seed/configuration data remained absent from the player projection.

The review identified a minor missing negative-origin check in standalone V5
surface validation; Store already rejected it before persistence. The explicit
surface check was added before freezing backend source for the long-run test.
The review did not independently exercise PostgreSQL restore or the long-run
fixture; those are separate verification gates.

## Verification and visual review

The first candidate passed the new desktop browser script across all six V5
presets and both styles: full canvas coverage, inverse pointer-zoom invariance,
drag to four chart limits, overview pointer/keyboard navigation, Forge → local
Economy → Map camera/selection retention, desktop resize and unchanged snapshot
hashes. No uncaught JavaScript errors occurred in those paths.

Broader legacy testing caught two real regressions: cover zoom displayed an
aspect-dependent114% minimum rather than100%, and safe-area filtering removed
a legacy holding's label beneath persistent chrome. Both were corrected in a
bounded Sol medium implementation escalation and the failing suites rerun.
Cover-relative zoom now spans100–500%; V5 opens at200%. Stable cached recorded
land anchors feed labels, military anchors and Recenter. Holding labels can
displace into the clear area with leaders rather than disappearing under UI.

Python discovery exercised93 tests in295.099s.92 passed initially; the backup
test could not find `pg_dump`. That test subsequently passed in1.544s with the
existing QA `pg_dump`/`pg_restore` wrappers on PATH. This includes the new V5
history/restore, far-province deployment, projection and real CLI tests. The
new tests do not depend on ignored screenshots or runtime fixtures.

The final committed navigation script also verifies every overlay's Forge
label, 100% legacy holding access, control/label non-overlap at1280×720 and
1920×1080, stable canvas identity and unchanged map/window handler counts.
Final delivery rerun: PASS, with no page errors. `browser_planet_presets.py`,
`browser_cartography.py` and the broad `browser_strategic.py` passed as well.
The latter exercises actual Chromium browser zoom100/125/150/200%, hierarchy,
management context, authentication/stale-request handling and historical views.
Its24 warm management cycles retained2656 DOM nodes,193 JS listeners and47 API
resources, with the original canvas retained. Older responsive checks in that
suite are supplementary; this milestone's acceptance is desktop only.

## Independent visual and interaction outcome

A fresh GPT-6.1 Sol medium critic first examined anonymous full-frame A/B
screenshots without source or implementation discussion. It found stronger
spatial continuity and orientation in the continuous chart, with moderate
confidence: terrain samples and map scales differed, so this was not a
pixel-equivalent or commercial-game comparison. These are actual application
captures, not generated concept art. No new commercial reference was examined
for this narrowly scoped navigation correction.

The same critic then used the actual application. Its first findings confirmed
the major100% label-access problem, unclear zoom percentages and inspector
obstruction of the minimap. The corrected candidate recovered labels, normalized
percentages, and positioned the minimap beside the inspector, retaining that
clear position after collapse. Captions and navigation hints use11px text.

Final independent verdict: **desktop map navigation accepted, with no unresolved
major or critical finding**. The reviewer independently switched arid →
archipelago → arid, waited for actual map readiness, selected Population and
Forge, completed Economy → Construction → Map, and retained Province01,
Population, zoom and visual camera. Pan/wheel, Recenter at unchanged zoom,
100% displaced-label selection, Dark/Light and1280×720 were exercised. Input
inside the inspector did not pan/zoom the map; no captured page errors occurred.

A remaining minor Forces/Province04 collision was subsequently fixed by
including the measured Forces control in planetary label and military obstacles.
A matched1280×720 Population capture and the final navigation regression verify
no overlap. This last correction received localized QA, not another full
independent workflow review. The accepted review's remaining minor points are
faint boundaries on light/frozen terrain and peripheral navigation instructions;
the explicit Provinces overlay provides stronger boundaries, and grab cursors,
labeled zoom/Recenter and the overview provide visible navigation controls.

Evidence: ignored `data/continuous-map/critic/final/`, regional captures,
`navigation-metrics.json`, `preset-regression/metrics.json`,
`v3-regression/metrics.json` and the broad legacy-regression captures/log.

## Performance and long-run persistence

Environment: shared Linux, three logical CPUs, Python3.12, PostgreSQL17 and
system Chromium154.0.8037.57. Browser and renderer samples ran alongside QA
work; they do not establish production-scale throughput or frame rate.

- Raster source remains1536×960 per style, including V5. Weak-reference caches
  index immutable geography once rather than filtering every tile for every
  province each redraw. No new renderer dependency or GPU engine was added.
- One cold direct renderer sample per preset/style measured412–1078ms; ten
  synchronous warm draws averaged2.0–14.3ms. These omit input, network, military
  DOM and compositing. Before indexing, warm samples ranged8.1–80.5ms under a
  different concurrent QA load; do not treat the ranges as a controlled speedup.
- Final browser campaign-to-first-draw samples are in `navigation-metrics.json`;
  these include network/projection and initial draw, unlike the direct timings.
- Mixed V5 arid/archipelago/oceanic/frozen fixture: **10,000 turns PASS in2529.31s**,
  10,001 source snapshots, population1199, largest serialized state958,198 bytes.
  Summed source-state JSON was7,496,344,717 bytes; this is not physical database
  disk usage. Checkpoint history, conservation and exact restore assertions passed.
- Current-state read60.1ms;50-entry history read3980.1ms on this fixture. Persisting
  full immutable surface arrays in every snapshot materially increases history
  and storage cost. A separately reviewed persistence migration to reference
  immutable geography is a future integration concern, not silently included here.

The ignored `data/verification/stress-v5-navigation.json` records all backend
source hashes, verified equal to final delivery source. Test schemas were
disposable; no campaign database was overwritten.

## Use, integration and limits

```sh
python -m app.cli init-v2 --campaign-id new-chart --planet-generator planet-v5 \
  --preset continental --planet-preset new-chart-planet-ash=barren
```

Creation stays in the existing CLI/Store path; there is no live preset switch or
new browser write endpoint. The default generator remains V1. V5 has distinct
terrain samples, not an enlarged copy of V4. Existing campaigns receive the
bounded camera/overview improvements without geography conversion. Preserve
the V5 dimension/configuration/province lookup when integrating unrecovered
cartography; legacy64×40 projection retains its compatibility path. Keep the
character-relationships branch separate and use the existing management entry.

Chromium is verified; bundled WebKit and native macOS Safari were unavailable
and remain unverified. No mobile acceptance or production operational-security
certification is claimed. Remaining boundaries: finite planar charts, rectangular
province topology, stylized geological relief, whole-planet survey visibility,
and full-snapshot history cost. Wrapping, spherical coverage, waves, partial
reconnaissance, canonical data recovery and production persistence redesign
remain separate work. No merge, deployment or recovered-cloud-data claim.

This is an **interface release candidate**. Implementation: `c488e3f`.
Delivery and continuation references are recorded in
`docs/branches/map-generation.md`.
