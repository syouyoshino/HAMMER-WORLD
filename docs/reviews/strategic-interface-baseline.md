# Strategic interface baseline and reference research

Baseline: `65f8321` on `feature/map-desktop-shell`. `c488aa1` added the mounted-map desktop shell, retained report containers, window geometry and lifecycle, edge launcher, epoch checks and browser regression. `65f8321` added continuation documentation. Neither commit recovered the unavailable cartography workspace or database.

Fresh baseline: `tests/browser_desktop.py` completed successfully against a disposable PostgreSQL schema with real private API workflows and Chromium. The five current screenshots were copied to ignored `data/strategic-baseline/` and inspected. This was a fresh run, not reuse of prior-turn evidence.

## Observed usability gaps

1. Clean map provides only HW: campaign, turn, historical/live mode and pending decisions cannot be understood without opening the chooser or reports.
2. Economy, History, Cartography and inspector are independent floating windows. They overlap, repeat title bars and require arrangement/closing to restore map visibility.
3. The province inspector exposes terrain/population but lacks a direct economy/construction path. Campaign-wide resources and local conditions are not connected by navigation.
4. Report tables expose raw record structures and repeated Unknown canonical fields. Generic boxed icons provide weak recognition; labels are essential.
5. Mobile launcher labels now work, but full-size overlapping sheets still expose stacked title bars and tiny desktop control conventions.

These observations support replacing the visible desktop metaphor while keeping working map, data boundaries and retained screen contents. Terrain tiles, sparse galactic demo and geographic selection outlines are inherited rendering/content limitations; they are not addressed by a UI redesign.

## Research method and limits

Official developer descriptions, available image-search results, and Open-IG source/documentation were examined. Commercial game image descriptions are secondary evidence; screenshots available only as indexed descriptions are not treated as independently inspected pixels or playable workflows. The network proxy rejected direct downloads from images.ctfassets.net. No alternate route was used to bypass that restriction. Open-IG screenshots were obtained from its public source repository and opened locally. They are research-only ignored artifacts; no assets or game code were copied into Hammer World.

The user's specific A World Divided visual reference was not supplied in this chat. A clarification was requested; Gary Grigsby's title found by search is not assumed to be the same reference.

## Sources actually examined

| Source | Evidence examined | Relevant strength / restriction |
| --- | --- | --- |
| [Victoria 3 UX diary #74](https://www.paradoxinteractive.com/games/victoria-3/news/dev-diary-74-ux-improvements) | Official text, especially Economy, map interaction, population and outliner sections; linked construction/trade image metadata | Direct movement between related panels, local labor/infrastructure context, higher-priority information first. Actual commercial pixels were not locally inspectable. |
| [Hearts of Iron IV state-selection example](https://forum.paradoxplaza.com/forum/threads/quick-questions-quick-answers-hoi4.942351/page-182) | Indexed screenshot/description: selected Lazio, ownership panel, map-mode and flag tooltip | Selection remains the reference point; overlays and military information share the map. Indexed evidence only, no playable interaction assessment. |
| [Stellaris main-interface documentation](https://agentmystia.github.io/StellarisWiki/Main_interface.html) | Static wiki mirror: system/galaxy actions, top-bar state, management destinations, tabbed outliner and selected-item navigation; indexed planet summary | Persistent orientation and consistent entity navigation. Mirror/version limits, not a live-game audit. |
| [Crusader Kings III Console diary #3](https://www.paradoxinteractive.com/games/crusader-kings-iii/news/ck3-console-dev-diary-3-uiux-and-controls) | Official control hierarchy, command bar, submenu tabs and contextual access description; character screenshot metadata | Consistent navigation vocabulary and explicit context rather than imitating a desktop pointer. Console-specific guidance; not PC equivalence. |
| [Shadow Empire logistics guide](https://gamepretty.com/shadow-empire-logistics-guide-all-you-should-know/) | Indexed logistics-panel screenshot description (selected hex, logistics signs and event log); official manual request timed out | Strategic density must explain a selected place and actual logistics. Not an endorsement of every dense control. No local pixel/live interaction verification. |
| [Starsector system example](https://www.himajin-block30.com/entry/2024/07/02/200420) | Indexed Corvus-system screenshot/description: object names, map filter tabs, common command navigation | Readable space hierarchy and stable contextual navigation. Official UI article fetch failed; this is secondary indexed evidence. |
| [Open-IG repository](https://github.com/akarnokd/open-ig) | Source commit `9891378f2f00ba83d51ad92773f8cb2dd9744b12`, README UI enhancements, `InfoScreen.java` navigation callbacks, `PlanetScreen.java`, full `doc/open-ig-0.88-starmap.png`, `open-ig-0.88-info-01.png`, `open-ig-0.88-info-07.png`, `open-ig-0.86-colony-01.png`; local pixels inspected | Existing open-source primary/secondary screen distinction, direct colony/starmap/research/production links and bounded contextual panels. Used as architectural/reference study, no copied assets/code/dependency. Older screenshots and different content/art budget limit comparison. |
| User's A World Divided | Specific reference not identified; clarification requested | No comparison or parity claim until identified. Search results for Gary Grigsby's game are not silently substituted. |

Open-IG's small feature snippets (`feat-colinfo-1`, `feat-planets-1`, `feat-prod-1`) were also opened as component references; these repository images are already excerpts and are not used as full-interface comparisons. Full frames are retained for critique without cropping defects.

## Comparison protocol

Use original, unmodified full frames with neutral filenames; origins and expected winner are withheld from the initial independent critic. Visible game identities may still be recognizable, so this is not guaranteed statistical blinding. Preserve aspect ratios. Compare selected-place navigation and campaign-information grouping only where the data load is reasonably comparable; busy colony artwork and many-system maps do not establish equivalence to a tiny fictional fixture. Document uncertainty rather than awarding an average score. Screenshot assessment is separate from actual scripted workflow evidence.

## Representative journey evidence

After the fresh full baseline run, the committed `65f8321` source was archived to a temporary separate directory for equivalent-view capture. A private loopback server and a disposable schema ran the original UI at 1280×900. Actual pointer/menu actions selected a province, opened Economy and opened Construction. The three full frames are `data/strategic-baseline/journey-{inspector,economy,construction}-1280.png`; the temporary schema/server were removed. No source branch or campaign records were reset.

The first new vertical slice passed login/selection, fixed 1280×900 map frame, planet/province selection, recorded local holdings, labelled campaign/local economy, construction and Return to map. Anonymous copies of these candidate and equivalent baseline frames plus two original full reference frames were supplied to one fresh Sol medium critic. Origins/desired winner and prior verdicts were withheld before its initial assessment. The critic receives interaction evidence separately; screenshots alone do not prove behavior.
