# Tinted command surfaces and explorable system navigation

## Scope and baseline

The user requested transparent tinted controls, a planet critique and Google
Earth-like freedom between surface, planet and solar-system views, then explicitly
rejected the old solar chart. Desktop only. No database/generator/history changes;
recorded astronomy and surveyed intelligence remain authoritative.

Fresh baseline: `data/navigation-glass/baseline/01-globe.png` through
`06-economy-light.png`, with matching DOM snapshots and browser report. Actual
Chromium workflows selected the demo, changed globe/surface/system/planet views
and opened Economy in both themes. No prior screenshots were used as current
audit evidence.

Findings tied to that baseline:

1. Globe: strong spherical silhouette, readable settlement labels and physically
   directional day/night. Many selected settlements lie on the night side, so
   geographic reading there requires the cartographic surface view. Opaque title,
   control and label blocks interrupt the map. High priority: tinted surfaces.
2. Surface: recorded rivers and settlement anchors are legible. Large categorical
   biome boundaries, stepped coastlines and broad repeated ridges look synthetic;
   magnification does not add geographic detail. These are inherited source/detail
   limits, not solved by transparent chrome or a camera animation.
3. System: tiny disconnected symbols span a largely empty rectangle. Chart x/y
   normalization is topological, not astronomy; there is no free viewing angle.
   High priority: a perspective system view over actual public saved positions.
4. Return to planet: camera and projection reset instead of preserving the visited
   location. High priority: contextual camera memory and safe asynchronous restore.
5. Economy (dark/light): stacked near-opaque panels obscure map context. Text and
   charts have useful hierarchy, but multiple fills undermine transparency.
   High priority: one tinted shell and quiet inner report surfaces.

## Implementation decisions

Use the existing mounted canvas and lightweight JavaScript modules. The system
view projects frozen public star-relative vectors with one common distance scale;
body symbols are enlarged for readability. It does not simulate orbital elements,
move unknown contacts into space, or claim physical travel between system and
geocentric cameras. Unknown-position bodies remain separately labelled contacts.
A cartographic X–Z coordinate grid provides orientation; it is not an orbital path.

In-memory per-node camera history is bounded and scoped by campaign, snapshot and
context epoch. Save committed identities, not requested destinations; accepted
responses alone restore cameras. Exact body-focus return tickets retain priority.
Matching detail must arrive before a restored globe is painted. Retain the previous
canvas with a loading status and blocked map interaction during that brief hold;
do not flash a different projection or mark WebGL unavailable simply because a
saved detail request is pending.

Tint belongs to backgrounds, never global element opacity. Text, selected actions,
focus indicators and semantic colors stay crisp. Main management shells supply
one fogged/tinted layer; nested reports use only a slight fill. Native option lists
retain solid backgrounds for legibility.

## Reference and limits

Examined Cesium `CameraFlightPath.js` at commit
`ad366f071293b28bdf330c822965b8bd0bdeb781`: bounded duration, easing, completion and
cancellation are relevant navigation strengths. No Cesium code/dependency was
copied. Prior Earth Enterprise/terrain research remains in `planet-scale.md`.
Live Google Earth interaction and imagery were not examined in this increment;
Google Earth is the requested interaction target, not a verified parity claim.

The scene remains a strategy map built from finite saved geography and frozen
astronomical records. No streaming optical imagery, terrain mesh, physical free
flight, planetary time progression or recovered original cartography is implied.

## Independent critique loop and corrections

A fresh Sol 6.1 medium critic first received only anonymous, uncropped 1440×1000
pairs (`data/navigation-glass/anonymous`, separate key), without origins, source or
prior verdicts. It judged the perspective system substantially clearer, but flagged
ambiguous duplicate moon contacts, a boxed sky boundary, weak host relationships,
and the largely dark initial globe. Origins and root-executed interaction evidence
were revealed afterward. The same critic reviewed the corrections and matched
management panels; no alternate reviewer was sought for a favorable result.

