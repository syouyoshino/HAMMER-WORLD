"""Deterministic fictional demo-v2 fixture and versioned public projections."""
import hashlib
import random

from .engine import generate_planet
from .planet_generation import generate_planet_v2, generate_planet_v3, project_surface

V2_SCHEMA = "world-v2"
V2_RULES = "demo-v2"
RESOURCES = ("food", "ore", "energy", "materiel", "data", "metals", "promethium", "credits")


def _seed(seed, parent, domain, ordinal=0):
    raw = f"{seed}:{parent}:{domain}:v1:{ordinal}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def build_universe(campaign_id, seed, *, planet_generator="planet-v1"):
    """Build the approved compact node hierarchy, settlements and fixture accounts."""
    if planet_generator not in ("planet-v1", "planet-v2", "planet-v3"):
        raise ValueError("unsupported planet generator")
    rng = random.Random(_seed(seed, campaign_id, "universe"))
    root = f"{campaign_id}-galaxy"
    nodes = [{"id": root, "parent_id": None, "kind": "galaxy", "name": "The Reach", "knowledge": "surveyed", "x": 0, "y": 0}]
    sibling_ordinals={}
    def node(suffix, parent, kind, name, knowledge, x, y):
        parent_id=f"{campaign_id}-{parent}" if parent else root
        ordinal=sibling_ordinals.get(parent_id,0); sibling_ordinals[parent_id]=ordinal+1
        pos=random.Random(_seed(seed,parent_id,"position",ordinal))
        value = {"id": f"{campaign_id}-{suffix}", "parent_id": parent_id,
                 "kind": kind, "name": name, "knowledge": knowledge,
                 "x":round(x+pos.uniform(-.08,.08),4),"y":round(y+pos.uniform(-.08,.08),4)}
        nodes.append(value)
        return value["id"]
    region = node("region-01", None, "region", "Kestrel Reach", "surveyed", 0, 0)
    hearth = node("sector-hearth", "region-01", "sector", "Hearth", "surveyed", 0, 0)
    frontier = node("sector-frontier", "region-01", "sector", "Frontier", "detected", 1, 0)
    hsys = node("system-hearth", "sector-hearth", "system", "Cinder", "surveyed", 0, 0)
    gsys = node("system-glimmer", "sector-hearth", "system", "Glimmer", "detected", 1, 0)
    dsys = node("system-dusk", "sector-frontier", "system", "Dusk", "hidden", 0, 0)
    reach = node("planet-reach", "system-hearth", "planet", "Reach", "surveyed", 0, 0)
    ash = node("planet-ash", "system-hearth", "planet", "Ash", "detected", 1, 0)
    haven = node("planet-haven", "system-glimmer", "planet", "Haven", "hidden", 0, 0)
    veil = node("planet-veil", "system-dusk", "planet", "Veil", "hidden", 0, 0)
    for planet_id in (reach,ash,haven,veil):
        planet_rng=random.Random(_seed(seed,planet_id,"body-class",0))
        next(n for n in nodes if n["id"]==planet_id).update({"class":planet_rng.choice(("terrestrial","oceanic","arid","ice")),"radius":round(planet_rng.uniform(.65,1.55),3)})
    for system_suffix,system_id,visibility in (("system-hearth",hsys,"surveyed"),("system-glimmer",gsys,"hidden"),("system-dusk",dsys,"hidden")):
        body_rng=random.Random(_seed(seed,system_id,"bodies",0))
        node(f"{system_suffix}-star",system_suffix,"star","Cinder Star" if visibility=="surveyed" else "Unsurveyed Star",visibility,
            body_rng.uniform(-.15,.15),body_rng.uniform(-.15,.15))
        nodes[-1].update({"stellar_class":body_rng.choice(("G","K","M")),"radius":round(body_rng.uniform(.7,1.3),3)})
        belt_rng=random.Random(_seed(seed,system_id,"bodies",1))
        node(f"{system_suffix}-belt",system_suffix,"belt","Cinder Belt" if visibility=="surveyed" else "Unsurveyed Belt",visibility,
            belt_rng.uniform(.8,1.2),belt_rng.uniform(-.15,.15))
        nodes[-1].update({"radius":round(belt_rng.uniform(1.5,3.5),3),"density":belt_rng.choice(("sparse","moderate","dense"))})
    for planet_suffix,planet_id,knowledge in (("planet-reach",reach,"detected"),("planet-ash",ash,"hidden"),
            ("planet-haven",haven,"hidden"),("planet-veil",veil,"hidden")):
        moon_rng=random.Random(_seed(seed,planet_id,"bodies",0))
        node(f"{planet_suffix}-moon-01",planet_suffix,"moon","Unsurveyed Moon" if knowledge=="hidden" else "Detected Moon",knowledge,
            moon_rng.uniform(.3,.7),moon_rng.uniform(.3,.7))
        nodes[-1].update({"class":moon_rng.choice(("rocky","icy")),"radius":round(moon_rng.uniform(.12,.48),3)})
    planet_ids=[n["id"] for n in nodes if n["kind"]=="planet"]
    if planet_generator in ("planet-v2", "planet-v3"):
        generator = generate_planet_v3 if planet_generator == "planet-v3" else generate_planet_v2
        geography={pid:generator(f"{campaign_id}-{pid.rsplit('-',1)[-1]}",_seed(seed,pid,"geography"),
                    next(n["class"] for n in nodes if n["id"] == pid)) for pid in planet_ids}
    else:
        geography={pid:generate_planet(f"{campaign_id}-{pid.rsplit('-',1)[-1]}",_seed(seed,pid,"geography")) for pid in planet_ids}
    geometry = geography[reach]
    land_provinces = [p["id"] for p in geometry["provinces"]]
    # Choose stable valid land locations with separate domain streams.
    land_ids = []
    codes = geometry["terrain_grid"]
    for province in geometry["provinces"]:
        px, py = province["x"], province["y"]
        if any(codes[y * geometry["planet"]["width"] + x] != "o"
               for y in range(py, py + province["height"]) for x in range(px, px + province["width"])):
            land_ids.append(province["id"])
    land_ids = land_ids or land_provinces
    if planet_generator in ("planet-v2", "planet-v3") and len(land_ids) < 3:
        raise ValueError("new demo geography requires three land provinces")
    # Fixture assignments are explicit; the adversary is its own private account.
    def settlement(sid, name, province, civilians, owned, stock, unrest=0):
        return {"id": f"{campaign_id}-{sid}", "name": name, "planet_id": reach,
                "province_id": province, "owned": owned, "civilians": civilians,
                "housing": 1200,
                "stocks": dict(zip(RESOURCES, stock)), "unrest": unrest,
                "policy": {"tax_rate": 1, "welfare": False, "growth_enabled": False},
                "allocations": {"farmers": 0, "miners": 0, "technicians": 0,
                    "machinists": 0, "scientists": 0, "builders": 0, "refiners": 0, "drillers": 0}}
    settlements = [
        settlement("forge", "Forge", land_ids[0], 890, True, (5900,1800,3000,100,20,100,180,200)),
        settlement("outpost", "Outpost", land_ids[1], 300, True, (2000,600,1000,50,10,100,200,200)),
        settlement("adversary-home", "The Adversary", land_ids[2], 20, False, (100,100,0,50,0,0,0,1000)),
    ]
    settlements[2]["intel"]={"observed_turn":0,"confidence":"unknown","planet_id":reach,"province_id":land_ids[2]}
    facilities = []
    fixture = {"forge": {"farm": 2, "mine": 1, "generator": 1, "factory": 1, "refinery": 1,
                         "promethium_well": 1, "lab": 1, "depot": 1},
               "outpost": {"farm": 1, "mine": 1, "generator": 1, "depot": 1}}
    for sid, buildings in fixture.items():
        for kind, count in buildings.items():
            for n in range(count):
                facilities.append({"id": f"{campaign_id}-{sid}-{kind}-{n+1}", "settlement_id": f"{campaign_id}-{sid}",
                                   "kind": kind, "active_turn": 0, "completed": True})
    factions = [{"id": f"{campaign_id}-faction-ash", "name": "Ash Compact", "contacted": True,
                 "treaties": [], "stocks": {"food":100,"ore":100,"materiel":50,"credits":1000}}]
    units = [{"id": f"{campaign_id}-enemy-ground", "kind":"ground", "owner":"enemy", "planet_id":reach,"settlement_id":f"{campaign_id}-adversary-home", "location_id":land_ids[2],
              "strength":10,"readiness":100,"created_turn":0,"acted_turn":-1,"intel":{"confidence":"high","observed_turn":0,"location_id":land_ids[2],"strength":10,"readiness":100}}]
    fleets = [{"id": f"{campaign_id}-transport-01", "kind":"transport", "owner":"player", "system_id":hsys,
              "location_id":reach,"settlement_id":f"{campaign_id}-forge","strength":10,"crew":10,"capacity":100,"food_reserve":100,"promethium_reserve":20,
               "moving_until":None,"created_turn":0,"acted_turn":-1},
              {"id": f"{campaign_id}-enemy-fleet", "kind":"fleet", "owner":"enemy", "settlement_id":f"{campaign_id}-adversary-home", "system_id":hsys,
               "location_id":reach,"strength":10,"crew":10,"moving_until":None,"created_turn":0,"acted_turn":-1,
               "capacity":100,
               "intel":{"confidence":"high","observed_turn":0,"system_id":hsys,"location_id":reach,"strength":10}}]
    characters = [{"id":f"{campaign_id}-character-{role}","role":role,"assignment":None,"experience":0,"owned":True}
                  for role in ("engineer","steward","general","scout")]
    private = {"seed": seed, "campaign_id": campaign_id, "seeded_marker": f"secret:{seed}", "enemy_population":20,
               "generator_version":"hierarchical-v1",
               "generator_config":{"hierarchy":"hierarchical-v1","planet":planet_generator,"grid":"grid64x40",
                                   "domain_seed_derivation":"sha256-parent-domain-v1"},
               "enemy_allocations":{"farmers":14,"technicians":2}, "adjacency":[[hsys,gsys],[gsys,dsys]],
               "generation_nonce":rng.randrange(1, 2**31)}
    return {"turn":0,"nodes":nodes,"links":[{"a":hsys,"b":gsys},{"a":gsys,"b":dsys}],
        "geography":geography,"settlements":settlements,"facilities":facilities,"projects":[],
        "units":units,"fleets":fleets,"shipments":[],"factions":factions,"expeditions":[],
        "characters":characters,"technologies":[],"discoveries":[],"latest_outcome":None,
        "latest_budget":None,"latest_production":None,"narrative":"","_private":private}


