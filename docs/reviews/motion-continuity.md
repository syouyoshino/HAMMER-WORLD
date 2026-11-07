# Motion correction — 6–7 November 2026

Baseline `f547851` on `map-generation`. The previous UI RC expressly withheld
fluid-motion acceptance. The user requested that motion be fixed. This milestone
is limited to render scheduling, redundant work and camera handoffs, preserving
recorded geography/IDs/sun/history/authentication and existing input/cameras.

## Fresh baseline and causal probes

Actual desktop Chromium154/Linux software ANGLE/Vulkan SwiftShader,1440×1000.
Fresh normal-motion20-step screenshots/native recording and raw trusted-input
trace: `data/motion-fix/baseline/`. No page errors, changed records or source edits.
Median trusted-drag browser completion75.83ms (58.75–164.76); layer update39.74ms.
Warm System→Orbit0.947s, two648×450 native arrival draws. The fresh recording
exposes an initial398.9ms bridge gap with progress0→.994: animation time was spent
publishing the prepared frame, not visibly moving it. API enqueue time is not GPU
completion or physical-display FPS.

One bounded Sol high diagnosis was revised against causal A/B evidence. The
initial full-viewport2D-backdrop hypothesis was explicitly withdrawn:

| Probe (temporary instrumentation only) | Median browser drag / layer update | Implication |
| --- | --- | --- |
| Fresh unchanged baseline |75.83 /39.74ms | Motion is below target. |
| Freeze background drawing and permanent map clearing during drag |74.50 /41.69ms | Backdrop invalidation is not the demonstrated main cause. Reject the proposed new canvas/SVG background rewrite. |
| Freeze native GL draws during drag |41.49 /6.38ms | Native GPU publication dominates the excess cost. This is a diagnostic, never an acceptable frozen-world implementation. |
| Pin moving native output230×160 |71.83 /32.90ms | Resizing contributes, but pinning alone does not fix motion. No lower detail floor is authorized to conceal lag. |

Probes remain under `data/motion-fix/diagnostic-*`; none change campaign data or
constitute delivered visual evidence. FreezeGL mis-trains the output profile and
therefore its subsequent entry timing is not a valid product comparison. The
~41ms frozen-GL browser sample also establishes a harness/presentation floor;
requiring an arbitrary sub40ms number would be unsupported.

Full render-input instrumentation identifies the duplicate arrival precisely:
same revision, pose, output dimensions, sun and viewport, but safe rectangle bottom
changes908.609→891.219CSSpx. `renderMapHeading` writes a short generic planet footer
after `renderOrbitControl` wrote its long Orbit footer. Preparation measures the
short layout; final drawing measures the long layout, causing a second valid but
avoidable native draw. Fix chrome ordering/ownership; do not ignore differing keys.

Acceptance requires changed motion: actual intermediate bridge movement after
presentation, no large initial progress jump, material native-work/drag reduction,
retained detail and dynamic sky, then lifecycle/context/resource regression checks
and an independent motion review. Passing still-image review is insufficient.

Additional isolated shader/context probes did not meet the motion gate:
no-MSAA77.02/38.83ms; conservative sphere-bounds scissor73.87/33.25ms;
decode-gamma bypass105.51/62.65ms; all transfer-gamma bypass91.93/45.61ms
(browser/layer medians). Do not ship these bypasses or claim their timing proves
mathematical color equivalence. Gamma probes served immutable baseline app/orbit/
CSS bytes through browser routing so concurrent candidate edits could not alter
the measured app. An initial route-handler signature error prevented page load;
that failed harness run is not an application or performance result. Corrected
runs above completed with unchanged served-source hashes and no page errors.

Luna's first bounded clock/footer/pinned-tier candidate passed Node checks but its
browser motion probe captured no bridge frames. That attempt is not motion
acceptance. Localized Sol medium escalation checks both instrumentation setup and
actual animation rather than assuming an empty trace means a smooth transition.

