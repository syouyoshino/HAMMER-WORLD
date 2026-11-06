# Every-view critique and correction — 6 November 2026

Continuation on `map-generation`, baseline `04a405c`. The user requested a heavier
critique of each view and fixes. Prior scoped acceptance remains scoped: it did
not prove fluid motion or finish every view. No deployment/merge/data reset.

Final outcome: independent Sol medium accepts the scoped desktop visual and
interaction release candidate; no unresolved critical/major navigation defect
remains in examined workflows.13 targeted Node suites and9 frozen-source browser
suites pass; selected-atlas placement received relevant follow-up regressions and
a refreshed20-step native capture. See the final evidence/verdict sections below.

Motion remains visibly limited in software Chromium:~80ms median trusted-drag
completion,~0.95s warm System→Orbit entry and a recorded~287ms bridge gap. This is
not a fluid-motion/commercial-parity endorsement. Minor softness/label limits and
unverified hardware/WebKit/native Safari/production operations are explicit below.
No backend, saved geography, schema, history, campaign data or character-branch
changes. Earlier adverse findings and rejected candidates are preserved.

## Fresh evidence and independent findings

Root recaptured the actual normal-motion 20-step journey at 1440×1000 in Chromium
154.0.8037.57: `data/deep-critique/baseline/` (screenshots, raw native video and
report). No page errors or changed campaign records. A fresh Sol 6.1 medium critic
with no inherited implementation discussion inspected all 20 screenshots. Still
findings do not establish frame pacing. Sparse records are not a defect and must
not be padded with invented contacts. The prior reference research remains in
`universe-research-and-redesign.md`; no commercial game was executed this turn.

| ID | Severity / step | Specific defect and practical correction | Status |
| --- | --- | --- | --- |
| D01 | Major / Orbit 09,10,14 | Almost-black land under settlement labels prevents strategic terrain reading at a useful orbit distance. Introduce earlier analytical illumination while preserving recorded sun, terminator and day/night distinction. | Corrected; final evidence below |
| D02 | Major / star/moon 07,08 | Selected row uses near-white text on pale grey. Use theme-specific selected foreground/background and a persistent accent. | Corrected; final evidence below |
| D03 | Medium / Galactic,Sector 02,03,18,19 | Hierarchy changes but composition does not: same Hearth/Cinder card. Galactic must emphasize actual region/sector containment; Sector its systems. | Corrected; final evidence below |
| D04 | Medium / Galactic,Sector | Upper-left actionable record loses priority to bright central decorative galaxy. Deliberately group known contacts and subordinate background. | Corrected; final evidence below |
| D05 | Medium / star/moon | Planet/Terrain/Natural controls and Reach-ending breadcrumb describe the source, not focused body. Hide irrelevant controls and show actual focused body's ancestry. | Corrected; final evidence below |
| D06 | Medium / celestial return | 'Back to origin map' hides actual saved destination. Name world and Orbit/Surface/System while preserving exact saved camera. | Corrected; final evidence below |
| D07 | Medium / System 15 | Visible Ash loses its name despite free canvas; footer sends user to list. Improve alternate placement/compact identifiers and retain hover/focus identification. | Corrected; final evidence below |
| D08 | Medium / focused System 20 | Two offscreen context bodies explained only in footer. Put explicit full-system recovery near selected body controls, preserving focus camera. | Corrected; final evidence below |
| D09 | Medium / Surface 11,12 | 'Select a province' instruction with no visible boundaries in Terrain. Reveal useful hover/selected boundaries and expose Provinces near inspection action. | Corrected; final evidence below |
| D10 | Medium / Universe 01,16,17 | Repeated 'VIEW ORIGIN · ANCESTOR' and tiny 'DEST' require decoding. Separate 'Contains origin: Cinder' and selected destination treatments. | Corrected; final evidence below |
| D11 | Minor / Surface entry | Forge/crosshair/ENTRY FOCUS/north/coordinates pile up. Consolidate anchor and make coordinates secondary. | Corrected; final evidence below |
| D12 | Minor / cross-view scales | D1.55 and Orbit1.69R unexplained. Name camera-scale meaning, maintain coherent zoom-control arrangement. | Corrected; final evidence below |
| D13 | Major / continuous globe motion | Synchronous full globe copy into 2D on every pose; unbounded framebuffer at DPR2, full-resolution pullback/final draws and redundant pointer draws. Remove forced continuous copies, bound output resolution, coalesce input. | Corrected; final evidence below |
| D14 | Minor / revised Orbit still | Adaptive output exposes stair steps on the planet silhouette; smooth the analytical edge without adding atmosphere or changing terrain. Interior softness remains a documented software profile tradeoff. | Corrected; final evidence below |

