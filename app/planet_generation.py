"""Opt-in, integer-quantized fictional geography; never regenerates saved worlds.

Bounded planar 64×40 grid, ocean boundary, four-neighbour drainage. Depression
filling raises terrain before persistence; no lakes or physical erosion model.
The existing six terrain classes and rectangular provinces remain authoritative.
"""
import hashlib
import heapq

VERSION = "planet-v2"
SURFACE_VERSIONS = (VERSION, "planet-v3", "planet-v4", "planet-v5")
WIDTH, HEIGHT, SEA_LEVEL = 64, 40, 400
V5_WIDTH, V5_HEIGHT = 128, 80
FIELDS = ("elevation", "temperature", "moisture", "drainage", "accumulation")
SURFACE_KEYS = {"version", "sea_level", *FIELDS, "rivers"}
PRESETS = ("continental", "archipelago", "oceanic", "arid", "barren", "frozen")
PLANET_CLASSES = {"continental":"terrestrial", "archipelago":"oceanic", "oceanic":"oceanic",
                  "arid":"arid", "barren":"barren", "frozen":"ice"}


def _planet_v4_value(seed, domain, x=0, y=0):
    return int.from_bytes(hashlib.sha256(f"{seed}:planet-v4:{domain}:{x}:{y}".encode()).digest()[:4], "big") % 1001


