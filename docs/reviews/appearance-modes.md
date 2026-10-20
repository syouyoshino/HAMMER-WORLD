# Light, Dark and System appearance — 20 October 2026

User-approved follow-up to `0b778d5`: add dark mode and useful additional colours. Interface release candidate only; no merge, deployment, recovery, security certification or commercial-game parity claim.

## Behaviour and design

Menu → Appearance offers System, Light and Dark. System is the default and follows `prefers-color-scheme`; explicit choices override it. A small synchronous same-origin script before the stylesheets applies the resolved appearance before normal content paint. It updates the native `color-scheme` hint and browser theme-colour metadata. Only the whitelisted preference is saved under `hw.theme.v1`; invalid/missing values use System, and blocked browser storage leaves the controls operable. Authentication remains page-session memory only. Campaign data is neither fetched nor changed by a theme switch.

Light retains the approved63% panel /78% map-readout opacity and10px localized blur. Dark uses charcoal panels at86%, readout plates at88%, off-white primary text and brighter accents. These alpha values preserve readable labels over the bright temporary artwork. Unsupported blur has solid surface fallbacks. Access dialogs remain solid. Sharp corners, compact typography and the existing one-workspace/inspector shell remain. No inversion, recolouring, filtering, replacement or remounting of the actual map canvas or generated artwork.

Section families remain mint economy/exchange, orange development/supply, indigo forces, teal knowledge and blue administration/navigation. Additional status colours supplement visible labels: yellow archive pending, green verified archives/ready previews/explicitly completed local facilities, orange explicitly unfinished facilities, red error feedback. Unknown facility completion remains neutral. Foreign is not inferred to mean hostile; no shortage/health diagnosis or new statistics were invented. Purple is available as a paired palette token; no arbitrary extra category colouring is required.

The current official [Apple HIG colour specifications](https://developer.apple.com/design/human-interface-guidelines/color) were re-examined on20 October. These are reference RGB values implemented in CSS, not native UIColor/SwiftUI dynamic colours. Default-dark/increased-contrast-dark pairs used:

| Colour | Default dark | Increased-contrast dark |
|---|---|---|
| Red | #FF4245 | #FF6165 |
| Orange | #FF9230 | #FFA056 |
| Yellow | #FFD600 | #FEDF43 |
| Green | #30D158 | #4AD968 |
| Mint | #00DAC3 | #54DFCB |
| Teal | #00D2E0 | #3BDDEC |
| Blue | #0091FF | #5CB8FF |
| Indigo | #6D7CFF | #A7AAFF |
| Purple | #DB34F2 | #EA8DFF |

Small strokes/text use increased-contrast variants. Selected tabs retain the darker official blue#1E6EF4 behind white text, and error toasts retain official red#E9152D behind light text, rather than putting white on the brighter dark-mode accents. Neutral charcoal surfaces are Hammer World's own presentation colours. Added light yellow/green/purple default/increased-contrast pairs match the same HIG table.

## Verification and critique loop

Luna built the bounded presentation change. Root's fresh first captures exposed a stale duplicate light-background CSS rule; a localized Sol medium escalation consolidated it. Root and a fresh independent Sol medium critic then identified fixed dark SVG food-flow text on charcoal. The same localized specialist replaced text/track/grid/series literals with inherited CSS variables, so cached graphs adapt without replacing their DOM or reloading records. Both defects are preserved here rather than hidden behind initially passing functional checks.

Fresh full-frame evidence, all1440×960 and390×844: `data/dark-theme-candidate/` (initial defect), `data/dark-theme-final/` (surface correction, graph defect), `data/dark-theme-corrected/` (graph correction), and `data/light-theme-final/` (equivalent light states). Thirty frames per set include19 management/compatibility destinations, the selected settlement journey, charts, Menu and access. Recorded fixture data is identical across modes. Temporary fictional artwork remains visibly disclosed. No proprietary screenshots or new commercial comparison are part of this review.

Root's final `tests/browser_strategic.py` run passes in isolated PostgreSQL schemas, including all existing destinations, actual Galaxy→Sector→System→Planet pointer navigation, settlement→Economy→Construction→Map, selection/camera/overlay retention, panel input boundaries, campaign/login/logout stale requests, turn preview/commit, historical read-only behaviour/restore, malicious-looking record names and supported public-data graphics. New theme checks verify:

- System follows OS appearance changes; explicit Dark ignores an OS switch to Light.
- Sixteen explicit switches and OS changes produce no campaign API request and retain the canvas object/pixels and turn.
- Explicit preference survives reload, while the access token does not enter browser storage.
- Invalid or blocked preference storage falls back safely and still allows theme selection.
- Workspace, inspector and Menu actually use dark surfaces, not merely a dark attribute.
- An already-mounted local food-flow SVG changes text colour in Dark and Light while retaining its object identity and recorded values.
- Desktop,390px phone, actual100/125/150/200% Chromium browser zoom and existing12px history axes remain operable. No uncaught JavaScript errors.

Final regression evidence: `data/theme-verified-regression/metrics.json`; syntax/diff checks pass. No simulation/backend/schema changes and no repeated10,000-turn simulation stress under the user's UI-only exception.

The same independent critic accepted the corrected full desktop/mobile frames with no remaining theme-blocking defect. It independently exercised read-only Chromium appearance selection, live OS preference changes under System, native keyboard selection, Menu closing, mobile Military scrolling/navigation and return to Map. No non-read API requests were observed. Final visual scope includes Menu, Military, Economy/history, Construction, Inspector and access at1440×960 and390×844. Its acceptance is scoped; small secondary metadata remains dense, especially on mobile. It did not perform a contrast-compliance certification, screen-reader audit, state-changing Orders actions, wider dataset review or other-browser verification. Root's separate regression supplies the broader functional evidence above.

## Performance and coverage limits

Managed Debian13 Linux6.18.55,3 logical CPUs, Chromium154, Python3.12.14, PostgreSQL17, isolated fictional demo-v2. Final first Economy/Construction action-to-ready70.27/58.16ms;24 cached transitions median17.02ms/p9552.94ms. DOM2551→2551; post-GC documents1/nodes5002/listeners180 unchanged; API resource entries47→47. Eight cold Economy opens share one held history request. The run overlapped a separate screenshot capture process, so these observations are not a controlled before/after benchmark. Timings exclude startup, full paint/chart completion, image transfer and GPU blur cost. No production-scale or long-session leak-free claim. Theme changes themselves are CSS/token changes with one OS-preference listener; the test observes no campaign API work.

Chromium desktop/emulated touch and OS colour preference emulation were tested. WebKit, native macOS Safari, physical devices, real display colour/ambient-light conditions and production-scale data remain unverified. Missing recovered cartography/database, economic diagnosis and character relationships remain unchanged limitations.

Integration: retain the theme bootstrap before styles; use shared tokens for new surfaces and SVGs rather than capturing resolved colours at creation. Keep persistent map chrome/projection independent of transient surfaces. The relationships branch is untouched. Do not store any token or campaign record with appearance preferences.
