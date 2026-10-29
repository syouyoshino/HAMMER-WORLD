# Physical scale and celestial focus — 29 October 2026

This is a scoped interface release candidate on `map-generation`. The request is
about terrain size relative to the world, alongside clickable celestial bodies.
It does not establish planetary physics, Google Earth detail, or whole-game parity.

## Generation contract

New demos may opt into `planet-v11`. Every planet requires an explicit positive
physical radius in metres, as a decimal string. There is no Earth-sized default
and no new interpretation of old chart-radius tokens. Global `--radius-m` and
repeatable `--planet-radius-m PLANET_ID=DECIMAL` overrides are supported. Omitting
the global value requires complete per-planet coverage. For example:

```sh
python -m app.cli init-v2 --campaign-id scale-demo --seed 731609 \
  --planet-generator planet-v11 --radius-m 1e8 --preset continental \
  --planet-radius-m scale-demo-planet-ash=1e5
```

Radius is saved as canonical scientific text in the private generation config,
surveyed node and surface metadata. Decimal processing preserves up to 64 supplied
coefficient digits, with a 256-byte input limit and signed 32-bit adjusted exponent.
These are finite representation limits, not an Earth-based size range. Fractional
and extremely large/small values are supported without float overflow or allocating
a raster proportional to the radius. Sizes outside planetary physics are fictional.

Terrain uses radius-dependent fictional physical wavelength bands. Broad, warped
land-probability regions maintain continent/ocean composition; subordinate bands
change coast, island, mountain, crater and lake grain with radius. Sub-four-sample
bands attenuate; very large wavelengths generalize. Lake/crater omission is accepted
only with matching validated resolution metadata. Water, lava, hydrocarbon, no-lake,
ice-cap and dry presets remain independent choices. Radius alone does not infer
climate, water, greenery, gravity, habitability or a new economic rule.

This remains a fixed 1024×640 immutable detail asset with a 128×80 strategic summary
and existing 8 MiB per-asset ceiling. It is a finite global overview, not unlimited
local detail. Larger extreme worlds can have all physical bands unresolved; broad
regional structure then remains generalized. The UI reports radius, approximate
metres per equatorial sample, and unresolved detail. Exact technical metadata is
in the tooltip. No generation seeds/private configuration are projected.

`static-v1` astronomy has its own existing whole-kilometre format/range. V11 combined
with it requires every radius to be an exact whole kilometre from 1,000 through
100,000 km. Other explicit sizes work without that optional astronomy contract;
the CLI rejects incompatible combinations rather than clamping or rounding.
Node, surface, private config and saved astronomy radii must agree.

## Celestial navigation and motion

The actual saved host-star marker is now a mouse/touch/keyboard button. Selecting
it, a known planet, or moon opens a focused destination in the main map area. Known
bodies are grouped by star/planet/moon with explicit surveyed/detected states.
Other surveyed planets use their existing real map and retain pan, zoom and forces;
detected planets and moons have neutral silhouettes and explicitly unknown surface,
position and size where absent. No terrain or celestial coordinates are invented.

One in-memory return ticket retains the original camera, selection, overlay, style
and public map/detail references across multiple body destinations. It is bound to
campaign, snapshot and context epoch. Campaign/history/login/logout changes clear
it; stale work cannot restore the prior identity. It stores no credentials. The
main map canvas and orbit renderer remain mounted. Existing hierarchy and management
navigation remain available; the character branch is untouched.

The focused star has a quiet illustrative corona. Reduced motion disables it;
hidden documents pause it and closing focus removes it. This is not recorded flare
activity. No rings or dynamic orbital ephemeris were fabricated for unrecorded bodies.

## Review and corrections

Luna built the bounded initial candidate. Sol 6.1 high approved the radius/data
contract and audited the localized final kernel revision. Sol 6.1 medium corrected
two failed candidates: the initial popup left the planet visually dominant, and
large-world terrain exposed a square maze. These became a main-area destination and
warped broad-region terrain respectively. The same independent Sol medium critic
retained those findings throughout reassessment; it was not replaced for approval.

The critic initially received anonymous, uncropped matched viewport/camera images
without origins or a preferred result. Fresh actual persisted 100 km, 6,371 km and
100,000 km radius fixtures use the same namespace, seed and camera; the middle size
is a comparison sample, not a default. Light, dark and surface captures were supplied.
The critic accepted the corrected geography and body destinations with no unresolved
critical/major issue in this scope. Competing focus headings, weak selected-row
indication, raw scientific ordinary-scale values, duplicate scale text and a blank
legend strip were corrected; some empty space remains inside the narrower legend panel. Minor remaining defects are stepped coasts, occasional
near-square islands and weak directional relief. They are not physical realism
acceptance. Tiny worlds can look ocean-dominant from a single selected camera.

Interaction evidence was supplied separately: `tests/browser_body_focus.py` records
actual Chromium pointer, touch and keyboard use, other-surveyed-map pan/zoom, exact
return across a map load, historical detected state/read-only orders, private logout,
identity clearing and unchanged records. Screenshots alone do not establish those.

## Comparison record and evidence limits

