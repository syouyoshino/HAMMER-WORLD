"""Connected deterministic demo-v2 rules. All amounts and actions are fictional fixtures."""
import hashlib
import json
import math
import re

from .universe import V2_RULES, V2_SCHEMA, RESOURCES, build_universe, owned_resources

ACTION_LIMIT = 32
ACTION_TYPES = {"build", "set_policy", "dispatch", "research", "recruit", "attack", "fleet_attack",
    "build_transport", "fleet_move", "resupply_fleet", "deploy_unit", "colonize", "treaty", "trade", "explore", "investigate", "assign"}
ALLOCATIONS = {"farmers", "miners", "technicians", "machinists", "scientists", "builders", "refiners", "drillers"}
FACILITIES = {"farm", "mine", "generator", "factory", "refinery", "promethium_well", "lab", "depot", "habitation", "orbital_battery"}


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def initial_state(campaign_id, seed):
    return build_universe(campaign_id, seed)


def validate_submission(payload):
    required = {"schema_version", "rules_version", "base_turn", "base_hash", "submission_id", "orders", "narrative"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("proposal must contain exactly the documented fields")
    if payload["schema_version"] != V2_SCHEMA or payload["rules_version"] != V2_RULES:
        raise ValueError("unsupported schema_version or rules_version")
    if type(payload["base_turn"]) is not int or payload["base_turn"] < 0:
        raise ValueError("base_turn must be a nonnegative integer")
    if not isinstance(payload["base_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", payload["base_hash"]):
        raise ValueError("base_hash must be a SHA256 hex digest")
    if not isinstance(payload["submission_id"], str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,100}", payload["submission_id"]):
        raise ValueError("invalid submission_id")
    if not isinstance(payload["narrative"], str) or len(payload["narrative"]) > 2000:
        raise ValueError("narrative must be at most 2000 characters")
    orders = payload["orders"]
    if not isinstance(orders, dict) or set(orders) != {"allocations", "actions"}:
        raise ValueError("v2 orders require allocations and actions")
    allocations = orders["allocations"]
    if not isinstance(allocations, list) or len(allocations) > 20:
        raise ValueError("allocations must be a bounded list")
    for allocation in allocations:
        if not isinstance(allocation, dict) or set(allocation) != {"settlement_id", *ALLOCATIONS}:
            raise ValueError("allocation has unknown or missing fields")
        if not isinstance(allocation["settlement_id"], str):
            raise ValueError("allocation settlement_id must be text")
        if any(type(allocation[k]) is not int or not 0 <= allocation[k] <= 1_000_000 for k in ALLOCATIONS):
            raise ValueError("allocations must be bounded nonnegative integers")
    actions = orders["actions"]
    if not isinstance(actions, list) or len(actions) > ACTION_LIMIT:
        raise ValueError(f"actions must be a list of at most {ACTION_LIMIT}")
    for action in actions:
        if not isinstance(action, dict) or action.get("type") not in ACTION_TYPES:
            raise ValueError("action type is missing or unsupported")
        if len(canonical_json(action)) > 2048:
            raise ValueError("action exceeds size limit")


def _by_id(rows, key):
    return next((row for row in rows if row["id"] == key), None)


def _owned_settlement(state, key):
    row = _by_id(state["settlements"], key)
    if not row or not row["owned"]:
        raise ValueError("unknown owned settlement")
    return row


def _charge(account, costs):
    for resource, amount in costs.items():
        if account[resource] < amount:
            raise ValueError(f"insufficient {resource}")
    for resource, amount in costs.items():
        account[resource] -= amount


def _account(s):
    return s["stocks"]


def _record_flow(outcomes, direction, category, amounts):
    row=outcomes["resources"][direction].setdefault(category,{})
    for resource, amount in amounts.items():
        if type(amount) is not int or amount < 0 or resource not in RESOURCES:
            raise ValueError("invalid resource flow")
        row[resource]=row.get(resource,0)+amount


def _cleanup_destroyed_units(state, outcomes):
    for unit in state["units"]:
        if unit.get("owner")!="player" or unit["strength"]>0: continue
        food=unit.get("transit_food",0)+unit.get("food_reserve",0)
        if food:
            sponsor=_by_id(state["settlements"],unit.get("supply_source_id") or unit.get("settlement_id"))
            if sponsor and sponsor["owned"]:
                sponsor["stocks"]["food"]+=food
            else:
                outcomes.setdefault("resource_losses",[]).append({"entity_id":unit["id"],"food":food})
        unit["transit_food"]=0; unit["food_reserve"]=0
        if unit.get("moving_until"):
            unit["location_id"]=unit.get("origin_province_id")
        unit["moving_until"]=None
        for key in ("destination_province_id","origin_province_id","departure_turn","ration_turn"):
            unit.pop(key,None)


def _apply_actions(state, actions, turn, submission_id, outcomes, reserved_routes=None):
    # User-ordered action validation and reservations happen against the working copy.
    ledger={"credit_spending":0,"trade_revenue":0,"trade_spending":0}; pending_attacks=[]; reserved_combatants=set()
    route_use=dict(reserved_routes or {})
    for shipment in state["shipments"]:
        if shipment["created_turn"]==turn:
            route_use[shipment["source_id"]]=route_use.get(shipment["source_id"],0)+shipment["quantity"]
    for index, action in enumerate(actions):
        credit_before=sum(s["stocks"]["credits"] for s in state["settlements"] if s["owned"])
        kind = action["type"]
        identity=canonical_json([state["_private"]["campaign_id"],submission_id,index,kind])
        new_id=f"{state['_private']['campaign_id']}-entity-{hashlib.sha256(identity.encode()).hexdigest()[:24]}"
        if kind == "build":
            if set(action) != {"type", "settlement_id", "facility_kind"} or action["facility_kind"] not in FACILITIES:
                raise ValueError("build requires a settlement_id and supported facility_kind")
            s = _owned_settlement(state, action["settlement_id"])
            _charge(_account(s), {"ore":20,"materiel":10, **({"metals":20} if action["facility_kind"]=="orbital_battery" else {})})
            state["projects"].append({"id":new_id,"kind":"facility","facility_kind":action["facility_kind"],
                "settlement_id":s["id"],"work_required":10,"work_done":0,"created_turn":turn,"owned":True})
        elif kind == "set_policy":
            if set(action) != {"type","settlement_id","tax_rate","welfare","growth_enabled"}:
                raise ValueError("set_policy fields do not match schema")
            s=_owned_settlement(state,action["settlement_id"])
            if type(action["tax_rate"]) is not int or action["tax_rate"] not in (0,1,2) or type(action["welfare"]) is not bool or type(action["growth_enabled"]) is not bool:
                raise ValueError("invalid policy values")
            s["policy"]={"tax_rate":action["tax_rate"],"welfare":action["welfare"],"growth_enabled":action["growth_enabled"]}
        elif kind == "dispatch":
            if set(action)!={"type","source_id","destination_id","resource","quantity"} or action["resource"] not in RESOURCES[:-1]:
                raise ValueError("dispatch fields or resource are invalid")
            source=_owned_settlement(state,action["source_id"]); destination=_owned_settlement(state,action["destination_id"])
            q=action["quantity"]
            if type(q) is not int or q <= 0 or source["id"]==destination["id"]:
                raise ValueError("dispatch quantity or route is invalid")
            capacity=20*sum(1 for f in state["facilities"] if f["settlement_id"]==source["id"] and f["kind"]=="depot" and f["active_turn"]<=turn)
            if "logistics-I" in state["technologies"]: capacity*=2
            used=route_use.get(source["id"],0)
            if used+q>capacity: raise ValueError("shipment exceeds depot route capacity")
            route_use[source["id"]]=used+q
            _charge(source["stocks"],{action["resource"]:q})
            state["shipments"].append({"id":new_id,"source_id":source["id"],"destination_id":destination["id"],
                "resource":action["resource"],"quantity":q,"arrive_turn":turn+1,"created_turn":turn,"owned":True})
        elif kind == "research":
            if set(action)!={"type","settlement_id","technology_id"} or action["technology_id"] not in ("logistics-I","industry-I"):
                raise ValueError("research fields or technology are invalid")
            s=_owned_settlement(state,action["settlement_id"]); tech=action["technology_id"]
            if tech in state["technologies"] or any(p.get("technology_id")==tech for p in state["projects"]):
                raise ValueError("technology already researched or in progress")
            state["projects"].append({"id":new_id,"kind":"research","technology_id":tech,"settlement_id":s["id"],
                "work_required":20,"work_done":0,"created_turn":turn,"owned":True})
        elif kind == "recruit":
            if set(action)!={"type","settlement_id"}: raise ValueError("recruit fields do not match schema")
            s=_owned_settlement(state,action["settlement_id"])
            _charge(s["stocks"],{"materiel":10,"credits":10})
            if s["civilians"] < 10: raise ValueError("recruitment requires ten civilians")
            s["civilians"]-=10
            state["units"].append({"id":new_id,"kind":"ground","owner":"player","location_id":s["province_id"],
                "planet_id":s["planet_id"],"settlement_id":s["id"],"strength":10,"readiness":100,"created_turn":turn,"acted_turn":-1,"food_reserve":0})
        elif kind in ("attack","fleet_attack"):
            fields={"type","unit_id","target_id"} if kind=="attack" else {"type","fleet_id","target_id"}
            if set(action)!=fields: raise ValueError("attack fields do not match schema")
            collection="units" if kind=="attack" else "fleets"; key="unit_id" if kind=="attack" else "fleet_id"
            attacker=_by_id(state[collection],action[key]); target=_by_id(state[collection],action["target_id"])
            if not attacker or attacker.get("owner")!="player" or not target or target.get("owner")!="enemy": raise ValueError("attack target is not a known hostile")
            if not target.get("intel") or target["intel"].get("observed_turn") is None: raise ValueError("attack target is not in recorded intelligence")
            if attacker.get("acted_turn")==turn or target.get("acted_turn")==turn or attacker["strength"]<=0 or attacker.get("moving_until") or target.get("moving_until"): raise ValueError("attacker or target cannot act this turn")
            if attacker.get("created_turn")==turn: raise ValueError("new units cannot attack during their recruitment turn")
            if kind=="fleet_attack" and attacker["crew"]!=attacker["strength"]: raise ValueError("fleet crew strength invariant failed")
            if kind=="attack" and attacker["location_id"]!=target["location_id"]: raise ValueError("ground units are not co-located")
            if kind=="fleet_attack" and attacker["system_id"]!=target["system_id"]: raise ValueError("fleets are not in the same system")
            if attacker["id"] in reserved_combatants or target["id"] in reserved_combatants: raise ValueError("combatant may participate only once per turn")
            reserved_combatants.update((attacker["id"],target["id"]))
            pending_attacks.append((kind,attacker["id"],target["id"]))
        elif kind == "build_transport":
            if set(action)!={"type","settlement_id"}: raise ValueError("build_transport fields do not match schema")
            s=_owned_settlement(state,action["settlement_id"])
            _charge(s["stocks"],{"metals":20,"materiel":20,"credits":50})
            state["projects"].append({"id":new_id,"kind":"transport","settlement_id":s["id"],"work_required":20,
                "work_done":0,"created_turn":turn,"owned":True})
        elif kind == "fleet_move":
            if set(action)!={"type","fleet_id","destination_system_id","source_id"}: raise ValueError("fleet_move fields do not match schema")
            fleet=_by_id(state["fleets"],action["fleet_id"])
            if not fleet or fleet["owner"]!="player" or fleet["moving_until"] or fleet.get("crew",0)<=0 or fleet.get("acted_turn")==turn: raise ValueError("fleet cannot move")
            dest=action["destination_system_id"]
            if not isinstance(dest,str): raise ValueError("destination system ID must be text")
            destination=_by_id(state["nodes"],dest)
            if not destination or destination["kind"]!="system" or destination["knowledge"]=="hidden": raise ValueError("destination system is not known")
            if not any({edge["a"],edge["b"]}=={fleet["system_id"],dest} for edge in state["links"]): raise ValueError("destination is not a known adjacent system")
            source_id=action["source_id"]
            source=_owned_settlement(state,source_id) if source_id is not None else None
            if source and (source["planet_id"]!=fleet["location_id"] or source["planet_id"] not in [n["id"] for n in state["nodes"] if n["parent_id"]==fleet["system_id"]]):
                raise ValueError("fuel source is not colocated")
            if source:
                _charge(source["stocks"],{"food":2*fleet["crew"],"promethium":5})
                fleet["food_reserve"]+=2*fleet["crew"]
                fleet["promethium_reserve"]+=5
            if fleet.get("promethium_reserve",0)<5 or fleet.get("food_reserve",0)<2*fleet["crew"]:
                raise ValueError("fleet lacks reserved travel food or fuel")
            fleet["promethium_reserve"]-=5
            fleet["destination_system_id"]=dest; fleet["origin_settlement_id"]=fleet.get("settlement_id")
            fleet["departure_turn"]=turn; fleet["moving_until"]=turn+2; fleet["acted_turn"]=turn
            fleet["settlement_id"]=None
        elif kind == "resupply_fleet":
            if set(action)!={"type","source_id","fleet_id","food_quantity","promethium_quantity"}: raise ValueError("resupply_fleet fields do not match schema")
            source=_owned_settlement(state,action["source_id"]); fleet=_by_id(state["fleets"],action["fleet_id"])
            food=action["food_quantity"]; fuel=action["promethium_quantity"]
            if type(food)is not int or type(fuel)is not int or food<0 or fuel<0 or food+fuel==0: raise ValueError("resupply quantities must be nonnegative and nonzero")
            if not fleet or fleet["owner"]!="player" or fleet.get("moving_until") or fleet.get("crew",0)<=0: raise ValueError("fleet cannot be resupplied")
            if source["planet_id"]!=fleet["location_id"] or source["planet_id"] not in [n["id"] for n in state["nodes"] if n["parent_id"]==fleet["system_id"]]: raise ValueError("resupply source is not colocated")
            _charge(source["stocks"],{"food":food,"promethium":fuel})
            fleet["food_reserve"]+=food; fleet["promethium_reserve"]+=fuel
        elif kind == "deploy_unit":
            if set(action)!={"type","unit_id","destination_province_id","source_id"}: raise ValueError("deploy_unit fields do not match schema")
            unit=_by_id(state["units"],action["unit_id"]); source=_owned_settlement(state,action["source_id"])
            if not unit or unit.get("owner")!="player" or unit["strength"]<=0 or unit.get("moving_until") or unit.get("acted_turn")==turn or unit.get("created_turn")==turn:
                raise ValueError("unit cannot deploy this turn")
            geo=state["geography"].get(source["planet_id"])
            target=next((p for p in (geo or {}).get("provinces",[]) if p["id"]==action["destination_province_id"]),None)
            if not target or not any(state["geography"][source["planet_id"]]["terrain_grid"][y*geo["planet"]["width"]+x]!="o"
                for y in range(target["y"],target["y"]+target["height"]) for x in range(target["x"],target["x"]+target["width"])):
                raise ValueError("destination must be surveyed land on the sponsor planet")
            if unit.get("location_id") not in {p["id"] for p in geo["provinces"]} or unit.get("location_id")==target["id"]:
                raise ValueError("unit must be stationed in a different province on the sponsor planet")
            if source["planet_id"]!=unit.get("planet_id"): raise ValueError("unit and sponsor are on different planets")
            depots=sum(1 for f in state["facilities"] if f["settlement_id"]==source["id"] and f["kind"]=="depot" and f["active_turn"]<=turn)
            cap=40 if "logistics-I" in state["technologies"] else 20
            capacity=cap*depots
            if route_use.get(source["id"],0)+unit["strength"]>capacity: raise ValueError("deployment exceeds depot route capacity")
            food=unit["strength"]; energy=math.ceil(unit["strength"]/10)
            _charge(source["stocks"],{"food":food,"energy":energy})
            route_use[source["id"]]=route_use.get(source["id"],0)+unit["strength"]
            unit["planet_id"]=source["planet_id"]; unit["origin_province_id"]=unit["location_id"]
            unit["destination_province_id"]=target["id"]; unit["location_id"]=None
            unit["supply_source_id"]=source["id"]; unit["transit_food"]=food
            unit["departure_turn"]=turn; unit["moving_until"]=turn+1
        elif kind == "colonize":
            if set(action)!={"type","fleet_id","source_id","target_planet_id"}: raise ValueError("colonize fields do not match schema")
            fleet=_by_id(state["fleets"],action["fleet_id"]); source=_owned_settlement(state,action["source_id"])
            target=next((n for n in state["nodes"] if n["id"]==action["target_planet_id"] and n["kind"]=="planet"),None)
            if not fleet or fleet["owner"]!="player" or fleet["kind"]!="transport" or fleet["moving_until"] or fleet.get("acted_turn")==turn or not target or target["knowledge"]!="surveyed": raise ValueError("colonization requires an idle transport and surveyed target")
            if any(s["planet_id"]==target["id"] for s in state["settlements"]): raise ValueError("target is occupied")
            target_system=target["parent_id"]
            if target_system!=fleet["system_id"] and not any({e["a"],e["b"]}=={target_system,fleet["system_id"]} for e in state["links"]):
                raise ValueError("target is outside the transport's reachable systems")
            if source["civilians"]<100 or fleet["settlement_id"]!=source["id"] or fleet["location_id"]!=source["planet_id"] or fleet["crew"]<10:
                raise ValueError("colonization requires 100 settlers and an idle transport docked at its source")
            _charge(source["stocks"],{"food":400,"ore":20,"metals":10,"materiel":10,"credits":20,"promethium":5})
            source["civilians"]-=100
            fleet["origin_settlement_id"]=source["id"]; fleet["settlement_id"]=None
            fleet["departure_turn"]=turn; fleet["destination_system_id"]=target_system
            fleet["moving_until"]=turn+2; fleet["acted_turn"]=turn
            state["expeditions"].append({"id":new_id,"kind":"colonize","fleet_id":fleet["id"],"source_id":source["id"],
                "target_planet_id":target["id"],"settlers":100,"food_cargo":400,"departure_turn":turn,
                "arrive_turn":turn+2,"owned":True})
        elif kind == "treaty":
            if set(action)!={"type","faction_id","operation"} or action["operation"] not in ("propose","accept","reject"): raise ValueError("treaty fields are invalid")
            faction=_by_id(state["factions"],action["faction_id"])
            if not faction or not faction["contacted"]: raise ValueError("faction is not contacted")
            treaty=next((t for t in faction["treaties"] if t["kind"]=="trade"),None)
            if action["operation"]=="propose":
                if treaty and treaty["status"]=="active": raise ValueError("trade treaty already active")
                if not treaty: faction["treaties"].append({"kind":"trade","status":"pending","proposed_turn":turn,"accepted_by_gm":False})
                else: treaty.update({"status":"pending","proposed_turn":turn,"accepted_by_gm":False})
            elif action["operation"]=="accept":
                if not treaty or treaty["status"]!="pending": raise ValueError("no pending proposal to accept")
                treaty.update({"status":"active","accepted_by_gm":True,"accepted_turn":turn})
            else:
                if not treaty or treaty["status"]!="pending": raise ValueError("no pending proposal to reject")
                treaty["status"]="rejected"
        elif kind == "trade":
            if set(action)!={"type","source_id","faction_id","resource","quantity","direction"} or action["resource"] not in ("food","ore","materiel") or action["direction"] not in ("buy","sell"):
                raise ValueError("trade fields are invalid")
            s=_owned_settlement(state,action["source_id"]); faction=_by_id(state["factions"],action["faction_id"])
            if not faction or not any(t["kind"]=="trade" and t["status"]=="active" for t in faction["treaties"]): raise ValueError("trade requires active treaty")
            q=action["quantity"]
            if type(q)is not int or q<1: raise ValueError("trade quantity must be positive")
            price={"food":1,"ore":2,"materiel":3}[action["resource"]]*q
            account=faction["stocks"]
            if action["direction"]=="buy":
                _charge(account,{action["resource"]:q}); _charge(s["stocks"],{"credits":price})
                s["stocks"][action["resource"]]+=q; account["credits"]+=price
            else:
                _charge(s["stocks"],{action["resource"]:q}); _charge(account,{"credits":price})
                account[action["resource"]]+=q; s["stocks"]["credits"]+=price
        elif kind == "explore":
            if set(action)!={"type","source_id","node_id"}: raise ValueError("explore fields do not match schema")
            s=_owned_settlement(state,action["source_id"]); target=_by_id(state["nodes"],action["node_id"])
            if not target or target["knowledge"]!="detected" or not any(n["id"]==target["parent_id"] and n["knowledge"]!="hidden" for n in state["nodes"]): raise ValueError("explore target is not detected from a known parent")
            scout=next((c for c in state["characters"] if c["owned"] and c["role"]=="scout" and c["assignment"]==s["id"]),None)
            _charge(s["stocks"],{"energy":1 if scout else 2,"data":1})
            if scout: scout["experience"]+=1
            state["expeditions"].append({"id":new_id,"kind":"explore","source_id":s["id"],"node_id":target["id"],"arrive_turn":turn+2,"owned":True})
        elif kind == "investigate":
            if set(action)!={"type","source_id","entity_id"}: raise ValueError("investigate fields do not match schema")
            s=_owned_settlement(state,action["source_id"]); entity=_by_id(state["settlements"],action["entity_id"])
            known_planet=_by_id(state["nodes"],entity.get("intel",{}).get("planet_id")) if entity else None
            known_provinces={p["id"] for g in state["geography"].values() for p in g.get("provinces",[])}
            if not entity or entity["owned"] or not entity.get("intel") or entity["intel"].get("observed_turn") is None or not known_planet or known_planet.get("knowledge")!="surveyed" or entity["intel"].get("province_id") not in known_provinces:
                raise ValueError("investigation target is not a known foreign contact")
            _charge(s["stocks"],{"data":1,"credits":5})
            state["expeditions"].append({"id":new_id,"kind":"investigate","source_id":s["id"],"entity_id":entity["id"],"finish_turn":turn+1,"owned":True})
        elif kind == "assign":
            if set(action)!={"type","character_id","target_id"}: raise ValueError("assign fields do not match schema")
            character=_by_id(state["characters"],action["character_id"])
            if not character or not character["owned"]: raise ValueError("unknown owned character")
            target_id=action["target_id"]
            valid={s["id"] for s in state["settlements"] if s["owned"]}|{u["id"] for u in state["units"] if u["owner"]=="player"}|{f["id"] for f in state["fleets"] if f["owner"]=="player"}
            if target_id is not None and target_id not in valid: raise ValueError("assignment target is not owned")
            character["assignment"]=target_id
        costs={}
        if kind=="build": costs={"ore":20,"materiel":10, **({"metals":20} if action["facility_kind"]=="orbital_battery" else {})}
        elif kind=="recruit": costs={"materiel":10,"credits":10}
        elif kind=="build_transport": costs={"metals":20,"materiel":20,"credits":50}
        elif kind=="fleet_move": costs={"promethium":5}
        elif kind=="deploy_unit": costs={"energy":energy}
        elif kind=="colonize": costs={"ore":20,"metals":10,"materiel":10,"credits":20,"promethium":5}
        elif kind=="explore": costs={"energy":1 if scout else 2,"data":1}
        elif kind=="investigate": costs={"data":1,"credits":5}
        elif kind=="trade":
            incoming={action["resource"]:q} if action["direction"]=="buy" else {"credits":price}
            outgoing={"credits":price} if action["direction"]=="buy" else {action["resource"]:q}
            _record_flow(outcomes,"inflows","trade",incoming)
            _record_flow(outcomes,"outflows","trade",outgoing)
        if costs: _record_flow(outcomes,"outflows","action_costs",costs)
        credit_after=sum(s["stocks"]["credits"] for s in state["settlements"] if s["owned"])
        delta=credit_after-credit_before
        if delta<0:
            ledger["credit_spending"]-=delta
            if kind=="trade": ledger["trade_spending"]-=delta
        elif kind=="trade" and delta>0: ledger["trade_revenue"]+=delta
        outcomes.setdefault("actions",[]).append({"index":index,"type":kind,"status":"accepted"})
    return ledger,pending_attacks


def _resolve_battles(state, attacks, turn, outcomes):
    for kind,attacker_id,target_id in attacks:
        collection="units" if kind=="attack" else "fleets"
        attacker=_by_id(state[collection],attacker_id); target=_by_id(state[collection],target_id)
        if not attacker or not target: raise ValueError("combatant disappeared before battle resolution")
        if attacker["strength"]<=0 or target["strength"]<=0: raise ValueError("defeated combatants cannot fight")
        if attacker.get("moving_until") or target.get("moving_until"): raise ValueError("traveling combatants cannot fight")
        power=lambda unit:max(0,unit["strength"]*unit.get("readiness",100)//100)
        general=next((c for c in state["characters"] if c["owned"] and c["role"]=="general" and c["assignment"]==attacker_id),None)
        ap,tp=power(attacker)+(1 if general else 0),power(target)
        if kind=="fleet_attack":
            battle_system=attacker["system_id"]
            defense=sum(2 for f in state["facilities"] if f["kind"]=="orbital_battery" and f.get("active_turn",0)<=turn
                and any(s["id"]==f["settlement_id"] and s["owned"] and
                    next((n["parent_id"] for n in state["nodes"] if n["id"]==s["planet_id"]),None)==battle_system
                    for s in state["settlements"]))
            ap+=defense
        casualties_target=min(target["strength"],math.ceil(ap/10))
        casualties_attacker=min(attacker["strength"],math.ceil(tp/10))
        target["strength"]-=casualties_target; attacker["strength"]-=casualties_attacker
        if kind=="fleet_attack":
            attacker["crew"]=attacker["strength"]; target["crew"]=target["strength"]
        attacker["acted_turn"]=turn; target["acted_turn"]=turn
        if general: general["experience"]+=1
        if target.get("owner")!="player" and target.get("intel") is not None:
            target["intel"].update({"strength":target["strength"],"observed_turn":turn,"confidence":"high"})
            if kind=="attack": target["intel"]["location_id"]=target["location_id"]
            else: target["intel"].update({"system_id":target["system_id"],"location_id":target["location_id"]})
        if attacker.get("owner")=="player" and casualties_attacker:
            outcomes["deaths"].append({"entity_id":attacker_id,"group":"soldiers" if kind=="attack" else "crew","count":casualties_attacker})
        if target.get("owner")=="player" and casualties_target:
            outcomes["deaths"].append({"entity_id":target_id,"group":"soldiers" if kind=="attack" else "crew","count":casualties_target})
        outcomes["battles"].append({"attacker_id":attacker_id,"target_id":target_id,
            "attacker_losses":casualties_attacker,"target_losses":casualties_target})


def _cleanup_destroyed_fleets(state, outcomes):
    for fleet in state["fleets"]:
        if fleet.get("owner")!="player" or fleet.get("crew",0)>0: continue
        for mission in list(state["expeditions"]):
            if mission.get("kind")!="colonize" or mission.get("fleet_id")!=fleet["id"]: continue
            if mission.get("settlers",0):
                outcomes["deaths"].append({"entity_id":mission["id"],"group":"settlers","count":mission["settlers"]})
                mission["settlers"]=0
            outcomes.setdefault("resource_losses",[]).append({"entity_id":fleet["id"],
                "food":mission.get("food_cargo",0)+fleet.get("food_reserve",0),
                "promethium":fleet.get("promethium_reserve",0)})
            mission["food_cargo"]=0; fleet["food_reserve"]=0; fleet["promethium_reserve"]=0
            state["expeditions"].remove(mission)
        food=fleet.get("food_reserve",0); fuel=fleet.get("promethium_reserve",0)
        if food or fuel:
            outcomes.setdefault("resource_losses",[]).append({"entity_id":fleet["id"],"food":food,"promethium":fuel})
        fleet["food_reserve"]=0; fleet["promethium_reserve"]=0
        fleet["moving_until"]=None; fleet["settlement_id"]=None
        fleet.pop("destination_system_id",None); fleet.pop("origin_settlement_id",None); fleet.pop("departure_turn",None)


def _phase_arrivals(state, turn, outcomes):
    already_fed={"settlements":set(),"fleets":set(),"units":set()}
    state["discoveries"]=[]
    arrived=[]
    for shipment in state["shipments"]:
        if shipment["arrive_turn"]<=turn:
            target=_owned_settlement(state,shipment["destination_id"])
            target["stocks"][shipment["resource"]]+=shipment["quantity"]
            outcomes.setdefault("deliveries",[]).append({"shipment_id":shipment["id"],"quantity":shipment["quantity"]})
            arrived.append(shipment)
    state["shipments"]=[s for s in state["shipments"] if s not in arrived]
    for unit in state["units"]:
        if unit.get("owner")!="player" or not unit.get("moving_until") or unit.get("departure_turn",turn)>=turn:
            continue
        strength=max(0,unit["strength"]); available=max(0,unit.get("transit_food",0))
        meal=min(strength,available)
        unit["transit_food"]=0
        unit["food_reserve"]=unit.get("food_reserve",0)+available-meal
        _record_flow(outcomes,"outflows","meals",{"food":meal})
        loss=min(strength,max(0,strength-available))
        if loss:
            unit["strength"]-=loss
            outcomes["deaths"].append({"entity_id":unit["id"],"group":"soldiers","count":loss})
        unit["location_id"]=unit.pop("destination_province_id")
        unit["moving_until"]=None; unit["acted_turn"]=turn
        unit.pop("origin_province_id",None); unit.pop("departure_turn",None)
        already_fed["units"].add(unit["id"])
    colonizing={m["fleet_id"] for m in state["expeditions"] if m.get("kind")=="colonize"}
    for fleet in state["fleets"]:
        if fleet.get("owner")!="player" or not fleet.get("moving_until") or fleet.get("departure_turn",turn)>=turn or fleet["id"] in colonizing:
            continue
        crew=max(0,fleet["crew"]); available=max(0,fleet.get("food_reserve",0))
        _record_flow(outcomes,"outflows","meals",{"food":min(crew,available)})
        meal=crew; fleet["food_reserve"]=max(0,available-meal)
        loss=min(crew,max(0,meal-available))
        if loss:
            fleet["crew"]-=loss; fleet["strength"]=fleet["crew"]
            outcomes["deaths"].append({"entity_id":fleet["id"],"group":"crew","count":loss})
    for fleet in state["fleets"]:
        if fleet.get("owner")!="player" or fleet.get("moving_until") or fleet.get("settlement_id") or fleet["id"] in colonizing or fleet["id"] in already_fed["fleets"]:
            continue
        crew=max(0,fleet["crew"]); available=max(0,fleet.get("food_reserve",0))
        _record_flow(outcomes,"outflows","meals",{"food":min(crew,available)})
        fleet["food_reserve"]=max(0,available-crew)
        loss=min(crew,max(0,crew-available))
        if loss:
            fleet["crew"]-=loss; fleet["strength"]=fleet["crew"]
            outcomes["deaths"].append({"entity_id":fleet["id"],"group":"crew","count":loss})
    # Colony passengers and crew receive the departure meal locally. On each
    # subsequent travel tick, consume reserved cargo before processing arrival.
    for mission in list(state["expeditions"]):
        kind=mission.get("kind")
        if kind=="colonize":
            if mission.get("departure_turn",-1)<turn:
                fleet=_by_id(state["fleets"],mission["fleet_id"])
                passengers=max(0,mission["settlers"]); crew=max(0,fleet["crew"] if fleet else 0)
                available=max(0,mission["food_cargo"]); meal=passengers+crew
                _record_flow(outcomes,"outflows","meals",{"food":min(meal,available)})
                mission["food_cargo"]=max(0,available-meal)
                shortage=max(0,meal-available)
                passenger_loss=min(passengers,shortage); mission["settlers"]-=passenger_loss; shortage-=passenger_loss
                if passenger_loss: outcomes["deaths"].append({"entity_id":mission["id"],"group":"settlers","count":passenger_loss})
                crew_loss=min(crew,shortage)
                if crew_loss and fleet:
                    fleet["crew"]-=crew_loss; fleet["strength"]=fleet["crew"]
                    outcomes["deaths"].append({"entity_id":fleet["id"],"group":"crew","count":crew_loss})
                if fleet and fleet["crew"]==0:
                    if mission["settlers"]:
                        outcomes["deaths"].append({"entity_id":mission["id"],"group":"settlers","count":mission["settlers"]})
                        mission["settlers"]=0
                    outcomes.setdefault("resource_losses",[]).append({"entity_id":fleet["id"],
                        "food":mission["food_cargo"]+fleet.get("food_reserve",0),
                        "promethium":fleet.get("promethium_reserve",0)})
                    mission["food_cargo"]=0; fleet["food_reserve"]=0; fleet["promethium_reserve"]=0
                    fleet["moving_until"]=None; fleet["settlement_id"]=None
                    fleet.pop("destination_system_id",None); fleet.pop("origin_settlement_id",None); fleet.pop("departure_turn",None)
                    state["expeditions"].remove(mission)
                    continue
            if mission["arrive_turn"]<=turn:
                target=mission["target_planet_id"]; geo=state["geography"].get(target)
                if geo is None: raise ValueError("surveyed colonization target has no geography")
                grid=geo["terrain_grid"]; width=geo["planet"]["width"]
                eligible=[p["id"] for p in geo["provinces"] if any(
                    grid[y*width+x]!="o" for y in range(p["y"],p["y"]+p["height"])
                    for x in range(p["x"],p["x"]+p["width"]))]
                if not eligible: raise ValueError("surveyed target has no habitable province")
                fleet=_by_id(state["fleets"],mission["fleet_id"])
                if mission["settlers"]>0 and fleet and fleet["crew"]>0:
                    token=hashlib.sha256(mission["id"].encode()).hexdigest()[:20]
                    new_sid=f"{state['_private']['campaign_id']}-colony-{token}"
                    while any(s["id"]==new_sid for s in state["settlements"]): new_sid+="-x"
                    stocks={resource:0 for resource in RESOURCES}; stocks["food"]=mission["food_cargo"]
                    colony={"id":new_sid,"name":"New Settlement","planet_id":target,"province_id":eligible[0],"owned":True,
                        "civilians":mission["settlers"],"housing":1200,"stocks":stocks,"unrest":0,
                        "policy":{"tax_rate":1,"welfare":False,"growth_enabled":False},"allocations":{k:0 for k in ALLOCATIONS}}
                    state["settlements"].append(colony)
                    for facility in ("farm","depot"):
                        state["facilities"].append({"id":f"{new_sid}-{facility}-1","settlement_id":new_sid,"kind":facility,
                            "active_turn":turn+1,"completed":True})
                    fleet["system_id"]=next(n["parent_id"] for n in state["nodes"] if n["id"]==target)
                    fleet["location_id"]=target; fleet["settlement_id"]=new_sid
                    fleet["moving_until"]=None; fleet["acted_turn"]=turn; fleet.pop("destination_system_id",None); fleet.pop("origin_settlement_id",None); fleet.pop("departure_turn",None)
                    already_fed["settlements"].add(new_sid)
                    outcomes.setdefault("colonies",[]).append({"settlement_id":new_sid,"planet_id":target,
                        "settlers":mission["settlers"],"food_delivered":mission["food_cargo"]})
                    state["discoveries"].append({"turn":turn,"node_id":target,"kind":"colonized"})
                elif fleet:
                    fleet["system_id"]=next(n["parent_id"] for n in state["nodes"] if n["id"]==target)
                    fleet["location_id"]=target; fleet["settlement_id"]=None; fleet["moving_until"]=None; fleet["acted_turn"]=turn
                    fleet.pop("destination_system_id",None); fleet.pop("origin_settlement_id",None); fleet.pop("departure_turn",None)
                state["expeditions"].remove(mission)
        elif kind=="explore" and mission["arrive_turn"]<=turn:
            target=_by_id(state["nodes"],mission["node_id"]); target["knowledge"]="surveyed"
            for child in state["nodes"]:
                if child["parent_id"]==target["id"] and child["knowledge"]=="hidden": child["knowledge"]="detected"
            if target["kind"]=="planet" and target["id"] not in state["geography"]:
                raise ValueError("exploration target has no persisted geography")
            state["discoveries"]=[d for d in state["discoveries"] if d.get("node_id")!=target["id"]]
            state["discoveries"].append({"turn":turn,"node_id":target["id"],"kind":"surveyed"})
            state["expeditions"].remove(mission)
        elif kind=="investigate" and mission["finish_turn"]<=turn:
            entity=_by_id(state["settlements"],mission["entity_id"])
            if entity:
                civilians=entity["civilians"]
                observed={"min":(civilians//100)*100,"max":(civilians//100)*100+99}
                previous=entity.get("intel") or {}
                entity["intel"]={"observed_turn":turn,"confidence":"low","planet_id":previous.get("planet_id"),
                    "province_id":previous.get("province_id"),"civilian_population_range":observed}
                state["discoveries"]=[d for d in state["discoveries"] if d.get("entity_id")!=entity["id"]]
                state["discoveries"].append({"turn":turn,"entity_id":entity["id"],"kind":"investigated",
                    "observed":{"civilian_population_range":observed,"confidence":"low"}})
            state["expeditions"].remove(mission)
    for fleet in state["fleets"]:
        if fleet.get("moving_until") and fleet["moving_until"]<=turn and not any(m.get("fleet_id")==fleet["id"] for m in state["expeditions"]):
            destination=fleet.pop("destination_system_id")
            fleet["system_id"]=destination; fleet["moving_until"]=None; fleet["acted_turn"]=turn
            fleet.pop("origin_settlement_id",None); fleet.pop("departure_turn",None)
            docked=next((s for s in state["settlements"] if s["owned"] and s["planet_id"] in
                         [n["id"] for n in state["nodes"] if n["parent_id"]==destination]),None)
            if docked:
                fleet["location_id"]=docked["planet_id"]; fleet["settlement_id"]=docked["id"]
                already_fed["fleets"].add(fleet["id"])
            else:
                fleet["location_id"]=destination; fleet["settlement_id"]=None
    return already_fed


def _reserve_remote_unit_food(state, turn, already_fed):
    route_use={}
    for unit in sorted(state["units"],key=lambda x:x["id"]):
        if unit.get("owner")!="player" or unit["strength"]<=0 or unit.get("moving_until") or unit["id"] in already_fed["units"]:
            continue
        home=_by_id(state["settlements"],unit.get("settlement_id"))
        if not home or unit.get("location_id")==home["province_id"]: continue
        source=_by_id(state["settlements"],unit.get("supply_source_id") or home["id"])
        if not source: continue
        depots=sum(1 for f in state["facilities"] if f["settlement_id"]==source["id"] and f["kind"]=="depot" and f["active_turn"]<=turn)
        per_depot=40 if "logistics-I" in state["technologies"] else 20
        capacity=per_depot*depots
        remaining=max(0,capacity-route_use.get(source["id"],0))
        quantity=min(unit["strength"],remaining,source["stocks"]["food"])
        source["stocks"]["food"]-=quantity
        unit["food_reserve"]=unit.get("food_reserve",0)+quantity
        unit["ration_turn"]=turn
        route_use[source["id"]]=route_use.get(source["id"],0)+quantity
    return route_use


def _resolve(state, payload):
    humans_before=sum(s["civilians"] for s in state["settlements"] if s["owned"])+sum(u["strength"] for u in state["units"] if u["owner"]=="player")+sum(f["crew"] for f in state["fleets"] if f["owner"]=="player")+sum(m.get("settlers",0) for m in state["expeditions"] if m.get("kind")=="colonize")
    turn=state["turn"]+1; orders=payload["orders"]; outcomes={"turn":turn,"actions":[],"births":[],"deaths":[],"production":{},"consumption":{},"battles":[]}
    outcomes["resources"]={"opening":owned_resources(state),"inflows":{},"outflows":{},"closing":{}}
    already_fed=_phase_arrivals(state,turn,outcomes)
    # Worker orders last one turn. Clear them before processing actions so every
    # proposal starts from a clean allocation slate.
    for settlement in state["settlements"]:
        if settlement["owned"]: settlement["allocations"]={key:0 for key in ALLOCATIONS}
    owned_at_open=[s for s in state["settlements"] if s["owned"]]
    opening_credits=sum(s["stocks"]["credits"] for s in owned_at_open)
    reserved_routes=_reserve_remote_unit_food(state,turn,already_fed)
    credit_ledger,pending_attacks=_apply_actions(state,orders["actions"],turn,payload["submission_id"],outcomes,reserved_routes)
    assigned={}
    for row in orders["allocations"]:
        settlement=_owned_settlement(state,row["settlement_id"])
        if settlement["id"] in assigned: raise ValueError("duplicate settlement allocation")
        if sum(row[k] for k in ALLOCATIONS)>settlement["civilians"]: raise ValueError("assigned workers exceed civilian population")
        settlement["allocations"]={k:row[k] for k in ALLOCATIONS}; assigned[settlement["id"]]=True
    budget={"opening_credits":opening_credits,"tax_revenue":0,"trade_revenue":credit_ledger["trade_revenue"],
        "action_credit_spending":credit_ledger["credit_spending"],"trade_spending":credit_ledger["trade_spending"],
        "spending":{},"unmet_upkeep":{},"closing_credits":0}
    production={}; consumption={}; productive_lab_workers={}; owned=[s for s in state["settlements"] if s["owned"]]
    facility_capacity=lambda s,kind,cap: cap*sum(1 for f in state["facilities"] if f["settlement_id"]==s["id"] and f["kind"]==kind and f["active_turn"]<=turn)
    # Project work produces facilities that activate after this turn's production phase.
    characters={c["assignment"]:c for c in state["characters"] if c["owned"] and c["role"]=="engineer" and c["assignment"]}
    for s in owned:
        a=s["allocations"]; stocks=s["stocks"]; sid=s["id"]
        steward=next((c for c in state["characters"] if c["owned"] and c["role"]=="steward" and c["assignment"]==sid),None)
        income=(s["civilians"]//100)*s["policy"]["tax_rate"]+(1 if steward else 0)
        if steward: steward["experience"]+=1
        _record_flow(outcomes,"inflows","taxes",{"credits":income})
        stocks["credits"]+=income; budget["tax_revenue"]+=income
        if s["policy"]["tax_rate"]==2: s["unrest"]=min(100,s["unrest"]+1)
        welfare_paid=False
        if s["policy"]["welfare"] and stocks["credits"]>=5:
            _record_flow(outcomes,"outflows","welfare",{"credits":5})
            stocks["credits"]-=5; welfare_paid=True; s["unrest"]=max(0,s["unrest"]-2)
        elif s["policy"]["welfare"]:
            budget["unmet_upkeep"].setdefault(sid,{})["welfare"]=5
        farm_workers=min(a["farmers"],facility_capacity(s,"farm",300)); farm=3*farm_workers
        tech_workers=min(a["technicians"],facility_capacity(s,"generator",100)); energy=2*tech_workers
        miner_workers=min(a["miners"],facility_capacity(s,"mine",100),stocks["energy"]+energy); ore=2*miner_workers
        ore_produced=ore
        energy_used=miner_workers
        ref_workers=min(a["refiners"],facility_capacity(s,"refinery",10),(stocks["ore"]+ore)//2,(stocks["energy"]+energy-energy_used)//2)
        ore_spent=2*ref_workers; from_new=min(ore,ore_spent); ore-=from_new; stocks["ore"]-=ore_spent-from_new
        energy_used+=2*ref_workers; metals=ref_workers; metals_produced=metals
        drill_workers=min(a["drillers"],facility_capacity(s,"promethium_well",10),(stocks["energy"]+energy-energy_used))
        energy_used+=drill_workers; prom=2*drill_workers
        factory_cap=15 if "industry-I" in state["technologies"] else 10
        mach_workers=min(a["machinists"],facility_capacity(s,"factory",factory_cap),(stocks["ore"]+ore)//2,stocks["metals"]+metals,(stocks["energy"]+energy-energy_used))
        ore_spent=2*mach_workers; from_new=min(ore,ore_spent); ore-=from_new; stocks["ore"]-=ore_spent-from_new
        metal_spent=mach_workers; from_new_metal=min(metals,metal_spent); metals-=from_new_metal; stocks["metals"]-=metal_spent-from_new_metal
        energy_used+=mach_workers; materiel=mach_workers
        lab_workers=min(a["scientists"],facility_capacity(s,"lab",10),(stocks["energy"]+energy-energy_used))
        productive_lab_workers[sid]=lab_workers
        energy_used+=lab_workers; data=lab_workers
        engineer=characters.get(sid)
        engineer_bonus=1 if engineer and a["builders"] else 0
        builder_work=a["builders"]+engineer_bonus
        active_projects=[p for p in state["projects"] if p.get("settlement_id")==sid and p["kind"] in ("facility","transport")]
        total_builder_work=0
        for project in active_projects:
            work=min(builder_work,project["work_required"]-project["work_done"]); project["work_done"]+=work; builder_work-=work
            total_builder_work+=work
            if project["work_done"]>=project["work_required"]:
                if project["kind"]=="facility":
                    state["facilities"].append({"id":project["id"],"settlement_id":sid,"kind":project["facility_kind"],"active_turn":turn+1,"completed":True})
                    if project["facility_kind"]=="habitation": s["housing"]+=200
                else:
                    fleet={"id":project["id"],"kind":"transport","owner":"player","system_id":None,
                        "location_id":s["planet_id"],"settlement_id":sid,"strength":0,"crew":0,"capacity":100,
                        "food_reserve":0,"promethium_reserve":0,"moving_until":None,"created_turn":turn,"acted_turn":-1}
                    system=next((n["parent_id"] for n in state["nodes"] if n["id"]==s["planet_id"]),None); fleet["system_id"]=system
                    if s["civilians"]>=10:
                        s["civilians"]-=10; fleet["crew"]=10; fleet["strength"]=10
                        state["fleets"].append(fleet)
                    else:
                        project["work_done"]=project["work_required"]
                        continue
                state["projects"].remove(project)
        # Docked people eat locally. Departure-turn travelers eat once at the
        # origin; their later meals come from their paid onboard/mission stores.
        remote_units=sorted((u for u in state["units"] if u.get("owner")=="player" and u.get("supply_source_id",u.get("settlement_id"))==sid
            and u.get("location_id")!=s["province_id"] and not u.get("moving_until") and u.get("ration_turn")==turn and u["strength"]>0),key=lambda x:x["id"])
        for unit in remote_units:
            reserve=unit.get("food_reserve",0); loss=min(unit["strength"],max(0,unit["strength"]-reserve))
            _record_flow(outcomes,"outflows","meals",{"food":min(unit["strength"],reserve)})
            unit["food_reserve"]=max(0,reserve-unit["strength"]); unit.pop("ration_turn",None)
            if loss:
                unit["strength"]-=loss
                outcomes["deaths"].append({"entity_id":unit["id"],"group":"soldiers","count":loss})
        departure_local=sorted((u for u in state["units"] if u.get("owner")=="player" and u.get("departure_turn")==turn and
            u.get("supply_source_id")==sid and u.get("origin_province_id")==s["province_id"] and u["strength"]>0),key=lambda x:x["id"])
        departure_remote=sorted((u for u in state["units"] if u.get("owner")=="player" and u.get("departure_turn")==turn and
            u.get("supply_source_id")==sid and u.get("origin_province_id")!=s["province_id"] and u["strength"]>0),key=lambda x:x["id"])
        for unit in departure_remote:
            reserve=unit.get("food_reserve",0); loss=min(unit["strength"],max(0,unit["strength"]-reserve))
            _record_flow(outcomes,"outflows","meals",{"food":min(unit["strength"],reserve)})
            unit["food_reserve"]=max(0,reserve-unit["strength"]); unit.pop("ration_turn",None)
            if loss:
                unit["strength"]-=loss
                outcomes["deaths"].append({"entity_id":unit["id"],"group":"soldiers","count":loss})
        local_units=sorted((u for u in state["units"] if u["id"] not in already_fed["units"] and u.get("owner")=="player" and u.get("settlement_id")==sid and u["strength"]>0 and
            (u.get("location_id")==s["province_id"] or u in departure_local)),key=lambda x:x["id"])
        local_fleets=sorted((f for f in state["fleets"] if f["id"] not in already_fed["fleets"] and f.get("owner")=="player" and f.get("crew",0)>0 and
            ((f.get("settlement_id")==sid and not f.get("moving_until")) or (f.get("origin_settlement_id")==sid and f.get("departure_turn")==turn))),key=lambda x:x["id"])
        departing_missions=sorted((m for m in state["expeditions"] if m.get("kind")=="colonize" and m.get("source_id")==sid and m.get("departure_turn")==turn),key=lambda x:x["id"])
        unit_people=sum(u["strength"] for u in local_units); crew_people=sum(f["crew"] for f in local_fleets)
        passenger_people=sum(m["settlers"] for m in departing_missions)
        total_people=0 if sid in already_fed["settlements"] else s["civilians"]+unit_people+crew_people+passenger_people
        food_available=stocks["food"]+farm; shortage=max(0,total_people-food_available)
        civilian_loss=min(s["civilians"],shortage); s["civilians"]-=civilian_loss; shortage-=civilian_loss
        if civilian_loss: outcomes["deaths"].append({"settlement_id":sid,"group":"civilians","count":civilian_loss})
        for unit in local_units:
            loss=min(unit["strength"],shortage); unit["strength"]-=loss; shortage-=loss
            if loss: outcomes["deaths"].append({"entity_id":unit["id"],"group":"soldiers","count":loss})
        for fleet in local_fleets:
            loss=min(fleet["crew"],shortage); fleet["crew"]-=loss; fleet["strength"]=fleet["crew"]; shortage-=loss
            if loss: outcomes["deaths"].append({"entity_id":fleet["id"],"group":"crew","count":loss})
        for mission in departing_missions:
            loss=min(mission["settlers"],shortage); mission["settlers"]-=loss; shortage-=loss
            if loss: outcomes["deaths"].append({"entity_id":mission["id"],"group":"settlers","count":loss})
        feed=min(total_people,food_available); stocks["food"]=max(0,food_available-feed)
        _record_flow(outcomes,"outflows","meals",{"food":feed})
        total_people-=min(total_people,shortage)
        _cleanup_destroyed_units(state,outcomes)
        if civilian_loss: s["unrest"]=min(100,s["unrest"]+5)
        else: s["unrest"]=max(0,s["unrest"])
        if sid not in already_fed["settlements"] and s["policy"]["growth_enabled"] and s["civilians"]>0 and stocks["food"]>=2*s["civilians"]:
            births=min(max(1,s["civilians"]//100),max(0,s["housing"]-total_people),stocks["food"]//2)
            _record_flow(outcomes,"outflows","growth",{"food":2*births})
            s["civilians"]+=births; stocks["food"]-=2*births
            if births: outcomes["births"].append({"settlement_id":sid,"count":births})
        if engineer_bonus and total_builder_work>a["builders"]: engineer["experience"]+=1
        # Owned unit/fleet maintenance is charged to its home settlement when known.
        upkeep_energy=sum(math.ceil(u["strength"]/10) for u in state["units"] if u.get("owner")=="player" and u.get("supply_source_id",u.get("settlement_id"))==sid and u["strength"]>0)
        upkeep_credits=upkeep_energy
        paid_energy=min(stocks["energy"]+energy,upkeep_energy); energy_total=stocks["energy"]+energy-energy_used
        paid_energy=min(energy_total,upkeep_energy); energy_total-=paid_energy
        paid_credits=min(stocks["credits"],upkeep_credits); stocks["credits"]-=paid_credits
        if paid_energy<upkeep_energy or paid_credits<upkeep_credits:
            for unit in state["units"]:
                if unit.get("owner")=="player" and unit.get("supply_source_id",unit.get("settlement_id"))==sid and unit["strength"]>0:
                    unit["readiness"]//=2
        stocks.update({"food":stocks["food"],"ore":stocks["ore"]+ore,"energy":energy_total,"metals":stocks["metals"]+metals,
            "promethium":stocks["promethium"]+prom,"materiel":stocks["materiel"]+materiel,"data":stocks["data"]+data})
        budget["spending"][sid]={"upkeep_energy":paid_energy,"upkeep_credits":paid_credits,"welfare":5 if welfare_paid else 0}
        if paid_energy<upkeep_energy: budget["unmet_upkeep"].setdefault(sid,{})["energy"]=upkeep_energy-paid_energy
        if paid_credits<upkeep_credits: budget["unmet_upkeep"].setdefault(sid,{})["credits"]=upkeep_credits-paid_credits
        outcomes["production"][sid]={"food":farm,"ore":ore_produced,"energy":energy,"metals":metals_produced,"promethium":prom,"materiel":materiel,"data":data}
        _record_flow(outcomes,"inflows","production",outcomes["production"][sid])
        _record_flow(outcomes,"outflows","recipes",{"ore":2*ref_workers+2*mach_workers,"metals":mach_workers,"energy":energy_used})
        _record_flow(outcomes,"outflows","upkeep",{"energy":paid_energy,"credits":paid_credits})
        outcomes["consumption"][sid]={"food":feed,"metals":mach_workers,"ore":2*ref_workers+2*mach_workers,"energy":energy_used+paid_energy,"population":total_people}
        production[sid]=dict(outcomes["production"][sid]); consumption[sid]=dict(outcomes["consumption"][sid])
        budget["closing_credits"]+=stocks["credits"]
    # Keep the resolved worker plan in the event summary, then clear the
    # one-turn assignments before this new snapshot becomes authoritative.
    outcomes["allocations"]={s["id"]:dict(s["allocations"]) for s in owned}
    for settlement in owned:
        settlement["allocations"]={key:0 for key in ALLOCATIONS}
    # Complete bounded technology projects; each productive scientist can do
    # at most one unit of sponsored lab work this turn.
    for project in list(state["projects"]):
        if project["kind"]=="research":
            sponsor=_by_id(owned,project["settlement_id"])
            productive=productive_lab_workers.get(sponsor["id"],0) if sponsor else 0
            work=min(5,productive,max(0,project["work_required"]-project["work_done"]),sponsor["stocks"]["data"] if sponsor else 0)
            if work and sponsor and sponsor["stocks"]["data"]>=work:
                _record_flow(outcomes,"outflows","research",{"data":work})
                sponsor["stocks"]["data"]-=work
                productive_lab_workers[sponsor["id"]]-=work
            else:
                work=0
            project["work_done"]+=work
            if project["work_done"]>=project["work_required"]:
                state["technologies"].append(project["technology_id"]); state["projects"].remove(project)
    _resolve_battles(state,pending_attacks,turn,outcomes)
    _cleanup_destroyed_fleets(state,outcomes)
    _cleanup_destroyed_units(state,outcomes)
    for loss in outcomes.get("resource_losses",[]):
        _record_flow(outcomes,"outflows","destruction",{k:v for k,v in loss.items() if k in RESOURCES})
    ledger=outcomes["resources"]; ledger["closing"]=owned_resources(state)
    for resource in RESOURCES:
        expected=ledger["opening"][resource]+sum(row.get(resource,0) for row in ledger["inflows"].values())-sum(row.get(resource,0) for row in ledger["outflows"].values())
        if expected!=ledger["closing"][resource]: raise ValueError(f"resource reconciliation invariant failed: {resource}")
    outcomes["total_consumption"]={resource:sum(row.get(resource,0) for category,row in ledger["outflows"].items() if category not in ("trade","destruction")) for resource in RESOURCES}
    state["turn"]=turn; state["narrative"]=payload["narrative"]
    budget["closing_credits"]=sum(s["stocks"]["credits"] for s in owned)
    upkeep=sum(row["upkeep_credits"]+row["welfare"] for row in budget["spending"].values())
    expected_credits=budget["opening_credits"]+budget["tax_revenue"]+budget["trade_revenue"]-budget["action_credit_spending"]-upkeep
    if budget["closing_credits"]!=expected_credits: raise ValueError("treasury reconciliation invariant failed")
    state["latest_budget"]=budget; state["latest_production"]=production
    outcomes["production"]=production; outcomes["consumption"]=consumption
    state["latest_outcome"]=outcomes
    humans_after=sum(s["civilians"] for s in state["settlements"] if s["owned"])+sum(u["strength"] for u in state["units"] if u["owner"]=="player")+sum(f["crew"] for f in state["fleets"] if f["owner"]=="player")+sum(m.get("settlers",0) for m in state["expeditions"] if m.get("kind")=="colonize")
    births_total=sum(row["count"] for row in outcomes["births"]); deaths_total=sum(row["count"] for row in outcomes["deaths"])
    if humans_before+births_total-deaths_total!=humans_after: raise ValueError("population reconciliation invariant failed")
    return state,outcomes


def advance(state, payload):
    validate_submission(payload)
    work=json.loads(canonical_json(state))
    campaign_id=work.get("_private",{}).get("campaign_id")
    if not campaign_id: raise ValueError("v2 state invariant missing campaign identity")
    outcome_state,outcome=_resolve(work,payload)
    return outcome_state,outcome
