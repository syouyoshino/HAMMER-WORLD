# Coherent chart navigation — interface release candidate

5 November 2026 (UTC), `map-generation`, based on `d7c85c7`.
The user rejected the complete transition recording: Planet and Universe had
more visual finish than Galaxy, Sector and System, and the journey was abrupt.
Earlier scoped navigation acceptance did not establish a finished continuous
experience. This continuation addresses that gap; scoped evidence and remaining limits follow.

## Baseline evidence and actual defects

The native 93-second recording and screenshots are in `data/phone-transitions/`.
Research and the original three-step critique are recorded separately in
`docs/reviews/universe-research-and-redesign.md`; no new commercial-game parity
claim is made here. The comparison is about equivalent navigation tasks, not
matching a late-game reference's density with invented records.

Fresh normal-motion Chromium 154.0.8037.57 measurements at 1440×1000 are under
`data/coherent-navigation/baseline/`. Source hashes are anchored to `d7c85c7`.

- Both System planet previews ready: 6.17 s. Explicit System-to-Orbit entry:
  4.61 s. These samples are one fictional fixture in software Chromium.
- Four texture builds: median 812.85 ms, maximum 2383.5 ms. System draw calls:
  median 2.7 ms; hierarchy calls: median 0.5 ms. These are CPU call timings,
  not frame presentation latency or a production benchmark.
- Direct Enter orbit left zoom controls disabled after the globe was ready.
  The baseline's planned four zoom actions were therefore not performed. The
  previous video incidentally refreshed controls via a separate body journey.
- Entry enlarged a 128px preview before requesting the destination, waited on
  another map/detail load, then switched render products. Separately parsed detail
  objects defeated the renderer's WeakMap cache and repeated expensive terrain
  preparation. A generic opacity fade supplied no geographic correspondence.
- Higher charts were weak single-dot compositions; unlocated Universe contacts
  nevertheless had plotted positions. Breadcrumb code omitted region names
  matching `/reach/i`. Theme changes redrew Universe but not the other charts.

An initial suspicion about mismatched default style names was disproved:
`orbital` is the internal enum for the UI's Natural style. Pass the actual selected
enum consistently; do not invent a new `natural` enum or cite that suspicion as
a demonstrated cause of gray loading previews.

## Bounded architecture and preservation contracts

One Sol 6.1 high diagnosis approved two existing integration boundaries:

1. Reuse the atlas renderer for compatible higher-chart composition. Keep both
   Universe and Galactic reachable as schematic detail lenses. Show parentage,
   public system links and unknown contacts honestly. Parent-local coordinates
   are not a universal physical frame, and containment is not territory.
2. Prepare authorized saved planet data before approach. Reuse the existing
   globe renderer once to make a native-resolution transparent planet frame,
   then transform that frame during the handoff. Do not redraw the expensive
   shader on every approach frame, magnify background stars with the planet, or
   invent physical interstellar flight.

The prepared frame must use the actual selected style, recorded sun, relief,
emission, orientation and readability. Its final rectangle must be measured after
destination chrome layout, frozen through the animation, and match the first
native frame. The reverse path must restore the exact saved System camera and
avoid a bearing change when the small sprite returns.

Tickets must reject stale auth/campaign/snapshot/map request/input/planet/style/
viewport work; resize, cancellation and context changes release scratch canvases.
Reduced motion commits the prepared authorized destination directly. Keep the
permanent map canvas, all existing reachable management views, history read-only
rules, selection, geography and persistent IDs. UI state stays outside campaign
persistence. Backend, generator, schema and existing records remain unchanged.

## Initial implementation and retained findings

Luna's first higher-chart candidate improved contrast and breadcrumbs. A fresh
Sol medium critic, shown anonymous matched captures, found remaining ambiguous
diagonal links into the unlocated tray, territory-like containment, clipped
parent text and Forces overlap. These findings were retained for correction.

Localized Sol medium corrections give unlocated connections explicit text instead
of a plotted line, use open containment brackets and viewing-origin ancestry
labels, increase tray padding, clip visible targets and preserve only located
offscreen focus anchors. System annotations include public direct-child planet
names and an Open system cue; these are nonspatial labels, not added planet
coordinates. A separate service correction confines full assets to two retained
entries and 16 MiB of declared detail bytes, keeps up to 24 lightweight sprites,
coalesces queued/in-flight requests and rejects stale work. The byte limit is a
wire-size retention budget, not a measured JavaScript heap bound.

Root's expanded tests cover atlas unknown ancestry, hidden exclusion, immutable
public inputs, offscreen bounds and action targets; preview tests cover retained
object identity, cache/byte bounds, duplicate work, canceled waiters and invalid
snapshot/checksum/parent responses. Those checks preceded actual integration, complete forward/return motion and
performance reassessment; they were not sufficient acceptance evidence. A source-checkpoint browser run found a preview syntax error; those
captures are not a clean application acceptance run.

