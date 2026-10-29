# Globe depth and celestial placement — 29 October 2026

The user asked for accurate neighbouring planets/stars, clearer globe depth, and
an explanation for the predominantly grey world in the latest screenshots.

## Recorded materials and corrected illumination

The current caps screenshot uses the existing fictional `material-caps` fixture:
its public surface records `barren`, `cratered`, `hydrology: none`, no lake material
and water-ice polar caps. Grey exposed rock is therefore intentional. The water
fixture is continental with ocean-draining hydrology; lava is barren with saved
lava lakes; hydrocarbon is frozen with hydrocarbon lakes and ice. No fixture was
regenerated or recolored to suggest unrecorded water, vegetation or atmosphere.
Saved public surface descriptors are in ignored `data/globe-depth/materials.json`.

The old orbital shader retained 72% illumination everywhere, limiting spherical
form. Three shader lines now use 30% ambient and continuous diffuse falloff with a
soft transition near grazing illumination. Geometry, camera/picking, texture
coordinates, pole filtering and albedo remain unchanged. This is camera-relative
presentation lighting for readable navigation, not a measured sun direction or
simulated astronomical day/night cycle. No atmosphere or terrain mesh was added.

## Independent visual and interaction review

Fresh Chromium 154, 1440×1024 full-frame caps baseline captures were taken before
editing; `candidate-final` repeats four exact poses/themes. `candidate` retains an
intermediate threshold-lighting version and was excluded from final comparison.
A fresh Sol medium critic viewed anonymous A/B images without origins or a desired
winner. It preferred B (new continuous lighting): visibly rounder, preserved rock/
ice discrimination, readable labels and no major visual blocker. It then viewed
nine water/lava/hydrocarbon frames in home/pullback/dark states and upheld acceptance.
Those fixtures visibly retain their distinct recorded material palettes.

Remaining polish: stepped material boundaries, somewhat flat-looking ice patches,
and faint radial lines inside water polar ice. Family baselines do not establish
these as new regressions. This change improves spherical form without claiming
physical realism or commercial/Google Earth parity.

Actual final-source orbital browser regression passes zoom/reset, native drag,
overlay camera retention, Surface→management→Map context retention, reversible
orbit return (longitude equivalent modulo 2π), mouse/touch controls, same main map
canvas, forced WebGL context loss and unavailable-WebGL surface fallback. No page
errors. Its report is `data/globe-depth/browser/workflow.json`. The independent
critic inspected this report and accepts scoped functional continuity. Endpoint
assertions and screenshots do not establish native-rate smoothness; the nominal
transition screenshot is not treated as every-frame transition proof.

Node projection/inverse/seam/pole/resource checks, settlement landmark checks,
actual sky bitmap/cache/seam checks, JS syntax and diff checks pass. Authentication,
history and turn-processing source are untouched; protected simulation/auth suites
and the retained 10,000-turn gate were not repeated for three shader lines.
No new textures, render targets, loops or handlers are introduced. GPU timings and
whole-frame FPS were not measured for this small shading change. Native macOS
Safari and WebKit remain unverified.

Final shader SHA256:
`602774732a38dd9144ca99174480ebd3b7b4c8e7bd0b2696ac14d5fe90619f0e`.
The app, surface renderer and background module remain unchanged. Runtime captures,
databases and context files remain ignored. No merge, deployment or real-data recovery.

## Accurate celestial positions: precise data blocker

One bounded Sol high read-only audit found that present records cannot determine
accurate apparent sky positions:

- `app/universe.py:44–50` assigns jittered 2D chart coordinates; these have no
  astronomical units, 3D frame, physical orbital elements or epoch.
- `public_state_v2` (`app/universe.py:235–247`) removes hidden bodies and nulls
  detected coordinates. Surveyed chart positions do not become sky bearings.
- `app/store.py:503–509` returns the safe system projection; planet maps contain
  the selected planet and visible moons, not a physical ephemeris.
- `public/app.js:371` explicitly labels the system chart topological, not orbital
  positions. ADR-013 prohibits inventing orbits or placing unknown coordinates.
- `public/planet-orbit.js:7–21` defines planet-fixed camera latitude/longitude;
  there is no astronomical spin/orientation reference or time epoch.

Accurate apparent placement requires approved public 3D body positions at a shared
epoch, or orbital elements sufficient to calculate them, consistent units/reference
frame and the selected planet's orientation/rotation. Apparent discs/brightness
would additionally require distance, radius and illumination information. Distant
star constellations need their own directional catalogue/reference frame. Current
background points remain explicitly decorative; none is labeled as a recorded
body or secretly positioned using chart coordinates.

Continuation: add a versioned astronomical contract only when its recorded inputs
and authority are available, preserve existing chart IDs, and project visibility
before serialization. Until then use the existing system breadcrumb/chart, which
already separates unlocated bodies. No duplicate locator panel or invented sky
positions were added. This is a precise feature blocker, not claimed completion.

Delivery implementation/review: `4335f6f` on `map-generation`.
