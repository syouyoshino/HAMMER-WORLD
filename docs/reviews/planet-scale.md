# Saved planetary detail and scale

Status: scoped interface release candidate accepted by independent continuation
review. Backend milestone `128a45a` is pushed; final frontend verification and
delivery references are recorded below. Old negative findings remain in this log.

The user identified a regional-board sense of scale and requested a Google
Earth-like planetary view. Fresh baseline browser captures are under ignored
`data/hydrography-pass/scale-baseline/`: 1440×1024 Chromium, actual128×80 saved
geography at200% with broad stepped coasts, biome slabs and axial river paths.
The existing1536×960 raster and5× zoom ceiling do not add geographic information.
There is no recorded physical planet radius or cartographic unit in kilometres;
the hierarchy's relative body radius cannot supply one.

## Initial bounded architecture (superseded after critique)

Sol high reviewed generation, camera/rendering and persistence. The completed
V9 gate measured9,538,588,921 bytes of snapshot JSON over10,001 snapshots and a
10,021.3ms50-record history read. Simply multiplying every saved geography's
resolution16× would multiply repeated immutable data. The selected first slice
is opt-inV10 composition: unchangedV9 strategic128×80 provinces and numerical
rules plus one genuinely saved512×320 natural-detail asset per planet. This is
finer cartography over a coarse strategic simulation; it is not a spherical
renderer, a new physical scale, or Google Earth fidelity.

Snapshots contain only a strict versioned checksum/dimensions/byte-length
manifest. Assets live in a separate immutable PostgreSQL table and are created
atomically with a new campaign. Existing maps and histories are never converted.
Loading does not regenerate geography. Detail retrieval is bound to an authorized
campaign, snapshot and surveyed planet, rather than an exposed digest endpoint.
Restoration preserves entity IDs and asset references. PostgreSQL schema backups
include the assets; versioned public archives include only surveyed assets.
The client must invalidate pending work on campaign/login/history changes.

Natural coast refinement must preserve province eligibility and canonical anchor
halos, associate water with existing recorded features and keep new inlets
connected to recorded water. Rivers retain their recorded identities/corridors.
Dry presets cannot acquire green vegetation or water through detail generation.
Lake materials and polar ice remain independently chosen recorded layers.
No physical area, travel, hazard or resource rules are inferred from finer pixels.

## References actually examined

