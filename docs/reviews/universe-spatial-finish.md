# Universe spatial presentation and motion — 31 October 2026

## User correction and baseline

Baseline `66e9099` passed its scoped navigation/legibility checks, but the user
rejected the result as ugly and too static. That acceptance did not establish
that it felt like a space atlas. Fresh baseline actual-browser capture:
`data/universe-space/baseline/01-universe.png`. It shows three tiny contacts on
industrial diagonal hatching, a vertical hierarchy connector and repeated
non-geographic caveats. It reads as a relationship diagram, not a spatial scene.

The Product Design audit skill guided screenshot-first observation. Its context
preflight found no saved design context; this repository and the user's existing
visual direction were used. Available cloud Chromium/Playwright captured the
actual interface. No canvas publication or commercial screenshot comparison was
requested or performed. The audit is bounded to this desktop Universe surface.

## Representative steps and findings

1. **Enter Universe.** Explicit controls and knowledge labels worked, but flat
   hatching and diagram layout failed the requested atmosphere. Keep navigation
   and recorded knowledge; replace the scene composition.
2. **Pan, zoom and observe.** Background depth/motion were absent. Add scenery
   parallax and restrained drift, while contact targets stay stable. First new
   artwork candidate was also rejected: giant rounded strokes and a hard oval
   looked like unfinished vector shapes; detected metadata crowded another label.
3. **Open management, leave and return.** Motion must pause when obscured and
   resume without multiplying handlers or altering campaign state. Reduced-motion
   users need a static ambient scene; this is verified by actual pixel checks,
   not assumed from screenshots.

A separate inherited minimum-zoom edge case appeared during regression: surface
zoom called enterOrbit and immediately recursively applied more outward zoom,
which could skip directly into System before the globe was observable. One
input now enters Orbit and stops; subsequent outward input can enter System.
No physical travel or astronomical time progression is added.

## Final implementation

- Replace hatching/org-chart connections with a star-atlas composition, known
  region/sector markers and visible parent context. Sector labels have more
  separation and an explicit `Within [recorded region]` line.
- Diffuse broken stellar haze, irregular fine dust and soft core replace broad
  vector ribbons. Artwork is generated once into a fixed1400×900 canvas per
  theme, at most two theme textures (~10.1MB raw RGBA total). It contains no
  records, private seeds or navigable undiscovered entities. It is decorative,
  not a measured galaxy or discovery footprint.
- Sparse foreground stars move at multiple parallax depths with camera pan;
  cached scenery drifts gently. Selection can add a quiet focus sweep.
- One Universe RAF loop caps drawing at24Hz. It runs only while the view is active
  and visible, without reduced motion or an obscuring command/menu/workspace.
  Exit, context reset, visibility and media-preference changes stop/resume it.
- Compact short-desktop layout, label hit frames, exact camera return, public
  contact derivation and historical/auth request guards remain intact.

No backend, schema, generator, saved geography, campaign record or immutable
history change. Root coordinator owns browser evidence/tests/docs; Luna performs
bounded building and Sol medium handles localized failed-candidate corrections.

## Independent critique ledger

A fresh Sol medium critic received anonymous uncropped A/B images at the same
viewport and information load, without origins, intended winner or prior verdict.
A was the rejected baseline; B the rejected first moving-scene candidate. Neither
was accepted. Intended workflows and executed motion results were supplied only
afterward; the same critic is reused for corrected evidence.

| Finding | Severity | Correction |
|---|---|---|
| S01 Thick rounded ribbons dominate and look unfinished | High | Cached irregular particle/cloud texture; no stroked arms or hard ellipse |
| S02 Crowded sector metadata and unclear parent context | High | Expanded arcs, concise state and explicit parent line |
| S03 Background or emptiness dominates useful contacts | High | Quiet diffuse artwork, clear luminous contact markers and label separation |
| S04 Flat industrial hatch | Medium | Multi-depth star/haze composition with pan response and restrained drift |
| S05 Repeated technical caveats | Medium | One quiet atlas/schematic caption; meaningful unknown-state footer retained |
| S06 Canvas action affordance needs interaction evidence | Medium | Explicit contact controls retained; actual selection/navigation tests |

The corrected full-height/dark/light/panned/short-desktop/historical captures
passed the same critic: no remaining major visual blocker. S01/S02/S04 resolved;
S03 substantially improved. S05 repetition was low severity; S06 first-use
affordance remained medium polish. CSS150% canvas raster softness was an
additional polish finding. These led to bounded final corrections: Universe-only
CSS/display-aware canvas resolution, destination-specific hover text/pointer,
tooltip retention through animation, and consolidated atlas/extent captions.
The final frozen-source browser evidence is recorded below.