The critic's suspected 10-versus-14 camera mismatch was explicitly withdrawn:
Surface pan at step12 intentionally changes the next committed Orbit camera;
step14 must restore step13, not step10. Retain the evidence correction rather than
inventing a camera regression.

## Bounded motion diagnosis

One Sol 6.1 high read-only diagnosis examined newly exposed continuous-motion cost.
Current framebuffer output is only scaled by DPR≤2, not absolute output pixels;
at 1440×1000 DPR2 it can reach 5.76 million pixels. Return pullback is omitted from
moving detection, and pointer input draws synchronously per event. Eight albedo
and relief samples per globe pixel also warrant measurement, not guessed blame.

The approved minimal boundary is existing globe presentation and renderer output:
show its existing transparent WebGL canvas directly above the permanent 2D map,
below landmarks/UI, with no pointer capture. Transform that globe layer during the
prepared bridge; keep background and picking on the existing permanent map. Retain
only actual small return sprites, add absolute framebuffer bounds and coalesce
input draws. Keep the full existing shader initially. Do not replace the map stack,
add a framework or change backend/schema/generation.

A controlled warm baseline probe (`completed-render-cost.json`) calls gl.finish
before timing the copy: full1440×1000 completed-render call0.3ms then copy1545.8ms;
720×500 render24.5ms/copy382.8ms;360×250 render8.0ms/copy79.8ms. These single software
ANGLE/Vulkan SwiftShader samples support removing the forced composition copy.
They do not establish presented FPS or hardware performance; a sync measurement
can include driver behavior and must not be generalized to every GPU.

Implementation, independent reassessment, per-view final evidence and regression
outcomes will be recorded after verified candidates. Keep all findings open until
their actual correction is demonstrated.

## Phase A — direct presentation, not yet accepted for performance

Luna implemented the bounded direct WebGL layer, exact circle-centered CSS bridge,
2048-side/2,097,152-pixel framebuffer bounds (floored dimensions with actual
per-axis viewport mapping), RAF-coalesced pointer movement and guarded180ms idle
refinement. The existing shader and recorded inputs remain unchanged. Before a
return thumbnail copy, the renderer is forced to refresh its unpreserved drawing
buffer; displayed cached pixels cannot be assumed readable later.

The first actual browser run passed its functional assertions but failed its final
source-hash freeze check because a late builder refinement changed code during the
run. It is not clean acceptance evidence. The frozen rerun at
`phase-a/native-layer-final/report.json` passes: zero ordinary/drag WebGL→2D copies,
only one128px return capture, pointer-through input, same permanent/renderer canvases,
Surface/focus/System/campaign hiding, DPR2 buffer1737×1206 and actual context-loss
Surface fallback. No page errors or changed campaign records.

`phase-a/coherent/report.json` also passes zero duplicate detail requests, direct
Orbit stability/controls, exact System return and cold/held campaign cancellation.
However, warm entry measured4.015s, worse than the prior2.203s sample. The native
layer test's20-step trusted mouse drag plus900ms wait took9.205s, with main-thread
RAF median16.7ms/max433.3ms. Removing explicit copies is therefore not sufficient
performance acceptance. These scheduling/API samples do not establish presented
FPS. A bounded diagnosis is tracing compositing and entry render duplication before
another implementation correction. No unrelated cosmetic fix is substituted for
this unresolved motion issue.

## Measured motion correction and rejected quality tradeoff

