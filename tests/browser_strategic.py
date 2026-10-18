"""Focused strategic command journey using an isolated PostgreSQL fixture."""
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
import json
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
import psycopg
from psycopg import sql
from playwright.sync_api import sync_playwright
from app.store import Store
from app.engine_v2 import ALLOCATIONS


def main():
    dsn = os.environ["WOLD_TEST_DATABASE_URL"]
    schema = "browser_strategic_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    server = None
    try:
        db = Store(dsn, schema=schema)
        db.create_demo_v2()
        db.create_demo()
        db.create_pregame()
        gm, player = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        environment = os.environ.copy()
        environment.update(WOLD_DATABASE_URL=dsn, WOLD_DB_SCHEMA=schema, WOLD_ACCESS_MODE="private",
                           WOLD_GM_TOKEN=gm, WOLD_PLAYER_TOKEN=player, WOLD_PLAYER_CAMPAIGNS="demo-v2")
        with socket.socket() as connection:
            connection.bind(("127.0.0.1", 0))
            port = connection.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        with tempfile.TemporaryDirectory() as scratch, open(Path(scratch) / "server.log", "w") as log:
            server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                                       "--port", str(port), "--no-access-log"], env=environment, stdout=log, stderr=log)
            for _ in range(100):
                try:
                    if httpx.get(base + "/api/access").status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                time.sleep(.1)
            else:
                raise RuntimeError("Strategic browser test server failed to start")
            with sync_playwright() as playwright:
                executable = os.environ.get("WOLD_CHROMIUM_EXECUTABLE") or shutil.which("chromium")
                browser = playwright.chromium.launch(executable_path=executable, headless=True,
                                                       args=["--no-sandbox", "--disable-dev-shm-usage"])
                page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1, has_touch=True)
                page.set_default_timeout(10000)
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                timings = {}
                page.goto(base)
                page.fill("#access-token", player)
                page.click("#login-button")
                page.wait_for_function("document.querySelectorAll('#campaign-select option').length === 2")
                # Use the visible modal close and real pointer/keyboard selection path.
                page.locator("[data-dialog-close]").click()
                page.locator("#campaign-select").click()
                page.keyboard.press("ArrowDown")
                page.keyboard.press("Enter")
                page.wait_for_function("document.querySelector('#command-turn').textContent === 'TURN 0' && document.querySelector('#map-placeholder').hidden")
                page.evaluate("document.querySelector('.toast')?.remove()")
                assert page.locator("#command-workspace").is_hidden()
                assert page.locator("#command-inspector").is_hidden()
                assert page.locator("#planet-map").evaluate("el=>el.isConnected")
                map_frame = page.locator(".map-frame")
                initial_size = map_frame.bounding_box()
                assert initial_size["width"] == 1280 and initial_size["height"] == 900
                out = Path("data/strategic-candidate")
                out.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(out / "map.png"))
                page.select_option("#map-level", "planet")
                page.wait_for_function("document.querySelector('#map-scale').textContent.includes('GRID')")
                page.wait_for_load_state("networkidle")
                state = db.player_state(db.current("demo-v2")["snapshot"])
                settlement = next(x for x in state["settlements"] if x.get("planet_id"))
                planet = next(x for x in state["nodes"] if x["id"] == settlement["planet_id"])
                province = next(x for x in db.map_view("demo-v2", "planet", planet["id"])["geometry"]["provinces"]
                                if x["id"] == settlement["province_id"])
                frame = map_frame.bounding_box()
                tile = min(frame["width"] / 64, frame["height"] / 40)
                click_x = frame["x"] + (province["x"] + province["width"] / 2) * tile
                click_y = frame["y"] + (frame["height"] - 40 * tile) / 2 + (province["y"] + province["height"] / 2) * tile
                page.mouse.click(click_x, click_y)
                page.wait_for_selector("#command-inspector:not([hidden])")
                page.wait_for_function("document.querySelector('#inspector-content').innerText.includes('LOCAL SETTLEMENTS')", timeout=2000)
                inspector_text = page.locator("#inspector-content").inner_text()
                assert settlement["id"] in inspector_text
                assert "Province ID" in inspector_text
                page.screenshot(path=str(out / "inspector.png"))
                # Retain a nondefault overlay/camera and the actual selected province.
                page.select_option("#overlay-select", "population")
                page.wait_for_load_state("networkidle")
                page.locator("#zoom-in").click()
                page.mouse.move(700, 500)
                page.mouse.down()
                page.mouse.move(730, 520, steps=3)
                page.mouse.up()
                preserved_map = page.evaluate("({pixels:document.querySelector('#planet-map').toDataURL(),zoom:document.querySelector('#zoom-reset').textContent,overlay:document.querySelector('#overlay-select').value,selection:document.querySelector('#inspector-content').textContent})")
                page.evaluate("window.__preservedCanvas=document.querySelector('#planet-map')")
                page.locator("#inspector-content .inspector-actions button").first.click()
                started = time.perf_counter()
                page.wait_for_function("!document.querySelector('#command-workspace').hidden && !document.querySelector('#economy-panel .local-scope').hidden")
                timings["cold_economy_ms"] = (time.perf_counter() - started) * 1000
                economy = page.locator(".workspace-content").inner_text()
                assert "LOCAL HOLDINGS" in economy and "CAMPAIGN-WIDE TOTALS" not in economy
                assert settlement["id"] not in economy
                assert "Housing" in economy and "Unrest" in economy
                assert "Main economic issue and forecast are unrecorded" in economy
                page.locator("#economy-panel details summary").click()
                assert settlement["id"] in page.locator("#economy-panel").inner_text()
                page.locator("#economy-panel details summary").click()
                page.locator("#economy-panel [data-scope=campaign]").click()
                assert "CAMPAIGN-WIDE TOTALS" in page.locator("#economy-panel").inner_text()
                page.locator("#economy-panel [data-scope=local]").click()
                page.screenshot(path=str(out / "economy.png"))
                assert page.locator("#command-workspace .workspace-title").inner_text() == "Economy"
                page.locator(".workspace-tabs button[data-tab=construction]").click()
                started = time.perf_counter()
                page.wait_for_function("(()=>{const p=document.querySelector('#management-construction'),l=p?.querySelector('.local-scope');return !!l&&!l.hidden&&p.innerText.includes('LOCAL CONSTRUCTION')})()")
                timings["cold_construction_ms"] = (time.perf_counter() - started) * 1000
                construction = page.locator(".workspace-content").inner_text()
                assert "LOCAL CONSTRUCTION" in construction and "Farm" in construction
                local_ids = {item["id"] for item in state["settlements"]
                             if item.get("planet_id") == planet["id"] and item.get("province_id") == province["id"]}
                local_facility_count = sum(item.get("settlement_id") in local_ids for item in state.get("facilities", []))
                facility_label = "facility" if local_facility_count == 1 else "facilities"
                assert f"{local_facility_count} recorded {facility_label}" in construction
                page.locator("#management-construction [data-scope=campaign]").click()
                assert "CAMPAIGN-WIDE FACILITIES" in page.locator("#management-construction").inner_text()
                page.locator("#management-construction [data-scope=local]").click()
                page.locator("#management-construction .local-scope details summary").first.click()
                assert settlement["id"] in page.locator("#management-construction").inner_text()
                page.screenshot(path=str(out / "construction.png"))
                page.locator("[data-return-map]").click()
                assert page.locator("#command-workspace").is_hidden()
                assert page.locator("#planet-map").evaluate("el=>el.isConnected")
                assert page.locator(".map-frame").bounding_box() == initial_size
                assert page.locator("#selected-record").count() == 0
                assert page.evaluate("window.__preservedCanvas===document.querySelector('#planet-map')")
                assert page.evaluate("({pixels:document.querySelector('#planet-map').toDataURL(),zoom:document.querySelector('#zoom-reset').textContent,overlay:document.querySelector('#overlay-select').value,selection:document.querySelector('#inspector-content').textContent})") == preserved_map
                # The command menu remains available while the map stays behind it.
                page.click("#hw-command")
                assert page.locator("#command-menu .menu-grid button").count() == 19
                page.screenshot(path=str(out / "menu.png"))
                page.locator("#edge-shortcut").check()
                assert page.evaluate("localStorage.getItem('hw.command.edge.v1')") == "true"
                page.keyboard.press("Escape")
                page.mouse.move(1, 350)
                page.wait_for_function("!document.querySelector('#command-menu').hidden", timeout=2000)
                page.mouse.move(500, 350)
                page.wait_for_function("document.querySelector('#command-menu').hidden", timeout=2500)
                # A map gesture across the edge suppresses the optional hover reveal.
                page.mouse.move(30, 500)
                page.mouse.down()
                page.mouse.move(1, 505, steps=3)
                assert page.locator("#command-menu").is_hidden()
                page.mouse.up()
                page.click("#hw-command")
                page.locator("#edge-shortcut").uncheck()
                page.keyboard.press("Escape")
                assert page.evaluate("localStorage.getItem('hw.command.edge.v1')") == "false"
                page.click("#hw-command")
                page.locator("#command-menu").get_by_role("button", name="Military", exact=True).click()
                page.wait_for_function("document.querySelector('#command-workspace .workspace-title').textContent === 'Military' && document.querySelector('.workspace-content').innerText.includes('Military')")
                assert page.locator("#command-workspace").is_visible()
                assert page.locator("#command-inspector").is_hidden()
                page.wait_for_function("id=>document.querySelector('#management-military')?.textContent.includes(id)", arg=state["units"][0]["id"])
                assert page.locator(".workspace-scope").inner_text().startswith("Campaign-wide")
                page.screenshot(path=str(out / "military.png"))
                military_wrapper = page.locator(".workspace-content #management-military")
                assert military_wrapper.evaluate("el=>el.isConnected && !el.hidden")
                # Every menu destination resolves to its own retained, connected wrapper.
                destinations = ["economy", "industry", "fleet", "politics", "trade", "factions", "budget",
                                "logistics", "construction", "research", "military", "diplomacy",
                                "intelligence", "exploration", "colonies", "characters"]
                for destination in destinations:
                    if destination == "economy":
                        page.evaluate("window.HWDesktop.open('economy')")
                    else:
                        page.evaluate("document.querySelector('#hw-command').click();")
                        page.locator(f"#command-menu button[data-open='{destination}']").click()
                    page.wait_for_function("view=>document.querySelector('#command-workspace .workspace-title').textContent.toLowerCase()===view", arg=destination)
                    if destination != "economy":
                        aliases = {"industry":["economy","construction"], "fleet":["military"], "politics":["overview","diplomacy"], "trade":["logistics","diplomacy"], "factions":["diplomacy"]}
                        sections = aliases.get(destination, [destination])
                        expected = [db.systems("demo-v2", section)["records"] for section in sections]
                        def strings(value):
                            if isinstance(value, dict):
                                return [x for child in value.values() for x in strings(child)]
                            if isinstance(value, list):
                                return [x for child in value for x in strings(child)]
                            if value is None:
                                return ["Unknown"]
                            if isinstance(value, bool):
                                return ["Yes" if value else "No"]
                            return [str(value)] if isinstance(value, (str, int, float)) else []
                        sentinels = list(dict.fromkeys(x for record in expected for x in strings(record)))[:3]
                        page.wait_for_function("arg=>{const p=document.querySelector('#management-'+arg.view);return p&&arg.values.every(x=>p.textContent.includes(x))}", arg={"view":destination,"values":sentinels})
                        if not sentinels:
                            page.wait_for_function("view=>document.querySelector('#management-'+view)?.querySelector('.empty-note')?.textContent.match(/No recorded values|No records/)", arg=destination)
                    visible = page.locator(".workspace-content > :not([hidden])")
                    assert visible.count() == 1, f"More than one primary report visible for {destination}"
                page.evaluate("window.HWDesktop.open('history')")
                page.wait_for_function("document.querySelector('.workspace-content #history-panel')?.innerText.includes('Historical record')")
                page.evaluate("window.HWDesktop.open('orders')")
                page.wait_for_selector("#proposal-json")
                page.fill("#proposal-json", "retained unsent order draft")
                assert page.locator(".workspace-scope").inner_text().startswith("Campaign-wide")
                page.screenshot(path=str(out / "orders.png"))
                page.evaluate("window.HWDesktop.open('history')")
                page.evaluate("window.HWDesktop.open('orders')")
                assert page.locator("#proposal-json").input_value() == "retained unsent order draft"
                assert page.locator("#history-panel").evaluate("el=>el.isConnected")
                page.evaluate("window.HWDesktop.open('characters')")
                page.wait_for_selector("#management-characters .entity-select")
                page.locator("#management-characters .entity-select").first.click()
                character = page.locator("#inspector-content").inner_text()
                assert "Character · Engineer" in character and "Assignment" in character
                assert "Relationships are not recorded" in character
                page.screenshot(path=str(out / "character-inspector.png"))
                page.locator("#command-inspector [data-inspector-close]").click()
                # Compare the same map and Economy surfaces at reference-size and ordinary desktop viewports.
                page.evaluate("window.HWDesktop.returnMap()")
                page.set_viewport_size({"width": 656, "height": 518})
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
                page.screenshot(path=str(out / "map-656x518.png"))
                page.evaluate("window.HWDesktop.open('economy')")
                page.wait_for_function("!document.querySelector('#command-workspace').hidden && document.querySelector('#command-workspace .workspace-title').textContent==='Economy' && !!document.querySelector('#economy-panel .local-scope:not([hidden])')")
                page.screenshot(path=str(out / "economy-656x518.png"))
                page.set_viewport_size({"width": 1280, "height": 900})
                page.screenshot(path=str(out / "economy-1280x900.png"))
                page.evaluate("window.HWDesktop.returnMap()")
                page.set_viewport_size({"width": 390, "height": 844})
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
                assert page.locator("#planet-map").evaluate("el=>el.isConnected")
                assert page.locator(".map-frame").bounding_box()["width"] == 390
                page.screenshot(path=str(out / "mobile.png"))
                page.locator("#hw-command").tap()
                page.locator("#command-menu button[data-open=economy]").tap()
                page.wait_for_selector("#economy-panel .local-scope:not([hidden])")
                assert page.locator("#command-workspace").is_visible()
                page.screenshot(path=str(out / "mobile-economy.png"))
                page.locator("[data-workspace-inspect]").tap()
                assert page.locator("#command-inspector").is_visible()
                page.screenshot(path=str(out / "mobile-inspector.png"))
                page.locator("[data-inspector-close]").tap()
                page.locator("#zoom-out").tap()
                assert page.locator("#zoom-reset").inner_text() == "100%"
                # Cold path and repeated warm navigation counts remain bounded.
                page.set_viewport_size({"width": 1280, "height": 900})
                cdp = page.context.new_cdp_session(page)
                cdp.send("HeapProfiler.collectGarbage")
                before_memory = cdp.send("Memory.getDOMCounters")
                before_dom = page.evaluate("document.querySelectorAll('*').length")
                before_requests = page.evaluate("performance.getEntriesByType('resource').filter(x=>x.name.includes('/api/')).length")
                page.evaluate("window.__strategicMapNode=document.querySelector('#planet-map')")
                cycle_times=[]
                for view in ["economy", "construction", "planet"] * 8:
                    started=time.perf_counter()
                    page.evaluate("view=>window.HWDesktop.open(view)", view)
                    if view=="planet":page.wait_for_function("document.querySelector('#command-workspace').hidden")
                    else:page.wait_for_function("view=>!document.querySelector('#command-workspace').hidden && document.querySelector('#command-workspace .workspace-title').textContent.toLowerCase()===view",arg=view)
                    cycle_times.append((time.perf_counter()-started)*1000)
                cdp.send("HeapProfiler.collectGarbage")
                after_memory = cdp.send("Memory.getDOMCounters")
                assert after_memory["jsEventListeners"] <= before_memory["jsEventListeners"], (before_memory, after_memory)
                after_dom = page.evaluate("document.querySelectorAll('*').length")
                after_requests = page.evaluate("performance.getEntriesByType('resource').filter(x=>x.name.includes('/api/')).length")
                assert page.evaluate("window.__strategicMapNode===document.querySelector('#planet-map')")
                assert after_dom-before_dom <= 8, (before_dom,after_dom)
                assert after_requests-before_requests <= 1, (before_requests,after_requests)
                page.evaluate("window.HWDesktop.open('campaign')")
                page.locator("#logout-button").click()
                page.fill("#access-token", gm)
                page.locator("#login-button").click()
                page.wait_for_function("document.querySelectorAll('#campaign-select option').length === 4")
                page.select_option("#campaign-select", "demo-v2")
                page.wait_for_function("document.querySelector('#command-turn').textContent === 'TURN 0'")
                held = []
                page.route("**/api/player/campaigns/demo-v2", lambda route: held.append(route))
                page.select_option("#campaign-select", "demo-v2")
                page.wait_for_timeout(50)
                page.select_option("#campaign-select", "campaign")
                page.wait_for_function("document.querySelector('#campaign-kind').textContent.includes('PRE-GAME')")
                page.select_option("#campaign-select", "demo-v2")
                page.wait_for_timeout(50)
                assert len(held) == 2
                held[1].continue_()
                page.wait_for_function("document.querySelector('#command-turn').textContent==='TURN 0'")
                held[0].fulfill(status=500, body="stale strategic response")
                page.unroute("**/api/player/campaigns/demo-v2")
                page.wait_for_load_state("networkidle")
                assert "stale strategic response" not in page.locator("body").inner_text()
                assert page.locator("#campaign-select").input_value() == "demo-v2"
                page.evaluate("window.HWDesktop.open('orders')")
                page.get_by_role("button",name="Load example proposal").click()
                page.wait_for_function("document.querySelector('#proposal-json').value.length > 50")
                proposal=json.loads(page.locator("#proposal-json").input_value())
                proposal["submission_id"]="strategic-browser-turn"
                proposal["orders"]={"allocations":[
                    {"settlement_id":"demo-v2-forge",**{key:0 for key in ALLOCATIONS},"farmers":300,"miners":20,"technicians":32,"refiners":10,"drillers":10,"machinists":5,"scientists":5,"builders":5},
                    {"settlement_id":"demo-v2-outpost",**{key:0 for key in ALLOCATIONS},"farmers":100}],"actions":[]}
                page.fill("#proposal-json",json.dumps(proposal))
                page.click("#preview-order")
                page.wait_for_function("document.querySelector('#command-preview').hidden===false && !document.querySelector('#commit-order').disabled")
                page.evaluate("window.HWDesktop.open('history'); window.HWDesktop.open('orders')")
                assert page.locator("#proposal-json").input_value()==json.dumps(proposal)
                page.click("#commit-order")
                page.wait_for_function("document.querySelector('#command-turn').textContent === 'TURN 1' && document.querySelector('#command-preview').hidden")
                page.evaluate("window.HWDesktop.open('history')")
                page.wait_for_function("document.querySelectorAll('#history-panel tbody tr').length===2")
                page.select_option("#history-compare-from","0")
                page.select_option("#history-compare-to","1")
                page.screenshot(path=str(out / "history.png"))
                page.get_by_role("button",name="Inspect turn 0",exact=True).click()
                page.wait_for_function("document.querySelector('#historical-badge').hidden===false")
                page.evaluate("window.HWDesktop.open('history')")
                assert page.get_by_role("button",name="Return to live",exact=True).is_visible()
                page.get_by_role("button",name="Return to live",exact=True).click()
                page.wait_for_function("document.querySelector('#historical-badge').hidden && document.querySelector('#command-turn').textContent==='TURN 1'")
                page.on("dialog",lambda dialog:dialog.accept("strategic-branch-turn0") if dialog.type=="prompt" else dialog.accept())
                branch_maps = []
                page.route("**/api/player/campaigns/strategic-branch-turn0/map?*", lambda route: branch_maps.append(route))
                page.get_by_role("button",name="Restore turn 0 into a new branch",exact=True).click()
                page.wait_for_function("document.querySelector('#campaign-select').value==='strategic-branch-turn0' && document.querySelector('#command-turn').textContent==='TURN 0'")
                page.evaluate("window.HWDesktop.open('campaign')")
                page.wait_for_function("!document.querySelector('#command-dialog').hidden")
                page.wait_for_timeout(50)
                assert branch_maps
                for route in branch_maps:
                    route.continue_()
                page.unroute("**/api/player/campaigns/strategic-branch-turn0/map?*")
                page.wait_for_load_state("networkidle")
                assert page.locator("#command-dialog").is_visible(), "Restore completion closed a newly opened access dialog"
                page.locator("#logout-button").click()
                delayed_login = []
                page.route("**/api/player/campaigns", lambda route: delayed_login.append(route))
                page.fill("#access-token", player)
                page.click("#login-button")
                page.wait_for_timeout(50)
                assert delayed_login
                page.click("#logout-button")
                delayed_login[0].continue_()
                page.unroute("**/api/player/campaigns")
                page.wait_for_load_state("networkidle")
                assert page.locator("#campaign-select option").count() == 1
                assert page.locator("#command-turn").inner_text() == "TURN —"
                assert page.locator("#access-token").input_value()==""
                assert set(page.evaluate("Object.keys(localStorage)")) <= {"hw.command.edge.v1"}
                assert not errors, errors
                ordered=sorted(cycle_times)
                timings["warm_cycle_p50_ms"]=statistics.median(ordered)
                timings["warm_cycle_p95_ms"]=ordered[round(.95*(len(ordered)-1))]
                metrics={"viewport":"1280x900, 656x518, 390x844","fixture":"isolated demo-v2 PostgreSQL","timings":timings,"warm_cycles":len(cycle_times),"dom_nodes_before":before_dom,"dom_nodes_after":after_dom,"api_resources_before":before_requests,"api_resources_after":after_requests,"canvas_identity":"retained", "camera_overlay_selection":"pixels and controls retained", "cdp_before":before_memory, "cdp_after":after_memory,"page_errors":errors}
                assert not errors, errors
                (out/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
                browser.close()
        print(json.dumps(metrics))
    finally:
        if server:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
        with psycopg.connect(dsn, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))


if __name__ == "__main__":
    main()
