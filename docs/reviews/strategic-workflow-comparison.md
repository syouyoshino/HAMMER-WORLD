# Scoped strategic-interface comparison record

This record compares interface qualities and representative tasks, not whole-game parity. Research provenance and explicit evidence limits are in `strategic-interface-baseline.md`. The tiny fictional fixture does not reproduce late-game reference density or art budgets. No numeric average is an acceptance gate.

| Representative task | Examined reference / relevant strength | Baseline gap | Intended implemented response | Candidate evidence and independent verdict |
| --- | --- | --- | --- | --- |
| Enter campaign; understand turn and pending state | Stellaris main-interface documentation: stable campaign/date/resources; Open-IG full starmap: compact persistent status | Cleared desktop hides campaign/turn and report state behind HW | Labelled Menu and persistent campaign/turn/historical/recorded pending indicators | Verified in Chromium; persistent campaign selector, turn and recorded indicators |
| Galaxy → Sector → System → Planet | Stellaris hierarchy/actions; Starsector indexed system-map example: stable object context/filter navigation | Map controls require a separate Cartography window | Map controls and breadcrumbs directly above the permanent map, same canvas and camera | Verified in Chromium; independent scope verdict recorded in strategic-quality-loop.md |
| Select province/settlement → economy → construction → map | Victoria 3 official UX74: context and direct related-panel navigation; Open-IG full info/colony and navigation source | Disconnected windows and local/campaign scope confusion; arrangement overhead | Collapsible contextual inspector, local record scope, related tabs, one Return to map | Verified in Chromium; independent scope verdict recorded in strategic-quality-loop.md |
| Economy/resources and construction/projects | Victoria 3 economy descriptions; Open-IG full financial/information screens: consistent categories and selected-place context | Repeated unknown metadata, raw records and nested frames | Recorded primary values first; explicit local/campaign scope; compact Unknown explanation, retained view state | Verified in Chromium; independent scope verdict recorded in strategic-quality-loop.md |
| Military/fleet/logistics | HOI4 indexed state/map selection; Shadow Empire indexed logistics panel; Open-IG fleet/info source | Independent windows obscure selected place and repeat title chrome | Single primary destination, related navigation, one inspector for records, actual recorded data | Verified in Chromium; independent scope verdict recorded in strategic-quality-loop.md |
| Events/history and historical read-only | Open-IG source/direct information navigation; Stellaris situation-log documentation | Multiple windows, context can be hard to find | Consistent History/Turn report/Log navigation, visible historical state, preserved comparison and safe live return | Verified in Chromium; independent scope verdict recorded in strategic-quality-loop.md |
| Supported decision prepare → preview → commit | Open-IG source distinction of primary/secondary screen and bounded actions; no exact commercial equivalence claimed for JSON handoff | Window arrangement distracts; engineering-oriented handoff inherited | Retained existing supported handoff, clear preview/commit states and explicit read-only restriction | Verified in Chromium; independent scope verdict recorded in strategic-quality-loop.md |
| Characters/context | CK3 official command hierarchy/character-access descriptions | Generic record presentation, no new relationships mechanics available | Reachable Characters destination and compatible screen registration, no invented relationships | Verified in Chromium; independent scope verdict recorded in strategic-quality-loop.md |
| Mouse/touch, small screens and return navigation | CK3 official consistent control vocabulary; Open-IG source direct screen links | Tiny window controls and stacked sheets; hover shortcut can be mistaken for primary access | Labelled commands, fitted single sheet, clear collapse/back/return, optional edge shortcut | Verified in Chromium; independent scope verdict recorded in strategic-quality-loop.md |

User-specific A World Divided comparison remains unavailable until the reference is identified. Local Open-IG original full frames support actual pixel critique; commercial indexed images/descriptions support bounded research only. Remaining renderer limitations are documented separately from shell defects.

## User-refined task gates

The user explicitly requested the following equivalent-task comparisons during implementation. These replace vague whole-interface scoring.

### Selected settlement → main economic problem, against Victoria 3

[Official data-visualization diary #61](https://www.paradoxinteractive.com/games/victoria-3/news/victoria-3-dev-diary-61-data-visualization) distinguishes current stock from trend, magnitude and context; a deficit is not automatically a structural problem. Together with UX74, it supplies the task standard: relevant local condition first, why it matters, and a direct route to the related management action.

Hammer World's public projection supplies settlement stocks, civilians/local population, housing/unrest, facilities/projects and, after resolution, local `latest_outcome.production` / `consumption` plus recorded deaths. Initial turn zero has no resolved production/outcome. Stocks alone cannot identify the main economic problem; no ranked diagnosis, local forecast or sufficiency model is supplied. UI improvements can expose recorded condition and past imbalances honestly; they cannot claim equivalent forward-looking diagnosis without additional authoritative data. No backend simulation or fixture values are changed for this comparison.

### Selected character → relationships, against CK3

The [official CK3 console control diary](https://www.paradoxinteractive.com/games/crusader-kings-iii/news/ck3-console-dev-diary-3-uiux-and-controls) supports contextual character access; [official Friends & Foes material](https://prod-paradox-hub.paradox-interactive.com/games/crusader-kings-iii/add-ons/crusader-kings-iii-friends-and-foes) and the [publisher's update announcements](https://store.steampowered.com/news/posts/?appids=1158310&enddate=1662637090&feed=steam_community_announcements) establish relationship/history comprehension as a distinct task.

Actual `public_state_v2` exposes character `id`, `role`, `assignment`, `experience` only (`app/universe.py`). It has no relationship edges, opinion/reason records, family, friends or rivals. A human-readable role/assignment view and explicit unavailable-relationships state can improve inspection, but the relationship task is blocked by absent authorized data/mechanics. This branch neither modifies nor depends on `feature/character-relationships`. No invented relationship graph, percentages or named personas are added.

### Return to strategic navigation, against Stellaris

The [examined main-interface documentation](https://agentmystia.github.io/StellarisWiki/Main_interface.html) describes consistent management destinations, system/galaxy context and direct selected-object navigation. The scoped standard is one clear return action with the same strategic location, zoom, overlay and selected entity, plus immediately available hierarchy controls. This task can be fully tested in the current fixture; no commercial game is claimed to have been instrumented or played here.

The independent critic reports each task separately as accepted within scope, partial, or blocked, including evidence limits. A successful return-to-map test cannot compensate for absent economic diagnosis or character relationships.
