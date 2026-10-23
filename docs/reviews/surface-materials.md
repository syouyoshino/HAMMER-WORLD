# Lake materials and polar caps

Branch `map-generation`, following verified V7 delivery `ed66cb6` / `84ecff5`.
Status: corrected V8 scoped visual/interaction and backend reviews accepted;
final 10,000-turn delivery gate remains in progress. V7 acceptance is separate.

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
major findings. It independently checked all90 committed V1–V7 private/public
pairs (180 hashes, including nine cratered V7 cases): no mismatches. Its34 V8
variants across all presets retained exact V7 base dictionaries; hidden/detected
material canaries were omitted. Lakes reserve anchor halos; ice stays continuous
over holdings. No engine, schema, authentication or archive path was changed.

## Initial independent visual critique

A fresh Sol medium critic first examined anonymous full-frame1440×1024 images
before receiving provenance, implementation discussion or any previous verdict.
The set contained200% lake details and100% cap overviews for distinct worlds;
it was expressly not a winner comparison between different information loads.

It identified new lakes as flat cutouts with abrupt, regular corners, and lava's
orange rim as a possible selection/glow cue. It also flagged river tails extending
past shores, unclear settlement anchoring/occluded labels, repeated crater rings
and coarse blurred biome blocks. The latter two are inherited V7 limitations;
they remain recorded rather than being presented as new realism achievements.
New material finish and concrete navigation findings require correction/recheck.
Interaction assessment and the full persistence gate are still in progress.

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

122 Python tests passed in389.713s in the isolated QA PostgreSQL environment.
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

A fresh Chromium154 browser run at1440×1024 observed campaign-to-first-draw
961.5–1467.1ms on shared Linux with a concurrent persisted-turn gate. This is a
fixture observation, not controlled before/after benchmarking or production FPS.
Full captures and metrics remain ignored under `data/surface-materials/`.


## Same-critic final scoped outcome

After fresh corrected captures and a declared frontend freeze, the same critic
accepted V8 with no remaining critical/major issue in its new material/annotation
findings. It confirmed the selection-like lava keyline gone, inward shoreline
transitions and subtle interiors integrating with ground, and outlets ending at
shore. Offscreen north triangles/leaders explain the previously floating row.

Its actual frozen browser recheck at100% hovered Forge's explicit north-anchor
message, clicked its tag to select Province02/Forge900 without camera relocation,
and hovered hydrocarbon to read both composition and underlying Ice field.
1024×768 retained the full header, legend, status and inspector. Its earlier
bounded Economy/Construction/context, themes and four-level navigation checks
were recorded separately; only its frozen recheck is final material acceptance.
It discarded a capture that raced cold campaign loading instead of treating the
transient “No recorded geography” message as a permanent missing-record defect.

Remaining minor finish limits:128×80 lake outlines can look coarse at200%, shore
softness, small legend/meta type, and a long composition hover tooltip can extend
behind an open right inspector (core composition remains visible). Inherited
repeated concentric craters, overlapping bowls, broad biome blocks and axial
rivers remain limits. No lunar/Titan photographic, thermodynamic or commercial
game quality parity is established. New reviewed references were actual matched
application states and recorded masks, not externally recovered planet photos.
