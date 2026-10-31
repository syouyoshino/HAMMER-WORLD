# Universe fog and outward zoom — 31 October 2026

## Scope and baseline

The user asks whether outward zoom connects surface, planet, solar system and
universe, and requests a Universe view with fog over undiscovered space.
Baseline `7ed3023`: surface minimum already enters orbit; beyond 4.2 planet radii
contained an intended parent-system transition. Actual browser execution found
that transition broken: the parent lookup used a celestial-only resolver that
excludes systems. System distance previously clamped at20.
Universe was absent. Fresh browser captures are in
`data/universe-navigation/baseline/`; actual dropdown navigation also exposed a
new Galactic chart inheriting planet pan/zoom and putting its marker offscreen.

## Architecture and authority

A bounded Sol high review selected a client-only schematic derived from the
existing authorized Galactic map response. No schema, backend, generator or
campaign changes are required. Physical universal positions, discovery footprints
and total extent are absent from these records. Regions are regions, not galaxies.

Only returned `groups[].region` and their returned sectors become contacts.
Hidden records have no placeholders, count or fog holes. Detected contacts retain
the public generic name and unknown physical coordinates. Screen layout encodes
hierarchy, never physical distance. No planet/system chart coordinates are
repurposed as universal positions. Fog is qualitative unknown-space treatment,
explicitly labelled with unknown extent/distances; it is not a measured explored
area or a claim that all undiscovered output has been generated.

Universe uses the same authenticated `/map?level=galactic` request, including
historical snapshot ID, then converts the guarded response locally. Backend map
allowlist remains unchanged. Universe and Galactic have distinct root camera keys.
Campaign/snapshot/login context governs return targets, pending work and caches.
No new credentials or browser token storage.

## Interaction decisions

Outward surface zoom → globe → parent system → Universe. Further outward Universe
input stays there. Sector/Galactic charts remain explicit navigation options.
Universe zoom-in can return to the remembered surveyed system in the same context;
otherwise use the visible contact list. No arbitrary first system is chosen.
A known region opens the existing Galactic chart (not a fictitious region-filtered
API), and a sector opens its Sector chart. The same canvas is retained.

The new schematic renderer draws lightweight fog, hierarchy symbols and labels;
no additional WebGL context, framework or per-draw handler registration. Light and
dark controls remain toggleable. Fresh hierarchy charts fit on first entry rather
than inheriting surface pan. Saved camera contexts remain separate.

## Verification and independent review

Initial candidate was rejected during actual outward navigation: globe distance
reached4.2 but could not enter System. The coordinator corrected the earlier
source-based claim to the user and escalated the bounded parent-lookup defect to
Sol medium. The rejected capture remains in
`data/universe-navigation/rejected-parent-lookup/`. Final evidence follows below.
Root owns actual browser/testing; Luna owns bounded implementation. A failed
bounded implementation will receive localized Sol medium correction under AGENTS.
Final reports will distinguish visual observation from executed workflows.

## Limits and integration

No intergalactic simulation, invented galaxies, measured survey boundaries,
explored percentage, new campaign generation or recovery of unavailable cartography.
No deployment, merge or data reset. Commercial fidelity and Google Earth animation
smoothness are not established. This is desktop scope; mobile is intentionally
excluded. WebKit/native Safari/hardware graphics remain unverified unless actual
coverage is recorded below.

Backend source unchanged: retained applicable10,000-turn fixture stress gate
`data/terrain-finish/stress-v2.json` passes257.97s,10,001 snapshots and exact restore;
no costly simulation repeat for frontend navigation. Keep explicit authorized
coverage data as a future prerequisite for physical fog footprints.

## Candidate findings and corrections

The first outward test found the inherited globe-parent lookup defect above. A
localized Sol medium correction uses the authorized surveyed system node from
current snapshot state, preserving the narrower celestial-body lookup elsewhere.
The next candidate reached Universe but exposed a separate shell integration bug:
only the System strip was moved into the fixed desktop heading. Universe's toolbar
was below the canvas. The correction mounts both strips, shares the existing sharp
translucent styling and measures them as safe-area/resize obstacles. A generic
"Map · Universe" title was corrected in both render paths; map accessibility
identity resets when leaving Universe.

