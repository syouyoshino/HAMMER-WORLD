"""Opt-in fictional worlds for continuous system/planet browser review.

Only creates new demo campaigns. Call create_review_fixtures(store) in an
isolated review schema; nothing runs on import. The Store transaction publishes
real native detail assets and immutable snapshots together. Generation of all
15 1024x640 surfaces is deliberately expensive (allow several minutes).
"""
from dataclasses import asdict, dataclass
from copy import deepcopy
import json
from unittest.mock import patch

from app import astronomy
from app.detail_assets import detail_reference
from app.planet_generation import PLANET_CLASSES
from app.planet_materials import validate_choices
from app.planet_scale import canonical_radius
from app.planet_v11 import generate_planet_v11
from app.store import Store
from app.universe import V2_RULES, V2_SCHEMA, _seed, build_universe


@dataclass(frozen=True)
class PlanetSpec:
    suffix: str
    name: str
    radius_km: int
    preset: str
    lake_material: str = "none"
    polar_caps: str = "none"
    geology: str = "none"
    knowledge: str = "surveyed"

    @property
    def radius_m(self):
        return canonical_radius(str(self.radius_km * 1000))


# These are saved fictional generation choices, not measured campaign facts.
# The static-v1 astronomy contract bounds supported radii to these whole km.
WORLDS = {
    "sparse": (
        PlanetSpec("reach", "Fictional Sere", 3000, "arid", geology="cratered"),
        PlanetSpec("02", "Fictional Rime", 1800, "frozen", "hydrocarbon", "water-ice", knowledge="detected"),
    ),
    "rich": (
        PlanetSpec("reach", "Fictional Ember", 4500, "arid", "lava"),
        PlanetSpec("02", "Fictional Shoals", 7200, "archipelago", "water", "water-ice"),
        PlanetSpec("03", "Fictional Pelagic", 12000, "oceanic", "water"),
        PlanetSpec("04", "Fictional Frost", 2800, "frozen", "hydrocarbon", "water-ice"),
        PlanetSpec("05", "Fictional Shard", 1600, "barren", geology="cratered"),
        PlanetSpec("06", "Fictional Vale", 9200, "continental", "water", "water-ice"),
        PlanetSpec("07", "Fictional Salt", 19000, "arid", polar_caps="water-ice"),
        PlanetSpec("08", "Fictional Far Ice", 35000, "frozen", knowledge="detected"),
    ),
    "extreme": (
        PlanetSpec("reach", "Fictional Minimum", 1000, "barren", geology="cratered"),
        PlanetSpec("02", "Fictional Colossus", 100000, "arid", "lava"),
        PlanetSpec("03", "Fictional Ice Vast", 65000, "frozen", "hydrocarbon", "water-ice"),
        PlanetSpec("04", "Fictional Deep", 40000, "oceanic", "water", "water-ice"),
        PlanetSpec("05", "Fictional Remote", 1400, "barren", knowledge="detected"),
    ),
}
SEEDS = {"sparse": 918231, "rich": 918232, "extreme": 918233}

# Explicit frozen fictional layout: 0.02, 0.3, 5, 45 and 90 AU, respectively.
# Integer 3:4:5 vectors keep the radial distances exact at varied bearings.
EXTREME_POSITIONS = ((20000, 0, 0), (0, 0, 300000), (-3000000, 0, 4000000),
                     (27000000, 0, -36000000), (-54000000, 0, -72000000))


def apply_extreme_layout(state):
    planets = [n for n in state["nodes"] if n["kind"] == "planet"]
    systems = {n["parent_id"] for n in planets}
    if len(planets) != 5 or len(systems) != 1:
        raise ValueError("extreme layout requires five planets in one system")
    system_id = next(iter(systems))
    records = state["astronomy"]["systems"][system_id]["bodies"]
    for planet, position in zip(planets, EXTREME_POSITIONS):
        records[planet["id"]]["position"] = list(position)
    state["_private"]["review_layout"] = {
        "label": "Fictional frozen extreme separations",
        "planet_positions_micro_au": {p["id"]: list(pos) for p, pos in zip(planets, EXTREME_POSITIONS)},
    }
    astronomy.validate(state)
    return system_id


