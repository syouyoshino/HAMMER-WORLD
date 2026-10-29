import argparse
import json
from .archive import worker_from_environment
from .sqlite_migration import import_sqlite
from .store import Store
from .planet_generation import GEOLOGIES, PRESETS, LAKE_MATERIALS, POLAR_CAPS
from .universe import build_universe, V2_SCHEMA, V2_RULES


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main():
    p=argparse.ArgumentParser(prog="hammer-world")
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("init")
    q=sub.add_parser("init-v2"); q.add_argument("--campaign-id",default="demo-v2"); q.add_argument("--seed",type=int,default=741903)
    q.add_argument("--planet-generator",choices=("planet-v1","planet-v2","planet-v3","planet-v4","planet-v5","planet-v6","planet-v7","planet-v8","planet-v9","planet-v10"),default="planet-v1",
                   help="generator for a new isolated demo; existing campaigns are never regenerated")
    q.add_argument("--preset",choices=("auto",*PRESETS),default=None,
                   help="planet-v4 through v10 water/surface preset applied to every planet unless overridden")
    q.add_argument("--planet-preset",action="append",default=[],metavar="PLANET_ID=PRESET",
                   help="planet-v4 through v10 override; repeat for independent stable planet node IDs")
    q.add_argument("--geology",choices=GEOLOGIES,default=None,help="planet-v7 through v10 geology applied to every planet")
    q.add_argument("--planet-geology",action="append",default=[],metavar="PLANET_ID=CHOICE",
                   help="planet-v7 through v10 per-planet geology override; repeat for independent planet IDs")
    q.add_argument("--lake-material", choices=LAKE_MATERIALS, default=None, help="planet-v8 saved lake composition")
    q.add_argument("--polar-caps", choices=POLAR_CAPS, default=None, help="planet-v8 saved polar composition")
    q.add_argument("--planet-lake-material", action="append", default=[], metavar="PLANET_ID=CHOICE")
    q.add_argument("--planet-polar-caps", action="append", default=[], metavar="PLANET_ID=CHOICE")
    q.add_argument("--feature-names", choices=("none", "generated"), default=None)
    q.add_argument("--feature-names-file", default=None, metavar="JSON")
    q.add_argument("--astronomy", choices=("static-v1",), default=None,
                   help="save deterministic frozen system coordinates for this new demo only")
    q.add_argument("--catalog", action="store_true", help="validate in memory and print a hydrography authoring catalog without opening the database")
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
        geologies={}
        for value in args.planet_geology:
            if "=" not in value: p.error("--planet-geology must be PLANET_ID=CHOICE")
            planet_id,choice=value.split("=",1)
            if planet_id in geologies: p.error(f"duplicate --planet-geology for {planet_id}")
            if choice not in GEOLOGIES: p.error(f"unsupported planet geology: {choice}")
            geologies[planet_id]=choice
        args.planet_geologies=geologies or None
        if args.planet_generator not in ("planet-v4","planet-v5","planet-v6","planet-v7","planet-v8","planet-v9","planet-v10") and (args.preset is not None or args.planet_presets is not None):
            p.error("--preset and --planet-preset require planet-v4 through planet-v10")
        if args.planet_generator not in ("planet-v7","planet-v8","planet-v9","planet-v10") and (args.geology is not None or args.planet_geologies is not None):
            p.error("--geology and --planet-geology require --planet-generator planet-v7 or later")
        for option, destination, choices in (("planet_lake_material", "planet_lake_materials", LAKE_MATERIALS),
                                               ("planet_polar_caps", "planet_polar_caps_map", POLAR_CAPS)):
            overrides = {}
            flag = "--"+option.replace("_", "-")
            for value in getattr(args, option):
                if "=" not in value: p.error(f"{flag} must be PLANET_ID=CHOICE")
                planet_id, choice = value.split("=", 1)
                if planet_id in overrides: p.error(f"duplicate {flag} for {planet_id}")
                if choice not in choices: p.error(f"unsupported surface material: {choice}")
                if planet_id not in {f"{args.campaign_id}-planet-{suffix}" for suffix in ("reach", "ash", "haven", "veil")}:
                    p.error(f"unknown planet ID: {planet_id}")
                overrides[planet_id] = choice
            setattr(args, destination, overrides or None)
        if args.planet_generator != "planet-v8" and (args.lake_material is not None or args.polar_caps is not None or args.planet_lake_materials is not None or args.planet_polar_caps_map is not None):
            if args.planet_generator not in ("planet-v9","planet-v10"): p.error("surface material options require --planet-generator planet-v8 or later")
        feature_file = None
        if args.feature_names_file:
            if args.planet_generator not in ("planet-v9","planet-v10"): p.error("--feature-names-file requires --planet-generator planet-v9")
            try:
                with open(args.feature_names_file, encoding="utf8") as f:
                    feature_file = json.load(f, object_pairs_hook=_unique_object)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                p.error(f"invalid feature names JSON: {exc}")
            if not isinstance(feature_file, dict) or any(not isinstance(k, str) or not isinstance(v, dict) for k, v in feature_file.items()):
                p.error("feature names file must map planet node IDs to feature ID maps")
        if args.feature_names is not None and args.planet_generator not in ("planet-v9","planet-v10"):
            p.error("--feature-names requires --planet-generator planet-v9")
        args.feature_name_overrides = feature_file
        if args.catalog and args.planet_generator not in ("planet-v9","planet-v10"):
            p.error("--catalog requires --planet-generator planet-v9")
        if args.catalog:
            try:
                detail_assets = {}
                state = build_universe(args.campaign_id, args.seed, planet_generator=args.planet_generator,
                    preset=args.preset, planet_presets=args.planet_presets, geology=args.geology or "none",
                    planet_geologies=args.planet_geologies, lake_material=args.lake_material, polar_caps=args.polar_caps,
                    planet_lake_materials=args.planet_lake_materials, planet_polar_caps=args.planet_polar_caps_map,
                    feature_names=args.feature_names, feature_name_overrides=args.feature_name_overrides, detail_assets=detail_assets,
                    astronomy=args.astronomy)
                Store.validate_state(V2_SCHEMA, V2_RULES, 0, state)
            except (ValueError, TypeError) as exc:
                p.error(str(exc))
            catalog = []
            for planet_id, geo in state["geography"].items():
                if args.planet_generator == "planet-v10":
                    from collections import Counter
                    payload = detail_assets[geo["detail_ref"]["sha256"]]
                    counts = Counter(payload["feature_index"])
                    courses = {r["id"]:len(r["points"]) for r in payload["rivers"]}
                    for index, feature in enumerate(payload["hydrography"]["features"], 1):
                        catalog.append({"planet_id":planet_id,"feature_id":feature["id"],"kind":feature["kind"],
                            "material":feature["material"],"cell_count":courses.get(feature["id"],counts[index]),
                            "anchor":feature["anchor"],"name":feature["name"]})
                else:
                    for feature in geo["surface"]["hydrography"]["features"]:
                        catalog.append({"planet_id":planet_id,"feature_id":feature["id"],"kind":feature["kind"],
                            "material":feature["material"],"cell_count":len(feature["cells"]),"anchor":feature["anchor"],"name":feature["name"]})
            print(json.dumps({"status":"uncommitted_creation_preview","campaign_id":args.campaign_id,"catalog":catalog},indent=2,ensure_ascii=False))
            return
    db=Store()
    if args.command=="init":
        try: sid=db.create_demo()
        except ValueError: sid=db.current("demo")["campaign"]["current_snapshot_id"]
        if not any(c["id"] == "campaign" for c in db.campaigns()):
            db.create_pregame()
        out={"demo_snapshot_id":sid,"campaigns":db.campaigns()}
    elif args.command=="init-v2":
        sid=db.create_demo_v2(args.campaign_id,args.seed,planet_generator=args.planet_generator,
                              preset=args.preset,planet_presets=args.planet_presets,
                              geology=args.geology or "none",planet_geologies=args.planet_geologies,
                              lake_material=args.lake_material, polar_caps=args.polar_caps,
                              planet_lake_materials=args.planet_lake_materials, planet_polar_caps=args.planet_polar_caps_map,
                              feature_names=args.feature_names, feature_name_overrides=args.feature_name_overrides,
                              astronomy=args.astronomy)
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