A fresh Sol medium critic first inspected anonymous uncropped dark/light captures
without implementation history or a desired winner. These images were current
Universe states, not equivalent commercial-reference comparisons. The intended
workflow and actual execution observations were supplied only afterward. The same
critic retains this ledger for corrected-candidate reassessment:

| Finding | Severity | Response |
|---|---|---|
| U01 No visible open/return affordance | High | Mount labeled contact list, Open chart and Return to system above canvas |
| U02 Type, knowledge and gold-ring meaning ambiguous | Medium | Explicit type/state labels, distinct detected/surveyed symbols |
| U03 Vertical dotted connector could be a travel route | Medium | Branching containment hierarchy with explicit non-travel caption |
| U04 Nearly uniform field does not communicate unknown-space treatment | Medium | Qualitative layered mist and non-geographic unknown-space explanation |
| U05 Repeated caveats, tiny text, crowded footer | Medium | Larger contact labels, concise separated status and navigation instructions |
| U06 Irrelevant surface settings and weak immediate-task hierarchy | Low–medium | Hide irrelevant settings in Universe; retain clear chart actions |

The critic withdrew the initial suggestion of a geographical fog frontier after
learning that no coverage/extent data exists. No physical survey boundary will be
invented to satisfy a visual critique. U01–06 were accepted at full height after the bounded revision. The same critic
then identified U07 (high): fixed vertical spacing clipped a region, overlapped
the caption and hid a detected sector at1280×720 CSS150%. A localized Sol medium
layout correction keeps full-height composition and uses a compact horizontal
hierarchy below a reserved caption band on short charts. Full label frames and
hit targets now have separate bounds; tests check all three reviewed contacts fit
without clipping or overlap. This finding was preserved, not averaged away.


## Executed verification

Final `data/universe-navigation/final/report.json` and trace pass on frozen source:

- Actual surface wheel → globe → parent system → Universe; an intentional inward
  Universe zoom and the Return button restore the exact departing system view.
- Six wheel events while the Universe response is held create exactly one
  transition request, with the correct return target retained.
- Universe/Galactic root cameras remain separate; fresh charts start fitted.
  Canvas region activation opens Galactic; labeled sector selection opens Sector.
- Only the public response's region/sector IDs appear; detected coordinates remain
  unknown. No `level=universe` backend request is sent. Historical contacts match
  the historical authorized response; a live return target cannot cross snapshots.
- Held old responses cannot repaint a switched campaign or logged-out private
  session. Login tokens are absent from local/session storage.
- Actual dark/light redraws,1280×720 CSS150% contact/control bounds, retained canvas
  and stable canvas listener count pass. Campaign responses are unchanged and no
  JavaScript errors occur in exercised journeys.

The test harness initially attempted to press Return to map after historical
inspection, but inspection had already returned to the map. The hidden-button
wait was a harness error, corrected to press only when visible; no application
change was made for it. Final execution reached and passed history/private checks.

`data/universe-navigation/context/report.json` separately passes existing
star/moon/planet mouse/touch/keyboard journeys, exact camera/selection/overlay/style
return, historical read-only/unknown behavior, reduced motion, private logout and
unchanged records. That run uses the same final app/shell source; only the isolated
Universe compact layout changed subsequently. Node projection, surveyed-preview
isolation/cache, body-return and Universe derivation/immutable-layout checks pass.
New compact-frame unit checks cover both themes at800×180 safe area, all three
contacts below captions and mutually non-overlapping full label frames.

## Performance and browser bounds