def validate_specs(specs):
    if len({p.suffix for p in specs}) != len(specs) or specs[0].suffix != "reach":
        raise ValueError("review fixture needs unique suffixes and Reach economy anchor")
    for p in specs:
        if type(p.radius_km) is not int or not 1000 <= p.radius_km <= 100000:
            raise ValueError("review radius is outside whole-km static-v1 limits")
        validate_choices(p.preset, p.lake_material, p.polar_caps)
        if p.preset not in PLANET_CLASSES or p.knowledge not in ("surveyed", "detected"):
            raise ValueError("unsupported review surface or visibility")
        if p.geology not in ("none", "cratered") or (p.geology == "cratered" and p.preset not in ("arid", "barren", "frozen")):
            raise ValueError("unsupported review geology")


def build_review_world(campaign_id, seed, specs, detail_assets):
    """Assemble new topology before generating any saved astronomy records."""
    validate_specs(specs)
    # Reuse the actual fixture economy, then replace all physical geographies.
    # Legacy generation is cheap and publishes no native asset to this mapping.
    state = build_universe(campaign_id, seed)
    keep = {f"{campaign_id}-{suffix}" for suffix in (
        "galaxy", "region-01", "sector-hearth", "system-hearth", "system-hearth-star")}
    state["nodes"] = [n for n in state["nodes"] if n["id"] in keep]
    system_id = f"{campaign_id}-system-hearth"
    for n in state["nodes"]:
        n["name"] = f"Fictional Review {n['kind'].title()}"
    state["links"] = []
    state["geography"] = {}
    config = {"hierarchy": "hierarchical-v1", "planet": "planet-v11", "grid": "grid128x80",
              "domain_seed_derivation": "sha256-parent-domain-v1", "feature_names": "generated",
              "astronomy": "static-v1", "planet_presets": {}, "planet_geologies": {},
              "planet_lake_materials": {}, "planet_polar_caps": {}, "planet_radii_m": {}}
    for ordinal, p in enumerate(specs):
        pid = f"{campaign_id}-planet-{p.suffix}"
        state["nodes"].append({"id": pid, "parent_id": system_id, "kind": "planet",
            "name": p.name, "knowledge": p.knowledge, "class": PLANET_CLASSES[p.preset],
            "radius_m": p.radius_m, "x": ordinal, "y": 0})
        geo, payload = generate_planet_v11(pid, _seed(seed, pid, "geography"), p.preset,
            p.geology, p.lake_material, p.polar_caps, "generated", radius_m=p.radius_m)
        ref = detail_reference(payload)
        geo["detail_ref"] = ref
        detail_assets[ref["sha256"]] = payload
        state["geography"][pid] = geo
        for key, value in (("planet_presets", p.preset), ("planet_geologies", p.geology),
                           ("planet_lake_materials", p.lake_material), ("planet_polar_caps", p.polar_caps),
                           ("planet_radii_m", p.radius_m)):
            config[key][pid] = value
    # Contacts carry no invented physical moon/belt coordinates or native maps.
    state["nodes"].extend([
        {"id": f"{campaign_id}-review-moon", "parent_id": f"{campaign_id}-planet-reach",
         "kind": "moon", "name": "Unknown Moon", "knowledge": "detected"},
        {"id": f"{campaign_id}-review-belt", "parent_id": system_id,
         "kind": "belt", "name": "Unknown Belt", "knowledge": "detected"},
    ])
    home = state["geography"][f"{campaign_id}-planet-reach"]
    width = home["planet"]["width"]
    land = [p["id"] for p in home["provinces"] if any(
        home["terrain_grid"][y * width + x] != "o"
        for y in range(p["y"], p["y"] + p["height"])
        for x in range(p["x"], p["x"] + p["width"]))]
    if len(land) < len(state["settlements"]):
        raise ValueError("review home surface lacks initial land settlements")
    for settlement, province in zip(state["settlements"], land):
        settlement["province_id"] = province
        if "intel" in settlement:
            settlement["intel"]["province_id"] = province
    enemy = next(s for s in state["settlements"] if not s["owned"])
    for unit in state["units"]:
        unit["location_id"] = enemy["province_id"]
        unit["intel"]["location_id"] = enemy["province_id"]
    state["_private"]["generator_config"] = config
    state["_private"]["adjacency"] = []
    state["_private"]["review_fixture"] = "Fictional isolated review; supported solid surfaces only"
    state["astronomy"] = astronomy.generate(state["nodes"], seed)
    if tuple(specs) == WORLDS["extreme"]:
        apply_extreme_layout(state)
    state["narrative"] = "Fictional isolated review fixture. Moon and belt physical records remain unknown."
    Store.validate_state(V2_SCHEMA, V2_RULES, 0, state)
    return state


