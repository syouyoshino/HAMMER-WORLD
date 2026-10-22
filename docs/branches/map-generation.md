# Map generation — research and visual direction plan

Date: 22 October 2026 UTC. Branch: `map-generation`, created from `edf243e` on `feature/map-desktop-shell`. The preceding military interface implementation is `2379356`; owned movement projection milestone is `3e97811`. The source branch was clean and its push reported up to date before this branch was created.

## Authorized scope of this milestone

Research the generation/presentation approach, propose three visual directions and generate independent concept images. No chosen direction is implemented yet. No campaign geography, database, history, rules, IDs or authentication are changed. No unavailable cloud cartography/database is claimed recovered. Generated images are fictional design studies, not output from the game's generator and not implementation or performance evidence. Nothing is merged or deployed.

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

Visual selection is pending. The preferred implementation must be chosen from the images actually displayed in the chat; a mixed direction should first be shown as a revised concept. Do not start map implementation merely because a concept image looks finished.

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

## Acceptance gates for future implementation

Presentation: unchanged saved geography/IDs/checksums; same canvas/camera/selection/overlay through management changes; readable labels/counters at desktop, phone and browser zoom; no map input through panels; all destinations remain reachable.

Generation: same version/config/private seed yields exact output; different seeds vary structure; finite and bounded fields/dimensions; coherent connected land where intended; rivers terminate in ocean or explicit lakes without cycles; complete terrain classification; valid stable province membership and references. Do not assert physical realism from attractive images.

Security/history: frozen foreign observations, no hidden marker/seed leakage, campaign/login/logout staleness guards, read-only historical views and exact restore continue to pass. Existing records are never rewritten to match a visual.

Performance: measure generation time, serialized size, map load, redraw and resource/handler stability on named fixture sizes. Use existing Canvas/backend first; evaluate rendering libraries only against a demonstrated need. Run meaningful generation/projection/browser tests and the required 10,000-turn fixture gate at implementation acceptance, not for this documentation/ideation-only milestone.

## Delivery evidence and continuation

Current milestone changes documentation only. Generated concept files are retained outside tracked source, under `/workspace/generated_images/` and ignored `data/map-generation-concepts/`. The chat's displayed image order is the authoritative selection order. No UI code, generator or database has been changed or tested in this planning milestone. Next step is a visual selection, then the presentation-only slice before any new-fixture generation work.
