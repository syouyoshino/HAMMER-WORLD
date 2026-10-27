# Orbital settlement orientation

Status: bounded annotation interface release candidate independently accepted
and functionally verified on `map-generation`.
The accepted globe/Surface release remains `34a9f25` with delivery notes in
`39919a3`; this continuation does not replace its evidence.

## Demonstrated gap and bounded decision

The user authorized further improvement. Fresh 1440×1024 Chromium interactions
show a sparse exposed-rock globe with no visible settlement names, while Surface
exposes recorded Forge/Outpost anchors. Ignored evidence:
`data/orbit-orientation/baseline/{rock-globe,rock-surface}.png` and `workflow.json`.
No baseline page errors were observed. This is an orientation problem, rather
than evidence for inventing new natural geography or orbital relief.

A bounded Sol high review approved settlement annotations using only the current
public settlement projection and recorded fine province anchors. Coordinates
represent a province anchor, not a separately measured city position. The
existing sphere projection supplies perspective horizon rejection and the same
safe viewport as rendering. Multiple settlements sharing an anchor are grouped.
The selected province and owned settlements have priority; public foreign
settlements are not silently excluded.

Keep the accepted albedo sphere, pole reconstruction, terrain, immutable assets,
backend rules and saved geography unchanged. Proper spherical height normals and
new LOD assets remain separate architectural work. Physical polar distortion is
not solved by adding navigation annotations.

## Intended workflow and boundaries

Recognize a settlement in Orbit, activate its labeled marker, descend to its
saved province anchor and inspect that province. Economy/Construction/Map return
must preserve selection and camera context. Marker activation must never stage
or commit a military decision.

Annotations must reject wrong-planet/invalid/backside anchors, avoid active UI
panels and other labels, and preserve the distinction between the anchor and a
displaced label. Clicks use the recorded anchor, not inverse projection of the
label's displaced center. Hidden far-side labels cannot remain clickable or
keyboard-focusable. Ordinary terrain clicks and map drag must retain their
existing behavior. Names controls remain specific to hydrographic labels.

Derive annotations on each draw from the authorized current context; clear them
on hierarchy/planet/campaign/history/login changes and WebGL fallback. UI state
is not campaign data. No new API or local persistence is needed.

## Findings and corrections

An independent Sol medium critic first received anonymous full-frame A/B images,
without source or implementation history. A was the fresh baseline and B the
first candidate, at matched viewport, camera, data and information load. B
provided recognizable settlement references, but the critic found missing
north/up information (high), detached labels without leaders, generic point
symbols and ambiguous “Names Off” alongside visible settlement names (medium).
The initial blind assessment is retained; it was not replaced with a new critic.

Root browser testing confirmed correct pointer activation and canonical province
selection, but ordinary resize lost keyboard focus. The builder had reused
buttons, then hidden them at the start of every draw. Localized Sol medium fixes
retain active keyed buttons through redraws and clear only invalid/non-Orbit
contexts. Source review also found the initial cap applied before horizon
filtering; it now caps successful visible placements. Invalid anchors are
rejected, and label/marker collisions are resolved deterministically.

The revised candidate adds an explicit north-up cue, short anchor leaders,
settlement/building glyphs, square labels, “Hydro names” wording and explanatory
Recenter help. Coordinates remain recorded province anchors. Selected symbols
use the existing Apple system-blue token in both themes. Inactive buttons are
evicted from the DOM/cache, keeping resident annotations within the 12-item cap.
No new backend fields, requests, local persistence or gameplay rules were added.

The same critic accepts the corrected bounded annotation task, with no remaining
new major issue observed. On caps/water/hydrocarbon it exercised symbol, text,
Enter and Space activation; each opened the corresponding province and local
settlement inspector. Focus survived redraw. A south-facing rotation removed
visible annotations, Recenter restored them, Hydro names remained independent,
and campaign switching cleared stale selection/inspector context. No page
errors occurred in its three primary activation checks.

