"""Real celestial focus navigation, map-context return and access clearance.

Use WOLD_BODY_FOCUS_BASE/CAMPAIGN with an isolated V10/V11 static-v1 demo.
The Reach and Ash planets must be surveyed through supported exploration (the
fixture reaches turn 3); its turn-0 snapshot must still have Ash detected.
Optional WOLD_BODY_FOCUS_PRIVATE_CONTEXT names a local secret JSON file containing
private_port/player_token/gm_token for a private server with this same campaign.
No credentials or fixture database are embedded in this test or its report.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.browser_planet_orbit import HOOK
from tests.browser_orbit_background import SKY_HOOK
from tests.browser_quality_control import act

FOCUS_HOOK = '''(()=>{const timer=setInterval(()=>{const f=window.HWBodyFocus;if(!f)return;clearInterval(timer);
 const capture=f.capture,restore=f.restore,a=window.__bodyAudit={captures:0,returns:[]};
 const ui=s=>({mapLevel:s.mapLevel,mapNodeId:s.mapNodeId,panX:s.panX,panY:s.panY,zoom:s.zoom,
 orbitActive:s.orbitActive,orbitView:{...s.orbitView},selectedProvince:s.selectedProvince,
 selectedEntityId:s.selectedEntity?.id||null,selectedFeatureId:s.selectedFeatureId,
 selectedFeaturePlanetId:s.selectedFeaturePlanetId,selectedFeatureReturnProvince:s.selectedFeatureReturnProvince,
 selectedComposition:s.selectedComposition?{...s.selectedComposition}:null,overlay:s.overlay,
 mapStyle:s.mapStyle,showFeatureNames:s.showFeatureNames,featureListOpen:s.featureListOpen,featureListQuery:s.featureListQuery});
 f.capture=function(s){a.captures++;a.origin=ui(s);return capture(s);};
 f.restore=function(t,s){const ok=restore(t,s);a.returns.push({ok,ui:ui(s)});return ok;};},5)})()'''


def main():
    base = os.environ.get("WOLD_BODY_FOCUS_BASE", "http://127.0.0.1:4213").rstrip("/")
    campaign = os.environ.get("WOLD_BODY_FOCUS_CAMPAIGN", "nav-demo")
    out = Path(os.environ.get("WOLD_BODY_FOCUS_OUT", ROOT / "data/scale-focus/body-browser"))
    out.mkdir(parents=True, exist_ok=True)
    files = ["public/app.js", "public/body-focus.js", "public/style.css", "public/index.html",
             "public/map-renderer.js", "public/planet-orbit.js", "public/orbit-background.js"]
    hashes = lambda: {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files}
    start_hashes, errors = hashes(), []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1440, "height": 1024}, has_touch=True)
        for hook in (HOOK, SKY_HOOK, FOCUS_HOOK): page.add_init_script(hook)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base)
        page.wait_for_selector(f'#campaign-select option[value="{campaign}"]', state="attached")
        if page.locator("[data-dialog-close]").is_visible():
            act(page, out, "close-access", lambda: page.locator("[data-dialog-close]").click())
        before = page.request.get(f"{base}/api/player/campaigns/{campaign}").json()
        nodes = before["state"]["nodes"]
        planet = next(n for n in nodes if n["kind"] == "planet" and n["id"].endswith("-reach"))
        other = next(n for n in nodes if n["kind"] == "planet" and n["id"].endswith("-ash"))
        assert other["knowledge"] == "surveyed", "Use a fixture with a real completed exploration"
        star = next(n for n in nodes if n["kind"] == "star" and n["parent_id"] == planet["parent_id"])
        moon = next(n for n in nodes if n["kind"] == "moon" and n["parent_id"] == planet["id"])
        history = page.request.get(f"{base}/api/player/campaigns/{campaign}/history").json()
        original_id = next(row["id"] for row in history["items"] if row["turn"] == 0)
        original_state = page.request.get(f"{base}/api/player/snapshots/{original_id}").json()["state"]
        historical_other = next(n for n in original_state["nodes"] if n["id"] == other["id"])
        act(page, out, "select-campaign", lambda: page.select_option("#campaign-select", campaign))
        page.wait_for_selector("#orbit-toggle:visible", timeout=90000)
        act(page, out, "locate-home", lambda: page.locator("#map-recenter").click())
        page.wait_for_selector(".orbit-landmark:visible", timeout=90000)
        canvas = page.locator("#planet-map").element_handle()
        focus = page.locator("#body-focus-view")

        def capture(name):
            page.wait_for_timeout(600)
            page.screenshot(path=str(out / f"{name}.png"))
            (out / f"{name}-aria.yml").write_text(page.locator("body").aria_snapshot())

        def focused(node):
            page.wait_for_selector(f'#body-focus-view[data-body-id="{node["id"]}"]:visible')
            assert node["name"] in focus.inner_text()

        def choose(node, name):
            act(page, out, name, lambda: focus.locator(f'[data-body-id="{node["id"]}"]').click())

        def exact_return():
            page.wait_for_function("__bodyAudit.returns.length&&__bodyAudit.returns.at(-1).ok")
            result = page.evaluate("({origin:__bodyAudit.origin,last:__bodyAudit.returns.at(-1)})")
            assert result["last"]["ui"] == result["origin"], result
            assert page.locator("#body-focus-view").is_hidden()
            assert page.locator("#body-focus-view").get_attribute("data-body-id") is None
            assert page.locator("#overlay-select").input_value() == result["origin"]["overlay"]
            assert page.locator("#map-style").input_value() == result["origin"]["mapStyle"]
            assert page.evaluate("__orbitAudit.view") == result["origin"]["orbitView"]
            assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')

        # Keep a real selected province and a nondefault overlay/style in origin.
        act(page, out, "select-forge", lambda: page.locator(".orbit-landmark:visible").filter(has_text="Forge").click())
        page.wait_for_function("document.querySelector('#orbit-toggle').textContent==='Orbit'")
        act(page, out, "population-overlay", lambda: page.select_option("#overlay-select", "population"))
        page.wait_for_function("__surfaceAudit.o.overlay==='population'")
        act(page, out, "survey-style", lambda: page.select_option("#map-style", "survey"))
        act(page, out, "enter-orbit", lambda: page.locator("#orbit-toggle").click())
        page.wait_for_timeout(650)
        act(page, out, "locate-star", lambda: page.locator("#orbit-star-locate").click())
        page.wait_for_timeout(650)
        capture("01-origin-context")
        point, box = page.evaluate("__skyAudit.point"), page.locator("#planet-map").bounding_box()
        assert point
        x, y = box["x"] + point["x"], box["y"] + point["y"]
        assert page.evaluate('p=>document.elementFromPoint(p.x,p.y)?.id==="planet-map"', {"x": x, "y": y})
        act(page, out, "stellar-point-click", lambda: page.mouse.click(x, y))
        focused(star)
        assert page.evaluate("__bodyAudit.captures") == 1
        assert page.evaluate("__bodyAudit.origin.selectedProvince")
        assert star["name"] in page.locator(".section-title h1").inner_text()
        stage = focus.locator(".body-focus-star").bounding_box()
        assert stage["width"] >= 200 and stage["height"] >= 200
        frame, toolbar = focus.bounding_box(), page.locator("#view-title").bounding_box()
        assert frame["y"] >= toolbar["y"] + toolbar["height"]
        assert page.locator("#map-style").is_disabled()
        assert focus.locator(f'[data-body-id="{star["id"]}"]').get_attribute("aria-current") == "true"
        capture("02-star-focus")
        act(page, out, "reduce-motion", lambda: page.emulate_media(reduced_motion="reduce"))
        page.wait_for_timeout(500)
        assert focus.evaluate("e=>e.getAnimations({subtree:true}).filter(a=>a.playState==='running').length") == 0
        act(page, out, "normal-motion", lambda: page.emulate_media(reduced_motion="no-preference"))
        assert focus.evaluate("e=>e.getAnimations({subtree:true}).some(a=>a.playState==='running')")
        choose(moon, "moon-destination")
        focused(moon)
        assert "Unknown" in focus.inner_text() and "No terrain, craters" in focus.inner_text()
        assert focus.evaluate("e=>e.getAnimations({subtree:true}).filter(a=>a.playState==='running').length") == 0
        capture("03-moon-focus")
        choose(star, "star-again")
        assert page.evaluate("__bodyAudit.captures") == 1
        act(page, out, "back-origin", lambda: page.locator("#body-focus-back").click())
        exact_return()
        capture("04-exact-origin-return")

        # Native keyboard activation, then a different genuinely surveyed map.
        act(page, out, "focus-star-keyboard", lambda: (page.locator(".orbit-star-marker:visible").focus(), page.keyboard.press("Enter")))
        focused(star)
        choose(other, "other-surveyed-planet")
        page.wait_for_function("id=>__surfaceAudit?.o.planetId===id&&__surfaceAudit.o.detail?.version==='planet-detail-v2'", arg=other["id"], timeout=90000)
        assert page.locator("#zoom-in").is_enabled()
        surface_before = page.evaluate("({ox:__surfaceAudit.t.ox,oy:__surfaceAudit.t.oy,tile:__surfaceAudit.t.tile})")
        bounds = page.locator("#planet-map").bounding_box()
        dx, dy = bounds["x"] + bounds["width"] * .35, bounds["y"] + bounds["height"] * .55
        assert page.evaluate('p=>document.elementFromPoint(p.x,p.y)?.id==="planet-map"', {"x": dx, "y": dy})
        act(page, out, "pan-other-planet", lambda: (page.mouse.move(dx, dy), page.mouse.down(), page.mouse.move(dx+100, dy+35, steps=6), page.mouse.up()))
        assert page.evaluate("({ox:__surfaceAudit.t.ox,oy:__surfaceAudit.t.oy,tile:__surfaceAudit.t.tile})") != surface_before
        tile = page.evaluate("__surfaceAudit.t.tile")
        act(page, out, "zoom-other-planet", lambda: page.locator("#zoom-in").click())
        assert page.evaluate("__surfaceAudit.t.tile") > tile
        capture("05-other-planet-interactive")
        choose(moon, "moon-from-other-planet")
        assert page.evaluate("__bodyAudit.captures") == 2
        act(page, out, "back-across-map-load", lambda: page.locator("#body-focus-back").click())
        page.wait_for_function("document.querySelector('#body-focus-view').hidden", timeout=90000)
        exact_return()
        capture("06-origin-after-other-map")

        # Touch target and changing history/context must clear the focus ticket.
        point = page.evaluate("__skyAudit.point")
        act(page, out, "stellar-point-touch", lambda: page.touchscreen.tap(point["x"] + box["x"], point["y"] + box["y"]))
        focused(star)
        def command(name):
            act(page, out, f"menu-{name}", lambda: page.locator("#hw-command").click())
            act(page, out, name, lambda: page.locator(f'#command-menu [data-open="{name}"]').click())
        command("history")
        act(page, out, "inspect-turn-zero", lambda: page.get_by_role("button", name="Inspect turn 0", exact=True).click())
        page.wait_for_function("!document.querySelector('#historical-badge').hidden")
        page.wait_for_selector("#orbit-star-locate:visible", timeout=90000)
        assert focus.is_hidden() and focus.get_attribute("data-body-id") is None
        act(page, out, "historical-locate", lambda: page.locator("#orbit-star-locate").click())
        act(page, out, "historical-star", lambda: page.locator(".orbit-star-marker:visible").click())
        focused(star)
        choose(other, "historical-detected-planet")
        focused(historical_other)
        assert focus.get_attribute("data-body-knowledge") == "detected"
        assert "Unknown" in focus.inner_text() and "No terrain, craters" in focus.inner_text()
        capture("07-historical-detected-planet")
        command("orders")
        page.wait_for_function("document.querySelector('#orders-panel').textContent.includes('Return to the live campaign revision')")
        assert not page.locator("#commit-order").count() or page.locator("#commit-order").is_disabled()
        act(page, out, "switch-campaign", lambda: page.select_option("#campaign-select", "legacy-demo"))
        page.wait_for_timeout(700)
        assert focus.is_hidden() and focus.get_attribute("data-body-id") is None
        assert focus.get_attribute("aria-label") is None and not focus.inner_text()
        assert page.request.get(f"{base}/api/player/campaigns/{campaign}").json() == before

        private_verified = False
        private_path = os.environ.get("WOLD_BODY_FOCUS_PRIVATE_CONTEXT")
        if private_path:
            context = json.loads(Path(private_path).read_text())
            secure = browser.new_page(viewport={"width": 1440, "height": 1024})
            secure.on("pageerror", lambda error: errors.append(str(error)))
            secure.goto(f'http://127.0.0.1:{context["private_port"]}')
            secure.wait_for_selector("#access-token:visible")
            secure.locator("#access-token").fill(context["player_token"])
            secure.locator("#login-button").click()
            secure.wait_for_selector(f'#campaign-select option[value="{campaign}"]', state="attached")
            secure.locator("[data-dialog-close]").click()
            secure.select_option("#campaign-select", campaign)
            secure.wait_for_selector("#orbit-star-locate:visible", timeout=90000)
            secure.locator("#orbit-star-locate").click()
            secure.wait_for_selector(".orbit-star-marker:visible")
            secure.locator(".orbit-star-marker:visible").click()
            secure.wait_for_selector("#body-focus-view:visible")
            secure.locator("#hw-command").click()
            secure.locator('#command-menu [data-open="campaign"]').click()
            secure.locator("#logout-button").click()
            secure.wait_for_function("document.querySelector('#body-focus-view').hidden")
            assert not secure.locator("#body-focus-view").inner_text()
            assert secure.locator("#body-focus-view").get_attribute("data-body-id") is None
            storage = secure.evaluate("JSON.stringify({local:{...localStorage},session:{...sessionStorage}})")
            assert context["player_token"] not in storage and context["gm_token"] not in storage
            private_verified = True
            secure.close()
        assert not errors and hashes() == start_hashes
        report = {"browser": browser.version, "viewport": [1440, 1024],
                  "point_mouse_touch_and_label_keyboard": True, "star_moon_planet_navigation": True,
                  "other_surveyed_planet_pan_zoom": True, "one_ticket_per_journey": True,
                  "exact_origin_camera_selection_overlay_style": True, "main_canvas_retained": True,
                  "reduced_motion": True, "hidden_star_animation_removed": True,
                  "historical_detected_planet_and_read_only": True, "context_identity_cleared": True,
                  "private_logout_and_token_storage": private_verified, "records_unchanged": True,
                  "page_errors": errors, "source_hashes": hashes()}
        (out / "workflow.json").write_text(json.dumps(report, indent=2)+"\n")
        print(json.dumps(report, indent=2))
        browser.close()


if __name__ == "__main__":
    main()
