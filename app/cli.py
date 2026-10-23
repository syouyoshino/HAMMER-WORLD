import argparse
import json
from .archive import worker_from_environment
from .sqlite_migration import import_sqlite
from .store import Store
from .planet_generation import PRESETS


def main():
    p=argparse.ArgumentParser(prog="hammer-world")
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("init")
    q=sub.add_parser("init-v2"); q.add_argument("--campaign-id",default="demo-v2"); q.add_argument("--seed",type=int,default=741903)
    q.add_argument("--planet-generator",choices=("planet-v1","planet-v2","planet-v3","planet-v4","planet-v5"),default="planet-v1",
                   help="generator for a new isolated demo; existing campaigns are never regenerated")
    q.add_argument("--preset",choices=("auto",*PRESETS),default=None,
                   help="planet-v4/v5 preset applied to every planet unless overridden")
    q.add_argument("--planet-preset",action="append",default=[],metavar="PLANET_ID=PRESET",
                   help="planet-v4/v5 override; repeat for independent stable planet node IDs")
    q=sub.add_parser("packet"); q.add_argument("campaign_id")
    q=sub.add_parser("preview"); q.add_argument("campaign_id"); q.add_argument("proposal")
    q=sub.add_parser("import-turn"); q.add_argument("campaign_id"); q.add_argument("proposal")
    q=sub.add_parser("restore"); q.add_argument("campaign_id"); q.add_argument("snapshot_id"); q.add_argument("new_campaign_id")
    q=sub.add_parser("backup"); q.add_argument("destination")
    q=sub.add_parser("sync"); q.add_argument("--limit",type=int,default=10)
    q=sub.add_parser("import-sqlite"); q.add_argument("source"); q.add_argument("--backup",required=True)
    args=p.parse_args()
    if args.command=="init-v2":
        overrides={}
        for value in args.planet_preset:
            if "=" not in value:
                p.error("--planet-preset must be PLANET_ID=PRESET")
            planet_id, choice=value.split("=",1)
            if planet_id in overrides:
                p.error(f"duplicate --planet-preset for {planet_id}")
            if choice not in PRESETS:
                p.error(f"unsupported planet preset: {choice}")
            overrides[planet_id]=choice
        args.planet_presets=overrides or None
        if args.planet_generator not in ("planet-v4","planet-v5") and (args.preset is not None or args.planet_presets is not None):
            p.error("--preset and --planet-preset require --planet-generator planet-v4 or planet-v5")
    db=Store()
    if args.command=="init":
        try: sid=db.create_demo()
        except ValueError: sid=db.current("demo")["campaign"]["current_snapshot_id"]
        if not any(c["id"] == "campaign" for c in db.campaigns()):
            db.create_pregame()
        out={"demo_snapshot_id":sid,"campaigns":db.campaigns()}
    elif args.command=="init-v2":
        sid=db.create_demo_v2(args.campaign_id,args.seed,planet_generator=args.planet_generator,
                              preset=args.preset,planet_presets=args.planet_presets)
        out={"campaign_id":args.campaign_id,"snapshot_id":sid,"campaigns":db.campaigns()}
    elif args.command=="packet": out=db.packet(args.campaign_id)
    elif args.command in ("preview","import-turn"):
        with open(args.proposal,encoding="utf8") as f: proposal=json.load(f)
        out=(db.preview if args.command=="preview" else db.commit)(args.campaign_id,proposal)
    elif args.command=="restore": out={"snapshot_id":db.restore(args.campaign_id,args.snapshot_id,args.new_campaign_id)}
    elif args.command=="backup": out={"backup":db.backup(args.destination)}
    elif args.command=="sync":
        worker=worker_from_environment(db)
        try: out=worker.sync(limit=args.limit)
        finally:
            if worker.adapter is not None: worker.adapter.close()
    else: out=import_sqlite(args.source,args.backup,db)
    print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=="__main__": main()
