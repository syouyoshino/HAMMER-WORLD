"""Focused strategic command journey using an isolated PostgreSQL fixture."""
import os
import base64
import struct
import re
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


def click_map_marker(page, name, touch=False):
    """Find actual painted markers/cards, identify their normal hover labels, then click.

    Do not reproduce the projection math or expose private application state.
    """
    page.wait_for_load_state("networkidle")
    page.evaluate("()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
    for attempt in range(5):
        points = page.locator("#planet-map").evaluate("""canvas=>{
            const ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height;
            const data=ctx.getImageData(0,0,w,h).data,r=canvas.getBoundingClientRect();
            const colors=new Set(['98,106,108','133,141,141','92,100,102','168,174,172','181,187,186',
                '79,128,144','135,146,138','183,123,51','119,126,116','98,119,124',
                '164,134,80','119,115,110','208,208,201','113,128,138']);
            const color=i=>`${data[i*4]},${data[i*4+1]},${data[i*4+2]}`;
            const points=[],seen=new Uint8Array(w*h);
            // Connected painted regions work for circular bodies and legacy squares.
            for(let i=0;i<w*h;i++){
                if(seen[i])continue;seen[i]=1;const c=color(i);if(!colors.has(c))continue;
                const stack=[i];let minX=w,minY=h,maxX=0,maxY=0,count=0;
                while(stack.length){const at=stack.pop(),x=at%w,y=Math.floor(at/w);count++;
                    minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);
                    for(const n of [x?at-1:-1,x<w-1?at+1:-1,y?at-w:-1,y<h-1?at+w:-1])
                        if(n>=0&&!seen[n]&&color(n)===c){seen[n]=1;stack.push(n);}
                }
                if(count>=8&&maxX-minX>=2&&maxY-minY>=2)points.push({
                    x:r.left+(minX+maxX+1)/2*r.width/w,y:r.top+(minY+maxY+1)/2*r.height/h});
            }
            // Nonspatial destination cards have painted text rather than a body
            // marker. Group the actual bright glyph pixels into rendered rows.
            const rows=[];
            for(let y=0;y<h;y++){
                let left=w,right=-1;
                for(let x=0;x<w;x++)if(color(y*w+x)==='227,229,221'){
                    left=Math.min(left,x);right=Math.max(right,x);
                }
                if(right>=left){const previous=rows[rows.length-1];
                    if(previous&&y-previous.bottom<=2){previous.bottom=y;previous.left=Math.min(previous.left,left);previous.right=Math.max(previous.right,right);}
                    else rows.push({left,right,top:y,bottom:y});
                }
            }
            for(const row of rows)if(row.right-row.left>=8)points.push({
                x:r.left+(row.left+row.right+1)/2*r.width/w,
                y:r.top+(row.top+row.bottom+1)/2*r.height/h});
            return points;
        }""")
        for point in points:
            # A context redraw can hide the tooltip while the pointer remains at
            # this same position. Force an actual pointer entry before identifying.
            page.mouse.move(0, 0)
            page.mouse.move(point["x"], point["y"])
            tooltip = page.locator("#map-tooltip")
            if tooltip.is_visible() and tooltip.inner_text().startswith(name + " ·"):
                assert page.evaluate("p=>document.elementFromPoint(p.x,p.y)?.id==='planet-map'", point), name
                if touch:
                    page.touchscreen.tap(point["x"], point["y"])
                else:
                    page.mouse.click(point["x"], point["y"])
                return
        page.wait_for_timeout(80)
    raise AssertionError(f"No visible, pointer-reachable map marker for {name}: {points}")


def descend_hierarchy(page, names, touch=False):
    page.select_option("#map-level", "galactic")
    page.wait_for_function("document.querySelector('#map-coordinates').textContent.startsWith('GALACTIC CARTOGRAPHY')")
    for name, level in zip(names, ["sector", "system", "planet"]):
        click_map_marker(page, name, touch)
        page.wait_for_function("level=>document.querySelector('#map-coordinates').textContent.startsWith(level.toUpperCase()+' ')", arg=level)


def province_point(page, province):
    """Observe the real camera projection, including displaced holding labels.

    Test-only instrumentation avoids duplicating camera formulas or assuming a
    64x40 grid. A holding hidden beneath persistent chrome uses its visible label.
    """
    return page.evaluate("""p=>{
        if(!window.__provinceTestInstalled){
            const draw=window.HWMapRenderer.drawPlanet;
            window.HWMapRenderer.drawPlanet=function(ctx,options){
                const t=draw(ctx,options);window.__provinceTest={t,geometry:options.geometry};return t;
            };window.__provinceTestInstalled=true;
        }
        document.querySelector('#map-style').dispatchEvent(new Event('change'));
        const {t,geometry}=window.__provinceTest,f=document.querySelector('#planet-map').getBoundingClientRect();
        let x=t.ox+(p.x+p.width/2)*t.tile,y=t.oy+(p.y+p.height/2)*t.tile;
        const tile=geometry.tiles[Math.floor(p.y)*t.cols+Math.floor(p.x)];
        const label=t.provinceTargets.find(a=>a.provinceId===(p.id||tile?.province_id));
        const safe=t.safeRect||{left:0,right:f.width,top:0,bottom:f.height};
        if(label&&(x<safe.left||x>safe.right||y<safe.top||y>safe.bottom)){
            x=(label.left+label.right)/2;y=(label.top+label.bottom)/2;
        }
        return {x:f.left+x,y:f.top+y};
    }""", province)


def check_browser_zoom(playwright, executable, base, player, out):
    """Actual desktop tab zoom through Chrome Settings in a disposable profile."""
    results = []
    with tempfile.TemporaryDirectory() as profile:
        context = playwright.chromium.launch_persistent_context(
            profile, executable_path=executable, headless=True, no_viewport=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--window-size=1280,960"])
        page = context.pages[0]
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base)
        page.fill("#access-token", player)
        page.locator("#login-button").click()
        page.wait_for_function("document.querySelectorAll('#campaign-select option').length===2")
        page.locator("[data-dialog-close]").click()
        page.select_option("#campaign-select", "demo-v2")
        page.wait_for_function("document.querySelector('#map-placeholder').hidden")
        page.wait_for_selector(".toast", state="hidden", timeout=6000)
        settings = context.new_page()
        settings.goto("chrome://settings/appearance")
        settings.wait_for_function("typeof chrome.settingsPrivate?.setDefaultZoom==='function'")
        capture_session = context.new_cdp_session(page)
        for factor in [1, 1.25, 1.5, 2]:
            actual = settings.evaluate("""async factor=>{
                await new Promise(resolve=>chrome.settingsPrivate.setDefaultZoom(factor,resolve));
                return await new Promise(resolve=>chrome.settingsPrivate.getDefaultZoom(resolve));
            }""", factor)
            assert actual == factor
            page.bring_to_front()
            page.wait_for_function("factor=>Math.abs(devicePixelRatio-factor)<.01", arg=factor)
            assert page.evaluate("visualViewport.scale") == 1
            assert not page.evaluate("document.documentElement.scrollWidth>innerWidth")
            for selector in ["#hw-command", "#campaign-select", "#command-turn", "#zoom-in", "#zoom-out"]:
                assert page.locator(selector).is_visible(), (factor, selector)
                assert page.locator(selector).evaluate("el=>{const r=el.getBoundingClientRect();return r.x>=0&&r.y>=0&&r.right<=innerWidth&&r.bottom<=innerHeight;}")
            assert page.locator("#campaign-select").bounding_box()["width"] >= 100
            page.locator("#hw-command").click()
            page.locator("#command-menu button[data-open=economy]").click()
            page.wait_for_selector("#economy-panel:not([hidden])")
            page.locator("[data-return-map]").click()
            assert page.locator("#command-workspace").is_hidden()
            page.locator("#zoom-in").click()
            page.locator("#zoom-reset").click()
            descend_hierarchy(page, ["Hearth", "Cinder", "Reach"])
            # Playwright's implicit viewport clip crops browser-zoomed no_viewport pages.
            shot = capture_session.send("Page.captureScreenshot", {"format":"png", "fromSurface":True, "captureBeyondViewport":False})
            png = base64.b64decode(shot["data"])
            (out / f"browser-zoom-{round(factor*100)}.png").write_bytes(png)
            results.append({"zoom":actual, "viewport":page.evaluate("({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,visualScale:visualViewport.scale})"), "capture_pixels":list(struct.unpack(">II",png[16:24]))})
        assert not errors, errors
        context.close()
    return results


def check_placeholder_review(browser, base, player, out):
    """The opt-in review backdrop must retain normal controls and canvas input."""
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    try:
        page.goto(base + "?map=placeholder")
        page.fill("#access-token", player)
        page.locator("#login-button").click()
        page.wait_for_function("document.querySelectorAll('#campaign-select option').length===2")
        page.locator("[data-dialog-close]").click()
        page.select_option("#campaign-select", "demo-v2")
        page.wait_for_function("document.querySelector('#map-placeholder').hidden")
        review = page.locator(".map-review-placeholder")
        assert review.is_visible()
        assert review.evaluate("el=>getComputedStyle(el).pointerEvents") == "none"
        image_url = review.evaluate("el=>getComputedStyle(el).backgroundImage")
        assert "/static/images/tactical-placeholder.png" in image_url
        page.wait_for_function("performance.getEntriesByType('resource').some(r=>r.name.includes('/static/images/tactical-placeholder.png')&&r.responseEnd>0)")
        page.evaluate("window.reviewCanvas=document.querySelector('#planet-map')")
        descend_hierarchy(page, ["Hearth", "Cinder", "Reach"])
        public_state = httpx.get(base + "/api/player/campaigns/demo-v2", headers={"Authorization": "Bearer " + player}).json()["state"]
        settlement = public_state["settlements"][0]
        recorded_map = httpx.get(base + "/api/player/campaigns/demo-v2/map", params={"level": "planet", "node_id": settlement["planet_id"]}, headers={"Authorization": "Bearer " + player}).json()
        province = next(item for item in recorded_map["geometry"]["provinces"] if item["id"] == settlement["province_id"])
        point = province_point(page, province)
        page.mouse.click(point["x"], point["y"])
        page.wait_for_selector("#command-inspector:not([hidden])")
        page.locator("#hw-command").click()
        page.locator("[data-open=economy]").click()
        page.wait_for_selector("#command-workspace:not([hidden])")
        page.locator("#economy-panel .economy-turn-details > summary").first.click()
        flow = page.locator("#economy-panel .local-scope .resource-flow-chart svg").first
        flow.wait_for(state="visible")
        produced = public_state["latest_outcome"]["production"][settlement["id"]]["food"]
        consumed = public_state["latest_outcome"]["consumption"][settlement["id"]]["food"]
        assert f"{produced:,}" in flow.get_attribute("aria-label")
        assert f"{consumed:,}" in flow.get_attribute("aria-label")
        page.screenshot(path=str(out / "placeholder-economy.png"))
        # Already-mounted SVG labels must adapt too, without a chart reload.
        page.evaluate("window.reviewFlow=document.querySelector('#economy-panel .local-scope .resource-flow-chart svg')")
        for mode in ("dark", "light"):
            page.locator("#hw-command").click()
            page.select_option("#appearance-select", mode)
            page.locator("[data-menu-close]").click()
            label_channels = flow.locator("text").evaluate_all("nodes=>nodes.map(n=>getComputedStyle(n).fill.match(/[\\d.]+/g).slice(0,3).map(Number))")
            assert all(min(rgb) > 200 if mode == "dark" else max(rgb) < 80 for rgb in label_channels), label_channels
            assert page.evaluate("reviewFlow===document.querySelector('#economy-panel .local-scope .resource-flow-chart svg')")
            if mode == "dark":
                page.screenshot(path=str(out / "dark-local-economy.png"))
        page.locator("[data-return-map]").click()
        assert page.evaluate("window.reviewCanvas===document.querySelector('#planet-map')")
        assert "Reach" in page.locator("#map-breadcrumbs").inner_text()
        assert province["name"] in page.locator(".map-footer").inner_text()
        assert page.locator("#command-workspace").is_hidden()
        page.screenshot(path=str(out / "placeholder-map.png"))
        pixels = page.locator("#planet-map").evaluate("el=>el.toDataURL()")
        page.locator("#hw-command").click()
        page.locator("#temporary-map-toggle").uncheck()
        assert review.is_hidden()
        page.locator("#temporary-map-toggle").check()
        assert review.is_visible()
        assert page.locator("#planet-map").evaluate("el=>el.toDataURL()") == pixels
        # Navigation labels remain readable, with distinct domain symbols and colour
        # cues supplementing the labels rather than replacing them.
        menu_items = page.locator("#command-menu .menu-grid button").evaluate_all("""nodes=>nodes.map(n=>{
          const label=n.querySelector('span'), icon=n.querySelector('svg');
          const a=n.getBoundingClientRect(), b=label.getBoundingClientRect();
          return {id:n.dataset.open, fits:b.right<=a.right+1 && b.left>=a.left,
            stroke:getComputedStyle(icon).stroke, path:icon.querySelector('path').getAttribute('d')};
        })""")
        assert all(item["fits"] for item in menu_items), menu_items
        assert len({item["stroke"] for item in menu_items}) >= 4
        distinct = {item["path"] for item in menu_items if item["id"] in ("characters", "diplomacy", "trade", "orders")}
        assert len(distinct) == 4
        page.keyboard.press("Escape")
        # A public response fixture proves record names remain literal text with SVG icons.
        literal_title = '<img src=x onerror="window.recordTitleInjected=true">'
        def named_record(route):
            response = route.fetch()
            data = response.json()
            data["records"]["units"][0]["name"] = literal_title
            route.fulfill(response=response, json=data)
        page.route("**/systems?section=military*", named_record)
        page.evaluate("HWDesktop.open('military')")
        page.wait_for_function("document.querySelector('#management-military')?.innerText.includes('onerror')")
        title = page.locator("#management-military .force-record .record-summary-title").first
        assert title.evaluate("el=>[...el.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.textContent).join('').trim()") == literal_title
        assert title.locator("svg").count() == 1 and title.locator("img").count() == 0
        assert not page.evaluate("Boolean(window.recordTitleInjected)")
        page.evaluate("HWDesktop.open('fleet')")
        page.wait_for_selector("#management-fleet .force-owner-tag")
        fleet_cards = page.locator("#management-fleet .force-record")
        ground = fleet_cards.filter(has=page.locator("h3", has_text="Ground")).first
        transport = fleet_cards.filter(has=page.locator("h3", has_text="Transport")).first
        assert ground.locator("h3 path").get_attribute("d") != transport.locator("h3 path").get_attribute("d")
        assert page.locator("#management-fleet .force-owner-tag", has_text="FOREIGN").count() > 0
        page.evaluate("HWDesktop.open('industry')")
        page.wait_for_selector("#management-industry .settlement-breakdown")
        production = public_state["latest_outcome"]["production"][settlement["id"]]
        breakdown = page.locator("#management-industry .settlement-breakdown").filter(has=page.locator("h4", has_text=settlement["name"])).first
        assert f"{production['food']} units" in breakdown.inner_text()
        page.evaluate("HWDesktop.open('budget')")
        page.wait_for_selector("#management-budget .settlement-breakdown")
        budget = httpx.get(base + "/api/player/campaigns/demo-v2/systems?section=budget", headers={"Authorization": "Bearer " + player}).json()["records"]
        spending = page.locator("#management-budget .settlement-breakdown").filter(has=page.locator("h4", has_text=settlement["name"])).first
        assert f"{budget['spending'][settlement['id']]['upkeep_credits']} credits" in spending.inner_text()
        assert "{" not in spending.inner_text()
        def invalid_project(route):
            response = route.fetch()
            data = response.json()
            data["records"]["projects"][0]["work_done"] = -1
            route.fulfill(response=response, json=data)
        page.route("**/systems?section=construction*", invalid_project)
        page.evaluate("HWDesktop.open('construction')")
        page.wait_for_selector("#management-construction .project-progress-unknown", state="attached")
        assert page.locator("#management-construction .campaign-scope progress").count() == 0
        assert not errors, errors
        return {"direct_hierarchy_input": "passes through review backdrop", "canvas_identity": "retained", "page_errors": errors}
    finally:
        page.close()


def check_theme_preferences(browser, base, player, out):
    """Theme is a local UI preference; switching cannot replace strategic state."""
    context = browser.new_context(viewport={"width": 1280, "height": 900}, color_scheme="dark")
    page = context.new_page()
    errors, requests = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: requests.append(request.url) if "/api/" in request.url else None)
    try:
        page.goto(base + "?map=placeholder")
        page.wait_for_function("document.documentElement.dataset.theme==='dark'")
        page.fill("#access-token", player)
        page.locator("#login-button").click()
        page.wait_for_function("document.querySelectorAll('#campaign-select option').length===2")
        page.locator("[data-dialog-close]").click()
        page.select_option("#campaign-select", "demo-v2")
        page.wait_for_function("document.querySelector('#map-placeholder').hidden")
        page.wait_for_load_state("networkidle")
        page.evaluate("window.themeCanvas=document.querySelector('#planet-map'); window.themePixels=themeCanvas.toDataURL()")
        before_turn = page.locator("#command-turn").inner_text()
        page.locator("#hw-command").click()
        request_count = len(requests)
        for mode in ["light", "dark"] * 8:
            page.select_option("#appearance-select", mode)
            assert page.evaluate("document.documentElement.dataset.theme") == mode
        page.emulate_media(color_scheme="light")
        assert page.evaluate("document.documentElement.dataset.theme") == "dark"
        page.select_option("#appearance-select", "system")
        page.wait_for_function("document.documentElement.dataset.theme==='light'")
        page.emulate_media(color_scheme="dark")
        page.wait_for_function("document.documentElement.dataset.theme==='dark'")
        assert len(requests) == request_count, "Theme switching fetched campaign records"
        assert page.evaluate("themeCanvas===document.querySelector('#planet-map') && themePixels===themeCanvas.toDataURL()")
        assert page.locator("#command-turn").inner_text() == before_turn
        page.select_option("#appearance-select", "dark")
        page.screenshot(path=str(out / "dark-menu.png"))
        page.locator("#command-menu [data-open=economy]").click()
        page.wait_for_function("document.querySelector('#economy-panel').dataset.ready==='true'")
        surfaces = page.evaluate("""['#command-workspace','#command-inspector','#command-menu'].map(s=>{
          const c=getComputedStyle(document.querySelector(s)).backgroundColor;
          return {selector:s, rgba:c.match(/[\\d.]+/g).map(Number)};
        })""")
        assert all(max(item["rgba"][:3]) < 50 and item["rgba"][3] >= .8 for item in surfaces), surfaces
        page.screenshot(path=str(out / "dark-economy.png"))
        page.set_viewport_size({"width": 390, "height": 844})
        assert not page.evaluate("document.documentElement.scrollWidth>innerWidth")
        page.screenshot(path=str(out / "dark-mobile-economy.png"))
        page.emulate_media(color_scheme="light")
        page.reload()
        page.wait_for_function("document.documentElement.dataset.theme==='dark'")
        assert page.locator("#access-token").input_value() == ""
        assert page.evaluate("localStorage.getItem('hw.theme.v1')") == "dark"
        assert set(page.evaluate("Object.keys(localStorage)")) == {"hw.theme.v1"}
        assert not errors, errors
    finally:
        context.close()
    # Invalid or unavailable preference storage must not prevent startup.
    for blocked in (False, True):
        context = browser.new_context(color_scheme="dark")
        if blocked:
            context.add_init_script("for(const name of ['getItem','setItem'])Object.defineProperty(Storage.prototype,name,{value(){throw new Error('Storage blocked')}})")
        else:
            context.add_init_script("localStorage.setItem('hw.theme.v1','invalid')")
        page = context.new_page()
        page.goto(base)
        page.wait_for_function("document.documentElement.dataset.theme==='dark'")
        page.locator("[data-dialog-close]").click()
        page.locator("#hw-command").click()
        assert page.locator("#appearance-select").input_value() == "system"
        page.select_option("#appearance-select", "light")
        page.wait_for_function("document.documentElement.dataset.theme==='light'")
        context.close()
    return {"system_changes": "followed only in System mode", "reload": "explicit preference retained; auth not retained", "storage_unavailable": "operable", "theme_api_requests": 0, "canvas_pixels": "retained", "page_errors": errors}


