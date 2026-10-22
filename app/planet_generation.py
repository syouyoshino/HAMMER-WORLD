"""Opt-in, integer-quantized fictional geography; never regenerates saved worlds.

Bounded planar 64×40 grid, ocean boundary, four-neighbour drainage. Depression
filling raises terrain before persistence; no lakes or physical erosion model.
The existing six terrain classes and rectangular provinces remain authoritative.
"""
import hashlib
import heapq

VERSION = "planet-v2"
SURFACE_VERSIONS = (VERSION, "planet-v3")
WIDTH, HEIGHT, SEA_LEVEL = 64, 40, 400
FIELDS = ("elevation", "temperature", "moisture", "drainage", "accumulation")
SURFACE_KEYS = {"version", "sea_level", *FIELDS, "rivers"}


def _value(seed, domain, x, y):
    return int.from_bytes(hashlib.sha256(f"{seed}:planet-v2:{domain}:{x}:{y}".encode()).digest()[:4], "big") % 1001


def _noise(seed, domain, x, y, scale):
    # Integer smoothstep and bilinear interpolation, independent of traversal.
    gx, dx = divmod(x, scale)
    gy, dy = divmod(y, scale)
    def smooth(n):
        t = n * 1000 // scale
        return t * t * (3000 - 2 * t) // 1_000_000
    tx, ty = smooth(dx), smooth(dy)
    a = (_value(seed, domain, gx, gy) * (1000-tx) + _value(seed, domain, gx+1, gy) * tx) // 1000
    b = (_value(seed, domain, gx, gy+1) * (1000-tx) + _value(seed, domain, gx+1, gy+1) * tx) // 1000
    return (a * (1000-ty) + b * ty) // 1000


def _neighbors(index, width, height):
    x, y = index % width, index // width
    return [ny*width+nx for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))
            if 0 <= nx < width and 0 <= ny < height]


def generate_planet_v2(namespace, seed, planet_class="terrestrial"):
    if planet_class not in ("terrestrial", "oceanic", "arid", "ice"):
        raise ValueError("unsupported fictional demo planet class")
    width, height = WIDTH, HEIGHT
    elevation = []
    for y in range(height):
        for x in range(width):
            broad = sum(_noise(seed, f"height-{scale}", x, y, scale)*weight
                        for scale, weight in ((24,5),(12,3),(6,1),(3,1))) // 10
            # Bounded ocean rim and central continental support guarantee useful
            # land provinces without relocating any saved settlement.
            edge = min(x, y, width-1-x, height-1-y)
            support = max(0, 160 - abs(x-32)*4 - abs(y-20)*5)
            value = broad + support - (65 if planet_class == "oceanic" else 0)
            if value > 460:
                value += max(0, _noise(seed, "ridges", x, y, 8)-350)
            elevation.append(max(0, min(850, value, 250 + edge*70)))
    return _finish_planet(namespace, seed, planet_class, elevation, VERSION)