The bounded high diagnosis used a screenshot-free Chromium trace at frozen PhaseA
source. All20 trusted drag events stayed720×500 at requested scale.5: no refinement
between drag steps occurred. Median browser EventLatency was431.41ms (417.86–463.48),
while the native render call took0.1ms. `LayerTreeHost::DoUpdateLayers` waited397.32ms
median wall/7.51ms threadCPU. This is real browser input/presentation delay, not
merely serial automation overhead or demonstrated expensive application JavaScript.
Warm entry rendered an identical1440×1000 pose twice, with1.609s and1.793s layer waits;
its probe entry took3.664s. Raw trace/report/derived summary are retained under
`phase-a/trusted-motion-trace/`. Shader rewriting was not supported by this evidence.

Sol medium corrected successful forward-bridge cache retention and added a
session-only measured output budget, trained after two RAFs with context guards.
The first adaptive candidate was fast (.707s entry,1.694s20-step drag including a
fixed.9s wait) but allowed a156×108 full-viewport buffer and visibly blurred globe.
Root rejected that candidate; the screenshot and trace remain under
`motion-correction/`. Speed did not excuse lost map readability.

The revised profile uses robust recent throughput and bounded recovery, rejects
changed authorization/map record/style/overlay/viewport/DPR/presentation generations,
and imposes physical short-side detail floors160px while moving/450px stable,
capped by the original requested quality. Fast presentations retain normal output;
there is no saved campaign preference or hardware-driver-name detection. The
existing shader, sun, relief, emission, coordinates and picking remain unchanged.

`motion-balanced/summary.json` records the revised frozen-source results:20 actual
trusted drag event completions median76.45ms (66.86–99.17), versus431.41ms in PhaseA;
layer-update median41.56ms. The full20-step drag plus fixed.9s wait took2.312s. Warm
entry took.726s with exactly one arrival native render. Requested quality adapts
from moving230×160 upward; the stable buffer is648×450 in this software fixture.
No browser errors or source changes occurred. These are browser completion samples,
not physical-display FPS or production benchmarks.

The same independent critic inspected the actual1440×1000 revised Orbit still.
Coastlines, terrain bands, mountain belt and principal rivers remain interpretable;
no new major planet defect was established. It retained minor interior softness
and stair steps along the high-contrast silhouette. D14 records that edge finish
finding for correction/reassessment; no atmospheric halo or invented terrain
should hide it. This does not close D01–D12 or establish full motion fluidity.

PhaseB now addresses the per-view information/interaction ledger with Luna as the
primary builder. Final combined screenshots, motion, functional regressions and
same-critic reassessment are required before delivery.

## UI candidate, keyboard correction and replacement review

Luna's UI candidate passed targeted Node checks but was not accepted from those
checks alone. The first UI contrast probe sampled a detached name element after
panel replacement: its computed colors were empty and the helper reported1:1.
Actual live white-on-navy contrast was11.43:1. Sol medium corrected the observer
with reconnect-aware sampling without lowering any contrast threshold.

That investigation demonstrated a real new finding D15 (medium): incidental
celestial-panel redraws discarded the focused heading/Return button. Bounded
DOM reuse for unchanged authorized record/context fixes it; hiding clears its key.
A separate test setup incorrectly expected night lift at4.2R after Locate and an
exact named return. Recenter correctly preserves scale. The test now resets and
zooms with real controls into useful~1.70R; physical far-night behavior is retained.
No blanket illumination floor or shader rewrite was added to pass that test.

`candidate/view-quality/report.json` passes both themes, normal/selected/hover
control contrast (minimum6.668:1; selected name11.429/meta9.906), focus heading→Tab→
Return and viewport-resize retention, complete saved-camera return, focused
ancestry/hidden irrelevant controls, useful1.701389R night lift.597036, and5206
changed canvas pixels for actual province hover. No errors, changed records or
source hashes. Source-matched full normal-motion20-step journey in
`candidate/journey/` completes at~71seconds including pauses/captures with no errors
or changed records. This is not evidence that every visual issue is resolved.

