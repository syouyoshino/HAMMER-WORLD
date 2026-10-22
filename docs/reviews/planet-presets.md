# Creation-time planet presets

User instruction: islands are an additional generation choice, not a change applied to every Warhammer40,000 world. Some fictional worlds have neither water nor vegetation. Presets are selected independently per planet at creation, saved in immutable geography and never changed by a map-style or appearance control.

## Options and use

| Preset | Saved geography | Water / vegetation |
| --- | --- | --- |
| Continental | Dominant mainland continuing beyond a regional edge, with smaller offshore islands | Ocean-draining; mixed recorded terrain |
| Archipelago | Irregular separated island groups | Ocean-draining; mixed recorded terrain |
| Oceanic | Mostly ocean with smaller exposed islands | Ocean-draining; limited recorded land |
| Arid | Desert plains and rock | No open water, rivers, forest or marsh |
| Barren | Exposed rock | No water, rivers or vegetation |
| Frozen | Cold ground and rock with icy presentation | No open liquid water, rivers, forest or marsh |

`auto` resolves one of these six independently from the private seed and stable planet ID. An override changes only its target planet. A fixed ordered preset list and V4-specific seed domain preserve reproducibility. These are fictional surface descriptors; no canonical planet data, habitability, resources, farming, movement, climate physics or economic rules are inferred.

The existing operator creation path is CLI/Store, not a web creation form. With the intended database configured, create a **new fictional demo ID**, for example:

```sh
python -m app.cli init-v2 --campaign-id new-demo \
  --planet-generator planet-v4 --preset auto \
  --planet-preset new-demo-planet-reach=barren \
  --planet-preset new-demo-planet-ash=archipelago
```

Other planets receive independent auto choices. `--preset PRESET` provides a common fallback if deliberately requested; per-planet overrides still win. IDs must match full stable planet node IDs. Duplicate, unknown, nonplanet or invalid choices are rejected; an existing campaign cannot be overwritten. There is no live preset switch or automatic conversion of saved maps. Orbital/Survey and Light/Dark/System remain presentation choices.

## Architecture and preservation

Sol6.1 high specified and reviewed the contract. V4 adds exactly `surface.preset` and `surface.hydrology` to the existing64×40 surface fields. Wet presets retain sea-level400, bounded integer fields, cardinal acyclic drainage, exact accumulation and ocean-ending rivers. Small islands may legitimately have no substantial river; no decorative stream is forced to satisfy a test.

Dry/cold presets store `sea_level:null`, `hydrology:"none"`, drainage all−1, accumulation all1 and no rivers. Disabled hydrology arrays are explicit sentinels, not simulated watersheds. Arid/barren moisture is zero; their allowed terrain excludes ocean, coast, forest and marsh. Barren uses only rock. Frozen has bounded cold temperatures and no open-water/vegetation codes. Exact keys, primitive types and hydrology/preset/field agreement are validated before authoritative persistence.

Resolved choices are stored in private generator configuration and compared against saved geometry/body class on V4 validation. Only surveyed geography exposes its own preset; hidden planets' choices and seeds remain private. System glyphs use already-public surveyed body class; no extra hidden-preset inference or public global mapping was introduced. Existing IDs, province membership, positional/radius streams, rules, authentication and historical restore semantics are preserved.

V1 remains the default; V1/V2/V3 generation outputs remain unchanged. Earlier generators reject the new preset arguments. No migrations, new terrain codes, dependencies, write endpoints or character-relationship changes were introduced.

## Review findings and corrections

The first Luna implementation received a bounded Sol high contract/source review and localized Sol medium correction:

- Wet sea level accepted400.0; now requires integer400.
- Dry hydrology accepted malformed falsy river values; now requires an empty list.
- Regular3×3 island placement looked artificial; now uses deterministic irregular separated centers and smooth fixed-point coast warping.
- Forced continental edge cells were removed; the continuous land field itself determines edge contact.
- Bathymetry could exceed the sea threshold and generate unintended land; ocean elevations now remain below the threshold.
- Shared wet renderer tint could make frozen ground green; dry/frozen palettes, relief and backgrounds now use recorded preset-specific treatment. Dry legends omit irrelevant water/vegetation, and surveyed dry-world body symbols avoid Earthlike patches.

Final twelve-seed morphology evidence: continental571–722 land cells, dominant component544–703, edge contact in all12; archipelago512–622 land cells across5–9 substantial components; oceanic244–352 land cells with7 substantial components. All retain at least16 land-bearing provinces, exceeding the fixture's three-settlement need. These are samples, not claims about every seed or global planetary topology. Ninety-six complete V2/V3 baseline geometry comparisons match the preceding committed module exactly.

## Evidence and limits

Focused generator/preset gate:14 tests passed in27.748s. It covers malformed fields, private mapping/class consistency, deterministic independent overrides, all six presets across12 seeds, default/legacy goldens, duplicate CLI rejection, private projections, persistence, historical map reads and exact restore. A separate real CLI integration test passed: explicit per-planet choices survive creation; repeated and invalid creation cannot replace records.

