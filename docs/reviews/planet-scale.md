# Saved planetary detail and scale

Status: native V10 backend gates pass; water map scoped visual review accepted.
Final dry/ice relief reassessment and frontend delivery remain pending.

The user identified a regional-board sense of scale and requested a Google
Earth-like planetary view. Fresh baseline browser captures are under ignored
`data/hydrography-pass/scale-baseline/`: 1440×1024 Chromium, actual128×80 saved
geography at200% with broad stepped coasts, biome slabs and axial river paths.
The existing1536×960 raster and5× zoom ceiling do not add geographic information.
There is no recorded physical planet radius or cartographic unit in kilometres;
the hierarchy's relative body radius cannot supply one.

## Bounded architecture

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
