# Cratered worlds and map presentation

Branch: `map-generation`, following `4fb3d09`. Corrected scoped visual review
accepts the idealized cratered-world candidate; delivery checks passed.
User approved fixes after actual Continental/Barren/Frozen captures exposed
angular uniform rivers, stepped coastlines, soft relief, weak geological identity,
heavy province grids, a tall header and an empty status mark beside Forces.

## Baseline and scope

Fresh1440×1024 Chromium captures from the clean previous release are retained
under ignored `data/geology-pass/baseline-{continental,barren,frozen}.png`.
Committed-source private/public hashes cover63 combinations across V1–V6,
three seeds and every supported preset. Existing saved campaigns must not change.

One bounded Sol high review approves new opt-in V7 with a separate `none` or
`cratered` geology choice. V1 remains default. Explicit per-planet choices are
persisted with private creation configuration and public surveyed-only geometry.
Cratered supports dry Arid/Barren/Frozen; wet combinations fail explicitly because
the existing ocean-draining depression fill would erase impact bowls. Presets
continue to govern water, vegetation and climate independently of geology.

V7 saves bounded integer crater descriptors and samples their bowl/rim relief
into elevation. The renderer may reconstruct only that recorded subcell profile,
with a residual correction that preserves saved canonical samples. No client
random craters, rewritten history, new resource rules or schema migration.

This first geological family can depict impact-scarred rock or ice. Fractured
ice, basalt composition/maria, volcanic resurfacing and gas-giant atmospheres
are separate future families and are not acceptance claims for this slice.
The current enforced network policy excludes NASA image hosts; no new lunar
photo study is claimed or bypassed. Visual acceptance must name this evidence gap.

## Required verification

Determinism, all63 legacy pairs, strict malformed/configuration checks, public
allowlists/defensive copies, seam/pole behavior, save/history/restore, protected
orders and navigation, fresh equivalent-scale captures, independent same-critic
corrections, relevant legacy regressions, bounded performance and the required
10,000-turn persisted fixture gate. All required scoped checks passed as recorded below.

## Backend review and tests

The first Luna backend candidate passed targeted tests but the bounded high
review reproduced four gaps: descriptor projection copied extra keys; V7 omitted
exact province coverage; older versions accepted unused geology configuration;
and direct older-generator calls ignored geology arguments. A localized Sol
medium correction closed all four and fixed a CLI test that had rejected an
unknown planet ID before exercising its intended wet-geology error.

The same high reviewer rechecked the corrected source and accepted the freeze,
with no remaining critical/major backend finding. It independently verified all
63 legacy private/public pairs after correction, strict fields/configuration,
12 explicit legacy CLI rejection cases, surveyed-only projection, defensive
copies, bounded integer profile behavior, cell-centre sampling, periodic distance
and exact elevation reconstruction for three dry presets.

Full Python discovery: **111 tests passed in285.031s** against isolated
PostgreSQL17, with existing QA backup clients on PATH. The backend hashes are
frozen in ignored `data/geology-pass/backend-frozen-hashes.json`; the mixed
10,000-turn V7 fixture passed against this source. Numeric engines/schema/archive
paths are unchanged.

A small Node regression loads the actual renderer helper in an isolated VM and
checks every canonical sample for a central and two seam-crossing crater cases.
Maximum residual error was0.0000035604 elevation units. This caught and corrected
a seam-side coordinate issue before the first frontend candidate was frozen.
The production renderer exports no test hook and campaign data is not injected.


## Persisted-turn gate

Mixed V7 arid/archipelago/oceanic/frozen, with separate cratered choices for
arid and frozen: **10,000 turns PASS in2465.58s**,10,001 immutable source
snapshots, final owned population1199. Every-turn conservation, checkpoint
hashes, original timeline and exact independent initial-state restore passed.
Largest serialized state968,119 bytes; summed source-state JSON7,582,653,347
bytes (not physical database disk use). Current read64.9ms; history50 read4095.5ms.
Full geography in repeated snapshots remains a material inherited storage/history
cost, not a resolved production concern.

All backend hashes in ignored `data/verification/stress-v7-geology.json` equal
the initial frozen manifest and final source. Test schemas are disposable,
and only the explicitly isolated QA PostgreSQL was used.

## First visual candidate

Fresh full-frame captures are in ignored `data/geology-pass/candidate/`.
A fresh Sol medium critic initially examined anonymous A/B dry-world and C/D
continental pairs without origins or implementation discussion. It preferred
the new cratered identity and modestly preferred the new contour finish, but
identified embossed/stamped bowls with crosshatched interiors, a uniform cyan
shore halo, persistent axis-aligned rivers, equal-weight numbered-province
labels and a large UI stack. It expressly rejected photographic-accuracy
claims from these stills. Origins were then revealed as committed V6 versus
new V7 at matched preset/seed IDs, viewport and200% Orbital scale.

Actual private V7 browser workflows passed on that candidate across six presets,
both styles, seam traversal/selection, all overlays, management return, themes,
resize, real DRAFT/PREVIEW/commit, historical read-only → live, stable canvas/
handlers and no page errors. This functional result did not establish visual
acceptance. The critic's live1024×768 check also found caption/legend overlap.

The critic's session hit an external usage limit, then resumed after the user's
next continuation. The same critic retained its findings and rechecked the
corrected candidate; no replacement critic was selected to obtain approval.