`tests/browser_planet_presets.py` uses disposable fictional fixtures with actual Chromium, both styles and Light/Dark UI, all six presets, real land-tile selection, desktop controls, dry legends, surveyed-only metadata, zero-request theme changes with stable canvas pixels, campaign clearing and unchanged source hashes. The user subsequently narrowed acceptance to desktop only. The final default script now stays at1440×1024 and checks actual mouse-driven hierarchy descent for wet archipelago and dry barren bodies. Its final captures/metrics are ignored under `data/planet-presets-desktop/`. Earlier phone observations are supplementary historical evidence, not a continuing acceptance requirement. Broad legacy management/browser-zoom regressions and the mixed V4 long-run gate are recorded below.

The map remains a bounded64×40 regional projection with rectangular provinces and stylized relief; it is not a spherical planetary simulation or recovered canonical cartography. New presets do not imply new economic rules. Rivers/ocean continuity, wave treatment and higher-resolution geological finish from the earlier ideas discussion are separate work, not silently merged into every preset. WebKit/native Safari/physical-device coverage and production operation remain unverified.

## Independent desktop review and functional gates

A fresh independent Sol6.1 medium critic opened all six desktop presets in both styles and Light/Dark, then exercised wet and dry Forge→Economy→Construction→Map, appearance/style changes, body glyph inspection and pregame switching. It found no critical/major issue in this scoped integration. It identified one minor shared System-card overlap with Forces; the same critic verified the measured-inset correction on desktop and confirmed the unlocated row still selects the recorded entity with Unknown coordinates. Original finding and resolution remain in ignored `data/planet-preset-critic/review.md` with fresh full captures. No reference/commercial/canonical-fidelity claim follows from that acceptance. Earlier mobile observations are not a current release gate after the user's explicit desktop-only direction.

Full discovery passed87 tests in322.402s, plus the separate real CLI integration test passed in4.877s:88 distinct tests. Broad `browser_strategic.py` passed after the final shared layout fix, including actual Chrome100/125/150/200% zoom with direct painted-marker navigation, retained camera/selection/overlay/canvas, all management destinations, auth clearing/stale requests and theme/storage/retry checks. That existing suite also exercised responsive states before the scope update; future preset acceptance is desktop-only. The existing V3 cartography regression passed, separately from the new six-preset browser tests. No uncaught JavaScript error occurred in the exercised paths.

Generation and validation timings were measured on shared Linux/three logical CPUs, Python3.12/PostgreSQL17/system Chromium154, with concurrent QA. Across three four-planet builds per preset, medians ranged50–499ms; five validations per resulting state averaged4.9–14.8ms. Serialized state was243–272KB and expanded public projection229–282KB. A single cold raster per style/preset took153–541ms; ten warm synchronous draws averaged1.4–13.5ms. Those direct calls exclude input, network, compositing and force DOM work. Samples and rendering/DB costs are not production-scale guarantees. Detailed raw metrics remain ignored under `data/planet-presets/`.

Implementation commits: `af28097` (versioned presets/creation/validation/tests) and `01c4271` (recorded preset rendering, body symbols and measured System-card placement). The desktop-only final test adjustment follows them. No merge, deployment, original-cloud recovery, live data conversion or character-relationships change occurred.

## Final mixed-world gate and delivery

The frozen V4 mixed fixture passed **10,000 turns in923.01s**, with an Arid homeworld, Archipelago colonization target, Oceanic neighbour and Frozen hidden world. Every turn checks conservation and budgets; checkpoints retain exact immutable hashes, and restore preserves the initial geography/preset choices without changing the source timeline.10,001 source snapshots, population1,199, largest serialized state262,538bytes, summed serialized source states2,075,942,731bytes (not physical database disk usage). Final current read17.1ms and50-entry history931.4ms are fixture observations, not production guarantees. All recorded backend hashes match the tested committed source; numeric engine remains unchanged. The source-hashed report is ignored at `data/verification/stress-v4-presets.json`, retaining V3 evidence separately.

Final desktop-only preset regression passed after shared layout correction and the user's scope update. Both styles/themes, actual mouse hierarchy, recorded land selection, private metadata boundaries, context clearing and unchanged source snapshots pass with no page errors. Broad final management/actual100–200% desktop zoom also passed. Current browser coverage is system Chromium154; WebKit and native Safari remain unverified. The independent critic accepted scoped desktop quality and rechecked the only minor layout finding; it did not perform protected GM operations or the stress run.

Delivery milestones: `af28097` generation/persistence/CLI, `01c4271` rendering/layout, `b629ccb` desktop-only acceptance. This remains an interface release candidate, with no merge/deployment, operational-security certification or commercial/canonical-fidelity claim. Generated records, databases, captures and performance reports remain outside Git.
