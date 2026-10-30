"""Hold actual detail responses to verify projection continuity and stale rejection."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK
from tests.browser_navigation_continuity import HOOK_SYSTEM


def main():
    out=Path('data/navigation-glass/loading');out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1280,'height':900});errors=[]
        for hook in [HOOK,HOOK_SYSTEM]:page.add_init_script(hook)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:4213');page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached')
        if page.locator('[data-dialog-close]').is_visible():page.locator('[data-dialog-close]').click()
        page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000)
        origin=page.evaluate('__orbitAudit.view')
        page.select_option('#map-level','system');page.wait_for_function('window.__systemAudit?.layout.supported')
        page.wait_for_timeout(300)
        held=[]
        def hold(route):held.append((route,route.fetch()))
        page.route('**/detail?**',hold)
        page.select_option('#map-level','planet')
        page.wait_for_function("document.querySelector('#detail-status').textContent.includes('Opening saved orbit')")
        pixels=page.locator('#planet-map').evaluate('c=>c.toDataURL()')
        page.select_option('#overlay-select','population')
        for _ in range(100):
            if len(held)>=2:break
            page.wait_for_timeout(100)
        assert len(held)>=2,'Replacement detail request never arrived'
        assert 'Opening saved orbit' in page.locator('#detail-status').inner_text()
        assert page.locator('#planet-map').evaluate('c=>c.toDataURL()')==pixels,'Pending detail flashed a different projection'
        page.mouse.move(600,500);page.mouse.down();page.mouse.move(680,540,steps=4);page.mouse.up();page.mouse.wheel(0,-120)
        assert page.locator('#planet-map').evaluate('c=>c.toDataURL()')==pixels,'Pending frame accepted map manipulation'
        page.screenshot(path=str(out/'01-held-frame.png'))
        held[0][0].fulfill(response=held[0][1]);page.wait_for_timeout(300)
        assert 'Opening saved orbit' in page.locator('#detail-status').inner_text(),'Stale detail released the newer hold'
        for route,response in held[1:]:route.fulfill(response=response)
        page.wait_for_function("document.querySelector('#orbit-toggle').textContent==='Surface'",timeout=90000)
        assert page.evaluate('__orbitAudit.view')==origin
        assert page.locator('#overlay-select').input_value()=='population'
        page.screenshot(path=str(out/'02-restored-orbit.png'))
        assert not errors,errors
        report={'browser':browser.version,'retained_canvas_pixels':True,'input_blocked_while_loading':True,
                'stale_detail_rejected':True,'same_planet_overlay_hold':True,'exact_camera_restored':True,'page_errors':errors}
        (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close()


if __name__=='__main__':main()