def create_review_fixtures(store, prefix="review-continuous", worlds=None):
    """Return manifest by sparse/rich/extreme; refuse any existing target ID.

    Use only while this Store process is not serving concurrent requests: the
    temporary test mock replaces app.store.build_universe during creation.
    No campaigns are deleted and each creation retains Store atomicity.
    """
    chosen = tuple(WORLDS if worlds is None else worlds)
    if not chosen or len(set(chosen)) != len(chosen) or any(w not in WORLDS for w in chosen):
        raise ValueError("choose unique supported review worlds")
    ids = {world: f"{prefix}-{world}" for world in chosen}
    existing = {c["id"] for c in store.campaigns()}
    if existing.intersection(ids.values()):
        raise ValueError("review campaign already exists; choose a fresh prefix")
    result = {}
    for world in chosen:
        specs, campaign_id = WORLDS[world], ids[world]
        def factory(cid, seed, *, detail_assets, **_ignored):
            return build_review_world(cid, seed, specs, detail_assets)
        with patch("app.store.build_universe", side_effect=factory):
            snapshot_id = store.create_demo_v2(campaign_id, SEEDS[world], planet_generator="planet-v11")
        result[world] = {"campaign_id": campaign_id, "snapshot_id": snapshot_id,
            "system_id": f"{campaign_id}-system-hearth", "planet_count": len(specs),
            "planets": [{"id": f"{campaign_id}-planet-{p.suffix}", **asdict(p), "radius_m": p.radius_m} for p in specs]}
    return result


def create_extreme_layout_variant(store, source_campaign_id, new_campaign_id):
    """Create a fresh immutable demo reusing a review source's real assets/IDs.

    No terrain is regenerated. Source snapshot and native asset digests are
    preserved as private provenance; only this new fixture receives the layout.
    As with create_review_fixtures, run outside a concurrent server process.
    """
    if any(c["id"] == new_campaign_id for c in store.campaigns()):
        raise ValueError("review campaign already exists; choose a fresh ID")
    source = store.current(source_campaign_id)
    if not source or source["campaign"]["kind"] != "demo" or not source.get("snapshot"):
        raise ValueError("source must be a persisted review demo")
    snap = source["snapshot"]
    if ((snap["schema_version"], snap["rules_version"]) != (V2_SCHEMA, V2_RULES)
            or not snap["state"].get("_private", {}).get("review_fixture") or snap["turn"] != 0):
        raise ValueError("source must be an initial fictional review fixture")
    state = deepcopy(snap["state"])
    state["_private"]["campaign_id"] = new_campaign_id
    state["_private"]["review_source"] = {"campaign_id": source_campaign_id,
        "snapshot_id": snap["id"], "state_hash": snap["state_hash"],
        "preserved_body_ids": True, "preserved_native_asset_digests": True}
    system_id = apply_extreme_layout(state)
    state["narrative"] = "Fictional frozen separation review: planets at 0.02, 0.3, 5, 45 and 90 AU. Moon and belt physical records remain unknown."
    Store.validate_state(V2_SCHEMA, V2_RULES, 0, state)
    assets = {}
    with store.connect() as connection:
        for geo in state["geography"].values():
            ref = geo["detail_ref"]
            row = connection.execute("SELECT payload_json FROM planet_detail_assets WHERE sha256=%s", (ref["sha256"],)).fetchone()
            if not row:
                raise ValueError("source native detail asset is missing")
            payload = json.loads(row["payload_json"])
            if detail_reference(payload) != ref:
                raise ValueError("source native detail checksum mismatch")
            assets[ref["sha256"]] = payload
    def factory(cid, seed, *, detail_assets, **_ignored):
        detail_assets.update(assets)
        return state
    with patch("app.store.build_universe", side_effect=factory):
        snapshot_id = store.create_demo_v2(new_campaign_id, state["_private"]["seed"], planet_generator="planet-v11")
    planets = [n for n in state["nodes"] if n["kind"] == "planet"]
    return {"campaign_id": new_campaign_id, "snapshot_id": snapshot_id,
        "system_id": system_id, "planet_count": len(planets),
        "source_campaign_id": source_campaign_id, "source_snapshot_id": snap["id"],
        "positions_micro_au": deepcopy(state["_private"]["review_layout"]["planet_positions_micro_au"]),
        "planets": [{"id": p["id"], "name": p["name"], "knowledge": p["knowledge"],
            "radius_m": p["radius_m"],
            **{key: state["geography"][p["id"]]["surface"][key] for key in ("preset", "geology", "lake_material", "polar_caps")}}
            for p in planets]}
