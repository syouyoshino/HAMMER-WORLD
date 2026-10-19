# Instrument interface design QA

final result: passed

## Source and implementation

Source visual truth: the four user-supplied local attachments `1-Photo-1.jpg` (1179×788), `2-Photo-2.jpg` (1179×784), `3-Photo-3.jpg` (1179×813), `4-Photo-4.jpg` (1179×768), under `/tmp/codex-remote-attachments/01a14c1d-6b47-70cf-9a77-6141184380af/AB1E1F68-BC97-42A6-A0EE-769DE30BDC0F/`. All four were opened and inspected before implementation. They depict portions of an avionics interface, photographed at an angle with blur. They establish a design language, not equivalent strategy-game content or a 1:1 viewport layout.

Baseline: fresh browser run at `b6836be`, copied to ignored `data/instrument-baseline/`, 1280×900 / 656×518 / 390×844. Baseline and source were opened in the same comparison input. Heavy bevels, navy title bars, nested frames and equal-weight record rows are substantive mismatches.

Final implementation screenshots: `data/instrument-final/` (map, inspector, Economy, Construction, all management destinations, phone menu/inspector/workspace), plus `data/instrument-candidate/` (validated Orders, four hierarchy levels and full browser-zoom captures). Capture sizes1440×960 and390×844 CSS pixels at device scale factor1. Reference aspect ratios will be preserved; no skew correction, cropping of defects, density-equivalence or pixel-perfect match will be claimed.

## Required fidelity surfaces

- Fonts/typography: replace fallback/pixel display type with a bundled readable technical monospace; assess hierarchy and wrapping in actual captures.
- Spacing/layout: replace nested frames with alignment and space, retain operable controls and map context, inspect desktop/phone composition.
- Colours/tokens: off-white/graphite, fine dividers, solid selected states, readable essential contrast. Photographic blur/faintness is intentionally not reproduced.
- Image/asset fidelity: no reference illustrations or photos belong inside the product. The live functional map remains real canvas rendering. Controls and measurement labels are editable UI rather than raster imitations. No fictional gauges or copied logos.
- Copy/content: retain recorded values, clear data scope, historical restrictions and unavailable states; remove technical/provenance repetition from primary reading paths without hiding needed context.

## Comparison history

The initial baseline comparison blocked implementation acceptance. Subsequent capture/review iterations and their corrections are recorded below.

## Implementation checklist

1. Capture and compare the local settlement journey at normal desktop and phone sizes.
2. Correct material style/readability defects before extending patterns to the remaining destinations.
3. Review fresh extended screens independently and resolve P0/P1/P2 findings.
4. Complete actual browser regression and record evidence/limits separately from visual critique.

## Candidate 1 observations

Actual captures: `data/instrument-candidate-1/{map,inspector,economy,construction,military,characters,history,orders}.png`,1440×960 at1x. Source and these full frames were opened before judgement. A normal pointer click on Menu timed out: canvas intercepted the event. This is a P0 regression, not a screenshot-only concern; the command bar is obscured by map stacking. Localized Sol medium correction assigned.

The new palette and real monospace remove the old chrome, and primary values/secondary identifier disclosures improve the inspector. Economy still repeats workspace/body/context headings and places recent recorded condition below the first viewport. This needs hierarchy correction before acceptance, not extra ornament. At that milestone the extended screen and phone review was still pending; later sections record its completion.

The independent critic's first report rejects the complete presentation candidate. In addition to the commandbar regression, priorities are readable Military record summaries, a decision-state hierarchy in Orders, removal of repeated headings, readable core typography, purposeful single-snapshot History, contextual map labels/selection and plain domain copy. Fresh 1b phone captures show arrow-only campaign choice and map-control overlap. These findings remain blocking until revised captures and real interactions resolve them. See `docs/reviews/instrument-design.md` for the preserved finding list.

## Candidates 2 and 3

