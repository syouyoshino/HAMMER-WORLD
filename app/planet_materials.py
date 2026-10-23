"""Saved V8 composition layers; no terrain or simulation changes."""
import hashlib
import heapq

LAKE_MATERIALS = ("none", "water", "hydrocarbon", "lava")
POLAR_CAPS = ("none", "water-ice")
MATERIAL_KEYS = {"lake_material", "polar_caps", "lake_mask", "ice_mask"}


def validate_choices(preset, lake_material, polar_caps):
    if lake_material not in LAKE_MATERIALS or polar_caps not in POLAR_CAPS:
        raise ValueError("unsupported planet surface material")
    if lake_material == "lava" and polar_caps == "water-ice":
        raise ValueError("lava with water-ice caps is unsupported")
    if preset == "frozen" and lake_material in ("water", "lava"):
        raise ValueError("water/lava lakes require a nonfrozen world")
    if lake_material == "hydrocarbon" and preset != "frozen":
        raise ValueError("hydrocarbon lakes require a frozen world")


def reserved_anchors(geometry):
    """Match provinceLand's nearest land centroid, including coast; reserve a halo."""
    w = geometry["planet"]["width"]
    h = geometry["planet"]["height"]
    codes = geometry["terrain_grid"]
    reserved = set()
    for p in geometry["provinces"]:
        cells = [y*w+x for y in range(p["y"], p["y"]+p["height"])
                 for x in range(p["x"], p["x"]+p["width"]) if codes[y*w+x] != "o"]
        if not cells:
            continue
        # Integer centroid distance preserves row-major tie breaking without floats.
        n = len(cells)
        sx, sy = sum(i % w for i in cells), sum(i // w for i in cells)
        anchor = min(cells, key=lambda i: (n*(i % w)-sx)**2 + (n*(i // w)-sy)**2)
        ax, ay = anchor % w, anchor // w
        reserved.update(y*w+(x % w) for y in range(max(0, ay-1), min(h, ay+2))
                        for x in range(ax-1, ax+2))
    return reserved


def _value(seed, domain, ordinal):
    return int.from_bytes(hashlib.sha256(f"{seed}:planet-v8:{domain}:{ordinal}".encode()).digest()[:4], "big")


def cap_edges(seed, width, pole):
    # Eight coarse periodic knots, linearly interpolated in fixed point. The
    # last knot joins the first, including the cell-centre interval at the seam.
    knots = [5 + _value(seed, f"cap-{pole}", i) % 8 for i in range(8)]
    return [(knots[(x*8)//width]*(width-(x*8)%width) +
             knots[((x*8)//width+1)%8]*((x*8)%width)) // width for x in range(width)]


def generate_materials(geometry, seed, lake_material, polar_caps):
    validate_choices(geometry["surface"]["preset"], lake_material, polar_caps)
    w, h = geometry["planet"]["width"], geometry["planet"]["height"]
    size = w*h
    ice, lake = ["0"]*size, ["0"]*size
    if polar_caps != "none":
        north, south = cap_edges(seed, w, "north"), cap_edges(seed, w, "south")
        for y in range(h):
            for x in range(w):
                if y < north[x] or y >= h-south[x]:
                    ice[y*w+x] = "1"
    if lake_material != "none":
        reserved = reserved_anchors(geometry)
        eligible = {i for i, code in enumerate(geometry["terrain_grid"])
                    if code not in "oc" and i not in reserved and ice[i] == "0"}
        if not eligible:
            raise ValueError("no eligible land for enabled lake material")
        elevation = geometry["surface"]["elevation"]
        # Grow a handful of connected lowland basins. Independent hash domains
        # rank centres and break equal elevation ties; the frontier is 4-connected.
        ranked = sorted(eligible, key=lambda i: (elevation[i], _value(seed, "basin-centre", i)))
        used = set()
        for ordinal in range(7):
            centre = next((i for i in ranked if i not in used and
                           all(min(abs(i%w-j%w), w-abs(i%w-j%w))**2 + (i//w-j//w)**2 > 100
                               for j in used)), None)
            if centre is None:
                break
            target = 24 + _value(seed, "basin-area", ordinal) % 57
            cx, cy = centre % w, centre // w
            frontier = [(0, centre)]
            queued = {centre}
            basin = set()
            while frontier and len(basin) < target:
                _, i = heapq.heappop(frontier)
                basin.add(i)
                x, y = i % w, i // w
                for j in (y*w+(x-1)%w, y*w+(x+1)%w,
                          (y-1)*w+x if y else -1, (y+1)*w+x if y+1<h else -1):
                    if j not in eligible or j in used or j in queued:
                        continue
                    dx = min(abs(j%w-cx), w-abs(j%w-cx))
                    dy = j//w-cy
                    priority = elevation[j] + (dx*dx+dy*dy)*5
                    heapq.heappush(frontier, (priority, j))
                    queued.add(j)
            used.update(basin)
        for i in used:
            lake[i] = "1"
    return {"lake_material": lake_material, "polar_caps": polar_caps,
            "lake_mask": "".join(lake), "ice_mask": "".join(ice)}


def validate_materials(geometry):
    surface = geometry["surface"]
    materials = surface.get("materials")
    if not isinstance(materials, dict) or set(materials) != MATERIAL_KEYS:
        raise ValueError("invalid planet materials contract")
    lm, pc = materials["lake_material"], materials["polar_caps"]
    validate_choices(surface["preset"], lm, pc)
    size = geometry["planet"]["width"]*geometry["planet"]["height"]
    for key, choice in (("lake_mask", lm), ("ice_mask", pc)):
        mask = materials[key]
        if not isinstance(mask, str) or len(mask) != size or any(c not in "01" for c in mask) or ((choice == "none") != ("1" not in mask)):
            raise ValueError("invalid planet material mask")
    lake, ice = materials["lake_mask"], materials["ice_mask"]
    reserved = reserved_anchors(geometry)
    if any(lake[i] == "1" and (ice[i] == "1" or code in "oc" or i in reserved)
           for i, code in enumerate(geometry["terrain_grid"])):
        raise ValueError("invalid planet material placement")
    # Caps are solid from each pole to a single irregular boundary per longitude.
    if pc != "none":
        w, h = geometry["planet"]["width"], geometry["planet"]["height"]
        edges = []
        for x in range(w):
            column = "".join(ice[y*w+x] for y in range(h))
            north = len(column)-len(column.lstrip("1"))
            south = len(column)-len(column.rstrip("1"))
            if not 3 <= north <= 16 or not 3 <= south <= 16 or column != "1"*north+"0"*(h-north-south)+"1"*south:
                raise ValueError("invalid polar cap continuity")
            edges.append((north, south))
        if any(abs(edges[x][p]-edges[(x+1)%w][p]) > 1 for x in range(w) for p in (0, 1)):
            raise ValueError("invalid periodic polar cap boundary")
