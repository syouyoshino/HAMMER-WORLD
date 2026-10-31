# Continuous recorded-world journey — 31 October 2026

## Scope and decisions

Continuation of WIP `5004eb2` on `map-generation`. System symbols now use the same
saved surveyed terrain as the planet renderer, rather than generic coloured
marbles. Selection, Focus, Inspect, Enter orbit and Enter surface are distinct
controls. Grid is optional and off initially. True frozen star-relative positions
share one scale; enlarged symbols are explicitly disclosed. A Body list keeps
crowded and offscreen destinations reachable without inventing orbit spacing.

Focus enlarges the selected world; the selected symbol and label paint last.
Context symbols fade when they overlap it. Enter orbit holds the system view
while authorized detail loads, then opens the globe at the preview bearing.
Enter surface passes through that globe and carries the geographic focus into
the regional map. Explicit orbit stays in orbit until the player chooses a point.
User input cancels automatic entry. Return restores the original system camera.
The mounted map canvas and existing renderer are retained.

Body inspection presents recorded identity, parent, radius in km, survey status,
position status and the selected body's known moons. IDs and raw coordinates are
collapsed technical detail. Unknown means unknown; no moon surfaces, invented
orbital paths, hidden intelligence or atmosphere terrain were added. Inspector
placement reserves the selected world and destination action strip. The geographic
entry crosshair follows the world under panning and clears with context changes.

Preview generation is serial and asynchronous, uses no additional WebGL contexts,
and retains at most 24 cached 128px sprites. Source references, snapshot/campaign,
request tickets and epochs reject mismatches. Campaign refresh with a new snapshot
clears cached previews as well as cameras; history, login and logout invalidate
pending work. UI state remains outside campaign records.

## Evidence provenance

`tests/review_world_fixtures.py` is an opt-in, test-only factory for new isolated
fictional demos: sparse (2 planets), rich (8) and extreme (5). All supported solid
surfaces have real generated native assets and explicit radii. The extreme-wide
variant spans 0.02–90 AU; the detected outer world stays position-redacted.
Unknown moon/belt contacts have no fabricated locations. Existing campaigns and
production generation code were not changed. Duplicate creation refuses rather
than replacing data. Private data, manifests, generated maps and captures are
ignored runtime artifacts and are not committed.

Fresh Chromium captures and traces: `data/continuous-world/release-candidate/`.
The earlier `accepted-candidate/` pass predates the marker CSS fix and is not final
visual evidence. `03-transition-capture.png` may show the already-completed
surface because screenshots are slow on software graphics; use the captured
render timeline for handoff ordering and `05-orbit-choice.png` for stable orbit.
Screenshots alone do not establish animation quality.

## Independent critique ledger

The same independent Sol medium critic first received anonymous full-aspect
images without implementation discussion, then separate observed browser evidence.
It was reused for corrections rather than replaced to obtain approval.

| Finding | Severity | Correction / disposition |
|---|---|---|
| CW-01 Raw IDs, scientific radius and wrapped JSON dominate inspection | High | Factual summary, ordinary km, parent-specific moon rows, collapsed technical disclosure |
| CW-02 Context star/symbols cover the selected world in extreme system | High | Selected-last draw/pick priority, context fading, collision-aware labels and Body list |
| CW-03 Orbit/Surface ambiguous; Orbital style name confusing | Medium | Heading follows actual mode including direct entry; display style renamed Natural |
| CW-04 No carried geographic focus/orientation | Medium | Scoped coordinate crosshair, north-up label, actual overlay CSS and viewport bounds check |
| CW-05 Province instruction without visible province boundaries | Medium | Terrain inspection instruction and explicit Provinces overlay hint |
| CW-06 Finite, soft procedural terrain looks synthetic | Medium | Inherited recorded-source limit; no fabricated fine detail |
| CW-07 Dense small metadata, similar action weights, Forces fill outlier | Low–medium | Forces tinted; compact technical metadata remains a minor density limitation |
| CW-08 Inspector obscures selected label/actions | Medium | Reserved map safe area and inspector top below destination strip |

The final reassessment is recorded below; CW-04 required one additional precise
crosshair anchoring correction after the three-system pass.

## Reference comparison and limits

This milestone follows the navigation investigation in
[the preceding review](navigation-and-tinted-ui.md): Cesium CameraFlightPath source
was examined for cancellation and continuous camera context. No Cesium dependency
or proprietary assets were copied. The user's Google Earth analogy guides
continuous orientation, selection and camera freedom; no fresh Google Earth or
commercial-game task comparison was performed in this milestone. Anonymous images
compare Hammer World states, not equivalent commercial-game screenshots. Therefore
this review cannot establish parity with Google Earth, Victoria 3, CK3 or Stellaris.
Settlement economy and character relationships are outside this celestial fix.

## Verification and performance limits

Targeted projection, preview isolation/cache and body-return checks pass. Browser
journeys verify real asset SHA identity, preview/globe bearing, no early surface
flash, regional center, explicit orbit/manual descent, geographic marker movement,
inspector clearance, exact system return, unknown restrictions, same canvas,
unchanged campaign responses and absence of exercised JavaScript errors.