The environment restarted and prior agents became unavailable. A replacement
Sol 6.1 medium critic first inspected all20 fresh full screenshots independently,
with no prior verdicts or implementation discussion, then received the behavioral
evidence above. This replacement was required by environment lifecycle, not by an
unfavorable verdict. All earlier D findings remain retained. The new assessment
explicitly rejects screenshot-based fluidity, accessibility-certification or
commercial-parity claims and identifies remaining issues:

| ID | Severity / view | Retained concrete finding / next correction |
| --- | --- | --- |
| C01 | High / all | Parent/current scope is still a tiny low-contrast breadcrumb. Make the existing persistent named level ladder prominent with clear current/parent states and practical targets, without losing map area. |
| C02 | High / Galactic | The new heading says regions contain sectors, but Hearth/Cinder dominate while Kestrel Reach is secondary. Actual region→sector→system grouping is required; changed caption alone is insufficient. |
| C03 | Medium / common controls | Tiny same-weight rectangles flatten hierarchy. Group navigation/mode and cartography controls, increase important supporting type/contrast and distinguish primary/disabled controls; retain tint and sharp corners. |
| C04 | Medium / Universe | Origin and selected-destination prose still crowd markers. Reserve stable annotation space, reduce repeated prose and keep an explicit atlas/schematic cue. |
| C05 | Medium / System | Repeated caveats, opaque System D values and remote offscreen-body status obscure framing. Name camera zoom meaning and put full-system recovery/count by selection; unsupported-action reasons require an actual test. |
| C06 | Medium / Orbit | Mode/annotation/navigation controls mix in one row. Group them and expose automatic analytical-lighting status clearly; retain physical illumination records. |
| C07 | Medium / Surface | Hover/selected/entry emphasis is ambiguous. Distinguish preview versus selected borders/names and entry annotation; retain minimap and honest world-width scale. A stable north cue is minor polish. |
| C08 | Medium / Moon | Identically named moon records need their actual parent in the title/list/detail, not solely a tiny breadcrumb. Unknown surface/positions must stay unknown. |
| C09 | Medium / Star/Moon | Keep consistent prominent parent navigation as well as the source-specific return; soften opaque UI record blocks with readable tint. No invented activity/terrain. |
| C10 | Low / utilities | Detached Forces control and indistinct facility glyph semantics need clearer grouping/categories using only actual public records. |
| C11 | Low / Orbit | Interior softness and silhouette aliasing remain measured software-profile tradeoffs; an edge polish must not invent atmospheric/terrain detail. |

Actual root inspection also catches a regression: the focus-control visibility
helper unhides Terrain/Natural labels in Galactic/Sector on later redraws. Restore
level-aware hiding rather than leaving irrelevant disabled tools visible. The
existing eight-planet fictional fixture is now part of review: baseline tracked
04a405c JS/CSS/HTML was served read-only against the same saved records at4220,
with eight located bodies and three hidden labels. Captures/report under
`rich-baseline/`; no new campaign data was created for this test.


## Final correction record — 6 November

The retained C findings above were addressed together: a persistent named scope
ladder with 44px targets; actual Region→Sector→System containment; grouped view,
cartography and camera controls; separate destination/origin annotation; named
relative system zoom and adjacent full-system recovery; explicit analytical-light
status; dashed province hover versus solid selection; moon parent identity;
source-named return and tinted reading panels; and a labelled Military layers
control. Inward-only globe-edge coverage softens silhouette aliasing without an
atmosphere, lighting floor or replacement terrain.

Additional demonstrated defects: D15 rebuilt celestial panels discarded keyboard
focus on incidental redraw; unchanged authorized content now retains its DOM.
D16 rich-fixture headings/breadcrumbs incorrectly prefixed “The Reach”; they now
use the actual public Galaxy ancestor, unique known Galaxy, or honest generic
context. Hidden records do not contribute. Sector record counts distinguish
charted containment from all public records, including unlocated contacts;
missing arrays remain unknown rather than zero.

