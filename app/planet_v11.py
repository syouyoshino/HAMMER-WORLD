"""Opt-in physical-scale surface contract layered onto the bounded V10 payload."""
import math
from .planet_detail import (WIDTH, HEIGHT, SIZE, PRESETS, DRY, _value,
    _drainage, _climate_terrain, _materials, _river_courses, _catalog, _summaries,
    validate_planet_detail)
from .planet_scale import (metadata, canonical_radius,
    PHYSICAL_WAVELENGTHS_M as WAVELENGTHS_M, physical_octave_periods)

VERSION = "planet-v11"
# Representative fictional feature wavelengths; they describe generator bands,
# not discovered geological measurements.
def scale_bands(radius_m):
    return {name:record["status"] for name,record in physical_octave_periods(radius_m).items()}


def _noise_v11(seed,x,y,scale,domain):
    """V11 sampler targeting the bounded nominal pixel period in its metadata."""
    scale=max(4,int(scale))
    count=max(1,(WIDTH+scale//2)//scale)
    gx,rx=divmod(x*count,WIDTH);gy,ry=divmod(y,scale)
    tx,ty=rx*1000//WIDTH,ry*1000//scale
    tx,ty=tx*tx*(3000-2*tx)//1000000,ty*ty*(3000-2*ty)//1000000
    def at(a,b): return _value(seed,domain,a%count,b)%2001-1000
    a=(at(gx,gy)*(1000-tx)+at(gx+1,gy)*tx)//1000
    b=(at(gx,gy+1)*(1000-tx)+at(gx+1,gy+1)*tx)//1000
    return (a*(1000-ty)+b*ty)//1000


def _pixel_wavelength(radius_m, wavelength_m, generalized_index):
    """Map physical wavelengths to bounded samples, attenuating subpixel bands."""
    name=next((key for key,value in WAVELENGTHS_M.items() if value==wavelength_m),None)
    if name is not None:
        return int(physical_octave_periods(radius_m)[name]["sample_period_px"])
    return 0


def _fine_height_v11(seed,preset,radius_m):
    scales={name:_pixel_wavelength(radius_m,wave,index) for index,(name,wave) in enumerate(WAVELENGTHS_M.items())}
    # Planetary land probability is distinct from physical feature wavelengths.
    # Keep several broad clusters even when physical continents are only a few
    # pixels wide, while decreasing their angular footprint on larger bodies.
    continental=scales["continental"]
    broad=max(WIDTH//8,min(WIDTH//3,continental*2)) if continental else WIDTH//8
    if preset=="archipelago":
        broad=broad*3//4
    warp_period=max(16,min(96,continental*3))
    warp_amplitude=min(12,max(2,continental//2)) if continental else 0
    fields=[];mountains=[]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            # Bounded continuous warps break the Cartesian noise lattice. The
            # longitude sampler wraps normally, including warped coordinates.
            wx=x+_noise_v11(seed,x,y,WIDTH//4,"v11:warp-x")*48//1000
            wy=y+_noise_v11(seed,x,y,WIDTH//3,"v11:warp-y")*40//1000
            scaffold=(_noise_v11(seed,wx,wy,broad,"v11:land-probability")*60
                      +_noise_v11(seed,wx,wy,max(4,broad//2),"v11:land-regions")*28
                      +_noise_v11(seed,wx,wy,max(4,broad//4),"v11:land-fragments")*12)//100
            # Bend short wavelength cells locally as well, so resolved fine
            # coast detail does not reveal an axis-aligned lattice at overview.
            px=wx+_noise_v11(seed,wx,wy,warp_period,"v11:coast-warp-x")*warp_amplitude//1000 if warp_amplitude else wx
            py=wy+_noise_v11(seed,wx,wy,warp_period,"v11:coast-warp-y")*warp_amplitude//1000 if warp_amplitude else wy
            physical=0
            for name,weight in (("continental",61),("shelf",26),("island",10),("coast",3)):
                scale=scales[name]
                if scale:
                    amp=weight*min(1000,scale*1000//8)//1000
                    physical+=_noise_v11(seed,px,py,scale,"v11:"+name)*amp
            # Physical detail changes shorelines, bays and island groups around
            # the broad probability field; it cannot perforate every continent
            # and ocean into equally sized cells when only one band resolves.
            mass=(scaffold*72+physical*28//100)//100
            if scales["inlet"]:
                mass += _noise_v11(seed,px,py,scales["inlet"],"v11:inlet")*2//100
            fields.append(mass)
            mountain_scale=scales["mountain"]
            if mountain_scale:
                folded=abs(_noise_v11(seed,wx,wy,mountain_scale,"v11:mountain")+
                           _noise_v11(seed,wx,wy,max(4,mountain_scale//3),"v11:mountain-fold")//3)
                ridge=max(0,440-folded)
                gate=max(0,_noise_v11(seed,wx,wy,max(4,min(WIDTH//2,mountain_scale*2)),"v11:range-belt")+550)
                mountains.append(ridge*gate//1050 + max(0,180-abs(_noise_v11(seed,wx,wy,max(4,mountain_scale//4),"v11:foothills")))//3)
            else:
                mountains.append(0)
    if preset in DRY:
        return [max(40,min(1000,530+v//3+r*3//4)) for v,r in zip(fields,mountains)]
    land_fraction={"continental":54,"archipelago":31,"oceanic":17}[preset]
    ordered=sorted(fields)
    threshold=ordered[SIZE*(100-land_fraction)//100]
    height=[]
    for value,ridge in zip(fields,mountains):
        delta=value-threshold
        height.append(max(0,min(1000,400+delta*9//10+(ridge*min(120,delta)//120 if delta>0 else 0))))
    return height


def _craters_v11(namespace,seed,geology,height,radius_m):
    if geology=="none": return []
    from .planet_generation import crater_profile_q
    pixel=_pixel_wavelength(radius_m,"1.5e5",7)
    # Small bodies use a few globe-scale basins; bodies with unresolved impact
    # bands retain no invented subpixel craters.
    if not pixel:
        return []
    # A crater support must fit within the existing latitude validity bound.
    radius_q=max(16,min(3072,pixel*8))
    descriptors=[]
    for ordinal in range(24):
        xq=_value(seed,"v11-crater-x",ordinal)%(WIDTH*16)
        margin=(5*radius_q+3)//4
        yq=margin+_value(seed,"v11-crater-y",ordinal)%(HEIGHT*16-2*margin)
        c={"id":f"{namespace}-v11-crater-{ordinal:03d}","x_q":xq,"y_q":yq,"radius_q":radius_q,
           "depth":24+_value(seed,"v11-crater-depth",ordinal)%80,"rim_height":10+_value(seed,"v11-crater-rim",ordinal)%50}
        descriptors.append(c)
        extent=(margin+15)//16
        for y in range(max(0,yq//16-extent),min(HEIGHT,yq//16+extent+1)):
            for xx in range(xq//16-extent,xq//16+extent+1):
                x=xx%WIDTH; dx=abs(x*16+8-xq); dx=min(dx,WIDTH*16-dx); dy=y*16+8-yq
                distance=math.isqrt(dx*dx+dy*dy)
                if distance*4<=radius_q*5:
                    i=y*WIDTH+x
                    height[i]=max(0,min(1000,height[i]+crater_profile_q(distance,radius_q,c["depth"],c["rim_height"])))
    return descriptors


def generate_planet_v11(namespace, seed, preset, geology="none", lake_material="none",
                        polar_caps="none", naming="none", custom_names=None, radius_m=None):
    canonical = canonical_radius(radius_m)  # explicit and string-only by contract
    if preset not in PRESETS or geology not in ("none","cratered") or naming not in ("none","generated"):
        raise ValueError("unsupported V11 planet choices")
    if geology=="cratered" and preset not in DRY:
        raise ValueError("cratered geology requires dry preset")
    from .planet_materials import validate_choices
    validate_choices(preset,lake_material,polar_caps)
    height=_fine_height_v11(seed,preset,canonical)
    craters=_craters_v11(namespace,seed,geology,height,canonical)
    ocean={i for i,v in enumerate(height) if v<=400} if preset not in DRY else set()
    receivers,accumulation=_drainage(height,ocean,seed) if ocean else (None,None)
    terrain=_climate_terrain(seed,preset,height,ocean)
    materials=_materials(seed,lake_material,polar_caps,height,terrain,_pixel_wavelength(canonical,"2.5e5",7))
    courses=_river_courses(namespace,receivers,accumulation,ocean) if ocean else []
    features,indexes=_catalog(namespace,naming,custom_names,terrain,materials,courses)
    visible={f["id"] for f in features}
    courses=[r for r in courses if r["id"] in visible]
    provinces,summary,anchors=_summaries(namespace,terrain,materials)
    geo={"planet":{"id":f"{namespace}-planet-001","name":"Kestrel's Reach","width":128,"height":80},
         "provinces":provinces,"terrain_grid":summary,
         "surface":{"version":VERSION,"preset":preset,"topology":"cylinder-x",
            "hydrology":"none" if preset in DRY else "ocean-draining","sea_level":None if preset in DRY else 400,
            "geology":geology,"lake_material":lake_material,"polar_caps":polar_caps}}
    payload={"version":"planet-detail-v2","width":WIDTH,"height":HEIGHT,"terrain_grid":"".join(terrain),
        "elevation":height,"materials":"".join(materials),"feature_index":indexes,
        "feature_ids":[f["id"] for f in features],
        "hydrography":{"version":"hydrography-v2","naming":naming,"features":features},
        "rivers":courses,"province_anchors":anchors,"craters":craters}
    info = metadata(canonical)
    # Canonical fine arrays remain fixed-size and are projected with the same V10
    # validators/assets. V11's scale contract tells readers which real bands the
    # sampled detail can support.
    geo["surface"].update(version=VERSION, **info,
                          physical_octaves=physical_octave_periods(canonical),
                          physical_bands=scale_bands(canonical),
                          scale_model="fictional-wavelengths-v1")
    from .planet_generation import validate_surface
    validate_surface(geo)
    validate_planet_detail(payload,geo)
    return geo, payload
