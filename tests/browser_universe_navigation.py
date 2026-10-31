"""Read-only outward zoom, qualitative fog and authorized Universe navigation."""
import hashlib
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK
from tests.browser_navigation_continuity import HOOK_SYSTEM, HOOK_HIERARCHY

HOOK_UNIVERSE='''(()=>{window.__universeFrames=[];window.__mapListenerAdds=0;const add=EventTarget.prototype.addEventListener;EventTarget.prototype.addEventListener=function(...args){if(this.id==='planet-map')__mapListenerAdds++;return add.apply(this,args);};const timer=setInterval(()=>{if(!window.HWUniverseView)return;clearInterval(timer);
const draw=HWUniverseView.draw;HWUniverseView.draw=function(ctx,o){const started=performance.now(),result=draw.call(this,ctx,o);__universeFrames.push(performance.now()-started);window.__universeAudit={record:o.record,theme:o.theme,zoom:o.zoom,panX:o.panX,panY:o.panY,layout:result};return result;};},5)})()'''


def main():
    base=os.environ.get('WOLD_UNIVERSE_BASE','http://127.0.0.1:4213');cid='nav-demo'
    out=Path(os.environ.get('WOLD_UNIVERSE_OUT','data/universe-navigation/candidate'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/universe-view.js','public/index.html','public/style.css','public/desktop-shell.js','public/desktop-shell.css']
    hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files}
    initial=hashes();errors=[];requests=[];steps=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        context.tracing.start(screenshots=True,snapshots=True);page=context.new_page()
        for hook in [HOOK,HOOK_SYSTEM,HOOK_HIERARCHY,HOOK_UNIVERSE]:page.add_init_script(hook)
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:requests.append(request.url) if '/map?' in request.url else None)
        page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached')
        if page.locator('[data-dialog-close]').is_visible():page.locator('[data-dialog-close]').click()
        before=page.request.get(base+'/api/player/campaigns/'+cid).json()
        page.select_option('#campaign-select',cid);page.wait_for_function('window.__orbitAudit?.result',timeout=90000)
        page.evaluate("HWTheme.set('dark')");canvas=page.locator('#planet-map').element_handle();listener_count=page.evaluate('__mapListenerAdds')
        def snap(name):
            page.screenshot(path=str(out/(name+'.png')));steps.append(name)
        def wait_level(level):
            page.wait_for_function('level=>document.querySelector("#map-level").value===level&&document.querySelector("#view-title h1").textContent.includes(level[0].toUpperCase()+level.slice(1))',arg=level,timeout=90000)
        # Actual wheel crosses surface minimum to globe, then +/− controls pull out.
        page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Orbit"')
        page.locator('#zoom-reset').click();page.mouse.move(600,500);page.mouse.wheel(0,120)
        page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Surface"',timeout=90000);snap('01-surface-to-orbit')
        for _ in range(30):
            if page.locator('#map-level').input_value()=='system':break
            page.locator('#zoom-out').click();page.wait_for_timeout(220)
        wait_level('system');page.wait_for_function('window.__systemAudit?.layout.supported');snap('02-orbit-to-system')
        # Change angle before pulling out, so return verifies more than default Fit.
        page.mouse.move(600,500);page.mouse.down();page.mouse.move(660,525,steps=4);page.mouse.up()
        outward_held=[]
        def outward_hold(route):
            if 'level=galactic' in route.request.url:outward_held.append(route)
            else:route.continue_()
        page.route('**/api/player/campaigns/nav-demo/map?*',outward_hold)
        for _ in range(30):
            if page.locator('#map-level').input_value()=='universe':break
            last_system=page.evaluate('__systemAudit.view')
            page.locator('#zoom-out').click();page.wait_for_timeout(200)
        page.mouse.move(500,500)
        for _ in range(6):page.mouse.wheel(0,300)
        page.wait_for_timeout(300);assert len(outward_held)==1, 'Wheel burst must request exactly one Universe transition'
        outward_held[0].fulfill(response=outward_held[0].fetch());page.unroute('**/api/player/campaigns/nav-demo/map?*',outward_hold)
        wait_level('universe');page.wait_for_function('window.__universeAudit?.record.level==="universe"')
        for level in ['sector','system','planet']:assert page.locator('#map-level option[value="'+level+'"]').evaluate('n=>n.disabled')
        audit=page.evaluate('__universeAudit');assert audit['zoom']==1 and audit['panX']==0 and audit['panY']==0,audit
        public=page.request.get(base+'/api/player/campaigns/'+cid+'/map?level=galactic').json()
        allowed={n['id'] for group in public['groups'] for n in [group['region'],*group['sectors']]}
        contacts=audit['record']['nodes'];assert {n['id'] for n in contacts}==allowed
        assert all(n['knowledge']!='hidden' for n in contacts)
        assert not any('level=universe' in url for url in requests),'UI level must not broaden backend map API'
        assert 'unknown' in page.locator('#detail-status').inner_text().lower() or 'unknown' in page.locator('#map-coordinates').inner_text().lower()
        snap('03-universe-dark')
        page.evaluate("HWTheme.set('light')");page.wait_for_function('__universeAudit.theme==="light"');snap('04-universe-light');page.evaluate("HWTheme.set('dark')");page.wait_for_function('__universeAudit.theme==="dark"')
        # More outward wheel events stay in Universe. Return is explicit and scoped.
        page.mouse.move(500,500)
        for _ in range(8):page.mouse.wheel(0,300)
        page.wait_for_timeout(500);wait_level('universe')
        page.locator('#universe-return').click();wait_level('system');page.wait_for_timeout(300)
        assert page.evaluate('__systemAudit.view')==last_system,(last_system,page.evaluate('__systemAudit.view'))
        # An intentional inward zoom from Universe returns to the remembered system.
        page.select_option('#map-level','universe');wait_level('universe');page.wait_for_timeout(350)
        for _ in range(15):
            if page.locator('#map-level').input_value()=='system':break
            page.locator('#zoom-in').click();page.wait_for_timeout(90)
        wait_level('system');page.wait_for_timeout(200)
        assert page.evaluate('__systemAudit.view')==last_system
        # Universe and Galactic have independent root cameras, and no inherited planet pan.
        page.select_option('#map-level','universe');wait_level('universe');page.locator('#zoom-reset').click()
        page.mouse.move(600,550);page.mouse.down();page.mouse.move(680,575,steps=4);page.mouse.up()
        page.locator('#zoom-in').click();page.wait_for_timeout(300);universe_camera=page.evaluate('({zoom:__universeAudit.zoom,panX:__universeAudit.panX,panY:__universeAudit.panY})')
        page.select_option('#map-level','galactic');wait_level('galactic');page.wait_for_timeout(250)
        assert page.evaluate('__hierarchyAudit.zoom')==1 and page.evaluate('__hierarchyAudit.panX')==0
        page.select_option('#map-level','universe');wait_level('universe')
        assert page.evaluate('({zoom:__universeAudit.zoom,panX:__universeAudit.panX,panY:__universeAudit.panY})')==universe_camera
        page.locator('#zoom-reset').click();page.wait_for_timeout(150)
        region_point=page.evaluate('__universeAudit.layout.positions.find(p=>p.n.kind==="region")')
        page.mouse.click(region_point['x'],region_point['y']);wait_level('galactic')
        page.select_option('#map-level','universe');wait_level('universe')
        # Known sector is reachable through the labeled dropdown; detected is generic.
        sector=next(n for n in contacts if n['kind']=='sector' and n['knowledge']=='surveyed')
        page.select_option('#universe-contact-select',sector['id']);page.locator('#universe-open').click();wait_level('sector')
        page.select_option('#map-level','universe');wait_level('universe')
        page.set_viewport_size({'width':1280,'height':720});page.evaluate("document.documentElement.style.zoom='1.5'");page.wait_for_timeout(300)
        small=page.evaluate('__universeAudit');s=small['layout']['safeRect']
        assert {p['n']['id'] for p in small['layout']['positions']}==allowed,'Fit must retain all reviewed contacts on short desktop chart'
        for point in small['layout']['positions']:
            assert point['y']-22>=s['top']+45 and point['hitRect']['bottom']<=s['bottom'],point
        snap('05-desktop-zoom')
        for selector in ['#universe-contact-select','#universe-open','#universe-return','#map-level']:
            r=page.locator(selector).bounding_box();assert r and r['x']>=0 and r['y']>=0 and r['x']+r['width']<=1281 and r['y']+r['height']<=721,(selector,r)
        page.evaluate("document.documentElement.style.zoom='1'");page.set_viewport_size({'width':1440,'height':1000})
        # History uses its own authorized map response and loses live return target.
        page.locator('#hw-command').click();page.locator('#command-menu [data-open="history"]').click()
        page.get_by_role('button',name='Inspect turn 0',exact=True).click();page.wait_for_function('!document.querySelector("#historical-badge").hidden')
        if page.locator('[data-return-map]').is_visible():page.locator('[data-return-map]').click()
        page.select_option('#map-level','universe');wait_level('universe');page.wait_for_function('id=>__universeAudit.record.snapshot_id!==id',arg=before['snapshot_id'])
        historical=page.evaluate('__universeAudit.record');assert historical['snapshot_id']!=before['snapshot_id']
        expected=page.request.get(base+'/api/player/campaigns/'+cid+'/map?level=galactic&snapshot_id='+historical['snapshot_id']).json()
        assert {n['id'] for n in historical['nodes']}=={n['id'] for g in expected['groups'] for n in [g['region'],*g['sectors']]}
        assert page.locator('#universe-return').is_disabled();snap('06-historical-fog')
        # A held old map response cannot repaint another campaign.
        held=[]
        def hold(route):
            if 'level=galactic' in route.request.url:held.append(route)
            else:route.continue_()
        page.route('**/api/player/campaigns/nav-demo/map?*',hold)
        page.select_option('#map-level','universe');page.wait_for_timeout(300);assert held
        page.select_option('#campaign-select','legacy-demo');page.wait_for_timeout(800)
        for route in held:route.fulfill(status=200,content_type='application/json',body=json.dumps(expected))
        page.wait_for_timeout(700)
        assert 'Universe' not in page.locator('#view-title h1').inner_text()
        assert page.locator('#universe-selection').is_hidden()
        assert canvas.evaluate('n=>n===document.querySelector("#planet-map")')
        assert page.evaluate('__mapListenerAdds')==listener_count,'Panel/map navigation must not add canvas handlers'
        frame_times=page.evaluate('__universeFrames');assert frame_times
        assert before==page.request.get(base+'/api/player/campaigns/'+cid).json()
        private_verified=False
        private_path=os.environ.get('WOLD_BODY_FOCUS_PRIVATE_CONTEXT')
        if private_path:
            credentials=json.loads(Path(private_path).read_text())
            secure=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
            secure.on('pageerror',lambda error:errors.append(str(error)))
            secure.goto('http://127.0.0.1:'+str(credentials['private_port']))
            secure.wait_for_selector('#access-token:visible');secure.locator('#access-token').fill(credentials['player_token']);secure.locator('#login-button').click()
            secure.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');secure.locator('[data-dialog-close]').click()
            secure.select_option('#campaign-select',cid);secure.wait_for_function('document.querySelector("#view-title h1").textContent.includes("Planet")',timeout=90000)
            private_held=[]
            def private_hold(route):
                if 'level=galactic' in route.request.url:private_held.append(route)
                else:route.continue_()
            secure.route('**/api/player/campaigns/nav-demo/map?*',private_hold)
            secure.select_option('#map-level','universe');secure.wait_for_timeout(300);assert private_held
            secure.locator('#hw-command').click();secure.locator('#command-menu [data-open="campaign"]').click();secure.locator('#logout-button').click()
            secure.wait_for_selector('#access-token:visible')
            for route in private_held:route.fulfill(status=200,content_type='application/json',body=json.dumps(public))
            secure.wait_for_timeout(500);assert secure.locator('#universe-selection').is_hidden()
            assert 'Universe' not in secure.locator('#view-title h1').inner_text()
            storage=secure.evaluate('JSON.stringify({local:{...localStorage},session:{...sessionStorage}})')
            assert credentials['player_token'] not in storage and credentials['gm_token'] not in storage
            private_verified=True;secure.close()
        assert not errors and initial==hashes(),errors
        context.tracing.stop(path=str(out/'workflow-trace.zip'))
        report={'browser':browser.version,'steps':steps,'surface_orbit_system_universe_outward':True,'same_system_camera_return':True,'separate_root_cameras':True,'authorized_contacts_only':True,'historical_fog_context':True,'held_response_campaign_isolation':True,'dark_light':True,'private_logout_held_response':private_verified,'desktop_css_zoom':True,'same_canvas':True,'stable_canvas_handlers':True,'universe_draw_calls':len(frame_times),'universe_draw_ms_median':sorted(frame_times)[len(frame_times)//2],'universe_draw_ms_max':max(frame_times),'records_unchanged':True,'page_errors':errors,'source_hashes':hashes(),'limits':'Qualitative schematic fog; no physical explored-area data. Reduced-motion Chromium software graphics; no motion smoothness, native browser zoom or Safari claim.'}
        (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close()


if __name__=='__main__':main()