Environment: Chromium 154.0.8037.57, 1440×1000, shared Linux two-CPU quota,
software ANGLE/Vulkan SwiftShader. The previous sequential three-case run measured
cold preview readiness at 3.87s (one), 15.29s (four), 23.92s (seven). These include
asset fetch/decode and serial CPU generation, not per-frame latency or production
capacity. Final regression runs may contend with other browser checks; do not
interpret them as isolated benchmarks. Cached previews avoid repeated GL setup.
Inherited globe zoom was 1.87–1.91s on this software environment; Google Earth
smoothness is not achieved or claimed. Hardware graphics remain unverified.

Backend source is unchanged. Retained applicable 10,000-turn fixture gate:
`data/terrain-finish/stress-v2.json`, pass in 257.97s, 10,001 snapshots and exact
restoration. No costly simulation rerun for these frontend corrections.
WebKit executable and native Safari coverage remain unavailable.

## Integration

Keep `system-previews.js` loaded before app initialization and retain authorized
API/context invalidation. Cartography can replace saved detail sources without
changing entity IDs or camera tickets. Preview resolution/projection is deliberately
bounded; CPU orthographic sprites and perspective globe are not pixel-identical.
Keep geographic focus in body-return tickets. Do not store login tokens or these
UI preferences in campaign state. Character relationships branch, unrecovered
cartography and existing immutable history were not modified. No deployment,
merge, data reset or operational backup/recovery certification was performed.

## Source-frozen regression results

All three cases passed in `release-candidate/report.json`: 2/8/5 planets,
1/7/4 authorized surveyed previews, matching real source SHA and initial bearing,
correct mode labels, exact system return and unchanged campaign responses.
No JavaScript errors were observed. Cold readiness during concurrent regressions
was 4.10s / 31.61s / 33.52s respectively; contention prevents a clean comparison
with the earlier sequential observations.

`context/report.json` passes star/moon/planet mouse/touch/keyboard navigation,
exact origin camera/selection/overlay/style return, main canvas retention,
reduced motion, historical read-only/unknown intelligence, private logout and
absence of token browser storage. `system-regression/report.json` passes orbit,
Shift-pan, zoom, keyboard Fit, rail-owned clipped hits, unknown moon/star Inspect,
planet entry/return and unchanged records. `reflow/report.json` passes desktop
1280×720 at CSS zoom 100/150/200% and 1920×1080 at100%, grouped controls,
map drag/management return and same canvas. CSS zoom is not native browser zoom.

All reports record source hashes. Only the marker transform changed afterward:
the whole-label centered anchor was corrected so the crosshair's 22px line box
centers exactly on the projected coordinate, with labels below. The supplemental
`marker-anchor-final/` journey checks actual viewport bounds, noninteractive
absolute positioning and crosshair-center error below1px, as well as the complete
sparse workflow. This narrow CSS correction does not invalidate earlier camera,
authentication or data checks. Marker bounds and movement alone were insufficient
to detect the earlier20px visual displacement; the explicit anchor assertion now
covers it.

Final frontend hashes (SHA-256):

| File | SHA-256 |
|---|---|
| `public/app.js` | `531c4b82160d7fd006bf8bd7ccb1dcd98f2052c6476f4b5ff34fe30ea34fc4ff` |
| `public/system-view.js` | `21239c03239c68ccf094526516b238eec6bdbbaf431f55844952d23be0932637` |
| `public/system-previews.js` | `411d391f298a899d0c938e6329b0d2ce4bd6d14f8d829642802aa96950f114c1` |
| `public/style.css` | `f411184025187e26a8a2d6cece926df45f8952c53068a604aaebe2d97cd84027` |
| `public/index.html` | `09b84d3ae8ec8f0989800b67077c7b08c12997d6b2c08e8cd63d1cc2db7301aa` |


Bounded architectural review: no unresolved critical/major authority, persistence
or numeric findings. Snapshot-change cache clearing resolves its moderate cache
lifecycle finding. Separate sphere projections and the deep default regional
landing remain presentation limitations rather than data defects.

## Final independent verdict

The same critic grants scoped acceptance: no unresolved critical or major visual
defect in the reviewed sparse, rich and extreme evidence. CW-01/02/03/04/08 are
resolved for the reviewed bodies/states; CW-05 is addressed; CW-06 remains inherited;
CW-07 retains minor dense-control/secondary-text limitations. Distinctive rockland
and crater geography is recognisable across system preview, globe and surface.
Unselected overview glyphs can cluster and peripheral neighbours can be cropped;
selected-world identity and actions remain clear in reviewed frames.

The critic independently inspected the screenshots and read the final sparse
report. Exact camera return, coordinate accuracy, redaction, unchanged records
and error-free navigation rely on browser execution reports rather than stills.
It did not independently drive the browser, certify animation smoothness, compare
commercial fidelity, or cover every viewport/arbitrary crowding/unsupported world.
Final supplemental sparse run passes, with one preview ready in4.31s, no errors,
exact return, correct anchor and unchanged records. This is an interface release
candidate, not a deployment, operational security or recovery certification.

Continuation: profile hardware frame/readback costs before promising smoothness;
retain the existing critic ledger for further changes. Extend supported recorded
terrain independently of UI work; never invent atmospheric/moon surfaces to fill
the fixture. Recheck extreme crowding when adding new celestial symbol types.

Verified implementation, regressions and review record: `ed352f1`, pushed to
`origin/map-generation` (WIP baseline `5004eb2`). Runtime evidence remains local
and ignored; the durable findings, environment, metrics and source hashes above
are committed. No private fixture credentials or campaign databases are included.