The first frozen final run passed all nine browser suites (information quality,
native globe lifecycle, eight-planet chart, coherent bridges, body return/private
session, universe/private context, navigation/resource continuity, desktop reflow,
night facilities) and thirteen targeted Node suites. Artifacts and exact public
source hashes are in `data/deep-critique/final/run-summary.json` and
`verified-source.json`. Tests include 1440×1000, 1280×720 and CSS150% desktop
controls; actual context loss; DPR2 limits; public/geometry ID separation; stale
campaign/logout work; historical read-only behavior; exact cameras/selection;
unchanged records and no uncaught errors in exercised journeys. These are scoped
browser observations, not proof that every game mechanic or deployment is secure.

Final root probing found D17: keyboard Enter on System Focus returned focus to
BODY during its animation. The same incidental-reparenting cause was localized
without changing the camera or action order. The regression observes intermediate
animation frames and keyboard Tab/Space full-system recovery. Independent richer
chart review also rejected the assertion that eight label rectangles meant eight
readable names: two central labels overlapped/truncated. The first rich “all named”
claim is withdrawn; actual full-name noncollision checks replace that weak gate.

The earlier environment lifecycle made the prior critic unavailable. A fresh
Sol medium critic first inspected current full screenshots without implementation
history or previous verdicts, retaining earlier adverse findings afterward.
This was not a search for a favorable verdict. No additional numerical score is
used as an acceptance gate.

Backend stress gate: the retained 10,000-turn/10,001-snapshot fixture passed in
257.97 seconds; all 17 recorded backend source hashes still match. No backend,
generation, schema, simulation, history, private campaign data or character branch
was changed. Do not rerun costly simulation stress solely for these UI changes.

Integration: keep the existing map canvas, recorded geography and public IDs;
the added native transparent globe is presentation-only. Surface changes are a
small optional hovered-province input/stroke, not regenerated cartography.
Characters remain an existing management integration destination; no relationship
model/screens were modified. Unrecovered cloud cartography/database has not been
recovered or replaced. Orbital structures still require actual public records;
no station, travel, orbit or time mechanics are invented by this presentation.

The final independent screenshot review retained four further concrete issues:
rich-chart full names collided/truncated (medium); Universe origin text collided
with a parent bracket heading (medium); reduced-motion Surface kept the native
globe visible after exit (material lifecycle defect); and CSS150% desktop charts
clipped their actionable system cards (medium/high). These were not waived by
passing unit checks. The nine-suite run above is an intermediate verified source,
not the final post-correction hash. One bounded Sol high layout diagnosis found
that fixed strategic vertical offsets placed the first Open system below the
available chart; min zoom1 prevented reset/fit recovery. The next correction must
adapt layout to measured space and test actual chart content, not only controls.

## Final localized resolutions

The same critic reassessed the corrected richer fit/focus screenshots in both
themes: eight full body names are now readable, labels avoid each other/body
symbols, and Focus has a named selected target plus explicit full-system
recovery. Residual low-severity inner-body/leader attachment ambiguity remains
where the recorded projection overlaps bodies; use the named chooser/Focus.
No positions were displaced for appearance. The unchecked overlapping compact
fallback was removed and text measurement now matches13px semibold rendering.

Reduced motion bypassed the old fade cleanup; settled Surface now explicitly
clears/hides the native globe even without a fade. Normal/reduced exit and hover
checks assert actual layer visibility. The critic inspected the corrected Surface
and confirmed the sphere is gone. Universe origin annotations now sit beside the
markers; actual text-rectangle checks and both-theme captures verify separation
from containment headings. A final local tooltip issue at the entry anchor is
corrected using the actual marker bounds. A first nearby-only placement attempt
hid the tooltip; above/below-marker candidates now preserve visible, nonoverlapping
text and viewport/inspector constraints. The failed attempt remains recorded here.

One bounded Sol high diagnosis guided the short-shell correction. Existing
ResizeObserver measures actual shell CSS height and activates compact spacing,
retaining named levels/camera/primary actions while hiding the resource strip in
short mode. The schematic strategic layout budgets its full first card/action
inside the safe chart; repeated secondary headings are omitted there. Saved
coordinates and System vector projection do not change. The same critic inspected
all four corrected150% views and accepted closure of the clipping impediment:
complete Open system/unknown-contact contents visible, System selected body and
recovery remain clear, and Planet regains meaningful chart area. Actual clicks
then reached System at each tested viewport/zoom. Minor: dense inner projections
and very short-view glyph detail still favor selection/Focus for closer reading.