- [Cesium quadtree source](https://github.com/CesiumGS/cesium/blob/ad366f071293b28bdf330c822965b8bd0bdeb781/packages/engine/Source/Scene/QuadtreePrimitive.js),
  and `GlobeSurfaceTileProvider.js`, examined25October2026. The source projects
  geometric error against distance/frustum pixel size and bounds/prioritizes
  loading. The relevant strength is real data behind closer views. No Cesium
  code/runtime/dependency is incorporated; this first asset is not a quadtree.
- [Google Earth Enterprise README](https://github.com/google/earthenterprise/blob/893f6b470673e2bad4cacdd8eec5ad1f179b6249/README.md):
  imagery/vector/terrain ingestion, serving and viewing are separate; the
  repository explicitly does not provide Google Earth imagery and is archived.
  Google Earth live interaction and proprietary imagery were not examined.
- Eleanor Lutz's Moon/Mars topographic pair and Moon label-placement process,
  actually inspected in the [previous review](hydrography-names.md), provide
  terrain/annotation references. They are authored topographic charts, not
  optical photographs or comparable interactive zoom evidence. Research-only
  artwork remains ignored; no artwork or data is incorporated.

The network policy excludes NASA/USGS/IAU hosts. No new optical-photo accuracy or
commercial-game parity claim follows from these references. Browser comparisons,
independent findings, corrections and performance observations will be appended
after the candidate is exercised.

## Initial independent findings and revision

A fresh Sol medium critic inspected anonymous full-frame A/B images at the same
1440×1024 viewport,200% camera and fixture load, plus a separately identified
498% close view. No implementation discussion, origins, previous verdict or
desired winner was supplied. The critic preferred A (the existing V9 treatment)
to B (the first detail candidate). Initial high findings: no dependable scale
cue; square lake/staircase shore/orthogonal river ladders; effectively absent
relief. Medium findings: ambiguous settlement anchoring and feature hierarchy;
chrome concentrated around sparse geography; broad blur/shore halos. The close
view exposed enlarged source blocks and unclear province-chip extent. These
were still-only findings; no interaction quality was inferred.

The first detail raster was rejected. Sol medium reused the existing smooth
terrain/material/crater compositor on actual saved fine fields, suppressed the
coarse river overlay, aligned fine river selection/labels and cached fine body
boundaries. Root added truthful dimensionless viewport/world-width context and
removed new technical sample/version readouts from the ordinary map flow.

An internal capture of that renderer repair, still using the earlier saved
asset, showed the same coarse shoreline stairs with small sawteeth. Root asked
Sol high for a bounded diagnosis rather than another cosmetic pass. The initial
one-sided inlet contract mathematically retained the coarse silhouette. The
approved correction permits a fine shore on both sides of a coarse cell edge
for new V10 planets only, preserving coarse land/ocean centre cores, land-eligible
provinces, anchor halos and connected recorded water identities. Saved fine
relative elevation plus bounded periodic variation determines the new shore.
It is finer canonical shoreline geometry around coarse strategic samples, not
an independently simulated planet at every scale. Existing bodies must neither
split nor merge; added fine land must attach to an existing land centre.
Fine inverse picking uses saved province rectangles even where a finer shore
adds land inside an originally ocean-classified parent cell. Commands continue
to use canonical province IDs, never fine/display-copy coordinates.

The initial Luna generator also failed a real dry-preset creation check because
its new validator rejected an already recorded terrain class. A localized Sol
medium correction fixed that mismatch, feature-owner priority, false river
connections, anchor routing, material edge refinement and strict projections.
These failures and the negative initial verdict remain part of the record.
Corrected candidate acceptance and final persisted-turn evidence remain pending.

## Second independent rejection and fine-first revision

The SAME critic reviewed seven fresh candidate3 full frames (water regional,
close and overview, plus lava, hydrocarbon and cap views). It accepted improved
relative world coverage and some water/crater presentation, but retained high
findings: enlarged grid-shaped biome/polar/lake outlines, diagrammatic straight
river trunks and ticks, weak connected relief, and sparse waterless-world
landmarks. It explicitly rejected texture/blur/zoom alone as satisfying the
requested geographic feeling. `DETAILED PLANETARY SURVEY` overclaimed the result.
No new critic was sought and no interaction acceptance was inferred.

After two substantive visual revisions failed the same major geometry issue,
root requested bounded Sol high architectural diagnosis. The active revised
contract is fine-FIRST generation for NEW V10 worlds: canonical natural height,
terrain, drainage, materials, hydrographic names/courses and actual province
anchors live in the immutable detail asset. Derive compact128×80 strategic
summaries and forty province IDs from that natural world at creation. Do not
force new geography into V9's pre-existing silhouettes or drainage corridors.
Existing V1–V9 generation, saves, API outputs and historical checks remain exact.

The new `planet-detail-v2` asset carries fine arrays, compact named-feature
metadata, full shared river courses and recorded fine province anchor cells.
V10 turn snapshots contain only strategic terrain/provinces, strict surface
metadata and the manifest; no fine climate/drainage/catalog arrays. The selected
surveyed asset supplies map inspection after loading. Camera, settlement and
force markers use recorded fine anchors; movement still commits province IDs.
This supersedes the earlier additive/two-sided V9-refinement proposal, which is
retained above as the rejected design history. Final resolution/size bounds,
actual browser acceptance and persisted-turn results are still pending.

## Frozen native backend and functional gates

The final generator uses canonical1024×640 `planet-detail-v2` assets with an8MiB
bound. Actual corrected sample:23.762s,5,273,879 canonical UTF8 bytes,182MiB peak
RSS (Python process measurement, shared Linux2-CPU environment). Final backend
SHA256 includes planet_detail`906165ce90c09dd47ffec6e7a7fc101aa0664258f91c16672433b63d98e16f4d`.
All14 app hashes remain frozen in ignored`data/planet-scale/backend-freeze.json`.

Full147-test Python suite passed1144.544s under concurrent fixture generation;
V1–V8 retain240 exact private/public baseline hashes and V9 retains24 versus
committed`feaf766`. Actual protected Chromium154 native browser passes saved
feature selection/search, default settlement orientation, economy/construction
return, pointer zoom, repeated campaign switching and stable input/canvas, real
fine-map province targeting/PREVIEW/COMMIT, historical read-only behavior and
actual late authorized assets discarded after campaign switch and logout. No
page errors or persisted tokens. UI-only reruns use a source/creation-option
verified cache of previously generated fictional fixtures; API/SQL/turn writes
remain real. No production/private campaign records are involved.

The final10,000-turn persisted fixture passed459.36s:10,001 snapshots; population
1199 under the fixture's conservation/loss rules; exact historical checkpoints
and independent restoration; unchanged geography and four immutable assets
through live/history/branch checks. Snapshot JSON sum713,976,548B; asset bytes
20,906,145B; largest state75,232B. Current read12.0ms/history50 290.1ms. This is
not disk usage. The older V9 fixture measured9,538,588,921 snapshot-JSON bytes,
5450.49s and10,021.3ms history50 on a different QA service/cache/load context.
V10's structural reduction is measurable; a controlled production speedup or
production-scale capacity is not claimed.

Ignored evidence:`data/planet-scale/{stress-v10,legacy-verification,
v9-verification,native-backend-verification,native-generation-quality-verification}.json`,
`browser-final/workflow.json`; logs under`/workspace/scratch/native-*.log`.

## Observed inherited startup concurrency failure

A QA fixture writer overlapped uvicorn's inherited schema initializer. PostgreSQL
reported a lock inversion between campaigns and snapshots while initialization
executed `ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaign_current_snapshot_fk`.
Sol high checked the server lock log: new asset-table DDL had not been reached.
Fine generation inside creation extends the overlap window, but the initializer
lock-order defect predates this branch. The failed fixture transaction rolled
back completely: no failed campaign/head, orphan asset or orphan outbox job; the
existing water snapshot and asset still verify. Setup was serialized after
readiness. This is an observed operational limitation, not an unverified claim
or a data-reset workaround. A later dedicated concurrency change should run
versioned migrations before admitting writers; initializer-only advisory locking
would not coordinate ordinary writers. No production/concurrent-migration
certification is part of this interface candidate.

## Clarified orbital workflow — 27 October 2026

The user selected “Globe to surface: orbit a planet, then smoothly zoom into
strategic terrain.” This supersedes flat magnification as the camera acceptance
criterion. A bounded Sol high review selected one offscreen WebGL sphere,
composited into the existing persistent map canvas, using the same recorded
terrain and overlays. Orbit navigation must not enter planar targeting or picking
paths. A focus-preserving projection dissolve leads into the existing strategic
surface; this is not exact geometric unfolding or Google Earth imagery.
Failure to initialize WebGL must retain the working surface. Legacy bounded
charts, campaign authority, simulation rules and persisted geography remain intact.

Fresh independent review of the strengthened dry lighting still rejected
regular ladder/crosshatch artifacts and hard embossed ribbons (HIGH), and ice
highlight washout. Actual feature search/selection/material inspection passed
with no observed page errors; water retained its prior scoped acceptance.
Evidence: ignored `data/planet-scale/final-dry-review/`, all four fictional
material families, both cartographic styles, both interface themes, regional
and close scales. The previous critic process was unavailable after environment
restart; the replacement received the unresolved findings and did not erase them.

After two revisions a bounded Sol high diagnosis separated quantized lighting
artifacts from actual folded ridges in the immutable height field. The approved
correction filters background lighting normals at two native sample scales and
preserves separate analytic crater normals. Raw elevations, material boundaries,
hydrography and picking remain authoritative. Broad folded ridge structure is
a generator limitation; filtering must not invent a different landscape.

## Follow-up candidate findings

Filtered background normals resolved the major dry crosshatch/ladder defect in
fresh stable flat captures. The independent critic accepted dry/caps relief with
limits: broad folded loops and albedo ribbons remain medium fictional-generator
limitations. A remaining HIGH frozen-ground/ice washout prompted a native-only
blue-gray palette and fuller saved lighting range; final reassessment is pending.

The first actual globe candidate rotated, descended on terrain click, returned
with the same geographic focus, retained overlays and management context, and
fell back on context loss without page errors. It was rejected for HIGH stale
planar hover information and polar fan artifacts. Source review additionally
found flat-only zoom/recenter controls and stale force markers. Sol medium's
localized fixes isolate orbit interaction, share a safe projection viewport,
clear planar force positions, descend before targeting, and retain a working
surface when WebGL is absent. These findings are not hidden by the passing
basic workflow. A final zoom handoff must respect available native samples.

One earlier performance supplement completed its interactions and20 cycles,
but app source hashes differed before/after; it is not final source verification.
It showed one lazy two-node addition, then stable DOM/listeners from10to20 cycles,
and a persistent map canvas. A corrected final run will warm the workspace
before its baseline and retain exact source hashes. Several earlier scratch QA
failures were harness defects (uninvoked init hook, wrong hierarchy planet ID,
hidden return button, hidden record ID assumption), not product passes.

## Accepted surface and orbital endpoint corrections

The same continuation critic accepted the final native frozen/ice contrast fix:
blue-gray interior/highlight/shadow values retain slope edges and crater rims;
hydrocarbon lakes remain distinct. Evidence: ignored
`data/planet-scale/final-ice-targeted/`, both styles/themes at regional and close
scales, including the selected recorded Hydrocarbon feature with1100survey cells.
Close enlargement and synthetic broad relief remain documented medium limits.

Actual Chromium checks after localized orbit fixes verify working distance
buttons, reset, recenter, safe viewport, suppressed planar hover/counters,
descent before force targeting, and explicit WebGL fallback. The native detail
endpoint is derived from available samples: in the1440×1024fixture safe viewport,
distance1.121375037 maps to strategic tile96 (12CSSpixels per native sample).
Outward zoom from the surface minimum returns to orbit. These checks reported
zero page errors; final independent orbital visual acceptance is still pending.

Sol high diagnosed the remaining pole fan as chart-lighting convergence plus
singular texture footprint. The correction is restricted to the navigation
globe: taper baked planar directional lighting near the pole and filter sampled
color coverage toward a unique endpoint-row mean. Actual saved masks, coordinates
and the authoritative strategic surface remain unchanged. This boundary does
not establish physically coherent spherical terrain or a globe terrain mesh.

## Final independent outcome and comparison record

The continuation critic accepts the bounded albedo navigation globe and Surface
workflow. Fresh caps/hydrocarbon rotated views remove the prior HIGH shaded
star/pinwheel. Water retains coast, river and material separation. The sphere
clears the toolbar; planar tooltips remain suppressed. Actual terrain-click
descent and return pass for water, caps and hydrocarbon with no page errors.
Evidence: ignored `data/planet-scale/final-orbit-unlit-review/{workflow.json,*.png}`.
Earlier flat dry and ice acceptance remains valid. This is a scoped interface
verdict, not optical accuracy, physical spherical terrain or Google Earth parity.

The successful correction separates lighting: orbit exports categorical surface
albedo and the sphere shader supplies illumination. Planar hillshade, elevation
tint and Survey contours remain on the strategic Surface. Repeated taper tuning
was abandoned after the independent failure; the high architectural diagnosis
and the negative caps/hydrocarbon frames remain recorded above.

| Journey/reference examined | Relevant strength and gap | Implemented response and evidence | Verdict/limit |
| --- | --- | --- | --- |
| Orbit to surface; Cesium quadtree source and Earth Enterprise README | Real detail must support closer views; old128×80 magnification added no data | Saved1024×640 native assets, reversible camera and detail-limited endpoint; protected browser and orbital regression | Scoped interaction accepted; no terrain mesh, streaming tiles, exact unfolding or live Google Earth comparison |
| Surface relief/annotation; Lutz Moon/Mars topographic pair and Moon label-placement process | Distinguishable landforms and controlled labels; initial native dry grid/ribbons obscured relief | Filtered background normals, independent crater normals, ice contrast, fine feature search and recorded anchors; stable flat/ice captures | Dry/ice accepted with synthetic relief and enlargement limits; authored charts are not optical photos or equivalent game sessions |
| Orbital material inspection; actual native water/lava/hydrocarbon/cap fixtures | Preserve distinct recorded classes while navigating | Unlit orbit composition, exact masks, footprint/pole sampling; native renderer checks and actual fixture captures | Navigation globe accepted; sparse rock landmarks and polar material distortion remain |

## Final functional and browser evidence

Protected native Chromium journey passes after orbital integration: initial
Orbit/Surface access, home settlement, Economy→Construction→Map context, refined
water picking, feature search/no-match/clear, pointer zoom/pan, six campaign
switch cycles with the same canvas/handlers, canonical ground target, actual
preview/commit, read-only historical snapshot and exact return live. Held real
authorized detail responses are ignored after campaign switch and logout. Tokens
remain absent from local/session storage. Evidence:
`data/planet-scale/browser-orbit-final/workflow.json`; zero page errors.

The read-only orbital regression exercises drag, +/− distance controls, reset,
overlay orientation, terrain descent, Economy return, touch return to orbit,
context loss and WebGL-unavailable fallback; zero page errors. It is reproducible
with `tests/browser_planet_orbit.py` against an explicitly supplied isolated V10
local preview through `WOLD_ORBIT_TEST_BASE` and `WOLD_ORBIT_TEST_CAMPAIGN`.
`tests/check_orbit.cjs` covers inverse projection, seam, pole/back-face/background
handling, inset viewport, source-row means and the native-detail endpoint.
Actual shader compilation/rendering also passed with derivatives/texture-LOD
extensions deliberately unavailable.

Actual Chrome Settings tab zoom100/125/150/200% passes1280×960 and1920×1280
physical desktop windows, including Orbit, Names/Features, inspector close,
management return and four-level hierarchy navigation. At the smallest CSS
viewport640×436 controls remain reachable; informational strips are intentionally
hidden at short heights. Evidence: `browser-orbit-zoom-{1280,1920}/metrics.json`.
Final coverage is Chromium154.0.8037.57 on Linux. WebKit is unavailable here;
native macOS Safari is unverified. Desktop scope only.

Native renderer checks pass for saved fields/catalog/anchors, explicit river
courses, exact-sea color stability, material boundaries/seam, linear normals,
quantization filtering, crater preservation, ice headroom and separate unlit
orbit bytes. Strategic output hashes and material alpha remain unchanged by the
orbit export. Legacy material/crater/hydro-label checks pass. The renderer-only
corrections do not justify repeating the already frozen147-test/264-hash/10,000-
turn backend gates.

## Retained limits and integration

The globe is a navigation sphere textured from the recorded chart, not displaced
spherical terrain. Crater relief is available on Surface; exposed-rock globes
can be sparse. Polar material lobes/distortion, stepped boundaries, softened
close enlargement, synthetic climate/ridge ribbons, compact chrome/locator and
settlement edge-arrow identity remain known quality limits. No physical radius
or kilometres are invented. A geometrically exact sphere-to-plane unfold and
new multiscale information beyond the native samples are not implemented.

New V10 generation is opt-in (`init-v2 --planet-generator planet-v10` with a new
isolated campaign ID); the default remains V1 and existing worlds are never
converted. Recovered cartography should integrate through explicit asset and
generator versions with the surveyed allowlist. Original cloud cartography and
private campaign records were not recovered, replaced or fabricated. The
character-relationships branch remains untouched; its existing management
screen entry is the integration point. No merge, deployment or data reset.
The observed inherited startup-DDL/writer deadlock remains an operational
limitation; run migrations before admitting writers in a dedicated follow-up.
This release candidate does not certify operational security, external backups,
production recovery or commercial-game parity.

## Final performance observations

The final source-frozen supplement passes all mouse/Space/touch Names controls,
touch command→Economy→Map return, light/dark appearance and camera invariance
checks, with zero page errors. Four actual native families and both styles were
used. After two warm management cycles,20further cycles retain the identical
map canvas,2602DOM nodes,369JS listeners and7canvas listeners at baseline/10/20.
Collected JS heap moves33,737,852→33,891,512bytes; this small observed increase
is reported rather than claiming zero memory growth or indefinite leak freedom.

Environment: Linux6.18.55 x86_64/glibc2.41, Python3.12.14, Chromium154,1440×1024,
touch-capable desktop context,2-CPU cgroup quota, shared workspace. Styles were
already shown before direct Surface measurements, so these are cached draws,
not cold creation/asset/raster times. Ten-draw warm means range2.19–15.90ms across
eight family/style combinations; first cached samples2.0–22.7ms. The1536×960
compositor limit is retained. Measurements exclude input, DOM force markers,
compositing and GPU execution; they are not frame-rate or production claims.
Three loopback API samples per family measure map77.91–103.76ms and detail
1067.59–1670.77ms, including local response retrieval. Large-scale or remote
network behavior is not established. The final native generation sample was
23.762s,5,273,879canonical UTF-8bytes and182MiB peakRSS.

Exact before/after frontend hashes match the frozen files. Evidence:
`data/planet-scale/orbit-final-performance/{performance,supplementary}.json` and
`frontend-freeze.json`. Earlier overloaded parallel browser attempts timed out
before detail readiness; they are not passes. Serial protected/orbital runs and
this completed supplement supersede those attempts.

Reproducible commands: `node tests/check_orbit.cjs`,
`node tests/check_detail_renderer.cjs`, the three legacy renderer scripts, and
`tests/browser_planet_detail.py` with an isolated PostgreSQL test DSN. Its optional
fixture cache is backend-source-hashed, stores only fictional QA data and checks
creation choices; uncached generation is the default. The final protected
journey used this cache for setup, then real SQL, HTTP authorization and turn
operations. Runtime evidence, assets, cache, snapshots and screenshots remain
ignored and are not distributed as campaign data.
