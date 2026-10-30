# Terrain lighting and desktop reflow — 30 October 2026

Continuation from `1e69533` on `map-generation`, addressing the remaining interface
finish issues. This is an interface release candidate, not a deployment or an
optical/Google Earth/commercial-game fidelity claim. Existing explicit-radius V11
creation remains unchanged, with no Earth-size default.

## Scope and authority

All changes are frontend presentation. The 17 backend modules, generator outputs,
physical radii, immutable detail assets, entity/province/feature IDs, material masks,
turn rules and historical records remain unchanged. The resumed workspace contained
local QA records; restoring their loopback servers is not recovery of the unavailable
original cloud cartography or campaign database. No real values were manufactured.

Fresh actual-browser baselines cover the same persisted 100 km, 6,371 km and
100,000 km radius demos and water/lava/hydrocarbon/ice fixtures. Matched cameras,
full aspect ratios and ordinary desktop viewports were retained. Header captures
also exercise 1280×720 at CSS100/150/200%; these are not native browser zoom tests.

## Rendering decisions

Native V10/V11 terrain Orbit textures may carry one optional internal relief canvas.
It derives signed east/north slopes from saved elevations, excludes ocean/liquid
samples and liquid neighbors, smooths only that derived lighting field with a fixed
3×3 stencil, and tapers toward the poles. Gain is fixed cartographic exaggeration;
recorded heights have no approved metre interpretation. Nothing regenerates or
moves terrain, and picking still uses the existing recorded fields/transforms.

The existing globe renderer adds one persistent texture, uploaded alongside albedo
only when its source revision changes. Missing relief uses a neutral 1×1 texture.
Slopes remain linear data; longitude sampling wraps and each sample uses its own
world tangent basis. Existing pole filtering suppresses undefined polar directions.
The saved star direction still lights the globe. Geometric intersection, silhouette,
limb, ambient illumination and terminator gating remain intact. Statistical overlays
retain their prior treatment. Palette changes reuse the derived relief canvas.

The source tangent cap is approximately25°; mixed-longitude filtering has a
conservative angular bound below30°. This is not physical terrain displacement. The dry background cache adds at most5 MiB per
immutable cached detail; temporary filters remain bounded to the validated detail
dimensions. A longitude-angle recurrence preserves all eight sample bases while
reducing repeated trigonometry. A uniform skips relief work for neutral sources.
Liquid source samples are neutral, but filtering can blend adjoining land relief
into shoreline texels; perfectly flat shading for every liquid fragment is not
claimed. There are no new rings, flare events, physical heights or resource values.
Hydrocarbon interiors use stable warm brown, with subtle mask-depth variation and
a sharper opacity transition around the mask boundary. The legend uses the same
body tone. Ice precedence and canonical material-cell identities remain intact.

Wet surface shading has a modest contrast bound. Dry background and recorded crater
derivatives stay separate through illumination: background contrast has an independent
±4% budget and recorded crater contrast an independent ±8% budget. Ice uses quiet
background shading. Dry Orbit similarly uses a crater-subtracted background and
adds analytic crater derivatives once. Liquid-aware Gaussian passes and a separate
Orbit background cache prevent lake heights leaking into adjacent land slopes.
The unmasked filter path preserves its previous accumulation order. Orbital ice
albedo resets both chart-lighting components to neutral. A narrow `.45` native-cell
cartographic shore stroke follows recorded elevation crossings. It is contour ink,
not area antialiasing, topology repair or proof that a coast moved by less than half
a cell. Saved square islands, stepped geometry and categorical material regions
remain recognizable limitations of the fixed overview asset.

## Layout decisions

The command bar, resources, chart title/tools, breadcrumbs and historical banner now
share natural document flow. Their actual height positions secondary Forces UI.
The backdrop fills its containing shell, avoiding viewport-unit oversizing at CSS
zoom. DOM obstacles, pointer/drag and overview coordinates convert screen pixels to
local canvas coordinates; at ordinary zoom the factor is one.

Floating workspace/dialog/menu bounds use the shell's real size. Management content
scrolls without stranding Map/Close. Existing zoom-minus/readout/plus/Recenter nodes
form one wrapping unit. Caption and legend fit their content; the bottom status line
remains clear. No default window arrangement, authentication storage or campaign-state
preference was introduced. Light/dark and the existing character-screen integration
remain available; the character branch is untouched.

