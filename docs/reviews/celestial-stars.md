# Saved stellar astronomy — 29 October 2026

The user chose **generate astronomy for new demo systems**. The earlier proposed
schematic placement was abandoned before delivery. This implementation creates
optional saved astronomical records for new demos; it never adds synthetic
bearings to existing campaigns or rewrites their history.

## Contract and integration

`--astronomy static-v1` opts a newly created demo into a versioned static epoch:

- Integer Cartesian positions in micro-AU in each system's own `system-xyz-v1`
  frame; exactly one existing host star at the origin and distinct planets at
  deterministic, coplanar positions. No new entity IDs are manufactured.
- Physical radii in km. Stellar radii use class-specific generation ranges;
  legacy chart radii are not treated as physical solar-radius measurements.
- Epoch turn 0, explicitly frozen motion, with declared aligned planet axes:
  +Y north, longitude zero +Z, longitude +90 degrees +X. No rotating orbital
  ephemeris, cross-system distance frame, climate or gravitational simulation.
- Separate generation stream; the default path omits the optional block entirely.
  Existing terrain, province IDs, resource rules and generated legacy outputs stay
  unchanged. The new block is part of the immutable snapshot, including restore.

`app/astronomy.py` generates, strictly validates and explicitly projects the data.
Validation rejects unknown headers/fields, boolean epochs/coordinates/radii,
nonfinite/out-of-range positions, wrong or missing entity references, empty or
starless systems, multiple origin stars and physically intersecting bodies. The
intersection check uses integer arithmetic and the exact AU conversion. Public
snapshots/maps expose only surveyed systems and surveyed bodies, with no hidden
IDs, positions, counts or private generation metadata.

The orbital view shows the selected planet's recorded host star, its name/class,
and `Epoch 0 · static · symbol not to scale`. The warm marker is an interface
symbol, not a photometric rendering or angular-size measurement. Decorative field
points remain decorative. Planet positions are saved for consistency; this slice
does not draw neighbouring planetary discs or supply interstellar constellations.
The system chart remains explicitly topological.

The marker and globe share the same perspective camera, including finite observer
parallax from the camera's distance and saved planet radius. The star's saved
planet-centred direction also controls globe illumination. Old campaigns retain
the existing presentation light and have no new named star. In Orbit they show a
disabled **Star unlocated** control explaining that positions are not recorded. Default entry keeps
home terrain context; **Locate star** explicitly moves the camera to a usable
view of the actual source. Normal Surface/Orbit and management returns preserve
context. Historical views consume their saved records and remain read only.

For a new native demo, using the configured local PostgreSQL environment:

```sh
.venv/bin/python -m app.cli init-v2 --campaign-id astronomy-demo \
  --seed 731609 --planet-generator planet-v10 --preset continental \
  --astronomy static-v1
```

Use a fresh campaign ID; creation rejects an existing ID. Astronomy defaults to
absent. The orbital UI requires the existing native V10 globe support. Existing
records cannot be converted through this command.

## Independent review and corrections

One bounded Sol high review owns the optional persistence/public contract. It
accepted the final strict validation, legacy compatibility, privacy and observed
transaction/history/restore checks. All 15 backend hashes match the frozen source
and stress report. A later bounded continuation resolved a new camera integration
issue without changing that accepted backend.

The first frontend passed vector/identity checks but used the decorative sky's
wider perspective for the named star. Root review caught that evidence gap: a
correct saved direction alone did not prove correct apparent placement. The
candidate and its passing but insufficient report are retained under ignored
`rejected-projection-browser`. One localized Sol medium correction introduced
exact recorded-body projection, observer parallax and corrected Locate math.
High independently checked 2,000 poses: finite surface projections agree with the
existing globe within 1.84e-12 px and reconstructed rays within 3.73e-16. Committed
Node/browser tests now independently reconstruct the actual shader camera ray.

The same correction preserves initial terrain context and routine return
orientation, displays historical astronomy, and prevents offscreen labels from
being clamped falsely into view. A fresh Sol medium visual critic first examined
anonymous full-frame states without source or prior verdicts. Its concrete
findings were a dark night-first entry, tiny metadata, caption overflow and a
conditional concern about offscreen recovery. Default home context is preserved,
metadata is now 10px, the widened caption fits, and actual Locate recovery passes.
The same critic accepts the final visual and tested interaction scope with no
unresolved major stellar-feature issue.

**Retained medium limitation:** surveying the unlit hemisphere is dark. It is a
nonblocking limit for the explicit stellar-inspection view, not proof of optimal
night-side terrain selection. Existing stepped material boundaries and polar
texture artifacts remain separate. No cinematic, photometric, commercial-game or
full astrophysical accuracy claim follows.

## Functional and preservation evidence

Ignored evidence is under `data/celestial-stars/`:

