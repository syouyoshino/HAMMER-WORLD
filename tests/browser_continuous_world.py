"""Recorded miniature -> focused planet -> surface, using isolated real demos."""
import hashlib
import json
import math
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK
from tests.browser_navigation_continuity import HOOK_SYSTEM

TIMELINE='''(()=>{const t=setInterval(()=>{if(!window.HWMapRenderer)return;clearInterval(t);window.__journey=[];
const m=HWMapRenderer,draw=m.drawPlanet;m.drawPlanet=function(ctx,o){const r=draw.apply(this,arguments);__journey.push({kind:'surface',detail:!!o.detail,planet:o.planetId,time:performance.now()});return r;};
const timer=setInterval(()=>{if(!window.__orbitEngine)return;clearInterval(timer);const r=__orbitEngine,render=r.render;r.render=function(...args){const value=render.apply(this,args);__journey.push({kind:'globe',view:{...args[4]},time:performance.now()});return value;};},5);},5)})()'''


def main():
    base=os.environ.get('WOLD_CONTINUOUS_BASE','http://127.0.0.1:4220')
    manifest=json.loads(Path('data/continuous-world/fixture-manifest.json').read_text())
    worlds=os.environ.get('WOLD_CONTINUOUS_CASES','sparse,rich,extreme').split(',')
    out=Path(os.environ.get('WOLD_CONTINUOUS_OUT','data/continuous-world/candidate'));out.mkdir(parents=True,exist_ok=True)
    sources=['public/app.js','public/system-view.js','public/system-previews.js','public/style.css','public/index.html']
    hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in sources}
    initial=hashes();rows=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':1000});page.context.tracing.start(screenshots=True,snapshots=True)
        for h in [HOOK,HOOK_SYSTEM,TIMELINE]:page.add_init_script(h)
        def record_error(error):
            errors.append(str(error));(out/'page-errors.json').write_text(json.dumps(errors,indent=2))
        page.on('pageerror',record_error)
        page.goto(base);page.wait_for_selector('#campaign-select option[value="'+manifest[worlds[0]]['campaign_id']+'"]',state='attached')
        if page.locator('[data-dialog-close]').is_visible():page.locator('[data-dialog-close]').click()
        for world in worlds:
            case=manifest[world];cid=case['campaign_id'];folder=out/world;folder.mkdir(exist_ok=True)
            before=page.request.get(base+'/api/player/campaigns/'+cid).json()
            page.select_option('#campaign-select',cid)
            page.wait_for_function('cid=>window.__orbitAudit?.result&&String(__orbitAudit.revision).startsWith(cid+":")',arg=cid,timeout=90000)
            canvas=page.locator('#planet-map').element_handle();page.evaluate("HWTheme.set('dark')")
            preview_started=time.perf_counter();page.select_option('#map-level','system')
            page.wait_for_function('id=>window.__systemAudit?.layout.model.systemId===id',arg=case['system_id'])
            surveyed=[n for n in before['state']['nodes'] if n['kind']=='planet' and n['knowledge']=='surveyed']
            pid=surveyed[0]['id']
            page.wait_for_function('ids=>ids.every(id=>window.HWSystemPreviewService?.stateFor(id)==="ready")',arg=[n['id'] for n in surveyed],timeout=180000)
            preview_ready_ms=(time.perf_counter()-preview_started)*1000
            assert not page.evaluate('__systemAudit.view.showGrid')
            page.screenshot(path=str(folder/'01-system.png'))
            page.select_option('#system-body-select',pid)
            assert page.locator('#map-level').input_value()=='system','Selecting a body must not navigate'
            meta=page.evaluate('id=>{const p=HWSystemPreviewService.get(id);return {sourceSha:p.sourceSha,orientation:p.orientation,width:p.sprite.width,height:p.sprite.height}}',pid)
            recorded=page.request.get(base+'/api/player/campaigns/'+cid+'/map?level=planet&node_id='+pid+'&overlay=terrain').json()
            assert meta['sourceSha']==recorded['geometry']['detail_ref']['sha256'] and meta['width']==128 and meta['height']==128
            saved_vectors=page.evaluate('__systemAudit.layout.model.located.map(p=>({id:p.n.id,relative:p.relative}))')
            page.locator('#system-focus').click()
            page.wait_for_function('id=>__systemAudit.view.targetBodyId===id&&__systemAudit.view.focusProgress===1',arg=pid)
            page.screenshot(path=str(folder/'02-focus.png'))
            focused=page.evaluate('__systemAudit.view')
            assert page.evaluate('__systemAudit.layout.model.located.map(p=>({id:p.n.id,relative:p.relative}))')==saved_vectors
            assert page.evaluate('id=>__systemAudit.layout.positions.find(p=>p.n.id===id).radius',pid)>40
            page.locator('#system-inspect').click();page.wait_for_selector('#command-inspector:visible')
            inspect_text=page.locator('#command-inspector').inner_text()
            assert 'Physical radius' in inspect_text and 'km' in inspect_text and '{' not in inspect_text,inspect_text
            assert not page.locator('#command-inspector details').first.evaluate('n=>n.open')
            inspector=page.locator('#command-inspector').bounding_box();strip=page.locator('#system-selection').bounding_box()
            assert inspector['y']>=strip['y']+strip['height']-1,'Inspector obstructs destination actions'
            selected_point=page.evaluate('id=>__systemAudit.layout.positions.find(p=>p.n.id===id)',pid)
            assert selected_point['x']+selected_point['radius']<=inspector['x'] or selected_point['x']-selected_point['radius']>=inspector['x']+inspector['width'],'Inspector obscures selected world'
            page.screenshot(path=str(folder/'02b-inspect.png'))
            page.locator('[data-inspector-close]').click();assert page.evaluate('__systemAudit.view')==focused
            if world==worlds[0]:
                page.locator('#system-enter').click();page.locator('#system-inspect').click()
                page.wait_for_timeout(1200)
                assert page.locator('#map-level').input_value()=='system','Inspect must cancel automatic entry'
                assert page.locator('#command-inspector').is_visible();page.locator('[data-inspector-close]').click()
            origin=page.evaluate('__systemAudit.view');page.evaluate('__journey=[]')
            page.locator('#system-enter').click()
            page.wait_for_function('__journey.some(x=>x.kind==="globe")',timeout=90000)
            page.screenshot(path=str(folder/'03-transition-capture.png'))
            page.wait_for_function('__journey.some(x=>x.kind==="globe")&&document.querySelector("#orbit-toggle").textContent==="Orbit"&&window.__surfaceAudit?.o.detail?.version==="planet-detail-v2"',timeout=90000)
            timeline=page.evaluate('__journey');(folder/'timeline.json').write_text(json.dumps(timeline,indent=2))
            first_globe=next(i for i,r in enumerate(timeline) if r['kind']=='globe')
            assert not any(r['kind']=='surface' for r in timeline[:first_globe]),'Surface flashed before globe handoff'
            entry=timeline[first_globe]['view'];assert abs(entry['latitude']-meta['orientation']['latitude'])<1e-7
            assert abs(entry['longitude']-meta['orientation']['longitude'])<1e-7
            page.screenshot(path=str(folder/'04-surface.png'))
            assert page.locator('#system-selection').is_hidden(),'System-only actions must hide on the surface'
            assert 'Surface' in page.locator('#view-title h1').inner_text()
            center=page.evaluate('''()=>{const {t,o}=__surfaceAudit,s=t.safeRect,x=((s.left+s.right)/2-t.ox)/t.tile,y=((s.top+s.bottom)/2-t.oy)/t.tile;
              return {latitude:Math.PI*(.5-y/o.geometry.planet.height),longitude:x/o.geometry.planet.width*Math.PI*2-Math.PI};}''')
            assert abs(center['latitude']-entry['latitude'])<.02,(center,entry)
            assert abs((center['longitude']-entry['longitude']+math.pi)%(2*math.pi)-math.pi)<.02,(center,entry)
            marker=page.locator('#entry-focus-marker');assert marker.is_visible(),'Carried geographic focus missing'
            location=page.locator('#entry-focus-coordinates').inner_text();assert 'N' in location and '°' in location
            marker_before=marker.evaluate('n=>({x:parseFloat(n.style.left),y:parseFloat(n.style.top)})')
            page.mouse.move(400,600);page.mouse.down();page.mouse.move(480,620,steps=5);page.mouse.up()
            marker_after=marker.evaluate('n=>({x:parseFloat(n.style.left),y:parseFloat(n.style.top)})')
            assert abs(marker_after['x']-marker_before['x'])>30,'Focus marker must follow geography, not screen centre'
            assert page.locator('#entry-focus-coordinates').inner_text()==location
            page.screenshot(path=str(folder/'04b-focus-panned.png'))
            page.select_option('#map-level','system');page.wait_for_function('id=>__systemAudit.layout.model.systemId===id',arg=case['system_id'])
            page.wait_for_timeout(300);assert page.evaluate('__systemAudit.view')==origin,(origin,page.evaluate('__systemAudit.view'))
            # Explicit orbit is a stable destination, allowing the player to choose a location.
            page.locator('#system-orbit').click()
            page.wait_for_function('document.querySelector("#map-level").value==="planet"&&document.querySelector("#orbit-toggle").textContent==="Surface"',timeout=90000)
            page.wait_for_timeout(1300)
            assert page.locator('#orbit-toggle').inner_text()=='Surface','Explicit orbit must not descend automatically'
            assert 'Orbit' in page.locator('#view-title h1').inner_text()
            assert page.locator('#system-selection').is_hidden()
            assert abs(page.evaluate('__orbitAudit.view.longitude')-meta['orientation']['longitude'])<1e-7
            page.screenshot(path=str(folder/'05-orbit-choice.png'))
            point=page.evaluate('''()=>{const r=__orbitAudit.rect;return{x:r.left+r.width/2,y:r.top+r.height/2}}''')
            page.mouse.click(point['x'],point['y']);page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Orbit"')
            page.select_option('#map-level','system');page.wait_for_function('id=>__systemAudit.layout.model.systemId===id',arg=case['system_id'])
            page.wait_for_timeout(250);assert page.evaluate('__systemAudit.view')==origin
            unknown=next(n for n in before['state']['nodes'] if n['kind']=='planet' and n['knowledge']=='detected')
            page.select_option('#system-body-select',unknown['id'])
            assert page.locator('#system-focus').is_disabled() and page.locator('#system-enter').is_disabled()
            assert page.locator('#system-orbit').is_disabled()
            assert page.evaluate('id=>HWSystemPreviewService.get(id)',unknown['id']) is None
            page.locator('#system-inspect').click();assert page.locator('#command-inspector').is_visible();page.locator('[data-inspector-close]').click()
            page.locator('#system-grid-toggle').click();assert page.evaluate('__systemAudit.view.showGrid')
            page.locator('#system-grid-toggle').click();assert not page.evaluate('__systemAudit.view.showGrid')
            assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')
            assert before==page.request.get(base+'/api/player/campaigns/'+cid).json()
            rows.append({'world':world,'planet_count':case['planet_count'],'surveyed_previews':len(surveyed),'preview_ready_ms':preview_ready_ms,'selected':pid,'preview':meta,'same_bearing_globe_surface':True,'exact_system_return':True,'explicit_orbit_and_manual_descent':True,'geographic_focus_follows_pan':True,'readable_body_summary':True,'inspector_clearance':True,'unknown_surface_restricted':True,'records_unchanged':True})
        assert not errors and initial==hashes(),errors
        page.context.tracing.stop(path=str(out/'workflow-trace.zip'))
        report={'browser':browser.version,'rows':rows,'page_errors':errors,'source_hashes':hashes(),'limits':'Isolated real supported-solid-surface demos; no gas-giant or moon terrain. Software Chromium, no hardware/Safari claim.'}
        (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close()


if __name__=='__main__':main()