Critic captures are preserved unmodified under ignored
`data/orbit-orientation/critic-final/`. The existing Surface glyph differs from
the orbital building glyph: retain this minor consistency limit. Dense layout
and cap behavior were covered by focused unit checks, not an independent large
campaign browser stress test. Prior faint microtext/standard control styling and
sparse natural globe relief remain inherited limits, not new acceptance claims.

## Verified behavior

`tests/browser_orbit_landmarks.py` is a read-only regression against explicitly
supplied isolated local-mode V10 fixtures. It checks exact saved anchors,
keyboard and touch-symbol activation, unobscured selected location, focus after
resize, Economy return, drag without activation, backside disappearance and
inactive former hit positions, campaign isolation, WebGL fallback and unchanged
campaign snapshot/state. Its final run has zero page errors and matching
before/after source hashes. Evidence:
`data/orbit-orientation/browser-touch-final/workflow.json`.

The protected native browser regression also passes with the final application:
settlement→Economy→Construction→Map, refined feature selection, canonical military
map target and real preview/commit, read-only history, six campaign switches,
stable canvas/input handlers, held real asset responses after switch/logout,
and absence of stored tokens. Logout now explicitly asserts no remaining orbital
landmark nodes. Evidence: `data/orbit-orientation/protected-final/workflow.json`.
These are fictional test campaigns, not changes to private campaign records.

Actual Chromium Settings tab zoom 100/125/150/200% passes physical desktop
windows 1280×960 and 1920×1280. Checks include the visible north cue, settlement
label bounds, command/map controls, inspector close, management return and the
four-level hierarchy. The smallest CSS viewport is 640×436. Evidence:
`data/orbit-orientation/zoom-{1280,1920}/metrics.json`. Touch emulation also
activated the native settlement button correctly. Light/dark selected-symbol
colors match the existing system-blue variables, and hierarchy navigation clears
annotations/cue; see `appearance/workflow.json` and `touch-final/workflow.json`.
Coverage is Linux Chromium154; WebKit/native macOS Safari remain unverified.
Desktop scope only; no accessibility certification is claimed.

Focused Node checks pass for canonical grouping, selected/owned/stable priority,
wrong-planet and invalid-anchor exclusion, seam/horizon handling, 12 backside
anchors followed by a visible front anchor, successful-placement cap, marker/
label collision avoidance and leader endpoints. Existing orbit projection and
hydrographic label checks pass. The backend's 14 frozen hashes and both terrain/
sphere renderer hashes match the accepted release. The prior 147-test, 264-hash
and 10,000-turn backend gates remain applicable; simulation was not rerun for
this frontend-only annotation change.

## Performance and limits

On the shared 2-CPU Linux fixture, Chromium1440×1024, 20 management/map cycles
after warmup retained the same map canvas, 1302DOM nodes, 130JS listeners and two
resident/visible annotations at samples0/10/20. There were no page errors.
44actual layout calls averaged0.043ms, maximum0.300ms, with this small fixture.
These timings exclude DOM, compositing and GPU work; they establish neither FPS
nor large-campaign performance. Evidence: ignored `resources/metrics.json`.
Final selected-color/copy polish is separately browser-verified; the unchanged
application/module hashes tie functional and resource evidence together.

The improvement supplies strategic landmarks, not natural rock relief or a new
spherical terrain engine. Physical polar material distortion, source-grid
softness and sparse terrain-based orientation remain documented in the
[planet-scale review](planet-scale.md). No new commercial-game or Google Earth
comparison was performed or claimed. No original cloud records/cartography were
recovered, no campaign data was reset, and no merge or deployment was performed.

Reproduce the read-only check with `WOLD_ORBIT_TEST_BASE`,
`WOLD_ORBIT_TEST_CAMPAIGN` and optional `WOLD_ORBIT_TEST_OTHER` pointing to isolated
local V10 fixtures, then run `python tests/browser_orbit_landmarks.py`. Run
`node tests/check_orbit_landmarks.cjs` for pure layout checks. Generated captures,
metrics, test databases and caches remain excluded from Git.
