# Orbital day/night and sky visibility

Scope: frontend presentation on `map-generation`. Recorded astronomy remains the
lighting authority where available. No generator, campaign, history, schema or
simulation rule changes; no new astronomical records, emissive cities, flare events
or navigable decorative stars.

The old 30% all-surface light floor is now 4.5%, a deliberate strategic visibility
allowance rather than physical ambient space light. A narrower geometric incidence
ramp controls the day/night boundary. Relief still changes only surface lighting;
coverage, silhouette, picking and world positions remain independent. In snapshots
without astronomy the illustrative sun is fixed in the planet frame and transformed
through the same camera basis as recorded sunlight, so orbiting reveals phases.
The status/footer labels this case “illustrative lighting · star position unknown”.
There is no automatic physical rotation/time simulation or multiple-sun lighting.

Decorative background stars are more legible (260 deterministic directions, modestly
larger/brighter points) and haze modulation is quieter. Recorded named bodies retain
their separate projection and interaction path; decorative points are not destinations.

## Evidence

`python3 -m tests.browser_orbit_lighting` measures actual GPU white-texture day/night
and opposite-view fallback light, checks alpha coverage and GL errors, captures the
real demo and checks public record equality. Runtime outputs are ignored under
`data/orbit-lighting/`. Day center 255/255/255, night 11/11/11, opposite fallback
views 211 versus 11 in the initial run; equal geometric alpha, GL error zero,
unchanged campaign response and no exercised JavaScript errors.

`check_orbit.cjs`, `check_orbit_background.cjs` and `check_body_focus.cjs` pass:
projection/picking, pole/seam continuity, sky cache/deterministic return and
focus-ticket context isolation remain intact. Required 10,000-turn fixture evidence
is retained from the immediately preceding release in
`terrain-and-desktop-finish.md` (257.97s, PASS). Backend and turn-processing sources
are unchanged; no expensive simulation rerun is justified by these shader/color edits.

Browser coverage: Chromium 154 software GPU on Linux. Native Safari/WebKit and
hardware graphics remain unverified. No production performance or photographic
planet realism claim. Broader terrain topology/finite-detail limitations from the
preceding review remain.

## Independent critique and correction

A fresh Sol 6.1 medium critic reviewed actual screenshots, source and bounded GPU
reports. Initial candidate had a material defect: grazing relief produced black
trench-like bands inside daylight. A localized Sol medium correction bounds relief
incidence around geometric incidence by min(0.08, 25% of positive incidence), leaving
the dark night floor and geometric terminator intact. This is illustrative strategic
relief, not a physical terrain-shadow calculation. The same critic accepts final
current/rotated dark/light captures with no scoped visual blocker: readable labels,
coherent light across the recorded drag, explicit unknown-light disclosure and more
apparent but restrained stars. Stars remain subtle at full desktop size. The critic
inspected supplied evidence; it did not independently execute the browser tests.
No commercial-game comparison or scientific astronomy validation was conducted.

Final recorded-astronomy GPU regression (`data/orbit-lighting/recorded-final/report.json`)
passes: 3,597 pixels change with relief, exact alpha coverage retained, 657 night
samples unchanged by relief, no over-albedo bright rim, no GL/context/page errors,
stable texture/upload counts over 12 frames, shared relief reused on palette change,
statistical overlay exclusion and unchanged public campaign records. Shared software
GPU readback median 305.3ms at 512×384; includes synchronous rendering/readback and
concurrent QA, not production frame time or a measured optimization claim.

The initial local preview processes disappeared during QA. Existing PostgreSQL was
restarted and the same isolated fixture servers reused; no databases/worlds were
reset or regenerated. Real mouse drag and both UI themes were then captured and
checked. Legacy generation/detail and unrecovered cartography work remain untouched.
