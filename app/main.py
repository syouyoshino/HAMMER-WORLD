import hmac
import os
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request, Query
from pathlib import Path
from .store import Store
from .universe import owned_humans, owned_resources

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"
app = FastAPI(title="Hammer World API", version="0.1.0")
app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")
store = Store()


def validate_access_configuration(environ=None):
    env=os.environ if environ is None else environ
    mode=env.get("WOLD_ACCESS_MODE","local")
    gm=env.get("WOLD_GM_TOKEN")
    player=env.get("WOLD_PLAYER_TOKEN")
    if mode not in ("local","private"): raise RuntimeError("WOLD_ACCESS_MODE must be local or private")
    if mode=="private" and not gm: raise RuntimeError("private access requires WOLD_GM_TOKEN")
    if player and gm and hmac.compare_digest(player,gm): raise RuntimeError("player and GM tokens must differ")
    allowed={x.strip() for x in env.get("WOLD_PLAYER_CAMPAIGNS","").split(",") if x.strip()}
    if "*" in allowed: raise RuntimeError("WOLD_PLAYER_CAMPAIGNS cannot contain wildcards")
    return mode,allowed


validate_access_configuration()


def player_projection(snapshot):
    return Store.player_state(snapshot)



MAX_PROPOSAL_BYTES = 32768

@app.middleware("http")
async def limit_admin_proposal_body(request: Request, call_next):
    if request.url.path.startswith("/api/admin/") and request.method == "POST":
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > MAX_PROPOSAL_BYTES):
            return HTMLResponse("request body too large", status_code=413)
        chunks=[]
        total=0
        while True:
            message=await request.receive()
            if message["type"] == "http.disconnect":
                return HTMLResponse("request disconnected", status_code=400)
            chunk=message.get("body",b"")
            total += len(chunk)
            if total > MAX_PROPOSAL_BYTES:
                return HTMLResponse("request body too large", status_code=413)
            chunks.append(chunk)
            if not message.get("more_body",False): break
        body=b"".join(chunks)
        async def receive():
            return {"type":"http.request", "body":body, "more_body":False}
        request._receive=receive
    return await call_next(request)


def gm_auth(authorization: str | None = Header(default=None)):
    token = os.environ.get("WOLD_GM_TOKEN")
    if not token or not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "GM authorization required")
    if not hmac.compare_digest(authorization[7:], token):
        raise HTTPException(401, "GM authorization required")


def _player_role(authorization):
    mode,allowed=validate_access_configuration()
    if mode=="local": return "local"
    gm=os.environ.get("WOLD_GM_TOKEN"); player=os.environ.get("WOLD_PLAYER_TOKEN")
    token=authorization[7:] if authorization and authorization.startswith("Bearer ") else None
    if token and gm and hmac.compare_digest(token,gm): return "gm"
    if token and player and hmac.compare_digest(token,player): return "player"
    return None


def _require_campaign_access(campaign_id,authorization):
    role=_player_role(authorization)
    if role=="local" or role=="gm": return role
    mode,allowed=validate_access_configuration()
    if role=="player" and campaign_id in allowed: return role
    raise HTTPException(404,"campaign not found")


def translate_error(exc):
    message = str(exc)
    if isinstance(exc, KeyError): raise HTTPException(404, message.strip("'"))
    if isinstance(exc, RuntimeError): raise HTTPException(409, message)
    if isinstance(exc, ValueError): raise HTTPException(409 if "submission_id" in message else 422, message)
    raise exc


@app.get("/api/player/campaigns")
def player_campaigns(authorization: str|None=Header(default=None)):
    role=_player_role(authorization)
    if role is None: raise HTTPException(401,"player authorization required")
    _,allowed=validate_access_configuration()
    output=[]
    for campaign in store.campaigns():
        if role=="player" and campaign["id"] not in allowed: continue
        snap=store.current(campaign["id"])["snapshot"]
        output.append({"id":campaign["id"],"kind":campaign["kind"],"turn":snap["turn"] if snap else None,
                       "snapshot_id":snap["id"] if snap else None,
                       "schema_version":snap["schema_version"] if snap else None,
                       "rules_version":snap["rules_version"] if snap else None})
    return output


def _archive(snapshot_id):
    with store.connect() as c:
        r=c.execute("SELECT status FROM outbox WHERE snapshot_id=%s",(snapshot_id,)).fetchone()
    return r["status"] if r else None


@app.get("/api/player/campaigns/{campaign_id}")
def player_campaign(campaign_id: str,authorization: str|None=Header(default=None)):
    _require_campaign_access(campaign_id,authorization)
    cur=store.current(campaign_id)
    if not cur: raise HTTPException(404,"campaign not found")
    snap=cur["snapshot"]
    return {"id":campaign_id,"kind":cur["campaign"]["kind"],"state":player_projection(snap) if snap else None,
            "snapshot_id":snap["id"] if snap else None,"turn":snap["turn"] if snap else None,
            "archive_status":_archive(snap["id"]) if snap else None,
            "created_at":snap["created_at"] if snap else None}