## Completed implementation and second critique

The actual API uses different public planet and geometry IDs. An intermediate
preview validator incorrectly required equality and prevented previews from
settling. It was corrected against the real public contract, with a realistic
regression fixture: `selected_planet.id` is the public ID; the planet map's
`parent` is that planet, whose `parent_id` is the system. Existing records were
not changed to satisfy a mock. The failed checkpoint is not acceptance evidence.

The completed forward handoff prepares the authorized asset before approach,
reuses its detail object, measures the native destination once, and animates only
the transparent native globe's circle. The source renderer suppresses its cheap
selected-body sprite during that bridge. Explicit Enter orbit stays in Orbit;
Enter surface descends only when requested. Arrival refreshes disabled controls.
The reverse path captures the current bearing, restores the exact System camera,
and retains a matching 128px return sprite. A guarded close-orbit pullback saves
the user's close camera before its transient movement. Reduced motion bypasses
the bridge. One keyed native frame avoids duplicate identical GPU renders/copies;
context, pose, texture, style, overlay, viewport, DPR and render-scale changes
invalidate it. No reliance on an unpreserved WebGL drawing buffer is introduced.

A fresh Sol 6.1 medium critic first received anonymous matched Sector and System
captures without implementation history. It preferred the clearer Sector state
but correctly found the first System pair visually indistinguishable. Its major
System finding was clustered bodies with weak spatial interpretation. Medium
findings were equally weak action choices, tiny unlocated/readout labels and
irrelevant surface controls. These findings prompted a substantive correction:

- Fit chooses a camera from recorded bounds and a recorded host-body direction;
  it never moves bodies. Exact saved-camera returns bypass Fit.
- A linear AU overview compares recorded host-star separations, explicitly
  labelled as separations, not orbital paths. It hides when it would cover a body.
- Enter orbit is the selected world's primary action. Other actions are secondary.
  The empty selector asks for a recorded body. Unknown-contact labels are readable
  and only advertise list scrolling when overflow exists.
- Planet controls are hidden in space charts. Light System has a compatible
  subdued field and readable text; the theme participates in the sky cache key.

On final selected dark/light captures, the same critic closed the major spatial
finding and the medium action/tray/irrelevant-control findings. It retained minor
small breadcrumb/status type, weaker light selection contrast, redundant factual
metadata and a footer that still says to select a body after selection. It did
not infer smoothness from still images. Final motion assessment is recorded below.

## Frozen-source functional evidence

All generated captures/traces/reports are local ignored QA artifacts, not campaign
archives. Browser checks use the existing explicitly fictional `nav-demo`; no
new campaign records or fabricated density were added for this presentation.

| Evidence | Observed result |
| --- | --- |
| `data/coherent-navigation/final/report.json` | Both previews ready before warm entry; 2.203 s entry, zero duplicate Reach detail requests; Orbit remains Orbit with usable zoom; exact System camera; held cold detail retains source and cannot enter an old campaign; same canvas, unchanged records, no page errors. |
| `data/coherent-navigation/body-context/workflow.json` | Mouse/touch and keyboard celestial focus, surveyed-world navigation, exact camera/selection/style/overlay returns, reduced motion, history read-only, private logout and stale context isolation; no errors or browser-token persistence. |
| `data/coherent-navigation/navigation-context/report.json` | Exact Orbit/Surface/System camera restoration, rejected held stale navigation, both translucent themes, same canvas, unchanged records and no page errors. The test initially wrote its default generated output directory; the completed result was copied here without rerunning the browser. |
| `data/coherent-navigation/universe-context/report.json` | Complete outward zoom chain, exact remembered System camera, separate root cameras, located/tray public partition, retained offscreen anchors, historical/private delayed-response isolation, stable handlers and 1280×720 CSS150% control bounds plus hit reachability; unchanged records, no errors. |
| `data/coherent-navigation/night-context/report.json` | Actual native rendering plus isolated shader fixtures retain night-only owned facility emission, close-night readability without moving the sun, unchanged day/coverage, and clearing between worlds/history; same canvas, unchanged records, no errors. |

Node checks cover atlas unknown ancestry/hidden exclusion/immutable inputs/targets,
preview cancellation/coalescing/object reuse/raw and sprite bounds/actual API IDs,
native bridge geometry, frame-cache invalidation and failed-render clearing,
System layout, background, Orbit relief/landmarks, body focus and facility lights.
Syntax and diff whitespace checks pass. Retained 10,000-turn gate backend hashes
all still match: 257.97 s, 10,001 snapshots and exact restoration; the frontend-only
change does not require another simulation stress run.

