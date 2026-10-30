"""Read-only desktop hierarchy camera continuity and translucent chrome checks."""
import hashlib
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK

HOOK_HIERARCHY='''(()=>{const t=setInterval(()=>{if(!window.HWMapRenderer)return;clearInterval(t);
const m=HWMapRenderer,draw=m.drawHierarchy;m.drawHierarchy=function(ctx,o){const result=draw.call(this,ctx,o);
window.__hierarchyAudit={level:o.record.level,parent:o.record.parent?.id,zoom:o.zoom,panX:o.panX,panY:o.panY,
positions:result.positions.map(p=>({id:p.n.id,x:p.x,y:p.y}))};return result;};
window.__zoomFrames=[];const timer=setInterval(()=>{const r=window.__orbitEngine;if(!r)return;clearInterval(timer);
const render=r.render;r.render=function(...args){const start=performance.now(),result=render.apply(this,args);
__zoomFrames.push({distance:args[4].distance,time:start,scale:args[7]??1,renderCallMs:performance.now()-start,buffer:[r.canvas.width,r.canvas.height]});
if(__zoomFrames.length>400)__zoomFrames.shift();return result;};
const proto=CanvasRenderingContext2D.prototype,copy=proto.drawImage;proto.drawImage=function(source,...args){const result=copy.call(this,source,...args);
if(source===r.canvas&&__zoomFrames.length){const frame=__zoomFrames.at(-1);frame.throughGlobeCopyMs=performance.now()-frame.time;}return result;};},5);},5)})()'''

HOOK_SYSTEM='''(()=>{const t=setInterval(()=>{if(!window.HWSystemView)return;clearInterval(t);
const draw=HWSystemView.draw;HWSystemView.draw=function(ctx,o){const result=draw.call(this,ctx,o);
window.__systemAudit={view:{...o.view},layout:result};window.__hierarchyAudit={level:'system',parent:o.record.parent?.id,
zoom:o.view.distance,panX:o.view.panX||0,panY:o.view.panY||0,positions:result.positions.map(p=>({id:p.n.id,x:p.x,y:p.y}))};return result;};},5)})()'''


