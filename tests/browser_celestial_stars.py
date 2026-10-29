"""Actual saved-star bearing, illumination, visibility and context workflows."""
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


def main():
    base = os.environ.get("WOLD_CELESTIAL_BASE", "http://127.0.0.1:4206")
    campaign = os.environ.get("WOLD_CELESTIAL_CAMPAIGN", "astronomy-demo")
    out = Path(os.environ.get("WOLD_CELESTIAL_OUT", ROOT / "data/celestial-stars/browser"))
    out.mkdir(parents=True, exist_ok=True)
    paths = ["public/app.js", "public/planet-orbit.js", "public/orbit-background.js",
             "public/index.html", "public/style.css"]
    hashes = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    initial_hashes, errors = hashes(), []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path="/usr/bin/chromium",
                                    args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1440, "height": 1024}, has_touch=True)
        page.add_init_script(HOOK)
        page.add_init_script(SKY_HOOK)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base)
        page.wait_for_selector(f'#campaign-select option[value="{campaign}"]', state="attached")
        if page.locator("[data-dialog-close]").is_visible():
            act(page, out, "close-access", lambda: page.locator("[data-dialog-close]").click())
        before = page.request.get(f"{base}/api/player/campaigns/{campaign}").json()
        state = before["state"]
        planet = next(n for n in state["nodes"] if n["kind"] == "planet" and n["knowledge"] == "surveyed")
        star = next(n for n in state["nodes"] if n["kind"] == "star" and n["parent_id"] == planet["parent_id"])
        bodies = state["astronomy"]["systems"][planet["parent_id"]]["bodies"]
        raw = [a-b for a, b in zip(bodies[star["id"]]["position"], bodies[planet["id"]]["position"])]
        direction = [v / math.hypot(*raw) for v in raw]
        act(page, out, "select-astronomy", lambda: page.select_option("#campaign-select", campaign))
        marker = page.locator(".orbit-star-marker")
        page.wait_for_selector("#orbit-star-locate:visible", timeout=90000)
        page.wait_for_timeout(700)
        page.screenshot(path=str(out / "00-home-context.png"))
        act(page, out, "locate-initial-mouse", lambda: page.locator("#orbit-star-locate").click())
        page.wait_for_selector(".orbit-star-marker:visible", timeout=90000)
        page.wait_for_timeout(700)
        canvas = page.locator("#planet-map").element_handle()

        def capture(name):
            page.wait_for_timeout(600)
            page.screenshot(path=str(out / f"{name}.png"))
            (out / f"{name}-aria.yml").write_text(page.locator("body").aria_snapshot())

        def view(): return page.evaluate("__orbitAudit.view")

        def check_direction_and_light():
            actual = page.evaluate("__orbitAudit.starDirection")
            assert max(abs(a-b) for a, b in zip(actual, direction)) < 1e-12
            saved = page.evaluate("__skyAudit.last.star")
            assert saved["node"]["id"] == star["id"]
            assert max(abs(a-b) for a, b in zip(saved["direction"], direction)) < 1e-12
            error = page.evaluate('''d=>{const r=__orbitEngine,f=HWPlanetOrbit.basis(__orbitAudit.view.latitude,__orbitAudit.view.longitude),
              light=r.gl.getUniform(r.program,r.locations.lightDirection),expected=[f.E,f.U,f.N].map(v=>v.reduce((s,n,i)=>s+n*d[i],0));
              return Math.max(...expected.map((n,i)=>Math.abs(n-light[i])));}''', direction)
            assert error < 1e-6, "Actual shader illumination must follow the saved star"
            # Independent camera oracle: reconstruct the shader's world ray from
            # the drawn point, then compare with the saved finite star-camera ray.
            ray_error = page.evaluate('''()=>{const a=__orbitAudit,star=__skyAudit.last.star,p=__skyAudit.point;
              if(!p)return 0;const f=HWPlanetOrbit.basis(a.view.latitude,a.view.longitude),
              F=Math.min(a.rect.width,a.rect.height)*.36*a.view.distance,
              x=(p.x-a.rect.left-a.rect.width/2)/F,y=-(p.y-a.rect.top-a.rect.height/2)/F,
              ray=f.E.map((n,i)=>n*x+f.U[i]*y-f.N[i]),
              expected=star.offsetKm.map((n,i)=>n-a.view.distance*star.planetRadiusKm*f.N[i]),
              r=Math.hypot(...ray),e=Math.hypot(...expected);
              return Math.max(...ray.map((n,i)=>Math.abs(n/r-expected[i]/e)));}''')
            assert ray_error < 1e-10, "Drawn star must use the actual globe camera, including finite parallax"

        check_direction_and_light()
        assert star["name"] in marker.inner_text() and "Epoch 0" in marker.inner_text()
        assert "symbol not to scale" in marker.inner_text()
        assert page.locator(".orbit-star-scale").evaluate("e=>e.scrollWidth<=e.getBoundingClientRect().width+1"), "Epoch/scale caption must fit its label"
        assert page.evaluate("__skyAudit.point!==null")
        capture("01-recorded-star")
        calls = page.evaluate("__skyAudit.calls")
        page.wait_for_timeout(350)
        assert page.evaluate("__skyAudit.calls") == calls
        located = view()
        act(page, out, "dark-theme", lambda: page.evaluate('HWTheme.set("dark")'))
        check_direction_and_light()
        assert view() == located
        capture("02-dark-star")

        def drag(dx, dy, name):
            rect = page.evaluate("__orbitAudit.rect")
            cx, cy = rect["left"] + rect["width"] / 2, rect["top"] + rect["height"] / 2
            choices = [(cx+220, cy+90), (cx-220, cy+90), (cx, cy+160)]
            x, y = next((x, y) for x, y in choices if page.evaluate(
                'p=>document.elementFromPoint(p.x,p.y)?.id==="planet-map"', {"x": x, "y": y}))
            act(page, out, name, lambda: (page.mouse.move(x, y), page.mouse.down(),
                page.mouse.move(x+dx, y+dy, steps=8), page.mouse.up()))
            page.wait_for_timeout(600)

        rect = page.evaluate("__orbitAudit.rect")
        focal = min(rect["width"], rect["height"]) * .36
        # This generated contract uses coplanar bodies, so bringing latitude to
        # zero puts the actual star behind the globe, at the same longitude.
        drag(0, -view()["latitude"] * focal, "occlude-star")
        check_direction_and_light()
        assert page.evaluate("__skyAudit.point===null") and marker.is_hidden()
        capture("03-globe-occlusion")
        drag(-math.pi*focal, 0, "turn-away")
        assert page.evaluate("__skyAudit.point===null") and marker.is_hidden()
        capture("04-behind-camera")
        act(page, out, "locate-touch", lambda: page.locator("#orbit-star-locate").tap())
        page.wait_for_selector(".orbit-star-marker:visible")
        check_direction_and_light()
        capture("05-located-again")

        def command(name):
            act(page, out, f"menu-{name}", lambda: page.locator("#hw-command").click())
            act(page, out, name, lambda: page.locator(f'#command-menu [data-open="{name}"]').click())

        camera = view()
        command("economy")
        act(page, out, "return-map", lambda: page.locator("[data-return-map]:visible").click())
        assert view() == camera
        act(page, out, "surface", lambda: page.locator("#orbit-toggle").click())
        page.wait_for_timeout(650)
        assert marker.is_hidden() and page.locator("#orbit-star-locate").is_hidden()
        act(page, out, "return-orbit", lambda: page.locator("#orbit-toggle").click())
        page.wait_for_timeout(650)
        returned = view()
        assert abs(math.atan2(math.sin(returned["longitude"]-camera["longitude"]),
                             math.cos(returned["longitude"]-camera["longitude"]))) < .03
        check_direction_and_light()
        command("history")
        act(page, out, "inspect-turn-zero", lambda: page.get_by_role("button", name="Inspect turn 0", exact=True).click())
        page.wait_for_function("!document.querySelector('#historical-badge').hidden")
        page.wait_for_selector("#orbit-star-locate:visible", timeout=90000)
        act(page, out, "locate-historical-star", lambda: page.locator("#orbit-star-locate").click())
        page.wait_for_selector(".orbit-star-marker:visible", timeout=90000)
        check_direction_and_light()
        capture("06-historical-sky")
        command("orders")
        page.wait_for_function("document.querySelector('#orders-panel').textContent.includes('Return to the live campaign revision')")
        assert not page.locator("#commit-order").count() or page.locator("#commit-order").is_disabled()
        command("history")
        act(page, out, "return-live", lambda: page.get_by_role("button", name="Return to live", exact=True).click())
        page.wait_for_function("document.querySelector('#historical-badge').hidden")
        act(page, out, "return-live-map", lambda: page.locator("[data-return-map]:visible").click())
        page.wait_for_selector("#orbit-star-locate:visible", timeout=90000)
        act(page, out, "locate-live-star", lambda: page.locator("#orbit-star-locate").click())
        page.wait_for_selector(".orbit-star-marker:visible", timeout=90000)
        act(page, out, "legacy-campaign", lambda: page.select_option("#campaign-select", "legacy-demo"))
        page.wait_for_timeout(850)
        assert page.locator(".orbit-star-marker:visible").count() == 0
        assert page.locator("#orbit-star-locate").is_hidden()
        capture("07-legacy-no-astronomy")
        act(page, out, "pregame-campaign", lambda: page.select_option("#campaign-select", "campaign"))
        page.wait_for_timeout(650)
        assert page.locator(".orbit-star-marker:visible").count() == 0
        assert page.locator("#orbit-star-locate").is_hidden()
        capture("08-pregame-no-astronomy")
        assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')
        assert page.request.get(f"{base}/api/player/campaigns/{campaign}").json() == before
        assert not errors and hashes() == initial_hashes
        report = {"browser": browser.version, "viewport": [1440, 1024],
                  "saved_body_direction": direction, "recorded_identity": star["id"],
                  "shader_matches_saved_direction": True, "finite_star_matches_globe_camera_ray": True,
                  "native_occlusion_and_turn_away": True,
                  "mouse_and_touch_locate": True, "theme_preserves_bearing": True,
                  "management_preserves_camera": True, "surface_orbit_preserves_longitude": True,
                  "historical_record_rendering_read_only": True, "legacy_and_pregame_empty": True,
                  "map_canvas_retained": True, "no_idle_render": True,
                  "campaign_records_unchanged": True, "page_errors": errors, "source_hashes": hashes()}
        (out / "workflow.json").write_text(json.dumps(report, indent=2)+"\n")
        print(json.dumps(report, indent=2))
        browser.close()


if __name__ == "__main__":
    main()