## Reference comparison record and limits

| Workflow / reference actually examined | Relevant strength / current gap | Implemented response and evidence | Comparative limit |
| --- | --- | --- | --- |
| Strategic return / Stellaris developer navigation/exploration notes | Stable context and connected known destinations; prior tiny breadcrumbs and generic returns obscured scope. | Named scope ladder; source-named exact-camera return; browser body/universe/navigation suites. | Text reference, not executed Stellaris or a matched screenshot task; no parity claim. |
| Cross-scale inspection / Endless Space2 manual and SinsII guides | Zoom changes information meaning and retains entity identity; redundant chrome and fixed-height cards previously obscured targets. | Grouped controls, focused identity, adjacent full-system recovery, visible short-layout destinations, native globe bridge; final reflow/journey. | Documentation examined; no physical orbital movement or continuous universal camera invented. |
| Known-space reading / Endless Sky official topology illustration | Restrained points/links reveal actual connectivity; decorative background previously competed with records. | Explicit containment and authorized links, subdued art, unknown/unlocated trays; final Galactic/Sector/Universe captures. | The reference has much greater information density and is not an equivalent whole-UI visual comparison. |
| Settlement economic diagnosis / Victoria3; character relationships / CK3 | Original broader brief names these task comparisons. | Existing management integration retained; this milestone tests map/record navigation, not new economy/relationship mechanics. | Neither commercial game nor equivalent economic/relationship task was executed here; those comparisons are not established by this map RC. |

No proprietary assets or new renderer/framework dependencies were imported. The
full research/source-access ledger remains in `universe-research-and-redesign.md`.

The same critic independently confirmed the corrected tooltip is fully legible
above ENTRY ANCHOR. It can slightly overlap the end of the Forge canvas name
while hovered; this remains a low-severity transient label tradeoff. Do not
claim universal label collision freedom. Body-label collision checks apply to
the tested System fit/focus arrangements, not arbitrary future chart density.

## Final source, browser and performance evidence

All13 targeted Node suites and all9 browser suites passed on frozen source under
`final/rc-qa/`, with no product source changes during that run. The final20-step
normal-motion recording then revealed a selected DESTINATION badge colliding
with its containment heading (step17); passing unselected-state checks had missed
this. Only `public/universe-view.js` placement changed afterward: destination is
right of the marker, origin left, with content bounds. Actual selected-Hearth
badge/name/marker/parent-heading rectangles now pass both themes in the full
coherent suite (`final/badge-fix/`). Follow-up Universe/private context and reflow
checks plus a fresh complete recording use the final source manifest; no unrelated
lighting/physics/backend test is represented as rerun after that local change.
Final exact hashes/verification: `final/final-source.json`,
`final/final-verification.json`. Earlier recording preserved separately; final
captures/video are under `final/journey/`.

Quiet screenshot-free trusted-input trace:
`final/performance/{report,chromium-trace,summary}.json`. Environment: Linux,
Chromium154.0.8037.57, software ANGLE/Vulkan SwiftShader,1440×1000. Twenty drag
completion samples: median80.3015ms,65.514–101.285ms; layer-update median40.2225ms.
Twenty moves plus fixed900ms wait:2.30993seconds. Warm System→Orbit entry:
0.95240seconds. Two648×450 native arrival draws were observed; the earlier balanced
candidate's single-draw result must not be repeated as this final run's count.
Compare PhaseA median431.41ms/3.664s warm entry above, not an unmeasured commercial
baseline. Stable output adapts to a450px short side in this software fixture;
fast devices may retain requested output, but hardware results are unverified.
These are browser-completion/presentation opportunities, not physical display FPS.

