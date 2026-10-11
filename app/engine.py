"""Deterministic fictional demo-world generation and economy rules."""
import hashlib
import json
import random
import re

SCHEMA_VERSION = "world-v1"
RULES_VERSION = "economy-v1"
NARRATIVE_LIMIT = 2000
SUBMISSION_RE = re.compile(r"^[A-Za-z0-9._:-]{1,100}$")
ORDER_KEYS = {"farmers", "miners", "technicians"}


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def domain_seed(seed, label):
    return int.from_bytes(hashlib.sha256(f"{seed}:{label}".encode()).digest()[:8], "big")


def generate_planet(campaign_id, seed):
    # Two deterministic broad landmasses plus a small independent detail field.
    continents = random.Random(domain_seed(seed, "planet:continents:v1"))
    centers = [(continents.uniform(6, 58), continents.uniform(5, 35), continents.uniform(8, 17), continents.uniform(5, 11)) for _ in range(3)]
    detail = random.Random(domain_seed(seed, "planet:terrain-detail:v1"))
    width, height = 64, 40
    provinces = []
    for py in range(5):
        for px in range(8):
            pid = f"{campaign_id}-p-{py:02d}-{px:02d}"
            provinces.append({"id": pid, "name": f"Province {py * 8 + px + 1:02d}",
                              "x": px * 8, "y": py * 8, "width": 8, "height": 8})
    tiles = []
    for y in range(height):
        for x in range(width):
            elevation = max(0.0, *(1 - ((x-cx)/rx)**2 - ((y-cy)/ry)**2 for cx,cy,rx,ry in centers))
            if elevation < 0.12:
                terrain = "ocean"
            elif elevation < 0.30:
                terrain = "coast"
            else:
                terrain = detail.choice(["plains", "rock", "forest", "marsh"])
            province = provinces[(y // 8) * 8 + (x // 8)]["id"] if terrain != "ocean" else None
            tiles.append({"x": x, "y": y, "terrain": terrain, "province_id": province})
    terrain_codes = {"ocean":"o", "coast":"c", "plains":"p", "rock":"r", "forest":"f", "marsh":"m"}
    return {"planet": {"id": f"{campaign_id}-planet-001", "name": "Kestrel's Reach",
                        "width": width, "height": height}, "provinces": provinces,
            "terrain_grid": "".join(terrain_codes[t["terrain"]] for t in tiles)}


def initial_state(campaign_id, seed):
    state = generate_planet(campaign_id, seed)
    state.update({"turn": 0, "population": 1200, "food": 8000, "ore": 2400, "energy": 4000,
                  "outcomes": [], "narrative": "", "_private": {"seed": seed, "seeded_marker": f"secret:{seed}"}})
    return state


def public_state(state):
    # Explicit nested projection prevents future private fields leaking into player APIs.
    planet = {key: state["planet"][key] for key in ("id", "name", "width", "height")}
    provinces = [{key: p[key] for key in ("id", "name", "x", "y", "width", "height")} for p in state["provinces"]]
    codes = {"o":"ocean", "c":"coast", "p":"plains", "r":"rock", "f":"forest", "m":"marsh"}
    width, height = planet["width"], planet["height"]
    grid = state["terrain_grid"]
    tiles = []
    for y in range(height):
        for x in range(width):
            code = grid[y * width + x]
            province = provinces[(y // 8) * 8 + (x // 8)]["id"] if code != "o" else None
            tiles.append({"x": x, "y": y, "terrain": codes[code], "province_id": province})
    outcome_fields = ("turn", "assigned_workers", "food_produced", "food_consumed", "food_shortage",
                      "population_lost", "ore_produced", "energy_produced", "energy_consumed")
    outcomes = [{key: item[key] for key in outcome_fields} for item in state["outcomes"]]
    return {"planet": planet, "provinces": provinces, "tiles": tiles,
            "turn": state["turn"], "population": state["population"], "food": state["food"],
            "ore": state["ore"], "energy": state["energy"], "outcomes": outcomes,
            "narrative": state["narrative"]}


def validate_submission(payload):
    required = {"schema_version", "rules_version", "base_turn", "base_hash", "submission_id", "orders", "narrative"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("proposal must contain exactly the documented fields")
    if payload["schema_version"] != SCHEMA_VERSION or payload["rules_version"] != RULES_VERSION:
        raise ValueError("unsupported schema_version or rules_version")
    if type(payload["base_turn"]) is not int or payload["base_turn"] < 0:
        raise ValueError("base_turn must be a nonnegative integer")
    if not isinstance(payload["base_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", payload["base_hash"]):
        raise ValueError("base_hash must be a SHA256 hex digest")
    if not isinstance(payload["submission_id"], str) or not SUBMISSION_RE.fullmatch(payload["submission_id"]):
        raise ValueError("invalid submission_id")
    orders = payload["orders"]
    if not isinstance(orders, dict) or set(orders) != ORDER_KEYS:
        raise ValueError("orders must contain exactly farmers, miners, technicians")
    if any(type(v) is not int or v < 0 or v > 10_000_000 for v in orders.values()):
        raise ValueError("orders must be nonnegative integers")
    if not isinstance(payload["narrative"], str) or len(payload["narrative"]) > NARRATIVE_LIMIT:
        raise ValueError(f"narrative must be a string of at most {NARRATIVE_LIMIT} characters")


def advance(state, payload):
    validate_submission(payload)
    orders = payload["orders"]
    population, food, ore, energy = (state[k] for k in ("population", "food", "ore", "energy"))
    assigned = sum(orders.values())
    if assigned > population:
        raise ValueError("assigned workers exceed population")
    energy_made = orders["technicians"] * 2
    available_energy = energy + energy_made
    productive_miners = min(orders["miners"], available_energy)
    energy_used = productive_miners
    ore_made = productive_miners * 2
    food_made = orders["farmers"] * 3
    food_available = food + food_made
    food_need = population
    shortage = max(0, food_need - food_available)
    population_loss = min(population, shortage)
    next_state = dict(state)
    next_state.update({"turn": state["turn"] + 1, "population": population - population_loss,
                       "food": max(0, food_available - food_need), "ore": ore + ore_made,
                       "energy": available_energy - energy_used,
                       "narrative": payload["narrative"]})
    outcome = {"turn": next_state["turn"], "assigned_workers": assigned,
               "food_produced": food_made, "food_consumed": min(food_need, food_available),
               "food_shortage": shortage, "population_lost": population_loss,
               "ore_produced": ore_made, "energy_produced": energy_made, "energy_consumed": energy_used}
    next_state["outcomes"] = [outcome]
    return next_state, outcome