## Verified timing correction and bounded moving filter

Sol medium corrected the hook race, then actual browser traces exposed remaining
footer ownership: loading redraws re-showed the transient status while destination
preparation waited. The final owner hides that status in the prepared phase while
retaining the input lock, and builds the facility texture before settling its label.
One strict native key now serves preparation and arrival; no epsilon key comparison.
The bridge publishes the exact source pose, waits guarded publication opportunities,
and then runs its full420ms smoothstep curve. Runtime callback-interleaving tests
prove an old publication/animation callback cannot cancel a replacement ticket.
Every preparation and animation RAF has a tracked owner; moving tiers survive a
held-pointer pause and refine once on idle.

Candidate B: one648×450 arrival render, stable rectangle,28 bridge samples with
small initial progress. Its55.09ms tool-RPC median was initially mislabeled as
browser completion in a progress update. Correction: actual Chromium EventLatency
median67.81ms, layer31.55ms. The fresh unchanged baseline is75.83/39.74ms. Do not mix
RPC acknowledgement, native API calls, browser completion and physical-display FPS.

The unrestricted single-tap diagnostic let adaptive output grow from353×245 to
607×421 while latency stayed similar. This is a confound, not evidence that kernel
work is cheap. At fixed230×160, one diagnostic tap reduced layer cost32.90→17.44ms.
The diagnostic is not shipped. A bounded Sol high review approved maximum4 centered
taps only for slow-device motion and modest longitudinal anisotropy. The exact8-tap
path remains for idle/fast-device output, demanding footprints, polar blending and
missing gradient support. Centered quadrature preserves the original filter interval;
pole means, gamma, relief limits, sun, emission and geometry are retained. A16ms
moving work budget preserves the160px floor; idle retains80ms/450px. Only full-kernel
observations train throughput, so faster moving frames cannot inflate idle quality.
Existing test hooks forward the added optional render argument instead of silently
testing the old kernel.

Real fixed230×160 GPU comparisons against the committed renderer cover16 terrain/
province cases: coast, equator, both poles, longitude seam, night and analytical
lighting. Idle and restored pixels are byte-identical; alpha coverage is identical.
Moving p99 channel error≤1byte, maximum8 in rare channels, worst mean0.0498byte.
Median isolated completion/readback work27.35→14.30ms. These are not display FPS.
Candidate C end-to-end:20 moving230×160 frames, one648×450 idle refinement; browser
completion57.15ms, layer21.41ms, warm arrival0.952s with one native draw. Coherent,
native lifecycle, navigation and night-light regressions pass without record changes
or page errors. Evidence: `data/motion-fix/candidate-{b,c}/`.

## Additional demonstrated fade defect

A dedicated actual opacity/trace probe rejects stopping at candidate C: Orbit→
Surface exposes only3 intermediate samples, with a370ms stall; Surface→Orbit only2,
including a418ms publication gap and a jump to complete. Both clocks begin before
preparation and the fade repaints the full map/composite on every tick. Applying
opacity independently to native globe and backdrop also gives nested alpha rather
than a flattened scene.

One bounded high review approves a permanent pointer-through presentation wrapper
containing the existing GL child plus one temporary prepared backdrop. Draw each
surface once, publish the near-endpoint composite while the clock is pending, then
animate only group opacity for420ms. No GL render, map clear, Surface draw or backdrop
redraw belongs inside opacity ticks. Track identity/context/input/viewport guards,
settle on interruption, and release the temporary canvas after the atomic final draw.
This preserves the permanent input canvas and existing renderer/world contracts.
The next candidate needs actual opacity/trace evidence and independent motion review;
C's functional success does not establish completion of the motion request.

## Independent motion comparison and retained major finding

