"""Full private-dashboard workflow in Chromium or WebKit; isolated PostgreSQL."""
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
import psycopg
from psycopg import sql
from playwright.sync_api import sync_playwright
from app.engine_v2 import ALLOCATIONS
from app.store import Store


def main(kind="chromium"):
    dsn = os.environ["WOLD_TEST_DATABASE_URL"]
    schema = "browser_v2_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    server = None
    try:
        db = Store(dsn, schema=schema)
        initial = db.create_demo_v2()
        db.create_demo()
        db.create_demo("restricted")
        db.create_pregame()
        gm, player = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        environment = os.environ.copy()
        environment.update(WOLD_DATABASE_URL=dsn, WOLD_DB_SCHEMA=schema, WOLD_ACCESS_MODE="private",
                           WOLD_GM_TOKEN=gm, WOLD_PLAYER_TOKEN=player, WOLD_PLAYER_CAMPAIGNS="demo-v2,demo,campaign")
        with socket.socket() as connection:
            connection.bind(("127.0.0.1", 0))
            port = connection.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        with tempfile.TemporaryDirectory() as scratch, open(Path(scratch) / "server.log", "w") as log:
            server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                                       "--port", str(port), "--no-access-log"], env=environment, stdout=log, stderr=log)
            for _ in range(80):
                try:
                    if httpx.get(base + "/api/access").status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                time.sleep(.1)
            else:
                raise RuntimeError("Private browser test server failed to start")
            with sync_playwright() as playwright:
                if kind == "webkit":
                    browser = playwright.webkit.launch(headless=True)
                else:
                    executable = os.environ.get("WOLD_CHROMIUM_EXECUTABLE") or shutil.which("chromium")
                    browser = playwright.chromium.launch(executable_path=executable, headless=True,
                                                         args=["--no-sandbox", "--disable-dev-shm-usage"])
                page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
                page.set_default_timeout(10000)
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base)
                page.wait_for_selector("#login-button", state="visible")
                assert page.locator("#campaign-select option").count() == 0
                page.fill("#access-token", player)
                page.click("#login-button")
                page.wait_for_function("document.querySelector('#campaign-select').value === 'demo-v2'")
                page.wait_for_function("document.querySelector('#map-placeholder').hidden")
                values = page.locator("#campaign-select option").evaluate_all("els=>els.map(x=>x.value)")
                assert set(values) == {"demo", "demo-v2", "campaign"}
                assert page.evaluate("Object.keys(localStorage).length+Object.keys(sessionStorage).length") == 0
                assert page.locator(".desktop").evaluate("el=>getComputedStyle(el).backgroundColor") == "rgb(192, 192, 192)"
                assert page.locator(".titlebar").evaluate("el=>getComputedStyle(el).backgroundColor") == "rgb(0, 0, 128)"
                previews = Path(__file__).resolve().parents[1] / "data/previews"
                previews.mkdir(parents=True, exist_ok=True)
                contexts = {"sector": "demo-v2-sector-hearth", "system": "demo-v2-system-hearth", "planet": "demo-v2-planet-reach"}
                for level in ("galactic", "sector", "system", "planet"):
                    with page.expect_response(lambda r: "/map?" in r.url and f"level={level}" in r.url and r.status == 200):
                        page.select_option("#map-level", level)
                    page.wait_for_function("document.querySelector('#map-placeholder').hidden")
                    page.evaluate("()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
                    page.screenshot(path=str(previews / f"{kind}-{level}.png"), full_page=True)
                page.click("#zoom-in")
                assert page.locator("#zoom-reset").inner_text() == "120%"
                page.click("#zoom-reset")
                overlay_images = set()
                for overlay in ("population", "infrastructure", "military", "politics", "terrain"):
                    with page.expect_response(lambda r: "/map?" in r.url and f"overlay={overlay}" in r.url and r.status == 200):
                        page.select_option("#overlay-select", overlay)
                    page.wait_for_function("document.querySelector('#map-legend').textContent.length > 0")
                    page.evaluate("()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
                    overlay_images.add(page.locator("#planet-map").evaluate("el=>el.toDataURL()"))
                assert len(overlay_images) == 5, "Recorded overlays must change map rendering"
                geometry = db.map_view("demo-v2", "planet", contexts["planet"])["geometry"]
                settlement = db.player_state(db.current("demo-v2")["snapshot"])["settlements"][0]
                tile_record = next(t for t in geometry["tiles"] if t["province_id"] == settlement["province_id"])
                box = page.locator("#planet-map").bounding_box()
                tile = min(box["width"] / 64, box["height"] / 40)
                x = box["x"] + (box["width"] - 64 * tile) / 2 + (tile_record["x"] + .5) * tile
                y = box["y"] + (box["height"] - 40 * tile) / 2 + (tile_record["y"] + .5) * tile
                page.mouse.move(x, y)
                assert page.locator("#map-tooltip").is_visible()
                page.mouse.click(x, y)
                assert "Province ID" in page.locator("#inspector-content").inner_text()
                # Every management report must resolve from actual saved records.
                views = ("industry", "fleet", "politics", "trade", "factions", "budget", "logistics", "construction",
                         "research", "military", "diplomacy", "intelligence", "exploration", "colonies", "characters")
                for view in views:
                    page.click(f'.nav-item[data-view="{view}"]')
                    page.wait_for_function("document.querySelector('#management-panel').querySelector('.metadata-grid') !== null")
                    assert "unavailable:" not in page.locator("#management-panel").inner_text().lower()
                page.click('.nav-item[data-view="fleet"]')
                page.wait_for_selector("#management-panel tbody tr")
                page.locator("#management-panel tbody tr").first.click()
                assert "transport" in page.locator("#inspector-content").inner_text().lower()
                page.click('.nav-item[data-view="economy"]')
                page.wait_for_selector("#economy-panel .economy-box")
                assert "8,000" in page.locator("#economy-panel").inner_text()
                page.click("#logout-button")
                assert page.locator("#campaign-select option").count() == 0
                page.fill("#access-token", gm)
                page.click("#login-button")
                page.wait_for_function("document.querySelector('#campaign-select').value === 'demo-v2'")
                page.click('.nav-item[data-view="orders"]')
                page.get_by_role("button", name="Load example proposal").click()
                page.wait_for_function("document.querySelector('#proposal-json').value.length > 50")
                proposal = json.loads(page.locator("#proposal-json").input_value())
                proposal["submission_id"] = "browser-verified-turn"
                proposal["orders"] = {"allocations": [
                    {"settlement_id": "demo-v2-forge", **{k: 0 for k in ALLOCATIONS}, "farmers": 300, "miners": 20,
                     "technicians": 32, "refiners": 10, "drillers": 10, "machinists": 5, "scientists": 5, "builders": 5},
                    {"settlement_id": "demo-v2-outpost", **{k: 0 for k in ALLOCATIONS}, "farmers": 100}],
                    "actions": [{"type": "build", "settlement_id": "demo-v2-forge", "facility_kind": "farm"},
                                {"type": "recruit", "settlement_id": "demo-v2-forge"}]}
                proposal["narrative"] = "Verified fictional browser turn."
                page.fill("#proposal-json", json.dumps(proposal))
                page.click("#preview-order")
                page.wait_for_function("!document.querySelector('#commit-order').disabled")
                assert db.current("demo-v2")["snapshot"]["turn"] == 0
                page.click("#commit-order")
                page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 1'")
                page.click('.nav-item[data-view="history"]')
                page.wait_for_selector("#history-metric")
                for metric in ("population", "food", "ore", "energy", "treasury", "military", "projects", "research"):
                    page.select_option("#history-metric", metric)
                    page.wait_for_function("document.querySelector('#history-chart svg') !== null")
                page.select_option("#history-metric", "treasury")
                page.select_option("#history-compare-from", "0")
                page.select_option("#history-compare-to", "1")
                page.wait_for_function("document.querySelector('#history-chart').textContent.includes('Turn 1 vs 0')")
                page.get_by_label("Inspect turn 0", exact=True).click()
                page.wait_for_function("document.querySelector('#historical-badge').hidden === false")
                assert page.locator("#turn-badge").inner_text() == "TURN 0"
                page.click('.nav-item[data-view="orders"]')
                assert "Return to the live" in page.locator("#orders-panel").inner_text()
                # A history response must not replace an enabled control mid-click.
                held_history = []
                history_route = "**/history?offset=0&limit=50"
                def hold_history(route):
                    held_history.append(route)
                page.route(history_route, hold_history)
                page.click('.nav-item[data-view="history"]')
                page.wait_for_function("document.querySelector('#history-panel').getAttribute('aria-busy') === 'true'")
                assert page.get_by_role("button", name="Return to live").is_disabled()
                assert held_history
                held_history[0].continue_()
                page.unroute(history_route, hold_history)
                page.wait_for_function("document.querySelector('#history-panel').getAttribute('aria-busy') === 'false'")
                page.get_by_role("button", name="Return to live").click()
                page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 1'")
                page.on("dialog", lambda dialog: dialog.accept("qa-v2-branch") if dialog.type == "prompt" else dialog.accept())
                page.get_by_label("Restore turn 0 into a new branch", exact=True).click()
                page.wait_for_function("document.querySelector('#campaign-select').value === 'qa-v2-branch'")
                assert db.current("demo-v2")["snapshot"]["turn"] == 1
                page.select_option("#campaign-select", "campaign")
                page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN —'")
                assert "UNKNOWN" in page.locator("#resource-strip").inner_text()
                page.click('.nav-item[data-view="planet"]')
                assert page.locator("#map-placeholder").is_visible()
                page.select_option("#campaign-select", "demo-v2")
                page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 1'")
                page.select_option("#map-level", "planet")
                page.wait_for_function("document.querySelector('#map-placeholder').hidden")
                page.evaluate("document.querySelector('.toast')?.remove()")
                page.screenshot(path=str(previews / f"{kind}-desktop-turn1.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                assert page.locator(".nav-item .nav-icon").count() == page.locator(".nav-item").count()
                assert page.locator(".nav-item").evaluate_all("els=>els.every(el=>el.getAttribute('aria-label')&&el.title)")
                assert page.locator("#access-token").bounding_box()["width"] > 90
                assert page.locator(".resource-card").evaluate_all("els=>els.every(el=>el.scrollWidth<=el.clientWidth)")
                page.screenshot(path=str(previews / f"{kind}-mobile.png"), full_page=True)
                page.reload()
                page.wait_for_selector("#login-button", state="visible")
                assert page.locator("#campaign-select option").count() == 0
                assert page.locator("#access-token").input_value() == ""
                assert not errors, errors
                print(json.dumps({"browser": kind, "private_v2_workflow": "PASS", "map_levels": 4,
                                  "management_views": len(views), "metrics": 8, "page_errors": errors}))
                browser.close()
    finally:
        if server is not None:
            server.terminate()
            server.wait(timeout=10)
        with psycopg.connect(dsn, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "chromium")
