import argparse
import json
from .archive import worker_from_environment
from .sqlite_migration import import_sqlite
from .store import Store


def main():
    p=argparse.ArgumentParser(prog="hammer-world")
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("init")
    q=sub.add_parser("init-v2"); q.add_argument("--campaign-id",default="demo-v2"); q.add_argument("--seed",type=int,default=741903)
    q=sub.add_parser("packet"); q.add_argument("campaign_id")
    q=sub.add_parser("preview"); q.add_argument("campaign_id"); q.add_argument("proposal")
    q=sub.add_parser("import-turn"); q.add_argument("campaign_id"); q.add_argument("proposal")
    q=sub.add_parser("restore"); q.add_argument("campaign_id"); q.add_argument("snapshot_id"); q.add_argument("new_campaign_id")
    q=sub.add_parser("backup"); q.add_argument("destination")
    q=sub.add_parser("sync"); q.add_argument("--limit",type=int,default=10)
    q=sub.add_parser("import-sqlite"); q.add_argument("source"); q.add_argument("--backup",required=True)
    args=p.parse_args(); db=Store()
    if args.command=="init":
        try: sid=db.create_demo()
        except ValueError: sid=db.current("demo")["campaign"]["current_snapshot_id"]
        if not any(c["id"] == "campaign" for c in db.campaigns()):
            db.create_pregame()
        out={"demo_snapshot_id":sid,"campaigns":db.campaigns()}
    elif args.command=="init-v2":
        sid=db.create_demo_v2(args.campaign_id,args.seed)
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
