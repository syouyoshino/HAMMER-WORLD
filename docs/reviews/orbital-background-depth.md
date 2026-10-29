# Orbital background depth — 29 October 2026

The user found the accepted adaptive background visually flat. This follow-up
addresses the decorative space layer only; the globe's subdued lighting/relief
remains a separate inherited limitation. No claim of cinematic or physical parity.

## Critique and response

Fresh full-frame Chromium captures repeat four exact camera/theme poses against
the prior committed background. No crops, fabricated units or campaign data.
A Luna implementation of layered curves was rejected for visible tubes/end caps.
A localized Sol medium revision added elliptical dust wisps; the fresh independent
Sol medium critic inspected all eight anonymous images before origins were
revealed. It preferred the old background's natural restraint, while finding the
new version stronger on layering but visibly streaked (left middle/lower margins,
horizontal band near y=290, lower-right fan). Both retained good label readability.
The critic also identified weak star hierarchy and the unchanged globe's flatness.

After two substantive attempts exposed the same primitive-pattern defect, one
bounded Sol high diagnosis recommended continuous world-direction noise instead
of adjusting cloud opacity or adding more splats. The resulting small procedural
bitmap combines independent broad coverage, several cloud detail scales and dark
channels. It remains fixed in world space, responds to the existing orbital
camera, has no idle animation, and is identical in both UI themes. Sparse stars
retain fixed directions with a wider restrained brightness hierarchy.

## Evidence and limits

Local ignored evidence is under `data/space-depth/`: `baseline`, rejected
`candidate` and `revised`, original blind `anonymous`, and `noise` and final `optimized` captures.
The first band revision's passing functional report is retained separately as
`rejected-band-browser`; passing tests did not override its failed visual review.

No campaign records, geography, shaders, map renderer, simulation or auth code
changed. All 14 frozen backend hashes match; prior simulation stress coverage
remains applicable, without rerunning it for decoration. Generated screenshots,
database context and runtime artifacts remain outside Git. No merge/deployment.

## Rendering bounds

One reusable sky bitmap has a longest side of 128 pixels (at 1440×1024 it is
128×91), upscaled smoothly. The RGBA ImageData and canvas backing each have at
most 64 KiB of pixel storage, plus one 32 KiB value-noise lattice. Actual browser
allocation overhead is not measured. One last-pose key caches the current image;
there is no growing cache or per-camera image retention. This small decorative
scratch canvas is intentionally retained, separate from the app's released
transition composite. There are no added handlers, timers or idle render loop.

The initial 192-side version and 128-side optimization preserve the same world
cloud field and colors. The independent critic found the noise version preferable
to the original baseline, with no major static blocker; the previous tube/stripe
findings are resolved. Remaining medium softness of larger fog masses and modest
star hierarchy are recorded as polish limits, not hidden by the acceptance.
The result is quiet layered space, not cinematic volumetric nebulae.

## Final checks and independent outcome

The same Sol medium critic inspected all four optimized frames and found no
material visual regression from 192 to 128, no renewed stripes/fan, and no
conspicuous pixelation at this display size. After reading the final workflow
report it accepted the scoped visual and interaction result with no unresolved
major background issue. It retains the medium softness/minor star-hierarchy
limits above. This updates, rather than replaces, its earlier adverse verdict.

- Node sky checks pass actual bitmap bounds/opacity/visible clouds, exact-pose
  cache reuse, deterministic orbit-away/back, poles and full-orbit/yaw seam pixel
  continuity. Existing orbital projection and landmark checks pass. JavaScript
  syntax and diff checks pass.
- Actual Chromium 154.0.8037.57, Linux, 1440×1024:
  `data/space-depth/browser/workflow.json` records changed background pixels during
  native canvas drag and zoom, no idle sky draws, identical sky through theme
  changes, Economy→Map camera retention, five Surface/Orbit cycles, a retained
  main map canvas, missing-module fallback, unchanged fixture records and no
  page errors. Zero retained app transition composites after settling; peak
  composite 1,474,560 pixels. The small sky bitmap is intentionally retained.
- Final sky SHA256:
  `d916392def51b279cf522ea0a214bab7adbbccc7369761d9193241fd1ac68cd7`.
  The app/index/surface renderer/globe/landmark module remain unchanged. Prior
  protected auth/history/movement checks were not rerun for this sky-only change.
- Over 134 mixed cached and changing browser draw calls, sky command CPU median
  was 0.20 ms,95th percentile 3.10 ms,maximum 21.50 ms. Cache hits dominate the median;
  these are not changed-pose timings, GPU/raster completion or whole-frame FPS.
  Noise adds changed-pose CPU work compared with the old haze. Its lower
  resolution is a deliberate bounded quality/performance tradeoff.
- A separate inline Chromium 154 CPU probe timed 20 draws advancing longitude by
  .01 each, followed by 20 unchanged-pose draws, without warmup. The 128-side run
  measured 9.0 ms changed-pose median, 49.8 ms maximum and 0.1 ms cached median. It
  overlapped screenshot capture and survives only in tool stdout, not a raw
  artifact. The prior 192-side probe measured 13.9/56.6/0.1ms respectively without
  that overlap. These unpaired probes suggest reduced work but do not establish
  a speedup ratio or stable frame budget. Occasional CPU spikes remain a limit.
- No WebKit/native macOS Safari or native-rate smoothness verification. No new
  unretimed motion recording this follow-up; stills and automated assertions
  establish the bounded findings, not cinematic movement or physical accuracy.

Replay using the existing fictional preview (no regeneration):

```sh
node tests/check_orbit_background.cjs
WOLD_SKY_OUT=data/space-depth/browser .venv/bin/python tests/browser_orbit_background.py
```

Delivery implementation/tests/review: `5ef3d75`, branch `map-generation`.
