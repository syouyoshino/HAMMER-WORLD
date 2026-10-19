# Icon and information audit — 19 October 2026

Scope: the user requested a broad critique of the military command station, especially icon colour and section meaning. This is an interface release candidate; it does not certify deployment, operational security, backup/recovery or parity with entire commercial games.

## Evidence and design decision

Fresh baseline: ignored `data/icon-audit-baseline/`, full1440×960 and390×844 frames across all19 management/compatibility destinations, selected settlement Economy/Construction, campaign access and Menu. Actual browser captures and computed styles established that baseline menu icons inherited graphite, many destinations shared a document glyph, and Construction clipped in the desktop menu. No campaign data was recovered or substituted. The temporary generated map remains visibly disclosed and separate from recorded geography.

Use Apple's current official [HIG colour palette](https://developer.apple.com/design/human-interface-guidelines/color), already examined for the preceding release, with its increased-contrast samples for small strokes. Hammer World's category meanings are product decisions, not meanings prescribed by Apple:

| Family | Destinations | Role |
|---|---|---|
| Mint | Economy, Industry, Budget, Trade | Resources and exchange |
| Orange | Construction, Logistics, Colonies | Development and supply |
| Indigo | Military, Fleet | Forces |
| Teal | Research, Intelligence, Exploration | Knowledge and discovery |
| Blue | Politics, diplomacy, factions, characters, records, campaign and navigation | Administration and context |

Every destination retains a text label and distinct fixed SVG symbol. Active icons become white on blue. Category colour is separate from quantitative meaning: strength/crew remain neutral; readiness uses blue; errors retain red and explicit text. Foreign ownership does not imply hostility. No decorative telemetry or fabricated graphs were added.

## Independent critique and correction record

A fresh GPT-6.1 Sol medium critic inspected all30 baseline captures before implementation discussion/source, then exercised a read-only Chromium candidate. Luna was the sole implementation builder. The same critic follows corrections; no replacement critic or numerical acceptance score.

| Finding | Severity | Response |
|---|---|---|
| Shared generic glyphs; no category cue | P2 | Distinct labeled symbols and restrained colour families in Menu and related tabs |
| Desktop Construction clipping; campaign label wrapping | P2 | Wider desktop menu and full-width campaign entry |
| Phone report starts below tall map chrome; scope truncation | P2 | Workspace overlays beneath command bar without resizing/repositioning map chrome or canvas; scope wraps |
| Nested production/spending JSON obscures actual values | P2 | Structured settlement production and spending with public labels and units |
| Player/foreign identity too weak; ground record uses fleet symbol | P2 | Title-adjacent ownership; record-type symbols; neutral strength/crew |
| Related reports/empty records lack domain context | P2 | Explicit scope, relevant ordering and specific recorded-empty states |
| Small secondary metadata and exact chart endpoint annotation | P3 | Retained bounded polish; existing axis and recorded series remain readable |

The critic explicitly retracted an initial energy-axis reading error after reopening the original image: ticks were correctly8,000/6,000/4,000/2,000/0. No axis defect/fix is claimed. A budget reconciliation concern was also withdrawn: recorded settlement upkeep1 explains400 opening+11 revenue−10 action spending−1 upkeep=400 closing. The UI exposes the existing record; no balancing adjustment or calculation rule was invented.

Actual candidate browser evidence already confirms390×844 Menu→Military→Fleet→Map, keyboard Enter/Tab/Escape, focus restoration, panel scrolling and no horizontal document overflow. Read-only review issued no non-GET requests. Final candidate acceptance and regression evidence follow below.

## Final assessment and checks

The same critic reviewed the fresh final full-frame set `data/icon-information-final/` at original resolution and accepted all confirmed P2 corrections: icon identity, phone workspace, structured production/spending, explicit ownership, type-correct force symbols, report context and empty states. It found no remaining P1/P2 in the reviewed fixture states. It retained P3 Campaign/access composition, small metadata and exact stock endpoint/delta annotations. Its additional P3 bare Unmet Upkeep heading was corrected with an explicit “No unmet upkeep entries are recorded” message for an actual empty object; root verified that in a fresh browser capture `budget-empty-corrected.png`. No numeric zero was substituted.

Final content was independently screenshot-reviewed; independent actual interaction coverage is the preceding candidate navigation described above. Root's full final Chromium regression separately verifies complete exercised workflows. Exact icon strokes were checked against the existing official Apple increased-contrast tokens: blue#1E6EF4, mint#008575, orange#C55300, indigo#564ADE, teal#008198. Computed surfaces remain63% opacity/10px local blur; text stays opaque. No new palette claims depend on screenshot colour estimation.

`tests/browser_strategic.py` passed with isolated PostgreSQL schemas, actual player/GM authorization and teardown. It exercises all16 primary destinations plus History/Orders, Galaxy→Sector→System→Planet pointer navigation, settlement→Economy→Construction→Map, real preview/commit/restore and immutable historical views, stale campaign/login/logout work, map input blocking, stable canvas/camera/overlay/selection, emulated touch and actual100/125/150/200% Chromium browser zoom. Added checks cover menu label bounds/colour cues/distinct symbols, literal hostile-looking title text alongside the new badge, ground versus transport symbols, explicit foreign ownership, and API-matched production/upkeep figures. Existing stock retry/recovery, invalid work, readiness, chart axes and request de-duplication checks pass. No uncaught page errors. An old test expected generic empty copy; its matcher was updated for the new domain-specific wording before the final passing run. Syntax/diff checks pass. No backend/rules/schema changes; user-directed UI-only stress-test exception applies.

Performance: managed Debian13 Linux6.18.55,3 logical CPUs, Chromium154.0.8037.57, Python3.12.14, PostgreSQL17 isolated demo-v2. First local Economy/Construction action-to-ready26.90/48.50ms;24 cached transitions median5.63ms/p958.93ms. DOM2545→2545; post-GC documents1/nodes4971/listeners178 unchanged; API resource entries47→47. Eight cold Economy opens share one held history request. These programmatic fixture timings exclude startup, full paint/chart completion, generated-artwork transfer and GPU blur cost; they do not establish production performance or long-session leak freedom. Runtime evidence: `data/icon-information-regression/metrics.json`. Fresh captures were run separately against the isolated loopback preview, not a production dataset.

Browser coverage: Chromium desktop and emulated touch, including actual browser zoom. WebKit, native macOS Safari and physical mobile devices remain unverified. No commercial-reference parity claim follows from this review. Missing diagnosis/relationships, unrecovered cartography/database and large-data behaviour remain explicit limitations.

## Comparison limits

This follow-up compares baseline and revised equivalent Hammer World states. The examined external reference is Apple's official palette; previous instrument-photo and commercial task-reference examinations remain recorded in the linked branch documentation. This audit does not claim a new anonymous visual comparison with Victoria3, CK3 or Stellaris. Missing ranked settlement diagnosis and character relationships remain data/mechanics limits; do not invent them. The generated map is presentation artwork, not evidence of geographic quality.

## Integration boundaries

Keep the mounted map, persistent safe bounds and canvas input independent of transient workspace overlays. UI preferences stay separate from campaign records; no storage/auth/rules/schema/cartography changes. The character-relationships branch remains untouched and can register a recorded relationship screen through the existing shell registry. Recovered cartography can integrate without depending on icon metadata.
