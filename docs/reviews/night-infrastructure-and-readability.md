# Night infrastructure and close-view readability

1 November 2026, `map-generation`, continuation of `c88e3d9`. Interface release
candidate; no merge, deployment, recovery or operational-security claim.

## Reference and design

Examined the user's Blackwatch Command screenshot directly: warm settlement
lights give the dark globe scale, restrained regional labels keep sites legible,
and the blue atmospheric limb communicates curvature. It is a visual reference,
not interaction evidence or an asset source. No proprietary assets were copied.
The source renderer's terrain, atmosphere and city-footprint fidelity remain
different. This milestone does not claim commercial-game or Google Earth parity.

Keep actual distant day/night shading. Add a separate warm emissive layer using
only public, owned, completed facilities active at the selected snapshot turn.
Use distinct schematic production rows, tank groups and warehouse bars around
saved province anchors. Footprints, building coordinates and actual illumination
networks are not recorded; these patterns must not be represented as those facts.
The map footer/terrain hover disclose schematic province anchors. Foreign
observed settlements get no inferred infrastructure lights.

Close orbit gradually becomes an analytical terrain view: normalized altitude
`distance - 1` blends night readability from four times descent altitude to the
descent threshold. The minimum terrain illumination approaches 0.9; brighter
daylight is never dimmed. This uses the existing radius-relative descent distance,
not an Earth-size default. Zoom does not move the recorded star. Flat strategic
surface behavior remains unchanged.

## Implementation and boundaries

`facility-lights.js` joins selected-turn public facilities to owned settlements
and saved land anchors, rejects unknown/future/incomplete activations and invalid
anchors, and sorts by persistent ID. Type symbols share a compact illustrative
layout at each anchor; another province cannot shift that layout. Longitude seam
copies include the whole symbol group. Recorded IDs and source data are unchanged.

The public planet ID can differ from the terrain's internal planet ID. The app
passes the public ID explicitly; both identities join the epoch/campaign/snapshot/
detail/style/overlay texture cache key. This corrects an integration failure found
by actual browser testing, without rewriting either record.

One emission canvas accompanies each cached orbit source. One reusable GPU
texture uploads with albedo/relief at the same revision. Missing emission uploads
black, preventing the previous world's lights from surviving. Alpha contributes
to intensity; globe UV, sun incidence, silhouette and existing far-side occlusion
govern the result. No extra rendering loop, map mount or event listeners are added.
The existing positional render API remains compatible; readability is an optional
transient view property, not campaign state or a persisted camera field.

## Independent critique and corrections

A bounded Sol 6.1 high contract review preceded Luna implementation. A localized
Sol medium correction handled invalid anchors, periodic support, daylight
monotonicity, the public/internal ID mismatch and emission alpha.

A fresh Sol 6.1 medium critic first received anonymous baseline/candidate captures
without implementation history. Its initial verdict was partial improvement:
multiple facilities at one anchor made near-identical fuzzy amber ovals, especially
at close zoom. Luna separated facilities into compact stable slots, reduced bloom,
and sharpened the production/tank/warehouse silhouettes. The same critic accepted
the revision: separated warm clusters, distinct Forge/Outpost cues, labels still
primary and close terrain readable. No remaining scoped visual blocker.

The critic explicitly retained a recognition limit: individual factory types are
too small/soft to infer reliably at globe scale. They convey patterned
infrastructure, not a legible building plan. Initial distant darkness and close
viewport cropping were reassessed as intended orbital/analytical behavior, not
fixed through unrelated renderer changes. Screenshot acceptance alone does not
establish interactions; browser evidence is separate below.

## Evidence

Fresh actual Chromium captures and traces are local generated artifacts, excluded
from Git:

- `data/night-infrastructure/baseline/`: actual pre-change night orbit and closer
  terrain, without facility lights.
- `data/night-infrastructure/candidate/`: first integrated candidate, rejected for
  merged bloom. Its report predates the final test's additional probes.
- `data/night-infrastructure/final/`: revised night orbit, close readable terrain,
  surface and historical captures, GPU probes and source hashes.

`tests/check_facility_lights.cjs` verifies owned/planet/activation filtering,
history eligibility, immutable inputs, invalid anchors, distinct IDs, deterministic
patterns, independent site placement, seam support and monotonic radius-relative
readability across several descent scales. Existing projection/occlusion,
landmarks, relief, sky and body-focus Node suites also pass.