## Independent critique loop

Luna built bounded candidates. The required Sol medium escalations corrected a
remaining mature-toolbar collision, the workspace's viewport-unit/minimum-height
stranding, and a per-frame relief upload plus mismatched slope encoding caught by
root QA. Sol high reviewed the renderer contract and inspected the corrected source;
its precise numeric/filtering/shore limitations are retained above.

A fresh independent Sol medium critic first received six anonymous, uncropped image
pairs without implementation discussion, origins, previous verdicts or a desired
winner. Pair sizes/information loads were equivalent; available map space caused a
small globe-radius difference, explicitly disclosed. It preferred the new medium
globe, qualified the new lava globe, found surface-material comparisons uncertain,
and strongly preferred the new enlarged-zoom headers. No screenshot score was used.

Findings retained through correction:

- F1: New relief improved form but was uniformly wrinkled. Added lighting-only
  smoothing, reduced gain and stronger polar suppression. Thin/faint recorded rivers
  remain a minor overview limitation; their paths are not invented or amplified.
- F2: Coastal steps and hard material regions persist in the recorded overview.
  The critic classified these as a documented geometry-preservation limitation,
  rather than authority to alter old data. Shore ink is not claimed to solve them.
- F3: Polar fans and dark looped emboss in the new barren globe required correction;
  the derived lighting filter/gain/taper reduces it. The later structural separation
  of background and crater contributions further quiets those false channel cues.
- F4: Dark frozen-world shadows could resemble liquid boundaries. Two contrast/filter revisions were insufficient, and the same critic retained
  this finding. One bounded Sol high diagnosis identified nonlinear recombination of
  background and crater light. The structural split above, stable hydrocarbon tone
  and matched legend resolve actual three-lake identification without changing masks.
- F5: Header overlap/offscreen tools were resolved; the residual split zoom control
  was corrected by grouping the existing controls as one unit.
- F6: Header overlap was resolved; compact readouts preserve more map space at high
  CSS zoom. Native dropdown options remain available when the selected text truncates.

Intended workflows and execution reports were supplied separately after the initial
blind assessment. The critic treats them as bounded supplied evidence, not interaction
proof from screenshots or its own re-execution. The same critic accepts the scoped geometry-preserving strategic overview/material
location and desktop reflow tasks, with no major visual blocker in the reviewed
views. F4 is accepted on a fresh view centered through the real feature catalogue
on a saved hydrocarbon lake:3821 liquid-mask samples are visible, and the two
unselected neighboring brown bodies are also distinct. The original default-camera
view did not establish material-in-view; arbitrary globe orientations remain untested.
F5 grouping and the header overlap are resolved. F1 repetitive wet-world wrinkling,
F2 stepped/category geometry and faint rivers, F3 synthetic grooves/bowls and F6
limited map space at CSS200% remain minor-to-moderate presentation debt. This accepts
the stated strategic tasks, not naturalistic terrain form or perfect finish.

Review also found a new segmented bright globe rim after shader optimization. A
finite helper-lane ray path followed by the original coverage rejection removes
undefined edge derivatives. Actual same-camera lava framebuffer comparison has
1276→0 bright covered pixels,365934 covered pixels on both sides, every alpha byte
identical and no GL error. The same critic verified the clean fresh silhouettes.
No decorative edge/halo hides the regression.

## Reference and evidence limits

This increment compares the actual previous release candidate against the same
recorded worlds and workflows. Earlier examined Cesium/Earth Enterprise/Lutz map
references remain recorded in `physical-scale-and-body-focus.md`; no new optical
imagery, live Google Earth, Victoria3, CK3 or Stellaris comparison was performed.
No proprietary art or new external code was incorporated.

Runtime images, anonymous key/pairs, rejected candidates, reports and logs stay
ignored under `data/terrain-finish/` and workspace scratch. Credentials, private
records and databases are excluded from Git. Final verification/performance/browser results follow below; delivery is recorded
after final diff review and push.

## Final verification and performance