An environment turn made the first motion-review agent unavailable before any
verdict. Its replacement received only anonymous actual uncropped A/B MP4s, with
no origins, implementation history or desired winner. After its initial media-only
assessment, root disclosed A as D and B as the unchanged baseline, then supplied
traces and workflow facts. This is not a search for a favorable verdict.

The critic inspected full-runtime1-second samples, dense100–200ms handoff/drag
sequences, native-resolution spot checks and successive decoded-frame differences.
A distributes the visible changes over planet-enter and Orbit/Surface handoffs;
B concentrates them into abrupt changes. This measures captured visual change,
not rendered/display FPS. A briefly overlays divergent globe/map geography during
crossfade; retain that as minor polish. The initial apparent vertical-chrome shift
was explicitly withdrawn after native-resolution checks showed it was a montage
reading artifact; do not report it as a game defect.

The critic BLOCKED the motion RC on one major retained route: returning from
System to a saved close Orbit at A39.5–42.63seconds. The source System scene remains
under a Surface heading while loading, then jumps to the globe. B has the same
defect; intentional recording dwell does not explain the actual loading interval.
D's other improvements and successful functional tests do not waive this finding.

A bounded Sol high integration review traced this to `completeOrbitRestore`, which
directly enables Orbit after detail arrives instead of using the prepared bridge.
The correction carries a cloned saved camera and captured System source in the
existing enter ticket, reuses authorized bounded raw detail only against the fresh
map reference, and prepares the native target at the exact saved pose. It retains
the normal authoritative map request; no map record is fabricated from cache.
Pending chrome consistently says Opening saved orbit. Overlay replacement carries
the same source/intent with the new request, while older callbacks are rejected.
Wrong campaign/snapshot/planet/survey responses are rejected before map assignment
or cache attachment, with a truthful System fallback on map failure.

Saved-route tests cover valid cached normal/reduced motion with zero target-detail
requests and exact noncanonical camera; uncached held detail and population-overlay
replacement; stale release; mismatched snapshot; cancellation; detail503 fallback;
and actual native bridge endpoint. The uncached route records28 bridge poses,
25positive, first progress.003589, maximum moving gap17ms and final1. A first cache
counter mistakenly included another planet's preview request; it was restricted to
the target request. Test cleanup now ignores the already-aborted preview route
handler after all assertions rather than treating its closed-page fetch as an app
error. These harness corrections do not lower route or authority assertions.

## Final independent outcome — 7 November

The same motion critic inspected the corrected E return with100ms full-frame
samples38.6–42.6seconds and every decoded frame40.1–41.0, plus adjacent handoffs.
At~40.0s the heading truthfully says Opening saved orbit;~40.30–40.83 shows multiple
intermediate scales/positions;~40.87–40.90 reaches stable Orbit. The earlier~3s
mismatch and direct pop are resolved. It independently read progress0→1/source and
destination geometry plus exact-camera/cached/reduced/cancel results. Its final
verdict: scoped motion RC passes for app SHA `f1d38db7`; no critical or major
remaining issue established in the reviewed journey. Minor globe/map dissolve
ghosting and software scheduling limits remain. The review was dense sampled
inspection, not continuously watched playback, render-FPS certification or hardware
validation. Its earlier blocked verdict is retained above.

Final evidence: `data/motion-fix/final-e/verification.json` and `source.json` bind
14 targeted Node suites, seven fresh final browser stages (quiet latency, coherent
bridges, native lifecycle, navigation, private body-focus, private Universe and
actual fades), saved cached/error/cancel/reduced tests and uncached replacement
coverage to the frozen source. Actual20-step normal-motion capture has no page
errors or changed campaign records. Separate GPU quality evidence applies to the
unchanged shader hash `7cad2d88`; D's night and Universe-motion lifecycle checks
also remain retained. A missing ffmpeg cache caused one earlier harness launch
failure before any page opened; installed system ffmpeg was reused without a new
dependency or source change, and that suite then passed.

