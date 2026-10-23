# Cylindrical planetary charts

Branch: `map-generation`, following continuous-chart release `583eec1`.
Desktop only. Scoped navigation critique and the10,000-turn persisted fixture
gate passed. This is an interface release candidate, not a deployment.

## Baseline and architectural decision

Fresh Chromium drags on committed V5 reached its finite east/west limits.
Full-frame ignored captures: `data/planet-wrap/baseline-{west,east}.png`.
This milestone extends that accepted finite chart with genuinely periodic
longitude; it does not tile legacy regional maps to invent additional geography.

One bounded GPT-6.1 Sol high review approved opt-in `planet-v6`,128×80 canonical
samples, forty16×16 province rectangles and explicit `topology: "cylinder-x"`.
Periodic integer noise, land influence, coast, climate and flood drainage share
the same seam. Latitude remains bounded. A seam-only ocean-outlet fixture
checks actual cross-seam drainage/river connectivity, acyclicity and exact
accumulation. Arid/Barren/Frozen retain disabled hydrology and no open water or
vegetation. Presets remain independent creation-time choices per planet.

The client normalizes longitude for camera/hits and renders translated views
of that recorded world. Raster interpolation, contours, rivers, province borders,
overlays, labels, selection and military anchors share its projection. Short
endpoint connectors and split overview footprints cross the seam consistently;
display-copy coordinates never enter orders or persisted state. Connectors
remain recorded endpoints, not simulated terrain paths or interpolated travel.
Two-phase raster/annotation drawing prevents a neighboring strip overpainting
labels. V6 route SVG is clipped to the viewport.

Default generation stays V1. No existing records are converted, regenerated or
overwritten. Schema, numeric rules, movement costs, archive paths, authentication
and history authority are unchanged. Whole-planet survey filtering remains the
existing intelligence boundary; no partial reconnaissance model was added.

## Independent backend review and compatibility

The Sol high reviewer found no critical or major backend defect. It independently
matched45 private/public SHA pairs against isolated committed `583eec1`: V1–V5,
seeds0/55/741903, and every preset where supported. It validated all six V6
presets through Store, malformed topology/config rejection, hidden/detected
exclusion, nested surface allowlists and defensive array copies. Seeds/private
configuration remain excluded from player data. Backend source was frozen for
the persisted-turn gate; retained hashes are in ignored
`data/planet-wrap/backend-frozen-hashes.json`.

Luna built the bounded first candidate. Browser use exposed a caught
`cylinder is not defined` error before map presentation; the localized Sol medium
escalation corrected that scope and neighboring-strip annotation overpainting.
It also clipped V6 route SVG while retaining legacy overflow behavior.

## Functional verification

Full Python discovery: **98 tests passed in221.872s**, with isolated PostgreSQL17
and existing QA `pg_dump`/`pg_restore` tools on PATH. New checks exercise periodic
noise, six presets/determinism, seam-only drainage, topology validation and V6
CLI/configuration without changing the default. Existing persistence, history,
restore, privacy and numeric-rule checks remain part of discovery.

Existing desktop V5 navigation, V4 preset, V3 cartography, protected movement
and broad strategic browser regressions passed on the candidate. The V6
workflow passed across six presets and both styles: repeated seam traversal,
full raster coverage, inverse cursor zoom, canonical seam-cell selection, holding
selection on every overlay, Economy → Construction → Map, unchanged theme
pixels,1280×720/1920×1080 resize, real seam DRAFT/PREVIEW/commit and read-only
history → live return. Canvas identity and window/map handler counts remained
stable; no page errors occurred. Final V6 delivery rerun and protected legacy
movement rerun passed after the minor presentation fixes. Active Forces hover
contrast and legend/overview non-overlap are now explicit browser assertions.
Long-run results are recorded below. Test scaffolding was corrected to wait for attached
horizontal SVG connectors (zero geometric height), asynchronous historical map
readiness and the actual historical Orders message; these were test assumptions,
not additional product defects.

## Performance environment and limits