@app.get("/api/player/campaigns/{campaign_id}/history")
def player_history(campaign_id: str, offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100),authorization: str|None=Header(default=None)):
    _require_campaign_access(campaign_id,authorization)
    if not store.current(campaign_id): raise HTTPException(404,"campaign not found")
    history,total=store.history(campaign_id,limit=limit,offset=offset)
    page=history
    items=[]
    for h in page:
        projected=player_projection({"schema_version":h["schema_version"],"rules_version":h["rules_version"],"state":h["state"]})
        if h["state"].get("settlements") is not None:
            owned=[s for s in h["state"]["settlements"] if s["owned"]]
            economy={"population":owned_humans(h["state"]),**owned_resources(h["state"])}
            outcome=projected.get("latest_outcome")
        else:
            economy={key:h["state"][key] for key in ("population","food","ore","energy")}
            outcome=(projected.get("outcomes") or [None])[-1]
        metrics={"population":economy.get("population"),"food":economy.get("food"),"ore":economy.get("ore"),
                 "energy":economy.get("energy"),"treasury":economy.get("credits")}
        if (h.get("schema_version"),h.get("rules_version"))==("world-v2","demo-v2"):
            raw_outcome=h["state"].get("latest_outcome") or {}
            resource_ledger=raw_outcome.get("resources") or {}
            produced=resource_ledger.get("inflows",{}).get("production",{})
            consumed=raw_outcome.get("total_consumption",{})
            budget=h["state"].get("latest_budget") or {}
            metrics.update({"military":sum(1 for x in h["state"].get("units",[]) if x.get("owner")=="player" and x.get("strength",0)>0)
                                      +sum(1 for x in h["state"].get("fleets",[]) if x.get("owner")=="player" and x.get("crew",0)>0),
                            "military_personnel":sum(x.get("strength",0) for x in h["state"].get("units",[]) if x.get("owner")=="player")
                                      +sum(x.get("crew",0) for x in h["state"].get("fleets",[]) if x.get("owner")=="player"),
                            "projects":sum(1 for x in h["state"].get("projects",[]) if x.get("owned",True)),
                            "research":len(h["state"].get("technologies",[])),
                            "metals":economy.get("metals"),"materiel":economy.get("materiel"),
                            "promethium":economy.get("promethium"),"data":economy.get("data"),
                            "food_produced":produced.get("food"),"energy_produced":produced.get("energy"),
                            "food_consumed":consumed.get("food"),"energy_consumed":consumed.get("energy"),
                            "tax_revenue":budget.get("tax_revenue"),"trade_revenue":budget.get("trade_revenue"),
                            "action_credit_spending":budget.get("action_credit_spending"),"trade_spending":budget.get("trade_spending"),
                            "territories":sum(1 for x in owned),"facilities":sum(1 for x in h["state"].get("facilities",[]) if x.get("owned",True))})
        else:
            metrics.update({key:None for key in ("military","military_personnel","projects","research","metals","materiel","promethium","data","food_produced","energy_produced","food_consumed","energy_consumed","tax_revenue","trade_revenue","action_credit_spending","trade_spending","territories","facilities")})
        items.append({"id":h["id"],"turn":h["turn"],"economy":economy,"metrics":metrics,"outcome":outcome,
            "narrative":h["state"]["narrative"],"created_at":h["created_at"],"archive_status":h["archive_status"]})
    return {"offset":offset,"limit":limit,"total":total,"items":items}


@app.get("/api/player/snapshots/{snapshot_id}")
def player_snapshot(snapshot_id: str,authorization: str|None=Header(default=None)):
    snap=store.snapshot(snapshot_id)
    if not snap: raise HTTPException(404,"snapshot not found")
    _require_campaign_access(snap["campaign_id"],authorization)
    return {"id":snap["id"],"campaign_id":snap["campaign_id"],"turn":snap["turn"],"state":player_projection(snap),"created_at":snap["created_at"],"archive_status":_archive(snapshot_id)}


@app.get("/api/player/campaigns/{campaign_id}/map")
def player_map(campaign_id: str, level: str=Query(default="galactic"), node_id: str|None=None,
               snapshot_id: str|None=None, overlay: str=Query(default="terrain"),authorization: str|None=Header(default=None)):
    _require_campaign_access(campaign_id,authorization)
    try: return store.map_view(campaign_id,level,node_id,snapshot_id,overlay)
    except Exception as e: translate_error(e)


@app.get("/api/player/campaigns/{campaign_id}/systems")
def player_systems(campaign_id: str, section: str=Query(...), snapshot_id: str|None=None,authorization: str|None=Header(default=None)):
    _require_campaign_access(campaign_id,authorization)
    try: return store.systems(campaign_id,section,snapshot_id)
    except Exception as e: translate_error(e)


@app.get("/api/access")
def access_status():
    mode,_=validate_access_configuration()
    return {"mode":mode,"login_required":mode=="private"}


@app.get("/api/admin/campaigns",dependencies=[Depends(gm_auth)])
def admin_campaigns(): return store.campaigns()


@app.get("/api/admin/campaigns/{campaign_id}/packet",dependencies=[Depends(gm_auth)])
def packet(campaign_id: str):
    try:return store.packet(campaign_id)
    except Exception as e: translate_error(e)


@app.post("/api/admin/campaigns/{campaign_id}/preview",dependencies=[Depends(gm_auth)])
def preview(campaign_id: str, payload: dict):
    try:return store.preview(campaign_id,payload)
    except Exception as e: translate_error(e)


@app.post("/api/admin/campaigns/{campaign_id}/commit",dependencies=[Depends(gm_auth)])
def commit(campaign_id: str, payload: dict):
    try:return store.commit(campaign_id,payload)
    except Exception as e: translate_error(e)


@app.post("/api/admin/campaigns/{campaign_id}/restore",dependencies=[Depends(gm_auth)])
def restore(campaign_id: str, payload: dict):
    if not isinstance(payload,dict) or set(payload)!={"snapshot_id","new_campaign_id"}:
        raise HTTPException(422,"restore requires snapshot_id and new_campaign_id")
    try:return {"campaign_id":payload["new_campaign_id"],"snapshot_id":store.restore(campaign_id,payload["snapshot_id"],payload["new_campaign_id"])}
    except Exception as e: translate_error(e)


@app.get("/",response_class=HTMLResponse)
def dashboard():
    return FileResponse(PUBLIC_DIR / "index.html")