The browser suite `tests/browser_facility_night_lights.py` exercises native zoom
and descent, fixed recorded sun, historical revision eligibility, another world
clearing emission, unchanged public records and reuse of the map canvas. Synthetic
GPU fixtures separately probe day/night masking, alpha intensity, missing-layer
fallback, daylight monotonicity, close-night lift, unchanged sphere coverage and
opposite-side patch occlusion. Synthetic pixels are not campaign records.

`data/night-infrastructure/context-final/workflow.json` records the final native
body-focus regression: star/moon/planet navigation, pan/zoom on the other world,
mouse/touch/keyboard, normal/reduced motion, exact camera/selection/overlay/style
return, historical detected-body restrictions and read-only orders, campaign
switch clearing, private login/logout and no tokens in browser storage. Public
records are unchanged, the main canvas is retained, and page errors are empty.
The test's rendered-view equality was updated to compare camera fields separately
from the newly derived `nightReadability`; its full captured/restored UI-state
equality remains exact. The first run stopped on that instrumentation mismatch,
not a changed saved camera. The final run passes.

The source-frozen final Chromium 154.0.8037.57 run passes: 13 eligible facilities
on a 1536×960 emission source, zero on the other surveyed world, 13 from the
selected historical snapshot. Readability rises from 0 at 1.746R to 0.864 at
1.212R without changing the star direction. GPU center red-channel probes:
day 128, night with emission 255, no mask 6, faint-alpha emission 32, close night
115 and close day 128. A localized patch facing the camera reads 255; from the
opposite side it matches the same-camera no-mask baseline at 128. Coverage is
identical, outside pixels clear, GL error zero; no page errors. The same critic
reviewed this refreshed report and accepted scoped visual and behavioral quality.

Environment: Linux x86_64, three exposed Intel Xeon Platinum 8573C CPUs, headless
Chromium at 1440×1000, reduced motion. A fresh WebGL probe reports ANGLE Vulkan
SwiftShader. Three paint samples were 4.8 ms (13 facilities), 0 ms (empty world),
3.7 ms (historical); these are local samples, not a benchmark or a frame-rate
claim. The added source mask uses about 5.6 MiB at this fixture size, plus the
bounded GPU upload/mipmaps. There is one reusable extra GPU texture, not one per
facility or frame. No production-scale performance or hardware smoothness claim.

WebKit's executable is unavailable here; native macOS Safari is unverified.
The retained 10,000-turn gate at `data/terrain-finish/stress-v2.json` still matches
all recorded backend source hashes: 257.97 s, 10,001 snapshots, exact restoration.
It was not rerun for these frontend-only changes. Deployment, Drive operations,
backups and real campaign recovery were not newly verified.

## Orbital structures: integration point, not fabricated stations

Shipyards, defense platforms and void stations would reinforce planetary scale.
Keep them distinct from surface facilities, with a restrained orbital symbol,
selection/inspector and appropriate occlusion at their recorded location. Do not
add decorative floating structures that resemble saved campaign entities.

The current `orbital_battery` is settlement-linked defense. The current public
astronomy contract has star/planet records, not station positions; fleet location
IDs are also insufficient to derive an orbit. No orbital structures were created
or inferred in this milestone.

A future station contract needs public persistent ID, parent planet, kind,
visibility and selected-turn existence/status, plus an explicit planet-relative
position with frame/units. Unlocated contacts can instead be listed honestly as
unlocated; schematic placement must be explicitly identified. Add authorization
and immutable snapshot serialization before any rendering layer. This requires
a separate bounded schema/authority review. Preserve existing geography and
unrecovered cartography; do not modify the character-relationships branch.

## Delivery status

Verified implementation/review is committed locally as `eae4f8e`, with delivery
references in `0d85bc6`. Push to `origin/map-generation` is blocked: the configured
GitHub credential is invalid (`gh auth status` and authenticated Git push both
fail). The connected GitHub read tool confirms the remote head is still
`c88e3d9`; its first attempted object write returned “MCP tool call requires
approval, but approval policy is never.” No connector objects or branch updates
were published. No force push, history rewrite, merge or deployment occurred.
Restore working GitHub write authentication/approval configuration, then push the
existing local commits; implementation work does not need to be recreated.
