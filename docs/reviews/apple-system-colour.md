# Apple system-colour graphs and transparent command station

Implementation: `e39e550`, following the requests for more graphs, more colour, more transparent panels, and Apple's official system palette.

## Colour source and application

Examined Apple's current [Human Interface Guidelines: Color](https://developer.apple.com/design/human-interface-guidelines/color), including the system-colour specifications updated in2025. The browser uses centralized reference tokens, not native SwiftUI/UIColor integration or automatic OS colour resolution. Existing neutral instrument surfaces and recorded cartography remain separate.

| Use | Official light reference | Official increased-contrast light |
| --- | --- | --- |
| Blue: active controls, readiness, energy history | `#0088FF` | `#1E6EF4` |
| Mint: food production/history and recorded force values | `#00C8B3` | `#008575` |
| Orange: consumption and construction work | `#FF8D28` | `#C55300` |
| Indigo: ore history | `#6155F5` | `#564ADE` |
| Red: existing error feedback | `#FF383C` | `#E9152D` |

Larger food bars use default-light samples; selected controls, coloured text and thin history lines use official increased-contrast variants where needed. Text labels and recorded numbers remain the source of meaning; colour does not designate allegiance. No Apple assets or native interface components were copied.

Panel opacity decreases from82% to63%, with10px local backdrop blur. Global map-readout plates decrease from91% to78%. Text itself stays opaque. Unsupported backdrop blur retains solid fallback surfaces; campaign/access dialogs stay solid.

## Graphs and correctness

Local Economy shows recorded food production and consumption on one shared scale, with explicit labels/values, replacing duplicate text rows. Unknown or invalid amounts do not become zero bars. No outcome at the baseline means no invented food-flow graph. Readiness gauges use the existing public percentage; construction work remains recorded work/max.

Campaign stock history switches between food, energy and ore using the same fetched snapshot series. Existing campaign/epoch/snapshot/root/selection guards and an individual chart render sequence reject stale results. A localized Sol medium correction keeps consecutive failures explicit, supports in-place metric recovery, and marks readiness only after a current-context completion.

Initial review found a significant phone defect: SVG text scaled to roughly5px. The chart now combines a responsive SVG plot with fixed12px HTML value/turn axes, including when resizing an already cached chart. It retains points, comparison annotations and turn range, with a zero-based1/2/5 scale and explicit resource/stock-unit context. No new observers, chart dependency, simulation rule or backend schema.

## Independent critique

A fresh Sol medium critic first opened four anonymous instrument references and eight full product frames before source/history discussion. It raisedP2 for scaled phone axes and subdued functional labels;P3 covered missing units/awkward ticks, tall phone chrome and possible allegiance interpretation of metric colours.

The same critic reviewed eight fresh full updated frames and independently used campaign selection, Economy → Campaign totals, Food→Energy selection, and390→1280→390px resizing. It confirmed12px axes throughout and accepted bothP2 fixes, with no remainingP1/P2. Units/ticks are also resolved. RemainingP3: phone chrome uses substantial vertical space; metric colour could be mistaken for allegiance despite explicit ownership labels. Its interaction coverage was bounded and read-only, separate from root regression coverage. No commercial-game parity claim.

## Browser and performance evidence

The full `tests/browser_strategic.py` Chromium run passes the existing16 destinations, map/canvas/camera/selection preservation, authentication/campaign staleness, preview/commit/history/restore, emulated touch and actual100/125/150/200% browser zoom. New assertions check food-flow values against the authorized API, absence of fabricated baseline bars, no new history requests on metric changes, consecutive failures and in-place recovery, and12px axes/no horizontal overflow after390/1280 resizing. Existing literal-title and invalid-progress regressions remain passing. Syntax/diff checks pass. Final small palette/text/axis-width refinements were then checked in fresh actual captures.

Fresh full-frame captures: ignored `data/apple-colour-final/`,1440×960 and390×844; `capture-evidence.json` confirms63%/10px panel styles and12px phone axes with17.39px line boxes. Full test artifacts: `data/apple-colour-regression/`.

Environment: managed Linux6.18.55/Debian13,3 logical CPUs, Chromium154.0.8037.57, Python3.12.14, Node24.19.0, PostgreSQL17 disposable demo-v2 schema. A workspace restart required restarting the existing QA container and a new isolated fictional preview, without modifying campaign sources.

Fixture action-to-ready Economy35.03ms/Construction49.57ms;24 cached baseline-context transitions median4.96ms/p957.57ms. DOM2499, post-GC nodes4897/listeners178, and API resource entries47 stayed stable across cached transitions; eight cold Economy opens shared one request. These timings exclude startup, full paint/chart completion, and generated-map transfer/GPU blur cost. They are not production-scale or long-session leak proof. Two-turn chart correctness/readability is tested separately from cached baseline navigation timings.

Chromium only; WebKit, native Safari and physical mobile remain unverified. The artwork remains temporary and unrelated to recorded geography. Unsupported relationship/diagnostic records, unrecovered cloud data and cartography integration limits remain unchanged. Interface release candidate only; no merge/deployment or operational certification.
