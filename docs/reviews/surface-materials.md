# Lake materials and polar caps

Branch `map-generation`, following verified V7 delivery `ed66cb6` / `84ecff5`.
Status: V8 scoped backend, visual/interaction and final persisted-turn gates
passed. Implementation **`50a4afa`**; V7 acceptance is recorded separately.

## Authorized scope and architecture

The user requested lava lakes, other liquid lakes and polar ice-cap generation
options. Add opt-in V8 creation options independently of existing surface presets
and cratered geology. Preserve all V1–V7 outputs and existing campaign/history
records; never regenerate established maps.

A bounded Sol high review selected saved binary lake and ice masks on the existing
128×80 cylindrical grid. Explicit lake choices: none, water, hydrocarbon, lava.
Explicit cap choices: none, water-ice. Each layer has an independent creation input;
changing lake material must not silently introduce oceans, vegetation or craters.

Hydrocarbon lakes are supported only on Frozen; water/lava only on nonfrozen
presets. Lava plus water-ice caps is unsupported in this first bounded slice.
These are deliberately limited authoring combinations, not a planetary climate,
pressure or thermodynamic model. Other fictional chemicals, liquid metals,
cryovolcanism and gas atmospheres are not implied by “other liquids”.

Masks are saved authoritative composition records. The browser renders them,
without selecting new features or creating random lake geometry. Lakes occupy
land away from settlement-placement anchors and caps; caps can cover ocean or
land, with irregular periodic latitude boundaries. Existing elevation, terrain,
climate, hydrology, provinces and numeric simulation rules remain unchanged.
Ice can cover a holding; it must not develop artificial holes around every town.

These features annotate recorded surface composition. They do not establish
new movement barriers, hazards, extractable resources or production values.
Those mechanics require separately approved rules. Avoid visual claims that
suggest such mechanics already exist.

## Verification and review gates

Before delivery: strict malformed/compatibility/configuration validation;
determinism and independent-option tests; exact committed V1–V7 hash comparison;
surveyed-only explicit projection and defensive-copy tests; persisted history/
restore checks; relevant regression tests and the required 10,000-turn V8 gate.
Then actual full-frame browser captures and workflows, independent critique,
concrete corrections, bounded performance and documented browser coverage.
No acceptance, realism or performance result is claimed until observed.

## Backend evidence

The first Luna attempt left integration incomplete and was escalated to localized
Sol medium implementation. A small `app/planet_materials.py` replaced that partial
helper. Separate full private maps record per-planet lake materials and caps;
strict nested surveyed surface projection exposes only the four explicit keys.

The same bounded Sol high reviewer accepted the final backend with zero critical/
major findings. It independently checked all 90 committed V1–V7 private/public
pairs (180 hashes, including nine cratered V7 cases): no mismatches. Its 34 V8
variants across all presets retained exact V7 base dictionaries; hidden/detected
material canaries were omitted. Lakes reserve anchor halos; ice stays continuous
over holdings. No engine, schema, authentication or archive path was changed.

## Initial independent visual critique

A fresh Sol medium critic first examined anonymous full-frame 1440×1024 images
before receiving provenance, implementation discussion or any previous verdict.
The set contained 200% lake details and 100% cap overviews for distinct worlds;
it was expressly not a winner comparison between different information loads.

It identified new lakes as flat cutouts with abrupt, regular corners, and lava's
orange rim as a possible selection/glow cue. It also flagged river tails extending
past shores, unclear settlement anchoring/occluded labels, repeated crater rings
and coarse blurred biome blocks. The latter two are inherited V7 limitations;
they remain recorded rather than being presented as new realism achievements.
New material finish and concrete navigation findings require correction/recheck.
Interaction assessment and the persistence gate were pending at this initial
candidate; their final outcomes are recorded below.

## Creation interface

These are new-campaign CLI authoring options, consistent with existing generator
options; no player-side creation dialog or mutable in-campaign terrain toggle is
introduced. Omitted options select no lakes/no caps; the overall default remains
V1. Existing campaigns refuse duplicate creation and are never converted.

```sh
python -m app.cli init-v2 --campaign-id mantle --planet-generator planet-v8 \
  --preset barren --geology cratered --lake-material lava

python -m app.cli init-v2 --campaign-id boreal --planet-generator planet-v8 \
  --preset frozen --geology cratered --lake-material hydrocarbon \
  --polar-caps water-ice

python -m app.cli init-v2 --campaign-id pelagic --planet-generator planet-v8 \
  --preset continental --lake-material water --polar-caps water-ice
```

These commands create fictional demo campaigns in the explicitly configured
database. Per-planet `--planet-lake-material ID=CHOICE` and
`--planet-polar-caps ID=CHOICE` override globals using existing stable planet IDs.
Duplicate/unknown IDs, invalid combinations and explicit material flags on legacy
generators fail. Generation seeds and private choice maps stay server-side.

## Corrected candidate and observed checks

The bounded frontend correction uses inward shore transitions, mask-interior
basin distance, recorded elevation tint and existing fine surface grain. Lava
now has a dark cooling margin with a warmer interior rather than a luminous
selection-like keyline. Liquids do not inherit terrain hillshade. The renderer
trims outlets at the first recorded sea-height crossing, including longitude
seams, and covers river/contour ink beneath saved lake/ice layers.

V8 annotation ink is clipped to the safe map area. Holdings whose north/south
anchors are obscured retain accessible tags with explicit directional edge
triangles and tooltip explanation; offscreen duplicate world anchors no longer
produce misleading clamped tags. Actual saved lake/ice composition appears in
hover text separately from underlying ground. Camera/selection are preserved.

