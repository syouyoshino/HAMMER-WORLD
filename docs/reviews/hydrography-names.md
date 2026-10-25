# Hydrographic identity and planetary chart review

Status: scoped UI/backend review accepted, representative browsers pass, and the
final frozen-backend V9 10,000-turn gate passes. Implementation `feaf766` is pushed.
Earlier V8 acceptance is not used as acceptance of the naming candidate.

## Examined references and limits

On 24 October 2026 we inspected Eleanor Lutz's paired Moon/Mars topographic
maps and Moon typography process from [Topography Atlas of Space](https://github.com/eleanorlutz/topography_atlas_of_space),
commit `17383b391bf2a982689ca1d1bd41cc914fd4c8ed`. The images are authored
DEM/hillshade cartography, not optical photographs. Their useful strengths are
region/local label hierarchy, geographic alignment, quiet graticules and readable
relief. The manual typography process is not evidence of automatic placement.
Artwork is CC BY-NC-ND 4.0 and remains unmodified, ignored research material;
no artwork, data or implementation is incorporated into the application.

We also examined Stellarium's [nomenclature data](https://github.com/Stellarium/stellarium/blob/master/data/nomenclature.fab)
and [display source](https://github.com/Stellarium/stellarium/blob/master/src/core/modules/NomenclatureItem.cpp),
retrieved 24 October 2026. Titan's Kraken Mare, Ligeia Mare, Punga Mare and Vid
Flumina illustrate named seas/channels. Display source checks projection and
apparent size, but does not demonstrate collision avoidance. No Titan chart image
was inspected. No Stellarium code is reused. A lunar mare is basaltic plains;
physical material must come from saved records rather than a name.

Network policy permitted native GitHub publications but excluded NASA/USGS/IAU
hosts. No new optical-photo comparison or physical/scientific validation is
claimed. Unmodified references and provenance are in ignored
`data/hydrography-pass/references/`; research notes in
`/workspace/scratch/naming-references.md`.

The reference globes contain much finer source data and many more named
landforms than this 128×80 cylindrical demo. They are compared for geographic
identity, hierarchy and label placement, not as equivalent information loads,
projections or evidence of overall visual parity.

## Fresh baseline and independent findings

Six actual Chromium captures at 1440×1024 cover water regional/chart view,
lake hover/click, lava chart and hydrocarbon chart. Exact sources, browser,
steps and page errors are recorded in ignored
`data/hydrography-pass/baseline/workflow.json`, at commit `2a3c16e`.
No page errors occurred in these exercised steps.

The independent Sol medium critic inspected all six captures and both Lutz
images before reading workflow metadata or implementation discussion. Findings:

| Severity | Affected task | Concrete finding | Required response |
| --- | --- | --- | --- |
| High | Select and identify a lake | Hover says Water lake / Ground Forest, click opens Province 20 / Main terrain Forest without lake identity | Carry actual feature identity/material into selection; province context secondary |
| High | Follow hydrography | Anonymous lakes share ocean color, thin cyan rivers lose their course in forest | Optional geographic labels, modest river contrast and selected emphasis |
| High | Read frozen/lava chart | Large repeated overlapping crater rings dominate small liquid features | Quiet existing relief weight without inventing different geology |
| Medium | Read coastline and terrain | Glowing soft stair steps and blurred biome slabs | Reduce avoidable glow; document inherited 128×80 data limit |
| Medium | Keep selected map context | Header and inspector obscure map locations; full chart has large empty ocean | Safe label placement and selected-feature visibility; preserve user camera |

Screenshots alone do not prove connected rivers, source/outlet correctness,
selection behaviour or campaign safety. Interaction and regression evidence will
be recorded separately after implementation.

## Workflow comparison record

| Workflow | Reference strength | Baseline gap | Implemented response / evidence | Critic verdict and limits |
| --- | --- | --- | --- | --- |
| Identify a connected sea/lake | Lutz regional names lie over their geographic region | No saved identity/name; lake click loses material | Saved catalog, inside names, one material inspector; RC03/04 and protected feature workflow | Accepted; coarse source boundary and simple body-kind convention remain |
| Follow and inspect a river | Lutz distinguishes local/regional type; Stellarium limits labels by apparent size | Thin course, no selectable river context | Readable unique-span names, blue course hierarchy, correct periodic projection and painted targets; RC01/05 and label-fixed4978/6036 | Accepted after panned-case diagnosis; sparse overview text and axial routes remain |
| Understand non-water geography | Moon/Titan nomenclature has body-dependent meaning | Names alone would be ambiguous for lava/hydrocarbon worlds | Explicit saved material, separate polar ice and name provenance; RC06/07/09 plus legacy surface probe | Accepted; no phase, hazard or physical-material simulation inferred |
| Return to strategic map | Static chart hierarchy keeps relief primary | Inspector could hide target and selected identity diverged | One bounded inspector, visible-cell selection, separate catalog scroll, camera/selection-preserving return; protected browser and native zoom evidence | Accepted scoped UI; static references do not establish interaction parity, high zoom consumes space |

## Integration boundary

Existing maps and immutable history must remain unchanged. Names are optional
new-map authoring metadata, not recovered real-campaign records. No simulation
resource, hazard, physical area, lake barrier or river travel rule follows from
a cartographic name. Recovered cartography must integrate through explicit
versions and surveyed-only public contracts.

## Backend review and preservation evidence

One bounded Sol high review of Luna's first concrete backend candidate found a
major nested-projection defect: spreading a feature dictionary exposed an
injected private canary. It also found a river anchor chosen from sorted cells
could fall on an ocean outlet, Unicode line/paragraph separators were accepted,
and malformed river inputs could fail before the existing structural validator.
The no-database catalog needs an explicit uncommitted-preview marker and a
stronger test of the actual database setting/constructor boundary. These are
assigned to a localized Sol medium correction; acceptance is pending correction
review. Saved canonical name validation is nonmutating, surveyed filtering and
set-based traversal were sound in the reviewed candidate.

Root captured 120 private/public V1–V8 cases from committed `2a3c16e` before
edits, then checked the candidate: all **240 hashes match**, 130.22 seconds
under shared test load. Cases include three seeds, six supported presets,
cratered geology and representative V8 water/lava/hydrocarbon/cap options.
Ignored exact records are `data/hydrography-pass/legacy-state-goldens.json` and
`legacy-verification.json`. Final corrections must preserve this result.

The same high reviewer accepted the localized correction after rerunning the
reported reproductions: nested private canaries are absent; the previously
misplaced river anchor is on recorded land; Unicode separators reject;
malformed rivers produce validation errors. Sol medium's ten focused tests
passed in 37.908 seconds with disposable PostgreSQL schemas, including exact
mixed-world V8 base preservation, independent custom names, public/player/map/
archive canaries, defensive copies, canonical-name nonmutation and history/
restore. Root froze all twelve backend Python hashes before frontend work and
started the final suite, final legacy comparison and V9 10,000-turn gate.
Their final outcomes remain pending below.

## Authoring and saved contract

V9 is opt-in; V1 remains the default. V9 wraps unchanged V8 and adds only a
saved `surface.hydrography` catalog and version change. No old records or history
are regenerated. No database migration or mutable naming endpoint is added.

```
hydrography = {version: "hydrography-v1", naming: "none" | "generated", features: [...]}
feature = {id, kind, material, cells, anchor, name, name_source}
```

`cells` are sorted unique saved-grid indices; `anchor` is an index in the feature.
Body components join four-neighbour cells across longitude, with bounded latitude.
The largest connected existing ocean-terrain component is called an ocean;
other components are called seas. This is a catalog convention, not physical
inference about enclosed seas. Lake components come only from the saved V8 mask,
with recorded water, hydrocarbon or lava. Ocean and existing river material is
water. Ice remains its separate recorded composition mask, including ice over
water. Anchors prefer suitable uncovered interior cells; river anchors follow
ordered saved paths and prefer non-ocean, non-lake, non-ice cells.

Existing river IDs represent headwater-to-outlet courses that can share a
trunk. They are not invented separate downstream waterways. Lake overlays do
not imply new drainage connections, movement barriers or resource rules.

Names are nullable. Sources are `none`, `generated` or `custom`; generated names
are explicitly fictional and independent of geography. Supplied names normalize
NFC and trim, require 1–80 Unicode code points, and reject controls and line/
paragraph separators. Persisted names must already be canonical; reading and
validation never rewrite them. Names remain plain text. Public projection copies
only the seven documented fields and nested cell lists, only for surveyed planets.

Creation preview (does not open a database or recover an existing map):

```sh
python -m app.cli init-v2 --campaign-id named-demo --seed 741903 \
  --planet-generator planet-v9 --preset continental \
  --lake-material water --polar-caps water-ice \
  --feature-names generated --catalog
```

The output status is `uncommitted_creation_preview`. Use its stable planet and
feature IDs to prepare a names file shaped as `{planetNodeId: {featureId: name}}`.
Repeat the **same** campaign ID, seed and generation choices with
`--feature-names-file names.json --catalog` to validate supplied names. Remove
`--catalog` only when deliberately creating that new isolated fictional demo in
the configured database. Duplicate JSON keys and unknown planet/feature IDs reject.
Existing campaign IDs cannot be replaced. The authoring catalog includes all
creation-time planets for the operator; it is not a player survey endpoint.
`--feature-names none` keeps identities inspectable without generated names and
still permits supplied names. Naming options are rejected on V1–V8, even explicit
`none`. There is no live rename operation in this release.

## Candidate 1: independent visual and browser critique

All eight fresh 1440×1024 Chromium images in
`data/hydrography-pass/candidate-1/` were independently inspected before the
critic read workflow metadata or source. This was a same-critic milestone
recheck, not a blind winner comparison. Labels were compared with the unchanged
Lutz references for the stated cartographic qualities only.

Accepted improvements: a selected lake retains its water/material identity;
inside labels generally associate with their actual lake shapes; geographic
text is distinct from settlement boxes; actual cell counts and province context
replace invented statistics. Names toggle preserved camera in the exercised run;
no page errors occurred in that capture workflow.

Unresolved findings, assigned to localized Sol medium after Luna's first
frontend candidate:

| Priority | Concrete evidence | Correction |
| --- | --- | --- |
| High | Image 05 footer/list select CororPyr, map still highlights FenaraFen lake; protected browser times out waiting for new renderer selection | Always redraw after feature/composition selection, even with inspector already open and no pan |
| High | Image 05 long list scrolls identity out of the panel and rows behind SELECTED RECORD | Bounded separate list scrolling, visible selected identity and reachable controls |
| High | 100/200% rivers look like heavy black angular pipes/borders | Reduce casing and use a visible blue centre on the same recorded course |
| Medium | Bright lake and province outlines compete | Give feature selection the primary accent; quiet secondary province context |
| Medium | Tiny, often vertical river names are difficult to read | Larger minimum type, stronger overview decluttering, useful course placement |
| High | Broad overlapping crater rims still compete with liquid shapes | Further quiet existing relief without new geology |
| Medium | Excessive coast glow remains | Reduce avoidable shore treatment; retain honest grid-limit documentation |

The original capture's `river_identity_visible_after_list_selection=true` was
an invalid visibility probe: it compared an overflowing content box instead of
the visible inspector panel. Manual image review rejects that boolean. The next
capture compares the visible panel bounds. The failure screenshot and original
record are retained; they are not replaced by a favourable test claim.

The first protected V9 browser run completed six presets/both styles before
failing on the first list-selected lake's renderer update. It does **not** count
as a full workflow pass. Root's final backend suite passed **132 tests in
408.988 s**, and final legacy comparison again matched **240 hashes** in
205.19 s under concurrent gate load. The backend remains frozen while frontend
corrections proceed.

## Candidate 2: accepted stills, broader functional defect retained

The same critic inspected all nine fresh root captures under
`data/hydrography-pass/candidate-2/`, then separately reviewed recorded workflows
and performed fresh Chromium keyboard/name-list interactions. The bounded
visual scope was accepted: lake/river identity and map emphasis agree; list
scrolling retains the heading; blue rivers and quieter rims restore hierarchy.
Sparse hydrocarbon chart labels were checked by selecting KelionIly from the
catalog at regional zoom: material, inside name and contour are present.
This is a minor fit/discovery tradeoff, not lost records.

Residual visual limitations: soft/coarse coast silhouette and broad biomes from
128×80 source sampling, rectilinear saved drainage, sparse chart labels, idealized
relief, and ice selection shown through province context rather than precise
single-cell emphasis. No physical/photo accuracy or overall atlas parity is
claimed. Reference typography/hierarchy improved; reference source-data detail
is not matched.

Root's fresh surface browser probe passed V8 unnamed-water composition and V9
polar-ice selection through Population overlay changes, with no page errors.
The protected broader V9 journey passed name mouse/keyboard/touch controls,
actual lake/river list records, collapse and Economy return, but then exposed a
missing painted-river-label case after substantial horizontal panning. It did
not count as a complete pass. An initial arbitrary-short-course test target was
improved to a recorded long horizontal course; the failure remained. The failed
viewport and public metadata are retained under `data/hydrography-pass/label-debug/`.

After two substantive river-label revisions, root requested a bounded Sol high
architectural diagnosis instead of further cosmetic iteration. It reproduced a
**high-severity coordinate bug**: `riverScreenPoints` mixed screen and world X
when unwrapping longitude. At the failed camera, the first four projected points
of river 4978 were `[464,-2813,-6064,-9341]` rather than `[464,464,489,489]`.
The base river raster remained correct, while labels and selected highlights
could drift offscreen. A second placement defect chose a global path midpoint
before checking visibility, discarding a usable visible unshared span. The
accepted correction is world-space unwrapping before projection plus deterministic
visible-span candidate placement with existing ownership, readability, fit and
collision restrictions. No backend, geometry or numeric rules change. Localized
implementation and the complete protected workflow remain pending at this entry.

Legacy V3 cartography browser regression passed. The broad strategic browser
completed its navigation/report/context/auth checks, then failed a native tab
zoom control-bounds check at 150% in a 1280×960 window. Localized CSS now lays out
the desktop toolbar at 781–1200 CSS pixels and keeps breadcrumb/Forces offsets
clear on compact heights. Focused bounds checks passed 853×582, 1280×960,
1440×1024 and 640×436; native Settings-based verification is recorded below.
The unchanged short-height policy hides the informational legend at <=550 CSS
pixels; it does not hide the interactive controls. That deliberate state is
excluded from an inappropriate always-visible-legend assertion.

## Final scoped review and desktop verification

The renderer correction was accepted by the same high diagnosis reviewer at
SHA256 `2009c345ec9a6b252e1a54243ca2ad56871ca3155461590931856e14fcde551f`.
Independent replay of the exact failed public fixture/camera now produces river
4978 and partially visible 6036 targets. Root's actual painted clicks select
those canonical records without camera changes. The separate app handler resolves
the painted label centre to a recorded member cell, retaining the saved anchor
for catalog selection and legitimate occlusion panning.

The same visual critic inspected nine fresh release captures, four panned-river
before/after captures, one actual maximum-length-name capture and eight native-
zoom captures before reading the bounded workflow metadata. Final scoped visual
acceptance has no remaining critical/major finding. Selection, river hierarchy,
inside label association, quiet relief, long-name wrapping and compact controls
hold. The original failures and invalid visibility probe remain documented;
there was no critic substitution or numerical score gate. The critic's own live
keyboard toggling and regional hydrocarbon selection were separate bounded
interaction evidence, not a claim to have performed every regression.

Complete protected V9 browser **PASS**, Chromium154, desktop1440×1024:

1. Enter six recorded presets and retain map coverage across repeated wrapped
   panning, both styles, zoom and all supported overlays — pass.
2. Toggle Names by mouse, keyboard and desktop touch without moving the map;
   expose every surveyed feature through Features — pass.
3. Select lake/river records and painted river names; keep actual material,
   identity and visible-map selection aligned — pass.
4. Collapse inspector and return from management with camera/selection intact;
   use unnamed/legacy states and supplied names honestly — pass.
5. Render a script-like supplied name as plain text, wrap all80 characters of
   a valid unbroken name, and clear feature context on campaign switch — pass.
6. Draft, preview and commit a real supported canonical seam movement, inspect
   historical state read-only and return live — pass.
7. Verify immutable non-target fixture hashes, stable canvas/window input
   handlers, no browser-stored authentication, then open Campaign & access and
   sign out through its visible control — pass; zero page errors.

The first added sign-out test attempted a hidden modal button and timed out;
correcting the harness to open Campaign & access produced the complete pass,
without changing product code. Earlier panned-label and max-length failures were
real product defects and were corrected before this pass.

Legacy V3 cartography and the complete broad strategic browser also pass. Broad
strategic24 warm cycles retain DOM nodes2661, CDP nodes5321/listeners195 and API
resource count47; the canvas persists. Under shared gate load its observed warm
navigation median24.61ms /95th67.53ms is fixture evidence, not a production budget.
Actual Chromium Settings zoom100/125/150/200% passes physical1280×960 and
1920×1280 windows (CSS down to640×436 and960×596), with new controls and selected
feature close operable. Root corrected an overbroad legend visibility assertion:
<=550px height intentionally hides informational legend/resource strip while
retaining command/map controls and inspection.

Four material fixtures ×two styles,1440×1024,1536×960 rasters, shared Linux
6.18.55/glibc2.41,2-CPU quota,Chromium154 and concurrent V9 gate: cold direct
renderer537–1612.9ms; ten synchronous warm averages Names On1.95–14ms,
Off0.84–5.37ms,selected1.17–7.8ms. One cold sample/case and no controlled load
isolation. API/input, force DOM, compositing and GPU residency are excluded.
No production FPS, scientific realism or production-scale throughput is claimed.
Exact ignored records: `performance.json`, `protected-browser/{wrap-metrics.json,
hydrography-workflow.json}`, `legacy-cartography/metrics.json`,
`legacy-strategic-final/metrics.json`, `browser-zoom-{1280,1920}/metrics.json`,
`release-candidate/workflow.json`, `label-fixed/workflow.json` under
`data/hydrography-pass/`. All captured screenshots are actual application views.
WebKit executable is absent; native macOS Safari remains unverified.

Remaining limits are those accepted above: source-grid coast/biome/drainage
coarseness and soft shores, idealized relief, sparse overview names, province
context for ice rather than exact-cell emphasis, high browser zoom reducing map
space, no live rename operation and full-snapshot persistence/history cost.
Operational deployment/security/backups and original cloud recovery are outside
this interface candidate; no other branch is merged or deployed.

## Final persistence gate and delivery

The isolated V9 10,000-turn gate passed in 5450.49s, preserving geography,
conservation, historical checkpoints and exact independent restoration. It wrote
10,001 snapshots; largest state 1,183,300 bytes; summed snapshot JSON 9,538,588,921
bytes (not disk usage). Current read 161.4ms; history 50 10,021.3ms. All twelve
source hashes match freeze, final report and pushed implementation `feaf766`.
Evidence: `data/hydrography-pass/stress-v9.json`; shared 2-CPU Linux fixture, not
production-scale performance. The measured snapshot cost constrains the newly
requested planetary-scale work; larger geometry must not be multiplied blindly
through every turn. No records were recovered, replaced or fabricated.