## Evidence limits and continuation

Scenery does not confer physical authority. Actual universal positions,
exploration footprints and unrecovered cartography remain unavailable. Dense
multi-region scenes remain outside the small-fixture visual coverage. The sky is
not an additional list of clickable/hidden objects.

No accessibility certification: contact label/target states, normal inputs and
reduced motion are checked; contrast measurements, screen-reader behavior and
all desktop zoom combinations are not certified. Native Safari/WebKit and hardware
graphics remain unverified. Software globe smoothness remains an inherited limit.

Backend source is unchanged. Retained applicable10,000-turn fixture gate:
`data/terrain-finish/stress-v2.json`,257.97s,10,001 snapshots and exact restoration.
No costly simulation stress repeat for this visual/motion correction. No merge,
deployment, data reset or operational backup/recovery claim.


## Frozen-source execution and final review

`data/universe-space/release-motion/` contains actual dark/drift/panned/light
screenshots, trace, video and report. It passes ambient pixel change with stable
contact targets, camera pan, hover action retained across ambient frames, static
reduced motion, real menu/workspace pause/resume, exit/reentry, campaign stop,
retained canvas/listener count, unchanged records and no page errors. Visibility
pause/resume uses a `document.hidden` getter/event injection, not a native OS tab
visibility claim. Motion is tested through actual canvas output over time; it is
not inferred from screenshots. The short preview is an excerpt of the real
recording, with full viewport aspect ratio retained.

`data/universe-space/release-navigation/` passes the entire surface→Orbit→System→
Universe journey, one-boundary surface gesture, exact system return (button and
inward zoom), independent root cameras, authorized known contacts, canvas region
activation and labeled sector activation, historical authorized state, held old
responses during campaign switch/private logout, no token browser storage,
unchanged records and no page errors. Short-desktop all-contact bounds and both
themes pass. Four existing Node projection/preview/body-focus/Universe checks,
syntax and diff checks pass. No backend simulation test repeated.

Final actual coverage: Chromium154.0.8037.57, shared Linux/two-CPU quota with
software graphics,1440×1000;1280×720 at CSS150% in the navigation suite. Universe
canvas backing resolution now accounts for CSS display scaling (bounded to3×),
while other map renderers retain their original resolution behavior. Browser
native zoom and Safari/WebKit remain unverified.

During concurrent video/trace capture and regression, the motion sample observed
40 draw calls over2,521.1ms (~15.87 calls/s). The scheduler caps Universe drawing
at24Hz; that cap is not a guarantee of achieved frame rate. Renderer draw-call
median was0.50ms; maximum188.4ms includes cold texture generation in the measured
population. The navigation suite measured0.50ms median and107.6ms maximum. These
are JS draw submission timings, not compositor/presentation latency. Cached theme
creation can cause a one-time hitch. Hardware, larger fixtures and full-scene
presentation timing remain unmeasured; inherited native globe rendering is slow
on this software environment. No commercial-game/Google Earth smoothness claim.

The same critic accepts the corrected scene, then independently inspects the final
polish images: S05 wording, S06 hover affordance and CSS150% sharpness are closed
for this fixture; no new blocking issue. It inspected stills and read execution
reports; it did not repeat browser interactions or certify animated smoothness.
All S01–S06 findings remain above, including rejected candidates and corrections.

Final source hashes (SHA-256):

| File | SHA-256 |
|---|---|
| `public/app.js` | `2cdd6c88c8b6f76221892bd049a3dca9a106928820d979373ec5172fff2c5676` |
| `public/universe-view.js` | `e741cb2b198bb9d7323477fcdc0cdb5a59328682364533b42df1fd9cd0e4c558` |
| `public/index.html` | `c1c299bdd5296b90537ef961ad23ea8ab16e3d9c63304dcac341191ae6f27df8` |
| `public/style.css` | `60f5bc845dbd593be2731fad32cccbc4d5b434e33b51d1dc56099de8ada2aaa5` |
| `public/desktop-shell.js` | `02190928ec72d2a275f81ecff58571ee7da546efe5dee4a8d34e1bad6bf59ad2` |
| `public/desktop-shell.css` | `530ac6ccbeeabe1dd5c9f7bb9ffac551fccb580dc6ff75d23c4b14eaec6ebbe7` |
