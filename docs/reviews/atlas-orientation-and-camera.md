# Atlas orientation, camera intent and compact controls — 31 October 2026

## Scope and baseline

User approved three concrete improvements after `4867696`: show the current
system/region and selected destination clearly; use purposeful camera movement;
compress the Universe header. Fresh baseline screenshots are under
`data/atlas-orientation/baseline/`. They show a selected Hearth sector, but no
explicit viewing-origin summary and about202px before the scene begins. The
existing diffuse decorative backdrop and bounded ambient motion are retained.
This is an interface release candidate; no deployment/operations claim.

## Design and authority contracts

A bounded Sol high read-only architecture review specified:

- “Viewing origin” is navigation context, not a fleet's physical location. Reuse
  the existing page-local origin ticket; derive a surveyed system only from a
  committed public Planet/System ancestor chain. No arbitrary home/first system.
  Origin sector/region markers intersect existing public chart contacts; no
  fabricated system coordinate is placed on the Universe schematic.
- Clear origin/selection across campaign, login and snapshot changes. Unknown
  ancestry stays unknown. A historical origin may be rederived, but returning
  must stay in that historical authorized snapshot.
- Select a contact to preview/focus; explicitly Open its chart. The renderer
  exposes all authorized schematic anchors separately from visible hit targets,
  so an offscreen contact can be focused through the selector.
- Save the visible Universe camera before an approach and skip transient camera
  saving when opening the existing Galactic/Sector destination. Returning restores
  the camera before approach, including under reduced motion.
- One existing RAF loop advances optional focus/approach tweens. Guard epoch,
  campaign, snapshot, map request/record, selected contact and input sequence.
  Manual input, selection, overlays, visibility and context changes cancel pending
  opening without executing navigation. Reduced motion opens/focuses immediately.
- Universe zoom-in endpoint opens the selected known contact, else returns to a
  validated viewing origin, else stays. No arbitrary first destination.

Compact styling is scoped to the committed Universe chart. Redundant resource,
breadcrumb and eyebrow rows collapse; campaign/menu/turn/pending/map controls
remain visible. Other map headers restore on navigation. Origin and destination
are readable navigation facts, not campaign statistics or browser-persisted state.

No backend, schema, generation, astronomy, authentication or immutable-history
changes. Character branch and unrecovered cartography remain untouched.

## Candidate checks and independent findings

Luna built the bounded implementation. Initial actual browser checks pass normal
focus/approach interpolation, offscreen focus, exact return, manual/overlay/
selection/context cancellation, reduced motion, compact desktop control bounds,
HUD restoration and unknown-origin handling. No records changed or page errors.
Initial Universe header was111.4px (Planet header144.1px); that tiny9px orientation
text was not a sufficient visual result despite the recovered space.

A fresh Sol medium critic first inspected anonymous full-aspect A/B screenshots,
with origins and desired winner withheld. Both use the same1440×1000 viewport and
known contact load with Hearth selected. B's camera focuses the selection, so this
is an equivalent task comparison, not a claim of equal map scale or terrain
improvement. Intended workflows/executed evidence were supplied afterward. The
same critic is retained through fixes.

| Finding | Severity | Response |
|---|---|---|
| No explicit origin versus destination | High in baseline | Public ancestor-derived viewing-origin and separate destination summaries |
| Origin region looks more selected than destination | Medium | Distinct destination brackets/label, cyan origin cue and state legend |
| Open action has same weight as return/routine controls | Medium | Restrained primary action treatment and destination-specific action text |
| Core orientation prose looks like tiny diagnostics; region truncates | Medium | Readable label/value grouping, wrapping and dedicated context space |
| Header hides too much map | Low–medium | Scoped compact header; preserve readability rather than minimizing pixels |
| Instructions imply immediate open; state key unclear | Low | Select-then-open wording and origin/destination state cues |

The earlier historical test expected a disabled return action. That assertion
became obsolete with valid origin derivation from a historical committed planet.
The updated test verifies the actual System response remains in the historical
snapshot, rather than rejecting useful read-only navigation. No historical write
is enabled.

Final evidence, scoped verdict and remaining limits follow below.


## Final execution and independent verdict

Frozen-source reports and traces:

- `data/atlas-orientation/final/`: normal interpolated preview/focus and opening;
  single-click selection stays in Universe; an offscreen contact focuses through
  the complete anchor set; exact camera return before approach under both normal
  and reduced motion, including manual pan; wheel/menu/selection/context cancel;
  reduced-motion opening; inactive readout text/titles/action labels cleared;
  unknown origin not invented; other map HUD restored; retained canvas; unchanged
  campaign response and no page errors. Cancellation race cases use synchronous
  DOM events and are not claimed as separate physical input-device trials.
