"""Chromium regression for the map-first desktop shell and private context changes."""
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


def main():
    dsn = os.environ["WOLD_TEST_DATABASE_URL"]
    schema = "browser_desktop_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    server = None
    try:
        (Path(__file__).resolve().parents[1] / "data/previews").mkdir(parents=True, exist_ok=True)
        db = Store(dsn, schema=schema)
        db.create_demo_v2()
        db.create_demo()
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
            for _ in range(100):
                try:
                    if httpx.get(base + "/api/access").status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                time.sleep(.1)
            else:
                raise RuntimeError("Desktop browser test server failed to start")
            with sync_playwright() as playwright:
                executable = os.environ.get("WOLD_CHROMIUM_EXECUTABLE") or shutil.which("chromium")
                browser = playwright.chromium.launch(executable_path=executable, headless=True,
                                                       args=["--no-sandbox", "--disable-dev-shm-usage"])
                page = browser.new_page(viewport={"width": 1440, "height": 960}, device_scale_factor=1,
                                        has_touch=True, is_mobile=True)
                page.set_default_timeout(10000)
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base)
                page.wait_for_selector("#campaign-select option", state="attached")
                assert page.locator("#campaign-select").input_value() == ""
                assert page.locator("#campaign-select option").count() == 1, "No campaign is silently selected before login"
                assert page.locator("#desktop-windows .desk-window").count() == 8
                page.fill("#access-token", player)
                page.click("#login-button")
                page.wait_for_function("document.querySelector('#campaign-select option').value === '' && document.querySelectorAll('#campaign-select option').length === 4")
                assert page.locator("#campaign-select").input_value() == ""
                page.select_option("#campaign-select", "demo-v2")
                page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 0' && document.querySelector('#map-placeholder').hidden")
                assert page.locator('[data-window="campaign"]').is_hidden(), "Campaign selection closes only after a successful explicit choice"
                page.evaluate("document.querySelector('.toast')?.remove()")
                page.screenshot(path="data/previews/chromium-desktop-map.png")
                page.mouse.move(2, 500)
                page.wait_for_selector("#desktop-launcher:not([hidden])", timeout=2000)
                page.mouse.move(500, 500)
                page.wait_for_selector("#desktop-launcher", state="hidden", timeout=2500)
                # Escape and Clear cancel an edge reveal even before it becomes visible.
                page.mouse.move(2, 500)
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
                assert page.locator("#desktop-launcher").is_hidden()
                page.mouse.move(500, 500)
                page.mouse.move(2, 500)
                page.evaluate("window.HWDesktop.clear()")
                page.wait_for_timeout(300)
                assert page.locator("#desktop-launcher").is_hidden()
                page.click("#hw-command")
                assert page.locator("#launcher-commands .nav-item").first.evaluate("el=>getComputedStyle(el).fontSize") != "0px"
                assert page.locator("#launcher-commands .nav-item .nav-icon").first.evaluate("el=>getComputedStyle(el).position") == "static"
                page.wait_for_selector("#desktop-launcher:not([hidden])")
                page.screenshot(path="data/previews/chromium-desktop-launcher.png")
                page.click("#launcher-pin")
                assert page.evaluate("localStorage.getItem('hw.desktop.pinned')") == "true"
                page.click("#launcher-commands [data-view=planet]")
                page.wait_for_selector('[data-window="planet"]:not([hidden])')
                page.click("#hw-command")
                page.click("#launcher-commands [data-view=planet]")
                # The four map levels remain real API views behind a permanently mounted canvas.
                for level in ("galactic", "sector", "system", "planet"):
                    with page.expect_response(lambda response: "/map?" in response.url and f"level={level}" in response.url and response.status == 200):
                        page.select_option("#map-level", level)
                    assert page.locator("#planet-map").evaluate("el=>el.isConnected")
                map_window = page.locator('[data-window="planet"]')
                before = map_window.bounding_box()
                page.mouse.move(before["x"] + 120, before["y"] + 12)
                page.mouse.down()
                page.mouse.move(before["x"] + 155, before["y"] + 42, steps=4)
                page.mouse.up()
                after_drag = map_window.bounding_box()
                assert after_drag["x"] > before["x"] + 20 and after_drag["y"] > before["y"] + 15
                page.mouse.move(after_drag["x"] + after_drag["width"] - 5, after_drag["y"] + after_drag["height"] - 5)
                page.mouse.down()
                page.mouse.move(after_drag["x"] + after_drag["width"] + 35, after_drag["y"] + after_drag["height"] + 25, steps=4)
                page.mouse.up()
                resized = map_window.bounding_box()
                assert resized["width"] > after_drag["width"] + 20 and resized["height"] > after_drag["height"] + 15
                # Window gestures also suppress edge reveal, including a queued reveal.
                for handle in (map_window.locator(".desk-titlebar"), map_window.locator(".desk-resize-grip")):
                    box = handle.bounding_box()
                    start_x, start_y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                    page.mouse.move(2, 500)
                    page.mouse.move(start_x, start_y)
                    page.mouse.down()
                    page.mouse.move(2, start_y, steps=3)
                    page.wait_for_timeout(300)
                    assert page.locator("#desktop-launcher").is_hidden()
                    page.mouse.move(start_x, start_y, steps=3)
                    page.mouse.up()
                max_button = map_window.locator(".desk-controls button").nth(1)
                max_button.click()
                assert map_window.bounding_box()["width"] > 1300
                max_button.click()
                assert map_window.bounding_box()["width"] < 800
                with page.expect_response(lambda response: "/map?" in response.url and "overlay=population" in response.url and response.status == 200):
                    page.select_option("#overlay-select", "population")
                page.click("#zoom-in")
                map_context = page.locator("#map-level").input_value()
                # Map panning suppresses the nearby edge trigger during the active gesture.
                page.mouse.move(20, 500)
                page.mouse.down()
                page.mouse.move(2, 510, steps=3)
                page.wait_for_timeout(300)
                assert page.locator("#desktop-launcher").is_hidden()
                page.mouse.up()
                map_pixels = page.locator("#planet-map").evaluate("el=>el.toDataURL()")
                page.click("#hw-command")
                page.click("#launcher-commands [data-view=economy]")
                page.wait_for_selector('[data-window="economy"] .economy-box')
                page.click("#hw-command")
                page.click("#launcher-commands [data-view=history]")
                page.wait_for_selector('[data-window="history"] #history-metric')
                assert page.locator('[data-window="economy"]').is_visible()
                assert page.locator('[data-window="history"]').is_visible()
                page.screenshot(path="data/previews/chromium-desktop-multiple-windows.png")
                # Minimize/restore and clear preserve the live map context and object identity.
                page.evaluate("window.HWDesktop.open('economy')")
                page.locator('[data-window="economy"] .desk-controls button').first.click()
                assert page.locator('[data-window="economy"]').is_hidden()
                page.click("#hw-command")
                page.locator("#desktop-minimized button").filter(has_text="Economy ledger").click()
                assert page.locator('[data-window="economy"]').is_visible()
                level_before = page.locator("#map-level").input_value()
                page.click("#launcher-clear")
                assert page.locator('[data-window="economy"]').is_hidden()
                assert page.locator("#planet-map").evaluate("el=>el.isConnected")
                assert page.locator("#planet-map").evaluate("el=>el.toDataURL()") == map_pixels
                page.click("#hw-command")
                page.click("#launcher-commands [data-view=planet]")
                assert page.locator("#map-level").input_value() == map_context == level_before
                # A real province selection opens the existing contextual inspector.
                page.click("#zoom-reset")
                geometry = db.map_view("demo-v2", "planet", "demo-v2-planet-reach")["geometry"]
                settlement = db.player_state(db.current("demo-v2")["snapshot"])["settlements"][0]
                tile_record = next(t for t in geometry["tiles"] if t["province_id"] == settlement["province_id"])
                box = page.locator("#planet-map").bounding_box()
                tile = min(box["width"] / 64, box["height"] / 40)
                x = box["x"] + (box["width"] - 64 * tile) / 2 + (tile_record["x"] + .5) * tile
                y = box["y"] + (box["height"] - 40 * tile) / 2 + (tile_record["y"] + .5) * tile
                page.evaluate("window.HWDesktop.clear()")
                page.mouse.click(x, y)
                page.wait_for_selector('[data-window="inspector"]:not([hidden])')
                assert "Province ID" in page.locator("#inspector-content").inner_text()
                page.screenshot(path="data/previews/chromium-desktop-inspector.png")
                # Utility windows remain reachable from the launcher after Clear.
                page.evaluate("window.HWDesktop.clear()")
                page.click("#hw-command")
                for utility in ("turn", "log", "inspector"):
                    page.locator(f'#launcher-commands [data-window-open="{utility}"]').click()
                    assert page.locator(f'[data-window="{utility}"]').is_visible()
                    page.evaluate("window.HWDesktop.clear()")
                    page.click("#hw-command")
                page.evaluate("window.HWDesktop.open('orders')")
                page.get_by_label("PROPOSAL JSON").fill("unsaved desktop draft")
                page.evaluate("window.HWDesktop.open('industry'); window.HWDesktop.open('fleet')")
                page.wait_for_selector('[data-window="industry"] .metadata-grid')
                page.wait_for_selector('[data-window="fleet"] .metadata-grid')
                assert page.locator('[data-window="orders"] #proposal-json').input_value() == "unsaved desktop draft"
                # Every real management screen gets its own retained window and view-specific records.
                management_views = ("industry", "fleet", "politics", "trade", "factions", "budget", "logistics",
                                   "construction", "research", "military", "diplomacy", "intelligence",
                                   "exploration", "colonies", "characters")
                opened_management = []
                for view in management_views:
                    page.evaluate("view=>window.HWDesktop.open(view)", view)
                    page.wait_for_selector(f'[data-window="{view}"] .metadata-grid')
                    opened_management.append(page.locator(f'[data-window="{view}"]').get_attribute("data-window"))
                    if view == "industry":
                        entity = page.locator('[data-window="industry"] .entity-select').first
                        assert entity.count(), "Industry records expose a selectable entity"
                        entity.evaluate("el=>el.click()")
                        assert page.locator('[data-window="inspector"]').is_visible()
                        assert "RECORDED ENTITY" in page.locator("#inspector-content").inner_text()
                        page.evaluate("window.HWDesktop.close('inspector')")
                    page.evaluate("view=>window.HWDesktop.close(view)", view)
                assert len(set(opened_management)) == 15
                page.evaluate("window.HWDesktop.clear(); window.HWDesktop.open('orders')")
                assert page.locator('[data-window="orders"] #proposal-json').input_value() == "unsaved desktop draft"
                # Switching A→B→A cannot let a held first A response win over the latest context.
                held = []
                def hold_demo(route):
                    held.append(route)
                page.route("**/api/player/campaigns/demo-v2", hold_demo)
                page.evaluate("window.HWDesktop.open('campaign')")
                page.select_option("#campaign-select", "demo-v2")
                page.wait_for_function("document.querySelector('#campaign-kind').textContent === 'NO CAMPAIGN'")
                page.select_option("#campaign-select", "campaign")
                page.wait_for_function("document.querySelector('#campaign-select').value === 'campaign'")
                page.wait_for_function("document.querySelector('[data-window=campaign]').hidden")
                page.evaluate("window.HWDesktop.open('campaign')")
                page.select_option("#campaign-select", "demo-v2")
                page.wait_for_function("window.location.href.length > 0")
                for _ in range(60):
                    if len(held) >= 2:
                        break
                    time.sleep(.05)
                assert len(held) >= 2
                held[1].continue_()
                page.wait_for_function("document.querySelector('#campaign-kind').textContent === 'FICTIONAL DEMO'")
                held[0].fulfill(status=500, body="stale failure")
                page.unroute("**/api/player/campaigns/demo-v2", hold_demo)
                assert page.locator("#campaign-select").input_value() == "demo-v2"
                assert "stale failure" not in page.locator("body").inner_text()
                # Logout invalidates a login request that is still in flight.
                page.wait_for_function("document.querySelector('[data-window=campaign]').hidden")
                page.evaluate("window.HWDesktop.open('campaign')")
                page.wait_for_function("document.querySelector('[data-window=campaign]').hidden === false")
                assert page.locator("#logout-button").is_visible()
                page.click("#logout-button")
                delayed = []
                def hold_campaigns(route):
                    delayed.append(route)
                page.route("**/api/player/campaigns", hold_campaigns)
                page.fill("#access-token", player)
                page.click("#login-button")
                page.wait_for_function("document.querySelector('#campaign-kind').textContent === 'NO CAMPAIGN'")
                for _ in range(60):
                    if delayed:
                        break
                    time.sleep(.05)
                assert delayed
                page.click("#logout-button")
                delayed[0].continue_()
                page.unroute("**/api/player/campaigns", hold_campaigns)
                time.sleep(.15)
                assert page.locator("#campaign-select").input_value() == ""
                assert page.locator("#access-token").input_value() == ""
                assert set(page.evaluate("Object.keys(localStorage)")) <= {"hw.desktop.geometry", "hw.desktop.pinned"}
                assert page.evaluate("Object.keys(sessionStorage).length") == 0
                # GM turn preview, commit and history remain functional in retained windows.
                page.fill("#access-token", gm)
                page.click("#login-button")
                page.wait_for_function("document.querySelectorAll('#campaign-select option').length === 4")
                page.select_option("#campaign-select", "demo-v2")
                page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 0'")
                page.evaluate("window.HWDesktop.open('orders')")
                page.get_by_role("button", name="Load example proposal").click()
                page.wait_for_function("document.querySelector('#proposal-json').value.length > 50")
                proposal = json.loads(page.locator("#proposal-json").input_value())
                proposal["submission_id"] = "desktop-shell-turn"
                proposal["orders"] = {"allocations": [
                    {"settlement_id": "demo-v2-forge", **{key: 0 for key in ALLOCATIONS}, "farmers": 300, "miners": 20,
                     "technicians": 32, "refiners": 10, "drillers": 10, "machinists": 5, "scientists": 5, "builders": 5},
                    {"settlement_id": "demo-v2-outpost", **{key: 0 for key in ALLOCATIONS}, "farmers": 100}], "actions": []}
                page.fill("#proposal-json", json.dumps(proposal))
                page.click("#preview-order")
                page.wait_for_function("!document.querySelector('#commit-order').disabled")
                page.click("#commit-order")
                page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 1'")
                page.evaluate("window.HWDesktop.open('history')")
                page.wait_for_selector('[data-window="history"] #history-metric')
                page.wait_for_function("document.querySelectorAll('[data-window=history] tbody tr').length === 2")
                assert page.locator('[data-window="history"] tbody tr').count() == 2
                assert page.get_by_label("Inspect turn 1", exact=True).count() == 1
                page.select_option("#history-compare-from", "0")
                page.select_option("#history-compare-to", "1")
                page.evaluate("window.HWDesktop.open('economy')")
                page.wait_for_selector('[data-window="economy"] .chart-box svg polyline[points]', state="attached")
                page.wait_for_selector('[data-window="history"] #history-chart svg polyline[points]', state="attached")
                # Focusing either window cannot change the source or cancel the other's chart.
                assert page.locator('[data-window="economy"]').evaluate("el=>el.classList.contains('desk-active')")
                assert not page.locator('[data-window="history"]').evaluate("el=>el.classList.contains('desk-active')")
                page.evaluate("window.HWDesktop.open('history')")
                assert page.locator('[data-window="history"]').evaluate("el=>el.classList.contains('desk-active')")
                page.locator('[data-window="economy"] .desk-titlebar').click(position={"x": 30, "y": 12}, force=True)
                assert page.locator('[data-window="economy"]').evaluate("el=>el.classList.contains('desk-active')")
                assert not page.locator('[data-window="history"]').evaluate("el=>el.classList.contains('desk-active')")
                assert page.locator('[data-window="history"] #history-compare-from').input_value() == "0"
                assert page.locator('[data-window="history"] #history-compare-to').input_value() == "1"
                page.evaluate("window.HWDesktop.open('history')")
                page.get_by_label("Inspect turn 0", exact=True).click()
                page.wait_for_function("document.querySelector('#historical-badge').hidden === false")
                assert page.locator('[data-window="history"] #history-compare-from').input_value() == "0"
                assert page.get_by_role("button", name="Return to live").is_visible()
                assert page.locator('[data-window="history"] tbody tr').count() == 2
                page.get_by_role("button", name="Return to live").click()
                page.wait_for_function("document.querySelector('#historical-badge').hidden === true && document.querySelector('#turn-badge').textContent === 'TURN 1'")
                page.on("dialog", lambda dialog: dialog.accept("browser-desktop-branch") if dialog.type == "prompt" else dialog.accept())
                page.get_by_label("Restore turn 0 into a new branch", exact=True).click()
                page.wait_for_function("document.querySelector('#campaign-select').value === 'browser-desktop-branch' && document.querySelector('#turn-badge').textContent === 'TURN 0'")
                page.set_viewport_size({"width": 390, "height": 844})
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
                for item in page.locator("#desktop-windows .desk-window:not([hidden])").all():
                    r = item.bounding_box()
                    assert r and r["x"] >= 0 and r["y"] >= 0 and r["x"] + r["width"] <= 390 and r["y"] + r["height"] <= 844
                page.click("#hw-command")
                page.click("#launcher-pin")
                assert page.evaluate("localStorage.getItem('hw.desktop.pinned')") == "false"
                page.click("#hw-command")
                page.touchscreen.tap(20, 20)
                page.wait_for_selector("#desktop-launcher:not([hidden])")
                page.wait_for_timeout(700)
                assert page.locator("#desktop-launcher").is_visible(), "Touch-open launcher remains available after edge timers expire"
                assert page.locator('#launcher-commands [data-view="economy"]').evaluate("el=>getComputedStyle(el).fontSize") != "0px"
                page.screenshot(path="data/previews/chromium-desktop-mobile.png")
                economy_command = page.locator('#launcher-commands [data-view="economy"]').bounding_box()
                page.touchscreen.tap(economy_command["x"] + economy_command["width"] / 2,
                                     economy_command["y"] + economy_command["height"] / 2)
                page.wait_for_selector('[data-window="economy"]:not([hidden])')
                page.reload()
                page.wait_for_selector("#login-button", state="visible")
                assert page.locator("#campaign-select").input_value() == ""
                assert page.locator("#access-token").input_value() == ""
                assert not errors, errors
                print(json.dumps({"browser": "chromium", "desktop_shell": "PASS", "map_levels": 4,
                                  "turn_history": "PASS", "auth_context": "PASS", "page_errors": errors}))
                browser.close()
    finally:
        if server is not None:
            server.terminate()
            server.wait(timeout=10)
        with psycopg.connect(dsn, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


if __name__ == "__main__":
    main()