| Motion workflow | Final observed health |
| --- | --- |
| Fresh System→Orbit | Pass: published source pose,420ms smoothstep, one native arrival draw; no clock consumed by initial publication. |
| Saved System→Orbit (steps13→14) | Pass: truthful pending context, normal/reduced exact noncanonical pose, cached target detail0requests, prepared handoff. Uncached/replacement/failure paths covered separately. |
| Orbit→Surface and Surface→Orbit | Pass:17intermediate samples each in final run, maximum moving gaps22.9/23.5ms; zero native render/map clear/backdrop draw during opacity interiors. |
| Orbit dragging/refinement | Improved:20changing230×160 moving frames then one648×450 full-quality idle refinement; no resolution-floor reduction. Idle/restored GPU pixels match original in16tested cases. |
| Surface pan and strategic charts | Pass in exercised journey; source camera/context preserved. Universe scheduling/menus/visibility/reduced motion and listener bounds remain tested. |
| Star/moon inspection and return | Pass: exact source context, truthful unknowns; no invented coordinates or terrain. |

Final quiet software-Chromium154/Linux measurement: browser EventLatency median
59.94ms (56.27–94.56), layer-update median22.29ms, versus baseline75.83/39.74ms.
Warm fresh entry1.005s, one648×450 native draw. Its restored full animation is not
shortened to manufacture a better response-time number. This is~21% lower browser
completion latency and~44% lower layer cost in this fixture, not measured display
FPS. C/D repeat results and the distinction from RPC time are retained above.

The marked D fade trace proves incoming298.906ms native publication completes
before visible movement; largest layer update within visible fade4.595ms. The
final E fade regression retains zero interior raster work and small pose gaps.
Preparation still takes time; it no longer becomes a large jump inside the motion.

Final MP4:63.02seconds,5,658,711bytes,20chapters,1440×1000,H.264 Main/yuv420p30fps,
AAC silence, faststart and complete decode verified. It is spatially uncropped and
normal speed, with no synthesized motion frames. It starts one second before the
first scoped Universe state; raw pre-roll (startup/campaign selection/initial
renderer) is retained separately and is not a cold-start performance benchmark.
Artifact: `data/motion-fix/final-e/journey/hammer-world-transitions.mp4`. Workspace
artifact availability is not a publicly hosted phone URL or physical-phone test.

Limits: one fictional fixture/software GPU, sampled media review, no production
scale/hardware-WebKit/native Safari/phone verification or commercial/Google Earth
parity claim. The explicit strategic lenses remain distinct projections; minor
cross-dissolve geography ghosting is not a continuous3Dterrain mesh. Missing cloud
cartography/database has not been recovered, regenerated or overwritten. Backend,
authority/history, physical generation, persistent IDs and character branch are
unchanged; the retained10,000-turn backend source gate still matches. No merge,
deployment or operational-security/backups/recovery certification is implied.

Final diff review found one error-path ownership gap after the accepted normal
recording: the retained System context still had its old request number following
a failed saved return. One assignment now rebinds that retained context, so later
pan/Focus changes can be saved. The actual wrong-snapshot case pans/focuses, retries
Planet, returns System and asserts the exact adjusted camera. It and cached normal/
reduced/cancel/error cases pass on app SHA `404da876`. Removing that sole assignment
mechanically reproduces the accepted recording's `f1d38db7` hash; every other public
file matches. `final-e/delivery-source.json` records this distinction. The same
critic confirms scoped acceptance carries forward to404da876; no normal movement,
renderer or easing changed, and minor/evidence limits remain.


## Verified delivery

Implementation/tests/review commit `7efcfd5` pushed successfully to
`origin/map-generation` on7 November2026. Final app hash404da876 is independently
accepted with the one tested error-only correction documented above. Source and
video manifests remain under `data/motion-fix/final-e/`; generated media, runtime
records, private contexts and databases are excluded from Git. No product edits
followed final verification. No merge, deployment or data reset.
