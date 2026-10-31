"""Viewing origin, destination focus, compact controls and guarded camera opening."""
import hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_universe_navigation import HOOK_UNIVERSE

POSES='''(()=>{const timer=setInterval(()=>{if(!window.HWUniverseView)return;clearInterval(timer);window.__atlasPoses=[];const draw=HWUniverseView.draw;HWUniverseView.draw=function(c,o){const r=draw.call(this,c,o);__atlasPoses.push({zoom:o.zoom,panX:o.panX,panY:o.panY,time:performance.now()});if(__atlasPoses.length>600)__atlasPoses.shift();return r;};},5)})()'''


def main():
    out=Path(os.environ.get('WOLD_ATLAS_OUT','data/atlas-orientation/candidate'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/universe-view.js','public/index.html','public/desktop-shell.css'];hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files};initial=hashes();errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage']);context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='no-preference')
        context.tracing.start(screenshots=True,snapshots=True);page=context.new_page()
        for hook in [HOOK_UNIVERSE,POSES]:page.add_init_script(hook)
        page.on('pageerror',lambda e:errors.append(str(e)));base='http://127.0.0.1:4213'
        def level(value):page.wait_for_function('v=>document.querySelector("#map-level").value===v&&document.querySelector("#view-title h1").textContent.includes(v[0].toUpperCase()+v.slice(1))',arg=value)
        def camera():return page.evaluate('({zoom:__universeAudit.zoom,panX:__universeAudit.panX,panY:__universeAudit.panY})')
        def snap(name):page.screenshot(path=str(out/(name+'.png')))
        def open_universe():page.select_option('#map-level','universe');level('universe');page.wait_for_timeout(150)
        page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click()
        page.evaluate("HWTheme.set('dark')");before=page.request.get(base+'/api/player/campaigns/nav-demo').json();page.select_option('#campaign-select','nav-demo');level('planet')
        old_header=page.locator('#chart-heading').bounding_box()['height'];canvas=page.locator('#planet-map').element_handle();open_universe()
        origin=page.locator('#universe-origin').inner_text();assert all(name in origin for name in ['Cinder','Hearth','Kestrel Reach']),origin
        assert page.locator('#universe-return').is_enabled();compact_header=page.locator('#chart-heading').bounding_box()['height']
        assert page.locator('#resource-shell').is_hidden() and page.locator('#map-breadcrumbs').is_hidden();snap('01-origin')
        # Focus previews a selected destination without opening its chart.
        page.locator('#zoom-reset').click();page.evaluate('__atlasPoses=[]');start=camera()
        target=page.evaluate('__universeAudit.layout.positions.find(p=>p.n.id==="nav-demo-sector-hearth")')
        page.mouse.click(target['x'],target['y']);page.wait_for_timeout(450)
        assert page.locator('#map-level').input_value()=='universe';assert page.locator('#universe-contact-select').input_value()=='nav-demo-sector-hearth'
        dest=page.locator('#universe-destination').inner_text();assert 'Hearth' in dest and 'Sector' in dest,dest
        focused=camera();assert focused!=start
        poses=page.evaluate('__atlasPoses');assert len({round(p['zoom'],4) for p in poses})>1,'Normal focus must have camera interpolation'
        selected=page.evaluate('__universeAudit.layout.positions.find(p=>p.n.id==="nav-demo-sector-hearth")');safe=page.evaluate('__universeAudit.layout.safeRect')
        assert abs(selected['x']-(safe['left']+safe['right'])/2)<45
        snap('02-destination-focus')
        # All public layout anchors remain selectable after manual panning offscreen.
        for _ in range(4):
            page.mouse.move(900,720);page.mouse.down();page.mouse.move(180,720,steps=3);page.mouse.up()
        assert not page.evaluate('__universeAudit.layout.positions.some(p=>p.n.id==="nav-demo-sector-hearth")')
        page.select_option('#universe-contact-select','nav-demo-sector-hearth');page.wait_for_timeout(450)
        assert page.evaluate('__universeAudit.layout.positions.some(p=>p.n.id==="nav-demo-sector-hearth")'),'Offscreen selection must use complete layout anchors'
        # A short approach opens the chart and returns to the pre-approach focus camera.
        pre_open=camera();page.evaluate('__atlasPoses=[]');page.locator('#universe-open').click();level('sector')
        assert len({round(p['zoom'],4) for p in page.evaluate('__atlasPoses')})>1
        open_universe();assert camera()==pre_open,(pre_open,camera())
        # Synchronous race inputs test cancellation before approach completion.
        for action in ['wheel','menu','selection']:
            page.locator('#zoom-reset').click();page.select_option('#universe-contact-select','nav-demo-sector-hearth');page.wait_for_timeout(300)
            if action=='wheel':page.evaluate('document.querySelector("#universe-open").click();document.querySelector("#planet-map").dispatchEvent(new WheelEvent("wheel",{deltaY:120,bubbles:true,cancelable:true}))')
            elif action=='menu':page.evaluate('document.querySelector("#universe-open").click();document.querySelector("#hw-command").click()')
            else:page.evaluate('document.querySelector("#universe-open").click();const s=document.querySelector("#universe-contact-select");s.value="nav-demo-region-01";s.dispatchEvent(new Event("change",{bubbles:true}))')
            page.wait_for_timeout(550);assert page.locator('#map-level').input_value()=='universe',action
            if action=='menu':page.locator('[data-menu-close]').click()
        page.locator('#zoom-reset').click();page.set_viewport_size({'width':1280,'height':720});page.evaluate("document.documentElement.style.zoom='1.5'");page.wait_for_timeout(300);page.locator('#zoom-reset').click();page.wait_for_timeout(100)
        for selector in ['#universe-contact-select','#universe-open','#universe-return','#map-level','#universe-origin','#universe-destination']:
            r=page.locator(selector).bounding_box();assert r and r['x']>=0 and r['y']>=0 and r['x']+r['width']<=1281 and r['y']+r['height']<=721,(selector,r)
        for selector in ['#universe-origin','#universe-destination']:
            assert page.locator(selector).evaluate('n=>n.scrollWidth<=n.clientWidth+2&&n.scrollHeight<=n.clientHeight+2'),selector
        snap('03-compact-desktop')
        page.evaluate("document.documentElement.style.zoom='1'");page.set_viewport_size({'width':1440,'height':1000});page.emulate_media(reduced_motion='reduce');page.locator('#zoom-reset').click();page.select_option('#universe-contact-select','nav-demo-sector-hearth')
        page.mouse.move(900,720);page.mouse.down();page.mouse.move(980,750,steps=3);page.mouse.up();reduced_pre_open=camera()
        page.locator('#universe-open').click();level('sector')
        assert page.locator('#resource-shell').is_visible(),'Other map HUD must be restored';open_universe();assert camera()==reduced_pre_open
        # A new campaign cancels an opening and clears both readouts.
        page.emulate_media(reduced_motion='no-preference');page.select_option('#universe-contact-select','nav-demo-sector-hearth');page.wait_for_timeout(300)
        page.evaluate('document.querySelector("#universe-open").click();const s=document.querySelector("#campaign-select");s.value="campaign";s.dispatchEvent(new Event("change",{bubbles:true}))')
        page.wait_for_timeout(650);assert page.locator('#universe-selection').is_hidden();assert 'Sector' not in page.locator('#view-title h1').inner_text()
        assert 'Cinder' not in page.locator('#universe-origin').inner_text() and 'Hearth' not in page.locator('#universe-destination').inner_text()
        assert 'Cinder' not in (page.locator('#universe-origin').get_attribute('title') or '')
        assert 'Hearth' not in (page.locator('#universe-destination').get_attribute('title') or '')
        assert 'Hearth' not in page.locator('#universe-open').inner_text()
        # Starting from an unanchored Galactic chart must not invent a current system.
        page.select_option('#campaign-select','nav-demo');level('planet');page.select_option('#map-level','galactic');level('galactic');open_universe()
        unknown=page.locator('#universe-origin').inner_text();assert 'Cinder' not in unknown and ('unrecorded' in unknown.lower() or 'unknown' in unknown.lower()),unknown
        assert page.locator('#universe-return').is_disabled();snap('04-unrecorded-origin')
        assert canvas.evaluate('n=>n===document.querySelector("#planet-map")');assert before==page.request.get(base+'/api/player/campaigns/nav-demo').json();assert not errors and initial==hashes(),errors
        context.tracing.stop(path=str(out/'workflow-trace.zip'));report={'browser':browser.version,'recorded_origin_from_planet':True,'destination_preview_before_open':True,'animated_focus_and_approach':True,'offscreen_destination_focus':True,'exact_pre_approach_camera_return':True,'wheel_overlay_selection_cancel':True,'context_cancel_clears_readouts':True,'reduced_motion_open':True,'compact_header_height_px':compact_header,'planet_header_height_px':old_header,'desktop_css_zoom':True,'unrecorded_origin_not_invented':True,'other_map_hud_restored':True,'same_canvas':True,'records_unchanged':True,'page_errors':errors,'source_hashes':hashes(),'limits':'Software Chromium, small recorded fixture; cancellation races use synchronous DOM events. CSS zoom only, not native Safari or physical universal positions.'};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close()


if __name__=='__main__':main()