## Performance, reference comparison and limits

Chromium 154.0.8037.57, desktop 1440×1000, Linux ANGLE/Vulkan SwiftShader software
rendering. Normal-motion warm entry fell from a baseline 4.614 s to 2.203 s in
one same-fixture sample. This is about 52% less elapsed entry time, not a repeated
benchmark. A quiet intermediate probe exposed two identical native GPU-to-2D
copies of 1.539 s and 1.473 s; caching removes the redundant copy. The renderer's
remaining full-resolution software readback still limits latency. Sampled draw
calls do not establish presented FPS, hardware performance or production scale.

The comparison record inherits only actually examined material from
`universe-research-and-redesign.md`: Stellaris connected-chart developer text,
Endless Space 2 scan/navigation manual text, Sins II zoom/context documentation,
and the actual Endless Sky topology illustration. None of those commercial games
was run. Reference PDFs/portfolio pixels were unavailable; no pixel comparison or
commercial/Google Earth parity is claimed. The implemented response to connected
navigation is existing public links and explicit unlocated endpoints; the response
to scale/context continuity is hierarchy-preserving lenses and the native globe
bridge. No proprietary art or speculative physical routes were copied.

WebKit's executable is absent in this environment. Native macOS Safari, physical
phone playback, hardware GPU performance and production-density layout remain
unverified. Desktop is the requested scope. Universe/Galactic/Sector are schematic
charts over qualitative illustrative scenery; parent-local coordinates are not
universal astronomy, fog is not a measured discovery footprint, and System symbols
are enlarged. Moon contacts without recorded terrain remain records, not invented
surfaces. No recovered original cloud cartography/database is claimed.

Integration: preserve the preview-service API and public-ID/geometry-ID distinction,
cache/ticket authority keys and exact camera restoration when cartography returns.
The existing terrain engine, planet shader, backend, schema, generation, campaign
records and character-relationships branch are untouched. Existing management
screens remain reachable through their original shell; this milestone does not
re-certify every unrelated management decision. This is an interface release
candidate, not independently verified deployment, backups or operational security.

## Final motion evidence and independent outcome

`data/coherent-navigation/final-motion/report.json` records the actual normal-motion
20-step Universe → Galactic → Sector → System → Orbit → star/moon contact → planet
→ close orbit → Surface/pan → System/close-camera return → Universe → light charts
journey. Frozen source hashes match the final functional checks. No page errors,
changed campaign records or generated/interpolated navigation frames occurred.

`hammer-world-navigation.mp4` in that directory is the full 97.37-second actual
journey after initial fixture loading, 5,865,270 bytes, uncropped 1440×1000, normal
speed, H.264 Main level 4.0/yuv420p/30fps with AAC-LC silent audio, faststart and
20 scene chapters. Full ffmpeg decoding and moov-before-mdat were verified;
`media-verification.json` records the result. This encoding is compatible with
common phone players, but physical phone playback and a remotely accessible
sharing URL were not verified. Workspace paths are not public hosted URLs.

Three native globe bridge groups contain 20/19/22 instrumented draw calls spanning
516/489/537 ms. Median call intervals are 25.7/23.95/20.7 ms; maximums are
57.4/63.4/76.3 ms. These are scheduling samples, not presented-frame timing or a
60fps claim. Actual 4fps uncropped-aspect frame sheets span forward and both return
bridges. Preparation holds remain visible and software readback remains costly.

The same independent Sol 6.1 medium critic accepted the **scoped atlas/bridge
release candidate** on the supplied browser regression evidence, selected dark/
light screenshots, recording report and actual transition frame samples. No
remaining major/medium visual blocker was found in the revised selected Solar
view. The samples retain the selected globe and resolve to the expected destination
without a visible blank canvas or unrelated-body substitution. The critic did
not continuously watch the full MP4; its sheets establish sampled continuity,
not fluidity. Functional judgment relies on the supplied browser evidence.

Retained minor findings: small supporting metadata; redundant context notes;
'Select a recorded body' instruction persists after selecting one; weaker light
selection-ring contrast. Material limits: preparation/readback pauses, sparse
fixture coverage, no hardware/phone/Safari testing and no executed commercial
reference comparison. Neither this review nor average timing establishes Google
Earth-like smoothness or whole-game parity.

Delivery/continuation: commit this verified UI/test/documentation milestone to
`map-generation`, review its explicit tracked diff, and push without merge or
deployment. Prior ordinary Git authentication failed and connector writes were
blocked by approval policy `never`; do not claim remote delivery without observing
it. Integrate recovered cartography through the retained boundaries above. A
future hardware-GPU motion assessment should measure presented-frame latency and
native readback before deciding whether renderer composition needs replacement.