## Corrections and final independent outcome

Localized Sol medium renderer corrections resolved the concrete presentation
findings without changing stored height fields or the frozen backend:

- Use one matching raster-pixel stencil for base and residual elevation gradients.
  The previous mixed cell/pixel stencils produced crosshatching inside bowls.
- Normalize soft relief lighting instead of clipping broad regions to flat bright/
  dark bands. A further precise northwest-light correction uses the proper sign
  for the surface normal derived from positive height gradients. The critic's
  small/medium crater examples now read as concave bowls rather than buttons.
- Reduce the uniform cyan shore blend and taper narrower, muted river strokes
  using recorded accumulation. Midpoint curves preserve the recorded path corridor;
  this does not replace its four-neighbour hydrology.
- Hide ordinary Terrain province borders and generic names below250% cover zoom.
  Holdings, selected names and explicit Provinces labels remain available; all
  canonical province picking remains unchanged.
- Compact desktop resource/title padding and spacing while keeping values/units
  and controls readable. Resource values end at98px before the title starts105px;
  title ends146px before breadcrumbs148px at the checked desktop layouts.
- Hide the empty Forces status span while retaining genuine empty/targeting text.
- At781–1100px desktop width, stack caption and legend. The critic reproduced
  their separate readable rows at1024×768; the overview remains above them.

Fresh corrected full-frame captures: ignored `data/geology-pass/corrected/` and
`corrected-nw/`, with the latter documenting the final crater lighting. The same
critic directly confirmed crosshatching, label clutter, shore glow and caption
overlap resolved, and final northwest lighting giving the correct bowl cue.
Its bounded live checks covered Forge inspection, matching local Economy context,
return to map retaining Provinces/200%, four map levels, both styles, campaign
switching and1024px resizing, with no page errors. It did not independently
repeat protected order commits, history or every seam/overlay case; those are
separate parent regression evidence.

Final scoped verdict: **acceptable for idealized cratered rock/ice and clearer
terrain navigation, with no major concrete UI defect in the tested path**.
Repeated circular profiles and conspicuous/nested overlaps remain minor
stylization limits of this first saved family. Axial source rivers and coarse
landform boundaries remain visible inherited data limits. No photographic,
scientific, physical erosion or whole-game quality parity is established.

## Creation and integration

```sh
python -m app.cli init-v2 --campaign-id NEW_ID --planet-generator planet-v7 \
  --preset auto --planet-preset NEW_ID-planet-reach=barren \
  --planet-geology NEW_ID-planet-reach=cratered
```

This uses the explicitly configured database and creates a new fictional demo;
existing IDs are refused. `--geology cratered` applies globally only when every
resolved preset is dry; `--planet-geology` overrides independent named planets.
Wet+cratered and geology flags on older generators fail explicitly. V7 without
geology flags defaults to `none`, and the overall generator default remains V1.

Keep V1–V6 records/versioned algorithms unchanged when integrating unrecovered
cartography. V7 adds surveyed-only `geology` and explicit crater descriptors to
the existing surface and complete private `planet_geologies` creation metadata.
No schema migration, turn/resource rule, archive/authentication change, map-ID
conversion or character-relationships branch edit. No original cloud data was
recovered or fabricated. This is an interface release candidate, without merge,
deployment or operational-security/backups certification.


## Final browser and performance evidence

Final post-correction V7 browser delivery run passed all six presets/both styles,
repeated seams, canonical selection/overlays, management camera return, theme
pixel stability, desktop resize, supported movement draft/preview/commit and
historical read-only return. No page errors, canvas replacement or accumulated
map/window handlers occurred in exercised paths. Legacy V5 navigation, V3
cartography, broad strategic/auth/stale-context/browser zoom and protected movement
checks passed. Broad management checks retained 2656 DOM nodes and193 listeners
through24 warm transitions. Chromium154.0.8037.57 on shared Linux was tested;
WebKit executable was absent and native macOS Safari remains unverified.

The final Node check also executes the actual raster branch for a dry lowland
fixture with subcell crater relief and verifies zero ocean rendering: a geometric
undershoot of the old sea reference cannot create liquid on a waterless world.

1440×1024 Chromium,1536×960 cached rasters, shared Linux with2 CPU quota:
one cold direct draw per preset/style ranged143.6–472.2ms; ten synchronous warm
draw averages ranged0.36–5.02ms. These exclude input, API, force DOM, compositing
and GPU residency, and are not frame-rate or production-scale promises. Actual
campaign-to-first-draw observations ranged697.8–1243.7ms. Separate warm management
transitions had median28.75ms/p9573.79ms. The persisted gate's history50 read of
4095.5ms remains a documented full-snapshot limitation.

Matched baseline comparison used actual V6 and V7 full-frame1440×1024 screenshots
at200% Orbital, the same seed/preset IDs and equivalent information load. The
response to weak dry-world identity was recorded crater geometry and concave
lighting; to terrain clutter, selective labels/grid; to coarse shores/rivers,
restrained contours and variable-width strokes. The same critic accepted those
bounded improvements after corrections. These comparisons establish improvement
over the prior build, not equivalence to lunar photographs or commercial games.

V7 implementation and verified source: **`ed66cb6`**. Subsequent liquid-lake and
polar-cap options are a separate opt-in continuation; this verdict covers V7.