Fresh full desktop/phone captures were compared with the same originals. Candidate2 corrected the initial major presentation findings: visible campaign/turn/Menu, land-following selection, distinct main/hovered terrain wording, human-readable report summaries, local condition before stocks, Orders state/progressive disclosure, and explicit single-turn History. Two P2s remained: phone menu text clipping/joining, and unexplained empty collections.

Candidate3 fixed both. The same critic independently exercised normal desktop Menu → Military → Map, initial campaign selection, 15 Tab and15 Shift+Tab presses confined to the access dialog, Escape close, and a scrolled phone menu → Orders path. No writes were performed and no page errors occurred. Actual full private Chromium regression also passed, including turn/history/auth races and browser zoom.

A newly captured validated Orders state exposed a further P2: nested production/consumption JSON wrapped into narrow columns. Localized Sol medium correction keeps scalar balances, shows concise array counts and puts exact per-settlement resource breakdowns in readable disclosure sections. A narrow private fixture verified actual backend values, retained validation when source collapsed, turn remaining0 and no page errors. Fresh summary/breakdown captures are `data/instrument-candidate/orders-validated-{readable,production}.png`.

The apparent 200% clipping was diagnosed as a Playwright screenshot viewport-clip artifact, not inferred away. Actual Chrome Settings zoom yields CSS640×436/DPR2/visualViewport.scale1 in a fixed1280×960 browser window. Direct CDP `Page.captureScreenshot` without clip captures the complete1280×873 physical viewport; all normal click and DOM-bounds checks pass. The reproducible test now uses this full-viewport capture method.

The same critic subsequently accepted the corrected Orders, map-label and full zoom evidence. Broader hierarchy testing then extended the gate as described below.


## Final hierarchy gate and disposition

Fresh four-level captures exposed markers beneath fixed headers despite passing selector navigation. A bounded Sol high architectural diagnosis led to a hierarchy-only safe drawing rectangle, clipping and hit-test correction. The canvas remains full-frame, planetary projection is unchanged and overlays do not change hierarchy bounds. An rAF-scheduled single ResizeObserver observes persistent map chrome.

The final full private Chromium run passes direct painted-marker Hearth → Cinder → Reach descent, breadcrumb ascent/repeat descent, nondefault hierarchy pan/zoom/image retention through management, planetary pan/zoom/overlay/selection retention, actual phone taps and actual100/125/150/200% browser zoom. The independent critic separately performed desktop clicks,390×844 touchscreen taps and actual200% browser-zoom direct descent, reviewing fresh full captures. It reports no remaining evidenced P0/P1/P2, including the extended hierarchy path. Independent read-only captures: `data/instrument-independent/{desktop-planet,phone-planet,zoom200-planet}.png`.

Final fidelity assessment:

- **Typography:** bundled Noto Sans Mono regular/bold, clear20px local readouts, readable primary controls/record facts and secondary identifiers. Photographic blur/faintness is intentionally excluded. Small tertiary captions remain a P3.
- **Spacing/layout:** open alignment-led groups, fine rules, sparse inverse selected controls and one retained workspace replace bevels and repeated navy frames. Desktop, phone and actual browser zoom keep navigation reachable. Subtle scrolling cues and generous record spacing remain P3 refinements.
- **Colour/tokens:** graphite `#272c2f`, paper `#f8f8f4`, map field `#f1f2ee`; selected states are dark with light text. No glass, gradients-as-ornament, rounded dashboard cards or shadows. Source palette is inferred from angled photographs, not claimed as exact sampled colour fidelity.
- **Assets/rendering:** real map rendering and actual recorded data remain functional. No reference photos, logos, proprietary assets or invented gauges/telemetry are embedded. Font attribution/OFL terms are included. Pixel geography and sparse fixture worlds remain inherited renderer/content limitations.
- **Copy/content:** population/civilians differ explicitly; known holdings and saved location names are primary, identifiers/proposal transport are secondary. Economic diagnosis/forecast and character relationships remain explicitly unavailable. The design does not imply commercial-game or missing-mechanics parity.

