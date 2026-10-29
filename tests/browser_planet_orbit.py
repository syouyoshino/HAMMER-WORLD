"""Read-only Chromium orbital regression for an explicitly supplied V10 fixture.

Set WOLD_ORBIT_TEST_BASE and WOLD_ORBIT_TEST_CAMPAIGN to an isolated local-mode
preview. Protected writes/auth/history are covered by browser_planet_detail.py.
"""
import json,time,hashlib,math,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HOOK='''(()=>{const id=setInterval(()=>{if(!window.HWPlanetOrbit||!window.HWMapRenderer)return;clearInterval(id);const m=window.HWPlanetOrbit,create=m.create;m.create=function(...args){const r=create(...args);if(r){window.__orbitEngine=r;const render=r.render;r.render=function(source,revision,w,h,view,rect,starDirection){const start=performance.now();const result=render.call(this,source,revision,w,h,view,rect,starDirection);window.__orbitAudit={view:{...view},starDirection:starDirection?[...starDirection]:null,rect,w,h,revision,ms:performance.now()-start,result};return result;};}return r;};const r=window.HWMapRenderer,draw=r.drawPlanet;r.drawPlanet=function(ctx,o){const t=draw(ctx,o);window.__surfaceAudit={o,t};return t;};},5);})()'''
def wait_mode(page,mode):
 page.wait_for_function('mode=>document.querySelector("#orbit-toggle")?.textContent.trim()===mode',arg=mode,timeout=90000);page.wait_for_timeout(600)
def open_campaign(page,cid):
 page.select_option('#campaign-select',cid);wait_mode(page,'Surface')
def view(page):return page.evaluate('window.__orbitAudit?.view')
def surface_camera(page):return page.evaluate('''()=>{const t=window.__surfaceAudit?.t;return t?{ox:t.ox,oy:t.oy,tile:t.tile}:null}''')
def main():
    BASE=os.environ['WOLD_ORBIT_TEST_BASE'].rstrip('/')
    CAMPAIGN=os.environ['WOLD_ORBIT_TEST_CAMPAIGN']
    OUT=Path(os.environ.get('WOLD_ORBIT_TEST_OUT', ROOT/'data/planet-scale/orbit-browser'));OUT.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
     b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
     context=b.new_context(viewport={'width':1440,'height':1024},has_touch=True);page=context.new_page();page.add_init_script(HOOK);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     page.goto(BASE);page.wait_for_selector(f'#campaign-select option[value="{CAMPAIGN}"]',state='attached')
     if page.locator('[data-dialog-close]').is_visible():page.locator('[data-dialog-close]').click()
     open_campaign(page,CAMPAIGN);page.screenshot(path=str(OUT/'01-globe.png'));initial=view(page)
     saved_astronomy=page.request.get(f'{BASE}/api/player/campaigns/{CAMPAIGN}').json()['state'].get('astronomy')
     if not saved_astronomy:
      assert page.locator('#orbit-star-locate').is_visible() and page.locator('#orbit-star-locate').is_disabled()
      assert page.locator('#orbit-star-locate').inner_text()=='Star unlocated'
     page.locator('#zoom-in').click();after_in=view(page);assert after_in['distance']<initial['distance'],'Orbit zoom-in button did not descend'
     page.locator('#zoom-out').click();assert view(page)['distance']>after_in['distance'],'Orbit zoom-out button did not pull back'
     page.locator('#zoom-reset').click();assert abs(view(page)['distance']-2.45)<1e-8,'Orbit reset failed'
     initial=view(page)
     box=page.locator('#planet-map').bounding_box();cx=box['x']+box['width']/2;cy=box['y']+box['height']/2
     page.evaluate('window.__mapCanvas=document.querySelector("#planet-map")')
     page.mouse.move(cx,cy);page.wait_for_timeout(50);assert page.locator('#map-tooltip').is_hidden(),'Planar tooltip leaked into orbit'
     page.mouse.down();page.mouse.move(cx+400,cy-70,steps=12);page.mouse.up();page.wait_for_timeout(250);rotated=view(page);page.screenshot(path=str(OUT/'02-rotated.png'))
     assert initial!=rotated,'Orbit drag did not rotate'
     page.select_option('#overlay-select','population');page.wait_for_timeout(750);overlay_view=view(page)
     assert abs(overlay_view['longitude']-rotated['longitude'])<.001,'Overlay changed orbit orientation'
     page.select_option('#overlay-select','terrain');page.wait_for_timeout(750)
     page.locator('#orbit-toggle').click();page.wait_for_timeout(70);page.screenshot(path=str(OUT/'03-transition.png'));wait_mode(page,'Orbit');camera=surface_camera(page);page.screenshot(path=str(OUT/'04-surface.png'))
     assert camera and camera['tile']>0,'Surface renderer not restored'
     page.locator('#hw-command').tap();page.locator('#command-menu [data-open="economy"]').click();page.wait_for_function('!document.querySelector("#command-workspace").hidden');page.locator('[data-return-map]:visible').click();page.wait_for_timeout(150)
     assert surface_camera(page)==camera,'Management return changed camera'
     page.locator('#orbit-toggle').tap();wait_mode(page,'Surface');returned=view(page);page.screenshot(path=str(OUT/'05-return-orbit.png'))
     print(json.dumps({'initial':initial,'rotated':rotated,'returned':returned,'camera':camera}),flush=True)
     assert abs(math.atan2(math.sin(returned['longitude']-rotated['longitude']),math.cos(returned['longitude']-rotated['longitude'])))<.03,'Roundtrip lost longitude'
     # Actual context loss must restore usable surface.
     page.evaluate('window.__orbitEngine.gl.getExtension("WEBGL_lose_context").loseContext()');page.wait_for_timeout(500);loss_status=page.locator('#planet-orbit-status').inner_text();page.screenshot(path=str(OUT/'06-context-loss.png'))
     assert page.evaluate('document.querySelector("#planet-map")===window.__mapCanvas'),'Map canvas remounted'
     # A separate browser context without WebGL must retain recorded surface.
     fallback=context.new_page();fallback.add_init_script('''(()=>{const get=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind==='webgl'||kind==='webgl2'?null:get.call(this,kind,...args)};})()''');fallback.goto(BASE);fallback.wait_for_selector(f'#campaign-select option[value="{CAMPAIGN}"]',state='attached')
     if fallback.locator('[data-dialog-close]').is_visible():fallback.locator('[data-dialog-close]').click()
     fallback.select_option('#campaign-select',CAMPAIGN);fallback.wait_for_timeout(2500);fallback.screenshot(path=str(OUT/'07-webgl-unavailable.png'));fallback_status=fallback.locator('#planet-orbit-status').inner_text()
     assert 'unavailable' in fallback_status.lower(),'Missing explicit WebGL fallback state'
     assert fallback.locator('#orbit-toggle').is_hidden() or fallback.locator('#orbit-toggle').is_disabled(),'Unavailable WebGL exposed broken orbit action'
     report={'initial':initial,'rotated':rotated,'overlay_view':overlay_view,'surface_camera':camera,'returned':returned,'context_loss_status':loss_status,'fallback_status':fallback_status,'errors':errors,'chromium':b.version,'viewport':[1440,1024],'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['public/app.js','public/map-renderer.js','public/planet-orbit.js']}}
     (OUT/'workflow.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert not errors
     b.close()


if __name__ == "__main__":
    main()