def main():
    out=Path(os.environ.get('WOLD_NAV_OUT','data/navigation-glass/final'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/style.css','public/desktop-shell.css','public/system-view.js','public/body-focus.js','public/planet-orbit.js']
    hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files}
    initial=hashes();errors=[];steps=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.context.tracing.start(screenshots=True,snapshots=True)
        for hook in [HOOK,HOOK_HIERARCHY,HOOK_SYSTEM]:page.add_init_script(hook)
        page.on('pageerror',lambda e:errors.append(str(e)))
        base='http://127.0.0.1:4213';page.goto(base)
        page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached')
        if page.locator('[data-dialog-close]').is_visible():page.locator('[data-dialog-close]').click()
        before=page.request.get(base+'/api/player/campaigns/nav-demo').json()
        page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000)
        page.evaluate("HWTheme.set('dark')");canvas=page.locator('#planet-map').element_handle()
        def snap(name):
            page.wait_for_timeout(500);page.screenshot(path=str(out/(name+'.png')))
            (out/(name+'.yml')).write_text(page.locator('body').aria_snapshot());steps.append(name)
        def navigate(level):
            page.select_option('#map-level',level)
            if level=='planet':page.wait_for_function("document.querySelector('#view-title h1').textContent.includes('Planet')")
            else:page.wait_for_function('level=>window.__hierarchyAudit?.level===level',arg=level)
            page.wait_for_timeout(700)
        def drag():
            point=page.evaluate('''()=>{for(let y=innerHeight*.55;y<innerHeight-120;y+=40)for(let x=innerWidth*.35;x<innerWidth*.65;x+=40)if(document.elementFromPoint(x,y)?.id==='planet-map')return {x,y};return null}''')
            assert point
            page.mouse.move(point['x'],point['y']);page.mouse.down();page.mouse.move(point['x']+65,point['y']+15,steps=6);page.mouse.up()
            page.wait_for_timeout(400)
        snap('01-globe')
        page.evaluate('__zoomFrames=[]');page.locator('#zoom-in').click();page.wait_for_timeout(1100)
        frames=page.evaluate('__zoomFrames');assert frames
        assert any(f['scale']==.5 for f in frames) and frames[-1]['scale']==1,frames
        zoom_distances=sorted(set(round(f['distance'],7) for f in frames))
        drag();orbit=page.evaluate('({...__orbitAudit.view})');snap('02-globe-moved')
        assert page.evaluate('__orbitAudit.renderScale')==1,'Drag release must restore full resolution'
        navigate('system');snap('03-system')
        system_before=page.evaluate('__systemAudit.view')
        drag();page.locator('#zoom-in').click();page.wait_for_timeout(300)
        system_view=page.evaluate('__systemAudit.view')
        assert system_view['yaw']!=system_before['yaw'] or system_view['pitch']!=system_before['pitch']
        assert system_view['distance']<system_before['distance']
        snap('03b-system-orbited')
        system=page.evaluate('({...__hierarchyAudit})')
        navigate('planet');page.wait_for_function("document.querySelector('#orbit-toggle').textContent==='Surface'",timeout=90000)
        assert page.evaluate('__orbitAudit.view')==orbit, (orbit,page.evaluate('__orbitAudit.view'))
        snap('04-globe-restored')
        page.locator('#orbit-toggle').click();page.wait_for_timeout(900);drag()
        surface=page.evaluate('({ox:__surfaceAudit.t.ox,oy:__surfaceAudit.t.oy,tile:__surfaceAudit.t.tile})')
        snap('05-surface')
        navigate('system')
        restored=page.evaluate('__hierarchyAudit')
        assert all(restored[k]==system[k] for k in ['zoom','panX','panY','parent']), (restored,system)
        assert page.evaluate('__systemAudit.view')==system_view
        navigate('planet');page.wait_for_function("document.querySelector('#orbit-toggle').textContent==='Orbit'")
        actual=page.evaluate('({ox:__surfaceAudit.t.ox,oy:__surfaceAudit.t.oy,tile:__surfaceAudit.t.tile})')
        assert actual==surface,(actual,surface)
        snap('06-surface-restored')
        # One accepted destination must win over an older held map request.
        held=[]
        def hold(route):
            if 'level=system' in route.request.url and not held:held.append((route,route.fetch()))
            else:route.continue_()
        page.route('**/map?**',hold);page.select_option('#map-level','system')
        page.wait_for_function("document.querySelector('#map-level').value==='system'")
        navigate('sector');assert held
        held[0][0].fulfill(response=held[0][1]);page.wait_for_timeout(500)
        assert page.locator('#map-level').input_value()=='sector'
        assert page.evaluate('__hierarchyAudit.level')=='sector'
        page.unroute('**/map?**',hold)
        navigate('planet')
        # Real workspace panels and chart chrome in both themes.
        glass={}
        for theme in ['dark','light']:
            page.evaluate('(t)=>HWTheme.set(t)',theme)
            page.locator('#hw-command').click();page.locator('#command-menu [data-open="economy"]').click()
            page.wait_for_selector('#command-workspace:visible');snap('07-economy-'+theme)
            glass[theme]=page.evaluate('''()=>Object.fromEntries(['.commandbar','#view-title','#command-workspace'].map(s=>{
              const c=getComputedStyle(document.querySelector(s));return [s,{background:c.backgroundColor,opacity:c.opacity,filter:c.backdropFilter}];}))''')
            for value in glass[theme].values():
                assert value['opacity']=='1',value
                assert value['background'].startswith('rgba('),value
            page.locator('[data-return-map]').click()
        # Reduced motion should not leave a transition or queued globe movement.
        page.emulate_media(reduced_motion='reduce');navigate('system');navigate('planet')
        page.wait_for_timeout(500)
        assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')
        assert before==page.request.get(base+'/api/player/campaigns/nav-demo').json()
        assert not errors and initial==hashes(),errors
        report={'browser':browser.version,'steps':steps,'orbit_camera_restored':True,'surface_camera_restored':True,
                'system_camera_restored':True,'stale_navigation_rejected':True,'same_canvas':True,
                'both_themes':glass,'reduced_motion_exercised':True,'zoom_unique_distances':zoom_distances,
                'zoom_render_samples':frames,'records_unchanged':True,'page_errors':errors,'source_hashes':hashes(),
                'limits':'Desktop Chromium software GPU. Recorded-position perspective system; enlarged symbols, not physical orbital flight. ThroughGlobeCopyMs includes render/background/readback, not all UI work. Sampled render calls do not prove smooth hardware FPS.'}
        page.context.tracing.stop(path=str(out/'workflow-trace.zip'))
        (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close()


if __name__=='__main__':main()