- `tests/test_astronomy.py` plus existing V2 acceptance/movement projection tests:
  13 methods pass. They cover exact pre-change private/public default digests,
  isolated deterministic/order-independent generation, malformed records,
  surveyed-only projection/private-marker exclusion, real preview/commit,
  immutable history, exact restore, duplicate-ID rejection and private API access.
- The retained legacy corpus passes 120 cases / 240 private/public hashes with no
  differences (128.93 s). `legacy-verification.json` records the actual count.
- Connected PostgreSQL stress with `WOLD_STRESS_ASTRONOMY=static-v1` passes 10,000
  persisted turns, checking unchanged astronomy every turn and at historical
  checkpoints, exact restoration, population/resource/budget conservation and
  existing connected mechanics. It uses V1 cartography: this tests persistence
  and simulation compatibility, not native renderer scale. Report: `stress-v2.json`.
- A separate isolated native V10 demo is actually generated with astronomy and
  retains it through a real committed turn. `preview-creation.json` records the
  fixture. An initial QA proposal used an invalid allocations dictionary and was
  rejected before commit; correction to the documented list required no terrain
  regeneration or snapshot replacement. CLI creation was separately exercised.
- `browser/workflow.json`: actual Chromium drag, globe occlusion, turn-away,
  mouse/touch Locate, theme invariance, actual GL light uniform, independent
  finite-distance camera-ray oracle, management return, Surface/Orbit longitude
  retention, historical sky/read-only orders, legacy/pregame absence, retained
  main map canvas, no idle sky redraw, unchanged records and no page errors.
  `00-home-context` and `01-recorded-star` distinguish default and explicit Locate.
- `legacy-orbit/workflow.json`: existing native fixture still supports zoom/reset,
  rotation, overlays, management/Surface returns, touch, unchanged main canvas,
  forced WebGL context loss and missing-WebGL surface fallback, with no page errors.
- Original five preview campaign projections have identical before/after hashes.
  No real records, cloud data, seeds, credentials, databases or runtime artifacts
  enter Git. All backend freeze hashes still match after verification.

The new browser hooks forward both the star data and lighting argument so QA
exercises the real feature rather than silently dropping those arguments. No
recorded motion divergence exists in this frozen epoch fixture; historical tests
do not establish a future moving-orbit model. No new motion recording was made,
and screenshots/logged endpoints do not prove native-rate smoothness.

## Browser and performance limits

Primary coverage: Linux, Chromium 154.0.8037.57, 1440×1024 desktop with mouse/touch
input. Native macOS Safari and WebKit remain unverified. No new native browser-zoom
certification or exhaustive seed/viewport coverage is claimed.

The isolated 10,000-turn fixture took 211.76 s, saved 10,001 source snapshots
(390,084,162 state bytes), and measured a 6.2 ms current read and 134.5 ms 50-row
history read. Work ran in a shared QA workspace with legacy compatibility checks
overlapping part of it. These are one synthetic fixture's local observations,
not production-scale capacity or renderer performance.

No new map terrain, GPU textures or free-running animation loop is introduced.
The stellar point adds a small gradient/disc and one reusable DOM label; existing
sky scratch and transition bounds remain. CPU draw timing excludes GPU/raster
completion. Delivery remains an interface release candidate, without merge,
deployment or newly verified operational backups/recovery.


Final desktop supplement (`desktop-supplement/report.json`) passes label and
caption fit plus Locate reachability at 1280×960, 1920×1080 and 1440×1024. Twenty
repeated Locate actions retain the same main canvas and star-label element, one
star DOM node, and zero active app transition composites after settling. With an
unchanged pose, cached sky CPU command time has median 0.20 ms, p95 0.40 ms, max 0.40 ms;
orbital render submission has median 0.10 ms, p95 0.10 ms, max 0.20 ms (20 samples each).
These are warm, repeated-pose API submission measurements, not changed-pose noise
cost, input latency, GPU completion or game FPS. No page errors. WebKit's expected
Playwright executable was absent; no installation or Safari test is implied.

Replay the bounded gates against disposable test schemas and an opt-in preview:

```sh
WOLD_TEST_DATABASE_URL=... .venv/bin/python -m unittest tests.test_astronomy tests.test_v2_acceptance tests.test_movement_projection
WOLD_TEST_DATABASE_URL=... WOLD_STRESS_ASTRONOMY=static-v1 .venv/bin/python tests/stress_v2.py 10000
node tests/check_orbit.cjs
node tests/check_orbit_background.cjs
WOLD_CELESTIAL_BASE=http://127.0.0.1:4206 .venv/bin/python tests/browser_celestial_stars.py
```

The ignored QA preview uses a newly created isolated schema on loopback port 4206;
the original preview on 4203 retains all its original records. A separate CLI demo
also verifies opt-in creation. These are local fictional QA data, not deployment
or recovered campaign databases.