def check_stock_history_retry(browser, base, player):
    """Repeated failures remain explicit; a later metric retry recovers in place."""
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    try:
        page.goto(base)
        page.fill("#access-token", player)
        page.locator("#login-button").click()
        page.wait_for_function("document.querySelectorAll('#campaign-select option').length===2")
        page.locator("[data-dialog-close]").click()
        page.select_option("#campaign-select", "demo-v2")
        page.wait_for_function("document.querySelector('#map-placeholder').hidden")
        pattern = "**/history?limit=1&offset=0"
        page.route(pattern, lambda route: route.fulfill(status=500, content_type="application/json", body='{"detail":"Fixture history unavailable"}'))
        page.locator("#hw-command").click()
        page.locator("[data-open=economy]").click()
        page.wait_for_function("document.querySelector('#economy-panel .economy-history-plot')?.textContent.includes('Food stock history is unavailable')")
        page.select_option("#economy-panel .economy-metric", "energy")
        page.wait_for_function("document.querySelector('#economy-panel .economy-history-plot')?.textContent.includes('Energy stock history is unavailable')")
        page.unroute(pattern)
        page.select_option("#economy-panel .economy-metric", "ore")
        page.wait_for_function("document.querySelector('#economy-panel .economy-history-plot svg')?.getAttribute('aria-label').toLowerCase().includes('ore') && document.querySelector('#economy-panel').dataset.ready==='true'")
        assert not errors, errors
        return {"consecutive_failures": "explicit per-resource errors", "metric_retry": "recovered in place", "page_errors": errors}
    finally:
        page.close()


