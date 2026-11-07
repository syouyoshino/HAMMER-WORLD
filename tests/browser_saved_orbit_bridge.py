"""Read-only saved camera return: validated raw reuse and actual bridge publication."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK
from tests.browser_navigation_continuity import HOOK_SYSTEM


def main():
    out=Path('data/motion-fix/saved-orbit');out.mkdir(parents=True,exist_ok=True)
    reports=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        for reduced in [False,True]:
            page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce' if reduced else 'no-preference')
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            for hook in [HOOK,HOOK_SYSTEM]:page.add_init_script(hook)
            page.goto('http://127.0.0.1:4213');page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached')
            if page.locator('[data-dialog-close]').is_visible():page.locator('[data-dialog-close]').click()
            page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000);page.wait_for_timeout(800)
            # Save a camera that differs from canonical arrival distance and orientation.
            page.locator('#zoom-in').click();page.wait_for_timeout(500)
            origin=page.evaluate('__orbitAudit.view')
            page.select_option('#map-level','system');page.wait_for_function('window.__systemAudit?.layout.supported');page.wait_for_function("document.querySelector('.section-title h1').textContent.includes('System') && document.querySelector('#detail-status').hidden && !document.querySelector('.map-frame').classList.contains('is-orbit-bridging')",timeout=90000)
            page.wait_for_function('HWSystemPreviewService.getPlanet("nav-demo-planet-reach","orbital")',timeout=90000)
            page.evaluate('HWSystemPreviewService.suspend()')
            page.evaluate('''()=>{window.__savedBridge=[];const bridge=HWSystemView.bridgeCircle;HWSystemView.bridgeCircle=(from,to,t)=>{const circle=bridge(from,to,t);__savedBridge.push({time:performance.now(),progress:t,circle,from,to});return circle;};}''')
            requests=[];page.on('request',lambda request:requests.append(request.url) if '/detail?' in request.url and 'planet_id=nav-demo-planet-reach&' in request.url else None)
            page.select_option('#map-level','planet')
            page.wait_for_function("document.querySelector('.section-title h1').textContent.endsWith(' · Orbit') && document.querySelector('#orbit-toggle').textContent==='Surface'",timeout=90000)
            assert page.evaluate('__orbitAudit.view')==origin
            assert not requests,requests
            cached_requests=len(requests)
            frames=page.evaluate('__savedBridge')
            if not reduced:
                assert frames and frames[0]['progress']==0,frames
                moving=[f for f in frames if 0<f['progress']<1]
                assert len(moving)>=8 and moving[0]['progress']<.1,frames
                assert frames[-1]['progress']==1
                for key in ['x','y','radius']:assert abs(frames[-1]['circle'][key]-frames[-1]['to'][key])<1e-8
            else:assert not frames
            assert not errors,errors
            if not reduced:
                page.select_option('#map-level','system');page.wait_for_function("document.querySelector('.section-title h1').textContent.includes('System') && document.querySelector('#detail-status').hidden && !document.querySelector('.map-frame').classList.contains('is-orbit-bridging')",timeout=90000)
                page.evaluate('HWSystemPreviewService.clear()')
                def mismatch(route):
                    if 'level=planet' not in route.request.url:return route.continue_()
                    response=route.fetch();data=response.json();data['snapshot_id']='fixture-wrong-snapshot'
                    route.fulfill(response=response,json=data)
                page.route('**/map?**',mismatch)
                page.evaluate('__savedBridge=[]')
                page.select_option('#map-level','planet')
                page.wait_for_function("document.querySelector('.toast')?.textContent.includes('did not match')")
                assert page.locator('#map-level').input_value()=='system'
                assert 'System' in page.locator('.section-title h1').inner_text()
                assert page.evaluate('__savedBridge.length')==0
                page.unroute('**/map?**',mismatch)
                # The retained System record must accept a new camera save after rollback.
                point=page.evaluate('''()=>{for(let y=innerHeight*.55;y<innerHeight-120;y+=40)for(let x=innerWidth*.35;x<innerWidth*.65;x+=40)if(document.elementFromPoint(x,y)?.id==='planet-map')return {x,y};return null}''')
                assert point
                previous_source=page.evaluate('__systemAudit.view')
                page.keyboard.down('Shift');page.mouse.move(point['x'],point['y']);page.mouse.down()
                page.mouse.move(point['x']+80,point['y']+30,steps=6);page.mouse.up();page.keyboard.up('Shift')
                page.select_option('#system-body-select','nav-demo-planet-reach');page.locator('#system-focus').click();page.wait_for_timeout(500)
                adjusted_source=page.evaluate('__systemAudit.view')
                assert adjusted_source!=previous_source
                assert adjusted_source['panX']!=previous_source['panX'] or adjusted_source['panY']!=previous_source['panY']
                page.select_option('#map-level','planet')
                page.wait_for_function("document.querySelector('.section-title h1').textContent.endsWith(' · Orbit') && document.querySelector('#orbit-toggle').textContent==='Surface'",timeout=90000)
                page.select_option('#map-level','system')
                page.wait_for_function("document.querySelector('.section-title h1').textContent.includes('System') && document.querySelector('#detail-status').hidden && !document.querySelector('.map-frame').classList.contains('is-orbit-bridging')",timeout=90000)
                assert page.evaluate('__systemAudit.view')==adjusted_source,'Post-error System camera was not saved for the successful retry'
                page.evaluate('HWSystemPreviewService.clear()')
                held=[];holding=True
                def hold(route):
                    if not holding:return route.continue_()
                    held.append((route,route.fetch()))
                page.route('**/detail?**',hold)
                page.select_option('#map-level','planet')
                page.wait_for_function("document.querySelector('#detail-status').textContent.includes('Opening saved orbit')")
                for _ in range(100):
                    if held:break
                    page.wait_for_timeout(50)
                assert held,'Uncached saved return did not request detail'
                holding=False
                page.select_option('#map-level','system');page.wait_for_timeout(600)
                for route,response in held:route.fulfill(response=response)
                page.wait_for_timeout(600)
                assert 'System' in page.locator('.section-title h1').inner_text()
                page.unroute('**/detail?**',hold)
                page.evaluate('HWSystemPreviewService.clear()')
                page.route('**/detail?**',lambda route:route.fulfill(status=503,content_type='application/json',body='{"detail":"Fixture unavailable"}'))
                page.select_option('#map-level','planet')
                page.wait_for_function("document.querySelector('#detail-status').textContent.toLowerCase().includes('unavailable')",timeout=90000)
                assert 'Opening' not in page.locator('.section-title h1').inner_text()
                assert page.locator('#zoom-reset').is_enabled()
                assert not errors,errors
            reports.append({'post_error_system_camera':not reduced,'cancel_stale_release':not reduced,'detail_error_usable':not reduced,'reduced':reduced,'exact_camera':True,'detail_requests':cached_requests,'frames':frames,'page_errors':errors})
            page.unroute_all(behavior='ignoreErrors')
            page.close()
        browser.close()
    (out/'report.json').write_text(json.dumps(reports,indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='frames'} for r in reports]))


if __name__=='__main__':main()
