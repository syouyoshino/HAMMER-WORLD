"""Versioned, frozen fictional astronomy records for opted-in demo worlds."""
import math
import random


VERSION = "static-v1"
HEADER = {
    "version": VERSION,
    "epoch_turn": 0,
    "motion": "frozen",
    "position_unit": "micro-AU",
    "frame": "system-xyz-v1",
    "planet_frame": "aligned-xyz-v1",
}
MAX_POSITION = 100_000_000  # 100 AU, expressed in micro-AU.


def generate(nodes, seed):
    """Create deterministic static coordinates for existing star and planet nodes."""
    systems = [node for node in nodes if node.get("kind") == "system"]
    bodies = [node for node in nodes if node.get("kind") in ("star", "planet")]
    result = {**HEADER, "systems": {}}
    for system in systems:
        children = [node for node in bodies if node.get("parent_id") == system["id"]]
        if not children:
            continue
        records = {}
        planets = sorted((node for node in children if node["kind"] == "planet"), key=lambda node: node["id"])
        for node in children:
            if node["kind"] == "star":
                low, high = {"G": (590_000, 765_000), "K": (417_000, 590_000), "M": (104_000, 383_000)}.get(node.get("stellar_class"), (590_000, 765_000))
                radius_km = random.Random(_seed(seed, system["id"], f"astronomy-static-v1:star:{node['id']}")).randint(low, high)
                position = [0, 0, 0]
            else:
                ordinal = planets.index(node)
                rng = random.Random(_seed(seed, system["id"], f"astronomy-static-v1:{node['id']}"))
                distance = (450_000 + ordinal * 650_000 + rng.randrange(0, 200_000))
                angle = rng.random() * math.tau
                position = [round(distance * math.sin(angle)), 0, round(distance * math.cos(angle))]
                if position == [0, 0, 0]:
                    position[0] = distance
                radius_km = round(node.get("radius", 1) * 6_371)
            records[node["id"]] = {"position": position, "radius_km": radius_km}
        result["systems"][system["id"]] = {"bodies": records}
    return result


def _seed(seed, parent, domain):
    # Isolated deterministic stream: it does not consume or perturb legacy RNG state.
    import hashlib
    raw = f"{seed}:{parent}:{domain}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def validate(state):
    """Check the complete persisted contract against the hierarchy."""
    config = state.get("_private", {}).get("generator_config", {})
    astronomy = state.get("astronomy")
    if "astronomy" not in state:
        if "astronomy" in config:
            raise ValueError("astronomy configuration has no saved records")
        return
    if config.get("astronomy") != VERSION:
        raise ValueError("saved astronomy and generator configuration differ")
    if not isinstance(astronomy, dict) or set(astronomy) != {*HEADER, "systems"}:
        raise ValueError("saved astronomy header invariant failed")
    if any((type(astronomy.get(key)) is not int or astronomy.get(key) != value)
           if key == "epoch_turn" else astronomy.get(key) != value for key, value in HEADER.items()):
        raise ValueError("unsupported saved astronomy version or frame")
    nodes = {node["id"]: node for node in state.get("nodes", [])}
    expected = {node_id: set() for node_id, node in nodes.items() if node.get("kind") == "system"}
    for node in nodes.values():
        if node.get("kind") in ("star", "planet"):
            parent = nodes.get(node.get("parent_id"))
            if parent and parent.get("kind") == "system":
                expected.setdefault(parent["id"], set()).add(node["id"])
    systems = astronomy.get("systems")
    if not isinstance(systems, dict) or set(systems) != set(expected):
        raise ValueError("saved astronomy system identity invariant failed")
    for system_id, expected_bodies in expected.items():
        system = systems[system_id]
        if not isinstance(system, dict) or set(system) != {"bodies"} or not isinstance(system["bodies"], dict) or set(system["bodies"]) != expected_bodies:
            raise ValueError("saved astronomy body identity invariant failed")
        if sum(nodes[node_id].get("kind") == "star" for node_id in expected_bodies) != 1:
            raise ValueError("saved system requires exactly one star")
        checked = []
        for node_id, record in system["bodies"].items():
            if not isinstance(record, dict) or set(record) != {"position", "radius_km"}:
                raise ValueError("saved astronomy body record invariant failed")
            position, radius = record["position"], record["radius_km"]
            if not isinstance(position, list) or len(position) != 3 or any(type(value) is not int or abs(value) > MAX_POSITION for value in position):
                raise ValueError("saved astronomy coordinate invariant failed")
            if type(radius) is not int or not 1_000 <= radius <= 1_500_000:
                raise ValueError("saved astronomy radius invariant failed")
            node = nodes[node_id]
            if node["kind"] == "star":
                if position != [0, 0, 0]:
                    raise ValueError("saved star must be the system origin")
            else:
                if position == [0, 0, 0] or radius > 100_000:
                    raise ValueError("saved planet orbit or radius invariant failed")
            checked.append((position, radius))
        for index, (position, radius) in enumerate(checked):
            for other_position, other_radius in checked[index + 1:]:
                distance_squared = sum((position[axis] - other_position[axis]) ** 2 for axis in range(3))
                if distance_squared * 1_495_978_707**2 <= (radius + other_radius)**2 * 10_000_000**2:
                    raise ValueError("saved astronomical bodies physically intersect")


def project(astronomy, visible_nodes, system_id=None):
    """Build a clean player-facing projection with no hidden body references."""
    if astronomy is None:
        return None
    visible = {node["id"]: node for node in visible_nodes
               if node.get("knowledge") == "surveyed" and node.get("kind") in ("system", "star", "planet")}
    systems = {}
    for current_system, record in astronomy["systems"].items():
        if system_id is not None and current_system != system_id:
            continue
        if current_system not in visible or visible[current_system]["kind"] != "system":
            continue
        body_rows = {}
        for node_id, body in record["bodies"].items():
            node = visible.get(node_id)
            if node and node.get("parent_id") == current_system and node.get("kind") in ("star", "planet"):
                body_rows[node_id] = {"position": list(body["position"]), "radius_km": body["radius_km"]}
        if body_rows:
            systems[current_system] = {"bodies": body_rows}
    if not systems:
        return None
    return {**HEADER, "systems": systems}