Shared Linux, Python3.12, PostgreSQL17, system Chromium154.0.8037.57;
1440×1024 direct-render samples while mixed V6 stress/browser QA also ran.
One cold sample and ten synchronous warm draws per preset/style exclude API,
input, force DOM, compositing and GPU residency. Raster cap remains1536×960.
Cold direct draws measured309.5–784.6ms; ten warm draws averaged1.7–18.9ms
per preset/style. Final campaign-to-first-draw samples ranged597.7–2142.1ms, including
API/projection and initial rendering. These samples
ran under concurrent QA, not controlled before/after benchmarking. Long-run
observations are recorded below.
No production-scale throughput or frame-rate claim is established.

## Integration and use

```sh
python -m app.cli init-v2 --campaign-id NEW_ID --planet-generator planet-v6 \
  --preset auto --planet-preset NEW_ID-planet-reach=barren
```

This intentionally creates only a new fictional demo in the explicitly configured
database. Existing IDs are refused. Per-ID overrides remain independent; never
use creation to replace records or disguise missing original cloud data.

No schema migration or character-relationships branch edit. Integration with
unrecovered cartography should retain saved generator versions/topology and
public allowlists, rather than loading old charts as V6. Latitude/poles remain
planar and bounded; there is no spherical traversal. Geology families, gas giants,
natural province boundaries and persistence deduplication remain separate work.
Full immutable geography arrays still impose the previously demonstrated history
latency/storage cost; this milestone does not solve it.

## Planet-photo question during implementation

The current maps are stylized strategic charts, not validated geological
reconstructions. Continental/Archipelago/Oceanic/Arid/Barren/Frozen describe
water and surface conditions; they do not yet distinguish cratered regolith,
basalt plains, fractured ice, volcanic resurfacing or atmospheric cloud bands.
The Moon, Europa and Io illustrate different geological families. Saturn would
need atmospheric/orbital presentation rather than a terrestrial province map.
Any future body-family options must remain separate creation-time choices,
rather than blending water, vegetation, craters and ice onto every world.

These are design recommendations, not additional implemented V6 features.
Attempts to fetch new NASA image-library references returned403 in this
environment; no fresh photograph-side-by-side assessment is claimed. Wrapping
improves navigation and topology but does not establish physical realism.


The actual V6 continental, barren and frozen full-frame captures were inspected.
Continental rivers can appear excessively straight/uniform; barren/frozen
surfaces mostly read as recolored relief rather than recognizable geology.
The current art is sufficient for chart-navigation testing, not finished
planetary authenticity. A future acceptance pass should compare equivalent
map scales and body families against accessible primary photographs: crater
bowls/rims and basalt plains for lunar terrain, fractures/ridges for icy moons,
volcanic fields for active bodies, and atmospheric bands/vortices for gas giants.
Do not add blue rivers to dry worlds or fictional strategic/economic readings
merely to make a screenshot resemble a reference.


## Independent visual and interaction outcome

A fresh GPT-6.1 Sol medium critic first inspected anonymous full-frame A/B
captures without implementation discussion or origins. A was actual V5 at its
west limit; B was a V6 arid chart. It preferred A's captured landmarks and
composition for orientation, but expressly declined an overall release preference
because terrain/scale/information loads differed. No commercial-game or fresh
planet-photo comparison is established by that pair.

The same critic then used the actual isolated Chromium preview. Seven successive
westward drags retained terrain; seam-side selection, wheel zoom, overlays,
keyboard overview centering,1024×768 resize and Economy → Construction → Map
worked. The latter retained the selected province and pixel-identical map.
It directly verified real transit connector visibility, overview pointer input
with inspector open, and unchanged map pixels after wheel/drag inside inspector.
Root's broader six-preset/protected-order/history/security coverage is separate
provided QA, not the critic's direct interaction evidence.

Concrete findings and responses:

- Medium: active Forces text disappeared on hover. Root identified selector
  specificity against the generic hover rule; explicit active/hover/focus rules
  retain Apple's existing blue token and opaque white text. Builder measured
 4.57:1 in light/dark normal/hover/focus; critic directly confirmed the corrected
  normal/hover/focus colors. No new palette replaces the user's Apple choice.