def check_decision_readability(browser, base, player, out):
    """Readouts retain public facts, explicit unknowns and current access context."""
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    headers = {"Authorization": "Bearer " + player}
    try:
        page.goto(base)
        page.wait_for_function("document.querySelector('[data-summary=access]')?.textContent==='Sign in required'")
        assert page.locator("[data-summary=view]").inner_text() == "No snapshot"
        assert page.locator("#dialog-campaign-select").is_disabled()
        page.fill("#access-token", player)
        page.locator("#login-button").click()
        page.wait_for_function("!document.querySelector('#dialog-campaign-select').disabled")
        page.locator("#dialog-campaign-select").click()
        page.keyboard.press("Escape")
        page.select_option("#dialog-campaign-select", "demo-v2")
        page.wait_for_function("document.querySelector('#map-placeholder').hidden")
        page.evaluate("document.querySelector('#status-text').textContent='Unrelated report error'; HWDesktop.open('campaign')")
        assert "demo-v2" in page.locator("[data-summary=campaign]").inner_text()
        assert page.locator("[data-summary=access]").inner_text() == "Private access verified"
        assert player not in page.locator(".campaign-current-summary").inner_text()
        page.locator("[data-dialog-close]").click()
        page.evaluate("HWDesktop.open('economy')")
        page.wait_for_function("document.querySelector('#economy-panel').dataset.ready==='true'")
        history = httpx.get(base + "/api/player/campaigns/demo-v2/history?limit=100&offset=0", headers=headers).json()["items"]
        for metric in ("food", "energy", "ore"):
            page.select_option("#economy-panel .economy-metric", metric)
            page.wait_for_function("m=>document.querySelector('#economy-panel .economy-history-plot svg')?.dataset.metric===m", arg=metric)
            summary = page.locator("#economy-panel .history-range-summary").inner_text()
            values = [item["metrics"][metric] for item in history if isinstance(item["metrics"].get(metric), (int, float))]
            delta = values[-1] - values[0]
            assert f"{values[0]:,}" in summary and f"{values[-1]:,}" in summary
            assert f"Net change {'+' if delta > 0 else ''}{delta:,} stock units" in summary
        page.evaluate("HWDesktop.open('fleet')")
        page.wait_for_selector("#management-fleet .force-record")
        foreign = page.locator("#management-fleet .force-record").filter(has=page.locator(".force-owner-tag", has_text="FOREIGN")).first
        assert foreign.locator(".fact-strength dd").inner_text() == "10"
        assert foreign.locator(".fact-crew dd").inner_text() == "Unknown"
        assert "Observed turn 0" in foreign.inner_text()
        # Response-only fixtures exercise recorded problems and unavailable fields;
        # stored campaign records are never changed for these UI cases.
        def constraint_response(route):
            response = route.fetch()
            data = response.json()
            s = data["state"]
            sid = s["settlements"][0]["id"]
            s["latest_budget"] = {"unmet_upkeep": {sid: {"energy": 7, "credits": 5, "welfare": 2}}}
            s["latest_outcome"] = {"production": {sid: {"food": 1}}, "consumption": {sid: {"food": 9}}, "deaths": [{"settlement_id": sid, "count": 3}]}
            route.fulfill(response=response, json=data)
        pattern = "**/api/player/campaigns/demo-v2"
        page.route(pattern, constraint_response)
        page.select_option("#campaign-select", "demo-v2")
        page.wait_for_function("document.querySelector('#map-placeholder').hidden")
        page.evaluate("HWDesktop.returnMap()")
        page.select_option("#map-level", "planet")
        page.wait_for_load_state("networkidle")
        current = httpx.get(base + "/api/player/campaigns/demo-v2", headers=headers).json()["state"]
        settlement = current["settlements"][0]
        record = httpx.get(base + "/api/player/campaigns/demo-v2/map", params={"level": "planet", "node_id": settlement["planet_id"]}, headers=headers).json()
        province = next(x for x in record["geometry"]["provinces"] if x["id"] == settlement["province_id"])
        point = province_point(page, province)
        page.mouse.click(point["x"], point["y"])
        page.wait_for_selector("#command-inspector:not([hidden])")
        page.locator("#inspector-content").get_by_role("button", name="Economy", exact=True).click()
        constraints = page.locator(".local-scope .economy-recorded-condition").first
        constraints.wait_for()
        for fact in ("7 energy", "5 credits", "2 credits", "3 people", "-8 units"):
            assert fact in constraints.inner_text()
        assert page.locator(".economy-turn-details").first.get_attribute("open") is None
        page.screenshot(path=str(out / "response-fixture-constraints.png"))
        page.unroute(pattern)
        page.evaluate("HWDesktop.open('campaign')")
        page.locator("#logout-button").click()
        assert page.locator("[data-summary=access]").inner_text() == "Sign in required"
        assert page.locator("[data-summary=view]").inner_text() == "No snapshot"
        assert "demo-v2" not in page.locator("[data-summary=campaign]").inner_text()
        assert page.locator("#dialog-campaign-select").is_disabled()
        held = []
        page.route("**/api/player/campaigns", lambda route: held.append(route))
        page.fill("#access-token", player)
        page.locator("#login-button").click()
        page.wait_for_function("document.querySelector('[data-summary=access]').textContent==='Checking access'")
        assert page.locator("#refresh-button").is_disabled()
        assert page.locator("#dialog-refresh-campaigns").is_disabled()
        page.evaluate("document.querySelector('#refresh-button').onclick()")
        assert len(held) == 1
        held[0].fulfill(status=401, content_type="application/json", body='{"detail":"Response-only rejected login fixture"}')
        page.wait_for_function("document.querySelector('[data-summary=access]').textContent==='Sign in required'")
        assert page.locator("#refresh-button").is_enabled()
        page.unroute("**/api/player/campaigns")
        page.fill("#access-token", player)
        page.locator("#login-button").click()
        page.wait_for_function("document.querySelector('[data-summary=access]').textContent==='Private access verified'")
        assert not errors, errors
        # A transient list failure at startup must recover through Refresh.
        recovery = browser.new_page()
        authorized_list = httpx.get(base + "/api/player/campaigns", headers=headers).json()
        attempts = []
        recovery.route("**/api/access", lambda route: route.fulfill(json={"login_required": False}))
        def list_retry(route):
            attempts.append(True)
            if len(attempts) == 1:
                route.fulfill(status=503, json={"detail": "Response-only startup failure"})
            else:
                route.fulfill(json=authorized_list)
        recovery.route("**/api/player/campaigns", list_retry)
        try:
            recovery.goto(base)
            recovery.wait_for_function("document.querySelector('[data-summary=access]').textContent==='Access unavailable'")
            recovery.locator("#dialog-refresh-campaigns").click()
            recovery.wait_for_function("!document.querySelector('#dialog-campaign-select').disabled")
            assert recovery.locator("[data-summary=access]").inner_text() == "Local access"
        finally:
            recovery.close()
        return {"modal_selection": "operable", "access_summary": "current and cleared on logout", "login_refresh": "pending refresh blocked; rejection/retry honest", "startup_retry": "modal recovered", "history_summary": "API-matched", "force_strength": "retained with observation context", "constraints": "response-only positive fixture", "page_errors": errors}
    finally:
        page.close()


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
                out = Path(os.environ.get("WOLD_BROWSER_ARTIFACT_DIR", "data/instrument-candidate"))
                out.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(out / "map.png"))
                map_canvas = page.locator("#planet-map").element_handle()
                for level in ["galactic", "sector", "system", "planet"]:
                    with page.expect_response(lambda response: "/map?" in response.url and f"level={level}" in response.url) as response:
                        page.select_option("#map-level", level)
                    assert response.value.ok and response.value.json()["level"] == level
                    page.wait_for_function("level=>document.querySelector('#map-coordinates').textContent.startsWith(level.toUpperCase()+' ')", arg=level)
                    assert map_canvas.evaluate("el=>el===document.querySelector('#planet-map')")
                    page.screenshot(path=str(out / f"map-{level}.png"))
                page.wait_for_function("document.querySelector('#map-scale').textContent.includes('GRID')")
                page.wait_for_load_state("networkidle")
                descend_hierarchy(page, ["Hearth", "Cinder", "Reach"])
                # Ascend with an actual breadcrumb, then repeat the two lower links.
                page.locator("#map-breadcrumbs").get_by_role("button", name="Hearth", exact=True).click()
                page.wait_for_function("document.querySelector('#map-level').value==='sector' && document.querySelector('#map-coordinates').textContent.startsWith('SECTOR CARTOGRAPHY')")
                click_map_marker(page, "Cinder")
                page.wait_for_function("document.querySelector('#map-coordinates').textContent.startsWith('SYSTEM CHART')")
                page.locator("#zoom-in").click()
                page.mouse.move(650, 500);page.mouse.down();page.mouse.move(675, 520, steps=3);page.mouse.up()
                hierarchy_context = page.evaluate("({pixels:document.querySelector('#planet-map').toDataURL(),level:document.querySelector('#map-level').value,zoom:document.querySelector('#zoom-reset').textContent,path:document.querySelector('#map-breadcrumbs').textContent})")
                page.evaluate("HWDesktop.open('military');HWDesktop.open('economy');HWDesktop.returnMap()")
                page.evaluate("()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
                assert page.evaluate("({pixels:document.querySelector('#planet-map').toDataURL(),level:document.querySelector('#map-level').value,zoom:document.querySelector('#zoom-reset').textContent,path:document.querySelector('#map-breadcrumbs').textContent})") == hierarchy_context
                page.locator("#zoom-reset").click()
                click_map_marker(page, "Reach")
                page.wait_for_function("document.querySelector('#map-coordinates').textContent.startsWith('PLANET CARTOGRAPHY')")
                state = db.player_state(db.current("demo-v2")["snapshot"])
                settlement = next(x for x in state["settlements"] if x.get("planet_id"))
                planet = next(x for x in state["nodes"] if x["id"] == settlement["planet_id"])
                province = next(x for x in db.map_view("demo-v2", "planet", planet["id"])["geometry"]["provinces"]
                                if x["id"] == settlement["province_id"])
                point = province_point(page, province)
                page.mouse.click(point["x"], point["y"])
                page.wait_for_selector("#command-inspector:not([hidden])")
                page.wait_for_function("document.querySelector('#inspector-content').innerText.includes('LOCAL SETTLEMENTS')", timeout=2000)
                inspector_text = page.locator("#inspector-content").inner_text()
                assert settlement["name"] in inspector_text
                assert settlement["id"] not in inspector_text
                page.locator("#inspector-content details summary").first.click()
                assert settlement["id"] in page.locator("#inspector-content").inner_text()
                assert "Province ID" in page.locator("#inspector-content").inner_text()
                page.locator("#inspector-content details summary").first.click()
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
                started = time.perf_counter()
                page.locator("#inspector-content .inspector-actions button").first.click()
                page.wait_for_function("!document.querySelector('#command-workspace').hidden && !document.querySelector('#economy-panel .local-scope').hidden")
                timings["first_economy_action_ready_ms"] = (time.perf_counter() - started) * 1000
                economy = page.locator(".workspace-content").inner_text()
                assert settlement["name"] in economy and "CAMPAIGN-WIDE TOTALS" not in economy
                assert settlement["id"] not in economy
                assert "Housing" in economy and "Unrest" in economy
                assert "Economic diagnosis and forecasts are unrecorded" in economy
                assert page.locator("#economy-panel .resource-flow-chart").count() == 0, "Baseline must not fabricate food flow"
                page.locator("#economy-panel .economy-settlement > details:not(.economy-turn-details) > summary").click()
                assert settlement["id"] in page.locator("#economy-panel").inner_text()
                page.locator("#economy-panel .economy-settlement > details:not(.economy-turn-details) > summary").click()
                page.locator("#economy-panel [data-scope=campaign]").click()
                assert "CAMPAIGN-WIDE TOTALS" in page.locator("#economy-panel").inner_text()
                page.wait_for_selector("#economy-panel .history-range-summary")
                assert "Net change" not in page.locator("#economy-panel .economy-history-plot").inner_text()
                assert page.locator("#economy-panel .economy-history-plot svg").count() == 0
                page.locator("#economy-panel [data-scope=local]").click()
                page.screenshot(path=str(out / "economy.png"))
                assert page.locator("#command-workspace .workspace-title").inner_text() == "Economy"
                started = time.perf_counter()
                page.locator(".workspace-tabs button[data-tab=construction]").click()
                page.wait_for_function("(()=>{const p=document.querySelector('#management-construction'),l=p?.querySelector('.local-scope');return !!l&&!l.hidden&&p.innerText.includes('Farm')})()")
                timings["first_construction_action_ready_ms"] = (time.perf_counter() - started) * 1000
                construction = page.locator(".workspace-content").inner_text()
                assert settlement["name"] in construction and "Farm" in construction
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
                page.mouse.move(800, 350)
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
                page.wait_for_function("document.querySelector('#command-workspace .workspace-title').textContent === 'Military'")
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
                                return []
                            if isinstance(value, bool):
                                return ["Yes" if value else "No"]
                            return [str(value)] if isinstance(value, (str, int, float)) else []
                        sentinels = list(dict.fromkeys(x for record in expected for x in strings(record)))[:3]
                        page.wait_for_function("arg=>{const p=document.querySelector('#management-'+arg.view);return p&&arg.values.every(x=>p.textContent.includes(x))}", arg={"view":destination,"values":sentinels})
                        if not sentinels:
                            page.wait_for_function("view=>[...document.querySelectorAll('#management-'+view+' .empty-note')].some(n=>/^No .*record/.test(n.textContent))", arg=destination)
                    visible = page.locator(".workspace-content > :not([hidden])")
                    assert visible.count() == 1, f"More than one primary report visible for {destination}"
                page.evaluate("window.HWDesktop.open('history')")
                page.wait_for_function("document.querySelectorAll('#history-panel tbody tr').length>0")
                page.evaluate("window.HWDesktop.open('orders')")
                page.wait_for_selector("#proposal-json", state="attached")
                page.screenshot(path=str(out / "orders-empty.png"))
                page.locator("#orders-panel .order-source summary").click()
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
                descend_hierarchy(page, ["Hearth", "Cinder", "Reach"], touch=True)
                # First-action readiness and repeated warm navigation counts remain bounded.
                page.set_viewport_size({"width": 1280, "height": 900})
                # This new selected-place context is cold. Verify de-duplication
                # separately, then warm both reports before cached timing/counters.
                cold_history = []
                history_pattern = re.compile(re.escape(base) + r"/api/player/campaigns/demo-v2/history\?limit=1&offset=0$")
                page.route(history_pattern, lambda route: cold_history.append(route))
                with page.expect_request(history_pattern):
                    page.evaluate("for(let i=0;i<8;i++)HWDesktop.open('economy')")
                page.wait_for_timeout(50)
                assert len(cold_history) == 1, f"Duplicate cold Economy requests: {len(cold_history)}"
                cold_history[0].continue_()
                page.unroute(history_pattern)
                page.wait_for_function("document.querySelector('#economy-panel').dataset.ready==='true'")
                page.evaluate("HWDesktop.open('construction')")
                page.wait_for_function("document.querySelector('#management-construction')?.textContent.includes('demo-v2-forge-farm-1')")
                page.wait_for_load_state("networkidle")
                page.evaluate("HWDesktop.returnMap()")
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
                    {"settlement_id":"demo-v2-outpost",**{key:0 for key in ALLOCATIONS},"farmers":100}],"actions":[{"type":"build","settlement_id":"demo-v2-forge","facility_kind":"farm"},{"type":"recruit","settlement_id":"demo-v2-forge"}]}
                page.fill("#proposal-json",json.dumps(proposal))
                page.click("#preview-order")
                page.wait_for_function("document.querySelector('#command-preview').hidden===false && !document.querySelector('#commit-order').disabled")
                page.screenshot(path=str(out / "orders-validated.png"))
                page.locator("#orders-panel .order-source summary").click()
                assert page.locator("#commit-order").is_enabled()
                page.screenshot(path=str(out / "orders-validated-readable.png"))
                production_detail = page.locator("#order-result details").filter(has=page.locator("summary", has_text="Production by settlement"))
                production_detail.locator("summary").click()
                assert settlement["name"] in production_detail.inner_text()
                assert "Food" in production_detail.inner_text()
                assert not production_detail.locator("pre").count(), "Production should use readable fields"
                page.screenshot(path=str(out / "orders-validated-production.png"))
                production_detail.locator("summary").click()
                page.evaluate("window.HWDesktop.open('history'); window.HWDesktop.open('orders')")
                assert page.locator("#proposal-json").input_value()==json.dumps(proposal)
                page.click("#commit-order")
                page.wait_for_function("document.querySelector('#command-turn').textContent === 'TURN 1' && document.querySelector('#command-preview').hidden")
                # Actual supported build/recruit commands supply the new graphics' values.
                committed = httpx.get(base + "/api/player/campaigns/demo-v2", headers={"Authorization": "Bearer " + player}).json()["state"]
                project = committed["projects"][0]
                page.evaluate("HWDesktop.open('construction')")
                page.wait_for_selector("#management-construction [data-scope=campaign]")
                page.locator("#management-construction [data-scope=campaign]").click()
                progress = page.locator("#management-construction .campaign-scope progress").first
                progress.wait_for(state="visible")
                assert progress.evaluate("el=>({value:el.value,max:el.max})") == {"value": project["work_done"], "max": project["work_required"]}
                page.screenshot(path=str(out / "construction-progress.png"))
                page.evaluate("HWDesktop.open('military')")
                readiness = page.locator("#management-military .fact-readiness dd").first
                readiness.wait_for(state="visible")
                expected_unit = next(unit for unit in committed["units"] if unit.get("owner") == "player")
                assert readiness.inner_text().rstrip("%") == str(expected_unit["readiness"])
                page.screenshot(path=str(out / "military-readiness.png"))
                page.evaluate("HWDesktop.open('economy')")
                page.locator("#economy-panel [data-scope=campaign]").click()
                page.wait_for_selector("#economy-panel .chart-box svg")
                page.wait_for_function("document.querySelector('#economy-panel').dataset.ready==='true'")
                history_requests_before = page.evaluate("performance.getEntriesByType('resource').filter(r=>r.name.includes('/history?')).length")
                for metric in ["energy", "ore", "food"]:
                    page.select_option("#economy-panel .economy-metric", metric)
                    page.wait_for_function("metric=>document.querySelector('#economy-panel .chart-box svg')?.getAttribute('aria-label')?.toLowerCase().includes(metric)", arg=metric)
                assert page.evaluate("performance.getEntriesByType('resource').filter(r=>r.name.includes('/history?')).length") == history_requests_before, "Switching stock metrics should reuse recorded history"
                assert "stock units" in page.locator("#economy-panel .economy-history-head").inner_text()
                for width in [390, 1280]:
                    page.set_viewport_size({"width": width, "height": 900})
                    axis_labels = page.locator("#economy-panel .history-value-axis span")
                    assert axis_labels.count() == 5
                    assert axis_labels.evaluate_all("nodes=>nodes.every(el=>parseFloat(getComputedStyle(el).fontSize)>=12 && el.getBoundingClientRect().height>=12)"), "Stock axes must remain readable after resizing"
                    assert not page.evaluate("document.documentElement.scrollWidth>innerWidth")
                page.screenshot(path=str(out / "economy-trend.png"))
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
                metrics={"viewport":"1280x900, 656x518, 390x844","fixture":"isolated demo-v2 PostgreSQL","map_levels":["galactic","sector","system","planet"],"timings":timings,"cold_burst_history_requests":len(cold_history),"warm_cycles":len(cycle_times),"dom_nodes_before":before_dom,"dom_nodes_after":after_dom,"api_resources_before":before_requests,"api_resources_after":after_requests,"canvas_identity":"retained", "camera_overlay_selection":"pixels and controls retained", "cdp_before":before_memory, "cdp_after":after_memory,"page_errors":errors}
                assert not errors, errors
                (out/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
                metrics["placeholder_review"] = check_placeholder_review(browser, base, player, out)
                metrics["stock_history_retry"] = check_stock_history_retry(browser, base, player)
                metrics["theme_preferences"] = check_theme_preferences(browser, base, player, out)
                metrics["decision_readability"] = check_decision_readability(browser, base, player, out)
                browser.close()
                metrics["browser_zoom"] = check_browser_zoom(playwright, executable, base, player, out)
                (out/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
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