122 Python tests passed in 389.713 s in the isolated QA PostgreSQL environment.
Focused Node checks exercise actual raster code for saved-mask centres and seams,
solid poles, material palettes, restrained texture without inherited lake
hillshade, recorded river crossings and safe accessible edge labels. Existing
crater canonical/seam/dry-lowland checks also pass.

The first protected V8 browser candidate timed out selecting Forge in an overlay
loop. It is preserved as a failure, with diagnostic capture support added to the
runner. After the annotation correction the full protected run passed six
presets/both styles, repeated seams/coverage, canonical province and holding
selection on every overlay, management camera/selection return, stable theme
pixels and desktop resize, real recruitment/movement draft/preview/commit,
historical read-only return, unchanged fixture hashes and stable canvas/handlers.
No exercised page errors. That success does not replace independent visual review.

A fresh Chromium 154 browser run at 1440×1024 observed campaign-to-first-draw
961.5–1467.1 ms on shared Linux with a concurrent persisted-turn gate. This is a
fixture observation, not controlled before/after benchmarking or production FPS.
Full captures and metrics remain ignored under `data/surface-materials/`.


## Same-critic final scoped outcome

After fresh corrected captures and a declared frontend freeze, the same critic
accepted V8 with no remaining critical/major issue in its new material/annotation
findings. It confirmed the selection-like lava keyline gone, inward shoreline
transitions and subtle interiors integrating with ground, and outlets ending at
shore. Offscreen north triangles/leaders explain the previously floating row.

Its actual frozen browser recheck at 100% hovered Forge's explicit north-anchor
message, clicked its tag to select Province 02 and Forge (900 recorded residents) without camera relocation,
and hovered hydrocarbon to read both composition and underlying Ice field.
1024×768 retained the full header, legend, status and inspector. Its earlier
bounded Economy/Construction/context, themes and four-level navigation checks
were recorded separately; only its frozen recheck is final material acceptance.
It discarded a capture that raced cold campaign loading instead of treating the
transient “No recorded geography” message as a permanent missing-record defect.

Remaining minor finish limits: 128×80 lake outlines can look coarse at 200%, shore
softness, small legend/meta type, and a long composition hover tooltip can extend
behind an open right inspector (core composition remains visible). Inherited
repeated concentric craters, overlapping bowls, broad biome blocks and axial
rivers remain limits. No lunar/Titan photographic, thermodynamic or commercial
game quality parity is established. New reviewed references were actual matched
application states and recorded masks, not externally recovered planet photos.


## Final persisted delivery gate

Mixed V8 Barren/Archipelago/Oceanic/Frozen, with lava/water/hydrocarbon lakes,
water-ice caps and separately selected dry cratered geology:
**10,000 turns PASS in 3291.49 s**. All 10,001 source snapshots remained intact;
every-turn conservation, checkpoints/history and exact independent initial-state
restore passed. Largest serialized state 1,050,779 bytes; summed source-state
JSON 8,408,795,953 bytes (not physical database disk consumption). Current read
75.1 ms; read of 50 history records 5558.8 ms. Full-geography repeated snapshots remain a
material inherited storage/history-performance limitation, not a solved
production-scaling concern.

All 11 backend source hashes equal the initial frozen manifest, completed report,
current source and pushed implementation `50a4afa`. The gate used only isolated
QA PostgreSQL and its own disposable schema. No live records, credentials,
databases, generated fixtures or runtime captures are committed.

Legacy V7 protected navigation and V3 cartography browser regressions also passed.
An additional actual Chromium tab-zoom check used a disposable browser profile,
Chrome Settings 100/125/150/200% zoom, physical window 1920×1280 and full CDP
captures 1920×1193. CSS viewports ranged 1920×1193 to 960×596 with visual scale 1.
The V8 material legend, command/campaign/map controls, Economy return and hierarchy
remained operable/in bounds, without page errors. This is desktop Chromium 154
coverage; WebKit executable is absent and native macOS Safari remains unverified.
Mobile acceptance is excluded per user direction.

Continue by authoring new fictional campaigns through explicit V8 options.
Integrate unrecovered cartography through versioned saved contracts and surveyed
allowlists, without converting established maps. Additional liquid compositions,
fractures/volcanic terrain, thermodynamics and traversal/resource hazards require
separate scoped work. No original cloud data recovery, character-relationships
branch edit, merge, deployment, operational-security certification or scientific/
whole-game commercial parity is claimed. This is an interface release candidate.


## Rendering measurements and environment

Shared Linux 6.18.55/glibc 2.41 with 2 CPU quota, Chromium 154.0.8037.57,
1440×1024 viewport and 1536×960 cached rasters; four saved material fixtures
in both Orbital/Survey styles (eight samples). After the stress and regression
processes completed, one cold direct draw per case ranged 323.8–856.7 ms;
ten synchronous cached-draw averages ranged 1.09–5.23 ms. Earlier concurrent
stress/browser load samples ranged 812.6–2103.9 ms cold and 2.31–18.53 ms warm.
These uncontrolled observations do not establish an attributed speedup or
production-scale performance. They exclude input, API, force DOM, compositing
and GPU residency; they are not frame-rate measurements. Actual campaign-first-
draw timings from the protected browser run are recorded above.

Ignored evidence: `data/surface-materials/performance.json`,
`performance-quiet.json`, `corrected-browser/wrap-metrics.json`,
`browser-zoom/metrics.json` and `data/verification/stress-v8-materials.json`.
The independent critic's frozen screenshots are under scratch/material-critic;
product captures remain in ignored `data/surface-materials/corrected/`.
