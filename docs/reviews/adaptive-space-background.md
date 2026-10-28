# Adaptive orbital space — 28 October 2026

The user's space reference supplied the subdued near-black/slate atmosphere and
sparse stars. Its ships were not copied or introduced as fictional campaign units.
The new background is generic decoration, not recorded astronomy, intelligence or
undiscovered systems. It never uses campaign seeds or records.

## Design and integration

A small `orbit-background.js` paints150 fixed sphere directions and24 broad slate
haze lobes. The orbital camera basis projects them using forward=-N, with a modest
bounded zoom response. This keeps continuity through longitude wrapping and the
poles without reseeding the scene. UI light/dark changes do not recolor space.
The physical starfield is intentionally interpretive, not an astronomical sky.

App integration paints behind the existing transparent globe. During the existing
420ms view transition, one temporary2D canvas flattens sky and globe so alpha is
applied once. It is capped at2048px per side and2,097,152 total pixels, reused during
the transition, and released on completion/cancel/no-map/hierarchy contexts.
Opaque orbital frames paint directly. Missing optional sky code retains a clean
flat fallback. No new handlers, timers, idle animation loop or dependencies.
Existing reduced-motion handling continues to bypass the view fade.

The surface renderer, globe shader/lighting, landmark module, geography, IDs,
simulation/persistence and authentication are unchanged. No real campaign data
was regenerated. The stopped local PostgreSQL/preview processes were restarted
against their existing fictional fixture schema; no cloud recovery is claimed.

## Fresh evidence and critique

Ignored `data/space-background/baseline/` contains the prior committed app at the
same four exact native camera poses as `candidate/` and `revised/`: home, orbit,
pullback and dark interface. Baseline was captured by serving the committed app.js
in the browser while keeping actual fixture/API responses. The new module was
unused by that committed app. No screenshot crops or mocked campaign records.

A fresh Sol medium critic first saw anonymous A/B full-frame images with no source
origins or desired winner. It found the initial candidate's sparse stars useful
but haze imperceptible, leaving a flat navy appearance. One bounded Sol medium
implementation escalation replaced the weak single glow with broad fixed-world
haze and a darker base, precomputed star vectors/styles, and corrected transition
compositing. The same critic accepts the revised static appearance: visible broad
uneven slate space, subordinate pinpoints, legible UI and consistency across themes.
The globe's flatter relief remains inherited and outside this background task.
The same critic inspected current native drag and transition frames plus the
functional/resource evidence. It accepts the scoped camera-responsive background
and clean dissolve/return, with no remaining visual blocker. It does not establish
cinematic descent, every-frame seam absence or native-rate smoothness.

## Verification

- `tests/check_orbit_background.cjs` passes actual camera-basis orientation,
  behind-camera rejection, pole finiteness, longitude seam/full-orbit continuity,
  deterministic repeated projection and bounded zoom response. Existing orbital
  projection/landmark Node checks and JavaScript syntax pass.
- `tests/browser_orbit_background.py` passes actual canvas drag and zoom, changing
  background pixels in exposed space, invariant background through theme change,
  management return preserving camera, zero idle sky draws, five Surface/Orbit
  cycles, no retained transition pixels, unchanged campaign records, persistent
  map canvas and missing-module fallback. No JavaScript page errors. Source-hashed
  JSON and full-frame captures are under `data/space-background/browser/`.
- The protected native browser suite passes actual authentication, history
  read-only behavior, supported movement preview/commit, stale asset rejection on
  campaign switch/logout, token-storage exclusion, stable handlers and canvas,
  and native/legacy map interaction. Evidence:
  `data/space-background/protected/workflow.json`.
- Chromium154.0.8037.57 at1440×1024, Linux QA environment. Measured sky draw command
  construction over58 exercised calls: median0.20ms,95th percentile0.40ms,
  maximum1.10ms. These CPU timings exclude GPU/raster completion and do not prove
  whole-game FPS. Peak measured temporary composite1,474,560 pixels; zero active
  offscreen pixels after settling. No production-scale performance claim.
- WebKit and native macOS Safari were not tested here. No backend/numeric changes
  justify repeating the retained10,000-turn gate. The prior native detail and
  shader limitations remain; no commercial-game or physical-planet parity claim.

## Continuation and delivery

Original unretimed browser recordings are under `data/space-background/motion/`
and `motion-direct/`, with timeline JSON. The94.04-second first recording contains
paced native drags, pullback and view switches; six unmodified full-frame extracts
of the Surface transition and two drag samples were inspected. Media capture
required a temporary workspace-accessible system-FFmpeg shim; no app dependency
was added. An initially requested “transition screenshot” had already settled and
was not treated as transient proof; actual video frames supply that evidence.

Native eight-step drag timing without video was10.585s for the committed baseline
and7.082s for the revised app at identical poses in this QA environment. This one
noisy pair shows no observed regression, not a speedup or FPS guarantee. Automated
input pacing already existed before this change. GPU and real native-rate motion
remain unverified; do not infer smoothness from the recorded25fps container rate.

Replay against an existing fictional preview:

```sh
node tests/check_orbit_background.cjs
WOLD_QC_BASE=http://127.0.0.1:4203 WOLD_QC_CAMPAIGN=material-caps \
.venv/bin/python tests/browser_orbit_background.py
```
Delivery commit references are recorded after the implementation commit.
Keep generated media, runtime databases and connection files out of Git. This
remains an interface release candidate, without merge or deployment.