def owned_humans(state):
    return (sum(s["civilians"] for s in state["settlements"] if s["owned"])
            + sum(u["strength"] for u in state["units"] if u["owner"] == "player")
            + sum(f["crew"] for f in state["fleets"] if f["owner"] == "player")
            + sum(m["settlers"] for m in state["expeditions"] if m.get("kind") == "colonize"))


def owned_resources(state):
    totals={key:sum(s["stocks"][key] for s in state["settlements"] if s["owned"]) for key in RESOURCES}
    for fleet in state["fleets"]:
        if fleet.get("owner")=="player":
            totals["food"]+=fleet.get("food_reserve",0)
            totals["promethium"]+=fleet.get("promethium_reserve",0)
    for unit in state["units"]:
        if unit.get("owner")=="player":
            totals["food"]+=unit.get("food_reserve",0)+unit.get("transit_food",0)
    for shipment in state["shipments"]:
        if shipment.get("owned",True): totals[shipment["resource"]]+=shipment["quantity"]
    for mission in state["expeditions"]:
        if mission.get("owned") and mission.get("kind")=="colonize":
            totals["food"]+=mission.get("food_cargo",0)
    return totals


def public_state_v2(state):
    """Explicit player projection; hidden hierarchy and foreign balances stay hidden."""
    visible = [n for n in state["nodes"] if n["knowledge"] != "hidden"]
    visible_ids = {n["id"] for n in visible}
    nodes = []
    for n in visible:
        surveyed = n["knowledge"] == "surveyed"
        projection={"id":n["id"],"parent_id":n["parent_id"] if n["parent_id"] in visible_ids else None,
            "kind":n["kind"],"name":n["name"] if surveyed else f"Unsurveyed {n['kind'].title()}",
            "knowledge":n["knowledge"],"x":n["x"] if surveyed else None,"y":n["y"] if surveyed else None}
        if surveyed:
            for key in ("class","stellar_class","radius","density"):
                if key in n: projection[key]=n[key]
        nodes.append(projection)
    links = [{"a":x["a"],"b":x["b"]} for x in state["links"] if x["a"] in visible_ids and x["b"] in visible_ids]
    settlements = []
    for s in state["settlements"]:
        # Foreign survey data is disclosed only as its small approved observation.
        if s["owned"]:
            local_units=[u for u in state["units"] if u.get("owner")=="player" and u.get("planet_id")==s["planet_id"] and u.get("location_id")==s["province_id"] and not u.get("moving_until")]
            local_fleets=[f for f in state["fleets"] if f.get("owner")=="player" and f.get("settlement_id")==s["id"]
                          and f.get("location_id")==s["planet_id"] and not f.get("moving_until")]
            soldiers=sum(u["strength"] for u in local_units)
            crew=sum(f["crew"] for f in local_fleets)
            settlements.append({"id":s["id"],"name":s["name"],"planet_id":s["planet_id"],"province_id":s["province_id"],
                "owned":True,"civilians":s["civilians"],"local_soldiers":soldiers,"local_crew":crew,
                "local_population":s["civilians"]+soldiers+crew,
                "housing":s["housing"],"stocks":{key:s["stocks"][key] for key in RESOURCES},"unrest":s["unrest"],
                "policy":{key:s["policy"][key] for key in ("tax_rate","welfare","growth_enabled")},
                "allocations":{key:s["allocations"][key] for key in ("farmers","miners","technicians","machinists","scientists","builders","refiners","drillers")}})
        elif s.get("intel") and s["intel"].get("observed_turn") is not None:
            intel=s["intel"]
            if intel.get("planet_id") in visible_ids and next((n for n in visible if n["id"]==intel.get("planet_id")),{}).get("knowledge")=="surveyed":
                settlement_view={"id":s["id"],"name":"Observed foreign settlement","planet_id":intel["planet_id"],
                    "province_id":intel.get("province_id"),"owned":False,"civilians":None,"local_soldiers":None,"local_crew":None,
                    "local_population":None,"housing":None,"stocks":None,"unrest":None,"confidence":intel.get("confidence","unknown"),
                    "observed_turn":intel["observed_turn"]}
                estimate=intel.get("civilian_population_range")
                if estimate and type(estimate.get("min")) is int and type(estimate.get("max")) is int:
                    settlement_view["civilian_population_range"]={"min":estimate["min"],"max":estimate["max"]}
                settlements.append(settlement_view)
    facilities = [{"id":f["id"],"settlement_id":f["settlement_id"],"kind":f["kind"],"completed":f["completed"],
                   "active_turn":f["active_turn"]} for f in state["facilities"]
                  if any(s["id"] == f["settlement_id"] and s["owned"] for s in state["settlements"])]
    # Owned movement endpoints are recorded orders, not a geometric travel path.
    units = [{k:u[k] for k in ("id","kind","owner","location_id","strength","readiness","planet_id","settlement_id","moving_until","food_reserve","transit_food",
                              "origin_province_id","destination_province_id","departure_turn","supply_source_id") if k in u}
             for u in state["units"] if u["owner"] == "player"]
    units += [{"id":u["id"],"kind":u["kind"],"owner":"foreign","location_id":u["intel"].get("location_id"),
               "strength":u["intel"].get("strength"),"confidence":u["intel"]["confidence"],"observed_turn":u["intel"]["observed_turn"]}
              for u in state["units"] if u["owner"]!="player" and u.get("intel")]
    fleets = [{k:f[k] for k in ("id","kind","owner","system_id","location_id","settlement_id","strength","crew","capacity","food_reserve","promethium_reserve","moving_until",
                               "destination_system_id","origin_settlement_id","departure_turn") if k in f}
              for f in state["fleets"] if f["owner"] == "player"]
    fleets += [{"id":f["id"],"kind":f["kind"],"owner":"foreign","system_id":f["intel"].get("system_id"),
                "location_id":f["intel"].get("location_id"),"strength":f["intel"].get("strength"),"confidence":f["intel"]["confidence"],
                "observed_turn":f["intel"]["observed_turn"]} for f in state["fleets"] if f["owner"]!="player" and f.get("intel")]
    characters = [{k:c[k] for k in ("id","role","assignment","experience")} for c in state["characters"] if c["owned"]]
    projects=[{key:p[key] for key in ("id","kind","facility_kind","technology_id","settlement_id","work_required","work_done","created_turn") if key in p}
              for p in state["projects"] if p.get("owned",True)]
    shipments=[{key:s[key] for key in ("id","source_id","destination_id","resource","quantity","arrive_turn","created_turn") if key in s}
               for s in state["shipments"] if s.get("owned",True)]
    expeditions=[{key:e[key] for key in ("id","kind","source_id","node_id","entity_id","target_planet_id","arrive_turn","finish_turn","settlers","food_cargo","departure_turn") if key in e}
                 for e in state["expeditions"] if e.get("owned",True)]
    factions=[{"id":f["id"],"name":f["name"],"contacted":f["contacted"],"treaties":[
        {key:t[key] for key in ("kind","status","proposed_turn","accepted_by_gm","accepted_turn") if key in t} for t in f["treaties"]]}
        for f in state["factions"] if f["contacted"]]
    discoveries=[]
    for d in state["discoveries"]:
        row={key:d[key] for key in ("turn","node_id","entity_id","kind") if key in d}
        observed=d.get("observed")
        if isinstance(observed,dict):
            safe_observed={"confidence":observed["confidence"]} if observed.get("confidence") in ("low","medium","high","unknown") else {}
            bounds=observed.get("civilian_population_range")
            if isinstance(bounds,dict) and type(bounds.get("min")) is int and type(bounds.get("max")) is int and bounds["min"]>=0 and bounds["max"]>=bounds["min"]:
                safe_observed["civilian_population_range"]={"min":bounds["min"],"max":bounds["max"]}
            row["observed"]=safe_observed
        discoveries.append(row)
    outcomes=state["latest_outcome"]
    if outcomes:
        owned_settlement_ids={s["id"] for s in state["settlements"] if s["owned"]}
        def rows(name,keys,integer_keys=()):
            safe=[]
            for item in outcomes.get(name,[]):
                if not isinstance(item,dict):continue
                row={}
                for key in keys:
                    value=item.get(key)
                    if key in integer_keys and type(value)is int and value>=0:row[key]=value
                    elif key not in integer_keys and isinstance(value,str):row[key]=value
                safe.append(row)
            return safe
        def per_settlement(name):
            result={}
            for sid,values in outcomes.get(name,{}).items():
                if sid not in owned_settlement_ids or not isinstance(values,dict):continue
                safe={k:v for k,v in values.items() if k in (*RESOURCES,"population") and type(v)is int and v>=0}
                result[sid]=safe
            return result
        def resources_projection():
            raw=outcomes.get("resources")
            if not isinstance(raw,dict):return None
            result={}
            for account in ("opening","closing"):
                values=raw.get(account)
                if isinstance(values,dict):result[account]={k:v for k,v in values.items() if k in RESOURCES and type(v)is int and v>=0}
            categories={"inflows":("production","taxes","trade"),"outflows":("action_costs","recipes","meals","growth","research","upkeep","welfare","trade","destruction")}
            for ledger,cats in categories.items():
                result[ledger]={}
                for category in cats:
                    values=raw.get(ledger,{}).get(category,{}) if isinstance(raw.get(ledger),dict) else {}
                    if isinstance(values,dict):result[ledger][category]={k:v for k,v in values.items() if k in RESOURCES and type(v)is int and v>=0}
            if isinstance(outcomes.get("total_consumption"),dict):
                result["total_consumption"]={k:v for k,v in outcomes["total_consumption"].items() if k in RESOURCES and type(v)is int and v>=0}
            return result
        allocation_events={sid:{key:values[key] for key in ("farmers","miners","technicians","machinists","scientists","builders","refiners","drillers") if type(values.get(key)) is int and values[key]>=0}
            for sid,values in outcomes.get("allocations",{}).items() if sid in owned_settlement_ids and isinstance(values,dict)}
        actions=[]
        for item in outcomes.get("actions",[]):
            if isinstance(item,dict) and type(item.get("index")) is int and item.get("type") in ("build","set_policy","dispatch","research","recruit","attack","fleet_attack","build_transport","fleet_move","resupply_fleet","deploy_unit","colonize","treaty","trade","explore","investigate","assign") and item.get("status") in ("accepted","rejected"):
                actions.append({"index":item["index"],"type":item["type"],"status":item["status"]})
        outcomes={"turn":outcomes.get("turn") if type(outcomes.get("turn")) is int else None,"actions":actions,"allocations":allocation_events,
            "resources":resources_projection(),"births":rows("births",("settlement_id","count"),("count",)),"deaths":rows("deaths",("entity_id","settlement_id","group","count"),("count",)),
            "total_consumption":{k:v for k,v in outcomes.get("total_consumption",{}).items() if k in RESOURCES and type(v)is int and v>=0} if isinstance(outcomes.get("total_consumption"),dict) else None,
            "production":per_settlement("production"),"consumption":per_settlement("consumption"),
            "battles":rows("battles",("attacker_id","target_id","attacker_losses","target_losses"),("attacker_losses","target_losses")),
            "deliveries":rows("deliveries",("shipment_id","quantity"),("quantity",)),"colonies":rows("colonies",("settlement_id","planet_id","settlers","food_delivered"),("settlers","food_delivered")),
            "resource_losses":rows("resource_losses",("entity_id","food","promethium"),("food","promethium"))}
    budget=state["latest_budget"]
    if budget:
        budget={key:budget[key] for key in ("opening_credits","tax_revenue","trade_revenue","action_credit_spending","trade_spending","closing_credits") if type(budget.get(key)) is int and budget[key]>=0}
        owned_ids={s["id"] for s in state["settlements"] if s["owned"]}
        budget["spending"]={sid:{key:value for key,value in values.items() if key in ("upkeep_energy","upkeep_credits","welfare") and type(value)is int and value>=0}
            for sid,values in state["latest_budget"].get("spending",{}).items() if sid in owned_ids and isinstance(values,dict)}
        budget["unmet_upkeep"]={sid:{key:value for key,value in values.items() if key in ("energy","credits","welfare") and type(value)is int and value>=0}
            for sid,values in state["latest_budget"].get("unmet_upkeep",{}).items() if sid in owned_ids and isinstance(values,dict)}
    def project_geometry(geo):
        planet={key:geo["planet"][key] for key in ("id","name","width","height")}
        provinces=[{key:p[key] for key in ("id","name","x","y","width","height")} for p in geo["provinces"]]
        codes={"o":"ocean","c":"coast","p":"plains","r":"rock","f":"forest","m":"marsh"}
        tiles=[]; width=planet["width"]
        for index,code in enumerate(geo["terrain_grid"]):
            x,y=index%width,index//width
            province=provinces[(y//8)*8+(x//8)]["id"] if code!="o" else None
            tiles.append({"x":x,"y":y,"terrain":codes[code],"province_id":province})
        return {"planet":planet,"provinces":provinces,"tiles":tiles,**project_surface(geo)}
    return {"turn":state["turn"],"owned_totals":{"population":owned_humans(state),"resources":owned_resources(state)},"nodes":nodes,"links":links,"settlements":settlements,"facilities":facilities,
        "projects":projects,"units":units,"fleets":fleets,"shipments":shipments,"factions":factions,
        "expeditions":expeditions,"characters":characters,"technologies":list(state["technologies"]),"discoveries":discoveries,
        "latest_outcome":outcomes,"latest_budget":budget,
        "latest_production":{sid:{resource:values[resource] for resource in RESOURCES if resource in values and type(values[resource]) is int and values[resource]>=0}
            for sid,values in state["latest_production"].items() if sid in {s["id"] for s in state["settlements"] if s["owned"]} and isinstance(values,dict)} if state["latest_production"] else None,
        "narrative":state["narrative"],"geography":{pid:project_geometry(geo) for pid,geo in state["geography"].items()
            if pid in visible_ids and next((n for n in visible if n["id"]==pid),{}).get("knowledge")=="surveyed"}}