| Finding | Response | Final verdict / limit |
| --- | --- | --- |
| Disconnected solar icons, no viewing freedom | Saved-position perspective, orbit/Shift-pan/zoom, Fit system, coordinate plane | Scoped composition accepted; actual empty space remains moderate debt, not grounds to move recorded bodies |
| Duplicate unlocated moon identity | Parent-world/name labels | Resolved without inventing names or positions |
| Host relationship unclear | Recorded AU distance sublabels and host-star label | Resolved; no orbital trajectories inferred |
| Rectangular sky boundary | Full-canvas sky; clip only world symbols to scene | Resolved in final capture |
| Initial view conceals most geography in night | Untouched first entry favors illuminated geography at a 0.6-radian phase from the recorded sun | Resolved visually; night floor/light fixed; Recenter still finds home/selection; visited cameras are not reoriented |
| Opaque nested panels | Single theme tint, 7px outer fog, quiet inner fills, tinted labels/buttons | Dark/light matched panels accepted; readable totals and chart, visible geography through shell |
| Faint Local holdings | Confirmed disabled until province selected | Intentional disabled state, not active text defect |
| Tiny metadata / synthetic geography | Preserved compact command hierarchy and finite source | Residual moderate hierarchy/detail limitation; no optical-realism claim |

The matched panel run explicitly used Recenter before descending, so both versions
show the same home geography, screen size and recorded economic values. Prior
assets came from baseline commit `5e20f60` through a loopback read-only API
passthrough to the same existing fixture. No demonstration records were replaced.
Final images: `data/navigation-glass/matched-after/` (globe, surface, system and
Economy in both themes); comparator: `matched-before/`.

The critic accepts the scoped visual result. It did not execute browser tests,
endorse smooth animation, or compare live Google Earth sessions. A bounded Sol
high implementation audit independently verified common-scale projection, unknown
isolation, numeric guards, context copies, transient render scale and the two
corrected picking/loading defects, with no remaining critical/major regression in
those contracts.

## Functional evidence

All runtime captures/reports/traces are ignored artifacts, excluded from Git.

- `browser_navigation_continuity.py`: exact globe, surface and system camera
  restoration; branch dropdown navigation; stale map response rejection; real
  map drag; management return; both tinted themes; reduced motion; mounted canvas
  retained; source hashes, unchanged API record and no exercised page errors.
  Trace: `data/navigation-glass/final/workflow-trace.zip`.
- `browser_system_view.py`: real orbit drag, Shift-pan, zoom, keyboard Fit,
  unknown moon and star focus/return, planet entry/system-camera return, smaller
  desktop and clipped-body/contact-rail picking. Physical symbols cannot steal
  clicks from the separately visible contact rail.
- `browser_orbit_restore_loading.py`: held actual detail responses prove the
  canvas does not change projection while loading; input is blocked; changing
  overlay keeps the hold; stale detail cannot release the newer hold; exact
  camera restored after matching detail. Report: `data/navigation-glass/loading/`.
- `browser_body_focus.py`: actual mouse/touch/keyboard body journeys, other
  surveyed planet, exact camera/selection/overlay/style return, historical
  detected/read-only state, context invalidation, private logout, no token
  browser storage, unchanged records and no page errors. Recenter explicitly
  locates home after the new sun-aware overview before selecting Forge.
- Node checks: system common-distance ratios, free projection, finite guards,
  missing/invalid astronomy and unknown-contact isolation, immutable inputs and
  actual draw smoke; body-ticket copy/context isolation (including system camera);
  globe inverse picking/seams/poles; sky cache/continuity; settlement landmarks.