def resolve_planet_presets(seed, planet_ids, preset="auto", overrides=None):
    """Resolve explicit or stable per-node choices before any persistence begins."""
    if preset not in ("auto", *PRESETS):
        raise ValueError("unsupported planet preset")
    overrides = {} if overrides is None else overrides
    if not isinstance(overrides, dict):
        raise ValueError("planet preset overrides must be a mapping")
    if any(not isinstance(key, str) or key not in planet_ids for key in overrides):
        raise ValueError("planet preset override must reference a known planet node")
    if any(value not in PRESETS for value in overrides.values()):
        raise ValueError("unsupported planet preset override")
    choices = {}
    for planet_id in planet_ids:
        if planet_id in overrides:
            choices[planet_id] = overrides[planet_id]
        elif preset != "auto":
            choices[planet_id] = preset
        else:
            value = _planet_v4_value(seed, f"planet-preset:{planet_id}")
            choices[planet_id] = PRESETS[value * len(PRESETS) // 1001]
    return choices


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


def generate_planet_v4(namespace, seed, preset):
    """Generate an explicit fictional surface preset, separate from V1–V3."""
    if preset not in PRESETS:
        raise ValueError("unsupported planet preset")
    size = WIDTH * HEIGHT
    if preset in ("arid", "barren", "frozen"):
        elevation, temperature, moisture, terrain = [], [], [], []
        for y in range(HEIGHT):
            for x in range(WIDTH):
                noise = _noise(seed, f"v4-{preset}-relief", x, y, 11)
                elevation.append(520 + noise // 3)
                temperature.append((40 + noise // 10) if preset == "frozen" else
                                   330 + _noise(seed, "v4-arid-temperature", x, y, 19) // 2)
                moisture.append(0 if preset in ("arid", "barren") else 500 + noise // 4)
                if preset == "barren":
                    terrain.append("r")
                elif preset == "arid":
                    terrain.append("r" if noise > 590 else "p")
                else:
                    terrain.append("r" if noise > 680 else "p")
        geo = _geometry(namespace, "planet-v4", preset, None, elevation, temperature, moisture,
                        [-1] * size, [1] * size, [], "".join(terrain))
        validate_surface(geo)
        return geo

    domain = f"{seed}:planet-v4:{preset}"
    centers = []
    if preset == "continental":
        side = _planet_v4_value(domain, "continent-edge") % 4
        if side == 0:
            centers.append((7, 17 + _planet_v4_value(domain,"continent-offset") % 6, 18, 13))
        elif side == 1:
            centers.append((56, 17 + _planet_v4_value(domain,"continent-offset") % 6, 18, 13))
        elif side == 2:
            centers.append((28 + _planet_v4_value(domain,"continent-offset") % 8, 5, 20, 15))
        else:
            centers.append((28 + _planet_v4_value(domain,"continent-offset") % 8, 34, 20, 15))
        for n in range(3):
            centers.append((7 + _planet_v4_value(domain,"offshore-x",n) % 50,
                            6 + _planet_v4_value(domain,"offshore-y",n) % 28, 3, 2))
    else:
        count = 9 if preset == "archipelago" else 7
        margin_x,margin_y=(9,7) if preset=="archipelago" else (7,6)
        candidates={(margin_x + _planet_v4_value(domain,"candidate-x",n) * (WIDTH-2*margin_x-1)//1001,
                     margin_y + _planet_v4_value(domain,"candidate-y",n) * (HEIGHT-2*margin_y-1)//1001)
                    for n in range(256)}
        ordered=sorted(candidates,key=lambda point:(_planet_v4_value(domain,"candidate-order",*point),point))
        minimum=(14,12,10,8) if preset=="archipelago" else (12,10,8)
        centers_xy=[]
        for separation in minimum:
            centers_xy=[]
            for point in ordered:
                if all((point[0]-x)**2+(point[1]-y)**2>=separation**2 for x,y in centers_xy):
                    centers_xy.append(point)
                    if len(centers_xy)==count: break
            if len(centers_xy)==count: break
        for n,(x,y) in enumerate(centers_xy):
            if preset == "archipelago":
                rx = 4 + _planet_v4_value(domain,"island-rx",n) % 4
                ry = 3 + _planet_v4_value(domain,"island-ry",n) % 2
            else:
                rx = 3 + _planet_v4_value(domain,"island-rx",n) % 4
                ry = 2 + _planet_v4_value(domain,"island-ry",n) % 3
            centers.append((x,y,rx,ry))

    elevation = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            # Shared smooth warping bends coastlines without imposing a grid
            # of identical oval islands or adding disconnected noise specks.
            wx = x * 1000 + (_noise(domain, "coast-warp-x", x, y, 9) - 500) * 3
            wy = y * 1000 + (_noise(domain, "coast-warp-y", x, y, 7) - 500) * 3
            influence = max(1000 - (((wx-cx*1000)**2 // (rx*rx*1000)) +
                                    ((wy-cy*1000)**2 // (ry*ry*1000)))
                            for cx,cy,rx,ry in centers)
            edge_noise = _noise(domain, "island-coast", x, y, 7)
            land = influence + (edge_noise - 500) // 3 > 0
            if land:
                relief = _noise(domain, "land-relief", x, y, 9)
                elevation.append(425 + max(0, influence) // 6 + relief // 5)
            else:
                depth = _noise(domain, "ocean-depth", x, y, 13)
                # Bathymetry stays below sea level throughout its noise range;
                # deeper water must never become an unrelated land patch.
                elevation.append(SEA_LEVEL - 20 - depth * 300 // 1000)
    geo = _finish_planet(namespace, seed, PLANET_CLASSES[preset], elevation, "planet-v2")
    geo["surface"].update({"version":"planet-v4", "preset":preset, "hydrology":"ocean-draining"})
    validate_surface(geo)
    return geo


def generate_planet_v5(namespace, seed, preset):
    """Generate an opt-in 128x80 surface with stable 16x16 province cells."""
    if preset not in PRESETS:
        raise ValueError("unsupported planet preset")
    width, height, size = V5_WIDTH, V5_HEIGHT, V5_WIDTH * V5_HEIGHT
    def noise(domain, x, y, scale):
        # Independent V5 domains; _noise's interpolation and quantization are
        # reused while the versioned domain keeps every value separate.
        return _noise(seed, f"planet-v5:{preset}:{domain}", x, y, scale)
    def value(domain, ordinal=0):
        raw=f"{seed}:planet-v5:{preset}:{domain}:{ordinal}".encode()
        return int.from_bytes(hashlib.sha256(raw).digest()[:4],"big")
    elevation = []
    if preset in ("arid", "barren", "frozen"):
        temperature, moisture, terrain = [], [], []
        for y in range(height):
            for x in range(width):
                relief = noise("relief", x, y, 19)
                elevation.append(540 + relief // 3)
                temperature.append(40 + relief // 10 if preset == "frozen" else 330 + noise("temperature", x, y, 31) // 2)
                moisture.append(0 if preset in ("arid", "barren") else 500 + relief // 4)
                terrain.append("r" if preset == "barren" or relief > (600 if preset == "arid" else 700) else "p")
        provinces = _province_rectangles(namespace, width, height, 16)
        geo = {"planet":{"id":f"{namespace}-planet-001","name":"Kestrel's Reach","width":width,"height":height},
               "provinces":provinces,"terrain_grid":"".join(terrain),
               "surface":{"version":"planet-v5","preset":preset,"hydrology":"none","sea_level":None,
                          "elevation":elevation,"temperature":temperature,"moisture":moisture,
                          "drainage":[-1]*size,"accumulation":[1]*size,"rivers":[]}}
        validate_surface(geo)
        return geo
    # Versioned, full-resolution land masks produce distinct continental,
    # island-chain and oceanic distributions from independent V5 domains.
    centers=[]
    if preset=="continental":
        side=value("continent-edge")%4
        if side==0: centers.append((10,30+value("continent-offset")%20,54,31))
        elif side==1: centers.append((118,30+value("continent-offset")%20,54,31))
        elif side==2: centers.append((50+value("continent-offset")%28,5,48,36))
        else: centers.append((50+value("continent-offset")%28,75,48,36))
        for n in range(5): centers.append((10+value("offshore-x",n)%109,9+value("offshore-y",n)%63,5,4))
    else:
        count=13 if preset=="archipelago" else 7
        points=sorted({(8+value("island-x",n)%113,7+value("island-y",n)%67) for n in range(512)},
                      key=lambda point:(value("island-order",point[0]*1000+point[1]),point))
        separation=17 if preset=="archipelago" else 20
        chosen=[]
        for point in points:
            if all((point[0]-x)**2+(point[1]-y)**2>=separation**2 for x,y in chosen): chosen.append(point)
            if len(chosen)==count: break
        for n,(x,y) in enumerate(chosen):
            rx=(7+value("island-rx",n)%8) if preset=="archipelago" else (5+value("island-rx",n)%7)
            ry=(5+value("island-ry",n)%6) if preset=="archipelago" else (4+value("island-ry",n)%5)
            centers.append((x,y,rx,ry))
    for y in range(height):
        for x in range(width):
            wx=x+(_noise(seed,f"planet-v5:{preset}:warp-x",x,y,23)-500)//180
            wy=y+(_noise(seed,f"planet-v5:{preset}:warp-y",x,y,19)-500)//200
            influence=max(1000-((wx-cx)**2*1000//(rx*rx))-((wy-cy)**2*1000//(ry*ry)) for cx,cy,rx,ry in centers)
            coast=noise("coast",x,y,11)
            land=influence+(coast-500)//3>0 and x not in (0,width-1) and y not in (0,height-1)
            elevation.append(425+max(0,influence)//6+noise("land-relief",x,y,13)//5 if land
                             else SEA_LEVEL-20-noise("ocean-depth",x,y,17)*300//1000)
    geo = _finish_planet(namespace, seed, PLANET_CLASSES[preset], elevation, "planet-v5",
                         width=width, height=height, province_size=16, surface_preset=preset)
    geo["surface"].update({"version":"planet-v5","preset":preset,"hydrology":"ocean-draining"})
    validate_surface(geo)
    return geo


def _province_rectangles(namespace, width, height, cell):
    return [{"id":f"{namespace}-p-{py:02d}-{px:02d}","name":f"Province {py*8+px+1:02d}",
             "x":px*cell,"y":py*cell,"width":cell,"height":cell}
            for py in range(height//cell) for px in range(width//cell)]


def _geometry(namespace, version, preset, sea_level, elevation, temperature, moisture,
              drainage, accumulation, rivers, terrain):
    provinces = [{"id":f"{namespace}-p-{py:02d}-{px:02d}","name":f"Province {py*8+px+1:02d}",
                  "x":px*8,"y":py*8,"width":8,"height":8} for py in range(5) for px in range(8)]
    return {"planet":{"id":f"{namespace}-planet-001","name":"Kestrel's Reach","width":WIDTH,"height":HEIGHT},
            "provinces":provinces,"terrain_grid":terrain,
            "surface":{"version":version,"preset":preset,"hydrology":"none","sea_level":sea_level,
                       "elevation":elevation,"temperature":temperature,"moisture":moisture,
                       "drainage":drainage,"accumulation":accumulation,"rivers":rivers}}


def _finish_planet(namespace, seed, planet_class, elevation, version, *, width=WIDTH, height=HEIGHT, province_size=8, surface_preset=None):
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
            latitude=abs(2*y-(height-1))
            if height>HEIGHT: latitude=latitude*HEIGHT//height
            temp = 950-latitude*19-altitude//2
            temp += {"terrestrial":0,"oceanic":0,"arid":120,"ice":-390}[planet_class]
            temperature.append(max(0, min(1000, temp)))
            if i in ocean:
                air = 900
            else:
                air = max(80, air-8-max(0, elevation[i]-elevation[i-1])//2)
            moisture_noise=_noise(seed,"planet-v5:moisture",x,y,13) if version=="planet-v5" else _noise(seed,"moisture",x,y,9)
            wet = (moisture_noise*3 + air*2)//5
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
    provinces = _province_rectangles(namespace,width,height,province_size)
    result = {"planet":{"id":f"{namespace}-planet-001","name":"Kestrel's Reach","width":width,"height":height},
              "provinces":provinces,"terrain_grid":"".join(terrain),
              "surface":{"version":version,"sea_level":SEA_LEVEL,"elevation":elevation,
                         "temperature":temperature,"moisture":moisture,"drainage":drainage,
                         "accumulation":accumulation,"rivers":rivers}}
    if version == "planet-v5":
        result["surface"].update({"preset":surface_preset,"hydrology":"ocean-draining"})
    validate_surface(result)
    return result


def project_surface(geometry):
    """Explicit nested public allowlist, including defensive copies of arrays."""
    surface = geometry.get("surface")
    if not isinstance(surface, dict) or surface.get("version") not in SURFACE_VERSIONS:
        return {}
    projected={"version":surface["version"],"sea_level":surface["sea_level"],
               **{key:list(surface[key]) for key in FIELDS},
               "rivers":[{"id":r["id"],"points":[[p[0],p[1]] for p in r["points"]]} for r in surface["rivers"]]}
    if surface["version"] in ("planet-v4","planet-v5"):
        projected.update({"preset":surface["preset"],"hydrology":surface["hydrology"]})
    return {"surface":projected}


def validate_surface(geometry):
    """Validate optional new geography on creation/import/read; absent means v1."""
    if "surface" not in geometry:
        return
    surface = geometry["surface"]
    version = surface.get("version") if isinstance(surface,dict) else None
    expected_keys = SURFACE_KEYS | {"preset","hydrology"} if version in ("planet-v4","planet-v5") else SURFACE_KEYS
    if not isinstance(surface, dict) or set(surface) != expected_keys or version not in SURFACE_VERSIONS:
        raise ValueError("unsupported planet surface contract")
    if version in ("planet-v4","planet-v5"):
        preset, hydrology = surface.get("preset"), surface.get("hydrology")
        if preset not in PRESETS or hydrology != ("none" if preset in ("arid","barren","frozen") else "ocean-draining"):
            raise ValueError("invalid planet preset surface contract")
        if (hydrology == "none" and surface.get("sea_level") is not None) or (hydrology != "none" and
                (type(surface.get("sea_level")) is not int or surface["sea_level"] != SEA_LEVEL)):
            raise ValueError("invalid planet preset sea level")
    elif type(surface.get("sea_level")) is not int or surface["sea_level"] != SEA_LEVEL:
        raise ValueError("unsupported planet surface contract")
    planet = geometry.get("planet")
    if not isinstance(planet,dict):
        raise ValueError("invalid planet surface dimensions")
    width, height = planet.get("width"), planet.get("height")
    expected_dimensions = (V5_WIDTH,V5_HEIGHT) if version == "planet-v5" else (WIDTH,HEIGHT)
    if type(width) is not int or type(height) is not int or (width,height) != expected_dimensions:
        raise ValueError("versioned planet surface has unsupported dimensions")
    size = width*height
    for key in FIELDS:
        low, high = (-1,size-1) if key == "drainage" else (1,size) if key == "accumulation" else (0,1000)
        values = surface[key]
        if not isinstance(values,list) or len(values) != size or any(type(v) is not int or not low <= v <= high for v in values):
            raise ValueError("invalid planet surface field")
    codes, elevation, drainage = geometry["terrain_grid"], surface["elevation"], surface["drainage"]
    if not isinstance(codes,str) or len(codes) != size or any(c not in "ocprfm" for c in codes):
        raise ValueError("invalid planet surface terrain")
    if version == "planet-v5":
        provinces=geometry.get("provinces")
        cell=16
        if not isinstance(provinces,list) or len(provinces)!=40:
            raise ValueError("invalid planet province coverage")
        coverage=[0]*size
        for province in provinces:
            if any(type(province.get(key)) is not int for key in ("x","y","width","height")):
                raise ValueError("invalid planet province coverage")
            x,y,w,h=(province[key] for key in ("x","y","width","height"))
            if x<0 or y<0 or (x,y,w,h)!=(x//cell*cell,y//cell*cell,cell,cell) or x+w>width or y+h>height:
                raise ValueError("invalid planet province coverage")
            for row in range(y,y+h):
                for column in range(x,x+w): coverage[row*width+column]+=1
        if any(value!=1 for value in coverage): raise ValueError("invalid planet province coverage")
    if version in ("planet-v4","planet-v5") and surface["hydrology"] == "none":
        preset = surface["preset"]
        allowed = {"arid":"pr", "barren":"r", "frozen":"pr"}[preset]
        if (any(c not in allowed for c in codes) or any(v <= SEA_LEVEL for v in elevation) or
                (preset in ("arid","barren") and any(m != 0 for m in surface["moisture"])) or
                (preset == "frozen" and any(t > 220 for t in surface["temperature"])) or
                any(j != -1 for j in drainage) or any(v != 1 for v in surface["accumulation"]) or
                not isinstance(surface["rivers"],list) or surface["rivers"] != []):
            raise ValueError("invalid dry planet preset fields")
        return
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
