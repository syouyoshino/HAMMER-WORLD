# Map generation — interface release candidate

Date: 22 October 2026 UTC. Branch: `map-generation`, created from `edf243e` on `feature/map-desktop-shell`. The preceding military interface implementation is `2379356`; owned movement projection milestone is `3e97811`. The source branch was clean and its push reported up to date before this branch was created.

## Authorized scope of this milestone

Initial milestone `4cad437` researched the generation/presentation approach and produced three concept images. The user subsequently approved implementation of the richer Orbital direction with Light/Dark/System interface modes and all four map levels, through independent critique and testing. Existing saved geography/history/rules/IDs/authentication must remain unchanged; new generation is opt-in for new fictional demo records. No unavailable cloud cartography/database is claimed recovered. Generated images remain design studies, not generator output or implementation/performance evidence. No merge or deployment is authorized.

## Research actually examined

| Primary source | Examined material | Design/generation implication |
| --- | --- | --- |
| [Red Blob Games: terrain from noise](https://www.redblobgames.com/maps/terrain-from-noise/) | Elevation, multi-frequency structure, biomes/climate and map edge/wrap discussion. | Broad coherent fields before local texture; separate data generation from drawing. Noise alone does not establish drainage, playable regions or economic facts. |
| [Red Blob Games mapgen2 source](https://github.com/redblobgames/mapgen2) | README, file structure and repository license listing; mesh connectivity separate from elevation/rivers/biomes. Apache-2.0 listed. | Useful algorithm/source reference, not a dependency decision. Consider mesh-based geography only after preserving current membership contracts; check all relevant licenses before reuse. |
| [USGS contours with shaded relief](https://www.usgs.gov/media/images/contour-lines-and-shaded-relief-a-us-topo-map) | Public-domain example page and medium image reference. | Combine selective contours with restrained relief; keep labels and operational symbols above terrain detail. Do not reproduce an entire real-world map as fictional campaign geography. |
| [NASA Blue Marble topography/bathymetry](https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/topography-bathymetry-maps/) | Primary explanatory page and image-search preview for the related composite. Full-resolution asset fetch timed out. | Natural-color land/ocean and large landforms inform orbital presentation; no claim of full-resolution asset inspection, download or reuse. |

Actual Hammer World grounding: `data/movement-candidate/ground-stack.png` was inspected and attached to every image-generation request. The first concept was also attached to later requests to preserve comparable fictional geography. Existing aerospace/monospace identity, sharp controls, selected blue and transparent locally fogged inspector are retained. Product Design context preflight reported no saved context; the current repository and user brief supplied the design context. Some ancillary plugin reference resources were unavailable; no missing reference is treated as reviewed.

## Three independent concept directions

All use one fictional regional view: northern ridge, west coast/southwest gulf, central river-bend Forge, northeast Outpost, downstream observed settlement and southeast forest/delta. Same settlement-selection workflow and approximate information load; inspector shows unavailable economy values honestly. Requested target is 1440×1024 desktop; image-generation output dimensions may differ slightly and are retained without stretching. These are planetary-map direction studies, not four hierarchy levels or proposed new game mechanics.

| Direction | Main treatment | Strength to test | Risk to test |
| --- | --- | --- | --- |
| Survey Atlas | Light modern survey sheet; muted sage/ochre land, pale-blue water, graphite relief and sparse contour detail. | Immediate terrain/label reading and compatibility with current light command shell. | Contours can clutter at small scales; excessive illustrated detail can exceed a lean procedural renderer. |
| Orbital Reconnaissance | Top-down natural-color terrain, restrained geological relief, dark sea/coastal shelf and sparse province overlays. | World identity and recognizable terrain while keeping the same military controls. | Texture may compete with labels; asset cost and blending require evidence, not a claim of easy photorealism. |
| Vector Operations | Dark charcoal/navy field, muted biome surfaces, selective terrain/river vectors, strong settlement/ownership hierarchy. | Force/province/selection reading and operational emphasis in dark mode. | Low-contrast boundaries or decorative scan effects can reduce geographic understanding. No neon hologram treatment. |

The common interaction stays map-first: compact command access, hierarchy breadcrumbs, map/overlay controls, Forces, one contextual inspector. Local blur under panels is presentation; actual fog of war remains server-filtered intelligence. Terrain colors describe land cover/elevation; Apple functional accents describe selection/ownership/actions. Foreign does not automatically mean hostile. No fake economic values, gauges, telemetry or decorative charts are authorized by these concepts.

All three independent images were generated and displayed once in the chat, in this order: Survey Atlas, Orbital Reconnaissance, Vector Operations. Files in ignored `data/map-generation-concepts/` are `survey-atlas.png`, `orbital-reconnaissance.png`, `vector-operations.png`. Original outputs remain in `/workspace/generated_images/`. Generated details such as illustrative force counts, turn labels and terrain names are mock content, not approved records. The third result retains more illustrated relief than the requested flat vector treatment; a truly flat treatment would require refinement. No concept establishes algorithmic feasibility, physical geography accuracy, legibility across devices or final interaction quality.

Selected direction: Orbital Reconnaissance's terrain, restrained military command composition, and toggleable Light/Dark/System interface. The user explicitly authorized building through critique and checks. The existing application remains the functional target; concepts do not authorize fabricated map facts or economic values.

## Actual current generator and compatibility limits

A bounded read-only Sol high review examined the existing source rather than assuming the missing cloud work is present:

- `app/engine.py::generate_planet` produces a 64×40 grid from three overlapping ellipse fields (the source comment says two landmasses). Inland terrain is independent per-cell random selection; elevation is discarded.
- Only six terrain classes are stored. No persisted elevation, drainage, rivers, temperature or moisture exists. Planet class labels do not currently drive terrain generation.
- Forty provinces are fixed 8×8 rectangles, with ocean excluded from membership. Land can be disconnected or absent within a province. Public projection reconstructs membership by grid arithmetic; deployment/colonization use rectangular bounds.
- Hierarchy generation is a small explicit fixture with seeded positional jitter, not a general procedural galaxy. Seed domains and stable identity/insertion order need deliberate handling in future expansion.
- Public map APIs filter by campaign/snapshot/knowledge; surveyed planets expose geography. Raw/private generator state and hidden descendants must remain server-side.

This means smoothing existing presentation cannot legitimately create recorded mountains, rivers or natural province boundaries. Generation and styling need separate tracks.

## Proposed implementation sequence after visual selection

1. **Presentation-only vertical slice.** Improve rendering of already stored terrain/province membership and labels. Preserve source geography, state hashes, IDs, coordinates and rule behavior. Compare settlement → economy → construction → map, and Forces → movement draft → Orders → map. Any new decorative texture must not imply authoritative rivers/resources or displace recorded locations.
2. **Versioned `planet-v2` for isolated new fixtures.** Keep the bounded planar projection/edge policy initially. Persist generator version and configuration; never regenerate existing geography on screen load. Derive independent domain streams from private stable identifiers/configuration so adding a detail pass does not reshuffle the world.
3. **Coherent geographic fields.** Broad landmass/elevation structure → coast classification → deterministic depression/lake handling → downstream flow/accumulation → river selection → temperature/moisture → biome classification. Use a quantized, reproducible representation. Start with broad fields and a small bounded pipeline, not a tectonic/erosion simulation framework.
4. **Compatibility before more detail.** Retain existing supported grid dimensions and rectangular province contract for the first new-generator slice. The concepts' natural watershed borders are a later separately versioned membership/topology change, not a renderer trick. Grid resolution, wrapping, new terrain codes, settlement placement and adjacency-based travel rules require explicit integration decisions and tests.
5. **Semantic detail through current hierarchy.** Galactic: sectors and known extent. Sector: systems and recorded links. System: bodies/orbits only if supported by recorded data. Planet: terrain → province → holding labels as screen scale permits. Start with existing explicit level navigation; continuous cross-level zoom/globes are optional later work. Remember camera/context per level where the implementation supports it.
6. **Independent critique and delivery.** Fresh actual browser captures and equivalent workflow evidence, one independent Sol medium critic, bounded fixes through the established Luna/Sol hierarchy. Commit/push verified milestones; no merge/deployment/data reset.

## Architecture and preservation boundaries

- PostgreSQL/saved immutable snapshots remain authoritative. Preserve v1 decoding, historical rendering, exact restore and all persistent references; new fixtures opt into a new generator version.
- Existing `terrain_grid` validation accepts `ocprfm`; additional fields/codes need versioned persistence and explicit public allowlists in both projection paths. Never expose private seeds or hidden-world generation intermediates.
- Existing geometry planet IDs and hierarchy node IDs differ; do not normalize established records silently.
- `public/app.js` must keep drawing, picking, labels, selection and force anchors on the same transform. New label rectangles feed `forceObstacles`; counter collision displacement remains presentation, with stems tied to recorded origins.
- Province adjacency for inspection is distinct from changing deployment rules. New terrain visuals do not automatically change production, combat, movement costs or colonization rules.
- Keep changes small and modular enough to integrate unrecovered cartography later. Character-relationships branch stays untouched.

## Acceptance gates

Presentation: unchanged saved geography/IDs/checksums; same canvas/camera/selection/overlay through management changes; readable labels/counters at desktop, phone and browser zoom; no map input through panels; all destinations remain reachable.

Generation: same version/config/private seed yields exact output; different seeds vary structure; finite and bounded fields/dimensions; coherent connected land where intended; rivers terminate in ocean or explicit lakes without cycles; complete terrain classification; valid stable province membership and references. Do not assert physical realism from attractive images.

Security/history: frozen foreign observations, no hidden marker/seed leakage, campaign/login/logout staleness guards, read-only historical views and exact restore continue to pass. Existing records are never rewritten to match a visual.

Performance: measure generation time, serialized size, map load, redraw and resource/handler stability on named fixture sizes. Use existing Canvas/backend first; evaluate rendering libraries only against a demonstrated need. Run meaningful generation/projection/browser tests and the required 10,000-turn fixture gate at implementation acceptance, not for this documentation/ideation-only milestone.

## Delivery evidence and continuation

Planning milestone `4cad437` changed documentation only. Generated concept files remain outside tracked source, under `/workspace/generated_images/` and ignored `data/map-generation-concepts/`. Implementation evidence follows separately below; the concepts alone establish no functional or visual acceptance.

## Implementation contract

`planet-v1` remains the default and its golden output hashes remain unchanged. A new demo can explicitly select `planet-v3` through `python -m app.cli init-v2 --campaign-id NEW_ID --planet-generator planet-v3`. The CLI refuses an existing campaign ID. No server startup regeneration, automatic conversion or data reset is introduced. The earlier `planet-v2` candidate remains readable and deterministic; its output is preserved rather than silently replaced.

New geography retains64×40 cells, six existing terrain codes and rectangular province IDs, and persists a versioned `surface` object with integer elevation/temperature/moisture, cardinal drainage, accumulation and recorded river-point networks. Warped continental influences, class-dependent land coverage and narrow ridge fields precede priority-flood drainage filling. Rivers terminate in ocean; there are no lakes, plate simulation or physical climate claims. Existing planet classes influence fictional climate without new game rules. Seeds and generator configuration remain private; nested public allowlists expose only surveyed geometry.

The renderer is a separate dependency-free Canvas module. It consumes saved geometry and returns the same transforms used for input, labels and military anchors. Natural terrain styling and a Survey presentation are separate from the Light/Dark/System chrome preference. Unlocated bodies are explicitly nonspatial; charts do not claim orbital positions. A planar regional grid cannot honestly become a full spherical surface by wrapping a texture. Full global planetary coverage and a canonical Milky Way/Imperium map remain unavailable data, not fabricated visuals.

Baseline:9 fresh1440×1024/390×844 captures across all four levels and both themes, no page errors, at ignored `data/map-baseline/`. Initial candidate critique identified enlarged terrain blur, stepped rivers/coasts, equal-weight province/holding labels, tiny edge-clipped hierarchy markers, phone toolbar clipping and a displaced label without a matching hit target. Localized Sol medium correction follows the unsuccessful Luna visual candidate; the same independent critic rechecks the improved candidate. Protected preview/commit and broad regressions are root evidence, separate from critic read-only workflows.

## Critique and correction record

The first independent comparison used anonymous full frames at preserved aspect ratios: the previously generated Orbital concept, actual planet, system and galactic screens. The critic then exercised the actual application separately; the concept was never treated as interaction evidence or a commercial screenshot. Subsequent reviews use the same critic, preserving unresolved findings.

| Finding | Correction / status |
| --- | --- |
| Equal-weight province labels hid relevant holdings. | Holdings have priority, recognizable anchors and ownership labels. Bare province names appear on selection, at higher zoom or in the Provinces overlay. |
| Displaced holding labels lacked matching selection targets. | Labels and markers share explicit44px province targets with hover, selection and military targeting. |
| Tiny hierarchy bodies clipped against chrome; missing coordinates were visually assigned positions. | Kind-specific markers fit measured safe bounds. Unlocated records use an explicitly nonspatial list, while coordinates remain Unknown. System charts explicitly describe topology rather than orbits. |
| Orbital and Survey were barely distinguishable. | Separate ocean/land treatments and recorded-elevation contours in Survey; UI appearance stays independent of terrain style. |
| Phone Style controls stranded zoom controls. | Three-column selectors and a separate44px zoom row; breadcrumbs and force panels follow beneath. |
| Inspecting an unlocated body then descending left stale selected identity. | Explicit hierarchy navigation clears entity selection; management/theme/style changes preserve selection. |
| Force picker remained underneath Orders after Move/Inspect. | Choosing an action closes the picker before entering its destination workflow. |
| V2 clipped elevation at850 and used an edge cap, producing rectangular coastlines and plateaus. | Bounded Sol high diagnosis led to opt-in V3, preserving V1/V2. Across six tested seeds, oceanic land coverage is25–30% versus44–49% terrestrial, longest straight coasts7–18cells versus33–58, and no clipped850 plateau. Earlier snapshots remain intact. |
| Actual200% browser zoom collapsed map safe bounds and compressed system icons overlapped. | Short-height layout reserves usable chart space; deterministic symbol/label offsets use leaders to unchanged true anchors. Actual100–200% zoom regression and same-critic short-height clicks pass. |
| Military overlay inherited4px dark squares that disappeared over dark water. | 12px owned Apple-blue squares, neutral observed diamonds and unknown circles have light outlines, matching legend and recorded province-land anchors. Same critic confirms the readability defect resolved. |

A final protected-flow check found that skipping an unlocated endpoint also discarded its transit text. Recorded route readouts now render independently of finite positions, explicitly say Position unavailable, preserve departure/arrival and omit invented connectors. The corrected protected movement suite and final critic capture check pass.

The first V2 long-run check was deliberately interrupted after the structural geography defect was established; it is not a passing10,000-turn result. The final gate runs against frozen V3 source. Coarse coast/ridge resolution and cardinal river topology remain explicit limits of this compatibility-preserving release, not illustrated-geology parity.

## Integration notes

- New backend surface handling is localized to `app/planet_generation.py`, explicit demo creation, snapshot validation and the two public projection paths. Existing numeric rules, schema migrations, node/geography IDs and V1/V2 golden outputs are unchanged.
- Rendering is localized to `public/map-renderer.js` and thin existing draw/pick hooks. Unrecovered cartography can provide its own recorded geometry without rewriting authentication, campaign state or management navigation. Unsupported surface versions must receive a deliberate adapter/validation decision, not be interpreted as V3.
- Natural province membership, larger grids, new terrain codes, additional classes, global spherical coordinates and travel-cost effects require separately versioned contracts and checks. No generated detail can silently become an economic or movement rule.
- `HWDesktop` registration remains the character-screen integration boundary. The separate character-relationships branch was not changed; this release cannot fabricate a CK3-style relationship graph from absent records.
- Management transitions retain the current camera/selection/overlay. Explicit hierarchy changes fit the selected chart; independent per-level camera memory and continuous cross-level zoom are not implemented.

## Representative comparison record

| Workflow / material examined | Relevant strength | Gap and implemented response | Evidence / verdict limits |
| --- | --- | --- | --- |
| Settlement → Economy → Construction → Map; prior Victoria3 official UX material documented in `docs/reviews/strategic-workflow-comparison.md` | Local identity and related reports with understandable causes | New terrain obscured holdings; priority labels, matching hit targets and retained local report scope restore the journey. No new economic diagnosis is inferred. | Same critic exercised desktop/phone V3 journey (`/tmp/map-review/v3-*-construction.png`). Readability/context accepted; authoritative main-economic-problem comparison remains partial where recorded diagnosis is absent. |
| Select character → understand relationships; prior CK3 material in the same comparison record | Relationship hierarchy and explicit character context | No relationship records exist in this branch. Existing character information stays reachable; integration boundary is retained. | No new CK3 comparison or relationship parity is claimed. Separate branch remains untouched. |
| Return to strategic navigation; prior Stellaris main-interface documentation in the same record | Consistent return and hierarchy controls | Same permanent canvas, clear Return to map, four-level controls and actual painted-marker descent; management retains current camera/selection/overlay. | Critic desktop/phone journey plus root regression. Explicit hierarchy navigation fits the new chart; per-level camera memory is not implemented. |
| Orbital concept A, NASA preview and USGS relief example | Recognizable landforms with operational labels above relief | V1 had no elevation/drainage data. Opt-in V3 saves real fields; Orbital/Survey interpolate them, prioritize holdings and disclose legacy/unknown context. | Anonymous initial image review followed by same-critic actual-browser rechecks. Stylized strategic finish accepted at normal sizes; concept A is substantially richer in geology, and physical/commercial equivalence is not claimed. |

## Functional and browser verification

The frozen backend passed **79 Python tests in297.623s**, using only disposable schemas on the explicit QA PostgreSQL17 instance. This includes default-generator golden compatibility, V3 shape/class/determinism checks, corrupt-surface rejection, nested privacy filtering, persistence/history/exact restore, numeric rules and existing authentication/archive checks. The earlier31 focused generator/persistence tests also passed. No live campaign baseline or archive destination was modified.

Fresh system **Chromium154.0.8037.57**, Linux headless, three logical CPUs:

- Full `browser_strategic.py` passes at1280×900,656×518 and390×844, including every retained management destination, settlement/report return, panel input, historical read-only behavior, auth clearing/stale responses, theme persistence/OS changes/storage failure, no theme API calls and retained canvas/camera/selection/overlay. Actual Chrome tab zoom100/125/150/200% passes direct Hearth→Cinder→Reach navigation, with full physical viewport captures. At200%, CSS viewport640×436 and DPR2; controls are not stranded. No uncaught page errors. Evidence: ignored `data/map-legacy-regression/metrics.json` and full screenshots.
- `browser_cartography.py` passes on a newly created isolated V3 fixture plus a separately retained legacy fixture: four levels in Light/Dark, actual marker descent, distinct deterministic Orbital/Survey, Light/Dark/System with unchanged terrain pixels and zero requests, same canvas,24 style changes with stable DOM/listeners, touch controls/force stacks, unknown-campaign clearing and unchanged snapshot hashes. Evidence: ignored `data/map-release/`.
- Full protected `browser_movement.py` passes on its disposable legacy fixture after the unlocated-endpoint integration correction. Player denial, exact GM packet/preview/commit, JSON preservation, pending-preview invalidation, actual ground transit, owned fleet departure3/arrival5, refresh/arrival/history/campaign clearing and phone targeting/counter separation pass. An unlocated destination produces recorded timing/from/to plus **Position unavailable**, without a fabricated SVG connector.24 redraws retain canvas and122 listeners before/after; DOM nodes1557→1563 are bounded. Evidence: ignored `data/map-release/movement/movement-results.json` and full captures. These protected mutations are test evidence, not actions on the read-only critic preview.

The first full strategic run found the real200% defect; the initial movement run found the missing unlocated transit readout. Neither failed run is counted as acceptance. Their successful reruns and preserved corrective tests establish the final behavior. WebKit's Playwright executable is absent in this environment; bundled Chromium is also absent, so system Chromium was used explicitly. WebKit, native macOS Safari and physical touch devices remain unverified. Older branch WebKit results do not establish new coverage.

## Independent final verdict

The same GPT-6.1 Sol medium critic accepts the scoped cartography/interface after resolving every identified critical/major finding. Its own actual interactions covered normal desktop/phone settlement reports, actual hierarchy mouse/touch descent, unlocated inspection, appearance/OS changes, styles and military overlay reading. It separately clicked through the short-height640×436 CSS viewport; root/builder supplied actual Chrome200% tab-zoom coverage. Its last unlocated-transit check used a full fresh committed-flow capture and passing protected-test report, not independent GM authentication/commit. Evidence boundaries are intentional.

Final full captures include `/tmp/map-review/final-1440-orbital.png`, `final-390-orbital.png`, `final-short-system.png`, `final-military.png`, and ignored `data/map-release/movement/fleet-transit.png`. The critic preserves minor blurred/stylized relief bands, cardinal/orthogonal river runs, small metadata, limited overlay stacking room (the Forces control can cover part of the unlocated-card heading at short heights while its row remains reachable) and unused phone space at default overview scale. These do not block the exercised journeys; they are not erased by an average score. Concept A remains substantially richer in geological detail. No whole-game, Victoria3/CK3/Stellaris or illustrated-concept parity is claimed.

## Performance observations

Environment: shared Linux QA, three logical CPUs, Python3.12, PostgreSQL17, system headless Chromium154,1440×1024 renderer viewport; other tests ran concurrently. Frozen V3 measurement: four planets generate in327ms; validation averages13ms over20 calls; initial state271,940 JSON bytes and public projection247,861 bytes. This is a compact fictional fixture, not a production-scale world or network benchmark.

The first measured cold raster build took about1.75s. Reusing horizontal interpolation scanlines and eliminating per-pixel allocations preserves the rendered values (only1 Orbital /23 Survey channels differed by a rounding unit across5.9million channels in the builder comparison). Subsequent measurements were217–411ms per cold style raster; root's final contended sample was396ms Orbital/411ms Survey.20 warm synchronous draws per style averaged6.0ms/4.5ms in that sample, with maxima34.3/35.8ms. These direct calls exclude compositing, input, network and force DOM work; they are not FPS or worst-case latency claims. Temporary scanlines are released; at most two style rasters are cached per weakly referenced live geometry.

Broad legacy management test: first Economy action-ready213ms, Construction190ms;24 warm cycles median24ms /p9569.6ms, one de-duplicated cold history request, stable DOM5302nodes/189listeners before/after. Final V3 style-switch actions average16.8ms with1174DOMnodes/114listeners before/after; military-redraw actions average50.5ms with122listeners before/after, separately recorded in their JSON evidence; Playwright action-to-completion timings include automation overhead. No handler accumulation, unnecessary canvas remount or exercised JavaScript error was observed. Full snapshots retain saved geography each turn; the new persisted fields increase storage/validation cost, so this opt-in candidate does not imply production-scale persistence performance.

## Final long-run gate and delivery

Implementation milestone: **`c5e9516` — Add versioned terrain and map-first orbital charts**; verified context clarification: **`049c6a2` — Clarify planetary surface-style availability**. Planning remains `4cad437`; original `feature/map-desktop-shell` work is not merged or rewritten.

Frozen-source V3 connected gate: **10,000 turns PASS in1,263.39s**,10,001 immutable source snapshots, population1,199, largest serialized state275,778 bytes, summed serialized source-state bytes2,192,674,403. Exact checkpoint hashes and restore into a new branch pass; source timeline remains at10,000. Current-state read25.5ms;50-entry history page1,305.3ms. This is JSON payload accounting, not measured physical PostgreSQL disk use. Source hashes in ignored `data/verification/stress-v2.json` match the committed generator, universe, store and unchanged numeric engine. Compared with earlier compact V1 evidence, the full-snapshot surface fields materially increase history/storage cost. Separately referencing immutable geography would require a deliberate persistence migration and is outside this compatibility-preserving release.

Final `browser_cartography.py` recheck after integration fixes passes:24 style changes average16.83ms action-to-completion,1174DOMnodes/114listeners before and after, no page errors. Protected movement and broad strategic results are recorded above. Syntax/compile and final diff-whitespace checks pass. Final cleanup removed two unreferenced declarations, with syntax verification. A final context clarification disables the surface-style control outside Planet view rather than presenting an inert action; the cartography regression explicitly checks enabled/disabled states across all four levels.

This is an **interface release candidate**, not a deployment or operational-security/backups/recovery certification. No merge, deployment, data reset, live archive write or fabricated campaign recovery occurred. Credentials, databases, QA snapshots, screenshots and generated concept/runtime files are excluded from Git. Remaining future work: real source/data recovery and explicit import, larger/global geography contracts if required, independent native/browser/device coverage, production-scale persistence profiling and separate character-relationship integration. Retain the documented minor visual limitations rather than treating them as commercial parity.

## Independent generation presets — subsequent user direction

Opt-in `planet-v4` adds separately chosen Continental, Archipelago, Oceanic, Arid, Barren and Frozen planet presets. Dry/frozen choices genuinely contain no open water, vegetation or rivers; their rendering, legends and surveyed body glyphs reflect saved records. Stable auto selection and explicit per-planet creation overrides preserve independent world identity. V1/V2/V3 maps and generation remain unchanged. Creation stays in the existing CLI/Store path, with no live map preset switch or new web write endpoint.

The user subsequently set **desktop-only acceptance**. See [planet-presets review](../reviews/planet-presets.md) for exact options/commands, architecture and localized correction, independent desktop findings, tests, performance and continuing limits. Earlier phone evidence above remains historical and does not define ongoing acceptance. Implementation milestones: `af28097`, `01c4271`.

## Continuous map navigation — subsequent delivery

The user approved replacing the exposed regional rectangle with a larger saved
surface and natural map navigation. Opt-in V5 generates128×80 cells with forty
16×16 provinces; V1–V4 outputs, existing geography, campaign records and rules
are preserved. Legacy projection keeps its compatibility path; V5 membership
uses saved rectangles. No hidden terrain is generated by the client.

The main map fills the canvas and pans within its saved extent. Wheel zoom
anchors to the cursor; buttons zoom around the clear viewing area. Cover-relative
zoom reads100–500%, with V5 opening at200%. Grab/grabbing cursors, a full-extent
overview with viewport outline, and a separate Recenter action expose navigation.
The overview supports pointer navigation and keyboard centering, and stays clear
of the inspector. Cached stable recorded land anchors unify labels, military
anchors and recentering; displaced holding labels remain selectable under fixed
chrome. Planetary labels/counters avoid the overview and measured Forces control.
Light/Dark/System and Orbital/Survey remain independent controls.

Bounded Sol high contract review and independent Sol medium desktop critique
passed. The critique's major legacy holding-access issue and minor zoom/minimap
findings were corrected and reassessed by the same critic. The last minor Forces
collision received localized browser QA. Remaining minor limits are faint terrain
boundaries and peripheral navigation instructions. This is a comparison against
the actual prior build; no commercial-game parity or new reference study is claimed.

Verified:93 distinct Python tests, final desktop navigation across six V5 presets
and both styles, existing preset/V3 cartography/broad strategic browser regressions,
actual Chromium browser zoom100–200%, stable canvas/listener counts and no page
errors in exercised paths. Initial backup-test failure was a missing QA `pg_dump`
PATH entry; the test passed with existing PostgreSQL17 QA tools configured.

The mixed V5 **10,000-turn gate passed in2529.31s** with10,001 immutable source
snapshots and exact history/restore assertions. Current read60.1ms; history 50
3980.1ms. Full surface arrays make snapshot/history storage expensive: summed
source JSON7.50GB, distinct from physical database disk use. Raster size remains
1536×960; sampled warm direct draws averaged2.0–14.3ms under concurrent QA.
These fixture observations are not production-scale performance guarantees.

Read [continuous-map review](../reviews/continuous-map.md) for exact evidence,
review resolutions, creation command and integration notes. Chromium154 is
verified; WebKit/native Safari remain unavailable/unverified. Desktop is the
acceptance scope. Charts remain finite and planar; wrapping, waves, spherical
generation, partial reconnaissance and immutable-geography persistence migration
are separate future work. Do not regenerate old maps to integrate unrecovered
cartography. The character-relationships branch remains untouched.

Delivery is an **interface release candidate**, with no merge or deployment.
Implementation: **`c488e3f` — Add larger saved planetary charts and continuous
map navigation**. The following documentation commit records this reference;
backend hashes in the completed stress report match the implementation. The
next substantive work is separately versioned seam-aware generation or a
reviewed immutable-geography persistence design, rather than converting old
campaigns or adding decorative terrain outside saved geography.


## V6 cylindrical-chart continuation — 23 October 2026 (Australia/Melbourne)

New opt-in `planet-v6` supplies genuine east–west periodic terrain and hydrology
at128×80, with forty16×16 canonical provinces and bounded north/south. V1–V5
outputs/defaults and existing records are preserved. The client uses the same
wrapped projection for raster interpolation, rivers/contours, overlays, labels,
selection, forces, short endpoint connectors and split overview footprints.
`EAST–WEST WRAPPING` and `EAST ↔ WEST JOIN` disclose the navigation model;
Recenter, overview navigation, cursor zoom, management context and Light/Dark/
System remain available. No saved map is converted or regenerated.

One bounded Sol high review accepted the backend contract and independently
matched45 legacy private/public baseline pairs. Luna implemented the first
candidate; a real browser runtime failure escalated locally to Sol medium.
The fresh independent Sol medium critic accepted scoped desktop navigation
after correcting Forces hover contrast, legend/overview/counter overlap,
wrapping explanation and clipped label leaders. It directly verified repeated
seam drags, selection/zoom/overlays, overview keyboard/pointer, inspector input
isolation, management return, transit connector visibility and desktop resize.
Remaining minor points: small metadata and a visible polar route close to the
breadcrumb. The anonymous A/B assessment preferred the older capture's
landmarks; differing terrain/scale prevent an overall visual winner claim.

Verified Python discovery:98 tests passed. V6 six-preset/both-style navigation,
canonical seam hits, real DRAFT/PREVIEW/commit and read-only history pass, along
with legacy V5 navigation, V4 presets, V3 cartography, movement and broad
strategic/auth/browser-zoom regressions. Final V6 and movement reruns passed
after the presentation corrections. Exercised workflows had no page errors;
map canvas/window handlers remained stable. Chromium154 verified; WebKit/native
Safari unavailable/unverified. Desktop only.

Cold direct-render samples309.5–784.6ms; ten warm draws averaged1.7–18.9ms
per style/preset under concurrent QA, capped at1536×960 raster. These omit API,
input, force DOM and compositing and do not establish production performance.
The mixed V6 **10,000-turn gate passed in2722.03s**, retaining10,001 immutable
source snapshots and exact checkpoint/history/restore assertions. Largest state
956,759 bytes; summed source-state JSON7,481,633,246 bytes (not database disk
use). Current read60.0ms;history 50 read3721.7ms. All stress-report source hashes
equal the initial freeze and final backend. Delivery references follow below.

Read [cylindrical-chart review](../reviews/planet-wrap.md) for exact boundaries,
critique/evidence and creation command. The user's planet-photo question
exposed a separate art gap: barren/frozen maps mostly read as recolored relief,
continental rivers can be too uniform, and lunar craters, ice fractures,
volcanic terrain and gas-giant atmospheres are not generated. New NASA reference
fetches returned403; no fresh photo comparison or realism acceptance is claimed.
Future geological/body families must remain separate from creation-time water/
vegetation presets. Saturn-like worlds require atmospheric/orbital presentation,
rather than terrestrial province textures. Do not disguise this with decorative
statistics or fabricate records.

No schema/numeric-rule change, character-relationships branch edit, recovered
cloud data, merge or deployment. Integration must preserve old generator versions,
canonical IDs and surveyed-only public allowlists. Full immutable surface arrays
still impose known history/storage cost; deduplication requires its own reviewed
persistence design. This remains an interface release candidate.


Delivery implementation: **`d43a4cd` — Add opt-in cylindrical planetary charts
and seam-aware navigation**. This follow-up documentation commit records that
reference. Backend hashes in the completed V6 stress report match delivery.
Continue from this release without converting old maps; address geological
families or immutable-geography persistence as separate reviewed work.


## V7 cratered-world and presentation continuation

User authorized implementation after the actual V6 captures showed weak barren/
frozen identity, angular rivers/coasts, heavy grid labels and excess chrome.
New opt-in `planet-v7` saves40–64 varied crater descriptors for explicit
`cratered` geology on dry Arid/Barren/Frozen worlds; `none` remains the V7 default.
Water/vegetation presets and per-planet geology choices are separate creation
inputs. Wet+cratered is explicitly unsupported by the current depression-fill
hydrology. Existing V1–V6 generation/private/public outputs match63 committed
baseline pairs; old campaign geography/history is never regenerated or converted.

The renderer reconstructs only saved subcell crater geometry, preserving canonical
elevation samples and seams. Matching gradient stencils removed bowl crosshatching;
soft normalized northwest lighting now makes concave depth clear. Ocean contours
require recorded ocean drainage/non-null sea level, preserving waterless worlds.
Muted tapered river strokes and sea-contour coast treatment improve readability;
Terrain hides generic province grids/names below250% while holdings/selected names
and the explicit Provinces overlay remain available. Desktop header spacing is
more compact, the empty Forces mark is gone, and1024px captions/legend no longer
overlap. Light/Dark/System, Apple functional accents, selection/camera/overlays,
management context, authority and recorded numeric rules are preserved.

The bounded Sol high review accepted corrected backend contract/privacy checks.
Luna built the first candidate; localized Sol medium corrections closed strict
validation/allowlist gaps and presentation artifacts. The same fresh independent
Sol medium critic accepted the corrected idealized cratered rock/ice scope after
anonymous matched full-frame comparison and bounded live navigation/inspection/
Economy/map-level/style/resize checks. Its external usage-limit interruption was
resolved by resuming that same critic; no approval-shopping substitute was used.

111 Python tests and the canonical/seam/dry-renderer Node check pass. Final private
V7 six-preset/both-style seam navigation, overlays, management return, real movement
DRAFT/PREVIEW/commit and historical read-only return pass. Legacy V5 navigation,
V3 cartography, broad strategic/auth/browser-zoom and protected movement regressions
pass. No exercised page errors; canvas identity and map/window handlers remain
stable. Browser evidence is Chromium154; WebKit binary absent/native Safari
unverified. Desktop-only acceptance; older responsive tests are supplementary.

Mixed V7 **10,000-turn gate passed in2465.58s**, retaining10,001 source snapshots
and exact conservation/checkpoint/history/restore assertions. Largest state
968,119 bytes; summed source JSON7,582,653,347 bytes (not physical disk use).
Current read64.9ms;history 50 read4095.5ms. Final backend hashes match the stress
report and initial freeze. Rendering samples and exact critique/evidence are in
[cratered-world review](../reviews/cratered-worlds.md).

Remaining limits: idealized circular profiles and nested overlaps, coarse landform
boundaries/axial four-neighbour rivers, full-snapshot history/storage cost, and no
new NASA photo comparison (network policy excludes those hosts). Fractured ice,
basalt composition/maria, volcanic resurfacing and gas atmospheres remain separate
future families. No physical/scientific realism, commercial-game parity, original
cloud recovery, character-relationships merge, schema/rule migration or deployment
is claimed. This remains an interface release candidate. Delivery references are recorded below. Integrate recovered cartography through explicit versions
and surveyed-only allowlists, not old-map conversion.


V7 delivery rendering observations: shared Linux2 CPU quota, Chromium154,
1440×1024 viewport and1536×960 rasters; cold direct draws143.6–472.2ms,
ten-draw warm averages0.36–5.02ms, campaign-to-first-draw697.8–1243.7ms.
Direct renderer samples exclude API/input/compositing; no production FPS claim.

V7 implementation and verified source: **`ed66cb6`**. Subsequent liquid-lake and
polar-cap options are a separate opt-in continuation; this verdict covers V7.


## V8 lake materials and polar caps

User requested separately chosen lava/other liquid lakes and polar ice caps.
Opt-in V8 adds saved 128×80 composition masks with explicit lake choices
None/Water/Hydrocarbon/Lava and cap choices None/Water ice through existing
new-campaign CLI/global/per-planet flags. Existing presets and cratered geology
remain independent; no existing records, base geography or rules are converted.
Supported authoring combinations and integration contract are documented in
[surface-material review](../reviews/surface-materials.md).

Luna's incomplete first backend attempt was escalated to localized Sol medium.
One bounded Sol high review accepted strict contracts/privacy, all 90 legacy
private/public pairs (180 hashes),34 exact V7-base variants and hidden canaries.
The same fresh visual critic accepted the corrected candidate after anonymous
stills, specific material/river/anchor findings, implementation and frozen live
recheck. Initial failures and remaining minor limits are retained in the review.

122 Python tests, focused renderer checks, corrected protected V8 six-preset/
both-style seam/overlay/context/order/history browser workflows, and V7 navigation
plus V3 cartography regressions pass. No exercised page errors; canvas/handlers
remain stable. Chromium 154 on shared Linux was tested; WebKit binary absent and
native Safari unverified. Desktop acceptance only. The final 10,000-turn V8
persisted fixture gate passed in 3291.49 s with 10,001 source snapshots, conservation,
history/checkpoint and exact independent restore checks. All 11 backend hashes
match the initial freeze, report and pushed implementation **`50a4afa`**.
Largest state 1,050,779 bytes; source JSON sum 8,408,795,953 bytes (not disk use).
Current read 75.1 ms; read of 50 history records 5558.8 ms remains a full-snapshot limitation.

Known scope limits: coarse/soft lake shores, idealized overlapping craters,
coarse biomes/axial rivers, small legend type, long tooltip under inspector,
full-snapshot storage/history cost and unsupported authoring combinations. No
new hazards, movement barriers, lake resources or production rules are invented.
No physical/photo realism, whole-game parity, original cloud recovery, character
branch merge, schema/rule migration or operational deployment is claimed.


V8 actual desktop Chromium tab zoom 100/125/150/200% passed in a 1920×1280
window (CSS 1920×1193 down to 960×596), including the full material legend,
command/campaign/map controls, Economy return and hierarchy. Full source,
independent review, test, browser and performance limits are in the linked review.
Implementation delivery: **`50a4afa`**; this follow-up record completes its gate.


After other checks finished, shared 2-CPU Linux/Chromium 154 direct renderer
samples at 1440×1024 with 1536×960 rasters ranged 323.8–856.7 ms cold;
ten synchronous warm-draw averages ranged 1.09–5.23 ms across eight material/style
cases. Concurrent-load samples and exclusions are retained in the review.
No production FPS or physical/photo accuracy is established.

## V9 hydrographic names and feature inspection

Opt-in V9 wraps the unchanged V8 map with saved identities for connected ocean/
sea/lake regions and existing recorded river courses. Names are independently
optional generated fiction or operator-supplied at new-map creation. The CLI
provides a no-database `--catalog` authoring preview and `--feature-names-file`;
there is no live rename endpoint or retroactive naming of existing maps. V1
remains the default. All 120 V1–V8 private/public baseline cases, 240 hashes,
remain exact. Terrain, history, IDs, auth/intelligence and numeric rules are
preserved. The user requested desktop acceptance only.

The permanent map retains one inspector. Names is a UI preference; Features
exposes every surveyed catalog record even when labels are hidden for fit.
Selection carries actual kind/material/name provenance and underlying province;
legacy V8 composition remains inspectable without fabricated identities. Labels
use recorded interior cells/readable unique river spans, safe bounds, collision
checks and canonical IDs. River coordinates unwrap before screen projection;
painted-name selection uses the visible recorded cell rather than jumping to a
remote saved anchor. List selection still uses that anchor when needed. Blue
river strokes, quiet relief/shore treatment, bounded list scrolling, max-length
name wrapping and compact desktop controls address the demonstrated critiques.

Luna built the initial backend/UI candidates. Localized Sol medium corrections
resolved concrete high-review and browser findings. Sol high accepted explicit
surveyed nested projection and strict persistence contracts, then diagnosed and
verified the later panned-river coordinate/visible-span fix. The same independent
Sol medium critic preserved all initial findings and accepted the corrected
scope after fresh screenshots and bounded real-browser checks. A favourable
stills verdict did not override the later panned-browser failure. Exact findings,
resolutions, actual references, authoring examples and limits are in
[hydrography naming review](../reviews/hydrography-names.md).

Verified before the final persisted-turn gate: 132 Python tests; 240 exact legacy
hashes; hydro-label/material/crater renderer regressions; full protected V9 six-
preset/both-style seam, selection, Names mouse/keyboard/touch, literal/80-character
custom name, management return, DRAFT/PREVIEW/commit, history, sign-out and stable
canvas/handler workflows; legacy V3 cartography and broad strategic regressions.
No exercised page errors. Actual Chromium Settings zoom 100/125/150/200% passes
1280×960 and 1920×1280 physical windows, including Names/Features and inspector
close. At <=550 CSS-pixel height the informational legend/resource strip is
intentionally hidden to preserve controls. WebKit binary is absent; native
macOS Safari remains unverified. This is not a compliance certification.

Observed direct renderer samples on shared Linux 6.18.55 / glibc2.41, 2-CPU quota,
Chromium154, 1440×1024 with 1536×960 rasters, concurrent V9 gate: cold537–1612.9ms;
ten-draw warm averages Names On1.95–14ms, Off0.84–5.37ms, selected1.17–7.8ms across
eight fixture/style cases. These exclude API/input, force DOM, compositing and
GPU residency; no production FPS or large-campaign claim.

Implementation **`feaf766`** is pushed. The frozen V9 10,000-turn gate passed
5450.49 seconds with 10,001 snapshots, conserved fixture population, unchanged
geography and exact history/independent restore. All twelve source hashes match
freeze, report and committed code. Largest state 1,183,300 bytes; snapshot JSON sum
9,538,588,921 bytes (not disk usage); current read 161.4ms; history 50 10,021.3ms.
These shared 2-CPU fixture measurements establish a full-snapshot scale limit,
not production capacity. Exact ignored report: `data/hydrography-pass/stress-v9.json`.

Continuation: user requests increased planetary geographic scale with a Google
Earth-like sense of descent. Diagnose renderer, geometry and persistence together
before expanding grids; preserve all saved maps and version any new generation.

Known limitations: 128×80 coast/biome sampling and soft shores, axial saved river
routes, idealized quiet craters, sparse overview labels, province-level ice
emphasis, high native zoom consuming map space, and full-snapshot history/storage
cost. No new NASA optical-photo comparison, physical/cartographic atlas parity,
whole-game commercial parity, recovered cloud data, character-relationships
merge, operational security, deployment or backup-service verification is claimed.
This remains an interface release candidate. Recovered cartography should join
through explicit generator/catalog versions and surveyed public allowlists;
never regenerate old records. Character inspection remains a separate existing
integration point.

## Native V10 backend milestone

The requested increase in planetary scale required fine-first generation. New
opt-in V10 worlds save1024×640 natural geography (64×V9's sample count), then
derive128×80 strategic summaries and forty canonical province IDs. Existing
V1–V9 worlds/defaults/IDs/history and turn rules are preserved. Names, waterless
classes, independently chosen liquids/caps and surveyed visibility remain explicit.
Immutable assets are stored once, scoped to selected campaign/snapshot/planet
reads, included in surveyed archive bundles and exact PostgreSQL recovery. No
fine arrays repeat in turn snapshots. See ADR014 and the full
[scale review](../reviews/planet-scale.md) for rejected designs and current status.

Verified frozen backend:147 Python tests;264 exact legacy private/public hashes;
10,000 fixture turns in459.36s with10,001 snapshots and exact history/restore. Four
assets total20,906,145B, unchanged through turns/branch; snapshot JSON713,976,548B;
largest state75,232B; current read12.0ms; history50 290.1ms. These shared2-CPU local
measurements are not disk usage or production performance. Original cloud data
has not been recovered or replaced. No merge/deploy. Frontend completion remains
pending the same independent critic's dry/ice relief reassessment.

## Orbital navigation release candidate — 27 October 2026

User priority is “Globe to surface: orbit a planet, then smoothly zoom into
strategic terrain.” New V10 worlds open a genuine rotatable sphere over the same
saved geography. Wheel/+descent and outward zoom return between globe and the
existing strategic surface, retaining geographic focus. A short projection
dissolve has matched vertical scale and a native-detail endpoint; it is not an
exact geometric unwrap. Orbit/Surface is always explicit; reduced motion and
WebGL-unavailable/context-loss surface fallback are supported. Surface selection,
feature search, force targeting, management return, history and authentication
retain their existing authority. Light/dark remains toggleable.

Native surface quality corrections include fine anchors, searchable recorded
features, exact-sea coast colors, background-normal filtering with separate
craters, and readable frozen/ice contrast. Independent review rejected additive
detail, dry grid artifacts, ice washout, stale orbital picking and polar spokes
before accepting the final scoped candidate. The final globe exports unlit
composition and uses spherical lighting; Surface retains detailed relief and
Survey contours. Do not reuse Cartesian chart normals on the globe. Full
findings, reference pins, comparison record and evidence are in the
[scale review](../reviews/planet-scale.md).

Verified:147 backend tests,264 legacy private/public hashes and the frozen
10,000-turn persisted gate described above; five relevant native/legacy renderer
checks; protected Chromium settlement→Economy→Construction→Map, feature search,
canonical movement preview/commit, read-only history, campaign/logout stale-work
rejection and persistent canvas/handlers; read-only globe controls, rotation,
context preservation and explicit fallback. No exercised JavaScript page errors.
Actual Chromium154 Settings zoom100/125/150/200% passes1280×960 and1920×1280
physical desktops. WebKit absent; native macOS Safari unverified. Desktop only.

Final shared2-CPU Linux1440×1024 measurements: cached Surface ten-draw means
2.19–15.90ms across four native families/two styles; not cold or GPU/FPS evidence.
Loopback map reads77.91–103.76ms, detail1067.59–1670.77ms. Twenty warmed workspace
cycles keep one canvas,2602nodes,369listeners and7canvas listeners; collected heap
33.74→33.89MB is reported, not proof of indefinite leak freedom. Native generation
sample23.762s/182MiB. Full source-hashed evidence remains ignored under
`data/planet-scale/`. Backend10,000-turn fixture metrics are not production scale.

Limits: globe is an albedo navigation sphere without displaced terrain or
orbital crater relief; rock worlds may be sparse. Polar material distortion,
stepped/soft native enlargement and synthetic ridge/climate ribbons remain.
There are no physical kilometre units or additional streaming detail. No Google
Earth, atlas/optical accuracy or whole-game commercial parity claim. Original
cloud cartography/private data remain unrecovered; no data reset/merge/deploy or
character-relationships branch change. Integrate recovered work through explicit
generator/asset versions and surveyed allowlists; retain the existing Characters
management entry. The observed inherited startup migration/writer deadlock
needs separate operational work before concurrent deployment. This is an
interface release candidate, not operational security/backup certification.

Delivery: native backend [`128a45a`](https://github.com/syouyoshino/HAMMER-WORLD/commit/128a45a94d260557c0a5b25f79a73492b27554e4)
and interface/tests [`34a9f25`](https://github.com/syouyoshino/HAMMER-WORLD/commit/34a9f25329701989828dc8114694031f0cdbf1ac)
are committed and pushed to `origin/map-generation`; remote refs were checked.
No merge or deployment.

Continuation: keep the frozen backend and existing saves intact. For a new
isolated preview, use `python -m app.cli init-v2 --campaign-id NEW_ID
--planet-generator planet-v10 --preset continental --feature-names generated`
with the configured PostgreSQL environment; never reuse a real campaign ID.
Run the committed native/orbit browser regressions against isolated fixtures.
Further globe detail should use proper spherical height normals and real LOD
assets, with separate architecture/persistence review; do not restore baked
planar shadows. Address startup migration/writer coordination separately before
operational deployment. Native Safari and remote performance remain unverified.

## Orbital settlement orientation — 27 October 2026

New recorded settlement markers make the previously sparse navigation globe
useful for finding places. Symbols, short leaders and compact square labels
project exact saved province anchors; front-visible labels prioritize selection
and ownership, group shared anchors, avoid panels/collisions and cap at12.
Activate a symbol/name with mouse, touch, Enter or Space to descend to that
province and open its inspector. North-up is visible and Hydro names explicitly
controls sea/lake/river labels. Selected symbols use the existing Apple system
blue in both themes. No new terrain, physics, campaign fields or persistence.

Independent blind A/B review identified orientation, anchor pairing and label
state ambiguity; follow-up review accepts the corrected annotation workflow.
Root checks also fixed focus loss on resize, cap-before-visibility filtering and
inactive DOM accumulation. Full findings and preserved evidence are in the
[orientation review](../reviews/orbital-orientation.md). Minor Surface/orbital
glyph inconsistency, natural-rock sparsity and physical polar material distortion
remain documented; no whole-game or optical-fidelity comparison is implied.

Verified: focused Node layout/projection/hydro-label checks; read-only saved-anchor
selection, keyboard/touch, resize focus, backside/old-hit behavior, management
return, campaign/fallback clearing and unchanged campaign records; protected
real preview/commit/history/auth/stale-request regression. Actual Chromium154
Settings zoom100–200% passes1280×960 and1920×1280 physical windows. No exercised
page errors. WebKit/native Safari unverified; desktop scope only.

Twenty warmed map/management cycles keep the same canvas,1302DOM nodes,130JS
listeners and two visible annotations. Small-fixture layout mean0.043ms/max0.300ms
excludes DOM/GPU and is not production FPS. Backend and terrain/sphere renderer
hashes are unchanged; prior147/264-hash/10,000-turn gates were not repeated for
this frontend change. Original cloud data remains unrecovered. No merge, deploy
or data reset; character-relationships work remains untouched.

Delivery: orientation implementation/tests/review [`61f19a8`](https://github.com/syouyoshino/HAMMER-WORLD/commit/61f19a854af875c0c26bb718d4d1da623adf7c99)
is committed and pushed to `origin/map-generation`; the remote branch reference
was verified. No merge or deployment. Continue through the existing versioned
asset integration boundary if adding spherical terrain/LOD; keep annotations
derived from public records and retain exact province-anchor semantics.


## Desktop quality-control follow-up — 27 October 2026

Fresh current-run screenshots and interactions exposed contradictory initial
campaign state, terrain behind report text, missing/stale pressed semantics and
an unnamed campaign dialog. Bounded Luna implementation and localized Sol medium
correction resolve these findings. Persistent settlement context, known units,
grouped identical facilities preserving IDs and an explicit project empty state
complete the representative settlement journey. The same independent Sol medium
critic accepts the scoped corrected visual candidate; no major finding remains.
See `docs/reviews/quality-control.md` for step health, evidence, tests and limits.

All generation/backend, native map, sphere and annotation module hashes remain
unchanged. Preserve these boundaries when integrating unrecovered cartography;
UI scope/context changes introduce no campaign data migration. Native Chromium
protected campaign/auth/history/movement regression passes. This is an interface
release candidate, not deployment or commercial/Google Earth parity. Prior
references remain recorded above; no new commercial comparison is claimed.


Desktop checks: actual Chromium154 tab zoom100–200% at1280×960 and1920×1280;
additional1280/200% Recenter center hit-testing after a narrow-toolbar overlap fix.
Independent review accepts the correction; extreme shortheight minimap/footer
proximity remains minor. Twenty warmed panel cycles retain1302 nodes,130 listeners,
two landmark nodes and one canvas; annotation-layout mean0.045ms/max0.200ms is not a
renderer/frame-rate benchmark. Linux two-CPU quota; WebKit and native Safari were
not tested in this pass. Keep the detail/albedo contracts intact for later globe
LOD work; no campaign records or generation profiles were modified.

Final focused `tests/browser_quality_control.py` passes: keyboard modal cycle,
truthful startup/pregame state, canonical settlement selection, both scopes in
both reports, nine facility IDs retained, light/dark screenshots and exact map
return. Public demo/pregame records stay unchanged and no page errors occur.
Delivery code/docs/test commit: `917fb6af3e979804ff8dca72f2d10c1fdf2703b4`, pushed to `origin/map-generation`.


## All-environment quality control — 28 October 2026

Expanded the same desktop settlement journey to all six terrain presets and the
implemented water/lava/hydrocarbon and polar-ice choices: nine representative
profiles, both themes. Four existing fictional fixtures remain unchanged; five
missing variants were generated in a separate disposable QA schema. This is not
an exhaustive seed/option-combination certification. Read
`docs/reviews/environment-quality.md` for per-step evidence and limits.

Fresh review corrected faint Complete labels, an obscured northern lava anchor,
a minimap-obscured southern anchor and redundant empty-catalog search copy.
Neutral status labels retain Apple-green square accents. Native-only vertical
pan limits use the existing safe viewport; feature reveal candidates avoid live
inspector/overview/force DOM rectangles. This is app camera/presentation work:
no backend, schema, terrain engine, assets, geography/IDs or relationship-branch
change. Preserve these small app/style boundaries when integrating unrecovered
cartography. The full map, sphere and landmark module hashes remain unchanged.

The critic rejected early transition screenshots despite passing functional
assertions; final primary captures explicitly wait beyond the420ms transition.
Ninety settled primary frames are in the ignored local screenshot gallery. The
same critic accepts all nine primary placements and corrected demonstrated lava
selection. Latest feature-material edge checks and final delivery references are
recorded in the review. No merge, deployment or real campaign recovery is claimed.


Final environment matrix: all9primary + all9material checks pass. Forty-five
saved-feature anchor samples cover north/south/chosen records at regional,
minimum and maximum detail. Empty catalogues remain empty on caps/arid/dry-rock/
frozen; no fake water or rivers. Public fixture records stay unchanged; no page
errors. The single Sol medium critic accepts all nine tested profiles after the
corrections; inherited low terrain/legend/ice-outline limits are documented.
The protected private native suite passes, including refined open-water picking,
legacy switching, stale work, movement preview/commit/history and logout. Its
fixed picking harness now uses actual safe bounds and excludes ice from its
open-water test. Primary/auth evidence precedes only the final feature-only DOM
obstacle correction; latest-source materials tests cover that callback directly.
No production performance or commercial-game parity claim follows. Current
coverage is Chromium154 desktop1440×1024; WebKit/native Safari unverified here.

The ignored gallery at `data/environment-quality/final/gallery.html` contains126
primary/material frames and was visually checked through a loopback-only preview.
Keep generated captures, databases, test schemas and connection context out of
Git. Replay commands and continuation paths are in the review. Delivery implementation/tests/review: `2c918fd9ddacde764d203288e3dc2486f8e9701f`,
committed and pushed to `origin/map-generation`; remote reference verified.


## Adaptive orbital space — 28 October 2026

The supplied space image informs a near-black/slate haze and sparse star pins,
with no copied or invented ships. New `orbit-background.js` follows the orbital
camera basis and bounded zoom response using generic fixed directions. It is
visual decoration, not generated campaign astronomy. Both UI themes share the
same physical backdrop. The existing globe/shader, surface engine and geography
remain unchanged. Minimal app compositing flattens sky+globe once during fades
using a capped/released temporary canvas; optional-code failure falls back cleanly.

Fresh anonymous comparison rejected the first flat-looking navy candidate. One
localized correction made the haze perceptible and fixed alpha compositing. The
same independent Sol medium critic accepts the scoped revised appearance and
camera/transition/resource evidence. Node sky/projection/landmark contracts,
actual Chromium drag/zoom/background-pixel/idle/Surface-Orbit-cycle checks and the
protected auth/history/movement/stale-response/logout suite pass with no page
errors. See `docs/reviews/adaptive-space-background.md` for source boundaries,
full-frame captures, unretimed motion records and performance limits. No native
FPS, GPU, WebKit or macOS Safari claim; inherited terrain/globe quality is separate.

Integration: retain the new script immediately after `planet-orbit.js`; its
projection consumes the existing camera basis and safe rect. Do not entangle
this decoration with campaign state, hidden seeds, renderer assets or auth tokens.
No backend/numeric source changed and no simulation stress rerun was warranted.
Keep runtime media and database context out of Git. Delivery implementation/tests/review `9a78a627effded1f3ab57e9e06512db53062ebaa`
is committed and pushed to `origin/map-generation`; no merge or deployment.


## Orbital background depth — 29 October 2026

The user's flatness critique prompted a new comparison and correction. Layered
curves and then elliptical dust bands failed for visible tubes/streaks; those
findings remain documented. One bounded Sol high diagnosis led to continuous
world-ray noise instead of another cosmetic pass. The final 128-side cached bitmap
adds irregular slate cloud masses, dark gaps and restrained varied stars while
preserving camera orientation, theme consistency and existing renderer modules.

Read `docs/reviews/orbital-background-depth.md` for the independent comparison,
actual browser evidence, performance costs and retained softness/globe limits.
Integrate only the small background module and its tests; keep unrecovered
cartography, campaign records and authentication independent. No schema, geography,
shader, map-renderer or app-navigation source changes. Generated evidence remains
ignored. This is an interface release candidate, without merge or deployment.

Delivery implementation/tests/review: `5ef3d75` on `map-generation`.


## Globe lighting and celestial data — 29 October 2026

The existing orbital shader now uses stronger continuous form shading, preserving
recorded material colors and all geometry/picking. Independent blind caps A/B and
water/lava/hydrocarbon review accept the scoped roundness/readability improvement;
actual orbital camera/overlay/management-return/context-loss/fallback checks pass.
Read `docs/reviews/globe-lighting-and-celestial-data.md` for evidence and remaining
ice/material artifacts, browser and performance limits.

Accurate neighbouring-body sky placement is explicitly blocked: current positions
are schematic 2D chart coordinates without ephemeris/reference frame/orientation.
No false celestial markers or new campaign records were created. The review lists
the future versioned astronomical contract's required inputs. Existing breadcrumbs
and the safe system chart remain the integration point. Only three shader lines
change product code; unrecovered cartography and the character branch are untouched.
This remains an interface release candidate without merge or deployment.

Delivery implementation/review: `4335f6f` on `map-generation`.


## Saved stellar astronomy — 29 October 2026

The user's chosen direction is opt-in generated astronomy for NEW demos.
`init-v2 --astronomy static-v1` persists frozen epoch0 system positions/radii and
aligned planet frames without altering existing campaigns/default outputs.
Survey knowledge filtering applies before player serialization. In native Orbit,
the recorded host star drives its named marker and directional globe light;
Locate star explicitly navigates to it. Marker scale is disclosed; old native
records show Star unlocated. Initial home and Surface/management context remain.

Read `docs/reviews/celestial-stars.md` for the exact creation command, field
contract, independent high/medium acceptances and rejected camera-projection
candidate. Final tests include private API/persistence/history/restore, 240 legacy
hashes, 10,000 connected turns preserving astronomy, actual Chromium star-camera
ray/lighting/occlusion/touch/history/fallback checks and desktop sizing/resource
observations. Native macOS Safari/WebKit and production FPS remain unverified.
Night-side terrain surveying stays a medium, nonblocking stellar-view limitation.

Integration: retain optional fields unchanged in old snapshots; never infer a
bearing from topological chart x/y. Keep saved-body camera projection separate
from decorative sky projection, and preserve the public allowlist if unrecovered
cartography is integrated. The surface generator/renderer, province IDs and
character-relationships branch are untouched. Dynamic orbits or additional body
classes require a future explicit version; do not reinterpret frozen epoch0 as a
live ephemeris. Runtime evidence/databases remain ignored. No merge/deployment.

Delivery implementation/tests/review: `1887986` on `map-generation`.

## Explicit planet radius and celestial destinations — 29 October 2026

New `planet-v11` demos require explicit metre radii globally/per planet; there is no
Earth-sized default. Size changes actual terrain wavelengths, coast/island grain,
crater/lake sampling and resolution disclosure, while preserving independent
water/lava/hydrocarbon/no-liquid/ice choices. Exact decimal strings support very
small/large fictional sizes within documented representation limits. The fixed
1024×640 overview does not promise unlimited local detail. Existing records remain
unchanged. Optional static-v1 astronomy has its own exact whole-kilometre range.

Stars/moons/known planets now have main-area destinations; surveyed planets use real
maps. Unknown details stay unknown. A context-bound return ticket restores original
camera, selection and overlay across body changes, and clears on history/campaign/
auth changes. Focused stellar glow respects reduced motion; no ring/flare data is
invented. Light/dark remain available. Desktop scope retained.

Read `docs/reviews/physical-scale-and-body-focus.md` for the final contract, creation
example, independent critique/resolutions, browser/performance evidence, research
limits and continuation. Luna's popup and regular large-world terrain candidates
were rejected, then corrected by bounded Sol medium work; Sol high approved numeric
and authority contracts and final kernel. The same critic accepted scoped quality,
with minor coast stepping, occasional square islands and weak directional relief.

Integrate recovered work through optional V11 metadata and immutable detail hashes;
keep old versions unchanged, public allowlists and context-epoch guards intact.
The character-relationships branch is untouched. Future deep zoom requires bounded
real detail tiles; future rings/dynamic orbits require recorded versioned data.
This is an interface release candidate, without merge, deployment or canonical-data
recovery claims.

Verified implementation/tests/review: `39b015f`, pushed to `origin/map-generation`.
Final source-matched 10,000-turn gate passes (598.82s), including detail retention
and exact restore. Nine V11/radius tests, thirteen existing tests, 240 legacy hashes,
eight preserved campaign responses, final Chromium workflows and20-cycle resource/
desktop CSS-zoom checks pass. Full metrics and limits are in the linked review.

## Terrain lighting and desktop reflow — 30 October 2026

Frontend-only continuation from1e69533. Natural-flow command/title/tools/breadcrumbs
and shell-bounded management/dialogs fix control overlap and stranded Map/Close at
high CSS zoom. Existing zoom/recenter controls form one unit; readouts fit content.
Screen/local coordinate conversions preserve map input. Light/dark remain available.

V10/V11 Orbit uses a cached, optional signed-slope texture derived from recorded
heights. Background and crater light stay separate; quiet dry/ice background and
stable warm hydrocarbon fill/legend improve material reading. No geographic field,
material mask, ID, physical radius, turn rule or historical record is regenerated.
There is no Earth-size default. Statistics overlays retain prior lighting behavior.

Read `docs/reviews/terrain-and-desktop-finish.md` for the independent blind comparison,
preserved F1–F6 findings, bounded architectural diagnosis, failed-candidate fixes,
actual lake-in-view evidence, final checks, numeric/resource and browser limits.
The same critic accepts the scoped tasks with no major visual blocker in examined
views; synthetic terrain form, fixed-detail/category steps, faint rivers and very
high CSS-zoom space constraints remain documented debt, not commercial/optical parity.

Integration: retain optional internal canvas relief separately from recorded data;
reuse immutable detail caches and revision-gated uploads. Keep map picking and
campaign/history/auth invalidation independent of this presentation. The character
branch and unrecovered cartography remain untouched. No merge or deployment.

Verified implementation/tests/review: `9edde3d`, pushed to `origin/map-generation`.
Final source-matched browser/reflow/private/GPU/fallback/resource checks and the
10,000-turn gate pass. Full metrics, residual findings and continuation are in the
linked review.

## Orbital day/night follow-up — 30 October 2026

World-fixed fallback sunlight (explicitly illustrative when star positions are
unknown), dark night hemisphere, narrow terminator, bounded relief contrast and
clearer decorative stars. Recorded host-star directions retain priority. No data
or simulation changes. Independent scoped visual acceptance after correcting
black dayside relief grooves; actual Chromium GPU/drag/theme and recorded-astronomy
regressions pass. See `docs/reviews/orbit-lighting.md` for evidence and limitations.

## Explorable system and tinted interface — 30 October 2026

Baseline `5e20f60` → current release candidate: transparent theme-tinted controls,
management shells and labels; a free perspective system view over public frozen
astronomy; drag orbit, Shift-drag pan, wheel/buttons zoom, keyboard Fit system and
context-preserving planet/surface navigation. Unlocated contacts retain unknown
positions and parent-world identity. AU labels are derived only from saved data;
body symbols are enlarged, the grid is a coordinate reference, and no orbit paths
are invented. Untouched initial globe entry favors sunlit geography without
changing light or saved cameras; Recenter still locates home/selection.

Fresh blind/same-critic visual review accepts the scoped result after moon identity,
scene boundary, initial globe and panel-stacking fixes. Functional browser tests
cover camera return, held/stale detail, contact picking, history/private logout,
reduced motion, desktop zoom and unchanged records. Tests retain the mounted canvas.
Full evidence, rejected-candidate findings, source/browser limits and integration
notes: `docs/reviews/navigation-and-tinted-ui.md`.

Performance remains a material limitation: shared two-CPU SwiftShader measured
1.87–1.91s per globe zoom despite transient half-resolution output. The interface
has the requested camera controls; Google Earth animation smoothness is not met
in this environment. Hardware graphics and native Safari/WebKit remain unverified.
No backend/generation/data changes, merge, deployment or character-branch changes.

Verified implementation and tests: `defae73` (baseline `5e20f60`). Continuation:
profile hardware/render readback before claiming smoothness; preserve the scoped
visual findings and camera/data contracts in the linked review.

## Continuous-world work-in-progress backup — 31 October 2026

This checkpoint adds recorded-terrain system previews, selected-body focus,
explicit orbit/surface entry, an optional grid, and opt-in isolated sparse/rich/
extreme review fixtures. Preview work is snapshot/context guarded and bounded;
existing campaign data and production generators are unchanged. Further review
changes add a factual body inspector, geographic entry marker and crowded-symbol
priority. Generated assets, databases and runtime captures are excluded from Git.

Earlier three-system browser journeys passed before the latest review changes.
Current JavaScript syntax and system projection, preview isolation/cache bounds,
and body-return unit checks pass. Final browser acceptance remains incomplete:
`tests/browser_continuous_world.py` most recently failed its Surface-mode title
assertion after descent. Fix mode-label updates, then verify the latest inspector,
entry marker, crowded labels and regressions with the existing critic's CW-01–08
ledger before calling this an accepted interface release candidate. Software-GPU
smoothness, native Safari/WebKit, gas atmospheres and recorded moon surfaces retain
previous limitations. No merge, deployment or data reset was performed.

## Continuous-world corrections — 31 October 2026

Supersedes the WIP acceptance status above. Mode headings now track actual orbit
and surface state, the geographic entry crosshair is a visible precise overlay,
selected-world labels have clearance, and moon status rows are separated. A new
snapshot clears system preview caches. The same independent critic's CW-01–08
ledger, three-system actual-browser evidence and context/reflow regressions are
recorded in `docs/reviews/continuous-world-journey.md`.

System previews reuse authorized saved geography. Separate Select/Focus/Inspect/
Enter orbit/Enter surface actions preserve original camera context. Unknown
positions remain unlocated, selected bodies take draw/pick priority and all
contacts remain available through the Body list. Optional grid starts off.
Preview work is bounded and context-gated. Production generation, existing
campaign records, immutable history and the character branch remain unchanged.

This is a scoped interface release candidate. Software-GPU globe motion remains
slow, terrain detail remains finite, and native Safari/WebKit/hardware graphics
are unverified. No Google Earth or commercial-game parity claim. Integrate through
saved detail references and body-return tickets; keep UI state out of campaign
persistence. No merge/deployment/data reset. Baseline backup: `5004eb2`; delivery
commit is recorded in the review after push.