def generate_planet_v3(namespace, seed, planet_class="terrestrial"):
    """Organic strategic terrain, retaining the bounded simulation grid.

    Signed, warped continental influences determine coast shape. A percentile
    chooses a fictional class-dependent sea coverage; it shifts the continuous
    height field, rather than flattening values at a clipping threshold.
    Narrow ridged fields add actual persisted relief. No generated detail is
    inferred on the client and no previously saved geography is regenerated.
    """
    if planet_class not in ("terrestrial", "oceanic", "arid", "ice"):
        raise ValueError("unsupported fictional demo planet class")
    width, height = WIDTH, HEIGHT
    # Separate domains leave existing v2 fields and identities untouched.
    domain = f"{seed}:continental-ridges-v3"
    centers = [(16+_value(domain,"center-x",n,0)%33,
                13+_value(domain,"center-y",n,0)%15,
                15+_value(domain,"radius-x",n,0)%8,
                8+_value(domain,"radius-y",n,0)%5) for n in range(3)]
    scores, warped = [], []
    for y in range(height):
        for x in range(width):
            wx = x+(_noise(domain,"warp-x",x,y,17)-500)//100
            wy = y+(_noise(domain,"warp-y",x,y,13)-500)//130
            warped.append((wx,wy))
            continent = max(1000-(wx-cx)**2*1000//(rx*rx)-(wy-cy)**2*1000//(ry*ry)
                            for cx,cy,rx,ry in centers)
            coast = (_noise(domain,"coast-9",wx,wy,9)*3+
                     _noise(domain,"coast-4",wx,wy,4)*2)//5-500
            edge = min(x,y,width-1-x,height-1-y)
            # A smooth offshore falloff changes the signed mask, not elevation
            # caps. Only the outermost boundary is a mandatory ocean outlet.
            offshore = max(0,7-edge)**2*35
            scores.append(continent+coast*3//4-offshore)
    fraction = {"terrestrial":48,"oceanic":29,"arid":45,"ice":42}[planet_class]
    fraction += _value(domain,"land-fraction",0,0)%11-5
    threshold = sorted(scores)[len(scores)*(100-fraction)//100]
    elevation = []
    for i, score in enumerate(scores):
        x, y = i%width, i//width
        delta = score-threshold
        if delta <= 0 or x in (0,width-1) or y in (0,height-1):
            elevation.append(max(0,min(400,395+delta//4)))
            continue
        wx,wy = warped[i]
        # Ridged noise peaks along narrow contours instead of broad positive
        # blobs. Multiple wavelengths break up long uniform crests.
        ridge = 1000-abs(2*_noise(domain,"ridge-8",wx,wy,8)-1000)
        detail = 1000-abs(2*_noise(domain,"ridge-4",wx,wy,4)-1000)
        relief = ridge**3*300//1_000_000_000+detail**3*80//1_000_000_000
        inland = min(1000,delta*6)
        elevation.append(401+min(180,delta//4)+relief*inland//1000)
    return _finish_planet(namespace, seed, planet_class, elevation, "planet-v3")


def _finish_planet(namespace, seed, planet_class, elevation, version):
    width, height = WIDTH, HEIGHT
    ocean = {i for i, value in enumerate(elevation) if value <= SEA_LEVEL}
    # Priority flood: each land cell gets a previously visited downstream parent.
    # Raising enclosed depressions eliminates ambiguous sinks and cycles.
    heap = [(elevation[i], i) for i in ocean]
    heapq.heapify(heap)
    visited = set(ocean)
    drainage = [-1] * (width*height)
    order = []
    while heap:
        level, i = heapq.heappop(heap)
        order.append(i)
        for j in _neighbors(i, width, height):
            if j in visited:
                continue
            visited.add(j)
            drainage[j] = i
            elevation[j] = max(elevation[j], level+1)
            heapq.heappush(heap, (elevation[j], j))
    peak = max(elevation)
    if peak > 1000:
        elevation = [v if v <= SEA_LEVEL else 401+(v-401)*599//(peak-401) for v in elevation]
    accumulation = [1] * (width*height)
    for i in reversed(order):
        if drainage[i] >= 0:
            accumulation[drainage[i]] += accumulation[i]
    temperature, moisture, terrain = [], [], []
    for y in range(height):
        air = 750
        for x in range(width):
            i = y*width+x
            altitude = max(0, elevation[i]-SEA_LEVEL)
            temp = 950-abs(2*y-(height-1))*19-altitude//2
            temp += {"terrestrial":0,"oceanic":0,"arid":120,"ice":-390}[planet_class]
            temperature.append(max(0, min(1000, temp)))
            if i in ocean:
                air = 900
            else:
                air = max(80, air-8-max(0, elevation[i]-elevation[i-1])//2)
            wet = (_noise(seed, "moisture", x, y, 9)*3 + air*2)//5
            wet += {"terrestrial":0,"oceanic":100,"arid":-310,"ice":-100}[planet_class]
            wet = max(0, min(1000, wet))
            moisture.append(wet)
            if i in ocean:
                code = "o"
            elif any(j in ocean for j in _neighbors(i, width, height)):
                code = "c"
            elif elevation[i] >= 680 or temperature[i] < 160 or wet < 210:
                code = "r"
            elif wet > 650 and elevation[i] < 490:
                code = "m"
            elif wet > 460 and temperature[i] > 280:
                code = "f"
            else:
                code = "p"
            terrain.append(code)
    # Headwater paths share downstream segments and end at their ocean outlet.
    river_cells = {i for i in range(width*height) if i not in ocean and accumulation[i] >= 22}
    has_tributary = {drainage[i] for i in river_cells}
    rivers = []
    for source in sorted(river_cells-has_tributary):
        path, i = [], source
        while i >= 0:
            path.append([i % width, i // width])
            if i in ocean:
                break
            i = drainage[i]
        if len(path) >= 4:
            rivers.append({"id":f"{namespace}-river-{source:04d}", "points":path})
    provinces = [{"id":f"{namespace}-p-{py:02d}-{px:02d}","name":f"Province {py*8+px+1:02d}",
                  "x":px*8,"y":py*8,"width":8,"height":8} for py in range(5) for px in range(8)]
    result = {"planet":{"id":f"{namespace}-planet-001","name":"Kestrel's Reach","width":width,"height":height},
              "provinces":provinces,"terrain_grid":"".join(terrain),
              "surface":{"version":version,"sea_level":SEA_LEVEL,"elevation":elevation,
                         "temperature":temperature,"moisture":moisture,"drainage":drainage,
                         "accumulation":accumulation,"rivers":rivers}}
    validate_surface(result)
    return result


def project_surface(geometry):
    """Explicit nested public allowlist, including defensive copies of arrays."""
    surface = geometry.get("surface")
    if not isinstance(surface, dict) or surface.get("version") not in SURFACE_VERSIONS:
        return {}
    return {"surface":{"version":surface["version"],"sea_level":surface["sea_level"],
                       **{key:list(surface[key]) for key in FIELDS},
                       "rivers":[{"id":r["id"],"points":[[p[0],p[1]] for p in r["points"]]} for r in surface["rivers"]]}}


def validate_surface(geometry):
    """Validate optional new geography on creation/import/read; absent means v1."""
    if "surface" not in geometry:
        return
    surface = geometry["surface"]
    if not isinstance(surface, dict) or set(surface) != SURFACE_KEYS or surface.get("version") not in SURFACE_VERSIONS or type(surface.get("sea_level")) is not int or surface["sea_level"] != SEA_LEVEL:
        raise ValueError("unsupported planet surface contract")
    planet = geometry.get("planet")
    if not isinstance(planet,dict):
        raise ValueError("invalid planet surface dimensions")
    width, height = planet.get("width"), planet.get("height")
    if type(width) is not int or type(height) is not int or (width,height) != (WIDTH,HEIGHT):
        raise ValueError("versioned planet surface requires grid64x40")
    size = width*height
    for key in FIELDS:
        low, high = (-1,size-1) if key == "drainage" else (1,size) if key == "accumulation" else (0,1000)
        values = surface[key]
        if not isinstance(values,list) or len(values) != size or any(type(v) is not int or not low <= v <= high for v in values):
            raise ValueError("invalid planet surface field")
    codes, elevation, drainage = geometry["terrain_grid"], surface["elevation"], surface["drainage"]
    if not isinstance(codes,str) or len(codes) != size or any(c not in "ocprfm" for c in codes):
        raise ValueError("invalid planet surface terrain")
    for i, j in enumerate(drainage):
        ocean = codes[i] == "o"
        if ocean != (elevation[i] <= SEA_LEVEL) or (ocean and j != -1) or (not ocean and (j not in _neighbors(i,width,height) or elevation[j] > elevation[i])):
            raise ValueError("invalid planet surface drainage")
        if not ocean and ((codes[i] == "c") != any(codes[n] == "o" for n in _neighbors(i,width,height))):
            raise ValueError("invalid planet surface coast")
    # Topological leaf removal checks cycles and exact contributing cell counts.
    indegree, expected = [0]*size, [1]*size
    for j in drainage:
        if j >= 0:
            indegree[j] += 1
    pending = [i for i, n in enumerate(indegree) if n == 0]
    processed = 0
    while pending:
        i = pending.pop()
        processed += 1
        j = drainage[i]
        if j >= 0:
            expected[j] += expected[i]
            indegree[j] -= 1
            if indegree[j] == 0:
                pending.append(j)
    if processed != size or expected != surface["accumulation"]:
        raise ValueError("cyclic or inconsistent planet drainage")
    rivers = surface["rivers"]
    if not isinstance(rivers,list) or len(rivers) > size:
        raise ValueError("invalid planet rivers")
    ids = set()
    for river in rivers:
        if not isinstance(river,dict) or set(river) != {"id","points"} or not isinstance(river["id"],str) or not river["id"] or river["id"] in ids:
            raise ValueError("invalid planet river identity")
        ids.add(river["id"])
        points = river["points"]
        if not isinstance(points,list) or not 4 <= len(points) <= size or any(not isinstance(p,list) or len(p) != 2 or any(type(v) is not int for v in p) or not 0 <= p[0] < width or not 0 <= p[1] < height for p in points):
            raise ValueError("invalid planet river path")
        indices = [y*width+x for x,y in points]
        if codes[indices[0]] == "o" or codes[indices[-1]] != "o" or any(drainage[a] != b for a,b in zip(indices,indices[1:])):
            raise ValueError("planet river must follow drainage to ocean")