Full-view and detail evidence: source photos1–4 were opened alongside rendered full frames; inspector/local readouts, Military summaries, phone menu/empty states and the expanded Orders production breakdown received focused readable inspection. Captures are original full frames; no defects were cropped out. Source and app differ in content, perspective and viewport, so this is a style-family adaptation review rather than a1:1 layout claim. Primary workflow/console evidence is separate from screenshots.

The final implementation checklist is complete: material findings corrected; fresh evidence reviewed; actual workflows pass; limits documented. Remaining follow-up polish is P3 only. Final acceptance is an interface release candidate, not a deployment, security audit or production-scale certification.


The hierarchy extension is now independently accepted as well: actual desktop clicks, phone taps and200% browser-zoom direct Hearth → Cinder → Reach descent passed, with all known markers below persistent chrome. No new P0/P1/P2 remained. Final full-suite metrics and boundaries are recorded in `docs/reviews/instrument-verification.md`. Per-context in-flight de-duplication/stale-completion/retry probes passed separately; cached timing starts only after the new context is warmed.


## Command-station polish acceptance (`1ce20be`)

Passed scoped visual review with map artwork excluded. Fresh source photographs and eight full product frames were supplied anonymously to a fresh Sol medium critic; no previous verdict/source history was supplied before its initial assessment. It accepted the instrument/military command-station direction with no evidenced P1/P2, then accepted two final expanded facility-ID frames. Independent review was visual only. Root browser workflow checks passed separately; see the branch continuation record for exact paths, browser/performance evidence and retained P3 findings. Final desktop/mobile captures: ignored `data/instrument-polish-final/`.


## Tactical overlay and selective graphics (`093aff7`)

Passed. A fresh Sol medium critic reviewed four anonymously named original instrument photos and eight full current product frames before source/history discussion, then independently exercised read-only desktop/phone navigation, resizing and keyboard scrolling. No confirmedP1/P2; small muted metadata and long truncated phone scope remainP3. The mid-record retained-scroll phone capture is preserved; independent first opening and resize navigation showed identity before metrics. Root full regression separately passes data-backed graphics, map/context, authentication/history/Orders, real browser zoom, malicious-looking record names and invalid work handling. A bounded Sol high review verified safe fixed SVG/text-node record titles after identifying and correcting the initial interpolation defect. See `docs/reviews/tactical-overlay.md` and branch continuation for exact evidence/method/limits.


## Apple palette, graphs and increased transparency (`e39e550`)

Passed scoped independent follow-up. A fresh critic initially found twoP2 issues: scaled phone graph text (~5px) and subdued operational labels. The same critic reviewed eight updated full frames and independently confirmed12px axes at390→1280→390px, Food→Energy selection, clearer operational copy and preserved63% fogged panels. No remainingP1/P2; units/friendly ticks resolved. RetainedP3: tall phone chrome and potential metric-colour/allegiance ambiguity despite ownership labels. See `docs/reviews/apple-system-colour.md` for source verification, preserved findings/resolutions, exact functional/performance/browser boundaries and capture paths.

## Icon and information audit — 19 October 2026

Passed scoped independent review. Fresh Sol medium critic inspected30 baseline captures, reviewed two improved candidate sets, and exercised read-only mobile/keyboard navigation. Confirmed P2 issues are resolved: generic icons, clipped Menu labels, phone working area, raw production/spending structures, weak ownership, ground/fleet symbol confusion and unclear report/empty context. No remaining P1/P2 in final reviewed frames. Root full Chromium regression passes, including added real-data/symbol/ownership/menu assertions; no page errors. A final explicit empty-upkeep message was browser-checked. Remaining P3: small metadata, Campaign/access composition and exact history endpoint/delta annotations. Independent interaction scope and final screenshot scope are distinguished in `docs/reviews/icon-information-audit.md`; Apple token exactness is source/computed-style verified. No new commercial comparison, Safari or production-scale claim.
