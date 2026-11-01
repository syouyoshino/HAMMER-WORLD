# Universe research and redesign recommendation

1 November 2026. Research and fresh workflow audit of `map-generation` at
`384f968`; no implementation changes in this review. The earlier scoped acceptance
established working navigation and improved ambience, not a finished strategic
atlas. The user's further criticism is justified.

## What was examined

| Reference | Material actually examined | Relevant lesson; limits |
| --- | --- | --- |
| [Stellaris developer patch notes](https://store.steampowered.com/news/posts/?appids=281990&enddate=1527781438&feed=steam_community_announcements) | May 2018 developer notes describing connected constellations, chokepoints and exploration-revealed hyperlanes. Text, not a current live-game audit. | Connectivity makes space strategically intelligible. Adapt only existing public links; do not import its travel rules. |
| [Endless Space 2 official manual](https://cdn.cloudflare.steamstatic.com/steam/apps/392110/manuals/ES2_PC_OM_JAN_2018_210x297_UK_HR.PDF) | January 2018 manual text, printed pages 10–12: nodes/constellations, camera, zoom-sensitive Scan View, unexplored versus discovered-but-unobserved space and route preview. | Zoom should change information meaning, and knowledge states need distinct treatment. PDF screenshot calls exposed only text placeholders; local PDF retrieval was blocked, so no pixel-level visual verdict. |
| [Sins II media guide](https://www.stardock.com/sinsofasolarempire/sinsofasolarempire2/press/sins-documents/sinsii_mediaguide_aug2024.pdf) and [official Getting Started guide](https://stardock.atlassian.net/wiki/spaces/SSEFW/pages/1718714371/Getting%2BStarted%2BGuide) | August 2024 documentation: tactical-to-empire zoom, phase links, exploration and pinned Empire Tree access. Text, not executed gameplay. | Preserve identity/context across scales; allow compact access to important known entities. No reason to add moving planets or simulation rules solely for animation. |
| [Endless Sky project site](https://endless-sky.github.io/), [player manual](https://github.com/endless-sky/endless-sky/wiki/PlayersManual), [map data contract](https://github.com/endless-sky/endless-sky/wiki/MapData) | Actual official `map.png` topology illustration downloaded from the project's website source and visually inspected. Manual navigation/commodity-map text and data specification read. | Restrained points and links communicate clusters and bottlenecks; selection can answer a task-specific question. Its topology illustration has far more systems than this fixture and is not an equivalent information-load UI comparison. No assets/code copied into the app. |
| [Battlefleet Gothic Armada II campaign UI artist portfolio](https://xarden.artstation.com/projects/nQ5N16?album_id=1916561) | Author's text identifies campaign screens/mockups and galaxy/campaign map concepts, 2018–2019. Image retrieval unavailable. | Relevant Warhammer-specific follow-up reference, but no visual comparison or interaction quality claim from unavailable images. |

Commercial games were not launched. Research supports design patterns, not parity
or a screenshot ranking. The Product Design context preflight found no saved user
context; the current repository and conversation supplied the brief. Its
critical-overrides resource could not be read. Actual screenshots came from the
running cloud Chromium fixture; the injected Browser control binding was not
available. Reference PDF/portfolio binary downloads were explicitly denied by
network policy, not treated as inspected visuals.

## Fresh three-step audit

Chromium 154.0.8037.57, 1440×1000, dark theme, reduced motion, fictional `nav-demo`.
Current-run screenshots, DOM snapshots and observations are under
`data/universe-research/audit/`; generated evidence is excluded from Git.

1. **Orient — workable, spatial semantics weak.**
   `01-orient.png`: Cinder/Hearth/Kestrel Reach origin text is readable. Region
   and sectors appear as three nearby points; containment depends on tiny
   subtitles. The unlocated sector receives a precise-looking position. Decorative
   galaxy detail is much richer than the strategic structure.
2. **Select Hearth — good action feedback, shallow information.**
   `02-select-destination.png`: native selector focuses the destination and enables
   the clearly labelled Open Hearth action. The new summary repeats name/type/
   parent, without answering a strategic question about the destination. Selection
   brackets and a blue primary action are worth retaining.
3. **Open sector — works, continuity needs improvement.**
   `03-open-sector.png`: native Open enters Hearth, showing Cinder and a separate
   unlocated-system tray. This useful tray should be reused in Universe. The new
   chart loses the richer atlas composition. Planet-specific disabled hydro/feature
   controls and terrain/province instructions are irrelevant to a sector chart.
   The breadcrumb omits the region level: The Reach is the galaxy, Kestrel Reach
   the region; they are not two names for the same entity.

No page errors occurred in this exercised journey. This is a small sparse fixture;
few records are not themselves a defect. These captures do not establish keyboard,
screen-reader, color-contrast compliance, native Safari, production density or
unexercised interactions. Small status text and low-contrast explanatory labels
are visible operability risks worth addressing without a separate certification
project.

![Step 1: orient in the current Universe chart](/workspace/HAMMER-WORLD/data/universe-research/audit/01-orient.png)

![Step 2: select the Hearth destination](/workspace/HAMMER-WORLD/data/universe-research/audit/02-select-destination.png)

![Step 3: enter the Hearth sector chart](/workspace/HAMMER-WORLD/data/universe-research/audit/03-open-sector.png)

## Independent findings

A fresh Sol 6.1 medium critic inspected all three captures without previous
verdicts or implementation history. It rated precise placement of an unlocated
contact high priority, and map-origin distinction, parent-child grouping,
cross-level continuity and explanatory text size medium priority. It found the
selection/Open feedback clear and warned against treating sparse fixture density
as a defect.

Two factual qualifications are retained: origin means viewing/navigation context,
not the physical position of a player or fleet; any badge should say Viewing
Cinder or Return to Cinder. The breadcrumb problem is an omitted hierarchy level,
not inconsistent naming of the same entity. No new candidate was implemented or
accepted in this research turn.

## Recommended direction

Use a restrained **Imperial galactic command chart**: coherent hierarchy, known
connections, intelligence status and purposeful selection over subdued space.
Retain sharp corners, compact readable typography, tinted transparency and the
light/dark toggle. Avoid adding gothic decoration, dashboard cards or animation
that competes with the chart.

| Priority | Change | Implementation/data boundary |
| --- | --- | --- |
| P1 | Make the highest view a clear Galaxy / Known Space overview. Resolve the role of the extra Universe and Galactic destinations. | Presentation should simplify the existing hierarchy without deleting reachable data. Broader Universe navigation is useful only with actual broader scope. |
| P1 | Move unlocated contacts into an explicit tray with known parent and knowledge state. | No fabricated positions, directions, sensor circles or discovery boundaries. Existing sector tray provides a reusable pattern. |
| P1 | Make containment and existing connections legible. | Public state already includes visibility-filtered `links`. These join systems, not regions: do not invent region-to-sector travel routes. Use explicitly schematic grouping for containment, public system links for topology, and a truthful unlocated endpoint when coordinates are missing. |
| P1 | Give Galaxy, Sector and System a consistent navigation/selection/return vocabulary and compatible visual treatment. | Keep camera context, selected entity and per-level return behavior. Remove irrelevant planet controls at higher levels. Use the correct full breadcrumb and a Viewing Cinder badge, not a physical player-location claim. |
| P2 | Make zoom reveal different levels of detail: region groups, sector contents, known systems, then actual system bodies. | Semantic zoom can work on a schematic topology; do not pretend parent-local chart coordinates are a common physical coordinate frame. Numeric interstellar distances remain unknown. |
| P2 | Add a compact tinted inspector showing relevant recorded facts and actions. | Show type, parent, knowledge, applicable known contents/owned assets, selected-turn observation and reachable supported actions. Explicit unknowns; do not infer complete totals from partial intelligence. Open chart is navigation, not a fleet-movement command. |
| P2 | Offer a few task-based overlays: navigation, intelligence and military. | Derive only from authorized selected-turn links, contacts and forces. Military icons attach to their recorded coarse location; no invented trajectories or ETA. Political territory needs actual claims/bounds, not decorative Voronoi ownership. |
| P2 | Clearly distinguish uncharted, detected/unlocated, surveyed, and dated observations where recorded. | Existing data does not establish a physical exploration footprint; a real fog boundary requires saved coverage. Known-state styling can improve immediately without fabricating that coverage. |
| P3 | Refine type, glyphs, color and movement. | Increase important text selectively, give region/sector/system glyphs distinct shapes, keep origin/destination unambiguous when coincident, reduce repeated footer/header text. Camera parallax and selection motion should aid orientation; keep strategic targets stable and respect reduced motion. |

Recommended next vertical slice: **overview → select a known sector → inspect its
known systems/connections → enter a system → return with exact context**. First
resolve unlocated placement and cross-level consistency. Then test richer,
explicitly new demo records with branches, multiple sectors and unknown contacts;
never alter an existing campaign to make a screenshot appear busy. Only after
these workflows read clearly should further scenery/motion be considered.

No application code, campaign data, schema or generator was changed by this audit.
Remaining implementation needs a bounded review of coordinate and visibility
contracts before extending the existing renderer.