- Medium: connector legend obscured the shifted overview. Move the legend to
  upper-left, retain pointer transparency, and include its measured rectangle
  in existing military counter obstacles. The same critic reproduced its prior
  collision position and verified39px clearance (legend bottom281, badge top320).
  The overview remains clear with inspector.
- Low/medium: split viewport boxes and `CYLINDER X` were unexplained. V6 now
  says `EAST–WEST WRAPPING`, captions the overview `EAST ↔ WEST JOIN`, and provides
  explicit split-box/bounded-latitude help. Legacy captions remain unchanged.
- Low: orphan label leaders continued under chrome. Clip V6 label leaders to
  the existing clear bounds while preserving true anchors and label hit targets.
  Do not clip the default y192 transit connector out of view merely to improve
  spacing; its original coordinates and visible endpoint readout remain honest.

Final scoped critic verdict: **accept periodic-longitude desktop navigation**,
with no blocking observed navigation defect. It does not accept photographic
realism, overall V6 art superiority, production readiness or whole-game parity.
Remaining minor points are small metadata and a visible polar-route connector
close to the breadcrumb. Uniform terrain limits orientation and planetary
identity; the photo assessment above keeps that art limitation explicit.

| Representative task/reference actually examined | Strength or gap | Response and evidence | Review limit |
| --- | --- | --- | --- |
| E/W navigation against actual committed V5 | V5 has finite chart limits | Opt-in periodic V6 fields and common projection; root seam regression and critic repeated drags | No spherical/polar traversal |
| Selected province → Economy → Construction → Map against existing workflow | Retain strategic context through management | Pixel-identical map and selection; root/critic actual workflow | Existing recorded economy mechanics, no new diagnostic model |
| Owned movement against existing military presenter | A longitude seam needs a short truthful endpoint connector | Canonical real preview/commit; shared anchor projection and translated visible segments | Connectors are not simulated routes; small header clearance remains |
| Barren/frozen appearance against proposed planetary photo standard | Missing recognizable geology families | Gaps documented from actual captures; no fabricated photo study or cosmetic claim of accuracy | New NASA fetch403; geology work remains unimplemented |


Final browser evidence is ignored under `data/planet-wrap/`: `wrap-metrics.json`,
`{continental,archipelago,oceanic,arid,barren,frozen}-regional.png`, seam draft/
preview/transit/history captures, `performance.json` and legacy regression folders.
Independent original/recheck captures are in `/workspace/scratch/critic-browser/`;
these are transient runtime evidence, not campaign recovery or tracked assets.
Chromium154 is verified. Linux WebKit binaries/native macOS Safari were
unavailable and remain unverified. Older responsive checks in legacy scripts
are supplementary; no mobile acceptance is claimed for this milestone.


## Final persisted-turn gate and delivery

Mixed V6 arid/archipelago/oceanic/frozen fixture: **10,000 turns PASS in2722.03s**,
10,001 immutable source snapshots, final owned population1199. Every turn checked
people/resources/treasury reconciliation; checkpoint hashes, original timeline
and exact independent initial-state restore passed. Largest serialized state
956,759 bytes; summed source-state JSON7,481,633,246 bytes (not physical database
disk use). Current read60.0ms;50-entry history3721.7ms. Full repeated geography
arrays remain a material storage/history cost, not a resolved production concern.

The ignored `data/verification/stress-v6-wrap.json` records all backend source
hashes. Its hashes equal both the pre-run frozen manifest and final source.
All tests used disposable schemas in the explicit isolated QA PostgreSQL;
no real campaign database or recovered original cloud records were used.

Final source/diff checks pass. Delivery commits are recorded in the branch
record after creation; no merge, deployment or data reset is part of delivery.
The next substantive art milestone should introduce versioned geological/body
families, informed by actually accessible reference photos, independently of
water/vegetation presets. A persistence optimization needs its own bounded
high review. Neither is silently bundled into navigation acceptance.