- Final source matches the artifacts for `browser_desktop_reflow.py`,
  `browser_body_focus.py`, `browser_body_focus_resources.py` and both feature-probe
  paths of `browser_orbit_relief.py`. Body navigation, exact origin context return,
  actual other-planet drag/zoom, history read-only behavior, protected logout and
  campaign identity clearing pass. Every exercised page reports no uncaught error.
- Desktop1280×720 at CSS100/150/200% and1920×1080 at100% pass visible-control bounds,
  nonoverlap, breadcrumbs below tools, grouped zoom controls, map drag and
  Economy→Map. Dialog/inspector close and focused Back remain reachable. This is
  CSS zoom coverage; native browser zoom is not claimed.
- Actual WebGL normal and forced gradient-extension-probe-disabled paths pass:
  silhouette alpha unchanged,657 sampled night-side pixels unchanged, no GL error
  or context loss, stable uploads/textures over12 frames, no over-albedo bright-edge
  pixels, cached palette reuse and exclusion from statistical overlays. Disabled
  probes exercise a code path on Chromium; they are not another browser/device.
- Twenty warmed body-focus/return cycles keep listeners244→244 and DOM nodes
  1846→1846 after GC, with the same main canvas and Orbit renderer. Sampled JS heap
  33,858,352→34,032,920 bytes; this does not establish a lifetime memory bound.
  Under concurrent QA, automated round trips measured median2596.0ms/max4173.8ms.
- Controlled single-browser SwiftShader readback at512×384 measured12 warm terrain
  frames: median260.1ms/max495.4ms. The same shader's neutral-relief mode measured
  median146.1ms. These include rendering, driver and synchronous one-pixel readback;
  neutral mode is not a prior-release benchmark. Shared-load runs were slower and
  cannot be compared as an optimization speedup. Software rendering on this
  two-CPU Linux quota remains visibly slow; hardware/browser performance is
  unverified. No production FPS, GPU latency or production-scale claim follows.
- Source-matched default V2 connected fixture passes10,000 turns in257.97s:
  conservation, resource ledgers, immutable history and exact restore. It creates
  10,001 snapshots/382,083,362 state bytes; largest serialized state41,896 bytes;
  current read12.0ms/history50 read153.8ms. The prior V11+astronomy10,000-turn gate
  remains applicable because every one of the17 backend module hashes is unchanged;
  no extra native generation stress was repeated for frontend presentation.
- All eight pre-existing public fixture responses match fresh baseline hashes.
  Native detail, material, crater, Orbit projection/picking, recorded-star rays,
  sky pixel/cache, landmark, focus-ticket, derived-slope and shore-crossing checks
  pass. The detail-renderer test now checks subdued background contrast and
  separately legible recorded crater form instead of requiring the rejected deep
  emboss; canonical material-cell identity and exact ice/unrelated alpha remain
  checked. Tests expose private helpers only inside an isolated VM, without
  production test exports.
- Browser is Chromium154.0.8037.57 on Linux/ANGLE Vulkan SwiftShader. WebKit's
  executable is absent; native macOS Safari and physical touch devices remain
  unverified. Automated pointer, touchscreen and keyboard input are bounded
  execution evidence, not physical-device coverage or accessibility certification.

Final audited source hashes:

- `public/map-renderer.js`:
  `d134eb84c1a7de398003089609ca42acbd287ef9d15ef85bf54f98bb7a9769ff`
- `public/planet-orbit.js`:
  `6ba18e7f514e814f6b77517e99f540c0681ede65030dac0cce5989e961bdfd86`

The same independent critic accepts the reviewed visual tasks and supplied final
interaction reports with no major blocker. Acceptance remains limited to tested
views/workflows, including the actual lake view. It does not certify every seed,
camera orientation, planet material or renderer/platform combination.

## Integration and continuation

Keep `hwOrbitRelief` internal to derived canvas objects. Do not persist it or treat
it as authoritative terrain. Preserve immutable detail references, campaign/snapshot
request guards, analytic crater pairing and original geometric picking. New smoother
recorded topology needs an explicit generator version for new worlds; deep zoom
requires actual bounded finer data rather than magnifying this fixed overview.
Test on hardware graphics and native Safari before making performance/browser
claims. Preserve the light/dark toggle and existing character-screen integration.
No merge, deployment, real-data recovery or operational certification was performed.
