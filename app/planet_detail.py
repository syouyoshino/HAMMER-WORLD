"""V10 fine-first saved cartography; strategic summaries never generate detail."""
from collections import Counter, deque
from functools import lru_cache
import hashlib
import heapq
import json
import math

from .planet_hydrography import clean_name, _name
from .planet_materials import validate_choices

VERSION = 'planet-detail-v2'
WIDTH, HEIGHT, SCALE = 1024, 640, 8
RESOLUTION = 2
SIZE = WIDTH * HEIGHT
MAX_BYTES = 8 * 1024 * 1024
PRESETS = ('continental', 'archipelago', 'oceanic', 'arid', 'barren', 'frozen')
DRY = ('arid', 'barren', 'frozen')
FIELDS = {'version','width','height','terrain_grid','elevation','materials',
          'feature_index','feature_ids','hydrography','rivers','province_anchors','craters'}


@lru_cache(maxsize=65536)
def _value(seed, domain, x=0, y=0):
    return int.from_bytes(hashlib.sha256(f'{seed}:planet-detail-v2:{domain}:{x}:{y}'.encode()).digest()[:4], 'big')


def _noise(seed, x, y, scale, domain):
    """Periodic integer smoothstep noise; the longitude seam is an ordinary edge."""
    scale *= RESOLUTION
    count = max(1, (WIDTH+scale//2)//scale)
    gx, rx = divmod(x*count, WIDTH)
    gy, ry = divmod(y, scale)
    tx, ty = rx*1000//WIDTH, ry*1000//scale
    tx, ty = tx*tx*(3000-2*tx)//1000000, ty*ty*(3000-2*ty)//1000000
    def at(a,b): return _value(seed,domain,a%count,b)%2001-1000
    a=(at(gx,gy)*(1000-tx)+at(gx+1,gy)*tx)//1000
    b=(at(gx,gy+1)*(1000-tx)+at(gx+1,gy+1)*tx)//1000
    return (a*(1000-ty)+b*ty)//1000


def _neighbors(i, diagonal=False):
    x,y=i%WIDTH,i//WIDTH
    yield y*WIDTH+(x-1)%WIDTH
    yield y*WIDTH+(x+1)%WIDTH
    if y: yield i-WIDTH
    if y+1<HEIGHT: yield i+WIDTH
    if diagonal:
        for ny in (y-1,y+1):
            if 0<=ny<HEIGHT:
                yield ny*WIDTH+(x-1)%WIDTH
                yield ny*WIDTH+(x+1)%WIDTH


def _components(cells):
    remaining=set(cells)
    result=[]
    while remaining:
        start=min(remaining);remaining.remove(start)
        todo=[start];component=[]
        while todo:
            i=todo.pop();component.append(i)
            for j in _neighbors(i):
                if j in remaining: remaining.remove(j);todo.append(j)
        result.append(sorted(component))
    return result


def _fine_height(seed,preset):
    fields=[];mountains=[]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            wx=x+_noise(seed,x,y,91,'warp-x')*33*RESOLUTION//1000
            wy=y+_noise(seed,x,y,113,'warp-y')*27*RESOLUTION//1000
            broad=96 if preset=='archipelago' else 205
            mass=(_noise(seed,wx,wy,broad,'continent')*61+
                  _noise(seed,wx,wy,67,'shelf')*26+
                  _noise(seed,wx,wy,25,'coast')*10+
                  _noise(seed,wx,wy,8,'inlet')*3)//100
            fields.append(mass)
            folded=abs(_noise(seed,wx,wy,83,'range')+_noise(seed,wx,wy,27,'range-fold')//3)
            ridge=max(0,440-folded)
            gate=max(0,_noise(seed,wx,wy,147,'range-belt')+550)
            mountains.append(ridge*gate//1050 + max(0,180-abs(_noise(seed,wx,wy,17,'foothills')))//3)
    if preset in DRY:
        return [max(40,min(1000,530+v//3+r*3//4)) for v,r in zip(fields,mountains)]
    land_fraction={'continental':54,'archipelago':31,'oceanic':17}[preset]
    threshold=sorted(fields)[SIZE*(100-land_fraction)//100]
    height=[]
    for value,ridge in zip(fields,mountains):
        delta=value-threshold
        height.append(max(0,min(1000,400+delta*9//10+(ridge*min(120,delta)//120 if delta>0 else 0))))
    return height


def _craters(namespace,seed,geology,height):
    if geology=='none': return []
    from .planet_generation import crater_profile_q
    descriptors=[]
    for ordinal in range(72):
        value=_value(seed,'crater-radius',ordinal)
        band=value%100
        radius=(48+value//100%193 if band<74 else 256+value//100%321 if band<96 else 640+value//100%481)
        radius *= RESOLUTION
        margin=(5*radius+3)//4
        xq=_value(seed,'crater-x',ordinal)%(WIDTH*16)
        yq=margin+_value(seed,'crater-y',ordinal)%(HEIGHT*16-2*margin)
        depth=24+_value(seed,'crater-depth',ordinal)%130
        rim=10+_value(seed,'crater-rim',ordinal)%70
        descriptor={'id':f'{namespace}-v10-crater-{ordinal:03d}','x_q':xq,'y_q':yq,
                    'radius_q':radius,'depth':depth,'rim_height':rim}
        descriptors.append(descriptor)
        extent=(margin+15)//16
        for y in range(max(0,yq//16-extent),min(HEIGHT,yq//16+extent+1)):
            for xx in range(xq//16-extent,xq//16+extent+1):
                x=xx%WIDTH
                dx=abs(x*16+8-xq);dx=min(dx,WIDTH*16-dx)
                dy=y*16+8-yq
                distance=math.isqrt(dx*dx+dy*dy)
                if distance*4<=radius*5:
                    i=y*WIDTH+x
                    height[i]=max(0,min(1000,height[i]+crater_profile_q(distance,radius,depth,rim)))
    return descriptors


def _drainage(height,ocean,seed):
    """Priority flood produces a finite D8 receiver DAG, including flat basins."""
    original=list(height)
    receivers=[-1]*SIZE
    visited=bytearray(SIZE)
    heap=[]
    for i in ocean: visited[i]=1;heap.append((height[i],original[i],_value(seed,'drainage-tie',i),i))
    heapq.heapify(heap)
    order=[]
    while heap:
        level,_,_,i=heapq.heappop(heap);order.append(i)
        for j in _neighbors(i,True):
            if visited[j]: continue
            visited[j]=1;receivers[j]=i
            height[j]=max(height[j],level)
            heapq.heappush(heap,(height[j],original[j],_value(seed,'drainage-tie',j),j))
    if len(order)!=SIZE: raise ValueError('fine drainage did not reach every cell')
    # The flood establishes routing only. Carve narrow receiving channels in
    # the original relief instead of persisting broad, artificial filled flats.
    height[:] = original
    accumulation=[1]*SIZE
    for i in reversed(order):
        downstream=receivers[i]
        if downstream>=0:
            if downstream not in ocean:
                height[downstream]=max(401,min(height[downstream],height[i]))
            accumulation[downstream]+=accumulation[i]
    if any(j>=0 and height[j]>height[i] for i,j in enumerate(receivers)):
        raise ValueError('uphill fine drainage')
    return receivers,accumulation


def _mix_latitude(values,radius):
    """Bounded meridional air exchange; wind rows are not isolated climates."""
    result=[0]*SIZE
    for x in range(WIDTH):
        total=sum(values[y*WIDTH+x] for y in range(radius+1))
        for y in range(HEIGHT):
            count=min(HEIGHT-1,y+radius)-max(0,y-radius)+1
            result[y*WIDTH+x]=total//count
            if y-radius>=0: total-=values[(y-radius)*WIDTH+x]
            if y+radius+1<HEIGHT: total+=values[(y+radius+1)*WIDTH+x]
    return result


def _climate_terrain(seed,preset,height,ocean):
    coast={j for i in ocean for j in _neighbors(i) if j not in ocean}
    # Two passes of a prevailing wind carry humidity inland and lose it over ridges.
    humidity=[0]*SIZE
    if preset not in DRY:
        for y in range(HEIGHT):
            air=500
            for xx in range(WIDTH*2):
                x=xx%WIDTH;i=y*WIDTH+x
                if i in ocean:
                    air=820+_noise(seed,x,y,97,'maritime-humidity')//8
                else:
                    upwind=y*WIDTH+(x-1)%WIDTH
                    climb=max(0,height[i]-height[upwind])
                    air=max(0,air-max(1,(air-90)//270)-climb//13)
                if xx>=WIDTH: humidity[i]=air
        for _ in range(2): humidity=_mix_latitude(humidity,8*RESOLUTION)
    terrain=[]
    for i,value in enumerate(height):
        x,y=i%WIDTH,i//WIDTH
        if i in ocean: terrain.append('o');continue
        if preset=='barren': terrain.append('r');continue
        if preset in ('arid','frozen'):
            terrain.append('r' if value>650 else 'p');continue
        # Air masses and local circulation bend ecotones across latitude and
        # relief; classification is saved geography, never a client color blur.
        temperature=900-abs(2*y-(HEIGHT-1))*800//HEIGHT-max(0,value-400)//2
        temperature+=_noise(seed,x,y,107,'airmass-temperature')//10
        temperature+=_noise(seed,x,y,31,'local-temperature')*35//1000
        moisture=humidity[i]*2//3+140
        moisture+=_noise(seed,x,y,67,'moisture-belt')*150//1000
        moisture+=_noise(seed,x,y,23,'moisture')*90//1000
        if i in coast: code='c'
        elif value>740 or temperature<70: code='r'
        elif moisture>650 and value<470: code='m'
        elif moisture>490 and temperature>120: code='f'
        else: code='p'
        terrain.append(code)
    return terrain


def _materials(seed,choice,caps,height,terrain):
    materials=['0']*SIZE
    if caps!='none':
        for x in range(WIDTH):
            north=(28+_noise(seed,x,0,93,'north-cap')//55)*RESOLUTION
            south=(28+_noise(seed,x,0,107,'south-cap')//55)*RESOLUTION
            for y in range(max(5*RESOLUTION,north)): materials[y*WIDTH+x]='i'
            for y in range(HEIGHT-max(5*RESOLUTION,south),HEIGHT): materials[y*WIDTH+x]='i'
    if choice=='none': return materials
    eligible={i for i,c in enumerate(terrain) if c not in 'oc' and materials[i]=='0'}
    if not eligible: raise ValueError('no eligible fine lake terrain')
    ranked=sorted(eligible,key=lambda i:(height[i],_value(seed,'lake-center',i)))
    used=set();centers=[]
    for ordinal in range(7):
        center=next((i for i in ranked if i not in used and all(
            min(abs(i%WIDTH-j%WIDTH),WIDTH-abs(i%WIDTH-j%WIDTH))**2+(i//WIDTH-j//WIDTH)**2>(55*RESOLUTION)**2
            for j in centers)),None)
        if center is None: break
        centers.append(center);cx,cy=center%WIDTH,center//WIDTH
        queue=[(height[center],center)];queued={center};basin=[]
        target=(110+_value(seed,'lake-size',ordinal)%460)*RESOLUTION**2
        while queue and len(basin)<target:
            _,i=heapq.heappop(queue)
            if i in used: continue
            basin.append(i);used.add(i)
            for j in _neighbors(i):
                if j not in eligible or j in used or j in queued: continue
                queued.add(j)
                dx=min(abs(j%WIDTH-cx),WIDTH-abs(j%WIDTH-cx));dy=j//WIDTH-cy
                cost=height[j]*18+(dx*dx+dy*dy)//(5*RESOLUTION**2)+_noise(seed,j%WIDTH,j//WIDTH,11,'lake-shore')//8
                heapq.heappush(queue,(cost,j))
        for i in basin: materials[i]={'water':'w','hydrocarbon':'h','lava':'l'}[choice]
    return materials


def _river_courses(namespace,receivers,accumulation,ocean):
    cells={i for i in range(SIZE) if i not in ocean and accumulation[i]>=110*RESOLUTION**2}
    tributaries={receivers[i] for i in cells}
    sources=sorted(cells-tributaries,key=lambda i:(-accumulation[i],i))
    courses=[]
    for source in sources:
        path=[];i=source
        while i>=0:
            path.append(i)
            if i in ocean: break
            i=receivers[i]
        if len(path)<14*RESOLUTION: continue
        courses.append({'id':f'{namespace}-v10-river-{source}','points':path})
        if len(courses)>=96: break
    return courses


def _body_anchor(cells,materials):
    group=set(cells)
    distance={i:0 for i in cells if any(j not in group for j in _neighbors(i))}
    queue=deque(distance)
    while queue:
        i=queue.popleft()
        for j in _neighbors(i):
            if j in group and j not in distance: distance[j]=distance[i]+1;queue.append(j)
    return min(cells,key=lambda i:(materials[i]=='i',-distance.get(i,0),i))


def _catalog(namespace,naming,custom,terrain,materials,courses):
    custom={} if custom is None else dict(custom)
    features=[];indexes=[0]*SIZE
    oceans=_components(i for i,c in enumerate(terrain) if c=='o')
    largest=min(oceans,key=lambda cells:(-len(cells),cells[0])) if oceans else None
    def add(fid,kind,material,cells):
        name,source=(_name(fid),'generated') if naming=='generated' else (None,'none')
        if fid in custom: name,source=clean_name(custom.pop(fid)),'custom'
        features.append({'id':fid,'kind':kind,'material':material,'anchor':_body_anchor(cells,materials),
                         'name':name,'name_source':source})
        index=len(features)
        for i in cells: indexes[i]=index
    for cells in oceans:
        kind='ocean' if cells is largest else 'sea'
        add(f'{namespace}-v10-{kind}-{cells[0]}',kind,'water',cells)
    for code,material in (('w','water'),('h','hydrocarbon'),('l','lava')):
        for cells in _components(i for i,c in enumerate(materials) if c==code):
            add(f'{namespace}-v10-{material}-{cells[0]}','lake',material,cells)
    # Longest full course owns shared raster trunk; explicit courses retain every ID.
    for river in sorted(courses,key=lambda r:(-len(r['points']),r['id'])):
        fid=river['id'];owned=[i for i in river['points'] if indexes[i]==0]
        if not owned: continue
        name,source=(_name(fid),'generated') if naming=='generated' else (None,'none')
        if fid in custom: name,source=clean_name(custom.pop(fid)),'custom'
        candidates=[i for i in owned if materials[i]!='i'] or owned
        features.append({'id':fid,'kind':'river','material':'water','anchor':candidates[len(candidates)//2],
                         'name':name,'name_source':source})
        for i in owned: indexes[i]=len(features)
    if custom: raise ValueError('custom hydrographic name references unknown fine feature')
    return features,indexes


def _summaries(namespace,terrain,materials):
    from .planet_generation import _province_rectangles
    provinces=_province_rectangles(namespace,128,80,16)
    summary=[]
    for py in range(80):
        for px in range(128):
            eligible=[terrain[(py*SCALE+dy)*WIDTH+px*SCALE+dx] for dy in range(SCALE) for dx in range(SCALE)
                      if terrain[(py*SCALE+dy)*WIDTH+px*SCALE+dx]!='o' and materials[(py*SCALE+dy)*WIDTH+px*SCALE+dx] not in 'whl']
            counts=Counter(eligible)
            summary.append(min(counts,key=lambda c:(-counts[c],c)) if counts else 'o')
    anchors=[]
    for p in provinces:
        cells=[y*WIDTH+x for y in range(p['y']*SCALE,(p['y']+p['height'])*SCALE)
               for x in range(p['x']*SCALE,(p['x']+p['width'])*SCALE)
               if terrain[y*WIDTH+x]!='o' and materials[y*WIDTH+x] not in 'whl']
        n=len(cells)
        if n:
            sx,sy=sum(i%WIDTH for i in cells),sum(i//WIDTH for i in cells)
            anchor=min(cells,key=lambda i:((i%WIDTH*n-sx)**2+(i//WIDTH*n-sy)**2,i))
        else: anchor=None
        anchors.append({'province_id':p['id'],'cell':anchor})
    return provinces,''.join(summary),anchors


def generate_planet_v10(namespace,seed,preset,geology='none',lake_material='none',polar_caps='none',naming='none',custom_names=None):
    if preset not in PRESETS or geology not in ('none','cratered') or naming not in ('none','generated'):
        raise ValueError('unsupported fine planet choices')
    if geology=='cratered' and preset not in DRY: raise ValueError('cratered geology requires dry preset')
    if custom_names is not None and not isinstance(custom_names,dict): raise ValueError('invalid custom fine names')
    validate_choices(preset,lake_material,polar_caps)
    _value.cache_clear()
    height=_fine_height(seed,preset)
    craters=_craters(namespace,seed,geology,height)
    ocean={i for i,v in enumerate(height) if v<=400} if preset not in DRY else set()
    receivers,accumulation=_drainage(height,ocean,seed) if ocean else (None,None)
    terrain=_climate_terrain(seed,preset,height,ocean)
    materials=_materials(seed,lake_material,polar_caps,height,terrain)
    courses=_river_courses(namespace,receivers,accumulation,ocean) if ocean else []
    features,indexes=_catalog(namespace,naming,custom_names,terrain,materials,courses)
    # Courses with no exclusive visible cell cannot introduce an unrepresented ID.
    visible={f['id'] for f in features}
    courses=[r for r in courses if r['id'] in visible]
    provinces,summary,anchors=_summaries(namespace,terrain,materials)
    geometry={'planet':{'id':f'{namespace}-planet-001','name':"Kestrel's Reach",'width':128,'height':80},
              'provinces':provinces,'terrain_grid':summary,
              'surface':{'version':'planet-v10','preset':preset,'topology':'cylinder-x',
                         'hydrology':'none' if preset in DRY else 'ocean-draining','sea_level':None if preset in DRY else 400,
                         'geology':geology,'lake_material':lake_material,'polar_caps':polar_caps}}
    payload={'version':VERSION,'width':WIDTH,'height':HEIGHT,'terrain_grid':''.join(terrain),
             'elevation':height,'materials':''.join(materials),'feature_index':indexes,
             'feature_ids':[f['id'] for f in features],
             'hydrography':{'version':'hydrography-v2','naming':naming,'features':features},
             'rivers':courses,'province_anchors':anchors,'craters':craters}
    validate_planet_detail(payload,geometry)
    _value.cache_clear()
    return geometry,payload


def validate_planet_detail(payload,geometry):
    """Validate the saved fine authority and every coarse projection invariant."""
    if not isinstance(payload,dict) or set(payload)!=FIELDS:
        raise ValueError('invalid fine planet fields')
    if payload['version']!=VERSION or type(payload['width']) is not int or type(payload['height']) is not int or (payload['width'],payload['height'])!=(WIDTH,HEIGHT):
        raise ValueError('unsupported fine planet version or dimensions')
    terrain,materials,height,indexes,ids=(payload[k] for k in ('terrain_grid','materials','elevation','feature_index','feature_ids'))
    if not isinstance(terrain,str) or len(terrain)!=SIZE or set(terrain)-set('ocprfm') or not isinstance(materials,str) or len(materials)!=SIZE or set(materials)-set('0iwhl'):
        raise ValueError('invalid fine terrain/material grids')
    if not isinstance(height,list) or len(height)!=SIZE or any(type(v) is not int or not 0<=v<=1000 for v in height):
        raise ValueError('invalid fine relative elevation')
    hydro=payload['hydrography']
    if not isinstance(hydro,dict) or set(hydro)!={'version','naming','features'} or hydro['version']!='hydrography-v2' or hydro['naming'] not in ('none','generated'):
        raise ValueError('invalid fine hydrography')
    features=hydro['features']
    if not isinstance(features,list) or len(features)>4096 or not isinstance(ids,list) or len(ids)!=len(features) or any(not isinstance(v,str) or not v or len(v)>200 for v in ids) or len(set(ids))!=len(ids):
        raise ValueError('invalid fine feature palette')
    if not isinstance(indexes,list) or len(indexes)!=SIZE or any(type(v) is not int or not 0<=v<=len(ids) for v in indexes):
        raise ValueError('invalid fine feature indices')
    groups={k:[] for k in range(1,len(ids)+1)}
    for i,k in enumerate(indexes):
        if k: groups[k].append(i)
    for k,f in enumerate(features,1):
        if not isinstance(f,dict) or set(f)!={'id','kind','material','anchor','name','name_source'} or f['id']!=ids[k-1] or f['kind'] not in ('ocean','sea','lake','river') or f['material'] not in ('water','hydrocarbon','lava'):
            raise ValueError('invalid fine feature catalog')
        if not groups[k] or type(f['anchor']) is not int or not 0<=f['anchor']<SIZE or indexes[f['anchor']]!=k:
            raise ValueError('unrepresented fine feature or invalid feature anchor')
        if f['name_source'] not in ('none','generated','custom') or (f['name_source']=='none')!=(f['name'] is None):
            raise ValueError('invalid fine hydrographic name provenance')
        if f['name'] is not None and clean_name(f['name'])!=f['name']: raise ValueError('invalid fine hydrographic name')
        if f['name_source']=='generated' and (hydro['naming']!='generated' or f['name']!=_name(f['id'])):
            raise ValueError('invalid generated fine hydrographic name')
        if f['kind']!='lake' and f['material']!='water': raise ValueError('invalid fine feature material')
    surface=geometry['surface'];preset=surface['preset']
    dry=preset in DRY
    if dry and set(terrain)-set('r' if preset=='barren' else 'pr'): raise ValueError('dry fine planet gained wet vegetation or ocean')
    for i,c in enumerate(terrain):
        f=features[indexes[i]-1] if indexes[i] else None
        kind=f['kind'] if f else None
        if (c=='o') != (kind in ('ocean','sea')): raise ValueError('fine ocean membership mismatch')
        if not dry and ((c=='o')!=(height[i]<=400)): raise ValueError('fine sea/elevation inconsistency')
        m=materials[i]
        if m in 'whl':
            if kind!='lake' or f['material']!={'w':'water','h':'hydrocarbon','l':'lava'}[m] or c in 'oc': raise ValueError('fine lake material/identity mismatch')
        elif kind=='lake': raise ValueError('fine lake lacks material')
    for k,f in enumerate(features,1):
        if f['kind'] in ('ocean','sea','lake') and len(_components(groups[k]))!=1:
            raise ValueError('disconnected fine water body')
    for code in ('o','w','h','l'):
        components=_components(i for i in range(SIZE) if (terrain[i]=='o' if code=='o' else materials[i]==code))
        for cells in components:
            if len({indexes[i] for i in cells})!=1:
                raise ValueError('fine connected body has multiple identities')
        if code=='o' and components:
            largest=max(components,key=lambda cells:(len(cells),-cells[0]))
            if features[indexes[largest[0]]-1]['kind']!='ocean':
                raise ValueError('fine ocean identity must name largest component')
    if sum(f['kind']=='ocean' for f in features)!=(0 if dry else 1): raise ValueError('invalid fine ocean catalog')
    if surface['lake_material']=='none' and set(materials)&set('whl') or surface['lake_material']!='none' and not any(f['kind']=='lake' and f['material']==surface['lake_material'] for f in features):
        raise ValueError('fine lake choice not represented')
    if any(m in 'whl' and {'w':'water','h':'hydrocarbon','l':'lava'}[m]!=surface['lake_material'] for m in materials): raise ValueError('fine lake choice differs')
    if surface['polar_caps']=='none':
        if 'i' in materials: raise ValueError('unexpected fine polar ice')
    else:
        for x in range(WIDTH):
            column=''.join(materials[y*WIDTH+x]=='i' and '1' or '0' for y in range(HEIGHT))
            north=len(column)-len(column.lstrip('1'));south=len(column)-len(column.rstrip('1'))
            if not 1<=north<=80*RESOLUTION or not 1<=south<=80*RESOLUTION or column!='1'*north+'0'*(HEIGHT-north-south)+'1'*south:
                raise ValueError('invalid fine polar cap continuity')
    _validate_courses(payload,features,indexes,height,dry)
    namespace=geometry['planet']['id'].removesuffix('-planet-001')
    provinces,summary,anchors=_summaries(namespace,terrain,materials)
    if geometry['planet'].get('width')!=128 or geometry['planet'].get('height')!=80 or geometry['provinces']!=provinces or geometry['terrain_grid']!=summary or payload['province_anchors']!=anchors:
        raise ValueError('fine geography differs from strategic summary/anchors')
    _validate_craters(payload['craters'],surface)
    if len(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())>MAX_BYTES:
        raise ValueError('fine planet asset exceeds size limit')


def _validate_courses(payload,features,indexes,height,dry):
    courses=payload['rivers']
    if not isinstance(courses,list) or len(courses)>96 or dry and courses: raise ValueError('invalid fine river list')
    byid={f['id']:f for f in features};seen=set();receivers={};membership={}
    total=0
    for river in courses:
        if not isinstance(river,dict) or set(river)!={'id','points'} or river['id'] in seen or river['id'] not in byid or byid[river['id']]['kind']!='river': raise ValueError('invalid fine river identity')
        seen.add(river['id']);points=river['points']
        if not isinstance(points,list) or not 2<=len(points)<=SIZE or any(type(i) is not int or not 0<=i<SIZE for i in points) or len(set(points))!=len(points): raise ValueError('invalid fine river course')
        total+=len(points)
        for i in points: membership.setdefault(i,set()).add(river['id'])
        if not indexes[points[-1]] or features[indexes[points[-1]]-1]['kind'] not in ('ocean','sea'): raise ValueError('fine river lacks ocean termination')
        for a,b in zip(points,points[1:]):
            if b not in _neighbors(a,True) or height[b]>height[a] or a in receivers and receivers[a]!=b:
                raise ValueError('fine river has invalid downstream topology')
            if indexes[a] and features[indexes[a]-1]['kind'] in ('ocean','sea'): raise ValueError('fine river continues through ocean')
            receivers[a]=b
    if total>2*SIZE or seen!={f['id'] for f in features if f['kind']=='river'}: raise ValueError('fine river catalog coverage mismatch')
    # Shared receivers plus individual ocean termination imply a DAG. Verify it
    # explicitly so a future terminal rule cannot accidentally admit cycles.
    complete=set()
    for start in receivers:
        path=set();i=start
        while i in receivers and i not in complete:
            if i in path: raise ValueError('cyclic fine river drainage')
            path.add(i);i=receivers[i]
        complete.update(path)
    for i,k in enumerate(indexes):
        if k and features[k-1]['kind']=='river' and features[k-1]['id'] not in membership.get(i,set()):
            raise ValueError('fine river raster differs from explicit course')
    for i,rivers in membership.items():
        if not indexes[i] or features[indexes[i]-1]['kind']=='river' and features[indexes[i]-1]['id'] not in rivers:
            raise ValueError('fine course has unrepresented river pixels')


def _validate_craters(craters,surface):
    if not isinstance(craters,list) or len(craters)>128 or surface['geology']=='none' and craters:
        raise ValueError('invalid fine crater list')
    if surface['geology']=='cratered' and not craters: raise ValueError('missing fine crater descriptors')
    seen=set()
    for c in craters:
        if not isinstance(c,dict) or set(c)!={'id','x_q','y_q','radius_q','depth','rim_height'} or not isinstance(c['id'],str) or not c['id'] or c['id'] in seen:
            raise ValueError('invalid fine crater descriptor')
        seen.add(c['id'])
        for key,low,high in (('x_q',0,WIDTH*16-1),('y_q',0,HEIGHT*16-1),('radius_q',16,1536*RESOLUTION),('depth',1,300),('rim_height',0,200)):
            if type(c[key]) is not int or not low<=c[key]<=high: raise ValueError('invalid fine crater dimensions')
        margin=(5*c['radius_q']+3)//4
        if not margin<=c['y_q']<HEIGHT*16-margin: raise ValueError('fine crater exceeds latitude bounds')


def project_planet_detail(payload):
    """Fresh public allowlist, including copies of every nested mutable value."""
    return {'version':payload['version'],'width':payload['width'],'height':payload['height'],
            'terrain_grid':payload['terrain_grid'],'elevation':list(payload['elevation']),
            'materials':payload['materials'],'feature_index':list(payload['feature_index']),
            'feature_ids':list(payload['feature_ids']),
            'hydrography':{'version':payload['hydrography']['version'],'naming':payload['hydrography']['naming'],
                          'features':[{k:f[k] for k in ('id','kind','material','anchor','name','name_source')} for f in payload['hydrography']['features']]},
            'rivers':[{'id':r['id'],'points':list(r['points'])} for r in payload['rivers']],
            'province_anchors':[{'province_id':a['province_id'],'cell':a['cell']} for a in payload['province_anchors']],
            'craters':[{k:c[k] for k in ('id','x_q','y_q','radius_q','depth','rim_height')} for c in payload['craters']]}