The independent critic sampled decoded frames from the actual normal-speed MP4
and the bridge trace. Navigation completes and settled Surface is clean, but the
recorded entry includes an approximately287ms progress gap/jump. This is a real
software-profile responsiveness/animation-quality limitation. The critic accepts
functional navigation with that disclosed limit, not premium/fluid motion or60fps.
No basis exists to promise a hardware run will fix it. Further quality claims need
actual hardware/browser evidence; increasing framebuffer work here would reinstate
the measured multi-second stalls, and the previously rejected blurry candidate
shows why reducing detail without bounds is also unacceptable.

The final MP4 is an uncropped1440×1000 actual capture, normal speed,20 chapters,
H.264 Main/yuv420p30fps, AAC silence and faststart; complete ffmpeg decode and moov
ordering are checked in `journey/video-verification.json`. No generated transition
frames. A workspace video path is not a publicly hosted phone URL, and no physical
phone playback is claimed. The critic inspected representative decoded frames,
not a continuously watched full video.

Coverage: actual Chromium mouse, touch and keyboard paths; dark/light; normal and
reduced motion;1440×1000,1280×720 and CSS150%; DPR2 bound; WebGL loss fallback;
stale campaign/logout/history contexts; same canvases and bounded resources.
WebKit executable is absent; native macOS Safari, physical devices, hardware GPU
performance, production operations/security/backups/recovery remain unverified.
The retained backend gate is not a new turn-preview/commit browser run.

Remaining minor/inherited limits: adaptive interior softness; crowded recorded
inner-body symbols/leader attachment; a transient hover tooltip can slightly cover
a settlement name; very short-view glyph detail is limited. Existing Surface
terrain/finite survey resolution is retained, not regenerated. Star art is
illustrative; detected moons have no recorded surface/position and remain neutral.
No fake content fills those gaps. No data recovery, deployment or whole-game
commercial comparison is established by this interface release candidate.

## Independent final verdict and per-view health

Sol6.1 medium's definitive review: scoped visual/interaction RC acceptable for the
exercised desktop Chromium workflows, conditional on the final local badge-change
regressions completing. No unresolved critical/major visual/navigation defect was
found in the examined evidence. The final local Universe/private-context and
reflow regressions both passed; final recording is the same frozen product source.
The critic explicitly withholds a premium/fluid-motion endorsement. Its evidence
included all20 journey screenshots, correction captures, observed behavior reports,
representative decoded video frames and actual reference/access ledger. Prior
adverse findings, rejected candidates and remaining limits are retained above.

| Journey step(s) | Actual state/task | General health and remaining limit |
| --- | --- | --- |
| 01,16,17 | Universe entry, outward return, selected sector | Pass: origin/destination/unknown context and visible descent; final local badge collision corrected. Schematic, not universal astronomical coordinates. |
| 02 | Galactic containment | Pass: actual Region→Sector→System hierarchy; compact entry card usable at CSS150%. Sparse public records remain sparse. |
| 03,18,19 | Sector, opened sector, light theme | Pass: recorded systems and unlocated tray separated; actual card click enters System. |
| 04,05,13,15,20 | System fit, Focus, return, zoom-out arrival, light state | Pass: selected identity/actions, named framing and exact return. Rich fit tested separately with8 full names. Extreme zoom in20 is not fit; hidden-label counts/recovery explicit. Minor inner-body leader ambiguity. |
| 06,09,10,14 | Orbit entry, celestial return, close view, restored orbit | Pass navigation/identity/lighting; physical night preserved and close analytical lift shown. Software motion pauses/interior softness remain. |
| 07 | Star focus | Pass: known record, illustrative disc and named origin return; no invented flare/activity values. |
| 08 | Moon contact | Pass: parent identity, clear selected row/return; unrecorded terrain/position remain unknown. |
| 11,12 | Surface descent and pan | Pass: no stale sphere, actual province hover/selection and entry anchor/minimap; minor transient tooltip/settlement-name overlap. |

Continuation: validate representative hardware GPU frame pacing and actual WebKit/
macOS Safari before broader motion/browser claims; test higher real chart density
without fabricating player records; integrate unrecovered cartography via existing
optional renderer inputs. Do not claim deployment, operational security or backup
verification. This milestone is an interface release candidate with explicit
software-renderer limits, not complete-game/commercial parity.