Chromium154.0.8037.57 on shared Linux, two-CPU quota, software ANGLE SwiftShader.
At1440×1000,44 Universe draw calls measured median0.30ms, maximum2.60ms using
`performance.now()` around the canvas draw call. This is command-submission/draw
call duration on one small fixture during a browser workflow, not full presentation
latency, frame rate or production capacity. No extra WebGL context is created.
Existing software globe motion remains slow; no Google Earth smoothness claim.
Tests used reduced motion; screenshots cannot establish animated continuity.

Desktop coverage here:1440×1000 and1280×720 at CSS150%. Actual native browser zoom,
all other viewport/zoom combinations, WebKit/native Safari and hardware graphics
remain unverified. Existing renderer evidence from earlier reviews is retained,
not represented as a fresh cross-browser run. Many-region/dense Universe layouts
are not visually validated; the contact list remains the reliable navigation path.
Legacy campaigns without recorded hierarchy do not gain fabricated Universe data.

Primary suite source hashes (SHA-256; see final control-only supplement below):

| File | SHA-256 |
|---|---|
| `public/app.js` | `a6eed6bef85a6c81142492c06cddc8cde63d9b1f26f58e8caa36b8ec9ebab80c` |
| `public/universe-view.js` | `5203ff1d307f8e8da43d28cad8af1a80fad54e84a6a62deecd4219d0236d5984` |
| `public/index.html` | `c1c299bdd5296b90537ef961ad23ea8ab16e3d9c63304dcac341191ae6f27df8` |
| `public/style.css` | `60f5bc845dbd593be2731fad32cccbc4d5b434e33b51d1dc56099de8ada2aaa5` |
| `public/desktop-shell.js` | `02190928ec72d2a275f81ecff58571ee7da546efe5dee4a8d34e1bad6bf59ad2` |
| `public/desktop-shell.css` | `530ac6ccbeeabe1dd5c9f7bb9ffac551fccb580dc6ff75d23c4b14eaec6ebbe7` |

## Final independent verdict and continuation

The same critic accepts the scoped final dark/light/short-desktop/historical
captures: no unresolved major visual defect. U01/02/03/04/06/07 are resolved in
reviewed states; U05 is substantially resolved, with small footer text remaining
minor. Optional detected/selected legend entries could supplement the explicit
adjacent labels. Historical turn0/read-only status and disabled live return are
clear. No additional redesign was requested after the compact-layout correction.

The critic independently inspected fresh images and read `final/report.json`.
Interaction results are coordinator-executed evidence, not browser actions the
critic repeated. It does not certify screen-reader access, measured contrast,
animation smoothness, all sizes, dense universes or browser parity. This is a
scoped interface release candidate, not operational/deployment certification.

Continuation: add authoritative physical coverage/galaxy positions before claiming
spatial exploration fog; validate substantially denser contact layouts using new
isolated fixtures; profile hardware globe rendering before promising smoothness.
Keep these tasks separate from existing campaign history and unrecovered terrain.


Final diff review found two control-state refinements: preserve the unavailable-map
overlay disabled state, and disable lower-level map choices in Universe rather
than silently ignoring a choice that lacks a known destination. Descend through
the explicit known-contact or Return to system actions; outside Universe those
map choices are restored. No arbitrary system or planet is selected at this root.
`data/universe-navigation/controls-final.json` passes actual pre-game/Planet/
Universe/Galactic→Planet control checks with no page errors. Option disabled state
is checked through its DOM property; the installed Playwright convenience method
did not reflect native option disabled attributes. Core navigation/renderer source
is unchanged by these two UI refinements, so earlier executed flow and visual
acceptance remain applicable. The isolated control-state supplement uses final
`public/app.js` SHA-256 `09ccecad045f769de20a6b9b16a6e61ddcd0913e5bb4e552644dc0e90218aec2`; all other frontend hashes above
are unchanged. Neither supplemental check is represented as a fresh full-suite run.

Verified implementation, tests and review record: `8269a63`, pushed to
`origin/map-generation` (baseline `7ed3023`). Captures, traces and runtime fixtures
remain local ignored artifacts; durable findings/metrics/source hashes are above.
No private records, tokens, databases or generated assets are committed.