Initial candidates exposed real defects: globe restoration before detail could
mark orbit unavailable; a missing committed identity prevented camera saves;
undefined entity IDs matched unrelated records; sector→planet dropdown traversal
excluded all descendants. Localized Sol medium fixes were tested before release.
A later architecture audit caught union-rectangle picking into the contact rail
and premature clearing of a pending restore on overlay reload; final targeted
checks cover both. Failed candidate evidence is retained in `nav-fix/` and the
original baseline; successful reports alone are not the entire review history.

Backend/generator files are unchanged. The required 10,000-turn connected fixture
gate remains source-applicable from the preceding release: PASS, 257.97s, 10,001
snapshots and exact restoration (`data/terrain-finish/stress-v2.json`). It was not
repeated for these frontend changes. No real campaign values were supplied,
records regenerated, history rewritten, character branch modified, or merge/
deployment performed.

## Browser, motion and performance limits

Chromium 154.0.8037.57 on shared Linux software graphics, two-CPU cgroup quota.
WebKit executable is absent; native macOS Safari and hardware graphics remain
unverified. Desktop CSS zoom is distinct from native browser zoom. Pointer/touch
simulation does not establish physical-device coverage.

Zoom has bounded easing and endpoint transitions, but actual globe→surface is a
geographic-focus/scale-preserving crossfade, not exact geometric unfolding.
System→planet preserves camera context through a short accepted-frame fade, not a
physical interplanetary flight. System coordinates remain frozen at their recorded
epoch. Solar and planetary cameras share navigation, not one continuous 3D engine.

Globe output temporarily renders at half resolution while dragging/zooming and
returns to full resolution at release/completion. Logical camera coordinates,
picking, texture revisions and immutable source detail stay unchanged. A concurrent
QA run at 1440×1000 recorded only two tween samples: half buffer 720×500 and final
1440×1000. Through-globe-copy times were approximately 850ms and 2,579ms, including
render/background/WebGL readback. This is visibly slow software rendering, not
Google Earth smoothness. Submission-only WebGL timing would conceal that cost.

A separate warm, single-browser measurement (no concurrent QA browser from this
task) confirms the limitation: three 1440×1000 zoom actions took 1.87–1.91s each.
Median half-resolution through-copy was 378.1ms; final full-resolution median was
1,476.2ms. Each tween produced two rendered samples. Driver: ANGLE Vulkan
SwiftShader; CPU quota `200000 100000`. Report:
`data/navigation-glass/performance/report.json`. Half-resolution output reduces
work, but this environment does not meet a Google Earth smoothness standard.
Production hardware graphics and the renderer/readback pipeline need profiling
before that claim; three fixture interactions are not a production benchmark.

Final desktop reflow checks pass at 1280×720 CSS zoom 100%, 150%, 200% and
1920×1080 100%, including grouped zoom controls, actual drag, workspace return,
same canvas, no errors and unchanged records (`data/navigation-glass/reflow/`).
Final system checks also pass the clipped-star/contact-row regression. All final
report source hashes were compared with the shipped frontend files.

## Integration and continuation

`public/system-view.js` is a small standalone projection/drawing module; preserve
its hierarchy transform contract for map picking and military anchors. Known body
positions are immutable and share one normalizer. Keep scene/rail hit ownership,
near-first circle/label picking and contact scrolling when integrating cartography.
There are no invented orbital paths or radius defaults.

Preserve committed camera identity, context-bound pending-detail restore and the
separate body-focus return ticket. Do not replace the camera cache with persistent
campaign fields or browser token storage. Interaction render scale changes output
buffers only, never logical picking or immutable texture revision keys.

Next terrain work requires new source detail/topology, not cosmetic upscaling.
Next smoothness work requires hardware comparison and renderer/readback profiling;
current correctness/visual acceptance does not close that performance gap. Retain
all unresolved moderate visual debt and inherited finite-detail limitations when
assessing future candidates. Interface release candidate only; no deployment,
operational-security, backup/recovery or whole-game acceptance is implied.

Delivered implementation, regression checks and review: `defae73` on
`map-generation` (baseline `5e20f60`). No merge or deployment.