The research already examined for scale remains applicable: Cesium's bounded
screen-error tile loading (`ad366f071293b28bdf330c822965b8bd0bdeb781`,
`QuadtreePrimitive.js`); archived Earth Enterprise's separate terrain/data/client
architecture (`893f6b470673e2bad4cacdd8eec5ad1f179b6249`); and Eleanor Lutz Moon/Mars
maps (`17383b391bf2a982689ca1d1bd41cc914fd4c8ed`) for connected relief and subordinate
labels. No artwork, Google imagery or implementation was incorporated. No new live
Google Earth, NASA optical imagery, Victoria 3, CK3 or Stellaris interaction comparison
was performed in this increment. Their earlier comparison records are not upgraded
by this review. The scoped gap addressed here is feature grain and context-preserving
body navigation; real multilevel terrain streaming remains future work.

Runtime evidence is ignored under `data/scale-focus/`: baseline, rejected candidates,
matched `size-revised` captures, `body-browser/workflow.json`, independent review
messages, generation matrices and verification reports. Secrets remain outside Git.
Final verification and measured performance are recorded below.

## Integration and continuation

V1–V10 generation and existing campaigns remain unchanged. V11 is opt-in only for new
records; do not regenerate old snapshots. Preserve optional radius metadata and
immutable detail hashes across recovered cartography integration. Reuse the public
allowlists, context epoch and existing map loads. Do not infer precise moon bearings
from topological chart coordinates. A future ring/orbit version needs recorded data;
a future deep zoom system needs bounded deterministic detail tiles, not an inflated
raster or a larger globe diameter. No merge, deployment, live recovery, backup,
operational security or native Safari verification is claimed.

## Final functional/browser/resource evidence

- Nine explicit-radius/V11 tests pass, including actual two-radius native terrain,
  finite extreme metadata, real elevation differences, asset bounds and nested
  allowlists/forged omission rejection. Thirteen existing astronomy, V2 acceptance
  and movement-projection tests pass against isolated PostgreSQL schemas. Syntax,
  focus-ticket, orbit projection, sky pixels/cache and landmark regressions pass.
- All 240 V1–V10 private/public golden hashes match (280.65 seconds under concurrent
  QA load). All eight pre-existing preview campaign public responses match their
  captured baseline hashes. New QA schemas/records were created separately; neither
  the rejected candidates nor old campaigns were overwritten.
- Final source Chromium 154.0.8037.57 workflow passes mouse point, touch point and
  keyboard label activation; star/moon/planet destinations; other surveyed planet
  pan/zoom; exact origin camera, selection, overlay and style return; retained main
  canvas; reduced motion; removed hidden animation; historical detected/redacted
  bodies and read-only actions; campaign clearing; protected logout; no browser
  token storage; unchanged fixture records; no uncaught page errors.
- Twenty additional warmed focus/return cycles retain the same canvas and orbit
  renderer. After forced GC, listeners remain 244→244 and DOM nodes 1842→1842;
  sampled heap 33,795,864→33,961,864 bytes. This small sample does not establish a
  lifetime memory bound. Automated round trips measured median 1,679.9 ms, maximum
  2,466.0 ms under concurrent QA load; this includes automation, rendering and UI
  waits, not GPU frame time or an input-latency benchmark.
- Desktop 1280×720 and 1920×1080, CSS150% at 1280×720 and CSS200% at 1440×1024
  pass focus bounds and reachable Back. The test exposed mixed screen/local
  coordinate positioning; the bounded correction converts coordinates and clips
  to the visible viewport. Independent review verified actual150/200% captures.
  Content may require vertical scrolling; high CSS zoom still crowds the global
  header and crops the illustration after scrolling. This is not full native
  browser-zoom or accessibility certification.
- Shared Linux environment has a two-CPU cgroup quota. Four-planet native generation
  at the three explicit radii took 124.12, 107.64 and 71.53 seconds respectively in
  the recorded creation matrix. These are fixture/host/load observations, not
  production-scale performance. WebKit executable is absent; native macOS Safari
  remains unverified. Desktop scope only, as requested.

Final backend source-set SHA-256 (ordered eight changed/new backend files, filename
+NUL+bytes+NUL) is `fbb4c944967630021e81156b3d82e27d0d187e104665912c35f85aa513b2676e`,
matching Sol high's accepted source. Final browser/resource app.js SHA-256 is
`af20bb8670b73ade086b68a77ba30331009ecea0621a6ad9fa5605c08640f586`.

The final source-matched V11 barren/cratered + static-v1 connected fixture passed
10,000 turns in 598.82 seconds, including conservation/resource ledgers, immutable
historical checkpoints, exact restore to a new branch, unchanged geography and
astronomy, and current/historical/restored detail equality. Exactly four immutable
assets remain (20,987,190 bytes); no turn/restore duplication. The 10,001 snapshots
occupy 767,361,886 state bytes; largest serialized state 81,010 bytes. Measured
current read 10.1 ms; history page of50 321.0 ms. Source hashes match the frozen
17 backend modules and final high-review source set. These include shared-host
QA contention and are not production-scale guarantees. An earlier initial-kernel
run and an interrupted final rerun are not substituted for this completed gate.

Verified implementation/tests/review committed and pushed as `39b015f` on
`map-generation`. No merge or deployment.