- `final-navigation/`: entire outward/inward zoom journey, origin return, independent
  root cameras, selected-contact preview then Open, surveyed/detected restrictions,
  snapshot-authorized historical return, held old responses across campaign switch
  and private logout, no token browser storage, both themes, stable canvas handlers,
  desktop CSS zoom and unchanged records all pass with no page errors.
- `final-motion/`: actual ambient pixel change with stable contact targets, pan,
  persistent action tooltip, static reduced motion, actual menu/workspace pauses,
  injected visibility event pause/resume, exit/reentry and campaign stop, retained
  canvas/handlers and unchanged records pass with no page errors.
- Node projection, preview isolation/cache, body-return and Universe tests pass.
  The Universe check now verifies all authorized focus anchors survive offscreen
  panning while clipped contacts stop being hit targets. Syntax/diff checks pass.

The same independent critic accepts the revised four orientation states: no
remaining high/medium visual blocker for the three approved goals. Explicit
origin/ancestry and selected destination are readable; named primary action and
white DEST brackets distinguish destination from the cyan origin cue; all names,
buttons and parent facts fit the tested150% desktop capture. Select-then-open
wording now matches behavior. The final default scene begins around163px versus
baseline202px, about39px reclaimed while improving core text size. The final
Universe heading DOM height is150.8px; this is not compared directly with the
baseline scene-edge measurement. At150% the scene occupies about332px of720px:
a useful sparse chart, not evidence for busy late-game density.

Remaining low-priority findings: small supporting map/legend/footer typography,
detached Forces control and tiny DEST tag (backed by clear brackets/HUD). No
further header compression was requested after readable grouping. Still-image
review does not independently execute browser workflows, certify keyboard/
screen-reader behavior, measure contrast or establish smooth animation. The
critic received executed evidence separately from its blind screenshot assessment.

## Browser and performance bounds

Chromium154.0.8037.57, shared Linux/two-CPU software graphics. Actual sizes:
1440×1000 and1280×720 CSS150%. Native browser zoom, WebKit/native Safari, hardware
rendering and much denser multi-region layouts remain unverified.

Ambient sample:39 draw calls over1,932.9ms (~20.18 calls/s), median0.50ms renderer
submission, maximum207.9ms in a population including cold artwork creation. The
navigation suite reports0.50ms median and79.7ms maximum. These are draw-call costs,
not compositor latency, production capacity or a guaranteed frame rate. Ambient
remains capped at24Hz; camera tweens use the same RAF lifecycle. The inherited
software globe cost and two-theme decorative bitmap cache are unchanged. No
commercial-game/Google Earth parity claim.

Backend source is unchanged. Retained applicable10,000-turn fixture gate:
`data/terrain-finish/stress-v2.json`,257.97s,10,001 snapshots and exact restoration.
No simulation stress repetition for this frontend change. UI camera/origin state
stays ephemeral; physical Universe positions and discovery footprints remain
unrecorded. No data reset, merge, deployment or operational recovery certification.

Final frontend SHA-256 hashes:

| File | SHA-256 |
|---|---|
| `public/app.js` | `10c5c6471a618d543e8f8f27f0f77edd3378c7a702dfec2df66647800d9c0e9f` |
| `public/universe-view.js` | `5da2d751fc1d127ad1fec51a0e6f4ac1b07c3c2318c4b8013ccfb94a684fea51` |
| `public/index.html` | `e61f62fe003ba89d1d8ac1e3c6d1a933bf82d0c095151fcea835699196fe3ded` |
| `public/style.css` | `60f5bc845dbd593be2731fad32cccbc4d5b434e33b51d1dc56099de8ada2aaa5` |
| `public/desktop-shell.js` | `02190928ec72d2a275f81ecff58571ee7da546efe5dee4a8d34e1bad6bf59ad2` |
| `public/desktop-shell.css` | `9209014687810685a4dcbc8b367601f3cb07d97875f74f43d639c44dd57b309e` |


Integration: retain the committed-context origin derivation, full contact anchors,
pre-approach camera save, and cancellation guards when combining unrecovered map
work. The single-click preview is intentional; Open (or selected-contact inward
zoom at the endpoint) performs navigation. Character relationships remain an
independent screen. Continue with busy-fixture and native-browser evidence before
making broader quality/performance claims.

Verified implementation/tests/review: `494c1e4`, pushed to `origin/map-generation`
from baseline `4867696`. Runtime captures/traces remain local ignored evidence;
no private campaign records, credentials or databases are committed.
