"""Saved, deterministic names and identities for V9 water features."""
import hashlib
import unicodedata


def _neighbors(index, width, height):
    x, y = index % width, index // width
    for nx, ny in (((x - 1) % width, y), ((x + 1) % width, y), (x, y - 1), (x, y + 1)):
        if 0 <= ny < height:
            yield ny * width + nx


def _components(mask, width, height):
    remaining = set(mask)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, cells = [start], []
        while stack:
            cell = stack.pop()
            cells.append(cell)
            for adjacent in _neighbors(cell, width, height):
                if adjacent in remaining:
                    remaining.remove(adjacent)
                    stack.append(adjacent)
        result.append(sorted(cells))
    return sorted(result, key=lambda cells: cells[0])


def _name(feature_id):
    digest = hashlib.sha256(("hydrography-v1:name:" + feature_id).encode()).digest()
    left = ("Aru", "Bel", "Cor", "Dra", "Eri", "Fen", "Gor", "Hes", "Ily", "Jor", "Kel", "Lun", "Mor", "Ner", "Oth", "Pyr")
    right = ("a", "en", "is", "or", "um", "eth", "ara", "ion", "e", "os", "yr", "an", "iel", "oth", "une", "as")
    return left[digest[0] & 15] + right[digest[1] & 15] + left[digest[2] & 15]


def clean_name(value):
    if not isinstance(value, str):
        raise ValueError("hydrographic name must be text")
    if any(unicodedata.category(ch).startswith("C") or unicodedata.category(ch) in ("Zl", "Zp") for ch in value):
        raise ValueError("invalid hydrographic name")
    value = unicodedata.normalize("NFC", value).strip()
    if not 1 <= len(value) <= 80:
        raise ValueError("invalid hydrographic name")
    return value


def _anchor(cells, ice, width, height):
    cellset = set(cells)
    edge = [i for i in cells if any(n not in cellset for n in _neighbors(i, width, height))]
    distance = {i: 0 for i in edge}
    queue = list(edge)
    head = 0
    while head < len(queue):
        cell = queue[head]
        head += 1
        for adjacent in _neighbors(cell, width, height):
            if adjacent in cellset and adjacent not in distance:
                distance[adjacent] = distance[cell] + 1
                queue.append(adjacent)
    interior = [i for i in cells if ice[i] == "0"] or cells
    return min(interior, key=lambda i: (-distance.get(i, 0), i))


def build_hydrography(geometry, naming="none", custom=None):
    if naming not in ("none", "generated"):
        raise ValueError("unsupported hydrographic naming mode")
    custom = {} if custom is None else custom
    if not isinstance(custom, dict):
        raise ValueError("hydrographic custom names must be a mapping")
    custom = dict(custom)
    surface = geometry["surface"]
    width, height = geometry["planet"]["width"], geometry["planet"]["height"]
    terrain = geometry["terrain_grid"]
    materials = surface["materials"]
    masks = materials["lake_mask"]
    ice = materials["ice_mask"]
    water_cells = [i for i, code in enumerate(terrain) if code == "o" and masks[i] == "0"]
    ocean_components = _components(water_cells, width, height)
    largest = min(ocean_components, key=lambda c: (-len(c), c[0])) if ocean_components else []
    ocean_set = set(largest)
    features = []

    def add(kind, material, cells, family):
        if not cells:
            return
        cells = sorted(set(cells))
        minimum = cells[0]
        fid = f"{geometry['planet']['id']}-{family}-{minimum}"
        anchor = _anchor(cells, ice, width, height)
        name = None
        source = "none"
        if naming == "generated":
            name, source = _name(fid), "generated"
        if fid in custom:
            name, source = clean_name(custom.pop(fid)), "custom"
        features.append({"id": fid, "kind": kind, "material": material, "cells": cells,
                         "anchor": anchor, "name": name, "name_source": source})

    for component in ocean_components:
        add("ocean" if set(component) == ocean_set else "sea", "water", component,
            "ocean" if set(component) == ocean_set else "sea")
    selected = [i for i, value in enumerate(masks) if value == "1"]
    for component in _components(selected, width, height):
        add("lake", materials["lake_material"], component, materials["lake_material"])
    for river in surface["rivers"]:
        path = [y * width + (x % width) for x, y in river["points"] if 0 <= y < height]
        cells = sorted(set(path))
        if cells:
            # Preserve saved route order; use dry, ice-free land where possible.
            # Degenerate routes fall back deterministically to their saved midpoint.
            land = [i for i in path if terrain[i] != "o"]
            candidates = [i for i in land if masks[i] == "0" and ice[i] == "0"] or land or path
            name = _name(river["id"]) if naming == "generated" else None
            source = "generated" if naming == "generated" else "none"
            if river["id"] in custom:
                name, source = clean_name(custom.pop(river["id"])), "custom"
            features.append({"id": river["id"], "kind": "river", "material": "water", "cells": cells,
                             "anchor": candidates[len(candidates)//2],
                             "name": name, "name_source": source})
    if custom:
        raise ValueError("custom hydrographic name references an unknown feature")
    return {"version": "hydrography-v1", "naming": naming, "features": features}


def validate_hydrography(geometry, value, naming):
    if not isinstance(value, dict) or set(value) != {"version", "naming", "features"} or value.get("version") != "hydrography-v1" or value.get("naming") != naming:
        raise ValueError("invalid hydrography contract")
    features = value.get("features")
    if not isinstance(features, list) or len(features) > 4096:
        raise ValueError("invalid hydrography feature list")
    seen = set()
    for feature in features:
        if not isinstance(feature, dict) or set(feature) != {"id", "kind", "material", "cells", "anchor", "name", "name_source"}:
            raise ValueError("invalid hydrography feature")
        if not isinstance(feature["id"], str) or not feature["id"] or len(feature["id"]) > 512 or feature["id"] in seen:
            raise ValueError("invalid hydrography feature ID")
        seen.add(feature["id"])
        cells = feature["cells"]
        size = geometry["planet"]["width"] * geometry["planet"]["height"]
        if not isinstance(cells, list) or not cells or len(cells) > size or any(type(i) is not int for i in cells) or cells != sorted(set(cells)):
            raise ValueError("invalid hydrography feature cells")
        if type(feature["anchor"]) is not int or feature["anchor"] not in cells:
            raise ValueError("invalid hydrography feature anchor")
        source, name = feature["name_source"], feature["name"]
        if source not in ("none", "generated", "custom"):
            raise ValueError("invalid hydrography name source")
        if ((source == "none") != (name is None) or
                (source == "none" and naming != "none") or
                (source == "generated" and naming != "generated")):
            raise ValueError("invalid hydrography name configuration")
        if source == "custom" and name is None:
            raise ValueError("custom hydrographic names must have text")
        if name is not None and clean_name(name) != name:
            raise ValueError("hydrographic names must be canonical")
    expected = build_hydrography(geometry, naming)
    # Geometry, stable identity, ordering, material and anchor are derived only
    # from the saved arrays and paths. Names may be operator-authored.
    if len(features) != len(expected["features"]):
        raise ValueError("hydrography coverage invariant failed")
    for actual, derived in zip(features, expected["features"]):
        if any(actual[key] != derived[key] for key in ("id", "kind", "material", "cells", "anchor")):
            raise ValueError("hydrography geometry invariant failed")
        if actual["name_source"] == "generated" and actual["name"] != derived["name"]:
            raise ValueError("generated hydrographic name invariant failed")
    return True
