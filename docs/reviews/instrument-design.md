# Aerospace instrument design direction

User-approved direction, 18 October 2026. Supersedes the Windows-era visual treatment while retaining the working strategic command navigation and campaign contracts. User supplied four photographs of monochrome avionics/instrument controls and authorized a complete design rework. This is an adaptation to a map-based strategy application, not a pixel clone of an audio/flight-control screen.

## Visual truth and interpretation

The four source attachments show off-white backgrounds, fine graphite linework, monospaced numeric displays, spaced uppercase labels, sparse alignment-led groups, solid selected controls and measurement geometry. The photographs contain blur, low contrast, perspective and partial framing; these are capture characteristics, not gameplay requirements. No proprietary logos, decorative gauges, fabricated telemetry or copied illustration assets belong in the application.

Use a self-hosted openly licensed monospaced typeface, readable primary text, fine dividers and restrained semantic state colours. Names and key values precede secondary metadata. Grouping should mostly come from alignment, spacing and shared headings. Thin outlines indicate controls or genuine boundaries rather than boxing every value. Selection, focus, loading, disabled, error and historical read-only states must remain distinguishable. No Windows bevels, blue title bars, rounded dashboard cards, glass, shadows or decorative instrument numbers.

## Product boundaries

The map remains mounted and its frame/camera is independent of workspace visibility. Existing geography, IDs, rules and backend persistence remain authoritative. Existing workspace/inspector/dialog navigation, request epochs, History comparison and Orders proposal retention stay functional. UI changes must not create character relationships, economic diagnoses, forecasts or records. Local population, civilians, crews and province aggregates must retain their distinct meanings.

First prove map → province/settlement inspector → local Economy → Construction → map. Then apply the same presentation system to reachable management screens, History and Orders. Render actual data in readable groups; preserve technical records as secondary details where needed. Map styling may be adapted without changing generation or saved geometry. Phone controls and primary actions must remain operable without arranging windows.

## Evidence protocol

Fresh baseline at `b6836be`: `tests/browser_strategic.py` passes, with captures copied to ignored `data/instrument-baseline/`. Source photos are local user attachments, not application assets. Fresh candidate screenshots, functional checks and one independent Sol medium critic loop will determine acceptance. Compare style at full frame and readable detail, explicitly accounting for source capture perspective and different content. Do not claim economic or character-task parity from a cosmetic rework.

## First candidate independent findings

A fresh GPT-6.1 Sol medium critic inspected all four original photographs and the actual full app frames before source or implementation discussion. It recognized the monochrome/monospace family but rejected the first candidate's remaining admin-tool presentation. Preserved findings:

- P1: absent visible global navigation/turn in the initial capture; selection rectangle visually crossing water/header space; raw overcompressed Military/Fleet IDs and columns; Orders dominated by technical transport mechanics.
- P2: undersized core typography, repeated workspace/body/section headings, unclear continuation, empty single-point History chart, storage-oriented prose.
- P3: control consistency and terrain legend differentiation.

Separately, actual pointer evidence established a P0: the canvas intercepted Menu because the new commandbar lacked positioned stacking/input. A localized Sol medium fix restored it; desktop pointer/mobile tap and campaign/turn hit tests passed without forced clicks. Fresh 1b captures then exposed phone campaign choice shrinking to an arrow, resource/title collision and breadcrumb/control wrapping. These are explicit revision work, not accepted limitations.

The Luna builder owns the next bounded correction across public presentation files. No unrelated data/mechanics work is being used to compensate for these findings.


## Later evidence and final corrections

The same critic found candidate2 in-family but still blocked phone navigation clipping and unexplained empty collections. Both were corrected. Actual validated Orders then exposed nested production/consumption JSON fragmentation; a localized Sol medium fix now presents scalar balances and exact per-settlement resource disclosures with full raw response retained. A screenshot clipping artifact at200% zoom was diagnosed with full-frame CDP capture; it did not establish an application control-access defect.

Broader four-level captures exposed a genuine inherited/integration gap: known hierarchy markers occupied the fixed header/resource region. A bounded Sol high architectural diagnosis approved a hierarchy-only measured safe rectangle, stable full canvas, preserved source coordinates/camera and clipped hit testing. Luna implemented it with a single rAF-scheduled ResizeObserver for persistent chrome. Direct pointer descent, breadcrumbs, mobile taps, actual100–200% zoom and hierarchy-context retention now pass, rather than relying on selector reachability alone.

Adding direct hierarchy navigation changed the local context before the repeated-navigation measurement. The test now explicitly warms that context before calling transitions cached. A separate cold burst exposed missing in-flight de-duplication; Sol medium added per-context loading guards and exact valid-completion checks, with successful held-response/stale-context/retry probes. No auth token or proposal persistence was introduced.

Independent final visual/interaction disposition is recorded in root `design-qa.md`. Remaining data limits are unchanged: no ranked economic diagnosis/forecast, no character relationship records, no recovered cloud cartography/database. This style adaptation does not claim whole-game or commercial task parity.


Final independent disposition: accepted across the complete presentation and the subsequently extended hierarchy path, with no remaining evidenced P0/P1/P2. The same critic independently performed actual desktop/phone/200% zoom direct descent as well as earlier report/dialog checks. P3 notes: small tertiary metadata, subtle scroll continuation and generous report spacing. See `design-qa.md` for comparison history and `instrument-verification.md` for exact testing/performance boundaries.
